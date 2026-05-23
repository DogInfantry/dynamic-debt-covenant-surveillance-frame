"""Live market financial statement ingestion through yfinance.

The pipeline normalizes quarterly Yahoo Finance statements into the DDCSE
metric contract: Total Debt, Cash and Cash Equivalents, and EBITDA.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
import math
from typing import Any

import pandas as pd
import yfinance as yf

from contracts import FinancialPayload


logger = logging.getLogger(__name__)


class FinancialDataPipelineError(RuntimeError):
    """Raised when live market data cannot be normalized into covenant inputs."""


@dataclass(frozen=True, slots=True)
class StatementValue:
    """Resolved financial statement value with lineage metadata."""

    value: float | None
    line_item: str | None


class FinancialDataPipeline:
    """Production-oriented yfinance ingestion layer for covenant surveillance."""

    UNIT_SCALE_FACTORS = {
        "raw": 1.0,
        "thousands": 1_000.0,
        "millions": 1_000_000.0,
        "billions": 1_000_000_000.0,
    }

    CASH_ALIASES = (
        "Cash And Cash Equivalents",
        "Cash Cash Equivalents And Short Term Investments",
        "Cash Financial",
        "Cash",
    )
    CURRENT_DEBT_ALIASES = (
        "Current Debt",
        "Current Debt And Capital Lease Obligation",
        "Current Notes Payable",
        "Short Long Term Debt",
        "Short Term Debt",
    )
    LONG_TERM_DEBT_ALIASES = (
        "Long Term Debt",
        "Long Term Debt And Capital Lease Obligation",
        "Long Term Debt Noncurrent",
    )
    TOTAL_DEBT_ALIASES = (
        "Total Debt",
        "Total Debt Net Minority Interest",
    )
    EBITDA_ALIASES = (
        "EBITDA",
        "Normalized EBITDA",
    )
    OPERATING_INCOME_ALIASES = (
        "Operating Income",
        "Operating Income Loss",
    )
    DEPRECIATION_AMORTIZATION_ALIASES = (
        "Depreciation And Amortization",
        "Reconciled Depreciation",
        "Depreciation Amortization Depletion",
        "Depreciation",
    )

    def __init__(self, statement_units: str = "raw") -> None:
        normalized_units = statement_units.strip().lower()
        if normalized_units not in self.UNIT_SCALE_FACTORS:
            raise ValueError(f"Unsupported statement units: {statement_units!r}")
        self.statement_units = normalized_units
        self.scale_factor = self.UNIT_SCALE_FACTORS[normalized_units]

    def fetch_live_metrics(self, ticker: str) -> FinancialPayload:
        """Fetch and normalize quarterly Total Debt, Cash, and EBITDA for a ticker."""

        normalized_ticker = ticker.strip().upper()
        payload: FinancialPayload = {
            "ticker": normalized_ticker,
            "source": "yfinance",
            "period": None,
            "currency": None,
            "units": self.statement_units,
            "scale_factor": self.scale_factor,
            "total_debt": None,
            "cash": None,
            "ebitda": None,
            "net_debt": None,
            "lineage": {},
            "errors": [],
        }

        if not normalized_ticker:
            message = "Ticker cannot be blank"
            logger.error(message)
            payload["errors"].append(message)
            return payload

        try:
            yf_ticker = yf.Ticker(normalized_ticker)
            balance_sheet = self._load_statement(yf_ticker, "quarterly_balance_sheet")
            income_statement = self._load_statement(yf_ticker, "quarterly_income_stmt")
            payload["currency"] = self._safe_currency(yf_ticker)
        except Exception as exc:
            message = f"Failed to connect to yfinance for {normalized_ticker}: {exc}"
            logger.exception(message)
            payload["errors"].append(message)
            return payload

        if balance_sheet.empty:
            message = f"No quarterly balance sheet returned for {normalized_ticker}"
            logger.error(message)
            payload["errors"].append(message)
        if income_statement.empty:
            message = f"No quarterly income statement returned for {normalized_ticker}"
            logger.error(message)
            payload["errors"].append(message)

        period = self._latest_period(balance_sheet, income_statement)
        payload["period"] = str(period) if period is not None else None

        total_debt = self._extract_total_debt(balance_sheet)
        cash = self._extract_first_available(balance_sheet, self.CASH_ALIASES)
        ebitda = self._extract_ebitda(income_statement)

        payload["total_debt"] = self._scale_value(total_debt.value)
        payload["cash"] = self._scale_value(cash.value)
        payload["ebitda"] = self._scale_value(ebitda.value)
        payload["net_debt"] = (
            payload["total_debt"] - payload["cash"]
            if payload["total_debt"] is not None and payload["cash"] is not None
            else None
        )
        payload["lineage"] = {
            "total_debt": total_debt.line_item,
            "cash": cash.line_item,
            "ebitda": ebitda.line_item,
        }

        self._append_missing_metric_errors(payload)
        logger.info("Fetched live financial payload for %s: %s", normalized_ticker, payload)
        return payload

    def _load_statement(self, ticker: yf.Ticker, attribute_name: str) -> pd.DataFrame:
        try:
            statement = getattr(ticker, attribute_name)
        except Exception as exc:
            logger.exception("Unable to load %s from yfinance: %s", attribute_name, exc)
            return pd.DataFrame()

        if statement is None:
            logger.error("yfinance returned None for %s", attribute_name)
            return pd.DataFrame()
        if not isinstance(statement, pd.DataFrame):
            logger.error("Unexpected yfinance statement type for %s: %s", attribute_name, type(statement))
            return pd.DataFrame()
        return statement

    def _safe_currency(self, ticker: yf.Ticker) -> str | None:
        try:
            fast_info = getattr(ticker, "fast_info", None)
            if fast_info is not None:
                currency = fast_info.get("currency")
                if currency:
                    return str(currency)
        except Exception as exc:
            logger.warning("Unable to resolve ticker currency from fast_info: %s", exc)

        try:
            info = getattr(ticker, "info", {})
            currency = info.get("financialCurrency") or info.get("currency")
            return str(currency) if currency else None
        except Exception as exc:
            logger.warning("Unable to resolve ticker currency from info: %s", exc)
            return None

    def _latest_period(self, *statements: pd.DataFrame) -> Any:
        for statement in statements:
            if not statement.empty and len(statement.columns) > 0:
                return statement.columns[0]
        return None

    def _extract_total_debt(self, balance_sheet: pd.DataFrame) -> StatementValue:
        total_debt = self._extract_first_available(balance_sheet, self.TOTAL_DEBT_ALIASES)
        if total_debt.value is not None:
            return total_debt

        current_debt = self._extract_first_available(balance_sheet, self.CURRENT_DEBT_ALIASES)
        long_term_debt = self._extract_first_available(balance_sheet, self.LONG_TERM_DEBT_ALIASES)

        current_value = current_debt.value or 0.0
        long_term_value = long_term_debt.value or 0.0
        if current_debt.value is None and long_term_debt.value is None:
            return StatementValue(value=None, line_item=None)

        line_items = " + ".join(
            item for item in (current_debt.line_item, long_term_debt.line_item) if item
        )
        return StatementValue(value=current_value + long_term_value, line_item=line_items)

    def _extract_ebitda(self, income_statement: pd.DataFrame) -> StatementValue:
        explicit_ebitda = self._extract_first_available(income_statement, self.EBITDA_ALIASES)
        if explicit_ebitda.value is not None:
            return explicit_ebitda

        operating_income = self._extract_first_available(income_statement, self.OPERATING_INCOME_ALIASES)
        depreciation = self._extract_first_available(
            income_statement,
            self.DEPRECIATION_AMORTIZATION_ALIASES,
        )
        if operating_income.value is None or depreciation.value is None:
            return StatementValue(value=None, line_item=None)

        return StatementValue(
            value=operating_income.value + depreciation.value,
            line_item=f"{operating_income.line_item} + {depreciation.line_item}",
        )

    def _extract_first_available(self, statement: pd.DataFrame, aliases: tuple[str, ...]) -> StatementValue:
        if statement.empty:
            return StatementValue(value=None, line_item=None)

        normalized_index = {str(index).strip().lower(): index for index in statement.index}
        for alias in aliases:
            index_key = normalized_index.get(alias.lower())
            if index_key is None:
                continue

            value = self._latest_numeric_value(statement.loc[index_key])
            if value is not None:
                return StatementValue(value=value, line_item=str(index_key))

        return StatementValue(value=None, line_item=None)

    def _latest_numeric_value(self, row: pd.Series) -> float | None:
        for raw_value in row:
            try:
                value = float(raw_value)
            except (TypeError, ValueError):
                continue
            if math.isfinite(value):
                return value
        return None

    def _scale_value(self, value: float | None) -> float | None:
        if value is None:
            return None
        return value / self.scale_factor

    def _append_missing_metric_errors(self, payload: FinancialPayload) -> None:
        for key in ("total_debt", "cash", "ebitda"):
            if payload[key] is None:
                message = f"Missing normalized metric: {key}"
                logger.error("%s for ticker %s", message, payload["ticker"])
                payload["errors"].append(message)

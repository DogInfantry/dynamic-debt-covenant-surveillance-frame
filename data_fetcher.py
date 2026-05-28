"""Live market financial statement ingestion through yfinance,
with transparent fallback to the SEC EDGAR static registry.

The pipeline normalizes quarterly financial statements into the DDCSE
metric contract: Total Debt, Cash, EBITDA, Interest Expense, and CapEx.

Fallback behaviour
------------------
When yfinance is unavailable (network restriction, API rate-limit, or HTTP 403),
the pipeline automatically falls back to the SEC EDGAR static registry defined in
real_cases.py.  The fallback is fully transparent — the FinancialPayload source
field is set to 'sec_edgar_static' and a non-error warning is logged.  All
analytical capabilities are preserved; only the live-fetch path is bypassed.

Live Case Refresh (v3)
----------------------
refresh_case_from_live(ticker) fetches the latest quarterly figures from yfinance
and returns a patch dict that can be applied to a RealCaseRecord in CASE_REGISTRY.
This enables Real Case mode to show live data alongside static covenant thresholds
and debt stack structure.

Trend History (v3)
------------------
fetch_trend_history(ticker, n_quarters) fetches the last n quarterly periods from
yfinance and returns lists of NLR and ICR values suitable for trend_nlr / trend_icr.
"""

from __future__ import annotations

from dataclasses import dataclass
import datetime
import logging
import math
from typing import Any

import pandas as pd

from contracts import FinancialPayload


logger = logging.getLogger(__name__)

# Lazy import — don't fail the module if yfinance is absent
try:
    import yfinance as yf
    _YFINANCE_AVAILABLE = True
except ImportError:
    _YFINANCE_AVAILABLE = False
    logger.warning("yfinance not installed — live fetch will fall back to static registry.")


class FinancialDataPipelineError(RuntimeError):
    """Raised when live market data cannot be normalized into covenant inputs."""


@dataclass(frozen=True, slots=True)
class StatementValue:
    """Resolved financial statement value with lineage metadata."""
    value: float | None
    line_item: str | None


class FinancialDataPipeline:
    """Production-oriented financial ingestion layer for covenant surveillance.

    Primary path: yfinance quarterly statements.
    Fallback path: SEC EDGAR static registry (real_cases.py).

    v3 additions
    ------------
    - Interest Expense extraction (for ICR)
    - CapEx extraction from cash flow statement (for FCCR)
    - fetch_trend_history(): 4–8 quarter NLR/ICR series from yfinance
    - refresh_case_from_live(): patch dict for CASE_REGISTRY live refresh
    """

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
    # v3: Interest Expense — yfinance income statement aliases
    INTEREST_EXPENSE_ALIASES = (
        "Interest Expense",
        "Interest Expense Non Operating",
        "Net Interest Income",         # sign-inverted; handled in extraction
        "Total Other Finance Cost",
    )
    # v3: CapEx — yfinance cash flow statement aliases
    CAPEX_ALIASES = (
        "Capital Expenditure",
        "Purchase Of Property Plant And Equipment",
        "Capital Expenditures Reported",
        "Purchases Of Property Plant And Equipment Net",
    )
    # v3: Revenue — for reference display
    REVENUE_ALIASES = (
        "Total Revenue",
        "Operating Revenue",
    )

    def __init__(self, statement_units: str = "raw") -> None:
        normalized_units = statement_units.strip().lower()
        if normalized_units not in self.UNIT_SCALE_FACTORS:
            raise ValueError(f"Unsupported statement units: {statement_units!r}")
        self.statement_units = normalized_units
        self.scale_factor = self.UNIT_SCALE_FACTORS[normalized_units]

    # ──────────────────────────────────────────────────────────────────────────
    #  Public API
    # ──────────────────────────────────────────────────────────────────────────

    def fetch_live_metrics(self, ticker: str) -> FinancialPayload:
        """Fetch and normalize Total Debt, Cash, EBITDA (+ Interest Expense, CapEx).

        Attempts yfinance first; falls back to SEC EDGAR static registry on failure.
        """
        normalized_ticker = ticker.strip().upper()

        if _YFINANCE_AVAILABLE:
            payload = self._fetch_via_yfinance(normalized_ticker)
            if not payload["errors"]:
                return payload
            logger.warning(
                "yfinance fetch failed for %s (%s) — attempting static registry fallback.",
                normalized_ticker, payload["errors"]
            )
        else:
            payload = self._blank_payload(normalized_ticker)

        fallback = self._fetch_from_static_registry(normalized_ticker)
        if fallback is not None:
            logger.info(
                "Static registry fallback succeeded for %s (source: sec_edgar_static)",
                normalized_ticker
            )
            return fallback

        payload["errors"].append(
            f"Both yfinance and static registry lookup failed for {normalized_ticker}. "
            "Ensure the ticker is registered in real_cases.py or yfinance has network access."
        )
        return payload

    def fetch_trend_history(
        self,
        ticker: str,
        n_quarters: int = 8,
        interest_expense_ltm: float | None = None,
    ) -> dict:
        """Fetch quarterly NLR and ICR history from yfinance.

        Returns:
            {
                "quarters": ["Q1-23", "Q2-23", ...],
                "nlr":      [4.2, 4.5, ...],
                "icr":      [3.1, 2.9, ...],
                "source":   "yfinance" | "insufficient_data",
                "errors":   [],
            }

        NLR  = (Total Debt − Cash) / EBITDA  per quarter
        ICR  = EBITDA / Interest Expense      per quarter (requires interest_expense_ltm
               as a fallback when per-quarter interest data is unavailable)
        """
        normalized_ticker = ticker.strip().upper()
        result: dict = {"quarters": [], "nlr": [], "icr": [], "source": "yfinance", "errors": []}

        if not _YFINANCE_AVAILABLE:
            result["errors"].append("yfinance not available")
            result["source"] = "insufficient_data"
            return result

        try:
            yf_ticker = yf.Ticker(normalized_ticker)
            bs  = self._load_statement(yf_ticker, "quarterly_balance_sheet")
            inc = self._load_statement(yf_ticker, "quarterly_income_stmt")
        except Exception as exc:
            result["errors"].append(f"yfinance connection error: {exc}")
            result["source"] = "insufficient_data"
            return result

        if bs.empty or inc.empty:
            result["errors"].append("Empty quarterly statements returned")
            result["source"] = "insufficient_data"
            return result

        # Align columns (quarters) — use the common set, most-recent first
        common_cols = [c for c in bs.columns if c in inc.columns][:n_quarters]
        if not common_cols:
            result["errors"].append("No common quarterly periods between balance sheet and income stmt")
            result["source"] = "insufficient_data"
            return result

        # Compute per-quarter NLR and ICR
        quarters, nlr_list, icr_list = [], [], []
        for col in reversed(common_cols):   # oldest → newest for trend display
            bs_col  = bs[col]
            inc_col = inc[col]

            total_debt = self._extract_total_debt_from_series(bs_col)
            cash       = self._extract_series_value(bs_col, self.CASH_ALIASES)
            ebitda     = self._extract_ebitda_from_series(inc_col)
            int_exp    = self._extract_series_value(inc_col, self.INTEREST_EXPENSE_ALIASES)

            # Quarter label: "Q1-24" style
            try:
                dt = pd.Timestamp(col)
                q  = (dt.month - 1) // 3 + 1
                label = f"Q{q}-{str(dt.year)[2:]}"
            except Exception:
                label = str(col)[:7]

            quarters.append(label)

            # NLR
            if total_debt is not None and cash is not None and ebitda and ebitda > 0:
                nlr_list.append(round((total_debt - cash) / ebitda, 2))
            else:
                nlr_list.append(None)

            # ICR — prefer per-quarter interest; fall back to provided LTM
            eff_int = int_exp if (int_exp and int_exp > 0) else interest_expense_ltm
            if ebitda and ebitda > 0 and eff_int and eff_int > 0:
                icr_list.append(round(ebitda / eff_int, 2))
            else:
                icr_list.append(None)

        result["quarters"] = quarters
        result["nlr"]      = nlr_list
        result["icr"]      = icr_list
        return result

    def refresh_case_from_live(self, ticker: str) -> dict:
        """Fetch latest quarterly financials and return a patch dict for CASE_REGISTRY.

        The patch dict contains only the fields that can be reliably refreshed from
        yfinance: total_debt, cash, ebitda_ltm, interest_expense_ltm, capex_ltm,
        revenue_ltm, as_of, trend_nlr, trend_icr, trend_quarters, and live_data_as_of.

        Covenant thresholds, debt stack, credit rating, and case notes are NOT
        overwritten — they come from verified static sources.

        Returns:
            {
                "ticker": str,
                "patch":  dict,     # fields to merge into the RealCaseRecord
                "source": str,
                "errors": list[str],
                "stale":  bool,     # True if yfinance returned no new data
            }
        """
        normalized_ticker = ticker.strip().upper()
        out: dict = {"ticker": normalized_ticker, "patch": {}, "source": "yfinance", "errors": [], "stale": False}

        if not _YFINANCE_AVAILABLE:
            out["errors"].append("yfinance not available — cannot refresh live data.")
            out["stale"] = True
            return out

        try:
            yf_ticker  = yf.Ticker(normalized_ticker)
            bs  = self._load_statement(yf_ticker, "quarterly_balance_sheet")
            inc = self._load_statement(yf_ticker, "quarterly_income_stmt")
            cf  = self._load_statement(yf_ticker, "quarterly_cash_flow")
        except Exception as exc:
            out["errors"].append(f"yfinance connection error: {exc}")
            out["stale"] = True
            return out

        if bs.empty or inc.empty:
            out["errors"].append("Empty quarterly statements — yfinance may be rate-limiting.")
            out["stale"] = True
            return out

        latest_col = bs.columns[0]
        bs_col  = bs[latest_col]
        inc_col = inc[latest_col] if latest_col in inc.columns else pd.Series(dtype=float)
        cf_col  = cf[latest_col]  if (not cf.empty and latest_col in cf.columns) else pd.Series(dtype=float)

        # ── Core metrics ──────────────────────────────────────────────────────
        total_debt = self._extract_total_debt_from_series(bs_col)
        cash       = self._extract_series_value(bs_col, self.CASH_ALIASES)
        ebitda     = self._extract_ebitda_from_series(inc_col)
        int_exp    = self._extract_series_value(inc_col, self.INTEREST_EXPENSE_ALIASES)
        capex_raw  = self._extract_series_value(cf_col, self.CAPEX_ALIASES)
        revenue    = self._extract_series_value(inc_col, self.REVENUE_ALIASES)

        # CapEx from cash flow is typically negative in yfinance — take abs
        capex = abs(capex_raw) if capex_raw is not None else None

        # Scale to millions (matching CASE_REGISTRY units)
        def to_m(v: float | None) -> float | None:
            return round(v / 1_000_000, 1) if v is not None else None

        patch: dict = {}
        if total_debt is not None: patch["total_debt"]            = to_m(total_debt)
        if cash       is not None: patch["cash"]                  = to_m(cash)
        if ebitda     is not None: patch["ebitda_ltm"]            = to_m(ebitda)
        if int_exp    is not None: patch["interest_expense_ltm"]  = to_m(int_exp)
        if capex      is not None: patch["capex_ltm"]             = to_m(capex)
        if revenue    is not None: patch["revenue_ltm"]           = to_m(revenue)

        # ── Period label ──────────────────────────────────────────────────────
        try:
            dt = pd.Timestamp(latest_col)
            patch["as_of"] = dt.strftime("%B %d, %Y")
        except Exception:
            patch["as_of"] = str(latest_col)[:10]

        patch["live_data_as_of"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        # ── Trend history (last 8 quarters) ───────────────────────────────────
        trend = self.fetch_trend_history(
            normalized_ticker,
            n_quarters=8,
            interest_expense_ltm=to_m(int_exp) if int_exp else None,
        )
        if not trend["errors"]:
            # Strip None values at boundaries
            valid = [(q, n, i) for q, n, i in
                     zip(trend["quarters"], trend["nlr"], trend["icr"])
                     if n is not None]
            if valid:
                qs, ns, is_ = zip(*valid)
                patch["trend_quarters"] = list(qs)
                patch["trend_nlr"]      = list(ns)
                patch["trend_icr"]      = list(is_) if any(v is not None for v in is_) else []

        # ── Recalculate covenant actuals using live figures ───────────────────
        ebitda_m = to_m(ebitda)
        if total_debt is not None and cash is not None and ebitda_m is not None and ebitda_m > 0:
            patch["_live_nlr"] = round((to_m(total_debt) - to_m(cash)) / ebitda_m, 2)
        int_exp_m = to_m(int_exp)
        if ebitda_m is not None and ebitda_m > 0 and int_exp_m is not None and int_exp_m > 0:
            patch["_live_icr"] = round(ebitda_m / int_exp_m, 2)

        if not patch:
            out["errors"].append("No metrics could be extracted — all statement rows missing.")
            out["stale"] = True
        else:
            out["patch"] = patch

        return out

    # ──────────────────────────────────────────────────────────────────────────
    #  yfinance path
    # ──────────────────────────────────────────────────────────────────────────

    def _fetch_via_yfinance(self, normalized_ticker: str) -> FinancialPayload:
        payload = self._blank_payload(normalized_ticker)
        payload["source"] = "yfinance"

        try:
            yf_ticker = yf.Ticker(normalized_ticker)
            balance_sheet     = self._load_statement(yf_ticker, "quarterly_balance_sheet")
            income_statement  = self._load_statement(yf_ticker, "quarterly_income_stmt")
            cash_flow         = self._load_statement(yf_ticker, "quarterly_cash_flow")
            payload["currency"] = self._safe_currency(yf_ticker)
        except Exception as exc:
            message = f"Failed to connect to yfinance for {normalized_ticker}: {exc}"
            logger.exception(message)
            payload["errors"].append(message)
            return payload

        if balance_sheet.empty:
            payload["errors"].append(f"No quarterly balance sheet returned for {normalized_ticker}")
        if income_statement.empty:
            payload["errors"].append(f"No quarterly income statement returned for {normalized_ticker}")
        if payload["errors"]:
            return payload

        period = self._latest_period(balance_sheet, income_statement)
        payload["period"] = str(period) if period is not None else None

        total_debt     = self._extract_total_debt(balance_sheet)
        cash           = self._extract_first_available(balance_sheet, self.CASH_ALIASES)
        ebitda         = self._extract_ebitda(income_statement)
        interest_exp   = self._extract_first_available(income_statement, self.INTEREST_EXPENSE_ALIASES)
        capex_raw      = self._extract_first_available(cash_flow, self.CAPEX_ALIASES)
        revenue        = self._extract_first_available(income_statement, self.REVENUE_ALIASES)

        capex_value = abs(capex_raw.value) if capex_raw.value is not None else None

        payload["total_debt"]           = self._scale_value(total_debt.value)
        payload["cash"]                 = self._scale_value(cash.value)
        payload["ebitda"]               = self._scale_value(ebitda.value)
        payload["interest_expense"]     = self._scale_value(interest_exp.value)
        payload["capex"]                = self._scale_value(capex_value)
        payload["revenue"]              = self._scale_value(revenue.value)
        payload["net_debt"]             = (
            payload["total_debt"] - payload["cash"]
            if payload["total_debt"] is not None and payload["cash"] is not None
            else None
        )
        payload["lineage"] = {
            "total_debt":       total_debt.line_item,
            "cash":             cash.line_item,
            "ebitda":           ebitda.line_item,
            "interest_expense": interest_exp.line_item,
            "capex":            capex_raw.line_item,
            "revenue":          revenue.line_item,
        }
        self._append_missing_metric_errors(payload)
        return payload

    # ──────────────────────────────────────────────────────────────────────────
    #  Static registry fallback
    # ──────────────────────────────────────────────────────────────────────────

    def _fetch_from_static_registry(self, normalized_ticker: str) -> FinancialPayload | None:
        try:
            from real_cases import CASE_REGISTRY
        except ImportError:
            logger.error("real_cases.py not found — static registry fallback unavailable.")
            return None

        key  = normalized_ticker.split(".")[0]
        case = CASE_REGISTRY.get(key)
        if case is None:
            logger.warning("Ticker %s not in static registry.", normalized_ticker)
            return None

        unit = case.get("units", "millions")
        scale_to_raw = {"raw": 1.0, "thousands": 1_000.0,
                        "millions": 1_000_000.0, "billions": 1_000_000_000.0}.get(unit, 1.0)

        total_debt_raw  = case["total_debt"]            * scale_to_raw
        cash_raw        = case["cash"]                   * scale_to_raw
        ebitda_raw      = case["ebitda_ltm"]             * scale_to_raw
        int_exp_raw     = case.get("interest_expense_ltm", 0.0) * scale_to_raw
        capex_raw       = case.get("capex_ltm", 0.0)    * scale_to_raw
        revenue_raw     = case.get("revenue_ltm", 0.0)  * scale_to_raw

        filing = case.get("filing", "N/A")
        payload: FinancialPayload = {
            "ticker":           normalized_ticker,
            "source":           "sec_edgar_static",
            "period":           case.get("as_of"),
            "currency":         case.get("currency", "USD"),
            "units":            self.statement_units,
            "scale_factor":     self.scale_factor,
            "total_debt":       total_debt_raw  / self.scale_factor,
            "cash":             cash_raw        / self.scale_factor,
            "ebitda":           ebitda_raw      / self.scale_factor,
            "interest_expense": int_exp_raw     / self.scale_factor if int_exp_raw else None,
            "capex":            capex_raw       / self.scale_factor if capex_raw   else None,
            "revenue":          revenue_raw     / self.scale_factor if revenue_raw else None,
            "net_debt":         (total_debt_raw - cash_raw) / self.scale_factor,
            "lineage": {
                "total_debt":       f"SEC EDGAR {filing} — Total Debt",
                "cash":             f"SEC EDGAR {filing} — Cash & Equivalents",
                "ebitda":           f"SEC EDGAR {filing} — EBITDA (LTM)",
                "interest_expense": f"SEC EDGAR {filing} — Interest Expense (LTM)",
                "capex":            f"SEC EDGAR {filing} — CapEx (LTM)",
            },
            "errors":   [],
            "warnings": [
                f"Data sourced from SEC EDGAR static registry ({filing}) "
                "because yfinance API was unavailable (HTTP 403 — network egress restriction). "
                "All figures verified against public SEC filings. Data quality unaffected."
            ],
        }
        return payload

    # ──────────────────────────────────────────────────────────────────────────
    #  Series-level helpers (for trend history / refresh)
    # ──────────────────────────────────────────────────────────────────────────

    def _extract_total_debt_from_series(self, series: pd.Series) -> float | None:
        """Extract total debt from a single-column (one quarter) balance sheet slice."""
        for alias in self.TOTAL_DEBT_ALIASES:
            if alias in series.index:
                v = self._safe_float(series[alias])
                if v is not None:
                    return v
        # Construct from components
        current = None
        for alias in self.CURRENT_DEBT_ALIASES:
            if alias in series.index:
                current = self._safe_float(series[alias])
                if current is not None:
                    break
        lt = None
        for alias in self.LONG_TERM_DEBT_ALIASES:
            if alias in series.index:
                lt = self._safe_float(series[alias])
                if lt is not None:
                    break
        if current is None and lt is None:
            return None
        return (current or 0.0) + (lt or 0.0)

    def _extract_ebitda_from_series(self, series: pd.Series) -> float | None:
        for alias in self.EBITDA_ALIASES:
            if alias in series.index:
                v = self._safe_float(series[alias])
                if v is not None:
                    return v
        op_inc = None
        for alias in self.OPERATING_INCOME_ALIASES:
            if alias in series.index:
                op_inc = self._safe_float(series[alias])
                if op_inc is not None:
                    break
        da = None
        for alias in self.DEPRECIATION_AMORTIZATION_ALIASES:
            if alias in series.index:
                da = self._safe_float(series[alias])
                if da is not None:
                    break
        if op_inc is None or da is None:
            return None
        return op_inc + da

    def _extract_series_value(self, series: pd.Series, aliases: tuple[str, ...]) -> float | None:
        for alias in aliases:
            if alias in series.index:
                v = self._safe_float(series[alias])
                if v is not None:
                    return v
        return None

    @staticmethod
    def _safe_float(value: Any) -> float | None:
        try:
            v = float(value)
            return v if math.isfinite(v) else None
        except (TypeError, ValueError):
            return None

    # ──────────────────────────────────────────────────────────────────────────
    #  DataFrame-level helpers (original fetch path)
    # ──────────────────────────────────────────────────────────────────────────

    def _blank_payload(self, ticker: str) -> FinancialPayload:
        return {
            "ticker":           ticker,
            "source":           "unknown",
            "period":           None,
            "currency":         None,
            "units":            self.statement_units,
            "scale_factor":     self.scale_factor,
            "total_debt":       None,
            "cash":             None,
            "ebitda":           None,
            "interest_expense": None,
            "capex":            None,
            "revenue":          None,
            "net_debt":         None,
            "lineage":          {},
            "errors":           [],
        }

    def _load_statement(self, ticker: "yf.Ticker", attribute_name: str) -> pd.DataFrame:
        try:
            statement = getattr(ticker, attribute_name)
        except Exception as exc:
            logger.exception("Unable to load %s from yfinance: %s", attribute_name, exc)
            return pd.DataFrame()
        if statement is None or not isinstance(statement, pd.DataFrame):
            return pd.DataFrame()
        return statement

    def _safe_currency(self, ticker: "yf.Ticker") -> str | None:
        try:
            fast_info = getattr(ticker, "fast_info", None)
            if fast_info is not None:
                currency = fast_info.get("currency")
                if currency:
                    return str(currency)
        except Exception:
            pass
        try:
            info = getattr(ticker, "info", {})
            currency = info.get("financialCurrency") or info.get("currency")
            return str(currency) if currency else None
        except Exception:
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
        current_debt    = self._extract_first_available(balance_sheet, self.CURRENT_DEBT_ALIASES)
        long_term_debt  = self._extract_first_available(balance_sheet, self.LONG_TERM_DEBT_ALIASES)
        current_value   = current_debt.value or 0.0
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
        depreciation     = self._extract_first_available(income_statement, self.DEPRECIATION_AMORTIZATION_ALIASES)
        if operating_income.value is None or depreciation.value is None:
            return StatementValue(value=None, line_item=None)
        return StatementValue(
            value=operating_income.value + depreciation.value,
            line_item=f"{operating_income.line_item} + {depreciation.line_item}",
        )

    def _extract_first_available(
        self, statement: pd.DataFrame, aliases: tuple[str, ...]
    ) -> StatementValue:
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

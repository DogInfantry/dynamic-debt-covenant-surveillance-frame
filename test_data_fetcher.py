"""Unit tests for yfinance-backed financial metric normalization."""

from __future__ import annotations

import unittest
from unittest.mock import patch

import pandas as pd

from data_fetcher import FinancialDataPipeline


class FakeTicker:
    """Minimal yfinance Ticker test double."""

    def __init__(self, ticker: str) -> None:
        self.ticker = ticker
        self.quarterly_balance_sheet = pd.DataFrame(
            {
                "2026-03-31": {
                    "Current Debt": 125.0,
                    "Long Term Debt": 875.0,
                    "Cash And Cash Equivalents": 90.0,
                }
            }
        )
        self.quarterly_income_stmt = pd.DataFrame(
            {
                "2026-03-31": {
                    "Operating Income": 210.0,
                    "Depreciation And Amortization": 40.0,
                    "Interest Expense": 35.0,
                }
            }
        )
        self.quarterly_cash_flow = pd.DataFrame(
            {
                "2026-03-31": {
                    "Capital Expenditure": -60.0,   # yfinance convention: negative
                }
            }
        )
        self.fast_info = {"currency": "USD"}


class ExplicitEbitdaTicker(FakeTicker):
    """Ticker test double with explicit EBITDA line item."""

    def __init__(self, ticker: str) -> None:
        super().__init__(ticker)
        self.quarterly_income_stmt = pd.DataFrame({"2026-03-31": {"EBITDA": 333.0}})


class FinancialDataPipelineTests(unittest.TestCase):
    """Validate standardized yfinance statement payloads."""

    @patch("data_fetcher.yf.Ticker", FakeTicker)
    def test_fetch_live_metrics_combines_debt_and_calculates_ebitda(self) -> None:
        payload = FinancialDataPipeline().fetch_live_metrics("msft")

        self.assertEqual(payload["ticker"], "MSFT")
        self.assertEqual(payload["currency"], "USD")
        self.assertEqual(payload["total_debt"], 1000.0)
        self.assertEqual(payload["cash"], 90.0)
        self.assertEqual(payload["ebitda"], 250.0)
        self.assertEqual(payload["net_debt"], 910.0)
        self.assertEqual(payload["errors"], [])

    @patch("data_fetcher.yf.Ticker", ExplicitEbitdaTicker)
    def test_fetch_live_metrics_prefers_explicit_ebitda(self) -> None:
        payload = FinancialDataPipeline().fetch_live_metrics("aapl")

        self.assertEqual(payload["ebitda"], 333.0)
        self.assertEqual(payload["lineage"]["ebitda"], "EBITDA")

    @patch("data_fetcher.yf.Ticker", FakeTicker)
    def test_fetch_live_metrics_normalizes_statement_units(self) -> None:
        payload = FinancialDataPipeline(statement_units="millions").fetch_live_metrics("msft")

        self.assertEqual(payload["units"], "millions")
        self.assertEqual(payload["scale_factor"], 1_000_000.0)
        self.assertEqual(payload["total_debt"], 0.001)
        self.assertEqual(payload["cash"], 0.00009)
        self.assertAlmostEqual(payload["net_debt"], 0.00091)

    @patch("data_fetcher.yf.Ticker", side_effect=RuntimeError("network unavailable"))
    def test_fetch_live_metrics_handles_api_disconnect(self, _mock_ticker: object) -> None:
        payload = FinancialDataPipeline().fetch_live_metrics("MSFT")

        self.assertIsNone(payload["total_debt"])
        self.assertTrue(payload["errors"])

    @patch("data_fetcher.yf.Ticker", FakeTicker)
    def test_fetch_live_metrics_extracts_interest_expense_and_capex(self) -> None:
        payload = FinancialDataPipeline().fetch_live_metrics("MSFT")

        self.assertEqual(payload.get("interest_expense"), 35.0)
        self.assertEqual(payload.get("capex"), 60.0)          # abs of -60.0

    @patch("data_fetcher.yf.Ticker", FakeTicker)
    def test_refresh_case_from_live_returns_patch_dict(self) -> None:
        result = FinancialDataPipeline().refresh_case_from_live("MSFT")

        # Even with FakeTicker the patch should contain core metrics
        patch = result.get("patch", {})
        self.assertIn("total_debt", patch)
        self.assertIn("cash", patch)
        self.assertIn("ebitda_ltm", patch)
        self.assertIn("live_data_as_of", patch)
        self.assertFalse(result.get("stale"))


if __name__ == "__main__":
    unittest.main(verbosity=2)

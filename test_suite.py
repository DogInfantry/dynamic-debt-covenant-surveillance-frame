"""Unit tests for Dynamic Debt Covenant Surveillance Engine boundaries."""

from __future__ import annotations

import ast
import math
from pathlib import Path
import unittest

from audit import audit_record_to_json, build_audit_record
from analytics import FacilityMetrics, build_portfolio_graph, simulate_macro_shock, track_buffer_proximity
from compiler import CovenantCompilerError, compile_covenant
from ingestion import covenant_templates, default_covenant_config, load_mock_article_vi_chunks, parse_article_vi_chunks


class IngestionTests(unittest.TestCase):
    """Validate structured covenant extraction from mock Article VI chunks."""

    def test_article_vi_chunks_parse_to_structured_dictionary(self) -> None:
        terms = parse_article_vi_chunks(load_mock_article_vi_chunks())

        self.assertGreaterEqual(len(terms), 1)
        self.assertEqual(terms[0]["relation"], "not to exceed")
        self.assertEqual(terms[0]["operator"], "less_than_or_equal")
        self.assertEqual(terms[0]["governors"], "Consolidated Net Leverage Ratio")
        self.assertEqual(terms[0]["objects"], "3.50")


class CompilerBoundaryTests(unittest.TestCase):
    """Validate mathematical and security boundaries for covenant compilation."""

    def setUp(self) -> None:
        self.covenant = compile_covenant(default_covenant_config())

    def test_compliance_and_exact_buffer_distance(self) -> None:
        compliant, buffer = self.covenant.evaluate(total_debt=400.0, cash=50.0, ebitda=100.0)

        self.assertTrue(compliant)
        self.assertAlmostEqual(buffer, 0.0)

    def test_ebitda_zero_returns_non_compliant_without_zero_division(self) -> None:
        compliant, buffer = self.covenant.evaluate(total_debt=100.0, cash=0.0, ebitda=0.0)

        self.assertFalse(compliant)
        self.assertEqual(buffer, -math.inf)

    def test_ebitda_negative_returns_non_compliant_without_zero_division(self) -> None:
        compliant, buffer = self.covenant.evaluate(total_debt=100.0, cash=0.0, ebitda=-25.0)

        self.assertFalse(compliant)
        self.assertEqual(buffer, -math.inf)

    def test_massive_debt_spike_produces_breach_and_large_negative_buffer(self) -> None:
        compliant, buffer = self.covenant.evaluate(total_debt=1_000_000_000.0, cash=0.0, ebitda=1.0)

        self.assertFalse(compliant)
        self.assertLess(buffer, -999_999_990.0)

    def test_interest_coverage_template_compiles_and_passes(self) -> None:
        covenant = compile_covenant(covenant_templates()["Interest Coverage"])
        compliant, buffer = covenant.evaluate(total_debt=0.0, cash=100.0, ebitda=300.0)

        self.assertTrue(compliant)
        self.assertAlmostEqual(buffer, 1.0)

    def test_minimum_liquidity_template_compiles_and_breaches(self) -> None:
        covenant = compile_covenant(covenant_templates()["Minimum Liquidity"])
        compliant, buffer = covenant.evaluate(total_debt=0.0, cash=25.0, ebitda=0.0)

        self.assertFalse(compliant)
        self.assertAlmostEqual(buffer, -25.0)

    def test_invalid_threshold_is_rejected(self) -> None:
        rule = default_covenant_config()
        rule["objects"] = "not-a-number"

        with self.assertRaises(CovenantCompilerError):
            compile_covenant(rule)

    def test_codebase_does_not_use_raw_eval_call(self) -> None:
        root = Path(__file__).resolve().parent
        module_names = (
            "analytics.py",
            "app.py",
            "audit.py",
            "compiler.py",
            "contracts.py",
            "data_fetcher.py",
            "ingestion.py",
        )
        for module_name in module_names:
            tree = ast.parse((root / module_name).read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                self.assertFalse(
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "eval",
                    f"Raw eval() found in {module_name}",
                )


class AnalyticsTests(unittest.TestCase):
    """Validate variance warnings and recursive cross-default propagation."""

    def setUp(self) -> None:
        self.covenant = compile_covenant(default_covenant_config())

    def test_10_percent_buffer_warning_system(self) -> None:
        signal = track_buffer_proximity(
            facility_id="Term Loan A",
            covenant=self.covenant,
            metrics=FacilityMetrics(total_debt=340.0, cash=0.0, ebitda=100.0),
        )

        self.assertTrue(signal.compliant)
        self.assertAlmostEqual(signal.buffer_distance, 0.10)
        self.assertTrue(signal.within_10_percent)
        self.assertFalse(signal.breached)

    def test_no_warning_when_more_than_10_percent_from_threshold(self) -> None:
        signal = track_buffer_proximity(
            facility_id="Term Loan A",
            covenant=self.covenant,
            metrics=FacilityMetrics(total_debt=250.0, cash=0.0, ebitda=100.0),
        )

        self.assertTrue(signal.compliant)
        self.assertFalse(signal.within_10_percent)

    def test_breach_is_not_labeled_as_proximity_warning(self) -> None:
        signal = track_buffer_proximity(
            facility_id="Term Loan A",
            covenant=self.covenant,
            metrics=FacilityMetrics(total_debt=500.0, cash=0.0, ebitda=100.0),
        )

        self.assertFalse(signal.compliant)
        self.assertTrue(signal.breached)
        self.assertFalse(signal.within_10_percent)

    def test_macro_shock_recursively_triggers_related_cross_defaults(self) -> None:
        graph = build_portfolio_graph()
        results = simulate_macro_shock(graph, default_node="MinorSub_1")

        self.assertEqual(results["MinorSub_1"]["trigger"], "primary_breach")
        self.assertEqual(results["OpCo_A"]["trigger"], "cross_default")
        self.assertEqual(results["HoldCo"]["trigger"], "cross_default")
        self.assertEqual(results["OpCo_B"]["trigger"], "cross_default")
        self.assertEqual(results["MinorSub_2"]["trigger"], "cross_default")
        self.assertTrue(graph.nodes["HoldCo"]["technical_default"])

    def test_audit_record_serializes_compliance_decision(self) -> None:
        record = build_audit_record(
            ticker="MSFT",
            covenant=self.covenant,
            total_debt=340.0,
            cash=0.0,
            ebitda=100.0,
            ratio=3.4,
            compliant=True,
            buffer_distance=0.1,
            warning_band=0.35,
            source_payload={"source": "manual", "errors": []},
        )

        encoded = audit_record_to_json(record)
        self.assertIn('"ticker": "MSFT"', encoded)
        self.assertIn('"compliant": true', encoded)


if __name__ == "__main__":
    unittest.main(verbosity=2)

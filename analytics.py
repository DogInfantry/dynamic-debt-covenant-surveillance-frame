"""Portfolio graph and variance analytics for debt covenant surveillance.

v2 upgrade: wires real_cases.py case registry into the graph layer,
adds severity scoring, and exposes the macro shock matrix via the
CorporateDebtNetwork facade so app.py can use it without touching
the underlying networkx calls directly.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
import math
from typing import Any

import networkx as nx

from compiler import CompiledCovenant
from analytics_v2 import (
    evaluate_package,
    portfolio_severity_score,
    macro_shock_matrix,
    detect_trend_erosion,
    build_envision_graph,
    simulate_cascade,
)

logger = logging.getLogger(__name__)

BUFFER_WARNING_FRACTION = 0.10


@dataclass(frozen=True, slots=True)
class FacilityMetrics:
    """Financial inputs for covenant surveillance."""

    total_debt: float
    cash: float
    ebitda: float


@dataclass(frozen=True, slots=True)
class VarianceSignal:
    """Current compliance, buffer, and warning state for a facility."""

    facility_id: str
    compliant: bool
    buffer_distance: float
    threshold: float
    within_10_percent: bool
    breached: bool


class CorporateDebtNetwork:
    """Portfolio debt hierarchy facade used by UI and orchestration layers.

    In v2, the graph is pre-populated from the Envision Healthcare real case
    by default but can be swapped for any EntityNode graph at construction time.
    """

    def __init__(self, use_real_case: bool = True) -> None:
        if use_real_case:
            self.graph = build_envision_graph()
        else:
            self.graph = _build_generic_graph()

    def simulate_macro_shock(
        self,
        default_node: str,
        shock_label: str = "macro_shock",
    ) -> dict[str, dict[str, Any]]:
        """Trigger BFS cross-default propagation from a breached node.

        In v2 this delegates to analytics_v2.simulate_cascade which
        respects per-tranche cross_default_clause flags rather than
        propagating to every graph neighbour blindly.
        """
        try:
            result = simulate_cascade(self.graph, breach_entity_id=default_node)
            results: dict[str, dict[str, Any]] = {}
            for node in result.propagation_path:
                trigger = "primary_breach" if node == default_node else "cross_default"
                try:
                    path = nx.shortest_path(
                        self.graph.to_undirected(),
                        source=default_node,
                        target=node,
                    )
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    path = [node]
                node_data = self.graph.nodes.get(node, {})
                results[node] = {
                    "technical_default": True,
                    "trigger": trigger,
                    "shock_label": shock_label,
                    "facility": node_data.get("label", node),
                    "face_value_usd_m": node_data.get("face_value", 0),
                    "propagation_path": path,
                }
            nx.set_node_attributes(
                self.graph,
                {node: True for node in result.propagation_path},
                name="technical_default",
            )
            logger.warning(
                "Cascade from %s impacted %s facilities | $%.0fM at risk",
                default_node,
                result.entities_affected,
                result.total_debt_at_risk_usd_m,
            )
            return results
        except Exception as exc:
            logger.exception("Cascade simulation failed: %s", exc)
            return {}

    def shock_matrix(
        self,
        total_debt: float,
        cash: float,
        ebitda: float,
        nlr_threshold: float,
    ) -> dict:
        """Return EBITDA-compression × debt-increase NLR sensitivity matrix."""
        return macro_shock_matrix(total_debt, cash, ebitda, nlr_threshold)

    def trend_signal(
        self,
        historical_nlr: list[float],
        nlr_threshold: float,
    ) -> dict:
        """Return directional erosion signal for a historical NLR series."""
        return detect_trend_erosion(historical_nlr, nlr_threshold, operator="lte")

    def evaluate_case_covenants(self, covenant_specs: list[dict]) -> dict:
        """Run evaluate_package on a real case's covenant list and return summary."""
        results = evaluate_package(covenant_specs)
        return {
            "results": results,
            "severity_score": portfolio_severity_score(results),
            "breach_count": sum(1 for r in results if r.status == "BREACH"),
            "watchlist_count": sum(1 for r in results if r.status == "WATCHLIST"),
        }

    def clear_defaults(self) -> None:
        """Reset dynamic default flags on all debt hierarchy nodes."""
        nx.set_node_attributes(
            self.graph,
            {node: False for node in self.graph.nodes},
            "technical_default",
        )

    @property
    def node_ids(self) -> list[str]:
        return list(self.graph.nodes)


def _build_generic_graph() -> nx.DiGraph:
    """Fallback generic graph (v1 structure) used when real case is disabled."""
    graph = nx.DiGraph()
    graph.add_node("HoldCo",     entity_type="parent",           facility="Revolver",        label="HoldCo — Revolver",     face_value=400,  cross_default=True,  status="breach")
    graph.add_node("OpCo_A",     entity_type="subsidiary",       facility="Term Loan A",     label="OpCo A — TLA",          face_value=1270, cross_default=True,  status="warning")
    graph.add_node("OpCo_B",     entity_type="subsidiary",       facility="Term Loan B",     label="OpCo B — TLB",          face_value=750,  cross_default=True,  status="compliant")
    graph.add_node("MinorSub_1", entity_type="minor_subsidiary", facility="ABL Facility",    label="Sub 1 — ABL",           face_value=200,  cross_default=True,  status="breach")
    graph.add_node("MinorSub_2", entity_type="minor_subsidiary", facility="Equipment Notes", label="Sub 2 — Equip. Notes",  face_value=90,   cross_default=True,  status="compliant")
    graph.add_edges_from(
        [("HoldCo", "OpCo_A"), ("HoldCo", "OpCo_B"),
         ("OpCo_A", "MinorSub_1"), ("OpCo_B", "MinorSub_2")],
        relationship="guarantee_or_cross_default",
    )
    return graph


def build_portfolio_graph() -> nx.DiGraph:
    """Public alias kept for backward compatibility with existing tests."""
    return _build_generic_graph()


def track_buffer_proximity(
    facility_id: str,
    covenant: CompiledCovenant,
    metrics: FacilityMetrics,
) -> VarianceSignal:
    """Flag covenants trending within 10% of the breach threshold."""

    compliant, buffer_distance = covenant.evaluate(
        metrics.total_debt,
        metrics.cash,
        metrics.ebitda,
    )
    breached = not compliant

    if metrics.ebitda <= 0 or not math.isfinite(buffer_distance):
        within_10_percent = False
    else:
        warning_band = abs(covenant.threshold) * BUFFER_WARNING_FRACTION
        within_10_percent = compliant and 0 <= buffer_distance <= warning_band

    signal = VarianceSignal(
        facility_id=facility_id,
        compliant=compliant,
        buffer_distance=buffer_distance,
        threshold=covenant.threshold,
        within_10_percent=within_10_percent,
        breached=breached,
    )
    logger.info("Generated variance signal: %s", signal)
    return signal


def simulate_macro_shock(
    graph: nx.DiGraph,
    default_node: str,
    shock_label: str = "macro_shock",
) -> dict[str, dict[str, Any]]:
    """Public function alias kept for backward compatibility with existing tests."""
    net = CorporateDebtNetwork(use_real_case=False)
    net.graph = graph
    return net.simulate_macro_shock(default_node=default_node, shock_label=shock_label)

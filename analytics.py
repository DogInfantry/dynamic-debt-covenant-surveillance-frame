"""Portfolio graph and variance analytics for debt covenant surveillance."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import math
from typing import Any

import networkx as nx

from compiler import CompiledCovenant


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
    """Portfolio debt hierarchy facade used by UI and orchestration layers."""

    def __init__(self) -> None:
        self.graph = build_portfolio_graph()

    def simulate_macro_shock(
        self,
        default_node: str,
        shock_label: str = "macro_shock",
    ) -> dict[str, dict[str, Any]]:
        """Trigger recursive cross-default propagation from a breached node."""

        return simulate_macro_shock(
            graph=self.graph,
            default_node=default_node,
            shock_label=shock_label,
        )

    def clear_defaults(self) -> None:
        """Reset dynamic default flags on all debt hierarchy nodes."""

        nx.set_node_attributes(self.graph, {node: False for node in self.graph.nodes}, "technical_default")


def build_portfolio_graph() -> nx.DiGraph:
    """Build a directed parent/subsidiary debt hierarchy graph."""

    graph = nx.DiGraph()
    graph.add_node("HoldCo", entity_type="parent", facility="Revolver")
    graph.add_node("OpCo_A", entity_type="subsidiary", facility="Term Loan A")
    graph.add_node("OpCo_B", entity_type="subsidiary", facility="Term Loan B")
    graph.add_node("MinorSub_1", entity_type="minor_subsidiary", facility="ABL Facility")
    graph.add_node("MinorSub_2", entity_type="minor_subsidiary", facility="Equipment Notes")

    graph.add_edges_from(
        [
            ("HoldCo", "OpCo_A"),
            ("HoldCo", "OpCo_B"),
            ("OpCo_A", "MinorSub_1"),
            ("OpCo_B", "MinorSub_2"),
        ],
        relationship="guarantee_or_cross_default",
    )
    logger.info("Built portfolio graph with %s nodes", graph.number_of_nodes())
    return graph


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


def _related_default_nodes(graph: nx.DiGraph, default_node: str) -> set[str]:
    if default_node not in graph:
        raise KeyError(f"Unknown facility node: {default_node!r}")

    ancestors = nx.ancestors(graph, default_node)
    descendants: set[str] = set()
    for ancestor in ancestors | {default_node}:
        descendants.update(nx.descendants(graph, ancestor))
    return ancestors | descendants | {default_node}


def simulate_macro_shock(
    graph: nx.DiGraph,
    default_node: str,
    shock_label: str = "macro_shock",
) -> dict[str, dict[str, Any]]:
    """Recursively propagate technical cross-defaults through related facilities."""

    impacted_nodes = _related_default_nodes(graph, default_node)
    results: dict[str, dict[str, Any]] = {}

    for node in impacted_nodes:
        path = []
        if node != default_node:
            try:
                path = nx.shortest_path(graph.to_undirected(), source=default_node, target=node)
            except nx.NetworkXNoPath:
                path = []
        results[node] = {
            "technical_default": True,
            "trigger": "primary_breach" if node == default_node else "cross_default",
            "shock_label": shock_label,
            "facility": graph.nodes[node].get("facility"),
            "propagation_path": path,
        }

    nx.set_node_attributes(
        graph,
        {node: True for node in impacted_nodes},
        name="technical_default",
    )
    logger.warning("Macro shock at %s impacted %s facilities", default_node, len(results))
    return results

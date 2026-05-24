"""
analytics_v2.py — DDCSE v2 Enhanced Analytics
================================================
Upgrades over v1:
  - Multi-covenant compliance runner (not just NLR)
  - Buffer severity scoring (0–100) for portfolio-level heat maps
  - Cross-default cascade using NetworkX with weighted propagation paths
  - Macro shock sensitivity matrix (EBITDA compression × debt increase)
  - Variance-from-threshold trend detection
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Literal

try:
    import networkx as nx
    NX_AVAILABLE = True
except ImportError:
    NX_AVAILABLE = False

# ──────────────────────────────────────────────────────────────────────────────
#  DATA STRUCTURES
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class CovenantResult:
    name: str
    cov_type: str
    threshold: float
    actual: float
    operator: Literal["lte", "gte"]
    unit: str | None
    compliant: bool
    buffer_distance: float        # positive = headroom; negative = breach depth
    buffer_pct: float             # as % of threshold (buffer / threshold)
    warning_band: float           # 10% of threshold by default
    status: Literal["COMPLIANT", "WATCHLIST", "WARNING", "BREACH"]
    severity_score: float         # 0 = no risk, 100 = deep breach

    @property
    def is_warning(self) -> bool:
        return self.status in ("WATCHLIST", "WARNING")


@dataclass
class EntityNode:
    """Represents a debt entity in the NetworkX cross-default graph."""
    entity_id: str
    label: str
    face_value_usd_m: float
    seniority: str
    rate: str
    status: Literal["breach", "warning", "compliant"]
    has_cross_default_clause: bool
    covenant_results: list[CovenantResult] = field(default_factory=list)


@dataclass
class CascadeResult:
    origin: str                          # entity_id that breached first
    propagation_path: list[str]          # ordered chain of affected entities
    total_debt_at_risk_usd_m: float
    entities_affected: int
    direct_breach_entities: list[str]
    technical_cross_defaults: list[str]
    cascade_depth: int                   # longest path from origin


# ──────────────────────────────────────────────────────────────────────────────
#  COVENANT EVALUATOR
# ──────────────────────────────────────────────────────────────────────────────

_WARNING_BAND_PCT = 0.10   # within 10% of threshold = WATCHLIST/WARNING


def evaluate_covenant(
    name: str,
    cov_type: str,
    threshold: float,
    actual: float,
    operator: Literal["lte", "gte"],
    unit: str | None = None,
    warning_band_pct: float = _WARNING_BAND_PCT,
) -> CovenantResult:
    """
    AST-safe covenant evaluation.  No eval() — pure arithmetic.

    Severity score:
      COMPLIANT  > 10% buffer  →  0–30
      WATCHLIST  0–10% buffer  →  30–60
      BREACH     0–25% depth   →  60–85
      BREACH     > 25% depth   →  85–100
    """
    if threshold == 0:
        raise ValueError(f"Covenant '{name}': threshold cannot be zero")

    warning_band = abs(threshold) * warning_band_pct

    if operator == "lte":
        compliant = actual <= threshold
        buffer_distance = threshold - actual          # positive = headroom
    else:  # gte
        compliant = actual >= threshold
        buffer_distance = actual - threshold          # positive = headroom

    buffer_pct = buffer_distance / abs(threshold)

    # Status classification
    if compliant:
        if buffer_pct <= warning_band_pct:
            status: Literal["COMPLIANT","WATCHLIST","WARNING","BREACH"] = "WATCHLIST"
        else:
            status = "COMPLIANT"
    else:
        status = "BREACH"

    # Severity score
    if status == "COMPLIANT":
        # Buffer pct capped at 50% for scoring purposes
        severity = max(0, 30 - (min(buffer_pct, 0.50) / 0.50) * 30)
    elif status == "WATCHLIST":
        # 0–10% buffer band → 30–60
        severity = 30 + (1 - buffer_pct / warning_band_pct) * 30
    else:
        # Breach: depth as pct of threshold
        breach_depth = abs(buffer_pct)
        severity = min(100, 60 + breach_depth / 0.25 * 25)

    return CovenantResult(
        name=name,
        cov_type=cov_type,
        threshold=threshold,
        actual=actual,
        operator=operator,
        unit=unit,
        compliant=compliant,
        buffer_distance=round(buffer_distance, 4),
        buffer_pct=round(buffer_pct, 4),
        warning_band=round(warning_band, 4),
        status=status,
        severity_score=round(severity, 1),
    )


def evaluate_package(covenant_specs: list[dict]) -> list[CovenantResult]:
    """
    Evaluate a full covenant package (list of CovenantSpec dicts from real_cases.py).
    Returns one CovenantResult per covenant.
    """
    results = []
    for spec in covenant_specs:
        r = evaluate_covenant(
            name=spec["name"],
            cov_type=spec["type"],
            threshold=spec["threshold"],
            actual=spec["actual"],
            operator=spec["operator"],
            unit=spec.get("unit"),
        )
        results.append(r)
    return results


def portfolio_severity_score(results: list[CovenantResult]) -> float:
    """
    Aggregate severity score for a covenant package: max severity × breach_fraction.
    Range 0–100.
    """
    if not results:
        return 0.0
    max_sev = max(r.severity_score for r in results)
    breach_frac = sum(1 for r in results if r.status == "BREACH") / len(results)
    return round(min(100, max_sev * (0.5 + 0.5 * breach_frac)), 1)


# ──────────────────────────────────────────────────────────────────────────────
#  NETWORKX CROSS-DEFAULT CASCADE
# ──────────────────────────────────────────────────────────────────────────────

def build_debt_graph(entities: list[EntityNode], edges: list[tuple[str, str]]) -> "nx.DiGraph":
    """
    Build a directed NetworkX graph where:
      - nodes = debt entities (HoldCo, OpCo, subs)
      - edges = structural / guarantee / cross-default linkages
      - direction = parent → child (guarantee flows downward, cross-defaults propagate upward)

    Parameters
    ----------
    entities : list of EntityNode describing each tranche/entity
    edges    : list of (parent_id, child_id) structural links
    """
    if not NX_AVAILABLE:
        raise ImportError("networkx is required for cascade analysis: pip install networkx")

    G = nx.DiGraph()
    for e in entities:
        G.add_node(
            e.entity_id,
            label=e.label,
            face_value=e.face_value_usd_m,
            seniority=e.seniority,
            status=e.status,
            cross_default=e.has_cross_default_clause,
        )
    for parent, child in edges:
        G.add_edge(parent, child, relation="structural_guarantee")
    return G


def simulate_cascade(
    G: "nx.DiGraph",
    breach_entity_id: str,
    max_depth: int = 5,
) -> CascadeResult:
    """
    BFS propagation of a covenant breach through the cross-default graph.

    A technical cross-default is triggered in an entity if:
      (a) a structural parent or child has cross_default_clause = True, AND
      (b) that parent/child is in breach or becomes in-scope via cascade.

    Returns a CascadeResult with the full propagation map.
    """
    if not NX_AVAILABLE:
        raise ImportError("networkx is required")

    if breach_entity_id not in G:
        raise ValueError(f"Entity '{breach_entity_id}' not in graph")

    visited: set[str] = {breach_entity_id}
    queue: list[tuple[str, int]] = [(breach_entity_id, 0)]
    propagation_path: list[str] = [breach_entity_id]
    technical_cross_defaults: list[str] = []
    total_at_risk = G.nodes[breach_entity_id].get("face_value", 0)

    while queue:
        current, depth = queue.pop(0)
        if depth >= max_depth:
            continue

        # Propagate to all neighbours (both directions = cross-default can go either way)
        neighbours = list(G.predecessors(current)) + list(G.successors(current))
        for nbr in neighbours:
            if nbr in visited:
                continue
            nbr_data = G.nodes[nbr]
            if nbr_data.get("cross_default", False):
                visited.add(nbr)
                queue.append((nbr, depth + 1))
                propagation_path.append(nbr)
                technical_cross_defaults.append(nbr)
                total_at_risk += nbr_data.get("face_value", 0)

    return CascadeResult(
        origin=breach_entity_id,
        propagation_path=propagation_path,
        total_debt_at_risk_usd_m=round(total_at_risk, 1),
        entities_affected=len(propagation_path),
        direct_breach_entities=[breach_entity_id],
        technical_cross_defaults=technical_cross_defaults,
        cascade_depth=max(
            (nx.shortest_path_length(G.to_undirected(), breach_entity_id, t)
             for t in technical_cross_defaults),
            default=0,
        ),
    )


def build_envision_graph() -> "nx.DiGraph":
    """
    Pre-built Envision Healthcare debt graph based on Ch.11 First-Day Declaration.
    """
    entities = [
        EntityNode("holdco_rcf",  "HoldCo — $400M RCF",     400,  "Super Senior / 1L", "SOFR+600",  "breach",    True),
        EntityNode("opco_a_tlb",  "OpCo A — $1,270M TLB",  1270,  "1st Lien Term",     "SOFR+575",  "warning",   True),
        EntityNode("opco_b_notes","OpCo B — $750M Sr Notes", 750,  "2nd Lien",          "8.75% Fx",  "compliant", False),
        EntityNode("sub1_abl",    "Sub 1 — $200M ABL",       200,  "Super Senior ABL",  "SOFR+200",  "breach",    True),
        EntityNode("sub2_mezz",   "Sub 2 — $180M Mezz",      180,  "Mezzanine",         "12% PIK",   "warning",   True),
        EntityNode("sub3_equip",  "Sub 3 — $90M Equip.",      90,  "Equipment Notes",   "7.5% Fx",   "compliant", False),
    ]
    edges = [
        ("holdco_rcf",   "opco_a_tlb"),
        ("holdco_rcf",   "opco_b_notes"),
        ("opco_a_tlb",   "sub1_abl"),
        ("opco_a_tlb",   "sub2_mezz"),
        ("opco_b_notes", "sub3_equip"),
    ]
    return build_debt_graph(entities, edges)


# ──────────────────────────────────────────────────────────────────────────────
#  MACRO SHOCK SENSITIVITY MATRIX
# ──────────────────────────────────────────────────────────────────────────────

def macro_shock_matrix(
    total_debt: float,
    cash: float,
    ebitda: float,
    nlr_threshold: float,
    ebitda_shocks: list[float] | None = None,
    debt_shocks: list[float] | None = None,
) -> dict:
    """
    Generates an (EBITDA compression × Debt increase) sensitivity matrix for NLR.

    Returns a dict with keys "rows", "cols", "matrix" for easy rendering.
    Each cell: {"nlr": float, "breached": bool, "buffer": float}
    """
    ebitda_shocks = ebitda_shocks or [0.0, 0.10, 0.20, 0.30, 0.40, 0.50]
    debt_shocks   = debt_shocks   or [0.0, 0.05, 0.10, 0.20, 0.30]

    matrix = []
    for e_shock in ebitda_shocks:
        row = []
        stressed_ebitda = ebitda * (1 - e_shock)
        for d_shock in debt_shocks:
            stressed_debt = total_debt * (1 + d_shock)
            if stressed_ebitda <= 0:
                nlr = math.inf
                breached = True
                buffer = -math.inf
            else:
                nlr = (stressed_debt - cash) / stressed_ebitda
                breached = nlr > nlr_threshold
                buffer = nlr_threshold - nlr
            row.append({
                "ebitda_shock": e_shock,
                "debt_shock": d_shock,
                "stressed_ebitda": round(stressed_ebitda, 1),
                "stressed_debt": round(stressed_debt, 1),
                "nlr": round(nlr, 2) if not math.isinf(nlr) else None,
                "breached": breached,
                "buffer": round(buffer, 2) if not math.isinf(buffer) else None,
            })
        matrix.append(row)

    return {
        "rows": [f"EBITDA –{int(s*100)}%" for s in ebitda_shocks],
        "cols": [f"Debt +{int(s*100)}%" for s in debt_shocks],
        "matrix": matrix,
        "base_nlr": round((total_debt - cash) / ebitda, 2),
        "threshold": nlr_threshold,
    }


# ──────────────────────────────────────────────────────────────────────────────
#  TREND EROSION DETECTOR
# ──────────────────────────────────────────────────────────────────────────────

def detect_trend_erosion(
    historical_ratios: list[float],
    threshold: float,
    operator: Literal["lte", "gte"],
    lookback_quarters: int = 4,
) -> dict:
    """
    Detects whether a covenant ratio is directionally eroding toward breach.

    Returns:
      - direction: "deteriorating" | "improving" | "stable"
      - quarters_to_breach_estimate: int | None
      - velocity: change per quarter (avg of last lookback_quarters)
      - current_buffer: float
    """
    if len(historical_ratios) < 2:
        return {"direction": "insufficient_data"}

    recent = historical_ratios[-lookback_quarters:]
    deltas = [recent[i+1] - recent[i] for i in range(len(recent)-1)]
    avg_velocity = sum(deltas) / len(deltas) if deltas else 0.0

    current = historical_ratios[-1]
    if operator == "lte":
        buffer = threshold - current
        deteriorating = avg_velocity > 0   # ratio climbing toward threshold
    else:
        buffer = current - threshold
        deteriorating = avg_velocity < 0   # ratio falling toward threshold

    if abs(avg_velocity) < 0.05:
        direction = "stable"
    elif deteriorating:
        direction = "deteriorating"
    else:
        direction = "improving"

    # Quarters to breach estimate
    qtb = None
    if direction == "deteriorating" and avg_velocity != 0 and buffer > 0:
        if operator == "lte":
            qtb = math.ceil(buffer / avg_velocity)
        else:
            qtb = math.ceil(buffer / abs(avg_velocity))

    return {
        "direction": direction,
        "velocity_per_quarter": round(avg_velocity, 3),
        "current_buffer": round(buffer, 3),
        "quarters_to_breach_estimate": qtb,
        "lookback_quarters": lookback_quarters,
        "current_ratio": round(current, 3),
        "threshold": threshold,
    }

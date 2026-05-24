"""Streamlit interface for the Dynamic Debt Covenant Surveillance Engine — v2.

v2 upgrade:
  - Real case mode: Envision Healthcare, Revlon Inc, Cineworld Group
    (all sourced from public SEC filings / Ch.11 petitions)
  - Full covenant package evaluation (not just NLR) via analytics_v2
  - Severity score (0-100) displayed per run
  - Macro shock sensitivity matrix (EBITDA compression × debt increase)
  - Trend erosion signal with quarters-to-breach estimate
  - NetworkX cascade now uses real tranche-level cross_default_clause flags
  - Audit record extended with severity_score and case_name
"""

from __future__ import annotations

import logging
import math

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import streamlit as st

from analytics import CorporateDebtNetwork, track_buffer_proximity, FacilityMetrics
from audit import audit_record_to_json, build_audit_record
from compiler import CompiledCovenant, CovenantCompiler
from data_fetcher import FinancialDataPipeline
from ingestion import covenant_templates
from real_cases import get_case, list_cases, CASE_REGISTRY
from analytics_v2 import evaluate_package, portfolio_severity_score, CovenantResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_STATUS_COLOR = {
    "BREACH": "#b42318",
    "WATCHLIST": "#b45309",
    "WARNING": "#b45309",
    "COMPLIANT": "#1f8f5f",
}
_NODE_COLOR_MAP = {
    "breach": "#d1495b",
    "warning": "#f4a261",
    "compliant": "#2a9d8f",
}


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _format_ratio(value: float) -> str:
    if not math.isfinite(value):
        return "N/A"
    return f"{value:,.2f}x"


def _net_leverage_ratio(total_debt: float, cash: float, ebitda: float) -> float:
    if ebitda <= 0:
        return math.inf
    return (total_debt - cash) / ebitda


def _display_value(
    covenant: CompiledCovenant,
    total_debt: float,
    cash: float,
    ebitda: float,
) -> float:
    if covenant.governor == "Consolidated Net Leverage Ratio":
        return _net_leverage_ratio(total_debt, cash, ebitda)
    if covenant.governor == "Minimum Liquidity":
        return cash
    _, buffer = covenant.evaluate(total_debt, cash, ebitda)
    if covenant.operator in {"greater_than", "greater_than_or_equal"}:
        return covenant.threshold + buffer
    return covenant.threshold - buffer


def _status_badge(compliant: bool) -> None:
    color = "#1f8f5f" if compliant else "#b42318"
    label = "Compliant" if compliant else "In Breach"
    st.markdown(
        f"""
        <div style="border:1px solid {color};color:{color};padding:0.8rem 1rem;
        border-radius:8px;font-size:1.4rem;font-weight:700;text-align:center;">
            {label}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _severity_badge(score: float) -> None:
    if score >= 70:
        color, label = "#b42318", f"Severity {score:.0f}/100 — HIGH RISK"
    elif score >= 40:
        color, label = "#b45309", f"Severity {score:.0f}/100 — WATCHLIST"
    else:
        color, label = "#1f8f5f", f"Severity {score:.0f}/100 — LOW RISK"
    st.markdown(
        f"""<div style="border:1px solid {color};color:{color};padding:0.5rem 1rem;
        border-radius:6px;font-size:0.9rem;font-weight:600;text-align:center;margin-top:6px;">
            {label}</div>""",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Covenant package table (v2: real case full package)
# ─────────────────────────────────────────────────────────────────────────────

def _render_covenant_package(results: list[CovenantResult]) -> None:
    st.subheader("Covenant Package — Full Article VI Tests")
    rows = []
    for r in results:
        actual_fmt = (
            f"${r.actual:.1f}M" if r.unit == "$M"
            else f"{r.actual:.2f}x"
        )
        threshold_fmt = (
            f"${r.threshold:.1f}M" if r.unit == "$M"
            else f"{r.threshold:.2f}x"
        )
        buffer_fmt = (
            f"{r.buffer_pct * 100:.1f}%"
            if r.compliant
            else f"–{abs(r.buffer_pct) * 100:.1f}%"
        )
        rows.append({
            "Covenant": r.name,
            "Type": r.cov_type,
            "Threshold": threshold_fmt,
            "Actual": actual_fmt,
            "Buffer": buffer_fmt,
            "Status": r.status,
            "Severity": f"{r.severity_score:.0f}",
        })

    df = pd.DataFrame(rows)

    def _color_status(val: str) -> str:
        colors = {
            "BREACH": "color: #b42318; font-weight: 700",
            "WATCHLIST": "color: #b45309; font-weight: 600",
            "WARNING": "color: #b45309; font-weight: 600",
            "COMPLIANT": "color: #1f8f5f",
        }
        return colors.get(val, "")

    styled = df.style.applymap(_color_status, subset=["Status"])
    st.dataframe(styled, hide_index=True, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Shock matrix renderer
# ─────────────────────────────────────────────────────────────────────────────

def _render_shock_matrix(matrix_data: dict) -> None:
    st.subheader("Macro Shock Sensitivity — NLR Matrix")
    st.caption(
        f"Base NLR: **{matrix_data['base_nlr']:.2f}x** | "
        f"Covenant threshold: **{matrix_data['threshold']:.2f}x** | "
        f"🔴 = breach, 🟢 = compliant"
    )
    rows_data = []
    for row_cells in matrix_data["matrix"]:
        row = {}
        for cell in row_cells:
            col_label = f"Debt +{int(cell['debt_shock'] * 100)}%"
            if cell["nlr"] is None:
                row[col_label] = "N/M"
            else:
                flag = "🔴" if cell["breached"] else "🟢"
                row[col_label] = f"{flag} {cell['nlr']:.1f}x"
        rows_data.append(row)
    df = pd.DataFrame(rows_data, index=matrix_data["rows"])
    st.dataframe(df, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Debt tree graph
# ─────────────────────────────────────────────────────────────────────────────

def _render_debt_tree(network: CorporateDebtNetwork, shock_triggered: bool) -> None:
    graph = network.graph
    nodes = list(graph.nodes)

    # Build positions — use stored positions or auto-layout
    pos_store = {
        "holdco_rcf":   (0.0, 2.0),
        "opco_a_tlb":   (-1.2, 1.0),
        "opco_b_notes": (1.2, 1.0),
        "sub1_abl":     (-1.6, 0.0),
        "sub2_mezz":    (-0.8, 0.0),
        "sub3_equip":   (1.2, 0.0),
        # Generic graph fallback
        "HoldCo":    (0.0, 2.0),
        "OpCo_A":    (-1.2, 1.0),
        "OpCo_B":    (1.2, 1.0),
        "MinorSub_1": (-1.2, 0.0),
        "MinorSub_2": (1.2, 0.0),
    }
    position = {n: pos_store[n] for n in nodes if n in pos_store}
    if len(position) < len(nodes):
        position = nx.spring_layout(graph, seed=42)

    node_colors = []
    for node in nodes:
        node_data = graph.nodes[node]
        if node_data.get("technical_default"):
            node_colors.append("#d1495b")
        else:
            raw_status = node_data.get("status", "compliant")
            node_colors.append(_NODE_COLOR_MAP.get(raw_status, "#2a9d8f"))

    labels = {
        node: (
            graph.nodes[node].get("label", node)
            .replace(" — ", "\n")
            .replace(" – ", "\n")
        )
        for node in nodes
    }

    fig, ax = plt.subplots(figsize=(9, 5))
    fig.patch.set_facecolor("#0e1117")
    ax.set_facecolor("#0e1117")

    nx.draw_networkx_edges(
        graph, position, ax=ax, arrows=True,
        edge_color="#4a5568", arrowsize=18, width=1.2,
    )
    nx.draw_networkx_nodes(
        graph, position, ax=ax,
        node_color=node_colors, node_size=2800,
        edgecolors="#ffffff", linewidths=0.8,
    )
    nx.draw_networkx_labels(
        graph, position, labels=labels, ax=ax,
        font_size=7, font_color="#ffffff", font_weight="bold",
    )

    title = "Debt Hierarchy — Cross-Default Graph"
    if shock_triggered:
        title += "  ⚠ SHOCK ACTIVE"
    ax.set_title(title, fontsize=10, color="#e2e8f0", pad=10)
    ax.axis("off")

    legend_elements = [
        plt.scatter([], [], c="#d1495b", s=120, label="Breach / Cross-default"),
        plt.scatter([], [], c="#f4a261", s=120, label="Warning"),
        plt.scatter([], [], c="#2a9d8f", s=120, label="Compliant"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", fontsize=7,
              facecolor="#1a202c", labelcolor="#e2e8f0", framealpha=0.8)

    st.pyplot(fig, clear_figure=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Session state initializer
# ─────────────────────────────────────────────────────────────────────────────

def _initialize_state() -> None:
    defaults = {
        "total_debt": 400.0,
        "cash": 50.0,
        "ebitda": 100.0,
        "source_payload": {"source": "manual", "errors": []},
        "ticker": "MSFT",
        "mode": "real_case",
        "selected_case": "EVHC",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


# ─────────────────────────────────────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(
        page_title="DDCSE — Covenant Surveillance Engine",
        page_icon="📊",
        layout="wide",
    )
    _initialize_state()

    st.title("Dynamic Debt Covenant Surveillance Engine")
    st.caption(
        "AST-safe covenant compiler · yfinance live financials · "
        "NetworkX cross-default cascade · Real distressed case data"
    )

    # ── Sidebar ──────────────────────────────────────────────────────────────
    st.sidebar.header("Mode")
    mode = st.sidebar.radio(
        "Data source",
        ["Real Case (Ch.11 Filing)", "Live Market (yfinance)", "Manual Input"],
        index=0,
        key="mode_radio",
    )

    templates = covenant_templates()
    covenant_name = st.sidebar.selectbox("Covenant Type", list(templates.keys()))
    covenant = CovenantCompiler().compile(templates[covenant_name])
    network = CorporateDebtNetwork(use_real_case=True)

    case_data = None
    case_covenant_results = None
    severity_score = 0.0
    case_name = None

    # ── Real case mode ───────────────────────────────────────────────────────
    if mode == "Real Case (Ch.11 Filing)":
        case_options = {
            f"{v['name']} ({v['filing_date']})": k
            for k, v in CASE_REGISTRY.items()
        }
        selected_label = st.sidebar.selectbox("Select filing case", list(case_options.keys()))
        case_key = case_options[selected_label]
        case_data = get_case(case_key)
        case_name = case_data["name"]

        st.session_state["total_debt"] = case_data["total_debt"]
        st.session_state["cash"] = case_data["cash"]
        st.session_state["ebitda"] = case_data["ebitda_ltm"]
        st.session_state["source_payload"] = {
            "source": case_data["filing"],
            "ticker": case_data["ticker"],
            "errors": [],
        }

        # Full package evaluation
        pkg = network.evaluate_case_covenants(case_data["covenants"])
        case_covenant_results = pkg["results"]
        severity_score = pkg["severity_score"]

        st.sidebar.markdown(
            f"**Rating:** {case_data['credit_rating']}  \n"
            f"**Outlook:** {case_data['outlook']}  \n"
            f"**Total Debt:** ${case_data['total_debt']:,.0f}M  \n"
            f"**Filing:** {case_data['filing_date']}"
        )

    # ── Live market mode ─────────────────────────────────────────────────────
    elif mode == "Live Market (yfinance)":
        st.sidebar.subheader("Live Market Fetch")
        ticker = st.sidebar.text_input("Ticker", key="ticker")
        statement_units = st.sidebar.selectbox(
            "Normalize Statements To",
            ["raw", "thousands", "millions", "billions"],
            index=0,
        )
        if st.sidebar.button("Fetch Live Metrics"):
            payload = FinancialDataPipeline(statement_units=statement_units).fetch_live_metrics(ticker)
            st.session_state["source_payload"] = payload
            if payload["total_debt"] is not None:
                st.session_state["total_debt"] = float(payload["total_debt"])
            if payload["cash"] is not None:
                st.session_state["cash"] = float(payload["cash"])
            if payload["ebitda"] is not None:
                st.session_state["ebitda"] = float(payload["ebitda"])
            if payload["errors"]:
                st.sidebar.error("; ".join(payload["errors"]))
            else:
                st.sidebar.success(f"Loaded {payload['ticker']} metrics")

        st.sidebar.subheader("Facility Inputs")
        st.sidebar.number_input("Total Debt", min_value=0.0, step=10.0, format="%.2f", key="total_debt")
        st.sidebar.number_input("Cash / Liquidity", min_value=0.0, step=5.0, format="%.2f", key="cash")
        st.sidebar.number_input("EBITDA", step=5.0, format="%.2f", key="ebitda")

    # ── Manual mode ──────────────────────────────────────────────────────────
    else:
        st.sidebar.subheader("Facility Inputs")
        st.sidebar.number_input("Total Debt", min_value=0.0, step=10.0, format="%.2f", key="total_debt")
        st.sidebar.number_input("Cash / Liquidity", min_value=0.0, step=5.0, format="%.2f", key="cash")
        st.sidebar.number_input("EBITDA", step=5.0, format="%.2f", key="ebitda")

    # ── Shock controls ───────────────────────────────────────────────────────
    st.sidebar.header("Shock Simulation")
    shock_node = st.sidebar.selectbox(
        "Primary Breach Facility",
        network.node_ids,
        index=min(3, len(network.node_ids) - 1),
    )
    shock_triggered = st.sidebar.toggle("Trigger Covenant Shock", value=False)
    reset_graph = st.sidebar.button("Reset Graph State")

    total_debt = st.session_state["total_debt"]
    cash = st.session_state["cash"]
    ebitda = st.session_state["ebitda"]

    compliant, buffer_distance = covenant.evaluate(total_debt, cash, ebitda)
    display_value = _display_value(covenant, total_debt, cash, ebitda)
    warning_band = covenant.threshold * 0.10
    shock_results = {}

    if reset_graph:
        network.clear_defaults()
        shock_triggered = False
    elif shock_triggered or not compliant:
        shock_results = network.simulate_macro_shock(default_node=shock_node)
    else:
        network.clear_defaults()

    # ── Metric cards ─────────────────────────────────────────────────────────
    if case_data:
        nlr = (case_data["total_debt"] - case_data["cash"]) / case_data["ebitda_ltm"]
        icr = case_data["ebitda_ltm"] / case_data["interest_expense_ltm"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Net Leverage Ratio", f"{nlr:.2f}x", f"Threshold {case_data['covenants'][0]['threshold']:.1f}x")
        c2.metric("Interest Coverage", f"{icr:.2f}x", f"Threshold {case_data['covenants'][1]['threshold']:.1f}x")
        c3.metric("Net Debt", f"${case_data['total_debt'] - case_data['cash']:,.0f}M")
        c4.metric("Credit Rating", case_data["credit_rating"], case_data["outlook"])
    else:
        ratio_col, status_col, buffer_col = st.columns(3)
        ratio_col.metric(covenant.governor, _format_ratio(display_value), f"Threshold {covenant.threshold:.2f}")
        with status_col:
            st.caption("Facility Status")
            _status_badge(compliant)
        buffer_col.metric("Buffer Cushion", _format_ratio(buffer_distance))

    # ── Severity score ───────────────────────────────────────────────────────
    if case_covenant_results:
        _severity_badge(severity_score)

    # ── Warnings ─────────────────────────────────────────────────────────────
    if compliant and math.isfinite(buffer_distance) and buffer_distance <= warning_band:
        st.warning(
            f"Buffer cushion is within 10% of the {covenant.threshold:.2f} threshold "
            f"({buffer_distance:.2f} ≤ {warning_band:.2f})."
        )
    elif not compliant:
        st.error("Facility is in breach. Cross-default propagation reflected in debt tree below.")

    # ── Real case tabs ────────────────────────────────────────────────────────
    if case_data:
        tab1, tab2, tab3, tab4 = st.tabs([
            "Covenant Package", "Debt Stack", "Shock Matrix", "Case Notes",
        ])

        with tab1:
            if case_covenant_results:
                _render_covenant_package(case_covenant_results)

        with tab2:
            st.subheader("Debt Stack — Tranche Detail")
            stack_rows = []
            for t in case_data["debt_stack"]:
                stack_rows.append({
                    "Tranche": t["tranche"],
                    "Face Value ($M)": f"${t['face_value_usd_m']:,.0f}M",
                    "Seniority": t["seniority"],
                    "Rate": t["rate"],
                    "Maturity": t["maturity"],
                    "Lender": t["lender"],
                    "Status": t["status"].upper(),
                    "Cross-Default": "Yes" if t["cross_default_clause"] else "No",
                })
            df_stack = pd.DataFrame(stack_rows)

            def _color_tranche(val: str) -> str:
                return {
                    "BREACH": "color: #b42318; font-weight: 700",
                    "WARNING": "color: #b45309; font-weight: 600",
                    "COMPLIANT": "color: #1f8f5f",
                }.get(val, "")

            st.dataframe(
                df_stack.style.applymap(_color_tranche, subset=["Status"]),
                hide_index=True,
                use_container_width=True,
            )

        with tab3:
            matrix_data = network.shock_matrix(
                total_debt=case_data["total_debt"],
                cash=case_data["cash"],
                ebitda=case_data["ebitda_ltm"],
                nlr_threshold=case_data["covenants"][0]["threshold"],
            )
            _render_shock_matrix(matrix_data)

            st.subheader("Trend Erosion Signal — NLR Historical")
            trend = network.trend_signal(
                historical_nlr=case_data["trend_nlr"],
                nlr_threshold=case_data["covenants"][0]["threshold"],
            )
            t1, t2, t3 = st.columns(3)
            t1.metric("Direction", trend["direction"].upper())
            t2.metric("Velocity (per quarter)", f"{trend['velocity_per_quarter']:+.2f}x")
            t3.metric(
                "Quarters to Breach Est.",
                str(trend["quarters_to_breach_estimate"]) if trend["quarters_to_breach_estimate"] else "N/A",
            )

        with tab4:
            st.subheader("Case Notes — Filing Context")
            st.info(case_data["case_notes"])
            st.caption(f"Source: {case_data['filing']} · Jurisdiction: {case_data['jurisdiction']}")

    # ── Debt tree + propagation paths ─────────────────────────────────────────
    st.divider()
    graph_col, detail_col = st.columns([2, 1])
    with graph_col:
        _render_debt_tree(network, shock_triggered=shock_triggered or not compliant)
    with detail_col:
        st.subheader("Propagation Paths")
        if shock_results:
            rows = [
                {
                    "Facility": detail.get("facility", node),
                    "Trigger": detail["trigger"],
                    "Face Value ($M)": f"${detail.get('face_value_usd_m', 0):,.0f}M",
                    "Path": " → ".join(detail["propagation_path"]) if detail["propagation_path"] else node,
                }
                for node, detail in sorted(shock_results.items())
            ]
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
            total_at_risk = sum(
                d.get("face_value_usd_m", 0) for d in shock_results.values()
            )
            st.metric("Total Debt at Risk", f"${total_at_risk:,.0f}M")
        else:
            st.info("No shock currently active.")

    # ── Audit export ──────────────────────────────────────────────────────────
    st.divider()
    audit_record = build_audit_record(
        ticker=str(st.session_state.get("ticker", case_data["ticker"] if case_data else "MANUAL")).upper(),
        covenant=covenant,
        total_debt=total_debt,
        cash=cash,
        ebitda=ebitda,
        ratio=display_value,
        compliant=compliant,
        buffer_distance=buffer_distance,
        warning_band=warning_band,
        source_payload=st.session_state["source_payload"],
        severity_score=severity_score,
        case_name=case_name,
    )
    st.download_button(
        "⬇ Download Audit JSON",
        data=audit_record_to_json(audit_record),
        file_name="ddcse_audit_record.json",
        mime="application/json",
    )


if __name__ == "__main__":
    main()

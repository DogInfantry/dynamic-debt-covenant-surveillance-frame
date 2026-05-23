"""Streamlit interface for the Dynamic Debt Covenant Surveillance Engine."""

from __future__ import annotations

import logging
import math

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import streamlit as st

from analytics import CorporateDebtNetwork
from audit import audit_record_to_json, build_audit_record
from compiler import CompiledCovenant, CovenantCompiler
from data_fetcher import FinancialDataPipeline
from ingestion import covenant_templates


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _format_ratio(value: float) -> str:
    if not math.isfinite(value):
        return "N/A"
    return f"{value:,.2f}x"


def _net_leverage_ratio(total_debt: float, cash: float, ebitda: float) -> float:
    if ebitda <= 0:
        return math.inf
    return (total_debt - cash) / ebitda


def _display_value(covenant: CompiledCovenant, total_debt: float, cash: float, ebitda: float) -> float:
    if covenant.governor == "Consolidated Net Leverage Ratio":
        return _net_leverage_ratio(total_debt, cash, ebitda)
    if covenant.governor == "Minimum Liquidity":
        return cash
    compliant, buffer = covenant.evaluate(total_debt, cash, ebitda)
    if covenant.operator in {"greater_than", "greater_than_or_equal"}:
        return covenant.threshold + buffer
    return covenant.threshold - buffer if compliant else covenant.threshold - buffer


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


def _render_debt_tree(network: CorporateDebtNetwork, shock_triggered: bool) -> None:
    graph = network.graph
    position = {
        "HoldCo": (0.0, 2.0),
        "OpCo_A": (-1.2, 1.0),
        "OpCo_B": (1.2, 1.0),
        "MinorSub_1": (-1.2, 0.0),
        "MinorSub_2": (1.2, 0.0),
    }
    node_colors = [
        "#d1495b" if graph.nodes[node].get("technical_default") else "#2a9d8f"
        for node in graph.nodes
    ]
    labels = {
        node: f"{node}\n{graph.nodes[node].get('facility', '')}"
        for node in graph.nodes
    }

    fig, ax = plt.subplots(figsize=(8, 4.8))
    nx.draw_networkx_edges(graph, position, ax=ax, arrows=True, edge_color="#8a94a6", arrowsize=16)
    nx.draw_networkx_nodes(
        graph,
        position,
        ax=ax,
        node_color=node_colors,
        node_size=2600,
        edgecolors="#17202a",
        linewidths=1.2,
    )
    nx.draw_networkx_labels(graph, position, labels=labels, ax=ax, font_size=8, font_weight="bold")
    ax.set_title("Corporate Debt Hierarchy" + (" - Shock Active" if shock_triggered else ""), fontsize=12)
    ax.axis("off")
    st.pyplot(fig, clear_figure=True)


def _initialize_state() -> None:
    defaults = {
        "total_debt": 400.0,
        "cash": 50.0,
        "ebitda": 100.0,
        "source_payload": {"source": "manual", "errors": []},
        "ticker": "MSFT",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def main() -> None:
    st.set_page_config(page_title="DDCSE", layout="wide")
    _initialize_state()

    st.title("Dynamic Debt Covenant Surveillance Engine")

    templates = covenant_templates()
    covenant_name = st.sidebar.selectbox("Covenant Type", list(templates.keys()))
    covenant = CovenantCompiler().compile(templates[covenant_name])
    network = CorporateDebtNetwork()

    st.sidebar.header("Live Market Fetch")
    ticker = st.sidebar.text_input("Ticker", key="ticker")
    statement_units = st.sidebar.selectbox("Normalize Statements To", ["raw", "thousands", "millions", "billions"], index=0)
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

    st.sidebar.header("Facility Inputs")
    total_debt = st.sidebar.number_input("Total Debt", min_value=0.0, step=10.0, format="%.2f", key="total_debt")
    cash = st.sidebar.number_input("Cash / Liquidity", min_value=0.0, step=5.0, format="%.2f", key="cash")
    ebitda = st.sidebar.number_input("EBITDA", step=5.0, format="%.2f", key="ebitda")

    st.sidebar.header("Shock Simulation")
    shock_node = st.sidebar.selectbox("Primary Breach Facility", list(network.graph.nodes), index=3)
    shock_triggered = st.sidebar.toggle("Trigger Covenant Shock", value=False)
    reset_graph = st.sidebar.button("Reset Graph State")

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

    ratio_col, status_col, buffer_col = st.columns(3)
    ratio_col.metric(covenant.governor, _format_ratio(display_value), f"Threshold {covenant.threshold:.2f}")
    with status_col:
        st.caption("Facility Status")
        _status_badge(compliant)
    buffer_col.metric("Buffer Cushion Delta", _format_ratio(buffer_distance))

    if compliant and math.isfinite(buffer_distance) and buffer_distance <= warning_band:
        st.warning(
            f"Buffer cushion is within 10% of the {covenant.threshold:.2f} threshold "
            f"({buffer_distance:.2f} <= {warning_band:.2f})."
        )
    elif not compliant:
        st.error("Facility is in breach. Cross-default propagation is reflected in the debt tree.")

    graph_col, detail_col = st.columns([2, 1])
    with graph_col:
        _render_debt_tree(network, shock_triggered=shock_triggered or not compliant)
    with detail_col:
        st.subheader("Propagation Paths")
        if shock_results:
            rows = [
                {
                    "facility": node,
                    "trigger": detail["trigger"],
                    "path": " -> ".join(detail["propagation_path"]) if detail["propagation_path"] else node,
                }
                for node, detail in sorted(shock_results.items())
            ]
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        else:
            st.info("No shock currently active.")

    audit_record = build_audit_record(
        ticker=str(st.session_state.get("ticker", "MANUAL")).upper(),
        covenant=covenant,
        total_debt=total_debt,
        cash=cash,
        ebitda=ebitda,
        ratio=display_value,
        compliant=compliant,
        buffer_distance=buffer_distance,
        warning_band=warning_band,
        source_payload=st.session_state["source_payload"],
    )
    st.download_button(
        "Download Audit JSON",
        data=audit_record_to_json(audit_record),
        file_name="ddcse_audit_record.json",
        mime="application/json",
    )


if __name__ == "__main__":
    main()

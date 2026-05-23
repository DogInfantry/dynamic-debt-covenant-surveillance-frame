# DDCSE Architecture Brief

## Operating Model

DDCSE turns legal covenant language, borrower or market financials, and debt
hierarchy relationships into a repeatable surveillance workflow.

```text
Contract Text -> Structured Covenant Rule -> AST Function -> Metrics -> Status
                                                       |
                                                       v
                                      Variance Warning + Cross-Default Graph
```

## Four-Stage Pipeline

| Stage | Module | Purpose | Output |
|---|---|---|---|
| Ingestion | `ingestion.py` | Converts Article VI-style covenant language into structured rule dictionaries. | Relation, operator, governor, object |
| Safe Compilation | `compiler.py` | Compiles validated rule dictionaries into constrained Python AST functions. | Compliance callable |
| Market Pipeline | `data_fetcher.py` | Pulls yfinance quarterly balance sheet and income statement data. | Normalized financial payload |
| Cross-Default Cascades | `analytics.py` | Models facility hierarchy and shock propagation with NetworkX. | Technical default map |

## Risk Controls

- No raw `eval()` parsing.
- Explicit covenant template registry.
- Unit normalization for statement-scale mismatches.
- Audit JSON export for every compliance decision.
- Unit tests for extreme financial boundaries.
- CI workflow for automated regression checks.

## Viewer Artifacts

- `docs/screenshots/streamlit_dashboard.png`
- `docs/screenshots/covenant_warning.png`
- `docs/screenshots/cross_default_graph.png`
- `docs/sample_audit_record.json`
- `docs/diagrams/pipeline.mmd`
- `docs/diagrams/debt_network.mmd`

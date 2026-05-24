# Dynamic Debt Covenant Surveillance Engine — v2.0

[![CI](https://github.com/DogInfantry/dynamic-debt-covenant-surveillance-frame/actions/workflows/ci.yml/badge.svg)](https://github.com/DogInfantry/dynamic-debt-covenant-surveillance-frame/actions/workflows/ci.yml/badge.svg) [![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org) [![License](https://img.shields.io/badge/license-Apache--2.0-green)](LICENSE) [![Streamlit](https://img.shields.io/badge/UI-Streamlit-red)](https://streamlit.io) [![NetworkX](https://img.shields.io/badge/Graph-NetworkX-2f6f9f)](https://networkx.org)

A **production-grade private credit covenant surveillance prototype** built for portfolio monitoring teams, credit risk functions, and PE/credit fund professionals. Features real-case distressed credit data, AST-safe covenant compilation, NetworkX cross-default cascade modeling, and a Streamlit monitoring dashboard.

---

## Real Case Coverage

Three real Chapter 11 bankruptcy cases, all sourced from public SEC filings, bankruptcy petitions, and court-filed First-Day Declarations:

| Company | Ticker | Filing | NLR at Filing | Total Debt |
|---------|--------|--------|---------------|-----------|
| Envision Healthcare | EVHC | Ch.11 May 2023 (SDNY) | **16.6x** | $7.1B |
| Revlon Inc | REV | Ch.11 Jun 2022 (SDNY) | **13.9x** | $3.7B |
| Cineworld Group | CINE.L | Ch.11 Sep 2022 (SDTX) | **13.8x** | $8.9B |

These cases illustrate the three dominant covenant-breach archetypes in private credit:
- **LBO leverage explosion** (Envision — regulatory revenue cliff post-KKR buyout)
- **M&A debt + operational disruption** (Revlon — Elizabeth Arden acquisition + DTC disruption)
- **Macro event covenant cascade** (Cineworld — COVID → 22.4x NLR → waiver → re-breach)

---

## Architecture: Four-Stage Pipeline

```
                    ┌─────────────────────────────────────────────────────┐
                    │           DDCSE v2 Surveillance Pipeline            │
                    └─────────────────────────────────────────────────────┘

 ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐
 │  1. Ingestion│───▶│ 2. AST-Safe  │───▶│ 3. Analytics │───▶│ 4. Output Layer  │
 │              │    │   Compiler   │    │   Engine     │    │                  │
 │ real_cases   │    │ compiler.py  │    │ analytics_v2 │    │ Streamlit UI     │
 │ .py (3 live  │    │              │    │              │    │ Audit JSON       │
 │  case files) │    │ No eval()    │    │ NetworkX     │    │ PPTX mini-deck   │
 │ yfinance     │    │ TypedDict    │    │ Shock Matrix │    │ PDF report       │
 │ live pull    │    │ contracts    │    │ Trend detect │    │                  │
 └──────────────┘    └──────────────┘    └──────────────┘    └──────────────────┘
```

### 1. Real-Case Ingestion (`real_cases.py`)

Structured `TypedDict`-typed records for each borrower, capturing:

- Full covenant package (leverage, coverage, FCCR, liquidity tests)
- Debt stack (tranche-level: face value, seniority, rate, lender, cross-default clause)
- LTM financial inputs (EBITDA, total debt, cash, interest expense, capex)
- Historical quarterly ratio trend (NLR + ICR across 8 periods)
- Case narrative (filing context, breach catalyst, restructuring outcome)

Source lineage is embedded at the field level (`source: "10-K FY2022 Note 9"`).

### 2. AST-Safe Covenant Compiler (`compiler.py`)

Converts structured `CovenantRuleConfig` dictionaries into typed Python callables using Abstract Syntax Tree generation. **Zero use of `eval()` or `exec()`.**

Why this matters:
- Covenant text extracted from PDFs or OCR is an injection surface
- AST constrains permitted operations to explicit arithmetic nodes
- Generated functions are deterministic, testable, and model-risk reviewable

### 3. Analytics Engine (`analytics_v2.py` — new in v2)

**Covenant Evaluator:**
- Multi-covenant package runner (leverage + coverage + FCCR + liquidity)
- Buffer severity scoring (0–100 continuous) for portfolio heat maps
- Status classification: `COMPLIANT` → `WATCHLIST` → `WARNING` → `BREACH`

**NetworkX Cross-Default Cascade:**
- Directed graph of debt entities (HoldCo, OpCo, subsidiaries)
- BFS propagation from initial breach entity
- Tracks: propagation path, entities triggered, total debt at risk, cascade depth
- Pre-built Envision Healthcare graph (`build_envision_graph()`) as reference case

**Macro Shock Matrix:**
- EBITDA compression × debt increase sensitivity grid
- Each cell: stressed NLR, breach flag, buffer distance
- Configurable shock vectors for custom scenario analysis

**Trend Erosion Detector:**
- Directional velocity analysis (improving / stable / deteriorating)
- Quarters-to-breach estimate under current trajectory
- Works on historical NLR or ICR time series

### 4. Output Layer (`app.py`, `audit.py`)

**Streamlit Dashboard:**
- Portfolio monitor with company selector (3 real cases)
- Live ticker fetch via `yfinance.FinancialDataPipeline`
- Covenant package status with buffer bars and severity badges
- Historical ratio trend chart (dual-axis: NLR + ICR)
- Macro stress test simulator (interactive EBITDA/debt sliders)
- NetworkX cascade visualization (matplotlib node coloring by status)
- JSON audit export per compliance run

**Audit Record (per run):**
```json
{
  "run_id": "DDCSE-2024-0331-001",
  "timestamp_utc": "2024-03-31T06:00:07Z",
  "engine_version": "2.0.0",
  "compiler": "AST-safe (no eval)",
  "ticker": "EVHC",
  "covenant_type": "Net Leverage Ratio",
  "threshold": 6.5,
  "actual": 16.61,
  "compliant": false,
  "buffer_distance": -10.11,
  "severity_score": 97.3,
  "status": "BREACH",
  "source_payload": { "filing": "10-K FY2022", "note": "Note 9" }
}
```

---

## Repository Layout

```
.
├── real_cases.py           ← Real case data registry (Envision / Revlon / Cineworld)
├── analytics_v2.py         ← Enhanced analytics engine (NEW in v2)
├── contracts.py            ← Shared TypedDict contracts
├── compiler.py             ← AST-safe covenant compiler
├── ingestion.py            ← Credit agreement ingestion layer
├── data_fetcher.py         ← yfinance live financial pipeline
├── audit.py                ← JSON audit record serializer
├── app.py                  ← Streamlit monitoring dashboard
├── requirements.txt
├── test_suite.py
├── test_data_fetcher.py
└── docs/
    ├── real_cases/
    │   ├── envision_case_notes.md
    │   ├── revlon_case_notes.md
    │   └── cineworld_case_notes.md
    ├── architecture.md
    ├── sample_audit_record.json
    ├── screenshots/
    └── deck/
        ├── DDCSE_Private_Credit_Surveillance_Mini_Deck.pptx
        └── ib_output.md
```

---

## Quick Start

```bash
# Install dependencies
pip install networkx pandas yfinance matplotlib streamlit

# Run the Streamlit dashboard
python -m streamlit run app.py --server.port 8501

# Run covenant evaluation on a real case
python3 -c "
from real_cases import get_case
from analytics_v2 import evaluate_package, portfolio_severity_score

case = get_case('EVHC')   # Envision Healthcare
results = evaluate_package(case['covenants'])
for r in results:
    print(f'{r.name}: {r.actual:.2f} vs {r.threshold:.2f} [{r.status}] severity={r.severity_score}')
print(f'Portfolio severity: {portfolio_severity_score(results):.1f}/100')
"

# Run cross-default cascade
python3 -c "
from analytics_v2 import build_envision_graph, simulate_cascade
G = build_envision_graph()
result = simulate_cascade(G, breach_entity_id='sub1_abl')
print(f'Cascade from Sub 1 ABL:')
print(f'  Path: {\" → \".join(result.propagation_path)}')
print(f'  Total debt at risk: \${result.total_debt_at_risk_usd_m:,.0f}M')
print(f'  Technical cross-defaults: {result.technical_cross_defaults}')
"
```

---

## Why This Matters in Private Credit

The conventional covenant monitoring workflow looks like this:

> PDF credit agreement → email to analyst → Excel tickler → quarterly cert → missed breach

DDCSE replaces that with:

1. **Structured ingestion** — covenant language → typed fields with source lineage
2. **AST compilation** — typed fields → deterministic, injectable compliance functions
3. **Live financial inputs** — yfinance quarterly statements → normalized financial payload
4. **Cascade impact** — any breach → propagation map showing total debt affected
5. **Audit trail** — every run produces a JSON record for credit, MRM, and internal audit

The result is faster breach detection, safer automation, and a reviewable artifact for regulators and internal audit.

---

## Design Decisions

### AST vs `eval()`

Credit agreement text arrives as PDFs, OCR output, or analyst-maintained templates. These are unsafe execution contexts. Raw `eval()` executes arbitrary code if the input is malformed or manipulated. DDCSE's AST compiler constrains allowed operations to explicit arithmetic nodes — the compiler validates operators, governors, and thresholds before execution, and the generated function is testable and model-risk reviewable.

### Real Case Data vs. Synthetic

V2 uses real Ch.11 cases because:
- Ratio trajectories are non-linear (Cineworld NLR: 2.9x → 22.4x → 12.1x → 13.8x)
- Cross-default chain behavior is specific to actual guarantee structures
- The Citibank/Revlon case demonstrates how cross-default clauses interact with payment errors
- Real source lineage makes this usable as a work sample for credit/PE interviews

---

## License

Apache-2.0. See [LICENSE](LICENSE).

---

*Built by Anklesh Rawat (DogInfantry) — Finance & Data Engineering portfolio.*
*Sources: SEC EDGAR, SDNY/SDTX PACER, Bloomberg Terminal (FY2022 data), company IR.*

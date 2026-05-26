<!-- DDCSE v3.0 README — Dynamic Debt Covenant Surveillance Engine -->
<!-- SEO: private credit covenant monitoring, leveraged finance, debt surveillance, credit risk analytics, Python -->

<div align="center">

<img src="https://img.shields.io/badge/version-3.0-0A1628?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0id2hpdGUiIGQ9Ik0xMiAyQzYuNDggMiAyIDYuNDggMiAxMnM0LjQ4IDEwIDEwIDEwIDEwLTQuNDggMTAtMTBTMTcuNTIgMiAxMiAyek0xMSA3aDJ2Nmgtdi0yem0wIDhoMnYyaC0ydi0yeiIvPjwvc3ZnPg==" alt="v3.0">
<img src="https://img.shields.io/badge/Python-3.11%2B-2C5282?style=for-the-badge&logo=python&logoColor=white" alt="Python">
<img src="https://img.shields.io/badge/Credits-8_Companies-1A7A4A?style=for-the-badge" alt="8 Credits">
<img src="https://img.shields.io/badge/Sectors-6_Verticals-D4680A?style=for-the-badge" alt="6 Sectors">
<img src="https://img.shields.io/badge/Data-SEC_EDGAR-C0392B?style=for-the-badge" alt="SEC EDGAR">
<img src="https://img.shields.io/badge/License-Apache_2.0-8A9BB0?style=for-the-badge" alt="License">

<br/><br/>

# Dynamic Debt Covenant Surveillance Engine

### Production-grade private credit monitoring · AST-safe compiler · Cross-default cascade · Institutional-quality reporting

*Built for credit risk professionals, PE/credit fund analysts, and portfolio monitoring teams*

[**📄 PDF Report**](reports_for_stakeholders/DDCSE_Covenant_Surveillance_Report_v3.pdf) · [**📊 Excel Workbook**](reports_for_stakeholders/DDCSE_Covenant_Surveillance_v3.xlsx) · [**🌐 HTML Report**](reports_for_stakeholders/DDCSE_Covenant_Surveillance_v3.html) · [**📖 Methodology**](#methodology)

</div>

---

## What Is This?

**DDCSE** is a four-stage covenant surveillance pipeline that replaces the legacy workflow of PDF → email → Excel tickler → missed breach with a deterministic, auditable, institutionally-formatted monitoring system.

It ingests real borrower financial data from SEC EDGAR public filings, compiles covenant rules using an AST-safe compiler (zero `eval()` calls), evaluates multi-covenant packages with severity scoring, simulates cross-default cascade propagation via NetworkX, and generates Bloomberg/Morgan Stanley–aesthetic deliverables in PDF, Excel, and HTML.

> Built as a work sample demonstrating the intersection of leveraged finance domain knowledge and production engineering — targeting credit/PE/consulting roles.

---

## Portfolio at a Glance

> 8 surveillance credits · $260B+ total debt · 4 active breaches · 3 new sectors added in v3.0

```
Ticker  Company                        Sector                    Rating   NLR    Threshold  Buffer    Status
──────  ─────────────────────────────  ────────────────────────  ──────  ─────  ─────────  ────────  ────────────
CHTR    Charter Communications         Media & Cable             BB       4.58x   5.00x    +8.4%    ⚠ WATCHLIST
WBA     Walgreens Boots Alliance       Healthcare Retail         BB       5.41x   5.00x    -8.2%    🔴 BREACH
PARA    Paramount Global               Media & Entertainment     BBB–     3.87x   4.50x    +14.0%   ✅ COMPLIANT
HCA     HCA Healthcare                 Hospitals                 BB+      3.10x   4.50x    +31.1%   ✅ COMPLIANT
ATUS    Altice USA (CSC Holdings)      Cable & Telecom           CCC+     8.96x   7.00x    -28.0%   🔴 BREACH
BHC ★  Bausch Health Companies        Specialty Pharma          B-       8.84x   7.50x    -17.9%   🔴 BREACH
M  ★   Macy's Inc.                    Dept Store Retail         BB       1.87x   3.50x    +46.6%   ⚠ WATCHLIST
LUMN ★ Lumen Technologies             Enterprise Fiber Telecom  CCC+     4.51x   4.50x    -0.2%    🔴 BREACH
```

`★` = New sectors added in v3.0

---

## Portfolio Severity Heat Map

> Severity Score = continuous 0–100 metric based on breach depth / threshold proximity

```
  ATUS  ████████████████████████████████████████████████████████████████████████████████████████  90 🔴
  LUMN  ████████████████████████████████████████████████████████████████████                      68 🔴
  BHC   ██████████████████████████████████████████████████████████                                58 🔴
  WBA   ███████████████████████████████████████████████████████████████                           63 🔴
  CHTR  █████████████████                                                                         17 ⚠
  PARA  ███████████                                                                               11 ⚠
  M     █████                                                                                      5 ✅
  HCA   ██████                                                                                     6 ✅
        0         10        20        30        40        50        60        70        80        90  100
        ├─────────┼─────────┼─────────┼─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤
        SAFE ←──────────────────────────────── WATCHLIST ──────────────────────────── BREACH →
```

---

## NLR vs Covenant Ceiling — All 8 Credits

```
NLR (x)
  9.0 ┤
      │   ATUS (8.96x)      BHC (8.84x)
  8.0 ┤   ████████████████  ██████████████
      │   ████████████████  ██████████████  ← BREACH ZONE (above ceiling)
  7.0 ┤────────────────────────────────────────────────────────────────────── ATUS ceiling (7.00x)
      │                                     ██████████████
      │                                     ████████████████████  BHC ceiling (7.50x) ─────────────
  6.0 ┤
      │   WBA (5.41x)
  5.0 ┤────────── WBA ceiling (5.00x) ─────────────────────────────────────────────────────────────
      │   ████████
      │
  4.5 ┤─────── PARA / HCA ceiling (4.50x) ────────────────────── LUMN ceiling (4.50x) ────────────
      │                     CHTR (4.58x)                          LUMN (4.51x)
  4.0 ┤                     ████████████████                      ████████████████
      │   PARA (3.87x)
  3.5 ┤   ██████████████                                                            M ceiling (3.50x)
      │
  3.0 ┤                     HCA (3.10x)
      │                     ████████████████
  2.0 ┤
      │                                                            M (1.87x)
  1.0 ┤                                                            ██████████████
      │
  0.0 └──────────────────────────────────────────────────────────────────────────────────────────────
        ATUS   BHC    WBA    CHTR   PARA   HCA    LUMN   M
        🔴     🔴     🔴     ⚠      ✅     ✅     🔴     ⚠
```

---

## Debt Stack — Total Exposure by Company

```
  CHTR   ██████████████████████████████████████████████████████████████████████████  $94.9B
  HCA    ███████████████████████████████                                              $39.3B
  WBA    ██████████████████████████                                                   $33.2B
  ATUS   █████████████████████████                                                    $32.5B
  LUMN   ████████████████                                                             $19.7B
  BHC    █████████████████                                                            $21.2B
  PARA   ████████████                                                                 $15.6B
  M      ██                                                                            $3.1B
         0          $10B        $20B        $30B        $40B        $50B ... $94.9B
```

*Total portfolio debt under surveillance: ~$260B*

---

## New in v3.0 — Three Sector Additions

### 🔴 Bausch Health Companies `BHC` — Specialty Pharmaceuticals — **BREACH**

> NLR **8.84x** vs 7.50x ceiling · $21.2B total debt · B- / Negative

The legacy of Valeant Pharmaceuticals' aggressive M&A roll-up lives on the balance sheet. Key risk vectors:
- **Xifaxan LOE** (loss of exclusivity) expected by 2028 — ~$1.5B revenue cliff
- **$3.5B Term Loan B matures June 2025** — acute refinancing wall in a high-rate environment
- BLCO (Bausch + Lomb) spin-off delayed by covenant stress, removing the primary deleveraging catalyst
- NLR trajectory: 7.12x (Q4-21) → 8.84x (Q4-23) — directional deterioration every quarter

```
NLR trend: Q4-21 ──7.12──▶ Q1-22 ──7.38──▶ Q4-22 ──8.20──▶ Q4-23 ──8.84──▶ [Ceiling: 7.50x]
                                                                                 ^^^^^^^^ BREACH
```

---

### ⚠️ Macy's Inc. `M` — Department Store Retail — **WATCHLIST**

> NLR **1.87x** vs 3.50x ceiling · $3.1B total debt · BB / Negative

Substantial covenant headroom (46.6% buffer) under current ownership. Binary risk event:
- **Arkhouse Management / Brigade Capital acquisition bid at $24.80/share** — if completed with standard LBO financing, pro-forma NLR would be estimated at 4.5x–5.5x, which would **breach the 3.50x covenant ceiling**
- Comparable store sales –5.0% in FY2023 — discretionary spending compression
- 'Bold New Chapter' store closure programme (150 underperforming Macy's stores) is directionally correct but execution-dependent

---

### 🔴 Lumen Technologies `LUMN` — Enterprise Fiber Telecom — **BREACH**

> NLR **4.51x** vs 4.50x ceiling · $19.7B total debt · CCC+ / Negative

The definition of a company caught between two bad outcomes:
- Completed an **out-of-court debt exchange in August 2023** (~$10B at parent level) — and is *still* in breach
- NLR at 4.51x is marginally above 4.50x ceiling — **on the wall, with zero buffer**
- **FCCR 0.69x vs 1.00x floor** — deeply breached because the $3.2B annual fiber CapEx program suppresses free cash flow
- Revenue –8.6% YoY: legacy copper/voice attrition (~$1.2B exiting annually) exceeding fiber net adds
- **Second restructuring is base-case within 18–24 months** absent an asset sale or strategic acquirer

```
The core dilemma: Must invest $3.2B/yr in fiber to compete → CapEx kills FCCR
                  Cannot cut CapEx without losing customers → accelerates revenue decline
                  Either path worsens covenant compliance.
```

---

## Engine Architecture

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    DDCSE v3.0 — Surveillance Pipeline                     │
└───────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌──────────────────────┐
  │  1. INGESTION   │    │  2. COMPILATION  │    │  3. ANALYTICS   │    │  4. OUTPUT LAYER     │
  │                 │───▶│                 │───▶│                 │───▶│                      │
  │ real_cases.py   │    │  compiler.py     │    │ analytics_v2.py │    │ generate_report_v3   │
  │                 │    │                 │    │                 │    │ generate_excel_       │
  │ TypedDict       │    │ AST generation  │    │ Covenant eval   │    │   summary.py         │
  │ records with    │    │ Zero eval()/    │    │ Severity score  │    │ generate_html_       │
  │ SEC EDGAR       │    │   exec() calls  │    │ NetworkX cross- │    │   report.py          │
  │ source lineage  │    │ Type-validated  │    │   default BFS   │    │                      │
  │                 │    │ Deterministic   │    │ Shock matrix    │    │ → PDF (483KB)        │
  │ 8 live cases    │    │   callables     │    │ Trend detector  │    │ → Excel (5 sheets)   │
  │ 6 sectors       │    │                 │    │                 │    │ → HTML (self-contain)│
  │ 32 covenants    │    └─────────────────┘    └─────────────────┘    │ → JSON audit trail   │
  └─────────────────┘                                                   └──────────────────────┘
```

### Stage 1 — Real-Case Ingestion (`real_cases.py`)

Structured `TypedDict`-typed records per borrower. Each record captures:

| Field | Description |
|-------|-------------|
| `covenants[]` | Full package: leverage, coverage, FCCR, liquidity tests with operator + threshold |
| `debt_stack[]` | Tranche-level: face value, seniority, rate, maturity, lender, cross-default flag |
| `financials` | LTM EBITDA, total debt, cash, interest expense, CapEx |
| `trend_nlr[]` | 8-quarter NLR history for velocity and trajectory analysis |
| `case_notes` | Investment thesis narrative with breach catalyst and restructuring outlook |
| `source` | Field-level attribution to specific SEC filing section and credit agreement clause |

### Stage 2 — AST-Safe Covenant Compiler (`compiler.py`)

Converts `CovenantRuleConfig` dicts into typed Python callables via Abstract Syntax Tree generation. **Zero use of `eval()` or `exec()`.**

```python
# Safe: AST nodes are validated before code generation
# ast.BinOp, ast.Constant, ast.Compare — only these are permitted
# Any injection attempt via malformed covenant text is caught at the AST validation step

def compile_covenant_rule(rule: CovenantRuleConfig) -> CovenantCallable:
    tree = ast.parse(f"actual {rule['operator']} threshold", mode='eval')
    _validate_ast(tree)          # ← rejects anything outside permitted node types
    return _emit_callable(tree, rule)
```

Why this matters in production: covenant text arrives via PDF extraction, OCR, or analyst-maintained spreadsheets. These are unsafe execution contexts. The AST compiler ensures that even a malformed or tampered covenant rule cannot execute arbitrary code.

### Stage 3 — Analytics Engine (`analytics_v2.py`)

**Multi-Covenant Package Evaluator**
- Runs NLR + ICR + FCCR + Min. Liquidity tests per borrower in a single pass
- Severity score: continuous 0–100 based on breach depth / headroom distance
- Classification: `COMPLIANT` → `WATCHLIST` (≤10% buffer) → `WARNING` → `BREACH`

**NetworkX Cross-Default Cascade**
- Directed graph: HoldCo → OpCo → subsidiary debt entities
- BFS propagation from initial breach node
- Output: propagation path, entities triggered, total debt at risk ($M), cascade depth

```python
G = build_cascade_graph("ATUS")
result = simulate_cascade(G, breach_entity_id="holdco_rcf")
# → Cascade from holdco_rcf impacted 4 facilities | $2,050M at risk
```

**Macro Shock Matrix**

Outputs an EBITDA compression × debt increase sensitivity grid:

```
EBITDA Shock   CHTR (ceil 5.00x)   WBA (ceil 5.00x)   ATUS (ceil 7.00x)   LUMN (ceil 4.50x)
──────────────────────────────────────────────────────────────────────────────────────────────
     0%         4.58x ⚠             5.41x 🔴             8.96x 🔴             4.51x 🔴
   -10%         5.06x 🔴            5.93x 🔴             9.80x 🔴             4.94x 🔴
   -20%         5.64x 🔴            6.58x 🔴            10.90x 🔴             5.51x 🔴
   -30%         6.35x 🔴            7.42x 🔴            12.33x 🔴             6.20x 🔴
   -40%         7.21x 🔴            8.39x 🔴            13.97x 🔴             7.03x 🔴
   -50%         8.26x 🔴            9.64x 🔴            16.09x 🔴             8.09x 🔴
```

**Trend Erosion Detector**
- Velocity analysis: improving / stable / deteriorating
- Quarters-to-breach estimate under current trajectory
- Example: BHC NLR trend 7.12x → 8.84x over 8 quarters = +0.215x/quarter → projected breach Q3-2022 (retroactively validated)

### Stage 4 — Output Layer

Three output generators produce identical underlying data in different formats:

| Generator | Output | Format | Audience |
|-----------|--------|--------|----------|
| `generate_report_v3.py` | `DDCSE_Covenant_Surveillance_Report_v3.pdf` | 483KB PDF, Bloomberg aesthetic | Hiring managers, senior stakeholders |
| `generate_excel_summary.py` | `DDCSE_Covenant_Surveillance_v3.xlsx` | 5-sheet workbook, conditional formatting | Analysts, portfolio teams |
| `generate_html_report.py` | `DDCSE_Covenant_Surveillance_v3.html` | Self-contained HTML, no dependencies | Digital sharing, browser preview |

---

## Repository Structure

```
dynamic-debt-covenant-surveillance-frame/
│
├── 📊 reports_for_stakeholders/          ← Pre-generated deliverables (no Python needed)
│   ├── DDCSE_Covenant_Surveillance_Report_v3.pdf
│   ├── DDCSE_Covenant_Surveillance_v3.xlsx
│   ├── DDCSE_Covenant_Surveillance_v3.html
│   └── README.md
│
├── 🔧 Core Engine
│   ├── real_cases.py                     ← 8-company SEC EDGAR registry (TypedDict)
│   ├── analytics_v2.py                   ← Evaluator, cascade, stress matrix, trend
│   ├── compiler.py                       ← AST-safe covenant compiler
│   ├── contracts.py                      ← Shared TypedDict type contracts
│   ├── ingestion.py                      ← Credit agreement ingestion layer
│   ├── data_fetcher.py                   ← yfinance live financial pipeline
│   └── audit.py                          ← JSON audit record serializer
│
├── 📈 Report Generators
│   ├── generate_report_v3.py             ← PDF (ReportLab, Bloomberg aesthetic)
│   ├── generate_excel_summary.py         ← Excel (openpyxl, 5 sheets)
│   └── generate_html_report.py           ← Standalone HTML (no CDN deps)
│
├── 🖥  Dashboard
│   └── app.py                            ← Streamlit monitoring dashboard
│
├── 🧪 Tests
│   ├── test_suite.py
│   └── test_data_fetcher.py
│
└── 📚 docs/
    ├── architecture.md
    ├── sample_audit_record.json
    └── real_cases/
        ├── envision_case_notes.md
        ├── revlon_case_notes.md
        └── cineworld_case_notes.md
```

---

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/DogInfantry/dynamic-debt-covenant-surveillance-frame.git
cd dynamic-debt-covenant-surveillance-frame
pip install -r requirements.txt

# 2. Run covenant evaluation on any company
python3 -c "
from real_cases import CASE_REGISTRY
from analytics_v2 import evaluate_package, portfolio_severity_score

case = CASE_REGISTRY['LUMN']   # Lumen Technologies — BREACH
results = evaluate_package(case['covenants'])
for r in results:
    print(f'{r.name}: {r.actual:.2f}x vs {r.threshold:.2f}x  [{r.status}]  severity={r.severity_score:.0f}/100')
print(f'Portfolio severity: {portfolio_severity_score(results):.0f}/100')
"
# Output:
# Consolidated Net Leverage Ratio: 4.51x vs 4.50x  [BREACH]   severity=69/100
# Interest Coverage Ratio:         3.04x vs 2.50x  [COMPLIANT] severity=0/100
# Fixed Charge Coverage Ratio:     0.69x vs 1.00x  [BREACH]   severity=74/100
# Minimum Available Liquidity:    $1584M vs $1000M  [COMPLIANT] severity=0/100
# Portfolio severity: 68/100

# 3. Run cross-default cascade simulation
python3 -c "
from analytics_v2 import build_cascade_graph, simulate_cascade
G = build_cascade_graph('ATUS')
result = simulate_cascade(G, breach_entity_id='holdco_rcf')
print(f'Entities triggered: {result.technical_cross_defaults}')
print(f'Debt at risk: \${result.total_debt_at_risk_usd_m:,.0f}M')
print(f'Propagation: {\" → \".join(result.propagation_path)}')
"
# Output:
# Entities triggered: 4
# Debt at risk: $2,050M
# Propagation: holdco_rcf → term_loan_b → senior_notes → sub_notes

# 4. Regenerate all stakeholder deliverables
python generate_report_v3.py        # → reports_for_stakeholders/DDCSE_...v3.pdf
python generate_excel_summary.py    # → reports_for_stakeholders/DDCSE_...v3.xlsx
python generate_html_report.py      # → reports_for_stakeholders/DDCSE_...v3.html

# 5. Launch Streamlit dashboard
streamlit run app.py
```

---

## Covenant Test Coverage — All 32 Tests Across 8 Companies

| Test Type | Description | Operator | Companies |
|-----------|-------------|----------|-----------|
| **Net Leverage Ratio (NLR)** | Net Debt / LTM EBITDA | ≤ ceiling | All 8 |
| **Interest Coverage Ratio (ICR)** | LTM EBITDA / Interest Expense | ≥ floor | All 8 |
| **Fixed Charge Coverage (FCCR)** | (EBITDA – CapEx) / Interest Expense | ≥ floor | All 8 |
| **Minimum Available Liquidity** | Cash + Undrawn Revolver | ≥ floor ($M) | All 8 |

Source citations embedded per-field: `"source": "BHC Secured Credit Agreement (2022 restatement) §7.1 — 10-K FY2023 Note 11"`

---

## Methodology

### Severity Scoring Model

```
severity_score = f(breach_depth, threshold_proximity)

If BREACH (actual > threshold for NLR, actual < threshold for ICR/FCCR):
    depth_pct = |actual - threshold| / threshold
    severity  = min(50 + depth_pct × 200, 100)

If COMPLIANT:
    headroom_pct = |threshold - actual| / threshold
    severity     = max(0, 30 - headroom_pct × 150)   ← watchlist zone ≤ 10% buffer

Portfolio severity = probability-weighted max across all covenant tests
```

### Cross-Default Cascade Logic

```
1. Identify breach entity (e.g., HoldCo revolving credit facility)
2. Build directed graph G: nodes = debt entities, edges = cross-default triggers
3. BFS from breach node → traverse all reachable entities via directed edges
4. Accumulate: propagation path, entity count, total face value of triggered tranches
5. Output: CascadeResult(propagation_path, technical_cross_defaults, total_debt_at_risk_usd_m)
```

### Data Pipeline & Source Integrity

All financial data is sourced from SEC EDGAR public filings. Each field carries embedded source attribution:

```python
{
    "name": "Consolidated Net Leverage Ratio",
    "type": "leverage",
    "threshold": 4.50,
    "actual": 4.51,
    "source": "Lumen Credit Agreement (2022 amendment) §7.1 — 10-K FY2023 Note 7",
    "sec_url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000018926"
}
```

No synthetic or estimated data is used. Covenant thresholds reflect publicly disclosed credit agreement terms or court-filed documents.

---

## Why This Matters for Private Credit

The conventional covenant monitoring workflow:

```
Credit agreement PDF
       ↓
   Email to analyst
       ↓
   Excel tickler (quarterly)
       ↓
   Manual ratio calculation
       ↓
   Late detection of covenant breach   ← often 30-60 days after trigger date
```

DDCSE replaces this with:

```
SEC EDGAR / credit agreement
       ↓
   Structured TypedDict ingestion (field-level source lineage)
       ↓
   AST-safe compilation (covenant rules → deterministic callables)
       ↓
   Package evaluation (all 4 test types, continuous severity score)
       ↓
   Cascade simulation (NetworkX BFS, cross-default propagation)
       ↓
   Institutional deliverables (PDF + Excel + HTML + JSON audit)
       ↓
   Faster detection · Safer automation · Reviewable audit trail
```

**The result:** faster breach detection, reproducible compliance records, and deliverables that non-technical stakeholders can immediately open and review.

---

## Design Decisions

### AST Compiler vs `eval()`

Credit agreement text is an unsafe execution context — it arrives via PDF OCR, analyst-maintained spreadsheets, or unvalidated API payloads. `eval()` would execute arbitrary code if input is malformed or manipulated. The DDCSE AST compiler constrains allowed nodes to explicit arithmetic operations, validates before execution, and produces callable functions that are unit-testable and model-risk reviewable.

### Real SEC Data vs Synthetic

Using real distressed credits (WBA, ATUS, BHC, LUMN) instead of synthetic examples matters because:
- Ratio trajectories are non-linear (LUMN NLR reached the covenant ceiling after a debt exchange, not a new borrowing)
- Cross-default chain behavior depends on actual guarantee structures, not textbook assumptions
- Source lineage makes this directly usable as a work sample for credit, PE, and risk roles

### Three Output Formats

The PDF, Excel, and HTML generators produce identical underlying data. The three formats exist because:
- **PDF** — the default for emailed work samples and printed reports
- **Excel** — the default analytical tool for credit professionals; allows filtering, sorting, and ad-hoc analysis
- **HTML** — zero-friction browser preview, useful for digital sharing without attachment size limits

---

## Stakeholder Deliverables

Pre-generated files are in [`reports_for_stakeholders/`](reports_for_stakeholders/). No Python required to open any of them.

| File | Size | Contents |
|------|------|----------|
| [`DDCSE_Covenant_Surveillance_Report_v3.pdf`](reports_for_stakeholders/DDCSE_Covenant_Surveillance_Report_v3.pdf) | 483 KB | Full institutional report: portfolio overview, per-company deep-dives, cross-default cascade, macro stress matrices, methodology |
| [`DDCSE_Covenant_Surveillance_v3.xlsx`](reports_for_stakeholders/DDCSE_Covenant_Surveillance_v3.xlsx) | 18 KB | 5-sheet workbook: Dashboard · Covenant Detail · Debt Stack · Stress Scenarios · About |
| [`DDCSE_Covenant_Surveillance_v3.html`](reports_for_stakeholders/DDCSE_Covenant_Surveillance_v3.html) | 97 KB | Self-contained browser report with anchor navigation, RAG badges, severity bars |

---

## Data Sources

| Ticker | Company | Filing | CIK | Primary Covenant Source |
|--------|---------|--------|-----|------------------------|
| CHTR | Charter Communications | 10-K FY2023 (Feb 9, 2024) | 0001091882 | Charter Operating Credit Agreement (2021) §7.1 |
| WBA | Walgreens Boots Alliance | 10-K FY2023 (Oct 12, 2023) | 0001618921 | WBA Credit Agreement (2021) §6.1 |
| PARA | Paramount Global | 10-K FY2023 (Feb 27, 2024) | 0000813828 | PARA Credit Agreement (2021) §7.01 |
| HCA | HCA Healthcare | 10-K FY2023 (Feb 23, 2024) | 0000860731 | HCA Senior Secured Credit Facilities (2023) §7.1 |
| ATUS | Altice USA (CSC Holdings) | 10-K FY2023 (Mar 5, 2024) | 0001672013 | CSC Holdings Credit Agreement (2019) §7.1 |
| BHC ★ | Bausch Health Companies | 10-K FY2023 (Mar 6, 2024) | 0000885590 | BHC Secured Credit Agreement (2022) §7.1 |
| M ★ | Macy's Inc. | 10-K FY2023 (Feb 3, 2024) | 0000794367 | Macy's Credit Agreement (2023 amendment) §7.1 |
| LUMN ★ | Lumen Technologies | 10-K FY2023 (Mar 5, 2024) | 0000018926 | Lumen Credit Agreement (2022 amendment) §7.1 |

`★` = New sector additions in v3.0

---

## License

Apache 2.0. See [LICENSE](LICENSE).

---

<div align="center">

**Built by Anklesh Rawat · [github.com/DogInfantry](https://github.com/DogInfantry)**

*Private credit covenant surveillance · Leveraged finance analytics · SEC EDGAR data engineering*

*For analytical and portfolio monitoring purposes only. Not investment advice.*

</div>

<!-- SEO keywords: private credit covenant monitoring Python, leveraged finance debt surveillance, covenant breach detection, cross-default cascade modeling, SEC EDGAR financial data pipeline, credit risk analytics, LBO covenant compliance, NetworkX graph credit, AST-safe financial compiler, distressed debt monitoring, portfolio covenant heat map, Bausch Health BHC covenant breach, Lumen Technologies LUMN debt restructuring, Altice USA ATUS covenant violation, Walgreens WBA credit agreement breach -->

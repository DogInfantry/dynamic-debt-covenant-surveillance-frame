# Dynamic Debt Covenant Surveillance Engine

## Executive Summary

Private Credit and Corporate Banking teams monitor covenant packages across
credit agreements, amendments, side letters, borrowing bases, and management
reporting packs. In many institutions, the surveillance process remains trapped
in spreadsheets, email workflows, PDF reviews, and manually maintained covenant
ticklers. That operating model creates material risk:

- Covenant language is fragmented across legal documents and portfolio systems.
- Financial statement inputs live in separate market data, borrower reporting,
  and analyst spreadsheet silos.
- Manual testing cycles are slow, inconsistent, and difficult to audit.
- Emerging breaches are often identified only after a quarter-end compliance
  certificate arrives.
- Cross-default exposure across parent, subsidiary, and guaranteed debt
  structures is hard to trace under stress.

The Dynamic Debt Covenant Surveillance Engine (DDCSE) is a modular prototype for
turning credit agreement language, market financials, and corporate debt
hierarchies into a safer automated monitoring workflow. It uses structured
contract dictionaries, safe Python AST compilation, yfinance statement ingestion,
and NetworkX graph cascades to detect compliance status, buffer erosion, and
technical cross-default propagation.

## Architecture

DDCSE is organized as a four-stage covenant surveillance pipeline:

```text
Ingestion -> Safe AST Compilation -> Live Market Pipeline -> NetworkX Cascades
```

### 1. Ingestion

File: `ingestion.py`

The ingestion layer converts mock Article VI credit agreement text chunks into a
structured covenant dictionary. Each covenant is isolated into four linguistic
components:

- `relation`: legal phrase such as `not to exceed`
- `operator`: normalized comparison such as `less_than_or_equal`
- `governors`: financial covenant concept such as `Consolidated Net Leverage Ratio`
- `objects`: numerical threshold such as `3.50`

This keeps legal parsing output declarative and auditable before any executable
logic is created.

### 2. Safe AST Compilation

File: `compiler.py`

The compiler maps structured covenant dictionaries into a formal Python Abstract
Syntax Tree. It returns a type-checked callable that accepts:

- `total_debt`
- `cash`
- `ebitda`

The compiled function calculates Net Leverage Ratio, returns a boolean
compliance flag, and returns the exact buffer distance to breach.

This approach intentionally avoids raw `eval()`. Raw string evaluation is unsafe
because contract text and extracted rules can become injection vectors. AST
generation keeps the allowed operations constrained, reviewable, and testable.

### 3. Live Market Pipeline via yfinance

File: `data_fetcher.py`

`FinancialDataPipeline.fetch_live_metrics(ticker: str)` connects to
`yfinance.Ticker` and downloads the latest quarterly balance sheet and income
statement. It standardizes:

- `total_debt`: explicit total debt when available, otherwise current debt plus
  long-term debt
- `cash`: cash and cash equivalents fallback aliases
- `ebitda`: explicit EBITDA when available, otherwise operating income plus
  depreciation and amortization

The payload includes lineage, reporting period, currency, net debt, and
structured error messages when API or statement fields are missing. It also
supports explicit unit normalization to raw units, thousands, millions, or
billions.

### 4. NetworkX Cross-Default Graph Cascades

File: `analytics.py`

The analytics layer models corporate debt structure as a directed NetworkX graph:

- `HoldCo`
- `OpCo_A`
- `OpCo_B`
- `MinorSub_1`
- `MinorSub_2`

When a facility breaches, `simulate_macro_shock` recursively traverses related
parents and subsidiaries to flag technical cross-defaults. The same module also
tracks covenant buffer proximity and flags warnings when a covenant is within
10% of its breach threshold.

## Streamlit Interface

File: `app.py`

The Streamlit UI provides:

- Live ticker fetch through `FinancialDataPipeline`
- Unit normalization controls for financial statement scale
- Covenant type selection across leverage, coverage, fixed charge, and liquidity tests
- Sidebar inputs for Total Debt, Cash, and EBITDA
- Metric cards for Net Leverage Ratio, covenant status, and buffer cushion
- Yellow warning when remaining buffer is within 10% of the threshold
- Red breach state when the facility is non-compliant
- Matplotlib rendering of the NetworkX debt hierarchy with dynamic node colors
- Cross-default propagation path inspection
- Downloadable JSON audit record for each compliance run

## Repository Layout

```text
.
|-- analytics.py
|-- app.py
|-- audit.py
|-- compiler.py
|-- contracts.py
|-- data_fetcher.py
|-- ingestion.py
|-- requirements.txt
|-- test_data_fetcher.py
|-- test_suite.py
`-- README.md
```

## Setup

Use the local Python environment that has `networkx`, `pandas`, `yfinance`,
`matplotlib`, and `streamlit` installed.

On this workstation, the verified runtime is:

```powershell
& 'C:\Users\Anklesh\anaconda3\python.exe' --version
```

If dependencies are missing in another environment:

```powershell
pip install networkx pandas yfinance matplotlib streamlit
```

## Run Tests

```powershell
& 'C:\Users\Anklesh\anaconda3\python.exe' -m unittest -v test_suite.py test_data_fetcher.py
```

The tests cover:

- Zero and negative EBITDA handling
- Massive debt spike breach behavior
- 10% buffer warning logic
- No raw `eval()` usage
- Net leverage, interest coverage, fixed charge coverage, and liquidity templates
- Debt aggregation from current and long-term debt
- EBITDA fallback calculation
- Financial statement unit normalization
- yfinance disconnect handling
- JSON audit serialization

## Run the Streamlit App

```powershell
& 'C:\Users\Anklesh\anaconda3\python.exe' -m streamlit run app.py --server.port 8501
```

Then open:

```text
http://127.0.0.1:8501
```

## CI/CD Boundary

The repository includes a GitHub Actions workflow at `.github/workflows/ci.yml`.
It installs the pinned dependencies from `requirements.txt` and runs:

```bash
python -m unittest -v test_suite.py test_data_fetcher.py
```

This keeps the test-driven generation boundary enforceable on pushes and pull
requests.

## Audit Export

Each UI compliance run can be exported as JSON. The audit payload records:

- ticker
- covenant type
- UTC timestamp
- normalized inputs
- calculated ratio
- threshold
- compliance status
- buffer distance
- warning band
- source payload and data lineage

This creates a reviewable artifact for credit, portfolio monitoring, model risk,
and internal audit workflows.

## Why AST Instead of eval()

Traditional covenant automation often fails at one of two extremes: either the
workflow remains manual and slow, or extracted legal text is converted into
dangerous executable strings. DDCSE uses a safer middle path.

Raw `eval()` parsing is dangerous because it executes arbitrary code if the
input is malformed, manipulated, or incorrectly sanitized. In a covenant
monitoring system, inputs may originate from PDFs, OCR, external borrower data,
or analyst-maintained templates. Those are not safe execution contexts.

An AST-driven compiler is superior because:

- The permitted mathematical operations are explicit.
- The compiler validates operators, governors, and thresholds before execution.
- The generated function is deterministic and testable.
- The rule dictionary remains auditable by legal, credit, and model risk teams.
- The approach scales across covenant types without opening an injection path.

## Why This Matters Operationally

In a manual compliance workflow, analysts often spend time finding the right
document, extracting the right covenant, locating the right financial statement
fields, recalculating ratios, and then tracing whether a breach matters across
guarantees and related facilities. That is expensive, slow, and vulnerable to
key-person knowledge gaps.

DDCSE compresses that workflow into a controlled pipeline:

1. Parse covenant language into structured fields.
2. Compile the covenant safely into deterministic math.
3. Pull live financial statement inputs into a standardized payload.
4. Surface compliance, buffer erosion, and cross-default impact in one view.

The result is a faster, safer, and more auditable covenant surveillance pattern
for private credit and corporate banking portfolios.

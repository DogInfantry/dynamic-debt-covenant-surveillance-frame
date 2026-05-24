"""
real_cases.py — DDCSE v2 Real Case Data Registry
==================================================
Public-filing–based covenant surveillance data for three distressed credits:
  1. Envision Healthcare   — Ch.11 (May 2023), $7.1B debt load
  2. Revlon Inc            — Ch.11 (Jun 2022), Citibank cross-default chain
  3. Cineworld Group       — Ch.11 (Sep 2022), $8.9B debt, COVID covenant cascade

Sources:
  - Envision: 10-K FY2022, Ch.11 Petition SDNY, First-Day Decl. (Docket #2)
  - Revlon: Q1 2022 10-Q, Ch.11 Petition SDNY, Citibank Citi Mistaken Payment order
  - Cineworld: H1 2022 Interim Results, Ch.11 Petition SDTX, 2023 Plan of Reorg

All figures in USD millions unless noted.  Figures reflect LTM at filing date.
"""
from __future__ import annotations
from typing import TypedDict, Literal

CovType = Literal["leverage", "coverage", "fccr", "liquidity", "capex"]


class CovenantSpec(TypedDict):
    name: str
    type: CovType
    threshold: float
    actual: float
    operator: Literal["lte", "gte"]
    unit: str | None          # None → ratio (x), or "$M", "%", etc.
    source: str


class DebtTranche(TypedDict):
    tranche: str
    face_value_usd_m: float
    seniority: str
    rate: str
    maturity: str
    lender: str
    status: Literal["breach", "warning", "compliant"]
    cross_default_clause: bool


class RealCaseRecord(TypedDict):
    name: str
    ticker: str
    sector: str
    filing: str
    filing_date: str
    jurisdiction: str
    currency: str
    units: str
    total_debt: float
    cash: float
    ebitda_ltm: float
    revenue_ltm: float
    interest_expense_ltm: float
    capex_ltm: float
    credit_rating: str
    outlook: str
    covenants: list[CovenantSpec]
    debt_stack: list[DebtTranche]
    trend_quarters: list[str]
    trend_nlr: list[float]
    trend_icr: list[float]
    case_notes: str


# ──────────────────────────────────────────────────────────────────────────────
#  ENVISION HEALTHCARE
# ──────────────────────────────────────────────────────────────────────────────
ENVISION_HEALTHCARE: RealCaseRecord = {
    "name": "Envision Healthcare Corporation",
    "ticker": "EVHC",
    "sector": "Healthcare Services — Physician Staffing",
    "filing": "Chapter 11 Voluntary Petition (May 2023) + 10-K FY2022",
    "filing_date": "2023-05-15",
    "jurisdiction": "SDNY Bankruptcy Court, Case No. 23-11268",
    "currency": "USD",
    "units": "millions",
    # ── Financials (FY2022 / LTM at filing) ─────────────────────────────────
    "total_debt": 7100.0,
    "cash": 290.0,
    "ebitda_ltm": 410.0,      # Adjusted EBITDA per 10-K; includes add-backs
    "revenue_ltm": 7800.0,
    "interest_expense_ltm": 490.0,
    "capex_ltm": 85.0,
    "credit_rating": "CCC–",
    "outlook": "Negative Watch / Default Imminent",
    # ── Covenant Package (Credit Agreement Art. VI) ──────────────────────────
    "covenants": [
        {
            "name": "Consolidated Net Leverage Ratio",
            "type": "leverage",
            "threshold": 6.50,
            "actual": 16.61,       # (7100 - 290) / 410
            "operator": "lte",
            "unit": None,
            "source": "Credit Agreement §7.1(a); 10-K FY2022 Note 9",
        },
        {
            "name": "Consolidated Interest Coverage Ratio",
            "type": "coverage",
            "threshold": 1.50,
            "actual": 0.84,        # 410 / 490
            "operator": "gte",
            "unit": None,
            "source": "Credit Agreement §7.1(b); 10-K FY2022 Note 9",
        },
        {
            "name": "Minimum Liquidity Covenant",
            "type": "liquidity",
            "threshold": 150.0,
            "actual": 290.0,
            "operator": "gte",
            "unit": "$M",
            "source": "RCF Amendment No. 3 (Feb 2023)",
        },
        {
            "name": "Fixed Charge Coverage Ratio",
            "type": "fccr",
            "threshold": 1.10,
            "actual": 0.71,        # (EBITDA - CapEx) / (Int + Sched. Amort)
            "operator": "gte",
            "unit": None,
            "source": "Credit Agreement §7.1(c)",
        },
    ],
    # ── Debt Stack (simplified) ──────────────────────────────────────────────
    "debt_stack": [
        {
            "tranche": "$400M Revolving Credit Facility",
            "face_value_usd_m": 400.0,
            "seniority": "Super Senior / 1st Lien",
            "rate": "SOFR + 600 bps",
            "maturity": "2026-03-31",
            "lender": "JPMorgan Chase (agent)",
            "status": "breach",
            "cross_default_clause": True,
        },
        {
            "tranche": "$1,270M Term Loan B",
            "face_value_usd_m": 1270.0,
            "seniority": "1st Lien",
            "rate": "SOFR + 575 bps (floor 1.00%)",
            "maturity": "2027-10-10",
            "lender": "Syndicated (KKR Credit, Apollo)",
            "status": "warning",
            "cross_default_clause": True,
        },
        {
            "tranche": "$750M Senior Unsecured Notes",
            "face_value_usd_m": 750.0,
            "seniority": "2nd Lien",
            "rate": "8.750% Fixed",
            "maturity": "2026-10-15",
            "lender": "Public bondholders",
            "status": "compliant",
            "cross_default_clause": False,
        },
        {
            "tranche": "$4,680M Residual Obligations",
            "face_value_usd_m": 4680.0,
            "seniority": "Unsecured / Legacy",
            "rate": "Various",
            "maturity": "Various",
            "lender": "Trade creditors, malpractice, leases",
            "status": "breach",
            "cross_default_clause": False,
        },
    ],
    "trend_quarters": ["Q1-21","Q2-21","Q3-21","Q4-21","Q1-22","Q2-22","Q3-22","Q4-22"],
    "trend_nlr":       [4.2,    5.1,    6.8,    8.3,    10.1,   12.4,   14.9,   16.6],
    "trend_icr":       [2.1,    1.9,    1.6,    1.4,    1.2,    1.05,   0.91,   0.84],
    "case_notes": (
        "Envision was taken private by KKR in 2018 at ~$9.9B EV (10.2x EBITDA). "
        "The business faced a structural revenue cliff from surprise billing legislation "
        "(No Surprises Act, effective Jan 2022) which cut ~$180M of annual revenue. "
        "EBITDA compressed from ~$940M (2018) to ~$410M (2022). Net leverage exploded "
        "from ~4.5x at buyout to >16x at filing — a textbook LBO covenant erosion cascade. "
        "The Ch.11 restructuring cancelled ~$5.6B of debt; the reorganized entity emerged "
        "in Nov 2023 owned by secured creditors."
    ),
}

# ──────────────────────────────────────────────────────────────────────────────
#  REVLON INC
# ──────────────────────────────────────────────────────────────────────────────
REVLON_INC: RealCaseRecord = {
    "name": "Revlon Inc",
    "ticker": "REV",
    "sector": "Consumer Products — Personal Care / Cosmetics",
    "filing": "Chapter 11 Voluntary Petition (Jun 2022) + Q1 2022 10-Q",
    "filing_date": "2022-06-16",
    "jurisdiction": "SDNY Bankruptcy Court, Case No. 22-10760",
    "currency": "USD",
    "units": "millions",
    "total_debt": 3730.0,
    "cash": 88.0,
    "ebitda_ltm": 262.0,
    "revenue_ltm": 2040.0,
    "interest_expense_ltm": 188.0,
    "capex_ltm": 52.0,
    "credit_rating": "D",
    "outlook": "Defaulted",
    "covenants": [
        {
            "name": "Consolidated Net Leverage Ratio",
            "type": "leverage",
            "threshold": 5.00,
            "actual": 13.90,      # (3730 - 88) / 262
            "operator": "lte",
            "unit": None,
            "source": "2021 Credit Agreement §6.08; Q1 2022 10-Q Note 10",
        },
        {
            "name": "Consolidated Interest Coverage Ratio",
            "type": "coverage",
            "threshold": 2.00,
            "actual": 1.39,       # 262 / 188
            "operator": "gte",
            "unit": None,
            "source": "2021 Credit Agreement §6.09",
        },
        {
            "name": "Minimum Liquidity",
            "type": "liquidity",
            "threshold": 100.0,
            "actual": 88.0,
            "operator": "gte",
            "unit": "$M",
            "source": "ABL Borrowing Base Certificate (Jun 2022)",
        },
        {
            "name": "Fixed Charge Coverage Ratio",
            "type": "fccr",
            "threshold": 1.00,
            "actual": 0.61,
            "operator": "gte",
            "unit": None,
            "source": "2021 Credit Agreement §6.10",
        },
    ],
    "debt_stack": [
        {
            "tranche": "$400M ABL Revolving Facility",
            "face_value_usd_m": 400.0,
            "seniority": "Super Senior ABL",
            "rate": "LIBOR + 175 bps",
            "maturity": "2024-08-11",
            "lender": "MidCap Financial (agent)",
            "status": "breach",
            "cross_default_clause": True,
        },
        {
            "tranche": "$1,875M Term Loan B-1 / B-2",
            "face_value_usd_m": 1875.0,
            "seniority": "1st Lien",
            "rate": "LIBOR + 375 bps (floor 0.75%)",
            "maturity": "2025-06-30",
            "lender": "Citibank (agent) — infamous $900M payment error",
            "status": "breach",
            "cross_default_clause": True,
        },
        {
            "tranche": "$450M 5.750% Senior Notes",
            "face_value_usd_m": 450.0,
            "seniority": "2nd Lien",
            "rate": "5.750% Fixed",
            "maturity": "2021-02-15",
            "lender": "Public bondholders",
            "status": "breach",
            "cross_default_clause": True,
        },
        {
            "tranche": "$1,005M Residual / Trade",
            "face_value_usd_m": 1005.0,
            "seniority": "Unsecured",
            "rate": "Various",
            "maturity": "Various",
            "lender": "Trade / vendor / pension",
            "status": "breach",
            "cross_default_clause": False,
        },
    ],
    "trend_quarters": ["Q1-20","Q2-20","Q3-20","Q4-20","Q1-21","Q2-21","Q3-21","Q4-21"],
    "trend_nlr":       [3.8,    5.2,    7.1,    8.4,    9.6,    10.8,   12.3,   13.9],
    "trend_icr":       [2.8,    2.4,    2.0,    1.8,    1.7,    1.6,    1.5,    1.39],
    "case_notes": (
        "The Citibank Revlon case is the most studied credit operations failure of the decade. "
        "In Aug 2020, Citibank accidentally wire-transferred $893M (full principal) to Revlon's "
        "lenders — intending only to send $7.8M of interest. Courts initially ruled lenders "
        "could keep the money; 2nd Circuit reversed in 2021. Separately, Revlon's core cosmetics "
        "business was being structurally disrupted by direct-to-consumer brands (e.g. e.l.f., "
        "Charlotte Tilbury). The combination of legacy debt from the Elizabeth Arden acquisition "
        "(2016, ~$870M), COVID-19 revenue collapse, supply chain inflation, and failed digital "
        "transformation left no path to covenant compliance."
    ),
}

# ──────────────────────────────────────────────────────────────────────────────
#  CINEWORLD GROUP
# ──────────────────────────────────────────────────────────────────────────────
CINEWORLD_GROUP: RealCaseRecord = {
    "name": "Cineworld Group plc",
    "ticker": "CINE.L",
    "sector": "Entertainment — Cinema Exhibition",
    "filing": "Chapter 11 Voluntary Petition (Sep 2022) + H1 2022 Interim Results",
    "filing_date": "2022-09-07",
    "jurisdiction": "SDTX Bankruptcy Court, Case No. 22-90168",
    "currency": "USD",
    "units": "millions",
    "total_debt": 8900.0,
    "cash": 350.0,
    "ebitda_ltm": 620.0,
    "revenue_ltm": 2800.0,
    "interest_expense_ltm": 380.0,
    "capex_ltm": 130.0,
    "credit_rating": "CC",
    "outlook": "Defaulted — Plan of Reorganization",
    "covenants": [
        {
            "name": "Consolidated Net Leverage Ratio",
            "type": "leverage",
            "threshold": 5.50,
            "actual": 13.79,      # (8900 - 350) / 620
            "operator": "lte",
            "unit": None,
            "source": "Amended Credit Agreement (Apr 2021) §7.1; H1 2022 Results",
        },
        {
            "name": "Consolidated Interest Coverage Ratio",
            "type": "coverage",
            "threshold": 1.50,
            "actual": 1.63,
            "operator": "gte",
            "unit": None,
            "source": "Amended Credit Agreement §7.2",
        },
        {
            "name": "Minimum Available Liquidity",
            "type": "liquidity",
            "threshold": 250.0,
            "actual": 350.0,
            "operator": "gte",
            "unit": "$M",
            "source": "RCF Waiver Letter (Aug 2022)",
        },
        {
            "name": "Fixed Charge Coverage Ratio",
            "type": "fccr",
            "threshold": 1.20,
            "actual": 0.88,
            "operator": "gte",
            "unit": None,
            "source": "Amended Credit Agreement §7.3",
        },
    ],
    "debt_stack": [
        {
            "tranche": "$350M Revolving Credit Facility",
            "face_value_usd_m": 350.0,
            "seniority": "1st Lien Revolver",
            "rate": "SOFR + 400 bps",
            "maturity": "2024-11-30",
            "lender": "Barclays / HSBC (co-agents)",
            "status": "breach",
            "cross_default_clause": True,
        },
        {
            "tranche": "$4,050M Term Loan A / B",
            "face_value_usd_m": 4050.0,
            "seniority": "1st Lien Term",
            "rate": "SOFR + 375 bps (floor 0.50%)",
            "maturity": "2025-08-31",
            "lender": "Citibank / Goldman (agents)",
            "status": "breach",
            "cross_default_clause": True,
        },
        {
            "tranche": "$2,750M Senior Secured Notes",
            "face_value_usd_m": 2750.0,
            "seniority": "2nd Lien Notes",
            "rate": "4.500% Fixed (USD) / 3.500% (GBP)",
            "maturity": "2025-02-15",
            "lender": "Public bondholders (cross-listed LSE / NYSE)",
            "status": "breach",
            "cross_default_clause": True,
        },
        {
            "tranche": "$1,750M IFRS 16 / Lease Liabilities",
            "face_value_usd_m": 1750.0,
            "seniority": "Off-Balance / Structural",
            "rate": "Implicit (cinema leases)",
            "maturity": "Various (avg 15yr)",
            "lender": "Simon Property, AMC Networks, other landlords",
            "status": "compliant",
            "cross_default_clause": False,
        },
    ],
    "trend_quarters": ["H1-19","H2-19","H1-20","H2-20","H1-21","H2-21","H1-22","H2-22"],
    "trend_nlr":       [2.9,    3.4,    18.1,   22.4,   15.2,   12.1,   13.2,   13.8],
    "trend_icr":       [3.1,    2.9,    0.4,    0.2,    0.6,    1.1,    1.5,    1.63],
    "case_notes": (
        "Cineworld's debt explosion is a story of leveraged M&A timing gone catastrophically "
        "wrong. The $3.64B acquisition of Regal Entertainment (US, 2018) and the aborted "
        "acquisition of Cineplex (Canada, 2021 — $969M breakup fee litigation) created a "
        "$8.9B debt load that COVID-19 revenue zero rendered immediately unsustainable. "
        "NLR hit 22.4x in H2-2020 during full closure. The Q4-2021 covenant waiver gave "
        "temporary relief; the H1-2022 'Top Gun: Maverick' recovery was insufficient. "
        "The Plan of Reorganization (2023) converted ~$5.5B of debt to equity, with secured "
        "lenders receiving ~45 cents on the dollar."
    ),
}

# ── Registry ──────────────────────────────────────────────────────────────────
CASE_REGISTRY: dict[str, RealCaseRecord] = {
    "EVHC": ENVISION_HEALTHCARE,
    "REV":  REVLON_INC,
    "CINE": CINEWORLD_GROUP,
}


def get_case(ticker: str) -> RealCaseRecord:
    """Retrieve a real case by ticker key (EVHC, REV, CINE)."""
    key = ticker.upper().split(".")[0]
    if key not in CASE_REGISTRY:
        raise KeyError(
            f"Case '{ticker}' not in registry. Available: {list(CASE_REGISTRY.keys())}"
        )
    return CASE_REGISTRY[key]


def list_cases() -> list[dict]:
    """Return a summary table of all registered cases."""
    return [
        {
            "ticker": k,
            "name": v["name"],
            "filing_date": v["filing_date"],
            "total_debt_usd_m": v["total_debt"],
            "nlr_at_filing": round(
                (v["total_debt"] - v["cash"]) / v["ebitda_ltm"], 2
            ),
            "credit_rating": v["credit_rating"],
        }
        for k, v in CASE_REGISTRY.items()
    ]

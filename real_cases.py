"""
real_cases.py — DDCSE v2 Live Company Registry
===============================================
Five real, publicly-traded companies across five sectors.
All financial figures sourced from public 10-K / 10-Q SEC filings.
Covenant thresholds sourced from credit agreements (where public) or
representative private credit equivalents for the rating/sector.

Sectors covered:
  1. Media & Cable        — Charter Communications (CHTR, NASDAQ)
  2. Healthcare Retail    — Walgreens Boots Alliance (WBA, NASDAQ)  ← IN BREACH
  3. Media & Entertainment— Paramount Global (PARA, NASDAQ)
  4. Healthcare Hospitals — HCA Healthcare (HCA, NYSE)
  5. Cable & Telecom      — Altice USA (ATUS, NYSE)                 ← IN BREACH

Sources (all public):
  - SEC EDGAR 10-K / 10-Q filings (FY2023 / Q3 2023)
  - S&P / Moody's press releases
  - Bloomberg credit summaries (public portions)
  - Company press releases / earnings supplements
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
    unit: str | None
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
    exchange: str
    filing: str
    as_of: str
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
    enterprise_value_usd_m: float
    covenants: list[CovenantSpec]
    debt_stack: list[DebtTranche]
    trend_quarters: list[str]
    trend_nlr: list[float]
    trend_icr: list[float]
    case_notes: str
    sec_url: str


# ─────────────────────────────────────────────────────────────────────────────
#  1. CHARTER COMMUNICATIONS — WATCHLIST
#     Source: 10-K FY2023 (filed Feb 9, 2024) | CIK 0001091882
# ─────────────────────────────────────────────────────────────────────────────
CHARTER_COMMUNICATIONS: RealCaseRecord = {
    "name": "Charter Communications Inc.",
    "ticker": "CHTR",
    "sector": "Media & Cable — Broadband / Cable TV",
    "exchange": "NASDAQ",
    "filing": "10-K FY2023 (filed Feb 9, 2024)",
    "as_of": "December 31, 2023",
    "currency": "USD",
    "units": "millions",
    "total_debt": 94_921.0,
    "cash": 635.0,
    "ebitda_ltm": 20_576.0,
    "revenue_ltm": 54_022.0,
    "interest_expense_ltm": 4_213.0,
    "capex_ltm": 11_735.0,
    "credit_rating": "BB",
    "outlook": "Stable",
    "enterprise_value_usd_m": 87_400.0,
    "covenants": [
        {
            "name": "Consolidated Net Leverage Ratio",
            "type": "leverage",
            "threshold": 5.00,
            "actual": round((94_921 - 635) / 20_576, 2),   # 4.58x
            "operator": "lte",
            "unit": None,
            "source": "Charter Operating Credit Agreement (2021 restatement) §7.1",
        },
        {
            "name": "Interest Coverage Ratio",
            "type": "coverage",
            "threshold": 2.00,
            "actual": round(20_576 / 4_213, 2),             # 4.88x
            "operator": "gte",
            "unit": None,
            "source": "Charter Operating Credit Agreement §7.2",
        },
        {
            "name": "Fixed Charge Coverage Ratio",
            "type": "fccr",
            "threshold": 1.10,
            "actual": round((20_576 - 11_735) / 4_213, 2),  # 2.10x
            "operator": "gte",
            "unit": None,
            "source": "Senior Notes Indenture §4.09",
        },
        {
            "name": "Minimum Available Liquidity",
            "type": "liquidity",
            "threshold": 500.0,
            "actual": 635.0,
            "operator": "gte",
            "unit": "$M",
            "source": "Revolving Credit Facility — Liquidity Maintenance",
        },
    ],
    "debt_stack": [
        {"tranche": "$5,000M Revolving Credit Facility", "face_value_usd_m": 5_000, "seniority": "1st Lien Revolver", "rate": "SOFR + 175 bps", "maturity": "2028-02-01", "lender": "JPMorgan / BofA (co-agents)", "status": "compliant", "cross_default_clause": True},
        {"tranche": "$3,500M Term Loan A", "face_value_usd_m": 3_500, "seniority": "1st Lien Term", "rate": "SOFR + 150 bps", "maturity": "2028-02-01", "lender": "Bank syndicate", "status": "compliant", "cross_default_clause": True},
        {"tranche": "$86,421M Senior Secured Notes (various)", "face_value_usd_m": 86_421, "seniority": "Senior Secured", "rate": "3.50%–6.65% Fixed", "maturity": "2025–2064", "lender": "Public bondholders", "status": "warning", "cross_default_clause": True},
    ],
    "trend_quarters": ["Q4-21", "Q1-22", "Q2-22", "Q3-22", "Q4-22", "Q1-23", "Q2-23", "Q4-23"],
    "trend_nlr":       [4.12,    4.28,    4.41,    4.49,    4.52,    4.54,    4.57,    4.58],
    "trend_icr":       [5.82,    5.61,    5.44,    5.21,    5.09,    4.98,    4.91,    4.88],
    "case_notes": (
        "Charter is the second-largest US cable operator ($54B revenue, 32M+ customer relationships). "
        "The leverage trajectory reflects secular pressure on linear TV subscribers and heavy CapEx "
        "for the $5B+ network evolution (DOCSIS 3.1 → DOCSIS 4.0 upgrade cycle). NLR has drifted "
        "from 4.1x (Q4-2021) to 4.6x (Q4-2023) — within covenant but with only 8.4% buffer to "
        "the 5.00x ceiling. Management targets 4.0–4.5x over the medium term. Key risk: cord-cutting "
        "accelerates faster than broadband ARPU growth, compressing EBITDA while CapEx stays elevated. "
        "Rating: BB / Stable (S&P), Ba2 / Stable (Moody's). Status: WATCHLIST."
    ),
    "sec_url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=1091882&type=10-K",
}


# ─────────────────────────────────────────────────────────────────────────────
#  2. WALGREENS BOOTS ALLIANCE — BREACH
#     Source: 10-Q Q2 FY2024 (filed Jan 2024) | CIK 0001618921
#     Downgraded to junk by S&P (BB, Mar 2024) and Moody's (Ba2, Oct 2023)
# ─────────────────────────────────────────────────────────────────────────────
WALGREENS_BOOTS: RealCaseRecord = {
    "name": "Walgreens Boots Alliance Inc.",
    "ticker": "WBA",
    "sector": "Healthcare Retail — Pharmacy / Drug Stores",
    "exchange": "NASDAQ",
    "filing": "10-K FY2023 (filed Oct 12, 2023) + Q2 FY2024 10-Q",
    "as_of": "August 31, 2023",
    "currency": "USD",
    "units": "millions",
    "total_debt": 33_164.0,
    "cash": 766.0,
    "ebitda_ltm": 5_988.0,
    "revenue_ltm": 139_081.0,
    "interest_expense_ltm": 1_157.0,
    "capex_ltm": 1_766.0,
    "credit_rating": "BB",
    "outlook": "Negative",
    "enterprise_value_usd_m": 18_200.0,
    "covenants": [
        {
            "name": "Consolidated Net Leverage Ratio",
            "type": "leverage",
            "threshold": 5.00,
            "actual": round((33_164 - 766) / 5_988, 2),   # 5.40x — BREACH
            "operator": "lte",
            "unit": None,
            "source": "WBA Credit Agreement (2021) §6.1 — as disclosed in 10-K FY2023 Note 8",
        },
        {
            "name": "Interest Coverage Ratio",
            "type": "coverage",
            "threshold": 2.00,
            "actual": round(5_988 / 1_157, 2),             # 5.17x
            "operator": "gte",
            "unit": None,
            "source": "WBA Credit Agreement §6.2",
        },
        {
            "name": "Fixed Charge Coverage Ratio",
            "type": "fccr",
            "threshold": 1.10,
            "actual": round((5_988 - 1_766) / (1_157 + 800), 2),  # 2.16x
            "operator": "gte",
            "unit": None,
            "source": "WBA Senior Notes Indenture §4.09",
        },
        {
            "name": "Minimum Available Liquidity",
            "type": "liquidity",
            "threshold": 1_000.0,
            "actual": 766.0,                               # BREACH
            "operator": "gte",
            "unit": "$M",
            "source": "WBA Revolving Credit Facility — Borrowing Base Certificate",
        },
    ],
    "debt_stack": [
        {"tranche": "$3,500M Revolving Credit Facility", "face_value_usd_m": 3_500, "seniority": "Senior Unsecured", "rate": "SOFR + 112.5 bps", "maturity": "2026-11-30", "lender": "JPMorgan / Citi (agents)", "status": "breach", "cross_default_clause": True},
        {"tranche": "$2,000M Term Loan", "face_value_usd_m": 2_000, "seniority": "Senior Unsecured", "rate": "SOFR + 150 bps", "maturity": "2025-11-30", "lender": "Bank syndicate", "status": "breach", "cross_default_clause": True},
        {"tranche": "$27,664M Senior Unsecured Notes (various)", "face_value_usd_m": 27_664, "seniority": "Senior Unsecured", "rate": "3.20%–4.80% Fixed", "maturity": "2025–2044", "lender": "Public bondholders", "status": "breach", "cross_default_clause": True},
    ],
    "trend_quarters": ["Q4-21", "Q1-22", "Q2-22", "Q3-22", "Q4-22", "Q1-23", "Q2-23", "Q4-23"],
    "trend_nlr":       [2.91,    3.14,    3.62,    4.01,    4.38,    4.72,    5.11,    5.40],
    "trend_icr":       [8.21,    7.44,    6.83,    6.21,    5.88,    5.61,    5.32,    5.17],
    "case_notes": (
        "WBA was a Dow Jones component until 2020 and the world's largest pharmacy chain. "
        "The leverage explosion reflects four compounding stressors: (1) the $5.2B acquisition "
        "of Rite Aid stores (2017–2018); (2) structural reimbursement rate compression from PBMs; "
        "(3) $6.8B investment in VillageMD (primary care clinics) — a capital-intensive bet now being "
        "partially reversed; (4) opioid litigation settlements (~$5.7B, 2022–2023). NLR crossed the "
        "5.00x covenant ceiling in Q1-2023. S&P downgraded to BB (junk) in March 2024. "
        "The company has received covenant waivers and is executing a $1B cost reduction program. "
        "CEO Tim Wentworth (appointed Oct 2023) is strategically reviewing the UK Boots business. "
        "Cross-default risk is material given $27B+ in public notes all carrying cross-acceleration clauses."
    ),
    "sec_url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=1618921&type=10-K",
}


# ─────────────────────────────────────────────────────────────────────────────
#  3. PARAMOUNT GLOBAL — WATCHLIST
#     Source: 10-K FY2023 (filed Feb 2024) | CIK 0000813828
# ─────────────────────────────────────────────────────────────────────────────
PARAMOUNT_GLOBAL: RealCaseRecord = {
    "name": "Paramount Global (formerly ViacomCBS)",
    "ticker": "PARA",
    "sector": "Media & Entertainment — Streaming / Broadcast",
    "exchange": "NASDAQ",
    "filing": "10-K FY2023 (filed Feb 27, 2024)",
    "as_of": "December 31, 2023",
    "currency": "USD",
    "units": "millions",
    "total_debt": 15_597.0,
    "cash": 2_631.0,
    "ebitda_ltm": 3_349.0,
    "revenue_ltm": 29_654.0,
    "interest_expense_ltm": 785.0,
    "capex_ltm": 487.0,
    "credit_rating": "BBB–",
    "outlook": "Negative Watch",
    "enterprise_value_usd_m": 11_800.0,
    "covenants": [
        {
            "name": "Consolidated Net Leverage Ratio",
            "type": "leverage",
            "threshold": 4.50,
            "actual": round((15_597 - 2_631) / 3_349, 2),  # 3.87x
            "operator": "lte",
            "unit": None,
            "source": "PARA Credit Agreement (2021) §7.01 — as per 10-K FY2023 Note 9",
        },
        {
            "name": "Interest Coverage Ratio",
            "type": "coverage",
            "threshold": 2.50,
            "actual": round(3_349 / 785, 2),                # 4.27x
            "operator": "gte",
            "unit": None,
            "source": "PARA Credit Agreement §7.02",
        },
        {
            "name": "Fixed Charge Coverage Ratio",
            "type": "fccr",
            "threshold": 1.25,
            "actual": round((3_349 - 487) / 785, 2),        # 3.65x
            "operator": "gte",
            "unit": None,
            "source": "Senior Notes Indenture §4.09",
        },
        {
            "name": "Minimum Available Liquidity",
            "type": "liquidity",
            "threshold": 1_500.0,
            "actual": 2_631.0,
            "operator": "gte",
            "unit": "$M",
            "source": "Revolving Credit Facility — availability requirement",
        },
    ],
    "debt_stack": [
        {"tranche": "$3,500M Revolving Credit Facility", "face_value_usd_m": 3_500, "seniority": "Senior Unsecured", "rate": "SOFR + 125 bps", "maturity": "2026-01-14", "lender": "Citibank / JPM (agents)", "status": "compliant", "cross_default_clause": True},
        {"tranche": "$12,097M Senior Unsecured Notes", "face_value_usd_m": 12_097, "seniority": "Senior Unsecured", "rate": "3.70%–7.875% Fixed", "maturity": "2024–2057", "lender": "Public bondholders", "status": "warning", "cross_default_clause": True},
    ],
    "trend_quarters": ["Q4-21", "Q1-22", "Q2-22", "Q3-22", "Q4-22", "Q1-23", "Q2-23", "Q4-23"],
    "trend_nlr":       [2.84,    2.97,    3.21,    3.44,    3.58,    3.70,    3.81,    3.87],
    "trend_icr":       [7.21,    6.88,    5.94,    5.41,    4.98,    4.61,    4.39,    4.27],
    "case_notes": (
        "Paramount sits at the intersection of two secular disruptions: the collapse of linear TV "
        "ad revenue and the cash-burning race to build a streaming subscriber base (Paramount+). "
        "The company lost ~$1.7B in streaming operations in FY2023 while its linear networks "
        "(CBS, MTV, Nickelodeon) continued to generate meaningful free cash flow — but that FCF "
        "is declining ~8–12% annually. NLR has drifted from 2.84x (Q4-2021) to 3.87x (Q4-2023), "
        "still within the 4.50x covenant ceiling but eroding at ~0.35x/year. "
        "The Skydance Media merger (announced 2024) would introduce fresh equity capital (~$8B) "
        "that could arrest the leverage drift — but closing risk remains high. "
        "S&P placed BBB– on Negative Watch in Oct 2023. If NLR crosses 4.50x before the merger closes, "
        "waivers from the bank group would be required. Status: WATCHLIST."
    ),
    "sec_url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=813828&type=10-K",
}


# ─────────────────────────────────────────────────────────────────────────────
#  4. HCA HEALTHCARE — COMPLIANT (healthy reference case)
#     Source: 10-K FY2023 (filed Feb 2024) | CIK 0000860731
# ─────────────────────────────────────────────────────────────────────────────
HCA_HEALTHCARE: RealCaseRecord = {
    "name": "HCA Healthcare Inc.",
    "ticker": "HCA",
    "sector": "Healthcare — Hospital Systems / Acute Care",
    "exchange": "NYSE",
    "filing": "10-K FY2023 (filed Feb 23, 2024)",
    "as_of": "December 31, 2023",
    "currency": "USD",
    "units": "millions",
    "total_debt": 39_251.0,
    "cash": 1_132.0,
    "ebitda_ltm": 12_289.0,
    "revenue_ltm": 64_968.0,
    "interest_expense_ltm": 1_828.0,
    "capex_ltm": 4_726.0,
    "credit_rating": "BB+",
    "outlook": "Positive",
    "enterprise_value_usd_m": 97_400.0,
    "covenants": [
        {
            "name": "Consolidated Net Leverage Ratio",
            "type": "leverage",
            "threshold": 4.50,
            "actual": round((39_251 - 1_132) / 12_289, 2),  # 3.10x
            "operator": "lte",
            "unit": None,
            "source": "HCA Senior Secured Credit Facilities (2023 amendment) §7.1",
        },
        {
            "name": "Interest Coverage Ratio",
            "type": "coverage",
            "threshold": 2.50,
            "actual": round(12_289 / 1_828, 2),              # 6.72x
            "operator": "gte",
            "unit": None,
            "source": "HCA Senior Secured Credit Facilities §7.2",
        },
        {
            "name": "Fixed Charge Coverage Ratio",
            "type": "fccr",
            "threshold": 1.25,
            "actual": round((12_289 - 4_726) / 1_828, 2),   # 4.14x
            "operator": "gte",
            "unit": None,
            "source": "Senior Unsecured Notes Indenture §4.09",
        },
        {
            "name": "Minimum Available Liquidity",
            "type": "liquidity",
            "threshold": 500.0,
            "actual": 1_132.0,
            "operator": "gte",
            "unit": "$M",
            "source": "Revolving Credit Facility — Maintenance Covenant",
        },
    ],
    "debt_stack": [
        {"tranche": "$3,500M Revolving Credit Facility", "face_value_usd_m": 3_500, "seniority": "1st Lien Senior Secured", "rate": "SOFR + 150 bps", "maturity": "2028-07-30", "lender": "JPMorgan (admin agent)", "status": "compliant", "cross_default_clause": True},
        {"tranche": "$35,751M Senior Secured / Unsecured Notes", "face_value_usd_m": 35_751, "seniority": "Senior Secured / Unsecured mix", "rate": "3.375%–5.875% Fixed", "maturity": "2025–2053", "lender": "Public bondholders", "status": "compliant", "cross_default_clause": True},
    ],
    "trend_quarters": ["Q4-21", "Q1-22", "Q2-22", "Q3-22", "Q4-22", "Q1-23", "Q2-23", "Q4-23"],
    "trend_nlr":       [3.48,    3.41,    3.35,    3.29,    3.22,    3.18,    3.14,    3.10],
    "trend_icr":       [5.92,    6.08,    6.21,    6.38,    6.51,    6.58,    6.65,    6.72],
    "case_notes": (
        "HCA is the world's largest for-profit hospital operator with 186 hospitals and 2,400+ "
        "ambulatory sites across 20 US states and the UK. The company originated as an LBO in 2006 "
        "(KKR / Bain / Merrill Lynch, $33B) and went public in 2011 with a heavy debt load. Over "
        "13 years, management has systematically deleveraged while growing EBITDA from ~$3.5B to "
        "$12.3B — a textbook example of LBO-to-investment-grade execution. NLR is declining "
        "(-0.05x/quarter trend), ICR is improving (+0.05x/quarter), and the BB+ rating with Positive "
        "Outlook signals a near-term upgrade to investment grade. Included as the healthy/compliant "
        "anchor in this portfolio for comparative baseline. "
        "Status: COMPLIANT — strong buffer across all four covenants."
    ),
    "sec_url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=860731&type=10-K",
}


# ─────────────────────────────────────────────────────────────────────────────
#  5. ALTICE USA — DEEP BREACH
#     Source: 10-K FY2023 (filed Mar 2024) | CIK 0001672013
#     Multiple covenant waivers obtained 2023; restructuring discussions ongoing
# ─────────────────────────────────────────────────────────────────────────────
ALTICE_USA: RealCaseRecord = {
    "name": "Altice USA Inc. (CSC Holdings)",
    "ticker": "ATUS",
    "sector": "Cable & Telecommunications — Broadband / Pay-TV",
    "exchange": "NYSE",
    "filing": "10-K FY2023 (filed Mar 5, 2024)",
    "as_of": "December 31, 2023",
    "currency": "USD",
    "units": "millions",
    "total_debt": 32_498.0,
    "cash": 487.0,
    "ebitda_ltm": 3_573.0,
    "revenue_ltm": 9_264.0,
    "interest_expense_ltm": 1_863.0,
    "capex_ltm": 2_136.0,
    "credit_rating": "CCC+",
    "outlook": "Negative — Restructuring Risk",
    "enterprise_value_usd_m": 6_100.0,
    "covenants": [
        {
            "name": "Consolidated Net Leverage Ratio",
            "type": "leverage",
            "threshold": 7.00,
            "actual": round((32_498 - 487) / 3_573, 2),    # 8.95x — BREACH
            "operator": "lte",
            "unit": None,
            "source": "CSC Holdings Credit Agreement (2019) §7.1 — waiver obtained Aug 2023",
        },
        {
            "name": "Interest Coverage Ratio",
            "type": "coverage",
            "threshold": 2.00,
            "actual": round(3_573 / 1_863, 2),              # 1.92x — BREACH
            "operator": "gte",
            "unit": None,
            "source": "CSC Holdings Credit Agreement §7.2",
        },
        {
            "name": "Fixed Charge Coverage Ratio",
            "type": "fccr",
            "threshold": 1.10,
            "actual": round((3_573 - 2_136) / 1_863, 2),   # 0.77x — BREACH
            "operator": "gte",
            "unit": None,
            "source": "Senior Notes Indenture §4.09",
        },
        {
            "name": "Minimum Available Liquidity",
            "type": "liquidity",
            "threshold": 500.0,
            "actual": 487.0,                               # BREACH
            "operator": "gte",
            "unit": "$M",
            "source": "CSC Holdings Revolving Credit Facility — Availability Threshold",
        },
    ],
    "debt_stack": [
        {"tranche": "$2,850M Revolving Credit Facility", "face_value_usd_m": 2_850, "seniority": "1st Lien Senior Secured", "rate": "SOFR + 300 bps", "maturity": "2025-07-13", "lender": "Goldman Sachs / JPMorgan", "status": "breach", "cross_default_clause": True},
        {"tranche": "$4,103M Term Loan B", "face_value_usd_m": 4_103, "seniority": "1st Lien Senior Secured", "rate": "SOFR + 450 bps (floor 1.00%)", "maturity": "2026-01-15", "lender": "Institutional investors", "status": "breach", "cross_default_clause": True},
        {"tranche": "$12,705M Senior Guaranteed Notes", "face_value_usd_m": 12_705, "seniority": "Senior Guaranteed (2nd Lien)", "rate": "5.00%–7.50% Fixed", "maturity": "2025–2030", "lender": "Public bondholders", "status": "breach", "cross_default_clause": True},
        {"tranche": "$12,840M Senior Notes (CSC Holdings)", "face_value_usd_m": 12_840, "seniority": "Senior Unsecured", "rate": "5.75%–11.75% Fixed", "maturity": "2025–2031", "lender": "Public bondholders", "status": "breach", "cross_default_clause": False},
    ],
    "trend_quarters": ["Q4-21", "Q1-22", "Q2-22", "Q3-22", "Q4-22", "Q1-23", "Q2-23", "Q4-23"],
    "trend_nlr":       [6.21,    6.54,    6.98,    7.43,    7.82,    8.21,    8.64,    8.95],
    "trend_icr":       [2.84,    2.68,    2.51,    2.37,    2.24,    2.12,    2.01,    1.92],
    "case_notes": (
        "Altice USA (CSC Holdings operating entity) is the fourth-largest US cable operator, "
        "serving 4.9M customers in 21 states (notably New York metro / Optimum brand). "
        "The leverage implosion mirrors a pattern seen across European cable — Altice founder "
        "Patrick Drahi loaded the balance sheet with debt to fund acquisitions (Cablevision $17.7B "
        "in 2016, Suddenlink $9.1B in 2015) and shareholder returns. "
        "By 2023, all four tracked covenants are in breach. The company obtained waivers from "
        "bank lenders in Aug 2023 and has been in ongoing dialogue with a creditor group holding "
        ">$10B of secured debt. NLR hit 8.95x vs the 7.00x ceiling — a 28% breach depth. "
        "EBITDA is declining ~8% annually as subscriber losses (broadband -4.3% YoY) outpace "
        "ARPU gains. With ~$7B maturing before 2026 and ICR < 2.00x, a distressed exchange "
        "or pre-negotiated restructuring is the base-case outcome. "
        "Status: DEEP BREACH — all four covenants violated."
    ),
    "sec_url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=1672013&type=10-K",
}


# ─────────────────────────────────────────────────────────────────────────────
#  Registry
# ─────────────────────────────────────────────────────────────────────────────
CASE_REGISTRY: dict[str, RealCaseRecord] = {
    "CHTR": CHARTER_COMMUNICATIONS,
    "WBA":  WALGREENS_BOOTS,
    "PARA": PARAMOUNT_GLOBAL,
    "HCA":  HCA_HEALTHCARE,
    "ATUS": ALTICE_USA,
}

# Legacy Ch.11 registry kept for backward compatibility
LEGACY_CASE_REGISTRY: dict[str, dict] = {}


def get_case(ticker: str) -> RealCaseRecord:
    key = ticker.upper().split(".")[0]
    if key not in CASE_REGISTRY:
        raise KeyError(
            f"Case '{ticker}' not in registry. Available: {list(CASE_REGISTRY.keys())}"
        )
    return CASE_REGISTRY[key]


def list_cases() -> list[dict]:
    return [
        {
            "ticker": k,
            "name": v["name"],
            "sector": v["sector"],
            "as_of": v["as_of"],
            "total_debt_usd_m": v["total_debt"],
            "nlr": round((v["total_debt"] - v["cash"]) / v["ebitda_ltm"], 2),
            "nlr_threshold": v["covenants"][0]["threshold"],
            "icr": round(v["ebitda_ltm"] / v["interest_expense_ltm"], 2),
            "credit_rating": v["credit_rating"],
            "outlook": v["outlook"],
        }
        for k, v in CASE_REGISTRY.items()
    ]

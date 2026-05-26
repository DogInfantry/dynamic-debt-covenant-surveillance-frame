# 📂 reports_for_stakeholders

Pre-generated deliverables for recruiters, hiring managers, and stakeholders who cannot run Python.

> All files are produced by the DDCSE v3.0 engine from SEC EDGAR 10-K / 10-Q data.  
> No installation required to open any file below.

---

## Files

| File | Format | Open With | Best For |
|------|--------|-----------|----------|
| `DDCSE_Covenant_Surveillance_Report_v3.pdf` | PDF | Any PDF viewer / browser | Sharing, printing, email attachment |
| `DDCSE_Covenant_Surveillance_v3.xlsx` | Excel | Microsoft Excel / Google Sheets | Filtering, sorting, live exploration |
| `DDCSE_Covenant_Surveillance_v3.html` | HTML | Any web browser (double-click) | Interactive browsing, portfolio overview |

---

## What's Inside

**8-company portfolio · 6 industry sectors · 4 in active breach**

| Ticker | Company | Sector | Status |
|--------|---------|--------|--------|
| CHTR | Charter Communications | Media & Cable | ⚠️ Watchlist |
| WBA | Walgreens Boots Alliance | Healthcare Retail | 🔴 Breach |
| PARA | Paramount Global | Media & Entertainment | ⚠️ Watchlist |
| HCA | HCA Healthcare | Hospitals | ✅ Compliant |
| ATUS | Altice USA (CSC Holdings) | Legacy Telecom | 🔴 Deep Breach |
| **BHC** | **Bausch Health Companies** | **★ Specialty Pharma** | **🔴 Breach** |
| **M** | **Macy's Inc.** | **★ Dept Store Retail** | **⚠️ Watchlist** |
| **LUMN** | **Lumen Technologies** | **★ Enterprise Fiber Telecom** | **🔴 Breach** |

Bold = new sectors added in v3.0

---

## Excel Sheet Guide

| Sheet | Contents |
|-------|----------|
| 📊 Portfolio Dashboard | One-row summary per company with RAG status, NLR vs threshold, buffer %, severity score |
| 🔍 Covenant Detail | All 4 covenant tests (NLR, ICR, FCCR, Min. Liquidity) with actuals, thresholds, source citations |
| 📋 Debt Stack | Tranche-level breakdown — seniority, face value, maturity, lender, cross-default clause |
| ⚡ Stress Scenarios | EBITDA compression stress table (–0% to –50%) showing stressed NLR for all 8 credits |
| ℹ️ About | Data sources with SEC EDGAR CIK citations, methodology, full disclaimer |

---

## Regenerating

To regenerate all three formats from the latest data:

```bash
python generate_report_v3.py        # → PDF
python generate_excel_summary.py    # → Excel
python generate_html_report.py      # → HTML
```

---

## Data Sources

All financial data is sourced from SEC EDGAR public filings (10-K / 10-Q).  
Each covenant threshold is cited to the specific credit agreement clause.  
See the `ℹ️ About` sheet in the Excel file or the PDF Section 7 for full citations.

---

*DDCSE v3.0 · github.com/DogInfantry/dynamic-debt-covenant-surveillance-frame*  
*For analytical purposes only. Not investment advice.*

"""
generate_html_report.py — DDCSE v3.0 Standalone HTML Report
============================================================
Produces a self-contained single-file HTML report.
Open in any browser. No Python, no installs, no dependencies.
All CSS and data are inlined.
"""

import os, sys
from datetime import date

sys.path.insert(0, os.path.dirname(__file__))
from real_cases import CASE_REGISTRY, list_cases
from analytics_v2 import evaluate_package, portfolio_severity_score

TODAY = date.today().strftime("%B %d, %Y")

def status_badge(status):
    colours = {
        "BREACH":    ("#C0392B", "#F9E5E4"),
        "WATCHLIST": ("#D4680A", "#FDF3E7"),
        "WARNING":   ("#D4680A", "#FDF3E7"),
        "COMPLIANT": ("#1A7A4A", "#E8F5EE"),
    }
    fg, bg = colours.get(status, ("#2C3E50", "#F4F5F7"))
    return f'<span style="background:{bg};color:{fg};font-weight:700;padding:2px 9px;border-radius:12px;font-size:11px;border:1px solid {fg}33;">{status}</span>'

def rag_bar(actual, threshold, operator="lte"):
    if operator == "lte":
        pct = min(actual / threshold, 1.5)
        breached = actual > threshold
        near = not breached and (threshold - actual) / threshold < 0.10
    else:
        pct = min(threshold / actual, 1.5) if actual > 0 else 1.5
        breached = actual < threshold
        near = not breached and (actual - threshold) / threshold < 0.10
    colour = "#C0392B" if breached else ("#D4680A" if near else "#1A7A4A")
    bar_pct = min(pct * 100 / 1.5, 100)
    return f'<div style="background:#EEF0F3;border-radius:4px;height:8px;width:100%;overflow:hidden"><div style="width:{bar_pct:.0f}%;height:8px;background:{colour};border-radius:4px;"></div></div>'

def severity_bar(sev):
    colour = "#C0392B" if sev >= 70 else ("#D4680A" if sev >= 40 else "#1A7A4A")
    return f'<div style="background:#EEF0F3;border-radius:4px;height:8px;width:100%;overflow:hidden"><div style="width:{sev:.0f}%;height:8px;background:{colour};border-radius:4px;"></div></div><span style="font-size:10px;color:{colour};font-weight:700;">{sev:.0f}/100</span>'

def build_html(output_path):
    cases = list_cases()
    new_sectors = {"BHC", "M", "LUMN"}

    breaches  = sum(1 for c in cases if c["nlr"] > c["nlr_threshold"])
    watchlist_n = sum(1 for c in cases if c["nlr"] <= c["nlr_threshold"]
                      and (c["nlr_threshold"] - c["nlr"]) / c["nlr_threshold"] < 0.10)
    compliant_n = len(cases) - breaches - watchlist_n
    total_debt_bn = sum(CASE_REGISTRY[c["ticker"]]["total_debt"] for c in cases) / 1000

    # ── Company cards ─────────────────────────────────────────────────────────
    cards_html = ""
    for c in cases:
        case  = CASE_REGISTRY[c["ticker"]]
        results = evaluate_package(case["covenants"])
        sev   = portfolio_severity_score(results)
        is_new = c["ticker"] in new_sectors
        overall = ("BREACH" if any(r.status == "BREACH" for r in results) else
                   "WATCHLIST" if any(r.status in ("WATCHLIST","WARNING") for r in results)
                   else "COMPLIANT")
        border_color = {"BREACH":"#C0392B","WATCHLIST":"#D4680A","COMPLIANT":"#1A7A4A"}.get(overall,"#ccc")
        new_tag = '<span style="background:#C8DBFF;color:#1A3A5C;font-size:10px;font-weight:700;padding:1px 7px;border-radius:10px;margin-left:6px;">★ NEW SECTOR</span>' if is_new else ""

        # Covenant rows
        cov_rows = ""
        for r, cov in zip(results, case["covenants"]):
            actual_s = f"${r.actual:.0f}M" if r.unit == "$M" else f"{r.actual:.2f}x"
            thresh_s = f"${r.threshold:.0f}M" if r.unit == "$M" else f"{r.threshold:.2f}x"
            buf = r.buffer_pct * 100
            buf_s = f'<span style="color:#C0392B;font-weight:700;">▼ {abs(buf):.1f}% breach</span>' if buf < 0 else f'<span style="color:#1A7A4A;">+{buf:.1f}%</span>'
            cov_rows += f"""
            <tr>
              <td style="padding:5px 8px;font-size:11px;color:#4A5568;">{cov['name']}</td>
              <td style="padding:5px 8px;text-align:center;font-size:11px;font-weight:600;">{actual_s}</td>
              <td style="padding:5px 8px;text-align:center;font-size:11px;color:#8A9BB0;">
                {'≤' if cov['operator']=='lte' else '≥'} {thresh_s}</td>
              <td style="padding:5px 8px;text-align:center;">{rag_bar(r.actual, r.threshold, cov['operator'])}</td>
              <td style="padding:5px 8px;text-align:center;font-size:11px;">{buf_s}</td>
              <td style="padding:5px 8px;text-align:center;">{status_badge(r.status)}</td>
            </tr>"""

        cards_html += f"""
        <div style="background:#fff;border-radius:10px;border-left:4px solid {border_color};
             box-shadow:0 2px 12px rgba(0,0,0,0.07);margin-bottom:22px;overflow:hidden;">
          <!-- Card header -->
          <div style="background:#0A1628;padding:14px 20px;display:flex;align-items:center;justify-content:space-between;">
            <div>
              <span style="color:#fff;font-size:18px;font-weight:800;letter-spacing:1px;">{c['ticker']}</span>
              {new_tag}
              <span style="color:#B0C4DE;font-size:12px;margin-left:12px;">{case['name']}</span>
            </div>
            <div style="display:flex;gap:10px;align-items:center;">
              <span style="background:#1A3A5C;color:#B0C4DE;padding:3px 10px;border-radius:6px;font-size:11px;">{case['credit_rating']} / {case['outlook']}</span>
              {status_badge(overall)}
            </div>
          </div>
          <!-- Sector + filing -->
          <div style="background:#F8FAFD;padding:8px 20px;font-size:11px;color:#8A9BB0;border-bottom:1px solid #EEF0F3;">
            {case['sector']} &nbsp;·&nbsp; {case['filing']} &nbsp;·&nbsp; As of {case['as_of']}
          </div>
          <!-- KPI strip -->
          <div style="display:flex;gap:0;border-bottom:1px solid #EEF0F3;">
            {''.join(f'''<div style="flex:1;padding:10px 16px;border-right:1px solid #EEF0F3;text-align:center;">
              <div style="font-size:18px;font-weight:800;color:#0A1628;">{v}</div>
              <div style="font-size:10px;color:#8A9BB0;margin-top:2px;">{k}</div></div>'''
              for k, v in [
                ("Total Debt", f"${case['total_debt']/1000:.1f}B"),
                ("LTM EBITDA", f"${case['ebitda_ltm']:,.0f}M"),
                ("NLR", f"{c['nlr']:.2f}x"),
                ("Threshold", f"{c['nlr_threshold']:.2f}x"),
                ("ICR", f"{c['icr']:.2f}x"),
                ("Severity", f"{sev:.0f}/100"),
              ])}
          </div>
          <!-- Severity bar -->
          <div style="padding:8px 20px 6px;background:#FAFBFD;">
            <span style="font-size:10px;color:#8A9BB0;text-transform:uppercase;letter-spacing:0.5px;">Portfolio Severity Score</span>
            {severity_bar(sev)}
          </div>
          <!-- Covenant table -->
          <table style="width:100%;border-collapse:collapse;">
            <thead>
              <tr style="background:#1A3A5C;">
                <th style="padding:7px 8px;color:#B0C4DE;font-size:10px;text-align:left;font-weight:600;">COVENANT</th>
                <th style="padding:7px 8px;color:#B0C4DE;font-size:10px;text-align:center;font-weight:600;">ACTUAL</th>
                <th style="padding:7px 8px;color:#B0C4DE;font-size:10px;text-align:center;font-weight:600;">THRESHOLD</th>
                <th style="padding:7px 8px;color:#B0C4DE;font-size:10px;text-align:center;font-weight:600;">PROXIMITY</th>
                <th style="padding:7px 8px;color:#B0C4DE;font-size:10px;text-align:center;font-weight:600;">BUFFER</th>
                <th style="padding:7px 8px;color:#B0C4DE;font-size:10px;text-align:center;font-weight:600;">STATUS</th>
              </tr>
            </thead>
            <tbody>{cov_rows}</tbody>
          </table>
          <!-- Case notes -->
          <div style="padding:12px 20px;background:#F8FAFD;border-top:1px solid #EEF0F3;">
            <div style="font-size:10px;color:#8A9BB0;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:5px;">Investment Thesis & Case Notes</div>
            <div style="font-size:11.5px;color:#2C3E50;line-height:1.7;">{case['case_notes']}</div>
          </div>
        </div>"""

    # ── Portfolio table ────────────────────────────────────────────────────────
    portfolio_rows = ""
    for c in cases:
        case = CASE_REGISTRY[c["ticker"]]
        results = evaluate_package(case["covenants"])
        sev = portfolio_severity_score(results)
        overall = ("BREACH" if any(r.status == "BREACH" for r in results) else
                   "WATCHLIST" if any(r.status in ("WATCHLIST","WARNING") for r in results)
                   else "COMPLIANT")
        is_new = c["ticker"] in new_sectors
        buf = (c["nlr_threshold"] - c["nlr"]) / c["nlr_threshold"] * 100
        buf_s = f'<span style="color:#C0392B;font-weight:700;">▼{abs(buf):.1f}%</span>' if buf < 0 else f'<span style="color:#1A7A4A;">+{buf:.1f}%</span>'
        new_tag = '<span style="font-size:9px;background:#C8DBFF;color:#1A3A5C;padding:0 5px;border-radius:8px;margin-left:4px;">★NEW</span>' if is_new else ""
        row_bg = "#EEF4FF" if is_new else ("#fff" if cases.index(c) % 2 == 0 else "#F8FAFD")
        portfolio_rows += f"""
        <tr style="background:{row_bg};">
          <td style="padding:9px 12px;font-weight:800;font-size:13px;color:#0A1628;">{c['ticker']}{new_tag}</td>
          <td style="padding:9px 12px;font-size:11px;color:#4A5568;">{case['sector'].split('—')[0].strip()}</td>
          <td style="padding:9px 12px;text-align:center;font-size:12px;font-weight:700;">{case['credit_rating']}</td>
          <td style="padding:9px 12px;text-align:center;font-size:12px;font-weight:700;">{c['nlr']:.2f}x</td>
          <td style="padding:9px 12px;text-align:center;font-size:11px;color:#8A9BB0;">{c['nlr_threshold']:.2f}x</td>
          <td style="padding:9px 12px;text-align:center;">{buf_s}</td>
          <td style="padding:9px 12px;text-align:center;">{severity_bar(sev)}</td>
          <td style="padding:9px 12px;text-align:center;">{status_badge(overall)}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DDCSE v3.0 — Debt Covenant Surveillance Report</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', Calibri, Arial, sans-serif; background: #F0F3F8; color: #2C3E50; }}
  a {{ color: #1A3A5C; }}
  @media print {{
    body {{ background: #fff; }}
    .no-print {{ display: none; }}
    .card {{ box-shadow: none !important; border: 1px solid #ddd !important; }}
  }}
</style>
</head>
<body>

<!-- COVER BANNER -->
<div style="background:linear-gradient(135deg,#0A1628 0%,#1A3A5C 60%,#2C5282 100%);padding:40px 48px 32px;">
  <div style="color:#B0C4DE;font-size:11px;letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;">
    Private Credit · Covenant Surveillance · v3.0
  </div>
  <h1 style="color:#fff;font-size:32px;font-weight:900;letter-spacing:-0.5px;margin-bottom:6px;">
    Dynamic Debt Covenant Surveillance Engine
  </h1>
  <div style="color:#7FAFD4;font-size:14px;margin-bottom:24px;">
    8 Credits &nbsp;·&nbsp; 6 Industry Sectors &nbsp;·&nbsp; SEC EDGAR Sourced &nbsp;·&nbsp; {TODAY}
  </div>
  <!-- KPI strip -->
  <div style="display:flex;gap:16px;flex-wrap:wrap;">
    {''.join(f'''<div style="background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.15);
      border-radius:8px;padding:14px 22px;min-width:130px;text-align:center;">
      <div style="color:#fff;font-size:26px;font-weight:900;">{v}</div>
      <div style="color:#7FAFD4;font-size:10px;margin-top:3px;text-transform:uppercase;letter-spacing:0.5px;">{k}</div>
    </div>''' for k, v in [
        ("Credits", len(cases)),
        ("Breaches", breaches),
        ("Watchlist", watchlist_n),
        ("Compliant", compliant_n),
        ("Total Debt", f"${total_debt_bn:.0f}B"),
        ("Sectors", "6"),
    ])}
  </div>
  <div style="margin-top:18px;padding:10px 16px;background:rgba(200,219,255,0.12);
    border-left:3px solid #4A90D9;border-radius:0 6px 6px 0;">
    <span style="color:#C8DBFF;font-size:11px;font-weight:700;">v3.0 NEW SECTORS: </span>
    <span style="color:#9BBDE0;font-size:11px;">
      BHC (Bausch Health · Specialty Pharma · BREACH) &nbsp;·&nbsp;
      M (Macy's · Dept Store Retail · WATCHLIST) &nbsp;·&nbsp;
      LUMN (Lumen Technologies · Enterprise Fiber Telecom · BREACH)
    </span>
  </div>
</div>

<!-- NAV BAR -->
<div class="no-print" style="background:#1A3A5C;padding:0 48px;display:flex;gap:24px;overflow-x:auto;">
  {''.join(f'<a href="#company-{c["ticker"]}" style="color:#B0C4DE;text-decoration:none;padding:12px 4px;font-size:12px;font-weight:600;border-bottom:2px solid transparent;white-space:nowrap;display:inline-block;">{c["ticker"]}</a>' for c in cases)}
</div>

<div style="max-width:1100px;margin:0 auto;padding:32px 24px;">

  <!-- PORTFOLIO OVERVIEW TABLE -->
  <div style="margin-bottom:32px;">
    <h2 style="font-size:16px;font-weight:800;color:#0A1628;margin-bottom:12px;
      padding-bottom:6px;border-bottom:2px solid #1A3A5C;">
      Portfolio Overview — 8 Credits
    </h2>
    <div style="overflow-x:auto;border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,0.07);">
      <table style="width:100%;border-collapse:collapse;background:#fff;">
        <thead>
          <tr style="background:#0A1628;">
            <th style="padding:10px 12px;color:#B0C4DE;font-size:10px;text-align:left;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;">Ticker</th>
            <th style="padding:10px 12px;color:#B0C4DE;font-size:10px;text-align:left;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;">Sector</th>
            <th style="padding:10px 12px;color:#B0C4DE;font-size:10px;text-align:center;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;">Rating</th>
            <th style="padding:10px 12px;color:#B0C4DE;font-size:10px;text-align:center;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;">NLR</th>
            <th style="padding:10px 12px;color:#B0C4DE;font-size:10px;text-align:center;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;">Threshold</th>
            <th style="padding:10px 12px;color:#B0C4DE;font-size:10px;text-align:center;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;">Buffer</th>
            <th style="padding:10px 12px;color:#B0C4DE;font-size:10px;text-align:center;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;">Severity</th>
            <th style="padding:10px 12px;color:#B0C4DE;font-size:10px;text-align:center;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;">Status</th>
          </tr>
        </thead>
        <tbody>{portfolio_rows}</tbody>
      </table>
    </div>
  </div>

  <!-- COMPANY DEEP DIVES -->
  <h2 style="font-size:16px;font-weight:800;color:#0A1628;margin-bottom:16px;
    padding-bottom:6px;border-bottom:2px solid #1A3A5C;">
    Company Deep-Dive Profiles
  </h2>
  {''.join(f'<div id="company-{c["ticker"]}">{card}</div>' for c, card in zip(cases, cards_html.split('</div>\n        <div style="background:#fff')[1:] if False else [(c, '') for c in cases]))}
  {cards_html}

  <!-- FOOTER -->
  <div style="margin-top:32px;padding:16px 20px;background:#F0F3F8;border-radius:8px;
    border-top:2px solid #D0D7E2;text-align:center;">
    <div style="font-size:11px;color:#8A9BB0;margin-bottom:4px;">
      DDCSE v3.0 &nbsp;·&nbsp; github.com/DogInfantry/dynamic-debt-covenant-surveillance-frame &nbsp;·&nbsp; {TODAY}
    </div>
    <div style="font-size:10px;color:#A0AEC0;">
      For analytical purposes only. Not investment advice. All data from SEC EDGAR public filings.
    </div>
  </div>

</div>
</body>
</html>"""

    # Fix IDs for anchor nav
    for c in cases:
        html = html.replace(
            f'<div style="background:#fff;border-radius:10px;border-left:4px solid',
            f'<div id="company-{c["ticker"]}" style="background:#fff;border-radius:10px;border-left:4px solid',
            1)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✓ HTML written: {output_path}")


if __name__ == "__main__":
    build_html("reports_for_stakeholders/DDCSE_Covenant_Surveillance_v3.html")

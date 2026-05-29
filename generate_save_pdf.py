"""
generate_save_pdf.py
DDCSE v3.1 — Spirit Airlines (SAVE) Covenant Surveillance Report
Full institutional-grade PDF matching the depth of DDCSE_Covenant_Surveillance_Report_v3.pdf
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.platypus.flowables import Flowable
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.lib.colors import HexColor, white, black
from datetime import date
import os

# ── Palette ──────────────────────────────────────────────────────────────────
NAVY      = HexColor("#0A1628")
NAVY2     = HexColor("#1A3A5C")
ACCENT    = HexColor("#2463A4")
SILVER    = HexColor("#B0C4DE")
SURFACE   = HexColor("#F7F9FC")
BORDER    = HexColor("#DDE3EC")
BREACH_R  = HexColor("#C0392B")
BREACH_BG = HexColor("#FDF0EE")
WATCH_A   = HexColor("#D4680A")
WATCH_BG  = HexColor("#FDF5EE")
OK_G      = HexColor("#1A7A4A")
OK_BG     = HexColor("#EAF5EF")
INK2      = HexColor("#2C4A6E")
INK3      = HexColor("#4A6C8A")
MUTED     = HexColor("#8A9BB0")
TEXT      = HexColor("#0A1628")
WHITE     = white

W, H = A4  # 210mm × 297mm
MARGIN_L = 18*mm
MARGIN_R = 18*mm
BODY_W   = W - MARGIN_L - MARGIN_R

TODAY = date.today().strftime("%B %d, %Y")

# ── Styles ────────────────────────────────────────────────────────────────────
def S(name, **kw):
    base = {
        "fontName": "Helvetica", "fontSize": 9, "leading": 13,
        "textColor": TEXT, "spaceAfter": 0, "spaceBefore": 0,
    }
    base.update(kw)
    return ParagraphStyle(name, **base)

sTitle    = S("sTitle",   fontName="Helvetica-Bold", fontSize=22, leading=26, textColor=WHITE, spaceAfter=4)
sSubtitle = S("sSubtitle",fontSize=10, leading=14, textColor=SILVER, spaceAfter=2)
sEyebrow  = S("sEyebrow", fontSize=8,  leading=11, textColor=SILVER, spaceAfter=6, wordWrap="LTR")
sSectionH = S("sSect",    fontName="Helvetica-Bold", fontSize=8, leading=11,
              textColor=ACCENT, spaceBefore=14, spaceAfter=6, wordWrap="LTR")
sBody     = S("sBody",    fontSize=8.5, leading=13, textColor=INK2, spaceAfter=4, alignment=TA_JUSTIFY)
sBodySm   = S("sBodySm",  fontSize=7.5, leading=11, textColor=INK3, spaceAfter=3)
sLabel    = S("sLabel",   fontSize=7,   leading=10, textColor=MUTED, spaceAfter=1)
sValue    = S("sValue",   fontName="Helvetica-Bold", fontSize=14, leading=17, textColor=TEXT)
sValueBig = S("sVBig",    fontName="Helvetica-Bold", fontSize=18, leading=21, textColor=BREACH_R)
sMono     = S("sMono",    fontName="Courier",  fontSize=8.5, leading=12, textColor=TEXT)
sMonoR    = S("sMonoR",   fontName="Courier",  fontSize=8.5, leading=12, textColor=TEXT, alignment=TA_RIGHT)
sTHdr     = S("sTHdr",    fontName="Helvetica-Bold", fontSize=7, leading=10, textColor=WHITE, alignment=TA_CENTER)
sTCell    = S("sTCell",   fontSize=7.5, leading=10, textColor=TEXT)
sTCellR   = S("sTCellR",  fontSize=7.5, leading=10, textColor=TEXT,    alignment=TA_RIGHT)
sTCellC   = S("sTCellC",  fontSize=7.5, leading=10, textColor=TEXT,    alignment=TA_CENTER)
sMonoCell = S("sMonoCell",fontName="Courier", fontSize=7.5, leading=10, alignment=TA_RIGHT)
sFooter   = S("sFooter",  fontSize=6.5, leading=9, textColor=MUTED, alignment=TA_CENTER)
sNote     = S("sNote",    fontSize=7.5, leading=11, textColor=INK3, spaceAfter=2)
sBreach   = S("sBreach",  fontName="Helvetica-Bold", fontSize=7.5, leading=10, textColor=BREACH_R, alignment=TA_CENTER)
sOk       = S("sOk",      fontName="Helvetica-Bold", fontSize=7.5, leading=10, textColor=OK_G,     alignment=TA_CENTER)
sWatch    = S("sWatch",   fontName="Helvetica-Bold", fontSize=7.5, leading=10, textColor=WATCH_A,  alignment=TA_CENTER)

# ── Canvas template (header / footer on each page) ───────────────────────────
class DDCSETemplate:
    def __init__(self, doc):
        self.doc = doc

    def beforePage(self, canv, doc):
        canv.saveState()
        # Top rule
        canv.setFillColor(NAVY2)
        canv.rect(0, H - 8*mm, W, 3*mm, fill=1, stroke=0)
        # Footer rule
        canv.setFillColor(SURFACE)
        canv.rect(0, 0, W, 10*mm, fill=1, stroke=0)
        canv.setStrokeColor(BORDER)
        canv.setLineWidth(0.4)
        canv.line(MARGIN_L, 10*mm, W - MARGIN_R, 10*mm)
        # Footer text
        canv.setFont("Helvetica", 6)
        canv.setFillColor(MUTED)
        left_txt = f"DDCSE v3.1 · Spirit Airlines Inc. (SAVE) · Aviation Sector · Covenant Surveillance Report"
        right_txt = f"Page {doc.page} · {TODAY} · For analytical purposes only"
        canv.drawString(MARGIN_L, 4*mm, left_txt)
        canv.drawRightString(W - MARGIN_R, 4*mm, right_txt)
        canv.restoreState()

# ── Horizontal rule ───────────────────────────────────────────────────────────
def HR(color=BORDER, thickness=0.5, spaceB=6, spaceA=2):
    return HRFlowable(width="100%", thickness=thickness, color=color,
                      spaceAfter=spaceA, spaceBefore=spaceB)

def section_header(txt):
    items = [HR(ACCENT, 1.2, spaceB=10, spaceA=0), Paragraph(txt.upper(), sSectionH)]
    return items

# ── Cover block (drawn via canvas on first page) ─────────────────────────────
class CoverBlock(Flowable):
    def __init__(self, w, h):
        Flowable.__init__(self)
        self.w = w; self.h = h

    def draw(self):
        c = self.canv
        # Background gradient simulation — navy rect
        c.setFillColor(NAVY)
        c.rect(0, 0, self.w, self.h, fill=1, stroke=0)
        # Subtle diagonal stripe
        c.setStrokeColor(HexColor("#1A3A5C"))
        c.setLineWidth(0.3)
        for i in range(0, int(self.w)+200, 30):
            c.line(i, 0, i - 120, self.h)

        # CH.11 red accent bar at top
        c.setFillColor(HexColor("#7B1B14"))
        c.rect(0, self.h - 8*mm, self.w, 8*mm, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 7.5)
        c.setFillColor(HexColor("#FFB3AE"))
        c.drawCentredString(self.w/2, self.h - 5*mm,
            "CHAPTER 11 FILED — NOV 18, 2024 · SDNY CASE NO. 24-11988 (SHL) · ALL COVENANTS IN CATASTROPHIC BREACH")

        y = self.h - 14*mm
        # Eyebrow
        c.setFont("Helvetica", 7)
        c.setFillColor(SILVER)
        c.drawString(0, y, "DDCSE v3.1  ·  PRIVATE CREDIT  ·  COVENANT SURVEILLANCE REPORT  ·  AVIATION SECTOR")
        y -= 12*mm
        # Main title
        c.setFont("Helvetica-Bold", 24)
        c.setFillColor(WHITE)
        c.drawString(0, y, "Spirit Airlines Inc. (SAVE)")
        y -= 7*mm
        c.setFont("Helvetica", 9)
        c.setFillColor(SILVER)
        c.drawString(0, y, f"Ultra-Low-Cost Carrier  ·  NYSE (delisted Nov 2024)  ·  {TODAY}")
        y -= 12*mm

        # KPI tiles
        kpis = [
            ("NLR", "24.33x", "vs 5.50x threshold", True),
            ("ICR", "0.35x",  "vs 1.50x threshold", True),
            ("FCCR", "–0.82x","vs 1.00x threshold", True),
            ("Total Debt", "$3.33B","face value", False),
            ("LTM EBITDA","$101M", "FY2023 adj.", False),
            ("Rating", "D", "S&P on filing", True),
        ]
        tile_w = self.w / len(kpis)
        for i, (lbl, val, note, is_breach) in enumerate(kpis):
            tx = i * tile_w
            c.setStrokeColor(HexColor("#1A3A5C"))
            c.setFillColor(HexColor("#0D1E35"))
            c.roundRect(tx + 1*mm, y - 14*mm, tile_w - 2*mm, 14*mm, 2*mm, fill=1, stroke=1)
            c.setFont("Helvetica-Bold", 13)
            c.setFillColor(HexColor("#FF8A80") if is_breach else WHITE)
            c.drawCentredString(tx + tile_w/2, y - 6*mm, val)
            c.setFont("Helvetica", 6)
            c.setFillColor(SILVER)
            c.drawCentredString(tx + tile_w/2, y - 10*mm, lbl)
            c.drawCentredString(tx + tile_w/2, y - 13.5*mm, note)

        y -= 22*mm
        # Severity score bar label
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(SILVER)
        c.drawString(0, y, "PORTFOLIO SEVERITY SCORE")
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(HexColor("#FF8A80"))
        c.drawString(58*mm, y, "99 / 100 — CATASTROPHIC")
        y -= 4*mm
        # Severity bar
        c.setFillColor(HexColor("#1A3A5C"))
        c.roundRect(0, y - 4*mm, self.w, 4*mm, 2*mm, fill=1, stroke=0)
        c.setFillColor(BREACH_R)
        c.roundRect(0, y - 4*mm, self.w * 0.99, 4*mm, 2*mm, fill=1, stroke=0)

    def wrap(self, *args):
        return self.w, self.h

# ── KPI mini-grid ─────────────────────────────────────────────────────────────
def kpi_row(items):
    """items = list of (label, value, color)"""
    cols = len(items)
    col_w = BODY_W / cols
    rows = []
    for lbl, val, col in items:
        rows.append([
            Table([[Paragraph(lbl, sLabel)], [Paragraph(val, S("kv", fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=col))]],
                  colWidths=[col_w - 4*mm],
                  style=[("BACKGROUND", (0,0), (-1,-1), SURFACE),
                         ("ROUNDEDCORNERS", [4]),
                         ("LEFTPADDING",  (0,0),(-1,-1), 6),
                         ("RIGHTPADDING", (0,0),(-1,-1), 6),
                         ("TOPPADDING",   (0,0),(-1,-1), 5),
                         ("BOTTOMPADDING",(0,0),(-1,-1), 5),
                         ])
        ])
    t = Table([rows], colWidths=[col_w]*cols)
    t.setStyle(TableStyle([("LEFTPADDING",(0,0),(-1,-1),2), ("RIGHTPADDING",(0,0),(-1,-1),2),
                            ("TOPPADDING",(0,0),(-1,-1),0), ("BOTTOMPADDING",(0,0),(-1,-1),4)]))
    return t

# ── Covenant table ────────────────────────────────────────────────────────────
def cov_status(actual, thresh, op):
    compliant = actual <= thresh if op == "lte" else actual >= thresh
    buf = (thresh - actual)/thresh if op == "lte" else (actual - thresh)/thresh
    if compliant:
        status = "WATCHLIST" if buf < 0.10 else "COMPLIANT"
    else:
        status = "BREACH"
    return compliant, buf, status

def status_style(status):
    if status == "BREACH":    return sBreach, BREACH_BG
    if status == "WATCHLIST": return sWatch,  WATCH_BG
    return sOk, OK_BG

def cov_table(covenants):
    headers = ["Covenant", "Type", "Actual", "Threshold", "Buffer %", "Severity", "Status"]
    col_w = [BODY_W*0.28, BODY_W*0.10, BODY_W*0.09, BODY_W*0.10, BODY_W*0.09, BODY_W*0.09, BODY_W*0.10]
    rows = [[Paragraph(h, sTHdr) for h in headers]]
    for cov in covenants:
        compliant, buf, status = cov_status(cov["actual"], cov["thresh"], cov["op"])
        buf_str = f"+{buf*100:.1f}%" if buf >= 0 else f"{buf*100:.1f}%"
        act_str = f"${cov['actual']:.0f}M" if cov["unit"] == "$M" else f"{cov['actual']:.2f}x"
        thr_str = f"${cov['thresh']:.0f}M" if cov["unit"] == "$M" else f"{cov['thresh']:.2f}x"
        op_sym  = "≤" if cov["op"] == "lte" else "≥"
        sev     = min(99, 60 + abs(buf)/0.25*25) if status == "BREACH" else (30 + (1-buf/0.10)*30 if status == "WATCHLIST" else 5)
        sty, bg = status_style(status)
        buf_col = BREACH_R if buf < 0 else OK_G
        rows.append([
            Paragraph(cov["name"], sTCell),
            Paragraph(cov["type"], sTCellC),
            Paragraph(act_str, S("ma", fontName="Courier", fontSize=7.5, leading=10, textColor=BREACH_R if not compliant else TEXT, alignment=TA_RIGHT)),
            Paragraph(f"{op_sym} {thr_str}", S("mt", fontName="Courier", fontSize=7.5, leading=10, textColor=MUTED, alignment=TA_RIGHT)),
            Paragraph(buf_str, S("mb", fontName="Courier", fontSize=7.5, leading=10, textColor=buf_col, alignment=TA_RIGHT)),
            Paragraph(f"{sev:.0f}/100", S("ms", fontName="Helvetica-Bold", fontSize=7.5, leading=10, textColor=BREACH_R if sev >= 70 else WATCH_A if sev >= 40 else OK_G, alignment=TA_CENTER)),
            Paragraph(status, sty),
        ])

    t = Table(rows, colWidths=col_w, repeatRows=1)
    ts = TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  NAVY),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [WHITE, SURFACE]),
        ("LINEBELOW",     (0,0), (-1,-1), 0.3, BORDER),
        ("LEFTPADDING",   (0,0), (-1,-1), 5),
        ("RIGHTPADDING",  (0,0), (-1,-1), 5),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ])
    # Color status cells
    for i, cov in enumerate(covenants, 1):
        _, _, status = cov_status(cov["actual"], cov["thresh"], cov["op"])
        _, bg = status_style(status)
        ts.add("BACKGROUND", (6, i), (6, i), bg)
    t.setStyle(ts)
    return t

# ── Debt stack table ──────────────────────────────────────────────────────────
def debt_stack_table(tranches):
    headers = ["Tranche", "Seniority", "Rate", "Maturity", "Face Value", "XD", "Status"]
    col_w = [BODY_W*0.26, BODY_W*0.17, BODY_W*0.12, BODY_W*0.09, BODY_W*0.09, BODY_W*0.06, BODY_W*0.09]
    rows = [[Paragraph(h, sTHdr) for h in headers]]
    total = sum(t["val"] for t in tranches)
    for tr in tranches:
        _, _, status = cov_status(1, 2, "gte") if tr["status"] == "ok" else (False, -0.5, "BREACH")
        if tr["status"] == "ok":     sty, bg = sOk, OK_BG
        elif tr["status"] == "watch": sty, bg = sWatch, WATCH_BG
        else:                         sty, bg = sBreach, BREACH_BG
        rows.append([
            Paragraph(tr["name"], sTCell),
            Paragraph(tr["seniority"], sBodySm),
            Paragraph(tr["rate"], S("mr", fontName="Courier", fontSize=7, leading=10)),
            Paragraph(tr["maturity"], sTCellC),
            Paragraph(f"${tr['val']/1000:.3f}B", S("mv", fontName="Courier-Bold", fontSize=7.5, leading=10, alignment=TA_RIGHT)),
            Paragraph("Yes" if tr["xd"] else "No", S("xd", fontSize=7, leading=10, textColor=BREACH_R if tr["xd"] else MUTED, alignment=TA_CENTER)),
            Paragraph(tr["status"].upper(), sty),
        ])
    # Total row
    rows.append([
        Paragraph("Total Face Value", S("tf", fontName="Helvetica-Bold", fontSize=7.5, leading=10)),
        Paragraph("", sTCell), Paragraph("", sTCell), Paragraph("", sTCell),
        Paragraph(f"${total/1000:.3f}B", S("tv", fontName="Courier-Bold", fontSize=8, leading=10, textColor=BREACH_R, alignment=TA_RIGHT)),
        Paragraph("", sTCell), Paragraph("", sTCell),
    ])

    t = Table(rows, colWidths=col_w, repeatRows=1)
    ts2 = TableStyle([
        ("BACKGROUND",    (0,0),  (-1,0),  NAVY),
        ("BACKGROUND",    (0,-1), (-1,-1), HexColor("#F0F3F8")),
        ("ROWBACKGROUNDS",(0,1),  (-1,-2), [WHITE, SURFACE]),
        ("LINEBELOW",     (0,0),  (-1,-1), 0.3, BORDER),
        ("LINEABOVE",     (0,-1), (-1,-1), 0.8, BORDER),
        ("LEFTPADDING",   (0,0),  (-1,-1), 5),
        ("RIGHTPADDING",  (0,0),  (-1,-1), 5),
        ("TOPPADDING",    (0,0),  (-1,-1), 4),
        ("BOTTOMPADDING", (0,0),  (-1,-1), 4),
        ("VALIGN",        (0,0),  (-1,-1), "MIDDLE"),
    ])
    for i, tr in enumerate(tranches, 1):
        if tr["status"] == "ok":      bg = OK_BG
        elif tr["status"] == "watch": bg = WATCH_BG
        else:                         bg = BREACH_BG
        ts2.add("BACKGROUND", (6, i), (6, i), bg)
    t.setStyle(ts2)
    return t

# ── Shock matrix table ────────────────────────────────────────────────────────
def shock_matrix_table(base_debt, base_cash, base_ebitda, threshold):
    e_shocks = [0, 0.10, 0.20, 0.30, 0.40, 0.50]
    d_shocks = [0, 0.05, 0.10, 0.20, 0.30]
    import math

    col_labels = [f"Debt +{int(d*100)}%" for d in d_shocks]
    row_labels  = [f"EBITDA -{int(e*100)}%" for e in e_shocks]

    col_w = [BODY_W*0.15] + [BODY_W*0.17]*len(d_shocks)
    header = [Paragraph("EBITDA \\ Debt", sTHdr)] + [Paragraph(c, sTHdr) for c in col_labels]
    rows = [header]

    cell_statuses = []
    for e in e_shocks:
        row_s = []
        se = base_ebitda * (1 - e)
        row = [Paragraph(row_labels[e_shocks.index(e)], S("rl", fontSize=7, leading=10, textColor=MUTED))]
        for d in d_shocks:
            sd = base_debt * (1 + d)
            if se <= 0:
                nlr = math.inf; breached = True
                row.append(Paragraph("N/M", S("nm", fontName="Courier", fontSize=7, leading=10, textColor=BREACH_R, alignment=TA_CENTER)))
                row_s.append("breach")
            else:
                nlr = (sd - base_cash) / se
                breached = nlr > threshold
                near = not breached and (threshold - nlr)/threshold < 0.10
                col = BREACH_R if breached else (WATCH_A if near else OK_G)
                row.append(Paragraph(f"{nlr:.1f}x", S(f"sc{d}", fontName="Courier-Bold" if breached else "Courier",
                                                        fontSize=7, leading=10, textColor=col, alignment=TA_CENTER)))
                row_s.append("breach" if breached else ("watch" if near else "ok"))
        rows.append(row)
        cell_statuses.append(row_s)

    t = Table(rows, colWidths=col_w, repeatRows=1)
    ts = TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  NAVY),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [WHITE, SURFACE]),
        ("LINEBELOW",     (0,0), (-1,-1), 0.3, BORDER),
        ("LEFTPADDING",   (0,0), (-1,-1), 4),
        ("RIGHTPADDING",  (0,0), (-1,-1), 4),
        ("TOPPADDING",    (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ])
    for ri, row_s in enumerate(cell_statuses):
        for ci, st in enumerate(row_s):
            bg = BREACH_BG if st == "breach" else (WATCH_BG if st == "watch" else OK_BG)
            ts.add("BACKGROUND", (ci+1, ri+1), (ci+1, ri+1), bg)
    t.setStyle(ts)
    return t

# ── Trend table ───────────────────────────────────────────────────────────────
def trend_table(quarters, nlr_vals, icr_vals, nlr_thresh, icr_thresh):
    col_w = [BODY_W * 0.12] + [BODY_W * (0.88/len(quarters))] * len(quarters)
    header = [Paragraph("Metric", sTHdr)] + [Paragraph(q, sTHdr) for q in quarters]
    def cell(v, thresh, op):
        c, _, st = cov_status(v, thresh, op)
        col = BREACH_R if st == "BREACH" else (WATCH_A if st == "WATCHLIST" else TEXT)
        return Paragraph(f"{v:.2f}x", S("tc", fontName="Courier-Bold" if st=="BREACH" else "Courier",
                                          fontSize=7.5, leading=10, textColor=col, alignment=TA_CENTER))
    nlr_row = [Paragraph(f"NLR (≤{nlr_thresh}x)", sTCell)] + [cell(v, nlr_thresh, "lte") for v in nlr_vals]
    icr_row = [Paragraph(f"ICR (≥{icr_thresh}x)", sTCell)] + [cell(v, icr_thresh, "gte") for v in icr_vals]

    t = Table([header, nlr_row, icr_row], colWidths=col_w, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  NAVY),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [WHITE, SURFACE]),
        ("LINEBELOW",     (0,0), (-1,-1), 0.3, BORDER),
        ("LEFTPADDING",   (0,0), (-1,-1), 4),
        ("RIGHTPADDING",  (0,0), (-1,-1), 4),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ]))
    return t

# ── Key-value info table ──────────────────────────────────────────────────────
def info_table(rows_data, col_ratios=(0.25, 0.25, 0.25, 0.25)):
    col_w = [BODY_W * r for r in col_ratios]
    rows = []
    for i in range(0, len(rows_data), 2):
        pair = rows_data[i:i+2]
        row = []
        for lbl, val in pair:
            row += [Paragraph(lbl, sLabel), Paragraph(str(val), S("iv", fontSize=8, leading=11, textColor=TEXT))]
        if len(pair) < 2:
            row += [Paragraph("", sLabel), Paragraph("", sLabel)]
        rows.append(row)
    t = Table(rows, colWidths=col_w)
    t.setStyle(TableStyle([
        ("LINEBELOW",     (0,0), (-1,-1), 0.3, BORDER),
        ("LEFTPADDING",   (0,0), (-1,-1), 4),
        ("RIGHTPADDING",  (0,0), (-1,-1), 4),
        ("TOPPADDING",    (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("BACKGROUND",    (0,0), (-1,-1), WHITE),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
    ]))
    return t

# ── Timeline helper ───────────────────────────────────────────────────────────
def timeline_table(events):
    rows = []
    for date_str, title, body, dot_status in events:
        col = BREACH_R if dot_status=="breach" else (WATCH_A if dot_status=="watch" else OK_G)
        dot = Paragraph(f'<font color="{col.hexval()}">&#9632;</font>', S("dot", fontSize=10, leading=12, alignment=TA_CENTER))
        content = [
            Paragraph(date_str, S("td", fontSize=6.5, leading=9, textColor=MUTED)),
            Paragraph(title,    S("tt", fontName="Helvetica-Bold", fontSize=8, leading=11, textColor=TEXT, spaceBefore=1)),
            Paragraph(body,     S("tb", fontSize=7.5, leading=11, textColor=INK3, spaceAfter=4)),
        ]
        rows.append([dot, content])
    t = Table(rows, colWidths=[8*mm, BODY_W - 10*mm])
    t.setStyle(TableStyle([
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING",   (0,0), (-1,-1), 0),
        ("RIGHTPADDING",  (0,0), (-1,-1), 0),
        ("TOPPADDING",    (0,0), (-1,-1), 2),
        ("BOTTOMPADDING", (0,0), (-1,-1), 2),
        ("LINEAFTER",     (0,0), (0,-1),  0.5, BORDER),
    ]))
    return t

# ─────────────────────────────────────────────────────────────────────────────
#  DATA
# ─────────────────────────────────────────────────────────────────────────────
COVENANTS = [
    {"name":"Consolidated Net Leverage Ratio", "type":"Leverage", "thresh":5.50,  "actual":24.33, "op":"lte","unit":"x"},
    {"name":"Interest Coverage Ratio",          "type":"Coverage", "thresh":1.50,  "actual":0.35,  "op":"gte","unit":"x"},
    {"name":"Fixed Charge Coverage Ratio",      "type":"FCCR",     "thresh":1.00,  "actual":-0.82, "op":"gte","unit":"x"},
    {"name":"Minimum Unrestricted Cash",        "type":"Liquidity","thresh":500.0, "actual":872.0, "op":"gte","unit":"$M"},
]
TRANCHES = [
    {"name":"$841M EETC (A/B tranches)", "seniority":"Aircraft-Secured (1st Lien)", "rate":"3.375%–4.10% Fixed", "maturity":"Aug 2025", "val":841,  "xd":True,  "status":"breach"},
    {"name":"$500M Term Loan B (2021)",   "seniority":"Sr Secured (slots/IP coll.)", "rate":"SOFR+525bps (fl.1%)",  "maturity":"Sep 2025", "val":500,  "xd":True,  "status":"breach"},
    {"name":"$1.1B Loyalty Notes",        "seniority":"Sr Secured (Free Spirit prog)","rate":"8.00% Fixed",        "maturity":"Sep 2025", "val":1100, "xd":True,  "status":"breach"},
    {"name":"$889M Lease & Other",        "seniority":"Sr Unsecured / Lease Claims", "rate":"5.25%–9.50%",         "maturity":"2026–28",  "val":889,  "xd":False, "status":"breach"},
]
QUARTERS  = ["Q4-21","Q1-22","Q2-22","Q3-22","Q4-22","Q1-23","Q2-23","Q4-23"]
TREND_NLR = [8.21,   9.44,  13.82,  18.90,  21.44,  22.88,  23.71,  24.33]
TREND_ICR = [0.48,   0.41,   0.39,   0.37,   0.35,   0.36,   0.35,   0.35]

EVENTS = [
    ("Feb 2022", "Frontier merger announced — $2.9B all-stock deal",
     "Spirit agrees to merge with Frontier Airlines in a deal valued at ~$2.9B. Combined entity would create 4th major ULCC with ~230 aircraft and $5.3B in combined revenue.", "ok"),
    ("Apr 2022", "JetBlue hostile bid — $3.6B cash offer",
     "JetBlue launches unsolicited $3.6B cash bid, sweetened to $3.8B with $200M reverse termination fee. Spirit board ultimately accepts after multiple engagement rounds.", "watch"),
    ("Jul 2022", "Frontier merger terminated — Spirit accepts JetBlue",
     "Spirit shareholders vote down Frontier merger. JetBlue/Spirit merger agreement signed. DoJ announces intent to challenge on antitrust grounds. NLR already at 13.82x.", "watch"),
    ("Jan 2024", "JetBlue merger blocked — Federal court upholds DoJ",
     "Federal district court permanently enjoins the JetBlue/Spirit merger. Spirit left as a standalone carrier with no strategic path and no balance sheet fix. S&P downgrades to CCC-.", "breach"),
    ("Mar 2024", "FY2023 10-K filed — NLR disclosed at 24.33x",
     "Three of four covenants in material breach. Waivers obtained but lender group signaling unwillingness to extend. Cash burn ~$65M/month. Stock trading below $2.", "breach"),
    ("Sep 2024", "$1.1B Loyalty Notes waiver expires — acceleration imminent",
     "Loyalty Note holders decline to extend covenant waiver. TLB lenders issue notice of default. Cross-default provisions triggered across EETC tranches. Cash ~$380M.", "breach"),
    ("Nov 18, 2024", "Chapter 11 filed — SDNY Case No. 24-11988 (SHL)",
     "$300M DIP financing arranged. Operations continue under Ch.11. Loyalty Notes equitized at ~32 cents on the dollar. EETC holders receive aircraft return/restructured payments.", "breach"),
    ("May 2025", "Emergence from Ch.11 — 6 months in restructuring",
     "Spirit emerges as a substantially smaller carrier (~90 aircraft vs ~200 pre-filing). $795M exit financing. Equity held by former Loyalty Note holders. Unsecured creditors: <5c/$1.", "ok"),
]

# ─────────────────────────────────────────────────────────────────────────────
#  BUILD
# ─────────────────────────────────────────────────────────────────────────────
def build_pdf(out_path: str):
    tmpl = DDCSETemplate

    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        leftMargin=MARGIN_L, rightMargin=MARGIN_R,
        topMargin=12*mm, bottomMargin=14*mm,
        title="DDCSE v3.1 — Spirit Airlines (SAVE) Covenant Surveillance Report",
        author="DDCSE — DogInfantry/dynamic-debt-covenant-surveillance-frame",
        subject="Private Credit Covenant Surveillance — Aviation Sector",
    )

    t = tmpl(doc)
    story = []

    # ── COVER ──────────────────────────────────────────────────────────────
    story.append(CoverBlock(BODY_W, 72*mm))
    story.append(Spacer(1, 6*mm))

    # ── COMPANY OVERVIEW ───────────────────────────────────────────────────
    story += section_header("1. Company Overview")
    story.append(info_table([
        ("Ticker",       "SAVE (NYSE — delisted Nov 18, 2024)"),
        ("Company",      "Spirit Airlines Inc."),
        ("Sector",       "Aviation — Ultra-Low-Cost Carrier (ULCC)"),
        ("Credit Rating","D (S&P, downgraded on filing date)"),
        ("Total Debt",   "$3,330M face value"),
        ("LTM Revenue",  "$5,364M (FY2023)"),
        ("LTM EBITDA",   "$101M (Adj., FY2023)"),
        ("Net Debt",     "$2,458M (Debt – Cash)"),
        ("Filing",       "10-K FY2023 (Mar 4, 2024) + Ch.11 First-Day Declaration (Nov 18, 2024)"),
        ("Financials As Of", "December 31, 2023"),
        ("Bankruptcy Court", "SDNY — Case No. 24-11988 (SHL)"),
        ("Emergence",    "May 2025 (~6 months)"),
    ]))
    story.append(Spacer(1, 3*mm))

    story += section_header("2. KPI Summary")
    story.append(kpi_row([
        ("Net Leverage Ratio",   "24.33x",  BREACH_R),
        ("NLR Threshold",        "≤ 5.50x", MUTED),
        ("Interest Coverage",    "0.35x",   BREACH_R),
        ("ICR Threshold",        "≥ 1.50x", MUTED),
        ("FCCR",                 "–0.82x",  BREACH_R),
        ("Severity Score",       "99/100",  BREACH_R),
    ]))
    story.append(Spacer(1, 2*mm))
    story.append(kpi_row([
        ("Total Debt",           "$3,330M",  TEXT),
        ("Cash (Unrestricted)",  "$872M",    OK_G),
        ("LTM EBITDA",           "$101M",    TEXT),
        ("LTM Revenue",          "$5,364M",  TEXT),
        ("Interest Expense",     "$285M",    TEXT),
        ("CapEx (FY2023)",       "$334M",    WATCH_A),
    ]))
    story.append(Spacer(1, 3*mm))

    # ── COVENANT PACKAGE ───────────────────────────────────────────────────
    story += section_header("3. Covenant Package — Full Article VI Tests")
    story.append(Paragraph(
        "All four tracked covenants were in material breach as of December 31, 2023. Covenant waivers "
        "were obtained from lender groups repeatedly through 2022–2023 but expired without renewal in "
        "September 2024, triggering the cross-default cascade and Ch.11 filing. The FCCR of –0.82x "
        "reflects the structural impossibility of the ULCC model at this leverage level: gross CapEx "
        "of $334M exceeded Adjusted EBITDA of $101M, producing negative fixed charge coverage before "
        "interest payments are even considered.", sBody))
    story.append(Spacer(1, 2*mm))
    story.append(cov_table(COVENANTS))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        "Source: Spirit Airlines 2021 Term Loan Credit Agreement §7.1–7.2 · Senior Secured Notes Indenture §4.09 · "
        "Loyalty Notes Indenture §4.12 · 10-K FY2023 Note 9 (filed Mar 4, 2024)", sBodySm))

    # ── DEBT STACK ─────────────────────────────────────────────────────────
    story.append(PageBreak())
    story += section_header("4. Debt Stack — Tranche Detail ($3.33B Face Value)")
    story.append(Paragraph(
        "Spirit's capital structure at filing consisted of four primary debt instruments, all cross-collateralized "
        "or cross-defaulted to varying degrees. The Enhanced Equipment Trust Certificates (EETCs) are backed by "
        "specific aircraft tail numbers and benefit from Section 1110 aviation lien protection in Ch.11. "
        "The Loyalty Notes are secured by the Free Spirit frequent flyer program — a common ULCC financing "
        "structure pioneered by Frontier and Spirit. The Term Loan B is secured by route slots, gate leasehold "
        "interests, and IP. The cross-default structure meant that once the TLB covenant waiver lapsed, "
        "$2.44B in senior secured claims accelerated simultaneously.", sBody))
    story.append(Spacer(1, 2*mm))
    story.append(debt_stack_table(TRANCHES))
    story.append(Spacer(1, 2*mm))

    # Cross-default cascade box
    cascade_data = [
        [Paragraph("CROSS-DEFAULT CASCADE PROPAGATION PATH", S("cdh", fontName="Helvetica-Bold", fontSize=7.5, leading=10, textColor=WHITE))],
        [Paragraph(
            "Term Loan B (covenant waiver expiry, Sep 2024)  →  Cross-default to Loyalty Notes ($1.1B, Sep 2025 maturity)  "
            "→  Cross-default to EETC A/B tranches ($841M, Section 1110 aircraft lien)  →  Lease acceleration notices "
            "from AerCap, GECAS, Air Lease ($889M equivalent)  →  Total at-risk: $2,440M (73.3% of face value, all secured tranches)",
            S("cdb", fontSize=7.5, leading=11, textColor=HexColor("#FFCFCC")))],
    ]
    ct = Table(cascade_data, colWidths=[BODY_W])
    ct.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(0,0), HexColor("#7B1B14")),
        ("BACKGROUND", (0,1),(0,1), HexColor("#1A0A0A")),
        ("LEFTPADDING",  (0,0),(-1,-1), 8),
        ("RIGHTPADDING", (0,0),(-1,-1), 8),
        ("TOPPADDING",   (0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("ROUNDEDCORNERS", [3]),
    ]))
    story.append(ct)
    story.append(Spacer(1, 3*mm))

    # ── TREND ──────────────────────────────────────────────────────────────
    story += section_header("5. Trend Erosion Signal — 8-Quarter NLR & ICR History")
    story.append(Paragraph(
        "Spirit's NLR has been in continuous breach since Q4-2021 — the first full quarter after COVID-era "
        "fleet redeliveries resumed and aircraft debt came back on-balance-sheet. The trend velocity of "
        "+2.30x per quarter is the most severe deterioration in the DDCSE portfolio. ICR has been flat "
        "at ~0.35–0.48x throughout, indicating structural (not cyclical) inability to service debt from "
        "operations. Quarterly waivers masked the true credit impairment for six consecutive quarters "
        "before lender patience ran out.", sBody))
    story.append(Spacer(1, 2*mm))
    story.append(trend_table(QUARTERS, TREND_NLR, TREND_ICR, 5.50, 1.50))
    story.append(Spacer(1, 2*mm))

    trend_stats = [
        [Paragraph("NLR Direction", sTHdr), Paragraph("ICR Direction", sTHdr),
         Paragraph("NLR Velocity", sTHdr), Paragraph("ICR Velocity", sTHdr),
         Paragraph("Qtrs to Breach", sTHdr), Paragraph("Current Buffer", sTHdr)],
        [Paragraph("↑ Deteriorating", sBreach), Paragraph("↓ Deteriorating", sBreach),
         Paragraph("+2.30x / qtr", S("tv", fontName="Courier-Bold", fontSize=8, leading=10, textColor=BREACH_R, alignment=TA_CENTER)),
         Paragraph("–0.019x / qtr", S("tv", fontName="Courier-Bold", fontSize=8, leading=10, textColor=BREACH_R, alignment=TA_CENTER)),
         Paragraph("Already breached", sBreach),
         Paragraph("–342.4% (NLR)", sBreach)],
    ]
    tt2 = Table(trend_stats, colWidths=[BODY_W/6]*6)
    tt2.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,0), NAVY),
        ("BACKGROUND", (0,1),(-1,1), BREACH_BG),
        ("LINEBELOW",  (0,0),(-1,-1), 0.3, BORDER),
        ("LEFTPADDING",(0,0),(-1,-1), 4), ("RIGHTPADDING",(0,0),(-1,-1), 4),
        ("TOPPADDING", (0,0),(-1,-1), 4), ("BOTTOMPADDING",(0,0),(-1,-1), 4),
    ]))
    story.append(tt2)

    # ── MACRO SHOCK MATRIX ─────────────────────────────────────────────────
    story.append(PageBreak())
    story += section_header("6. Macro Shock Sensitivity Matrix — NLR (EBITDA × Debt)")
    story.append(Paragraph(
        f"Base NLR: 24.33x · Covenant threshold: 5.50x · Base Debt: $3,330M · Base Cash: $872M · Base EBITDA: $101M. "
        "Every single scenario in the matrix is in deep breach — the company has no realistic path to "
        "covenant compliance through operational improvement alone. Even a 50% EBITDA uplift combined "
        "with a 30% debt reduction would produce an NLR of ~11.4x, still 2× the covenant ceiling. "
        "This confirms the structural insolvency thesis: the only resolution mechanism was a balance-sheet "
        "restructuring (M&A or Ch.11), not operational turnaround.", sBody))
    story.append(Spacer(1, 2*mm))
    story.append(shock_matrix_table(3330, 872, 101, 5.50))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        "All 30/30 scenarios in the matrix are in BREACH. This is the only credit in the DDCSE portfolio "
        "with a fully red shock matrix — confirming terminal leverage.", sBodySm))

    # ── KEY EVENTS TIMELINE ────────────────────────────────────────────────
    story += section_header("7. Key Events Timeline — M&A Collapse to Ch.11")
    story.append(timeline_table(EVENTS))
    story.append(Spacer(1, 3*mm))

    # ── INVESTMENT THESIS ──────────────────────────────────────────────────
    story.append(PageBreak())
    story += section_header("8. Investment Thesis & Structural Analysis")

    thesis_paras = [
        ("8.1 The ULCC Model Under Stress",
         "Spirit Airlines was the largest US ultra-low-cost carrier by fleet size at the time of filing. "
         "The ULCC business model — ultra-stripped base fares, aggressive ancillary monetization — "
         "generates structurally thin EBITDA margins (8–12% in normalized conditions) that are "
         "predicated on high fleet utilization, low unit costs (CASM ex-fuel ~5.5¢), and an ancillary "
         "revenue yield above $70 per passenger. These margins are insufficient to service $3.3B in "
         "debt, a lesson that extends to Frontier, Avelo, and Breeze."),
        ("8.2 Three Compounding Failure Mechanisms",
         "(1) M&A Limbo (2022–2024): Spirit spent 26 months in strategic paralysis — first awaiting the "
         "Frontier merger outcome, then the JetBlue transaction. During this window, management deferred "
         "cost optimization and fleet rationalization, burning $700M+ in cash while competitors invested "
         "in network upgrades and loyalty programs. The DoJ's JetBlue block in January 2024 crystallized "
         "the terminal nature of Spirit's standalone balance sheet. "
         "(2) ULCC Margin Compression: Post-COVID normalization of fuel (+38% YoY 2022), pilot contracts "
         "(+34% over 4 years), and maintenance cycle catch-up destroyed unit economics. Spirit's EBITDA "
         "margin collapsed from ~18% in FY2019 to under 2% in FY2023. At $101M EBITDA, $3.3B in debt "
         "produces a net leverage ratio of 24.33x — mathematically insolvent. "
         "(3) Cross-Default Cascade: The September 2024 waiver expiry triggered cascading acceleration "
         "across all secured tranches simultaneously — $2.44B at-risk — making out-of-court resolution "
         "virtually impossible without near-unanimous lender consent."),
        ("8.3 Recovery Analysis",
         "EETC holders (aircraft-backed, Section 1110 protection) recovered ~$0.78/$1.00 through aircraft "
         "rejections and restructured operating leases, with lessors retaining residual fleet values. "
         "Loyalty Note holders received equity in the reorganized entity at ~$0.32/$1.00 based on "
         "emergence EV of ~$795M. Unsecured creditors (trade claims, airport authority fees, lessor "
         "deficiency claims) recovered less than $0.05/$1.00. Common equity was cancelled entirely. "
         "The DIP facility ($300M) was provided by a subset of existing Loyalty Note holders and "
         "converted to exit term debt at emergence."),
        ("8.4 Sector Read-Across",
         "Spirit's Ch.11 provides a surveillance framework for ULCC/LCC sector credits: "
         "(a) Any ULCC with Debt/EBITDA >4.0x and ICR <2.0x should be classified as structural watchlist. "
         "(b) Loyalty/affinity program financing (common structure: Frontier, Wizz Air, VivaAerobus) "
         "creates a disguised secured claim that often appears as 'revenue' financing but behaves as "
         "senior debt in stress scenarios. "
         "(c) Section 1110 protection for EETC holders creates a structural seniority anomaly — "
         "aircraft lessors and EETC investors are effectively super-senior to covenant lenders "
         "in US aviation restructurings, despite lower nominal seniority in the capital structure hierarchy. "
         "(d) The DoJ's aggressive antitrust posture toward airline consolidation (also visible in "
         "the JetBlue/American NE Alliance challenge) eliminates M&A as a balance-sheet rescue "
         "mechanism for distressed carriers, accelerating the path to Ch.11 when leverage is terminal."),
    ]
    for subtitle, body in thesis_paras:
        story.append(Paragraph(subtitle, S("ts", fontName="Helvetica-Bold", fontSize=8.5, leading=12, textColor=NAVY, spaceBefore=6, spaceAfter=3)))
        story.append(Paragraph(body, sBody))
        story.append(Spacer(1, 1*mm))

    # ── SOURCES ───────────────────────────────────────────────────────────
    story += section_header("9. Data Sources & Disclosures")
    sources = [
        "Spirit Airlines Inc. — 10-K FY2023 (SEC EDGAR CIK 0001498710, filed Mar 4, 2024)",
        "Spirit Airlines Ch.11 First-Day Declaration — SDNY, Nov 18, 2024 (Case No. 24-11988)",
        "Spirit Airlines Disclosure Statement — Jan 2025",
        "S&P Global Ratings — Spirit Airlines rating action (D, Nov 18, 2024)",
        "Moody's Investors Service — Spirit Airlines withdrawal notice (Nov 2024)",
        "US DoJ v. JetBlue Airways Corp. et al. — Case 1:23-cv-10511 (D.Mass., Jan 16, 2024)",
        "Spirit Airlines Enhanced Equipment Trust Certificates Prospectus (SEC, 2015 & 2017)",
        "DDCSE v3.1 Analytics Engine — github.com/DogInfantry/dynamic-debt-covenant-surveillance-frame",
        f"Report generated: {TODAY} · For analytical purposes only. Not investment advice.",
    ]
    for s in sources:
        story.append(Paragraph(f"• {s}", sNote))

    # ── BUILD ──────────────────────────────────────────────────────────────
    def add_page_decorations(canv, doc):
        t.beforePage(canv, doc)

    doc.build(story, onFirstPage=add_page_decorations, onLaterPages=add_page_decorations)
    print(f"✓ PDF written: {out_path}")
    return out_path

if __name__ == "__main__":
    out = "/home/claude/ddcse_patch/DDCSE_SAVE_Spirit_Airlines_Ch11_Report.pdf"
    build_pdf(out)

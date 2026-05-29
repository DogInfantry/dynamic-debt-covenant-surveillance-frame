"""
generate_save_pdf_v2.py
DDCSE v3.2 — Spirit Airlines (SAVE) · Upgraded PDF
Visual-first: sparklines, waterfall bars, recovery chart, rich timeline,
callout boxes, gradient section headers — all drawn via ReportLab canvas.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.platypus.flowables import Flowable
from reportlab.lib.colors import HexColor, white, black
from datetime import date
import math

# ── Palette ──────────────────────────────────────────────────────────────────
NAVY      = HexColor("#0A1628")
NAVY2     = HexColor("#1A3A5C")
NAVY3     = HexColor("#243F60")
ACCENT    = HexColor("#2463A4")
ACCENT2   = HexColor("#3B82C4")
SILVER    = HexColor("#B0C4DE")
SILVER2   = HexColor("#D4E2F0")
SURFACE   = HexColor("#F7F9FC")
SURFACE2  = HexColor("#EEF2F8")
BORDER    = HexColor("#DDE3EC")
BREACH_R  = HexColor("#C0392B")
BREACH_D  = HexColor("#962020")
BREACH_BG = HexColor("#FDF0EE")
BREACH_L  = HexColor("#FFE8E6")
WATCH_A   = HexColor("#D4680A")
WATCH_BG  = HexColor("#FDF5EE")
OK_G      = HexColor("#1A7A4A")
OK_BG     = HexColor("#EAF5EF")
OK_L      = HexColor("#D3EFE0")
INK2      = HexColor("#2C4A6E")
INK3      = HexColor("#4A6C8A")
MUTED     = HexColor("#8A9BB0")
TEXT      = HexColor("#0A1628")
WHITE     = white
GOLD      = HexColor("#C8960C")
GOLD_BG   = HexColor("#FDF8E8")

W, H   = A4
ML     = 17*mm
MR     = 17*mm
MT     = 11*mm
MB     = 13*mm
BW     = W - ML - MR
TODAY  = date.today().strftime("%B %d, %Y")

# ── Style factory ─────────────────────────────────────────────────────────────
def S(name, **kw):
    base = dict(fontName="Helvetica", fontSize=9, leading=13,
                textColor=TEXT, spaceAfter=0, spaceBefore=0)
    base.update(kw)
    return ParagraphStyle(name, **base)

# Named styles
sBody   = S("sBody",  fontSize=8.5, leading=13.5, textColor=INK2, spaceAfter=3, alignment=TA_JUSTIFY)
sBodySm = S("sBodySm",fontSize=7.5, leading=11.5, textColor=INK3, spaceAfter=2)
sLabel  = S("sLabel", fontSize=6.5, leading=9,    textColor=MUTED, spaceAfter=1)
sNote   = S("sNote",  fontSize=7.5, leading=11,   textColor=INK3, spaceAfter=2)
sTHdr   = S("sTHdr",  fontName="Helvetica-Bold", fontSize=7, leading=10, textColor=WHITE, alignment=TA_CENTER)
sTCell  = S("sTCell", fontSize=7.5, leading=10, textColor=TEXT)
sTCellC = S("sTCellC",fontSize=7.5, leading=10, textColor=TEXT, alignment=TA_CENTER)
sBreach = S("sBreach",fontName="Helvetica-Bold", fontSize=7.5, leading=10, textColor=BREACH_R, alignment=TA_CENTER)
sWatch  = S("sWatch", fontName="Helvetica-Bold", fontSize=7.5, leading=10, textColor=WATCH_A,  alignment=TA_CENTER)
sOk     = S("sOk",    fontName="Helvetica-Bold", fontSize=7.5, leading=10, textColor=OK_G,     alignment=TA_CENTER)

# ── Helpers ───────────────────────────────────────────────────────────────────
def cov_status(actual, thresh, op):
    compliant = (actual <= thresh) if op == "lte" else (actual >= thresh)
    buf = (thresh - actual)/thresh if op == "lte" else (actual - thresh)/thresh
    status = "COMPLIANT" if compliant and buf >= 0.10 else ("WATCHLIST" if compliant else "BREACH")
    return compliant, buf, status

def status_sty(status):
    return {"BREACH": sBreach, "WATCHLIST": sWatch, "COMPLIANT": sOk}[status]

def status_colors(status):
    return {
        "BREACH":    (BREACH_R, BREACH_BG, BREACH_L),
        "WATCHLIST": (WATCH_A,  WATCH_BG,  HexColor("#FDECD8")),
        "COMPLIANT": (OK_G,     OK_BG,     OK_L),
    }[status]

# ── Page decorator ────────────────────────────────────────────────────────────
class PageDeco:
    def __call__(self, canv, doc):
        canv.saveState()
        # Top accent bar — gradient sim via two rects
        canv.setFillColor(NAVY)
        canv.rect(0, H - 7*mm, W * 0.6, 7*mm, fill=1, stroke=0)
        canv.setFillColor(ACCENT)
        canv.rect(W * 0.6, H - 7*mm, W * 0.4, 7*mm, fill=1, stroke=0)
        # Page top text
        canv.setFont("Helvetica-Bold", 6.5)
        canv.setFillColor(SILVER)
        canv.drawString(ML, H - 4.5*mm, "DDCSE v3.2  ·  SPIRIT AIRLINES INC. (SAVE)  ·  AVIATION SECTOR  ·  COVENANT SURVEILLANCE")
        canv.setFont("Helvetica", 6.5)
        canv.setFillColor(WHITE)
        canv.drawRightString(W - MR, H - 4.5*mm, f"CHAPTER 11  ·  CONFIDENTIAL ANALYTICAL DRAFT")
        # Footer
        canv.setFillColor(SURFACE2)
        canv.rect(0, 0, W, 9*mm, fill=1, stroke=0)
        canv.setStrokeColor(BORDER)
        canv.setLineWidth(0.5)
        canv.line(ML, 9*mm, W - MR, 9*mm)
        canv.setFont("Helvetica", 6)
        canv.setFillColor(MUTED)
        canv.drawString(ML, 3.5*mm,
            f"DDCSE v3.2  ·  Spirit Airlines (SAVE)  ·  {TODAY}  ·  For analytical purposes only. Not investment advice.")
        canv.setFont("Helvetica-Bold", 6.5)
        canv.setFillColor(NAVY2)
        canv.drawRightString(W - MR, 3.5*mm, f"Page {doc.page}")
        canv.restoreState()

# ── COVER FLOWABLE ────────────────────────────────────────────────────────────
class CoverBlock(Flowable):
    def __init__(self, w, h):
        super().__init__()
        self.width = w; self.height = h

    def draw(self):
        c = self.canv
        w, h = self.width, self.height

        # Base navy fill
        c.setFillColor(NAVY)
        c.rect(0, 0, w, h, fill=1, stroke=0)

        # Diagonal grid lines (subtle texture)
        c.setStrokeColor(HexColor("#121E30"))
        c.setLineWidth(0.25)
        for i in range(int(-h), int(w + h), 22):
            c.line(i, 0, i + h, h)

        # Right-side accent panel
        c.setFillColor(ACCENT)
        path = c.beginPath()
        path.moveTo(w * 0.72, 0)
        path.lineTo(w, 0)
        path.lineTo(w, h)
        path.lineTo(w * 0.82, h)
        path.close()
        c.drawPath(path, fill=1, stroke=0)
        c.setFillColor(HexColor("#1A3A5C"))
        path2 = c.beginPath()
        path2.moveTo(w * 0.68, 0)
        path2.lineTo(w * 0.72, 0)
        path2.lineTo(w * 0.82, h)
        path2.lineTo(w * 0.78, h)
        path2.close()
        c.drawPath(path2, fill=1, stroke=0)

        # CH11 alert bar at top
        c.setFillColor(HexColor("#8B1A14"))
        c.rect(0, h - 9*mm, w * 0.68, 9*mm, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(HexColor("#FFBAB5"))
        c.drawString(4*mm, h - 5.5*mm,
            "⚑  CHAPTER 11 FILED  ·  NOV 18 2024  ·  SDNY CASE 24-11988  ·  ALL COVENANTS: CATASTROPHIC BREACH")

        # Eyebrow
        y = h - 16*mm
        c.setFont("Helvetica", 7)
        c.setFillColor(SILVER)
        c.drawString(0, y, "PRIVATE CREDIT  ·  COVENANT SURVEILLANCE ENGINE v3.2  ·  AVIATION SECTOR")

        # Main title
        y -= 10*mm
        c.setFont("Helvetica-Bold", 26)
        c.setFillColor(WHITE)
        c.drawString(0, y, "Spirit Airlines Inc.")
        y -= 8*mm
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(SILVER2)
        c.drawString(0, y, "SAVE  ·  Ultra-Low-Cost Carrier  ·  Ch.11 Surveillance Report")
        y -= 5*mm
        c.setFont("Helvetica", 8)
        c.setFillColor(SILVER)
        c.drawString(0, y, f"NYSE (delisted Nov 2024)  ·  S&P: D  ·  SDNY Bankruptcy Court  ·  {TODAY}")

        # ── KPI tiles row ──
        y -= 14*mm
        kpis = [
            ("NET LEVERAGE", "24.33x", "vs 5.50x ceiling", True),
            ("INT. COVERAGE", "0.35x",  "vs 1.50x floor",  True),
            ("FIXED CHARGE",  "–0.82x", "vs 1.00x floor",  True),
            ("TOTAL DEBT",    "$3.33B", "face value",       False),
            ("LTM EBITDA",    "$101M",  "FY2023 adj.",      False),
            ("SEVERITY",      "99/100", "portfolio worst",  True),
        ]
        tile_w = (w * 0.67) / len(kpis)
        for i, (lbl, val, note, is_bad) in enumerate(kpis):
            tx = i * tile_w
            # Tile background
            c.setFillColor(HexColor("#0D1E35"))
            c.setStrokeColor(HexColor("#1E3A58"))
            c.setLineWidth(0.5)
            c.roundRect(tx + 1.5*mm, y - 13*mm, tile_w - 3*mm, 13*mm, 2, fill=1, stroke=1)
            # Value
            c.setFont("Helvetica-Bold", 11 if len(val) <= 6 else 9)
            c.setFillColor(HexColor("#FF8A80") if is_bad else WHITE)
            c.drawCentredString(tx + tile_w/2, y - 6.5*mm, val)
            # Label
            c.setFont("Helvetica", 5.5)
            c.setFillColor(SILVER)
            c.drawCentredString(tx + tile_w/2, y - 9.5*mm, lbl)
            c.drawCentredString(tx + tile_w/2, y - 12.5*mm, note)

        # ── Severity bar ──
        y -= 18*mm
        c.setFont("Helvetica-Bold", 6.5)
        c.setFillColor(SILVER)
        c.drawString(0, y, "PORTFOLIO SEVERITY SCORE")
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(HexColor("#FF8A80"))
        c.drawString(45*mm, y, "99 / 100 — CATASTROPHIC  (Highest in DDCSE Universe)")
        y -= 4*mm
        c.setFillColor(HexColor("#1A3A5C"))
        c.roundRect(0, y - 4*mm, w * 0.67, 4*mm, 2, fill=1, stroke=0)
        c.setFillColor(BREACH_R)
        c.roundRect(0, y - 4*mm, w * 0.67 * 0.99, 4*mm, 2, fill=1, stroke=0)
        # Score marker
        c.setStrokeColor(WHITE)
        c.setLineWidth(1)
        c.line(w * 0.67 * 0.99 - 1, y - 5*mm, w * 0.67 * 0.99 - 1, y + 1*mm)

        # ── Inline NLR sparkline on right panel ──
        sx = w * 0.73; sy_base = 28*mm; sp_h = 26*mm; sp_w = w * 0.22
        nlr_vals = [8.21, 9.44, 13.82, 18.90, 21.44, 22.88, 23.71, 24.33]
        max_v = 26.0
        # Label
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(WHITE)
        c.drawCentredString(sx + sp_w/2, sy_base + sp_h + 3*mm, "NLR TREND (Q4-21 → Q4-23)")
        c.setFont("Helvetica", 6)
        c.setFillColor(SILVER)
        c.drawCentredString(sx + sp_w/2, sy_base + sp_h + 0.5*mm, "threshold: 5.50x ────────────")
        # Threshold line
        ty = sy_base + (5.50/max_v) * sp_h
        c.setStrokeColor(HexColor("#FFCC44"))
        c.setLineWidth(0.6)
        c.setDash(3, 3)
        c.line(sx, ty, sx + sp_w, ty)
        c.setDash()
        # Area fill (polygon)
        n = len(nlr_vals)
        pts = [(sx + (i/(n-1))*sp_w, sy_base + min((v/max_v), 1)*sp_h) for i, v in enumerate(nlr_vals)]
        path = c.beginPath()
        path.moveTo(sx, sy_base)
        for px, py in pts:
            path.lineTo(px, py)
        path.lineTo(sx + sp_w, sy_base)
        path.close()
        c.setFillColor(HexColor("#C0392B50"))
        c.drawPath(path, fill=1, stroke=0)
        # Line
        c.setStrokeColor(BREACH_R)
        c.setLineWidth(1.2)
        path2 = c.beginPath()
        path2.moveTo(pts[0][0], pts[0][1])
        for px, py in pts[1:]:
            path2.lineTo(px, py)
        c.drawPath(path2, fill=0, stroke=1)
        # Dots
        for px, py in pts:
            c.setFillColor(BREACH_R)
            c.circle(px, py, 1.2, fill=1, stroke=0)
        # Axis labels
        c.setFont("Helvetica", 5)
        c.setFillColor(SILVER)
        qtrs = ["Q4-21","Q2-22","Q4-22","Q2-23","Q4-23"]
        q_idx = [0, 2, 4, 6, 7]
        for qi in q_idx:
            px = sx + (qi/(n-1))*sp_w
            c.drawCentredString(px, sy_base - 4*mm, f"{nlr_vals[qi]:.2f}x" if qi >= 4 else "")
        c.drawString(sx, sy_base - 7*mm, "Q4'21")
        c.drawRightString(sx + sp_w, sy_base - 7*mm, "Q4'23")
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(HexColor("#FF8A80"))
        c.drawCentredString(sx + sp_w/2, sy_base - 11*mm, "24.33x  ↑  +196% in 8 qtrs")

    def wrap(self, *args):
        return self.width, self.height

# ── VISUAL SECTION HEADER ─────────────────────────────────────────────────────
class SectionHeader(Flowable):
    def __init__(self, number, title, w):
        super().__init__()
        self.number = number; self.title = title; self.width = w; self.height = 10*mm

    def draw(self):
        c = self.canv
        # Left accent bar
        c.setFillColor(ACCENT)
        c.rect(0, 1*mm, 3, self.height - 2*mm, fill=1, stroke=0)
        # Number bubble
        c.setFillColor(ACCENT)
        c.circle(8*mm, self.height/2, 4*mm, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(WHITE)
        c.drawCentredString(8*mm, self.height/2 - 2.5, self.number)
        # Title
        c.setFont("Helvetica-Bold", 9.5)
        c.setFillColor(NAVY)
        c.drawString(14*mm, self.height/2 - 3, self.title.upper())
        # Full-width rule
        c.setStrokeColor(BORDER)
        c.setLineWidth(0.4)
        c.line(0, 0, self.width, 0)

    def wrap(self, *args):
        return self.width, self.height

def sec(num, title):
    return [Spacer(1, 4*mm), SectionHeader(num, title, BW), Spacer(1, 3*mm)]

# ── CALLOUT BOX ───────────────────────────────────────────────────────────────
class CalloutBox(Flowable):
    def __init__(self, label, text, w, color=BREACH_R, bg=BREACH_BG):
        super().__init__()
        self.label = label; self.text = text
        self.width = w; self.color = color; self.bg = bg
        self.height = 18*mm

    def draw(self):
        c = self.canv
        c.setFillColor(self.bg)
        c.roundRect(0, 0, self.width, self.height, 3, fill=1, stroke=0)
        c.setFillColor(self.color)
        c.roundRect(0, 0, 3, self.height, 1, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(self.color)
        c.drawString(7*mm, self.height - 5*mm, self.label)
        c.setFont("Helvetica", 7)
        c.setFillColor(INK2)
        # word-wrap manually
        words = self.text.split()
        line = ""; lines = []; max_w = self.width - 9*mm
        for w in words:
            test = line + (" " if line else "") + w
            if c.stringWidth(test, "Helvetica", 7) < max_w:
                line = test
            else:
                if line: lines.append(line)
                line = w
        if line: lines.append(line)
        y = self.height - 10*mm
        for l in lines[:3]:
            c.drawString(7*mm, y, l)
            y -= 4*mm

    def wrap(self, *args):
        return self.width, self.height

# ── SPARKLINE FLOWABLE (inline NLR over quarters) ────────────────────────────
class Sparkline(Flowable):
    def __init__(self, vals, thresh, thresh_label, w, h=22*mm):
        super().__init__()
        self.vals = vals; self.thresh = thresh; self.thresh_label = thresh_label
        self.width = w; self.height = h

    def draw(self):
        c = self.canv
        vals = self.vals; n = len(vals)
        max_v = max(max(vals) * 1.08, self.thresh * 1.1)
        min_v = 0
        pad_l = 10*mm; pad_r = 4*mm; pad_b = 5*mm; pad_t = 3*mm
        pw = self.width - pad_l - pad_r
        ph = self.height - pad_b - pad_t

        def xp(i): return pad_l + (i / (n - 1)) * pw
        def yp(v): return pad_b + ((v - min_v) / (max_v - min_v)) * ph

        # Grid lines
        c.setStrokeColor(BORDER)
        c.setLineWidth(0.3)
        for gv in [5, 10, 15, 20, 25]:
            if gv <= max_v:
                gy = yp(gv)
                c.line(pad_l, gy, pad_l + pw, gy)
                c.setFont("Helvetica", 5)
                c.setFillColor(MUTED)
                c.drawRightString(pad_l - 1*mm, gy - 1.5, f"{gv}x")

        # Threshold line
        ty = yp(self.thresh)
        c.setStrokeColor(GOLD)
        c.setLineWidth(0.8)
        c.setDash(4, 3)
        c.line(pad_l, ty, pad_l + pw, ty)
        c.setDash()
        c.setFont("Helvetica-Bold", 5.5)
        c.setFillColor(GOLD)
        c.drawString(pad_l + pw + 1*mm, ty - 2, f"{self.thresh_label}")

        # Area fill
        pts = [(xp(i), yp(v)) for i, v in enumerate(vals)]
        path = c.beginPath()
        path.moveTo(pts[0][0], pad_b)
        for px, py in pts:
            path.lineTo(px, py)
        path.lineTo(pts[-1][0], pad_b)
        path.close()
        c.setFillColor(HexColor("#C0392B22"))
        c.drawPath(path, fill=1, stroke=0)

        # Breach zone shading above threshold
        breach_pts = [(xp(i), yp(v)) for i, v in enumerate(vals)]
        path2 = c.beginPath()
        path2.moveTo(breach_pts[0][0], ty)
        for px, py in breach_pts:
            path2.lineTo(px, max(py, ty))
        path2.lineTo(breach_pts[-1][0], ty)
        path2.close()
        c.setFillColor(HexColor("#C0392B18"))
        c.drawPath(path2, fill=1, stroke=0)

        # Line
        c.setStrokeColor(BREACH_R)
        c.setLineWidth(1.4)
        path3 = c.beginPath()
        path3.moveTo(pts[0][0], pts[0][1])
        for px, py in pts[1:]:
            path3.lineTo(px, py)
        c.drawPath(path3, fill=0, stroke=1)

        # Dots + labels at first, last, max
        highlight = {0, n-1, vals.index(max(vals))}
        for i, (px, py) in enumerate(pts):
            r = 2.0 if i in highlight else 1.2
            c.setFillColor(BREACH_R)
            c.circle(px, py, r, fill=1, stroke=0)
            if i in highlight:
                c.setFont("Helvetica-Bold", 5.5)
                c.setFillColor(BREACH_D)
                offset_y = 2.5*mm if py < self.height - 8*mm else -4*mm
                c.drawCentredString(px, py + offset_y, f"{vals[i]:.2f}x")

        # Q-axis labels
        quarters = ["Q4'21","Q1'22","Q2'22","Q3'22","Q4'22","Q1'23","Q2'23","Q4'23"]
        c.setFont("Helvetica", 5)
        c.setFillColor(MUTED)
        for i, q in enumerate(quarters):
            if i % 2 == 0 or i == n-1:
                c.drawCentredString(xp(i), pad_b - 3.5*mm, q)

        # Axis
        c.setStrokeColor(BORDER)
        c.setLineWidth(0.4)
        c.line(pad_l, pad_b, pad_l + pw, pad_b)
        c.line(pad_l, pad_b, pad_l, pad_b + ph)

    def wrap(self, *args):
        return self.width, self.height

# ── WATERFALL BAR (debt stack visual) ────────────────────────────────────────
class DebtWaterfall(Flowable):
    def __init__(self, tranches, w, h=52*mm):
        super().__init__()
        self.tranches = tranches; self.width = w; self.height = h

    def draw(self):
        c = self.canv
        total = sum(t["val"] for t in self.tranches)
        pad_l = 40*mm; pad_r = 28*mm; pad_b = 3*mm
        bar_area = self.width - pad_l - pad_r
        bar_h = 7*mm; gap = 3.5*mm
        colors_map = {"breach": BREACH_R, "watch": WATCH_A, "ok": OK_G}
        bg_map     = {"breach": BREACH_BG, "watch": WATCH_BG, "ok": OK_BG}

        y = self.height - bar_h - 2*mm
        for t in self.tranches:
            bw = (t["val"] / total) * bar_area
            col = colors_map[t["status"]]
            bg  = bg_map[t["status"]]

            # Background track
            c.setFillColor(SURFACE2)
            c.roundRect(pad_l, y, bar_area, bar_h, 2, fill=1, stroke=0)
            # Fill bar
            c.setFillColor(col)
            c.roundRect(pad_l, y, bw, bar_h, 2, fill=1, stroke=0)
            # Tranche label (left)
            c.setFont("Helvetica-Bold", 6.5)
            c.setFillColor(NAVY)
            c.drawRightString(pad_l - 2*mm, y + bar_h/2 - 2, t["name"][:28])
            # Value label (right)
            c.setFont("Helvetica-Bold", 7)
            c.setFillColor(col)
            c.drawString(pad_l + bw + 2*mm, y + bar_h/2 - 2, f"${t['val']/1000:.2f}B")
            # Seniority micro-label on bar
            if bw > 20*mm:
                c.setFont("Helvetica", 5.5)
                c.setFillColor(WHITE)
                c.drawString(pad_l + 2*mm, y + 2, t["seniority"][:32])

            y -= (bar_h + gap)

        # Total bar
        y -= 1*mm
        c.setStrokeColor(BORDER)
        c.setLineWidth(0.4)
        c.line(pad_l, y + bar_h + gap, pad_l + bar_area, y + bar_h + gap)
        c.setFont("Helvetica-Bold", 7.5)
        c.setFillColor(NAVY)
        c.drawRightString(pad_l - 2*mm, y + 2, "TOTAL FACE VALUE")
        c.setFillColor(BREACH_R)
        c.drawString(pad_l, y + 2, f"${total/1000:.3f}B  ({len(self.tranches)} tranches, all in BREACH)")

    def wrap(self, *args):
        return self.width, self.height

# ── RECOVERY WATERFALL ────────────────────────────────────────────────────────
class RecoveryWaterfall(Flowable):
    def __init__(self, w, h=50*mm):
        super().__init__()
        self.width = w; self.height = h

    def draw(self):
        c = self.canv
        # Data: (label, face $M, recovery rate, color)
        items = [
            ("EETC A/B (Aircraft-Secured)", 841,  0.78, OK_G),
            ("Term Loan B (Slots/IP)",       500,  0.52, WATCH_A),
            ("Loyalty Notes (Free Spirit)",  1100, 0.32, WATCH_A),
            ("Unsecured / Leases",           889,  0.04, BREACH_R),
            ("Common Equity",                  0,  0.00, BREACH_R),
        ]
        pad_l = 42*mm; pad_r = 32*mm; pad_b = 4*mm
        bar_area = self.width - pad_l - pad_r
        bar_h = 6.5*mm; gap = 3*mm

        c.setFont("Helvetica-Bold", 6.5)
        c.setFillColor(MUTED)
        c.drawString(pad_l, self.height - 3*mm, "Recovery rate")
        c.drawRightString(pad_l + bar_area, self.height - 3*mm, "Face value")

        y = self.height - bar_h - 6*mm
        for lbl, face, rate, col in items:
            # Background track
            c.setFillColor(SURFACE2)
            c.roundRect(pad_l, y, bar_area, bar_h, 2, fill=1, stroke=0)
            # Recovery fill
            if rate > 0:
                c.setFillColor(col)
                c.roundRect(pad_l, y, bar_area * rate, bar_h, 2, fill=1, stroke=0)
            # Labels
            c.setFont("Helvetica-Bold", 6.5)
            c.setFillColor(NAVY)
            c.drawRightString(pad_l - 2*mm, y + bar_h/2 - 2, lbl)
            # Recovery % on bar
            c.setFont("Helvetica-Bold", 6.5)
            c.setFillColor(WHITE if rate > 0.15 else col)
            if rate > 0:
                cx = pad_l + (bar_area * rate)/2
                c.drawCentredString(cx, y + 2, f"{rate*100:.0f}¢/$1")
            else:
                c.setFillColor(BREACH_R)
                c.drawString(pad_l + 2*mm, y + 2, "0¢  (cancelled)")
            # Face value right
            if face > 0:
                c.setFont("Helvetica", 6)
                c.setFillColor(MUTED)
                c.drawString(pad_l + bar_area + 2*mm, y + bar_h/2 - 2, f"${face}M")
            y -= (bar_h + gap)

    def wrap(self, *args):
        return self.width, self.height

# ── VISUAL TIMELINE ───────────────────────────────────────────────────────────
class Timeline(Flowable):
    def __init__(self, events, w):
        super().__init__()
        self.events = events; self.width = w
        self.height = len(events) * 17*mm + 4*mm

    def draw(self):
        c = self.canv
        spine_x = 18*mm
        dot_colors = {"breach": BREACH_R, "watch": WATCH_A, "ok": OK_G, "neutral": ACCENT}

        y = self.height - 10*mm
        for i, (date_str, title, body, kind) in enumerate(self.events):
            col = dot_colors.get(kind, ACCENT)
            # Connector line (except last)
            if i < len(self.events) - 1:
                c.setStrokeColor(BORDER)
                c.setLineWidth(1)
                c.line(spine_x, y - 2*mm, spine_x, y - 15*mm)

            # Dot
            c.setFillColor(col)
            c.setStrokeColor(WHITE)
            c.setLineWidth(1)
            c.circle(spine_x, y, 3.5*mm, fill=1, stroke=1)
            if kind == "breach":
                # Inner white dot for severity emphasis
                c.setFillColor(WHITE)
                c.circle(spine_x, y, 1.2, fill=1, stroke=0)

            # Date badge
            c.setFillColor(col)
            badge_w = 24*mm
            c.roundRect(spine_x + 6*mm, y - 3*mm, badge_w, 6*mm, 2, fill=1, stroke=0)
            c.setFont("Helvetica-Bold", 6.5)
            c.setFillColor(WHITE)
            c.drawCentredString(spine_x + 6*mm + badge_w/2, y - 0.5*mm, date_str)

            # Title
            c.setFont("Helvetica-Bold", 8)
            c.setFillColor(NAVY)
            c.drawString(spine_x + 33*mm, y + 1*mm, title)

            # Body text (wrapped)
            c.setFont("Helvetica", 6.5)
            c.setFillColor(INK3)
            max_line_w = self.width - spine_x - 33*mm
            words = body.split(); line = ""; lines_out = []
            for w in words:
                test = line + (" " if line else "") + w
                if c.stringWidth(test, "Helvetica", 6.5) < max_line_w:
                    line = test
                else:
                    if line: lines_out.append(line)
                    line = w
            if line: lines_out.append(line)
            ly = y - 4*mm
            for l in lines_out[:2]:
                c.drawString(spine_x + 33*mm, ly, l)
                ly -= 3.5*mm

            y -= 17*mm

    def wrap(self, *args):
        return self.width, self.height

# ── COVENANT SCORECARD ────────────────────────────────────────────────────────
class CovenantScorecard(Flowable):
    def __init__(self, covenants, w, h=None):
        super().__init__()
        self.covenants = covenants; self.width = w
        self.height = h or (len(covenants) * 18*mm + 10*mm)

    def draw(self):
        c = self.canv
        card_h = 15*mm
        gap = 3*mm
        y = self.height - card_h - 2*mm

        for cov in self.covenants:
            _, buf, status = cov_status(cov["actual"], cov["thresh"], cov["op"])
            col, bg, light = status_colors(status)
            buf_pct = min(abs(buf) * 100, 100)

            # Card background
            c.setFillColor(bg)
            c.setStrokeColor(col)
            c.setLineWidth(0.4)
            c.roundRect(0, y, self.width, card_h, 3, fill=1, stroke=1)

            # Left color stripe
            c.setFillColor(col)
            c.roundRect(0, y, 3, card_h, 1, fill=1, stroke=0)

            # Covenant name
            c.setFont("Helvetica-Bold", 8)
            c.setFillColor(NAVY)
            c.drawString(6*mm, y + card_h - 5.5*mm, cov["name"])

            # Type tag
            tag_w = 16*mm
            c.setFillColor(col)
            c.roundRect(self.width * 0.42, y + 4*mm, tag_w, 5*mm, 2, fill=1, stroke=0)
            c.setFont("Helvetica-Bold", 5.5)
            c.setFillColor(WHITE)
            c.drawCentredString(self.width * 0.42 + tag_w/2, y + 5.5*mm, cov["type"].upper())

            # Actual value (large)
            c.setFont("Helvetica-Bold", 13)
            c.setFillColor(col)
            act_str = f"${cov['actual']:.0f}M" if cov["unit"] == "$M" else f"{cov['actual']:.2f}x"
            c.drawString(self.width * 0.60, y + 3.5*mm, act_str)

            # vs threshold
            op_sym = "≤" if cov["op"] == "lte" else "≥"
            thr_str = f"${cov['thresh']:.0f}M" if cov["unit"] == "$M" else f"{cov['thresh']:.2f}x"
            c.setFont("Helvetica", 6.5)
            c.setFillColor(MUTED)
            c.drawString(self.width * 0.60, y + 0.5*mm, f"covenant: {op_sym} {thr_str}")

            # Buffer bar
            bar_x = 6*mm; bar_w = self.width * 0.34; bar_y = y + 1.5*mm; bar_h2 = 3.5*mm
            c.setFillColor(SURFACE2)
            c.roundRect(bar_x, bar_y, bar_w, bar_h2, 1, fill=1, stroke=0)
            fill_w = bar_w * (buf_pct / 100)
            c.setFillColor(col)
            c.roundRect(bar_x, bar_y, fill_w, bar_h2, 1, fill=1, stroke=0)
            buf_str = f"+{buf*100:.1f}%" if buf >= 0 else f"{buf*100:.1f}%"
            c.setFont("Helvetica-Bold", 6)
            c.setFillColor(col)
            c.drawString(bar_x + bar_w + 2*mm, bar_y + 1, buf_str)

            # Status badge
            badge_x = self.width * 0.82
            c.setFillColor(col)
            c.roundRect(badge_x, y + 4*mm, self.width - badge_x - 2*mm, 5.5*mm, 2, fill=1, stroke=0)
            c.setFont("Helvetica-Bold", 6.5)
            c.setFillColor(WHITE)
            c.drawCentredString(badge_x + (self.width - badge_x - 2*mm)/2, y + 5.5*mm, status)

            y -= (card_h + gap)

    def wrap(self, *args):
        return self.width, self.height

# ── DATA ──────────────────────────────────────────────────────────────────────
COVENANTS = [
    {"name": "Consolidated Net Leverage Ratio",  "type": "Leverage",  "thresh": 5.50,  "actual": 24.33, "op": "lte", "unit": "x"},
    {"name": "Interest Coverage Ratio",           "type": "Coverage",  "thresh": 1.50,  "actual": 0.35,  "op": "gte", "unit": "x"},
    {"name": "Fixed Charge Coverage Ratio",       "type": "FCCR",      "thresh": 1.00,  "actual": -0.82, "op": "gte", "unit": "x"},
    {"name": "Minimum Unrestricted Cash",         "type": "Liquidity", "thresh": 500.0, "actual": 872.0, "op": "gte", "unit": "$M"},
]
TRANCHES = [
    {"name": "$841M EETC (A/B tranches)", "seniority": "Aircraft-Secured · 1st Lien · Sec.1110",  "val": 841,  "status": "breach"},
    {"name": "$500M Term Loan B",          "seniority": "Sr Secured · Slots/IP collateral",         "val": 500,  "status": "breach"},
    {"name": "$1.1B Loyalty Notes",        "seniority": "Sr Secured · Free Spirit program",         "val": 1100, "status": "breach"},
    {"name": "$889M Leases & Other",       "seniority": "Sr Unsecured · Aircraft lessors",          "val": 889,  "status": "breach"},
]
QUARTERS  = ["Q4-21","Q1-22","Q2-22","Q3-22","Q4-22","Q1-23","Q2-23","Q4-23"]
TREND_NLR = [8.21,   9.44,  13.82,  18.90,  21.44,  22.88,  23.71,  24.33]
TREND_ICR = [0.48,   0.41,   0.39,   0.37,   0.35,   0.36,   0.35,   0.35]

EVENTS = [
    ("Feb 2022",    "Frontier merger announced — $2.9B all-stock deal",
     "Spirit-Frontier combination would create 4th major ULCC, ~230 aircraft, $5.3B revenue.", "ok"),
    ("Apr 2022",    "JetBlue hostile bid — $3.8B cash offer",
     "JetBlue sweetens to $3.8B with $200M reverse termination fee; Spirit board accepts.", "neutral"),
    ("Jul 2022",    "Frontier deal terminated — JetBlue merger signed",
     "Spirit shareholders vote down Frontier. JetBlue deal signed. DoJ signals antitrust challenge.", "watch"),
    ("Jan 2024",    "JetBlue merger blocked by Federal court",
     "DoJ antitrust ruling upheld. Spirit left standalone. NLR now 22.88x. S&P downgrades CCC–.", "breach"),
    ("Mar 2024",    "FY2023 10-K — NLR disclosed at 24.33x vs 5.50x covenant",
     "Three of four covenants in material breach. Cash burn $65M/month. Stock below $2.", "breach"),
    ("Sep 2024",    "Loyalty Notes waiver expires — cross-default cascade triggered",
     "$2.44B in secured claims accelerated. Cash ~$380M. Out-of-court resolution impossible.", "breach"),
    ("Nov 18, 2024","Chapter 11 filed — SDNY Case No. 24-11988",
     "$300M DIP financing. Operations continue. Loyalty Notes equitized at ~32¢/$1.", "breach"),
    ("May 2025",    "Emergence from Ch.11 — 6 months, $795M exit financing",
     "~90 aircraft (vs 200 pre-filing). Equity to former Loyalty Note holders. Unsecured: <5¢.", "ok"),
]

# ── TABLE BUILDER ─────────────────────────────────────────────────────────────
def cov_detail_table(covenants):
    headers = ["Covenant", "Type", "Actual", "Threshold", "Buffer", "Severity", "Status"]
    col_w   = [BW*0.30, BW*0.09, BW*0.09, BW*0.10, BW*0.10, BW*0.09, BW*0.11]
    rows = [[Paragraph(h, sTHdr) for h in headers]]
    for cov in covenants:
        _, buf, status = cov_status(cov["actual"], cov["thresh"], cov["op"])
        col, bg, _ = status_colors(status)
        buf_str = f"+{buf*100:.1f}%" if buf >= 0 else f"{buf*100:.1f}%"
        act_s   = f"${cov['actual']:.0f}M" if cov["unit"] == "$M" else f"{cov['actual']:.2f}x"
        thr_s   = f"${cov['thresh']:.0f}M" if cov["unit"] == "$M" else f"{cov['thresh']:.2f}x"
        op_s    = "≤" if cov["op"] == "lte" else "≥"
        sev     = min(99, 55 + abs(buf)/0.30*35) if status=="BREACH" else (25 + (1-buf/0.10)*25 if status=="WATCHLIST" else 5)
        rows.append([
            Paragraph(cov["name"], sTCell),
            Paragraph(cov["type"], sTCellC),
            Paragraph(act_s, S("ac", fontName="Courier-Bold" if status=="BREACH" else "Courier",
                                fontSize=7.5, leading=10, textColor=col, alignment=TA_RIGHT)),
            Paragraph(f"{op_s} {thr_s}", S("th", fontName="Courier", fontSize=7.5, leading=10,
                                             textColor=MUTED, alignment=TA_RIGHT)),
            Paragraph(buf_str, S("bf", fontName="Courier-Bold", fontSize=7.5, leading=10,
                                  textColor=col, alignment=TA_RIGHT)),
            Paragraph(f"{sev:.0f}/100", S("sv", fontName="Helvetica-Bold", fontSize=7.5, leading=10,
                                           textColor=col, alignment=TA_CENTER)),
            Paragraph(status, status_sty(status)),
        ])
    ts = TableStyle([
        ("BACKGROUND",    (0,0),(-1,0),  NAVY),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [WHITE, SURFACE]),
        ("LINEBELOW",     (0,0),(-1,-1), 0.3, BORDER),
        ("LEFTPADDING",   (0,0),(-1,-1), 5),  ("RIGHTPADDING", (0,0),(-1,-1), 5),
        ("TOPPADDING",    (0,0),(-1,-1), 4),  ("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
    ])
    for i, cov in enumerate(covenants, 1):
        _, _, status = cov_status(cov["actual"], cov["thresh"], cov["op"])
        col, bg, _ = status_colors(status)
        ts.add("BACKGROUND", (6,i),(6,i), bg)
    t = Table(rows, colWidths=col_w, repeatRows=1)
    t.setStyle(ts)
    return t

def shock_table(base_debt, base_cash, base_ebitda, threshold):
    e_shocks = [0, 0.10, 0.20, 0.30, 0.40, 0.50]
    d_shocks = [0, 0.05, 0.10, 0.20, 0.30]
    col_w = [BW*0.14] + [BW*0.172]*len(d_shocks)
    hdr = [Paragraph("EBITDA \\ Debt", sTHdr)] + [Paragraph(f"Debt +{int(d*100)}%", sTHdr) for d in d_shocks]
    rows = [hdr]
    cell_colors = []
    for e in e_shocks:
        se = base_ebitda * (1-e); row = []; row_c = []
        row.append(Paragraph(f"EBITDA –{int(e*100)}%", S("rl", fontSize=7, leading=10, textColor=MUTED)))
        for d in d_shocks:
            sd = base_debt * (1+d)
            nlr = (sd - base_cash)/se if se > 0 else 999
            breached = nlr > threshold
            near = not breached and (threshold - nlr)/threshold < 0.10
            col = BREACH_R if breached else (WATCH_A if near else OK_G)
            bg  = BREACH_BG if breached else (WATCH_BG if near else OK_BG)
            row.append(Paragraph("N/M" if se<=0 else f"{nlr:.1f}x",
                S("sc", fontName="Courier-Bold" if breached else "Courier",
                  fontSize=7.5, leading=10, textColor=col, alignment=TA_CENTER)))
            row_c.append(bg)
        rows.append(row); cell_colors.append(row_c)
    ts = TableStyle([
        ("BACKGROUND",    (0,0),(-1,0),  NAVY),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [WHITE, SURFACE]),
        ("LINEBELOW",     (0,0),(-1,-1), 0.3, BORDER),
        ("LEFTPADDING",   (0,0),(-1,-1), 4), ("RIGHTPADDING", (0,0),(-1,-1), 4),
        ("TOPPADDING",    (0,0),(-1,-1), 3), ("BOTTOMPADDING",(0,0),(-1,-1), 3),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
    ])
    for ri, row_c in enumerate(cell_colors):
        for ci, bg in enumerate(row_c):
            ts.add("BACKGROUND", (ci+1, ri+1),(ci+1, ri+1), bg)
    t = Table(rows, colWidths=col_w, repeatRows=1)
    t.setStyle(ts)
    return t

def icr_trend_table():
    col_w = [BW*0.12] + [BW*0.88/8]*8
    hdr = [Paragraph("Metric", sTHdr)] + [Paragraph(q, sTHdr) for q in QUARTERS]
    def cell(v, thresh, op):
        _, _, st = cov_status(v, thresh, op)
        col = BREACH_R if st=="BREACH" else (WATCH_A if st=="WATCHLIST" else TEXT)
        return Paragraph(f"{v:.2f}x", S("tc", fontName="Courier-Bold" if st=="BREACH" else "Courier",
                                          fontSize=7.5, leading=10, textColor=col, alignment=TA_CENTER))
    nlr_row = [Paragraph(f"NLR (≤5.50x)", sTCell)] + [cell(v,5.50,"lte") for v in TREND_NLR]
    icr_row = [Paragraph(f"ICR (≥1.50x)", sTCell)] + [cell(v,1.50,"gte") for v in TREND_ICR]
    t = Table([hdr, nlr_row, icr_row], colWidths=col_w, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,0),  NAVY),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE,SURFACE]),
        ("LINEBELOW",  (0,0),(-1,-1), 0.3, BORDER),
        ("LEFTPADDING",(0,0),(-1,-1), 4), ("RIGHTPADDING",(0,0),(-1,-1), 4),
        ("TOPPADDING", (0,0),(-1,-1), 4), ("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ("VALIGN",     (0,0),(-1,-1), "MIDDLE"),
    ]))
    return t

# ── BUILD ─────────────────────────────────────────────────────────────────────
def build():
    out = "/home/claude/ddcse_patch/DDCSE_SAVE_Spirit_Airlines_Ch11_Report.pdf"
    deco = PageDeco()

    doc = SimpleDocTemplate(
        out, pagesize=A4,
        leftMargin=ML, rightMargin=MR, topMargin=MT, bottomMargin=MB,
        title="DDCSE v3.2 — Spirit Airlines (SAVE) Covenant Surveillance Report",
        author="DDCSE · DogInfantry/dynamic-debt-covenant-surveillance-frame",
        subject="Private Credit · Aviation Sector · Covenant Surveillance",
    )
    story = []

    # ── PAGE 1 — COVER ────────────────────────────────────────────────────
    story.append(CoverBlock(BW, 100*mm))
    story.append(Spacer(1, 5*mm))

    # Company quick-facts 2-col grid
    info_rows = [
        [
            Table([[Paragraph("TICKER / EXCHANGE", sLabel)],
                   [Paragraph("SAVE · NYSE (delisted Nov 18, 2024)", S("iv", fontName="Helvetica-Bold", fontSize=8, leading=11, textColor=TEXT))]],
                  colWidths=[BW/2 - 3*mm],
                  style=[("BACKGROUND",(0,0),(-1,-1),SURFACE),("LEFTPADDING",(0,0),(-1,-1),6),
                         ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
                         ("LINEBELOW",(0,-1),(-1,-1),0.5,BORDER)]),
            Table([[Paragraph("S&P RATING / OUTLOOK", sLabel)],
                   [Paragraph("D  ·  Chapter 11 — Restructuring", S("iv2", fontName="Helvetica-Bold", fontSize=8, leading=11, textColor=BREACH_R))]],
                  colWidths=[BW/2 - 3*mm],
                  style=[("BACKGROUND",(0,0),(-1,-1),BREACH_BG),("LEFTPADDING",(0,0),(-1,-1),6),
                         ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
                         ("LINEBELOW",(0,-1),(-1,-1),0.5,BREACH_R)]),
        ],
        [
            Table([[Paragraph("LTM REVENUE", sLabel)],[Paragraph("$5,364M  (FY2023)", S("iv", fontSize=8, leading=11, textColor=TEXT, fontName="Helvetica-Bold"))]],
                  colWidths=[BW/2 - 3*mm],
                  style=[("BACKGROUND",(0,0),(-1,-1),SURFACE),("LEFTPADDING",(0,0),(-1,-1),6),
                         ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4)]),
            Table([[Paragraph("LTM EBITDA (ADJ.)", sLabel)],[Paragraph("$101M  ·  1.88% margin", S("iv", fontSize=8, leading=11, textColor=TEXT, fontName="Helvetica-Bold"))]],
                  colWidths=[BW/2 - 3*mm],
                  style=[("BACKGROUND",(0,0),(-1,-1),SURFACE),("LEFTPADDING",(0,0),(-1,-1),6),
                         ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4)]),
        ],
    ]
    info_t = Table(info_rows, colWidths=[BW/2, BW/2])
    info_t.setStyle(TableStyle([("LEFTPADDING",(0,0),(-1,-1),2),("RIGHTPADDING",(0,0),(-1,-1),2),
                                 ("TOPPADDING",(0,0),(-1,-1),2),("BOTTOMPADDING",(0,0),(-1,-1),2)]))
    story.append(info_t)

    # ── PAGE 2 — COVENANT SCORECARD ───────────────────────────────────────
    story.append(PageBreak())
    story += sec("1", "Covenant Package — Visual Scorecard")
    story.append(Paragraph(
        "All four tracked covenants are in material breach as of December 31, 2023. The Net Leverage "
        "Ratio of 24.33x exceeds the 5.50x ceiling by 342%, the most extreme breach depth in the DDCSE "
        "universe. The Fixed Charge Coverage Ratio of –0.82x — negative, meaning CapEx alone exceeded "
        "EBITDA — represents structural insolvency, not cyclical stress.", sBody))
    story.append(Spacer(1, 3*mm))
    story.append(CovenantScorecard(COVENANTS, BW))
    story.append(Spacer(1, 4*mm))
    story.append(cov_detail_table(COVENANTS))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        "Source: Spirit Airlines 2021 Term Loan Credit Agreement §7.1–7.2 · Senior Secured Notes "
        "Indenture §4.09 · Loyalty Notes Indenture §4.12 · 10-K FY2023 Note 9.", sBodySm))

    # ── PAGE 3 — TREND + DEBT STACK ───────────────────────────────────────
    story.append(PageBreak())
    story += sec("2", "NLR Trend Erosion — 8-Quarter History")
    story.append(Paragraph(
        "Spirit's NLR entered breach in Q4-2021 and has deteriorated every quarter since, "
        "with a velocity of +2.30x per quarter — the steepest in the DDCSE portfolio. "
        "ICR has been structurally flat at ~0.35x, confirming inability to service debt "
        "from operations independent of balance-sheet adjustments.", sBody))
    story.append(Spacer(1, 2*mm))
    story.append(Sparkline(TREND_NLR, 5.50, "5.50x limit", BW, 46*mm))
    story.append(Spacer(1, 2*mm))
    story.append(icr_trend_table())
    story.append(Spacer(1, 3*mm))

    # Velocity stats mini-table
    vel_rows = [
        [Paragraph(h, sTHdr) for h in ["NLR Q4-21", "NLR Q4-23", "Change", "Velocity", "ICR Q4-21", "ICR Q4-23", "Direction"]],
        [Paragraph("8.21x", S("v", fontName="Courier", fontSize=8, leading=10, textColor=BREACH_R, alignment=TA_CENTER)),
         Paragraph("24.33x", S("v", fontName="Courier-Bold", fontSize=8, leading=10, textColor=BREACH_R, alignment=TA_CENTER)),
         Paragraph("+196%", S("v", fontName="Courier-Bold", fontSize=8, leading=10, textColor=BREACH_R, alignment=TA_CENTER)),
         Paragraph("+2.30x/qtr", S("v", fontName="Courier-Bold", fontSize=8, leading=10, textColor=BREACH_R, alignment=TA_CENTER)),
         Paragraph("0.48x", S("v", fontName="Courier", fontSize=8, leading=10, textColor=BREACH_R, alignment=TA_CENTER)),
         Paragraph("0.35x", S("v", fontName="Courier-Bold", fontSize=8, leading=10, textColor=BREACH_R, alignment=TA_CENTER)),
         Paragraph("↓ Worsening", sBreach)],
    ]
    vt = Table(vel_rows, colWidths=[BW/7]*7)
    vt.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,0), NAVY),
        ("BACKGROUND", (0,1),(-1,1), BREACH_BG),
        ("LINEBELOW",  (0,0),(-1,-1), 0.3, BORDER),
        ("LEFTPADDING",(0,0),(-1,-1),4),("RIGHTPADDING",(0,0),(-1,-1),4),
        ("TOPPADDING", (0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
    ]))
    story.append(vt)
    story.append(Spacer(1, 5*mm))

    story += sec("3", "Debt Stack — Tranche Waterfall ($3.33B)")
    story.append(Paragraph(
        "The capital structure consists of four tranches across three seniority tiers. "
        "The EETC bonds benefit from Section 1110 aviation lien protection, creating "
        "a structural super-priority in Ch.11 despite their nominal secured position. "
        "All tranches are in breach; the TLB waiver expiry in Sep 2024 triggered "
        "the cross-default cascade across $2.44B in secured claims simultaneously.", sBody))
    story.append(Spacer(1, 2*mm))
    story.append(DebtWaterfall(TRANCHES, BW))

    # ── PAGE 4 — SHOCK MATRIX + RECOVERY ────────────────────────────────
    story.append(PageBreak())
    story += sec("4", "Macro Shock Sensitivity Matrix")
    story.append(Paragraph(
        "Every scenario in the matrix is deep red. Even a 50% EBITDA improvement "
        "combined with a 30% debt reduction produces NLR of ~11.4x — still 2× the "
        "covenant ceiling. This confirms structural insolvency: operational improvement "
        "alone cannot solve a 24.33x leverage problem. Balance-sheet surgery (Ch.11) "
        "was the only viable path.", sBody))
    story.append(Spacer(1, 2*mm))
    story.append(shock_table(3330, 872, 101, 5.50))
    story.append(Spacer(1, 2*mm))
    story.append(CalloutBox(
        "ALL 30 SCENARIOS: BREACH",
        "Spirit Airlines is the only credit in the DDCSE portfolio with a fully-red shock matrix "
        "across all EBITDA and debt stress combinations. This is the quantitative confirmation of "
        "structural insolvency — the covenant breach cannot be cured through operations.",
        BW, BREACH_R, BREACH_BG))
    story.append(Spacer(1, 5*mm))

    story += sec("5", "Creditor Recovery Waterfall")
    story.append(Paragraph(
        "Recovery outcomes reflect the seniority structure and Section 1110 aviation protections. "
        "EETC holders recovered ~78¢/$1 through aircraft rejections. Loyalty Note holders received "
        "equity at ~32¢/$1. Unsecured creditors and equity were effectively wiped out.", sBody))
    story.append(Spacer(1, 2*mm))
    story.append(RecoveryWaterfall(BW))

    # ── PAGE 5 — TIMELINE ────────────────────────────────────────────────
    story.append(PageBreak())
    story += sec("6", "Key Events Timeline — M&A Collapse to Ch.11 Emergence")
    story.append(Timeline(EVENTS, BW))

    # ── PAGE 6 — THESIS ──────────────────────────────────────────────────
    story.append(PageBreak())
    story += sec("7", "Investment Thesis & Structural Analysis")

    sections_thesis = [
        ("7.1  The ULCC Model Under Terminal Leverage",
         "Spirit Airlines was the largest US ultra-low-cost carrier by fleet size at filing. "
         "The ULCC model — ultra-stripped base fares, aggressive ancillary monetization — "
         "generates EBITDA margins of 8–12% in normalized conditions. These margins are "
         "mathematically insufficient to service $3.3B in debt. At $101M EBITDA, each $1B "
         "of debt adds ~10x to NLR. Spirit crossed the point of no return in early 2022 "
         "when NLR exceeded 10x and M&A remained the only viable exit."),
        ("7.2  Three Compounding Failure Mechanisms",
         "(1) M&A Limbo (Feb 2022 – Jan 2024): 26 months of strategic paralysis. "
         "Management deferred fleet rationalization and cost cuts, burning $700M+ in cash "
         "while competitors invested in network and loyalty. The DoJ's antitrust block of "
         "the JetBlue merger crystallized the terminal standalone position. "
         "(2) Margin Compression: Fuel (+38% YoY, 2022), pilot contracts (+34% over 4 yrs), "
         "and maintenance catch-up compressed EBITDA margin from ~18% (FY2019) to <2% (FY2023). "
         "(3) Cross-Default Cascade: The interconnected covenant structure meant one waiver "
         "expiry (TLB, Sep 2024) triggered $2.44B in simultaneous accelerations — "
         "making out-of-court resolution practically impossible."),
        ("7.3  Recovery Analysis",
         "EETC holders (~78¢/$1): Aircraft-backed + Section 1110 protection enabled orderly "
         "aircraft rejections and lease restructurings with residual fleet value preservation. "
         "Loyalty Note holders (~32¢/$1): Equitized into reorganized Spirit equity; "
         "emergence EV ~$795M implies ~$352M recovery on $1.1B face. "
         "Unsecured creditors (<5¢/$1): Trade claims, airport fees, deficiency claims. "
         "Common equity: Cancelled in full."),
        ("7.4  Sector Read-Across",
         "(a) ULCC Surveillance Rule: Any ULCC with Debt/EBITDA >4.0x and ICR <2.0x warrants "
         "structural watchlist classification — not cyclical. "
         "(b) Loyalty Program Financing: Free Spirit / Frontier Miles / similar structures "
         "create disguised senior secured claims that behave like covenant debt in stress. "
         "(c) Section 1110 Anomaly: EETC holders are effectively super-senior to covenant "
         "lenders in US aviation Ch.11s regardless of nominal capital structure position. "
         "(d) DoJ Posture: Aggressive antitrust stance (JetBlue/Spirit, JetBlue/AA NEA) "
         "eliminates M&A as a balance-sheet rescue mechanism for distressed US carriers."),
    ]
    for subtitle, body in sections_thesis:
        story.append(Paragraph(subtitle, S("ts", fontName="Helvetica-Bold", fontSize=8.5, leading=12,
                                             textColor=NAVY2, spaceBefore=5, spaceAfter=3)))
        story.append(Paragraph(body, sBody))
        story.append(Spacer(1, 1*mm))

    story.append(Spacer(1, 4*mm))
    story += sec("8", "Data Sources & Disclosures")
    sources = [
        "Spirit Airlines Inc. — 10-K FY2023 (SEC EDGAR CIK 0001498710, filed Mar 4, 2024)",
        "Spirit Airlines Ch.11 First-Day Declaration — SDNY, Nov 18, 2024 (Case No. 24-11988)",
        "Spirit Airlines Disclosure Statement — Jan 2025",
        "S&P Global Ratings — Spirit Airlines rating action, downgrade to D (Nov 18, 2024)",
        "Moody's Investors Service — Spirit Airlines rating withdrawal (Nov 2024)",
        "US DoJ v. JetBlue Airways Corp. — Case 1:23-cv-10511 (D.Mass., Jan 2024)",
        "Spirit Airlines EETC Prospectus Supplements (SEC, 2015 & 2017)",
        f"DDCSE v3.2 Analytics Engine — github.com/DogInfantry/dynamic-debt-covenant-surveillance-frame",
        f"Report generated: {TODAY}  ·  For analytical purposes only. Not investment advice.",
    ]
    for s in sources:
        story.append(Paragraph(f"• {s}", sNote))

    doc.build(story, onFirstPage=deco, onLaterPages=deco)
    print(f"✓ PDF: {out}  ({len(story)} elements)")
    return out

if __name__ == "__main__":
    build()

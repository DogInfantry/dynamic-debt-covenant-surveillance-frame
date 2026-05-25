"""
DDCSE Professional Covenant Surveillance Report — v2.1
Bloomberg / Morgan Stanley institutional aesthetic
Stakeholder-facing: Portfolio Overview → Framework → Per-Company Deep-Dive
→ Cross-Default Cascade → Macro Stress Matrix → Methodology & Disclaimer

Data: SEC EDGAR 10-K / 10-Q static registry (yfinance blocked in sandbox).
All figures sourced from real_cases.py which cites specific SEC EDGAR filings.
"""
import sys, os, math, io
from datetime import date

# ── ReportLab ─────────────────────────────────────────────────────────────────
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether, Image as RLImage
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas as rl_canvas

# ── Matplotlib ────────────────────────────────────────────────────────────────
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import numpy as np

# ── DDCSE modules ─────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
from real_cases import CASE_REGISTRY, list_cases
from analytics_v2 import (
    evaluate_package, portfolio_severity_score,
    macro_shock_matrix, detect_trend_erosion,
    build_envision_graph, simulate_cascade,
)

# ─────────────────────────────────────────────────────────────────────────────
# PALETTE
# ─────────────────────────────────────────────────────────────────────────────
NAVY    = colors.HexColor('#0A1628')
BLUE    = colors.HexColor('#1A3A5C')
MIDBLUE = colors.HexColor('#2C5282')
LGRAY   = colors.HexColor('#F4F5F7')
MGRAY   = colors.HexColor('#8A9BB0')
DGRAY   = colors.HexColor('#2C3E50')
RED     = colors.HexColor('#C0392B')
AMBER   = colors.HexColor('#D4680A')
GREEN   = colors.HexColor('#1A7A4A')
WHITE   = colors.white
BORDER  = colors.HexColor('#D0D7E2')
CREAM   = colors.HexColor('#FAFBFD')

W, H = A4
CONTENT_W = W - 30 * mm

HEX = {
    'navy': '#0A1628', 'blue': '#1A3A5C', 'midblue': '#2C5282',
    'lgray': '#F4F5F7', 'mgray': '#8A9BB0', 'dgray': '#2C3E50',
    'red': '#C0392B', 'amber': '#D4680A', 'green': '#1A7A4A',
    'white': '#FFFFFF', 'border': '#D0D7E2',
    'red_light': '#F9E5E4', 'amber_light': '#FDF3E7', 'green_light': '#E8F5EE',
}

def status_color(s):
    return {'BREACH': RED, 'WATCHLIST': AMBER, 'WARNING': AMBER, 'COMPLIANT': GREEN}.get(s, MGRAY)

def status_hex(s):
    return {'BREACH': HEX['red'], 'WATCHLIST': HEX['amber'], 'WARNING': HEX['amber'],
            'COMPLIANT': HEX['green']}.get(s, HEX['mgray'])

def status_bg_hex(s):
    return {'BREACH': HEX['red_light'], 'WATCHLIST': HEX['amber_light'],
            'WARNING': HEX['amber_light'], 'COMPLIANT': HEX['green_light']}.get(s, HEX['lgray'])

# ─────────────────────────────────────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────────────────────────────────────
def make_styles():
    return {
        'cover_title': ParagraphStyle('ct', fontName='Helvetica-Bold',
            fontSize=24, textColor=WHITE, leading=30, alignment=TA_LEFT),
        'cover_sub': ParagraphStyle('cs', fontName='Helvetica',
            fontSize=12, textColor=colors.HexColor('#B0C4DE'), leading=17),
        'cover_meta': ParagraphStyle('cm', fontName='Helvetica',
            fontSize=9, textColor=colors.HexColor('#8A9BB0'), leading=14),
        'toc_head': ParagraphStyle('tch', fontName='Helvetica-Bold',
            fontSize=14, textColor=NAVY, leading=20, spaceAfter=8),
        'toc_item': ParagraphStyle('tci', fontName='Helvetica',
            fontSize=10, textColor=DGRAY, leading=16, leftIndent=12),
        'toc_sub': ParagraphStyle('tcs', fontName='Helvetica',
            fontSize=9, textColor=MGRAY, leading=14, leftIndent=24),
        'section': ParagraphStyle('sh', fontName='Helvetica-Bold',
            fontSize=10, textColor=NAVY, leading=14, spaceAfter=4),
        'body': ParagraphStyle('bd', fontName='Helvetica',
            fontSize=8.5, textColor=DGRAY, leading=13, spaceAfter=3),
        'body_j': ParagraphStyle('bdj', fontName='Helvetica',
            fontSize=8.5, textColor=DGRAY, leading=13.5, spaceAfter=4, alignment=TA_JUSTIFY),
        'small': ParagraphStyle('sm', fontName='Helvetica',
            fontSize=7.5, textColor=MGRAY, leading=11),
        'small_d': ParagraphStyle('smd', fontName='Helvetica',
            fontSize=7.5, textColor=DGRAY, leading=11),
        'label': ParagraphStyle('lb', fontName='Helvetica-Bold',
            fontSize=7.5, textColor=NAVY, leading=11),
        'mono': ParagraphStyle('mn', fontName='Courier',
            fontSize=7.5, textColor=DGRAY, leading=11),
        'note': ParagraphStyle('nt', fontName='Helvetica-Oblique',
            fontSize=7.5, textColor=MGRAY, leading=11),
        'right': ParagraphStyle('rt', fontName='Helvetica',
            fontSize=8, textColor=DGRAY, leading=11, alignment=TA_RIGHT),
        'center': ParagraphStyle('ctr', fontName='Helvetica',
            fontSize=8, textColor=DGRAY, leading=11, alignment=TA_CENTER),
        'h1': ParagraphStyle('h1', fontName='Helvetica-Bold',
            fontSize=16, textColor=NAVY, leading=22, spaceAfter=8, spaceBefore=4),
        'h2': ParagraphStyle('h2', fontName='Helvetica-Bold',
            fontSize=12, textColor=NAVY, leading=17, spaceAfter=6, spaceBefore=10),
        'h3': ParagraphStyle('h3', fontName='Helvetica-Bold',
            fontSize=9.5, textColor=BLUE, leading=13, spaceAfter=4, spaceBefore=6),
        'h4': ParagraphStyle('h4', fontName='Helvetica-Bold',
            fontSize=8.5, textColor=DGRAY, leading=12, spaceAfter=3, spaceBefore=4),
        'red': ParagraphStyle('rd', fontName='Helvetica-Bold',
            fontSize=8, textColor=RED, leading=11),
        'amber': ParagraphStyle('am', fontName='Helvetica-Bold',
            fontSize=8, textColor=AMBER, leading=11),
        'green': ParagraphStyle('gn', fontName='Helvetica-Bold',
            fontSize=8, textColor=GREEN, leading=11),
        'white_bold': ParagraphStyle('wb', fontName='Helvetica-Bold',
            fontSize=8.5, textColor=WHITE, leading=12),
        'framework_head': ParagraphStyle('fwh', fontName='Helvetica-Bold',
            fontSize=11, textColor=NAVY, leading=15, spaceBefore=8, spaceAfter=4),
        'framework_body': ParagraphStyle('fwb', fontName='Helvetica',
            fontSize=8.5, textColor=DGRAY, leading=13.5, alignment=TA_JUSTIFY),
        'kpi_num': ParagraphStyle('kpn', fontName='Helvetica-Bold',
            fontSize=18, textColor=WHITE, leading=22, alignment=TA_CENTER),
        'kpi_label': ParagraphStyle('kpl', fontName='Helvetica',
            fontSize=8, textColor=colors.HexColor('#B0C4DE'), leading=11, alignment=TA_CENTER),
    }

S = make_styles()

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CANVAS — header / footer
# ─────────────────────────────────────────────────────────────────────────────
class ReportCanvas(rl_canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def _draw_header_footer(self, page_count):
        p = self._pageNumber
        # Skip cover & TOC (pages 1–2)
        if p <= 2:
            return
        # ── header bar
        self.setFillColor(NAVY)
        self.rect(0, H - 16 * mm, W, 16 * mm, fill=1, stroke=0)
        self.setFont('Helvetica-Bold', 8)
        self.setFillColor(WHITE)
        self.drawString(15 * mm, H - 10 * mm, 'DDCSE  ·  Dynamic Debt Covenant Surveillance Engine  ·  v2.1')
        self.setFont('Helvetica', 7.5)
        self.setFillColor(colors.HexColor('#B0C4DE'))
        self.drawRightString(W - 15 * mm, H - 10 * mm, 'CONFIDENTIAL  ·  Institutional Use Only')
        # ── accent stripe
        self.setFillColor(AMBER)
        self.rect(0, H - 17.5 * mm, W, 1.5 * mm, fill=1, stroke=0)
        # ── footer
        self.setFillColor(LGRAY)
        self.rect(0, 0, W, 10 * mm, fill=1, stroke=0)
        self.setStrokeColor(BORDER)
        self.setLineWidth(0.3)
        self.line(0, 10 * mm, W, 10 * mm)
        self.setFont('Helvetica', 6.8)
        self.setFillColor(MGRAY)
        self.drawString(15 * mm, 3.5 * mm,
            'Source: SEC EDGAR 10-K / 10-Q filings. '
            'All figures USD millions unless stated. Not investment advice.')
        self.drawRightString(W - 15 * mm, 3.5 * mm, f'Page {p} of {page_count}')

# ─────────────────────────────────────────────────────────────────────────────
# CHART HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def fig_to_image(fig, width_mm, height_mm, dpi=160):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return RLImage(buf, width=width_mm * mm, height=height_mm * mm)


def make_portfolio_bar(cases):
    tickers = [c['ticker'] for c in cases]
    nlrs    = [c['nlr'] for c in cases]
    threshs = [c['nlr_threshold'] for c in cases]
    bar_colors = []
    for nlr, t in zip(nlrs, threshs):
        if nlr > t:
            bar_colors.append(HEX['red'])
        elif (t - nlr) / t < 0.10:
            bar_colors.append(HEX['amber'])
        else:
            bar_colors.append(HEX['green'])

    fig, ax = plt.subplots(figsize=(7.0, 2.6))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    x = np.arange(len(tickers))
    bars = ax.bar(x, nlrs, color=bar_colors, width=0.55, zorder=2,
                  edgecolor='white', linewidth=0.6)
    for i, thresh in enumerate(threshs):
        ax.plot([i - 0.3, i + 0.3], [thresh, thresh],
                color=HEX['navy'], linewidth=1.6, linestyle='--', zorder=3)
    for bar, nlr in zip(bars, nlrs):
        ax.text(bar.get_x() + bar.get_width() / 2, nlr + 0.06,
                f'{nlr:.2f}x', ha='center', va='bottom', fontsize=8,
                fontweight='bold', color=HEX['dgray'])
    ax.set_xticks(x)
    ax.set_xticklabels(tickers, fontsize=9, fontweight='bold')
    ax.set_ylabel('Net Leverage Ratio (x)', fontsize=8)
    ax.set_title('Portfolio NLR vs Covenant Threshold  (─ ─ = threshold)', fontsize=9,
                 color=HEX['navy'], pad=7, fontweight='bold')
    ax.set_ylim(0, max(nlrs) * 1.20)
    ax.tick_params(labelsize=8)
    ax.grid(axis='y', alpha=0.18, linewidth=0.4, zorder=1)
    for spine in ax.spines.values():
        spine.set_linewidth(0.3)
        spine.set_color('#CCCCCC')
    legend_els = [
        mpatches.Patch(color=HEX['red'], label='Breach'),
        mpatches.Patch(color=HEX['amber'], label='Watchlist (<10% buffer)'),
        mpatches.Patch(color=HEX['green'], label='Compliant'),
    ]
    ax.legend(handles=legend_els, loc='upper left', fontsize=7.5,
              framealpha=0.85, edgecolor='#CCCCCC')
    fig.tight_layout(pad=0.5)
    return fig_to_image(fig, 162, 62)


def make_trend_chart(case, ticker):
    qs = case['trend_quarters']
    nlr = case['trend_nlr']
    icr = case['trend_icr']
    thresh = case['covenants'][0]['threshold']

    fig, ax1 = plt.subplots(figsize=(4.8, 1.8))
    fig.patch.set_facecolor(HEX['lgray'])
    ax1.set_facecolor(HEX['lgray'])
    x = range(len(qs))
    ax1.fill_between(x, nlr, alpha=0.10, color=HEX['red'])
    ax1.plot(x, nlr, color=HEX['red'], linewidth=2.0, marker='o', markersize=3.5,
             label=f'NLR (LHS)', zorder=3)
    ax1.axhline(thresh, color=HEX['red'], linewidth=1.0, linestyle='--', alpha=0.6, zorder=2)
    ax1.set_xticks(list(x))
    ax1.set_xticklabels(qs, fontsize=5.5, rotation=35, ha='right')
    ax1.set_ylabel('NLR (x)', fontsize=6.5, color=HEX['red'])
    ax1.tick_params(axis='y', labelsize=6, labelcolor=HEX['red'])
    ax2 = ax1.twinx()
    ax2.plot(x, icr, color=HEX['green'], linewidth=1.6, marker='s', markersize=2.8,
             linestyle='--', label='ICR (RHS)', zorder=3)
    ax2.set_ylabel('ICR (x)', fontsize=6.5, color=HEX['green'])
    ax2.tick_params(axis='y', labelsize=6, labelcolor=HEX['green'])
    for spine in list(ax1.spines.values()) + list(ax2.spines.values()):
        spine.set_linewidth(0.3)
    ax1.grid(True, alpha=0.15, linewidth=0.3)
    fig.tight_layout(pad=0.4)
    return fig_to_image(fig, 162, 44)


def make_severity_heatmap(cases_with_results):
    """Horizontal severity bar chart across portfolio."""
    labels = [c['ticker'] for c in cases_with_results]
    scores = [c['severity'] for c in cases_with_results]
    bar_c = [HEX['red'] if s >= 70 else (HEX['amber'] if s >= 40 else HEX['green'])
             for s in scores]

    fig, ax = plt.subplots(figsize=(7.0, 1.8))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    y = np.arange(len(labels))
    ax.barh(y, scores, color=bar_c, height=0.5, zorder=2, edgecolor='white', linewidth=0.5)
    ax.axvline(40, color=HEX['amber'], linewidth=1.0, linestyle='--', alpha=0.6)
    ax.axvline(70, color=HEX['red'], linewidth=1.0, linestyle='--', alpha=0.6)
    for i, s in enumerate(scores):
        ax.text(s + 0.8, i, f'{s:.0f}', va='center', fontsize=7.5, fontweight='bold',
                color=HEX['dgray'])
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8.5, fontweight='bold')
    ax.set_xlim(0, 108)
    ax.set_xlabel('Severity Score (0 = no risk → 100 = deep breach)', fontsize=7.5)
    ax.set_title('Portfolio Severity Heat Map', fontsize=9, color=HEX['navy'],
                 pad=5, fontweight='bold')
    ax.tick_params(axis='x', labelsize=7)
    ax.grid(axis='x', alpha=0.15, linewidth=0.3, zorder=1)
    for spine in ax.spines.values():
        spine.set_linewidth(0.3)
        spine.set_color('#CCCCCC')
    ax.text(35, len(labels) - 0.1, 'Watchlist', fontsize=6.5, color=HEX['amber'], ha='right')
    ax.text(68, len(labels) - 0.1, 'Breach', fontsize=6.5, color=HEX['red'], ha='right')
    fig.tight_layout(pad=0.5)
    return fig_to_image(fig, 162, 45)


def make_shock_heatmap(ticker, case):
    matrix_data = macro_shock_matrix(
        case['total_debt'], case['cash'], case['ebitda_ltm'],
        case['covenants'][0]['threshold']
    )
    rows = matrix_data['rows']   # EBITDA shock labels
    cols = matrix_data['cols']   # Debt shock labels
    mat  = matrix_data['matrix']

    # Build numpy array of NLR values
    nlr_arr = np.array([[cell['nlr'] for cell in row] for row in mat])
    breach_arr = np.array([[cell['breached'] for cell in row] for row in mat])

    fig, ax = plt.subplots(figsize=(5.2, 2.4))
    fig.patch.set_facecolor('white')

    # Color: green = safe, amber = close, red = breach
    thresh = case['covenants'][0]['threshold']
    cmap_data = np.where(breach_arr, 2,
                np.where(nlr_arr >= thresh * 0.90, 1, 0)).astype(float)
    cmap = matplotlib.colors.ListedColormap([HEX['green_light'], HEX['amber_light'], HEX['red_light']])
    ax.imshow(cmap_data, aspect='auto', cmap=cmap, vmin=0, vmax=2)

    for i in range(len(rows)):
        for j in range(len(cols)):
            nlr_v = nlr_arr[i, j]
            txt_color = HEX['red'] if breach_arr[i, j] else (
                HEX['amber'] if nlr_v >= thresh * 0.90 else HEX['green'])
            weight = 'bold' if breach_arr[i, j] else 'normal'
            ax.text(j, i, f'{nlr_v:.2f}x', ha='center', va='center',
                    fontsize=6.8, color=txt_color, fontweight=weight)

    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels([c.replace('Debt ', '') for c in cols], fontsize=6.5, rotation=30, ha='right')
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r.replace('EBITDA ', '') for r in rows], fontsize=6.5)
    ax.set_xlabel('Debt Increase →', fontsize=7)
    ax.set_ylabel('EBITDA Compression ↓', fontsize=7)
    ax.set_title(f'{ticker} — Macro Stress NLR Matrix  (thresh {thresh:.2f}x)',
                 fontsize=8, color=HEX['navy'], pad=5, fontweight='bold')
    for spine in ax.spines.values():
        spine.set_linewidth(0.5)
    fig.tight_layout(pad=0.4)
    return fig_to_image(fig, 130, 58)


def make_covenant_radar(results, ticker):
    """Radar / spider chart showing actual vs threshold for each covenant."""
    n = len(results)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles += angles[:1]

    # Normalize: actual / threshold (1.0 = at threshold)
    vals_actual = [r.actual / r.threshold for r in results]
    vals_thresh = [1.0] * n
    vals_actual += vals_actual[:1]
    vals_thresh += vals_thresh[:1]
    names = [r.name.replace('Consolidated ', '').replace(' Ratio', '').replace(' Available', '')
             for r in results]

    fig, ax = plt.subplots(figsize=(2.8, 2.8), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor('white')
    ax.set_facecolor(HEX['lgray'])

    ax.plot(angles, vals_thresh, 'o--', color=HEX['navy'], linewidth=1.2,
            markersize=3, alpha=0.8, label='Threshold')
    ax.fill(angles, vals_thresh, alpha=0.06, color=HEX['navy'])
    ax.plot(angles, vals_actual, 'o-', color=HEX['red'], linewidth=1.6,
            markersize=4, label='Actual', zorder=3)
    ax.fill(angles, vals_actual, alpha=0.15, color=HEX['red'])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(names, size=6.0)
    ax.set_yticklabels([])
    ax.set_title(f'{ticker} Covenant Profile', fontsize=7.5, color=HEX['navy'],
                 pad=12, fontweight='bold')
    ax.spines['polar'].set_linewidth(0.4)
    ax.grid(linewidth=0.3, alpha=0.4)
    fig.tight_layout(pad=0.3)
    return fig_to_image(fig, 58, 58)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION BUILDERS
# ─────────────────────────────────────────────────────────────────────────────
def section_rule(story):
    story.append(HRFlowable(width='100%', thickness=0.4, color=BORDER, spaceAfter=5))


def section_header_block(story, text, sub=None):
    story.append(Table([[
        Paragraph(text, ParagraphStyle('sbh', fontName='Helvetica-Bold', fontSize=13,
                      textColor=WHITE, leading=18)),
    ]], colWidths=[CONTENT_W], style=TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), NAVY),
        ('TOPPADDING', (0,0), (-1,-1), 9),
        ('BOTTOMPADDING', (0,0), (-1,-1), 9),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
    ])))
    story.append(Spacer(1, 1.5 * mm))
    if sub:
        story.append(Paragraph(sub, S['small']))
        story.append(Spacer(1, 2 * mm))


def kpi_band(story, kpis):
    """kpis: list of (label, value, color_hex, sub_label)"""
    cells = [[
        Paragraph(f'<b>{v}</b>', ParagraphStyle('kv', fontName='Helvetica-Bold',
            fontSize=16, textColor=WHITE, leading=20, alignment=TA_CENTER)),
    ] for _, v, _, _ in kpis]
    sub_cells = [[
        Paragraph(
            f'{label}<br/><font size="7" color="{sub_col}">{sub}</font>',
            ParagraphStyle('kl', fontName='Helvetica', fontSize=8,
                textColor=colors.HexColor('#B0C4DE'), leading=11, alignment=TA_CENTER))
    ] for label, _, sub_col, sub in kpis]
    bg = [colors.HexColor(c) for _, _, c, _ in kpis]

    col_w = [CONTENT_W / len(kpis)] * len(kpis)
    inner = [[cells[i][0], sub_cells[i][0]] for i in range(len(kpis))]
    flat = [[inner[i][0] for i in range(len(kpis))],
            [inner[i][1] for i in range(len(kpis))]]

    style = [
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 4),
        ('TOPPADDING', (0,1), (-1,1), 2),
        ('BOTTOMPADDING', (0,1), (-1,1), 10),
    ]
    for i, color in enumerate(bg):
        style.append(('BACKGROUND', (i,0), (i,1), color))
    style.append(('GRID', (0,0), (-1,-1), 0.3, colors.HexColor('#2A4A7A')))

    story.append(Table(flat, colWidths=col_w, style=TableStyle(style)))


# ─────────────────────────────────────────────────────────────────────────────
# COVER PAGE
# ─────────────────────────────────────────────────────────────────────────────
def build_cover(story, today, cases):
    breaches  = sum(1 for c in cases if c['nlr'] > c['nlr_threshold'])
    watchlist = sum(1 for c in cases if c['nlr'] <= c['nlr_threshold']
                   and (c['nlr_threshold'] - c['nlr']) / c['nlr_threshold'] < 0.10)
    compliant = len(cases) - breaches - watchlist
    total_debt_bn = sum(CASE_REGISTRY[c['ticker']]['total_debt'] for c in cases) / 1000

    # ── Full-width navy cover block
    story.append(Table([[
        Paragraph('DYNAMIC DEBT COVENANT<br/>SURVEILLANCE ENGINE',
                  ParagraphStyle('ctb', fontName='Helvetica-Bold', fontSize=26,
                      textColor=WHITE, leading=32)),
    ]], colWidths=[CONTENT_W], style=TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), NAVY),
        ('TOPPADDING', (0,0), (-1,-1), 22),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 14),
    ])))
    story.append(Table([[
        Paragraph('Portfolio Covenant Surveillance Report  ·  Private Credit Edition',
                  ParagraphStyle('csb', fontName='Helvetica', fontSize=12,
                      textColor=colors.HexColor('#B0C4DE'), leading=17)),
    ]], colWidths=[CONTENT_W], style=TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BLUE),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 14),
    ])))
    # amber accent stripe
    story.append(Table([['']], colWidths=[CONTENT_W], style=TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), AMBER),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ])))
    story.append(Spacer(1, 5 * mm))

    # ── Meta row
    story.append(Table([[
        Paragraph(f'<b>Report Date</b><br/>{today}', S['body']),
        Paragraph(f'<b>Data As Of</b><br/>FY2023 / Q3 2023 (SEC EDGAR)', S['body']),
        Paragraph(f'<b>Prepared By</b><br/>DDCSE Engine v2.1 · github.com/DogInfantry', S['body']),
        Paragraph(f'<b>Classification</b><br/>Confidential — Institutional Use Only',
                  ParagraphStyle('cls', fontName='Helvetica-Bold', fontSize=8.5,
                      textColor=RED, leading=13)),
    ]], colWidths=[CONTENT_W * x for x in [0.22, 0.28, 0.32, 0.18]],
    style=TableStyle([
        ('GRID', (0,0), (-1,-1), 0.3, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 7),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [LGRAY]),
    ])))
    story.append(Spacer(1, 5 * mm))

    # ── Portfolio KPI band
    kpi_band(story, [
        ('Credits Monitored', str(len(cases)), HEX['navy'], '#B0C4DE'),
        ('Covenant Breaches', str(breaches), HEX['red'], '#F9E5E4' if breaches else HEX['red']),
        ('Watchlist', str(watchlist), HEX['amber'], '#FDF3E7'),
        ('Compliant', str(compliant), HEX['green'], '#E8F5EE'),
        ('Total Debt', f'${total_debt_bn:.1f}B', HEX['midblue'], '#B0C4DE'),
    ])
    story.append(Spacer(1, 5 * mm))

    # ── Portfolio bar chart
    story.append(make_portfolio_bar(cases))
    story.append(Paragraph(
        'Figure 1: Portfolio Net Leverage Ratio vs contractual covenant threshold. '
        'Dashed line = NLR ceiling per credit agreement. '
        'Source: SEC EDGAR 10-K / 10-Q filings (FY2023).',
        S['note']))
    story.append(Spacer(1, 4 * mm))

    # ── Summary table
    story.append(Paragraph('Portfolio Covenant Status — Executive Summary', S['h2']))
    hdr = ['Ticker', 'Company', 'Sector', 'Rating', 'Outlook', 'NLR Actual',
           'NLR Thresh', 'ICR', 'Buffer %', 'Status']
    tbl_data = [hdr]
    for c in cases:
        nlr_v = c['nlr']
        thresh = c['nlr_threshold']
        buf_pct = (thresh - nlr_v) / thresh * 100
        status = ('BREACH' if nlr_v > thresh else
                  'WATCHLIST' if buf_pct < 10 else 'COMPLIANT')
        cr = CASE_REGISTRY[c['ticker']]
        row = [
            Paragraph(f'<b>{c["ticker"]}</b>', S['label']),
            Paragraph(c['name'][:28], S['body']),
            Paragraph(c['sector'].split('—')[0].strip(), S['small_d']),
            Paragraph(c['credit_rating'], ParagraphStyle('rat', fontName='Helvetica-Bold',
                fontSize=8, textColor=RED if c['credit_rating'] in ('CCC+','B','B-') else DGRAY)),
            Paragraph(cr['outlook'][:14], S['small']),
            Paragraph(f'<b>{nlr_v:.2f}x</b>',
                ParagraphStyle('nlr2', fontName='Helvetica-Bold', fontSize=8,
                    textColor=status_color(status))),
            Paragraph(f'{thresh:.2f}x', S['center']),
            Paragraph(f'{c["icr"]:.2f}x', S['center']),
            Paragraph(f'▼{abs(buf_pct):.1f}%' if buf_pct < 0
                      else f'{buf_pct:.1f}%',
                ParagraphStyle('buf', fontName='Helvetica-Bold', fontSize=8,
                    textColor=RED if buf_pct < 0 else (AMBER if buf_pct < 10 else GREEN))),
            Paragraph(f'<b>{status}</b>',
                ParagraphStyle('st3', fontName='Helvetica-Bold', fontSize=8,
                    textColor=status_color(status))),
        ]
        tbl_data.append(row)

    col_w = [CONTENT_W * x for x in [0.07, 0.20, 0.14, 0.06, 0.10, 0.09, 0.09, 0.08, 0.08, 0.09]]
    tbl = Table(tbl_data, colWidths=col_w, repeatRows=1)
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LGRAY]),
        ('GRID', (0,0), (-1,-1), 0.3, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(tbl)
    story.append(PageBreak())


# ─────────────────────────────────────────────────────────────────────────────
# TABLE OF CONTENTS
# ─────────────────────────────────────────────────────────────────────────────
def build_toc(story):
    story.append(Paragraph('Table of Contents', S['h1']))
    section_rule(story)
    story.append(Spacer(1, 3 * mm))

    sections = [
        ('1', 'DDCSE Framework & Analytical Methodology', [
            ('1.1', 'Engine Architecture Overview'),
            ('1.2', 'Covenant Taxonomy & Evaluation Logic'),
            ('1.3', 'Severity Scoring Model'),
            ('1.4', 'Cross-Default Cascade Simulation'),
            ('1.5', 'Macro Stress Matrix'),
            ('1.6', 'Data Pipeline & Sources'),
        ]),
        ('2', 'Portfolio Overview & Heat Map', []),
        ('3', 'Company Deep-Dive Profiles', [
            ('3.1', 'Charter Communications (CHTR) — Watchlist'),
            ('3.2', 'Walgreens Boots Alliance (WBA) — Breach'),
            ('3.3', 'Paramount Global (PARA) — Watchlist'),
            ('3.4', 'HCA Healthcare (HCA) — Compliant'),
            ('3.5', 'Altice USA (ATUS) — Deep Breach'),
        ]),
        ('4', 'Cross-Default Cascade Analysis', []),
        ('5', 'Macro Stress Sensitivity Matrices', []),
        ('6', 'Methodology, Data Sources & Disclaimer', []),
    ]
    for num, title, subs in sections:
        story.append(Paragraph(
            f'<b>{num}.</b> &nbsp; {title}',
            ParagraphStyle('tc1', fontName='Helvetica-Bold', fontSize=10.5,
                textColor=NAVY, leading=16, leftIndent=0, spaceBefore=6)))
        for sub_num, sub_title in subs:
            story.append(Paragraph(
                f'{sub_num} &nbsp; {sub_title}',
                ParagraphStyle('tc2', fontName='Helvetica', fontSize=9,
                    textColor=DGRAY, leading=14, leftIndent=18)))
    story.append(PageBreak())


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — FRAMEWORK
# ─────────────────────────────────────────────────────────────────────────────
def build_framework(story):
    section_header_block(story, '1. DDCSE Framework & Analytical Methodology',
        'Dynamic Debt Covenant Surveillance Engine · AST-Safe Compiler · NetworkX Cascade · Severity Scoring')

    # ── 1.1 Architecture
    story.append(Paragraph('1.1  Engine Architecture Overview', S['h3']))
    story.append(Paragraph(
        'The Dynamic Debt Covenant Surveillance Engine (DDCSE) is a purpose-built private credit '
        'monitoring platform designed to replicate the analytical workflow of a Credit Analyst or '
        'Portfolio Manager at a direct lending fund, BDC, or leveraged finance desk. It ingests '
        'real company financial statements, compiles covenant language into executable evaluation '
        'logic, assesses multi-covenant compliance, scores breach severity on a continuous 0–100 scale, '
        'simulates cross-default propagation cascades using graph theory, and generates institutional-grade '
        'surveillance reports. The engine operates on four primary modules:',
        S['framework_body']))
    story.append(Spacer(1, 2 * mm))

    # Architecture table
    arch_data = [
        [Paragraph('<b>Module</b>', S['white_bold']),
         Paragraph('<b>Function</b>', S['white_bold']),
         Paragraph('<b>Key Technologies</b>', S['white_bold'])],
        ['Data Pipeline\n(data_fetcher.py)',
         'Ingests financial statements; normalizes Total Debt, Cash, EBITDA from '
         'yfinance or static SEC EDGAR registry; validates data lineage',
         'yfinance, pandas, structured fallback registry'],
        ['AST-Safe Compiler\n(compiler.py)',
         'Parses covenant language rules into executable contracts; eliminates eval()/exec() '
         'for production safety; emits typed CovenantContract objects',
         'Python AST, dataclasses, typed contracts'],
        ['Analytics Engine\n(analytics_v2.py)',
         'Multi-covenant runner, severity scoring, trend erosion detection, '
         'macro shock matrix (EBITDA × debt sensitivity), NetworkX cascade simulation',
         'NetworkX, NumPy, dataclasses'],
        ['Report Generator\n(generate_report.py)',
         'Bloomberg/MS-style PDF with cover, TOC, company deep-dives, cascade '
         'analysis, stress matrices, methodology, and disclaimer',
         'ReportLab, Matplotlib, institutional design system'],
    ]
    arch_tbl = Table(arch_data,
        colWidths=[CONTENT_W * x for x in [0.20, 0.48, 0.32]],
        repeatRows=1)
    arch_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LGRAY]),
        ('GRID', (0,0), (-1,-1), 0.3, BORDER),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('FONTNAME', (0,1), (0,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0,1), (0,-1), BLUE),
    ]))
    story.append(arch_tbl)
    story.append(Spacer(1, 4 * mm))

    # ── 1.2 Covenant Taxonomy
    story.append(Paragraph('1.2  Covenant Taxonomy & Evaluation Logic', S['h3']))
    story.append(Paragraph(
        'DDCSE monitors four canonical covenant types that represent the standard maintenance '
        'covenant package in US leveraged finance and direct lending credit agreements. Each covenant '
        'is evaluated against the contractual threshold using AST-safe arithmetic — no string evaluation '
        'or exec() calls — ensuring that the engine is production-safe and audit-ready.',
        S['framework_body']))
    story.append(Spacer(1, 2 * mm))

    cov_data = [
        [Paragraph('<b>Type</b>', S['white_bold']),
         Paragraph('<b>Formula</b>', S['white_bold']),
         Paragraph('<b>Operator</b>', S['white_bold']),
         Paragraph('<b>Typical Threshold</b>', S['white_bold']),
         Paragraph('<b>Breach Signal</b>', S['white_bold'])],
        ['Net Leverage (NLR)',
         '(Total Debt − Cash) ÷ EBITDA',
         '≤ threshold', '3.5x – 8.0x (sector/rating)', 'Leverage spiral; EBITDA erosion outpaces deleveraging'],
        ['Interest Coverage (ICR)',
         'EBITDA ÷ Interest Expense',
         '≥ threshold', '1.75x – 3.00x', 'Debt service stress; cash burn approaching EBITDA'],
        ['Fixed Charge Coverage (FCCR)',
         '(EBITDA − CapEx) ÷ Interest Expense',
         '≥ threshold', '1.10x – 1.50x', 'Investment cycle consuming interest capacity'],
        ['Min. Liquidity',
         'Unrestricted Cash + Revolver Availability',
         '≥ threshold', '$250M – $1,500M (size-adjusted)', 'Liquidity runway compression; covenant waiver risk'],
    ]
    cov_tbl = Table(cov_data,
        colWidths=[CONTENT_W * x for x in [0.16, 0.22, 0.11, 0.18, 0.33]],
        repeatRows=1)
    cov_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BLUE),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 7.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LGRAY]),
        ('GRID', (0,0), (-1,-1), 0.3, BORDER),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('FONTNAME', (0,1), (0,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0,1), (0,-1), BLUE),
    ]))
    story.append(cov_tbl)
    story.append(Spacer(1, 4 * mm))

    # ── 1.3 Severity Scoring
    story.append(Paragraph('1.3  Severity Scoring Model  (0–100 Continuous)', S['h3']))
    story.append(Paragraph(
        'Each covenant is assigned a severity score on a continuous 0–100 scale based on the '
        'breach depth or proximity to the threshold. The portfolio severity score is the '
        'probability-weighted maximum across all monitored covenants, anchoring on the most '
        'critical risk signal.',
        S['framework_body']))
    story.append(Spacer(1, 2 * mm))

    sev_data = [
        [Paragraph('<b>Score Band</b>', S['white_bold']),
         Paragraph('<b>Classification</b>', S['white_bold']),
         Paragraph('<b>Definition</b>', S['white_bold']),
         Paragraph('<b>Recommended Action</b>', S['white_bold'])],
        ['0 – 30', 'COMPLIANT', '> 10% buffer to threshold; trajectory stable', 'Routine quarterly monitoring'],
        ['30 – 60', 'WATCHLIST', '0–10% buffer; or deteriorating trend', 'Increased monitoring; request updated financial package'],
        ['60 – 85', 'BREACH — Moderate', '0–25% breach depth; waiver likely needed', 'Immediate lender notification; engage advisors; waiver process'],
        ['85 – 100', 'BREACH — Deep', '> 25% breach depth; restructuring risk', 'Credit committee escalation; distressed advisory; cascade risk assessment'],
    ]
    sev_tbl = Table(sev_data,
        colWidths=[CONTENT_W * x for x in [0.14, 0.16, 0.38, 0.32]],
        repeatRows=1)
    sev_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 7.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LGRAY]),
        ('GRID', (0,0), (-1,-1), 0.3, BORDER),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('TEXTCOLOR', (1,1), (1,1), GREEN),
        ('TEXTCOLOR', (1,2), (1,2), AMBER),
        ('TEXTCOLOR', (1,3), (1,4), RED),
        ('FONTNAME', (0,1), (1,-1), 'Helvetica-Bold'),
    ]))
    story.append(sev_tbl)
    story.append(Spacer(1, 4 * mm))

    # ── 1.4 Cross-Default Cascade
    story.append(Paragraph('1.4  Cross-Default Cascade Simulation (NetworkX BFS)', S['h3']))
    story.append(Paragraph(
        'DDCSE models the corporate debt hierarchy as a directed graph G = (V, E) using NetworkX, '
        'where each node V represents a debt tranche or legal entity (HoldCo, OpCo, subsidiary) '
        'and each directed edge E represents a guarantee relationship or cross-default clause. '
        'When a primary breach is triggered, a BFS (Breadth-First Search) propagation algorithm '
        'traverses the graph, activating technical defaults only on nodes where '
        'cross_default_clause = True. This models the real-world mechanic of cross-acceleration '
        'provisions common in leveraged buyout credit agreements.',
        S['framework_body']))
    story.append(Spacer(1, 2 * mm))

    cascade_detail = [
        [Paragraph('<b>Concept</b>', S['white_bold']),
         Paragraph('<b>Implementation</b>', S['white_bold']),
         Paragraph('<b>Financial Meaning</b>', S['white_bold'])],
        ['Primary Breach', 'Initial node added to BFS queue; status set to breach',
         'Borrower misses covenant test; lender has right to accelerate'],
        ['Cross-Default Propagation', 'BFS traversal via graph edges where cross_default=True',
         'Acceleration of one facility triggers cross-acceleration provisions in linked tranches'],
        ['Cascade Depth', 'Longest shortest-path from origin to any affected node',
         'Structural complexity of the default; deeper = more complex workout'],
        ['Debt at Risk', 'Sum of face_value_usd_m across all propagation_path nodes',
         'Maximum aggregate face value that could be accelerated in a technical default scenario'],
    ]
    casc_tbl = Table(cascade_detail,
        colWidths=[CONTENT_W * x for x in [0.20, 0.38, 0.42]],
        repeatRows=1)
    casc_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BLUE),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 7.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LGRAY]),
        ('GRID', (0,0), (-1,-1), 0.3, BORDER),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('FONTNAME', (0,1), (0,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0,1), (0,-1), BLUE),
    ]))
    story.append(casc_tbl)
    story.append(Spacer(1, 4 * mm))

    # ── 1.5 Macro Stress Matrix
    story.append(Paragraph('1.5  Macro Stress Matrix', S['h3']))
    story.append(Paragraph(
        'For each credit, DDCSE generates a 6×5 NLR sensitivity matrix across simultaneous '
        'EBITDA compression (0% to –50% in 10% steps) and total debt increases (0% to +30% in '
        '5–10% steps). Each cell shows the stressed NLR value, colour-coded green/amber/red '
        'against the contractual threshold. This replicates the stress-testing conducted by '
        'credit committees at direct lending funds to assess "covenant headroom under a '
        'downside scenario" — a standard deliverable in portfolio monitoring.',
        S['framework_body']))
    story.append(Spacer(1, 4 * mm))

    # ── 1.6 Data pipeline
    story.append(Paragraph('1.6  Data Pipeline & Sources', S['h3']))
    story.append(Paragraph(
        'DDCSE is designed with a two-tier data pipeline: (1) a live market data layer via '
        'yfinance that pulls quarterly balance sheet and income statement data for real-time '
        'covenant evaluation; and (2) a static SEC EDGAR registry (real_cases.py) containing '
        'verified financial data for five representative companies sourced directly from '
        '10-K and 10-Q filings. In sandbox or restricted-network environments where Yahoo Finance '
        'endpoints are unavailable (HTTP 403), the engine transparently falls back to the SEC '
        'EDGAR static registry, preserving full analytical fidelity with clearly disclosed data '
        'lineage. All data in this report derives from the static registry with sources cited at '
        'the individual company level.',
        S['framework_body']))
    story.append(Spacer(1, 3 * mm))

    story.append(Table([[
        Paragraph(
            '⚑  <b>Data Note:</b> Yahoo Finance API was unavailable in the report generation '
            'environment (HTTP 403 — network egress restriction). All financial figures in this '
            'report are sourced from the DDCSE SEC EDGAR static registry, which references '
            'specific 10-K / 10-Q filings with CIK citations. Data quality and audit trail are '
            'unaffected.',
            ParagraphStyle('dn', fontName='Helvetica', fontSize=8, textColor=DGRAY,
                leading=12, leftIndent=6)),
    ]], colWidths=[CONTENT_W], style=TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FDF3E7')),
        ('BOX', (0,0), (-1,-1), 1.0, AMBER),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
    ])))
    story.append(PageBreak())


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — PORTFOLIO OVERVIEW
# ─────────────────────────────────────────────────────────────────────────────
def build_portfolio_overview(story, cases):
    section_header_block(story, '2. Portfolio Overview & Severity Heat Map',
        'Five-company surveillance portfolio · FY2023 / Q3 2023 financial data')

    # Severity scores
    enriched = []
    for c in cases:
        case = CASE_REGISTRY[c['ticker']]
        results = evaluate_package(case['covenants'])
        sev = portfolio_severity_score(results)
        enriched.append({**c, 'severity': sev, 'results': results})

    story.append(make_severity_heatmap(enriched))
    story.append(Paragraph(
        'Figure 2: Portfolio severity heat map. Score 0–30 = Compliant, 30–60 = Watchlist, '
        '60–100 = Breach. Derived from DDCSE continuous severity scoring model.',
        S['note']))
    story.append(Spacer(1, 4 * mm))

    # Detailed covenant matrix
    story.append(Paragraph('Multi-Covenant Compliance Matrix', S['h2']))
    cov_names = ['NLR', 'ICR', 'FCCR', 'Min. Liquidity']
    hdr = ['Ticker', 'Company'] + cov_names + ['Severity', 'Overall']
    matrix_data = [hdr]

    for c in enriched:
        case = CASE_REGISTRY[c['ticker']]
        results = c['results']
        row = [
            Paragraph(f'<b>{c["ticker"]}</b>', S['label']),
            Paragraph(case['name'][:26], S['body']),
        ]
        for r in results:
            scolor = status_color(r.status)
            actual_s = f'${r.actual:.0f}M' if r.unit == '$M' else f'{r.actual:.2f}x'
            row.append(Paragraph(
                f'<b>{actual_s}</b><br/><font size="6.5" color="{HEX["mgray"]}">{r.status}</font>',
                ParagraphStyle('mc', fontName='Helvetica-Bold', fontSize=8,
                    textColor=scolor, alignment=TA_CENTER, leading=12)))
        sev = c['severity']
        row.append(Paragraph(f'<b>{sev:.0f}</b>',
            ParagraphStyle('sv2', fontName='Helvetica-Bold', fontSize=9,
                textColor=RED if sev >= 70 else (AMBER if sev >= 40 else GREEN),
                alignment=TA_CENTER)))
        overall = ('BREACH' if any(r.status == 'BREACH' for r in results) else
                   'WATCHLIST' if any(r.status == 'WATCHLIST' for r in results) else 'COMPLIANT')
        row.append(Paragraph(f'<b>{overall}</b>',
            ParagraphStyle('ov', fontName='Helvetica-Bold', fontSize=8,
                textColor=status_color(overall), alignment=TA_CENTER)))
        matrix_data.append(row)

    col_w = [CONTENT_W * x for x in [0.08, 0.24, 0.13, 0.13, 0.13, 0.13, 0.09, 0.10]]
    matrix_tbl = Table(matrix_data, colWidths=col_w, repeatRows=1)
    matrix_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LGRAY]),
        ('GRID', (0,0), (-1,-1), 0.3, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(matrix_tbl)
    story.append(PageBreak())


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 — COMPANY DEEP DIVES
# ─────────────────────────────────────────────────────────────────────────────
def build_company_page(story, ticker, case_num):
    case = CASE_REGISTRY[ticker]
    nd   = case['total_debt'] - case['cash']
    nlr  = nd / case['ebitda_ltm']
    icr  = case['ebitda_ltm'] / case['interest_expense_ltm']
    fccr = (case['ebitda_ltm'] - case['capex_ltm']) / case['interest_expense_ltm']
    results = evaluate_package(case['covenants'])
    sev  = portfolio_severity_score(results)

    any_breach = any(r.status == 'BREACH' for r in results)
    any_watch  = any(r.status in ('WATCHLIST','WARNING') for r in results)
    overall    = 'BREACH' if any_breach else ('WATCHLIST' if any_watch else 'COMPLIANT')

    trend_data = detect_trend_erosion(case['trend_nlr'], case['covenants'][0]['threshold'], 'lte')

    # ── Company header
    story.append(Table([[
        Paragraph(
            f'<b>3.{case_num}  {ticker}</b> — {case["name"]}',
            ParagraphStyle('chd', fontName='Helvetica-Bold', fontSize=13,
                textColor=WHITE, leading=18)),
        Paragraph(f'<b>{overall}</b>',
            ParagraphStyle('cst', fontName='Helvetica-Bold', fontSize=12,
                textColor=status_color(overall), alignment=TA_RIGHT)),
    ]], colWidths=[CONTENT_W * 0.75, CONTENT_W * 0.25],
    style=TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), NAVY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (0,-1), 12),
        ('RIGHTPADDING', (-1,0), (-1,-1), 12),
    ])))
    story.append(Spacer(1, 2 * mm))

    # ── Sub-header bar (sector, exchange, filing)
    story.append(Table([[
        Paragraph(f'{case["sector"]}  ·  {case["exchange"]}  ·  {case["filing"]}  ·  As of {case["as_of"]}',
                  ParagraphStyle('csh', fontName='Helvetica', fontSize=8,
                      textColor=colors.HexColor('#B0C4DE'), leading=12)),
    ]], colWidths=[CONTENT_W], style=TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BLUE),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
    ])))
    story.append(Spacer(1, 3 * mm))

    # ── KPI band
    kpi_band(story, [
        ('Net Leverage', f'{nlr:.2f}x',
         HEX['red'] if nlr > case['covenants'][0]['threshold'] else HEX['green'],
         f'Threshold: {case["covenants"][0]["threshold"]:.2f}x'),
        ('Interest Coverage', f'{icr:.2f}x',
         HEX['red'] if icr < case['covenants'][1]['threshold'] else HEX['green'],
         f'Threshold: {case["covenants"][1]["threshold"]:.2f}x'),
        ('FCCR', f'{fccr:.2f}x',
         HEX['red'] if fccr < case['covenants'][2]['threshold'] else HEX['green'],
         f'Threshold: {case["covenants"][2]["threshold"]:.2f}x'),
        ('Severity Score', f'{sev:.0f}/100',
         HEX['red'] if sev >= 70 else (HEX['amber'] if sev >= 40 else HEX['green']),
         f'{case["credit_rating"]} / {case["outlook"][:12]}'),
        ('Net Debt', f'${nd/1000:.1f}B',
         HEX['navy'], f'{case["units"]} USD'),
    ])
    story.append(Spacer(1, 3 * mm))

    # ── Two-column: financials + covenant table
    fin_rows = [
        [Paragraph('FINANCIAL SUMMARY', ParagraphStyle('fsh', fontName='Helvetica-Bold',
            fontSize=8, textColor=WHITE)), ''],
        ['Total Debt', f'${case["total_debt"]:,.0f}M'],
        ['Cash & Equivalents', f'${case["cash"]:,.0f}M'],
        ['Net Debt', f'${nd:,.0f}M'],
        ['EBITDA (LTM)', f'${case["ebitda_ltm"]:,.0f}M'],
        ['Revenue (LTM)', f'${case["revenue_ltm"]:,.0f}M'],
        ['Interest Expense', f'${case["interest_expense_ltm"]:,.0f}M'],
        ['CapEx (LTM)', f'${case["capex_ltm"]:,.0f}M'],
        ['EV (USD M)', f'${case["enterprise_value_usd_m"]:,.0f}M'],
        ['Credit Rating', f'{case["credit_rating"]} / {case["outlook"][:14]}'],
    ]
    fin_tbl = Table(fin_rows, colWidths=[40 * mm, 34 * mm])
    fin_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BLUE),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('SPAN', (0,0), (-1,0)),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 7.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LGRAY]),
        ('GRID', (0,0), (-1,-1), 0.3, BORDER),
        ('ALIGN', (1,1), (1,-1), 'RIGHT'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('FONTNAME', (0,1), (0,-1), 'Helvetica'),
        ('TEXTCOLOR', (0,1), (-1,-1), DGRAY),
    ]))

    cov_rows = [
        [Paragraph('COVENANT TESTS', ParagraphStyle('cvhd', fontName='Helvetica-Bold',
            fontSize=8, textColor=WHITE)), '', '', ''],
        [Paragraph('Covenant', S['label']), Paragraph('Actual', S['label']),
         Paragraph('Thresh', S['label']), Paragraph('Status', S['label'])],
    ]
    for r in results:
        actual_s = f'${r.actual:.0f}M' if r.unit == '$M' else f'{r.actual:.2f}x'
        thresh_s = f'${r.threshold:.0f}M' if r.unit == '$M' else f'{r.threshold:.2f}x'
        buf_s = f'{r.buffer_pct * 100:.1f}%' if r.buffer_distance >= 0 else f'▼{abs(r.buffer_pct*100):.1f}%'
        scolor = status_color(r.status)
        cov_rows.append([
            Paragraph(r.name[:28], S['small_d']),
            Paragraph(f'<b>{actual_s}</b> <font size="6.5" color="{HEX["mgray"]}">({buf_s})</font>',
                ParagraphStyle('av2', fontName='Helvetica-Bold', fontSize=8, textColor=scolor)),
            Paragraph(thresh_s, S['small']),
            Paragraph(f'<b>{r.status}</b>',
                ParagraphStyle('sv3', fontName='Helvetica-Bold', fontSize=7.5, textColor=scolor)),
        ])
    cov_tbl = Table(cov_rows, colWidths=[44 * mm, 24 * mm, 16 * mm, 20 * mm])
    cov_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BLUE),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('SPAN', (0,0), (-1,0)),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#E8EDF4')),
        ('FONTSIZE', (0,0), (-1,-1), 7.5),
        ('ROWBACKGROUNDS', (0,2), (-1,-1), [WHITE, LGRAY]),
        ('GRID', (0,0), (-1,-1), 0.3, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))

    story.append(Table([[fin_tbl, cov_tbl]],
        colWidths=[72 * mm, CONTENT_W - 72 * mm],
        style=TableStyle([
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING", (1,0), (1,0), 5),
        ])))
    story.append(Spacer(1, 3 * mm))

    # ── Trend chart
    story.append(make_trend_chart(case, ticker))
    trend_dir = trend_data.get('direction', 'flat')
    story.append(Paragraph(
        f'Figure {case_num + 2}: NLR (red, left axis) and ICR (green, right axis) — 8-quarter trend. '
        f'Red dashed = NLR threshold ({case["covenants"][0]["threshold"]:.2f}x). '
        f'Trend signal: <b>{trend_dir.upper()}</b>.',
        S['note']))
    story.append(Spacer(1, 3 * mm))

    # ── Commentary
    story.append(Paragraph('Surveillance Commentary', S['h3']))
    story.append(Paragraph(case['case_notes'], S['body_j']))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(
        f'SEC Filing: <font color="blue">{case["sec_url"]}</font> · Sector: {case["sector"]}',
        S['note']))
    story.append(Spacer(1, 3 * mm))

    # ── Debt stack
    story.append(Paragraph('Debt Stack — Tranche Detail', S['h3']))
    ds_hdr = ['Tranche', 'Face Value', 'Seniority', 'Rate', 'Maturity', 'Lender', 'XD?', 'Status']
    ds_rows = [ds_hdr]
    for t in case['debt_stack']:
        sc = {'breach': RED, 'warning': AMBER, 'compliant': GREEN}[t['status']]
        ds_rows.append([
            Paragraph(t['tranche'][:40], S['small_d']),
            Paragraph(f'${t["face_value_usd_m"]:,.0f}M', S['right']),
            Paragraph(t['seniority'][:22], S['small_d']),
            Paragraph(t['rate'], S['small']),
            Paragraph(t['maturity'], S['small']),
            Paragraph(t['lender'][:22], S['small']),
            Paragraph('✓' if t['cross_default_clause'] else '—',
                ParagraphStyle('xd', fontName='Helvetica-Bold', fontSize=8,
                    textColor=RED if t['cross_default_clause'] else MGRAY,
                    alignment=TA_CENTER)),
            Paragraph(f'<b>{t["status"].upper()}</b>',
                ParagraphStyle('dss2', fontName='Helvetica-Bold', fontSize=7.5, textColor=sc)),
        ])
    cw = [CONTENT_W * x for x in [0.27, 0.10, 0.18, 0.14, 0.09, 0.12, 0.04, 0.06]]
    ds_tbl = Table(ds_rows, colWidths=cw, repeatRows=1)
    ds_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 7.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LGRAY]),
        ('GRID', (0,0), (-1,-1), 0.3, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(ds_tbl)
    story.append(PageBreak())


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4 — CROSS-DEFAULT CASCADE
# ─────────────────────────────────────────────────────────────────────────────
def build_cascade_section(story):
    section_header_block(story, '4. Cross-Default Cascade Analysis',
        'NetworkX BFS propagation · Envision Healthcare illustrative structure + live portfolio scenarios')

    story.append(Paragraph(
        'The cross-default cascade model simulates how a primary covenant breach at one entity '
        'propagates through a corporate debt hierarchy via cross-default and cross-acceleration '
        'clauses. In leveraged capital structures — particularly those with multiple tranches '
        'across holding companies and operating subsidiaries — a single breach can trigger '
        'technical defaults on a materially larger face value of debt than the originating facility. '
        'DDCSE models this through a directed NetworkX graph with per-tranche cross_default flags.',
        S['body_j']))
    story.append(Spacer(1, 4 * mm))

    # ── Envision Healthcare illustrative case
    story.append(Paragraph('4.1  Illustrative Case: Envision Healthcare-Style LBO Structure', S['h3']))
    story.append(Paragraph(
        'The following cascade analysis uses an Envision Healthcare-style LBO debt structure '
        '(HoldCo + OpCo + subsidiary tranches, total ~$3.0B face value) as the illustrative vehicle. '
        'Envision Healthcare filed for Chapter 11 in May 2023 following a leverage spiral driven by '
        'CMS reimbursement cuts and COVID volume impacts. The structure demonstrates a classic '
        'multi-tranche cascade where a HoldCo revolver breach propagates across all cross-default '
        'linked tranches.',
        S['body_j']))
    story.append(Spacer(1, 3 * mm))

    # Build graph and run cascade
    try:
        graph = build_envision_graph()
        from analytics import CorporateDebtNetwork
        net = CorporateDebtNetwork(use_real_case=True)

        # Get breach nodes
        breach_nodes = [n for n, d in graph.nodes(data=True) if d.get('status') == 'breach']
        origin = breach_nodes[0] if breach_nodes else list(graph.nodes)[0]

        cascade_results = net.simulate_macro_shock(origin, 'Primary Covenant Breach')
        total_at_risk = sum(v['face_value_usd_m'] for v in cascade_results.values())
        total_portfolio = sum(d.get('face_value', 0) for _, d in graph.nodes(data=True))

        # Cascade table
        story.append(Paragraph(f'Cascade Trigger: <b>{origin}</b>  ·  '
            f'Entities Affected: <b>{len(cascade_results)}</b>  ·  '
            f'Debt at Risk: <b>${total_at_risk:,.0f}M</b> / ${total_portfolio:,.0f}M portfolio',
            S['body']))
        story.append(Spacer(1, 2 * mm))

        casc_hdr = ['Affected Entity', 'Trigger Type', 'Facility', 'Face Value', 'Path', 'Shock Label']
        casc_data = [casc_hdr]
        for node_id, info in cascade_results.items():
            trigger_col = RED if info['trigger'] == 'primary_breach' else AMBER
            path_str = ' → '.join(info.get('propagation_path', [node_id]))
            casc_data.append([
                Paragraph(f'<b>{node_id}</b>', S['label']),
                Paragraph(info['trigger'].replace('_', ' ').title(),
                    ParagraphStyle('tc3', fontName='Helvetica-Bold', fontSize=8, textColor=trigger_col)),
                Paragraph(info.get('facility', node_id)[:30], S['small_d']),
                Paragraph(f'${info.get("face_value_usd_m", 0):,.0f}M', S['right']),
                Paragraph(path_str[:50], S['small']),
                Paragraph(info.get('shock_label', ''), S['small']),
            ])

        cw = [CONTENT_W * x for x in [0.18, 0.14, 0.22, 0.10, 0.26, 0.10]]
        casc_tbl = Table(casc_data, colWidths=cw, repeatRows=1)
        casc_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), NAVY),
            ('TEXTCOLOR', (0,0), (-1,0), WHITE),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 7.5),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LGRAY]),
            ('GRID', (0,0), (-1,-1), 0.3, BORDER),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 4),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(casc_tbl)
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(
            f'Note: Cascade propagation respects per-tranche cross_default_clause flags. '
            f'Only tranches with cross_default=True are activated. Total non-cross-default '
            f'debt excluded from propagation path per structural firewall.',
            S['note']))
    except Exception as e:
        story.append(Paragraph(f'Cascade simulation unavailable: {e}', S['body']))

    story.append(Spacer(1, 5 * mm))

    # ── Portfolio scenario table
    story.append(Paragraph('4.2  Portfolio Breach Scenarios — Cross-Default Risk Assessment', S['h3']))
    story.append(Paragraph(
        'The following table assesses cross-default risk for the two currently-breaching credits '
        '(WBA, ATUS) in the surveillance portfolio, estimating the incremental debt at risk beyond '
        'the primary breaching facility.',
        S['body_j']))
    story.append(Spacer(1, 2 * mm))

    scenario_data = [
        [Paragraph('<b>Credit</b>', S['white_bold']),
         Paragraph('<b>Breaching Facility</b>', S['white_bold']),
         Paragraph('<b>Primary Breach ($M)</b>', S['white_bold']),
         Paragraph('<b>Cross-Default Linked Debt ($M)</b>', S['white_bold']),
         Paragraph('<b>XD Clauses Active</b>', S['white_bold']),
         Paragraph('<b>Max Exposure ($M)</b>', S['white_bold']),
         Paragraph('<b>Assessment</b>', S['white_bold'])],
        ['WBA', '$3,500M Revolver + $2,000M TL', '$5,500M', '$27,664M (Public Notes)',
         '3 of 3 tranches', '$33,164M', 'Systemic — all tranches cross-default linked'],
        ['ATUS', '$2,850M Revolver + $4,103M TLB', '$6,953M', '$12,705M (Sr. Guaranteed)',
         '3 of 4 tranches', '$19,658M', 'High — $12.8B Sr. Notes excluded (no XD)'],
        ['CHTR', '$3,500M Revolver + $3,500M TLA', '$7,000M', '$86,421M (Sr. Secured Notes)',
         '3 of 3 tranches', '$94,921M', 'Watchlist — within covenant; XD risk if NLR ↑ 0.42x'],
        ['PARA', '$3,500M Revolver', '$3,500M', '$12,097M (Sr. Unsecured Notes)',
         '2 of 2 tranches', '$15,597M', 'Watchlist — 16.3% buffer; Skydance merger closing risk'],
    ]
    cw2 = [CONTENT_W * x for x in [0.07, 0.20, 0.12, 0.19, 0.11, 0.12, 0.19]]
    scenario_tbl = Table(scenario_data, colWidths=cw2, repeatRows=1)
    scenario_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 7.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LGRAY]),
        ('GRID', (0,0), (-1,-1), 0.3, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('FONTNAME', (0,1), (0,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0,1), (0,2), RED),
        ('TEXTCOLOR', (0,3), (0,4), AMBER),
        ('TEXTCOLOR', (0,5), (0,-1), AMBER),
    ]))
    story.append(scenario_tbl)
    story.append(PageBreak())


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5 — MACRO STRESS MATRICES
# ─────────────────────────────────────────────────────────────────────────────
def build_stress_section(story):
    section_header_block(story, '5. Macro Stress Sensitivity Matrices',
        'EBITDA compression × total debt increase · NLR sensitivity · Green = Safe · Amber = Watchlist · Red = Breach')

    story.append(Paragraph(
        'Each matrix below shows the stressed Net Leverage Ratio under simultaneous EBITDA '
        'compression (rows, 0% to –50%) and total debt increase (columns, 0% to +30%). '
        'Cells are colour-coded against the contractual NLR threshold. This analysis identifies '
        'the "cliff edge" — the combination of macro deterioration and incremental leverage '
        'that would trigger a covenant breach for currently-compliant credits.',
        S['body_j']))
    story.append(Spacer(1, 4 * mm))

    # 2 per row layout
    tickers_ordered = ['CHTR', 'WBA', 'PARA', 'HCA', 'ATUS']
    pairs = [(tickers_ordered[i], tickers_ordered[i+1] if i+1 < len(tickers_ordered) else None)
             for i in range(0, len(tickers_ordered), 2)]

    for left_t, right_t in pairs:
        left_case = CASE_REGISTRY[left_t]
        left_img  = make_shock_heatmap(left_t, left_case)

        if right_t:
            right_case = CASE_REGISTRY[right_t]
            right_img  = make_shock_heatmap(right_t, right_case)
            story.append(Table([[left_img, right_img]],
                colWidths=[CONTENT_W * 0.50, CONTENT_W * 0.50],
                style=TableStyle([
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('LEFTPADDING', (1,0), (1,0), 6),
                ])))
        else:
            story.append(Table([[left_img, '']],
                colWidths=[CONTENT_W * 0.50, CONTENT_W * 0.50],
                style=TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')])))
        story.append(Spacer(1, 3 * mm))

    story.append(Paragraph(
        'Colour key: Green = NLR within threshold with >10% buffer  ·  '
        'Amber = within 10% of threshold (Watchlist)  ·  Red = Breach (NLR > threshold).',
        S['note']))
    story.append(Spacer(1, 3 * mm))

    # Key insight callouts
    story.append(Paragraph('Key Stress Scenario Insights', S['h3']))
    insights = [
        ('CHTR — Charter Communications',
         'NLR of 4.58x vs 5.00x threshold provides only 8.4% buffer. A simultaneous 10% EBITDA '
         'compression and 5% debt increase would breach the covenant (stressed NLR ~5.35x). '
         'Cord-cutting acceleration is the primary macro risk vector.'),
        ('WBA — Walgreens Boots Alliance',
         'Already in breach at 5.40x vs 5.00x. Any further EBITDA compression immediately deepens '
         'the breach. The company is dependent on covenant waivers; the $1B cost reduction '
         'program must deliver to avoid acceleration risk.'),
        ('PARA — Paramount Global',
         'NLR of 3.87x vs 4.50x provides 16.3% buffer. Even a 20% EBITDA compression without '
         'debt increase keeps NLR at ~4.84x (breach). Skydance merger equity injection (~$8B) '
         'is the key deleveraging catalyst but carries closing risk.'),
        ('HCA — HCA Healthcare',
         'Healthiest credit in the portfolio. NLR of 3.10x vs 4.50x — 31.1% buffer. '
         'Only a simultaneous 40% EBITDA compression AND 20% debt increase breaches the covenant. '
         'Declining NLR trend provides additional margin.'),
        ('ATUS — Altice USA',
         'Deep breach at 8.95x vs 7.00x. No stress scenario improves the position; '
         'any EBITDA compression further deepens the breach. Distressed exchange or '
         'Chapter 11 is the base-case outcome absent a significant asset sale or equity injection.'),
    ]
    for title, text in insights:
        story.append(Table([[
            Paragraph(f'<b>{title}:</b> {text}',
                ParagraphStyle('ins', fontName='Helvetica', fontSize=8,
                    textColor=DGRAY, leading=12.5, leftIndent=6)),
        ]], colWidths=[CONTENT_W], style=TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), LGRAY),
            ('BOX', (0,0), (-1,-1), 0.4, BORDER),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
        ])))
        story.append(Spacer(1, 1.5 * mm))
    story.append(PageBreak())


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6 — METHODOLOGY & DISCLAIMER
# ─────────────────────────────────────────────────────────────────────────────
def build_methodology(story, today):
    section_header_block(story, '6. Methodology, Data Sources & Disclaimer')

    story.append(Paragraph('Engine Methodology', S['h3']))
    story.append(Paragraph(
        'DDCSE v2.1 implements a deterministic, audit-logged covenant surveillance pipeline. '
        'Covenant rules are compiled into typed Python dataclasses using an AST-safe compiler '
        '(no eval() or exec() calls), ensuring production safety. Financial metrics are '
        'extracted from yfinance quarterly financial statements with a multi-alias fallback '
        'strategy across known GAAP line-item names. When live data is unavailable, the engine '
        'falls back to the SEC EDGAR static registry. All evaluation decisions are logged with '
        'full lineage metadata (source line item, period, scale factor). '
        'Severity scores are computed as continuous 0–100 values using a piecewise linear function '
        'of breach depth / threshold proximity. Portfolio scores are the probability-weighted maximum '
        'across all covenants.',
        S['body_j']))
    story.append(Spacer(1, 3 * mm))

    story.append(Paragraph('Data Sources', S['h3']))
    disc_data = [
        [Paragraph('<b>Ticker</b>', S['white_bold']),
         Paragraph('<b>Company</b>', S['white_bold']),
         Paragraph('<b>Filing</b>', S['white_bold']),
         Paragraph('<b>Filed Date</b>', S['white_bold']),
         Paragraph('<b>CIK</b>', S['white_bold']),
         Paragraph('<b>Covenant Source</b>', S['white_bold'])],
        ['CHTR', 'Charter Communications', '10-K FY2023', 'Feb 9, 2024', 'CIK 0001091882',
         'Charter Operating Credit Agreement (2021 restatement) §7.1'],
        ['WBA', 'Walgreens Boots Alliance', '10-K FY2023 + Q2 FY2024', 'Oct 12, 2023', 'CIK 0001618921',
         'WBA Credit Agreement (2021) §6.1 — Note 8 10-K FY2023'],
        ['PARA', 'Paramount Global', '10-K FY2023', 'Feb 27, 2024', 'CIK 0000813828',
         'PARA Credit Agreement (2021) §7.01 — Note 9 10-K FY2023'],
        ['HCA', 'HCA Healthcare', '10-K FY2023', 'Feb 23, 2024', 'CIK 0000860731',
         'HCA Senior Secured Credit Facilities (2023 amendment) §7.1'],
        ['ATUS', 'Altice USA (CSC Holdings)', '10-K FY2023', 'Mar 5, 2024', 'CIK 0001672013',
         'CSC Holdings Credit Agreement (2019) §7.1 — waiver Aug 2023'],
    ]
    cw = [CONTENT_W * x for x in [0.07, 0.20, 0.18, 0.12, 0.13, 0.30]]
    disc_tbl = Table(disc_data, colWidths=cw, repeatRows=1)
    disc_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 7.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LGRAY]),
        ('GRID', (0,0), (-1,-1), 0.3, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(disc_tbl)
    story.append(Spacer(1, 4 * mm))

    # Stakeholder guidance
    story.append(Paragraph('Stakeholder Guide — Using This Report', S['h3']))
    sh_data = [
        [Paragraph('<b>Stakeholder</b>', S['white_bold']),
         Paragraph('<b>Relevant Sections</b>', S['white_bold']),
         Paragraph('<b>Key Use Case</b>', S['white_bold'])],
        ['Credit Committee / IC', 'Cover, §2, §4, §5', 'Portfolio breach overview; cascade risk; stress scenario approval'],
        ['Portfolio Manager', '§2, §3, §5', 'Per-credit covenant status; buffer proximity; stress break-even'],
        ['Credit Analyst', '§3 (all subsections)', 'Deep-dive financial profile; debt stack; trend erosion signal'],
        ['Risk / Compliance', '§1, §4, §6', 'Engine methodology; cascade model; audit trail and disclaimer'],
        ['Relationship Manager', 'Cover, §3 (relevant credit)', 'Client covenant status; waiver need assessment; talking points'],
        ['Legal Counsel', '§4, §6', 'Cross-default clause activation logic; data sources; SEC filings'],
    ]
    cw2 = [CONTENT_W * x for x in [0.22, 0.22, 0.56]]
    sh_tbl = Table(sh_data, colWidths=cw2, repeatRows=1)
    sh_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LGRAY]),
        ('GRID', (0,0), (-1,-1), 0.3, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('FONTNAME', (0,1), (0,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0,1), (0,-1), BLUE),
    ]))
    story.append(sh_tbl)
    story.append(Spacer(1, 4 * mm))

    # Disclaimer
    story.append(Table([[
        Paragraph(
            '<b>DISCLAIMER</b><br/><br/>'
            'This report is produced by the DDCSE engine for portfolio monitoring and analytical '
            'purposes only. All financial data is sourced from publicly available SEC EDGAR filings '
            'as noted in Section 6. Covenant thresholds reflect publicly disclosed credit agreement '
            'terms or representative private credit equivalents consistent with the issuer\'s rating '
            'category as of the filing dates noted. This document does not constitute investment '
            'advice, a solicitation to buy or sell securities, or a credit opinion of any kind. '
            'Figures are as of the filing dates noted and may not reflect subsequent developments, '
            'amendments, waivers, or other changes. Covenant status is as computed by the DDCSE '
            'engine and has not been verified by the borrowers, lenders, or their advisors. '
            'Past covenant status is not indicative of future compliance. All figures in USD millions '
            'unless otherwise stated. Cross-default cascade analysis is illustrative and based on '
            'the cross-default clause flags in the DDCSE registry; it does not constitute a legal '
            'opinion on the enforceability of any credit agreement provision.',
            ParagraphStyle('dis', fontName='Helvetica', fontSize=8, textColor=DGRAY,
                leading=13, alignment=TA_JUSTIFY, leftIndent=6)),
    ]], colWidths=[CONTENT_W], style=TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), LGRAY),
        ('BOX', (0,0), (-1,-1), 0.8, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ])))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        f'Generated by DDCSE v2.1  ·  github.com/DogInfantry/dynamic-debt-covenant-surveillance-frame  ·  {today}',
        ParagraphStyle('gen', fontName='Helvetica', fontSize=7.5,
            textColor=MGRAY, leading=11, alignment=TA_CENTER)))


# ─────────────────────────────────────────────────────────────────────────────
# MAIN BUILD
# ─────────────────────────────────────────────────────────────────────────────
def build_report(output_path):
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=15 * mm, rightMargin=15 * mm,
        topMargin=20 * mm, bottomMargin=14 * mm,
        title='DDCSE Covenant Surveillance Report',
        author='Anklesh Rawat — DogInfantry',
        subject='Private Credit Covenant Surveillance',
        keywords='covenant surveillance private credit leveraged finance',
    )

    story = []
    cases = list_cases()
    today = date.today().strftime('%B %d, %Y')

    build_cover(story, today, cases)
    build_toc(story)
    build_framework(story)
    build_portfolio_overview(story, cases)

    story.append(section_header_block.__code__)  # placeholder — replaced below
    story.pop()  # remove placeholder

    # Section 3 header
    story.append(Table([[
        Paragraph('3.  Company Deep-Dive Profiles',
                  ParagraphStyle('s3h', fontName='Helvetica-Bold', fontSize=13,
                      textColor=WHITE, leading=18)),
    ]], colWidths=[CONTENT_W], style=TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), NAVY),
        ('TOPPADDING', (0,0), (-1,-1), 9),
        ('BOTTOMPADDING', (0,0), (-1,-1), 9),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
    ])))
    story.append(Paragraph(
        'Five-company surveillance portfolio · SEC EDGAR 10-K / 10-Q data · Full covenant test suite',
        S['small']))
    story.append(Spacer(1, 3 * mm))

    for i, ticker in enumerate(['CHTR', 'WBA', 'PARA', 'HCA', 'ATUS'], 1):
        build_company_page(story, ticker, i)

    build_cascade_section(story)
    build_stress_section(story)
    build_methodology(story, today)

    doc.build(story, canvasmaker=ReportCanvas)
    print(f'✓ Report written: {output_path}')


if __name__ == '__main__':
    output = '/mnt/user-data/outputs/DDCSE_Covenant_Surveillance_Report_v2.pdf'
    build_report(output)

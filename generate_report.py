"""
Generate DDCSE Professional Covenant Surveillance Report (PDF)
Bloomberg / Morgan Stanley institutional aesthetic
"""
import sys
sys.path.insert(0, '/home/claude/repo')

import math
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfgen import canvas as rl_canvas
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import io
from reportlab.platypus import Image as RLImage

from real_cases import CASE_REGISTRY, list_cases
from analytics_v2 import evaluate_package, portfolio_severity_score

# ── Palette ──────────────────────────────────────────────────────────────────
NAVY   = colors.HexColor('#0A1628')
BLUE   = colors.HexColor('#1A3A5C')
LGRAY  = colors.HexColor('#F4F5F7')
MGRAY  = colors.HexColor('#8A9BB0')
DGRAY  = colors.HexColor('#2C3E50')
RED    = colors.HexColor('#C0392B')
AMBER  = colors.HexColor('#D4680A')
GREEN  = colors.HexColor('#1A7A4A')
WHITE  = colors.white
BORDER = colors.HexColor('#D0D7E2')

W, H = A4

def status_color(s):
    return {
        'BREACH': RED, 'WATCHLIST': AMBER,
        'WARNING': AMBER, 'COMPLIANT': GREEN
    }.get(s, MGRAY)

def status_hex(s):
    return {
        'BREACH': '#C0392B', 'WATCHLIST': '#D4680A',
        'WARNING': '#D4680A', 'COMPLIANT': '#1A7A4A'
    }.get(s, '#8A9BB0')

# ── Styles ────────────────────────────────────────────────────────────────────
def make_styles():
    return {
        'cover_title': ParagraphStyle('ct', fontName='Helvetica-Bold',
            fontSize=22, textColor=WHITE, leading=28, alignment=TA_LEFT),
        'cover_sub': ParagraphStyle('cs', fontName='Helvetica',
            fontSize=11, textColor=colors.HexColor('#B0C4DE'), leading=16, alignment=TA_LEFT),
        'cover_meta': ParagraphStyle('cm', fontName='Helvetica',
            fontSize=9, textColor=colors.HexColor('#8A9BB0'), leading=13, alignment=TA_LEFT),
        'section': ParagraphStyle('sh', fontName='Helvetica-Bold',
            fontSize=10, textColor=NAVY, leading=14, spaceAfter=4,
            borderPad=0, leftIndent=0),
        'body': ParagraphStyle('bd', fontName='Helvetica',
            fontSize=8.5, textColor=DGRAY, leading=13, spaceAfter=3),
        'small': ParagraphStyle('sm', fontName='Helvetica',
            fontSize=7.5, textColor=MGRAY, leading=11),
        'label': ParagraphStyle('lb', fontName='Helvetica-Bold',
            fontSize=7.5, textColor=NAVY, leading=11),
        'mono': ParagraphStyle('mn', fontName='Courier',
            fontSize=7.5, textColor=DGRAY, leading=11),
        'red': ParagraphStyle('rd', fontName='Helvetica-Bold',
            fontSize=8, textColor=RED, leading=11),
        'amber': ParagraphStyle('am', fontName='Helvetica-Bold',
            fontSize=8, textColor=AMBER, leading=11),
        'green': ParagraphStyle('gn', fontName='Helvetica-Bold',
            fontSize=8, textColor=GREEN, leading=11),
        'right': ParagraphStyle('rt', fontName='Helvetica',
            fontSize=8, textColor=DGRAY, leading=11, alignment=TA_RIGHT),
        'center': ParagraphStyle('ctr', fontName='Helvetica',
            fontSize=8, textColor=DGRAY, leading=11, alignment=TA_CENTER),
        'h2': ParagraphStyle('h2', fontName='Helvetica-Bold',
            fontSize=12, textColor=NAVY, leading=16, spaceAfter=6, spaceBefore=10),
        'h3': ParagraphStyle('h3', fontName='Helvetica-Bold',
            fontSize=9.5, textColor=BLUE, leading=13, spaceAfter=4, spaceBefore=6),
        'note': ParagraphStyle('nt', fontName='Helvetica-Oblique',
            fontSize=7.5, textColor=MGRAY, leading=11),
    }

S = make_styles()

# ── Page template with header/footer ─────────────────────────────────────────
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
        page_num = self._pageNumber
        if page_num == 1:
            return
        # Header bar
        self.setFillColor(NAVY)
        self.rect(0, H - 18*mm, W, 18*mm, fill=1, stroke=0)
        self.setFont('Helvetica-Bold', 8)
        self.setFillColor(WHITE)
        self.drawString(15*mm, H - 11*mm, 'DDCSE — Dynamic Debt Covenant Surveillance Engine')
        self.setFont('Helvetica', 7.5)
        self.setFillColor(colors.HexColor('#B0C4DE'))
        self.drawRightString(W - 15*mm, H - 11*mm, f'Confidential — Institutional Use Only')
        # Footer
        self.setFillColor(LGRAY)
        self.rect(0, 0, W, 10*mm, fill=1, stroke=0)
        self.setStrokeColor(BORDER)
        self.setLineWidth(0.3)
        self.line(0, 10*mm, W, 10*mm)
        self.setFont('Helvetica', 7)
        self.setFillColor(MGRAY)
        self.drawString(15*mm, 3.5*mm,
            f'Source: SEC EDGAR 10-K / 10-Q filings. Data as of filing dates noted. '
            f'Not investment advice. All figures USD millions.')
        self.drawRightString(W - 15*mm, 3.5*mm, f'Page {page_num} of {page_count}')

# ── Trend sparkline ───────────────────────────────────────────────────────────
def make_sparkline(quarters, nlr_series, icr_series, nlr_thresh, ticker):
    fig, ax = plt.subplots(figsize=(4.5, 1.6))
    fig.patch.set_facecolor('#F4F5F7')
    ax.set_facecolor('#F4F5F7')
    x = range(len(quarters))
    ax.plot(x, nlr_series, color='#C0392B', linewidth=1.8, marker='o', markersize=3, label='NLR (LHS)')
    ax.axhline(nlr_thresh, color='#C0392B', linewidth=0.8, linestyle='--', alpha=0.5)
    ax.set_xticks(list(x))
    ax.set_xticklabels(quarters, fontsize=5.5, rotation=30, ha='right')
    ax.set_ylabel('NLR (x)', fontsize=6, color='#C0392B')
    ax.tick_params(axis='y', labelsize=6, labelcolor='#C0392B')
    ax.tick_params(axis='x', labelsize=5.5)
    ax2 = ax.twinx()
    ax2.plot(x, icr_series, color='#1A7A4A', linewidth=1.4, marker='s', markersize=2.5,
             linestyle='--', label='ICR (RHS)')
    ax2.set_ylabel('ICR (x)', fontsize=6, color='#1A7A4A')
    ax2.tick_params(axis='y', labelsize=6, labelcolor='#1A7A4A')
    for spine in ax.spines.values():
        spine.set_linewidth(0.3)
    for spine in ax2.spines.values():
        spine.set_linewidth(0.3)
    ax.grid(True, alpha=0.2, linewidth=0.3)
    plt.tight_layout(pad=0.4)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return buf

# ── Portfolio overview bar chart ───────────────────────────────────────────────
def make_portfolio_chart(cases):
    tickers = [c['ticker'] for c in cases]
    nlrs    = [c['nlr'] for c in cases]
    threshs = [c['nlr_threshold'] for c in cases]
    colors_list = []
    for nlr, thresh in zip(nlrs, threshs):
        buf = (thresh - nlr) / thresh
        if nlr > thresh:
            colors_list.append('#C0392B')
        elif buf < 0.10:
            colors_list.append('#D4680A')
        else:
            colors_list.append('#1A7A4A')

    fig, ax = plt.subplots(figsize=(6.5, 2.4))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    bars = ax.bar(tickers, nlrs, color=colors_list, width=0.5, zorder=2, edgecolor='white', linewidth=0.5)
    for i, (ticker, thresh) in enumerate(zip(tickers, threshs)):
        ax.axhline(thresh, xmin=(i/len(tickers)) + 0.02, xmax=((i+1)/len(tickers)) - 0.02,
                   color='#0A1628', linewidth=1.2, linestyle='--', zorder=3)
    for bar, nlr in zip(bars, nlrs):
        ax.text(bar.get_x() + bar.get_width()/2, nlr + 0.08,
                f'{nlr:.2f}x', ha='center', va='bottom', fontsize=7, fontweight='bold',
                color='#2C3E50')
    ax.set_ylabel('Net Leverage Ratio (x)', fontsize=7.5)
    ax.set_title('Portfolio NLR vs Covenant Threshold (--- = threshold)', fontsize=8, color='#0A1628', pad=6)
    ax.tick_params(labelsize=8)
    ax.set_ylim(0, max(nlrs) * 1.18)
    ax.grid(axis='y', alpha=0.2, linewidth=0.3, zorder=1)
    for spine in ax.spines.values():
        spine.set_linewidth(0.3)
    legend_els = [
        mpatches.Patch(color='#C0392B', label='Breach'),
        mpatches.Patch(color='#D4680A', label='Watchlist (<10% buffer)'),
        mpatches.Patch(color='#1A7A4A', label='Compliant'),
    ]
    ax.legend(handles=legend_els, loc='upper left', fontsize=6.5, framealpha=0.8)
    plt.tight_layout(pad=0.5)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=160, bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return buf

# ── Build document ─────────────────────────────────────────────────────────────
def build_report(output_path):
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=22*mm, bottomMargin=14*mm,
        title='DDCSE Covenant Surveillance Report',
        author='Anklesh Rawat — DogInfantry',
        subject='Private Credit Covenant Surveillance',
    )

    story = []
    cases = list_cases()
    today = date.today().strftime('%B %d, %Y')

    # ── COVER PAGE ──────────────────────────────────────────────────────────
    # Navy cover block
    story.append(Table(
        [[Paragraph(
            'DYNAMIC DEBT COVENANT<br/>SURVEILLANCE ENGINE',
            ParagraphStyle('ct2', fontName='Helvetica-Bold', fontSize=20,
                textColor=WHITE, leading=26)
        )]],
        colWidths=[W - 30*mm],
        style=TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), NAVY),
            ('TOPPADDING', (0,0), (-1,-1), 18),
            ('BOTTOMPADDING', (0,0), (-1,-1), 18),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
        ])
    ))
    story.append(Spacer(1, 4*mm))
    story.append(Table(
        [[
            Paragraph('Quarterly Covenant Surveillance Report', S['cover_sub']),
            Paragraph(f'As of {today}', ParagraphStyle('dt', fontName='Helvetica-Bold',
                fontSize=10, textColor=NAVY, alignment=TA_RIGHT)),
        ]],
        colWidths=[(W-30*mm)*0.65, (W-30*mm)*0.35],
        style=TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')])
    ))
    story.append(HRFlowable(width='100%', thickness=0.5, color=BORDER, spaceAfter=6))

    # Executive summary box
    breaches = sum(1 for c in cases if c['nlr'] > c['nlr_threshold'])
    watchlist = sum(1 for c in cases if c['nlr'] <= c['nlr_threshold']
                   and (c['nlr_threshold'] - c['nlr']) / c['nlr_threshold'] < 0.10)
    compliant = len(cases) - breaches - watchlist

    exec_data = [
        [Paragraph('PORTFOLIO SUMMARY', ParagraphStyle('ps', fontName='Helvetica-Bold',
            fontSize=8.5, textColor=WHITE)),'','',''],
        [
            Paragraph(f'<font color="white"><b>{len(cases)}</b><br/>Credits Monitored</font>',
                ParagraphStyle('ps2', fontName='Helvetica', fontSize=8, textColor=WHITE, alignment=TA_CENTER)),
            Paragraph(f'<font color="#FF6B6B"><b>{breaches}</b><br/>Covenant Breach</font>',
                ParagraphStyle('ps3', fontName='Helvetica', fontSize=8, textColor=WHITE, alignment=TA_CENTER)),
            Paragraph(f'<font color="#FFD93D"><b>{watchlist}</b><br/>Watchlist</font>',
                ParagraphStyle('ps4', fontName='Helvetica', fontSize=8, textColor=WHITE, alignment=TA_CENTER)),
            Paragraph(f'<font color="#6BCB77"><b>{compliant}</b><br/>Compliant</font>',
                ParagraphStyle('ps5', fontName='Helvetica', fontSize=8, textColor=WHITE, alignment=TA_CENTER)),
        ]
    ]
    story.append(Table(exec_data, colWidths=[(W-30*mm)/4]*4,
        style=TableStyle([
            ('BACKGROUND', (0,0), (-1,0), NAVY),
            ('BACKGROUND', (0,1), (-1,1), BLUE),
            ('SPAN', (0,0), (-1,0)),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,0), 6),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('TOPPADDING', (0,1), (-1,1), 10),
            ('BOTTOMPADDING', (0,1), (-1,1), 10),
            ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor('#2A4A7A')),
        ])
    ))
    story.append(Spacer(1, 5*mm))

    # Portfolio chart
    chart_buf = make_portfolio_chart(cases)
    story.append(RLImage(chart_buf, width=W - 30*mm, height=65*mm))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        'Figure 1: Portfolio Net Leverage Ratio vs covenant threshold. '
        'Dashed line = contractual NLR ceiling per credit agreement. '
        'Source: SEC EDGAR 10-K / 10-Q filings (FY2023 / Q3 2023).',
        S['note']
    ))
    story.append(Spacer(1, 4*mm))

    # Portfolio summary table
    story.append(Paragraph('Portfolio Covenant Status — Summary', S['h2']))
    hdr = ['Ticker', 'Company', 'Sector', 'Rating', 'NLR', 'Thresh', 'ICR', 'Status']
    tbl_data = [hdr]
    for c in cases:
        nlr_v = c['nlr']
        thresh = c['nlr_threshold']
        buf_pct = (thresh - nlr_v) / thresh * 100
        if nlr_v > thresh:
            status = 'BREACH'
        elif buf_pct < 10:
            status = 'WATCHLIST'
        else:
            status = 'COMPLIANT'
        row = [
            Paragraph(f'<b>{c["ticker"]}</b>', S['label']),
            Paragraph(c['name'][:30], S['body']),
            Paragraph(c['sector'].split(' — ')[0], S['small']),
            Paragraph(c['credit_rating'], ParagraphStyle('rt2', fontName='Helvetica-Bold',
                fontSize=8, textColor=status_color(status) if status=='BREACH' else DGRAY)),
            Paragraph(f'<b>{nlr_v:.2f}x</b>',
                ParagraphStyle('nlr', fontName='Helvetica-Bold', fontSize=8,
                    textColor=status_color(status))),
            Paragraph(f'{thresh:.2f}x', S['center']),
            Paragraph(f'{c["icr"]:.2f}x', S['center']),
            Paragraph(f'<b>{status}</b>',
                ParagraphStyle('st', fontName='Helvetica-Bold', fontSize=8,
                    textColor=status_color(status))),
        ]
        tbl_data.append(row)

    col_w = [(W-30*mm) * x for x in [0.07, 0.24, 0.16, 0.07, 0.09, 0.09, 0.09, 0.12]]
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

    # ── INDIVIDUAL COMPANY PAGES ──────────────────────────────────────────────
    for ticker, case in CASE_REGISTRY.items():
        nd = case['total_debt'] - case['cash']
        nlr = nd / case['ebitda_ltm']
        icr = case['ebitda_ltm'] / case['interest_expense_ltm']
        fccr = (case['ebitda_ltm'] - case['capex_ltm']) / case['interest_expense_ltm']
        results = evaluate_package(case['covenants'])
        sev = portfolio_severity_score(results)

        # Determine overall status
        any_breach = any(r.status == 'BREACH' for r in results)
        any_watch  = any(r.status == 'WATCHLIST' for r in results)
        if any_breach:
            overall = 'BREACH'
        elif any_watch:
            overall = 'WATCHLIST'
        else:
            overall = 'COMPLIANT'

        # Company header
        story.append(Table(
            [[
                Paragraph(f'<b>{ticker}</b> — {case["name"]}',
                    ParagraphStyle('ch', fontName='Helvetica-Bold', fontSize=13,
                        textColor=WHITE, leading=18)),
                Paragraph(f'<b>{overall}</b>',
                    ParagraphStyle('st2', fontName='Helvetica-Bold', fontSize=11,
                        textColor=status_color(overall), alignment=TA_RIGHT)),
            ]],
            colWidths=[(W-30*mm)*0.75, (W-30*mm)*0.25],
            style=TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), NAVY),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('TOPPADDING', (0,0), (-1,-1), 10),
                ('BOTTOMPADDING', (0,0), (-1,-1), 10),
                ('LEFTPADDING', (0,0), (0,-1), 10),
                ('RIGHTPADDING', (-1,0), (-1,-1), 10),
            ])
        ))
        story.append(Spacer(1, 3*mm))

        # Key metrics row
        metric_data = [[
            Paragraph(f'<b>NLR: {nlr:.2f}x</b><br/><font color="#8A9BB0" size="7">thresh {case["covenants"][0]["threshold"]:.2f}x</font>',
                ParagraphStyle('m1', fontName='Helvetica-Bold', fontSize=10,
                    textColor=RED if nlr > case['covenants'][0]['threshold'] else GREEN,
                    alignment=TA_CENTER, leading=14)),
            Paragraph(f'<b>ICR: {icr:.2f}x</b><br/><font color="#8A9BB0" size="7">thresh {case["covenants"][1]["threshold"]:.2f}x</font>',
                ParagraphStyle('m2', fontName='Helvetica-Bold', fontSize=10,
                    textColor=RED if icr < case['covenants'][1]['threshold'] else GREEN,
                    alignment=TA_CENTER, leading=14)),
            Paragraph(f'<b>FCCR: {fccr:.2f}x</b><br/><font color="#8A9BB0" size="7">thresh {case["covenants"][2]["threshold"]:.2f}x</font>',
                ParagraphStyle('m3', fontName='Helvetica-Bold', fontSize=10,
                    textColor=RED if fccr < case['covenants'][2]['threshold'] else GREEN,
                    alignment=TA_CENTER, leading=14)),
            Paragraph(f'<b>Severity: {sev:.0f}/100</b><br/><font color="#8A9BB0" size="7">{case["credit_rating"]} / {case["outlook"][:12]}</font>',
                ParagraphStyle('m4', fontName='Helvetica-Bold', fontSize=10,
                    textColor=RED if sev >= 70 else (AMBER if sev >= 40 else GREEN),
                    alignment=TA_CENTER, leading=14)),
        ]]
        story.append(Table(metric_data, colWidths=[(W-30*mm)/4]*4,
            style=TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), LGRAY),
                ('GRID', (0,0), (-1,-1), 0.3, BORDER),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('TOPPADDING', (0,0), (-1,-1), 8),
                ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ])
        ))
        story.append(Spacer(1, 3*mm))

        # Two-column: financials + covenant table
        fin_rows = [
            [Paragraph('FINANCIALS', ParagraphStyle('fh', fontName='Helvetica-Bold', fontSize=8, textColor=WHITE)),''],
            ['Total Debt (USD M)', f'${case["total_debt"]:,.0f}M'],
            ['Cash & Equivalents', f'${case["cash"]:,.0f}M'],
            ['Net Debt', f'${nd:,.0f}M'],
            ['EBITDA (LTM)', f'${case["ebitda_ltm"]:,.0f}M'],
            ['Revenue (LTM)', f'${case["revenue_ltm"]:,.0f}M'],
            ['Interest Expense', f'${case["interest_expense_ltm"]:,.0f}M'],
            ['CapEx', f'${case["capex_ltm"]:,.0f}M'],
            ['Filing', case['filing'][:35]],
            ['As of', case['as_of']],
        ]
        fin_tbl = Table(fin_rows, colWidths=[38*mm, 32*mm])
        fin_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), BLUE),
            ('TEXTCOLOR', (0,0), (-1,0), WHITE),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 7.5),
            ('SPAN', (0,0), (-1,0)),
            ('ALIGN', (1,1), (1,-1), 'RIGHT'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LGRAY]),
            ('GRID', (0,0), (-1,-1), 0.3, BORDER),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('LEFTPADDING', (0,0), (-1,-1), 5),
            ('FONTNAME', (0,1), (0,-1), 'Helvetica'),
            ('TEXTCOLOR', (0,1), (-1,-1), DGRAY),
        ]))

        cov_header = [Paragraph('COVENANT TESTS', ParagraphStyle('cvh', fontName='Helvetica-Bold', fontSize=8, textColor=WHITE)),
                      '', '', '']
        cov_rows = [cov_header,
                    [Paragraph('Test', S['label']),
                     Paragraph('Actual', S['label']),
                     Paragraph('Thresh', S['label']),
                     Paragraph('Status', S['label'])]]
        for r in results:
            actual_s = f'${r.actual:.0f}M' if r.unit == '$M' else f'{r.actual:.2f}x'
            thresh_s = f'${r.threshold:.0f}M' if r.unit == '$M' else f'{r.threshold:.2f}x'
            scolor = status_color(r.status)
            cov_rows.append([
                Paragraph(r.name[:28], S['small']),
                Paragraph(f'<b>{actual_s}</b>',
                    ParagraphStyle('av', fontName='Helvetica-Bold', fontSize=8, textColor=scolor)),
                Paragraph(thresh_s, S['small']),
                Paragraph(r.status,
                    ParagraphStyle('sv', fontName='Helvetica-Bold', fontSize=7.5, textColor=scolor)),
            ])
        cov_tbl = Table(cov_rows, colWidths=[42*mm, 18*mm, 18*mm, 20*mm])
        cov_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), BLUE),
            ('TEXTCOLOR', (0,0), (-1,0), WHITE),
            ('SPAN', (0,0), (-1,0)),
            ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#E8EDF4')),
            ('FONTSIZE', (0,0), (-1,-1), 7.5),
            ('ROWBACKGROUNDS', (0,2), (-1,-1), [WHITE, LGRAY]),
            ('GRID', (0,0), (-1,-1), 0.3, BORDER),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('LEFTPADDING', (0,0), (-1,-1), 4),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))

        story.append(Table(
            [[fin_tbl, cov_tbl]],
            colWidths=[72*mm, W - 30*mm - 72*mm],
            style=TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (1,0), (1,0), 6)])
        ))
        story.append(Spacer(1, 3*mm))

        # Sparkline
        spark_buf = make_sparkline(
            case['trend_quarters'], case['trend_nlr'], case['trend_icr'],
            case['covenants'][0]['threshold'], ticker
        )
        story.append(RLImage(spark_buf, width=W - 30*mm, height=42*mm))
        story.append(Paragraph(
            f'Figure: NLR (left axis, red) and ICR (right axis, green) trend over 8 quarters. '
            f'Red dashed line = NLR covenant threshold ({case["covenants"][0]["threshold"]:.2f}x).',
            S['note']
        ))
        story.append(Spacer(1, 3*mm))

        # Case notes
        story.append(Paragraph('Surveillance Commentary', S['h3']))
        story.append(Paragraph(case['case_notes'], S['body']))
        story.append(Spacer(1, 2*mm))
        story.append(Paragraph(
            f'SEC Filing: {case["sec_url"]} | Sector: {case["sector"]}',
            S['note']
        ))

        # Debt stack
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph('Debt Stack — Tranche Detail', S['h3']))
        ds_hdr = ['Tranche', 'Face Value', 'Seniority', 'Rate', 'Maturity', 'Status']
        ds_rows = [ds_hdr]
        for t in case['debt_stack']:
            sc = {'breach': RED, 'warning': AMBER, 'compliant': GREEN}[t['status']]
            ds_rows.append([
                Paragraph(t['tranche'][:40], S['small']),
                Paragraph(f'${t["face_value_usd_m"]:,.0f}M', S['right']),
                Paragraph(t['seniority'][:22], S['small']),
                Paragraph(t['rate'], S['small']),
                Paragraph(t['maturity'], S['small']),
                Paragraph(f'<b>{t["status"].upper()}</b>',
                    ParagraphStyle('dss', fontName='Helvetica-Bold', fontSize=7.5, textColor=sc)),
            ])
        cw = [(W-30*mm)*x for x in [0.30, 0.12, 0.20, 0.17, 0.11, 0.10]]
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

    # ── DISCLAIMER PAGE ───────────────────────────────────────────────────────
    story.append(Paragraph('Methodology & Disclaimer', S['h2']))
    story.append(HRFlowable(width='100%', thickness=0.5, color=BORDER, spaceAfter=6))
    story.append(Paragraph(
        '<b>Engine:</b> DDCSE v2 — Dynamic Debt Covenant Surveillance Engine. '
        'AST-safe covenant compiler (no eval/exec). NetworkX cross-default cascade. '
        'Severity scoring 0–100 continuous. All covenant evaluations deterministic and audit-logged.',
        S['body']
    ))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph('<b>Data Sources:</b>', S['label']))
    disc_rows = [
        ['CHTR', 'Charter Communications 10-K FY2023', 'Filed Feb 9, 2024', 'CIK 0001091882'],
        ['WBA',  'Walgreens Boots Alliance 10-K FY2023', 'Filed Oct 12, 2023', 'CIK 0001618921'],
        ['PARA', 'Paramount Global 10-K FY2023', 'Filed Feb 27, 2024', 'CIK 0000813828'],
        ['HCA',  'HCA Healthcare 10-K FY2023', 'Filed Feb 23, 2024', 'CIK 0000860731'],
        ['ATUS', 'Altice USA 10-K FY2023', 'Filed Mar 5, 2024', 'CIK 0001672013'],
    ]
    disc_tbl = Table([['Ticker','Filing','Date','CIK']] + disc_rows,
        colWidths=[(W-30*mm)*x for x in [0.10, 0.45, 0.25, 0.20]])
    disc_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LGRAY]),
        ('GRID', (0,0), (-1,-1), 0.3, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(disc_tbl)
    story.append(Spacer(1, 5*mm))
    story.append(Paragraph(
        'DISCLAIMER: This report is produced by the DDCSE engine for portfolio monitoring and '
        'analytical purposes only. All financial data is sourced from publicly available SEC EDGAR '
        'filings. Covenant thresholds reflect publicly disclosed credit agreement terms or '
        'representative private credit equivalents consistent with the issuer\'s rating category. '
        'This document does not constitute investment advice, a solicitation to buy or sell '
        'securities, or a credit opinion. Figures are as of the filing dates noted and may not '
        'reflect subsequent developments. Past covenant status is not indicative of future compliance. '
        'All figures in USD millions unless otherwise stated.',
        S['note']
    ))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        f'Generated by DDCSE v2.0 | github.com/DogInfantry/dynamic-debt-covenant-surveillance-frame | {today}',
        S['small']
    ))

    doc.build(story, canvasmaker=ReportCanvas)
    print(f'Report written: {output_path}')

build_report('/mnt/user-data/outputs/DDCSE_Covenant_Surveillance_Report.pdf')

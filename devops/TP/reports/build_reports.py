"""Build local worked-solution PDFs and clearly labeled synthetic figures.

Dependencies: reportlab, pillow. No cloud commands or network calls are made.
"""
from __future__ import annotations

import json
import re
import textwrap
import tempfile
import sys
from io import BytesIO
from html import escape
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable, Image as PDFImage, KeepTogether, Paragraph,
    SimpleDocTemplate, Spacer, Table, TableStyle,
)

BASE = Path(__file__).resolve().parent
ASSETS = BASE / 'assets'
NAVY = colors.HexColor('#132d46')
TEAL = colors.HexColor('#087c86')
MUTED = colors.HexColor('#526476')
FIGURES: dict[str, bytes] = {}


def save_figure(im: Image.Image, name: str) -> None:
    stream = BytesIO()
    im.save(stream, format='PNG')
    FIGURES[name] = stream.getvalue()
    path = ASSETS / name
    # Replace atomically; embedded PDF figures use the in-memory bytes directly.
    with tempfile.NamedTemporaryFile(dir=ASSETS, suffix='.tmp', delete=False) as output:
        output.write(FIGURES[name])
        temporary = Path(output.name)
    try:
        temporary.replace(path)
    except OSError:
        if not path.exists():
            raise
        print('Standalone figure locked; preserved existing PNG:', name)
    finally:
        if temporary.exists():
            temporary.unlink()


def font_path(kind: str) -> Path:
    candidates = {
        'regular': ['C:/Windows/Fonts/arial.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'],
        'bold': ['C:/Windows/Fonts/arialbd.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'],
        'mono': ['C:/Windows/Fonts/consola.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'],
    }
    for item in candidates[kind]:
        if Path(item).is_file():
            return Path(item)
    raise FileNotFoundError(f'Install Arial/Consolas or DejaVu fonts ({kind}).')


def render_terminal(spec: dict) -> None:
    width = 1440
    font = ImageFont.truetype(str(font_path('mono')), 24)
    label = ImageFont.truetype(str(font_path('bold')), 22)
    small = ImageFont.truetype(str(font_path('regular')), 21)
    max_chars = 91
    lines = []
    for line in spec['lines']:
        lines.extend(textwrap.wrap(line, max_chars, subsequent_indent='    ',
                                   replace_whitespace=False, drop_whitespace=False) or [''])
    height = 150 + 37 * len(lines) + 65
    im = Image.new('RGB', (width, height), '#0d1724')
    draw = ImageDraw.Draw(im)
    draw.rectangle((0, 0, width, 63), fill='#1d3046')
    for x, fill in [(27, '#ef7771'), (53, '#e9bd64'), (79, '#65b99a')]:
        draw.ellipse((x, 23, x + 14, 37), fill=fill)
    draw.text((115, 16), spec['title'], font=label, fill='#ecf2f9')
    draw.rounded_rectangle((24, 79, width - 24, 122), radius=7, fill='#5a391b')
    draw.text((40, 87), 'SIMULATED EXAMPLE  |  Not captured from a running environment',
              font=label, fill='#ffd994')
    y = 145
    for line in lines:
        color = '#dae6f3'
        if '$ ' in line or line.startswith('PS '):
            color = '#73d9d0'
        elif line.startswith('#') or line.startswith('['):
            color = '#a8b6c6'
        elif line in ('active', 'HTTP/1.1 200 OK', 'VM running', 'false', '[]'):
            color = '#a2d4a1'
        draw.text((30, y), line, font=font, fill=color)
        y += 37
    draw.line((24, height - 51, width - 24, height - 51), fill='#31465d', width=2)
    draw.text((30, height - 42), 'DevOps worked solution  /  Example values and abbreviated output',
              font=small, fill='#9badc0')
    save_figure(im, spec['file'])


def render_browser() -> None:
    im = Image.new('RGB', (1440, 780), '#ffffff')
    draw = ImageDraw.Draw(im)
    regular = lambda n: ImageFont.truetype(str(font_path('regular')), n)
    bold = lambda n: ImageFont.truetype(str(font_path('bold')), n)
    draw.rectangle((0, 0, 1440, 100), fill='#e8edf3')
    draw.rounded_rectangle((160, 24, 1375, 77), radius=13, fill='#ffffff')
    draw.text((184, 36), 'Not secure  |  http://203.0.113.10', font=regular(25), fill='#384b5d')
    draw.text((35, 33), '<  >  O', font=regular(27), fill='#536879')
    draw.rectangle((0, 100, 1440, 164), fill='#fff0d9')
    draw.text((35, 118), 'SIMULATED BROWSER VIEW — not a screenshot of a live Azure site',
              font=bold(26), fill='#87501c')
    draw.text((310, 235), 'Welcome to nginx!', font=bold(51), fill='#141b22')
    messages = [
        'Illustration of the default welcome page expected after installation.',
        'A real capture must show the allocated VM address and loaded content.',
        '',
        'No HTTP request was made to the example address in this figure.',
        '203.0.113.10 is a documentation address.',
    ]
    y = 340
    for line in messages:
        draw.text((220, y), line, font=regular(25), fill='#374859')
        y += 47
    draw.line((220, 645, 1220, 645), fill='#d2dce7', width=2)
    draw.text((220, 675), 'TP2 / Nginx remote-browser acceptance criterion / illustrative figure',
              font=regular(24), fill='#536879')
    save_figure(im, 'tp2-05-browser.png')


def inline(text: str) -> str:
    # Escape literal text first; preserve only our intentionally generated markup.
    tokens: list[str] = []

    def token(value: str) -> str:
        tokens.append(value)
        return f'@@TOKEN{len(tokens) - 1}@@'

    text = re.sub(r'`([^`]+)`', lambda m: token(
        '<font name="LabMono" color="#24485c">' + escape(m[1]) + '</font>'), text)
    text = re.sub(r'\[([^\]]+)\]\((https?://[^\s)]+)\)', lambda m: token(
        f'<link href="{escape(m[2], quote=True)}" color="#087c86">{escape(m[1])}</link>'), text)
    text = escape(text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
    for i, value in enumerate(tokens):
        text = text.replace(f'@@TOKEN{i}@@', value)
    return text


def code_lines(text: str, width: float, font_size: float = 8.0) -> list[str]:
    result = []
    for line in text.splitlines():
        remaining = line.expandtabs(4)
        prefix = ''
        if not remaining:
            result.append(' ')
        while remaining:
            n = len(remaining)
            while n > 1 and pdfmetrics.stringWidth(prefix + remaining[:n], 'LabMono', font_size) > width:
                n -= 1
            result.append(prefix + remaining[:n])
            remaining = remaining[n:]
            prefix = '    '
    return result


def build_pdf(stem: str, short: bool = False) -> None:
    actual_execution = 'Codespaces' in stem
    page_w, page_h = A4
    margin = 43
    width = page_w - 2 * margin
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='LabBody', fontName='LabSans',
                              fontSize=9.2 if actual_execution else (9.3 if not short else 9.1),
                              leading=13.0 if actual_execution else (13.4 if not short else 12.4),
                              textColor=NAVY,
                              spaceAfter=6 if actual_execution else (7 if not short else 5),
                              splitLongWords=True))
    styles.add(ParagraphStyle(name='LabTitle', fontName='LabBold', fontSize=23 if not short else 19,
                              leading=28 if not short else 23, textColor=NAVY, spaceAfter=15))
    styles.add(ParagraphStyle(name='LabH2', fontName='LabBold', fontSize=14 if not short else 10.2,
                              leading=18 if not short else 13.1, textColor=TEAL,
                              spaceBefore=16 if not short else 7, spaceAfter=8 if not short else 3,
                              keepWithNext=True))
    styles.add(ParagraphStyle(name='LabH3', fontName='LabBold', fontSize=11,
                              leading=14, textColor=NAVY, spaceBefore=10, spaceAfter=6,
                              keepWithNext=True))
    styles.add(ParagraphStyle(name='LabSmall', fontName='LabSans', fontSize=8,
                              leading=10.5, textColor=MUTED, spaceAfter=10))
    styles.add(ParagraphStyle(name='LabTable', fontName='LabSans', fontSize=8,
                              leading=10.4, textColor=NAVY, wordWrap='CJK'))
    styles.add(ParagraphStyle(name='LabTableHead', parent=styles['LabTable'],
                              fontName='LabBold', textColor=colors.white))
    styles.add(ParagraphStyle(name='LabCode', fontName='LabMono', fontSize=8,
                              leading=10.5, textColor=NAVY, backColor=colors.HexColor('#f1f5f8'),
                              borderPadding=0, leftIndent=7, rightIndent=7,
                              spaceBefore=0, spaceAfter=0))
    body = styles['LabBody']
    story = []
    lines = (BASE / f'{stem}.md').read_text(encoding='utf-8').splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith('```'):
            content = []
            i += 1
            while i < len(lines) and not lines[i].startswith('```'):
                content.append(lines[i])
                i += 1
            wrapped = code_lines('\n'.join(content), width - 20)
            # Split long blocks into individual lines so they can span pages safely.
            story.append(Spacer(1, 6))
            for code_line in wrapped:
                story.append(Paragraph(escape(code_line).replace(' ', '&#160;'), styles['LabCode']))
            story.append(Spacer(1, 7))
            i += 1
            continue
        image_match = re.fullmatch(r'!\[([^\]]*)\]\(([^)]+)\)', line)
        if image_match:
            path = BASE / image_match[2]
            data = FIGURES[path.name] if path.name in FIGURES else path.read_bytes()
            source = BytesIO(data)
            with Image.open(source) as im:
                iw, ih = im.size
            scale = min(width / iw, 390 / ih)
            fig = PDFImage(BytesIO(data), width=iw * scale, height=ih * scale)
            fig.hAlign = 'LEFT'
            story.append(KeepTogether([Spacer(1, 7), fig, Spacer(1, 5),
                                        Paragraph(inline(image_match[1]), styles['LabSmall'])]))
            i += 1
            continue
        if line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r'[:\- ]+', c) for c in cells):
                    rows.append(cells)
                i += 1
            columns = len(rows[0])
            # Prefer additional room for prose in the last column.
            weights = [1] * columns
            if columns == 2:
                weights = [0.9, 1.7]
            elif columns == 3:
                weights = [0.85, 1.2, 1.5]
            total = sum(weights)
            widths = [width * w / total for w in weights]
            data = [[Paragraph(inline(c), styles['LabTableHead' if r == 0 else 'LabTable'])
                     for c in row] for r, row in enumerate(rows)]
            table = Table(data, colWidths=widths, repeatRows=1, hAlign='LEFT')
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), NAVY),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f1f6f8'), colors.white]),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 7),
                ('RIGHTPADDING', (0, 0), (-1, -1), 7),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LINEBELOW', (0, 0), (-1, 0), 1, TEAL),
                ('LINEBELOW', (0, 1), (-1, -1), .25, colors.HexColor('#d8e2ea')),
            ]))
            story.extend([Spacer(1, 5), table, Spacer(1, 10)])
            continue
        if line.startswith('# '):
            story.append(Paragraph(inline(line[2:]), styles['LabTitle']))
            story.append(HRFlowable(width='100%', thickness=2, color=TEAL, spaceAfter=12))
        elif line.startswith('## '):
            story.append(Paragraph(inline(line[3:]), styles['LabH2']))
        elif line.startswith('### '):
            story.append(Paragraph(inline(line[4:]), styles['LabH3']))
        elif line.startswith('- '):
            story.append(Paragraph('• ' + inline(line[2:]), body))
        elif re.match(r'^\d+\. ', line):
            story.append(Paragraph(inline(line), body))
        else:
            paragraph = [line]
            while i + 1 < len(lines) and lines[i + 1].strip() and not re.match(
                    r'^(#|```|\||!\[|- |\d+\. )', lines[i + 1]):
                i += 1
                paragraph.append(lines[i].strip())
            story.append(Paragraph(inline(' '.join(paragraph)), body))
        i += 1

    def decoration(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(NAVY)
        canvas.rect(0, page_h - 8, page_w, 8, fill=1, stroke=0)
        canvas.setFont('LabSans', 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(margin, page_h - 27, 'USTHB  /  DEVOPS & CLOUD COMPUTING  /  2026–2027')
        canvas.drawRightString(page_w - margin, page_h - 27,
                               'EXECUTION REPORT' if actual_execution else 'WORKED SOLUTION')
        canvas.setStrokeColor(colors.HexColor('#d9e2eb'))
        canvas.line(margin, 35, page_w - margin, 35)
        canvas.setFont('LabSans', 7.1)
        footer = ('User-provided execution screenshots • GitHub Codespaces • 03 Nov 2026'
                  if actual_execution else
                  'Simulated illustrations • No cloud execution claimed • 03 Nov 2026')
        canvas.drawString(margin, 23, footer)
        canvas.drawRightString(page_w - margin, 23, str(doc.page))
        canvas.restoreState()

    document = SimpleDocTemplate(str(BASE / f'{stem}.pdf'), pagesize=A4,
                                 rightMargin=margin, leftMargin=margin,
                                 topMargin=47, bottomMargin=48,
                                 title=lines[0].removeprefix('# '),
                                 author='DevOps lab reports',
                                 subject=('Codespaces execution report based on user-provided screenshots'
                                          if actual_execution else
                                          'Detailed lab solution with explicitly simulated illustrations'))
    document.build(story, onFirstPage=decoration, onLaterPages=decoration)
    print('Built', stem + '.pdf')


def main():
    ASSETS.mkdir(exist_ok=True)
    for name, kind in [('LabSans', 'regular'), ('LabBold', 'bold'), ('LabMono', 'mono')]:
        pdfmetrics.registerFont(TTFont(name, str(font_path(kind))))
    pdfmetrics.registerFontFamily('LabSans', normal='LabSans', bold='LabBold', italic='LabSans', boldItalic='LabBold')
    if '--codespaces-only' in sys.argv:
        build_pdf('TP2-Codespaces-report')
        return
    for spec in json.loads((ASSETS / 'captures.json').read_text(encoding='utf-8')):
        render_terminal(spec)
    render_browser()
    build_pdf('TP1-report')
    build_pdf('TP2-report')
    build_pdf('TP2-short-report', short=True)
    if (BASE / 'TP2-Codespaces-report.md').exists():
        build_pdf('TP2-Codespaces-report')


if __name__ == '__main__':
    main()

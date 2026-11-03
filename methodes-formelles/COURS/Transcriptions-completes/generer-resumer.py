"""Generate resumer.pdf from ../resumer.md. Requires ReportLab."""
from __future__ import annotations

import importlib.util
import re
import textwrap
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, HRFlowable, KeepTogether, PageBreak,
    PageTemplate, Paragraph, Preformatted, Spacer, Table, TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

COURSES = Path(__file__).resolve().parent.parent
NAVY = colors.HexColor('#193650')
TEAL = colors.HexColor('#087d85')
GREY = colors.HexColor('#536778')
PALE = colors.HexColor('#eef4f8')


def register_fonts():
    spec = importlib.util.find_spec('matplotlib')
    bundled = Path(spec.origin).parent / 'mpl-data/fonts/ttf' if spec else Path('/nonexistent')
    linux = Path('/usr/share/fonts/truetype/dejavu')
    choices = {
        'CoursSans': [bundled/'DejaVuSans.ttf', linux/'DejaVuSans.ttf', Path('C:/Windows/Fonts/arial.ttf')],
        'CoursBold': [bundled/'DejaVuSans-Bold.ttf', linux/'DejaVuSans-Bold.ttf', Path('C:/Windows/Fonts/arialbd.ttf')],
        'CoursMono': [bundled/'DejaVuSansMono.ttf', linux/'DejaVuSansMono.ttf', Path('C:/Windows/Fonts/consola.ttf')],
    }
    for name, paths in choices.items():
        path = next((path for path in paths if path.is_file()), None)
        if path is None:
            raise FileNotFoundError('Install DejaVu fonts or Arial/Consolas')
        pdfmetrics.registerFont(TTFont(name, str(path)))
    pdfmetrics.registerFontFamily('CoursSans', normal='CoursSans', bold='CoursBold',
                                  italic='CoursSans', boldItalic='CoursBold')


def inline(text):
    tokens = []
    def code(match):
        tokens.append('<font name="CoursMono" size="8.4" color="#254d61">' + escape(match[1]) + '</font>')
        return f'@@CODE{len(tokens)-1}@@'
    text = escape(re.sub(r'`([^`]+)`', code, text))
    text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
    for index, value in enumerate(tokens):
        text = text.replace(f'@@CODE{index}@@', value)
    return text


class ResumeDocument(BaseDocTemplate):
    def __init__(self, path, **kwargs):
        super().__init__(str(path), **kwargs)
        self.heading_counter = 0
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height,
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates(PageTemplate(id='resume', frames=frame, onPage=self.decorate))

    def beforeDocument(self):
        self.heading_counter = 0

    def decorate(self, canvas, doc):
        canvas.saveState()
        width, height = A4
        canvas.setFillColor(NAVY)
        canvas.rect(0, height-8, width, 8, fill=1, stroke=0)
        canvas.setFillColor(GREY)
        canvas.setFont('CoursSans', 7.1)
        canvas.drawString(self.leftMargin, height-29, 'USTHB · MÉTHODES FORMELLES POUR LE GÉNIE LOGICIEL')
        canvas.drawRightString(width-self.rightMargin, height-29, 'RÉSUMÉ DES QUATRE CHAPITRES')
        canvas.setStrokeColor(colors.HexColor('#d5e1e9'))
        canvas.line(self.leftMargin, 36, width-self.rightMargin, 36)
        canvas.setFont('CoursSans', 7.2)
        canvas.drawString(self.leftMargin, 23, 'Dr MEKAHLIA Fatma Zohra · Notes de révision · 4 novembre 2026')
        canvas.drawRightString(width-self.rightMargin, 23, str(doc.page))
        canvas.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == 'Chapter':
            self.heading_counter += 1
            key = f'section-{self.heading_counter}'
            title = flowable.getPlainText()
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(title, key, level=0, closed=False)
            self.notify('TOCEntry', (0, title, self.page, key))


def build():
    register_fonts()
    styles = {
        'body': ParagraphStyle('Body', fontName='CoursSans', fontSize=9.2, leading=13.5,
                               textColor=NAVY, spaceAfter=7),
        'chapter': ParagraphStyle('Chapter', fontName='CoursBold', fontSize=18, leading=23,
                                  textColor=TEAL, spaceAfter=15, keepWithNext=True),
        'section': ParagraphStyle('Section', fontName='CoursBold', fontSize=11, leading=15,
                                  textColor=NAVY, spaceBefore=12, spaceAfter=7, keepWithNext=True),
        'title': ParagraphStyle('Title', fontName='CoursBold', fontSize=40, leading=46,
                                textColor=NAVY, spaceAfter=16),
        'subtitle': ParagraphStyle('Subtitle', fontName='CoursBold', fontSize=17, leading=23,
                                   textColor=TEAL, spaceAfter=16),
        'table': ParagraphStyle('TableBody', fontName='CoursSans', fontSize=8.1, leading=11,
                                textColor=NAVY),
        'tablehead': ParagraphStyle('TableHead', fontName='CoursBold', fontSize=8.1,
                                    leading=11, textColor=colors.white),
        'code': ParagraphStyle('Code', fontName='CoursMono', fontSize=8, leading=11,
                               textColor=NAVY),
        'toc': ParagraphStyle('TOC', fontName='CoursSans', fontSize=10, leading=15,
                              textColor=NAVY, leftIndent=0, firstLineIndent=0,
                              rightIndent=25, spaceBefore=11),
    }
    document = ResumeDocument(COURSES/'resumer.pdf', pagesize=A4, leftMargin=44,
                              rightMargin=44, topMargin=49, bottomMargin=49,
                              title='resumer', author='Notes de révision — Méthodes formelles pour GL',
                              subject='Résumé organisé des chapitres 1 à 4 du cours de Dr MEKAHLIA')
    story = [Spacer(1, 35), Paragraph('resumer', styles['title']),
             Paragraph('Méthodes formelles pour le génie logiciel', styles['subtitle']),
             Paragraph('Les quatre chapitres du cours', styles['body']),
             Paragraph('Dr MEKAHLIA Fatma Zohra · USTHB · 5e année Software Engineering', styles['body']),
             Spacer(1, 10), HRFlowable(width='100%', thickness=2, color=TEAL), Spacer(1, 20),
             Paragraph('Sommaire', styles['section'])]
    contents = TableOfContents()
    contents.levelStyles = [styles['toc']]
    contents.dotsMinLevel = 0
    story.extend([contents, Spacer(1, 24),
                  Paragraph('Résumé des 155 diapositives consultées dans Classroom. Les remarques signalées en fin de document permettent de distinguer les coquilles du support et les précisions utiles à la révision.', styles['body'])])
    lines = (COURSES/'resumer.md').read_text(encoding='utf-8').splitlines()
    index = 0
    started = False
    while index < len(lines):
        line = lines[index].strip()
        if not started and not line.startswith('## '):
            index += 1
            continue
        started = True
        if not line:
            index += 1
            continue
        if line.startswith('## '):
            title = line[3:]
            if title.startswith('Chapitre ') or title.startswith('Synthèse générale'):
                story.append(PageBreak())
            story.append(Paragraph(inline(title), styles['chapter']))
            index += 1
            continue
        if line.startswith('### '):
            story.append(Paragraph(inline(line[4:]), styles['section']))
            index += 1
            continue
        if line.startswith('```'):
            index += 1
            code = []
            while index < len(lines) and not lines[index].startswith('```'):
                code.extend(textwrap.wrap(lines[index], width=89, subsequent_indent='  ',
                                          replace_whitespace=False, drop_whitespace=False) or [''])
                index += 1
            box = Table([[Preformatted('\n'.join(code), styles['code'])]], colWidths=[document.width])
            box.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PALE),
                                     ('BOX',(0,0),(-1,-1),.35,colors.HexColor('#dce7ee')),
                                     ('LEFTPADDING',(0,0),(-1,-1),9),
                                     ('RIGHTPADDING',(0,0),(-1,-1),9),
                                     ('TOPPADDING',(0,0),(-1,-1),8),
                                     ('BOTTOMPADDING',(0,0),(-1,-1),8)]))
            story.extend([Spacer(1,3), box, Spacer(1,9)])
            index += 1
            continue
        if line.startswith('|'):
            rows = []
            while index < len(lines) and lines[index].strip().startswith('|'):
                cells = [cell.strip() for cell in lines[index].strip().strip('|').split('|')]
                if not all(re.fullmatch(r'[:\- ]+', cell) for cell in cells):
                    rows.append(cells)
                index += 1
            count = len(rows[0])
            weights = [0.9,1.15,1.3] if count == 3 else [1]*count
            widths = [document.width*weight/sum(weights) for weight in weights]
            cells = [[Paragraph(inline(cell), styles['tablehead' if row == 0 else 'table'])
                      for cell in values] for row,values in enumerate(rows)]
            table = Table(cells, colWidths=widths, repeatRows=1, hAlign='LEFT')
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),
                                       ('ROWBACKGROUNDS',(0,1),(-1,-1),[PALE,colors.white]),
                                       ('VALIGN',(0,0),(-1,-1),'TOP'),
                                       ('LEFTPADDING',(0,0),(-1,-1),7),
                                       ('RIGHTPADDING',(0,0),(-1,-1),7),
                                       ('TOPPADDING',(0,0),(-1,-1),6),
                                       ('BOTTOMPADDING',(0,0),(-1,-1),6),
                                       ('LINEBELOW',(0,0),(-1,0),1,TEAL)]))
            story.extend([Spacer(1,3), table, Spacer(1,10)])
            continue
        if line.startswith('- '):
            story.append(Paragraph('• '+inline(line[2:]), styles['body']))
        else:
            text = [line]
            while index+1 < len(lines) and lines[index+1].strip() and not re.match(r'^(#|```|\||- |\d+\. )',lines[index+1]):
                index += 1
                text.append(lines[index].strip())
            story.append(Paragraph(inline(' '.join(text)), styles['body']))
        index += 1
    document.multiBuild(story)
    print('Generated', COURSES/'resumer.pdf')


if __name__ == '__main__':
    build()

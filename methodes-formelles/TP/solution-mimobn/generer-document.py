"""Build ../solution-mimobn.pdf and its editable Markdown from verified sources.

Requires Python 3, ReportLab, Pillow and DejaVu or Windows Arial/Consolas fonts.
This script formats the report; the exercise implementation and checks use Java.
"""
from __future__ import annotations

import importlib.util
import re
import textwrap
from html import escape
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, PageBreak, PageTemplate, Paragraph,
    Preformatted, Spacer, Table, TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parent
NAVY = colors.HexColor('#193650')
TEAL = colors.HexColor('#087d85')
PALE = colors.HexColor('#eef4f8')
GREY = colors.HexColor('#536778')


def register_fonts():
    spec = importlib.util.find_spec('matplotlib')
    bundled = Path(spec.origin).parent/'mpl-data/fonts/ttf' if spec else Path('/nonexistent')
    linux = Path('/usr/share/fonts/truetype/dejavu')
    for name, filename, fallback in [
        ('TDPSans', 'DejaVuSans.ttf', 'arial.ttf'),
        ('TDPBold', 'DejaVuSans-Bold.ttf', 'arialbd.ttf'),
        ('TDPMono', 'DejaVuSansMono.ttf', 'consola.ttf'),
    ]:
        choices = [bundled/filename, linux/filename, Path('C:/Windows/Fonts')/fallback]
        font = next((p for p in choices if p.is_file()), None)
        if font is None:
            raise FileNotFoundError('Install DejaVu or Arial/Consolas fonts')
        pdfmetrics.registerFont(TTFont(name, str(font)))
    pdfmetrics.registerFontFamily('TDPSans', normal='TDPSans', bold='TDPBold',
                                 italic='TDPSans', boldItalic='TDPBold')


def inline(value):
    tokens = []
    def save(html):
        tokens.append(html)
        return f'ZZTOKEN{len(tokens)-1}ZZ'
    value = re.sub(r'`([^`]+)`', lambda m: save(
        '<font name="TDPMono" size="8">'+escape(m[1])+'</font>'), value)
    value = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', lambda m: save(
        '<link href="'+escape(m[2], quote=True)+'" color="#087d85">'+escape(m[1])+'</link>'), value)
    value = escape(value)
    value = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', value)
    for index, token in enumerate(tokens):
        value = value.replace(f'ZZTOKEN{index}ZZ', token)
    return value


class Document(BaseDocTemplate):
    def __init__(self, path):
        super().__init__(str(path), pagesize=A4, leftMargin=44, rightMargin=44,
                         topMargin=50, bottomMargin=49, title='solution tdtp',
                         author='Corrigé pédagogique — Méthodes formelles',
                         subject='Réservation : contrats, Java, Petri, NuSMV et PRISM')
        self.counter = 0
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height,
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates(PageTemplate(id='report', frames=frame, onPage=self.decorate))

    def beforeDocument(self):
        self.counter = 0

    def decorate(self, canvas, doc):
        canvas.saveState()
        canvas.setFillColor(NAVY)
        canvas.rect(0, A4[1]-8, A4[0], 8, fill=1, stroke=0)
        canvas.setFont('TDPSans', 7)
        canvas.setFillColor(GREY)
        canvas.drawString(self.leftMargin, A4[1]-29, 'USTHB · MÉTHODES FORMELLES POUR LE GÉNIE LOGICIEL')
        canvas.drawRightString(A4[0]-self.rightMargin, A4[1]-29, 'SOLUTION TDTP')
        canvas.setStrokeColor(colors.HexColor('#d5e1e9'))
        canvas.line(self.leftMargin, 36, A4[0]-self.rightMargin, 36)
        canvas.drawString(self.leftMargin, 23, 'Système de réservation · Corrigé détaillé · 4 novembre 2026')
        canvas.drawRightString(A4[0]-self.rightMargin, 23, str(doc.page))
        canvas.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == 'Chapter':
            self.counter += 1
            key = f'section-{self.counter}'
            title = flowable.getPlainText()
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(title, key, level=0, closed=False)
            self.notify('TOCEntry', (0, title, self.page, key))


def expand_source():
    source = (ROOT/'rapport-source.md').read_text(encoding='utf-8')
    def include(match):
        relative = match[1]
        path = (ROOT/relative).resolve()
        if not path.is_relative_to(ROOT):
            raise ValueError(relative)
        language = {'.java':'java', '.smv':'text', '.pm':'text', '.pctl':'text',
                    '.puml':'plantuml'}.get(path.suffix, 'text')
        return '```'+language+'\n'+path.read_text(encoding='utf-8').rstrip()+'\n```'
    source = re.sub(r'\{\{include:([^}]+)\}\}', include, source)
    editable = source.replace('](figures/', '](solution-mimobn/figures/')
    (ROOT.parent/'solution-mimobn.md').write_text(editable, encoding='utf-8')
    return source


def build():
    register_fonts()
    source = expand_source()
    document = Document(ROOT.parent/'solution-mimobn.pdf')
    styles = {
        'body': ParagraphStyle('Body', fontName='TDPSans', fontSize=9.2, leading=13.5,
                              textColor=NAVY, spaceAfter=7),
        'chapter': ParagraphStyle('Chapter', fontName='TDPBold', fontSize=17, leading=22,
                                 textColor=TEAL, spaceBefore=16, spaceAfter=12, keepWithNext=True),
        'section': ParagraphStyle('Section', fontName='TDPBold', fontSize=11, leading=15,
                                 textColor=NAVY, spaceBefore=11, spaceAfter=7, keepWithNext=True),
        'title': ParagraphStyle('Title', fontName='TDPBold', fontSize=38, leading=45,
                               textColor=NAVY, spaceAfter=20),
        'subtitle': ParagraphStyle('Subtitle', fontName='TDPBold', fontSize=19, leading=26,
                                  textColor=TEAL, spaceAfter=20),
        'table': ParagraphStyle('TableBody', fontName='TDPSans', fontSize=7.8, leading=10.8,
                               textColor=NAVY),
        'tablehead': ParagraphStyle('TableHead', fontName='TDPBold', fontSize=7.8, leading=10.8,
                                   textColor=colors.white),
        'code': ParagraphStyle('Code', fontName='TDPMono', fontSize=7.5, leading=10,
                              textColor=NAVY, backColor=PALE, leftIndent=7,
                              rightIndent=7, borderPadding=0, spaceAfter=0, spaceBefore=0),
        'caption': ParagraphStyle('Caption', fontName='TDPSans', fontSize=8, leading=11,
                                 textColor=GREY, spaceAfter=12),
        'toc': ParagraphStyle('TOC', fontName='TDPSans', fontSize=9.3, leading=13,
                             textColor=NAVY, rightIndent=25, spaceBefore=10),
    }
    story = [Spacer(1, 65), Paragraph('solution tdtp', styles['title']),
             Paragraph('Méthodes formelles pour le génie logiciel', styles['subtitle']),
             Paragraph('Système de réservation à capacité limitée', styles['section']),
             Paragraph('Contrats et invariants · Java 17 · Automate · Réseaux de Petri · NuSMV · PRISM', styles['body']),
             Spacer(1, 25), Paragraph('USTHB — Faculté d’informatique — Laboratoire MOVEP', styles['body']),
             Paragraph('Ingénieur 5 en Software Engineering', styles['body']),
             Paragraph('Sujet : Dr MEKAHLIA Fatma Zohra', styles['body']),
             Paragraph('Étudiant : ____________________', styles['body']),
             Spacer(1, 25), Paragraph('4 novembre 2026', styles['body']),
             Paragraph('Douze travaux résolus, code Java et résultats des vérifications exécutées.', styles['body']),
             PageBreak(), Paragraph('Sommaire', styles['section'])]
    toc = TableOfContents()
    toc.levelStyles = [styles['toc']]
    toc.dotsMinLevel = 0
    story.extend([toc, PageBreak()])
    lines = source.splitlines()
    index = next(i for i,line in enumerate(lines) if line.startswith('## '))
    while index < len(lines):
        line = lines[index].strip()
        if not line:
            index += 1
            continue
        if line.startswith('## '):
            if line.startswith('## Annexe'):
                story.append(PageBreak())
            story.append(Paragraph(inline(line[3:]), styles['chapter']))
        elif line.startswith('### '):
            story.append(Paragraph(inline(line[4:]), styles['section']))
        elif line.startswith('```'):
            index += 1
            story.append(Spacer(1, 4))
            while index < len(lines) and not lines[index].startswith('```'):
                # One flowable per visual line allows arbitrarily long code annexes
                # to split cleanly across pages while retaining indentation.
                wrapped = textwrap.wrap(lines[index].expandtabs(4), width=105,
                                        subsequent_indent='    ', replace_whitespace=False,
                                        drop_whitespace=False) or [' ']
                for visual in wrapped:
                    story.append(Preformatted(visual, styles['code']))
                index += 1
            story.append(Spacer(1, 10))
        elif line.startswith('|'):
            rows = []
            while index < len(lines) and lines[index].strip().startswith('|'):
                values = [v.strip() for v in lines[index].strip().strip('|').split('|')]
                if not all(re.fullmatch(r'[:\- ]+', v) for v in values):
                    rows.append(values)
                index += 1
            count = len(rows[0])
            weights = [1]*count
            if count == 3:
                weights = [1, 1.4, 1.5]
            cells = [[Paragraph(inline(cell), styles['tablehead' if r == 0 else 'table'])
                      for cell in row] for r,row in enumerate(rows)]
            table = Table(cells, colWidths=[document.width*w/sum(weights) for w in weights],
                          repeatRows=1, hAlign='LEFT')
            table.setStyle(TableStyle([
                ('BACKGROUND',(0,0),(-1,0),NAVY),
                ('ROWBACKGROUNDS',(0,1),(-1,-1),[PALE,colors.white]),
                ('VALIGN',(0,0),(-1,-1),'TOP'),
                ('LEFTPADDING',(0,0),(-1,-1),6), ('RIGHTPADDING',(0,0),(-1,-1),6),
                ('TOPPADDING',(0,0),(-1,-1),6), ('BOTTOMPADDING',(0,0),(-1,-1),6),
            ]))
            story.extend([Spacer(1,3), table, Spacer(1,9)])
            continue
        elif line.startswith('!['):
            match = re.fullmatch(r'!\[([^\]]+)\]\(([^)]+)\)', line)
            if not match:
                raise ValueError(line)
            path = ROOT/match[2]
            with PILImage.open(path) as picture:
                w,h = picture.size
            scale = min(document.width/w, 365/h)
            story.extend([Spacer(1,5), Image(str(path), width=w*scale, height=h*scale),
                          Paragraph(inline(match[1]), styles['caption'])])
        elif line.startswith('- '):
            story.append(Paragraph('• '+inline(line[2:]), styles['body']))
        else:
            paragraph = [line]
            while index+1 < len(lines) and lines[index+1].strip() and not re.match(
                    r'^(#|```|\||- |!\[|\d+\. )', lines[index+1]):
                index += 1
                paragraph.append(lines[index].strip())
            story.append(Paragraph(inline(' '.join(paragraph)), styles['body']))
        index += 1
    document.multiBuild(story)
    print('Generated:', document.filename)
    print('Editable:', ROOT.parent/'solution-mimobn.md')


if __name__ == '__main__':
    build()

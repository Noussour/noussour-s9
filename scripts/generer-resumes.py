"""Generate separate module revision PDFs from local Markdown.

Run from any directory: python scripts/generer-resumes.py
Requires reportlab, pymupdf and DejaVu or Arial/Consolas fonts.
"""
from __future__ import annotations

import hashlib
import argparse
import importlib.util
import json
import re
import textwrap
from html import escape
from pathlib import Path
from datetime import date

import pymupdf
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageBreak, PageTemplate, Paragraph, Preformatted,
    Spacer, Table, TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parent.parent
MODULES = [
    ('dev-mobile', 'Développement mobile'),
    ('devops', 'DevOps et Cloud Computing'),
    ('embedded', 'Développement de logiciels embarqués'),
    ('game-dev', 'Conception de jeux vidéo'),
    ('iot', 'Internet of Things'),
    ('methodes-formelles', 'Méthodes formelles pour le génie logiciel'),
]
NAVY = colors.HexColor('#193650')
TEAL = colors.HexColor('#087d85')
GREY = colors.HexColor('#536778')
PALE = colors.HexColor('#eef4f8')


def fonts():
    spec = importlib.util.find_spec('matplotlib')
    bundled = Path(spec.origin).parent/'mpl-data/fonts/ttf' if spec else Path('/nonexistent')
    for name, filename, fallback in [
        ('ResumeSans','DejaVuSans.ttf','arial.ttf'),
        ('ResumeBold','DejaVuSans-Bold.ttf','arialbd.ttf'),
        ('ResumeMono','DejaVuSansMono.ttf','consola.ttf'),
    ]:
        choices = [bundled/filename, Path('/usr/share/fonts/truetype/dejavu')/filename,
                   Path('C:/Windows/Fonts')/fallback]
        path = next((p for p in choices if p.is_file()), None)
        if path is None:
            raise FileNotFoundError('Install DejaVu or Arial/Consolas fonts')
        pdfmetrics.registerFont(TTFont(name, str(path)))
    pdfmetrics.registerFontFamily('ResumeSans', normal='ResumeSans', bold='ResumeBold',
                                 italic='ResumeSans', boldItalic='ResumeBold')


def inline(value):
    tokens = []
    def save(html):
        tokens.append(html)
        return f'ZZTOKEN{len(tokens)-1}ZZ'
    value = re.sub(r'`([^`]+)`', lambda m: save(
        '<font name="ResumeMono" size="8">'+escape(m[1])+'</font>'), value)
    value = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', lambda m: save(
        '<link href="'+escape(m[2],quote=True)+'" color="#087d85">'+escape(m[1])+'</link>'), value)
    value = escape(value)
    value = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', value)
    for i,token in enumerate(tokens):
        value = value.replace(f'ZZTOKEN{i}ZZ',token)
    return value


STYLES = {
    'body': ParagraphStyle('Body', fontName='ResumeSans', fontSize=9.4, leading=13.5,
                          textColor=NAVY, spaceAfter=6),
    'chapter': ParagraphStyle('Chapter', fontName='ResumeBold', fontSize=16, leading=21,
                             textColor=TEAL, spaceBefore=14, spaceAfter=11, keepWithNext=True),
    'section': ParagraphStyle('Section', fontName='ResumeBold', fontSize=11, leading=15,
                             textColor=NAVY, spaceBefore=9, spaceAfter=6, keepWithNext=True),
    'title': ParagraphStyle('Title', fontName='ResumeBold', fontSize=38, leading=45,
                           textColor=NAVY, spaceAfter=20),
    'subtitle': ParagraphStyle('Subtitle', fontName='ResumeBold', fontSize=23, leading=31,
                              textColor=TEAL, spaceAfter=20),
    'table': ParagraphStyle('TableBody', fontName='ResumeSans', fontSize=8.1, leading=11.3,
                           textColor=NAVY),
    'tablehead': ParagraphStyle('TableHead', fontName='ResumeBold', fontSize=8.1, leading=11.3,
                               textColor=colors.white),
    'code': ParagraphStyle('Code', fontName='ResumeMono', fontSize=7.7, leading=10.4,
                          textColor=NAVY, backColor=PALE, leftIndent=7, rightIndent=7),
    'toc': ParagraphStyle('TOC', fontName='ResumeSans', fontSize=9.4, leading=14,
                         textColor=NAVY, rightIndent=24, spaceBefore=10),
}


class ResumeDoc(BaseDocTemplate):
    def __init__(self,path,label):
        super().__init__(str(path), pagesize=A4, leftMargin=44, rightMargin=44,
                         topMargin=50, bottomMargin=49, title='resumer — '+label,
                         author='Notes de révision — S9', subject=label)
        self.label = label
        self.counter = 0
        frame=Frame(self.leftMargin,self.bottomMargin,self.width,self.height,
                    leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
        self.addPageTemplates(PageTemplate(id='summary',frames=frame,onPage=self.decorate))

    def beforeDocument(self):
        self.counter=0

    def decorate(self,canvas,doc):
        canvas.saveState()
        canvas.setFillColor(NAVY)
        canvas.rect(0,A4[1]-8,A4[0],8,fill=1,stroke=0)
        canvas.setFont('ResumeSans',7)
        canvas.setFillColor(GREY)
        canvas.drawString(self.leftMargin,A4[1]-29,'USTHB · SOFTWARE ENGINEERING · SEMESTRE 9')
        canvas.drawRightString(A4[0]-self.rightMargin,A4[1]-29,'RÉSUMÉ DE RÉVISION')
        canvas.setStrokeColor(colors.HexColor('#d5e1e9'))
        canvas.line(self.leftMargin,36,A4[0]-self.rightMargin,36)
        canvas.drawString(self.leftMargin,23,self.label)
        canvas.drawRightString(A4[0]-self.rightMargin,23,str(doc.page))
        canvas.restoreState()

    def afterFlowable(self,flowable):
        if isinstance(flowable,Paragraph) and flowable.style.name=='Chapter':
            self.counter+=1
            key=f'section-{self.counter}'
            title=flowable.getPlainText()
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(title,key,level=0,closed=False)
            self.notify('TOCEntry',(0,title,self.page,key))


def paragraphs(lines,document):
    story=[]
    i=0
    while i<len(lines):
        line=lines[i].strip()
        if not line:
            i+=1
            continue
        if line.startswith('## '):
            story.append(Paragraph(inline(line[3:]),STYLES['chapter']))
        elif line.startswith('### '):
            story.append(Paragraph(inline(line[4:]),STYLES['section']))
        elif line.startswith('```'):
            story.append(Spacer(1,4))
            i+=1
            while i<len(lines) and not lines[i].startswith('```'):
                for visual in textwrap.wrap(lines[i].expandtabs(4),width=102,
                        subsequent_indent='    ',replace_whitespace=False,drop_whitespace=False) or [' ']:
                    story.append(Preformatted(visual,STYLES['code']))
                i+=1
            story.append(Spacer(1,10))
        elif line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                cells=[c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r'[:\- ]+',c) for c in cells):
                    rows.append(cells)
                i+=1
            count=len(rows[0])
            assert all(len(r)==count for r in rows),rows
            weights=[1]*count
            if count==3:
                weights=[.85,1.25,1.4]
            table=Table([[Paragraph(inline(c),STYLES['tablehead' if r==0 else 'table'])
                          for c in row] for r,row in enumerate(rows)],
                        colWidths=[document.width*w/sum(weights) for w in weights],
                        repeatRows=1,hAlign='LEFT')
            table.setStyle(TableStyle([
                ('BACKGROUND',(0,0),(-1,0),NAVY),
                ('ROWBACKGROUNDS',(0,1),(-1,-1),[PALE,colors.white]),
                ('VALIGN',(0,0),(-1,-1),'TOP'),
                ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
                ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
            ]))
            story.extend([Spacer(1,3),table,Spacer(1,9)])
            continue
        elif line.startswith('- '):
            story.append(Paragraph('• '+inline(line[2:]),STYLES['body']))
        else:
            text=[line]
            while i+1<len(lines) and lines[i+1].strip() and not re.match(
                    r'^(#|```|\||- |\d+\. )',lines[i+1]):
                i+=1
                text.append(lines[i].strip())
            story.append(Paragraph(inline(' '.join(text)),STYLES['body']))
        i+=1
    return story


def build_module(module,label,revision_date=None):
    path=ROOT/module/'RESUME'
    source=(path/'resumer.md').read_text(encoding='utf-8')
    if revision_date is None:
        manifest=path/'sources.json'
        revision_date=(json.loads(manifest.read_text(encoding='utf-8'))['date']
                       if manifest.exists() else date.today().isoformat())
    edition=date.fromisoformat(revision_date)
    mois=['janvier','février','mars','avril','mai','juin','juillet','août',
          'septembre','octobre','novembre','décembre'][edition.month-1]
    edition_label=f'Mise à jour : {edition.day} {mois} {edition.year}'
    lines=source.splitlines()
    start=next(i for i,line in enumerate(lines) if line.startswith('## '))
    intro=[line for line in lines[1:start] if line.strip()]
    document=ResumeDoc(path/'resumer.pdf',label)
    story=[Spacer(1,60),Paragraph('resumer',STYLES['title']),
           Paragraph(escape(label),STYLES['subtitle']),
           Paragraph('USTHB · Ingénieur 5 · Software Engineering · S9',STYLES['body']),
           Paragraph('Définitions · Comparaisons · Méthodes · Révision active',STYLES['body']),
           Spacer(1,25)]
    story.extend(Paragraph(inline(line),STYLES['body']) for line in intro)
    story.extend([Spacer(1,20),Paragraph(edition_label,STYLES['body']),
                  PageBreak(),Paragraph('Sommaire',STYLES['section'])])
    toc=TableOfContents()
    toc.levelStyles=[STYLES['toc']]
    toc.dotsMinLevel=0
    story.extend([toc,PageBreak()])
    story.extend(paragraphs(lines[start:],document))
    document.multiBuild(story)
    return path/'resumer.pdf'


def sources_manifest(selected_modules=None,revision_date=None):
    inventory=[]
    for module,label in MODULES:
        for folder in ['COURS','TD','TP']:
            candidates=sorted((ROOT/module/folder).glob('*'))
            if module=='methodes-formelles' and folder=='COURS':
                candidates=sorted((ROOT/module/folder).glob('Chapitre-*/cours.md'))
            for path in candidates:
                if not path.is_file() or path.suffix.lower() not in ['.pdf','.txt','.md']:
                    continue
                if path.name.startswith(('resumer','solution-','fiche-revision','README')):
                    continue
                entry={'module':module,'source':path.relative_to(ROOT).as_posix(),
                       'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
                if path.suffix=='.pdf':
                    with pymupdf.open(path) as pdf:
                        entry['pages']=len(pdf)
                inventory.append(entry)
    for relative in ['methodes-formelles/TD_TP_MFGL_Dr Mekahlia.pdf',
                     'methodes-formelles/COURS/resumer.md']:
        path=ROOT/relative
        entry={'module':'methodes-formelles','source':relative,
               'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        if path.suffix=='.pdf':
            with pymupdf.open(path) as pdf:
                entry['pages']=len(pdf)
        inventory.append(entry)
    for module,label in MODULES:
        if selected_modules is not None and module not in selected_modules:
            continue
        pending = ['chapitre 1 : lien Prezi non accessible'] if module=='dev-mobile' else []
        destination=ROOT/module/'RESUME/sources.json'
        manifest_date=revision_date
        if manifest_date is None:
            manifest_date=(json.loads(destination.read_text(encoding='utf-8'))['date']
                           if destination.exists() else date.today().isoformat())
        destination.write_text(json.dumps({'date':manifest_date,
            'module':module, 'pending':pending,
            'documents':[entry for entry in inventory if entry['module']==module]},
            ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description='Generate separate module summaries.')
    parser.add_argument('--modules',nargs='+',choices=[m for m,_ in MODULES],
                        default=[m for m,_ in MODULES])
    parser.add_argument('--date',type=date.fromisoformat,help='Revision date, YYYY-MM-DD')
    args=parser.parse_args()
    revision_date=args.date.isoformat() if args.date else None
    fonts()
    for module,label in MODULES:
        if module not in args.modules:
            continue
        path=build_module(module,label,revision_date)
        with pymupdf.open(path) as pdf:
            print(module,len(pdf),'pages')
    sources_manifest(args.modules,revision_date)
    print('Generated separate summaries in each module RESUME folder.')


if __name__=='__main__':
    main()

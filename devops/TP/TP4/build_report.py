"""Build rapport.pdf from rapport.md and genuine evidence images.

Uses the repository's existing ReportLab formatting helpers.
Dependencies: reportlab, pymupdf, pillow; DejaVu or Arial/Consolas fonts.
"""
from pathlib import Path
from html import escape
import importlib.util
import re

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Image, PageBreak, Paragraph, Spacer
from reportlab.platypus.tableofcontents import TableOfContents

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
spec=importlib.util.spec_from_file_location('summary_format',ROOT/'scripts/generer-resumes.py')
formatting=importlib.util.module_from_spec(spec)
spec.loader.exec_module(formatting)


class LabReport(formatting.ResumeDoc):
    def decorate(self,canvas,doc):
        canvas.saveState()
        canvas.setFillColor(formatting.NAVY)
        canvas.rect(0,A4[1]-8,A4[0],8,fill=1,stroke=0)
        canvas.setFont('ResumeSans',7)
        canvas.setFillColor(formatting.GREY)
        canvas.drawString(self.leftMargin,A4[1]-29,'USTHB · DEVOPS ET CLOUD COMPUTING · TP4')
        canvas.drawRightString(A4[0]-self.rightMargin,A4[1]-29,'RAPPORT D’EXÉCUTION')
        canvas.setStrokeColor(colors.HexColor('#d5e1e9'))
        canvas.line(self.leftMargin,36,A4[0]-self.rightMargin,36)
        canvas.drawString(self.leftMargin,23,'OpenStack / DevStack · Ubuntu 24.04 · Azure')
        canvas.drawRightString(A4[0]-self.rightMargin,23,str(doc.page))
        canvas.restoreState()


def main():
    formatting.fonts()
    source=(BASE/'rapport.md').read_text(encoding='utf-8')
    lines=source.splitlines()
    first=next(i for i,line in enumerate(lines) if line.startswith('## '))
    document=LabReport(BASE/'rapport.pdf','TP4 — OpenStack avec DevStack')
    document.title='TP4 — Installation et vérification OpenStack / DevStack'
    story=[Spacer(1,50),Paragraph('TP4',formatting.STYLES['title']),
           Paragraph('OpenStack avec DevStack',formatting.STYLES['subtitle']),
           Paragraph('Installation, vérification et accès à Horizon',formatting.STYLES['section']),
           Paragraph('USTHB · Ingénieur 5 · Software Engineering · 2026–2027',formatting.STYLES['body']),
           Paragraph('Enseignante : Ameur Imane · Étudiant : ____________________',formatting.STYLES['body']),
           Spacer(1,20)]
    story.extend(formatting.paragraphs(lines[1:first],document))
    story.extend([PageBreak(),Paragraph('Sommaire',formatting.STYLES['section'])])
    toc=TableOfContents();toc.levelStyles=[formatting.STYLES['toc']];toc.dotsMinLevel=0
    story.extend([toc,PageBreak()])
    body='\n'.join(lines[first:])
    for part in re.split(r'(^!\[[^\]]*\]\([^)]+\)\s*$)',body,flags=re.M):
        match=re.fullmatch(r'!\[([^\]]*)\]\(([^)]+)\)\s*',part)
        if not match:
            story.extend(formatting.paragraphs(part.splitlines(),document));continue
        path=BASE/match[2]
        with PILImage.open(path) as image:
            w,h=image.size
        scale=min(document.width/w,350/h)
        story.extend([Spacer(1,6),Image(str(path),width=w*scale,height=h*scale),
                      Paragraph(formatting.inline(match[1]),formatting.STYLES['body'])])
    document.multiBuild(story)
    print('Built',BASE/'rapport.pdf')


if __name__=='__main__':
    main()

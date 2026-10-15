from pathlib import Path
import re
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Preformatted, Flowable
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4

ROOT = Path('/Users/abhitrambadiya/Developer/college/MultiAgent')
SRC = ROOT / 'output/AI-EOS_Research_Report.md'
OUT = ROOT / 'output/pdf/AI-EOS_Research_Report.pdf'
OUT.parent.mkdir(parents=True, exist_ok=True)
FONTDIR = Path('/System/Library/Fonts/Supplemental')
for name, file in [('Helvetica','Arial.ttf'),('Helvetica-Bold','Arial Bold.ttf'),('Helvetica-Oblique','Arial Italic.ttf'),('Helvetica-BoldOblique','Arial Bold Italic.ttf'),('Courier','Courier New.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(FONTDIR / file)))
pdfmetrics.registerFontFamily('Helvetica',normal='Helvetica',bold='Helvetica-Bold',italic='Helvetica-Oblique',boldItalic='Helvetica-BoldOblique')
NAVY, TEAL, INK = map(HexColor, ['#142F45', '#087F8C', '#263746'])
GRAY, PALE, LINE = map(HexColor, ['#647788', '#F0F6F8', '#D8E3E8'])

styles = {
    'body': ParagraphStyle('body', fontName='Helvetica', fontSize=10.1, leading=13.6, textColor=INK, spaceAfter=7),
    'h1': ParagraphStyle('h1', fontName='Helvetica-Bold', fontSize=21, leading=25, textColor=NAVY, spaceAfter=17),
    'title': ParagraphStyle('title', fontName='Helvetica-Bold', fontSize=28, leading=32, textColor=NAVY, spaceAfter=12),
    'h2': ParagraphStyle('h2', fontName='Helvetica', fontSize=15, leading=19, textColor=TEAL, spaceAfter=15),
    'h3': ParagraphStyle('h3', fontName='Helvetica-Bold', fontSize=11.7, leading=15, textColor=TEAL, spaceBefore=8, spaceAfter=7),
    'cell': ParagraphStyle('cell', fontName='Helvetica', fontSize=8.8, leading=11.3, textColor=INK),
    'th': ParagraphStyle('th', fontName='Helvetica-Bold', fontSize=8.8, leading=11.3, textColor=white),
    'bullet': ParagraphStyle('bullet', fontName='Helvetica', fontSize=10.1, leading=13.6, textColor=INK, leftIndent=11, firstLineIndent=-9, spaceAfter=6),
    'code': ParagraphStyle('code', fontName='Courier', fontSize=8.2, leading=11.4, textColor=INK, backColor=PALE, borderPadding=10, spaceAfter=10),
}

def inline(s):
    s = escape(s)
    s = re.sub(r'\[([^\]]+)\]\((https?://[^\s)]+)\)', lambda m: f'<link href="{m[2]}" color="#087F8C"><u>{m[1]}</u></link>', s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'`([^`]+)`', r'<font name="Courier">\1</font>', s)
    return s

class Architecture(Flowable):
    def __init__(self, width):
        Flowable.__init__(self); self.width=width; self.height=286
    def draw(self):
        c=self.canv; w=self.width
        def box(x,y,bw,bh,label,accent=False):
            c.setFillColor(TEAL if accent else PALE); c.setStrokeColor(LINE)
            c.roundRect(x,y,bw,bh,5,fill=1,stroke=not accent)
            c.setFillColor(white if accent else INK); c.setFont('Helvetica-Bold' if accent else 'Helvetica',9.4)
            for i,t in enumerate(label.split('\n')): c.drawCentredString(x+bw/2,y+bh/2+3-(i*11),t)
        def arrow(x,y,xx,yy):
            c.setStrokeColor(GRAY); c.setFillColor(GRAY); c.setLineWidth(.8); c.line(x,y,xx,yy)
            p=c.beginPath(); p.moveTo(xx,yy); p.lineTo(xx-3,yy+5); p.lineTo(xx+3,yy+5); p.close(); c.drawPath(p,fill=1,stroke=0)
        box(w*.2,254,w*.6,30,'Owner request / simulated event',True)
        arrow(w/2,254,w/2,241)
        box(w*.12,207,w*.76,34,'Scope + risk pre-check + safe reuse gateway')
        arrow(w/2,207,w/2,194)
        box(w*.25,164,w*.5,30,'Manager / task planner',True)
        c.setStrokeColor(GRAY); c.line(w/2,164,w/2,153); c.line(w*.12,153,w*.88,153)
        for i,label in enumerate(['Sales','Inventory','Marketing','Research']):
            x=i*w/4+4; bw=w/4-8
            arrow(x+bw/2,153,x+bw/2,140); box(x,111,bw,29,label)
            c.line(x+bw/2,111,x+bw/2,100)
        c.line(w*.12,100,w*.88,100); arrow(w/2,100,w/2,87)
        box(w*.08,53,w*.84,34,'Evidence merge + follow-up + finance + synthesis')
        arrow(w/2,53,w/2,40)
        box(0,5,w,35,'Action policy -> owner approval when required\nSimulated execution -> audit -> KPI follow-up',True)

class NumberedCanvas(canvas.Canvas):
    def __init__(self,*a,**kw): super().__init__(*a,**kw); self.states=[]
    def showPage(self): self.states.append(dict(self.__dict__)); self._startPage()
    def save(self):
        total=len(self.states)
        for state in self.states:
            self.__dict__.update(state)
            self.setFillColor(NAVY); self.setFont('Helvetica-Bold',8)
            self.drawString(43,A4[1]-28,'AI-EOS / RESEARCH & PROJECT DESIGN')
            self.setFillColor(GRAY); self.setFont('Helvetica',8)
            self.drawRightString(A4[0]-43,A4[1]-28,'14 OCTOBER 2026')
            self.setStrokeColor(LINE); self.line(43,39,A4[0]-43,39)
            self.drawString(43,26,'PROPOSED DESIGN  |  SYNTHETIC EXAMPLES  |  NO MEASURED RESULTS')
            self.drawRightString(A4[0]-43,26,f'{self._pageNumber:02d} / {total:02d}')
            super().showPage()
        super().save()

doc=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=43,leftMargin=43,topMargin=56,bottomMargin=53,
                      title='AI-EOS: Multi-Agent Business Workforce - Research Report',author='Research analysis for AI-EOS college project')
story=[]
sections=SRC.read_text().split('<!-- page -->')
for section_idx,section in enumerate(sections):
    if section_idx: story.append(PageBreak())
    lines=section.strip().splitlines(); i=0
    while i < len(lines):
        line=lines[i].strip()
        if not line: i+=1; continue
        if line.startswith('```'):
            code=[]; i+=1
            while i<len(lines) and not lines[i].strip().startswith('```'): code.append(lines[i]); i+=1
            if section_idx==4 and 'Owner request' in '\n'.join(code): story.append(Architecture(doc.width))
            else: story.append(Preformatted('\n'.join(code),styles['code']))
            i+=1; continue
        if line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                row=[x.strip() for x in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?',x.replace(' ','')) for x in row): rows.append(row)
                i+=1
            n=len(rows[0]); ratios={
                2:[.26,.74], 3:[.24,.37,.39],4:[.28,.21,.21,.30]
            }.get(n,[1/n]*n)
            if section_idx==3 and n==4: ratios=[.28,.20,.20,.32]
            if section_idx==10 and n==3: ratios=[.45,.18,.37]
            data=[[Paragraph(inline(x),styles['th' if ri==0 else 'cell']) for x in row] for ri,row in enumerate(rows)]
            table=Table(data,colWidths=[doc.width*x for x in ratios],repeatRows=1,hAlign='LEFT')
            table.setStyle(TableStyle([
                ('BACKGROUND',(0,0),(-1,0),NAVY),('VALIGN',(0,0),(-1,-1),'TOP'),
                ('ROWBACKGROUNDS',(0,1),(-1,-1),[white,PALE]),
                ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
                ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
                ('LINEBELOW',(0,0),(-1,0),.5,NAVY),('LINEBELOW',(0,1),(-1,-1),.3,LINE)
            ])); story.extend([table,Spacer(1,10)]); continue
        if line.startswith('# '):
            story.append(Paragraph(inline(line[2:]),styles['title' if section_idx==0 else 'h1'])); i+=1; continue
        if line.startswith('## '):
            story.append(Paragraph(inline(line[3:]),styles['h2'])); i+=1; continue
        if line.startswith('### '):
            story.append(Paragraph(inline(line[4:]),styles['h3'])); i+=1; continue
        if line.startswith('- '):
            story.append(Paragraph('&#8226; '+inline(line[2:]),styles['bullet'])); i+=1; continue
        if re.match(r'^\d+\. ',line):
            story.append(Paragraph(inline(line),styles['bullet'])); i+=1; continue
        para=[line]; i+=1
        while i<len(lines) and lines[i].strip() and not re.match(r'^(#|\||```|- |\d+\. )',lines[i].strip()):
            para.append(lines[i].strip()); i+=1
        story.append(Paragraph(inline(' '.join(para)),styles['body']))
doc.build(story,canvasmaker=NumberedCanvas)
print(OUT)

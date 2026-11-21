from pathlib import Path
from xml.sax.saxutils import escape
import hashlib
import json
import shutil
import zipfile

from PIL import Image as PILImage
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.utils import ImageReader
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'output' / 'pdf'
TMP = ROOT / 'tmp' / 'pdfs'
OUT.mkdir(parents=True, exist_ok=True)
TMP.mkdir(parents=True, exist_ok=True)
RESULTS = ROOT / 'output' / 'results'
RESULTS.mkdir(parents=True, exist_ok=True)

NAMES = ['01_caesar_encrypt', '02_caesar_decrypt', '03_playfair_encrypt',
         '04_playfair_decrypt', '05_vigenere_encrypt', '06_vigenere_decrypt']
EXPECTED = ['ZDOLG EHFKDU 222231326620',
            'ALGERIA FOOTBALL TEAM IS NOT GOOD NOW',
            'ZIRCECFDPKSW', 'THEWEATHERISFINE',
            'QSEPE VWVOBL 222231326620', 'JX RGXYKGL KL HCGHGEQGW']

# Preserve the actual text files produced by JCrypTool, not reconstructed outputs.
for i, (name, expected) in enumerate(zip(NAMES, EXPECTED), 1):
    src = RESULTS / f'{name}_output.txt'
    if not src.exists():
        src = ROOT / '.tools/jcryptool.app/Contents/MacOS/workspace/temp_data' / f'out{i:03}.txt'
    actual = src.read_text(encoding='utf-8').strip()
    assert actual == expected, (name, actual, expected)
    target = RESULTS / f'{name}_output.txt'
    if src.resolve() != target.resolve():
        shutil.copy2(src, target)

ABC = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
def caesar(text, shift):
    return ''.join(ABC[(ABC.index(c)+shift)%26] if c in ABC else c for c in text)

def vigenere(text, key, direction=1):
    out, rows, i = [], [], 0
    for c in text:
        if c not in ABC:
            out.append(c)
            continue
        k = key[i % len(key)]
        p, n = ABC.index(c), ABC.index(k)
        v = (p + direction*n) % 26
        out.append(ABC[v])
        rows.append([str(i+1), c, k, f'({p} - {n}) mod 26 = {v}', ABC[v]])
        i += 1
    return ''.join(out), rows

def playfair(text, key, direction=1):
    grid = ''.join(dict.fromkeys((key+ABC).replace('J', 'I')))
    clean = ''.join(c for c in text if c in ABC).replace('J', 'I')
    pairs = []
    i = 0
    while i < len(clean):
        a = clean[i]
        b = clean[i+1] if i+1 < len(clean) else 'X'
        if direction == 1 and (i+1 == len(clean) or a == b):
            pairs.append(a+'X'); i += 1
        else:
            pairs.append(a+b); i += 2
    result = ''
    for a, b in pairs:
        r, c = divmod(grid.index(a), 5)
        u, v = divmod(grid.index(b), 5)
        if r == u:
            result += grid[r*5+(c+direction)%5] + grid[u*5+(v+direction)%5]
        elif c == v:
            result += grid[((r+direction)%5)*5+c] + grid[((u+direction)%5)*5+v]
        else:
            result += grid[r*5+v] + grid[u*5+c]
    return result

PERSONAL = 'WALID BECHAR 222231326620'
CIPHER = 'BR EYRLCAY CF UUAUYYDYQ'
assert caesar(PERSONAL, 3) == EXPECTED[0]
assert caesar(EXPECTED[0], -3) == PERSONAL
assert caesar('DOJHULD IRRWEDOO WHDP LV QRW JRRG QRZ', -3) == EXPECTED[1]
assert playfair('WALIDBECHAR', 'KING') == EXPECTED[2]
assert playfair(EXPECTED[2], 'KING', -1) == 'WALIDBECHARX'
assert playfair('OMDXFNOMFQHUDLEK', 'SUN', -1) == EXPECTED[3]
assert playfair(EXPECTED[3], 'SUN') == 'OMDXFNOMFQHUDLEK'
assert vigenere(PERSONAL, 'USTHB')[0] == EXPECTED[4]
assert vigenere(EXPECTED[4], 'USTHB', -1)[0] == PERSONAL
assert vigenere(CIPHER, 'SUN', -1)[0] == EXPECTED[5]
assert vigenere(EXPECTED[5], 'SUN')[0] == CIPHER

# Cropping removes empty workspace areas. It does not alter any UI text or result.
for name in NAMES:
    for kind in ['input', 'settings', 'output']:
        im = PILImage.open(ROOT / 'screenshots' / f'{name}_{kind}.png')
        if kind != 'settings':
            im = im.crop((650, 95, 1960, 215))
        else:
            if name == '05_vigenere_encrypt':
                im = im.crop((880, 136, 2576, 1432))
            im = im.crop((0, 0, im.width, 925 if 'caesar' in name else 885))
        im.save(TMP / f'{name}_{kind}.png')

W, H = A4
M = 47
CW = W-2*M
PDF = OUT / 'TP1_Walid_BECHAR_Report.pdf'
c = canvas.Canvas(str(PDF), pagesize=A4)
c.setTitle('Practical Lab 1 Classical Ciphers - Walid BECHAR')
c.setAuthor('Walid BECHAR')
c.setSubject('Caesar, Playfair and Vigenere with JCrypTool screenshots and manual verification')
body = ParagraphStyle('Body', fontName='Helvetica', fontSize=9.8, leading=13.1, textColor=colors.black)
small = ParagraphStyle('Small', parent=body, fontSize=8.2, leading=10.5)
caption_style = ParagraphStyle('Caption', parent=small, textColor=colors.HexColor('#444444'))
heading = ParagraphStyle('Heading', parent=body, fontName='Helvetica-Bold', fontSize=15, leading=19)
subheading = ParagraphStyle('Subheading', parent=body, fontName='Helvetica-Bold', fontSize=10.8, leading=14)
code_style = ParagraphStyle('Code', parent=body, fontName='Courier', fontSize=9.4, leading=12.6)
page, y = 0, H-M
page_bottoms = []

def para(text, style=body, after=7, x=M, width=CW):
    global y
    p = Paragraph(text, style)
    _, height = p.wrap(width, H)
    p.drawOn(c, x, y-height)
    y -= height+after

def code(lines, after=7):
    para('<br/>'.join(escape(line).replace(' ', '&nbsp;') for line in lines), code_style, after)

def table(data, widths=None, fontsize=8.6, rowpad=4, x=M, header=True):
    global y
    data = [[Paragraph(escape(str(v)), ParagraphStyle('Cell', parent=body,
                 fontName='Helvetica-Bold' if header and i == 0 else 'Helvetica',
                 fontSize=fontsize, leading=fontsize+2)) for v in row] for i,row in enumerate(data)]
    t = Table(data, colWidths=widths, hAlign='LEFT')
    t.setStyle(TableStyle([
        ('GRID',(0,0),(-1,-1),0.45,colors.HexColor('#D9D9D9')),
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E8EDF2') if header else colors.white),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),
        ('TOPPADDING',(0,0),(-1,-1),rowpad),('BOTTOMPADDING',(0,0),(-1,-1),rowpad)
    ]))
    _, height = t.wrap(CW,H)
    t.drawOn(c,x,y-height)
    y -= height+9
    return height

def footer():
    page_bottoms.append(round(y, 1))
    assert y >= 43, (page, y)
    c.setFont('Helvetica',8)
    c.setFillColor(colors.HexColor('#666666'))
    c.drawString(M, 27, 'Securite de Logiciel  |  Practical Lab 1  |  Walid BECHAR')
    c.drawRightString(W-M,27,f'{page} / 8')
    c.setFillColor(colors.black)

def new_page(title=None):
    global y, page
    if page:
        footer(); c.showPage()
    page += 1
    y=H-M
    if page>1:
        c.setFont('Helvetica',8)
        c.setFillColor(colors.HexColor('#666666'))
        c.drawString(M,H-26,'USTHB  |  Classical cryptography')
        c.setFillColor(colors.black)
    if title:
        para(title,heading,9)

def shot(name,kind,caption):
    global y
    path=TMP / f'{name}_{kind}.png'
    im=PILImage.open(path)
    width=CW if kind!='settings' else CW*0.93
    height=width*im.height/im.width
    x=M+(CW-width)/2
    c.drawImage(ImageReader(im),x,y-height,width,height,mask='auto')
    c.setStrokeColor(colors.HexColor('#D9D9D9'))
    c.rect(x,y-height,width,height,stroke=1,fill=0)
    y-=height+3
    para(caption,caption_style,6)

def evidence(name,idx):
    para('JCrypTool results',subheading,4)
    shot(name,'input',f'Figure {idx}. Input text in the JCrypTool editor.')
    shot(name,'settings',f'Figure {idx+1}. Operation, alphabet and key.')
    shot(name,'output',f'Figure {idx+2}. JCrypTool output.')

new_page()
para('University of Science and Technology Houari Boumediene',subheading,3)
para('College of Informatique<br/>Securite de Logiciel',body,23)
para('Practical Lab 1',ParagraphStyle('Title',parent=heading,fontSize=26,leading=31),4)
para('Caesar Playfair and Vigenere Ciphers',heading,20)
para('<b>Student:</b> Walid BECHAR<br/><b>Student ID:</b> 222231326620',body,18)
para('Objective',subheading,6)
para('Encrypt and decrypt messages using Caesar, Playfair and Vigenere, then check the results manually.')
para('Software and working conventions',subheading,6)
para('We used <b>JCrypTool</b> because we are working on macOS.')
para('Caesar and Vigenere use A-Z with A = 0 through Z = 25. Spaces and ID digits remain unchanged and do not advance the Vigenere key. Playfair omits J, removes spaces and uses X as padding.')
para('Results overview',subheading,6)
table([
    ['Exercise','Key','Verified output'],
    ['Caesar encryption','3',EXPECTED[0]],
    ['Caesar decryption','3',EXPECTED[1]],
    ['Playfair encryption','KING',EXPECTED[2]],
    ['Playfair decryption','SUN','THE WEATHER IS FINE'],
    ['Vigenere encryption','USTHB',EXPECTED[4]],
    ['Vigenere decryption','SUN',EXPECTED[5]],
], [115,47,CW-162],fontsize=9,rowpad=6)
para('The supplied Vigenere ciphertext does not produce readable text with key SUN; the calculation is shown in Section 6.',body,0)

new_page('1 Caesar encryption with key 3')
para('Caesar replaces every letter with the letter three positions later in the alphabet. The operation wraps around after Z. Encryption is defined by <b>C = (P + 3) mod 26</b>.')
code(['Plaintext:  WALID BECHAR 222231326620',
      'Ciphertext: ZDOLG EHFKDU 222231326620'])
table([
    ['Letter']+list('WALIDBECHAR'),
    ['P']+[22,0,11,8,3,1,4,2,7,0,17],
    ['(P+3) mod 26']+[25,3,14,11,6,4,7,5,10,3,20],
    ['Output']+list('ZDOLGEHFKDU')
],[83]+[(CW-83)/11]*11,fontsize=8,rowpad=3)
para('Example: W = 22, so (22 + 3) mod 26 = 25 = Z. In JCrypTool, key character <b>D</b> corresponds to shift <b>3</b> when A represents shift 0.')
evidence(NAMES[0],1)

new_page('2 Caesar decryption with key 3')
para('Move each letter three positions backward using <b>P = (C - 3) mod 26</b>.')
code(['Ciphertext: DOJHULD IRRWEDOO WHDP LV QRW JRRG QRZ',
      'Plaintext:  ALGERIA FOOTBALL TEAM IS NOT GOOD NOW'])
table([
    ['Cipher word','DOJHULD','IRRWEDOO','WHDP','LV','QRW','JRRG','QRZ'],
    ['Plain word','ALGERIA','FOOTBALL','TEAM','IS','NOT','GOOD','NOW'],
],[68,76,85,63,40,50,62,CW-444],fontsize=8.3,rowpad=5)
para('Example: D = 3 gives (3 - 3) mod 26 = 0 = A. Applying the same subtraction to DOJHULD gives ALGERIA.')
evidence(NAMES[1],4)

new_page('3 Playfair encryption with key KING')
para('Build the square with KING followed by the unused letters, omitting J. Remove the space from the name and append X to pair its 11 letters.')
code(['Prepared input: WALIDBECHARX', 'Pairs:          WA LI DB EC HA RX',
      'Ciphertext:     ZIRCECFDPKSW'])
top=y
table([list(s) for s in ['KINGA','BCDEF','HLMOP','QRSTU','VWXYZ']],
      [26]*5,fontsize=11,rowpad=4,header=False)
left_bottom=y
y=top
table([['Input','Rule','Output'],['WA','Rectangle','ZI'],['LI','Column','RC'],
       ['DB','Row','EC'],['EC','Row','FD'],['HA','Rectangle','PK'],['RX','Rectangle','SW']],
      [50,105,58],fontsize=8.3,rowpad=2,x=M+168)
y=min(y,left_bottom)
para('In a shared row, move right; in a shared column, move down. Otherwise, each letter keeps its row and takes the other letter\'s column. Thus WA becomes ZI. Decrypting the result recovers WALIDBECHARX; the final X is the known padding.',after=5)
evidence(NAMES[2],7)

new_page('4 Playfair decryption with key SUN')
para('Build the key square from SUN and the unused letters. Decrypt pairs by moving left in a shared row or up in a shared column. The rectangle rule is unchanged.')
code(['Ciphertext: OMDXFNOMFQHUDLEK',
      'Plaintext:  THEWEATHERISFINE',
      'Readable:   THE WEATHER IS FINE'])
top=y
table([list(s) for s in ['SUNAB','CDEFG','HIKLM','OPQRT','VWXYZ']],
      [26]*5,fontsize=11,rowpad=4,header=False)
left_bottom=y
y=top
table([['Input','Rule','Output'],['OM','Rectangle','TH'],['DX','Rectangle','EW'],
       ['FN','Rectangle','EA'],['OM','Rectangle','TH'],['FQ','Rectangle','ER'],
       ['HU','Rectangle','IS'],['DL','Rectangle','FI'],['EK','Column','NE']],
      [50,105,58],fontsize=8.3,rowpad=1.4,x=M+168)
y=min(y,left_bottom)
para('Examples: OM becomes TH by the rectangle rule. EK shares column 3, so moving up gives NE.',after=5)
evidence(NAMES[3],10)

new_page('5 Vigenere encryption with key USTHB')
para('Vigenere applies a different shift at each letter according to a repeated keyword. With A = 0 through Z = 25, use <b>C<sub>i</sub> = (P<sub>i</sub> + K<sub>i</sub>) mod 26</b>. The keyword continues across word boundaries.')
code(['Plaintext:  WALID BECHAR 222231326620',
      'Key stream: USTHB USTHBU',
      'Ciphertext: QSEPE VWVOBL 222231326620'])
table([
    ['Plaintext']+list('WALIDBECHAR'),
    ['Key']+list('USTHBUSTHBU'),
    ['P']+[22,0,11,8,3,1,4,2,7,0,17],
    ['K']+[20,18,19,7,1,20,18,19,7,1,20],
    ['(P+K) mod 26']+[16,18,4,15,4,21,22,21,14,1,11],
    ['Output']+list('QSEPEVWVOBL')
],[83]+[(CW-83)/11]*11,fontsize=8,rowpad=2.3)
para('Example: W with key U gives (22 + 20) mod 26 = 16 = Q. The key repeats across the 11 letters.',after=5)
evidence(NAMES[4],13)

new_page('6 Vigenere decryption with key SUN')
para('Apply <b>P<sub>i</sub> = (C<sub>i</sub> - K<sub>i</sub>) mod 26</b> to the exact supplied ciphertext. Repeat SUN continuously over the letters, ignoring spaces when advancing the key.')
code(['Ciphertext: BR EYRLCAY CF UUAUYYDYQ',
      'Key stream: SU NSUNSUN SU NSUNSUNSU',
      'Output:     JX RGXYKGL KL HCGHGEQGW'])
_, rows=vigenere(CIPHER,'SUN',-1)
top=y
widths=[19,22,22,142,24]
table([['i','C','K','Subtraction mod 26','P']]+rows[:10],widths,fontsize=7.4,rowpad=1.5)
left_bottom=y
y=top
table([['i','C','K','Subtraction mod 26','P']]+rows[10:],widths,fontsize=7.4,rowpad=1.5,x=M+CW-229)
y=min(y,left_bottom)
para('Example: B - S = 1 - 18 = -17 = 9 mod 26 = J. JCrypTool confirms the result, but it is unreadable. The supplied ciphertext or key needs checking.',after=5)
evidence(NAMES[5],16)

new_page('7 Discussion and conclusion')
para('Comparison of the three ciphers',subheading,6)
table([
    ['Cipher','Unit processed','Role of the key'],
    ['Caesar','One letter','One fixed shift for all letters.'],
    ['Playfair','Two letters','A keyword determines a 5 by 5 substitution square.'],
    ['Vigenere','One letter','A repeated keyword determines a sequence of shifts.'],
],[83,111,CW-194],fontsize=9.5,rowpad=7)
para('Verification',subheading,6)
para('All six JCrypTool outputs match the manual calculations. Decrypting the personalized Caesar and Vigenere results recovers the original name and ID. Playfair recovers WALIDBECHARX, including its padding.')
para('Re-encrypting THEWEATHERISFINE with SUN gives OMDXFNOMFQHUDLEK. Re-encrypting the final Vigenere output with SUN also recovers the supplied ciphertext, confirming the calculation despite the unreadable plaintext.')
para('Conclusion',subheading,6)
para('This lab demonstrated three methods: a fixed shift with Caesar, letter-pair substitution with Playfair, and repeated keyword shifts with Vigenere. Manual calculations agreed with JCrypTool. The final Vigenere example requires checking because its supplied key and ciphertext do not produce readable text.')
para('References',subheading,6)
para('USTHB, Securite de Logiciel, Practical Lab 1.<br/><link href="https://www.cryptool.org/en/jct/">CrypTool project - JCrypTool</link>.',small,0)

footer()
c.save()
reader=PdfReader(str(PDF))
assert len(reader.pages)==8
text='\n'.join(p.extract_text() for p in reader.pages)
for expected in EXPECTED:
    assert expected in text, expected
assert '222231326620' in text
(TMP/'extracted_report.txt').write_text(text,encoding='utf-8')

manifest={
    'student':'Walid BECHAR','student_id':'222231326620',
    'software':'JCrypTool 1.0.9.1 weekly 20230901 on macOS',
    'software_download':'https://github.com/jcryptool/core/releases/download/Weekly-1.0.9.1-20230901/JCrypTool-Weekly-1.0.9.1-20230901-macOS-64bit.tar.gz',
    'note':'The assignment names CrypTool 1; these runs use the official JCrypTool edition.',
    'outputs':dict(zip(NAMES,EXPECTED)),
    'screenshots':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'screenshots').glob('*.png'))}
}
(ROOT/'output/evidence_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
ZIP=ROOT/'output/TP1_Walid_BECHAR_Evidence.zip'
with zipfile.ZipFile(ZIP,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for folder in ['screenshots','inputs','output/results']:
        for path in sorted((ROOT/folder).glob('*')):
            if path.is_file():
                z.write(path,str(path.relative_to(ROOT)))
    z.write(ROOT/'output/evidence_manifest.json','evidence_manifest.json')
    z.writestr('README.txt','TP1 - Walid BECHAR - 222231326620\n\nThe screenshots are original JCrypTool captures. The report crops relevant regions for readability.\nThe six input files and six actual JCrypTool output files are included.\n\nSoftware: JCrypTool 1.0.9.1 weekly build 20230901 on macOS. This is the official cross-platform CrypTool edition, not Windows CrypTool 1.\n\nVigenere decryption with SUN returns JX RGXYKGL KL HCGHGEQGW for the confirmed ciphertext BR EYRLCAY CF UUAUYYDYQ. This mismatch is documented in the report.\n')
print(json.dumps({'pdf':str(PDF),'pages':len(reader.pages),'bottoms':page_bottoms,'evidence':str(ZIP),'screenshots':len(manifest['screenshots'])},indent=2))

import io
import docx
from docx import Document
from docx.shared import RGBColor
from docx.oxml.ns import qn

def create_word_from_md(translated_lines):
    doc = Document()
    doc.styles['Normal'].font.name = '宋体'
    doc.styles['Normal']._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

    for line in translated_lines:
        line = line.strip()
        if not line: continue
        if line.startswith('# '): doc.add_heading(line[2:], level=1)
        elif line.startswith('## '): doc.add_heading(line[3:], level=2)
        elif line.startswith('### '): doc.add_heading(line[4:], level=3)
        elif line.startswith('- ') or line.startswith('* '): doc.add_paragraph(line[2:], style='List Bullet')
        elif line.startswith('|') or line.startswith('!['):
            p = doc.add_paragraph(line)
            p.runs[0].font.color.rgb = RGBColor(128, 128, 128)
        else: doc.add_paragraph(line)
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

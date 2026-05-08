import io
import docx  # 必须导入 docx 才能使用 docx.shared
from docx import Document
from docx.shared import Pt, RGBColor # 直接从共享模块导入 RGBColor
from docx.oxml.ns import qn

def create_word_from_md(translated_lines):
    """
    将翻译后的 Markdown 行列表转换为 Word 文档字节流
    """
    doc = Document()
    
    # 设置全局中文字体支持
    doc.styles['Normal'].font.name = '宋体'
    doc.styles['Normal']._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

    for line in translated_lines:
        line = line.strip()
        if not line:
            continue
            
        # 处理 Markdown 标题
        if line.startswith('# '):
            doc.add_heading(line[2:], level=1)
        elif line.startswith('## '):
            doc.add_heading(line[3:], level=2)
        elif line.startswith('### '):
            doc.add_heading(line[4:], level=3)
        # 处理列表项
        elif line.startswith('- ') or line.startswith('* '):
            doc.add_paragraph(line[2:], style='List Bullet')
        # 处理表格分隔符和图片占位符 (使用修正后的 RGBColor 导入)
        elif line.startswith('|') or line.startswith('!['):
            p = doc.add_paragraph(line)
            # 修正：直接使用导入的 RGBColor
            p.runs[0].font.color.rgb = RGBColor(128, 128, 128) 
        else:
            doc.add_paragraph(line)

    # 保存到内存
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

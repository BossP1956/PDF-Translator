import pypandoc
import os
import re

def clean_latex_math(md_text):
    """
    针对 MinerU OCR 的常见残缺语法进行洗白，防止 Pandoc 渲染崩溃
    """
    # 1. 修复过时的 \bf -> \mathbf
    md_text = re.sub(r'\{\\bf\s+(.*?)\}', r'\\mathbf{\1}', md_text)
    md_text = md_text.replace(r'\bf ', r'\mathbf ')

    # 2. 修复 MinerU 最爱犯的括号转义错误 (如 \left\\ 或 \left_ )
    replacements = {
        r'\left\\': r'\left[',
        r'\right\\': r'\right]',
        r'\left_': r'\left[',
        r'\right_': r'\right]',
        r'\left\left': r'\left',
        r'\right\right': r'\right',
        r'\left^': r'^'
    }
    for old, new in replacements.items():
        md_text = md_text.replace(old, new)

    # 3. 修复矩阵对齐中的多余空格 (Pandoc 遇到 {c c c} 会报错 "unexpected c")
    def fix_array_align(match):
        align_str = match.group(1).replace(' ', '')
        return f'{{array}}{{{align_str}}}'
    md_text = re.sub(r'\{array\}\{(.*?)\}', fix_array_align, md_text)

    # 4. 清理 LaTeX 公式自带的编号标签 (如 \tag{Eq.21})
    # Word 本身有公式管理，带这些标签 Pandoc 会渲染失败
    md_text = re.sub(r'\\tag\s*\{.*?\}', '', md_text)
    md_text = re.sub(r'\(Eq\..*?\)', '', md_text)

    return md_text

def generate_word(md_path, output_docx_path, working_dir):
    try:
        pypandoc.get_pandoc_version()
    except OSError:
        pypandoc.download_pandoc()

    # 1. 洗白 Markdown 中的 LaTeX 语法
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    sanitized_content = clean_latex_math(content)
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(sanitized_content)

    # 2. 调用 Pandoc 转换为 Word
    pypandoc.convert_file(
        md_path, 
        'docx', 
        outputfile=output_docx_path,
        extra_args=[
            f'--resource-path={working_dir}',
            '--from=markdown+tex_math_dollars+raw_tex', 
            '--mathml' # 关键：输出 Word 原生公式
        ]
    )
    
    with open(output_docx_path, 'rb') as f:
        docx_bytes = f.read()
    return docx_bytes

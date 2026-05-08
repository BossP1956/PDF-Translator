import pypandoc
import os
import re

def clean_latex_math(md_text):
    """
    LaTeX 语法终极洗白，解决所有 Pandoc [WARNING]。
    """
    # 1. 修复过时的 \bf -> \mathbf
    md_text = re.sub(r'\{\\bf\s+(.*?)\}', r'\\mathbf{\1}', md_text)
    md_text = md_text.replace(r'\bf ', r'\mathbf ')

    # 2. 强制修复配对符号: \left\\ -> \left[
    md_text = md_text.replace(r'\left\\', r'\left[').replace(r'\right\\', r'\right]')
    md_text = md_text.replace(r'\left\left[', r'\left[').replace(r'\right\right]', r'\right]')
    
    # 3. 修复对齐语法: {c c c} -> {ccc}
    def fix_array_align(match):
        align = match.group(1).replace(' ', '')
        return f'{{array}}{{{align}}}'
    md_text = re.sub(r'\{array\}\{(.*?)\}', fix_array_align, md_text)

    # 4. 移除会卡死 Word 渲染的 \tag
    md_text = re.sub(r'\\tag\{.*?\}', '', md_text)
    
    # 5. 修复非法连字符
    md_text = md_text.replace(r'\left.', r'\left[').replace(r'\right.', r'\right]')
    
    return md_text

def generate_word(md_path, output_docx_path, working_dir):
    try:
        pypandoc.get_pandoc_version()
    except OSError:
        pypandoc.download_pandoc()

    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 执行洗白
    cleaned = clean_latex_math(content)
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(cleaned)

    # Pandoc 深度转换
    pypandoc.convert_file(
        md_path, 
        'docx', 
        outputfile=output_docx_path,
        extra_args=[
            f'--resource-path={working_dir}',
            '--from=markdown+tex_math_dollars+raw_tex', 
            '--mathml',
            '--standalone'
        ]
    )
    
    with open(output_docx_path, 'rb') as f:
        return f.read()

import pypandoc
import os
import re

def clean_latex_math(md_text):
    """
    在交给 Pandoc 之前，对还原回来的 LaTeX 进行终极清洗。
    解决 MinerU 常见的识别瑕疵。
    """
    # 1. 修复过时的 \bf -> \mathbf{...}
    md_text = re.sub(r'\{\\bf\s+(.*?)\}', r'\\mathbf{\1}', md_text)
    md_text = md_text.replace(r'\bf ', r'\mathbf ')

    # 2. 彻底解决 \left\\ 和 \right\\ 问题 (MinerU 识别最严重的瑕疵)
    md_text = md_text.replace(r'\left\\', r'\left[').replace(r'\right\\', r'\right]')
    md_text = md_text.replace(r'\left\left[', r'\left[').replace(r'\right\right]', r'\right]')

    # 3. 修复矩阵对齐标识中的空格，解决 unexpected "c" 错误
    def fix_array_align(match):
        align_str = match.group(1).replace(' ', '')
        return f'{{array}}{{{align_str}}}'
    md_text = re.sub(r'\{array\}\{(.*?)\}', fix_array_align, md_text)

    # 4. 移除会干扰 Word 转换的内部 \tag{...}
    md_text = re.sub(r'\\tag\{.*?\}', '', md_text)

    # 5. 修复由于翻译或识别导致的非法符号连写
    md_text = md_text.replace(r'\left.', r'\left[').replace(r'\right.', r'\right]')
    
    return md_text

def generate_word(md_path, output_docx_path, working_dir):
    try:
        pypandoc.get_pandoc_version()
    except OSError:
        pypandoc.download_pandoc()

    # 读取并执行终极清洗
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 执行清洗
    sanitized_content = clean_latex_math(content)
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(sanitized_content)

    # Pandoc 转换
    # 增加 --standalone 参数确保文档结构完整
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
        docx_bytes = f.read()
    return docx_bytes

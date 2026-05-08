import pypandoc
import os
import re

def clean_latex_math(md_text):
    """
    工业级 LaTeX 洗白，解决 MinerU 识别的所有疑难杂症。
    """
    # 1. 修复 \bf -> \mathbf
    md_text = re.sub(r'\{\\bf\s+(.*?)\}', r'\\mathbf{\1}', md_text)
    md_text = md_text.replace(r'\bf ', r'\mathbf ')

    # 2. 核心：修复破碎的 \left 和 \right
    md_text = md_text.replace(r'\left\\', r'\left[').replace(r'\right\\', r'\right]')
    # 修复 OCR 常见的双重括号
    md_text = md_text.replace(r'\left\left[', r'\left[').replace(r'\right\right]', r'\right]')
    
    # 3. 修复矩阵对齐空格
    def fix_array(match):
        return f'{{array}}{{{match.group(1).replace(" ", "")}}}'
    md_text = re.sub(r'\{array\}\{(.*?)\}', fix_array, md_text)

    # 4. 移除 \tag，防止 Word 公式溢出
    md_text = re.sub(r'\\tag\{.*?\}', '', md_text)
    
    # 5. 修复不合法的连写
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

    # Pandoc 转换（开启所有公式引擎支持）
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

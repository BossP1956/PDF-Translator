import pypandoc
import os
import re

def clean_latex_math(md_text):
    """
    对 MinerU 生成的非标准 LaTeX 语法进行暴力纠错，防止 Pandoc 渲染崩溃。
    完全基于后台报错日志量身定制。
    """
    # 1. 修复过时的 \bf 指令 -> \mathbf
    md_text = re.sub(r'\{\\bf\s+(.*?)\}', r'\\mathbf{\1}', md_text)
    md_text = md_text.replace(r'\bf ', r'\mathbf ')

    # 2. 修复 MinerU 最常见的转义错误 \left\\ 和 \right\\
    md_text = md_text.replace(r'\left\\', r'\left[')
    md_text = md_text.replace(r'\right\\', r'\right]')
    
    # 3. 修复重复的 \left\left[ 错误
    md_text = md_text.replace(r'\left\left', r'\left')
    md_text = md_text.replace(r'\right\right', r'\right')

    # 4. 修复漏掉括号的上下标情况： \left_ {N} -> \left[ _{N}
    md_text = re.sub(r'\\left\s*\_', r'\\left[_', md_text)
    md_text = re.sub(r'\\left\s*\^', r'\\left[^', md_text)
    md_text = re.sub(r'\\right\s*\_', r'\\right]_', md_text)
    md_text = re.sub(r'\\right\s*\^', r'\\right]^', md_text)

    # 5. 修复矩阵对齐中多余的空格 {c c c} -> {ccc}
    def fix_array_align(match):
        align_str = match.group(1).replace(' ', '')
        return f'{{array}}{{{align_str}}}'
    md_text = re.sub(r'\{array\}\{(.*?)\}', fix_array_align, md_text)

    # 6. 移除 \tag{...} 指令 (Word的OMML原生公式不支持内嵌标签)
    md_text = re.sub(r'\\tag\s*\{.*?\}', '', md_text)

    return md_text

def generate_word(md_path, output_docx_path, working_dir):
    try:
        pypandoc.get_pandoc_version()
    except OSError:
        pypandoc.download_pandoc()

    # 1. 读取并洗白公式语法
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    sanitized_content = clean_latex_math(content)
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(sanitized_content)

    # 2. 调用 Pandoc 转换为 Word (强制使用 MathML 引擎)
    pypandoc.convert_file(
        md_path, 
        'docx', 
        outputfile=output_docx_path,
        extra_args=[
            f'--resource-path={working_dir}',
            '--from=markdown+tex_math_dollars+raw_tex', 
            '--mathml' 
        ]
    )
    
    with open(output_docx_path, 'rb') as f:
        docx_bytes = f.read()
    return docx_bytes

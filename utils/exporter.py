import pypandoc
import os
import re

def clean_latex_math(md_text):
    """
    针对 Pandoc 转换警告，自动修复 MinerU 生成的非标准 LaTeX 语法。
    """
    # 1. 修复过时的 \bf 指令 -> \mathbf{...}
    # 匹配 {\bf text}
    md_text = re.sub(r'\{\\bf\s+(.*?)\}', r'\\mathbf{\1}', md_text)
    # 匹配单独的 \bf 
    md_text = md_text.replace(r'\bf ', r'\mathbf ')

    # 2. 修复错误的转义 \left\\ 或 \right\\ -> \left[ / \right]
    md_text = md_text.replace(r'\left\\', r'\left[').replace(r'\right\\', r'\right]')

    # 3. 修复矩阵对齐中多余的空格，防止 Pandoc 报 unexpected "c"
    # 将 {c c c} 转换为 {ccc}
    def fix_array_align(match):
        align_str = match.group(1).replace(' ', '')
        return f'{{array}}{{{align_str}}}'
    md_text = re.sub(r'\{array\}\{(.*?)\}', fix_array_align, md_text)

    # 4. 移除 \tag{...} 指令
    # Word 的公式转换器不支持嵌入式 \tag，会导致整个公式渲染失败
    md_text = re.sub(r'\\tag\{.*?\}', '', md_text)

    # 5. 修复不合法的连字符 (如 \left^)
    md_text = md_text.replace(r'\left^', r'^')
    
    # 6. 修复大括号不匹配的常见 OCR 错误 (尝试闭合未闭合的 \left)
    # 此处为简单逻辑，主要处理 \left. 缺失配对的情况
    md_text = md_text.replace(r'\left.', r'\left[').replace(r'\right.', r'\right]')

    return md_text

def generate_word(md_path, output_docx_path, working_dir):
    """
    调用 Pandoc 将清洗后的 Markdown 转换为 Word。
    """
    try:
        pypandoc.get_pandoc_version()
    except OSError:
        pypandoc.download_pandoc()

    # 1. 读取并清洗公式
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    sanitized_content = clean_latex_math(content)
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(sanitized_content)

    # 2. 转换文件
    # 使用 --mathml 参数能显著提高公式在 Word 中的兼容性
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

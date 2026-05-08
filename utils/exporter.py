import pypandoc
import os
import re

def clean_latex_math(md_text):
    """
    对 MinerU 输出的不标准 LaTeX 语法进行工业级洗白，
    防止 Pandoc 渲染成乱码或报错崩溃。
    """
    # 1. 修复过时的 \bf -> \mathbf{...}
    md_text = re.sub(r'\{\\bf\s+(.*?)\}', r'\\mathbf{\1}', md_text)
    md_text = md_text.replace(r'\bf ', r'\mathbf ')

    # 2. 彻底解决 MinerU 最常见的转义崩溃: \left\\ 和 \right\\
    md_text = md_text.replace(r'\left\\', r'\left[').replace(r'\right\\', r'\right]')
    md_text = md_text.replace(r'\left\left[', r'\left[').replace(r'\right\right]', r'\right]')

    # 3. 修复矩阵对齐中的空格 {c c c} -> {ccc}，解决 unexpected "c" 错误
    def fix_array_align(match):
        align_str = match.group(1).replace(' ', '')
        return f'{{array}}{{{align_str}}}'
    md_text = re.sub(r'\{array\}\{(.*?)\}', fix_array_align, md_text)

    # 4. 移除 \tag{...} (Word 的原生数学对象不支持硬编码的 \tag，会导致整个公式不显示)
    md_text = re.sub(r'\\tag\{.*?\}', '', md_text)

    # 5. 修复由于翻译或识别导致的非法连字符
    md_text = md_text.replace(r'\left^', r'^')
    md_text = md_text.replace(r'\left.', r'\left[').replace(r'\right.', r'\right]')
    
    return md_text

def generate_word(md_path, output_docx_path, working_dir):
    try:
        pypandoc.get_pandoc_version()
    except OSError:
        pypandoc.download_pandoc()

    # 读取 -> 洗白公式语法 -> 写回
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    sanitized_content = clean_latex_math(content)
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(sanitized_content)

    # 终极转换：包含独立模式、公式支持、本地图片读取
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

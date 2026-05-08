import pypandoc
import os

def generate_word(md_file_path, output_docx_path, working_dir):
    """
    使用 Pandoc 将 Markdown 转为 Word。
    working_dir 指定为工作目录，这样 Pandoc 就能找到 images/ 文件夹下的图片。
    """
    try:
        pypandoc.get_pandoc_version()
    except OSError:
        pypandoc.download_pandoc()

    # Pandoc 会自动将 $...$ 和 $$...$$ 转为 Word 的原生公式 (OMML)
    pypandoc.convert_file(
        md_file_path, 
        'docx', 
        outputfile=output_docx_path,
        extra_args=[f'--resource-path={working_dir}'] # 关键：告诉引擎图片在哪里
    )
    
    with open(output_docx_path, 'rb') as f:
        docx_bytes = f.read()
        
    return docx_bytes

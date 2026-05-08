import pypandoc
import os

def create_word_from_md(md_text):
    """
    使用 Pandoc 引擎将 Markdown 渲染为排版良好的 Word 文档。
    自动处理公式 (转为 Word 原生公式) 和远端图片。
    """
    # 确保环境中有 Pandoc (Streamlit 如果漏装 packages.txt，这里会自动补救下载)
    try:
        pypandoc.get_pandoc_version()
    except OSError:
        pypandoc.download_pandoc()

    output_file = "translated_output.docx"
    
    # 核心转换逻辑：Markdown -> Docx
    # extra_args 指定一些样式优化
    pypandoc.convert_text(
        md_text, 
        'docx', 
        format='md', 
        outputfile=output_file,
        extra_args=['--mathml'] # 确保公式支持
    )
    
    # 读取生成的二进制文件供下载
    with open(output_file, 'rb') as f:
        docx_bytes = f.read()
        
    # 清理临时文件
    if os.path.exists(output_file):
        os.remove(output_file)
        
    return docx_bytes

from magic_pdf.pipe.UNIPipe import UNIPipe
from magic_pdf.rw.AbsReaderWriter import DiskReaderWriter

def parse_pdf_to_markdown(pdf_bytes, output_dir="./output"):
    # 将 bytes 写入临时文件
    with open("temp.pdf", "wb") as f:
        f.write(pdf_bytes)
    
    # 初始化 MinerU 解析器
    image_writer = DiskReaderWriter(output_dir)
    pipe = UNIPipe("temp.pdf", {}, image_writer)
    pipe.pipe_parse()
    
    # 获取 markdown 内容
    md_content = pipe.pipe_mk()
    return md_content
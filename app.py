import streamlit as st
import time
import tempfile
import zipfile
import os
import io
from utils.parser import parse_agent_api, parse_pro_api
from utils.translator import baidu_translate, mask_markdown, unmask_markdown
from utils.exporter import generate_word

st.set_page_config(page_title="MinerU 专业翻译官", layout="wide")
st.title("📄 MinerU PDF 原生排版翻译系统")

with st.sidebar:
    st.header("1. 解析引擎")
    mode = st.radio("选择模型", ["🎯 精准版 (带图片/公式, 需Token)", "⚡ 轻量版 (纯文本, 免Token)"])
    if "精准" in mode:
        mineru_token = st.text_input("输入 MinerU Token", type="password")
    else:
        mineru_token = None
        
    st.header("2. 翻译引擎")
    baidu_id = st.text_input("Baidu AppID", type="password")
    baidu_key = st.text_input("Baidu Secret Key", type="password")
    target_lang = st.selectbox("目标语言", [("中文", "zh"), ("英文", "en")], format_func=lambda x: x[0])

st.write("---")
uploaded_file = st.file_uploader("上传 PDF 文件", type="pdf")

if st.button("🚀 开始解析并翻译"):
    if not (baidu_id and baidu_key): st.error("请配置百度API！"); st.stop()
    if "精准" in mode and not mineru_token: st.error("精准版需 Token！"); st.stop()
    if not uploaded_file: st.warning("请上传文件！"); st.stop()

    # 创建一个安全的沙盒临时文件夹
    with tempfile.TemporaryDirectory() as tmpdir:
        # --- 阶段 1：解析获取资源 ---
        with st.status(f"正在启动 MinerU {mode[:3]} 解析...") as status:
            if "精准" in mode:
                res_data, msg = parse_pro_api(uploaded_file, mineru_token)
            else:
                res_data, msg = parse_agent_api(uploaded_file)
                
            if not res_data:
                status.update(label="解析失败", state="error")
                st.error(msg); st.stop()
                
            # 处理资源
            if res_data["type"] == "zip":
                # 解压 ZIP 到临时目录 (包含 .md 和 images/ 文件夹)
                with zipfile.ZipFile(io.BytesIO(res_data["content"])) as z:
                    z.extractall(tmpdir)
                md_files = [f for f in os.listdir(tmpdir) if f.endswith('.md')]
                md_path = os.path.join(tmpdir, md_files[0])
                with open(md_path, 'r', encoding='utf-8') as f:
                    source_md = f.read()
            else:
                # 轻量版纯文本
                source_md = res_data["content"]
                md_path = os.path.join(tmpdir, "source.md")
                
            status.update(label="资源提取成功！", state="complete")

        # --- 阶段 2：保护与极速翻译 ---
        with st.status("正在进行保护性极速翻译...") as status:
            masked_md, ph_dict = mask_markdown(source_md)
            lines = masked_md.split('\n')
            translated_lines = [""] * len(lines)
            
            chunks, current_chunk, current_len = [], [], 0
            
            for i, line in enumerate(lines):
                clean = line.strip()
                
                # 判断当前行是否完全是 Markdown 表格，或者是占位符本身
                is_md_table = clean.startswith('|')
                is_pure_placeholder = re.fullmatch(r'__PH_\d+__', clean)
                
                # 如果是有意义的纯文本，就加入翻译块
                if clean and not is_md_table and not is_pure_placeholder:
                    current_chunk.append((i, line))
                    current_len += len(line)
                    if current_len > 1500:
                        chunks.append(current_chunk)
                        current_chunk, current_len = [], 0
                else:
                    # 表格行、纯掩码行、空行直接保留原样，绝不发给百度！
                    translated_lines[i] = line
                    
            if current_chunk: chunks.append(current_chunk)

            # 批量发送给百度 API
            pbar = st.progress(0.0)
            for c_idx, chunk in enumerate(chunks):
                text_block = "\n".join([item[1] for item in chunk])
                trans_block = baidu_translate(text_block, baidu_id, baidu_key, to_lang=target_lang[1])
                trans_parts = trans_block.split('\n')
                
                if len(trans_parts) == len(chunk):
                    for k, (orig_idx, _) in enumerate(chunk):
                        translated_lines[orig_idx] = trans_parts[k]
                else:
                    translated_lines[chunk[0][0]] = trans_block
                    for orig_idx, _ in chunk[1:]: translated_lines[orig_idx] = ""
                
                pbar.progress((c_idx + 1) / len(chunks))
                time.sleep(1.2)

            final_masked_md = "\n".join(translated_lines)
            
            # 还原公式、HTML表格和图片
            final_md = unmask_markdown(final_masked_md, ph_dict)
            
            # 写入沙盒供 Pandoc 使用
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(final_md)
                
            status.update(label="翻译完毕，表格与公式已恢复！", state="complete")

        # --- 阶段 3：生成终极 Word ---
        with st.spinner("Pandoc 正在将图片和公式封装进 Word..."):
            docx_path = os.path.join(tmpdir, "output.docx")
            word_bytes = generate_word(md_path, docx_path, tmpdir)

        # --- 渲染展示 ---
        st.divider()
        st.subheader("💾 导出与下载")
        st.success("✅ 转换完成！公式已被转换为 Word 原生可编辑公式，图片已嵌入文档。")
        
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button("📥 下载完美排版 Word (.docx)", word_bytes, file_name=f"译文_{uploaded_file.name}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
        with col_dl2:
            st.download_button("📥 下载 Markdown 源码 (.md)", final_md, file_name=f"译文_{uploaded_file.name}.md", mime="text/markdown", use_container_width=True)

        st.write("---")
        st.subheader("翻译结果源码预览")
        st.text_area("Markdown", final_md, height=400)

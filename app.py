import streamlit as st
import time
from utils.parser import parse_agent_api, parse_pro_api
from utils.translator import baidu_translate, mask_markdown, unmask_markdown
from utils.exporter import create_word_from_md

st.set_page_config(page_title="MinerU 专业翻译官", layout="wide")
st.title("📄 MinerU PDF 保持排版翻译系统")

with st.sidebar:
    st.header("1. 解析引擎选择")
    mode = st.radio("选择模型", ["⚡ 轻量版 (免Token)", "🎯 精准版 (需Token)"])
    
    if "轻量" in mode:
        st.caption("限制: <=10MB, <=20页。极速体验。")
        mineru_token = None
    else:
        st.caption("限制: <=200MB, <=200页。最佳公式图表支持。")
        mineru_token = st.text_input("输入 MinerU Token", type="password")
    
    st.header("2. 翻译 API 配置")
    baidu_id = st.text_input("Baidu AppID", type="password")
    baidu_key = st.text_input("Baidu Secret Key", type="password")
    target_lang = st.selectbox("目标语言", [("中文", "zh"), ("英文", "en"), ("日文", "jp")], format_func=lambda x: x[0])

st.write("---")
uploaded_file = st.file_uploader("上传待翻译 PDF 文件", type="pdf")

if st.button("🚀 启动深度解析与翻译"):
    if not (baidu_id and baidu_key):
        st.error("请配置百度翻译 API！")
        st.stop()
    if "精准" in mode and not mineru_token:
        st.error("精准版必须输入 MinerU Token！")
        st.stop()
    if not uploaded_file:
        st.warning("请上传文件！")
        st.stop()

    # --- 阶段 1：解析 PDF ---
    md_content = ""
    with st.status(f"正在启动 {mode[:4]} 解析...") as status:
        if "轻量" in mode:
            md_content = parse_agent_api(uploaded_file)
        else:
            md_content = parse_pro_api(uploaded_file, mineru_token)
            
        if "失败" in md_content or "异常" in md_content or "超时" in md_content:
            status.update(label="解析出错", state="error")
            st.error(md_content)
            st.stop()
        status.update(label="文档结构和公式提取成功！", state="complete")

    # --- 阶段 2：保护与极速翻译 ---
    with st.status("正在进行保护性极速翻译...") as status:
        # 1. 隐藏公式和图片
        masked_md, ph_dict = mask_markdown(md_content)
        
        # 2. 准备分块发送 (大幅提速)
        lines = masked_md.split('\n')
        translated_lines = [""] * len(lines)
        chunks, current_chunk, current_len = [], [], 0
        
        for i, line in enumerate(lines):
            clean = line.strip()
            # 跳过空行和表格排版符，只翻译包含文本的行
            if clean and not clean.startswith('|'):
                current_chunk.append((i, line))
                current_len += len(line)
                if current_len > 1500:
                    chunks.append(current_chunk)
                    current_chunk, current_len = [], 0
            else:
                translated_lines[i] = line
                
        if current_chunk: chunks.append(current_chunk)

        # 3. 批量调用百度翻译
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
            time.sleep(1.2) # 遵守 API 限频

        # 4. 还原被保护的公式和图片
        final_masked_md = "\n".join(translated_lines)
        final_md = unmask_markdown(final_masked_md, ph_dict)
        
        status.update(label="翻译及排版还原完毕！", state="complete")

    # --- 阶段 3：生成最终文档 ---
    with st.spinner("正在将结果渲染为原生 Word 文档..."):
        word_bytes = create_word_from_md(final_md)

    st.divider()
    st.subheader("💾 导出与下载")
    st.success("✨ **转换成功！** 原有标题层级、图片均已保留。所有的数学公式（$ 和 $$）已转为 Word 原生可编辑公式。")
    
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button("📥 下载完美排版 Word (.docx)", word_bytes, file_name=f"译文_{uploaded_file.name}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
    with col_dl2:
        st.download_button("📥 下载 Markdown 源码 (.md)", final_md, file_name=f"译文_{uploaded_file.name}.md", mime="text/markdown", use_container_width=True)

    st.write("---")
    st.subheader("翻译结果预览")
    st.markdown(final_md)

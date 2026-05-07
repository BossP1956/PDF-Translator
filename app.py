import streamlit as st
import time
from utils.parser import parse_pdf_via_api
from utils.translator import baidu_translate

st.set_page_config(page_title="MinerU 翻译官", layout="wide")
st.title("📄 MinerU PDF 保持格式在线翻译")

# 侧边栏
with st.sidebar:
    st.header("1. API Key 配置")
    m_key = st.text_input("MinerU API Token", type="password")
    b_id = st.text_input("Baidu AppID", type="password")
    b_key = st.text_input("Baidu SecretKey", type="password")
    
    st.header("2. 翻译设置")
    target_lang = st.selectbox("目标语言", ["zh", "en", "jp", "kor"], index=0)
    st.info("提示：百度免费版 API 每秒只能请求 1 次，翻译较慢请见谅。")

# 主界面
uploaded_file = st.file_uploader("点击上传 PDF 文件", type="pdf")

if st.button("🚀 开始解析并翻译") and uploaded_file:
    if not (m_key and b_id and b_key):
        st.warning("请先填好侧边栏的所有 API Key")
        st.stop()

    # 步骤 1：调用 MinerU
    with st.status("正在通过 MinerU 解析 PDF 结构...") as status:
        md_content = parse_pdf_via_api(uploaded_file, m_key)
        if not md_content or "错误" in md_content or "失败" in md_content:
            st.error(md_content)
            st.stop()
        status.update(label="解析成功！正在启动翻译引擎...", state="complete")

    # 步骤 2：翻译 Markdown
    translated_lines = [] # 提前初始化，防止 NameError
    lines = md_content.split('\n')
    
    with st.status("正在进行格式保留翻译...") as status:
        progress_bar = st.progress(0)
        total_lines = len(lines)
        
        for i, line in enumerate(lines):
            # 基础过滤：不翻译图片、链接、代码块标记
            strip_line = line.strip()
            if strip_line and not strip_line.startswith('![') and not strip_line.startswith('```'):
                # 百度 QPS 限制：每秒 1 次
                translated_text = baidu_translate(line, b_id, b_key, to_lang=target_lang)
                translated_lines.append(translated_text)
                time.sleep(1.1) 
            else:
                translated_lines.append(line)
            
            # 更新进度条
            progress_bar.progress((i + 1) / total_lines)
        
        status.update(label="全部翻译完成！", state="complete")

    # 最终汇总
    final_md = "\n".join(translated_lines)

    # 步骤 3：结果展示
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("原文预览 (Markdown)")
        st.text_area("Source", md_content, height=400)
    with col2:
        st.subheader("翻译预览")
        st.markdown(final_md)
        st.download_button("💾 下载 Markdown 译文", final_md, file_name="translated.md")

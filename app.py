import streamlit as st
from utils.parser import parse_pdf_to_markdown
from utils.translator import baidu_translate
import os

st.set_page_config(page_title="MinerU PDF 翻译助手", layout="wide")

st.title("📄 MinerU PDF 保持格式翻译官")

# 侧边栏配置
with st.sidebar:
    st.header("API 配置")
    appid = st.text_input("Baidu AppID", type="password")
    secret_key = st.text_input("Baidu Secret Key", type="password")
    target_lang = st.selectbox("目标语言", ["zh", "en", "jp", "kor"], index=0)

uploaded_file = st.file_uploader("上传 PDF 文件", type="pdf")

if uploaded_file and appid and secret_key:
    if st.button("开始解析并翻译"):
        with st.spinner("MinerU 正在深度解析文档结构..."):
            # 1. 解析
            md_content = parse_pdf_to_markdown(uploaded_file.read())
            
        with st.spinner("正在逐段翻译..."):
            # 2. 翻译 (按行简单处理，实际可按段落提高API效率)
            lines = md_content.split('\n')
            translated_lines = []
            for line in lines:
                if line.strip() and not line.startswith('!['): # 略过图片链接
                    trans = baidu_translate(line, appid, secret_key, to_lang=target_lang)
                    translated_lines.append(trans)
                else:
                    translated_lines.append(line)
            
            final_md = "\n".join(translated_lines)
            
        # 3. 展示结果
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("原始 Markdown 结构")
            st.text_area("RAW MD", md_content, height=400)
        with col2:
            st.subheader("翻译后预览")
            st.markdown(final_md)
            
        st.download_button("下载翻译后的 Markdown", final_md, file_name="translated.md")
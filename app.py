import streamlit as st
import time
from utils.parser import parse_pdf_via_api
from utils.translator import baidu_translate

st.set_page_config(page_title="MinerU PDF 翻译助手", layout="wide")
st.title("📄 MinerU PDF 保持格式翻译官")

# 侧边栏配置
with st.sidebar:
    st.header("API 密钥配置")
    # 错误修复：type 必须是 "password"，不要把 key 粘在这里
    mineru_key = st.text_input("MinerU API Key", type="password", help="从 mineru.org.cn 获取的 Token")
    baidu_id = st.text_input("Baidu AppID", type="password")
    baidu_key = st.text_input("Baidu Secret Key", type="password")
    target_lang = st.selectbox("目标语言", ["zh", "en", "jp"], index=0)

uploaded_file = st.file_uploader("上传 PDF 文件", type="pdf")

if st.button("开始转换并翻译") and uploaded_file:
    if not (mineru_key and baidu_id and baidu_key):
        st.error("请在左侧边栏填写所有的 API 密钥！")
    else:
        # --- 步骤 1: 解析 ---
        with st.status("正在调用 MinerU 解析文档结构...") as status:
            md_content = parse_pdf_via_api(uploaded_file, mineru_key)
            if "错误" in md_content or not md_content:
                status.update(label="解析失败", state="error")
                st.error(md_content)
                st.stop()
            status.update(label="解析成功！正在准备翻译...", state="complete")

        # --- 步骤 2: 翻译 ---
        translated_lines = []
        lines = md_content.split('\n')
        
        with st.status("正在逐句翻译（保持 Markdown 格式）...") as status:
            pbar = st.progress(0)
            total = len(lines)
            
            for i, line in enumerate(lines):
                # 更新进度
                pbar.progress((i + 1) / total)
                
                # 过滤：只翻译文本，不翻译图片、链接和空行
                clean_line = line.strip()
                if clean_line and not clean_line.startswith('![') and not clean_line.startswith('<'):
                    # 百度 API 免费版 QPS 为 1，必须加延迟
                    try:
                        trans = baidu_translate(clean_line, baidu_id, baidu_key, to_lang=target_lang)
                        translated_lines.append(trans)
                        time.sleep(1.1) # 略大于 1 秒以确保安全
                    except Exception as e:
                        translated_lines.append(line) # 翻译失败保留原文
                else:
                    translated_lines.append(line)
            
            status.update(label="全部翻译完成！", state="complete")

        final_md = "\n".join(translated_lines)

        # --- 步骤 3: 展示 ---
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("原始结构")
            st.text_area("Source Markdown", md_content, height=500)
        with col2:
            st.subheader("翻译预览")
            st.markdown(final_md)
            st.download_button("📥 下载翻译后的 Markdown", final_md, file_name="translated_doc.md")

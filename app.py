import streamlit as st
from utils.parser import parse_pdf_via_api
from utils.translator import baidu_translate

st.title("📄 MinerU API 轻量化翻译助手")

with st.sidebar:
    st.header("API 密钥配置")
    mineru_key = st.text_input("MinerU API Key", type="eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiI2OTYwMjI1NCIsInJvbCI6IlJPTEVfUkVHSVNURVIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc3ODE1OTQyOCwiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiIiwib3BlbklkIjpudWxsLCJ1dWlkIjoiY2E4YTI5OTMtNTk5Ni00NzUzLWJjMWYtYzFhNTA0ZTQyOGNjIiwiZW1haWwiOiIiLCJleHAiOjE3ODU5MzU0Mjh9.SqcPYzQKE_CNbEZGAd8c9ab8HE1WuFUwB1s_hYX__IFGn33w4l9RSrjNsZLR7AteF-iwqkJ14200r74XUicZGg")
    baidu_id = st.text_input("Baidu AppID", type="password")
    baidu_key = st.text_input("Baidu Secret Key", type="password")

uploaded_file = st.file_uploader("上传 PDF", type="pdf")

if uploaded_file and mineru_key and baidu_id and baidu_key:
    if st.button("开始转换"):
        # 直接传递文件流
        with st.spinner("MinerU 云端正在解析..."):
            md_content = parse_pdf_via_api(uploaded_file, mineru_key)
        
        if md_content.startswith("解析失败"):
            st.error(md_content)
        else:
            with st.spinner("正在翻译..."):
                # 同样的翻译逻辑
                lines = md_content.split('\n')
                # ... (同之前的翻译代码)
                final_md = "\n".join(translated_lines)
                st.markdown(final_md)

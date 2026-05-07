import streamlit as st
import time
from utils.parser import parse_pdf_via_api
from utils.translator import baidu_translate

st.set_page_config(page_title="MinerU 翻译助手")
st.title("📄 MinerU PDF 翻译助手")

# 侧边栏配置
with st.sidebar:
    st.header("API 配置")
    mineru_key = st.text_input("MinerU API Key", type="password")
    appid = st.text_input("Baidu AppID", type="password")
    secret_key = st.text_input("Baidu Secret Key", type="password")
    target_lang = st.selectbox("目标语言", ["zh", "en", "jp"], index=0)

uploaded_file = st.file_uploader("上传 PDF 文件", type="pdf")

# 检查是否点击按钮且输入了必要信息
if st.button("开始转换") and uploaded_file:
    if not (mineru_key and appid and secret_key):
        st.error("请先在侧边栏配置所有 API Key！")
    else:
        # 1. 解析阶段
        with st.spinner("MinerU 正在云端解析..."):
            md_content = parse_pdf_via_api(uploaded_file, mineru_key)
        
        # 2. 判断解析是否成功
        if "解析失败" in md_content or not md_content:
            st.error(f"解析出现问题: {md_content}")
        else:
            # --- 关键修复：在此处初始化变量 ---
            translated_lines = [] 
            
            with st.spinner("正在逐句翻译，请稍候..."):
                lines = md_content.split('\n')
                progress_bar = st.progress(0)
                
                for i, line in enumerate(lines):
                    # 更新进度条
                    progress_bar.progress((i + 1) / len(lines))
                    
                    # 只有当行不是空行且不是图片引用时才翻译
                    if line.strip() and not line.strip().startswith('!['):
                        # 为了避免百度 API QPS 限制，建议此处加微小延迟
                        # 或者根据百度 API 等级调整
                        result = baidu_translate(line, appid, secret_key, to_lang=target_lang)
                        translated_lines.append(result)
                        time.sleep(0.1) # 基础版 API QPS 通常为 1
                    else:
                        translated_lines.append(line)
            
            # --- 确保这一行在定义了 translated_lines 的逻辑分支内 ---
            final_md = "\n".join(translated_lines)
            
            # 3. 结果展示
            st.success("翻译完成！")
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("原始 Markdown")
                st.text_area("Original", md_content, height=400)
            with col2:
                st.subheader("翻译结果")
                st.markdown(final_md)
                st.download_button("下载翻译结果", final_md, file_name="translated.md")

import streamlit as st
import time
from utils.parser import parse_pdf_via_api
from utils.translator import baidu_translate

# 页面配置
st.set_page_config(page_title="MinerU PDF 翻译助手", layout="wide")
st.title("📄 MinerU PDF 保持格式翻译官")
st.caption("基于 MinerU Agent 轻量解析接口 + 百度翻译 API")

# 1. 侧边栏配置
with st.sidebar:
    st.header("🔑 API 配置")
    # Agent 模式通常支持 IP 限频，若需更高额度请填入 Token
    mineru_token = st.text_input("MinerU Token (可选)", type="password", help="Agent 模式默认支持 IP 限频，填入 Token 可增加额度")
    
    st.divider()
    baidu_id = st.text_input("Baidu AppID", type="password")
    baidu_key = st.text_input("Baidu Secret Key", type="password")
    
    st.divider()
    target_lang = st.selectbox("目标语言", [
        ("中文", "zh"), 
        ("英语", "en"), 
        ("日语", "jp"), 
        ("韩语", "kor")
    ], format_func=lambda x: x[0])
    
    st.info("💡 百度免费版每秒限 1 次请求，翻译过程会加入延迟以防报错。")

# 2. 文件上传
uploaded_file = st.file_uploader("选择一个 PDF 文件", type="pdf")

if st.button("🚀 开始解析并翻译"):
    # 检查必要参数
    if not (baidu_id and baidu_key):
        st.error("请先在左侧边栏填写百度翻译 API 信息！")
        st.stop()
    
    if not uploaded_file:
        st.warning("请先上传 PDF 文件")
        st.stop()

    # --- 阶段 A: MinerU 解析 ---
    md_content = ""
    with st.status("正在通过 MinerU Agent 接口解析 PDF...") as status:
        # 调用 parser.py 中的接口
        md_content = parse_pdf_via_api(uploaded_file, mineru_token)
        
        if not md_content or "失败" in md_content or "异常" in md_content:
            status.update(label="解析失败", state="error")
            st.error(md_content)
            st.stop()
        
        status.update(label="文档结构解析成功！", state="complete")

    # --- 阶段 B: 百度翻译 ---
    translated_lines = [] # 初始化，防止 NameError
    lines = md_content.split('\n')
    total_lines = len(lines)
    
    with st.status("正在翻译 Markdown 文本...") as status:
        progress_bar = st.progress(0)
        
        for i, line in enumerate(lines):
            # 更新进度条
            progress_bar.progress((i + 1) / total_lines)
            
            # 过滤：不翻译图片、代码块标记、空行
            strip_line = line.strip()
            if strip_line and not strip_line.startswith('![') and not strip_line.startswith('```'):
                # 调用百度翻译
                result = baidu_translate(line, baidu_id, baidu_key, to_lang=target_lang[1])
                translated_lines.append(result)
                # 百度 QPS 限制，必须延迟
                time.sleep(1.1)
            else:
                translated_lines.append(line)
        
        status.update(label="翻译任务已全部完成！", state="complete")

    # --- 阶段 C: 结果展示 ---
    final_md = "\n".join(translated_lines)
    
    st.divider()
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("原文预览 (Markdown)")
        st.text_area("Source Text", md_content, height=500)
        
    with col2:
        st.subheader("翻译预览")
        # 直接预览翻译后的 Markdown
        st.markdown(final_md)
        # 提供下载
        st.download_button(
            label="📥 下载翻译后的 Markdown",
            data=final_md,
            file_name=f"translated_{uploaded_file.name.replace('.pdf', '.md')}",
            mime="text/markdown"
        )

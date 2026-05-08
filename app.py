import streamlit as st
import time
from utils.parser import parse_pdf_via_api
from utils.translator import baidu_translate

st.set_page_config(page_title="MinerU PDF 翻译助手", layout="wide")
st.title("📄 MinerU PDF 保持格式在线翻译")
st.caption("基于 MinerU Agent 签名上传机制 (无需 Token) + 百度翻译 API")

# 侧边栏配置
with st.sidebar:
    st.header("🔑 百度翻译 API 配置")
    st.markdown("MinerU 解析已采用免登录的 Agent 接口，只需配置百度翻译即可。")
    baidu_id = st.text_input("Baidu AppID", type="password")
    baidu_key = st.text_input("Baidu Secret Key", type="password")
    
    target_lang = st.selectbox("目标语言", [
        ("中文", "zh"), ("英语", "en"), ("日语", "jp")
    ], format_func=lambda x: x[0])
    
    st.warning("⚠️ 限制说明:\n1. MinerU Agent 最大支持 10MB，20页\n2. 百度免费 API 限 1次请求/秒")

uploaded_file = st.file_uploader("选择一个 PDF 文件 (<=10MB, <=20页)", type="pdf")

if st.button("🚀 开始解析并翻译"):
    if not (baidu_id and baidu_key):
        st.error("请先在左侧配置百度翻译 AppID 和 Secret Key！")
        st.stop()
        
    if not uploaded_file:
        st.warning("请上传 PDF 文件！")
        st.stop()

    # 步骤 1：MinerU 解析
    md_content = ""
    with st.status("正在通过 MinerU Agent 签名上传并解析...") as status:
        md_content = parse_pdf_via_api(uploaded_file)
        
        if "失败" in md_content or "异常" in md_content or "超时" in md_content:
            status.update(label="解析中断", state="error")
            st.error(md_content)
            st.stop()
            
        status.update(label="文档结构解析完成！", state="complete")

    # 步骤 2：逐行翻译
    translated_lines = []
    lines = md_content.split('\n')
    total_lines = len(lines)
    
    with st.status("正在保持 Markdown 格式翻译文本...") as status:
        pbar = st.progress(0)
        
        for i, line in enumerate(lines):
            pbar.progress((i + 1) / total_lines)
            
            clean_line = line.strip()
            # 过滤不需要翻译的格式 (图片链接、代码块标记、表格排版符号)
            if clean_line and not clean_line.startswith('![') and not clean_line.startswith('```') and not clean_line == '|':
                result = baidu_translate(line, baidu_id, baidu_key, to_lang=target_lang[1])
                translated_lines.append(result)
                # 严格遵守百度免费 API 1 QPS 限制
                time.sleep(1.2)
            else:
                translated_lines.append(line)
                
        status.update(label="全部翻译完成！", state="complete")

    # 步骤 3：展示
    final_md = "\n".join(translated_lines)
    
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("原始 Markdown 结构")
        st.text_area("Source", md_content, height=500)
    with col2:
        st.subheader("翻译预览")
        st.markdown(final_md)
        st.download_button(
            label="📥 下载翻译版 Markdown",
            data=final_md,
            file_name=f"translated_{uploaded_file.name}.md",
            mime="text/markdown"
        )

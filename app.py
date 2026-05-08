import streamlit as st
import time
from utils.parser import parse_agent_api, parse_pro_api
from utils.translator import baidu_translate
from utils.exporter import create_word_from_md

st.set_page_config(page_title="MinerU 翻译大师", layout="wide")
st.title("📄 MinerU PDF 保持格式在线翻译")

# 侧边栏配置
with st.sidebar:
    st.header("1. 解析引擎选择")
    mode = st.radio("选择 MinerU 模式", ["⚡ 轻量版 (免Token)", "🎯 精准版 (需Token)"])
    
    if "轻量" in mode:
        st.info("限制: <=10MB, <=20页。速度极快。")
        mineru_token = None
    else:
        st.success("限制: <=200MB, <=200页。支持高精尖公式表格。")
        mineru_token = st.text_input("输入 MinerU Token", type="password")
    
    st.header("2. 翻译 API 配置")
    baidu_id = st.text_input("Baidu AppID", type="password")
    baidu_key = st.text_input("Baidu Secret Key", type="password")
    
    target_lang = st.selectbox("目标语言", [("中文", "zh"), ("英语", "en"), ("日语", "jp")], format_func=lambda x: x[0])

# 主界面
st.write("---")
uploaded_file = st.file_uploader("上传 PDF 文件", type="pdf")

if st.button("🚀 开始解析并翻译"):
    # 校验参数
    if not (baidu_id and baidu_key):
        st.error("请在侧边栏配置百度翻译 API！")
        st.stop()
    if "精准" in mode and not mineru_token:
        st.error("精准版必须输入 MinerU Token！")
        st.stop()
    if not uploaded_file:
        st.warning("请上传 PDF！")
        st.stop()

    # --- 阶段 1：解析 ---
    md_content = ""
    with st.status(f"正在使用 {mode[:4]} 解析文档...") as status:
        if "轻量" in mode:
            md_content = parse_agent_api(uploaded_file)
        else:
            md_content = parse_pro_api(uploaded_file, mineru_token)
            
        if "失败" in md_content or "异常" in md_content or "超时" in md_content:
            status.update(label="解析出错", state="error")
            st.error(md_content)
            st.stop()
        status.update(label="解析完成！获取到结构化数据。", state="complete")

    # --- 阶段 2：翻译 ---
    translated_lines = []
    lines = md_content.split('\n')
    total_lines = len(lines)
    
    with st.status("正在逐句翻译并重组格式...") as status:
        pbar = st.progress(0)
        for i, line in enumerate(lines):
            pbar.progress((i + 1) / total_lines)
            clean_line = line.strip()
            
            # 保留原格式标记，只翻译普通文本
            if clean_line and not clean_line.startswith('![') and not clean_line.startswith('```') and '|' not in clean_line:
                result = baidu_translate(line, baidu_id, baidu_key, to_lang=target_lang[1])
                translated_lines.append(result)
                time.sleep(1.2) # 百度免费API必须延迟
            else:
                translated_lines.append(line)
        status.update(label="全部翻译完毕！", state="complete")

    # --- 阶段 3：展示与导出 ---
    final_md = "\n".join(translated_lines)
    
    # 生成 Word 文档
    word_bytes = create_word_from_md(translated_lines)
    
    st.divider()
    
    # 顶部下载区
    st.subheader("💾 导出翻译结果")
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button("📥 下载 Word (.docx) - 推荐", word_bytes, file_name=f"译文_{uploaded_file.name}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
    with col_dl2:
        st.download_button("📥 下载 Markdown (.md)", final_md, file_name=f"译文_{uploaded_file.name}.md", mime="text/markdown", use_container_width=True)
    
    st.caption("*提示：由于云端服务器字体限制，直接生成包含复杂排版的 PDF 易产生乱码。请下载 Word 文档后，在本地电脑用 Office 或 WPS 一键另存为 PDF 即可。*")

    # 预览区
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("原文预览 (Markdown)")
        st.text_area("Source", md_content, height=600)
    with col2:
        st.subheader("翻译排版预览")
        st.markdown(final_md)

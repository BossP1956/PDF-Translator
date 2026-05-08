import streamlit as st
import time
import re
from utils.parser import parse_agent_api, parse_pro_api
from utils.translator import baidu_translate
from utils.exporter import create_word_from_md

st.set_page_config(page_title="MinerU 深度翻译官", layout="wide")
st.title("📄 MinerU PDF 深度翻译助手")
st.caption("支持：高精度公式保持、图片自动插入、Word格式导出")

# 1. 保护公式和标签的逻辑
def translate_with_protection(text, appid, key, lang):
    """保护 $...$ 和 ![]() 等标记不被翻译"""
    # 提取公式和图片链接
    placeholders = []
    def substitute(match):
        placeholder = f" [#{len(placeholders)}#] "
        placeholders.append(match.group(0))
        return placeholder

    # 匹配公式 $...$ , $$...$$ 和 图片 ![]()
    pattern = r'(\$\$.*?\$\$|\$.*?\$|!\[.*?\]\(.*?\))'
    protected_text = re.sub(pattern, substitute, text)
    
    # 翻译主体文本
    translated = baidu_translate(protected_text, appid, key, to_lang=lang)
    
    # 还原占位符
    for i, original in enumerate(placeholders):
        translated = translated.replace(f"[#{i}#]", original).replace(f"[ # {i} # ]", original)
    
    return translated

# --- 侧边栏 ---
with st.sidebar:
    st.header("⚙️ 配置中心")
    mode = st.radio("解析引擎", ["⚡ 轻量(Agent)", "🎯 精准(V4)"])
    mineru_token = st.text_input("MinerU Token", type="password") if "精准" in mode else None
    
    st.divider()
    baidu_id = st.text_input("Baidu AppID", type="password")
    baidu_key = st.text_input("Baidu Secret Key", type="password")
    target_lang = st.selectbox("目标语言", [("中文", "zh"), ("英语", "en")], format_func=lambda x: x[0])

# --- 主界面 ---
uploaded_file = st.file_uploader("上传 PDF", type="pdf")

if st.button("🚀 开始深度解析并翻译") and uploaded_file:
    if not (baidu_id and baidu_key):
        st.error("请填入百度 API 信息"); st.stop()
        
    # 1. 解析阶段
    with st.status(f"MinerU 正在识别版式、提取图片和公式...") as status:
        if "轻量" in mode:
            md_content = parse_agent_api(uploaded_file)
        else:
            if not mineru_token: st.error("精准模式需输入Token"); st.stop()
            md_content = parse_pro_api(uploaded_file, mineru_token)
        
        if "失败" in md_content or "异常" in md_content:
            status.update(label="解析失败", state="error"); st.stop()
        status.update(label="解析完成！获取到 Markdown 结构数据。", state="complete")

    # 2. 翻译阶段 (带占位符保护)
    lines = md_content.split('\n')
    total_lines = len(lines)
    translated_lines = [""] * total_lines
    
    # 批量化处理以提高效率
    chunks, current_chunk, current_len = [], [], 0
    for i, line in enumerate(lines):
        clean = line.strip()
        # 跳过空行和纯表格分隔行
        if clean and not (clean.startswith('|') and '-' in clean):
            current_chunk.append((i, line))
            current_len += len(line)
            if current_len > 1200:
                chunks.append(current_chunk); current_chunk, current_len = [], 0
        else:
            translated_lines[i] = line
    if current_chunk: chunks.append(current_chunk)

    with st.status("正在翻译并重组文档...") as status:
        pbar = st.progress(0.0)
        for c_idx, chunk in enumerate(chunks):
            text_block = "\n".join([item[1] for item in chunk])
            # 调用保护翻译函数
            trans_block = translate_with_protection(text_block, baidu_id, baidu_key, target_lang[1])
            parts = trans_block.split('\n')
            
            if len(parts) == len(chunk):
                for k, (orig_idx, _) in enumerate(chunk): translated_lines[orig_idx] = parts[k]
            else:
                translated_lines[chunk[0][0]] = trans_block
            
            pbar.progress((c_idx + 1) / len(chunks))
            time.sleep(1.2)
        status.update(label="翻译与排版完成！", state="complete")

    # 3. 导出阶段
    final_md = "\n".join(translated_lines)
    word_bytes = create_word_from_md(translated_lines)

    st.divider()
    st.subheader("🎉 任务完成")
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("📥 下载翻译版 Word (含图表公式)", word_bytes, file_name=f"译文_{uploaded_file.name}.docx", use_container_width=True)
    with c2:
        st.download_button("📥 下载原始 Markdown", final_md, file_name=f"译文_{uploaded_file.name}.md", use_container_width=True)

    # 预览
    st.markdown("### 翻译效果预览")
    st.markdown(final_md)

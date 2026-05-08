import streamlit as st
import time
import tempfile
import zipfile
import os
import io
from utils.parser import parse_agent_api, parse_pro_api
from utils.translator import baidu_translate, mask_markdown, unmask_markdown
from utils.exporter import generate_word

# 1. 页面基础配置
st.set_page_config(page_title="MinerU 专业翻译官", layout="wide", page_icon="📄")

st.title("📄 MinerU PDF 原生排版翻译系统")
st.markdown("""
本系统通过 **MinerU** 深度解析文档结构，利用 **Pandoc** 引擎保持原文档排版，并支持将公式转换为 Word 可编辑格式。
""")

# 2. 侧边栏配置
with st.sidebar:
    st.header("⚙️ 第一步：解析引擎设置")
    mode = st.radio("选择 MinerU 解析模式", 
                    ["⚡ 轻量版 (免Token, <10M/20页)", "🎯 精准版 (需Token, <200M/200页)"])
    
    mineru_token = None
    if "精准" in mode:
        mineru_token = st.text_input("输入 MinerU API Token", type="password", help="从 mineru.net 获取")
    
    st.divider()
    
    st.header("🔑 第二步：翻译 API 配置")
    baidu_id = st.text_input("Baidu AppID", type="password")
    baidu_key = st.text_input("Baidu Secret Key", type="password")
    
    st.divider()
    
    st.header("🌍 第三步：语言设置")
    target_lang = st.selectbox("翻译目标语言", [
        ("中文", "zh"), 
        ("英语", "en"), 
        ("日语", "jp")
    ], format_func=lambda x: x[0])

    st.info("💡 提示：建议使用‘精准版’以获得最佳的公式和图片支持。")

# 3. 主界面文件上传
st.write("---")
uploaded_file = st.file_uploader("点击或拖拽上传 PDF 文件", type="pdf")

# 4. 核心执行逻辑
if st.button("🚀 启动深度解析与全格式翻译") and uploaded_file:
    # 参数校验
    if not (baidu_id and baidu_key):
        st.error("请配置百度翻译 API 密钥！")
        st.stop()
    if "精准" in mode and not mineru_token:
        st.error("使用精准版模式必须输入 MinerU Token！")
        st.stop()

    # 创建沙盒临时文件夹处理 ZIP 资源
    with tempfile.TemporaryDirectory() as tmpdir:
        
        # --- 阶段 1：解析 PDF 获取资源 ---
        source_md = ""
        md_filename = "source.md"
        
        with st.status(f"正在调用 MinerU {mode[:3]} 引擎解析文档结构...", expanded=True) as status:
            if "精准" in mode:
                res_data, msg = parse_pro_api(uploaded_file, mineru_token)
            else:
                res_data, msg = parse_agent_api(uploaded_file)
                
            if not res_data:
                status.update(label="解析阶段失败", state="error")
                st.error(f"MinerU 报错: {msg}")
                st.stop()
            
            # 处理返回的资源（ZIP 或 纯文本）
            if res_data["type"] == "zip":
                # 精准版通常返回包含 images/ 的 ZIP
                with zipfile.ZipFile(io.BytesIO(res_data["content"])) as z:
                    z.extractall(tmpdir)
                # 寻找解压后的 .md 文件
                md_files = [f for f in os.listdir(tmpdir) if f.endswith('.md')]
                if not md_files:
                    st.error("ZIP 包中未找到 Markdown 内容")
                    st.stop()
                md_filename = md_files[0]
                with open(os.path.join(tmpdir, md_filename), 'r', encoding='utf-8') as f:
                    source_md = f.read()
            else:
                # 轻量版直接返回内容
                source_md = res_data["content"]
                
            status.update(label="文档结构、图片、公式提取成功！", state="complete")

        # --- 阶段 2：公式保护与极速批量翻译 ---
        final_md = ""
        with st.status("正在进行全角标识符保护与极速翻译...", expanded=True) as status:
            # 1. 自动隐藏公式和图片 (使用 【PH_n】 格式)
            masked_md, ph_dict = mask_markdown(source_md)
            
            # 2. 准备分块发送 (大幅提升效率)
            lines = masked_md.split('\n')
            total_lines = len(lines)
            translated_lines = [""] * total_lines
            
            chunks, current_chunk, current_len = [], [], 0
            for i, line in enumerate(lines):
                clean = line.strip()
                # 排除表格符号和空行，减少翻译请求量
                if clean and not clean.startswith('|'):
                    current_chunk.append((i, line))
                    current_len += len(line)
                    if current_len > 1500: # 百度单次推荐长度
                        chunks.append(current_chunk)
                        current_chunk, current_len = [], 0
                else:
                    translated_lines[i] = line
            if current_chunk: chunks.append(current_chunk)

            # 3. 批量调用百度翻译
            if chunks:
                pbar = st.progress(0.0)
                for c_idx, chunk in enumerate(chunks):
                    # 组合
                    text_block = "\n".join([item[1] for item in chunk])
                    # 翻译
                    trans_block = baidu_translate(text_block, baidu_id, baidu_key, to_lang=target_lang[1])
                    # 拆分并写回
                    trans_parts = trans_block.split('\n')
                    
                    if len(trans_parts) == len(chunk):
                        for k, (orig_idx, _) in enumerate(chunk):
                            translated_lines[orig_idx] = trans_parts[k]
                    else:
                        # 若行数不匹配（极少见），整块写入首行
                        translated_lines[chunk[0][0]] = trans_block
                    
                    pbar.progress((c_idx + 1) / len(chunks))
                    # 遵守 API 限频 (实名认证后的高级版可改小)
                    time.sleep(1.1)

            # 4. 还原公式、图片及代码块
            final_masked_md = "\n".join(translated_lines)
            final_md = unmask_markdown(final_masked_md, ph_dict)
            
            # 将翻译好的内容重新存入沙盒，以便 Pandoc 读取本地图片
            translated_md_path = os.path.join(tmpdir, "translated.md")
            with open(translated_md_path, 'w', encoding='utf-8') as f:
                f.write(final_md)
                
            status.update(label="文本翻译及格式还原已完成！", state="complete")

        # --- 阶段 3：Pandoc 渲染 Word ---
        with st.spinner("Pandoc 正在缝合图片并渲染原生 Word 公式..."):
            docx_output_path = os.path.join(tmpdir, "final_output.docx")
            try:
                word_bytes = generate_word(translated_md_path, docx_output_path, tmpdir)
            except Exception as e:
                st.error(f"Word 生成失败: {str(e)}")
                st.stop()

        # --- 阶段 4：结果展示与下载 ---
        st.divider()
        st.subheader("💾 转换结果下载")
        st.success("✨ **完美转换成功！** 公式已转为原生可编辑对象，图片已自动嵌入。")
        
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button(
                label="📥 下载 Word 文档 (.docx)", 
                data=word_bytes, 
                file_name=f"译文_{uploaded_file.name.replace('.pdf', '')}.docx", 
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
                use_container_width=True
            )
        with col_dl2:
            st.download_button(
                label="📥 下载 Markdown 源码 (.md)", 
                data=final_md, 
                file_name=f"译文_{uploaded_file.name}.md", 
                mime="text/markdown", 
                use_container_width=True
            )

        st.info("提示：若 Word 中图片未显示，请检查是否选择了“精准版”解析。")
        
        with st.expander("预览翻译后的内容"):
            st.markdown(final_md)

else:
    st.info("请在左侧配置 API 密钥并上传 PDF 开始体验。")

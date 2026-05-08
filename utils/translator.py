import hashlib
import random
import requests
import re

def mask_markdown(md_text):
    """
    终极保护：在 ZPX 标识符的基础上，增加对表格块的完整保护。
    """
    placeholders = {}
    counter = 0

    def replacer(match):
        nonlocal counter
        key = f"ZPX{counter}"
        placeholders[counter] = match.group(0)
        counter += 1
        return f" {key} "

    # --- 遮罩顺序：必须从大到小，从复杂到简单 ---
    
    # 1. 保护代码块
    md_text = re.sub(r'```.*?```', replacer, md_text, flags=re.DOTALL)
    
    # 2. 保护大块公式 $$ ... $$
    md_text = re.sub(r'\$\$.*?\$\$', replacer, md_text, flags=re.DOTALL)
    
    # 3. 保护 HTML 表格 (MinerU 经常将复杂表格识别为 <table> 标签)
    md_text = re.sub(r'<table.*?>.*?</table>', replacer, md_text, flags=re.DOTALL)

    # 4. 保护 Markdown 表格 (识别以 | 开头的多行表格块)
    # 匹配模式：行首为 |，包含分隔符行 |---|，直到不再以 | 开头
    md_text = re.sub(r'((\n|^)\|.+\|.+\|(\n\|[-| :]+?\|.+\|)(\n\|.+\|.+\|)+)', replacer, md_text)

    # 5. 保护行间公式 \[ ... \]
    md_text = re.sub(r'\\\[.*?\\\]', replacer, md_text, flags=re.DOTALL)
    
    # 6. 保护复杂环境 \begin{...} \end{...}
    md_text = re.sub(r'\\begin\{.*?\}.*?\\end\{.*?\}', replacer, md_text, flags=re.DOTALL)
    
    # 7. 保护行内公式 $ ... $
    md_text = re.sub(r'(?<!\$)\$.*?\$(?!\$)', replacer, md_text)
    
    # 8. 保护图片 ![alt](url)
    md_text = re.sub(r'!\[.*?\]\(.*?\)', replacer, md_text)
    
    # 9. 保护其他 HTML 标签
    md_text = re.sub(r'<.*?>', replacer, md_text, flags=re.DOTALL)

    return md_text, placeholders

def unmask_markdown(text, placeholders):
    """
    全自动容错还原。
    """
    pattern = re.compile(r'[“"「\[\(]?\s*[Zz]\s*[Pp]\s*[Xx]\s*(\d[\s\d]*)\s*[”"」\]\)]?', re.IGNORECASE)
    
    def recover(match):
        try:
            idx_str = match.group(1).replace(' ', '')
            idx = int(idx_str)
            return placeholders.get(idx, match.group(0))
        except:
            return match.group(0)

    return pattern.sub(recover, text)

def baidu_translate(text, appid, secret_key, from_lang='auto', to_lang='zh'):
    if not text.strip(): return text
    endpoint = 'https://fanyi-api.baidu.com/api/trans/vip/translate'
    salt = str(random.randint(32768, 65536))
    sign = hashlib.md5((appid + text + salt + secret_key).encode('utf-8')).hexdigest()
    params = {'q': text, 'from': from_lang, 'to': to_lang, 'appid': appid, 'salt': salt, 'sign': sign}
    try:
        r = requests.get(endpoint, params=params, timeout=25).json()
        if "trans_result" in r:
            return "\n".join([item['dst'] for item in r['trans_result']])
        return text
    except: return text

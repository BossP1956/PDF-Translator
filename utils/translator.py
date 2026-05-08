import hashlib
import random
import requests
import re
import time

def mask_markdown(md_text):
    """
    深度保护：将公式、图片、HTML 标签替换为特殊标识符。
    使用生僻符号 ❖ 能够有效防止翻译引擎在标识符周围乱加空格。
    """
    placeholders = {}
    counter = 0

    def replacer(match):
        nonlocal counter
        key = f"❖PH{counter}❖"
        placeholders[key] = match.group(0)
        counter += 1
        return f" {key} "  # 留出空格防止粘连

    # 1. 保护 \begin{...} ... \end{...} 复杂数学环境 (必须最先处理)
    md_text = re.sub(r'\\begin\{.*?\}.*?\\end\{.*?\}', replacer, md_text, flags=re.DOTALL)
    
    # 2. 保护块级公式 $$ ... $$
    md_text = re.sub(r'\$\$.*?\$\$', replacer, md_text, flags=re.DOTALL)
    
    # 3. 保护行内公式 $ ... $
    md_text = re.sub(r'(?<!\$)\$.*?\$(?!\$)', replacer, md_text)
    
    # 4. 保护图片 ![alt](url)
    md_text = re.sub(r'!\[.*?\]\(.*?\)', replacer, md_text)
    
    # 5. 保护 HTML 表格/标签
    md_text = re.sub(r'<.*?>', replacer, md_text, flags=re.DOTALL)

    return md_text, placeholders

def unmask_markdown(text, placeholders):
    """翻译完成后，将所有占位符还原为原始公式和图片"""
    for key, val in placeholders.items():
        # 兼容翻译引擎可能导致的空格变化
        text = text.replace(f" {key} ", val).replace(key, val)
    return text

def baidu_translate(text, appid, secret_key, from_lang='auto', to_lang='zh'):
    """基础翻译 API 调用"""
    if not text.strip(): return text
    endpoint = 'https://fanyi-api.baidu.com/api/trans/vip/translate'
    salt = str(random.randint(32768, 65536))
    sign = hashlib.md5((appid + text + salt + secret_key).encode('utf-8')).hexdigest()
    params = {'q': text, 'from': from_lang, 'to': to_lang, 'appid': appid, 'salt': salt, 'sign': sign}
    
    try:
        r = requests.get(endpoint, params=params, timeout=15).json()
        if "trans_result" in r:
            return "\n".join([item['dst'] for item in r['trans_result']])
        return text
    except:
        return text

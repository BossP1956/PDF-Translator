import hashlib
import random
import requests
import re

def mask_markdown(md_text):
    """超级保护：将公式和图片替换为特殊标识符，防止百度破坏"""
    placeholders = {}
    counter = 0

    def replacer(match):
        nonlocal counter
        # 使用生僻符号包裹，防止百度翻译时加空格
        key = f" ❖PH{counter}❖ " 
        placeholders[key.strip()] = match.group(0)
        counter += 1
        return key

    # 1. 保护块级公式 $$ ... $$
    md_text = re.sub(r'\$\$.*?\$\$', replacer, md_text, flags=re.DOTALL)
    # 2. 保护行内公式 $ ... $
    md_text = re.sub(r'(?<!\$)\$.*?\$(?!\$)', replacer, md_text)
    # 3. 保护图片 ![alt](url)
    md_text = re.sub(r'!\[.*?\]\(.*?\)', replacer, md_text)
    # 4. 保护 HTML 标签 (MinerU 有时输出表格)
    md_text = re.sub(r'<.*?>', replacer, md_text, flags=re.DOTALL)

    return md_text, placeholders

def unmask_markdown(text, placeholders):
    """翻译后精准还原"""
    for key, val in placeholders.items():
        # 考虑到翻译可能吃掉两边的空格
        text = text.replace(key, val).replace(key.strip(), val)
    return text

def baidu_translate(text, appid, secret_key, from_lang='auto', to_lang='zh'):
    if not text.strip(): return text
    endpoint = 'https://fanyi-api.baidu.com/api/trans/vip/translate'
    salt = str(random.randint(32768, 65536))
    sign = hashlib.md5((appid + text + salt + secret_key).encode('utf-8')).hexdigest()
    params = {'q': text, 'from': from_lang, 'to': to_lang, 'appid': appid, 'salt': salt, 'sign': sign}
    try:
        r = requests.get(endpoint, params=params, timeout=10).json()
        if "trans_result" in r:
            return "\n".join([item['dst'] for item in r['trans_result']])
        return text
    except: return text

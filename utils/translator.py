import hashlib
import random
import requests
import re
import time

def mask_markdown(md_text):
    """提取并保护公式、图片等不需要翻译的内容"""
    placeholders = {}
    counter = 0

    def add_ph(match):
        nonlocal counter
        key = f"ZZZPH{counter}ZZZ"
        placeholders[key] = match.group(0)
        counter += 1
        return key

    # 1. 保护块级公式 $$...$$ (跨行)
    md_text = re.sub(r'\$\$.*?\$\$', add_ph, md_text, flags=re.DOTALL)
    # 2. 保护行内公式 $...$
    md_text = re.sub(r'\$.*?\$', add_ph, md_text)
    # 3. 保护图片 ![alt](url)
    md_text = re.sub(r'!\[.*?\]\(.*?\)', add_ph, md_text)

    return md_text, placeholders

def unmask_markdown(text, placeholders):
    """翻译后，将公式和图片还原回去"""
    for key, val in placeholders.items():
        text = text.replace(key, val)
    return text

def baidu_translate(text, appid, secret_key, from_lang='auto', to_lang='zh'):
    """百度翻译基础调用接口"""
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
    except:
        return text

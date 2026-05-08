import hashlib
import random
import requests
import re
import time

def mask_markdown(md_text):
    """
    使用全角中文括号标识符，百度翻译对该格式保留度极高。
    顺序极度重要：先屏蔽最大的块，再屏蔽小的。
    """
    placeholders = {}
    counter = 0

    def replacer(match):
        nonlocal counter
        key = f"【PH_{counter}】"  # 使用全角括号和下划线
        placeholders[counter] = match.group(0)
        counter += 1
        return key

    # 1. 保护代码块 (防止代码里的符号干扰)
    md_text = re.sub(r'```.*?```', replacer, md_text, flags=re.DOTALL)
    
    # 2. 保护复杂 LaTeX 环境 (\begin{...} ... \end{...})
    md_text = re.sub(r'\\begin\{.*?\}.*?\\end\{.*?\}', replacer, md_text, flags=re.DOTALL)
    
    # 3. 保护块级公式 ($$ ... $$)
    md_text = re.sub(r'\$\$.*?\$\$', replacer, md_text, flags=re.DOTALL)
    
    # 4. 保护行内公式 ($ ... $)
    md_text = re.sub(r'(?<!\$)\$.*?\$(?!\$)', replacer, md_text)
    
    # 5. 保护图片 ![alt](url)
    md_text = re.sub(r'!\[.*?\]\(.*?\)', replacer, md_text)
    
    # 6. 保护 HTML 标签
    md_text = re.sub(r'<.*?>', replacer, md_text, flags=re.DOTALL)

    return md_text, placeholders

def unmask_markdown(text, placeholders):
    """
    使用正则表达式还原标识符，自动容错百度翻译可能添加的空格。
    例如：【 PH _ 8 】 -> 【PH_8】
    """
    # 匹配模式：【 任意空格 PH 任意空格 _ 任意空格 数字 任意空格 】
    pattern = re.compile(r'【\s*PH\s*_\s*(\d+)\s*】')
    
    def recover(match):
        idx = int(match.group(1))
        return placeholders.get(idx, match.group(0))

    return pattern.sub(recover, text)

def baidu_translate(text, appid, secret_key, from_lang='auto', to_lang='zh'):
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

import hashlib
import random
import requests
import re

def mask_markdown(md_text):
    """
    终极保护机制：保护公式、图片、表格
    """
    placeholders = {}
    counter = 0

    def replacer(match):
        nonlocal counter
        # 使用全角方括号，百度翻译通常不会破坏这种中文标点包裹的内容
        core_id = f"PH_{counter}"
        key = f"【{core_id}】"
        placeholders[core_id] = match.group(0)
        counter += 1
        return f"\n\n{key}\n\n" if "\n" in match.group(0) else f" {key} "

    # 1. 保护 Markdown 表格 (连续的包含 | 的行)
    # MinerU 输出的表格通常每行都包含 |
    md_text = re.sub(r'(?:^[ \t]*\|.*\|[ \t]*\n?)+', replacer, md_text, flags=re.MULTILINE)

    # 2. 保护 HTML 表格/标签
    md_text = re.sub(r'<table.*?>.*?</table>', replacer, md_text, flags=re.DOTALL)
    md_text = re.sub(r'<.*?>', replacer, md_text, flags=re.DOTALL)

    # 3. 保护多行数学环境 \begin{...} ... \end{...}
    md_text = re.sub(r'\\begin\{.*?\}.*?\\end\{.*?\}', replacer, md_text, flags=re.DOTALL)
    
    # 4. 保护块级公式 $$ ... $$
    md_text = re.sub(r'\$\$.*?\$\$', replacer, md_text, flags=re.DOTALL)
    
    # 5. 保护行内公式 $ ... $
    md_text = re.sub(r'(?<!\$)\$.*?\$(?!\$)', replacer, md_text)
    
    # 6. 保护图片 ![alt](url)
    md_text = re.sub(r'!\[.*?\]\(.*?\)', replacer, md_text)

    return md_text, placeholders

def unmask_markdown(text, placeholders):
    """
    智能还原：无视翻译引擎加入的空格和大小写变化
    """
    def unmask_replacer(match):
        # 提取核心 ID，去除可能被百度加入的空格，并转大写
        # 例如：把 " PH _ 5 " 变成 "PH_5"
        core_id = match.group(1).replace(" ", "").upper()
        # 从字典中找回原始公式/表格，如果找不到（极端情况），就原样保留
        return placeholders.get(core_id, match.group(0))

    # 使用正则模糊匹配掩码：【 任意空格 PH_数字 任意空格 】
    pattern = r'【\s*(PH\s*_\s*\d+)\s*】'
    restored_text = re.sub(pattern, unmask_replacer, text, flags=re.IGNORECASE)
    
    return restored_text

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

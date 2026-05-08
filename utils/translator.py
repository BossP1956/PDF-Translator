import hashlib
import random
import requests
import re

def mask_markdown(md_text):
    """
    防弹衣级别保护：提取所有不想被翻译的块。
    使用纯英文数字标识 __PH_X__，防止翻译引擎破坏。
    """
    placeholders = {}
    counter = 0

    def replacer(match):
        nonlocal counter
        key = f"__PH_{counter}__"
        # 保存被替换的原始内容
        placeholders[str(counter)] = match.group(0)
        counter += 1
        return key

    # 1. 保护 HTML 表格块 (MinerU 经常用 HTML 生成表格)
    md_text = re.sub(r'<table.*?>.*?</table>', replacer, md_text, flags=re.DOTALL)
    
    # 2. 保护块级公式 $$ ... $$
    md_text = re.sub(r'\$\$.*?\$\$', replacer, md_text, flags=re.DOTALL)
    
    # 3. 保护 \begin{...} ... \end{...} 环境
    md_text = re.sub(r'\\begin\{.*?\}.*?\\end\{.*?\}', replacer, md_text, flags=re.DOTALL)
    
    # 4. 保护行内公式 $ ... $
    md_text = re.sub(r'(?<!\$)\$.*?\$(?!\$)', replacer, md_text)
    
    # 5. 保护图片 ![alt](url)
    md_text = re.sub(r'!\[.*?\]\(.*?\)', replacer, md_text)

    return md_text, placeholders

def unmask_markdown(text, placeholders):
    """
    精准还原：使用正则表达式，无视百度翻译添加的多余空格。
    匹配 __PH_1__, __ PH_ 1 __, __PH _ 1__ 等变体。
    """
    def restore(match):
        idx = match.group(1)
        # 如果能在字典找到，就还原；找不到就保留原样
        return placeholders.get(idx, match.group(0))

    # 忽略大小写和内部空格进行匹配
    restored_text = re.sub(r'__\s*PH\s*_\s*(\d+)\s*__', restore, text, flags=re.IGNORECASE)
    return restored_text

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
    except:
        return text

import hashlib
import random
import requests
import re
import time

def mask_markdown(md_text):
    """
    使用全角中文括号标识符，顺序极度重要：从大块到小块。
    """
    placeholders = {}
    counter = 0

    def replacer(match):
        nonlocal counter
        # 保持格式高度独特
        key = f"【PH_{counter}】" 
        placeholders[counter] = match.group(0) # 以数字作为 Key 存储原始对象
        counter += 1
        return f" {key} " # 前后留空格防止被翻译引擎合并到单词中

    # 1. 保护代码块
    md_text = re.sub(r'```.*?```', replacer, md_text, flags=re.DOTALL)
    
    # 2. 保护复杂 LaTeX 环境 (\begin{...} ... \end{...})
    md_text = re.sub(r'\\begin\{.*?\}.*?\\end\{.*?\}', replacer, md_text, flags=re.DOTALL)
    
    # 3. 保护块级公式 ($$ ... $$)
    md_text = re.sub(r'\$\$.*?\$\$', replacer, md_text, flags=re.DOTALL)
    
    # 4. 保护行内公式 ($ ... $) - 注意排除 $$
    md_text = re.sub(r'(?<!\$)\$.*?\$(?!\$)', replacer, md_text)
    
    # 5. 保护图片 ![alt](url)
    md_text = re.sub(r'!\[.*?\]\(.*?\)', replacer, md_text)
    
    # 6. 保护 HTML 标签
    md_text = re.sub(r'<.*?>', replacer, md_text, flags=re.DOTALL)

    return md_text, placeholders

def unmask_markdown(text, placeholders):
    """
    超级容错还原逻辑：
    无论百度把标识符变成了 【PH_1】、 [ph_1]、 ( PH - 1 ) 还是 【 PH _ 1 】，
    该正则都能精准定位中间的数字并还原。
    """
    # 这个正则匹配：
    # 1. 左括号：【 或 [ 或 (
    # 2. 任意空格
    # 3. 字母：PH 或 ph
    # 4. 任意空格
    # 5. 连接符：_ 或 - 或 没有任何符号
    # 6. 任意空格
    # 7. 目标数字：(\d+)
    # 8. 任意空格
    # 9. 右括号：】 或 ] 或 )
    pattern = re.compile(r'[【\[\(]\s*[Pp][Hh][\s\-_]*(\d+)\s*[】\]\)]')
    
    def recover(match):
        try:
            # 提取中间的数字索引
            idx = int(match.group(1))
            # 从字典中找回原始公式，如果找不到则返回匹配到的原样（防止程序崩溃）
            return placeholders.get(idx, match.group(0))
        except:
            return match.group(0)

    # 执行替换
    return pattern.sub(recover, text)

def baidu_translate(text, appid, secret_key, from_lang='auto', to_lang='zh'):
    if not text.strip(): return text
    endpoint = 'https://fanyi-api.baidu.com/api/trans/vip/translate'
    salt = str(random.randint(32768, 65536))
    sign = hashlib.md5((appid + text + salt + secret_key).encode('utf-8')).hexdigest()
    params = {'q': text, 'from': from_lang, 'to': to_lang, 'appid': appid, 'salt': salt, 'sign': sign}
    
    try:
        r = requests.get(endpoint, params=params, timeout=20).json()
        if "trans_result" in r:
            return "\n".join([item['dst'] for item in r['trans_result']])
        return text
    except:
        return text

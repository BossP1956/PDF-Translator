import hashlib
import random
import requests
import re

def mask_markdown(md_text):
    """
    使用极其独特的、不含任何 Markdown 敏感字符的标识符。
    例如：FORMULAID123
    """
    placeholders = {}
    counter = 0

    def replacer(match):
        nonlocal counter
        # 纯大写字母+数字，没有任何符号，防止被翻译器拆分，也防止 Markdown 解析
        key = f"FORMULAID{counter}"
        placeholders[counter] = match.group(0)
        counter += 1
        return f" {key} " # 前后留空格防止和中文粘连

    # 遮罩顺序：从大块到小块
    # 1. 保护代码块
    md_text = re.sub(r'```.*?```', replacer, md_text, flags=re.DOTALL)
    # 2. 保护大块公式 $$ ... $$
    md_text = re.sub(r'\$\$.*?\$\$', replacer, md_text, flags=re.DOTALL)
    # 3. 保护行间公式 \[ ... \]
    md_text = re.sub(r'\\\[.*?\\\]', replacer, md_text, flags=re.DOTALL)
    # 4. 保护复杂环境 \begin{...} \end{...}
    md_text = re.sub(r'\\begin\{.*?\}.*?\\end\{.*?\}', replacer, md_text, flags=re.DOTALL)
    # 5. 保护行内公式 $ ... $
    md_text = re.sub(r'(?<!\$)\$.*?\$(?!\$)', replacer, md_text)
    # 6. 保护图片
    md_text = re.sub(r'!\[.*?\]\(.*?\)', replacer, md_text)
    # 7. 保护 HTML
    md_text = re.sub(r'<.*?>', replacer, md_text, flags=re.DOTALL)

    return md_text, placeholders

def unmask_markdown(text, placeholders):
    """
    超级容错还原逻辑：
    即便翻译器把标识符变成了 " formula id 123 ", “FormulaID 123”, [FORMULAID123]
    该正则都能精准提取数字并还原。
    """
    # 匹配: (可能是引号/括号) + F + O + R + M + U + L + A + I + D + (任意空格) + (数字) + (可能是引号/括号)
    # 使用 re.IGNORECASE 忽略大小写
    pattern = re.compile(r'[“"「\[\(]?\s*F\s*O\s*R\s*M\s*U\s*L\s*A\s*I\s*D\s*(\d[\s\d]*)\s*[”"」\]\)]?', re.IGNORECASE)
    
    def recover(match):
        try:
            # 提取数字，去掉可能存在的空格
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
        r = requests.get(endpoint, params=params, timeout=20).json()
        if "trans_result" in r:
            return "\n".join([item['dst'] for item in r['trans_result']])
        return text
    except: return text

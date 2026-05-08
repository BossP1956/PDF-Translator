import hashlib
import random
import requests
import re

def mask_markdown(md_text):
    """
    使用极其简短且无元音的辅音组合 ZPX 作为标识符。
    这种组合在翻译引擎看来像是一个型号或内部代码，不会被翻译。
    """
    placeholders = {}
    counter = 0

    def replacer(match):
        nonlocal counter
        # 使用 ZPX + 数字，前后各留一个空格防止粘连
        key = f"ZPX{counter}"
        placeholders[counter] = match.group(0)
        counter += 1
        return f" {key} "

    # 遮罩顺序必须严格执行
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
    # 6. 保护图片 ![alt](url)
    md_text = re.sub(r'!\[.*?\]\(.*?\)', replacer, md_text)
    # 7. 保护 HTML
    md_text = re.sub(r'<.*?>', replacer, md_text, flags=re.DOTALL)

    return md_text, placeholders

def unmask_markdown(text, placeholders):
    """
    终极拼写容错正则：
    即便翻译器把 ZPX 变成了 'Z PX', 'zpx', 'Z-PX' 甚至错拼为 'ZPIX',
    正则都会以 Z 开头，找到后面的数字。
    """
    # 匹配模式：(开头可能有引号/括号) + Z + (可选空格) + P + (可选空格) + X + (可选空格) + 数字 + (结尾可能有引号/括号)
    pattern = re.compile(r'[“"「\[\(]?\s*[Zz]\s*[Pp]\s*[Xx]\s*(\d[\s\d]*)\s*[”"」\]\)]?', re.IGNORECASE)
    
    def recover(match):
        try:
            # 提取数字，去掉由于翻译产生的空格
            idx_str = match.group(1).replace(' ', '')
            idx = int(idx_str)
            # 从字典里拿回原始公式/图片/代码块
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

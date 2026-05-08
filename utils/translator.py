import hashlib
import random
import requests
import re

def mask_markdown(md_text):
    """
    终极保护掩码：
    1. 不含下划线 _，防止被 Markdown 误认为斜体
    2. 不含括号，防止百度擅自将其转为半角或破坏
    3. 顺序：必须先遮罩最大的 $$ 块，防止公式内部的 \begin 被撕碎
    """
    placeholders = {}
    counter = 0

    def replacer(match):
        nonlocal counter
        # 使用特殊符号 + 大写字母 + 数字，前后加空格
        key = f" ❖X{counter}X❖ "
        placeholders[counter] = match.group(0) # 以整数作为 Key，防止字符编码比对失败
        counter += 1
        return key

    # 1. 保护代码块
    md_text = re.sub(r'```.*?```', replacer, md_text, flags=re.DOTALL)
    
    # 2. 保护大块公式 $$ ... $$ (最优先！防止内部矩阵被撕碎)
    md_text = re.sub(r'\$\$.*?\$\$', replacer, md_text, flags=re.DOTALL)
    
    # 3. 保护行间公式 \[ ... \] (MinerU 偶尔会用这个格式)
    md_text = re.sub(r'\\\[.*?\\\]', replacer, md_text, flags=re.DOTALL)
    
    # 4. 保护孤立的 LaTeX 环境
    md_text = re.sub(r'\\begin\{.*?\}.*?\\end\{.*?\}', replacer, md_text, flags=re.DOTALL)
    
    # 5. 保护行内公式 $ ... $
    md_text = re.sub(r'(?<!\$)\$.*?\$(?!\$)', replacer, md_text)
    
    # 6. 保护图片 ![alt](url)
    md_text = re.sub(r'!\[.*?\]\(.*?\)', replacer, md_text)
    
    # 7. 保护 HTML 标签
    md_text = re.sub(r'<.*?>', replacer, md_text, flags=re.DOTALL)

    return md_text, placeholders

def unmask_markdown(text, placeholders):
    """
    超级容错还原逻辑：
    无论百度把掩码变成 '❖X2 20X❖', '❖ x 5 x ❖', 甚至去掉了空格，全都能认出来！
    """
    # 匹配: ❖ + 任意空格 + X或x + 任意空格 + (带空格的数字) + 任意空格 + X或x + 任意空格 + ❖
    pattern = re.compile(r'❖\s*[Xx]\s*(\d[\d\s]*)\s*[Xx]\s*❖')
    
    def recover(match):
        try:
            # 提取中间的数字，去掉百度强加的空格 (比如 '2 20' -> '220')
            idx_str = match.group(1).replace(' ', '')
            idx = int(idx_str)
            # 找回原始公式
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
        r = requests.get(endpoint, params=params, timeout=15).json()
        if "trans_result" in r:
            return "\n".join([item['dst'] for item in r['trans_result']])
        return text
    except:
        return text

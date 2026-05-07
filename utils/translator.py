import hashlib
import random
import requests

def baidu_translate(text, appid, secret_key, from_lang='auto', to_lang='zh'):
    if not text.strip(): 
        return text
    
    endpoint = 'https://fanyi-api.baidu.com/api/trans/vip/translate'
    salt = str(random.randint(32768, 65536))
    sign = hashlib.md5((appid + text + salt + secret_key).encode('utf-8')).hexdigest()
    
    params = {
        'q': text, 'from': from_lang, 'to': to_lang,
        'appid': appid, 'salt': salt, 'sign': sign
    }
    
    try:
        r = requests.get(endpoint, params=params, timeout=10)
        res = r.json()
        if "trans_result" in res:
            return "\n".join([item['dst'] for item in res['trans_result']])
        else:
            # 记录错误原因
            error_code = res.get("error_code")
            if error_code == "54003": return "[频率限制] " + text
            return f"[翻译错误 {error_code}] " + text
    except:
        return text # 报错则返回原文

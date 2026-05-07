import hashlib
import random
import requests

def baidu_translate(text, appid, secret_key, from_lang='auto', to_lang='zh'):
    if not text.strip(): return text
    
    endpoint = 'https://fanyi-api.baidu.com/api/trans/vip/translate'
    salt = str(random.randint(32768, 65536))
    sign = hashlib.md5((appid + text + salt + secret_key).encode('utf-8')).hexdigest()
    
    params = {'q': text, 'from': from_lang, 'to': to_lang, 'appid': appid, 'salt': salt, 'sign': sign}
    
    try:
        r = requests.get(endpoint, params=params, timeout=10)
        res = r.json()
        if "trans_result" in res:
            return "\n".join([item['dst'] for item in res['trans_result']])
        else:
            return f"[翻译出错: {res.get('error_msg', '未知错误')}] {text}"
    except Exception as e:
        return f"[网络错误] {text}"

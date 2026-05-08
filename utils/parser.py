import requests
import time
import zipfile
import io

def parse_pdf_via_api(uploaded_file, api_key=None):
    # Agent 接口地址
    url = "https://mineru.net/api/v1/agent/parse/file"
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    
    try:
        # 1. 准备上传内容
        # files 负责传输二进制流
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
        
        # --- 关键修复：增加 file_name 字段 ---
        # 很多接口要求显式传递文件名字符串
        data = {
            "file_name": uploaded_file.name,
            "model_version": "pipeline"  # 或者用 "vlm"
        }
        
        # 同时发送 files 和 data
        response = requests.post(url, headers=headers, files=files, data=data, timeout=60)
        
        # 解析返回结果
        res_json = response.json()
        
        # 获取 Task ID
        task_id = res_json.get("data", {}).get("task_id") or res_json.get("task_id")
        
        if not task_id:
            msg = res_json.get("msg") or res_json.get("message") or str(res_json)
            # 如果依然报错，我们继续输出详情诊断
            return f"提交失败。服务器返回: {msg}"

        # 2. 轮询状态
        status_url = "https://mineru.net/api/v1/agent/parse/status"
        
        for _ in range(40):
            time.sleep(3)
            status_res = requests.get(status_url, headers=headers, params={"task_id": task_id})
            
            if status_res.status_code != 200:
                continue
                
            status_json = status_res.json()
            res_data = status_json.get("data", {})
            status = res_data.get("status")
            
            if status == "success":
                # 尝试提取结果
                content = res_data.get("markdown_content")
                if content: return content
                
                # 如果返回的是链接，自动下载
                md_url = res_data.get("markdown_url") or res_data.get("download_url")
                if md_url:
                    return requests.get(md_url).text
                
                # 如果是 Zip 链接
                zip_url = res_data.get("full_zip_url")
                if zip_url:
                    z_res = requests.get(zip_url)
                    with zipfile.ZipFile(io.BytesIO(z_res.content)) as z:
                        for f in z.namelist():
                            if f.endswith('.md'): return z.read(f).decode('utf-8')
                
                return "解析成功，但未能提取到文本内容"
            
            if status == "failed":
                return f"解析失败: {res_data.get('error_msg', '未知原因')}"
        
        return "轮询超时，请稍后再试"
        
    except Exception as e:
        return f"连接异常: {str(e)}"

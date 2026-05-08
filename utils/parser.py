import requests
import time
import zipfile
import io

def parse_pdf_via_api(uploaded_file, api_key=None):
    # Agent 接口地址
    url = "https://mineru.net/api/v1/agent/parse/file"
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    
    try:
        # 1. 提交文件
        # 注意：这里 file_name 必须通过 params (URL 参数) 传递
        params = {
            "file_name": uploaded_file.name,
            "model_version": "pipeline"
        }
        
        # 二进制文件流
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
        
        # 核心修改：使用 params 传参，files 传文件
        response = requests.post(
            url, 
            headers=headers, 
            params=params,  # 移到这里
            files=files, 
            timeout=60
        )
        
        # 解析返回结果
        res_json = response.json()
        
        # 提取 Task ID
        task_id = res_json.get("data", {}).get("task_id") or res_json.get("task_id")
        
        if not task_id:
            msg = res_json.get("msg") or res_json.get("message") or str(res_json)
            # 如果依然报错，可能是字段名大小写问题，我们尝试打印完整响应
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
                
                # 兼容不同字段名
                md_url = res_data.get("markdown_url") or res_data.get("download_url")
                if md_url:
                    return requests.get(md_url).text
                
                # 兼容 Zip 包
                zip_url = res_data.get("full_zip_url")
                if zip_url:
                    z_res = requests.get(zip_url)
                    with zipfile.ZipFile(io.BytesIO(z_res.content)) as z:
                        for f in z.namelist():
                            if f.endswith('.md'): return z.read(f).decode('utf-8')
                
                return "解析成功，但未能提取到内容"
            
            if status == "failed":
                return f"解析失败: {res_data.get('error_msg', '未知原因')}"
        
        return "轮询超时"
        
    except Exception as e:
        return f"接口异常: {str(e)}"

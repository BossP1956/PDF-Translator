import requests
import time

def parse_pdf_via_api(uploaded_file, api_key=None):
    # 使用 Agent 接口，支持直接上传文件
    base_url = "https://mineru.net/api/v1/agent/parse/file"
    
    # 准备 Header
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    try:
        # 1. 直接提交二进制文件
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
        response = requests.post(base_url, headers=headers, files=files, timeout=60)
        
        if response.status_code != 200:
            return f"解析请求失败: {response.text}"
            
        task_id = response.json().get("data", {}).get("task_id")
        if not task_id:
            return "解析失败: 未获取到 Task ID"

        # 2. 轮询状态
        status_url = "https://mineru.net/api/v1/agent/parse/status"
        for _ in range(40):
            time.sleep(3)
            status_res = requests.get(status_url, params={"task_id": task_id}, headers=headers)
            if status_res.status_code != 200: continue
            
            res_data = status_res.json().get("data", {})
            status = res_data.get("status")
            
            if status == "success":
                # 优先获取 markdown_content
                content = res_data.get("markdown_content")
                if content: return content
                
                # 若返回的是 URL 则下载
                md_url = res_data.get("markdown_url")
                if md_url: return requests.get(md_url).text
                
                return "解析成功但内容为空"
            
            if status == "failed":
                return "MinerU Agent 解析失败"
                
        return "轮询超时"
        
    except Exception as e:
        return f"接口异常: {str(e)}"

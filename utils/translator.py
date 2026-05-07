import requests
import time

def parse_pdf_via_api(uploaded_file, api_key):
    # 官方文档指定的基准地址
    base_url = "https://mineru.net/api/v1"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        # 1. 提交任务 (接口: /extract)
        # 官方要求使用 multipart/form-data
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
        # data 参数根据文档可选，通常传空或指定特定功能
        submit_res = requests.post(f"{base_url}/extract", headers=headers, files=files, timeout=60)
        
        if submit_res.status_code != 200:
            return f"提交失败 ({submit_res.status_code}): {submit_res.json().get('msg', '未知错误')}"
        
        task_id = submit_res.json().get("data", {}).get("task_id")
        if not task_id:
            return "解析失败：未能获取任务ID"

        # 2. 轮询任务状态 (接口: /task-status)
        # 注意：官方文档查询状态通常带 task_id 参数
        max_retries = 30
        for _ in range(max_retries):
            time.sleep(3) # 官方解析较重，建议间隔3秒
            status_res = requests.get(f"{base_url}/task-status", headers=headers, params={"task_id": task_id})
            
            if status_res.status_code != 200:
                continue
            
            res_data = status_res.json().get("data", {})
            status = res_data.get("status")
            
            if status == "success":
                # 官方通常返回 markdown 内容或下载链接
                # 如果返回的是 md 内容直接使用，如果返回的是 url 则需再次 get
                content = res_data.get("markdown_content")
                if not content and res_data.get("full_zip_url"):
                    # 如果官方只给压缩包链接，这里需要处理，但通常 API 直接给 content
                    return "解析成功，但 API 仅返回了压缩包，请检查文档配置"
                return content
            
            if status == "failed":
                return f"MinerU 解析失败: {res_data.get('error_msg', '未知错误')}"
        
        return "解析超时，文件可能过大"
        
    except Exception as e:
        return f"API 调用异常: {str(e)}"

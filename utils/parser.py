import requests
import time

def parse_pdf_via_api(pdf_file, api_key):
    """通过 API 调用 MinerU 解析 PDF"""
    base_url = "https://mineru.org.cn/api/v1" # 请根据官方文档确认具体 URL
    
    # 1. 上传并提交任务
    headers = {"Authorization": f"Bearer {api_key}"}
    files = {"file": pdf_file}
    
    try:
        response = requests.post(f"{base_url}/extract", headers=headers, files=files)
        task_id = response.json().get("data", {}).get("task_id")
        
        if not task_id:
            return f"任务提交失败: {response.text}"

        # 2. 轮询等待结果
        while True:
            status_res = requests.get(f"{base_url}/task/{task_id}", headers=headers)
            res_data = status_res.json().get("data", {})
            status = res_data.get("status")
            
            if status == "success":
                # 获取解析后的 Markdown 内容
                return res_data.get("markdown_content")
            elif status == "failed":
                return "API 解析失败"
            
            time.sleep(2) # 每 2 秒查询一次
            
    except Exception as e:
        return f"API 调用异常: {str(e)}"

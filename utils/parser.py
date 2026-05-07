import requests
import time

def parse_pdf_via_api(uploaded_file, api_key):
    """
    通用 MinerU API 调用逻辑
    注意：这里的 URL 是示例，请替换为你实际申请到的 API Endpoint
    """
    api_url = "https://mineru.org.cn/api/v1/extract" # 请根据官方确认
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        # 上传文件
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
        response = requests.post(api_url, headers=headers, files=files, timeout=30)
        
        if response.status_code != 200:
            return f"API 错误: 状态码 {response.status_code}, 内容 {response.text}"
        
        res_json = response.json()
        task_id = res_json.get("data", {}).get("task_id")
        
        if not task_id:
            return "解析失败：未获取到任务 ID"

        # 轮询获取结果
        for _ in range(30): # 最多等待 60 秒
            time.sleep(2)
            status_url = f"https://mineru.org.cn/api/v1/task/{task_id}"
            status_res = requests.get(status_url, headers=headers)
            status_json = status_res.json()
            
            # 增加安全检查
            if status_json.get("data") is None:
                continue
                
            state = status_json["data"].get("status")
            if state == "success":
                return status_json["data"].get("markdown_content", "解析内容为空")
            elif state == "failed":
                return "MinerU 云端解析失败"
        
        return "解析超时"
        
    except Exception as e:
        return f"API 调用异常: {str(e)}"

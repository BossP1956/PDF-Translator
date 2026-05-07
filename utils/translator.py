import requests
import time

def parse_pdf_via_api(uploaded_file, api_key):
    # v4 版本的正式域名 (请根据官方文档确认，通常是如下地址)
    base_url = "https://mineru.org.cn/api/v4" 
    upload_url = f"{base_url}/extract"
    
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        # 1. 发起上传任务
        # v4 接口通常需要 multipart/form-data
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
        # data 参数可以根据 v4 文档添加，比如 {"is_ocr": True}
        response = requests.post(upload_url, headers=headers, files=files, timeout=45)
        
        if response.status_code != 200:
            return f"v4 API 错误: 状态码 {response.status_code}, 内容 {response.text}"
        
        res_json = response.json()
        # 注意：v4 的返回结构可能在 data.extract_id 或 data.task_id
        task_id = res_json.get("data", {}).get("task_id") or res_json.get("data", {}).get("extract_id")
        
        if not task_id:
            return f"解析失败：未获取到任务ID。完整响应: {res_json}"

        # 2. 轮询获取结果
        # v4 的查询接口可能是 /extract-result/{task_id} 或 /task/{task_id}
        status_url = f"{base_url}/extract-result/{task_id}"
        
        for i in range(60): # 最多等待 120 秒
            time.sleep(2)
            status_res = requests.get(status_url, headers=headers)
            if status_res.status_code != 200:
                continue
                
            result_json = status_res.json()
            data = result_json.get("data", {})
            status = data.get("status")
            
            if status == "success":
                # v4 版本解析成功后，markdown 内容通常在 data.full_markdown 中
                return data.get("full_markdown") or data.get("markdown") or "解析完成但未找到内容"
            elif status == "failed":
                return f"MinerU v4 解析任务失败: {data.get('error_msg')}"
            
            # 如果还在 processing，继续循环
            
        return "解析任务超时，请重试。"
        
    except Exception as e:
        return f"v4 API 调用异常: {str(e)}"

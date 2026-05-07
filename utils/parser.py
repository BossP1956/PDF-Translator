import requests
import time

def parse_pdf_via_api(uploaded_file, api_key):
    base_url = "https://mineru.net/api/v1"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        # 1. 提交任务
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
        # data 参数可以传递如 {"is_ocr": True} 等，这里保持默认
        submit_res = requests.post(f"{base_url}/extract", headers=headers, files=files, timeout=60)
        
        if submit_res.status_code != 200:
            msg = submit_res.json().get("msg", "未知错误")
            return f"提交错误: {msg} (请确认已在mineru.net订阅API服务)"
        
        task_id = submit_res.json().get("data", {}).get("task_id")
        if not task_id:
            return "解析失败：未获得 task_id"

        # 2. 轮询状态
        for i in range(40):  # 最多等待 120 秒
            time.sleep(3)
            status_res = requests.get(f"{base_url}/task-status", headers=headers, params={"task_id": task_id})
            
            if status_res.status_code != 200:
                continue
                
            res_data = status_res.json().get("data", {})
            status = res_data.get("status")
            
            if status == "success":
                # 获取结果内容
                return res_data.get("markdown_content", "解析结果为空")
            elif status == "failed":
                return f"MinerU 解析失败: {res_data.get('error_msg', '内部错误')}"
                
        return "解析超时：文档较大，请稍后在官网查看结果"
        
    except Exception as e:
        return f"解析异常: {str(e)}"

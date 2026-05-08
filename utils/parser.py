import requests
import time

def parse_agent_api(uploaded_file):
    """轻量版: 返回纯 Markdown 文本 (无图片/公式)"""
    base_url = "https://mineru.net/api/v1/agent"
    try:
        payload = {"file_name": uploaded_file.name, "language": "ch"}
        init_res = requests.post(f"{base_url}/parse/file", json=payload).json()
        if init_res.get("code") != 0: return None, f"获取链接失败: {init_res.get('msg')}"
        task_id, file_url = init_res["data"]["task_id"], init_res["data"]["file_url"]
        
        requests.put(file_url, data=uploaded_file.getvalue())
        for _ in range(40):
            time.sleep(3)
            poll_data = requests.get(f"{base_url}/parse/{task_id}").json()
            if poll_data.get("code") != 0: continue
            if poll_data["data"]["state"] == "done":
                md_text = requests.get(poll_data["data"]["markdown_url"]).text
                return {"type": "md", "content": md_text}, "success"
            elif poll_data["data"]["state"] == "failed":
                return None, "轻量版解析失败"
        return None, "解析超时"
    except Exception as e: return None, str(e)

def parse_pro_api(uploaded_file, token):
    """精准版: 返回 ZIP 二进制流 (包含完整图片和公式)"""
    base_url = "https://mineru.net/api/v4"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        payload = {"files": [{"name": uploaded_file.name, "data_id": "doc1"}], "model_version": "vlm"}
        init_res = requests.post(f"{base_url}/file-urls/batch", headers=headers, json=payload).json()
        if init_res.get("code") != 0: return None, f"鉴权失败: {init_res.get('msg')}"
        batch_id, file_url = init_res["data"]["batch_id"], init_res["data"]["file_urls"][0]
        
        requests.put(file_url, data=uploaded_file.getvalue())
        for _ in range(60): 
            time.sleep(4)
            poll_data = requests.get(f"{base_url}/extract-results/batch/{batch_id}", headers=headers).json()
            if poll_data.get("code") != 0: continue
            
            file_result = poll_data["data"]["extract_result"][0]
            if file_result["state"] == "done":
                # 下载完整的 ZIP 包并返回二进制流
                zip_res = requests.get(file_result["full_zip_url"])
                return {"type": "zip", "content": zip_res.content}, "success"
            elif file_result["state"] == "failed":
                return None, f"解析失败: {file_result.get('err_msg')}"
        return None, "解析超时"
    except Exception as e: return None, str(e)

import requests
import time
import zipfile
import io

def parse_agent_api(uploaded_file):
    """轻量版: <10M, <20页, 免 Token"""
    base_url = "https://mineru.net/api/v1/agent"
    try:
        payload = {"file_name": uploaded_file.name, "language": "ch", "enable_table": True, "enable_formula": True}
        init_res = requests.post(f"{base_url}/parse/file", json=payload).json()
        
        if init_res.get("code") != 0: return f"获取链接失败: {init_res.get('msg')}"
        task_id, file_url = init_res["data"]["task_id"], init_res["data"]["file_url"]
        
        put_res = requests.put(file_url, data=uploaded_file.getvalue())
        if put_res.status_code not in (200, 201): return "文件上传失败"
            
        for _ in range(60):
            time.sleep(3)
            poll_data = requests.get(f"{base_url}/parse/{task_id}").json()
            if poll_data.get("code") != 0: continue
            state = poll_data["data"]["state"]
            if state == "done":
                return requests.get(poll_data["data"]["markdown_url"]).text
            elif state == "failed":
                return f"解析失败: {poll_data['data'].get('err_msg')}"
        return "解析超时"
    except Exception as e: return f"Agent 异常: {str(e)}"

def parse_pro_api(uploaded_file, token):
    """精准版: <200M, <200页, 需 Token"""
    base_url = "https://mineru.net/api/v4"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        payload = {"files": [{"name": uploaded_file.name, "data_id": "doc1"}], "model_version": "vlm"}
        init_res = requests.post(f"{base_url}/file-urls/batch", headers=headers, json=payload).json()
        
        if init_res.get("code") != 0: return f"Pro 鉴权失败: {init_res.get('msg')}"
        batch_id = init_res["data"]["batch_id"]
        file_url = init_res["data"]["file_urls"][0]
        
        put_res = requests.put(file_url, data=uploaded_file.getvalue())
        if put_res.status_code not in (200, 201): return "Pro 文件上传失败"

        for _ in range(60): 
            time.sleep(4)
            poll_data = requests.get(f"{base_url}/extract-results/batch/{batch_id}", headers=headers).json()
            if poll_data.get("code") != 0: continue
            
            file_result = poll_data["data"]["extract_result"][0]
            state = file_result["state"]
            
            if state == "done":
                zip_url = file_result["full_zip_url"]
                z_res = requests.get(zip_url)
                with zipfile.ZipFile(io.BytesIO(z_res.content)) as z:
                    for f in z.namelist():
                        if f.endswith('.md'):
                            return z.read(f).decode('utf-8')
                return "解析成功，但未找到 Markdown 文件"
            elif state == "failed":
                return f"Pro 解析失败: {file_result.get('err_msg')}"
        return "解析耗时较长，已超时"
    except Exception as e: return f"Pro 接口异常: {str(e)}"

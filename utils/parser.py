import requests
import time
import zipfile
import io

def parse_agent_api(uploaded_file):
    url = "https://mineru.net/api/v1/agent/parse/file"
    try:
        params = {"file_name": uploaded_file.name, "model_version": "pipeline"}
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
        response = requests.post(url, params=params, files=files, timeout=60).json()
        task_id = response.get("data", {}).get("task_id")
        if not task_id: return f"解析失败: {response.get('msg')}"
        
        for _ in range(40):
            time.sleep(3)
            res = requests.get("https://mineru.net/api/v1/agent/parse/status", params={"task_id": task_id}).json()
            if res.get("data", {}).get("status") == "success":
                return res["data"].get("markdown_content") or requests.get(res["data"]["markdown_url"]).text
            if res.get("data", {}).get("status") == "failed": return "解析失败"
        return "解析超时"
    except Exception as e: return f"异常: {str(e)}"

def parse_pro_api(uploaded_file, token):
    url = "https://mineru.net/api/v4/extract/file/task"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
        data = {"file_name": uploaded_file.name, "model_version": "vlm"}
        res = requests.post(url, headers=headers, files=files, data=data, timeout=60).json()
        task_id = res.get("data", {}).get("task_id")
        if not task_id: return f"提交失败: {res.get('msg')}"
        
        for _ in range(40):
            time.sleep(3)
            res = requests.get(f"https://mineru.net/api/v4/extract/task/{task_id}", headers=headers).json()
            if res.get("data", {}).get("state") == "done":
                zip_res = requests.get(res["data"]["full_zip_url"])
                with zipfile.ZipFile(io.BytesIO(zip_res.content)) as z:
                    for f in z.namelist():
                        if f.endswith('.md'): return z.read(f).decode('utf-8')
        return "解析超时"
    except Exception as e: return f"异常: {str(e)}"

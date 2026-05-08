import requests
import time
import zipfile
import io

# ==========================================
# 模式 1：Agent 轻量解析 (无Token, <=10MB)
# ==========================================
def parse_agent_api(uploaded_file):
    base_url = "https://mineru.net/api/v1/agent"
    try:
        # 1. 申请上传 URL
        payload = {"file_name": uploaded_file.name, "language": "ch", "enable_table": True, "enable_formula": True}
        init_res = requests.post(f"{base_url}/parse/file", json=payload).json()
        
        if init_res.get("code") != 0: return f"获取上传链接失败: {init_res.get('msg')}"
        task_id, file_url = init_res["data"]["task_id"], init_res["data"]["file_url"]
        
        # 2. 上传文件
        put_res = requests.put(file_url, data=uploaded_file.getvalue())
        if put_res.status_code not in (200, 201): return "文件上传 OSS 失败"
            
        # 3. 轮询
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

# ==========================================
# 模式 2：v4 精准解析 (需Token, <=200MB)
# ==========================================
def parse_pro_api(uploaded_file, token):
    base_url = "https://mineru.net/api/v4"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        # 1. 申请批量上传 (v4必须走batch接口才能直传文件)
        payload = {
            "files": [{"name": uploaded_file.name, "data_id": "doc1"}],
            "model_version": "vlm" # 推荐的高精度模型
        }
        init_res = requests.post(f"{base_url}/file-urls/batch", headers=headers, json=payload).json()
        
        if init_res.get("code") != 0: return f"Pro 接口鉴权失败: {init_res.get('msg')}"
        batch_id = init_res["data"]["batch_id"]
        file_url = init_res["data"]["file_urls"][0]
        
        # 2. 上传文件
        put_res = requests.put(file_url, data=uploaded_file.getvalue())
        if put_res.status_code not in (200, 201): return "Pro 文件上传失败"

        # 3. 轮询 batch 结果
        for _ in range(60): # 考虑大文件，等久一点 (3分钟)
            time.sleep(3)
            poll_data = requests.get(f"{base_url}/extract-results/batch/{batch_id}", headers=headers).json()
            if poll_data.get("code") != 0: continue
            
            # 获取第一个文件的状态
            file_result = poll_data["data"]["extract_result"][0]
            state = file_result["state"]
            
            if state == "done":
                # 下载完整 ZIP 包并解压 Markdown
                zip_url = file_result["full_zip_url"]
                z_res = requests.get(zip_url)
                with zipfile.ZipFile(io.BytesIO(z_res.content)) as z:
                    for f in z.namelist():
                        if f.endswith('.md'):
                            return z.read(f).decode('utf-8')
                return "解析成功，但在 ZIP 中未找到 Markdown 文件"
            elif state == "failed":
                return f"Pro 解析失败: {file_result.get('err_msg')}"
        return "大文件解析耗时较长，轮询超时"
    except Exception as e: return f"Pro 接口异常: {str(e)}"

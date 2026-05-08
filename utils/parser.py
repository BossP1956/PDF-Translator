import requests
import time
import zipfile
import io

def parse_pdf_via_api(uploaded_file, api_key=None):
    # 优先尝试 Agent 接口 (支持直传且速度快)
    url = "https://mineru.net/api/v1/agent/parse/file"
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    
    try:
        # 1. 提交文件
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
        response = requests.post(url, headers=headers, files=files, timeout=60)
        
        # 调试：解析 JSON
        res_json = response.json()
        
        # 尝试从不同位置获取 Task ID
        # 路径1: data.task_id | 路径2: task_id (根目录)
        task_id = res_json.get("data", {}).get("task_id") or res_json.get("task_id")
        
        # --- 核心调试逻辑：如果没拿到 ID，上报服务器返回的原话 ---
        if not task_id:
            msg = res_json.get("msg") or res_json.get("message") or str(res_json)
            return f"提交成功但未获取到 ID。服务器返回: {msg}"

        # 2. 轮询状态
        # Agent 接口的状态查询路径
        status_url = "https://mineru.net/api/v1/agent/parse/status"
        
        for _ in range(40):
            time.sleep(3)
            status_res = requests.get(status_url, headers=headers, params={"task_id": task_id})
            
            if status_res.status_code != 200:
                continue
                
            status_json = status_res.json()
            res_data = status_json.get("data", {})
            status = res_data.get("status")
            
            if status == "success":
                # 尝试多种结果提取方式
                # 方式 A: 直接返回了内容
                content = res_data.get("markdown_content")
                if content: return content
                
                # 方式 B: 返回了 Zip 下载链接
                zip_url = res_data.get("full_zip_url") or res_data.get("download_url")
                if zip_url:
                    z_res = requests.get(zip_url)
                    with zipfile.ZipFile(io.BytesIO(z_res.content)) as z:
                        for f in z.namelist():
                            if f.endswith('.md'): return z.read(f).decode('utf-8')
                
                return "解析成功，但未能提取到 Markdown 文本或链接"
            
            if status == "failed":
                return f"解析失败: {res_data.get('error_msg', '未知原因')}"
        
        return "解析超时"
        
    except Exception as e:
        return f"接口连接异常: {str(e)}"

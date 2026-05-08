import requests
import time

def parse_pdf_via_api(uploaded_file, api_key=None):
    # 使用对比图右侧的 Agent 接口，支持文件上传
    # 注意：Agent 接口通常使用 v1 路径
    base_url = "https://mineru.net/api/v1/agent/parse/file"
    
    try:
        # 1. 提交文件
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
        # Agent 接口通常不需要 Authorization Header (根据对比图)
        # 但如果失效，可以保留 headers = {"Authorization": f"Bearer {api_key}"}
        
        submit_res = requests.post(base_url, files=files, timeout=60)
        
        if submit_res.status_code != 200:
            return f"Agent 接口提交失败 ({submit_res.status_code}): {submit_res.text}"
        
        res_json = submit_res.json()
        # 获取任务 ID 用于轮询
        task_id = res_json.get("data", {}).get("task_id")
        
        if not task_id:
            return f"未能获取任务ID: {res_json.get('msg')}"

        # 2. 轮询状态
        # 根据通用规范，Agent 的状态查询通常在 /agent/parse/status 或类似路径
        # 如果对比图没写，通常是 base_url 替换最后一段
        status_url = "https://mineru.net/api/v1/agent/parse/status"
        
        for _ in range(30):
            time.sleep(3)
            status_res = requests.get(status_url, params={"task_id": task_id})
            if status_res.status_code != 200: continue
            
            status_data = status_res.json().get("data", {})
            status = status_data.get("status")
            
            if status == "success":
                # Agent 接口通常直接在数据里返回 markdown_content 或一个 md 链接
                content = status_data.get("markdown_content")
                if content:
                    return content
                
                # 如果返回的是链接，则下载它
                md_url = status_data.get("markdown_url")
                if md_url:
                    return requests.get(md_url).text
                    
                return "解析成功但未提取到文本"
            
            if status == "failed":
                return "Agent 解析失败"
                
        return "解析超时"
        
    except Exception as e:
        return f"Agent 接口异常: {str(e)}"

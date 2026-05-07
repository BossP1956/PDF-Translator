import requests
import time

def parse_pdf_via_api(uploaded_file, api_key):
    # 根据官方文档，确保 URL 是准确的。
    # 提示：有时末尾有没有斜杠 / 也会影响返回格式
    base_url = "https://mineru.net/api/v1"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        # 1. 提交任务
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
        submit_res = requests.post(f"{base_url}/extract", headers=headers, files=files, timeout=60)
        
        # 调试：检查返回是否为 JSON
        try:
            submit_data = submit_res.json()
        except Exception:
            return f"API 提交阶段返回了非 JSON 内容: {submit_res.text[:100]}"

        if submit_res.status_code != 200:
            return f"提交失败 ({submit_res.status_code}): {submit_data.get('msg', '未知错误')}"
        
        task_id = submit_data.get("data", {}).get("task_id")
        if not task_id:
            return "解析失败：未能从返回数据中提取 task_id"

        # 2. 轮询状态
        for _ in range(40):
            time.sleep(3)
            status_res = requests.get(f"{base_url}/task-status", headers=headers, params={"task_id": task_id})
            
            # 同样增加 JSON 安全解析
            try:
                status_data = status_res.json()
            except Exception:
                # 有时 API 在处理中会返回纯文本 "processing"，这里做个兼容
                continue
                
            res_inner = status_data.get("data", {})
            status = res_inner.get("status")
            
            if status == "success":
                # 核心点：MinerU 有时将结果放在 markdown_content，有时在别的字段
                content = res_inner.get("markdown_content")
                return content if content else "解析成功但未提取到文本内容"
            
            if status == "failed":
                return f"MinerU 云端解析失败: {res_inner.get('error_msg', '原因未知')}"
        
        return "解析超时：文件解析时间过长，请稍后再试"
        
    except Exception as e:
        return f"解析过程发生程序异常: {str(e)}"

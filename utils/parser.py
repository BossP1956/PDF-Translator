import requests
import time
import zipfile
import io

def parse_pdf_via_api(uploaded_file, api_key):
    # 根据截图更新为 v4 接口
    base_url = "https://mineru.net/api/v4"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        # 1. 提交任务 (接口: /extract/task)
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
        # 精准解析模式通常可以带一些参数，这里保持默认
        submit_res = requests.post(f"{base_url}/extract/task", headers=headers, files=files, timeout=60)
        
        if submit_res.status_code != 200:
            return f"提交失败 ({submit_res.status_code}): {submit_res.text}"
        
        task_id = submit_res.json().get("data", {}).get("task_id")
        if not task_id:
            return "解析失败：未获取到任务 ID"

        # 2. 轮询任务状态
        # 根据 v4 规范，查询接口通常是 /extract/task/{task_id}
        status_url = f"{base_url}/extract/task/{task_id}"
        
        for _ in range(50): # 最多等待 150 秒
            time.sleep(3)
            status_res = requests.get(status_url, headers=headers)
            if status_res.status_code != 200: continue
            
            res_data = status_res.json().get("data", {})
            status = res_data.get("status")
            
            if status == "success":
                # 3. 获取下载链接并解压提取 Markdown
                # v4 成功后会返回 full_zip_url
                zip_url = res_data.get("full_zip_url")
                if not zip_url:
                    return "解析成功，但未找到结果下载链接"
                
                # 下载 Zip 包内容
                zip_res = requests.get(zip_url)
                with zipfile.ZipFile(io.BytesIO(zip_res.content)) as z:
                    # 遍历压缩包，寻找 .md 后缀的文件
                    for file_info in z.infolist():
                        if file_info.filename.endswith('.md'):
                            with z.open(file_info) as f:
                                return f.read().decode('utf-8')
                return "解析成功，但在结果包中未找到 Markdown 文件"
            
            if status == "failed":
                return f"MinerU 解析失败: {res_data.get('error_msg')}"
                
        return "解析超时"
        
    except Exception as e:
        return f"程序异常: {str(e)}"

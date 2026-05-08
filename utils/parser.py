import requests
import time

def parse_pdf_via_api(uploaded_file):
    """
    按照 MinerU 官方文档的 3步法(签名上传) 解析文件
    """
    base_url = "https://mineru.net/api/v1/agent"
    
    try:
        # ==========================================
        # 第一步：申请签名上传 URL
        # ==========================================
        # 提取文件名
        file_name = uploaded_file.name
        
        payload = {
            "file_name": file_name,
            "language": "ch",          # 默认中文
            "enable_table": True,      # 开启表格识别
            "is_ocr": False,           # Agent 模式默认为 False
            "enable_formula": True     # 开启公式识别
        }
        
        # 发送 JSON 请求获取上传链接
        init_res = requests.post(f"{base_url}/parse/file", json=payload)
        init_data = init_res.json()
        
        if init_data.get("code") != 0:
            return f"获取上传链接失败: {init_data.get('msg')}"
            
        task_id = init_data["data"]["task_id"]
        file_url = init_data["data"]["file_url"]
        
        # ==========================================
        # 第二步：将文件流 PUT 到 OSS
        # ==========================================
        # 使用 getvalue() 获取文件的 bytes 二进制流
        put_res = requests.put(file_url, data=uploaded_file.getvalue())
        if put_res.status_code not in (200, 201):
            return f"文件上传 OSS 失败, 状态码: {put_res.status_code}"
            
        # ==========================================
        # 第三步：轮询等待结果
        # ==========================================
        timeout = 180  # 最长等待 3 分钟
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            time.sleep(3) # 每3秒查一次
            
            poll_res = requests.get(f"{base_url}/parse/{task_id}")
            poll_data = poll_res.json()
            
            if poll_data.get("code") != 0:
                continue
                
            state = poll_data["data"]["state"]
            
            if state == "done":
                # 解析完成，获取 markdown 下载链接
                md_url = poll_data["data"]["markdown_url"]
                # 直接读取并返回 md 文本
                md_text = requests.get(md_url).text
                return md_text
                
            elif state == "failed":
                err_msg = poll_data["data"].get("err_msg", "未知错误")
                return f"解析失败: {err_msg}"
                
            # 其他状态如 "waiting-file", "pending", "running" 继续循环
            
        return "解析超时，请稍后再试或检查文件是否过大"
        
    except Exception as e:
        return f"系统调用异常: {str(e)}"

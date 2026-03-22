import requests
import base64
import os

# 配置本地 API 地址
URL = "http://127.0.0.1:8000/webhook"
# 指向你 templates 文件夹下的简历图片
IMG_PATH = "templates/resume1.png" 

def run_test():
    if not os.path.exists(IMG_PATH):
        print(f"错误: 找不到文件 {IMG_PATH}")
        return

    # 1. 将图片转换为 Base64 字符串
    with open(IMG_PATH, "rb") as f:
        img_base64 = base64.b64encode(f.read()).decode('utf-8')

    # 2. 构造模拟数据包
    payload = {
        "email": "li.z30@northeastern.edu", # 建议改为你的真实接收邮箱进行测试
        "first_name": "Jenny",
        "last_name": "Student",
        "college": "Khoury College",
        "major": "MS in AI",
        "enrollment_semester": "2024sp",
        "languages": "English,Mandarin",
        "cultural_background": "East Asian",
        "availability": "weekday_evening",
        "cv_base64": img_base64,
        "type": "requester", 
        "intent": "request_interview",
        "target_company": "Google",
        "role": "Software Engineer Intern",
        "focus_area": "Machine Learning",
        "interview_availability": "Mon 7pm, Tue 8pm, Thu 6pm"
    }

    print(f"正在向 {URL} 发送测试数据包并触发视觉解析...")
    
    try:
        response = requests.post(URL, json=payload)
        print(f"服务器响应状态码: {response.status_code}")
        print(f"服务器返回内容: {response.json()}")
        print("\n--- 请查看 Uvicorn 终端，确认解析、匹配及 SendGrid 邮件日志 ---")
        
    except Exception as e:
        print(f"发送失败: {e}")

if __name__ == "__main__":
    run_test()
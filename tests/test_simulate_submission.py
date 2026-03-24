import requests
import base64
import time
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# 配置参数：建议使用 127.0.0.1 避免某些系统上 localhost 解析慢的问题
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
WEBHOOK_URL = f"{BASE_URL}/api/v1/webhook"
HEALTH_URL = f"{BASE_URL}/api/v1/health"

def check_server_status():
    """检查 FastAPI 服务器是否已启动"""
    try:
        response = requests.get(HEALTH_URL, timeout=2)
        if response.status_code == 200:
            print(f"✅ 服务器在线 ({BASE_URL})")
            return True
    except Exception:
        print(f"❌ 错误: 无法连接到服务器 {BASE_URL}")
        print("请确保你已经运行了: uvicorn main:app --reload")
        return False

def simulate_student_submission():
    """
    模拟学生提交简历的流程
    """
    if not check_server_status():
        return

    print("\n--- 步骤 1: 模拟学生提交简历 ---")
    
    # 构造一个简单的 PDF Base64 字符串
    # 提示：你可以替换为真实的 base64 数据进行更深度的 AI 解析测试
    dummy_pdf_b64 = "JVBERi0xLjEKMSAwIG9iajw8L1R5cGUvQ2F0YWxvZy9QYWdlcyAyIDAgUj4+ZW5kb2JqIDIgMCBvYmo8PC9UeXBlL1BhZ2VzL0NvdW50IDEvS2lkc1szIDAgUl0+PmVuZG9iaiAzIDAgb2JqPDwvVHlwZS9QYWdlL1BhcmVudCAyIDAgUi9NZWRpYUJveFswIDAgNjEyIDc5Ml0vQ29udGVudHMgNCAwIFI+PmVuZG9iaiA0IDAgb2JqPDwvTGVuZ3RoIDQ0Pj5zdHJlYW0KQlQKL0YxIDI0IFRmCjcwIDcwMCBUZAooSGVsbG8gV29ybGQpIFRqCkVUCmVuZHN0cmVhbQplbmRvYmoKeHJlZgowIDUKMDAwMDAwMDAwMCA2NTUzNSBmIAowMDAwMDAwMDE4IDAwMDAwIG4gCjAwMDAwMDAwNzcgMDAwMDAgbiAKMDAwMDAwMDEyMiAwMDAwMCBuIAowMDAwMDAwMjI5IDAwMDAwIG4gCnRyYWlsZXI8PC9TaXplIDUvUm9vdCAxIDAgUj4+CnN0YXJ0eHJlZgozMjIKJSVFT0Y="

    payload = {
        "email": "student_test@example.com", # 接收通知的测试邮箱
        "first_name": "Test",
        "last_name": "Student",
        "major": "MS in AI",
        "college": "Khoury",
        "enrollment": "Fall 2025",
        "intent": "I want a mock interview (and I'll join the interviewer pool)",
        "cv_base64": dummy_pdf_b64,
        "target_company": "Google",
        "role": "Software Engineer",
        "focus_area": "Machine Learning",
        "slot_1": "2026-04-01T10:00:00",
        "pref_interviewer_bg": "Technical"
    }

    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        if response.status_code == 200:
            print("✅ Webhook 接收成功！")
            print("正在处理 AI 解析和匹配，请观察服务器控制台日志...")
        else:
            print(f"❌ 提交失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 提交请求时发生错误: {e}")

def verify_db_status():
    """
    提示用户去数据库检查
    """
    print("\n--- 步骤 2: 数据库与邮件校验 ---")
    print("1. 请前往 Supabase Dashboard 检查 'users' 表是否更新了 student_test@example.com 的数据。")
    print("2. 检查 'requests' 表是否生成了状态为 'pending' 的新请求。")
    print("3. 检查你的面试官邮箱（如果在池中已存在）是否收到了邀请邮件。")
    print("4. 找到邮件中的 URL: /api/v1/accept?req_id=xxx&intv_id=yyy 并访问它。")

if __name__ == "__main__":
    simulate_student_submission()
    verify_db_status()
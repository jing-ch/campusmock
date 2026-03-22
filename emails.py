import os
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# 获取 API Key
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
sg = SendGridAPIClient(SENDGRID_API_KEY)

# 统一发件人为已验证的邮箱
FROM_EMAIL = 'li.z30@northeastern.edu'

def send_match_invitation_email(interviewer_email: str, requester_major: str, accept_url: str):
    """发送匹配邀请 (英文版，中文注释)"""
    subject = "[CampusMock] New Mock Interview Invitation"
    content = f"""
    Hi there,
    
    A student from the {requester_major} program has requested a mock interview. 
    Based on your background, you are a great match!
    
    If you are available to help, please click the link below to accept this request:
    {accept_url}
    
    Best regards,
    CampusMock Team
    """
    
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=interviewer_email,
        subject=subject,
        plain_text_content=content
    )
    
    try:
        logger.info(f"Attempting to send invitation to {interviewer_email}...")
        response = sg.send(message) 
        # 打印状态码，202 表示 SendGrid 已接受请求 [cite: 2026-03-21]
        logger.info(f"SendGrid Success: Status Code {response.status_code}")
    except Exception as e:
        logger.error(f"SendGrid API Error: {e}")

def send_confirmation_email(requester_email: str, interviewer_name: str):
    """发送匹配成功确认"""
    subject = "[CampusMock] Match Successful!"
    content = f"Your mock interview request has been accepted by {interviewer_name}."
    
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=requester_email,
        subject=subject,
        plain_text_content=content
    )
    try:
        response = sg.send(message)
        logger.info(f"Confirmation sent! Status: {response.status_code}")
    except Exception as e:
        logger.error(f"Confirmation error: {e}")

def send_timeout_notification(requester_email: str):
    """发送 48 小时超时提醒"""
    subject = "[CampusMock] Update on your Interview Request"
    content = "We have assigned a specialized AI Interview Agent for you."
    
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=requester_email,
        subject=subject,
        plain_text_content=content
    )
    try:
        response = sg.send(message)
        logger.info(f"Timeout email sent! Status: {response.status_code}")
    except Exception as e:
        logger.error(f"Timeout error: {e}")
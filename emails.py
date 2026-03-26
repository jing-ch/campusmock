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
FROM_EMAIL = os.getenv('FROM_EMAIL', 'example@northeastern.edu')

def send_interviewer_pool_confirmation(interviewer_email: str):
    """Post-submit email for interviewer-only users."""
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=interviewer_email,
        subject="[CampusMock] You're in the pool! 🎉",
        plain_text_content=(
            "Hi there,\n\n"
            "You're in the pool — thank you for paying it forward! We'll reach out when someone needs you.\n\n"
            "— CampusMock Team"
        ),
    )
    try:
        response = sg.send(message)
        logger.info(f"Pool confirmation sent to {interviewer_email}: {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to send pool confirmation to {interviewer_email}: {e}")


def send_requester_queue_confirmation(requester_email: str):
    """Post-submit email for requesters."""
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=requester_email,
        subject="[CampusMock] We're on it! Finding your match 🔍",
        plain_text_content=(
            "Hi there,\n\n"
            "You're in the queue — we're finding your best match right now. We'll email you as soon as someone accepts. Fingers crossed 🤞\n\n"
            "— CampusMock Team"
        ),
    )
    try:
        response = sg.send(message)
        logger.info(f"Queue confirmation sent to {requester_email}: {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to send queue confirmation to {requester_email}: {e}")


def send_match_invitation_email(interviewer_email: str, requester_major: str, accept_url: str):
    """发送匹配邀请 (英文版，中文注释)"""
    subject = "[CampusMock] Someone needs your help — mock interview request 👋"
    content = (
        "Hi there,\n\n"
        f"A fellow {requester_major} student is looking for a mock interviewer and you look like a great match! Click below to accept:\n\n"
        f"{accept_url}\n\n"
        "— CampusMock Team"
    )
    
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

def send_confirmation_email(requester_email: str, interviewer_name: str, interviewer_email: str):
    """发送匹配成功确认"""
    subject = "[CampusMock] You've got a match! 🙌"
    content = (
        "Hi there,\n\n"
        f"{interviewer_name} has agreed to mock interview you! Reach out to them at {interviewer_email} to set up a video call. Good luck 💪\n\n"
        "— CampusMock Team"
    )
    
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
    subject = "[CampusMock] We couldn't find a match this time 😔"
    content = (
        "Hi there,\n\n"
        "No one was available this time around — but don't give up! More interviewers are joining every day. Feel free to submit again anytime.\n\n"
        "— CampusMock Team"
    )
    
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

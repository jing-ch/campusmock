import base64
import logging
import os
from fastapi import APIRouter, BackgroundTasks, Request

from cv_parser import parse_cv
from db import upsert_user, insert_request, get_interviewer_pool
from emails import (
    send_interviewer_pool_confirmation, 
    send_requester_queue_confirmation,
    send_match_invitation_email
)
from matching import find_best_matches
from models import UserUpsert, RequestInsert

router = APIRouter()
logger = logging.getLogger(__name__)

# 定义学生申请的意图字符串
REQUESTER_INTENT = "I want a mock interview (and I'll join the interviewer pool)"

async def _process_submission(payload: dict):
    """
    后台处理逻辑：解析 CV -> 存入数据库 -> 触发匹配 -> 发送邀请
    """
    is_requester = payload.get("intent") == REQUESTER_INTENT
    email = payload.get("email", "")
    major = payload.get("major", "")

    # 1. AI 解析逻辑：PDF -> PNG -> 结构化 JSON
    cv_pdf = payload.get("cv_base64")
    cv_parsed = None

    if cv_pdf:
        try:
            pdf_bytes = base64.b64decode(cv_pdf)
            cv_parsed = parse_cv(pdf_bytes)
            if cv_parsed:
                logger.info(f"CV parsed successfully for {email}")
            else:
                logger.warning(f"CV parsing failed for {email} - using fallback")
        except Exception as e:
            logger.error(f"Error during CV processing: {e}")

    # 2. 数据库持久化：保存/更新用户信息
    user = UserUpsert(
        email=email,
        first_name=payload.get("first_name", ""),
        last_name=payload.get("last_name", ""),
        college=payload.get("college", ""),
        major=major,
        enrollment_semester=payload.get("enrollment", ""),
        cultural_background=payload.get("cultural_background", ""),
        availability=payload.get("availability", ""),
        user_type="requester" if is_requester else "interviewer_only",
        cv_pdf=cv_pdf,
        cv_parsed=cv_parsed,
    )
    user_row = upsert_user(user)
    
    # 3. 处理学生面试请求
    if is_requester:
        # 3a. 插入请求记录并获取请求 ID
        req_data = RequestInsert(
            requester_id=user_row["id"],
            target_company=payload.get("target_company"),
            role_title=payload.get("role"),
            focus_area=payload.get("focus_area"),
            slot_1=payload.get("slot_1"),
            slot_2=payload.get("slot_2"),
            slot_3=payload.get("slot_3"),
            pref_cultural_bg=payload.get("pref_interviewer_bg"),
        )
        req_row = insert_request(req_data)
        logger.info(f"New request {req_row['id']} created for {email}")

        # 3b. 自动撮合流程：从数据库加载面试官池
        interviewer_pool = get_interviewer_pool()
        
        # 3c. 执行匹配算法获取 Top 3
        # 构造匹配所需的申请人元数据
        requester_meta = {"major": major, "email": email}
        matches = find_best_matches(requester_meta, interviewer_pool)
        
        # 3d. 遍历匹配结果，发送邀请邮件
        base_url = os.environ.get("BASE_URL", "http://localhost:8000")
        for intv in matches:
            if intv.get("is_ai"):
                continue # AI 兜底逻辑由 cron.py 在 48h 后触发
            
            # 构造面试官专属的抢单链接
            accept_url = f"{base_url}/api/v1/accept?req_id={req_row['id']}&intv_id={intv['id']}"
            
            # 发送 SendGrid 邮件
            # 注意：如果面试官在数据库中没有邮箱，这里需要根据业务逻辑处理，此处假设已获取
            intv_email = intv.get("email") # 确保 db.get_interviewer_pool 返回了 email 字段
            if intv_email:
                send_match_invitation_email(intv_email, major, accept_url)
                logger.info(f"Invitation sent to interviewer {intv['id']} for request {req_row['id']}")

        # 3e. 发送申请确认邮件给学生
        send_requester_queue_confirmation(email)
    else:
        # 如果只是加入面试官池，发送加入成功的通知
        send_interviewer_pool_confirmation(email)

@router.post("/webhook")
async def handle_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Webhook 入口：快速返回成功，后台异步处理复杂逻辑
    """
    payload = await request.json()
    background_tasks.add_task(_process_submission, payload)
    return {"status": "ok", "message": "Submission received and is being processed."}
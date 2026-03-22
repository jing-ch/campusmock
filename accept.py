from fastapi import APIRouter, HTTPException, Query
import threading
import logging
from emails import send_confirmation_email  # 导入确认邮件函数

router = APIRouter()
logger = logging.getLogger(__name__)

# --- 模拟内存数据库与原子锁 ---
# 线程锁：确保状态变更的排他性 [cite: 2026-03-21]
match_lock = threading.Lock()
# 存储已成功领取的 request_id: interviewer_id 映射 [cite: 2026-03-21]
claimed_matches = {}

@router.get("/accept")
async def accept_interview(
    req_id: str = Query(..., description="The ID of the interview request"),
    intv_id: str = Query(..., description="The ID of the interviewer")
):
    """
    处理面试官点击邮件链接后的抢单逻辑 (Handle interviewer claim logic)
    中文注释：利用原子锁确保‘先到先得’。 [cite: 2026-03-21]
    """
    logger.info(f"Interviewer {intv_id} attempting to claim request {req_id}")

    with match_lock: # 进入原子保护区 [cite: 2026-03-21]
        # 1. 检查是否已被领取 [cite: 2026-03-21]
        if req_id in claimed_matches:
            already_claimed_by = claimed_matches[req_id]
            logger.warning(f"Request {req_id} already claimed by {already_claimed_by}")
            return {
                "status": "fail",
                "message": "Sorry, this interview request has already been claimed by another peer."
            }

        # 2. 执行抢单操作 [cite: 2026-03-21]
        claimed_matches[req_id] = intv_id
        logger.info(f"Success! Request {req_id} assigned to {intv_id}")

    # 3. 成功后触发给学生的确认邮件
    # 临时开发阶段：假设学生的邮箱是你的测试邮箱 [cite: 2026-03-21]
    student_test_email = "li.z30@northeastern.edu" 
    send_confirmation_email(student_test_email, f"Interviewer_{intv_id}")

    return {
        "status": "success",
        "message": f"Confirmation successful! We have notified the student. Please check your calendar."
    }
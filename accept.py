import logging
from fastapi import APIRouter, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from db import get_request_by_id, update_request_status, get_user_by_id
from emails import send_confirmation_email

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/accept")
async def accept_request(
    background_tasks: BackgroundTasks,
    req_id: str = Query(..., description="申请 ID"),
    intv_id: str = Query(..., description="面试官 ID")
):
    """
    处理面试官抢单逻辑。
    增加了幂等性校验，防止邮件客户端自动预访问导致的逻辑失效。
    """
    logger.info(f"--- [抢单尝试] 请求: {req_id} | 面试官: {intv_id} ---")

    # 1. 获取请求详情
    request_data = get_request_by_id(req_id)
    if not request_data:
        return JSONResponse(
            status_code=404,
            content={"status": "fail", "message": "无效链接：找不到该请求。"}
        )

    # --- 关键修改：增加幂等性检查 ---
    # 如果链接已经被点击过（或被邮件系统预检），但领取人正是当前面试官，直接返回成功
    current_status = request_data.get("status")
    current_interviewer = request_data.get("interviewer_id")

    if current_status == "accepted" and current_interviewer == intv_id:
        logger.info(f"幂等成功：面试官 {intv_id} 已拥有该请求 {req_id}")
        return {
            "status": "success",
            "message": "You have already claimed this request! Please check your email for student details."
        }

    # 2. 状态校验：是否已被其他人抢走
    if current_status != "pending" or current_interviewer is not None:
        logger.warning(f"请求 {req_id} 已被他人抢占。")
        return {
            "status": "fail",
            "message": "Sorry, this interview request has already been claimed by another peer."
        }

    # 3. 执行原子化更新
    try:
        interviewer = get_user_by_id(intv_id)
        interviewer_name = interviewer.get("first_name", "A Peer") if interviewer else "A Peer"

        # 仅在状态为 pending 时尝试更新
        success = update_request_status(req_id, "accepted", intv_id)
        
        if success:
            logger.info(f"✅ 抢单成功: {req_id} 被 {intv_id} 领取")
            
            # 4. 异步发送通知
            student_email = request_data.get("email") 
            if student_email:
                background_tasks.add_task(send_confirmation_email, student_email, interviewer_name)
            
            return {
                "status": "success",
                "message": "Claim successful! You have been assigned to this interview."
            }
        else:
            return {
                "status": "fail", 
                "message": "Failed to claim. The request might have just been taken by someone else."
            }

    except Exception as e:
        logger.error(f"抢单过程异常: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})
import base64
import logging
from fastapi import APIRouter, BackgroundTasks, Request, HTTPException
from cv_parser import ClaudeCVParser 
from matching import find_best_matches 
# 导入邮件发送函数
from emails import send_match_invitation_email 
from fastapi import APIRouter, Request

from db import upsert_user, insert_request
from models import UserUpsert, RequestInsert

router = APIRouter()
logger = logging.getLogger(__name__)

feature/jenny
parser = ClaudeCVParser()

# 模拟面试官池
MOCK_INTERVIEWER_POOL = [
    {
        "id": "intv_001", 
        "first_name": "Senior", 
        "major": "Computer Science", 
        "has_detailed_cv": True, 
        "experience_years": 10 
    },
    {
        "id": "intv_002", 
        "first_name": "Peer", 
        "major": "Artificial Intelligence", 
        "has_detailed_cv": False, 
        "experience_years": 1 
    }
]

async def background_process_submission(payload: dict):
    email = payload.get("email")
    req_major = payload.get("major")
    
    try:
        # 1. 视觉解析简历
        cv_base64 = payload.get("cv_base64")
        img_bytes = base64.b64decode(cv_base64)
        cv_structured_data = parser.parse_image(img_bytes) 
        
        logger.info(f"--- [STEP 1: 解析] 用户 {email} 解析完成 ---")
        
        # 2. 执行匹配逻辑
        matches = find_best_matches(payload, MOCK_INTERVIEWER_POOL)
        
        logger.info(f"--- [STEP 2: 匹配结果] ---")
        for i, m in enumerate(matches, 1):
            is_ai = m.get("is_ai", False)
            type_str = "AI Agent" if is_ai else "真人面试官"
            logger.info(f"Top {i} ({type_str}): ID={m['id']}, 专业={m['major']}, 匹配分={m.get('match_score', 'N/A')}")
            
            # --- 核心修复：触发邮件发送 ---
            if not is_ai:
                # 生产环境此 email 应从数据库读取，目前使用你的测试邮箱 [cite: 2026-03-21]
                test_receiver = "jennyjingjing525@gmail.com" 
                # 构造模拟接受链接 [cite: 2026-03-21]
                accept_url = f"http://127.0.0.1:8000/accept?req_id=test_{m['id']}"
                
                send_match_invitation_email(
                    interviewer_email=test_receiver,
                    requester_major=req_major,
                    accept_url=accept_url
                )
        
        logger.info(f"--- [提示] 匹配与邮件发起流程结束 ---")

    except Exception as e:
        logger.error(f"Error in background task for {email}: {e}")

@router.post("/webhook")
async def handle_submission(request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json()
        if not data.get("email") or not data.get("cv_base64"):
            raise HTTPException(status_code=400, detail="Missing data")

        background_tasks.add_task(background_process_submission, data)
        return {"received": True, "status": "processing"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"received": False, "error": str(e)}
=======
REQUESTER_INTENT = "I want a mock interview (and I'll join the interviewer pool)"


@router.post("/webhook")
async def handle_webhook(request: Request):
    payload = await request.json()
    print("Received webhook payload:", payload)

    is_requester = payload.get("intent") == REQUESTER_INTENT

    name_parts = payload.get("name", "").split(None, 1)
    first_name = name_parts[0] if name_parts else ""
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    if is_requester:
        email = payload.get("email_s2", "")
        cultural_background = payload.get("cultural_background_s2", "")
        availability = payload.get("availability_s2", "")
    else:
        email = payload.get("email_s3", "")
        cultural_background = payload.get("cultural_background_s3", "")
        availability = payload.get("availability_s3", "")

    user = UserUpsert(
        email=email,
        first_name=first_name,
        last_name=last_name,
        college=payload.get("college", ""),
        major=payload.get("major", ""),
        enrollment_semester=payload.get("enrollment", ""),
        cultural_background=cultural_background,
        availability=availability,
        role="requester" if is_requester else "interviewer_only",
        cv_parsed=None,
    )
    user_row = upsert_user(user)

    if is_requester:
        req = RequestInsert(
            requester_id=user_row["id"],
            target_company=payload.get("target_company"),
            role_title=payload.get("role"),
            focus_area=payload.get("focus_area"),
            slot_1=payload.get("slot_1", ""),
            slot_2=payload.get("slot_2", ""),
            slot_3=payload.get("slot_3", ""),
            pref_cultural_bg=payload.get("pref_interviewer_bg"),
        )
        insert_request(req)

    return {"status": "ok"}

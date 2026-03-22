import base64
import logging
from fastapi import APIRouter, BackgroundTasks, Request

from cv_parser import parse_cv
from db import upsert_user, insert_request
from emails import send_interviewer_pool_confirmation, send_requester_queue_confirmation
from models import UserUpsert, RequestInsert

router = APIRouter()
logger = logging.getLogger(__name__)

REQUESTER_INTENT = "I want a mock interview (and I'll join the interviewer pool)"


async def _process_submission(payload: dict):
    is_requester = payload.get("intent") == REQUESTER_INTENT

    if is_requester:
        email = payload.get("email_s2", "")
        cultural_background = payload.get("cultural_background_s2", "")
        availability = payload.get("availability_s2", "")
    else:
        email = payload.get("email_s3", "")
        cultural_background = payload.get("cultural_background_s3", "")
        availability = payload.get("availability_s3", "")

    # 1. PDF → PNG (in memory) → cv_parsed JSON
    #    Keep original PDF base64 as fallback in case Claude fails
    cv_pdf = payload.get("cv_base64")  # original PDF, stored as fallback
    cv_parsed = None

    if cv_pdf:
        pdf_bytes = base64.b64decode(cv_pdf)
        cv_parsed = parse_cv(pdf_bytes)
        if cv_parsed:
            logger.info(f"CV parsed successfully for {email}")
        else:
            logger.warning(f"CV parsing failed for {email} — PDF stored as fallback")

    # 2. Upsert user
    name_parts = payload.get("name", "").split(None, 1)
    user = UserUpsert(
        email=email,
        first_name=name_parts[0] if name_parts else "",
        last_name=name_parts[1] if len(name_parts) > 1 else "",
        college=payload.get("college", ""),
        major=payload.get("major", ""),
        enrollment_semester=payload.get("enrollment", ""),
        cultural_background=cultural_background,
        availability=availability,
        role="requester" if is_requester else "interviewer_only",
        cv_pdf=cv_pdf,
        cv_parsed=cv_parsed,
    )
    user_row = upsert_user(user)
    logger.info(f"User upserted: {email} (id={user_row['id']})")

    # 3. Insert request + send confirmation email
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
        logger.info(f"Request inserted for {email}")
        send_requester_queue_confirmation(email)
    else:
        send_interviewer_pool_confirmation(email)


@router.post("/webhook")
async def handle_webhook(request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()
    background_tasks.add_task(_process_submission, payload)
    return {"status": "ok"}

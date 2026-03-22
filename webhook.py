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

    email = payload.get("email", "")
    cultural_background = payload.get("cultural_background", "")
    availability = payload.get("availability", "")

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
    user = UserUpsert(
        email=email,
        first_name=payload.get("first_name", ""),
        last_name=payload.get("last_name", ""),
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
            slot_1=payload.get("slot_1"),
            slot_2=payload.get("slot_2"),
            slot_3=payload.get("slot_3"),
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

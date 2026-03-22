from fastapi import APIRouter, Request

from db import upsert_user, insert_request
from models import UserUpsert, RequestInsert

router = APIRouter()

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
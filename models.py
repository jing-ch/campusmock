from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class UserUpsert(BaseModel):
    email: str
    first_name: str
    last_name: str
    college: str
    major: str
    enrollment_semester: str
    cultural_background: str
    availability: str
    user_type: str  # "requester" | "interviewer_only"
    languages: Optional[str] = None
    cv_pdf: Optional[str] = None    # base64-encoded original PDF, kept as fallback
    cv_parsed: Optional[dict] = None  # structured JSON parsed from CV by Claude


class RequestInsert(BaseModel):
    requester_id: str
    target_company: Optional[str] = None
    role_title: Optional[str] = None
    focus_area: Optional[str] = None
    slot_1: Optional[datetime] = None
    slot_2: Optional[datetime] = None
    slot_3: Optional[datetime] = None
    pref_cultural_bg: Optional[str] = None

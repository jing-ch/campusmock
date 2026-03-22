from typing import Optional
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
    role: str  # "requester" | "interviewer_only"
    languages: Optional[str] = None
    cv_parsed: Optional[dict] = None


class RequestInsert(BaseModel):
    requester_id: str
    target_company: Optional[str] = None
    role_title: Optional[str] = None
    focus_area: Optional[str] = None
    slot_1: str
    slot_2: str
    slot_3: str
    pref_cultural_bg: Optional[str] = None

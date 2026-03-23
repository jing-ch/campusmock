"""
Run with:
    pip install pytest
    pytest test_webhook.py -v
"""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from main import app
from db import _get_client, upsert_user, insert_request
from models import UserUpsert, RequestInsert

client = TestClient(app)

TEST_EMAIL = "test_integration@northeastern.edu"

DUMMY_USER = UserUpsert(
    email=TEST_EMAIL,
    first_name="Test",
    last_name="User",
    college="Khoury College",
    major="Computer Science",
    enrollment_semester="2024 Spring",
    cultural_background="East Asian",
    availability="weekday_evening",
    user_type="requester",
)

PARSED_SLOTS = [
    "2026-01-27T18:00:00-08:00",
    "2026-01-29T19:00:00-08:00",
    "2026-02-01T14:00:00-08:00",
]


@pytest.fixture(autouse=True)
def cleanup():
    yield
    db = _get_client()
    user_rows = db.table("users").select("id").eq("email", TEST_EMAIL).execute().data
    if user_rows:
        db.table("requests").delete().eq("requester_id", user_rows[0]["id"]).execute()
    db.table("users").delete().eq("email", TEST_EMAIL).execute()


def test_upsert_user():
    row = upsert_user(DUMMY_USER)
    assert row["email"] == TEST_EMAIL
    assert row["user_type"] == "requester"


def test_insert_request():
    user_row = upsert_user(DUMMY_USER)
    req = RequestInsert(
        requester_id=user_row["id"],
        target_company="Google",
        role_title="SWE Intern",
        focus_area="LeetCode",
        slot_1=PARSED_SLOTS[0],
        slot_2=PARSED_SLOTS[1],
        slot_3=PARSED_SLOTS[2],
    )
    row = insert_request(req)
    assert row["status"] == "pending"
    assert row["target_company"] == "Google"


def test_webhook_returns_200():
    with patch("webhook.parse_cv", return_value=None), \
         patch("webhook.send_requester_queue_confirmation"):
        response = client.post("/api/v1/webhook", json={
            "intent": "I want a mock interview (and I'll join the interviewer pool)",
            "first_name": "Test",
            "last_name": "User",
            "college": "Khoury College",
            "major": "Computer Science",
            "enrollment": "2024 Spring",
            "email": TEST_EMAIL,
            "cultural_background": "East Asian",
            "availability": "weekday_evening",
            "target_company": "Google",
            "role": "SWE Intern",
            "focus_area": "LeetCode",
            "slot_1": "2026-01-27T18:00:00-08:00",
            "slot_2": "2026-01-29T19:00:00-08:00",
            "slot_3": "2026-02-01T14:00:00-08:00",
        })
        assert response.status_code == 200

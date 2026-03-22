import os
from datetime import datetime, timezone, timedelta

from supabase import create_client, Client
from dotenv import load_dotenv

from models import UserUpsert, RequestInsert

load_dotenv()

_client: Client | None = None


def _get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(
            os.environ["SUPABASE_URL"],
            os.environ["SUPABASE_SERVICE_KEY"],
        )
    return _client


def upsert_user(user: UserUpsert) -> dict:
    row = user.model_dump(exclude_none=True)
    row["updated_at"] = datetime.now(timezone.utc).isoformat()

    result = (
        _get_client().table("users")
        .upsert(row, on_conflict="email")
        .execute()
    )
    return result.data[0]


def insert_request(req: RequestInsert) -> dict:
    now = datetime.now(timezone.utc)
    row = req.model_dump(exclude_none=True)
    row["status"] = "pending"
    row["expires_at"] = (now + timedelta(hours=48)).isoformat()
    row["created_at"] = now.isoformat()

    result = (
        _get_client().table("requests")
        .insert(row)
        .execute()
    )
    return result.data[0]

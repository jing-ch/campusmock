# Handles incoming Google Apps Script form submission webhooks.
from fastapi import APIRouter

router = APIRouter()


@router.post("/webhook")
def webhook():
    return {"received": True}

from fastapi import APIRouter, Request
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/webhook")
async def handle_webhook(request: Request):
    payload = await request.json()
    logger.info("Received webhook payload: %s", payload)
    return {"status": "ok"}
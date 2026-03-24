import base64
import json
import logging
import os

import anthropic
import fitz  # pymupdf
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def _pdf_to_png_bytes(pdf_bytes: bytes) -> bytes | None:
    """Convert the first page of a PDF to PNG bytes."""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pix = doc[0].get_pixmap(dpi=150)
        png_bytes = pix.tobytes("png")
        doc.close()
        return png_bytes
    except Exception as e:
        logger.error(f"PDF to PNG conversion failed: {e}")
        return None


def _parse_png(png_bytes: bytes) -> dict | None:
    """Send PNG to Claude Vision and return structured JSON. (Jenny's logic)"""
    try:
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        b64 = base64.standard_b64encode(png_bytes).decode("utf-8")
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": "image/png", "data": b64},
                    },
                    {
                        "type": "text",
                        "text": (
                            "Parse this resume image. "
                            "Return ONLY a valid JSON object with exactly these keys: "
                            "skills (list of strings), experience_years (number), "
                            "past_roles (list of strings), companies (list of strings)."
                        ),
                    },
                ],
            }],
        )
        raw = response.content[0].text.strip().removeprefix("```json").removesuffix("```").strip()
        return json.loads(raw)
    except Exception as e:
        logger.error(f"Claude Vision parsing failed: {e}")
        return None


def parse_cv(pdf_bytes: bytes) -> dict | None:
    """
    Full pipeline: PDF → PNG → Claude Vision → structured JSON.
    Returns None if any step fails.
    """
    png_bytes = _pdf_to_png_bytes(pdf_bytes)
    if not png_bytes:
        return None
    return _parse_png(png_bytes)

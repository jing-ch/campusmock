import os
import json
import logging
import anthropic
import base64
from dotenv import load_dotenv
from typing import Dict, Any

# 初始化日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class ClaudeCVParser:
    """负责调用 Claude API 将简历图片解析为结构化 JSON"""

    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables.")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-haiku-4-5-20251001"

    def parse_image(self, img_bytes: bytes) -> Dict[str, Any]:
        b64 = base64.standard_b64encode(img_bytes).decode("utf-8")
        content = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": b64
                }
            },
            {
                "type": "text",
                "text": "Parse this resume. Return ONLY a valid JSON object with keys: skills (list), experience_years (number), past_roles (list), companies (list)."
            }
        ]

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": content}]
            )
            raw = response.content[0].text.strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            return json.loads(raw)
        except Exception as e:
            logger.error(f"Error during Claude API call: {e}")
            return self._empty_schema()

    def _empty_schema(self) -> Dict[str, Any]:
        return {"skills": [], "experience_years": 0, "past_roles": [], "companies": []}


if __name__ == "__main__":
    TEMPLATES_DIR = "templates"
    TEST_FILES = ["resume1.png", "resume2.png"]

    parser = ClaudeCVParser()

    for filename in TEST_FILES:
        file_path = os.path.join(TEMPLATES_DIR, filename)

        if os.path.exists(file_path):
            print(f"\n--- Testing with: {file_path} ---")
            with open(file_path, "rb") as f:
                img_bytes = f.read()

            print("Calling Claude API...")
            result = parser.parse_image(img_bytes)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"File not found: {file_path}")
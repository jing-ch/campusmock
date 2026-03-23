import os
import json
import logging
import re
import base64
from anthropic import Anthropic
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()
logger = logging.getLogger(__name__)

# 初始化 Anthropic 客户端
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def _extract_json(text: str) -> str:
    """
    使用正则表达式从回复中提取 JSON 部分。
    解决 'Extra data' 或 Markdown 代码块导致的解析失败。
    """
    match = re.search(r'(\{.*\})', text, re.DOTALL)
    if match:
        return match.group(1)
    return text

def parse_cv(cv_data: str | bytes) -> dict | None:
    """
    调用 Claude Vision 3.5 解析简历数据。
    自动处理传入的是 Base64 字符串还是原始二进制字节流。 [cite: 2026-03-23]
    """
    
    # --- 关键修复：处理 bytes 类型，确保 JSON 序列化成功 ---
    pdf_image_base64 = cv_data
    if isinstance(cv_data, bytes):
        try:
            # 尝试作为 UTF-8 字符串解码（处理 Base64 格式的 bytes）
            pdf_image_base64 = cv_data.decode('utf-8')
            # 校验是否为合法 Base64，如果包含非 Base64 字符则跳转到 except
            if not re.match(r'^[A-Za-z0-9+/]*={0,2}$', pdf_image_base64):
                raise ValueError("Not a valid base64 string")
        except Exception:
            # 如果解码失败或者是原始二进制，则强制重新进行 Base64 编码
            pdf_image_base64 = base64.b64encode(cv_data).decode('utf-8')

    prompt = """
    Please parse this resume image into a structured JSON format. 
    Include the following fields:
    - experience_years (int)
    - top_skills (list of strings)
    - summary (string)
    
    Return ONLY the JSON object, nothing else.
    """

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": pdf_image_base64,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )
        
        raw_text = response.content[0].text
        # 清理可能存在的 Markdown 代码块或提示语
        json_str = _extract_json(raw_text)
        
        return json.loads(json_str)
        
    except Exception as e:
        logger.error(f"Claude Vision parsing failed: {e}")
        return None
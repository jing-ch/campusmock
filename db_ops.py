import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# 初始化 Supabase 客户端 
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def upsert_user_main(email: str, payload: Dict[str, Any], raw_cv_text: str = "") -> str:
    """
    存储到主数据库 (Main DB): 包含个人身份信息 
    表名: users
    """
    user_data = {
        "email": email,
        "first_name": payload.get("first_name"),
        "last_name": payload.get("last_name"),
        "college": payload.get("college"),
        "major": payload.get("major"),
        "enrollment_semester": payload.get("enrollment_semester"),
        "languages": payload.get("languages"),
        "cultural_background": payload.get("cultural_background"),
        "availability": payload.get("availability"), 
        "cv_text": raw_cv_text, 
        "is_interviewer": True,  # 只要申请/注册，就自动授权成为潜在面试官
        "has_detailed_cv": True, # 标记该用户拥有经过 Claude Vision 解析的详细画像 [cite: 2026-02-08, 2026-03-21]
        "last_updated": datetime.utcnow().isoformat() # 仅保留一个时间戳即可
    }


    try:
        # 使用 email 作为唯一键进行 upsert 
        response = supabase.table("users").upsert(user_data, on_conflict="email").execute()
        user_id = response.data[0]["id"]
        logger.info(f"Main DB: User {email} upserted. ID: {user_id}")
        return user_id
    except Exception as e:
        logger.error(f"Error saving to Main DB: {e}")
        raise

def save_to_mcp_isolation_layer(user_id: str, cv_parsed: Dict[str, Any]):
    """
    存储到隔离层 (Isolation Layer): 仅存放 AI 解析的特征标签 
    格式参考 MCP (Model Context Protocol) 资源定义，供 matching.py 语义调用。
    表名: structured_cvs (或隔离的 Schema)
    """
    mcp_resource = {
        "user_id": user_id,
        "content": {
            "metadata": {
                "source": "cv_vision_analysis",
                "version": "1.0"
            },
            # 这里的 JSON 结构直接对应 matching.py 的 Context 输入 
            "features": {
                "skills": cv_parsed.get("skills", []),
                "experience_years": cv_parsed.get("experience_years", 0),
                "past_roles": cv_parsed.get("past_roles", []),
                "companies": cv_parsed.get("companies", [])
            }
        },
        "created_at": datetime.utcnow().isoformat()
    }
    
    try:
        supabase.table("structured_cvs").upsert(mcp_resource, on_conflict="user_id").execute()
        logger.info(f"Isolation Layer: Structured features for User ID {user_id} stored in MCP format.")
    except Exception as e:
        logger.error(f"Error saving to Isolation Layer: {e}")

def create_interview_request(user_id: str, payload: Dict[str, Any]):
    """
    存储面试申请到主数据库 
    表名: requests
    """
    request_data = {
        "requester_id": user_id,
        "target_company": payload.get("target_company"),
        "role": payload.get("role"),
        "focus_area": payload.get("focus_area"),
        "availability": payload.get("interview_availability"), # 具体的3个时间点 
        "status": "pending",
        "created_at": datetime.utcnow().isoformat()
    }
    
    try:
        response = supabase.table("requests").insert(request_data).execute()
        logger.info(f"Main DB: Interview request created for user {user_id}")
        return response.data[0]["id"]
    except Exception as e:
        logger.error(f"Error creating request: {e}")
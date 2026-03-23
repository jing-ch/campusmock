import os
import logging
from datetime import datetime, timezone, timedelta

from supabase import create_client, Client
from dotenv import load_dotenv

from models import UserUpsert, RequestInsert

# 加载环境变量
load_dotenv()
logger = logging.getLogger(__name__)

# 单例模式初始化 Supabase 客户端
_client: Client | None = None

def _get_client() -> Client:
    """获取或初始化 Supabase 客户端"""
    global _client
    if _client is None:
        _client = create_client(
            os.environ["SUPABASE_URL"],
            os.environ["SUPABASE_SERVICE_KEY"],
        )
    return _client

def upsert_user(user: UserUpsert) -> dict:
    """新增或更新用户信息"""
    row = user.model_dump(exclude_none=True)
    row["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = _get_client().table("users").upsert(row, on_conflict="email").execute()
    return result.data[0]

def insert_request(req: RequestInsert) -> dict:
    """插入新的面试请求"""
    now = datetime.now(timezone.utc)
    row = req.model_dump(mode='json', exclude_none=True)
    row["status"] = "pending"
    row["expires_at"] = (now + timedelta(hours=48)).isoformat()
    row["created_at"] = now.isoformat()
    result = _get_client().table("requests").insert(row).execute()
    return result.data[0]

def get_interviewer_pool() -> list:
    """获取可用的面试官池"""
    try:
        result = _get_client().table("users").select("id, email, first_name, major, cv_parsed").not_.is_("cv_parsed", "null").execute()
        pool = []
        for row in result.data:
            cv = row.get("cv_parsed", {})
            pool.append({
                "id": row["id"],
                "email": row["email"],
                "first_name": row["first_name"],
                "major": row["major"],
                "has_detailed_cv": True,
                "experience_years": cv.get("experience_years", 0)
            })
        return pool
    except Exception as e:
        logger.error(f"Error fetching interviewer pool: {e}")
        return []

def get_request_by_id(req_id: str) -> dict | None:
    """根据 ID 获取申请详情"""
    try:
        result = _get_client().table("requests").select("*").eq("id", req_id).single().execute()
        return result.data
    except Exception as e:
        logger.error(f"Error fetching request {req_id}: {e}")
        return None

def get_user_by_id(user_id: str) -> dict | None:
    """根据 ID 获取用户信息"""
    try:
        result = _get_client().table("users").select("*").eq("id", user_id).single().execute()
        return result.data
    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {e}")
        return None

def update_request_status(req_id: str, status: str, intv_id: str) -> bool:
    """
    原子化更新面试请求状态。
    只有当原始状态为 'pending' 时才允许更新。
    """
    try:
        now = datetime.now(timezone.utc).isoformat()
        _get_client().table("requests").update({
            "status": status,
            "interviewer_id": intv_id,
            "matched_at": now,
            "slot_confirmed": now
        }).eq("id", req_id).eq("status", "pending").execute()

        # 用 SELECT 验证是否真的更新成功（兼容所有 supabase-py 版本）
        verify = _get_client().table("requests").select("id, status, interviewer_id") \
            .eq("id", req_id).eq("interviewer_id", intv_id).eq("status", status).execute()
        return len(verify.data) > 0
    except Exception as e:
        logger.error(f"更新请求状态失败 {req_id}: {e}")
        return False
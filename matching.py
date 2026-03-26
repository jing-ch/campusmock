import logging
from typing import List, Dict, Any

# 初始化日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 1. 定义专业相关性簇 (用于模糊匹配)
# 针对 Jenny 所在的 MS in AI 及其相关领域进行预设 [cite: 2025-08-22, 2026-02-26]
MAJOR_CLUSTERS = {
    "MS in AI": ["Computer Science", "Data Science", "Artificial Intelligence"],
    "Artificial Intelligence": ["Computer Science", "Data Science", "Machine Learning", "Robotics"],
    "Computer Science": ["Artificial Intelligence", "Software Engineering", "Computer Engineering", "Data Science"],
    "Financial Engineering": ["Finance", "Economics", "Data Science", "Mathematics", "FinTech"],
    "Information Systems": ["Information Technology", "Project Management", "Software Engineering"],
    "Data Science": ["Artificial Intelligence", "Computer Science", "Statistics", "Mathematics"]
}

def get_related_majors(major: str) -> List[str]:
    """获取目标专业及其在模糊匹配逻辑下的相关专业列表"""
    # 转换为标准格式进行匹配
    related = MAJOR_CLUSTERS.get(major, [])
    return [major] + related

def calculate_match_score(requester_cv: Dict, interviewer: Dict) -> int:
    """
    计算匹配得分逻辑：
    1. 专业精准匹配得分最高。
    2. 申请者转化而来的面试官（拥有详细解析数据）拥有更高权重。
    3. 经验年限作为辅助加分项。
    """
    score = 0
    req_major = requester_cv.get("major")
    int_major = interviewer.get("major")

    # 准则 A: 专业匹配程度
    if int_major == req_major:
        score += 50  # 精准匹配 [cite: 2026-02-08]
    else:
        score += 20  # 模糊/相关匹配

    # 准则 B: 数据详尽度 (由 Applicant 转化而来) [cite: 2025-10-15]
    if interviewer.get("has_detailed_cv", False):
        score += 30 

    # 准则 C: 经验年限  [cite: 2026-01-21]
    exp = interviewer.get("experience_years", 0)
    score += min(exp * 2, 20)  # 最高加 20 分

    return score

def find_best_matches(requester_payload: Dict, interviewer_pool: List[Dict]) -> List[Dict]:
    """
    核心匹配引擎：实现“专业优先 -> 模糊扩展 -> AI 兜底”逻辑
    """
    req_major = requester_payload.get("major")
    # 获取当前申请人的唯一标识
    req_id = requester_payload.get("id")
    req_email = requester_payload.get("email")
    
    related_majors = get_related_majors(req_major)
    
    logger.info(f"开始匹配：目标专业 [{req_major}]，搜索范围 {related_majors}")

    # 1. 初步筛选：寻找专业簇内的面试官，并【排除申请人本人】
    potential_matches = [
        intv for intv in interviewer_pool 
        if (intv.get("major") in related_majors) and 
           (intv.get("id") != req_id) and           # 过滤相同 ID
           (intv.get("email") != req_email)       # 过滤相同 Email
    ]

    # 2. 如果找到真人，进行评分排序
    if potential_matches:
        for intv in potential_matches:
            intv["match_score"] = calculate_match_score(requester_payload, intv)
        
        # 按分数降序排列
        potential_matches.sort(key=lambda x: x["match_score"], reverse=True)
        logger.info(f"成功找到 {len(potential_matches)} 位真人面试官。")
        return potential_matches[:3]  # 返回前 3 名

    # 3. AI 兜底逻辑：如果没有真人匹配，自动分配虚拟 AI 面试官
    logger.warning(f"未找到专业相关面试官，启动 AI Mocking 兜底方案。")
    ai_fallback = [{
        "id": "ai_agent_v1",
        "first_name": "CampusMock",
        "last_name": "AI Agent",
        "major": req_major,
        "type": "AI_BOT",
        "is_ai": True,
        "description": f"专业的 {req_major} 虚拟面试官，支持 24/7 模拟面试。"
    }]
    return ai_fallback

# 测试代码块
if __name__ == "__main__":
    # 模拟数据：包含一个精准匹配、一个相关匹配
    mock_pool = [
        {"id": "user_01", "major": "Artificial Intelligence", "has_detailed_cv": True, "experience_years": 5},
        {"id": "user_02", "major": "Computer Science", "has_detailed_cv": False, "experience_years": 2},
    ]
    
    # 模拟 Jenny 的申请 [cite: 2026-02-26]
    test_req = {"major": "Artificial Intelligence", "email": "jenny_test@northeastern.edu"}
    
    results = find_best_matches(test_req, mock_pool)
    print(f"匹配结果: {results}")
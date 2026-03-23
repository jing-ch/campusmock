import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# 将项目根目录添加到系统路径中，确保能找到 db.py [cite: 2026-03-23]
root_path = str(Path(__file__).parent.parent)
if root_path not in sys.path:
    sys.path.append(root_path)

from db import get_interviewer_pool

# 初始化配置
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_existing_data():
    """
    核实 Supabase 中已有的数据是否能被匹配引擎识别
    """
    print("--- Supabase 匹配池数据核查 ---")
    
    # 获取当前数据库中所有符合条件的面试官
    pool = get_interviewer_pool()
    
    if not pool:
        print("❌ 警告：匹配池为空！")
        print("原因可能是：")
        print("1. 'users' 表中没有数据。")
        print("2. 现有数据的 'cv_parsed' 字段为 NULL（匹配引擎只挑选已解析过简历的用户）。")
    else:
        print(f"✅ 成功找到 {len(pool)} 位可用的面试官：")
        for i, intv in enumerate(pool, 1):
            print(f"   [{i}] ID: {intv['id']} | Name: {intv['first_name']} | Major: {intv['major']} | Exp: {intv['experience_years']}y")
        
        print("\n--- 结论 ---")
        print("你可以直接开始全链路测试。")
        print("当你在测试脚本中提交申请时，系统会从上方列表中挑选最匹配的人员发送邮件。")

if __name__ == "__main__":
    verify_existing_data()
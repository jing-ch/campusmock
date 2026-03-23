import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    try:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_KEY")
        supabase = create_client(url, key)
        # 尝试读取 users 表的第一行
        res = supabase.table("users").select("count", count="exact").limit(1).execute()
        print("Successfully connected to Supabase!")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    test_connection()
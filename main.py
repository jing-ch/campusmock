import logging
import time
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates

# 导入业务模块
from webhook import router as webhook_router
from accept import router as accept_router
from cron import start_cron_jobs

# --- 1. 配置全局日志 (Standard Logging Configuration) ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- 2. 定义生命周期管理 (Lifespan Management) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    管理服务启动与关闭时的逻辑 [cite: 2026-03-21]
    Startup: 启动后台 Cron 调度任务
    Shutdown: 停止资源占用
    """
    logger.info("--- [STARTUP] CampusMock AI Service is initializing ---")
    
    try:
        # 启动处理 48h 超时逻辑的后台任务
        start_cron_jobs()
        logger.info("Cron scheduler is active.")
    except Exception as e:
        logger.error(f"Failed to start cron jobs: {e}")
        
    yield # 服务运行期间保持在此处
    
    logger.info("--- [SHUTDOWN] CampusMock AI Service is shutting down ---")

# --- 3. 实例化 FastAPI ---
app = FastAPI(
    title="CampusMock AI Service",
    description="Backend orchestration for resume parsing, matching, and interview claiming.",
    version="1.0.0",
    lifespan=lifespan
)

# --- 4. 配置中间件 (CORS) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置模板目录
templates = Jinja2Templates(directory="templates")

# --- 5. 挂载业务路由 (API Versioning) ---
# 使用 /api/v1 前缀确保与测试脚本和前端调用一致 [cite: 2026-03-21]
app.include_router(webhook_router, prefix="/api/v1", tags=["Matching"])
app.include_router(accept_router, prefix="/api/v1", tags=["Acceptance"])

# --- 6. 基础接口 (General Endpoints) ---

@app.get("/", tags=["General"])
async def root():
    return {"status": "ok", "service": "campusmock-backend"}

@app.get("/health", tags=["General"])
async def health_check_root():
    now = datetime.now()
    return {
        "status": "online",
        "current_date": now.strftime("%Y-%m-%d"),
        "timestamp": now.isoformat(),
        "service": "campusmock-backend"
    }

@app.get("/form", tags=["General"])
async def form(request: Request):
    """渲染前端表单页面"""
    return templates.TemplateResponse("form.html", {"request": request})

@app.get("/api/v1/health", tags=["General"])
async def health_check():
    """
    系统健康检查接口 (满足 test_full_flow.py 要求)
    动态返回当前日期和 ISO 时间戳 [cite: 2026-03-21]
    """
    now = datetime.now()
    return {
        "status": "online",
        "current_date": now.strftime("%Y-%m-%d"),
        "timestamp": now.isoformat(),
        "service": "campusmock-backend"
    }

if __name__ == "__main__":
    import uvicorn
    # 本地开发使用，部署时通常由 gunicorn 或 uvicorn 命令行驱动
    uvicorn.run(app, host="127.0.0.1", port=8000)
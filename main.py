import logging
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

# 导入自定义模块
from webhook import router as webhook_router
from accept import router as accept_router
from cron import start_cron_jobs

# --- 1. 配置全局日志 (Standard Logging Configuration) ---
# 确保所有模块的日志输出格式统一，包含时间戳 [cite: 2026-03-21]
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
# 仅定义一次实例，避免路由被覆盖 [cite: 2026-03-21]
app = FastAPI(
    title="CampusMock AI Service",
    description="Backend orchestration for resume parsing, matching, and interview claiming.",
    version="1.0.0",
    lifespan=lifespan
)

# --- 4. 挂载业务路由 (API Versioning) ---
# 使用 /api/v1 前缀符合生产环境规范 [cite: 2026-03-21]
app.include_router(webhook_router, prefix="/api/v1", tags=["Matching"])
app.include_router(accept_router, prefix="/api/v1", tags=["Acceptance"])

templates = Jinja2Templates(directory="templates")

# --- 5. 基础状态接口 (General Endpoints) ---
@app.get("/form", tags=["General"])
async def form(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})

@app.get("/health", tags=["General"])
def health():
    """
    系统健康检查接口
    动态返回当前日期和 ISO 时间戳 [cite: 2026-03-21]
    """
    now = datetime.now()
    return {
        "status": "ok", 
        "current_date": now.strftime("%Y-%m-%d"), # 格式化为 2026-03-21 [cite: 2026-03-21]
        "timestamp": now.isoformat(), # 精确到秒的时间戳 [cite: 2026-03-21]
        "timezone": "PDT (Seattle)" # 对应你所在的西雅图时区
    }

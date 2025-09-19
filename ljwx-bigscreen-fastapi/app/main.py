"""
LJWX BigScreen FastAPI 主应用
高性能大屏系统 - FastAPI 重构版本
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn
import time
import logging

from app.core.logger import setup_logging
from app.core.exceptions import setup_exception_handlers
from app.config.settings import get_settings
from app.api.v1 import auth, alert, message, health, device, dashboard, main_bigscreen, personal_bigscreen

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)

# 获取配置
settings = get_settings()

# 创建 FastAPI 应用
app = FastAPI(
    title="LJWX BigScreen API",
    description="灵境万象健康大屏系统 - 高性能FastAPI版本",
    version="2.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

# 添加中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# 性能监控中间件
@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # 记录慢请求
    if process_time > 1.0:
        logger.warning(
            f"Slow request: {request.method} {request.url} took {process_time:.3f}s"
        )
    
    return response

# 设置异常处理
setup_exception_handlers(app)

# 静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")

# 模板引擎
templates = Jinja2Templates(directory="templates")

# 注册 API 路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(dashboard.router, prefix="/api", tags=["仪表板数据"])  # 支持原有路径
app.include_router(main_bigscreen.router, tags=["主大屏API"])  # 主大屏API
app.include_router(personal_bigscreen.router, tags=["个人大屏API"])  # 个人大屏API
app.include_router(alert.router, prefix="/api/v1/alert", tags=["告警"])
app.include_router(message.router, prefix="/api/v1/message", tags=["消息"])
app.include_router(health.router, prefix="/api/v1/health", tags=["健康数据"])
app.include_router(device.router, prefix="/api/v1/device", tags=["设备"])

# 页面路由
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """首页"""
    return templates.TemplateResponse("pages/dashboard.html", {"request": request})

@app.get("/main", response_class=HTMLResponse)
async def main_bigscreen_page(request: Request):
    """主大屏页面"""
    context = {
        "request": request,
        "BIGSCREEN_TITLE": "智能健康数据分析平台",
        "BIGSCREEN_VERSION": "v2.0.0"
    }
    return templates.TemplateResponse("pages/main_optimized.html", context)

@app.get("/personal", response_class=HTMLResponse)
async def personal_bigscreen_page(request: Request):
    """个人大屏页面"""
    context = {
        "request": request,
        "BIGSCREEN_TITLE": "个人健康数据监控",
        "BIGSCREEN_VERSION": "v2.0.0"
    }
    return templates.TemplateResponse("pages/personal_optimized.html", context)

# 健康检查
@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "timestamp": int(time.time()),
        "version": "2.0.0"
    }

# 应用启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info("LJWX BigScreen FastAPI 应用启动")
    
    # 初始化数据库连接池
    from app.core.database import init_db_pool
    await init_db_pool()
    
    # 初始化 Redis 连接池
    from app.core.cache import init_redis_pool
    await init_redis_pool()
    
    logger.info("数据库和缓存连接池初始化完成")

# 应用关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    logger.info("LJWX BigScreen FastAPI 应用关闭")
    
    # 关闭数据库连接池
    from app.core.database import close_db_pool
    await close_db_pool()
    
    # 关闭 Redis 连接池
    from app.core.cache import close_redis_pool
    await close_redis_pool()
    
    logger.info("数据库和缓存连接池已关闭")

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else settings.WORKERS,
        log_level="info",
        access_log=True,
    )
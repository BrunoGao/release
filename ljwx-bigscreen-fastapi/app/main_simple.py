"""
简化版 FastAPI 主应用程序 - 用于测试
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn

# 创建 FastAPI 应用
app = FastAPI(
    title="LJWX BigScreen API",
    description="灵境万象健康大屏系统 - 高性能FastAPI版本",
    version="2.0.0"
)

# 模板引擎
templates = Jinja2Templates(directory="templates")

# 注册 API 路由
from app.api.v1 import main_bigscreen, personal_bigscreen

app.include_router(main_bigscreen.router, tags=["主大屏API"])
app.include_router(personal_bigscreen.router, tags=["个人大屏API"])

# 页面路由
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """首页"""
    return templates.TemplateResponse("pages/main_optimized.html", {
        "request": request,
        "BIGSCREEN_TITLE": "智能健康数据分析平台",
        "BIGSCREEN_VERSION": "v2.0.0"
    })

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
        "version": "2.0.0"
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main_simple:app",
        host="0.0.0.0",
        port=8888,
        reload=True,
        log_level="info"
    )
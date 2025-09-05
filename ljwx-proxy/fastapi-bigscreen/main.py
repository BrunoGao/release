"""
FastAPI服务 - 业务大屏API接口
提供bigscreen_main.html和personal.html所需的所有API接口
"""

from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import httpx
from datetime import datetime, date
from typing import Optional, List, Dict, Any
import uvicorn
import os

app = FastAPI(
    title="大屏业务API服务",
    description="提供业务大屏所需的所有API接口，代理到ljwx-boot服务",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件和模板配置
static_dir = os.path.join(os.path.dirname(__file__), "static")
templates_dir = os.path.join(os.path.dirname(__file__), "templates")

# 确保目录存在
os.makedirs(static_dir, exist_ok=True)
os.makedirs(templates_dir, exist_ok=True)

print(f"Static directory: {static_dir}")
print(f"Templates directory: {templates_dir}")
print(f"Static directory exists: {os.path.exists(static_dir)}")
print(f"Templates directory exists: {os.path.exists(templates_dir)}")

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# ljwx-boot服务配置
LJWX_BOOT_BASE_URL = "http://localhost:8080"  # 修改为实际的ljwx-boot服务地址

class LjwxBootClient:
    """ljwx-boot服务客户端"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get(self, endpoint: str, params: dict = None):
        """GET请求"""
        try:
            response = await self.client.get(f"{self.base_url}{endpoint}", params=params)
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            print(f"API调用失败: {e}")
            return None
    
    async def post(self, endpoint: str, data: dict = None):
        """POST请求"""
        try:
            response = await self.client.post(f"{self.base_url}{endpoint}", json=data)
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            print(f"API调用失败: {e}")
            return None

ljwx_client = LjwxBootClient(LJWX_BOOT_BASE_URL)

# HTML页面路由
@app.get("/main", response_class=HTMLResponse)
async def main_page(request: Request, customerId: Optional[str] = Query(None)):
    """业务大屏主页面"""
    context = {"request": request}
    if customerId:
        context["customerId"] = customerId
    return templates.TemplateResponse("bigscreen_main.html", context)

@app.get("/bigscreen", response_class=HTMLResponse)
async def bigscreen_page(request: Request):
    """业务大屏主页面（兼容性路由）"""
    return templates.TemplateResponse("bigscreen_main.html", {"request": request})

@app.get("/test-static")
async def test_static():
    """测试静态文件"""
    return {"message": "Static files should be accessible at /static/"}

@app.get("/personal", response_class=HTMLResponse)
async def personal_page(request: Request, deviceSn: Optional[str] = Query(None)):
    """个人健康页面"""
    context = {"request": request}
    if deviceSn:
        context["deviceSn"] = deviceSn
    return templates.TemplateResponse("personal.html", context)

# ==================== 健康相关API ====================

@app.get("/api/health/score/comprehensive")
async def get_comprehensive_health_score(
    userId: Optional[str] = Query(None),
    orgId: Optional[str] = Query(None),
    date: Optional[str] = Query(None)
):
    """获取健康综合评分"""
    params = {}
    if userId:
        params["userId"] = userId
    if orgId:
        params["orgId"] = orgId
    if date:
        params["date"] = date
    
    result = await ljwx_client.get("/health/score/comprehensive", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取健康评分")
    return result

@app.get("/api/health/realtime_data")
async def get_realtime_health_data(
    userId: Optional[str] = Query(None),
    deviceSn: Optional[str] = Query(None)
):
    """获取实时健康数据"""
    params = {}
    if userId:
        params["userId"] = userId
    if deviceSn:
        params["deviceSn"] = deviceSn
        
    result = await ljwx_client.get("/health/realtime", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取实时健康数据")
    return result

@app.get("/api/health/trends")
async def get_health_trends(
    userId: str = Query(...),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None)
):
    """获取健康趋势数据"""
    params = {"userId": userId}
    if startDate:
        params["startDate"] = startDate
    if endDate:
        params["endDate"] = endDate
        
    result = await ljwx_client.get("/health/trends", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取健康趋势数据")
    return result

@app.get("/health_data/chart/baseline")
async def get_baseline_chart_data(
    orgId: str = Query(...),
    startDate: str = Query(...),
    endDate: str = Query(...)
):
    """获取基线健康数据图表"""
    params = {
        "orgId": orgId,
        "startDate": startDate,
        "endDate": endDate
    }
    
    result = await ljwx_client.get("/health/baseline/chart", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取基线数据")
    return result

@app.post("/api/baseline/generate")
async def generate_baseline(request: Request):
    """生成基线数据"""
    data = await request.json()
    result = await ljwx_client.post("/health/baseline/generate", data)
    if result is None:
        raise HTTPException(status_code=500, detail="无法生成基线数据")
    return result

@app.get("/fetchHealthDataById")
async def fetch_health_data_by_id(id: str = Query(...)):
    """根据ID获取健康数据"""
    params = {"id": id}
    result = await ljwx_client.get("/health/data/detail", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取健康数据")
    return result

@app.get("/api/personal/health/scores")
async def get_personal_health_scores(
    userId: str = Query(...),
    date: Optional[str] = Query(None)
):
    """获取个人健康评分"""
    params = {"userId": userId}
    if date:
        params["date"] = date
        
    result = await ljwx_client.get("/health/personal/scores", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取个人健康评分")
    return result

@app.get("/api/health/recommendations")
async def get_health_recommendations(userId: str = Query(...)):
    """获取健康建议"""
    params = {"userId": userId}
    result = await ljwx_client.get("/health/recommendations", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取健康建议")
    return result

@app.get("/api/health/predictions")
async def get_health_predictions(userId: str = Query(...)):
    """获取健康预测"""
    params = {"userId": userId}
    result = await ljwx_client.get("/health/predictions", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取健康预测")
    return result

# ==================== 设备相关API ====================

@app.get("/api/device/user_info")
async def get_device_user_info(deviceSn: str = Query(...)):
    """获取设备用户信息"""
    params = {"deviceSn": deviceSn}
    result = await ljwx_client.get("/device/user/info", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取设备用户信息")
    return result

@app.get("/api/device/info")
async def get_device_info(deviceSn: str = Query(...)):
    """获取设备状态信息"""
    params = {"deviceSn": deviceSn}
    result = await ljwx_client.get("/device/info", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取设备信息")
    return result

@app.get("/api/device/user_org")
async def get_device_user_org(deviceSn: str = Query(...)):
    """获取设备用户组织信息"""
    params = {"deviceSn": deviceSn}
    result = await ljwx_client.get("/device/user/org", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取设备用户组织信息")
    return result

# ==================== 用户相关API ====================

@app.get("/api/user/profile")
async def get_user_profile(userId: str = Query(...)):
    """获取用户资料"""
    params = {"userId": userId}
    result = await ljwx_client.get("/user/profile", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取用户资料")
    return result

@app.get("/fetch_users")
async def fetch_users(orgId: str = Query(...)):
    """获取组织下的用户列表"""
    params = {"orgId": orgId}
    result = await ljwx_client.get("/org/users", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取用户列表")
    return result

# ==================== 组织相关API ====================

@app.get("/get_departments")
async def get_departments(orgId: str = Query(...)):
    """获取部门信息"""
    params = {"orgId": orgId}
    result = await ljwx_client.get("/org/departments", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取部门信息")
    return result

@app.get("/get_total_info")
async def get_total_info(customer_id: str = Query(...)):
    """获取总体信息"""
    params = {"customerId": customer_id}
    result = await ljwx_client.get("/org/total/info", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取总体信息")
    return result

# ==================== 统计相关API ====================

@app.get("/api/statistics/overview")
async def get_statistics_overview(
    orgId: str = Query(...),
    date: Optional[str] = Query(None)
):
    """获取统计概览"""
    params = {"orgId": orgId}
    if date:
        params["date"] = date
        
    result = await ljwx_client.get("/statistics/overview", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取统计概览")
    return result

@app.get("/api/realtime_stats")
async def get_realtime_stats(
    customerId: str = Query(...),
    date: Optional[str] = Query(None)
):
    """获取实时统计数据"""
    params = {"customerId": customerId}
    if date:
        params["date"] = date
        
    result = await ljwx_client.get("/statistics/realtime", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取实时统计")
    return result

# ==================== 消息告警相关API ====================

@app.get("/api/messages/user")
async def get_user_messages(userId: str = Query(...)):
    """获取用户消息"""
    params = {"userId": userId}
    result = await ljwx_client.get("/messages/user", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取用户消息")
    return result

@app.get("/api/alerts/user")
async def get_user_alerts(userId: str = Query(...)):
    """获取用户告警"""
    params = {"userId": userId}
    result = await ljwx_client.get("/alerts/user", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取用户告警")
    return result

@app.get("/api/personal/alerts")
async def get_personal_alerts(deviceSn: str = Query(...)):
    """获取个人告警"""
    params = {"deviceSn": deviceSn}
    result = await ljwx_client.get("/alerts/personal", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取个人告警")
    return result

@app.post("/acknowledge_alert")
async def acknowledge_alert(request: Request):
    """确认告警"""
    data = await request.json()
    result = await ljwx_client.post("/alerts/acknowledge", data)
    if result is None:
        raise HTTPException(status_code=500, detail="无法确认告警")
    return result

@app.get("/dealAlert")
async def deal_alert(alertId: str = Query(...)):
    """处理告警"""
    params = {"alertId": alertId}
    result = await ljwx_client.get("/alerts/deal", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法处理告警")
    return result

# ==================== 健康检查 ====================

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    # 确保模板目录存在
    os.makedirs("templates", exist_ok=True)
    
    print("🚀 启动FastAPI大屏服务...")
    print("📊 大屏页面: http://localhost:8888/bigscreen")
    print("👤 个人页面: http://localhost:8888/personal")
    print("📖 API文档: http://localhost:8888/docs")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8888,
        reload=True,
        reload_dirs=["./"],
        log_level="info"
    )
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
LJWX_BOOT_BASE_URL = "http://192.168.1.83:9998"  # ljwx-boot真实服务地址
LJWX_AUTH_URL = "http://192.168.1.83:3333/proxy-default/auth/user_name"  # 认证服务地址

# 默认认证信息
DEFAULT_AUTH = {
    "userName": "admin",
    "password": "80a3d119ee1501354755dfc3c4638d74c67c801689efbed4f25f06cb4b1cd776"
}

# 全局认证token
AUTH_TOKEN = None

class LjwxBootClient:
    """ljwx-boot服务客户端"""
    
    def __init__(self, base_url: str, auth_url: str = None):
        self.base_url = base_url
        self.auth_url = auth_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.token = None
    
    async def get_auth_token(self):
        """获取认证token"""
        if self.token:
            return self.token
            
        try:
            response = await self.client.post(self.auth_url, json=DEFAULT_AUTH)
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 200:
                    self.token = result.get("data", {}).get("token")
                    return self.token
        except Exception as e:
            print(f"认证失败: {e}")
        return None
    
    async def get_headers(self):
        """获取请求头"""
        token = await self.get_auth_token()
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}
    
    async def get(self, endpoint: str, params: dict = None):
        """GET请求"""
        try:
            headers = await self.get_headers()
            response = await self.client.get(f"{self.base_url}{endpoint}", params=params, headers=headers)
            if response.status_code == 200:
                result = response.json()
                # 检查返回的JSON中是否包含401错误码
                if isinstance(result, dict) and result.get("code") == 401:
                    print(f"⚠️  Token已过期，重新获取token...")
                    # Token过期，重新获取
                    self.token = None
                    headers = await self.get_headers()
                    response = await self.client.get(f"{self.base_url}{endpoint}", params=params, headers=headers)
                    return response.json() if response.status_code == 200 else None
                return result
            elif response.status_code == 401:
                # HTTP 401，重新获取
                print(f"🔄 HTTP 401错误，重新获取token...")
                self.token = None
                headers = await self.get_headers()
                response = await self.client.get(f"{self.base_url}{endpoint}", params=params, headers=headers)
                return response.json() if response.status_code == 200 else None
            else:
                print(f"❌ API请求失败: {endpoint}, 状态码: {response.status_code}, 响应: {response.text}")
            return None
        except Exception as e:
            print(f"❌ API调用异常: {endpoint}, 错误: {e}")
            return None
    
    async def post(self, endpoint: str, data: dict = None):
        """POST请求"""
        try:
            headers = await self.get_headers()
            headers["Content-Type"] = "application/json"
            response = await self.client.post(f"{self.base_url}{endpoint}", json=data, headers=headers)
            if response.status_code == 200:
                result = response.json()
                # 检查返回的JSON中是否包含401错误码
                if isinstance(result, dict) and result.get("code") == 401:
                    print(f"⚠️  Token已过期，重新获取token...")
                    # Token过期，重新获取
                    self.token = None
                    headers = await self.get_headers()
                    headers["Content-Type"] = "application/json"
                    response = await self.client.post(f"{self.base_url}{endpoint}", json=data, headers=headers)
                    return response.json() if response.status_code == 200 else None
                return result
            elif response.status_code == 401:
                # HTTP 401，重新获取
                print(f"🔄 HTTP 401错误，重新获取token...")
                self.token = None
                headers = await self.get_headers()
                headers["Content-Type"] = "application/json"
                response = await self.client.post(f"{self.base_url}{endpoint}", json=data, headers=headers)
                return response.json() if response.status_code == 200 else None
            else:
                print(f"❌ API POST请求失败: {endpoint}, 状态码: {response.status_code}, 响应: {response.text}")
            return None
        except Exception as e:
            print(f"❌ API POST调用异常: {endpoint}, 错误: {e}")
            return None

ljwx_client = LjwxBootClient(LJWX_BOOT_BASE_URL, LJWX_AUTH_URL)

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

# ==================== 规范化API (v1) ====================

# 规范化健康API
@app.get("/api/v1/health/scores/comprehensive")
async def get_comprehensive_health_score_v1(
    userId: Optional[str] = Query(None),
    orgId: Optional[str] = Query(None),
    date: Optional[str] = Query(None)
):
    """获取健康综合评分 (v1规范化版本) - GET方法"""
    params = {}
    if userId:
        params["userId"] = userId
    if orgId:
        params["orgId"] = orgId
    if date:
        params["date"] = date
    
    result = await ljwx_client.get("/api/v1/health/scores/comprehensive", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取健康评分")
    return result

@app.post("/api/v1/health/scores/comprehensive") 
async def post_comprehensive_health_score_v1(request: Request):
    """获取健康综合评分 (v1规范化版本) - POST方法"""
    try:
        data = await request.json()
        result = await ljwx_client.post("/api/v1/health/scores/comprehensive", data)
        if result is None:
            raise HTTPException(status_code=500, detail="无法获取健康评分")
        return result
    except Exception as e:
        # POST失败时回退到GET方法
        return await get_comprehensive_health_score_v1()

@app.get("/api/v1/health/realtime-data")
async def get_realtime_health_data_v1(
    userId: Optional[str] = Query(None),
    deviceSn: Optional[str] = Query(None)
):
    """获取实时健康数据 (v1规范化版本)"""
    params = {}
    if userId:
        params["userId"] = userId
    if deviceSn:
        params["deviceSn"] = deviceSn
        
    result = await ljwx_client.get("/api/v1/health/realtime-data", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取实时健康数据")
    return result

@app.get("/api/v1/health/baseline/chart")
async def get_baseline_chart_data_v1(
    userId: Optional[str] = Query(None),
    orgId: Optional[str] = Query(None)
):
    """获取基线健康数据图表 (v1规范化版本)"""
    params = {}
    if userId:
        params["userId"] = userId
    if orgId:
        params["orgId"] = orgId
        
    result = await ljwx_client.get("/api/v1/health/baseline/chart", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取基线数据")
    return result

@app.post("/api/v1/health/baseline/generate")
async def generate_baseline_v1(request: Request):
    """生成基线数据 (v1规范化版本)"""
    data = await request.json()
    result = await ljwx_client.post("/api/v1/health/baseline/generate", data)
    if result is None:
        raise HTTPException(status_code=500, detail="无法生成基线数据")
    return result

@app.get("/api/v1/health/data/{id}")
async def fetch_health_data_by_id_v1(id: str):
    """根据ID获取健康数据 (v1规范化版本)"""
    result = await ljwx_client.get(f"/api/v1/health/data/{id}")
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取健康数据")
    return result

@app.get("/api/v1/health/personal/scores")
async def get_personal_health_scores_v1(
    userId: Optional[str] = Query(None),
    deviceSn: Optional[str] = Query(None)
):
    """获取个人健康评分 (v1规范化版本)"""
    params = {}
    if userId:
        params["userId"] = userId
    if deviceSn:
        params["deviceSn"] = deviceSn
        
    result = await ljwx_client.get("/api/v1/health/personal/scores", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取个人健康评分")
    return result

@app.get("/api/v1/health/recommendations") 
async def get_health_recommendations_v1(userId: str = Query(...)):
    """获取健康建议 (v1规范化版本)"""
    params = {"userId": userId}
    result = await ljwx_client.get("/api/v1/health/recommendations", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取健康建议")
    return result

@app.get("/api/v1/health/predictions")
async def get_health_predictions_v1(userId: str = Query(...)):
    """获取健康预测 (v1规范化版本)"""
    params = {"userId": userId}
    result = await ljwx_client.get("/api/v1/health/predictions", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取健康预测")
    return result

@app.get("/api/v1/health/trends")
async def get_health_trends_v1(
    userId: Optional[str] = Query(None),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None)
):
    """获取健康趋势数据 (v1规范化版本)"""
    params = {}
    if userId:
        params["userId"] = userId
    if startDate:
        params["startDate"] = startDate
    if endDate:
        params["endDate"] = endDate
        
    result = await ljwx_client.get("/api/v1/health/trends", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取健康趋势数据")
    return result

# 规范化设备API
@app.get("/api/v1/devices/user-info")
async def get_device_user_info_v1(deviceSn: str = Query(...)):
    """获取设备用户信息 (v1规范化版本)"""
    params = {"deviceSn": deviceSn}
    result = await ljwx_client.get("/api/v1/devices/user-info", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取设备用户信息")
    return result

@app.get("/api/v1/devices/status")
async def get_device_info_v1(deviceSn: str = Query(...)):
    """获取设备状态信息 (v1规范化版本)"""
    params = {"deviceSn": deviceSn}
    result = await ljwx_client.get("/api/v1/devices/status", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取设备信息")
    return result

@app.get("/api/v1/devices/user-organization")
async def get_device_user_org_v1(deviceSn: str = Query(...)):
    """获取设备用户组织信息 (v1规范化版本)"""
    params = {"deviceSn": deviceSn}
    result = await ljwx_client.get("/api/v1/devices/user-organization", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取设备用户组织信息")
    return result

# 规范化用户API
@app.get("/api/v1/users/profile")
async def get_user_profile_v1(userId: str = Query(...)):
    """获取用户资料 (v1规范化版本)"""
    params = {"userId": userId}
    result = await ljwx_client.get("/api/v1/users/profile", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取用户资料")
    return result

@app.get("/api/v1/users")
async def fetch_users_v1(
    orgId: Optional[str] = Query(None),
    page: Optional[int] = Query(1),
    size: Optional[int] = Query(20)
):
    """获取用户列表 (v1规范化版本)"""
    params = {}
    if orgId:
        params["orgId"] = orgId
    if page:
        params["page"] = page
    if size:
        params["size"] = size
        
    result = await ljwx_client.get("/api/v1/users", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取用户列表")
    return result

# 规范化组织API
@app.get("/api/v1/organizations/statistics")
async def get_total_info_v1(orgId: Optional[str] = Query(None)):
    """获取组织统计信息 (v1规范化版本)"""
    params = {}
    if orgId:
        params["orgId"] = orgId
        
    result = await ljwx_client.get("/api/v1/organizations/statistics", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取组织统计信息")
    return result

@app.get("/api/v1/departments")
async def get_departments_v1(orgId: Optional[str] = Query(None)):
    """获取部门列表 (v1规范化版本)"""
    params = {}
    if orgId:
        params["orgId"] = orgId
        
    result = await ljwx_client.get("/api/v1/departments", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取部门信息")
    return result

# 规范化统计API
@app.get("/api/v1/statistics/overview")
async def get_statistics_overview_v1(
    orgId: Optional[str] = Query(None)
):
    """获取统计概览 (v1规范化版本)"""
    params = {}
    if orgId:
        params["orgId"] = orgId
        
    result = await ljwx_client.get("/api/v1/statistics/overview", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取统计概览")
    return result

@app.get("/api/v1/statistics/realtime")
async def get_realtime_stats_v1(
    orgId: Optional[str] = Query(None)
):
    """获取实时统计数据 (v1规范化版本)"""
    params = {}
    if orgId:
        params["orgId"] = orgId
        
    result = await ljwx_client.get("/api/v1/statistics/realtime", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取实时统计")
    return result

# 规范化告警API
@app.get("/api/v1/alerts/user")
async def get_user_alerts_v1(
    userId: str = Query(...),
    status: Optional[str] = Query(None)
):
    """获取用户告警 (v1规范化版本)"""
    params = {"userId": userId}
    if status:
        params["status"] = status
        
    result = await ljwx_client.get("/api/v1/alerts/user", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取用户告警")
    return result

@app.get("/api/v1/alerts/personal")
async def get_personal_alerts_v1(
    deviceSn: Optional[str] = Query(None),
    userId: Optional[str] = Query(None)
):
    """获取个人告警 (v1规范化版本)"""
    params = {}
    if deviceSn:
        params["deviceSn"] = deviceSn
    if userId:
        params["userId"] = userId
        
    result = await ljwx_client.get("/api/v1/alerts/personal", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取个人告警")
    return result

@app.post("/api/v1/alerts/acknowledge")
async def acknowledge_alert_v1(request: Request):
    """确认告警 (v1规范化版本)"""
    data = await request.json()
    result = await ljwx_client.post("/api/v1/alerts/acknowledge", data)
    if result is None:
        raise HTTPException(status_code=500, detail="无法确认告警")
    return result

@app.post("/api/v1/alerts/deal")
async def deal_alert_v1(alertId: int = Query(...)):
    """处理告警 (v1规范化版本)"""
    params = {"alertId": alertId}
    result = await ljwx_client.post("/api/v1/alerts/deal", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法处理告警")
    return result

# 规范化消息API
@app.get("/api/v1/messages/user")
async def get_user_messages_v1(
    userId: str = Query(...),
    messageType: Optional[str] = Query(None)
):
    """获取用户消息 (v1规范化版本)"""
    params = {"userId": userId}
    if messageType:
        params["messageType"] = messageType
        
    result = await ljwx_client.get("/api/v1/messages/user", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取用户消息")
    return result

# ==================== 原有API (保持向后兼容) ====================

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

# 已重定向到v1 API - 原始路由已移除

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

# 已重定向到v1 API - 原始路由已移除

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

# ==================== API标准化重定向 ====================

from fastapi.responses import RedirectResponse

@app.get("/get_departments")
async def get_departments_redirect(orgId: Optional[str] = Query(None)):
    """重定向到v1标准化API: /api/v1/departments"""
    # 直接调用标准化API而不是重定向（避免CORS问题）
    params = {}
    if orgId:
        params["orgId"] = orgId
    result = await ljwx_client.get("/api/v1/departments", params)
    if result is None:
        raise HTTPException(status_code=500, detail="无法获取部门信息")
    return result

@app.get("/api/realtime_stats")
async def get_realtime_stats_redirect(
    customerId: str = Query(...),
    date: Optional[str] = Query(None)
):
    """重定向到v1标准化API: /api/v1/statistics/realtime"""
    try:
        return await get_realtime_stats_v1(orgId=customerId)
    except Exception as e:
        print(f"❌ 实时统计重定向失败: {e}")
        raise HTTPException(status_code=500, detail="无法获取实时统计")

# 废弃的API端点 - 记录警告并重定向到标准API
@app.get("/generateHealthJson")
async def generate_health_json_deprecated(
    customerId: str = Query(...),
    userId: Optional[str] = Query(None)
):
    """⚠️ 已废弃：请使用 /api/v1/health/scores/comprehensive"""
    print(f"⚠️ 前端调用了已废弃的API: /generateHealthJson - 建议使用 /api/v1/health/scores/comprehensive")
    
    # 参数映射并调用标准化API
    params = {}
    if userId and userId != "-1":
        params["userId"] = userId
    if customerId:
        params["orgId"] = customerId
        
    result = await ljwx_client.get("/api/v1/health/scores/comprehensive", params)
    if result is None:
        return {"error": "无法获取健康数据", "data": []}
    
    # 转换为前端期望的格式
    return {
        "status": "success",
        "data": [result.get("data", {})],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/generateAlertJson")
async def generate_alert_json_deprecated(
    customerId: str = Query(...),
    userId: Optional[str] = Query(None),
    severityLevel: Optional[str] = Query(None)
):
    """⚠️ 已废弃：请使用 /api/v1/alerts/user"""
    print(f"⚠️ 前端调用了已废弃的API: /generateAlertJson - 建议使用 /api/v1/alerts/user")
    
    # 参数映射并调用标准化API
    params = {}
    if userId and userId != "-1":
        params["userId"] = userId
    if severityLevel:
        params["status"] = severityLevel
        
    result = await ljwx_client.get("/api/v1/alerts/user", params) if userId and userId != "-1" else None
    if result is None:
        # 返回模拟数据
        return {
            "status": "success", 
            "data": [
                {
                    "alertId": f"alert_{severityLevel or 'info'}_001",
                    "message": f"{severityLevel or 'info'}级别告警示例",
                    "severity": severityLevel or "info",
                    "timestamp": datetime.now().isoformat()
                }
            ]
        }
    
    return {
        "status": "success",
        "data": result.get("data", []),
        "timestamp": datetime.now().isoformat()
    }

# ==================== Socket.IO Fallback处理 ====================

@app.get("/socket.io/{path:path}")
async def socket_io_fallback():
    """Socket.IO回退处理，返回静默响应避免404错误"""
    return {"status": "Socket.IO not implemented", "message": "Using HTTP polling instead"}

@app.post("/socket.io/{path:path}")
async def socket_io_fallback_post():
    """Socket.IO POST回退处理"""
    return {"status": "Socket.IO not implemented", "message": "Using HTTP polling instead"}

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
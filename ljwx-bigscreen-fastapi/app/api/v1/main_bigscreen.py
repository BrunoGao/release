"""
Main BigScreen API 路由 - 主大屏页面数据接口
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException
from ...schemas.bigscreen import (
    HealthScoreResponse, StatisticsOverviewResponse, AlertInfoResponse,
    HealthBaselineResponse, HealthRecommendationResponse, UserInfoResponse,
    BaselineGenerateRequest, AlertAcknowledgeRequest
)
from ...services.mock_data_service import MockDataService

router = APIRouter(prefix="/api", tags=["Main BigScreen"])

@router.get("/health/score/comprehensive", response_model=HealthScoreResponse)
async def get_comprehensive_health_score(
    userId: Optional[str] = Query(None),
    orgId: Optional[str] = Query(None),
    customerId: Optional[str] = Query(None)
):
    """获取综合健康评分"""
    return MockDataService.generate_health_score()

@router.get("/health/charts/baseline", response_model=HealthBaselineResponse)
async def get_health_baseline(
    orgId: Optional[str] = Query(None),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None)
):
    """获取健康基线数据"""
    return MockDataService.generate_health_baseline()

@router.get("/health/recommendations/list")
async def get_health_recommendations(
    analysisType: str = Query("comprehensive")
):
    """获取健康建议列表"""
    recommendations = MockDataService.generate_health_recommendations()
    return {"recommendations": recommendations}

@router.post("/health/baseline/generate")
async def generate_health_baseline(request: BaselineGenerateRequest):
    """生成健康基线"""
    return {
        "status": "success",
        "message": "健康基线生成完成",
        "target_date": request.target_date,
        "baseline_id": f"BL{datetime.now().strftime('%Y%m%d%H%M%S')}"
    }

@router.get("/statistics/overview", response_model=StatisticsOverviewResponse)
async def get_statistics_overview(
    orgId: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
    customerId: Optional[str] = Query(None)
):
    """获取统计概览数据"""
    return MockDataService.generate_statistics_overview()

@router.get("/alerts/handle")
async def handle_alert(alertId: str = Query(...)):
    """处理告警"""
    return {
        "status": "success",
        "message": f"告警 {alertId} 已处理",
        "handled_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@router.post("/alerts/acknowledge")
async def acknowledge_alert(request: AlertAcknowledgeRequest):
    """确认告警"""
    return {
        "status": "success",
        "message": "告警已确认",
        "alert_id": request.alert_id,
        "acknowledged_by": request.acknowledged_by,
        "acknowledged_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "notes": request.notes
    }

@router.get("/users/list", response_model=List[UserInfoResponse])
async def get_users_list(orgId: Optional[str] = Query(None)):
    """获取用户列表"""
    return MockDataService.generate_users()

@router.get("/users/info", response_model=UserInfoResponse)
async def get_user_info(deviceSn: str = Query(...)):
    """根据设备号获取用户信息"""
    user = MockDataService.generate_users(1)[0]
    user.deviceSn = deviceSn
    return user

@router.get("/alerts", response_model=List[AlertInfoResponse])
async def get_alerts(
    orgId: Optional[str] = Query(None),
    userId: Optional[str] = Query(None),
    customerId: Optional[str] = Query(None),
    limit: int = Query(10),
    offset: int = Query(0)
):
    """获取告警列表"""
    return MockDataService.generate_alerts(limit)

@router.get("/messages")
async def get_messages(
    orgId: Optional[str] = Query(None),
    userId: Optional[str] = Query(None),
    customerId: Optional[str] = Query(None),
    limit: int = Query(15),
    offset: int = Query(0)
):
    """获取消息列表"""
    return MockDataService.generate_messages(limit)

@router.get("/devices")
async def get_devices(
    orgId: Optional[str] = Query(None),
    userId: Optional[str] = Query(None),
    customerId: Optional[str] = Query(None),
    limit: int = Query(20),
    offset: int = Query(0)
):
    """获取设备列表"""
    return MockDataService.generate_devices(limit)

# 兼容旧API路径
@router.get("/get_health_data_by_orgIdAndUserId")
async def get_health_data_by_org_and_user(
    orgId: Optional[str] = Query(None),
    userId: Optional[str] = Query(None),
    customerId: Optional[str] = Query(None),
    limit: int = Query(30),
    offset: int = Query(0)
):
    """根据组织ID和用户ID获取健康数据"""
    return MockDataService.generate_health_data(limit)

@router.get("/get_users_by_orgIdAndUserId", response_model=List[UserInfoResponse])
async def get_users_by_org_and_user(
    orgId: str = Query(...),
    userId: str = Query(...)
):
    """根据组织ID和用户ID获取用户"""
    return MockDataService.generate_users(5)

@router.get("/get_total_info")
async def get_total_info(customerId: str = Query(...)):
    """获取总体信息"""
    import random
    return {
        "total_users": random.randint(500, 1000),
        "total_devices": random.randint(400, 800),
        "total_health_data": random.randint(50000, 100000),
        "total_alerts": random.randint(100, 500),
        "active_rate": round(random.uniform(0.8, 0.95), 2),
        "health_coverage": round(random.uniform(0.85, 0.98), 2)
    }
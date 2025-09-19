"""
大屏仪表板数据 API
包含 main.html 和 personal.html 需要的所有 API 接口
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel

from app.api.deps import get_current_user

router = APIRouter()


# ============================================================================
# 响应模型定义
# ============================================================================

class StatisticsOverview(BaseModel):
    """统计概览响应模型"""
    total_users: int
    active_devices: int
    today_alerts: int
    health_score_avg: float
    org_count: int
    department_count: int
    device_online_rate: float
    data_upload_rate: float


class RealtimeStats(BaseModel):
    """实时统计响应模型"""
    current_online: int
    growth_rate: float
    alert_trend: List[Dict]
    device_status: Dict[str, int]


class HealthScore(BaseModel):
    """健康评分响应模型"""
    user_id: str
    overall_score: float
    heart_rate_score: float
    blood_oxygen_score: float
    temperature_score: float
    pressure_score: float
    stress_score: float
    exercise_score: float
    sleep_score: float
    trend: str
    risk_level: str
    device_breakdown: List[Dict]


class HealthBaseline(BaseModel):
    """健康基线响应模型"""
    baseline_data: Dict[str, Any]
    chart_data: List[Dict]
    comparison: Dict[str, float]
    generated_at: datetime


class PersonalInfo(BaseModel):
    """个人信息响应模型"""
    user_id: str
    device_sn: str
    realname: str
    avatar: str
    org_name: str
    latest_health_data: Dict[str, Any]
    device_status: str
    last_sync_time: datetime


class DeviceInfo(BaseModel):
    """设备信息响应模型"""
    device_sn: str
    device_name: str
    device_type: str
    battery_level: int
    signal_strength: int
    last_sync: datetime
    status: str
    firmware_version: str


class AlertData(BaseModel):
    """告警数据响应模型"""
    alert_id: str
    device_sn: str
    user_id: str
    alert_type: str
    severity: str
    message: str
    created_time: datetime
    status: str
    acknowledged: bool


class HealthTrends(BaseModel):
    """健康趋势响应模型"""
    device_sn: str
    time_range: str
    trends: Dict[str, List[Dict]]
    analysis: Dict[str, Any]
    predictions: List[Dict]


class HealthRecommendations(BaseModel):
    """健康建议响应模型"""
    user_id: str
    analysis_type: str
    recommendations: List[Dict]
    priority_alerts: List[Dict]
    generated_at: datetime


# ============================================================================
# 统计概览相关 API
# ============================================================================

@router.get("/statistics/overview", response_model=StatisticsOverview, summary="获取统计概览")
async def get_statistics_overview(
    customer_id: str = Query(..., description="客户ID"),
    date: Optional[str] = Query(None, description="日期"),
    current_user: dict = Depends(get_current_user)
):
    """获取系统统计概览数据"""
    # 模拟数据
    mock_data = StatisticsOverview(
        total_users=1247,
        active_devices=892,
        today_alerts=23,
        health_score_avg=78.5,
        org_count=15,
        department_count=48,
        device_online_rate=89.7,
        data_upload_rate=94.2
    )
    return mock_data


@router.get("/statistics/realtime", response_model=RealtimeStats, summary="获取实时统计")
async def get_realtime_stats(
    date: Optional[str] = Query(None, description="日期"),
    current_user: dict = Depends(get_current_user)
):
    """获取实时统计数据"""
    mock_data = RealtimeStats(
        current_online=756,
        growth_rate=2.3,
        alert_trend=[
            {"time": "00:00", "count": 3},
            {"time": "06:00", "count": 8},
            {"time": "12:00", "count": 15},
            {"time": "18:00", "count": 23}
        ],
        device_status={
            "online": 756,
            "offline": 136,
            "maintenance": 12
        }
    )
    return mock_data


# ============================================================================
# 健康数据相关 API
# ============================================================================

@router.get("/health/score/comprehensive", response_model=HealthScore, summary="获取综合健康评分")
async def get_comprehensive_health_score(
    customer_id: str = Query(..., description="客户ID"),
    include_device_breakdown: bool = Query(False, description="包含设备详情"),
    days: int = Query(7, description="天数"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    current_user: dict = Depends(get_current_user)
):
    """获取综合健康评分"""
    mock_data = HealthScore(
        user_id=current_user.get('id', 'mock_user'),
        overall_score=78.5,
        heart_rate_score=82.3,
        blood_oxygen_score=95.7,
        temperature_score=88.1,
        pressure_score=75.2,
        stress_score=68.9,
        exercise_score=71.4,
        sleep_score=79.8,
        trend="improving",
        risk_level="low",
        device_breakdown=[
            {"device_sn": "DEV001", "score": 78.5, "status": "normal"},
            {"device_sn": "DEV002", "score": 76.2, "status": "warning"}
        ] if include_device_breakdown else []
    )
    return mock_data


@router.get("/health/charts/baseline", response_model=HealthBaseline, summary="获取健康基线图表")
async def get_health_baseline_chart(
    org_id: str = Query(..., description="组织ID"),
    start_date: str = Query(..., description="开始日期"),
    end_date: str = Query(..., description="结束日期"),
    current_user: dict = Depends(get_current_user)
):
    """获取健康基线图表数据"""
    mock_data = HealthBaseline(
        baseline_data={
            "heart_rate": {"min": 60, "max": 100, "avg": 78},
            "blood_oxygen": {"min": 95, "max": 100, "avg": 97.8},
            "temperature": {"min": 36.0, "max": 37.5, "avg": 36.8}
        },
        chart_data=[
            {"date": "2025-09-15", "heart_rate": 78, "blood_oxygen": 98, "temperature": 36.7},
            {"date": "2025-09-16", "heart_rate": 82, "blood_oxygen": 97, "temperature": 36.9},
            {"date": "2025-09-17", "heart_rate": 75, "blood_oxygen": 98, "temperature": 36.6}
        ],
        comparison={
            "heart_rate_change": 2.3,
            "blood_oxygen_change": -0.5,
            "temperature_change": 0.1
        },
        generated_at=datetime.now()
    )
    return mock_data


@router.get("/health/recommendations", response_model=HealthRecommendations, summary="获取健康建议")
async def get_health_recommendations(
    analysis_type: str = Query("comprehensive", description="分析类型"),
    device_sn: Optional[str] = Query(None, description="设备序列号"),
    current_user: dict = Depends(get_current_user)
):
    """获取健康建议"""
    mock_data = HealthRecommendations(
        user_id=current_user.get('id', 'mock_user'),
        analysis_type=analysis_type,
        recommendations=[
            {
                "id": "rec_001",
                "title": "改善睡眠质量",
                "description": "建议每天保持7-8小时睡眠",
                "priority": "high",
                "category": "sleep"
            },
            {
                "id": "rec_002", 
                "title": "增加有氧运动",
                "description": "每周至少进行3次30分钟有氧运动",
                "priority": "medium",
                "category": "exercise"
            }
        ],
        priority_alerts=[
            {
                "id": "alert_001",
                "type": "blood_pressure",
                "message": "血压偏高，建议就医检查",
                "severity": "high"
            }
        ],
        generated_at=datetime.now()
    )
    return mock_data


@router.get("/health/trends/analysis", response_model=HealthTrends, summary="获取健康趋势分析")
async def get_health_trends_analysis(
    device_sn: str = Query(..., description="设备序列号"),
    time_range: str = Query("24h", description="时间范围"),
    current_user: dict = Depends(get_current_user)
):
    """获取健康趋势分析"""
    mock_data = HealthTrends(
        device_sn=device_sn,
        time_range=time_range,
        trends={
            "heart_rate": [
                {"time": "2025-09-19 00:00", "value": 72},
                {"time": "2025-09-19 06:00", "value": 68},
                {"time": "2025-09-19 12:00", "value": 85},
                {"time": "2025-09-19 18:00", "value": 78}
            ],
            "blood_oxygen": [
                {"time": "2025-09-19 00:00", "value": 98},
                {"time": "2025-09-19 06:00", "value": 97},
                {"time": "2025-09-19 12:00", "value": 96},
                {"time": "2025-09-19 18:00", "value": 98}
            ]
        },
        analysis={
            "heart_rate_trend": "stable",
            "blood_oxygen_trend": "normal",
            "recommendations": ["保持当前运动量", "注意休息"]
        },
        predictions=[
            {"metric": "heart_rate", "next_24h": 76, "confidence": 0.85},
            {"metric": "blood_oxygen", "next_24h": 97, "confidence": 0.92}
        ]
    )
    return mock_data


@router.get("/health/analysis/comprehensive", summary="获取综合健康分析")
async def get_comprehensive_health_analysis(
    device_sn: str = Query(..., description="设备序列号"),
    days: int = Query(30, description="分析天数"),
    current_user: dict = Depends(get_current_user)
):
    """获取综合健康分析"""
    return {
        "device_sn": device_sn,
        "analysis_period": f"{days} days",
        "overall_health_score": 78.5,
        "health_categories": {
            "cardiovascular": {"score": 82, "status": "good"},
            "respiratory": {"score": 95, "status": "excellent"},
            "sleep": {"score": 68, "status": "needs_improvement"},
            "exercise": {"score": 71, "status": "fair"}
        },
        "risk_factors": [
            {"factor": "irregular_sleep", "severity": "medium"},
            {"factor": "low_activity", "severity": "low"}
        ],
        "improvement_suggestions": [
            "建立规律作息时间",
            "增加日常活动量",
            "定期监测血压"
        ]
    }


# ============================================================================
# 个人信息相关 API
# ============================================================================

@router.get("/personal/realtime-health", summary="获取个人实时健康数据")
async def get_personal_realtime_health(
    user_id: str = Query(..., description="用户ID"),
    card_type: str = Query(..., description="卡片类型"),
    device_sn: str = Query(..., description="设备序列号"),
    current_user: dict = Depends(get_current_user)
):
    """获取个人实时健康数据"""
    return {
        "user_id": user_id,
        "device_sn": device_sn,
        "card_type": card_type,
        "realtime_data": {
            "heart_rate": 78,
            "blood_oxygen": 98,
            "temperature": 36.7,
            "blood_pressure": "120/80",
            "stress_level": 25,
            "last_update": datetime.now().isoformat()
        },
        "status": "normal",
        "device_online": True
    }


@router.get("/personal/history-health", summary="获取个人历史健康数据")
async def get_personal_history_health(
    user_id: str = Query(..., description="用户ID"),
    card_type: str = Query(..., description="卡片类型"),
    days: int = Query(7, description="天数"),
    current_user: dict = Depends(get_current_user)
):
    """获取个人历史健康数据"""
    return {
        "user_id": user_id,
        "card_type": card_type,
        "days": days,
        "history_data": [
            {"date": "2025-09-18", "heart_rate": 75, "blood_oxygen": 97, "temperature": 36.6},
            {"date": "2025-09-17", "heart_rate": 78, "blood_oxygen": 98, "temperature": 36.8},
            {"date": "2025-09-16", "heart_rate": 82, "blood_oxygen": 96, "temperature": 36.9}
        ],
        "trends": {
            "heart_rate": "stable",
            "blood_oxygen": "improving", 
            "temperature": "normal"
        }
    }


@router.get("/personal/ai-analysis", summary="获取个人AI分析")
async def get_personal_ai_analysis(
    user_id: str = Query(..., description="用户ID"),
    card_type: str = Query(..., description="卡片类型"),
    analysis_type: str = Query("comprehensive", description="分析类型"),
    current_user: dict = Depends(get_current_user)
):
    """获取个人AI分析"""
    return {
        "user_id": user_id,
        "card_type": card_type,
        "analysis_type": analysis_type,
        "ai_insights": {
            "health_score": 78.5,
            "risk_assessment": "low",
            "predictions": [
                "未来7天心率将保持稳定",
                "建议增加运动量以改善整体健康"
            ],
            "personalized_advice": [
                "根据您的睡眠模式，建议22:30前就寝",
                "您的血氧水平优秀，继续保持"
            ]
        },
        "generated_at": datetime.now().isoformat()
    }


@router.get("/personal/info", response_model=PersonalInfo, summary="获取个人信息")
async def get_personal_info(
    device_sn: str = Query(..., description="设备序列号"),
    current_user: dict = Depends(get_current_user)
):
    """获取个人信息"""
    mock_data = PersonalInfo(
        user_id=current_user.get('id', 'mock_user'),
        device_sn=device_sn,
        realname=current_user.get('realname', '模拟用户'),
        avatar=current_user.get('avatar', '/static/images/default_avatar.png'),
        org_name=current_user.get('org_name', '模拟组织'),
        latest_health_data={
            "heart_rate": 78,
            "blood_oxygen": 98,
            "temperature": 36.7,
            "recorded_at": datetime.now().isoformat()
        },
        device_status="online",
        last_sync_time=datetime.now()
    )
    return mock_data


@router.get("/personal/alerts", summary="获取个人告警")
async def get_personal_alerts(
    device_sn: str = Query(..., description="设备序列号"),
    current_user: dict = Depends(get_current_user)
):
    """获取个人告警信息"""
    return {
        "device_sn": device_sn,
        "alerts": [
            {
                "id": "alert_001",
                "type": "heart_rate_high",
                "message": "心率异常偏高",
                "severity": "warning",
                "created_time": "2025-09-19T10:30:00",
                "status": "active"
            },
            {
                "id": "alert_002",
                "type": "blood_oxygen_low", 
                "message": "血氧饱和度偏低",
                "severity": "info",
                "created_time": "2025-09-19T08:15:00",
                "status": "acknowledged"
            }
        ],
        "total_count": 2,
        "unread_count": 1
    }


# ============================================================================
# 设备相关 API
# ============================================================================

@router.get("/device/info", response_model=DeviceInfo, summary="获取设备信息")
async def get_device_info(
    device_sn: str = Query(..., description="设备序列号"),
    current_user: dict = Depends(get_current_user)
):
    """获取设备信息"""
    mock_data = DeviceInfo(
        device_sn=device_sn,
        device_name=f"智能手环 {device_sn}",
        device_type="smart_bracelet",
        battery_level=78,
        signal_strength=89,
        last_sync=datetime.now() - timedelta(minutes=5),
        status="online",
        firmware_version="v2.1.5"
    )
    return mock_data


@router.get("/device/user_org", summary="获取设备关联的用户和组织")
async def get_device_user_org(
    device_sn: str = Query(..., description="设备序列号"),
    current_user: dict = Depends(get_current_user)
):
    """获取设备关联的用户和组织信息"""
    return {
        "device_sn": device_sn,
        "user_id": current_user.get('id', 'mock_user'),
        "org_id": current_user.get('org_id', 'mock_org'),
        "customer_id": current_user.get('customer_id', 'mock_customer'),
        "user_info": {
            "username": current_user.get('username', 'mock_user'),
            "realname": current_user.get('realname', '模拟用户'),
            "org_name": current_user.get('org_name', '模拟组织')
        }
    }


# ============================================================================
# 数据管理相关 API (兼容旧版)
# ============================================================================

@router.get("/get_personal_info", summary="获取个人信息 (兼容旧版)")
async def get_personal_info_legacy(
    device_sn: str = Query(..., description="设备序列号"),
    current_user: dict = Depends(get_current_user)
):
    """获取个人信息 (兼容旧版API)"""
    return await get_personal_info(device_sn, current_user)


@router.get("/health_data/latest", summary="获取最新健康数据")
async def get_latest_health_data(
    device_sn: str = Query(..., description="设备序列号"),
    current_user: dict = Depends(get_current_user)
):
    """获取最新健康数据"""
    return {
        "device_sn": device_sn,
        "latest_data": {
            "heart_rate": 78,
            "blood_oxygen": 98,
            "temperature": 36.7,
            "blood_pressure_high": 120,
            "blood_pressure_low": 80,
            "stress_level": 25,
            "step_count": 8567,
            "calories": 245.6,
            "distance": 6.2,
            "sleep_duration": 7.5,
            "recorded_at": datetime.now().isoformat()
        },
        "quality_score": 95.2,
        "device_status": "online"
    }


# ============================================================================
# 用户和组织相关 API
# ============================================================================

@router.get("/users/list", summary="获取用户列表")
async def get_users_list(
    org_id: str = Query(..., description="组织ID"),
    current_user: dict = Depends(get_current_user)
):
    """获取用户列表"""
    return {
        "org_id": org_id,
        "users": [
            {
                "id": "user_001",
                "username": "zhangsan",
                "realname": "张三",
                "email": "zhangsan@example.com",
                "phone": "13800138001",
                "device_sn": "DEV001",
                "status": "active",
                "last_active": "2025-09-19T10:30:00"
            },
            {
                "id": "user_002",
                "username": "lisi",
                "realname": "李四", 
                "email": "lisi@example.com",
                "phone": "13800138002",
                "device_sn": "DEV002",
                "status": "active",
                "last_active": "2025-09-19T09:45:00"
            }
        ],
        "total_count": 2
    }


@router.get("/users/info", summary="获取用户信息")
async def get_user_info(
    device_sn: str = Query(..., description="设备序列号"),
    current_user: dict = Depends(get_current_user)
):
    """根据设备序列号获取用户信息"""
    return {
        "device_sn": device_sn,
        "user_info": {
            "id": current_user.get('id', 'mock_user'),
            "username": current_user.get('username', 'mock_user'),
            "realname": current_user.get('realname', '模拟用户'),
            "email": current_user.get('email', 'mock@example.com'),
            "phone": current_user.get('phone', '13800138000'),
            "org_id": current_user.get('org_id', 'mock_org'),
            "org_name": current_user.get('org_name', '模拟组织'),
            "device_binding_time": "2025-09-01T08:00:00"
        }
    }


@router.get("/departments", summary="获取部门列表")
async def get_departments(
    org_id: str = Query(..., description="组织ID"),
    customer_id: str = Query(..., description="客户ID"),
    current_user: dict = Depends(get_current_user)
):
    """获取部门列表"""
    return {
        "org_id": org_id,
        "customer_id": customer_id,
        "departments": [
            {
                "id": "dept_001",
                "name": "技术部",
                "parent_id": None,
                "user_count": 25,
                "device_count": 23,
                "health_score_avg": 78.5
            },
            {
                "id": "dept_002", 
                "name": "市场部",
                "parent_id": None,
                "user_count": 18,
                "device_count": 16,
                "health_score_avg": 82.1
            },
            {
                "id": "dept_003",
                "name": "人事部",
                "parent_id": None,
                "user_count": 12,
                "device_count": 12,
                "health_score_avg": 75.8
            }
        ],
        "total_count": 3
    }


# ============================================================================
# 告警相关 API
# ============================================================================

@router.get("/alerts", summary="获取告警列表")
async def get_alerts(
    org_id: Optional[str] = Query(None, description="组织ID"),
    user_id: Optional[str] = Query(None, description="用户ID"),
    customer_id: Optional[str] = Query(None, description="客户ID"),
    severity_level: Optional[str] = Query(None, description="严重级别"),
    current_user: dict = Depends(get_current_user)
):
    """获取告警列表"""
    return {
        "filters": {
            "org_id": org_id,
            "user_id": user_id,
            "customer_id": customer_id,
            "severity_level": severity_level
        },
        "alerts": [
            {
                "id": "alert_001",
                "user_id": "user_001",
                "device_sn": "DEV001",
                "alert_type": "heart_rate_high",
                "severity": "warning",
                "message": "心率异常偏高 (105 bpm)",
                "created_time": "2025-09-19T10:30:00",
                "status": "active",
                "acknowledged": False
            },
            {
                "id": "alert_002",
                "user_id": "user_002", 
                "device_sn": "DEV002",
                "alert_type": "blood_oxygen_low",
                "severity": "info",
                "message": "血氧饱和度偏低 (92%)",
                "created_time": "2025-09-19T08:15:00",
                "status": "acknowledged",
                "acknowledged": True
            }
        ],
        "total_count": 2,
        "unread_count": 1
    }


@router.get("/alerts/handle", summary="处理告警")
async def handle_alert(
    alert_id: str = Query(..., description="告警ID"),
    current_user: dict = Depends(get_current_user)
):
    """处理告警"""
    return {
        "alert_id": alert_id,
        "action": "handled",
        "handled_by": current_user.get('id', 'mock_user'),
        "handled_at": datetime.now().isoformat(),
        "status": "resolved"
    }


@router.post("/alerts/acknowledge", summary="确认告警")
async def acknowledge_alert(
    alert_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """确认告警"""
    return {
        "alert_id": alert_data.get('alert_id'),
        "acknowledged": True,
        "acknowledged_by": current_user.get('id', 'mock_user'),
        "acknowledged_at": datetime.now().isoformat(),
        "note": alert_data.get('note', '')
    }


# ============================================================================
# 消息相关 API
# ============================================================================

@router.get("/messages", summary="获取消息列表")
async def get_messages(
    org_id: Optional[str] = Query(None, description="组织ID"),
    user_id: Optional[str] = Query(None, description="用户ID"),
    customer_id: Optional[str] = Query(None, description="客户ID"),
    message_type: Optional[str] = Query(None, description="消息类型"),
    current_user: dict = Depends(get_current_user)
):
    """获取消息列表"""
    return {
        "filters": {
            "org_id": org_id,
            "user_id": user_id,
            "customer_id": customer_id,
            "message_type": message_type
        },
        "messages": [
            {
                "id": "msg_001",
                "user_id": "user_001",
                "type": "health_reminder",
                "title": "健康提醒",
                "content": "您今天的步数已达到目标，继续保持！",
                "created_time": "2025-09-19T10:00:00",
                "read": False
            },
            {
                "id": "msg_002",
                "user_id": "user_001",
                "type": "system_notification",
                "title": "系统通知",
                "content": "您的设备固件已更新到最新版本",
                "created_time": "2025-09-19T08:30:00", 
                "read": True
            }
        ],
        "total_count": 2,
        "unread_count": 1
    }


# ============================================================================
# 设备管理相关 API
# ============================================================================

@router.get("/devices", summary="获取设备列表")
async def get_devices(
    org_id: Optional[str] = Query(None, description="组织ID"),
    user_id: Optional[str] = Query(None, description="用户ID"),
    customer_id: Optional[str] = Query(None, description="客户ID"),
    current_user: dict = Depends(get_current_user)
):
    """获取设备列表"""
    return {
        "filters": {
            "org_id": org_id,
            "user_id": user_id,
            "customer_id": customer_id
        },
        "devices": [
            {
                "device_sn": "DEV001",
                "device_name": "智能手环 001",
                "device_type": "smart_bracelet",
                "user_id": "user_001",
                "user_name": "张三",
                "battery_level": 78,
                "signal_strength": 89,
                "status": "online",
                "last_sync": "2025-09-19T10:25:00",
                "firmware_version": "v2.1.5"
            },
            {
                "device_sn": "DEV002",
                "device_name": "智能手环 002", 
                "device_type": "smart_bracelet",
                "user_id": "user_002",
                "user_name": "李四",
                "battery_level": 45,
                "signal_strength": 76,
                "status": "online",
                "last_sync": "2025-09-19T10:20:00",
                "firmware_version": "v2.1.4"
            }
        ],
        "total_count": 2,
        "online_count": 2,
        "offline_count": 0
    }


# ============================================================================
# 健康基线相关 API
# ============================================================================

@router.post("/health/baseline/generate", summary="生成健康基线")
async def generate_health_baseline(
    target_date: str,
    current_user: dict = Depends(get_current_user)
):
    """生成健康基线"""
    return {
        "target_date": target_date,
        "status": "success",
        "message": "健康基线生成成功",
        "baseline_id": f"baseline_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "generated_at": datetime.now().isoformat(),
        "records_processed": 1247
    }


@router.get("/health/baseline/status", summary="获取健康基线状态")
async def get_health_baseline_status(
    current_user: dict = Depends(get_current_user)
):
    """获取健康基线生成状态"""
    return {
        "status": "completed",
        "last_generated": "2025-09-19T02:15:00",
        "next_scheduled": "2025-09-20T02:15:00",
        "records_count": 1247,
        "coverage_rate": 94.2,
        "quality_score": 98.7
    }
"""
Personal BigScreen API 路由 - 个人大屏页面数据接口
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Query
from ...schemas.bigscreen import (
    HealthDataResponse, DeviceInfoResponse, AlertInfoResponse,
    HealthRecommendationResponse
)
from ...services.mock_data_service import MockDataService

router = APIRouter(prefix="/api", tags=["Personal BigScreen"])

@router.get("/personal/realtime-health")
async def get_personal_realtime_health(
    userId: str = Query(...),
    cardType: str = Query(...),
    deviceSn: str = Query(...)
):
    """获取个人实时健康数据"""
    health_data = MockDataService.generate_health_data(1)[0]
    health_data.deviceSn = deviceSn
    
    return {
        "status": "success",
        "data": {
            "heart_rate": health_data.heart_rate,
            "blood_oxygen": health_data.blood_oxygen,
            "temperature": health_data.temperature,
            "pressure_high": health_data.pressure_high,
            "pressure_low": health_data.pressure_low,
            "step": health_data.step,
            "distance": health_data.distance,
            "calorie": health_data.calorie,
            "stress": health_data.stress,
            "timestamp": health_data.timestamp
        }
    }

@router.get("/personal/history-health")
async def get_personal_history_health(
    userId: str = Query(...),
    cardType: str = Query(...),
    days: int = Query(7)
):
    """获取个人历史健康数据"""
    history_data = MockDataService.generate_health_data(days)
    
    return {
        "status": "success",
        "data": [
            {
                "heart_rate": item.heart_rate,
                "blood_oxygen": item.blood_oxygen,
                "temperature": item.temperature,
                "pressure_high": item.pressure_high,
                "pressure_low": item.pressure_low,
                "step": item.step,
                "distance": item.distance,
                "calorie": item.calorie,
                "stress": item.stress,
                "timestamp": item.timestamp
            }
            for item in history_data
        ]
    }

@router.get("/personal/ai-analysis")
async def get_personal_ai_analysis(
    userId: str = Query(...),
    cardType: str = Query(...),
    analysisType: str = Query("comprehensive")
):
    """获取个人AI分析结果"""
    import random
    
    analysis_results = {
        "overall_assessment": {
            "score": random.randint(75, 95),
            "level": random.choice(["优秀", "良好", "一般"]),
            "trend": random.choice(["上升", "稳定", "下降"])
        },
        "health_insights": [
            "您的心率变异性良好，说明心血管健康状况较佳",
            "血氧饱和度保持在正常范围，呼吸系统功能正常",
            "建议保持规律的运动习惯，有助于维持当前的健康水平"
        ],
        "risk_factors": [
            {
                "factor": "久坐时间过长",
                "level": "中等",
                "recommendation": "建议每小时起身活动5-10分钟"
            }
        ],
        "recommendations": MockDataService.generate_health_recommendations()
    }
    
    return {
        "status": "success",
        "data": analysis_results
    }

@router.get("/health/trends/analysis")
async def get_health_trends_analysis(
    deviceSn: str = Query(...),
    timeRange: str = Query("7d")
):
    """获取健康趋势分析"""
    import random
    
    trends_data = {
        "heart_rate": {
            "trend": random.choice(["上升", "下降", "稳定"]),
            "change_percentage": random.randint(-10, 15),
            "average": random.randint(70, 85),
            "max": random.randint(90, 120),
            "min": random.randint(60, 70)
        },
        "blood_oxygen": {
            "trend": random.choice(["上升", "下降", "稳定"]),
            "change_percentage": random.randint(-5, 8),
            "average": random.randint(96, 99),
            "max": 99,
            "min": random.randint(94, 96)
        },
        "temperature": {
            "trend": random.choice(["上升", "下降", "稳定"]),
            "change_percentage": random.randint(-3, 3),
            "average": round(random.uniform(36.2, 36.8), 1),
            "max": round(random.uniform(36.8, 37.2), 1),
            "min": round(random.uniform(36.0, 36.3), 1)
        },
        "activity": {
            "step_trend": random.choice(["上升", "下降", "稳定"]),
            "step_average": random.randint(8000, 12000),
            "calorie_trend": random.choice(["上升", "下降", "稳定"]),
            "calorie_average": random.randint(300, 600)
        }
    }
    
    return {
        "status": "success",
        "data": trends_data
    }

@router.get("/health/analysis/comprehensive")
async def get_comprehensive_health_analysis(
    deviceSn: str = Query(...),
    days: int = Query(30)
):
    """获取综合健康分析"""
    import random
    
    analysis_data = {
        "overall_score": random.randint(75, 95),
        "health_status": random.choice(["优秀", "良好", "一般", "需要关注"]),
        "key_metrics": {
            "heart_rate_score": random.randint(80, 95),
            "blood_oxygen_score": random.randint(85, 98),
            "temperature_score": random.randint(85, 95),
            "activity_score": random.randint(70, 90),
            "sleep_score": random.randint(75, 90)
        },
        "health_factors": {
            "cardiovascular": random.randint(75, 90),
            "respiratory": random.randint(80, 95),
            "metabolic": random.randint(70, 85),
            "physical_activity": random.randint(65, 85)
        },
        "improvement_areas": [
            {
                "area": "运动量",
                "current_score": random.randint(60, 75),
                "target_score": 85,
                "suggestions": ["增加有氧运动", "保持规律运动习惯"]
            },
            {
                "area": "睡眠质量",
                "current_score": random.randint(70, 80),
                "target_score": 90,
                "suggestions": ["调整作息时间", "改善睡眠环境"]
            }
        ]
    }
    
    return {
        "status": "success",
        "data": analysis_data
    }

@router.get("/device/info", response_model=DeviceInfoResponse)
async def get_device_info(deviceSn: str = Query(...)):
    """获取设备信息"""
    device = MockDataService.generate_devices(1)[0]
    device.deviceSn = deviceSn
    return device

@router.get("/device/user_org")
async def get_device_user_org(deviceSn: str = Query(...)):
    """获取设备用户组织信息"""
    user = MockDataService.generate_users(1)[0]
    return {
        "user_id": user.user_id,
        "user_name": user.user_name,
        "org_id": user.org_id,
        "dept_name": user.dept_name,
        "deviceSn": deviceSn
    }

@router.get("/personal/alerts")
async def get_personal_alerts(deviceSn: str = Query(...)):
    """获取个人告警"""
    alerts = MockDataService.generate_alerts(5)
    # 设置设备序列号
    for alert in alerts:
        alert.deviceSn = deviceSn
    return alerts

@router.get("/health/recommendations")
async def get_health_recommendations_for_device(
    deviceSn: str = Query(...),
    analysisType: str = Query("comprehensive")
):
    """获取设备健康建议"""
    recommendations = MockDataService.generate_health_recommendations()
    return {
        "deviceSn": deviceSn,
        "recommendations": recommendations
    }

@router.get("/health_data/latest")
async def get_latest_health_data(deviceSn: str = Query(...)):
    """获取最新健康数据"""
    health_data = MockDataService.generate_health_data(1)[0]
    health_data.deviceSn = deviceSn
    return {
        "status": "success",
        "data": health_data
    }

# 兼容旧API路径
@router.get("/get_personal_info")
async def get_personal_info(deviceSn: str = Query(...)):
    """获取个人信息（兼容旧API）"""
    user = MockDataService.generate_users(1)[0]
    user.deviceSn = deviceSn
    
    return {
        "user_id": user.user_id,
        "user_name": user.user_name,
        "real_name": user.user_name,
        "dept_name": user.dept_name,
        "org_id": user.org_id,
        "phone": user.phone,
        "email": user.email,
        "deviceSn": deviceSn,
        "device_status": "在线",
        "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
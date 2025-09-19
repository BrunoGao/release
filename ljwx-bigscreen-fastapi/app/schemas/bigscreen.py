"""
BigScreen API 响应模型定义
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

# 响应模型 - 用于API返回
class HealthScoreResponse(BaseModel):
    overall_score: int
    heart_rate_score: int
    blood_oxygen_score: int
    temperature_score: int
    pressure_score: int
    step_score: int
    calorie_score: int
    stress_score: int
    sleep_score: int

class StatisticsOverviewResponse(BaseModel):
    total_users: int
    active_devices: int
    health_data_count: int
    pending_alerts: int
    unread_messages: int
    alert_trend: str
    device_trend: str
    health_trend: str
    message_trend: str

class AlertInfoResponse(BaseModel):
    alert_id: str
    user_name: str
    dept_name: str
    alert_type: str
    alert_level: str
    alert_status: str
    alert_timestamp: str
    health_id: Optional[str]
    deviceSn: str

class DeviceInfoResponse(BaseModel):
    deviceSn: str
    user_name: str
    dept_name: str
    device_status: str
    last_seen: str
    battery_level: int

class MessageInfoResponse(BaseModel):
    message_id: str
    message_type: str
    content: str
    sender: str
    timestamp: str
    read_status: bool

class HealthDataResponse(BaseModel):
    health_id: str
    user_name: str
    dept_name: str
    deviceSn: str
    heart_rate: Optional[int]
    blood_oxygen: Optional[int]
    temperature: Optional[float]
    pressure_high: Optional[int]
    pressure_low: Optional[int]
    step: Optional[int]
    distance: Optional[float]
    calorie: Optional[float]
    stress: Optional[int]
    timestamp: str

class UserInfoResponse(BaseModel):
    user_id: str
    user_name: str
    dept_name: Optional[str]
    org_id: Optional[str]
    deviceSn: Optional[str]
    phone: Optional[str]
    email: str

class HealthBaselineResponse(BaseModel):
    baseline_score: int
    trend: str
    comparison: dict
    factors: dict

class HealthRecommendationResponse(BaseModel):
    id: str
    title: str
    content: str
    priority: str
    category: str

# 请求模型
class BaselineGenerateRequest(BaseModel):
    target_date: str

class AlertAcknowledgeRequest(BaseModel):
    alert_id: str
    acknowledged_by: str
    notes: Optional[str] = None
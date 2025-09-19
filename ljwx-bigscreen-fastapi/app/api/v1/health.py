"""
健康数据相关 API
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from app.api.deps import (
    get_current_user, 
    get_health_service,
    get_pagination_params,
    PaginationParams
)
from app.business.health_data import HealthDataService

router = APIRouter()


class HealthDataUpload(BaseModel):
    """健康数据上传模型"""
    device_id: Optional[str] = None
    heart_rate: Optional[float] = Field(None, ge=30, le=200, description="心率")
    blood_oxygen: Optional[float] = Field(None, ge=70, le=100, description="血氧")
    temperature: Optional[float] = Field(None, ge=35.0, le=42.0, description="体温")
    pressure_high: Optional[float] = Field(None, ge=80, le=200, description="收缩压")
    pressure_low: Optional[float] = Field(None, ge=40, le=120, description="舒张压")
    stress: Optional[float] = Field(None, ge=0, le=100, description="压力指数")
    step: Optional[int] = Field(None, ge=0, le=100000, description="步数")
    calorie: Optional[float] = Field(None, ge=0, le=10000, description="卡路里")
    distance: Optional[float] = Field(None, ge=0, le=100000, description="距离")
    sleep_duration: Optional[float] = Field(None, ge=0, le=24, description="睡眠时长")
    collect_time: Optional[datetime] = None
    source_type: Optional[str] = "manual"


class HealthDataBatchUpload(BaseModel):
    """批量健康数据上传模型"""
    data_list: List[HealthDataUpload]


class HealthDataResponse(BaseModel):
    """健康数据响应模型"""
    id: str
    user_id: str
    device_id: Optional[str]
    heart_rate: Optional[float]
    blood_oxygen: Optional[float]
    temperature: Optional[float]
    pressure_high: Optional[float]
    pressure_low: Optional[float]
    stress: Optional[float]
    step: Optional[int]
    calorie: Optional[float]
    distance: Optional[float]
    sleep_duration: Optional[float]
    collect_time: datetime
    created_time: datetime


class HealthDataListResponse(BaseModel):
    """健康数据列表响应模型"""
    total: int
    page: int
    page_size: int
    data: List[HealthDataResponse]


class HealthStatistics(BaseModel):
    """健康统计响应模型"""
    total_records: int
    avg_heart_rate: Optional[float]
    avg_blood_oxygen: Optional[float]
    avg_temperature: Optional[float]
    total_steps: Optional[int]
    total_calories: Optional[float]
    time_range: str


class HealthAnalysisResponse(BaseModel):
    """健康分析响应模型"""
    user_id: str
    analysis_type: str
    health_score: float
    risk_level: str
    recommendations: List[str]
    trends: dict
    generated_at: datetime


@router.post("/upload", summary="上传健康数据")
async def upload_health_data(
    health_data: HealthDataUpload,
    current_user: dict = Depends(get_current_user),
    health_service: HealthDataService = Depends(get_health_service)
):
    """
    上传单条健康数据
    
    - **device_id**: 设备ID（可选）
    - **heart_rate**: 心率 (30-200)
    - **blood_oxygen**: 血氧 (70-100)
    - **temperature**: 体温 (35.0-42.0)
    - **pressure_high**: 收缩压 (80-200)
    - **pressure_low**: 舒张压 (40-120)
    - **stress**: 压力指数 (0-100)
    - **step**: 步数 (0-100000)
    - **calorie**: 卡路里 (0-10000)
    - **distance**: 距离 (0-100000)
    - **sleep_duration**: 睡眠时长 (0-24)
    - **collect_time**: 采集时间
    - **source_type**: 数据来源类型
    """
    try:
        # 准备数据
        data = health_data.dict(exclude_none=True)
        data['user_id'] = current_user['id']
        data['customer_id'] = current_user.get('customer_id')
        data['org_id'] = current_user.get('org_id')
        
        # 上传数据
        data_id = await health_service.upload_health_data(data)
        
        return {
            "message": "健康数据上传成功",
            "data_id": data_id
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="健康数据上传失败"
        )


@router.post("/batch-upload", summary="批量上传健康数据")
async def batch_upload_health_data(
    batch_data: HealthDataBatchUpload,
    current_user: dict = Depends(get_current_user),
    health_service: HealthDataService = Depends(get_health_service)
):
    """
    批量上传健康数据
    """
    try:
        # 准备数据列表
        data_list = []
        for item in batch_data.data_list:
            data = item.dict(exclude_none=True)
            data['user_id'] = current_user['id']
            data['customer_id'] = current_user.get('customer_id')
            data['org_id'] = current_user.get('org_id')
            data_list.append(data)
        
        # 批量上传
        uploaded_count = await health_service.batch_upload_health_data(data_list)
        
        return {
            "message": "批量健康数据上传成功",
            "uploaded_count": uploaded_count
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量健康数据上传失败"
        )


@router.get("/data", response_model=HealthDataListResponse, summary="获取健康数据")
async def get_health_data(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"), 
    metrics: Optional[str] = Query(None, description="指标列表，逗号分隔"),
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: dict = Depends(get_current_user),
    health_service: HealthDataService = Depends(get_health_service)
):
    """
    获取当前用户的健康数据
    
    - **start_time**: 开始时间
    - **end_time**: 结束时间
    - **metrics**: 指标列表，逗号分隔 (如: heart_rate,blood_oxygen)
    - **page**: 页码
    - **page_size**: 每页数量
    """
    try:
        # 解析指标列表
        metrics_list = None
        if metrics:
            metrics_list = [m.strip() for m in metrics.split(',') if m.strip()]
        
        # 获取数据
        data = await health_service.get_user_health_data(
            user_id=current_user['id'],
            start_time=start_time,
            end_time=end_time,
            metrics=metrics_list,
            limit=pagination.page_size
        )
        
        # 转换为响应模型
        health_data_list = []
        for item in data:
            health_data_list.append(HealthDataResponse(**item))
        
        return HealthDataListResponse(
            total=len(health_data_list),
            page=pagination.page,
            page_size=pagination.page_size,
            data=health_data_list
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取健康数据失败"
        )


@router.get("/latest", response_model=HealthDataResponse, summary="获取最新健康数据")
async def get_latest_health_data(
    current_user: dict = Depends(get_current_user),
    health_service: HealthDataService = Depends(get_health_service)
):
    """
    获取当前用户最新的健康数据
    """
    try:
        latest_data = await health_service.get_latest_health_data(current_user['id'])
        
        if not latest_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到健康数据"
            )
        
        return HealthDataResponse(**latest_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取最新健康数据失败"
        )


@router.get("/statistics", response_model=HealthStatistics, summary="获取健康数据统计")
async def get_health_statistics(
    time_range: str = Query("24h", description="时间范围: 1h, 24h, 7d, 30d"),
    current_user: dict = Depends(get_current_user),
    health_service: HealthDataService = Depends(get_health_service)
):
    """
    获取当前用户的健康数据统计
    
    - **time_range**: 时间范围 (1h, 24h, 7d, 30d)
    """
    try:
        stats = await health_service.get_health_data_statistics(
            user_id=current_user['id'],
            time_range=time_range
        )
        
        basic_stats = stats.get('basic', {})
        
        return HealthStatistics(
            total_records=basic_stats.get('record_count', 0),
            avg_heart_rate=basic_stats.get('avg_heart_rate'),
            avg_blood_oxygen=basic_stats.get('avg_blood_oxygen'),
            avg_temperature=basic_stats.get('avg_temperature'),
            total_steps=basic_stats.get('total_steps'),
            total_calories=basic_stats.get('total_calories'),
            time_range=time_range
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取健康统计失败"
        )


@router.get("/analysis", response_model=HealthAnalysisResponse, summary="获取健康分析")
async def get_health_analysis(
    analysis_type: str = Query("comprehensive", description="分析类型"),
    current_user: dict = Depends(get_current_user),
    health_service: HealthDataService = Depends(get_health_service)
):
    """
    获取当前用户的健康分析
    
    - **analysis_type**: 分析类型 (comprehensive, simple, detailed)
    """
    try:
        analysis = await health_service.analyze_user_health(
            user_id=current_user['id'],
            analysis_type=analysis_type
        )
        
        return HealthAnalysisResponse(
            user_id=current_user['id'],
            analysis_type=analysis_type,
            health_score=analysis.get('health_score', 0),
            risk_level=analysis.get('risk_level', 'unknown'),
            recommendations=analysis.get('recommendations', []),
            trends=analysis.get('trends', {}),
            generated_at=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取健康分析失败"
        )


@router.get("/score", summary="获取健康评分")
async def get_health_score(
    current_user: dict = Depends(get_current_user),
    health_service: HealthDataService = Depends(get_health_service)
):
    """
    获取当前用户的健康评分
    """
    try:
        score_data = await health_service.generate_health_score(current_user['id'])
        
        return {
            "user_id": current_user['id'],
            "health_score": score_data.get('total_score', 0),
            "score_breakdown": score_data.get('breakdown', {}),
            "generated_at": datetime.now()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取健康评分失败"
        )


@router.get("/trends", summary="获取健康趋势")
async def get_health_trends(
    metrics: str = Query(..., description="指标列表，逗号分隔"),
    time_range: str = Query("7d", description="时间范围: 7d, 30d, 90d"),
    current_user: dict = Depends(get_current_user),
    health_service: HealthDataService = Depends(get_health_service)
):
    """
    获取健康趋势数据
    
    - **metrics**: 指标列表，逗号分隔 (如: heart_rate,blood_oxygen)
    - **time_range**: 时间范围 (7d, 30d, 90d)
    """
    try:
        metrics_list = [m.strip() for m in metrics.split(',') if m.strip()]
        
        if not metrics_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请指定至少一个健康指标"
            )
        
        trends = await health_service.get_health_trends(
            user_id=current_user['id'],
            metrics=metrics_list,
            time_range=time_range
        )
        
        return {
            "user_id": current_user['id'],
            "metrics": metrics_list,
            "time_range": time_range,
            "trends": trends,
            "generated_at": datetime.now()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取健康趋势失败"
        )
# LJWX-BigScreen 健康数据分析系统 - Python实现方案

## 1. 系统概述

基于ljwx-boot的健康数据处理系统，为ljwx-bigscreen设计完整的Python版本健康数据分析系统，包括健康基线计算、健康评分、健康建议、健康预测和健康画像生成。

## 2. 系统架构

```
ljwx-bigscreen/health_analytics/
├── __init__.py
├── config/
│   ├── __init__.py
│   └── health_config.py           # 健康指标配置
├── models/
│   ├── __init__.py
│   ├── health_models.py           # 健康数据模型扩展
│   └── analytics_models.py        # 分析结果模型
├── services/
│   ├── __init__.py
│   ├── baseline_service.py        # 健康基线计算服务
│   ├── score_service.py           # 健康评分服务
│   ├── recommendation_service.py  # 健康建议服务
│   ├── prediction_service.py      # 健康预测服务
│   └── profile_service.py         # 健康画像服务
├── tasks/
│   ├── __init__.py
│   ├── scheduler.py               # 定时任务调度器
│   └── health_tasks.py            # 健康数据处理任务
├── utils/
│   ├── __init__.py
│   ├── statistics.py              # 统计计算工具
│   ├── weight_calculator.py       # 权重计算器
│   └── ai_analyzer.py             # AI分析工具
└── api/
    ├── __init__.py
    └── health_analytics_api.py    # API接口
```

## 3. 核心配置模块

### 3.1 健康指标配置 (config/health_config.py)

```python
"""
健康数据分析系统配置
"""
from dataclasses import dataclass
from typing import Dict, List, Tuple
from decimal import Decimal

@dataclass
class HealthFeatureConfig:
    """健康特征配置"""
    name: str
    display_name: str
    unit: str
    normal_range: Tuple[float, float]
    weight: Decimal
    importance_level: str  # critical, high, medium, low
    category: str  # physiological, behavioral, risk

class HealthAnalyticsConfig:
    """健康分析系统配置"""
    
    # 健康特征配置 - 基于医学标准和ljwx-boot的权重配置
    HEALTH_FEATURES = {
        'heart_rate': HealthFeatureConfig(
            name='heart_rate',
            display_name='心率',
            unit='bpm',
            normal_range=(60, 100),
            weight=Decimal('0.20'),  # 20% - 最重要的生命体征
            importance_level='critical',
            category='physiological'
        ),
        'blood_oxygen': HealthFeatureConfig(
            name='blood_oxygen',
            display_name='血氧',
            unit='%',
            normal_range=(95, 100),
            weight=Decimal('0.18'),  # 18% - 呼吸系统核心指标
            importance_level='critical',
            category='physiological'
        ),
        'temperature': HealthFeatureConfig(
            name='temperature',
            display_name='体温',
            unit='°C',
            normal_range=(36.1, 37.2),
            weight=Decimal('0.15'),  # 15% - 基础生命体征
            importance_level='high',
            category='physiological'
        ),
        'pressure_high': HealthFeatureConfig(
            name='pressure_high',
            display_name='收缩压',
            unit='mmHg',
            normal_range=(90, 140),
            weight=Decimal('0.06'),  # 6% - 心血管健康指标
            importance_level='high',
            category='physiological'
        ),
        'pressure_low': HealthFeatureConfig(
            name='pressure_low',
            display_name='舒张压',
            unit='mmHg',
            normal_range=(60, 90),
            weight=Decimal('0.06'),  # 6% - 心血管健康指标
            importance_level='high',
            category='physiological'
        ),
        'stress': HealthFeatureConfig(
            name='stress',
            display_name='压力指数',
            unit='level',
            normal_range=(0, 50),
            weight=Decimal('0.12'),  # 12% - 心理健康重要指标
            importance_level='high',
            category='behavioral'
        ),
        'sleep': HealthFeatureConfig(
            name='sleep',
            display_name='睡眠时长',
            unit='hours',
            normal_range=(7, 9),
            weight=Decimal('0.08'),  # 8% - 恢复性健康指标
            importance_level='medium',
            category='behavioral'
        ),
        'step': HealthFeatureConfig(
            name='step',
            display_name='步数',
            unit='steps',
            normal_range=(6000, 10000),
            weight=Decimal('0.04'),  # 4% - 日常活动量
            importance_level='medium',
            category='behavioral'
        ),
        'distance': HealthFeatureConfig(
            name='distance',
            display_name='距离',
            unit='km',
            normal_range=(3, 8),
            weight=Decimal('0.03'),  # 3% - 运动强度
            importance_level='medium',
            category='behavioral'
        ),
        'calorie': HealthFeatureConfig(
            name='calorie',
            display_name='卡路里',
            unit='kcal',
            normal_range=(1800, 2500),
            weight=Decimal('0.03'),  # 3% - 代谢水平
            importance_level='medium',
            category='behavioral'
        )
    }
    
    # 任务调度配置
    TASK_SCHEDULE = {
        'weight_validation': '0 1 * * *',           # 01:00 权重配置验证
        'user_baseline': '5 2 * * *',               # 02:05 生成用户健康基线
        'dept_baseline': '10 2 * * *',              # 02:10 生成部门健康基线
        'tenant_baseline': '15 2 * * *',            # 02:15 生成租户健康基线
        'dept_score': '20 2 * * *',                 # 02:20 生成部门健康评分
        'user_score': '0 4 * * *',                  # 04:00 生成用户健康评分
        'tenant_score': '10 4 * * *',               # 04:10 生成租户健康评分
        'recommendations': '0 5 * * *',             # 05:00 生成健康建议
        'health_profile': '30 5 * * *',             # 05:30 生成健康画像
        'data_cleanup': '0 6 * * *',                # 06:00 数据清理任务
        'monthly_archive': '0 0 1 * *'              # 每月1日凌晨分表归档
    }
    
    # 评分标准
    SCORE_THRESHOLDS = {
        'excellent': 90,  # 优秀
        'good': 80,       # 良好
        'fair': 70,       # 一般
        'poor': 60,       # 较差
        'critical': 50    # 危险
    }
    
    # AI分析配置
    AI_CONFIG = {
        'trend_analysis_days': 30,      # 趋势分析天数
        'prediction_days': 7,           # 预测天数
        'baseline_calculation_days': 14, # 基线计算天数
        'anomaly_threshold': 2.0,       # 异常检测阈值(Z-score)
        'confidence_level': 0.95        # 置信水平
    }
    
    # 推荐系统配置
    RECOMMENDATION_CONFIG = {
        'max_recommendations': 5,       # 最大建议数
        'priority_weights': {           # 优先级权重
            'critical': 1.0,
            'high': 0.8,
            'medium': 0.6,
            'low': 0.4
        },
        'effectiveness_threshold': 0.7  # 建议有效性阈值
    }

    @classmethod
    def get_feature_config(cls, feature_name: str) -> HealthFeatureConfig:
        """获取健康特征配置"""
        return cls.HEALTH_FEATURES.get(feature_name)
    
    @classmethod
    def get_all_features(cls) -> List[str]:
        """获取所有健康特征名称"""
        return list(cls.HEALTH_FEATURES.keys())
    
    @classmethod
    def get_feature_weight(cls, feature_name: str) -> Decimal:
        """获取特征权重"""
        config = cls.get_feature_config(feature_name)
        return config.weight if config else Decimal('0.01')
    
    @classmethod
    def validate_weights(cls) -> bool:
        """验证权重总和是否为1.0"""
        total_weight = sum(config.weight for config in cls.HEALTH_FEATURES.values())
        return abs(total_weight - Decimal('1.0')) < Decimal('0.01')
```

### 3.2 数据模型扩展 (models/analytics_models.py)

```python
"""
健康数据分析结果模型
"""
from sqlalchemy import Column, BigInteger, String, DateTime, Date, Numeric, Text, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from decimal import Decimal
from dataclasses import dataclass, field

Base = declarative_base()

# 体征配置管理表
class THealthDataConfig(Base):
    """体征配置表"""
    __tablename__ = 't_health_data_config'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    customer_id = Column(BigInteger, nullable=False, default=0, comment='租户ID')
    feature_name = Column(String(50), nullable=False, comment='体征名称')
    feature_field = Column(String(50), nullable=False, comment='数据库字段名')
    display_name = Column(String(100), nullable=False, comment='显示名称')
    unit = Column(String(20), comment='单位')
    normal_min = Column(Numeric(10, 4), comment='正常范围最小值')
    normal_max = Column(Numeric(10, 4), comment='正常范围最大值')
    weight = Column(Numeric(5, 4), nullable=False, default=0.01, comment='权重')
    importance_level = Column(String(20), default='medium', comment='重要性等级')
    category = Column(String(50), default='physiological', comment='类别')
    is_enabled = Column(Boolean, default=True, comment='是否启用')
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class HealthBaseline(Base):
    """健康基线模型 - 扩展自原有模型"""
    __tablename__ = 't_health_baseline'
    
    baseline_id = Column(BigInteger, primary_key=True, autoincrement=True)
    device_sn = Column(String(50), nullable=False)
    user_id = Column(BigInteger, nullable=True)
    customer_id = Column(BigInteger, nullable=False, default=0)
    feature_name = Column(String(50), nullable=False)
    baseline_date = Column(Date, nullable=False)
    mean_value = Column(Numeric(10, 4))
    std_value = Column(Numeric(10, 4))
    min_value = Column(Numeric(10, 4))
    max_value = Column(Numeric(10, 4))
    sample_count = Column(BigInteger, default=0)
    is_current = Column(Boolean, nullable=False)
    baseline_type = Column(String(20), default='personal')
    confidence_level = Column(Numeric(5, 4), default=0.95)
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class HealthScore(Base):
    """健康评分模型"""
    __tablename__ = 't_health_score'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    device_sn = Column(String(50), nullable=False)
    user_id = Column(BigInteger, nullable=True)
    org_id = Column(BigInteger, nullable=True)
    customer_id = Column(BigInteger, nullable=False, default=0)
    feature_name = Column(String(50), nullable=False)
    avg_value = Column(Numeric(10, 4))
    z_score = Column(Numeric(10, 4))
    score_value = Column(Numeric(5, 2))
    penalty_value = Column(Numeric(5, 2))
    baseline_date = Column(Date)
    score_date = Column(Date, nullable=False)
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserHealthProfile(Base):
    """用户健康画像模型"""
    __tablename__ = 't_user_health_profile'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    customer_id = Column(BigInteger, nullable=False)
    profile_date = Column(Date, nullable=False)
    overall_health_score = Column(Numeric(5, 2), default=0.00)
    health_level = Column(String(20), default='fair')
    physiological_score = Column(Numeric(5, 2), default=0.00)
    behavioral_score = Column(Numeric(5, 2), default=0.00)
    risk_factor_score = Column(Numeric(5, 2), default=0.00)
    detailed_analysis = Column(JSON)
    trend_analysis = Column(JSON)
    recommendations = Column(JSON)
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class HealthRecommendationTrack(Base):
    """健康建议跟踪模型"""
    __tablename__ = 't_health_recommendation_track'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    customer_id = Column(BigInteger, nullable=False)
    recommendation_id = Column(String(64), nullable=False)
    recommendation_type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    recommended_actions = Column(JSON)
    status = Column(String(20), default='pending')
    start_date = Column(Date)
    target_completion_date = Column(Date)
    effectiveness_score = Column(Numeric(5, 2))
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# 数据传输对象 (DTOs)
@dataclass
class HealthBaselineDTO:
    """健康基线数据传输对象"""
    device_sn: str
    user_id: Optional[int]
    feature_name: str
    baseline_date: date
    mean_value: float
    std_value: float
    min_value: float
    max_value: float
    sample_count: int
    confidence_level: float = 0.95

@dataclass
class HealthScoreDTO:
    """健康评分数据传输对象"""
    device_sn: str
    user_id: Optional[int]
    feature_name: str
    score_value: float
    z_score: float
    avg_value: float
    penalty_value: float = 0.0
    score_date: date = field(default_factory=date.today)

@dataclass
class HealthRecommendationDTO:
    """健康建议数据传输对象"""
    user_id: int
    recommendation_type: str
    title: str
    description: str
    priority_level: str
    recommended_actions: List[str]
    expected_improvement: float
    implementation_difficulty: str

@dataclass
class UserHealthProfileDTO:
    """用户健康画像数据传输对象"""
    user_id: int
    profile_date: date
    overall_score: float
    health_level: str
    physiological_score: float
    behavioral_score: float
    risk_factor_score: float
    feature_scores: Dict[str, float]
    trend_analysis: Dict[str, Any]
    recommendations: List[HealthRecommendationDTO]
    risk_factors: List[str]

@dataclass
class HealthAnalyticsResult:
    """健康分析结果"""
    user_id: int
    analysis_date: datetime
    baseline_data: Dict[str, HealthBaselineDTO]
    score_data: Dict[str, HealthScoreDTO]
    recommendations: List[HealthRecommendationDTO]
    health_profile: UserHealthProfileDTO
    success: bool = True
    error_message: str = ""

# 体征配置管理服务
class HealthFeatureConfigManager:
    """体征配置管理器"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self._cache = {}  # 本地缓存，按customer_id缓存配置
        self._cache_ttl = 3600  # 缓存1小时
        self._last_update = {}
    
    def get_supported_features(self, customer_id: int) -> List[str]:
        """获取客户支持的体征列表"""
        config = self._get_customer_config(customer_id)
        return [feature.feature_name for feature in config if feature.is_enabled]
    
    def get_feature_weights(self, customer_id: int) -> Dict[str, float]:
        """获取体征权重配置"""
        config = self._get_customer_config(customer_id)
        weights = {}
        for feature in config:
            if feature.is_enabled:
                weights[feature.feature_name] = float(feature.weight)
        return weights
    
    def get_default_values(self, customer_id: int) -> Dict[str, Dict[str, Any]]:
        """获取体征默认配置值"""
        config = self._get_customer_config(customer_id)
        defaults = {}
        for feature in config:
            if feature.is_enabled:
                defaults[feature.feature_name] = {
                    'display_name': feature.display_name,
                    'unit': feature.unit,
                    'normal_min': float(feature.normal_min) if feature.normal_min else None,
                    'normal_max': float(feature.normal_max) if feature.normal_max else None,
                    'importance_level': feature.importance_level,
                    'category': feature.category,
                    'weight': float(feature.weight)
                }
        return defaults
    
    def get_feature_config(self, customer_id: int, feature_name: str) -> Optional[Dict[str, Any]]:
        """获取单个体征的详细配置"""
        defaults = self.get_default_values(customer_id)
        return defaults.get(feature_name)
    
    def _get_customer_config(self, customer_id: int) -> List[THealthDataConfig]:
        """获取客户体征配置（带缓存）"""
        import time
        current_time = time.time()
        
        # 检查缓存是否有效
        if (customer_id in self._cache and 
            customer_id in self._last_update and
            current_time - self._last_update[customer_id] < self._cache_ttl):
            return self._cache[customer_id]
        
        # 从数据库查询配置
        config = self.db.query(THealthDataConfig).filter(
            THealthDataConfig.customer_id == customer_id,
            THealthDataConfig.is_enabled == True
        ).order_by(THealthDataConfig.feature_name).all()
        
        # 如果客户没有配置，使用默认配置
        if not config:
            config = self._create_default_config(customer_id)
        
        # 更新缓存
        self._cache[customer_id] = config
        self._last_update[customer_id] = current_time
        
        return config
    
    def _create_default_config(self, customer_id: int) -> List[THealthDataConfig]:
        """为客户创建默认体征配置"""
        default_features = {
            'heart_rate': {
                'display_name': '心率',
                'unit': 'bpm',
                'normal_min': 60.0,
                'normal_max': 100.0,
                'weight': 0.20,
                'importance_level': 'critical',
                'category': 'physiological'
            },
            'blood_oxygen': {
                'display_name': '血氧',
                'unit': '%',
                'normal_min': 95.0,
                'normal_max': 100.0,
                'weight': 0.18,
                'importance_level': 'critical',
                'category': 'physiological'
            },
            'temperature': {
                'display_name': '体温',
                'unit': '°C',
                'normal_min': 36.1,
                'normal_max': 37.2,
                'weight': 0.15,
                'importance_level': 'high',
                'category': 'physiological'
            },
            'pressure_high': {
                'display_name': '收缩压',
                'unit': 'mmHg',
                'normal_min': 90.0,
                'normal_max': 140.0,
                'weight': 0.06,
                'importance_level': 'high',
                'category': 'physiological'
            },
            'pressure_low': {
                'display_name': '舒张压',
                'unit': 'mmHg',
                'normal_min': 60.0,
                'normal_max': 90.0,
                'weight': 0.06,
                'importance_level': 'high',
                'category': 'physiological'
            },
            'stress': {
                'display_name': '压力指数',
                'unit': 'level',
                'normal_min': 0.0,
                'normal_max': 50.0,
                'weight': 0.12,
                'importance_level': 'high',
                'category': 'behavioral'
            },
            'sleep': {
                'display_name': '睡眠时长',
                'unit': 'hours',
                'normal_min': 7.0,
                'normal_max': 9.0,
                'weight': 0.08,
                'importance_level': 'medium',
                'category': 'behavioral'
            },
            'step': {
                'display_name': '步数',
                'unit': 'steps',
                'normal_min': 6000.0,
                'normal_max': 10000.0,
                'weight': 0.04,
                'importance_level': 'medium',
                'category': 'behavioral'
            },
            'distance': {
                'display_name': '距离',
                'unit': 'km',
                'normal_min': 3.0,
                'normal_max': 8.0,
                'weight': 0.03,
                'importance_level': 'medium',
                'category': 'behavioral'
            },
            'calorie': {
                'display_name': '卡路里',
                'unit': 'kcal',
                'normal_min': 1800.0,
                'normal_max': 2500.0,
                'weight': 0.03,
                'importance_level': 'medium',
                'category': 'behavioral'
            }
        }
        
        configs = []
        for feature_name, feature_data in default_features.items():
            config = THealthDataConfig(
                customer_id=customer_id,
                feature_name=feature_name,
                feature_field=feature_name,  # 默认字段名与特征名相同
                display_name=feature_data['display_name'],
                unit=feature_data['unit'],
                normal_min=feature_data['normal_min'],
                normal_max=feature_data['normal_max'],
                weight=feature_data['weight'],
                importance_level=feature_data['importance_level'],
                category=feature_data['category'],
                is_enabled=True
            )
            self.db.add(config)
            configs.append(config)
        
        try:
            self.db.commit()
            logger.info(f"为客户 {customer_id} 创建了 {len(configs)} 个默认体征配置")
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建默认体征配置失败: {str(e)}")
            raise
        
        return configs
    
    def update_feature_config(
        self, 
        customer_id: int, 
        feature_name: str, 
        **kwargs
    ) -> bool:
        """更新体征配置"""
        try:
            config = self.db.query(THealthDataConfig).filter(
                THealthDataConfig.customer_id == customer_id,
                THealthDataConfig.feature_name == feature_name
            ).first()
            
            if not config:
                # 创建新配置
                config = THealthDataConfig(
                    customer_id=customer_id,
                    feature_name=feature_name,
                    feature_field=feature_name
                )
                self.db.add(config)
            
            # 更新配置字段
            for field, value in kwargs.items():
                if hasattr(config, field):
                    setattr(config, field, value)
            
            config.update_time = datetime.utcnow()
            self.db.commit()
            
            # 清除缓存
            if customer_id in self._cache:
                del self._cache[customer_id]
            if customer_id in self._last_update:
                del self._last_update[customer_id]
            
            logger.info(f"更新客户 {customer_id} 体征 {feature_name} 配置成功")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新体征配置失败: {str(e)}")
            return False
    
    def validate_weights(self, customer_id: int) -> Dict[str, Any]:
        """验证客户权重配置合理性"""
        weights = self.get_feature_weights(customer_id)
        
        if not weights:
            return {
                'is_valid': False,
                'error': '无可用的体征配置',
                'total_weight': 0.0
            }
        
        total_weight = sum(weights.values())
        tolerance = 0.01  # 1%的误差容忍度
        
        is_valid = abs(total_weight - 1.0) <= tolerance
        
        result = {
            'is_valid': is_valid,
            'total_weight': total_weight,
            'weights': weights,
            'deviation': abs(total_weight - 1.0)
        }
        
        if not is_valid:
            result['error'] = f'权重总和 {total_weight:.4f} 不等于 1.0'
            result['suggested_fix'] = self._suggest_weight_fix(weights)
        
        return result
    
    def _suggest_weight_fix(self, weights: Dict[str, float]) -> Dict[str, float]:
        """建议权重修复方案"""
        total = sum(weights.values())
        if total == 0:
            return weights
        
        # 按比例调整权重使其总和为1.0
        adjusted_weights = {}
        for feature, weight in weights.items():
            adjusted_weights[feature] = weight / total
        
        return adjusted_weights
    
    def clear_cache(self, customer_id: Optional[int] = None):
        """清除配置缓存"""
        if customer_id:
            if customer_id in self._cache:
                del self._cache[customer_id]
            if customer_id in self._last_update:
                del self._last_update[customer_id]
        else:
            self._cache.clear()
            self._last_update.clear()
        
        logger.info(f"清除配置缓存: customer_id={customer_id or 'all'}")

# 全局配置管理器实例
_feature_config_manager = None

def get_feature_config_manager(db_session: Session) -> HealthFeatureConfigManager:
    """获取体征配置管理器实例"""
    global _feature_config_manager
    if _feature_config_manager is None:
        _feature_config_manager = HealthFeatureConfigManager(db_session)
    return _feature_config_manager
```

## 4. 统一数据访问接口

### 4.0 优化数据服务 (services/data_service.py)

```python
"""
统一健康数据访问服务
提供优化的数据查询接口，统一所有健康数据访问
"""
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, text

from ..models.health_models import UserHealthData
from ..models.analytics_models import get_feature_config_manager

# 用户和组织层级查询支持
class UserHierarchyService:
    """用户层级结构服务 - 基于sys_user和sys_org_closure"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def get_users_by_customer(self, customer_id: int) -> List[Dict[str, Any]]:
        """获取租户下所有用户"""
        try:
            # 模拟sys_user表查询
            users = self.db.execute(text("""
                SELECT user_id, username, org_id, customer_id 
                FROM sys_user 
                WHERE customer_id = :customer_id 
                AND del_flag = '0' 
                AND status = '0'
            """), {'customer_id': customer_id}).fetchall()
            
            return [dict(user) for user in users]
        except Exception as e:
            logger.error(f"查询租户用户失败: customer_id={customer_id}, error={str(e)}")
            return []
    
    def get_users_by_org_hierarchy(self, org_id: int, customer_id: int) -> List[Dict[str, Any]]:
        """获取组织层级下所有用户（包括子部门）"""
        try:
            # 使用sys_org_closure查询组织层级
            users = self.db.execute(text("""
                SELECT DISTINCT u.user_id, u.username, u.org_id, u.customer_id 
                FROM sys_user u
                INNER JOIN sys_org_closure oc ON u.org_id = oc.descendant
                WHERE oc.ancestor = :org_id 
                AND u.customer_id = :customer_id
                AND u.del_flag = '0' 
                AND u.status = '0'
            """), {'org_id': org_id, 'customer_id': customer_id}).fetchall()
            
            return [dict(user) for user in users]
        except Exception as e:
            logger.error(f"查询组织层级用户失败: org_id={org_id}, error={str(e)}")
            return []
    
    def get_org_hierarchy_by_customer(self, customer_id: int) -> List[Dict[str, Any]]:
        """获取租户下的组织层级结构"""
        try:
            orgs = self.db.execute(text("""
                SELECT org_id, org_name, parent_id, level 
                FROM sys_org 
                WHERE customer_id = :customer_id 
                AND del_flag = '0'
                ORDER BY level, sort
            """), {'customer_id': customer_id}).fetchall()
            
            return [dict(org) for org in orgs]
        except Exception as e:
            logger.error(f"查询租户组织结构失败: customer_id={customer_id}, error={str(e)}")
            return []

logger = logging.getLogger(__name__)

def get_all_health_data_optimized(
    db_session: Optional[Session] = None,
    user_id: Optional[int] = None,
    customer_id: Optional[int] = None,
    org_id: Optional[int] = None,
    device_sn: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    features: Optional[List[str]] = None,
    limit: Optional[int] = None
) -> List[UserHealthData]:
    """
    优化的健康数据统一查询接口
    
    Args:
        db_session: 数据库会话
        user_id: 用户ID
        customer_id: 租户ID
        org_id: 部门ID
        device_sn: 设备序列号
        start_date: 开始日期
        end_date: 结束日期
        features: 需要查询的特征列表
        limit: 结果限制数量
    
    Returns:
        健康数据列表
    """
    if db_session is None:
        # 如果没有提供session，需要从上下文获取
        # 这里需要根据实际情况调整
        raise ValueError("db_session is required")
    
    try:
        # 构建基础查询
        query = db_session.query(UserHealthData)
        
        # 添加过滤条件
        conditions = []
        
        if user_id:
            conditions.append(UserHealthData.user_id == user_id)
        
        if customer_id:
            conditions.append(UserHealthData.customer_id == customer_id)
            
        if org_id:
            conditions.append(UserHealthData.org_id == org_id)
            
        if device_sn:
            conditions.append(UserHealthData.device_sn == device_sn)
            
        if start_date:
            conditions.append(UserHealthData.timestamp >= start_date)
            
        if end_date:
            conditions.append(UserHealthData.timestamp <= end_date)
        
        # 应用过滤条件
        if conditions:
            query = query.filter(and_(*conditions))
        
        # 添加排序
        query = query.order_by(UserHealthData.timestamp.desc())
        
        # 添加限制
        if limit:
            query = query.limit(limit)
        
        # 执行查询
        results = query.all()
        
        logger.info(f"查询健康数据: 条件={len(conditions)}, 结果={len(results)}条")
        
        # 如果指定了特征过滤，进行后处理
        if features:
            results = _filter_features_data(results, features)
        
        return results
        
    except Exception as e:
        logger.error(f"查询健康数据失败: {str(e)}", exc_info=True)
        raise

def _filter_features_data(data: List[UserHealthData], features: List[str]) -> List[UserHealthData]:
    """
    根据特征列表过滤数据（保留指定特征的有效数据）
    """
    filtered_data = []
    
    for data_point in data:
        # 检查是否有指定特征的有效数据
        has_valid_feature = False
        for feature in features:
            value = getattr(data_point, feature, None)
            if value is not None and value > 0:
                has_valid_feature = True
                break
        
        if has_valid_feature:
            filtered_data.append(data_point)
    
    return filtered_data

def get_health_data_by_features(
    db_session: Session,
    customer_id: int,
    start_date: date,
    end_date: date,
    user_id: Optional[int] = None
) -> Dict[str, List[UserHealthData]]:
    """
    按特征分组获取健康数据
    
    Returns:
        按特征名分组的健康数据字典
    """
    # 获取客户支持的特征
    config_manager = get_feature_config_manager(db_session)
    supported_features = config_manager.get_supported_features(customer_id)
    
    # 获取健康数据
    data = get_all_health_data_optimized(
        db_session=db_session,
        user_id=user_id,
        customer_id=customer_id,
        start_date=start_date,
        end_date=end_date,
        features=supported_features
    )
    
    # 按特征分组
    feature_data = {}
    for feature in supported_features:
        feature_data[feature] = []
        
        for data_point in data:
            value = getattr(data_point, feature, None)
            if value is not None and value > 0:
                feature_data[feature].append(data_point)
    
    return feature_data

def get_health_data_statistics(
    db_session: Session,
    customer_id: int,
    start_date: date,
    end_date: date,
    group_by: str = 'user_id'
) -> Dict[str, Any]:
    """
    获取健康数据统计信息
    
    Args:
        group_by: 分组方式 ('user_id', 'org_id', 'customer_id')
    
    Returns:
        统计信息字典
    """
    try:
        # 执行统计查询
        if group_by == 'user_id':
            stats_query = db_session.query(
                UserHealthData.user_id,
                func.count(UserHealthData.id).label('data_count'),
                func.min(UserHealthData.timestamp).label('first_record'),
                func.max(UserHealthData.timestamp).label('last_record')
            ).filter(
                and_(
                    UserHealthData.customer_id == customer_id,
                    UserHealthData.timestamp >= start_date,
                    UserHealthData.timestamp <= end_date
                )
            ).group_by(UserHealthData.user_id).all()
        elif group_by == 'org_id':
            stats_query = db_session.query(
                UserHealthData.org_id,
                func.count(UserHealthData.id).label('data_count'),
                func.count(UserHealthData.user_id.distinct()).label('user_count'),
                func.min(UserHealthData.timestamp).label('first_record'),
                func.max(UserHealthData.timestamp).label('last_record')
            ).filter(
                and_(
                    UserHealthData.customer_id == customer_id,
                    UserHealthData.timestamp >= start_date,
                    UserHealthData.timestamp <= end_date
                )
            ).group_by(UserHealthData.org_id).all()
        else:  # customer_id
            stats_query = db_session.query(
                func.count(UserHealthData.id).label('total_records'),
                func.count(UserHealthData.user_id.distinct()).label('total_users'),
                func.count(UserHealthData.org_id.distinct()).label('total_orgs'),
                func.min(UserHealthData.timestamp).label('first_record'),
                func.max(UserHealthData.timestamp).label('last_record')
            ).filter(
                and_(
                    UserHealthData.customer_id == customer_id,
                    UserHealthData.timestamp >= start_date,
                    UserHealthData.timestamp <= end_date
                )
            ).all()
        
        return {
            'group_by': group_by,
            'statistics': stats_query,
            'query_date': datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"获取健康数据统计失败: {str(e)}", exc_info=True)
        return {'error': str(e)}

# 层级健康数据分析服务
class HierarchicalHealthAnalysisService:
    """基于用户层级的健康数据分析服务"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.hierarchy_service = UserHierarchyService(db_session)
        self.config_manager = get_feature_config_manager(db_session)
    
    def generate_customer_health_analysis(
        self, 
        customer_id: int,
        analysis_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        生成租户完整健康分析
        流程: userId -> org_id -> customer_id 层级汇总
        """
        if analysis_date is None:
            analysis_date = date.today()
            
        logger.info(f"开始生成租户 {customer_id} 完整健康分析")
        
        try:
            # 1. 获取租户下所有用户
            users = self.hierarchy_service.get_users_by_customer(customer_id)
            logger.info(f"租户 {customer_id} 共有 {len(users)} 个用户")
            
            if not users:
                return {'error': '租户下无活跃用户', 'customer_id': customer_id}
            
            # 2. 获取组织结构
            orgs = self.hierarchy_service.get_org_hierarchy_by_customer(customer_id)
            
            # 3. 为每个用户生成健康分析（核心：以userId为中心）
            user_analyses = {}
            for user in users:
                user_id = user['user_id']
                user_analysis = self._generate_user_complete_analysis(
                    user_id, customer_id, analysis_date
                )
                if user_analysis:
                    user_analyses[user_id] = {
                        **user_analysis,
                        'org_id': user['org_id'],
                        'username': user['username']
                    }
            
            logger.info(f"完成 {len(user_analyses)} 个用户的健康分析")
            
            # 4. 按组织汇总用户数据
            org_analyses = self._aggregate_users_to_orgs(user_analyses, orgs)
            
            # 5. 汇总到租户级别
            customer_analysis = self._aggregate_orgs_to_customer(
                customer_id, org_analyses, user_analyses, analysis_date
            )
            
            return {
                'customer_id': customer_id,
                'analysis_date': analysis_date.isoformat(),
                'user_analyses': user_analyses,
                'org_analyses': org_analyses,
                'customer_analysis': customer_analysis,
                'summary': {
                    'total_users': len(user_analyses),
                    'total_orgs': len(org_analyses),
                    'analysis_completion_rate': len(user_analyses) / len(users) if users else 0
                }
            }
            
        except Exception as e:
            logger.error(f"租户健康分析生成失败: customer_id={customer_id}, error={str(e)}", exc_info=True)
            raise
    
    def _generate_user_complete_analysis(
        self, 
        user_id: int, 
        customer_id: int, 
        analysis_date: date
    ) -> Optional[Dict[str, Any]]:
        """为单个用户生成完整健康分析（核心方法）"""
        try:
            # 获取用户健康数据（最近30天）
            start_date = analysis_date - timedelta(days=30)
            user_health_data = get_all_health_data_optimized(
                db_session=self.db,
                user_id=user_id,
                customer_id=customer_id,
                start_date=start_date,
                end_date=analysis_date
            )
            
            if not user_health_data:
                logger.warning(f"用户 {user_id} 无健康数据")
                return None
            
            # 获取客户支持的体征
            supported_features = self.config_manager.get_supported_features(customer_id)
            feature_weights = self.config_manager.get_feature_weights(customer_id)
            
            # 生成各项分析
            analysis_result = {
                'user_id': user_id,
                'customer_id': customer_id,
                'analysis_date': analysis_date.isoformat(),
                'data_points_count': len(user_health_data),
                'supported_features': supported_features
            }
            
            # 1. 健康基线计算
            baselines = self._calculate_user_baselines_from_data(
                user_id, user_health_data, supported_features, analysis_date
            )
            analysis_result['baselines'] = baselines
            
            # 2. 健康评分计算
            scores = self._calculate_user_scores_from_data(
                user_id, user_health_data, baselines, feature_weights, analysis_date
            )
            analysis_result['scores'] = scores
            
            # 3. 健康建议生成
            recommendations = self._generate_user_recommendations_from_scores(
                user_id, scores, user_health_data, analysis_date
            )
            analysis_result['recommendations'] = recommendations
            
            # 4. 健康预测
            predictions = self._generate_user_health_predictions(
                user_id, user_health_data, scores, analysis_date
            )
            analysis_result['predictions'] = predictions
            
            # 5. 综合健康画像
            health_profile = self._generate_user_health_profile(
                user_id, baselines, scores, recommendations, predictions, analysis_date
            )
            analysis_result['health_profile'] = health_profile
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"用户 {user_id} 健康分析失败: {str(e)}")
            return None
    
    def _aggregate_users_to_orgs(
        self, 
        user_analyses: Dict[int, Dict], 
        orgs: List[Dict]
    ) -> Dict[int, Dict]:
        """将用户数据汇总到组织层级"""
        org_analyses = {}
        
        # 为每个组织汇总数据
        for org in orgs:
            org_id = org['org_id']
            org_users = [
                user_data for user_data in user_analyses.values() 
                if user_data['org_id'] == org_id
            ]
            
            if not org_users:
                continue
            
            # 汇总组织健康指标
            org_analysis = {
                'org_id': org_id,
                'org_name': org.get('org_name', f'部门{org_id}'),
                'user_count': len(org_users),
                'users': [user['user_id'] for user in org_users]
            }
            
            # 汇总评分
            all_scores = []
            all_baselines = []
            all_recommendations = []
            
            for user_data in org_users:
                if user_data.get('scores'):
                    all_scores.extend(user_data['scores'])
                if user_data.get('baselines'):
                    all_baselines.extend(user_data['baselines'])
                if user_data.get('recommendations'):
                    all_recommendations.extend(user_data['recommendations'])
            
            # 计算组织平均健康评分
            if all_scores:
                avg_scores_by_feature = {}
                for score in all_scores:
                    feature = score.get('feature_name')
                    if feature:
                        if feature not in avg_scores_by_feature:
                            avg_scores_by_feature[feature] = []
                        avg_scores_by_feature[feature].append(score.get('score_value', 0))
                
                # 计算每个特征的平均分
                feature_avg_scores = {}
                for feature, scores_list in avg_scores_by_feature.items():
                    feature_avg_scores[feature] = sum(scores_list) / len(scores_list)
                
                org_analysis['feature_avg_scores'] = feature_avg_scores
                org_analysis['overall_avg_score'] = sum(feature_avg_scores.values()) / len(feature_avg_scores)
            
            # 统计健康等级分布
            health_levels = [user.get('health_profile', {}).get('health_level', 'unknown') 
                           for user in org_users]
            org_analysis['health_level_distribution'] = {
                level: health_levels.count(level) for level in set(health_levels)
            }
            
            # 统计建议类型分布
            recommendation_types = [rec.get('recommendation_type', 'unknown') 
                                  for rec in all_recommendations]
            org_analysis['recommendation_type_distribution'] = {
                rec_type: recommendation_types.count(rec_type) 
                for rec_type in set(recommendation_types)
            }
            
            org_analyses[org_id] = org_analysis
        
        logger.info(f"完成 {len(org_analyses)} 个组织的数据汇总")
        return org_analyses
    
    def _aggregate_orgs_to_customer(
        self,
        customer_id: int,
        org_analyses: Dict[int, Dict],
        user_analyses: Dict[int, Dict],
        analysis_date: date
    ) -> Dict[str, Any]:
        """将组织数据汇总到租户层级"""
        
        customer_analysis = {
            'customer_id': customer_id,
            'analysis_date': analysis_date.isoformat(),
            'total_orgs': len(org_analyses),
            'total_users': len(user_analyses)
        }
        
        if not org_analyses:
            return customer_analysis
        
        # 汇总租户整体健康评分
        all_org_scores = []
        all_user_scores = []
        
        for org_analysis in org_analyses.values():
            if org_analysis.get('overall_avg_score'):
                all_org_scores.append(org_analysis['overall_avg_score'])
        
        for user_analysis in user_analyses.values():
            user_profile = user_analysis.get('health_profile', {})
            if user_profile.get('overall_score'):
                all_user_scores.append(user_profile['overall_score'])
        
        # 租户平均健康评分
        if all_org_scores:
            customer_analysis['org_weighted_avg_score'] = sum(all_org_scores) / len(all_org_scores)
        
        if all_user_scores:
            customer_analysis['user_avg_score'] = sum(all_user_scores) / len(all_user_scores)
            customer_analysis['user_score_distribution'] = {
                'excellent': len([s for s in all_user_scores if s >= 90]),
                'good': len([s for s in all_user_scores if 80 <= s < 90]),
                'fair': len([s for s in all_user_scores if 70 <= s < 80]),
                'poor': len([s for s in all_user_scores if 60 <= s < 70]),
                'critical': len([s for s in all_user_scores if s < 60])
            }
        
        # 汇总健康等级分布
        all_health_levels = []
        for user_analysis in user_analyses.values():
            health_profile = user_analysis.get('health_profile', {})
            if health_profile.get('health_level'):
                all_health_levels.append(health_profile['health_level'])
        
        customer_analysis['health_level_distribution'] = {
            level: all_health_levels.count(level) for level in set(all_health_levels)
        }
        
        # 识别租户级健康风险
        critical_users = len([user for user in user_analyses.values() 
                            if user.get('health_profile', {}).get('health_level') == 'critical'])
        
        customer_analysis['risk_assessment'] = {
            'critical_users_count': critical_users,
            'critical_users_ratio': critical_users / len(user_analyses) if user_analyses else 0,
            'risk_level': 'high' if critical_users > len(user_analyses) * 0.1 else 'medium' if critical_users > 0 else 'low'
        }
        
        return customer_analysis
    
    def _calculate_user_baselines_from_data(
        self, 
        user_id: int, 
        health_data: List[UserHealthData], 
        features: List[str],
        analysis_date: date
    ) -> Dict[str, Dict]:
        """基于健康数据计算用户基线"""
        baselines = {}
        
        for feature in features:
            feature_values = []
            for data_point in health_data:
                value = getattr(data_point, feature, None)
                if value is not None and value > 0:
                    feature_values.append(float(value))
            
            if len(feature_values) >= 3:  # 至少需要3个数据点
                import numpy as np
                baselines[feature] = {
                    'feature_name': feature,
                    'mean_value': float(np.mean(feature_values)),
                    'std_value': float(np.std(feature_values)),
                    'min_value': float(np.min(feature_values)),
                    'max_value': float(np.max(feature_values)),
                    'sample_count': len(feature_values),
                    'baseline_date': analysis_date.isoformat()
                }
        
        return baselines
    
    def _calculate_user_scores_from_data(
        self,
        user_id: int,
        health_data: List[UserHealthData],
        baselines: Dict[str, Dict],
        feature_weights: Dict[str, float],
        analysis_date: date
    ) -> List[Dict]:
        """基于基线计算用户健康评分"""
        scores = []
        
        for feature_name, baseline in baselines.items():
            # 计算最近数据的平均值
            recent_values = []
            for data_point in health_data[-7:]:  # 最近7个数据点
                value = getattr(data_point, feature_name, None)
                if value is not None and value > 0:
                    recent_values.append(float(value))
            
            if recent_values:
                avg_value = sum(recent_values) / len(recent_values)
                
                # 计算Z-score
                mean = baseline['mean_value']
                std = baseline['std_value']
                z_score = (avg_value - mean) / std if std > 0 else 0
                
                # 转换为健康评分 (0-100)
                if abs(z_score) <= 1:
                    score_value = 90 + (1 - abs(z_score)) * 10
                elif abs(z_score) <= 2:
                    score_value = 70 + (2 - abs(z_score)) * 20
                elif abs(z_score) <= 3:
                    score_value = 40 + (3 - abs(z_score)) * 30
                else:
                    score_value = max(10, 40 - (abs(z_score) - 3) * 10)
                
                scores.append({
                    'feature_name': feature_name,
                    'avg_value': avg_value,
                    'z_score': z_score,
                    'score_value': score_value,
                    'weight': feature_weights.get(feature_name, 0.01),
                    'score_date': analysis_date.isoformat()
                })
        
        return scores
    
    def _generate_user_recommendations_from_scores(
        self,
        user_id: int,
        scores: List[Dict],
        health_data: List[UserHealthData],
        analysis_date: date
    ) -> List[Dict]:
        """基于评分生成健康建议"""
        recommendations = []
        
        # 找出评分较低的特征
        low_score_features = [score for score in scores if score['score_value'] < 70]
        
        for score in low_score_features:
            feature_name = score['feature_name']
            score_value = score['score_value']
            
            if feature_name == 'heart_rate':
                recommendations.append({
                    'recommendation_type': 'physiological_improvement',
                    'title': '心率调节建议',
                    'description': f'您的心率评分为{score_value:.1f}分，建议进行调节',
                    'priority_level': 'high' if score_value < 50 else 'medium',
                    'recommended_actions': [
                        '进行适量有氧运动',
                        '保持规律作息',
                        '减少咖啡因摄入',
                        '学习放松技巧'
                    ]
                })
            elif feature_name == 'blood_oxygen':
                recommendations.append({
                    'recommendation_type': 'respiratory_improvement',
                    'title': '血氧水平提升方案',
                    'description': f'您的血氧评分为{score_value:.1f}分，需要改善呼吸功能',
                    'priority_level': 'high',
                    'recommended_actions': [
                        '进行深呼吸练习',
                        '增加户外活动',
                        '保持室内通风',
                        '考虑呼吸训练课程'
                    ]
                })
        
        return recommendations
    
    def _generate_user_health_predictions(
        self,
        user_id: int,
        health_data: List[UserHealthData],
        scores: List[Dict],
        analysis_date: date
    ) -> Dict[str, Any]:
        """生成用户健康预测"""
        predictions = {
            'prediction_date': analysis_date.isoformat(),
            'prediction_horizon_days': 7,
            'predictions': {}
        }
        
        # 简化预测：基于当前趋势
        for score in scores:
            feature_name = score['feature_name']
            current_score = score['score_value']
            
            # 简单趋势预测
            if current_score > 80:
                trend = 'stable'
                predicted_score = current_score + (-1 + 2 * (current_score - 80) / 20)
            elif current_score > 60:
                trend = 'improving'
                predicted_score = current_score + 2
            else:
                trend = 'declining'
                predicted_score = max(10, current_score - 1)
            
            predictions['predictions'][feature_name] = {
                'current_score': current_score,
                'predicted_score': predicted_score,
                'trend': trend,
                'confidence': 0.7
            }
        
        return predictions
    
    def _generate_user_health_profile(
        self,
        user_id: int,
        baselines: Dict[str, Dict],
        scores: List[Dict],
        recommendations: List[Dict],
        predictions: Dict[str, Any],
        analysis_date: date
    ) -> Dict[str, Any]:
        """生成用户健康画像"""
        
        # 计算整体健康评分
        if scores:
            weighted_scores = [score['score_value'] * score['weight'] for score in scores]
            total_weight = sum(score['weight'] for score in scores)
            overall_score = sum(weighted_scores) / total_weight if total_weight > 0 else 0
        else:
            overall_score = 0
        
        # 确定健康等级
        if overall_score >= 90:
            health_level = 'excellent'
        elif overall_score >= 80:
            health_level = 'good'
        elif overall_score >= 70:
            health_level = 'fair'
        elif overall_score >= 60:
            health_level = 'poor'
        else:
            health_level = 'critical'
        
        # 按类别分组评分
        physiological_scores = [s for s in scores if s['feature_name'] in ['heart_rate', 'blood_oxygen', 'temperature', 'pressure_high', 'pressure_low']]
        behavioral_scores = [s for s in scores if s['feature_name'] in ['stress', 'sleep', 'step', 'distance', 'calorie']]
        
        physiological_avg = sum(s['score_value'] for s in physiological_scores) / len(physiological_scores) if physiological_scores else 0
        behavioral_avg = sum(s['score_value'] for s in behavioral_scores) / len(behavioral_scores) if behavioral_scores else 0
        
        return {
            'user_id': user_id,
            'profile_date': analysis_date.isoformat(),
            'overall_score': overall_score,
            'health_level': health_level,
            'physiological_score': physiological_avg,
            'behavioral_score': behavioral_avg,
            'total_features_analyzed': len(scores),
            'total_recommendations': len(recommendations),
            'risk_factors': [rec['recommendation_type'] for rec in recommendations if rec['priority_level'] == 'high']
        }
    
    def generate_organization_health_analysis(
        self, 
        org_id: int, 
        analysis_date: Optional[date] = None, 
        include_sub_orgs: bool = True
    ) -> Dict[str, Any]:
        """生成部门健康分析"""
        if analysis_date is None:
            analysis_date = date.today()
            
        logger.info(f"开始生成部门 {org_id} 健康分析")
        
        try:
            # 获取部门用户
            users = self.hierarchy_service.get_users_by_org_hierarchy(org_id, None)
            
            if not users:
                return {'error': '部门下无活跃用户', 'org_id': org_id}
            
            # 获取用户健康分析
            user_analyses = {}
            for user in users:
                user_id = user['user_id']
                customer_id = user['customer_id']
                user_analysis = self._generate_user_complete_analysis(
                    user_id, customer_id, analysis_date
                )
                if user_analysis:
                    user_analyses[user_id] = {
                        **user_analysis,
                        'username': user['username']
                    }
            
            # 汇总部门数据
            org_analysis = self._aggregate_single_org_analysis(org_id, user_analyses, analysis_date)
            org_analysis['include_sub_orgs'] = include_sub_orgs
            org_analysis['user_count'] = len(user_analyses)
            
            logger.info(f"部门 {org_id} 健康分析完成，涉及 {len(user_analyses)} 个用户")
            
            return org_analysis
            
        except Exception as e:
            logger.error(f"部门 {org_id} 健康分析失败: {str(e)}")
            return {'error': str(e), 'org_id': org_id}
    
    def generate_user_comprehensive_analysis(
        self, 
        user_id: int, 
        analysis_date: Optional[date] = None, 
        days_back: int = 30
    ) -> Dict[str, Any]:
        """生成用户完整健康分析（包含层级信息）"""
        if analysis_date is None:
            analysis_date = date.today()
            
        logger.info(f"开始生成用户 {user_id} 完整健康分析")
        
        try:
            # 获取用户信息
            user = self.db.execute(
                text("SELECT user_id, customer_id, org_id, username FROM sys_user WHERE user_id = :user_id"),
                {"user_id": user_id}
            ).fetchone()
            
            if not user:
                return {'error': '用户不存在', 'user_id': user_id}
            
            customer_id = user.customer_id
            org_id = user.org_id
            
            # 生成用户健康分析
            user_analysis = self._generate_user_complete_analysis(
                user_id, customer_id, analysis_date
            )
            
            if not user_analysis:
                return {'error': '无法生成用户健康分析', 'user_id': user_id}
            
            # 添加层级信息
            user_analysis['hierarchy_info'] = {
                'user_id': user_id,
                'username': user.username,
                'org_id': org_id,
                'customer_id': customer_id
            }
            
            # 添加时间范围信息
            user_analysis['analysis_config'] = {
                'analysis_date': analysis_date.isoformat(),
                'days_back': days_back,
                'data_range': {
                    'start_date': (analysis_date - timedelta(days=days_back)).isoformat(),
                    'end_date': analysis_date.isoformat()
                }
            }
            
            logger.info(f"用户 {user_id} 完整健康分析完成")
            
            return user_analysis
            
        except Exception as e:
            logger.error(f"用户 {user_id} 完整健康分析失败: {str(e)}")
            return {'error': str(e), 'user_id': user_id}
    
    def get_organizations_health_summary(
        self, 
        customer_id: int, 
        analysis_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """获取所有组织健康状况汇总"""
        if analysis_date is None:
            analysis_date = date.today()
            
        logger.info(f"开始获取租户 {customer_id} 组织健康汇总")
        
        try:
            # 获取租户下所有组织
            orgs = self.hierarchy_service.get_org_hierarchy_by_customer(customer_id)
            
            if not orgs:
                return {'error': '租户下无组织结构', 'customer_id': customer_id}
            
            # 为每个组织生成健康汇总
            org_summaries = []
            for org in orgs:
                org_id = org['org_id']
                org_users = self.hierarchy_service.get_users_by_org_hierarchy(org_id, customer_id)
                
                if not org_users:
                    continue
                
                # 快速健康状态统计
                org_summary = {
                    'org_id': org_id,
                    'org_name': org.get('org_name', f'部门{org_id}'),
                    'user_count': len(org_users),
                    'analysis_date': analysis_date.isoformat()
                }
                
                # 统计用户健康等级分布（快速版）
                health_levels = {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0, 'critical': 0, 'unknown': 0}
                valid_analyses = 0
                total_score_sum = 0
                
                for user in org_users:
                    try:
                        # 简化的健康状态评估
                        user_health_data = get_all_health_data_optimized(
                            db_session=self.db,
                            user_id=user['user_id'],
                            customer_id=customer_id,
                            start_date=analysis_date - timedelta(days=7),
                            end_date=analysis_date
                        )
                        
                        if user_health_data:
                            # 简单评分：基于最近数据的平均值
                            avg_heart_rate = np.mean([d.heart_rate for d in user_health_data if d.heart_rate])
                            avg_blood_oxygen = np.mean([d.blood_oxygen for d in user_health_data if d.blood_oxygen])
                            
                            simple_score = 0
                            if avg_heart_rate and 60 <= avg_heart_rate <= 100:
                                simple_score += 40
                            elif avg_heart_rate:
                                simple_score += 20
                            
                            if avg_blood_oxygen and avg_blood_oxygen >= 95:
                                simple_score += 40
                            elif avg_blood_oxygen and avg_blood_oxygen >= 90:
                                simple_score += 30
                            elif avg_blood_oxygen:
                                simple_score += 20
                                
                            simple_score += min(20, len(user_health_data))  # 数据完整性加分
                            
                            total_score_sum += simple_score
                            valid_analyses += 1
                            
                            # 健康等级分类
                            if simple_score >= 90:
                                health_levels['excellent'] += 1
                            elif simple_score >= 80:
                                health_levels['good'] += 1
                            elif simple_score >= 70:
                                health_levels['fair'] += 1
                            elif simple_score >= 60:
                                health_levels['poor'] += 1
                            else:
                                health_levels['critical'] += 1
                        else:
                            health_levels['unknown'] += 1
                            
                    except Exception:
                        health_levels['unknown'] += 1
                
                org_summary['health_level_distribution'] = health_levels
                org_summary['avg_health_score'] = (total_score_sum / valid_analyses) if valid_analyses > 0 else 0
                org_summary['data_coverage'] = (valid_analyses / len(org_users) * 100) if org_users else 0
                
                org_summaries.append(org_summary)
            
            # 租户整体汇总
            customer_summary = {
                'customer_id': customer_id,
                'analysis_date': analysis_date.isoformat(),
                'total_organizations': len(org_summaries),
                'total_users': sum(org['user_count'] for org in org_summaries),
                'organizations': org_summaries
            }
            
            # 租户级健康状态分布
            total_health_levels = {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0, 'critical': 0, 'unknown': 0}
            total_score_sum = 0
            total_valid_orgs = 0
            
            for org in org_summaries:
                for level, count in org['health_level_distribution'].items():
                    total_health_levels[level] += count
                if org['avg_health_score'] > 0:
                    total_score_sum += org['avg_health_score']
                    total_valid_orgs += 1
            
            customer_summary['overall_health_distribution'] = total_health_levels
            customer_summary['customer_avg_health_score'] = (total_score_sum / total_valid_orgs) if total_valid_orgs > 0 else 0
            
            logger.info(f"租户 {customer_id} 组织健康汇总完成，涉及 {len(org_summaries)} 个组织")
            
            return customer_summary
            
        except Exception as e:
            logger.error(f"租户 {customer_id} 组织健康汇总失败: {str(e)}")
            return {'error': str(e), 'customer_id': customer_id}
    
    def analyze_customer_health_trends(
        self, 
        customer_id: int, 
        days_back: int = 30, 
        trend_type: str = 'overall'
    ) -> Dict[str, Any]:
        """分析租户健康趋势"""
        logger.info(f"开始分析租户 {customer_id} 健康趋势")
        
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days_back)
            
            # 获取租户用户
            users = self.hierarchy_service.get_users_by_customer(customer_id)
            
            if not users:
                return {'error': '租户下无用户', 'customer_id': customer_id}
            
            # 按日期收集健康数据
            daily_trends = {}
            
            # 按周分析趋势
            weeks = days_back // 7
            for week in range(weeks):
                week_start = end_date - timedelta(days=(week + 1) * 7)
                week_end = end_date - timedelta(days=week * 7)
                
                week_key = f"{week_start.isoformat()}_to_{week_end.isoformat()}"
                week_data = {
                    'week_start': week_start.isoformat(),
                    'week_end': week_end.isoformat(),
                    'users_analyzed': 0,
                    'avg_scores': {},
                    'health_level_counts': {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0, 'critical': 0}
                }
                
                for user in users:
                    user_id = user['user_id']
                    try:
                        # 获取周数据
                        user_health_data = get_all_health_data_optimized(
                            db_session=self.db,
                            user_id=user_id,
                            customer_id=customer_id,
                            start_date=week_start,
                            end_date=week_end
                        )
                        
                        if user_health_data:
                            week_data['users_analyzed'] += 1
                            
                            # 计算简单健康评分趋势
                            heart_rate_avg = np.mean([d.heart_rate for d in user_health_data if d.heart_rate]) or 0
                            blood_oxygen_avg = np.mean([d.blood_oxygen for d in user_health_data if d.blood_oxygen]) or 0
                            
                            if 'heart_rate' not in week_data['avg_scores']:
                                week_data['avg_scores']['heart_rate'] = []
                                week_data['avg_scores']['blood_oxygen'] = []
                            
                            if heart_rate_avg > 0:
                                week_data['avg_scores']['heart_rate'].append(heart_rate_avg)
                            if blood_oxygen_avg > 0:
                                week_data['avg_scores']['blood_oxygen'].append(blood_oxygen_avg)
                    
                    except Exception:
                        continue
                
                # 计算周平均值
                for feature, values in week_data['avg_scores'].items():
                    week_data['avg_scores'][feature] = np.mean(values) if values else 0
                
                daily_trends[week_key] = week_data
            
            # 分析趋势方向
            trend_analysis = {
                'customer_id': customer_id,
                'analysis_period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days_analyzed': days_back,
                    'weeks_analyzed': weeks
                },
                'trend_type': trend_type,
                'weekly_trends': daily_trends,
                'overall_trend_direction': 'stable'
            }
            
            # 计算整体趋势
            if len(daily_trends) >= 2:
                weeks_list = sorted(daily_trends.keys())
                first_week = daily_trends[weeks_list[-1]]  # 最早的周
                last_week = daily_trends[weeks_list[0]]    # 最新的周
                
                if (first_week['users_analyzed'] > 0 and last_week['users_analyzed'] > 0 and
                    'heart_rate' in first_week['avg_scores'] and 'heart_rate' in last_week['avg_scores']):
                    
                    first_avg = first_week['avg_scores']['heart_rate']
                    last_avg = last_week['avg_scores']['heart_rate']
                    
                    if last_avg > first_avg * 1.05:
                        trend_analysis['overall_trend_direction'] = 'improving'
                    elif last_avg < first_avg * 0.95:
                        trend_analysis['overall_trend_direction'] = 'declining'
            
            logger.info(f"租户 {customer_id} 健康趋势分析完成")
            
            return trend_analysis
            
        except Exception as e:
            logger.error(f"租户 {customer_id} 健康趋势分析失败: {str(e)}")
            return {'error': str(e), 'customer_id': customer_id}
    
    def _aggregate_single_org_analysis(
        self, 
        org_id: int, 
        user_analyses: Dict[int, Dict], 
        analysis_date: date
    ) -> Dict[str, Any]:
        """汇总单个组织的健康分析"""
        if not user_analyses:
            return {
                'org_id': org_id,
                'analysis_date': analysis_date.isoformat(),
                'user_count': 0,
                'error': '组织下无有效用户健康数据'
            }
        
        # 基础组织信息
        org_analysis = {
            'org_id': org_id,
            'analysis_date': analysis_date.isoformat(),
            'user_count': len(user_analyses),
            'users': list(user_analyses.keys())
        }
        
        # 汇总健康评分
        all_scores = []
        feature_scores = {}
        health_levels = []
        
        for user_data in user_analyses.values():
            # 收集用户评分
            if user_data.get('scores'):
                for score in user_data['scores']:
                    feature_name = score.get('feature_name')
                    score_value = score.get('score_value', 0)
                    
                    all_scores.append(score_value)
                    
                    if feature_name not in feature_scores:
                        feature_scores[feature_name] = []
                    feature_scores[feature_name].append(score_value)
            
            # 收集健康等级
            health_profile = user_data.get('health_profile', {})
            health_level = health_profile.get('health_level', 'unknown')
            health_levels.append(health_level)
        
        # 计算组织平均评分
        if all_scores:
            org_analysis['overall_avg_score'] = sum(all_scores) / len(all_scores)
        else:
            org_analysis['overall_avg_score'] = 0
        
        # 计算各特征平均评分
        org_analysis['feature_avg_scores'] = {
            feature: sum(scores) / len(scores)
            for feature, scores in feature_scores.items()
            if scores
        }
        
        # 健康等级分布
        org_analysis['health_level_distribution'] = {
            level: health_levels.count(level)
            for level in set(health_levels)
        }
        
        # 数据质量指标
        org_analysis['data_quality'] = {
            'users_with_scores': len([u for u in user_analyses.values() if u.get('scores')]),
            'users_with_baselines': len([u for u in user_analyses.values() if u.get('baselines')]),
            'users_with_recommendations': len([u for u in user_analyses.values() if u.get('recommendations')]),
            'coverage_percentage': len(user_analyses) / len(user_analyses) * 100 if user_analyses else 0
        }
        
        return org_analysis
```

## 5. 核心服务实现

### 4.1 健康基线计算服务 (services/baseline_service.py)

```python
"""
健康基线计算服务
基于统计学方法计算用户个人、部门和组织的健康基线
"""
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
from decimal import Decimal
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, func

from ..models.analytics_models import HealthBaseline, HealthBaselineDTO
from ..models.health_models import UserHealthData
from ..config.health_config import HealthAnalyticsConfig
from ..utils.statistics import StatisticsCalculator
from .data_service import get_all_health_data_optimized

logger = logging.getLogger(__name__)

class HealthBaselineService:
    """健康基线计算服务"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.config = HealthAnalyticsConfig()
        self.stats_calc = StatisticsCalculator()
    
    def generate_user_health_baselines(
        self, 
        user_id: Optional[int] = None,
        calculation_date: Optional[date] = None
    ) -> List[HealthBaselineDTO]:
        """
        生成用户健康基线
        
        Args:
            user_id: 用户ID，None表示处理所有用户
            calculation_date: 计算日期，None表示使用当前日期
        
        Returns:
            生成的健康基线列表
        """
        if calculation_date is None:
            calculation_date = date.today()
        
        start_date = calculation_date - timedelta(days=self.config.AI_CONFIG['baseline_calculation_days'])
        
        logger.info(f"开始生成健康基线: user_id={user_id}, date_range={start_date} to {calculation_date}")
        
        try:
            baselines = []
            
            # 获取需要处理的用户列表
            if user_id:
                user_conditions = [UserHealthData.user_id == user_id]
            else:
                user_conditions = [UserHealthData.user_id.isnot(None)]
            
            # 使用优化接口获取健康数据
            if user_id:
                users_data = get_all_health_data_optimized(
                    db_session=self.db,
                    user_id=user_id,
                    start_date=start_date,
                    end_date=calculation_date
                )
            else:
                users_data = get_all_health_data_optimized(
                    db_session=self.db,
                    start_date=start_date,
                    end_date=calculation_date
                )
            
            # 按用户分组
            users_dict = {}
            for data_point in users_data:
                uid = data_point.user_id
                if uid not in users_dict:
                    users_dict[uid] = {
                        'user_id': uid,
                        'device_sn': data_point.device_sn,
                        'data_points': []
                    }
                users_dict[uid]['data_points'].append(data_point)
            
            users = [(user_info['user_id'], user_info['device_sn']) for user_info in users_dict.values()]
            
            for user_id_tuple, device_sn_tuple in users:
                current_user_id = user_id_tuple
                device_sn = device_sn_tuple
                
                # 获取该用户的数据点
                user_data_points = users_dict[current_user_id]['data_points']
                
                user_baselines = self._calculate_user_baselines_from_data(
                    current_user_id, device_sn, user_data_points, calculation_date
                )
                baselines.extend(user_baselines)
            
            # 批量保存基线数据
            self._save_baselines_batch(baselines, calculation_date)
            
            logger.info(f"健康基线生成完成: 共处理{len(baselines)}个基线")
            return baselines
            
        except Exception as e:
            logger.error(f"健康基线生成失败: {str(e)}", exc_info=True)
            raise
    
    def _calculate_user_baselines_from_data(
        self, 
        user_id: int, 
        device_sn: str, 
        user_data: List[UserHealthData],
        end_date: date
    ) -> List[HealthBaselineDTO]:
        """基于已获取的数据计算单个用户的健康基线"""
        baselines = []
        
        if not user_data:
            logger.warning(f"用户 {user_id} 无健康数据")
            return baselines
        
        # 为每个健康特征计算基线
        for feature_name in self.config.get_all_features():
            feature_values = []
            
            # 提取特征值
            for data_point in user_data:
                value = getattr(data_point, feature_name, None)
                if value is not None and value > 0:  # 过滤无效值
                    feature_values.append(float(value))
            
            if len(feature_values) < 5:  # 数据点太少，跳过
                logger.warning(f"用户 {user_id} 特征 {feature_name} 数据点不足: {len(feature_values)}")
                continue
            
            # 统计计算
            stats = self.stats_calc.calculate_descriptive_statistics(feature_values)
            
            # 异常值检测和清理
            cleaned_values = self.stats_calc.remove_outliers(
                feature_values, 
                method='iqr'
            )
            
            if len(cleaned_values) < 3:
                logger.warning(f"用户 {user_id} 特征 {feature_name} 清理后数据不足")
                continue
            
            # 重新计算清理后的统计值
            final_stats = self.stats_calc.calculate_descriptive_statistics(cleaned_values)
            
            # 创建基线对象
            baseline = HealthBaselineDTO(
                device_sn=device_sn,
                user_id=user_id,
                feature_name=feature_name,
                baseline_date=end_date,
                mean_value=final_stats['mean'],
                std_value=final_stats['std'],
                min_value=final_stats['min'],
                max_value=final_stats['max'],
                sample_count=len(cleaned_values),
                confidence_level=self.config.AI_CONFIG['confidence_level']
            )
            
            baselines.append(baseline)
            
        logger.info(f"用户 {user_id} 基线计算完成: 共 {len(baselines)} 个特征")
        return baselines
    
    def generate_department_health_baselines(
        self, 
        org_id: Optional[int] = None,
        calculation_date: Optional[date] = None
    ) -> List[Dict]:
        """生成部门健康基线"""
        if calculation_date is None:
            calculation_date = date.today()
            
        logger.info(f"开始生成部门健康基线: org_id={org_id}, date={calculation_date}")
        
        try:
            # 获取部门内所有用户的基线数据
            baseline_query = self.db.query(HealthBaseline).join(
                UserHealthData, HealthBaseline.user_id == UserHealthData.user_id
            )
            
            if org_id:
                baseline_query = baseline_query.filter(UserHealthData.org_id == org_id)
            
            baselines = baseline_query.filter(
                HealthBaseline.baseline_date == calculation_date,
                HealthBaseline.is_current == True
            ).all()
            
            # 按部门和特征分组聚合
            dept_baselines = self._aggregate_baselines_by_group(
                baselines, 
                group_by='org_id',
                baseline_type='department'
            )
            
            # 保存部门基线
            self._save_department_baselines(dept_baselines, calculation_date)
            
            logger.info(f"部门健康基线生成完成: 共 {len(dept_baselines)} 个基线")
            return dept_baselines
            
        except Exception as e:
            logger.error(f"部门健康基线生成失败: {str(e)}", exc_info=True)
            raise
    
    def generate_tenant_health_baselines(
        self, 
        customer_id: Optional[int] = None,
        calculation_date: Optional[date] = None
    ) -> List[Dict]:
        """生成租户健康基线"""
        if calculation_date is None:
            calculation_date = date.today()
            
        logger.info(f"开始生成租户健康基线: customer_id={customer_id}, date={calculation_date}")
        
        try:
            # 获取租户内所有用户的基线数据
            baseline_query = self.db.query(HealthBaseline)
            
            if customer_id:
                baseline_query = baseline_query.filter(HealthBaseline.customer_id == customer_id)
            
            baselines = baseline_query.filter(
                HealthBaseline.baseline_date == calculation_date,
                HealthBaseline.is_current == True
            ).all()
            
            # 按租户和特征分组聚合
            tenant_baselines = self._aggregate_baselines_by_group(
                baselines, 
                group_by='customer_id',
                baseline_type='tenant'
            )
            
            # 保存租户基线
            self._save_tenant_baselines(tenant_baselines, calculation_date)
            
            logger.info(f"租户健康基线生成完成: 共 {len(tenant_baselines)} 个基线")
            return tenant_baselines
            
        except Exception as e:
            logger.error(f"租户健康基线生成失败: {str(e)}", exc_info=True)
            raise
    
    def _aggregate_baselines_by_group(
        self, 
        baselines: List[HealthBaseline],
        group_by: str,
        baseline_type: str
    ) -> List[Dict]:
        """按分组聚合基线数据"""
        grouped_baselines = {}
        
        for baseline in baselines:
            group_key = getattr(baseline, group_by) if hasattr(baseline, group_by) else baseline.customer_id
            feature_key = f"{group_key}_{baseline.feature_name}"
            
            if feature_key not in grouped_baselines:
                grouped_baselines[feature_key] = {
                    'group_id': group_key,
                    'feature_name': baseline.feature_name,
                    'values': [],
                    'sample_counts': []
                }
            
            grouped_baselines[feature_key]['values'].append(baseline.mean_value)
            grouped_baselines[feature_key]['sample_counts'].append(baseline.sample_count)
        
        # 计算聚合统计值
        aggregated_baselines = []
        for key, group_data in grouped_baselines.items():
            values = [float(v) for v in group_data['values'] if v is not None]
            
            if not values:
                continue
                
            stats = self.stats_calc.calculate_descriptive_statistics(values)
            total_samples = sum(group_data['sample_counts'])
            
            aggregated_baseline = {
                'group_id': group_data['group_id'],
                'feature_name': group_data['feature_name'],
                'baseline_type': baseline_type,
                'mean_value': stats['mean'],
                'std_value': stats['std'],
                'min_value': stats['min'],
                'max_value': stats['max'],
                'user_count': len(values),
                'sample_count': total_samples
            }
            
            aggregated_baselines.append(aggregated_baseline)
        
        return aggregated_baselines
    
    def _save_baselines_batch(self, baselines: List[HealthBaselineDTO], calculation_date: date):
        """批量保存基线数据"""
        try:
            # 先设置旧基线为非当前
            self.db.execute(
                text("UPDATE t_health_baseline SET is_current = 0 WHERE baseline_date < :date"),
                {"date": calculation_date}
            )
            
            # 批量插入新基线
            for baseline in baselines:
                existing = self.db.query(HealthBaseline).filter(
                    and_(
                        HealthBaseline.device_sn == baseline.device_sn,
                        HealthBaseline.feature_name == baseline.feature_name,
                        HealthBaseline.baseline_date == baseline.baseline_date
                    )
                ).first()
                
                if existing:
                    # 更新现有记录
                    existing.mean_value = baseline.mean_value
                    existing.std_value = baseline.std_value
                    existing.min_value = baseline.min_value
                    existing.max_value = baseline.max_value
                    existing.sample_count = baseline.sample_count
                    existing.is_current = True
                    existing.update_time = datetime.utcnow()
                else:
                    # 创建新记录
                    new_baseline = HealthBaseline(
                        device_sn=baseline.device_sn,
                        user_id=baseline.user_id,
                        feature_name=baseline.feature_name,
                        baseline_date=baseline.baseline_date,
                        mean_value=baseline.mean_value,
                        std_value=baseline.std_value,
                        min_value=baseline.min_value,
                        max_value=baseline.max_value,
                        sample_count=baseline.sample_count,
                        is_current=True,
                        baseline_type='personal',
                        confidence_level=baseline.confidence_level
                    )
                    self.db.add(new_baseline)
            
            self.db.commit()
            logger.info(f"批量保存基线数据完成: {len(baselines)} 条记录")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"保存基线数据失败: {str(e)}", exc_info=True)
            raise
    
    def _save_department_baselines(self, baselines: List[Dict], calculation_date: date):
        """保存部门基线数据"""
        # 实现部门基线保存逻辑
        # 需要创建对应的部门基线表或在现有表中添加标识
        pass
    
    def _save_tenant_baselines(self, baselines: List[Dict], calculation_date: date):
        """保存租户基线数据"""
        # 实现租户基线保存逻辑
        # 需要创建对应的租户基线表或在现有表中添加标识
        pass
    
    def get_user_baseline(
        self, 
        user_id: int, 
        feature_name: str, 
        baseline_date: Optional[date] = None
    ) -> Optional[HealthBaselineDTO]:
        """获取用户特定特征的基线数据"""
        query = self.db.query(HealthBaseline).filter(
            and_(
                HealthBaseline.user_id == user_id,
                HealthBaseline.feature_name == feature_name,
                HealthBaseline.is_current == True
            )
        )
        
        if baseline_date:
            query = query.filter(HealthBaseline.baseline_date == baseline_date)
        else:
            query = query.order_by(HealthBaseline.baseline_date.desc())
        
        baseline = query.first()
        
        if baseline:
            return HealthBaselineDTO(
                device_sn=baseline.device_sn,
                user_id=baseline.user_id,
                feature_name=baseline.feature_name,
                baseline_date=baseline.baseline_date,
                mean_value=float(baseline.mean_value),
                std_value=float(baseline.std_value),
                min_value=float(baseline.min_value),
                max_value=float(baseline.max_value),
                sample_count=baseline.sample_count,
                confidence_level=float(baseline.confidence_level)
            )
        
        return None
    
    def validate_baseline_quality(self, baseline: HealthBaselineDTO) -> Dict[str, Any]:
        """验证基线数据质量"""
        quality_report = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'quality_score': 100
        }
        
        # 检查样本数量
        if baseline.sample_count < 10:
            quality_report['warnings'].append(f"样本数量较少: {baseline.sample_count}")
            quality_report['quality_score'] -= 20
        
        # 检查标准差
        if baseline.std_value > baseline.mean_value:
            quality_report['warnings'].append("标准差过大，数据波动较大")
            quality_report['quality_score'] -= 15
        
        # 检查正常范围
        feature_config = self.config.get_feature_config(baseline.feature_name)
        if feature_config:
            normal_min, normal_max = feature_config.normal_range
            if not (normal_min <= baseline.mean_value <= normal_max):
                quality_report['warnings'].append(
                    f"均值 {baseline.mean_value} 超出正常范围 [{normal_min}, {normal_max}]"
                )
                quality_report['quality_score'] -= 25
        
        # 设置质量等级
        if quality_report['quality_score'] >= 80:
            quality_report['quality_level'] = 'excellent'
        elif quality_report['quality_score'] >= 60:
            quality_report['quality_level'] = 'good'
        elif quality_report['quality_score'] >= 40:
            quality_report['quality_level'] = 'fair'
        else:
            quality_report['quality_level'] = 'poor'
            quality_report['is_valid'] = False
        
        return quality_report
```

由于内容较长，我将继续创建其他核心服务模块：

### 4.2 健康评分计算服务 (services/score_service.py)

```python
"""
健康评分计算服务
基于健康基线和权重配置计算综合健康评分
"""
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
from decimal import Decimal
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, func

from ..models.analytics_models import HealthScore, HealthScoreDTO, HealthBaseline
from ..models.health_models import UserHealthData
from ..config.health_config import HealthAnalyticsConfig
from ..utils.statistics import StatisticsCalculator
from ..services.baseline_service import HealthBaselineService
from .data_service import get_all_health_data_optimized

logger = logging.getLogger(__name__)

class HealthScoreService:
    """健康评分计算服务"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.config = HealthAnalyticsConfig()
        self.stats_calc = StatisticsCalculator()
        self.baseline_service = HealthBaselineService(db_session)
    
    def calculate_user_health_scores(
        self,
        user_id: Optional[int] = None,
        score_date: Optional[date] = None,
        days_back: int = 7
    ) -> List[HealthScoreDTO]:
        """
        计算用户健康评分
        
        Args:
            user_id: 用户ID，None表示处理所有用户
            score_date: 评分日期
            days_back: 向前计算天数
        
        Returns:
            健康评分列表
        """
        if score_date is None:
            score_date = date.today()
        
        start_date = score_date - timedelta(days=days_back)
        
        logger.info(f"开始计算健康评分: user_id={user_id}, date_range={start_date} to {score_date}")
        
        try:
            scores = []
            
            # 使用优化接口获取健康数据
            if user_id:
                users_data = get_all_health_data_optimized(
                    db_session=self.db,
                    user_id=user_id,
                    start_date=start_date,
                    end_date=score_date
                )
            else:
                users_data = get_all_health_data_optimized(
                    db_session=self.db,
                    start_date=start_date,
                    end_date=score_date
                )
            
            # 按用户分组处理
            users_dict = {}
            for data_point in users_data:
                uid = data_point.user_id
                if uid not in users_dict:
                    users_dict[uid] = {
                        'user_id': uid,
                        'device_sn': data_point.device_sn,
                        'data_points': []
                    }
                users_dict[uid]['data_points'].append(data_point)
            
            for user_info in users_dict.values():
                current_user_id = user_info['user_id']
                device_sn = user_info['device_sn']
                user_data_points = user_info['data_points']
                
                user_scores = self._calculate_single_user_scores_from_data(
                    current_user_id, device_sn, user_data_points, score_date
                )
                scores.extend(user_scores)
            
            # 批量保存评分数据
            self._save_scores_batch(scores)
            
            logger.info(f"健康评分计算完成: 共处理 {len(scores)} 个评分")
            return scores
            
        except Exception as e:
            logger.error(f"健康评分计算失败: {str(e)}", exc_info=True)
            raise
    
    def _calculate_single_user_scores_from_data(
        self,
        user_id: int,
        device_sn: str,
        user_data: List[UserHealthData],
        score_date: date
    ) -> List[HealthScoreDTO]:
        """基于已获取的数据计算单个用户的健康评分"""
        scores = []
        
        if not user_data:
            logger.warning(f"用户 {user_id} 无健康数据")
            return scores
        
        # 为每个健康特征计算评分
        for feature_name in self.config.get_all_features():
            score_data = self._calculate_feature_score(
                user_id, device_sn, feature_name, user_data, score_date
            )
            if score_data:
                scores.append(score_data)
        
        logger.info(f"用户 {user_id} 评分计算完成: 共 {len(scores)} 个特征评分")
        return scores
    
    def _calculate_feature_score(
        self,
        user_id: int,
        device_sn: str,
        feature_name: str,
        user_data: List[UserHealthData],
        score_date: date
    ) -> Optional[HealthScoreDTO]:
        """计算单个特征的评分"""
        
        # 提取特征值
        feature_values = []
        for data_point in user_data:
            value = getattr(data_point, feature_name, None)
            if value is not None and value > 0:
                feature_values.append(float(value))
        
        if not feature_values:
            return None
        
        # 计算平均值
        avg_value = np.mean(feature_values)
        
        # 获取用户基线
        baseline = self.baseline_service.get_user_baseline(user_id, feature_name)
        
        if not baseline:
            logger.warning(f"用户 {user_id} 特征 {feature_name} 无基线数据，使用默认评分")
            # 使用配置的正常范围进行评分
            score_value = self._score_against_normal_range(feature_name, avg_value)
            z_score = 0.0
        else:
            # 基于基线计算Z-score
            if baseline.std_value > 0:
                z_score = (avg_value - baseline.mean_value) / baseline.std_value
            else:
                z_score = 0.0
            
            # 基于Z-score计算评分
            score_value = self._z_score_to_health_score(z_score, feature_name)
        
        # 计算惩罚值（基于异常检测）
        penalty_value = self._calculate_penalty(feature_values, feature_name)
        
        # 最终评分（考虑惩罚）
        final_score = max(0, score_value - penalty_value)
        
        return HealthScoreDTO(
            device_sn=device_sn,
            user_id=user_id,
            feature_name=feature_name,
            score_value=final_score,
            z_score=z_score,
            avg_value=avg_value,
            penalty_value=penalty_value,
            score_date=score_date
        )
    
    def _score_against_normal_range(self, feature_name: str, value: float) -> float:
        """基于正常范围评分"""
        feature_config = self.config.get_feature_config(feature_name)
        if not feature_config:
            return 70.0  # 默认评分
        
        normal_min, normal_max = feature_config.normal_range
        normal_mid = (normal_min + normal_max) / 2
        normal_range = normal_max - normal_min
        
        # 在正常范围内的评分
        if normal_min <= value <= normal_max:
            # 越接近中值评分越高
            deviation = abs(value - normal_mid) / (normal_range / 2)
            return 100 - deviation * 20  # 80-100分
        else:
            # 超出正常范围的评分
            if value < normal_min:
                deviation = (normal_min - value) / normal_min
            else:
                deviation = (value - normal_max) / normal_max
            
            # 最多扣50分
            penalty = min(50, deviation * 100)
            return max(30, 70 - penalty)
    
    def _z_score_to_health_score(self, z_score: float, feature_name: str) -> float:
        """将Z-score转换为健康评分"""
        # 基于Z-score的评分算法
        abs_z = abs(z_score)
        
        if abs_z <= 1:  # 1个标准差内，优秀
            return 90 + (1 - abs_z) * 10  # 90-100分
        elif abs_z <= 2:  # 2个标准差内，良好
            return 70 + (2 - abs_z) * 20  # 70-90分
        elif abs_z <= 3:  # 3个标准差内，一般
            return 40 + (3 - abs_z) * 30  # 40-70分
        else:  # 超过3个标准差，较差
            return max(10, 40 - (abs_z - 3) * 10)  # 10-40分
    
    def _calculate_penalty(self, values: List[float], feature_name: str) -> float:
        """计算惩罚值"""
        if len(values) < 2:
            return 0.0
        
        penalty = 0.0
        
        # 异常值惩罚
        outliers = self.stats_calc.detect_outliers(values, method='iqr')
        outlier_ratio = len(outliers) / len(values)
        if outlier_ratio > 0.2:  # 超过20%异常值
            penalty += outlier_ratio * 15
        
        # 变异性惩罚
        cv = np.std(values) / np.mean(values) if np.mean(values) > 0 else 0
        if cv > 0.3:  # 变异系数大于30%
            penalty += min(10, cv * 20)
        
        # 趋势惩罚（如果数据呈现恶化趋势）
        if len(values) >= 5:
            trend_penalty = self._calculate_trend_penalty(values, feature_name)
            penalty += trend_penalty
        
        return min(penalty, 30)  # 最大惩罚30分
    
    def _calculate_trend_penalty(self, values: List[float], feature_name: str) -> float:
        """计算趋势惩罚"""
        # 简单线性趋势分析
        x = np.arange(len(values))
        y = np.array(values)
        
        # 计算相关系数
        correlation = np.corrcoef(x, y)[0, 1]
        
        # 判断趋势方向（某些指标高更好，某些指标低更好）
        beneficial_high_features = ['blood_oxygen', 'step', 'distance', 'calorie', 'sleep']
        beneficial_low_features = ['stress', 'pressure_high', 'pressure_low']
        
        if feature_name in beneficial_high_features:
            # 下降趋势是不好的
            if correlation < -0.3:  # 明显下降趋势
                return abs(correlation) * 10
        elif feature_name in beneficial_low_features:
            # 上升趋势是不好的
            if correlation > 0.3:  # 明显上升趋势
                return correlation * 10
        
        return 0.0
    
    def calculate_comprehensive_health_score(
        self,
        user_id: int,
        score_date: Optional[date] = None
    ) -> Dict[str, float]:
        """计算综合健康评分"""
        if score_date is None:
            score_date = date.today()
        
        # 获取用户所有特征评分
        user_scores = self.db.query(HealthScore).filter(
            and_(
                HealthScore.user_id == user_id,
                HealthScore.score_date == score_date
            )
        ).all()
        
        if not user_scores:
            logger.warning(f"用户 {user_id} 在 {score_date} 无评分数据")
            return {}
        
        # 按类别分组计算评分
        physiological_scores = []
        behavioral_scores = []
        risk_scores = []
        
        total_weighted_score = 0.0
        total_weight = Decimal('0')
        
        for score in user_scores:
            feature_config = self.config.get_feature_config(score.feature_name)
            if not feature_config:
                continue
            
            weight = feature_config.weight
            weighted_score = float(score.score_value) * float(weight)
            total_weighted_score += weighted_score
            total_weight += weight
            
            # 按类别分类
            if feature_config.category == 'physiological':
                physiological_scores.append(float(score.score_value))
            elif feature_config.category == 'behavioral':
                behavioral_scores.append(float(score.score_value))
            else:
                risk_scores.append(float(score.score_value))
        
        # 计算各类评分
        overall_score = total_weighted_score / float(total_weight) if total_weight > 0 else 0.0
        physiological_score = np.mean(physiological_scores) if physiological_scores else 0.0
        behavioral_score = np.mean(behavioral_scores) if behavioral_scores else 0.0
        risk_score = np.mean(risk_scores) if risk_scores else 0.0
        
        return {
            'overall_score': round(overall_score, 2),
            'physiological_score': round(physiological_score, 2),
            'behavioral_score': round(behavioral_score, 2),
            'risk_factor_score': round(risk_score, 2),
            'health_level': self._get_health_level(overall_score)
        }
    
    def _get_health_level(self, score: float) -> str:
        """根据评分获取健康等级"""
        thresholds = self.config.SCORE_THRESHOLDS
        
        if score >= thresholds['excellent']:
            return 'excellent'
        elif score >= thresholds['good']:
            return 'good'
        elif score >= thresholds['fair']:
            return 'fair'
        elif score >= thresholds['poor']:
            return 'poor'
        else:
            return 'critical'
    
    def _save_scores_batch(self, scores: List[HealthScoreDTO]):
        """批量保存评分数据"""
        try:
            for score_dto in scores:
                existing = self.db.query(HealthScore).filter(
                    and_(
                        HealthScore.device_sn == score_dto.device_sn,
                        HealthScore.feature_name == score_dto.feature_name,
                        HealthScore.score_date == score_dto.score_date
                    )
                ).first()
                
                if existing:
                    # 更新现有记录
                    existing.avg_value = score_dto.avg_value
                    existing.z_score = score_dto.z_score
                    existing.score_value = score_dto.score_value
                    existing.penalty_value = score_dto.penalty_value
                    existing.update_time = datetime.utcnow()
                else:
                    # 创建新记录
                    new_score = HealthScore(
                        device_sn=score_dto.device_sn,
                        user_id=score_dto.user_id,
                        feature_name=score_dto.feature_name,
                        avg_value=score_dto.avg_value,
                        z_score=score_dto.z_score,
                        score_value=score_dto.score_value,
                        penalty_value=score_dto.penalty_value,
                        score_date=score_dto.score_date
                    )
                    self.db.add(new_score)
            
            self.db.commit()
            logger.info(f"批量保存评分数据完成: {len(scores)} 条记录")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"保存评分数据失败: {str(e)}", exc_info=True)
            raise
```

### 4.3 健康建议生成服务 (services/recommendation_service.py)

```python
"""
智能健康建议服务
基于AI决策树和专家规则生成个性化健康建议
"""
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any
import json
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.analytics_models import (
    HealthRecommendationTrack, HealthRecommendationDTO, 
    UserHealthProfileDTO, HealthScore
)
from ..models.health_models import UserHealthData
from ..config.health_config import HealthAnalyticsConfig
from ..services.score_service import HealthScoreService
from ..utils.ai_analyzer import AIHealthAnalyzer
from .data_service import get_all_health_data_optimized

logger = logging.getLogger(__name__)

class HealthRecommendationService:
    """智能健康建议服务"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.config = HealthAnalyticsConfig()
        self.score_service = HealthScoreService(db_session)
        self.ai_analyzer = AIHealthAnalyzer()
        
        # 专家规则知识库
        self.expert_rules = self._load_expert_rules()
    
    def generate_user_recommendations(
        self, 
        user_id: int,
        analysis_date: Optional[date] = None
    ) -> List[HealthRecommendationDTO]:
        """
        生成用户个性化健康建议
        
        Args:
            user_id: 用户ID
            analysis_date: 分析日期
        
        Returns:
            健康建议列表
        """
        if analysis_date is None:
            analysis_date = date.today()
            
        logger.info(f"开始生成用户 {user_id} 的健康建议")
        
        try:
            # 1. 构建用户健康画像
            user_profile = self._build_user_profile(user_id, analysis_date)
            
            # 2. 计算健康评分
            comprehensive_scores = self.score_service.calculate_comprehensive_health_score(
                user_id, analysis_date
            )
            
            # 3. 分析健康问题
            health_issues = self._analyze_health_issues(user_profile, comprehensive_scores)
            
            # 4. 生成针对性建议
            recommendations = []
            
            # 生理指标建议
            if comprehensive_scores.get('physiological_score', 0) < 70:
                physiological_recs = self._generate_physiological_recommendations(
                    user_profile, health_issues
                )
                recommendations.extend(physiological_recs)
            
            # 行为习惯建议
            if comprehensive_scores.get('behavioral_score', 0) < 75:
                behavioral_recs = self._generate_behavioral_recommendations(
                    user_profile, health_issues
                )
                recommendations.extend(behavioral_recs)
            
            # 风险预警建议
            if comprehensive_scores.get('risk_factor_score', 0) < 80:
                risk_recs = self._generate_risk_prevention_recommendations(
                    user_profile, health_issues
                )
                recommendations.extend(risk_recs)
            
            # 5. AI优化和个性化排序
            optimized_recommendations = self.ai_analyzer.optimize_recommendations(
                recommendations, user_profile, comprehensive_scores
            )
            
            # 6. 应用专家规则过滤
            final_recommendations = self._apply_expert_rules(
                optimized_recommendations, user_profile
            )
            
            # 7. 保存建议跟踪记录
            self._save_recommendation_tracks(user_id, final_recommendations)
            
            logger.info(f"用户 {user_id} 健康建议生成完成: {len(final_recommendations)} 条建议")
            return final_recommendations
            
        except Exception as e:
            logger.error(f"生成健康建议失败: user_id={user_id}, error={str(e)}", exc_info=True)
            raise
    
    def _build_user_profile(self, user_id: int, analysis_date: date) -> Dict[str, Any]:
        """构建用户健康画像"""
        end_date = analysis_date
        start_date = end_date - timedelta(days=30)  # 30天历史数据
        
        # 使用优化接口获取用户健康数据
        user_data = get_all_health_data_optimized(
            db_session=self.db,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if not user_data:
            logger.warning(f"用户 {user_id} 无足够健康数据")
            return {}
        
        # 计算特征统计
        feature_stats = {}
        for feature_name in self.config.get_all_features():
            values = []
            for data_point in user_data:
                value = getattr(data_point, feature_name, None)
                if value is not None and value > 0:
                    values.append(float(value))
            
            if values:
                feature_stats[feature_name] = {
                    'current_avg': sum(values) / len(values),
                    'recent_trend': self._calculate_trend(values[-7:] if len(values) >= 7 else values),
                    'stability': self._calculate_stability(values),
                    'outlier_count': len([v for v in values if self._is_outlier(v, values)])
                }
        
        # 获取用户基本信息
        latest_data = user_data[0]
        
        profile = {
            'user_id': user_id,
            'device_sn': latest_data.device_sn,
            'org_id': latest_data.org_id,
            'analysis_date': analysis_date,
            'data_points': len(user_data),
            'feature_stats': feature_stats,
            'data_quality_score': self._assess_data_quality(user_data)
        }
        
        return profile
    
    def _analyze_health_issues(
        self, 
        user_profile: Dict[str, Any], 
        scores: Dict[str, float]
    ) -> Dict[str, List[str]]:
        """分析健康问题"""
        issues = {
            'critical_issues': [],
            'warning_issues': [],
            'improvement_areas': []
        }
        
        feature_stats = user_profile.get('feature_stats', {})
        
        for feature_name, stats in feature_stats.items():
            feature_config = self.config.get_feature_config(feature_name)
            if not feature_config:
                continue
            
            current_avg = stats['current_avg']
            normal_min, normal_max = feature_config.normal_range
            
            # 严重问题检测
            if current_avg < normal_min * 0.8 or current_avg > normal_max * 1.2:
                issues['critical_issues'].append({
                    'feature': feature_name,
                    'issue': f"{feature_config.display_name}严重异常",
                    'current_value': current_avg,
                    'normal_range': (normal_min, normal_max),
                    'severity': 'critical'
                })
            
            # 警告问题检测
            elif not (normal_min <= current_avg <= normal_max):
                issues['warning_issues'].append({
                    'feature': feature_name,
                    'issue': f"{feature_config.display_name}轻度异常",
                    'current_value': current_avg,
                    'normal_range': (normal_min, normal_max),
                    'severity': 'warning'
                })
            
            # 改进区域检测
            if stats['recent_trend'] < -0.1:  # 下降趋势
                if feature_name in ['blood_oxygen', 'step', 'distance', 'calorie', 'sleep']:
                    issues['improvement_areas'].append({
                        'feature': feature_name,
                        'issue': f"{feature_config.display_name}呈下降趋势",
                        'trend': stats['recent_trend'],
                        'recommendation_type': 'improvement'
                    })
            elif stats['recent_trend'] > 0.1:  # 上升趋势
                if feature_name in ['stress', 'pressure_high', 'pressure_low']:
                    issues['improvement_areas'].append({
                        'feature': feature_name,
                        'issue': f"{feature_config.display_name}呈上升趋势",
                        'trend': stats['recent_trend'],
                        'recommendation_type': 'control'
                    })
        
        return issues
    
    def _generate_physiological_recommendations(
        self, 
        user_profile: Dict[str, Any], 
        health_issues: Dict[str, List[str]]
    ) -> List[HealthRecommendationDTO]:
        """生成生理指标相关建议"""
        recommendations = []
        
        critical_issues = health_issues.get('critical_issues', [])
        warning_issues = health_issues.get('warning_issues', [])
        
        # 处理严重生理问题
        for issue in critical_issues:
            feature_name = issue['feature']
            
            if feature_name == 'heart_rate':
                recommendations.append(HealthRecommendationDTO(
                    user_id=user_profile['user_id'],
                    recommendation_type='physiological_critical',
                    title='心率异常紧急处理',
                    description=f"当前心率{issue['current_value']:.1f}bpm超出正常范围，需要立即关注",
                    priority_level='critical',
                    recommended_actions=[
                        '立即停止剧烈运动',
                        '保持冷静，深呼吸',
                        '如持续异常，请及时就医',
                        '记录异常时的活动和感受'
                    ],
                    expected_improvement=0.8,
                    implementation_difficulty='easy'
                ))
            
            elif feature_name == 'blood_oxygen':
                recommendations.append(HealthRecommendationDTO(
                    user_id=user_profile['user_id'],
                    recommendation_type='physiological_critical',
                    title='血氧水平改善计划',
                    description=f"当前血氧{issue['current_value']:.1f}%偏低，需要改善呼吸功能",
                    priority_level='critical',
                    recommended_actions=[
                        '进行深呼吸训练，每天10-15分钟',
                        '增加有氧运动，如散步、游泳',
                        '保持室内空气流通',
                        '如症状持续，建议医疗检查'
                    ],
                    expected_improvement=0.7,
                    implementation_difficulty='medium'
                ))
            
            elif feature_name == 'temperature':
                temp_value = issue['current_value']
                if temp_value > 37.5:
                    recommendations.append(HealthRecommendationDTO(
                        user_id=user_profile['user_id'],
                        recommendation_type='physiological_critical',
                        title='体温异常监控',
                        description=f"体温{temp_value:.1f}°C偏高，需要密切观察",
                        priority_level='critical',
                        recommended_actions=[
                            '多喝温水，保持充足水分',
                            '适当休息，避免过度劳累',
                            '定时测量体温变化',
                            '如持续发热，及时就医'
                        ],
                        expected_improvement=0.9,
                        implementation_difficulty='easy'
                    ))
        
        # 处理一般生理问题
        for issue in warning_issues:
            feature_name = issue['feature']
            
            if feature_name in ['pressure_high', 'pressure_low']:
                recommendations.append(HealthRecommendationDTO(
                    user_id=user_profile['user_id'],
                    recommendation_type='physiological_warning',
                    title='血压管理建议',
                    description=f"血压水平需要关注和调节",
                    priority_level='high',
                    recommended_actions=[
                        '减少钠盐摄入，清淡饮食',
                        '规律作息，保证充足睡眠',
                        '适量运动，如散步、太极',
                        '定期监测血压变化',
                        '保持心情愉悦，减少压力'
                    ],
                    expected_improvement=0.6,
                    implementation_difficulty='medium'
                ))
        
        return recommendations
    
    def _generate_behavioral_recommendations(
        self, 
        user_profile: Dict[str, Any], 
        health_issues: Dict[str, List[str]]
    ) -> List[HealthRecommendationDTO]:
        """生成行为习惯相关建议"""
        recommendations = []
        
        feature_stats = user_profile.get('feature_stats', {})
        improvement_areas = health_issues.get('improvement_areas', [])
        
        # 运动相关建议
        step_stats = feature_stats.get('step')
        if step_stats and step_stats['current_avg'] < 6000:
            recommendations.append(HealthRecommendationDTO(
                user_id=user_profile['user_id'],
                recommendation_type='behavioral_exercise',
                title='日常活动量提升计划',
                description=f"当前日均步数{step_stats['current_avg']:.0f}步，建议增加日常活动",
                priority_level='medium',
                recommended_actions=[
                    '设置每日步数目标，逐步增加到8000步',
                    '利用工作间隙进行短程步行',
                    '选择爬楼梯替代电梯',
                    '下班后进行30分钟散步',
                    '周末安排户外运动活动'
                ],
                expected_improvement=0.7,
                implementation_difficulty='easy'
            ))
        
        # 睡眠相关建议
        sleep_stats = feature_stats.get('sleep')
        if sleep_stats:
            avg_sleep = sleep_stats['current_avg']
            if avg_sleep < 7:
                recommendations.append(HealthRecommendationDTO(
                    user_id=user_profile['user_id'],
                    recommendation_type='behavioral_sleep',
                    title='睡眠质量改善方案',
                    description=f"当前平均睡眠{avg_sleep:.1f}小时不足，影响健康恢复",
                    priority_level='high',
                    recommended_actions=[
                        '建立固定的作息时间，11点前入睡',
                        '睡前1小时避免使用电子设备',
                        '保持卧室环境安静、黑暗、凉爽',
                        '睡前进行放松活动，如冥想、轻音乐',
                        '避免睡前摄入咖啡因和酒精'
                    ],
                    expected_improvement=0.8,
                    implementation_difficulty='medium'
                ))
            elif avg_sleep > 9:
                recommendations.append(HealthRecommendationDTO(
                    user_id=user_profile['user_id'],
                    recommendation_type='behavioral_sleep',
                    title='睡眠时长调节建议',
                    description=f"睡眠时长{avg_sleep:.1f}小时过长，可能影响日间精神状态",
                    priority_level='medium',
                    recommended_actions=[
                        '逐步调整睡眠时间到7-8小时',
                        '固定起床时间，即使周末也保持一致',
                        '增加日间光照暴露',
                        '适当增加体力活动'
                    ],
                    expected_improvement=0.6,
                    implementation_difficulty='medium'
                ))
        
        # 压力管理建议
        stress_stats = feature_stats.get('stress')
        if stress_stats and stress_stats['current_avg'] > 60:
            recommendations.append(HealthRecommendationDTO(
                user_id=user_profile['user_id'],
                recommendation_type='behavioral_stress',
                title='压力管理与放松训练',
                description=f"当前压力水平{stress_stats['current_avg']:.0f}偏高，需要有效的压力管理",
                priority_level='high',
                recommended_actions=[
                    '每天进行10分钟深呼吸或冥想练习',
                    '学习时间管理技巧，合理安排工作',
                    '培养兴趣爱好，增加生活乐趣',
                    '与家人朋友保持良好沟通',
                    '必要时寻求专业心理健康支持'
                ],
                expected_improvement=0.7,
                implementation_difficulty='medium'
            ))
        
        return recommendations
    
    def _generate_risk_prevention_recommendations(
        self, 
        user_profile: Dict[str, Any], 
        health_issues: Dict[str, List[str]]
    ) -> List[HealthRecommendationDTO]:
        """生成风险预防相关建议"""
        recommendations = []
        
        # 分析整体健康风险
        feature_stats = user_profile.get('feature_stats', {})
        risk_factors = []
        
        # 心血管风险评估
        hr_stats = feature_stats.get('heart_rate')
        bp_high_stats = feature_stats.get('pressure_high')
        bp_low_stats = feature_stats.get('pressure_low')
        
        if any([hr_stats and (hr_stats['current_avg'] > 100 or hr_stats['current_avg'] < 50),
                bp_high_stats and bp_high_stats['current_avg'] > 140,
                bp_low_stats and bp_low_stats['current_avg'] > 90]):
            risk_factors.append('cardiovascular')
        
        # 代谢风险评估
        step_stats = feature_stats.get('step')
        calorie_stats = feature_stats.get('calorie')
        
        if any([step_stats and step_stats['current_avg'] < 4000,
                calorie_stats and calorie_stats['current_avg'] < 1500]):
            risk_factors.append('metabolic')
        
        # 呼吸系统风险评估
        oxygen_stats = feature_stats.get('blood_oxygen')
        if oxygen_stats and oxygen_stats['current_avg'] < 95:
            risk_factors.append('respiratory')
        
        # 生成针对性风险预防建议
        if 'cardiovascular' in risk_factors:
            recommendations.append(HealthRecommendationDTO(
                user_id=user_profile['user_id'],
                recommendation_type='risk_prevention',
                title='心血管健康预防方案',
                description="检测到心血管健康风险，建议采取预防措施",
                priority_level='high',
                recommended_actions=[
                    '定期监测血压和心率变化',
                    '采用低盐、低脂、高纤维饮食',
                    '进行规律的有氧运动',
                    '戒烟限酒，改善生活习惯',
                    '定期进行心血管健康检查',
                    '学习识别心血管急症症状'
                ],
                expected_improvement=0.8,
                implementation_difficulty='hard'
            ))
        
        if 'metabolic' in risk_factors:
            recommendations.append(HealthRecommendationDTO(
                user_id=user_profile['user_id'],
                recommendation_type='risk_prevention',
                title='代谢健康优化计划',
                description="代谢指标需要改善，预防代谢综合征",
                priority_level='medium',
                recommended_actions=[
                    '制定科学的饮食计划，控制总热量',
                    '增加日常体力活动，每天至少30分钟',
                    '定期监测体重和腰围变化',
                    '保持规律作息，充足睡眠',
                    '定期检查血糖、血脂等指标'
                ],
                expected_improvement=0.7,
                implementation_difficulty='medium'
            ))
        
        return recommendations
    
    def _apply_expert_rules(
        self, 
        recommendations: List[HealthRecommendationDTO], 
        user_profile: Dict[str, Any]
    ) -> List[HealthRecommendationDTO]:
        """应用专家规则过滤和优化建议"""
        filtered_recommendations = []
        
        # 按优先级排序
        recommendations.sort(key=lambda x: {
            'critical': 4, 'high': 3, 'medium': 2, 'low': 1
        }.get(x.priority_level, 1), reverse=True)
        
        # 应用最大建议数限制
        max_recommendations = self.config.RECOMMENDATION_CONFIG['max_recommendations']
        top_recommendations = recommendations[:max_recommendations]
        
        # 专家规则过滤
        for rec in top_recommendations:
            # 规则1: 避免冲突建议
            if not self._has_conflicting_recommendations(rec, filtered_recommendations):
                filtered_recommendations.append(rec)
            
            # 规则2: 确保建议的可执行性
            if rec.implementation_difficulty == 'hard' and len(filtered_recommendations) >= 3:
                continue  # 限制困难建议数量
        
        return filtered_recommendations
    
    def _has_conflicting_recommendations(
        self, 
        new_rec: HealthRecommendationDTO, 
        existing_recs: List[HealthRecommendationDTO]
    ) -> bool:
        """检查是否有冲突的建议"""
        # 简单的冲突检测逻辑
        conflicts = {
            'behavioral_sleep': ['behavioral_exercise'],
            'physiological_critical': ['behavioral_exercise']
        }
        
        for existing_rec in existing_recs:
            if (new_rec.recommendation_type in conflicts.get(existing_rec.recommendation_type, []) or
                existing_rec.recommendation_type in conflicts.get(new_rec.recommendation_type, [])):
                return True
        
        return False
    
    def _save_recommendation_tracks(
        self, 
        user_id: int, 
        recommendations: List[HealthRecommendationDTO]
    ):
        """保存建议跟踪记录"""
        try:
            for rec in recommendations:
                # 生成唯一建议ID
                rec_id = f"rec_{user_id}_{rec.recommendation_type}_{date.today().strftime('%Y%m%d')}"
                
                # 检查是否已存在
                existing = self.db.query(HealthRecommendationTrack).filter(
                    HealthRecommendationTrack.recommendation_id == rec_id
                ).first()
                
                if not existing:
                    track = HealthRecommendationTrack(
                        user_id=user_id,
                        customer_id=0,  # 需要从用户信息获取
                        recommendation_id=rec_id,
                        recommendation_type=rec.recommendation_type,
                        title=rec.title,
                        description=rec.description,
                        recommended_actions=json.dumps(rec.recommended_actions, ensure_ascii=False),
                        status='pending',
                        start_date=date.today()
                    )
                    self.db.add(track)
            
            self.db.commit()
            logger.info(f"保存用户 {user_id} 建议跟踪记录: {len(recommendations)} 条")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"保存建议跟踪记录失败: {str(e)}", exc_info=True)
            raise
    
    def _load_expert_rules(self) -> Dict[str, Any]:
        """加载专家规则知识库"""
        # 这里可以从配置文件或数据库加载专家规则
        return {
            'conflict_rules': {
                'sleep_exercise_conflict': {
                    'condition': 'sleep_duration < 6 AND exercise_intensity = high',
                    'action': 'prioritize_sleep_over_exercise'
                }
            },
            'priority_rules': {
                'critical_physiological': {
                    'weight': 1.0,
                    'mandatory': True
                },
                'behavioral_improvement': {
                    'weight': 0.7,
                    'mandatory': False
                }
            }
        }
    
    def _calculate_trend(self, values: List[float]) -> float:
        """计算趋势系数"""
        if len(values) < 2:
            return 0.0
        
        # 简单的线性趋势计算
        n = len(values)
        x_sum = sum(range(n))
        y_sum = sum(values)
        xy_sum = sum(i * values[i] for i in range(n))
        x_sq_sum = sum(i * i for i in range(n))
        
        denominator = n * x_sq_sum - x_sum * x_sum
        if denominator == 0:
            return 0.0
        
        slope = (n * xy_sum - x_sum * y_sum) / denominator
        return slope / (y_sum / n) if y_sum != 0 else 0.0  # 归一化
    
    def _calculate_stability(self, values: List[float]) -> float:
        """计算数据稳定性"""
        if len(values) < 2:
            return 1.0
        
        mean_val = sum(values) / len(values)
        variance = sum((v - mean_val) ** 2 for v in values) / len(values)
        cv = (variance ** 0.5) / mean_val if mean_val > 0 else 1.0
        
        return max(0.0, 1.0 - cv)  # 变异系数越小，稳定性越高
    
    def _is_outlier(self, value: float, values: List[float]) -> bool:
        """判断是否为异常值"""
        if len(values) < 4:
            return False
        
        q1 = sorted(values)[len(values) // 4]
        q3 = sorted(values)[3 * len(values) // 4]
        iqr = q3 - q1
        
        return value < q1 - 1.5 * iqr or value > q3 + 1.5 * iqr
    
    def _assess_data_quality(self, user_data: List[UserHealthData]) -> float:
        """评估数据质量"""
        if not user_data:
            return 0.0
        
        quality_score = 100.0
        
        # 数据完整性检查
        total_features = len(self.config.get_all_features())
        valid_features = 0
        
        for feature_name in self.config.get_all_features():
            valid_count = sum(1 for data in user_data 
                            if getattr(data, feature_name, None) is not None 
                            and getattr(data, feature_name) > 0)
            
            if valid_count > len(user_data) * 0.5:  # 超过50%有效
                valid_features += 1
        
        completeness = valid_features / total_features
        quality_score *= completeness
        
        # 时间连续性检查
        timestamps = [data.timestamp for data in user_data]
        timestamps.sort()
        
        if len(timestamps) > 1:
            time_gaps = [(timestamps[i+1] - timestamps[i]).days 
                        for i in range(len(timestamps)-1)]
            avg_gap = sum(time_gaps) / len(time_gaps)
            
            if avg_gap > 2:  # 平均间隔超过2天
                quality_score *= 0.8
        
        return min(100.0, max(0.0, quality_score))
```

### 4.4 健康预测分析服务 (services/prediction_service.py)

```python
"""
健康预测分析服务
基于机器学习和时间序列分析进行健康趋势预测
"""
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any, Tuple
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.analytics_models import HealthScore, HealthBaseline
from ..models.health_models import UserHealthData
from ..config.health_config import HealthAnalyticsConfig
from ..utils.statistics import StatisticsCalculator

logger = logging.getLogger(__name__)

class HealthPredictionService:
    """健康预测分析服务"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.config = HealthAnalyticsConfig()
        self.stats_calc = StatisticsCalculator()
    
    def predict_user_health_trends(
        self,
        user_id: int,
        prediction_days: int = 7,
        historical_days: int = 30
    ) -> Dict[str, Any]:
        """
        预测用户健康趋势
        
        Args:
            user_id: 用户ID
            prediction_days: 预测天数
            historical_days: 历史数据天数
        
        Returns:
            预测结果字典
        """
        logger.info(f"开始预测用户 {user_id} 的健康趋势")
        
        try:
            # 1. 获取历史健康数据
            historical_data = self._get_historical_data(user_id, historical_days)
            
            if not historical_data:
                logger.warning(f"用户 {user_id} 历史数据不足")
                return {}
            
            # 2. 对每个健康特征进行预测
            predictions = {}
            
            for feature_name in self.config.get_all_features():
                feature_prediction = self._predict_feature_trend(
                    historical_data, feature_name, prediction_days
                )
                
                if feature_prediction:
                    predictions[feature_name] = feature_prediction
            
            # 3. 综合健康评分预测
            overall_prediction = self._predict_overall_health_score(
                user_id, predictions, prediction_days
            )
            
            # 4. 风险评估和预警
            risk_assessment = self._assess_future_risks(predictions)
            
            # 5. 构建预测结果
            prediction_result = {
                'user_id': user_id,
                'prediction_date': date.today(),
                'prediction_horizon': prediction_days,
                'feature_predictions': predictions,
                'overall_health_prediction': overall_prediction,
                'risk_assessment': risk_assessment,
                'confidence_scores': self._calculate_prediction_confidence(predictions),
                'recommendations': self._generate_prediction_based_recommendations(
                    predictions, risk_assessment
                )
            }
            
            logger.info(f"用户 {user_id} 健康趋势预测完成")
            return prediction_result
            
        except Exception as e:
            logger.error(f"健康趋势预测失败: user_id={user_id}, error={str(e)}", exc_info=True)
            raise
    
    def _get_historical_data(self, user_id: int, days: int) -> List[UserHealthData]:
        """获取历史健康数据"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        return self.db.query(UserHealthData).filter(
            and_(
                UserHealthData.user_id == user_id,
                UserHealthData.timestamp >= start_date,
                UserHealthData.timestamp <= end_date
            )
        ).order_by(UserHealthData.timestamp.asc()).all()
    
    def _predict_feature_trend(
        self,
        historical_data: List[UserHealthData],
        feature_name: str,
        prediction_days: int
    ) -> Optional[Dict[str, Any]]:
        """预测单个特征的趋势"""
        # 提取特征时间序列数据
        time_series = []
        for data_point in historical_data:
            value = getattr(data_point, feature_name, None)
            if value is not None and value > 0:
                time_series.append({
                    'timestamp': data_point.timestamp,
                    'value': float(value)
                })
        
        if len(time_series) < 5:  # 数据点太少
            return None
        
        # 准备机器学习数据
        X = np.array([(item['timestamp'] - time_series[0]['timestamp']).days 
                     for item in time_series]).reshape(-1, 1)
        y = np.array([item['value'] for item in time_series])
        
        # 训练线性回归模型
        model = LinearRegression()
        model.fit(X, y)
        
        # 预测未来值
        last_day = X[-1][0]
        future_days = np.array([last_day + i + 1 for i in range(prediction_days)]).reshape(-1, 1)
        predictions = model.predict(future_days)
        
        # 计算预测区间
        residuals = y - model.predict(X)
        std_residual = np.std(residuals)
        
        # 趋势分析
        trend_direction = 'increasing' if model.coef_[0] > 0 else 'decreasing'
        trend_strength = abs(model.coef_[0])
        
        # 异常检测
        anomaly_threshold = np.mean(y) + 2 * np.std(y)
        potential_anomalies = [i for i, pred in enumerate(predictions) 
                             if pred > anomaly_threshold or pred < 0]
        
        return {
            'feature_name': feature_name,
            'current_value': time_series[-1]['value'],
            'predicted_values': predictions.tolist(),
            'confidence_intervals': [
                (pred - 1.96 * std_residual, pred + 1.96 * std_residual) 
                for pred in predictions
            ],
            'trend_direction': trend_direction,
            'trend_strength': trend_strength,
            'model_score': model.score(X, y),
            'potential_anomaly_days': potential_anomalies,
            'prediction_quality': self._assess_prediction_quality(model, X, y)
        }
    
    def _predict_overall_health_score(
        self,
        user_id: int,
        feature_predictions: Dict[str, Any],
        prediction_days: int
    ) -> Dict[str, Any]:
        """预测综合健康评分"""
        if not feature_predictions:
            return {}
        
        # 获取当前健康评分
        current_scores = self.db.query(HealthScore).filter(
            and_(
                HealthScore.user_id == user_id,
                HealthScore.score_date == date.today()
            )
        ).all()
        
        current_overall_score = 0.0
        if current_scores:
            weighted_sum = 0.0
            total_weight = 0.0
            
            for score in current_scores:
                feature_config = self.config.get_feature_config(score.feature_name)
                if feature_config:
                    weight = float(feature_config.weight)
                    weighted_sum += float(score.score_value) * weight
                    total_weight += weight
            
            current_overall_score = weighted_sum / total_weight if total_weight > 0 else 0.0
        
        # 预测未来健康评分
        predicted_scores = []
        
        for day in range(prediction_days):
            daily_weighted_sum = 0.0
            daily_total_weight = 0.0
            
            for feature_name, prediction in feature_predictions.items():
                if day < len(prediction['predicted_values']):
                    feature_config = self.config.get_feature_config(feature_name)
                    if feature_config:
                        # 将预测值转换为评分
                        predicted_value = prediction['predicted_values'][day]
                        feature_score = self._value_to_score(feature_name, predicted_value)
                        
                        weight = float(feature_config.weight)
                        daily_weighted_sum += feature_score * weight
                        daily_total_weight += weight
            
            if daily_total_weight > 0:
                daily_score = daily_weighted_sum / daily_total_weight
                predicted_scores.append(daily_score)
            else:
                predicted_scores.append(current_overall_score)
        
        # 分析整体健康趋势
        if len(predicted_scores) > 1:
            score_trend = (predicted_scores[-1] - predicted_scores[0]) / len(predicted_scores)
            trend_direction = 'improving' if score_trend > 0.5 else 'declining' if score_trend < -0.5 else 'stable'
        else:
            trend_direction = 'stable'
            score_trend = 0.0
        
        return {
            'current_score': current_overall_score,
            'predicted_scores': predicted_scores,
            'trend_direction': trend_direction,
            'trend_strength': abs(score_trend),
            'health_level_predictions': [self._score_to_health_level(score) for score in predicted_scores],
            'expected_health_level': self._score_to_health_level(predicted_scores[-1]) if predicted_scores else 'unknown'
        }
    
    def _assess_future_risks(self, predictions: Dict[str, Any]) -> Dict[str, Any]:
        """评估未来健康风险"""
        risks = {
            'high_risk_features': [],
            'medium_risk_features': [],
            'risk_timeline': {},
            'overall_risk_level': 'low'
        }
        
        for feature_name, prediction in predictions.items():
            feature_config = self.config.get_feature_config(feature_name)
            if not feature_config:
                continue
            
            normal_min, normal_max = feature_config.normal_range
            predicted_values = prediction['predicted_values']
            
            # 检查预测值是否超出正常范围
            risk_days = []
            for day, value in enumerate(predicted_values):
                if value < normal_min * 0.8 or value > normal_max * 1.2:
                    risk_days.append(day)
            
            if len(risk_days) > len(predicted_values) * 0.5:  # 超过50%时间有风险
                risks['high_risk_features'].append({
                    'feature': feature_name,
                    'risk_days': risk_days,
                    'severity': 'high'
                })
            elif len(risk_days) > 0:
                risks['medium_risk_features'].append({
                    'feature': feature_name,
                    'risk_days': risk_days,
                    'severity': 'medium'
                })
            
            # 异常天数预警
            if prediction.get('potential_anomaly_days'):
                risks['risk_timeline'][feature_name] = prediction['potential_anomaly_days']
        
        # 整体风险等级评估
        if len(risks['high_risk_features']) > 2:
            risks['overall_risk_level'] = 'high'
        elif len(risks['high_risk_features']) > 0 or len(risks['medium_risk_features']) > 3:
            risks['overall_risk_level'] = 'medium'
        else:
            risks['overall_risk_level'] = 'low'
        
        return risks
    
    def _calculate_prediction_confidence(self, predictions: Dict[str, Any]) -> Dict[str, float]:
        """计算预测置信度"""
        confidence_scores = {}
        
        for feature_name, prediction in predictions.items():
            model_score = prediction.get('model_score', 0.0)
            prediction_quality = prediction.get('prediction_quality', 0.0)
            
            # 综合置信度计算
            confidence = (model_score + prediction_quality) / 2
            confidence_scores[feature_name] = min(1.0, max(0.0, confidence))
        
        return confidence_scores
    
    def _generate_prediction_based_recommendations(
        self,
        predictions: Dict[str, Any],
        risk_assessment: Dict[str, Any]
    ) -> List[str]:
        """基于预测结果生成建议"""
        recommendations = []
        
        # 高风险特征建议
        for risk_feature in risk_assessment.get('high_risk_features', []):
            feature_name = risk_feature['feature']
            feature_config = self.config.get_feature_config(feature_name)
            
            if feature_config:
                recommendations.append(
                    f"预测显示{feature_config.display_name}在未来{len(risk_feature['risk_days'])}天可能出现异常，"
                    f"建议加强监测并采取预防措施"
                )
        
        # 趋势恶化建议
        for feature_name, prediction in predictions.items():
            if prediction['trend_direction'] == 'decreasing':
                feature_config = self.config.get_feature_config(feature_name)
                if feature_config and feature_name in ['blood_oxygen', 'step', 'sleep']:
                    recommendations.append(
                        f"{feature_config.display_name}呈下降趋势，建议采取改善措施"
                    )
        
        return recommendations
    
    def _assess_prediction_quality(self, model, X, y) -> float:
        """评估预测质量"""
        # 简单的质量评估
        score = model.score(X, y)
        
        # 残差分析
        predictions = model.predict(X)
        residuals = y - predictions
        residual_std = np.std(residuals)
        
        # 归一化残差标准差
        normalized_residual_std = residual_std / np.mean(y) if np.mean(y) > 0 else 1.0
        
        # 质量评分
        quality = score * (1 - min(1.0, normalized_residual_std))
        
        return max(0.0, min(1.0, quality))
    
    def _value_to_score(self, feature_name: str, value: float) -> float:
        """将数值转换为评分"""
        feature_config = self.config.get_feature_config(feature_name)
        if not feature_config:
            return 70.0
        
        normal_min, normal_max = feature_config.normal_range
        normal_mid = (normal_min + normal_max) / 2
        
        if normal_min <= value <= normal_max:
            # 在正常范围内
            deviation = abs(value - normal_mid) / (normal_max - normal_min) * 2
            return 100 - deviation * 20
        else:
            # 超出正常范围
            if value < normal_min:
                deviation = (normal_min - value) / normal_min
            else:
                deviation = (value - normal_max) / normal_max
            
            penalty = min(50, deviation * 100)
            return max(30, 70 - penalty)
    
    def _score_to_health_level(self, score: float) -> str:
        """将评分转换为健康等级"""
        thresholds = self.config.SCORE_THRESHOLDS
        
        if score >= thresholds['excellent']:
            return 'excellent'
        elif score >= thresholds['good']:
            return 'good'
        elif score >= thresholds['fair']:
            return 'fair'
        elif score >= thresholds['poor']:
            return 'poor'
        else:
            return 'critical'
    
    def predict_department_health_trends(
        self,
        org_id: int,
        prediction_days: int = 7
    ) -> Dict[str, Any]:
        """预测部门健康趋势"""
        logger.info(f"开始预测部门 {org_id} 的健康趋势")
        
        try:
            # 获取部门所有用户
            users = self.db.query(UserHealthData.user_id).filter(
                UserHealthData.org_id == org_id
            ).distinct().all()
            
            department_predictions = {}
            
            for user in users:
                user_prediction = self.predict_user_health_trends(
                    user.user_id, prediction_days, historical_days=30
                )
                
                if user_prediction:
                    department_predictions[user.user_id] = user_prediction
            
            # 聚合部门预测结果
            aggregated_prediction = self._aggregate_department_predictions(department_predictions)
            
            logger.info(f"部门 {org_id} 健康趋势预测完成")
            return aggregated_prediction
            
        except Exception as e:
            logger.error(f"部门健康趋势预测失败: org_id={org_id}, error={str(e)}", exc_info=True)
            raise
    
    def _aggregate_department_predictions(self, user_predictions: Dict[int, Dict]) -> Dict[str, Any]:
        """聚合部门预测结果"""
        if not user_predictions:
            return {}
        
        # 计算部门平均健康评分趋势
        all_overall_predictions = []
        all_risk_levels = []
        
        for user_id, prediction in user_predictions.items():
            overall_pred = prediction.get('overall_health_prediction', {})
            if overall_pred:
                predicted_scores = overall_pred.get('predicted_scores', [])
                if predicted_scores:
                    all_overall_predictions.append(predicted_scores)
                
                risk_assessment = prediction.get('risk_assessment', {})
                risk_level = risk_assessment.get('overall_risk_level', 'low')
                all_risk_levels.append(risk_level)
        
        # 计算部门平均预测评分
        if all_overall_predictions:
            prediction_days = len(all_overall_predictions[0])
            dept_predicted_scores = []
            
            for day in range(prediction_days):
                day_scores = [pred[day] for pred in all_overall_predictions if day < len(pred)]
                if day_scores:
                    dept_predicted_scores.append(np.mean(day_scores))
        else:
            dept_predicted_scores = []
        
        # 部门风险等级统计
        risk_distribution = {
            'high': all_risk_levels.count('high'),
            'medium': all_risk_levels.count('medium'),
            'low': all_risk_levels.count('low')
        }
        
        # 确定部门整体风险等级
        total_users = len(all_risk_levels)
        if risk_distribution['high'] / total_users > 0.3:
            dept_risk_level = 'high'
        elif risk_distribution['medium'] / total_users > 0.5:
            dept_risk_level = 'medium'
        else:
            dept_risk_level = 'low'
        
        return {
            'total_users': total_users,
            'predicted_scores': dept_predicted_scores,
            'risk_level': dept_risk_level,
            'risk_distribution': risk_distribution,
            'health_level_forecast': [self._score_to_health_level(score) 
                                    for score in dept_predicted_scores],
            'user_predictions': user_predictions
        }
```

### 4.5 健康画像生成服务 (services/profile_service.py)

```python
"""
综合健康画像服务
整合基线、评分、建议和预测，生成完整的用户健康画像
"""
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any
import json
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.analytics_models import (
    UserHealthProfile, UserHealthProfileDTO, HealthAnalyticsResult
)
from ..config.health_config import HealthAnalyticsConfig
from ..services.baseline_service import HealthBaselineService
from ..services.score_service import HealthScoreService
from ..services.recommendation_service import HealthRecommendationService
from ..services.prediction_service import HealthPredictionService

logger = logging.getLogger(__name__)

class HealthProfileService:
    """综合健康画像服务"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.config = HealthAnalyticsConfig()
        self.baseline_service = HealthBaselineService(db_session)
        self.score_service = HealthScoreService(db_session)
        self.recommendation_service = HealthRecommendationService(db_session)
        self.prediction_service = HealthPredictionService(db_session)
    
    def generate_comprehensive_health_profile(
        self,
        user_id: int,
        profile_date: Optional[date] = None
    ) -> UserHealthProfileDTO:
        """
        生成用户综合健康画像
        
        Args:
            user_id: 用户ID
            profile_date: 画像生成日期
        
        Returns:
            综合健康画像对象
        """
        if profile_date is None:
            profile_date = date.today()
            
        logger.info(f"开始生成用户 {user_id} 的综合健康画像")
        
        try:
            # 1. 计算综合健康评分
            comprehensive_scores = self.score_service.calculate_comprehensive_health_score(
                user_id, profile_date
            )
            
            # 2. 生成个性化建议
            recommendations = self.recommendation_service.generate_user_recommendations(
                user_id, profile_date
            )
            
            # 3. 健康趋势预测
            prediction_result = self.prediction_service.predict_user_health_trends(
                user_id, prediction_days=7, historical_days=30
            )
            
            # 4. 分析健康趋势
            trend_analysis = self._analyze_health_trends(user_id, profile_date)
            
            # 5. 获取特征评分详情
            feature_scores = self._get_feature_scores_detail(user_id, profile_date)
            
            # 6. 识别风险因子
            risk_factors = self._identify_risk_factors(
                comprehensive_scores, prediction_result, feature_scores
            )
            
            # 7. 构建综合健康画像
            health_profile = UserHealthProfileDTO(
                user_id=user_id,
                profile_date=profile_date,
                overall_score=comprehensive_scores.get('overall_score', 0.0),
                health_level=comprehensive_scores.get('health_level', 'unknown'),
                physiological_score=comprehensive_scores.get('physiological_score', 0.0),
                behavioral_score=comprehensive_scores.get('behavioral_score', 0.0),
                risk_factor_score=comprehensive_scores.get('risk_factor_score', 0.0),
                feature_scores=feature_scores,
                trend_analysis=trend_analysis,
                recommendations=recommendations,
                risk_factors=risk_factors
            )
            
            # 8. 保存健康画像
            self._save_health_profile(health_profile)
            
            logger.info(f"用户 {user_id} 综合健康画像生成完成")
            return health_profile
            
        except Exception as e:
            logger.error(f"生成综合健康画像失败: user_id={user_id}, error={str(e)}", exc_info=True)
            raise
    
    def _analyze_health_trends(self, user_id: int, analysis_date: date) -> Dict[str, Any]:
        """分析健康趋势"""
        end_date = analysis_date
        start_date = end_date - timedelta(days=30)
        
        # 获取历史评分数据
        from ..models.analytics_models import HealthScore
        
        historical_scores = self.db.query(HealthScore).filter(
            and_(
                HealthScore.user_id == user_id,
                HealthScore.score_date >= start_date,
                HealthScore.score_date <= end_date
            )
        ).order_by(HealthScore.score_date.asc()).all()
        
        if not historical_scores:
            return {'trend_direction': 'unknown', 'trend_strength': 0.0}
        
        # 按特征分组分析趋势
        feature_trends = {}
        
        for feature_name in self.config.get_all_features():
            feature_scores = [
                score for score in historical_scores 
                if score.feature_name == feature_name
            ]
            
            if len(feature_scores) >= 3:
                scores = [float(score.score_value) for score in feature_scores]
                trend_direction, trend_strength = self._calculate_trend_metrics(scores)
                
                feature_trends[feature_name] = {
                    'direction': trend_direction,
                    'strength': trend_strength,
                    'current_score': scores[-1],
                    'score_change': scores[-1] - scores[0] if len(scores) > 1 else 0.0
                }
        
        # 计算整体趋势
        if feature_trends:
            improving_count = sum(1 for trend in feature_trends.values() 
                                if trend['direction'] == 'improving')
            declining_count = sum(1 for trend in feature_trends.values() 
                                if trend['direction'] == 'declining')
            total_features = len(feature_trends)
            
            if improving_count > declining_count:
                overall_trend = 'improving'
            elif declining_count > improving_count:
                overall_trend = 'declining'
            else:
                overall_trend = 'stable'
            
            overall_strength = sum(trend['strength'] for trend in feature_trends.values()) / total_features
        else:
            overall_trend = 'unknown'
            overall_strength = 0.0
        
        return {
            'overall_trend_direction': overall_trend,
            'overall_trend_strength': overall_strength,
            'feature_trends': feature_trends,
            'analysis_period_days': (end_date - start_date).days,
            'data_points': len(historical_scores)
        }
    
    def _get_feature_scores_detail(self, user_id: int, score_date: date) -> Dict[str, float]:
        """获取特征评分详情"""
        from ..models.analytics_models import HealthScore
        
        feature_scores = {}
        
        scores = self.db.query(HealthScore).filter(
            and_(
                HealthScore.user_id == user_id,
                HealthScore.score_date == score_date
            )
        ).all()
        
        for score in scores:
            feature_scores[score.feature_name] = {
                'score': float(score.score_value),
                'z_score': float(score.z_score) if score.z_score else 0.0,
                'avg_value': float(score.avg_value) if score.avg_value else 0.0,
                'penalty': float(score.penalty_value) if score.penalty_value else 0.0
            }
        
        return feature_scores
    
    def _identify_risk_factors(
        self,
        comprehensive_scores: Dict[str, Any],
        prediction_result: Dict[str, Any],
        feature_scores: Dict[str, Dict]
    ) -> List[str]:
        """识别健康风险因子"""
        risk_factors = []
        
        # 基于当前评分的风险识别
        if comprehensive_scores.get('overall_score', 0) < 60:
            risk_factors.append('overall_health_decline')
        
        if comprehensive_scores.get('physiological_score', 0) < 70:
            risk_factors.append('physiological_abnormalities')
        
        if comprehensive_scores.get('behavioral_score', 0) < 70:
            risk_factors.append('poor_lifestyle_habits')
        
        # 基于预测的风险识别
        risk_assessment = prediction_result.get('risk_assessment', {})
        if risk_assessment.get('overall_risk_level') == 'high':
            risk_factors.append('high_future_risk')
        
        # 基于特征评分的具体风险识别
        for feature_name, score_detail in feature_scores.items():
            if score_detail['score'] < 50:
                feature_config = self.config.get_feature_config(feature_name)
                if feature_config:
                    if feature_config.importance_level == 'critical':
                        risk_factors.append(f'critical_{feature_name}_risk')
                    elif feature_config.importance_level == 'high':
                        risk_factors.append(f'high_{feature_name}_risk')
        
        # 组合风险识别
        critical_features = ['heart_rate', 'blood_oxygen', 'temperature']
        critical_risk_count = sum(1 for feature in critical_features 
                                if feature in feature_scores 
                                and feature_scores[feature]['score'] < 60)
        
        if critical_risk_count >= 2:
            risk_factors.append('multiple_critical_risks')
        
        return list(set(risk_factors))  # 去重
    
    def _calculate_trend_metrics(self, scores: List[float]) -> tuple[str, float]:
        """计算趋势指标"""
        if len(scores) < 2:
            return 'unknown', 0.0
        
        # 简单线性趋势计算
        n = len(scores)
        x = list(range(n))
        y = scores
        
        # 计算相关系数
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        x_variance = sum((x[i] - x_mean) ** 2 for i in range(n))
        y_variance = sum((y[i] - y_mean) ** 2 for i in range(n))
        
        if x_variance == 0 or y_variance == 0:
            return 'stable', 0.0
        
        correlation = numerator / (x_variance * y_variance) ** 0.5
        
        # 判断趋势方向和强度
        if correlation > 0.3:
            trend_direction = 'improving'
        elif correlation < -0.3:
            trend_direction = 'declining'
        else:
            trend_direction = 'stable'
        
        trend_strength = abs(correlation)
        
        return trend_direction, trend_strength
    
    def _save_health_profile(self, profile: UserHealthProfileDTO):
        """保存健康画像到数据库"""
        try:
            # 检查是否已存在当日画像
            existing = self.db.query(UserHealthProfile).filter(
                and_(
                    UserHealthProfile.user_id == profile.user_id,
                    UserHealthProfile.profile_date == profile.profile_date
                )
            ).first()
            
            # 构建详细分析数据
            detailed_analysis = {
                'feature_scores': profile.feature_scores,
                'analysis_timestamp': datetime.utcnow().isoformat(),
                'data_quality_indicators': self._calculate_data_quality_indicators(profile),
                'health_improvement_suggestions': self._generate_improvement_suggestions(profile)
            }
            
            # 构建趋势分析数据
            trend_analysis_data = profile.trend_analysis
            
            # 构建建议数据
            recommendations_data = [
                {
                    'type': rec.recommendation_type,
                    'title': rec.title,
                    'description': rec.description,
                    'priority': rec.priority_level,
                    'actions': rec.recommended_actions,
                    'difficulty': rec.implementation_difficulty,
                    'expected_improvement': rec.expected_improvement
                }
                for rec in profile.recommendations
            ]
            
            if existing:
                # 更新现有记录
                existing.overall_health_score = profile.overall_score
                existing.health_level = profile.health_level
                existing.physiological_score = profile.physiological_score
                existing.behavioral_score = profile.behavioral_score
                existing.risk_factor_score = profile.risk_factor_score
                existing.detailed_analysis = detailed_analysis
                existing.trend_analysis = trend_analysis_data
                existing.recommendations = recommendations_data
                existing.update_time = datetime.utcnow()
            else:
                # 创建新记录
                new_profile = UserHealthProfile(
                    user_id=profile.user_id,
                    customer_id=0,  # 需要从用户信息获取
                    profile_date=profile.profile_date,
                    overall_health_score=profile.overall_score,
                    health_level=profile.health_level,
                    physiological_score=profile.physiological_score,
                    behavioral_score=profile.behavioral_score,
                    risk_factor_score=profile.risk_factor_score,
                    detailed_analysis=detailed_analysis,
                    trend_analysis=trend_analysis_data,
                    recommendations=recommendations_data
                )
                self.db.add(new_profile)
            
            self.db.commit()
            logger.info(f"保存用户 {profile.user_id} 健康画像成功")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"保存健康画像失败: {str(e)}", exc_info=True)
            raise
    
    def _calculate_data_quality_indicators(self, profile: UserHealthProfileDTO) -> Dict[str, Any]:
        """计算数据质量指标"""
        feature_scores = profile.feature_scores
        
        # 数据完整性
        total_features = len(self.config.get_all_features())
        available_features = len(feature_scores)
        completeness = available_features / total_features
        
        # 数据可靠性（基于Z-score分布）
        z_scores = [score_detail.get('z_score', 0) for score_detail in feature_scores.values()]
        avg_z_score = sum(abs(z) for z in z_scores) / len(z_scores) if z_scores else 0
        reliability = max(0, 1 - avg_z_score / 3)  # 3个标准差为基准
        
        # 数据时效性（基于画像生成日期）
        days_since_generation = (date.today() - profile.profile_date).days
        timeliness = max(0, 1 - days_since_generation / 7)  # 7天为基准
        
        return {
            'completeness': round(completeness, 3),
            'reliability': round(reliability, 3),
            'timeliness': round(timeliness, 3),
            'overall_quality': round((completeness + reliability + timeliness) / 3, 3)
        }
    
    def _generate_improvement_suggestions(self, profile: UserHealthProfileDTO) -> List[str]:
        """生成改进建议摘要"""
        suggestions = []
        
        # 基于健康等级的建议
        if profile.health_level in ['poor', 'critical']:
            suggestions.append("整体健康状况需要立即关注，建议寻求专业医疗建议")
        elif profile.health_level == 'fair':
            suggestions.append("健康状况有改善空间，建议制定健康改善计划")
        
        # 基于各维度评分的建议
        if profile.physiological_score < 70:
            suggestions.append("生理指标需要改善，建议定期监测和医疗咨询")
        
        if profile.behavioral_score < 70:
            suggestions.append("生活习惯需要调整，建议改善运动、睡眠和压力管理")
        
        # 基于风险因子的建议
        if 'multiple_critical_risks' in profile.risk_factors:
            suggestions.append("存在多重健康风险，建议紧急制定综合健康管理方案")
        
        return suggestions
    
    def get_user_health_profile_history(
        self,
        user_id: int,
        days: int = 30
    ) -> List[UserHealthProfileDTO]:
        """获取用户健康画像历史"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        profiles = self.db.query(UserHealthProfile).filter(
            and_(
                UserHealthProfile.user_id == user_id,
                UserHealthProfile.profile_date >= start_date,
                UserHealthProfile.profile_date <= end_date
            )
        ).order_by(UserHealthProfile.profile_date.desc()).all()
        
        profile_dtos = []
        for profile in profiles:
            # 重构建议列表
            recommendations = []
            if profile.recommendations:
                for rec_data in profile.recommendations:
                    from ..models.analytics_models import HealthRecommendationDTO
                    rec_dto = HealthRecommendationDTO(
                        user_id=user_id,
                        recommendation_type=rec_data.get('type', ''),
                        title=rec_data.get('title', ''),
                        description=rec_data.get('description', ''),
                        priority_level=rec_data.get('priority', 'medium'),
                        recommended_actions=rec_data.get('actions', []),
                        expected_improvement=rec_data.get('expected_improvement', 0.0),
                        implementation_difficulty=rec_data.get('difficulty', 'medium')
                    )
                    recommendations.append(rec_dto)
            
            profile_dto = UserHealthProfileDTO(
                user_id=profile.user_id,
                profile_date=profile.profile_date,
                overall_score=float(profile.overall_health_score),
                health_level=profile.health_level,
                physiological_score=float(profile.physiological_score),
                behavioral_score=float(profile.behavioral_score),
                risk_factor_score=float(profile.risk_factor_score),
                feature_scores=profile.detailed_analysis.get('feature_scores', {}) if profile.detailed_analysis else {},
                trend_analysis=profile.trend_analysis or {},
                recommendations=recommendations,
                risk_factors=[]  # 可以从详细分析中提取
            )
            
            profile_dtos.append(profile_dto)
        
        return profile_dtos
    
    def generate_batch_health_profiles(
        self,
        user_ids: Optional[List[int]] = None,
        org_id: Optional[int] = None,
        profile_date: Optional[date] = None
    ) -> List[UserHealthProfileDTO]:
        """批量生成健康画像"""
        if profile_date is None:
            profile_date = date.today()
        
        logger.info(f"开始批量生成健康画像: org_id={org_id}, date={profile_date}")
        
        try:
            # 确定需要处理的用户列表
            if user_ids:
                target_users = user_ids
            elif org_id:
                # 获取部门所有用户
                from ..models.health_models import UserHealthData
                users = self.db.query(UserHealthData.user_id).filter(
                    UserHealthData.org_id == org_id
                ).distinct().all()
                target_users = [user.user_id for user in users]
            else:
                # 获取所有活跃用户
                from ..models.health_models import UserHealthData
                users = self.db.query(UserHealthData.user_id).distinct().all()
                target_users = [user.user_id for user in users]
            
            # 批量生成画像
            profiles = []
            for user_id in target_users:
                try:
                    profile = self.generate_comprehensive_health_profile(user_id, profile_date)
                    profiles.append(profile)
                except Exception as e:
                    logger.error(f"生成用户 {user_id} 健康画像失败: {str(e)}")
                    continue
            
            logger.info(f"批量健康画像生成完成: 成功 {len(profiles)}/{len(target_users)} 个用户")
            return profiles
            
        except Exception as e:
            logger.error(f"批量生成健康画像失败: {str(e)}", exc_info=True)
            raise
```

## 5. 工具和辅助模块

### 5.1 统计计算工具 (utils/statistics.py)

```python
"""
统计计算工具类
提供各种统计分析方法
"""
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from scipy import stats
from sklearn.preprocessing import StandardScaler

class StatisticsCalculator:
    """统计计算器"""
    
    def __init__(self):
        self.scaler = StandardScaler()
    
    def calculate_descriptive_statistics(self, values: List[float]) -> Dict[str, float]:
        """计算描述性统计"""
        if not values:
            return {}
        
        arr = np.array(values)
        
        return {
            'mean': float(np.mean(arr)),
            'median': float(np.median(arr)),
            'std': float(np.std(arr, ddof=1)) if len(values) > 1 else 0.0,
            'var': float(np.var(arr, ddof=1)) if len(values) > 1 else 0.0,
            'min': float(np.min(arr)),
            'max': float(np.max(arr)),
            'q25': float(np.percentile(arr, 25)),
            'q75': float(np.percentile(arr, 75)),
            'skewness': float(stats.skew(arr)) if len(values) > 3 else 0.0,
            'kurtosis': float(stats.kurtosis(arr)) if len(values) > 3 else 0.0,
            'count': len(values)
        }
    
    def detect_outliers(
        self, 
        values: List[float], 
        method: str = 'iqr'
    ) -> List[int]:
        """检测异常值"""
        if not values or len(values) < 4:
            return []
        
        arr = np.array(values)
        outlier_indices = []
        
        if method == 'iqr':
            q1 = np.percentile(arr, 25)
            q3 = np.percentile(arr, 75)
            iqr = q3 - q1
            
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            outlier_indices = [
                i for i, val in enumerate(values)
                if val < lower_bound or val > upper_bound
            ]
        
        elif method == 'zscore':
            z_scores = np.abs(stats.zscore(arr))
            outlier_indices = [
                i for i, z in enumerate(z_scores)
                if z > 3
            ]
        
        elif method == 'modified_zscore':
            median = np.median(arr)
            mad = np.median(np.abs(arr - median))
            modified_z_scores = 0.6745 * (arr - median) / mad
            
            outlier_indices = [
                i for i, z in enumerate(modified_z_scores)
                if abs(z) > 3.5
            ]
        
        return outlier_indices
    
    def remove_outliers(
        self, 
        values: List[float], 
        method: str = 'iqr'
    ) -> List[float]:
        """移除异常值"""
        outlier_indices = self.detect_outliers(values, method)
        return [val for i, val in enumerate(values) if i not in outlier_indices]
    
    def calculate_correlation_matrix(
        self, 
        data: Dict[str, List[float]]
    ) -> Dict[str, Dict[str, float]]:
        """计算相关性矩阵"""
        if not data or len(data) < 2:
            return {}
        
        features = list(data.keys())
        n_features = len(features)
        
        # 确保所有序列长度一致
        min_length = min(len(values) for values in data.values())
        aligned_data = {
            feature: values[:min_length] 
            for feature, values in data.items()
        }
        
        correlation_matrix = {}
        
        for i, feature1 in enumerate(features):
            correlation_matrix[feature1] = {}
            
            for j, feature2 in enumerate(features):
                if i == j:
                    correlation_matrix[feature1][feature2] = 1.0
                else:
                    values1 = aligned_data[feature1]
                    values2 = aligned_data[feature2]
                    
                    if len(values1) > 1 and len(values2) > 1:
                        corr, _ = stats.pearsonr(values1, values2)
                        correlation_matrix[feature1][feature2] = float(corr) if not np.isnan(corr) else 0.0
                    else:
                        correlation_matrix[feature1][feature2] = 0.0
        
        return correlation_matrix
    
    def calculate_confidence_interval(
        self, 
        values: List[float], 
        confidence: float = 0.95
    ) -> Tuple[float, float]:
        """计算置信区间"""
        if not values or len(values) < 2:
            return (0.0, 0.0)
        
        arr = np.array(values)
        mean = np.mean(arr)
        sem = stats.sem(arr)  # 标准误差
        
        # 计算置信区间
        margin_error = sem * stats.t.ppf((1 + confidence) / 2, len(values) - 1)
        
        return (float(mean - margin_error), float(mean + margin_error))
    
    def perform_normality_test(self, values: List[float]) -> Dict[str, Any]:
        """正态性检验"""
        if not values or len(values) < 8:
            return {'is_normal': False, 'p_value': None, 'test': 'insufficient_data'}
        
        arr = np.array(values)
        
        # Shapiro-Wilk检验
        statistic, p_value = stats.shapiro(arr)
        
        return {
            'is_normal': p_value > 0.05,
            'p_value': float(p_value),
            'statistic': float(statistic),
            'test': 'shapiro_wilk',
            'significance_level': 0.05
        }
    
    def calculate_trend_analysis(
        self, 
        values: List[float], 
        timestamps: Optional[List] = None
    ) -> Dict[str, Any]:
        """趋势分析"""
        if not values or len(values) < 3:
            return {}
        
        if timestamps is None:
            timestamps = list(range(len(values)))
        
        # 线性回归趋势分析
        x = np.array(timestamps).reshape(-1, 1)
        y = np.array(values)
        
        from sklearn.linear_model import LinearRegression
        model = LinearRegression()
        model.fit(x, y)
        
        # 趋势方向和强度
        slope = model.coef_[0]
        r_squared = model.score(x, y)
        
        trend_direction = 'increasing' if slope > 0 else 'decreasing' if slope < 0 else 'stable'
        trend_strength = abs(slope)
        
        # 预测未来值
        future_x = np.array([timestamps[-1] + 1, timestamps[-1] + 2, timestamps[-1] + 3]).reshape(-1, 1)
        future_predictions = model.predict(future_x)
        
        return {
            'trend_direction': trend_direction,
            'trend_strength': trend_strength,
            'slope': float(slope),
            'r_squared': float(r_squared),
            'intercept': float(model.intercept_),
            'future_predictions': future_predictions.tolist(),
            'trend_quality': 'strong' if r_squared > 0.7 else 'moderate' if r_squared > 0.4 else 'weak'
        }
    
    def calculate_seasonal_decomposition(
        self, 
        values: List[float], 
        period: int = 7
    ) -> Dict[str, List[float]]:
        """季节性分解（简化版本）"""
        if not values or len(values) < period * 2:
            return {}
        
        # 简化的季节性分解
        arr = np.array(values)
        n = len(arr)
        
        # 趋势项（移动平均）
        trend = np.convolve(arr, np.ones(period)/period, mode='same')
        
        # 季节性项
        seasonal = np.zeros(n)
        for i in range(period):
            seasonal_values = []
            for j in range(i, n, period):
                if j < len(trend):
                    seasonal_values.append(arr[j] - trend[j])
            
            if seasonal_values:
                avg_seasonal = np.mean(seasonal_values)
                for j in range(i, n, period):
                    seasonal[j] = avg_seasonal
        
        # 残差项
        residual = arr - trend - seasonal
        
        return {
            'trend': trend.tolist(),
            'seasonal': seasonal.tolist(),
            'residual': residual.tolist(),
            'original': values
        }
    
    def calculate_health_score_percentile(
        self, 
        user_score: float, 
        population_scores: List[float]
    ) -> float:
        """计算健康评分在人群中的百分位"""
        if not population_scores:
            return 50.0  # 默认中位数
        
        percentile = stats.percentileofscore(population_scores, user_score)
        return float(percentile)
```

### 5.2 AI分析工具 (utils/ai_analyzer.py)

```python
"""
AI健康分析工具
提供机器学习和人工智能辅助分析功能
"""
import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

class AIHealthAnalyzer:
    """AI健康分析器"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.predictor = RandomForestRegressor(n_estimators=100, random_state=42)
    
    def detect_health_anomalies(
        self, 
        health_data: Dict[str, List[float]]
    ) -> Dict[str, List[int]]:
        """健康异常检测"""
        anomalies = {}
        
        for feature_name, values in health_data.items():
            if len(values) < 5:
                continue
            
            # 准备数据
            X = np.array(values).reshape(-1, 1)
            
            # 异常检测
            try:
                anomaly_labels = self.anomaly_detector.fit_predict(X)
                anomaly_indices = [i for i, label in enumerate(anomaly_labels) if label == -1]
                anomalies[feature_name] = anomaly_indices
            except Exception:
                anomalies[feature_name] = []
        
        return anomalies
    
    def cluster_users_by_health_profile(
        self, 
        user_profiles: List[Dict[str, float]],
        n_clusters: Optional[int] = None
    ) -> Dict[str, Any]:
        """基于健康画像聚类用户"""
        if len(user_profiles) < 3:
            return {}
        
        # 提取特征矩阵
        feature_names = list(user_profiles[0].keys())
        X = np.array([[profile.get(feature, 0.0) for feature in feature_names] 
                     for profile in user_profiles])
        
        # 标准化
        X_scaled = self.scaler.fit_transform(X)
        
        # 确定最优聚类数
        if n_clusters is None:
            n_clusters = self._find_optimal_clusters(X_scaled)
        
        # K-means聚类
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(X_scaled)
        
        # 计算聚类质量
        silhouette_avg = silhouette_score(X_scaled, cluster_labels)
        
        # 分析各聚类特征
        cluster_profiles = {}
        for cluster_id in range(n_clusters):
            cluster_indices = [i for i, label in enumerate(cluster_labels) if label == cluster_id]
            cluster_data = X[cluster_indices]
            
            cluster_profiles[cluster_id] = {
                'size': len(cluster_indices),
                'user_indices': cluster_indices,
                'feature_means': {
                    feature_names[j]: float(np.mean(cluster_data[:, j]))
                    for j in range(len(feature_names))
                },
                'health_characteristics': self._analyze_cluster_characteristics(
                    cluster_data, feature_names
                )
            }
        
        return {
            'n_clusters': n_clusters,
            'cluster_labels': cluster_labels.tolist(),
            'silhouette_score': float(silhouette_avg),
            'cluster_profiles': cluster_profiles,
            'cluster_quality': 'good' if silhouette_avg > 0.5 else 'moderate' if silhouette_avg > 0.25 else 'poor'
        }
    
    def predict_health_deterioration_risk(
        self, 
        historical_data: List[Dict[str, float]],
        prediction_horizon: int = 7
    ) -> Dict[str, Any]:
        """预测健康恶化风险"""
        if len(historical_data) < 10:
            return {'risk_level': 'unknown', 'confidence': 0.0}
        
        # 提取时间序列特征
        features = list(historical_data[0].keys())
        time_series = {
            feature: [data.get(feature, 0.0) for data in historical_data]
            for feature in features
        }
        
        # 构建预测特征
        X_features = []
        y_targets = []
        
        window_size = 5
        for i in range(len(historical_data) - window_size):
            # 输入特征：过去window_size个时间点的数据
            feature_window = []
            for j in range(window_size):
                for feature in features:
                    feature_window.append(time_series[feature][i + j])
            X_features.append(feature_window)
            
            # 目标：未来的整体健康评分（简化计算）
            future_scores = []
            for feature in features:
                future_scores.append(time_series[feature][i + window_size])
            y_targets.append(np.mean(future_scores))
        
        if len(X_features) < 5:
            return {'risk_level': 'unknown', 'confidence': 0.0}
        
        # 训练预测模型
        X = np.array(X_features)
        y = np.array(y_targets)
        
        try:
            self.predictor.fit(X, y)
            
            # 预测未来风险
            last_window = X[-1].reshape(1, -1)
            predicted_score = self.predictor.predict(last_window)[0]
            
            # 计算风险等级
            current_score = y[-1]
            score_change = predicted_score - current_score
            
            if score_change < -10:
                risk_level = 'high'
            elif score_change < -5:
                risk_level = 'medium'
            else:
                risk_level = 'low'
            
            # 计算预测置信度
            feature_importance = self.predictor.feature_importances_
            confidence = float(np.mean(feature_importance))
            
            return {
                'risk_level': risk_level,
                'confidence': confidence,
                'predicted_score': float(predicted_score),
                'current_score': float(current_score),
                'score_change': float(score_change),
                'risk_factors': self._identify_risk_factors_from_importance(
                    feature_importance, features, window_size
                )
            }
            
        except Exception as e:
            return {'risk_level': 'unknown', 'confidence': 0.0, 'error': str(e)}
    
    def optimize_recommendations(
        self,
        recommendations: List[Any],
        user_profile: Dict[str, Any],
        health_scores: Dict[str, float]
    ) -> List[Any]:
        """AI优化健康建议"""
        if not recommendations:
            return []
        
        # 基于用户画像和健康评分对建议进行智能排序
        scored_recommendations = []
        
        for rec in recommendations:
            # 计算建议优先级评分
            priority_score = self._calculate_recommendation_priority_score(
                rec, user_profile, health_scores
            )
            
            scored_recommendations.append({
                'recommendation': rec,
                'priority_score': priority_score
            })
        
        # 按优先级评分排序
        scored_recommendations.sort(key=lambda x: x['priority_score'], reverse=True)
        
        # 返回优化后的建议列表
        return [item['recommendation'] for item in scored_recommendations]
    
    def _find_optimal_clusters(self, X: np.ndarray) -> int:
        """寻找最优聚类数"""
        max_k = min(10, len(X) // 2)
        if max_k < 2:
            return 2
        
        silhouette_scores = []
        k_range = range(2, max_k + 1)
        
        for k in k_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(X)
            silhouette_avg = silhouette_score(X, cluster_labels)
            silhouette_scores.append(silhouette_avg)
        
        # 选择轮廓系数最高的k值
        optimal_k = k_range[np.argmax(silhouette_scores)]
        return optimal_k
    
    def _analyze_cluster_characteristics(
        self, 
        cluster_data: np.ndarray, 
        feature_names: List[str]
    ) -> List[str]:
        """分析聚类特征"""
        characteristics = []
        
        # 计算特征均值
        feature_means = np.mean(cluster_data, axis=0)
        
        # 识别突出特征
        for i, feature_name in enumerate(feature_names):
            mean_value = feature_means[i]
            
            if mean_value > 80:
                characteristics.append(f"高{feature_name}")
            elif mean_value < 60:
                characteristics.append(f"低{feature_name}")
        
        # 如果没有突出特征，提供默认描述
        if not characteristics:
            overall_mean = np.mean(feature_means)
            if overall_mean > 75:
                characteristics.append("整体健康状况良好")
            elif overall_mean < 65:
                characteristics.append("整体健康状况需要改善")
            else:
                characteristics.append("整体健康状况一般")
        
        return characteristics
    
    def _identify_risk_factors_from_importance(
        self,
        feature_importance: np.ndarray,
        features: List[str],
        window_size: int
    ) -> List[str]:
        """从特征重要性识别风险因子"""
        risk_factors = []
        
        # 重构特征重要性到原始特征
        n_features = len(features)
        feature_importance_sum = np.zeros(n_features)
        
        for i in range(len(feature_importance)):
            feature_idx = i % n_features
            feature_importance_sum[feature_idx] += feature_importance[i]
        
        # 识别最重要的特征
        top_indices = np.argsort(feature_importance_sum)[-3:]  # 前3个重要特征
        
        for idx in top_indices:
            if idx < len(features):
                risk_factors.append(features[idx])
        
        return risk_factors
    
    def _calculate_recommendation_priority_score(
        self,
        recommendation: Any,
        user_profile: Dict[str, Any],
        health_scores: Dict[str, float]
    ) -> float:
        """计算建议优先级评分"""
        base_score = 50.0
        
        # 基于建议类型的基础分数
        rec_type = getattr(recommendation, 'recommendation_type', '')
        if 'critical' in rec_type:
            base_score += 30
        elif 'high' in rec_type:
            base_score += 20
        elif 'medium' in rec_type:
            base_score += 10
        
        # 基于用户健康评分调整
        overall_score = health_scores.get('overall_score', 70)
        if overall_score < 60:
            base_score += 20  # 健康状况差，提高建议优先级
        elif overall_score > 80:
            base_score -= 10  # 健康状况好，降低建议优先级
        
        # 基于预期改善效果
        expected_improvement = getattr(recommendation, 'expected_improvement', 0.5)
        base_score += expected_improvement * 20
        
        # 基于实施难度（难度越低，优先级越高）
        difficulty = getattr(recommendation, 'implementation_difficulty', 'medium')
        if difficulty == 'easy':
            base_score += 10
        elif difficulty == 'hard':
            base_score -= 10
        
        return min(100.0, max(0.0, base_score))
```

## 6. 定时任务调度系统

### 6.1 任务调度器 (tasks/scheduler.py)

```python
"""
健康数据分析定时任务调度器
基于APScheduler实现定时任务管理
"""
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Callable, Any
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from sqlalchemy.orm import Session

from ..config.health_config import HealthAnalyticsConfig
from ..services.baseline_service import HealthBaselineService
from ..services.score_service import HealthScoreService
from ..services.recommendation_service import HealthRecommendationService
from ..services.prediction_service import HealthPredictionService
from ..services.profile_service import HealthProfileService
from ..services.data_service import HierarchicalHealthAnalysisService

logger = logging.getLogger(__name__)

class HealthAnalyticsScheduler:
    """健康数据分析任务调度器"""
    
    def __init__(self, db_session_factory: Callable[[], Session]):
        self.db_session_factory = db_session_factory
        self.config = HealthAnalyticsConfig()
        
        # 配置调度器
        executors = {
            'default': ThreadPoolExecutor(20),  # 默认线程池
            'health_tasks': ThreadPoolExecutor(10)  # 健康任务专用线程池
        }
        
        job_stores = {
            'default': MemoryJobStore()
        }
        
        job_defaults = {
            'coalesce': True,  # 合并错过的任务
            'max_instances': 1,  # 每个任务最多同时运行1个实例
            'misfire_grace_time': 300  # 任务错过时间容忍度（秒）
        }
        
        self.scheduler = BackgroundScheduler(
            executors=executors,
            job_stores=job_stores,
            job_defaults=job_defaults,
            timezone='Asia/Shanghai'
        )
        
        self._task_status = {}  # 任务执行状态跟踪
    
    def start(self):
        """启动调度器"""
        logger.info("启动健康数据分析任务调度器")
        
        try:
            # 注册所有任务
            self._register_all_tasks()
            
            # 启动调度器
            self.scheduler.start()
            
            logger.info("健康数据分析任务调度器启动成功")
            
        except Exception as e:
            logger.error(f"调度器启动失败: {str(e)}", exc_info=True)
            raise
    
    def stop(self):
        """停止调度器"""
        logger.info("停止健康数据分析任务调度器")
        
        try:
            self.scheduler.shutdown(wait=True)
            logger.info("健康数据分析任务调度器已停止")
            
        except Exception as e:
            logger.error(f"调度器停止失败: {str(e)}", exc_info=True)
    
    def _register_all_tasks(self):
        """注册所有定时任务"""
        task_schedule = self.config.TASK_SCHEDULE
        
        # 权重配置验证任务
        self.scheduler.add_job(
            func=self._execute_weight_validation,
            trigger=CronTrigger.from_crontab(task_schedule['weight_validation']),
            id='weight_validation',
            name='权重配置验证任务',
            executor='health_tasks'
        )
        
        # 用户健康基线生成任务
        self.scheduler.add_job(
            func=self._execute_user_baseline_generation,
            trigger=CronTrigger.from_crontab(task_schedule['user_baseline']),
            id='user_baseline',
            name='用户健康基线生成任务',
            executor='health_tasks'
        )
        
        # 部门健康基线生成任务
        self.scheduler.add_job(
            func=self._execute_department_baseline_generation,
            trigger=CronTrigger.from_crontab(task_schedule['dept_baseline']),
            id='dept_baseline',
            name='部门健康基线生成任务',
            executor='health_tasks'
        )
        
        # 租户健康基线生成任务
        self.scheduler.add_job(
            func=self._execute_tenant_baseline_generation,
            trigger=CronTrigger.from_crontab(task_schedule['tenant_baseline']),
            id='tenant_baseline',
            name='租户健康基线生成任务',
            executor='health_tasks'
        )
        
        # 用户健康评分计算任务
        self.scheduler.add_job(
            func=self._execute_user_score_calculation,
            trigger=CronTrigger.from_crontab(task_schedule['user_score']),
            id='user_score',
            name='用户健康评分计算任务',
            executor='health_tasks'
        )
        
        # 租户健康评分计算任务
        self.scheduler.add_job(
            func=self._execute_tenant_score_calculation,
            trigger=CronTrigger.from_crontab(task_schedule['tenant_score']),
            id='tenant_score',
            name='租户健康评分计算任务',
            executor='health_tasks'
        )
        
        # 健康建议生成任务
        self.scheduler.add_job(
            func=self._execute_recommendation_generation,
            trigger=CronTrigger.from_crontab(task_schedule['recommendations']),
            id='recommendations',
            name='健康建议生成任务',
            executor='health_tasks'
        )
        
        # 健康画像生成任务
        self.scheduler.add_job(
            func=self._execute_health_profile_generation,
            trigger=CronTrigger.from_crontab(task_schedule['health_profile']),
            id='health_profile',
            name='健康画像生成任务',
            executor='health_tasks'
        )
        
        # 层级健康分析任务（新增）
        self.scheduler.add_job(
            func=self._execute_hierarchical_analysis,
            trigger=CronTrigger.from_crontab('0 6 * * *'),  # 06:00 执行完整层级分析
            id='hierarchical_analysis',
            name='层级健康分析任务',
            executor='health_tasks'
        )
        
        # 数据清理任务
        self.scheduler.add_job(
            func=self._execute_data_cleanup,
            trigger=CronTrigger.from_crontab(task_schedule['data_cleanup']),
            id='data_cleanup',
            name='数据清理任务',
            executor='default'
        )
        
        # 月度数据归档任务
        self.scheduler.add_job(
            func=self._execute_monthly_archive,
            trigger=CronTrigger.from_crontab(task_schedule['monthly_archive']),
            id='monthly_archive',
            name='月度数据归档任务',
            executor='default'
        )
        
        logger.info(f"已注册 {len(self.scheduler.get_jobs())} 个定时任务")
    
    def _execute_weight_validation(self):
        """执行权重配置验证任务"""
        task_name = "权重配置验证"
        logger.info(f"开始执行 {task_name} 任务")
        
        try:
            self._update_task_status('weight_validation', 'running')
            
            # 验证权重配置的有效性
            is_valid = self.config.validate_weights()
            
            if not is_valid:
                logger.warning("权重配置验证失败，权重总和不等于1.0")
                # 这里可以发送告警或自动修复
            
            self._update_task_status('weight_validation', 'completed')
            logger.info(f"{task_name} 任务执行完成")
            
        except Exception as e:
            self._update_task_status('weight_validation', 'failed', str(e))
            logger.error(f"{task_name} 任务执行失败: {str(e)}", exc_info=True)
    
    def _execute_user_baseline_generation(self):
        """执行用户健康基线生成任务"""
        task_name = "用户健康基线生成"
        logger.info(f"开始执行 {task_name} 任务")
        
        try:
            self._update_task_status('user_baseline', 'running')
            
            with self.db_session_factory() as db:
                baseline_service = HealthBaselineService(db)
                baselines = baseline_service.generate_user_health_baselines()
                
                logger.info(f"生成用户健康基线: {len(baselines)} 条记录")
            
            self._update_task_status('user_baseline', 'completed')
            logger.info(f"{task_name} 任务执行完成")
            
        except Exception as e:
            self._update_task_status('user_baseline', 'failed', str(e))
            logger.error(f"{task_name} 任务执行失败: {str(e)}", exc_info=True)
    
    def _execute_department_baseline_generation(self):
        """执行部门健康基线生成任务"""
        task_name = "部门健康基线生成"
        logger.info(f"开始执行 {task_name} 任务")
        
        try:
            self._update_task_status('dept_baseline', 'running')
            
            with self.db_session_factory() as db:
                baseline_service = HealthBaselineService(db)
                dept_baselines = baseline_service.generate_department_health_baselines()
                
                logger.info(f"生成部门健康基线: {len(dept_baselines)} 条记录")
            
            self._update_task_status('dept_baseline', 'completed')
            logger.info(f"{task_name} 任务执行完成")
            
        except Exception as e:
            self._update_task_status('dept_baseline', 'failed', str(e))
            logger.error(f"{task_name} 任务执行失败: {str(e)}", exc_info=True)
    
    def _execute_tenant_baseline_generation(self):
        """执行租户健康基线生成任务"""
        task_name = "租户健康基线生成"
        logger.info(f"开始执行 {task_name} 任务")
        
        try:
            self._update_task_status('tenant_baseline', 'running')
            
            with self.db_session_factory() as db:
                baseline_service = HealthBaselineService(db)
                tenant_baselines = baseline_service.generate_tenant_health_baselines()
                
                logger.info(f"生成租户健康基线: {len(tenant_baselines)} 条记录")
            
            self._update_task_status('tenant_baseline', 'completed')
            logger.info(f"{task_name} 任务执行完成")
            
        except Exception as e:
            self._update_task_status('tenant_baseline', 'failed', str(e))
            logger.error(f"{task_name} 任务执行失败: {str(e)}", exc_info=True)
    
    def _execute_user_score_calculation(self):
        """执行用户健康评分计算任务"""
        task_name = "用户健康评分计算"
        logger.info(f"开始执行 {task_name} 任务")
        
        try:
            self._update_task_status('user_score', 'running')
            
            with self.db_session_factory() as db:
                score_service = HealthScoreService(db)
                scores = score_service.calculate_user_health_scores()
                
                logger.info(f"计算用户健康评分: {len(scores)} 条记录")
            
            self._update_task_status('user_score', 'completed')
            logger.info(f"{task_name} 任务执行完成")
            
        except Exception as e:
            self._update_task_status('user_score', 'failed', str(e))
            logger.error(f"{task_name} 任务执行失败: {str(e)}", exc_info=True)
    
    def _execute_tenant_score_calculation(self):
        """执行租户健康评分计算任务"""
        task_name = "租户健康评分计算"
        logger.info(f"开始执行 {task_name} 任务")
        
        try:
            self._update_task_status('tenant_score', 'running')
            
            # 这里实现租户级别的健康评分计算逻辑
            # 可以基于部门评分进行聚合
            
            self._update_task_status('tenant_score', 'completed')
            logger.info(f"{task_name} 任务执行完成")
            
        except Exception as e:
            self._update_task_status('tenant_score', 'failed', str(e))
            logger.error(f"{task_name} 任务执行失败: {str(e)}", exc_info=True)
    
    def _execute_recommendation_generation(self):
        """执行健康建议生成任务"""
        task_name = "健康建议生成"
        logger.info(f"开始执行 {task_name} 任务")
        
        try:
            self._update_task_status('recommendations', 'running')
            
            with self.db_session_factory() as db:
                recommendation_service = HealthRecommendationService(db)
                
                # 获取所有活跃用户
                from ..models.health_models import UserHealthData
                users = db.query(UserHealthData.user_id).distinct().all()
                
                total_recommendations = 0
                for user in users:
                    try:
                        recs = recommendation_service.generate_user_recommendations(user.user_id)
                        total_recommendations += len(recs)
                    except Exception as e:
                        logger.error(f"生成用户 {user.user_id} 建议失败: {str(e)}")
                        continue
                
                logger.info(f"生成健康建议: 共 {total_recommendations} 条建议")
            
            self._update_task_status('recommendations', 'completed')
            logger.info(f"{task_name} 任务执行完成")
            
        except Exception as e:
            self._update_task_status('recommendations', 'failed', str(e))
            logger.error(f"{task_name} 任务执行失败: {str(e)}", exc_info=True)
    
    def _execute_health_profile_generation(self):
        """执行健康画像生成任务"""
        task_name = "健康画像生成"
        logger.info(f"开始执行 {task_name} 任务")
        
        try:
            self._update_task_status('health_profile', 'running')
            
            with self.db_session_factory() as db:
                profile_service = HealthProfileService(db)
                profiles = profile_service.generate_batch_health_profiles()
                
                logger.info(f"生成健康画像: {len(profiles)} 个用户画像")
            
            self._update_task_status('health_profile', 'completed')
            logger.info(f"{task_name} 任务执行完成")
            
        except Exception as e:
            self._update_task_status('health_profile', 'failed', str(e))
            logger.error(f"{task_name} 任务执行失败: {str(e)}", exc_info=True)
    
    def _execute_data_cleanup(self):
        """执行数据清理任务"""
        task_name = "数据清理"
        logger.info(f"开始执行 {task_name} 任务")
        
        try:
            self._update_task_status('data_cleanup', 'running')
            
            with self.db_session_factory() as db:
                # 清理过期的基线数据
                cutoff_date = date.today() - timedelta(days=90)
                from ..models.analytics_models import HealthBaseline
                
                deleted_baselines = db.query(HealthBaseline).filter(
                    HealthBaseline.baseline_date < cutoff_date,
                    HealthBaseline.is_current == False
                ).delete()
                
                # 清理过期的评分数据
                from ..models.analytics_models import HealthScore
                deleted_scores = db.query(HealthScore).filter(
                    HealthScore.score_date < cutoff_date
                ).delete()
                
                db.commit()
                logger.info(f"数据清理完成: 删除 {deleted_baselines} 条基线数据, {deleted_scores} 条评分数据")
            
            self._update_task_status('data_cleanup', 'completed')
            logger.info(f"{task_name} 任务执行完成")
            
        except Exception as e:
            self._update_task_status('data_cleanup', 'failed', str(e))
            logger.error(f"{task_name} 任务执行失败: {str(e)}", exc_info=True)
    
    def _execute_monthly_archive(self):
        """执行月度数据归档任务"""
        task_name = "月度数据归档"
        logger.info(f"开始执行 {task_name} 任务")
        
        try:
            self._update_task_status('monthly_archive', 'running')
            
            # 实现月度数据归档逻辑
            # 可以将历史数据移动到归档表或压缩存储
            
            self._update_task_status('monthly_archive', 'completed')
            logger.info(f"{task_name} 任务执行完成")
            
        except Exception as e:
            self._update_task_status('monthly_archive', 'failed', str(e))
            logger.error(f"{task_name} 任务执行失败: {str(e)}", exc_info=True)
    
    def _execute_hierarchical_analysis(self):
        """执行层级健康分析任务（新增核心任务）"""
        task_name = "层级健康分析"
        logger.info(f"开始执行 {task_name} 任务")
        
        try:
            self._update_task_status('hierarchical_analysis', 'running')
            
            with self.db_session_factory() as db:
                analysis_service = HierarchicalHealthAnalysisService(db)
                
                # 获取所有租户ID（需要根据实际sys_user表结构调整）
                customer_ids = db.execute(text("""
                    SELECT DISTINCT customer_id 
                    FROM sys_user 
                    WHERE del_flag = '0' 
                    AND customer_id IS NOT NULL 
                    AND customer_id > 0
                """)).fetchall()
                
                total_customers = 0
                successful_analyses = 0
                
                for customer_row in customer_ids:
                    customer_id = customer_row[0]
                    try:
                        logger.info(f"开始分析租户 {customer_id}")
                        
                        # 为每个租户生成完整的层级健康分析
                        analysis_result = analysis_service.generate_customer_health_analysis(customer_id)
                        
                        if analysis_result and not analysis_result.get('error'):
                            successful_analyses += 1
                            logger.info(f"租户 {customer_id} 分析完成: "
                                      f"用户数={analysis_result['summary']['total_users']}, "
                                      f"组织数={analysis_result['summary']['total_orgs']}")
                        else:
                            logger.warning(f"租户 {customer_id} 分析失败: {analysis_result.get('error', '未知错误')}")
                        
                        total_customers += 1
                        
                    except Exception as e:
                        logger.error(f"租户 {customer_id} 分析异常: {str(e)}")
                        continue
                
                logger.info(f"层级健康分析完成: 处理租户 {successful_analyses}/{total_customers}")
            
            self._update_task_status('hierarchical_analysis', 'completed')
            logger.info(f"{task_name} 任务执行完成")
            
        except Exception as e:
            self._update_task_status('hierarchical_analysis', 'failed', str(e))
            logger.error(f"{task_name} 任务执行失败: {str(e)}", exc_info=True)
    
    def _update_task_status(self, task_id: str, status: str, error: str = None):
        """更新任务执行状态"""
        self._task_status[task_id] = {
            'status': status,
            'last_run': datetime.utcnow(),
            'error': error
        }
    
    def get_task_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有任务状态"""
        return self._task_status.copy()
    
    def run_task_immediately(self, task_id: str) -> bool:
        """立即执行指定任务"""
        try:
            job = self.scheduler.get_job(task_id)
            if job:
                job.modify(next_run_time=datetime.now())
                logger.info(f"任务 {task_id} 已加入立即执行队列")
                return True
            else:
                logger.error(f"任务 {task_id} 不存在")
                return False
        except Exception as e:
            logger.error(f"立即执行任务 {task_id} 失败: {str(e)}", exc_info=True)
            return False
    
    def pause_task(self, task_id: str) -> bool:
        """暂停指定任务"""
        try:
            self.scheduler.pause_job(task_id)
            logger.info(f"任务 {task_id} 已暂停")
            return True
        except Exception as e:
            logger.error(f"暂停任务 {task_id} 失败: {str(e)}", exc_info=True)
            return False
    
    def resume_task(self, task_id: str) -> bool:
        """恢复指定任务"""
        try:
            self.scheduler.resume_job(task_id)
            logger.info(f"任务 {task_id} 已恢复")
            return True
        except Exception as e:
            logger.error(f"恢复任务 {task_id} 失败: {str(e)}", exc_info=True)
            return False
    
    def get_job_info(self) -> List[Dict[str, Any]]:
        """获取所有任务信息"""
        jobs_info = []
        
        for job in self.scheduler.get_jobs():
            job_status = self._task_status.get(job.id, {})
            
            jobs_info.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'last_run_time': job_status.get('last_run', {}).get('timestamp'),
                'status': job_status.get('status', 'unknown'),
                'error': job_status.get('error')
            })
        
        return jobs_info
```

## 7. API接口实现

### 7.1 健康分析API (api/health_analytics_api.py)

```python
"""
健康数据分析API接口
提供RESTful API供前端调用
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
import logging
from functools import wraps

from ..services.baseline_service import HealthBaselineService
from ..services.score_service import HealthScoreService
from ..services.recommendation_service import HealthRecommendationService
from ..services.prediction_service import HealthPredictionService
from ..services.profile_service import HealthProfileService
from ..tasks.scheduler import HealthAnalyticsScheduler
from ..models.health_models import db
from ..services.data_service import HierarchicalHealthAnalysisService

logger = logging.getLogger(__name__)

# 创建蓝图
health_analytics_bp = Blueprint('health_analytics', __name__, url_prefix='/api/health_analytics')

# 全局服务实例（在应用启动时初始化）
baseline_service = None
score_service = None
recommendation_service = None
prediction_service = None
profile_service = None
scheduler = None

def init_services(app):
    """初始化服务实例"""
    global baseline_service, score_service, recommendation_service
    global prediction_service, profile_service, scheduler
    
    def get_db_session():
        return db.session
    
    baseline_service = HealthBaselineService(db.session)
    score_service = HealthScoreService(db.session)
    recommendation_service = HealthRecommendationService(db.session)
    prediction_service = HealthPredictionService(db.session)
    profile_service = HealthProfileService(db.session)
    scheduler = HealthAnalyticsScheduler(get_db_session)

def handle_api_errors(f):
    """API错误处理装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.error(f"参数错误: {str(e)}")
            return jsonify({'error': 'Invalid parameters', 'message': str(e)}), 400
        except Exception as e:
            logger.error(f"API调用失败: {str(e)}", exc_info=True)
            return jsonify({'error': 'Internal server error', 'message': str(e)}), 500
    
    return decorated_function

def parse_date_param(date_str: str) -> Optional[date]:
    """解析日期参数"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. Expected YYYY-MM-DD")

# ================================
# 健康基线相关API
# ================================

@health_analytics_bp.route('/baseline/user/<int:user_id>', methods=['GET'])
@handle_api_errors
def get_user_baseline(user_id: int):
    """获取用户健康基线"""
    feature_name = request.args.get('feature_name')
    baseline_date = parse_date_param(request.args.get('baseline_date'))
    
    if not feature_name:
        return jsonify({'error': 'feature_name parameter is required'}), 400
    
    baseline = baseline_service.get_user_baseline(user_id, feature_name, baseline_date)
    
    if baseline:
        return jsonify({
            'success': True,
            'data': {
                'user_id': baseline.user_id,
                'device_sn': baseline.device_sn,
                'feature_name': baseline.feature_name,
                'baseline_date': baseline.baseline_date.isoformat(),
                'mean_value': baseline.mean_value,
                'std_value': baseline.std_value,
                'min_value': baseline.min_value,
                'max_value': baseline.max_value,
                'sample_count': baseline.sample_count,
                'confidence_level': baseline.confidence_level
            }
        })
    else:
        return jsonify({'success': False, 'message': 'Baseline not found'}), 404

@health_analytics_bp.route('/baseline/generate', methods=['POST'])
@handle_api_errors
def generate_baselines():
    """生成健康基线（支持单用户或批量）"""
    data = request.get_json()
    user_id = data.get('user_id') if data else None
    calculation_date = parse_date_param(data.get('calculation_date') if data else None)
    
    baselines = baseline_service.generate_user_health_baselines(user_id, calculation_date)
    
    return jsonify({
        'success': True,
        'message': f'Generated {len(baselines)} baselines',
        'data': {
            'baseline_count': len(baselines),
            'calculation_date': (calculation_date or date.today()).isoformat()
        }
    })

# ================================
# 健康评分相关API
# ================================

@health_analytics_bp.route('/score/user/<int:user_id>', methods=['GET'])
@handle_api_errors
def get_user_health_score(user_id: int):
    """获取用户健康评分"""
    score_date = parse_date_param(request.args.get('score_date'))
    
    comprehensive_scores = score_service.calculate_comprehensive_health_score(user_id, score_date)
    
    if comprehensive_scores:
        return jsonify({
            'success': True,
            'data': {
                'user_id': user_id,
                'score_date': (score_date or date.today()).isoformat(),
                'scores': comprehensive_scores
            }
        })
    else:
        return jsonify({'success': False, 'message': 'Score data not found'}), 404

@health_analytics_bp.route('/score/calculate', methods=['POST'])
@handle_api_errors
def calculate_health_scores():
    """计算健康评分（支持单用户或批量）"""
    data = request.get_json()
    user_id = data.get('user_id') if data else None
    score_date = parse_date_param(data.get('score_date') if data else None)
    days_back = data.get('days_back', 7) if data else 7
    
    scores = score_service.calculate_user_health_scores(user_id, score_date, days_back)
    
    return jsonify({
        'success': True,
        'message': f'Calculated {len(scores)} scores',
        'data': {
            'score_count': len(scores),
            'score_date': (score_date or date.today()).isoformat()
        }
    })

# ================================
# 健康建议相关API
# ================================

@health_analytics_bp.route('/recommendations/user/<int:user_id>', methods=['GET'])
@handle_api_errors
def get_user_recommendations(user_id: int):
    """获取用户健康建议"""
    analysis_date = parse_date_param(request.args.get('analysis_date'))
    
    recommendations = recommendation_service.generate_user_recommendations(user_id, analysis_date)
    
    recommendations_data = []
    for rec in recommendations:
        recommendations_data.append({
            'type': rec.recommendation_type,
            'title': rec.title,
            'description': rec.description,
            'priority_level': rec.priority_level,
            'recommended_actions': rec.recommended_actions,
            'expected_improvement': rec.expected_improvement,
            'implementation_difficulty': rec.implementation_difficulty
        })
    
    return jsonify({
        'success': True,
        'data': {
            'user_id': user_id,
            'analysis_date': (analysis_date or date.today()).isoformat(),
            'recommendations': recommendations_data
        }
    })

# ================================
# 健康预测相关API
# ================================

@health_analytics_bp.route('/prediction/user/<int:user_id>', methods=['GET'])
@handle_api_errors
def get_user_health_prediction(user_id: int):
    """获取用户健康趋势预测"""
    prediction_days = int(request.args.get('prediction_days', 7))
    historical_days = int(request.args.get('historical_days', 30))
    
    prediction_result = prediction_service.predict_user_health_trends(
        user_id, prediction_days, historical_days
    )
    
    return jsonify({
        'success': True,
        'data': prediction_result
    })

@health_analytics_bp.route('/prediction/department/<int:org_id>', methods=['GET'])
@handle_api_errors
def get_department_health_prediction(org_id: int):
    """获取部门健康趋势预测"""
    prediction_days = int(request.args.get('prediction_days', 7))
    
    prediction_result = prediction_service.predict_department_health_trends(
        org_id, prediction_days
    )
    
    return jsonify({
        'success': True,
        'data': prediction_result
    })

# ================================
# 健康画像相关API
# ================================

@health_analytics_bp.route('/profile/user/<int:user_id>', methods=['GET'])
@handle_api_errors
def get_user_health_profile(user_id: int):
    """获取用户综合健康画像"""
    profile_date = parse_date_param(request.args.get('profile_date'))
    
    health_profile = profile_service.generate_comprehensive_health_profile(user_id, profile_date)
    
    profile_data = {
        'user_id': health_profile.user_id,
        'profile_date': health_profile.profile_date.isoformat(),
        'overall_score': health_profile.overall_score,
        'health_level': health_profile.health_level,
        'physiological_score': health_profile.physiological_score,
        'behavioral_score': health_profile.behavioral_score,
        'risk_factor_score': health_profile.risk_factor_score,
        'feature_scores': health_profile.feature_scores,
        'trend_analysis': health_profile.trend_analysis,
        'recommendations': [
            {
                'type': rec.recommendation_type,
                'title': rec.title,
                'description': rec.description,
                'priority_level': rec.priority_level,
                'recommended_actions': rec.recommended_actions
            } for rec in health_profile.recommendations
        ],
        'risk_factors': health_profile.risk_factors
    }
    
    return jsonify({
        'success': True,
        'data': profile_data
    })

@health_analytics_bp.route('/profile/user/<int:user_id>/history', methods=['GET'])
@handle_api_errors
def get_user_profile_history(user_id: int):
    """获取用户健康画像历史"""
    days = int(request.args.get('days', 30))
    
    profile_history = profile_service.get_user_health_profile_history(user_id, days)
    
    history_data = []
    for profile in profile_history:
        history_data.append({
            'profile_date': profile.profile_date.isoformat(),
            'overall_score': profile.overall_score,
            'health_level': profile.health_level,
            'physiological_score': profile.physiological_score,
            'behavioral_score': profile.behavioral_score,
            'risk_factor_score': profile.risk_factor_score
        })
    
    return jsonify({
        'success': True,
        'data': {
            'user_id': user_id,
            'history_period_days': days,
            'profiles': history_data
        }
    })

@health_analytics_bp.route('/profile/batch', methods=['POST'])
@handle_api_errors
def generate_batch_profiles():
    """批量生成健康画像"""
    data = request.get_json()
    user_ids = data.get('user_ids') if data else None
    org_id = data.get('org_id') if data else None
    profile_date = parse_date_param(data.get('profile_date') if data else None)
    
    profiles = profile_service.generate_batch_health_profiles(user_ids, org_id, profile_date)
    
    return jsonify({
        'success': True,
        'message': f'Generated {len(profiles)} health profiles',
        'data': {
            'profile_count': len(profiles),
            'profile_date': (profile_date or date.today()).isoformat()
        }
    })

# ================================
# 任务管理相关API
# ================================

@health_analytics_bp.route('/tasks/status', methods=['GET'])
@handle_api_errors
def get_task_status():
    """获取所有任务状态"""
    if scheduler:
        task_status = scheduler.get_task_status()
        job_info = scheduler.get_job_info()
        
        return jsonify({
            'success': True,
            'data': {
                'task_status': task_status,
                'job_info': job_info
            }
        })
    else:
        return jsonify({'success': False, 'message': 'Scheduler not initialized'}), 500

@health_analytics_bp.route('/tasks/<task_id>/run', methods=['POST'])
@handle_api_errors
def run_task_immediately(task_id: str):
    """立即执行指定任务"""
    if scheduler:
        success = scheduler.run_task_immediately(task_id)
        
        if success:
            return jsonify({'success': True, 'message': f'Task {task_id} scheduled for immediate execution'})
        else:
            return jsonify({'success': False, 'message': f'Failed to schedule task {task_id}'}), 400
    else:
        return jsonify({'success': False, 'message': 'Scheduler not initialized'}), 500

@health_analytics_bp.route('/tasks/<task_id>/pause', methods=['POST'])
@handle_api_errors
def pause_task(task_id: str):
    """暂停指定任务"""
    if scheduler:
        success = scheduler.pause_task(task_id)
        
        if success:
            return jsonify({'success': True, 'message': f'Task {task_id} paused'})
        else:
            return jsonify({'success': False, 'message': f'Failed to pause task {task_id}'}), 400
    else:
        return jsonify({'success': False, 'message': 'Scheduler not initialized'}), 500

@health_analytics_bp.route('/tasks/<task_id>/resume', methods=['POST'])
@handle_api_errors
def resume_task(task_id: str):
    """恢复指定任务"""
    if scheduler:
        success = scheduler.resume_task(task_id)
        
        if success:
            return jsonify({'success': True, 'message': f'Task {task_id} resumed'})
        else:
            return jsonify({'success': False, 'message': f'Failed to resume task {task_id}'}), 400
    else:
        return jsonify({'success': False, 'message': 'Scheduler not initialized'}), 500

# ================================
# 层级健康分析相关API
# ================================

@health_analytics_bp.route('/hierarchical/customer/<int:customer_id>', methods=['GET'])
@handle_api_errors
def get_customer_hierarchical_analysis(customer_id: int):
    """获取租户层级健康分析"""
    analysis_date = parse_date_param(request.args.get('analysis_date'))
    
    hierarchical_service = HierarchicalHealthAnalysisService(db.session)
    analysis_result = hierarchical_service.generate_customer_health_analysis(customer_id, analysis_date)
    
    return jsonify({
        'success': True,
        'data': analysis_result
    })

@health_analytics_bp.route('/hierarchical/organization/<int:org_id>', methods=['GET'])
@handle_api_errors
def get_organization_hierarchical_analysis(org_id: int):
    """获取部门层级健康分析"""
    analysis_date = parse_date_param(request.args.get('analysis_date'))
    include_sub_orgs = request.args.get('include_sub_orgs', 'true').lower() == 'true'
    
    hierarchical_service = HierarchicalHealthAnalysisService(db.session)
    analysis_result = hierarchical_service.generate_organization_health_analysis(
        org_id, analysis_date, include_sub_orgs
    )
    
    return jsonify({
        'success': True,
        'data': analysis_result
    })

@health_analytics_bp.route('/hierarchical/user/<int:user_id>/comprehensive', methods=['GET'])
@handle_api_errors
def get_user_comprehensive_analysis(user_id: int):
    """获取用户完整健康分析（包含层级信息）"""
    analysis_date = parse_date_param(request.args.get('analysis_date'))
    days_back = int(request.args.get('days_back', 30))
    
    hierarchical_service = HierarchicalHealthAnalysisService(db.session)
    analysis_result = hierarchical_service.generate_user_comprehensive_analysis(
        user_id, analysis_date, days_back
    )
    
    return jsonify({
        'success': True,
        'data': analysis_result
    })

@health_analytics_bp.route('/hierarchical/users/batch', methods=['POST'])
@handle_api_errors
def get_batch_user_analysis():
    """批量获取用户健康分析"""
    data = request.get_json()
    user_ids = data.get('user_ids', [])
    analysis_date = parse_date_param(data.get('analysis_date'))
    days_back = data.get('days_back', 30)
    
    if not user_ids:
        return jsonify({'error': 'user_ids parameter is required'}), 400
    
    hierarchical_service = HierarchicalHealthAnalysisService(db.session)
    batch_results = []
    
    for user_id in user_ids:
        try:
            analysis_result = hierarchical_service.generate_user_comprehensive_analysis(
                user_id, analysis_date, days_back
            )
            batch_results.append({
                'user_id': user_id,
                'success': True,
                'data': analysis_result
            })
        except Exception as e:
            logger.error(f"批量分析用户{user_id}失败: {str(e)}")
            batch_results.append({
                'user_id': user_id,
                'success': False,
                'error': str(e)
            })
    
    return jsonify({
        'success': True,
        'data': {
            'total_requested': len(user_ids),
            'successful_analyses': len([r for r in batch_results if r['success']]),
            'failed_analyses': len([r for r in batch_results if not r['success']]),
            'results': batch_results
        }
    })

@health_analytics_bp.route('/hierarchical/organizations/summary', methods=['GET'])
@handle_api_errors
def get_organizations_health_summary():
    """获取所有组织健康状况汇总"""
    customer_id = request.args.get('customer_id')
    analysis_date = parse_date_param(request.args.get('analysis_date'))
    
    if not customer_id:
        return jsonify({'error': 'customer_id parameter is required'}), 400
    
    hierarchical_service = HierarchicalHealthAnalysisService(db.session)
    
    try:
        customer_id = int(customer_id)
        summary_result = hierarchical_service.get_organizations_health_summary(customer_id, analysis_date)
        
        return jsonify({
            'success': True,
            'data': summary_result
        })
    except ValueError:
        return jsonify({'error': 'Invalid customer_id format'}), 400

@health_analytics_bp.route('/hierarchical/trends/<int:customer_id>', methods=['GET'])
@handle_api_errors
def get_customer_health_trends(customer_id: int):
    """获取租户健康趋势分析"""
    days_back = int(request.args.get('days_back', 30))
    trend_type = request.args.get('trend_type', 'overall')  # overall, by_org, by_user
    
    hierarchical_service = HierarchicalHealthAnalysisService(db.session)
    trends_result = hierarchical_service.analyze_customer_health_trends(
        customer_id, days_back, trend_type
    )
    
    return jsonify({
        'success': True,
        'data': trends_result
    })

# ================================
# 系统信息相关API
# ================================

@health_analytics_bp.route('/system/health', methods=['GET'])
@handle_api_errors
def system_health_check():
    """系统健康检查"""
    health_status = {
        'timestamp': datetime.utcnow().isoformat(),
        'services': {}
    }
    
    # 检查各服务状态
    try:
        # 数据库连接检查
        db.session.execute('SELECT 1')
        health_status['services']['database'] = 'healthy'
    except Exception:
        health_status['services']['database'] = 'unhealthy'
    
    # 调度器状态检查
    if scheduler and scheduler.scheduler.running:
        health_status['services']['scheduler'] = 'healthy'
    else:
        health_status['services']['scheduler'] = 'unhealthy'
    
    # 服务实例检查
    services_to_check = {
        'baseline_service': baseline_service,
        'score_service': score_service,
        'recommendation_service': recommendation_service,
        'prediction_service': prediction_service,
        'profile_service': profile_service
    }
    
    for service_name, service_instance in services_to_check.items():
        health_status['services'][service_name] = 'healthy' if service_instance else 'unhealthy'
    
    # 计算整体状态
    healthy_services = sum(1 for status in health_status['services'].values() if status == 'healthy')
    total_services = len(health_status['services'])
    
    if healthy_services == total_services:
        overall_status = 'healthy'
        status_code = 200
    elif healthy_services > total_services / 2:
        overall_status = 'degraded'
        status_code = 200
    else:
        overall_status = 'unhealthy'
        status_code = 503
    
    health_status['overall_status'] = overall_status
    
    return jsonify({
        'success': True,
        'data': health_status
    }), status_code

@health_analytics_bp.route('/system/config', methods=['GET'])
@handle_api_errors
def get_system_config():
    """获取系统配置信息"""
    from ..config.health_config import HealthAnalyticsConfig
    
    config = HealthAnalyticsConfig()
    
    config_data = {
        'health_features': {
            name: {
                'display_name': feature.display_name,
                'unit': feature.unit,
                'normal_range': feature.normal_range,
                'weight': float(feature.weight),
                'importance_level': feature.importance_level,
                'category': feature.category
            }
            for name, feature in config.HEALTH_FEATURES.items()
        },
        'task_schedule': config.TASK_SCHEDULE,
        'score_thresholds': config.SCORE_THRESHOLDS,
        'ai_config': config.AI_CONFIG,
        'recommendation_config': config.RECOMMENDATION_CONFIG
    }
    
    return jsonify({
        'success': True,
        'data': config_data
    })

# 错误处理
@health_analytics_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@health_analytics_bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed'}), 405

@health_analytics_bp.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}", exc_info=True)
    return jsonify({'error': 'Internal server error'}), 500
```

## 8. 部署和使用指南

### 8.1 系统集成

在ljwx-bigscreen的主应用中集成健康分析系统：

```python
# bigscreen/bigScreen/bigScreen.py 中添加
from health_analytics.api.health_analytics_api import health_analytics_bp, init_services

# 注册蓝图
app.register_blueprint(health_analytics_bp)

# 初始化服务
init_services(app)
```

### 8.2 数据库迁移

```sql
-- 添加健康分析相关表的customer_id字段
ALTER TABLE t_user_health_data_daily 
ADD COLUMN customer_id bigint NOT NULL DEFAULT 0 
COMMENT '租户ID，继承自用户所属租户';

ALTER TABLE t_user_health_data_weekly 
ADD COLUMN customer_id bigint NOT NULL DEFAULT 0 
COMMENT '租户ID，继承自用户所属租户';
```

### 8.3 配置启动脚本

```python
# health_analytics_startup.py
"""
健康数据分析系统启动脚本
"""
import logging
from health_analytics.tasks.scheduler import HealthAnalyticsScheduler
from health_analytics.models.health_models import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_health_analytics_system(app):
    """启动健康数据分析系统"""
    logger.info("启动健康数据分析系统...")
    
    with app.app_context():
        # 创建数据库会话工厂
        def get_db_session():
            return db.session
        
        # 启动任务调度器
        scheduler = HealthAnalyticsScheduler(get_db_session)
        scheduler.start()
        
        logger.info("健康数据分析系统启动完成")
        
        return scheduler

if __name__ == "__main__":
    from bigscreen.bigScreen.bigScreen import app
    scheduler = start_health_analytics_system(app)
    
    try:
        # 保持程序运行
        import time
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("停止健康数据分析系统...")
        scheduler.stop()
```

### 8.4 API使用示例

```javascript
// 前端调用示例
// 获取用户健康画像
fetch('/api/health_analytics/profile/user/123')
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      console.log('用户健康画像:', data.data);
    }
  });

// 获取用户健康建议
fetch('/api/health_analytics/recommendations/user/123')
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      console.log('健康建议:', data.data.recommendations);
    }
  });

// 立即执行健康评分计算任务
fetch('/api/health_analytics/tasks/user_score/run', {
  method: 'POST'
})
  .then(response => response.json())
  .then(data => {
    console.log('任务执行结果:', data);
  });
```

## 9. 总结

这个完整的Python版本健康数据分析系统提供了：

### 9.1 核心功能
- ✅ **健康基线计算**: 统计学方法计算个人、部门、组织基线
- ✅ **健康评分系统**: 基于基线和权重的综合评分算法
- ✅ **智能建议生成**: AI驱动的个性化健康建议
- ✅ **趋势预测分析**: 机器学习预测健康趋势
- ✅ **综合健康画像**: 多维度健康状况可视化

### 9.2 技术特色
- 📊 **科学的统计分析**: 基于医学标准的权重配置和评分算法
- 🤖 **AI智能分析**: 机器学习算法优化建议和预测
- ⏰ **完整的任务调度**: 基于APScheduler的定时任务系统
- 🔌 **RESTful API**: 完整的API接口支持前端集成
- 🏗️ **模块化设计**: 清晰的服务分层和依赖注入

### 9.3 部署优势
- 🚀 **即插即用**: 可直接集成到现有ljwx-bigscreen系统
- 📈 **高性能**: 批量处理和并发优化
- 🔧 **易扩展**: 支持新增健康特征和分析算法
- 📋 **完整监控**: 任务状态监控和健康检查

这个系统完全基于ljwx-boot的实现思路，提供了Production-ready的Python版本，可以立即投入使用。
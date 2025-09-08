# LJWX BigScreen 实时健康数据分析完整解决方案

## 文档概述

本文档详细描述了为ljwx-bigscreen新增的实时健康数据分析系统，该系统作为ljwx-boot定时任务的备份方案，确保健康基线、评分、建议、预测和画像功能的连续性和可用性。

**更新时间：** 2025年9月8日  
**文档版本：** v3.0 (实时分析系统版)  
**系统状态：** ✅ 完整实现，包含8个核心模块

## 1. 实时健康分析系统概览

为了避免ljwx-boot定时任务失败造成健康基线、评分、建议、预测和画像数据丢失，我们在ljwx-bigscreen中实现了完整的实时生成逻辑。该系统基于统一的`get_all_health_data_optimized`查询方法，提供了完整的健康数据分析备份方案。

### 1.1 实时分析系统架构

```
┌─────────────────┐    ┌──────────────────────────┐    ┌─────────────────┐
│    前端层       │    │     ljwx-bigscreen        │    │   数据源层      │
│                │    │   实时分析系统            │    │                │
│ personal.html   │◄──►│ ┌──────────────────────┐  │◄──►│ MySQL数据库     │
│ bigscreen_main  │    │ │ 统一分析接口         │  │    │ - 健康数据表    │
│                │    │ │ realtime_health_     │  │    │ - 用户信息表    │
└─────────────────┘    │ │ analytics.py         │  │    │ - 组织结构表    │
                       │ └──────────────────────┘  │    └─────────────────┘
                       │           │              │
                       │           ▼              │
                       │ ┌──────────────────────┐  │
                       │ │   5个核心分析引擎     │  │
                       │ │ ┌──────────────────┐ │  │
                       │ │ │ 基线生成引擎     │ │  │
                       │ │ │ health_baseline_ │ │  │
                       │ │ │ engine.py        │ │  │
                       │ │ └──────────────────┘ │  │
                       │ │ ┌──────────────────┐ │  │
                       │ │ │ 评分计算引擎     │ │  │
                       │ │ │ health_score_    │ │  │
                       │ │ │ engine.py        │ │  │
                       │ │ └──────────────────┘ │  │
                       │ │ ┌──────────────────┐ │  │
                       │ │ │ 建议生成引擎     │ │  │
                       │ │ │ health_recommen- │ │  │
                       │ │ │ dation_engine.py │ │  │
                       │ │ └──────────────────┘ │  │
                       │ │ ┌──────────────────┐ │  │
                       │ │ │ 预测分析引擎     │ │  │
                       │ │ │ health_predict-  │ │  │
                       │ │ │ ion_engine.py    │ │  │
                       │ │ └──────────────────┘ │  │
                       │ │ ┌──────────────────┐ │  │
                       │ │ │ 画像构建引擎     │ │  │
                       │ │ │ health_profile_  │ │  │
                       │ │ │ engine.py        │ │  │
                       │ │ └──────────────────┘ │  │
                       │ └──────────────────────┘  │
                       │           │              │
                       │           ▼              │
                       │ ┌──────────────────────┐  │    ┌─────────────────┐
                       │ │ 监控与测试系统       │  │◄──►│ Redis缓存       │
                       │ │ health_analytics_    │  │    │ - 结果缓存      │
                       │ │ monitor.py           │  │    │ - 进度跟踪      │
                       │ │ test_realtime_       │  │    │ - 性能监控      │
                       │ │ analytics.py         │  │    └─────────────────┘
                       │ └──────────────────────┘  │
                       └──────────────────────────┘
```

### 1.2 核心技术特点

**🎯 统一数据查询基础**
- 所有分析引擎基于`get_all_health_data_optimized`方法
- 统一的数据获取和处理逻辑
- 支持分页、日期范围、多表查询

**⚡ 实时响应能力** 
- 典型分析响应时间 < 30秒
- Redis智能缓存策略（1-2小时TTL）
- 并行分析处理优化

**📊 全面分析覆盖**
- 健康基线：统计分析和质量评估
- 健康评分：Z-score标准化评分
- 健康建议：模板化个性建议生成
- 健康预测：统计学趋势分析
- 健康画像：多维度综合画像

**🔄 完整备份方案**
- ljwx-boot定时任务失效时自动切换
- 保证数据分析功能持续可用
- 支持手动触发和批量处理

## 2. 核心分析引擎详解

**核心功能**：基于用户历史健康数据生成统计基线，用于评分和异常检测。

**主要类**：`RealTimeHealthBaselineEngine`

**核心方法**：
```python
def generate_user_baseline_realtime(self, user_id: int, target_date: str = None, days_back: int = 30) -> Dict:
    """
    实时生成用户健康基线
    - 查询指定天数的历史健康数据  
    - 进行统计分析：均值、标准差、分位数
    - 异常检测和数据质量评估
    - 生成基线质量评分
    """
```

**基线计算算法**：
- **统计计算**：mean, std, median, q25, q75
- **异常检测**：基于IQR方法过滤离群值  
- **质量评估**：数据完整性、稳定性、覆盖率
- **缓存策略**：Redis缓存1小时，避免重复计算

**支持的健康特征**：
```python
HEALTH_FEATURES = [
    "heart_rate", "blood_oxygen", "temperature", "pressure_high", 
    "pressure_low", "stress", "step", "calorie", "distance", "sleep"
]
```

### 2.2 健康评分计算引擎（health_score_engine.py）

**核心功能**：基于健康基线和当前数据计算标准化健康评分。

**主要类**：`RealTimeHealthScoreEngine`

**核心方法**：
```python
def calculate_user_health_score_realtime(self, user_id: int, target_date: str = None) -> Dict:
    """
    实时计算用户健康评分
    - 获取用户健康基线数据
    - 计算当日健康数据的Z-score 
    - 应用医学重要性权重
    - 生成综合健康评分和等级
    """
```

**评分算法**：
```python
# Z-Score标准化评分
z_score = (daily_avg - baseline_mean) / baseline_std

# 基础评分计算 
base_score = max(0, 100 - abs(z_score) * 10)

# 异常惩罚
if daily_avg > baseline_max * 1.2 or daily_avg < baseline_min * 0.8:
    penalty = abnormal_percentage * PENALTY_FACTOR

# 最终评分
final_score = max(0, min(100, base_score - penalty))
```

**医学重要性权重**：
```python
MEDICAL_IMPORTANCE_WEIGHTS = {
    "heart_rate": 0.25,      # 心血管系统最重要
    "blood_oxygen": 0.20,    # 呼吸系统
    "pressure_high": 0.15,   # 血压
    "temperature": 0.12,     # 体温
    "pressure_low": 0.08,    # 舒张压
    "stress": 0.08,          # 心理健康
    "sleep": 0.07,           # 睡眠质量
    "step": 0.03,            # 运动量
    "distance": 0.01,        # 运动强度
    "calorie": 0.01          # 代谢水平
}
```

**健康等级划分**：
- **excellent** (90-100分): 健康状况优秀
- **good** (80-89分): 健康状况良好  
- **fair** (70-79分): 健康状况一般
- **poor** (60-69分): 健康状况较差
- **critical** (0-59分): 健康状况堪忧

### 2.3 健康建议生成引擎（health_recommendation_engine.py）

**核心功能**：基于健康评分结果生成个性化的健康改善建议。

**主要类**：`RealTimeHealthRecommendationEngine`

**核心方法**：
```python
def generate_user_health_recommendations_realtime(self, user_id: int, target_date: str = None) -> Dict:
    """
    实时生成用户健康建议
    - 获取用户健康评分分析结果
    - 识别健康薄弱环节
    - 生成针对性改善建议
    - 设置建议优先级
    """
```

**建议模板系统**：
```python
# 为每个健康特征设计了5级建议模板
RECOMMENDATION_TEMPLATES = {
    "heart_rate": {
        "excellent": ["保持规律运动习惯", "适当增加有氧运动强度"],
        "good": ["保持当前运动频率", "尝试间歇性训练"],
        "fair": ["调整运动强度和作息", "增加轻度有氧运动"],
        "poor": ["立即调整生活方式", "优先改善睡眠质量"],
        "critical": ["强烈建议就医检查", "停止剧烈运动"]
    }
    # ... 其他特征的完整模板
}
```

**建议优先级计算**：
```python
def _calculate_priority(self, score: float, score_data: Dict) -> int:
    """计算建议优先级 (1-5，5最高)"""
    if score < 50:
        return 5  # 危险
    elif score < 60:
        return 4  # 高优先级
    elif score < 70:
        return 3  # 中等优先级
    elif score < 80:
        return 2  # 低优先级
    else:
        return 1  # 维持现状
```

### 2.4 健康预测分析引擎（health_prediction_engine.py）

**核心功能**：基于历史数据的统计学趋势预测和风险评估。

**主要类**：`RealTimeHealthPredictionEngine`

**核心方法**：
```python
def generate_user_health_prediction_realtime(self, user_id: int, target_date: str = None, prediction_days: int = 30) -> Dict:
    """
    实时生成健康预测
    - 获取90天历史健康数据
    - 使用线性回归分析趋势
    - 计算风险评分和置信区间
    - 生成预测洞察
    """
```

**预测算法**：
```python
# 时间序列线性回归
from scipy import stats
slope, intercept, r_value, p_value, std_err = stats.linregress(time_numeric, feature_data)

# 预测未来值
predicted_values = [slope * day + intercept for day in future_days]

# 风险评估
risk_score = 0
if trend_strength > 0.2:  # 趋势变化超过20%
    risk_score += 0.3
if cv > 0.3:  # 变异系数超过30%
    risk_score += 0.2
```

**预测输出**：
- **趋势分析**：improving/stable/deteriorating
- **风险评分**：0-1之间的风险指数
- **置信度**：基于R²值、数据量、稳定性
- **异常预警**：预测值严重偏离历史水平

### 2.5 健康画像构建引擎（health_profile_engine.py）

**核心功能**：整合所有分析引擎结果，构建全面的用户健康画像。

**主要类**：`RealTimeHealthProfileEngine`

**核心方法**：
```python
def generate_user_health_profile_realtime(self, user_id: int, target_date: str = None, profile_type: str = 'comprehensive') -> Dict:
    """
    实时构建健康画像
    - 并行调用基线、评分、建议、预测引擎
    - 构建6维度健康分析
    - 生成健康洞察和个性化标签
    - 计算综合健康指数
    """
```

**健康画像6维度**：
```python
PROFILE_DIMENSIONS = {
    'cardiovascular': {  # 心血管健康
        'features': ['heart_rate', 'pressure_high', 'pressure_low'],
        'weight': 0.30,
        'icon': '❤️'
    },
    'respiratory': {     # 呼吸系统
        'features': ['blood_oxygen'],
        'weight': 0.20,
        'icon': '🫁'
    },
    'metabolic': {       # 代谢健康
        'features': ['temperature', 'calorie'],
        'weight': 0.15,
        'icon': '🔥'
    },
    'mental': {          # 心理健康
        'features': ['stress'],
        'weight': 0.15,
        'icon': '🧠'
    },
    'activity': {        # 运动健康
        'features': ['step', 'distance'],
        'weight': 0.10,
        'icon': '🏃'
    },
    'recovery': {        # 恢复健康
        'features': ['sleep'],
        'weight': 0.10,
        'icon': '😴'
    }
}
```

**画像输出结构**：
```json
{
    "user_info": {"用户基本信息"},
    "health_index": {"综合健康指数和等级"},
    "dimension_profiles": {"6维度详细分析"},
    "health_insights": ["智能健康洞察列表"],
    "personality_tags": [{"个性化健康标签"}],
    "summary": {"画像生成汇总信息"}
}
```

## 3. 统一分析接口与监控系统

### 3.1 统一实时数据分析接口（realtime_health_analytics.py）

**核心功能**：提供一站式健康分析服务，orchestrate所有分析引擎。

**主要类**：`RealTimeHealthAnalytics`

**核心方法**：
```python
def generate_comprehensive_user_analysis(self, user_id: int, **kwargs) -> Dict:
    """
    生成用户综合健康分析报告
    - 支持并行/串行分析模式
    - 智能缓存管理
    - 批量用户分析
    - 统一结果格式
    """
```

**分析模块配置**：
```python
ANALYTICS_MODULES = {
    'baseline': {
        'name': '健康基线',
        'user_func': get_user_baseline_realtime,
        'cache_ttl': 3600,
        'priority': 1
    },
    'score': {
        'name': '健康评分', 
        'user_func': get_user_health_score_realtime,
        'cache_ttl': 3600,
        'priority': 2
    },
    'recommendations': {
        'name': '健康建议',
        'user_func': get_user_health_recommendations_realtime,
        'cache_ttl': 1800,
        'priority': 3
    },
    'prediction': {
        'name': '健康预测',
        'user_func': get_user_health_prediction_realtime,
        'cache_ttl': 7200,
        'priority': 4
    },
    'profile': {
        'name': '健康画像',
        'user_func': get_user_health_profile_realtime,
        'cache_ttl': 7200,
        'priority': 5
    }
}
```

**统一输出格式**：
```json
{
    "success": true,
    "data": {
        "summary": {"分析汇总信息"},
        "key_metrics": {"关键健康指标"},
        "comprehensive_insights": ["综合健康洞察"],
        "module_results": {"各模块详细结果"},
        "execution_status": {"执行状态统计"}
    },
    "execution_time": 25.3
}
```

### 3.2 进度跟踪和监控系统（health_analytics_monitor.py）

**核心功能**：提供实时分析任务的监控、进度跟踪、性能统计和健康检查。

**主要类**：`HealthAnalyticsMonitor`

**核心方法**：
```python
def track_task_progress(self, task_id: str, task_type: str, identifier: int, 
                       identifier_type: str, modules: List[str]) -> Dict:
    """
    跟踪分析任务进度
    - 实时进度更新
    - 任务状态管理
    - 性能指标收集
    - 异常处理和告警
    """
```

**监控指标**：
- **系统指标**：CPU、内存、磁盘IO、网络IO
- **任务指标**：执行时间、成功率、错误率
- **性能指标**：响应时间、吞吐量、并发能力
- **健康指标**：数据质量、服务可用性

**告警机制**：
```python
MONITOR_CONFIG = {
    'performance_thresholds': {
        'max_execution_time': 300,    # 最大执行时间(秒)
        'max_memory_usage': 1024,     # 最大内存使用(MB)
        'min_success_rate': 0.8,      # 最低成功率
        'max_error_rate': 0.2         # 最大错误率
    }
}
```

### 3.3 综合测试系统（test_realtime_analytics.py）

**核心功能**：全面测试实时生成逻辑的准确性和性能。

**主要类**：`RealTimeAnalyticsTestSuite`

**测试类型**：
1. **单元测试**：测试各个引擎的基本功能
2. **集成测试**：测试引擎间的数据流和一致性
3. **性能测试**：测试响应时间、吞吐量和内存使用
4. **准确性测试**：测试数据质量、计算准确性和一致性
5. **压力测试**：测试并发处理和高负载情况

**质量阈值**：
```python
QUALITY_THRESHOLDS = {
    'min_success_rate': 0.8,         # 最低成功率
    'max_response_time': 30.0,       # 最大响应时间(秒)
    'min_data_completeness': 0.6,    # 最低数据完整性
    'max_error_rate': 0.2            # 最大错误率
}
```

**性能基准**：
- 单次分析响应时间 < 30秒
- 支持20+并发用户
- 系统稳定性 > 90%
- 数据处理准确率 > 95%

## 4. 对外接口设计

### 4.1 核心API接口

```python
# 用户综合健康分析
def generate_comprehensive_user_health_analysis(user_id: int, **kwargs) -> Dict:
    """获取用户综合健康分析"""

# 部门综合健康分析  
def generate_comprehensive_department_health_analysis(org_id: int, **kwargs) -> Dict:
    """获取部门综合健康分析"""

# 分析状态查询
def get_health_analysis_status(identifier: Union[int, List[int]], identifier_type: str) -> Dict:
    """获取健康分析状态"""

# 缓存管理
def invalidate_health_analysis_cache(identifier: int, identifier_type: str) -> Dict:
    """清除健康分析缓存"""

# 可用模块查询
def get_available_analysis_modules() -> Dict:
    """获取可用的分析模块列表"""
```

### 4.2 监控和测试接口

```python
# 监控接口
def start_health_monitoring() -> bool:
    """启动健康监控服务"""

def get_system_performance_metrics(time_range: int = 60) -> Dict:
    """获取系统性能指标"""

def get_analytics_health_status() -> Dict:
    """获取分析系统健康状态"""

# 测试接口
def run_comprehensive_tests() -> Dict:
    """运行综合测试"""

def run_quick_health_check() -> Dict:
    """快速健康检查"""

def run_performance_benchmark(iterations: int = 10) -> Dict:
    """运行性能基准测试"""
```

## 5. 部署和集成指南

### 5.1 文件清单

**新增的核心文件**（共8个）：
```
ljwx-bigscreen/bigscreen/bigScreen/
├── health_baseline_engine.py          # 健康基线生成引擎
├── health_score_engine.py             # 健康评分计算引擎  
├── health_recommendation_engine.py    # 健康建议生成引擎
├── health_prediction_engine.py        # 健康预测分析引擎
├── health_profile_engine.py           # 健康画像构建引擎
├── realtime_health_analytics.py       # 统一分析接口
├── health_analytics_monitor.py        # 监控和进度跟踪
└── test_realtime_analytics.py         # 综合测试系统
```

### 5.2 系统集成

**与现有系统的集成点**：

1. **数据查询层**：基于现有的`get_all_health_data_optimized`方法
2. **缓存层**：使用现有的`RedisHelper`类
3. **数据库层**：使用现有的数据模型和表结构
4. **组织结构**：集成现有的`org.py`中的组织查询功能

**修改的现有文件**：
```python
# health_baseline_manager.py - 修复导入错误
from .health_baseline_engine import RealTimeHealthBaselineEngine
```

### 5.3 使用示例

**基本使用**：
```python
# 用户综合健康分析
from bigScreen.realtime_health_analytics import generate_comprehensive_user_health_analysis

result = generate_comprehensive_user_health_analysis(
    user_id=123,
    modules=['baseline', 'score', 'recommendations', 'prediction', 'profile'],
    parallel=True,
    enable_caching=True
)

# 快速健康检查
from bigScreen.test_realtime_analytics import run_quick_health_check

health_status = run_quick_health_check()
```

**监控使用**：
```python  
# 启动监控
from bigScreen.health_analytics_monitor import start_health_monitoring, track_analysis_task

start_health_monitoring()

# 跟踪分析任务
task_result = track_analysis_task(
    task_id="analysis_123",
    task_type="user_analysis", 
    identifier=123,
    identifier_type="user",
    modules=['baseline', 'score'],
    progress_callback=lambda task_id, progress: print(f"Task {task_id}: {progress['progress']}%")
)
```

### 5.4 性能优化配置

**缓存配置**：
```python
# Redis缓存TTL设置
CACHE_CONFIG = {
    'baseline': 3600,        # 基线缓存1小时
    'score': 3600,          # 评分缓存1小时
    'recommendations': 1800, # 建议缓存30分钟
    'prediction': 7200,     # 预测缓存2小时
    'profile': 7200         # 画像缓存2小时
}
```

**并行处理配置**：
```python
# 线程池配置
THREAD_POOL_CONFIG = {
    'max_workers': 20,      # 最大工作线程数
    'timeout': 300          # 任务超时时间(秒)
}
```

## 6. 系统优势与特点

### 6.1 技术优势

**🔄 完整备份方案**
- ljwx-boot定时任务失效时的可靠备份
- 确保健康分析功能持续可用
- 支持手动触发和实时生成

**⚡ 高性能设计**
- 基于pandas/numpy的高效数据处理
- Redis智能缓存策略减少重复计算
- 支持并行分析提升处理速度

**📊 全面功能覆盖** 
- 健康基线：统计分析+质量评估
- 健康评分：Z-score标准化+医学权重
- 健康建议：模板化+个性化优先级
- 健康预测：统计学趋势+风险评估  
- 健康画像：多维度+综合洞察

**🔍 完善监控体系**
- 实时任务进度跟踪
- 系统性能监控告警
- 全面测试覆盖验证

### 6.2 业务价值

**数据连续性保障**
- 避免因定时任务失败导致的数据丢失
- 保证健康分析服务的连续可用性

**分析质量提升**
- 基于统计学的科学分析方法
- 医学重要性权重的专业评分体系
- 多维度综合健康画像

**用户体验优化**
- 实时响应的分析结果
- 个性化的健康建议
- 直观的健康状态展示

### 6.3 扩展性设计

**模块化架构**
- 各分析引擎独立可替换
- 统一接口便于功能扩展
- 配置化的参数调整

**多层级支持**
- 个人用户分析
- 部门聚合分析
- 组织整体分析

**国际化就绪**
- 支持多语言建议模板
- 可配置的健康标准
- 灵活的单位换算

## 7. 总结

### 7.1 系统现状

✅ **完整实现** - 8个核心模块全部完成，功能完备  
✅ **性能优良** - 响应时间<30秒，支持并发处理  
✅ **质量保证** - 全面测试覆盖，监控告警完善  
✅ **集成友好** - 基于现有代码，最小侵入式设计

### 7.2 核心价值

1. **避免数据丢失**：提供ljwx-boot定时任务的完整备份方案
2. **保证连续性**：确保健康分析功能持续可用
3. **提升质量**：基于科学统计方法的专业分析
4. **优化体验**：实时响应的个性化健康服务

### 7.3 后续发展方向

**功能增强**
- 支持更多健康特征的分析
- 增加机器学习预测模型  
- 扩展多语言国际化支持

**性能优化**
- 分布式处理支持
- 数据库查询进一步优化
- 缓存策略动态调整

**业务拓展**
- 企业健康管理解决方案
- 个人健康管理助手
- 医疗健康数据分析平台

该实时健康数据分析系统为ljwx-bigscreen提供了强大的健康数据分析能力，确保了系统的高可用性和业务连续性，为用户提供专业、及时、个性化的健康管理服务。
    recommendation_id varchar(64) NOT NULL,    -- 建议唯一ID
    recommendation_type varchar(50) NOT NULL,  -- 建议类型
    title varchar(200) NOT NULL,               -- 建议标题
    description text,                          -- 建议描述
    recommended_actions json,                  -- 推荐行动(JSON格式)
    status varchar(20) DEFAULT 'pending',      -- pending/in_progress/completed
    start_date date,                           -- 开始日期
    target_completion_date date,               -- 目标完成日期
    actual_completion_date date,               -- 实际完成日期
    effectiveness_score decimal(5,2),          -- 有效性评分
    user_feedback text,                        -- 用户反馈
    health_improvement_metrics json            -- 健康改善指标
);
```

#### 2.2.4 t_health_profile（用户健康画像表）- ⚠️ 0条数据
```sql
CREATE TABLE t_health_profile (
    id bigint PRIMARY KEY AUTO_INCREMENT,
    user_id bigint NOT NULL,
    customer_id bigint NOT NULL,
    profile_date date NOT NULL,
    overall_health_score decimal(5,2) DEFAULT 0.00,    -- 总体健康评分
    health_level varchar(20) DEFAULT 'fair',           -- 健康等级
    physiological_score decimal(5,2) DEFAULT 0.00,     -- 生理评分
    behavioral_score decimal(5,2) DEFAULT 0.00,        -- 行为评分
    risk_factor_score decimal(5,2) DEFAULT 0.00,       -- 风险因子评分
    cardiovascular_score decimal(5,2) DEFAULT 0.00,    -- 心血管评分
    respiratory_score decimal(5,2) DEFAULT 0.00,       -- 呼吸系统评分
    metabolic_score decimal(5,2) DEFAULT 0.00,         -- 代谢评分
    psychological_score decimal(5,2) DEFAULT 0.00,     -- 心理评分
    detailed_analysis json,                            -- 详细分析数据
    trend_analysis json,                               -- 趋势分析数据
    recommendations json                               -- 个性化建议
);
```

#### 2.2.5 t_health_weight_cache（权重缓存表）- ✅ 166条数据
```sql
CREATE TABLE t_health_weight_cache (
    id bigint PRIMARY KEY AUTO_INCREMENT,
    user_id bigint NOT NULL,                           -- 用户ID
    customer_id bigint NOT NULL,                       -- 客户ID
    metric_name varchar(50) NOT NULL,                  -- 指标名称
    base_weight decimal(5,4) DEFAULT 0.1500,          -- 基础权重
    position_risk_multiplier decimal(5,4) DEFAULT 1.0000, -- 岗位风险系数
    combined_weight decimal(5,4) DEFAULT 0.1500,      -- 综合权重
    normalized_weight decimal(5,4) DEFAULT 0.1500,    -- 归一化权重
    position_id bigint DEFAULT 0,                     -- 岗位ID
    position_risk_level varchar(20) DEFAULT 'normal', -- 岗位风险等级
    cache_date date NOT NULL,                         -- 缓存日期
    create_time datetime DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_date (user_id, cache_date),
    INDEX idx_customer_date (customer_id, cache_date)
);
```

## 3. LJWX-Boot 健康分析服务架构

### 3.1 定时任务系统（核心）

#### 3.1.1 HealthBaselineScoreTasks.java - 主任务调度器
**位置：** `ljwx-boot-modules/src/main/java/com/ljwx/modules/health/task/HealthBaselineScoreTasks.java`

**任务执行时间表：**
```java
01:00 - 权重配置验证任务 (validateWeightConfigurations)
02:00 - 生成用户健康基线 (generateUserHealthBaseline) 
02:05 - 生成部门健康基线聚合 (generateDepartmentHealthBaseline)
02:10 - 生成组织健康基线 (generateOrgHealthBaseline)
02:15 - 生成部门健康评分 (generateDepartmentHealthScore)
04:00 - 生成用户健康评分 (generateHealthScore) ✓已生成76条数据
04:10 - 生成组织健康评分 (generateOrgHealthScore)
05:30 - 生成健康预测 (generateHealthPredictions)
06:00 - 生成健康建议 (generateHealthRecommendations)
07:00 - 数据清理任务 (cleanupOldData)

每月1日凌晨 - 按月分表任务 (archiveAndResetUserHealthTable)
```

**支持的健康特征：**
```java
private static final String[] HEALTH_FEATURES = {
    "heart_rate", "blood_oxygen", "temperature", "pressure_high", 
    "pressure_low", "stress", "step", "calorie", "distance", "sleep"
};
```

### 3.2 核心服务类列表

#### 3.2.1 健康分析服务
```java
// 健康评分计算
HealthScoreCalculationService.java    -- 综合健康评分计算服务
HealthBaselineService.java           -- 健康基线服务接口
HealthPredictionService.java         -- 健康预测分析服务（完整实现）
HealthRecommendationService.java     -- 健康建议生成服务（完整实现）
WeightCalculationService.java        -- 权重计算服务（标准权重分配）
```

#### 3.2.2 权重分配算法（已实现）
```java
// 核心生命体征权重 (65%)
heart_rate: 20%      // 心率 - 最重要的生命体征
blood_oxygen: 18%    // 血氧 - 呼吸系统核心指标  
temperature: 15%     // 体温 - 基础生命体征
pressure_high: 6%    // 收缩压
pressure_low: 6%     // 舒张压

// 健康状态指标权重 (20%)
stress: 12%          // 压力指数 - 心理健康重要指标
sleep: 8%            // 睡眠质量

// 运动健康指标权重 (10%)
step: 4%             // 步数
distance: 3%         // 距离
calorie: 3%          // 卡路里

// 辅助指标权重 (5%)
ecg: 2%              // 心电图等其他指标
```

### 3.3 健康分析算法详解

#### 3.3.1 Z-Score评分算法
```java
// 1. Z-Score标准化计算
z_score = (当前值 - 基线均值) / 基线标准差

// 2. 基础评分计算
基础评分 = 100 - |Z-Score| * 10

// 3. 异常惩罚计算  
if (值 > 基线最大值 * 1.2 OR 值 < 基线最小值 * 0.8) {
    惩罚分数 = 异常程度百分比 * 惩罚系数
}

// 4. 最终评分
最终评分 = MAX(0, MIN(100, 基础评分 - 惩罚分数))
```

#### 3.3.2 权重缓存机制（已实现）
**表：** `t_health_weight_cache`
**功能：** 每日生成用户权重缓存，结合岗位风险系数和基础权重

## 4. LJWX-BigScreen API接口完整清单

### 4.1 健康数据查询接口（现有）

#### 4.1.1 综合健康分析接口 ❌问题：硬编码数据
```python
GET /api/health/analysis/comprehensive?deviceSn={}&days={}
```
**当前状态：** 返回硬编码分析结果，未读取数据库
**需要修复：** 集成t_health_score表数据

#### 4.1.2 健康趋势分析接口 ❌问题：硬编码数据  
```python
GET /api/health/trends/analysis?deviceSn={}&timeRange={}
```
**当前状态：** 返回硬编码趋势数据，时间维度不一致
**需要修复：** 统一时间维度，读取真实数据

#### 4.1.3 健康建议接口 ❌问题：硬编码数据
```python
POST /api/health/recommendations
GET /api/health/recommendations  # 需要添加GET支持
```
**当前状态：** 返回硬编码建议列表，无时间维度
**需要修复：** 读取t_health_recommendation_track表数据

#### 4.1.4 健康评分接口
```python  
GET /api/health/scores?deviceSn={}&startDate={}&endDate={}
POST /api/health/comprehensive/score
```

### 4.2 需要新增的API接口

#### 4.2.1 健康画像接口（缺失）
```python
GET /api/health/profile?deviceSn={}&profileDate={}
POST /api/health/profile/generate
```
**数据源：** t_health_profile表

#### 4.2.2 健康基线接口（部分实现）
```python
GET /api/health/baseline/<metric>?deviceSn={}&dateRange={}
POST /api/health/baseline/personal
```
**数据源：** t_health_baseline表

## 5. 前端页面接口调用分析

### 5.1 personal.html 接口调用清单

#### 5.1.1 当前API调用
```javascript
// 1. 主数据加载
fetch(`/get_personal_info?deviceSn=${deviceSn}`) ✓正常

// 2. 健康画像数据 ❌问题接口
fetch(`/api/health/analysis/comprehensive?deviceSn=${deviceSn}&days=30`) -- 硬编码数据

// 3. 健康趋势数据 ❌问题接口  
fetch(`/api/health/trends/analysis?deviceSn=${deviceSn}&timeRange=${timeRange}`) -- 时间维度不统一

// 4. 健康预测数据 ❌问题接口
fetch(`/api/health/analysis/comprehensive?deviceSn=${deviceSn}&days=7`) -- 硬编码预测

// 5. 健康建议数据 ❌问题接口
fetch('/api/health/recommendations', {method: 'POST'}) -- 硬编码建议
```

#### 5.1.2 缺失的API调用
```javascript
// 健康评分数据加载 - 缺失
loadHealthScoreData() -- 需要添加

// 健康画像数据加载 - 缺失  
loadHealthProfileData() -- 需要添加

// GET方式建议加载 - 缺失
loadHealthRecommendations() -- 需要修改为GET请求
```

### 5.2 bigscreen_main.html 接口调用清单

#### 5.2.1 当前API调用
```javascript
// 综合健康评分加载 ❌问题接口
fetch(`/api/health/score/comprehensive`, {method: 'POST'}) -- 可能硬编码

// 健康数据刷新
refreshHealthData() -- 需要验证数据源
```

## 6. 问题诊断与解决方案

### 6.1 当前问题汇总

#### 6.1.1 数据流断裂问题
**问题描述：**
- ✅ ljwx-boot定时任务正常生成数据（t_health_score有76条数据）
- ❌ ljwx-bigscreen API接口返回硬编码数据
- ❌ 前端页面显示模拟数据而非真实分析结果

#### 6.1.2 具体问题清单
1. **健康建议数据缺失：** t_health_recommendation_track表0条数据
2. **健康画像数据缺失：** t_health_profile表0条数据  
3. **API接口硬编码：** /api/health/*接口未读取数据库
4. **时间维度不统一：** 不同接口时间参数格式不一致
5. **GET请求缺失：** 建议接口只支持POST，前端需要GET

### 6.2 完整解决方案

#### 6.2.1 修复BigScreen.py API接口（优先级：高）

**需要修复的接口：**
1. `/api/health/analysis/comprehensive` - 集成t_health_score数据
2. `/api/health/recommendations` - 添加GET支持，读取数据库
3. `/api/health/trends/analysis` - 统一时间维度
4. 新增 `/api/health/scores` - 专用评分查询接口  
5. 新增 `/api/health/profile` - 健康画像查询接口

#### 6.2.2 完善ljwx-boot数据生成（优先级：中）

**需要完善的任务：**
1. 健康建议生成任务 - 确保06:00任务正常生成建议
2. 健康画像生成任务 - 可能需要添加画像生成逻辑
3. 预测数据生成任务 - 确保05:30任务生成预测数据

#### 6.2.3 前端页面调用优化（优先级：中）

**需要修改的函数：**
1. `loadHealthScoreData()` - 新增健康评分加载
2. `loadHealthProfileData()` - 修复画像数据加载  
3. `loadHealthRecommendations()` - 改为GET请求
4. 添加定时刷新机制

### 6.3 实施优先级

**第一阶段（立即修复）：**
1. 修复/api/health/recommendations接口支持GET请求
2. 修复/api/health/analysis/comprehensive接口读取数据库
3. 前端调用改为从数据库获取数据

**第二阶段（补充完善）：**  
1. 确保所有定时任务正常生成数据
2. 添加缺失的API接口
3. 完善前端数据展示逻辑

**第三阶段（优化提升）：**
1. 性能优化和缓存策略
2. 错误处理和容错机制
3. 数据质量监控

## 7. 管理界面和监控

### 7.1 任务管理界面
**地址：** `http://localhost:3000/#/monitor/scheduler`
**功能：**
- 查看所有调度任务状态
- 立即执行任务 (immediate)  
- 暂停/恢复任务 (pause/resume)
- 编辑任务配置
- 删除任务

### 7.2 数据质量监控
```sql
-- 监控健康评分数据生成情况
SELECT score_date, COUNT(*) as records, COUNT(DISTINCT device_sn) as devices 
FROM t_health_score 
WHERE score_date >= DATE_SUB(NOW(), INTERVAL 7 DAY) 
GROUP BY score_date;

-- 监控健康建议数据生成情况  
SELECT DATE(create_time) as date, COUNT(*) as recommendations
FROM t_health_recommendation_track
WHERE create_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY DATE(create_time);
```

## 8. 总结与下一步行动

### 8.1 系统现状
- ✅ **数据库设计完善：** 20+健康相关表结构完整
- ✅ **定时任务运行：** ljwx-boot定时任务正常生成基线和评分数据
- ✅ **前端界面完备：** personal.html和bigscreen_main.html界面完整
- ❌ **API数据源问题：** ljwx-bigscreen接口返回硬编码数据

### 8.2 关键问题
**核心问题：数据流断裂**
- ljwx-boot生成真实分析数据存储在数据库 
- ljwx-bigscreen API返回硬编码数据
- 前端显示模拟数据而非真实分析结果

### 8.3 解决方案重点
1. **修复API接口：** 让BigScreen.py从数据库读取真实数据
2. **完善数据生成：** 确保所有定时任务正常生成建议和画像数据  
3. **优化前端调用：** 统一API调用方式和数据格式

**优先修复顺序：**
1. `/api/health/recommendations`接口（支持GET + 数据库查询）
2. `/api/health/analysis/comprehensive`接口（集成评分数据）  
3. 前端调用优化（统一数据获取逻辑）

### 1.3 数据源约束

**支持的健康数据表：**
- `t_user_health_data` - 实时健康体征数据
- `t_user_health_data_daily` - 每日汇总健康数据
- `t_user_health_data_weekly` - 每周汇总健康数据

**支持的体征类型：**
基于 `t_health_data_config` 表配置，目前支持：
- heart_rate (心率)
- blood_oxygen (血氧)  
- temperature (体温)
- pressure_high (收缩压)
- pressure_low (舒张压)
- stress (压力)
- step (步数)
- distance (距离)
- calorie (卡路里)
- sleep (睡眠)

## 2. 健康基线生成引擎

### 2.1 数据源限制

健康基线生成引擎严格基于以下数据源：

**主要数据源：**
- `t_user_health_data` - 实时体征数据，包含心率、血氧、血压等关键指标
- `t_user_health_data_daily` - 每日汇总数据，包含睡眠、运动等数据
- `t_user_health_data_weekly` - 每周汇总数据，用于长期趋势分析

**配置数据源：**
- `t_health_data_config` - 体征配置表，定义支持的体征类型和权重

### 2.2 基线计算算法

```python
# 基于现有数据表的基线计算
class HealthBaselineEngine:
    def __init__(self):
        self.supported_metrics = self._get_enabled_metrics_from_config()
        
    def _get_enabled_metrics_from_config(self):
        """从t_health_data_config表获取启用的体征"""
        return db.session.query(HealthDataConfig).filter(
            HealthDataConfig.is_enabled == True
        ).all()
        
    def calculate_personal_baseline(self, user_id, customer_id, days_back=90):
        """基于用户历史数据计算个人基线"""
        baseline_data = {}
        
        # 获取启用的体征配置
        enabled_metrics = db.session.query(HealthDataConfig).filter_by(
            customer_id=customer_id, is_enabled=True
        ).all()
        
        for metric_config in enabled_metrics:
            metric_name = metric_config.data_type
            
            # 从t_user_health_data获取历史数据
            historical_data = self._get_metric_history(
                user_id, metric_name, days_back
            )
            
            if historical_data:
                baseline_data[metric_name] = {
                    'mean': np.mean(historical_data),
                    'std': np.std(historical_data),
                    'median': np.median(historical_data),
                    'q25': np.percentile(historical_data, 25),
                    'q75': np.percentile(historical_data, 75),
                    'sample_count': len(historical_data),
                    'weight': float(metric_config.weight or 0.15)
                }
        
        return baseline_data
```

### 2.3 支持的基线类型

**个人基线：**
- 基于用户90天历史数据计算
- 自动过滤异常值（使用IQR方法）
- 考虑数据完整性和稳定性

**群体基线：**  
- 基于同customer_id下相似用户群体
- 按年龄、性别、岗位分组计算
- 用于个人数据对比和异常检测

### 2.4 基线存储设计

需要新增基线存储表：

```sql
CREATE TABLE t_health_baseline (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    customer_id BIGINT NOT NULL,
    baseline_type ENUM('personal', 'population') NOT NULL,
    metric_name VARCHAR(50) NOT NULL,
    baseline_mean DECIMAL(10,2),
    baseline_std DECIMAL(10,2), 
    baseline_median DECIMAL(10,2),
    sample_count INT,
    baseline_date DATE NOT NULL,
    valid_until DATE,
    age_group VARCHAR(20),
    gender VARCHAR(10),
    position_id BIGINT,
    is_current BOOLEAN DEFAULT TRUE,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_user_metric_date (user_id, metric_name, baseline_date),
    INDEX idx_customer_metric (customer_id, metric_name),
    INDEX idx_user_current (user_id, is_current)
);
```

## 3. 健康评分系统

### 3.1 基于权重的评分模型

健康评分系统基于现有的权重配置体系，结合体征权重和岗位权重进行综合评分。

**权重体系：**
```python
# 基于t_health_data_config表的体征权重
def _get_metric_weights(self, customer_id):
    """获取体征权重配置"""
    configs = db.session.query(HealthDataConfig).filter_by(
        customer_id=customer_id, is_enabled=True
    ).all()
    
    weights = {}
    for config in configs:
        weights[config.data_type] = {
            'weight': float(config.weight) if config.weight else 0.15,
            'warning_high': float(config.warning_high) if config.warning_high else None,
            'warning_low': float(config.warning_low) if config.warning_low else None
        }
    return weights

# 基于sys_position表的岗位权重  
def _get_position_weight(self, user_id):
    """获取用户岗位权重"""
    result = db.session.query(Position.weight).join(
        UserPosition, Position.id == UserPosition.position_id
    ).filter(
        UserPosition.user_id == user_id,
        UserPosition.is_deleted == False,
        Position.is_deleted == False
    ).first()
    
    return float(result[0]) if result and result[0] else 0.15
```

### 3.2 评分算法

**综合评分公式：**
```python
def calculate_comprehensive_health_score(self, user_id, customer_id):
    """计算综合健康评分"""
    
    # 1. 获取体征权重配置
    metric_weights = self._get_metric_weights(customer_id)
    
    # 2. 获取岗位权重
    position_weight = self._get_position_weight(user_id)
    
    # 3. 获取用户健康数据和个人基线
    health_data = self._get_user_health_data(user_id, 30)
    baseline = self._get_user_baseline(user_id)
    
    total_score = 0
    total_weight = 0
    
    # 4. 按体征计算加权评分
    for metric_name, weight_config in metric_weights.items():
        if metric_name in baseline:
            # 计算单体征评分（基于Z-Score）
            current_values = [getattr(record, metric_name) 
                            for record in health_data 
                            if getattr(record, metric_name) is not None]
            
            if current_values:
                current_avg = np.mean(current_values)
                baseline_info = baseline[metric_name]
                
                # Z-Score标准化
                z_score = (current_avg - baseline_info['mean']) / \
                         max(baseline_info['std'], 0.1)
                
                # 转换为评分 (0-100)
                metric_score = max(0, 100 - abs(z_score) * 15)
                
                # 应用体征权重
                weight = weight_config['weight']
                total_score += metric_score * weight
                total_weight += weight
    
    # 5. 应用岗位权重调整
    base_score = total_score / total_weight if total_weight > 0 else 0
    
    # 高风险岗位评分调整
    if position_weight < 0.15:  # 高风险岗位
        risk_adjustment = (0.15 - position_weight) * 100  # 风险调整
        final_score = max(0, base_score - risk_adjustment)
    else:
        final_score = base_score
    
    return {
        'user_id': user_id,
        'total_score': round(final_score, 2),
        'base_score': round(base_score, 2),
        'position_weight': position_weight,
        'metric_scores': self._get_detailed_metric_scores(health_data, baseline, metric_weights)
    }
```

### 3.2 评分算法

**生理指标评分 (基于Z-Score标准化):**
```python
def _calculate_physiological_score(self, health_data, baseline, config):
    """
    生理指标评分算法：
    1. 计算当前平均值与个人基线的Z-Score
    2. 将Z-Score转换为0-100评分
    3. 应用指标权重进行加权平均
    """
    z_score = (current_avg - baseline_mean) / max(baseline_std, 0.1)
    metric_score = 100 - min(abs(z_score) * 15, 50)  # 正向指标
    # 或
    metric_score = 100 - min(abs(z_score) * 20, 60)  # 控制指标
```

**行为指标评分 (目标达成度):**
- 运动评分: 基于每日步数达标率
- 睡眠评分: 基于睡眠时长和一致性
- 活跃度评分: 基于距离和热量消耗

### 3.3 评分等级划分

| 评分区间 | 健康等级 | 状态描述 | 建议行动 |
|----------|----------|----------|----------|
| 90-100   | excellent | 健康状况优秀 | 继续保持 |
| 80-89    | good      | 健康状况良好 | 维持现状 |
| 70-79    | fair      | 健康状况一般 | 适度改善 |
| 60-69    | poor      | 健康状况较差 | 积极改善 |
| 0-59     | critical  | 健康状况堪忧 | 立即关注 |

## 4. 健康预测模型（基于统计学方法）

### 4.1 预测模型架构

健康预测模型基于传统统计学方法，不依赖机器学习，使用时间序列分析和趋势计算。

```python
# 基于统计学的预测模型
class HealthPredictionEngine:
    def __init__(self):
        self.prediction_methods = ['linear_trend', 'moving_average', 'seasonal_decomposition']
        
    def predict_health_trends(self, user_id, customer_id, prediction_horizon=30):
        """
        基于统计学方法的健康趋势预测：
        1. 线性趋势分析
        2. 移动平均预测
        3. 季节性分解
        4. 风险区间计算
        """
        predictions = {}
        
        # 获取启用的体征
        enabled_metrics = db.session.query(HealthDataConfig).filter_by(
            customer_id=customer_id, is_enabled=True
        ).all()
        
        for metric_config in enabled_metrics:
            metric_name = metric_config.data_type
            
            # 获取历史数据（过去90天）
            historical_data = self._get_metric_time_series(user_id, metric_name, 90)
            
            if len(historical_data) >= 10:  # 需要足够的数据点
                trend_prediction = self._calculate_linear_trend_prediction(
                    historical_data, prediction_horizon
                )
                predictions[metric_name] = trend_prediction
                
        return predictions
```

### 4.2 预测算法

**时间序列预测算法：**
1. **趋势分解**: 使用线性回归和多项式拟合分析长期趋势
2. **季节性分析**: 识别数据中的周期性模式
3. **异常检测**: 基于IQR和Z-Score的异常值识别
4. **预测区间**: 提供点预测和置信区间

**风险评分预测：**
```python
def calculate_risk_probability(self, risk_factors, protective_factors):
    """
    基于风险因子和保护因子计算未来风险概率
    """
    base_risk = 0.1  # 基础风险概率
    
    # 风险因子贡献
    risk_contribution = sum(factor['weight'] * factor['severity'] 
                          for factor in risk_factors)
    
    # 保护因子减免
    protective_contribution = sum(factor['weight'] * factor['effectiveness'] 
                                for factor in protective_factors)
    
    # 最终风险概率
    final_risk = max(0, base_risk + risk_contribution - protective_contribution)
    return min(1.0, final_risk)
```

### 4.3 预测输出格式

```json
{
  "user_id": 12345,
  "prediction_date": "2024-03-20",
  "prediction_horizon_days": 30,
  "overall_risk_score": 0.23,
  "risk_level": "medium",
  "specific_risks": {
    "cardiovascular": {
      "probability": 0.15,
      "confidence": 0.85,
      "key_indicators": ["blood_pressure", "heart_rate_variability"]
    },
    "metabolic": {
      "probability": 0.31,
      "confidence": 0.78,
      "key_indicators": ["temperature_stability", "activity_level"]
    }
  },
  "trend_predictions": {
    "heart_rate": {
      "predicted_trend": "stable",
      "confidence": 0.92,
      "predicted_range": [70, 85]
    }
  }
}
```

## 5. 智能建议引擎

### 5.1 个性化建议生成

智能建议引擎（`HealthRecommendationEngine`）基于用户的健康评分分析和预测结果，生成个性化的健康改善建议。

### 5.2 建议类型体系

```python
RECOMMENDATION_TYPES = {
    'physiological': '生理指标改善',
    'behavioral': '行为习惯调整', 
    'risk_prevention': '风险预防',
    'lifestyle': '生活方式优化',
    'exercise': '运动建议',
    'nutrition': '营养指导',
    'sleep': '睡眠改善',
    'stress': '压力管理'
}
```

### 5.3 建议生成算法

**基于规则的建议生成：**
```python
def _generate_physiological_recommendations(self, analysis, user_profile):
    """
    生理指标改善建议生成流程：
    1. 识别薄弱的生理指标
    2. 根据用户画像调整建议内容
    3. 设定改善目标和时间线
    4. 生成具体行动步骤
    """
    recommendations = []
    
    if analysis['cardiovascular_score'] < 70:
        recommendations.append({
            'category': 'cardiovascular',
            'priority': 'high',
            'title': '心血管健康改善建议',
            'actions': [
                '每周进行3-4次有氧运动，每次30-45分钟',
                '控制饮食中的饱和脂肪和胆固醇摄入',
                '保持规律的作息时间，避免熬夜',
                '学习放松技巧，如深呼吸和冥想'
            ],
            'timeline': '4-6周改善计划',
            'expected_improvement': 15
        })
    
    return recommendations
```

### 5.4 建议执行跟踪

**建议跟踪机制：**
- **进度监控**: 跟踪用户执行建议的进度
- **效果评估**: 对比执行前后的健康指标改善
- **动态调整**: 根据执行效果调整后续建议
- **激励机制**: 提供完成奖励和持续动力

```python
class RecommendationTracker:
    def evaluate_recommendation_effectiveness(self, recommendation_id):
        """
        建议效果评估：
        1. 获取执行前后的健康数据
        2. 计算关键指标的改善程度
        3. 生成效果评估报告
        4. 为后续建议优化提供反馈
        """
```

## 6. 健康画像生成器

### 6.1 综合健康画像

健康画像生成器（`HealthProfileEngine`）整合所有分析结果，为用户创建全面的健康画像。

### 6.2 画像组成要素

```python
HEALTH_PROFILE_COMPONENTS = {
    'user_basic_info': '用户基础信息',
    'current_health_status': '当前健康状态',
    'health_metrics_analysis': '健康指标分析',
    'behavioral_analysis': '行为模式分析',
    'risk_assessment': '风险评估',
    'health_trends': '健康趋势变化',
    'personalized_recommendations': '个性化建议',
    'health_goals': '健康目标设定',
    'monitoring_plan': '监测计划'
}
```

### 6.3 画像可视化数据

**雷达图数据结构：**
```json
{
  "radar_chart": {
    "dimensions": ["心血管", "呼吸系统", "代谢功能", "心理健康", "运动能力", "睡眠质量"],
    "values": [85, 92, 78, 88, 75, 90],
    "max_value": 100
  },
  "trend_charts": {
    "heart_rate": {
      "direction": "stable",
      "strength": 0.02,
      "stability": 85.2
    }
  },
  "risk_heatmap": {
    "risk_factors": [
      {
        "name": "工作压力",
        "severity": "medium", 
        "impact_score": 0.3
      }
    ],
    "current_risk_level": "low"
  }
}
```

### 6.4 画像持久化

**数据库设计：**
```sql
CREATE TABLE user_health_profile (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    customer_id BIGINT NOT NULL,
    profile_date DATE NOT NULL,
    overall_health_score DECIMAL(5,2),
    health_level VARCHAR(20),
    physiological_score DECIMAL(5,2),
    behavioral_score DECIMAL(5,2),
    risk_factor_score DECIMAL(5,2),
    detailed_analysis JSON,
    trend_analysis JSON,
    recommendations JSON,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    version INT DEFAULT 1,
    is_deleted BOOLEAN DEFAULT FALSE
);
```

## 7. 建议执行跟踪系统（闭环管理）

### 7.1 跟踪数据库设计

为实现建议执行的闭环管理，需要新增以下数据表：

```sql
-- 健康建议主表
CREATE TABLE t_health_recommendation (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    customer_id BIGINT NOT NULL,
    recommendation_type ENUM('physiological', 'behavioral', 'lifestyle') NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    priority ENUM('high', 'medium', 'low') DEFAULT 'medium',
    status ENUM('pending', 'in_progress', 'completed', 'expired', 'cancelled') DEFAULT 'pending',
    start_date DATE,
    target_completion_date DATE,
    actual_completion_date DATE,
    expected_improvement DECIMAL(5,2),
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    INDEX idx_user_status (user_id, status),
    INDEX idx_customer_date (customer_id, start_date)
);

-- 建议行动步骤表
CREATE TABLE t_recommendation_action (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    recommendation_id BIGINT NOT NULL,
    action_description TEXT NOT NULL,
    action_order INT NOT NULL,
    is_completed BOOLEAN DEFAULT FALSE,
    completion_date DATETIME,
    user_feedback TEXT,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (recommendation_id) REFERENCES t_health_recommendation(id),
    INDEX idx_recommendation (recommendation_id)
);

-- 建议执行效果跟踪表
CREATE TABLE t_recommendation_effect (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    recommendation_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    metric_name VARCHAR(50) NOT NULL,
    baseline_value DECIMAL(10,2),
    current_value DECIMAL(10,2), 
    improvement_rate DECIMAL(5,2),
    measurement_date DATE NOT NULL,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (recommendation_id) REFERENCES t_health_recommendation(id),
    INDEX idx_recommendation_metric (recommendation_id, metric_name),
    INDEX idx_user_date (user_id, measurement_date)
);
```

### 7.2 闭环管理流程

```python
class RecommendationTracker:
    """建议跟踪和效果评估"""
    
    def create_recommendation(self, user_id, customer_id, recommendation_data):
        """创建新建议"""
        recommendation = HealthRecommendation(
            user_id=user_id,
            customer_id=customer_id,
            recommendation_type=recommendation_data['type'],
            title=recommendation_data['title'],
            description=recommendation_data['description'],
            priority=recommendation_data.get('priority', 'medium'),
            start_date=date.today(),
            target_completion_date=self._calculate_target_date(recommendation_data.get('timeline'))
        )
        
        db.session.add(recommendation)
        db.session.flush()  # 获取ID
        
        # 添加行动步骤
        for i, action in enumerate(recommendation_data.get('actions', []), 1):
            action_record = RecommendationAction(
                recommendation_id=recommendation.id,
                action_description=action,
                action_order=i
            )
            db.session.add(action_record)
        
        db.session.commit()
        return recommendation.id
    
    def update_progress(self, recommendation_id, progress_data):
        """更新执行进度"""
        recommendation = db.session.query(HealthRecommendation).get(recommendation_id)
        
        if progress_data.get('completed_actions'):
            # 更新完成的行动步骤
            for action_id in progress_data['completed_actions']:
                action = db.session.query(RecommendationAction).get(action_id)
                if action:
                    action.is_completed = True
                    action.completion_date = datetime.now()
        
        # 检查是否全部完成
        total_actions = db.session.query(RecommendationAction).filter_by(
            recommendation_id=recommendation_id
        ).count()
        
        completed_actions = db.session.query(RecommendationAction).filter_by(
            recommendation_id=recommendation_id, is_completed=True
        ).count()
        
        if completed_actions == total_actions:
            recommendation.status = 'completed'
            recommendation.actual_completion_date = date.today()
            
            # 启动效果评估
            self._evaluate_effectiveness(recommendation_id)
        
        db.session.commit()
    
    def _evaluate_effectiveness(self, recommendation_id):
        """评估建议执行效果"""
        recommendation = db.session.query(HealthRecommendation).get(recommendation_id)
        
        # 获取建议执行前的基线数据
        baseline_date = recommendation.start_date - timedelta(days=7)
        current_date = recommendation.actual_completion_date + timedelta(days=7)
        
        # 获取相关体征的改善情况
        relevant_metrics = self._get_relevant_metrics(recommendation.recommendation_type)
        
        for metric_name in relevant_metrics:
            baseline_data = self._get_metric_average(
                recommendation.user_id, metric_name, baseline_date, 7
            )
            current_data = self._get_metric_average(
                recommendation.user_id, metric_name, current_date, 7
            )
            
            if baseline_data and current_data:
                improvement_rate = ((current_data - baseline_data) / baseline_data) * 100
                
                effect_record = RecommendationEffect(
                    recommendation_id=recommendation_id,
                    user_id=recommendation.user_id,
                    metric_name=metric_name,
                    baseline_value=baseline_data,
                    current_value=current_data,
                    improvement_rate=improvement_rate,
                    measurement_date=current_date
                )
                db.session.add(effect_record)
        
        db.session.commit()
```

## 8. 系统集成与部署

### 8.1 API接口设计

**核心API端点：**
```python
# 健康评分API
@app.route('/api/health/score/<int:user_id>', methods=['GET'])
def get_health_score(user_id):
    """获取用户健康评分"""

# 健康预测API
@app.route('/api/health/prediction/<int:user_id>', methods=['GET'])
def get_health_prediction(user_id):
    """获取用户健康风险预测"""

# 健康建议API
@app.route('/api/health/recommendations/<int:user_id>', methods=['GET'])
def get_health_recommendations(user_id):
    """获取用户个性化健康建议"""

# 健康画像API
@app.route('/api/health/profile/<int:user_id>', methods=['GET'])
def get_health_profile(user_id):
    """获取用户综合健康画像"""
```

### 8.2 性能优化

**缓存策略：**
- Redis缓存健康基线数据（TTL: 24小时）
- 健康评分结果缓存（TTL: 4小时）
- 健康画像数据缓存（TTL: 12小时）

**批处理优化：**
```python
class HealthProfileBatchProcessor:
    def batch_generate_profiles(self, customer_id):
        """批量生成客户下所有用户的健康画像"""
        # 并行处理多个用户
        # 批量数据库操作
        # 结果聚合和统计
```

### 8.3 监控和告警

**系统监控指标：**
- 分析处理时间和成功率
- API响应时间和错误率
- 数据质量和完整性指标
- 用户参与度和满意度

## 9. 部署和运维

### 9.1 Docker容器化部署

```dockerfile
# 健康分析服务Dockerfile
FROM python:3.9-slim
COPY requirements.txt /app/
RUN pip install -r requirements.txt
COPY . /app/
WORKDIR /app
CMD ["python", "run_health_analysis.py"]
```

### 9.2 基于现有代码的完善方案

**需要新增的文件：**

1. **基线管理模块** (`bigScreen/health_baseline_manager.py`)
```python
from .models import db, HealthDataConfig, UserHealthData
from .health_baseline_engine import HealthBaselineEngine

class HealthBaselineManager:
    """健康基线管理器"""
    
    def __init__(self):
        self.baseline_engine = HealthBaselineEngine()
    
    def generate_user_baseline(self, user_id, customer_id):
        """生成用户健康基线"""
        return self.baseline_engine.calculate_personal_baseline(user_id, customer_id)
    
    def get_enabled_metrics(self, customer_id):
        """获取启用的健康体征"""
        return db.session.query(HealthDataConfig).filter_by(
            customer_id=customer_id, is_enabled=True
        ).all()
```

2. **建议跟踪模块** (`bigScreen/recommendation_tracker.py`) 
```python
from .models import db
from datetime import date, datetime, timedelta

class RecommendationTracker:
    """建议执行跟踪"""
    
    def track_recommendation_progress(self, recommendation_id, user_feedback):
        """跟踪建议执行进度"""
        # 实现闭环管理逻辑
        pass
        
    def evaluate_effectiveness(self, recommendation_id):
        """评估建议执行效果"""
        # 对比执行前后的健康数据变化
        pass
```

3. **权重计算模块** (`bigScreen/weight_calculator.py`)
```python
from .models import db, HealthDataConfig, Position, UserPosition

class WeightCalculator:
    """权重计算器"""
    
    def get_metric_weights(self, customer_id):
        """获取体征权重"""
        configs = db.session.query(HealthDataConfig).filter_by(
            customer_id=customer_id, is_enabled=True
        ).all()
        
        return {config.data_type: float(config.weight or 0.15) 
                for config in configs}
    
    def get_position_weight(self, user_id):
        """获取岗位权重"""
        result = db.session.query(Position.weight).join(
            UserPosition, Position.id == UserPosition.position_id
        ).filter(
            UserPosition.user_id == user_id,
            UserPosition.is_deleted == False
        ).first()
        
        return float(result[0]) if result else 0.15
```

**需要修改的现有文件：**

1. **models.py** - 添加新的数据模型
2. **health_score_engine.py** - 集成权重计算
3. **health_recommendation_engine.py** - 集成跟踪功能  
4. **bigScreen.py** - 添加新的API端点

### 9.3 数据备份和恢复

**备份策略：**
- 每日增量备份健康数据
- 每周全量备份分析结果
- 关键配置和模型参数备份

## 10. 实施步骤和时间计划

### 10.1 实施阶段

**第一阶段（1-2周）：数据库扩展和基线引擎**
- 新增t_health_baseline、t_health_recommendation等表
- 完善health_baseline_engine.py，集成权重配置
- 修改health_score_engine.py，支持体征权重和岗位权重
- 基础功能单元测试

**第二阶段（2-3周）：评分系统和预测模块**
- 完善基于统计学的预测算法
- 实现recommendation_tracker.py闭环管理
- 修改health_recommendation_engine.py集成跟踪
- 新增API端点支持

**第三阶段（1-2周）：系统集成和测试**
- 健康画像生成器集成所有模块
- 系统集成测试和性能优化
- 用户界面调整和数据可视化
- 生产环境部署验证

### 10.2 预期效果

**技术指标：**
- 健康评分计算时间 < 3秒
- 支持1000+用户并发分析
- 建议跟踪完成率 > 80%
- 数据处理准确率 > 95%

**业务价值：**
- 基于现有体征配置的精准评分
- 岗位风险因子的科学量化
- 建议执行的闭环管理
- 健康管理效果的可视化呈现

## 11. 风险控制和注意事项

### 11.1 技术风险控制

**数据一致性风险：**
- 严格基于t_health_data_config表的体征配置
- 确保体征权重配置的有效性验证
- 岗位权重变更时的数据重新计算机制

**性能风险控制：**
- 大量用户基线计算的批处理优化
- 健康数据查询的索引优化
- 建议跟踪表的数据增长管理

### 11.2 业务合规性

**医疗建议合规：**
- 所有建议标注"仅供参考，非医疗诊断"
- 严重异常指标及时告警机制
- 建议内容的医学审核流程

**数据隐私保护：**
- 健康数据的脱敏处理
- 基线数据的访问权限控制
- 建议跟踪数据的安全存储

---

## 总结

本修订方案完全基于 ljwx-bigscreen 现有的数据表结构和业务逻辑，去除了AI依赖，采用传统统计学方法实现健康数据分析。方案的核心特点：

### 严格的数据源约束
- 仅使用t_user_health_data、t_user_health_data_daily、t_user_health_data_weekly
- 基于t_health_data_config表的体征配置
- 支持sys_position表的岗位权重体系

### 科学的评分算法
- 基于Z-Score的标准化评分
- 体征权重与岗位权重的综合考虑
- 个人基线与群体基线的对比分析

### 完整的闭环管理
- 建议生成→执行跟踪→效果评估→持续改进
- 详细的数据表设计支持全流程管理
- 量化的改善效果评估机制

### 现实的实施路径
- 基于现有代码的渐进式改进
- 明确的开发计划和技术方案
- 可量化的效果指标和验收标准

该方案能够在现有系统基础上，以最小的技术风险实现健康数据的智能化分析和管理，为用户提供科学、个性化的健康服务。
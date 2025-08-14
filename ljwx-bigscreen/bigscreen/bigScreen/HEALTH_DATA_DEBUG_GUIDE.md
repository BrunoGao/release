# 健康数据调试指南

## 问题诊断与修复

### 问题1: pressure_high和pressure_low返回0
**原因**: get_all_health_data_optimized中的字段查询逻辑错误
**修复**: 
- 分离heart_rate和pressure字段的处理逻辑
- 添加独立的pressure字段处理分支

### 问题2: fetch_health_data_by_orgIdAndUserId返回字段格式不一致
**原因**: 统计计算中使用了错误的字段名(heartRate vs heart_rate)
**修复**:
- 修复avgHeartRate计算中的字段映射
- 统一使用数据库字段名格式(下划线)

## 调试工具使用

### 1. 无Print环境调试
使用`debug_health_data.py`工具:

```python
from debug_health_data import run_full_debug
# 设置实际参数
ORG_ID = 1  # 替换为实际组织ID
USER_ID = None  # None表示测试整个组织，或指定用户ID
run_full_debug(ORG_ID, USER_ID)
```

### 2. 查看调试日志
```bash
tail -f ljwx-bigscreen/bigscreen/bigScreen/debug_health.log
```

### 3. 分步调试
```python
# 测试健康数据配置
test_health_config(org_id)

# 测试原始数据查询
test_raw_data_query(org_id, user_id)

# 测试优化接口
test_optimized_query(org_id, user_id)

# 对比数据格式
compare_data_formats(org_id, user_id)
```

## 核心修复内容

### 修复1: 简化字段处理逻辑
```python
# 配置层面处理: get_health_data_config_by_org已包含pressure字段
default_metrics = ['heart_rate', 'blood_oxygen', 'pressure', 'pressure_high', 'pressure_low', ...]

# 简化后的处理逻辑: 直接使用enabled_metrics作为查询和返回字段
query_fields = base_fields + enabled_metrics

# 简化的数据处理: 根据字段类型直接处理
for metric in enabled_metrics:
    if metric in ['heart_rate', 'blood_oxygen', 'pressure_high', 'pressure_low', 'stress', 'step']:
        health_data[metric] = str(getattr(r, metric, None) or 0)
    elif metric == 'temperature':
        health_data['temperature'] = f"{float(getattr(r, 'temperature', None) or 0):.1f}"
    elif metric in ['distance', 'calorie', 'sleep']:
        health_data[metric] = float(getattr(r, metric, None) or 0)
```

### 修复2: 字段映射统一
```python
# 修复前
dept_stats[dn]['avgHeartRate']+=float(d['heartRate'])

# 修复后  
dept_stats[dn]['avgHeartRate']+=float(d.get('heart_rate',0))
```

## 验证步骤
1. 运行调试工具检查数据库字段存在性
2. 验证健康数据配置是否正确
3. 检查返回数据的字段格式一致性
4. 确认pressure_high/pressure_low有实际数值

## 注意事项
- 所有新数据使用数据库字段名格式(下划线)
- 保持向后兼容性，统计计算使用安全的字段获取方式
- 调试日志自动写入文件，避免print输出限制 
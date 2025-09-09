# 异步健康数据处理系统压力测试工具

## 概述

这套工具专门用于测试新实现的异步健康数据处理系统，验证1000台手表并发上传的性能优化效果。

## 文件说明

### 核心测试文件

1. **`async_health_stress_test.py`** - 主要压力测试脚本
   - 支持1000+台设备并发测试
   - 异步处理和批量上传测试
   - 详细性能统计和报告
   - 系统集成测试功能

2. **`quick_health_test.py`** - 快速验证测试
   - 基本功能验证
   - 系统状态检查
   - 适合日常快速测试

3. **`run_async_stress_test.sh`** - 测试启动脚本
   - 交互式菜单操作
   - 预定义测试场景
   - 自动依赖检查

4. **`async_stress_test_config.json`** - 测试配置文件
   - 多种测试场景配置
   - 性能目标定义
   - 服务端点配置

## 使用方法

### 1. 快速验证测试

```bash
# 基本功能验证
python3 quick_health_test.py

# 指定服务地址
python3 quick_health_test.py http://localhost:5225
```

### 2. 交互式压力测试

```bash
# 启动交互式菜单
./run_async_stress_test.sh

# 预定义场景
./run_async_stress_test.sh quick      # 快速验证 
./run_async_stress_test.sh standard   # 1000台标准测试
./run_async_stress_test.sh extreme    # 2000台极限测试
./run_async_stress_test.sh integration # 系统集成测试
```

### 3. 直接调用压力测试

```bash
# 1000台手表并发测试（推荐）
python3 async_health_stress_test.py \
    --devices 1000 \
    --concurrent 100 \
    --duration 10 \
    --url http://localhost:5225

# 系统集成测试
python3 async_health_stress_test.py --integration-test

# 自定义参数测试
python3 async_health_stress_test.py \
    --devices 500 \
    --concurrent 80 \
    --duration 5 \
    --interval 0.5
```

## 测试场景

### 预定义场景

1. **快速验证测试**
   - 100台设备，5分钟
   - 验证基本功能正常

2. **中等负载测试** 
   - 500台设备，8分钟
   - 测试中等并发负载

3. **高并发压力测试** ⭐ **推荐**
   - 1000台设备，10分钟
   - 主要验证场景

4. **极限负载测试**
   - 2000台设备，15分钟
   - 测试系统极限

5. **批量处理测试**
   - 专门测试批量上传优化

6. **系统集成测试**
   - 检查异步组件状态
   - 验证新架构功能

## 健康数据格式

测试使用符合真实场景的健康数据格式：

```json
{
  "data": {
    "deviceSn": "CRFTQ23409001890",
    "heart_rate": 81,
    "blood_oxygen": 97,
    "body_temperature": "36.8",
    "step": 5432,
    "distance": "3.2",
    "calorie": "156.7",
    "latitude": "22.540278",
    "longitude": "114.015232", 
    "altitude": "0.0",
    "stress": 45,
    "upload_method": "wifi",
    "blood_pressure_systolic": 122,
    "blood_pressure_diastolic": 84,
    "sleepData": "null",
    "exerciseDailyData": "null",
    "exerciseWeekData": "null",
    "scientificSleepData": "null", 
    "workoutData": "null",
    "timestamp": "2025-09-01 15:22:27"
  }
}
```

## 性能目标

基于异步优化系统，预期性能指标：

- **QPS目标**: 500+ 请求/秒
- **响应时间**: <0.2秒
- **成功率**: >99%
- **并发能力**: 1000+ 设备同时上传
- **整体性能提升**: 85-90%

## 测试报告

测试完成后会生成详细报告，包括：

- 📊 **整体统计**: QPS、成功率、响应时间
- ⚡ **性能分析**: 95%分位数、极值统计  
- ❌ **错误分析**: 错误类型和分布
- 🎯 **性能评估**: 与目标对比分析
- 🆚 **优化效果**: 与传统架构对比

## 依赖要求

```bash
pip3 install aiohttp asyncio
```

或者运行脚本会自动检查并安装依赖。

## 服务端点配置

### 默认端点
- **本地调试**: http://localhost:5225
- **Docker部署**: http://localhost:5001  
- **生产环境**: http://192.168.1.83:5001

### 健康检查端点
- `/health` - 基本健康检查
- `/api/health` - API健康检查
- `/get_optimizer_stats` - 优化器统计
- `/get_async_system_stats` - 异步系统统计

## 日志和输出

- **控制台输出**: 实时测试进度和关键指标
- **日志文件**: `logs/async_stress_test_YYYYMMDD_HHMMSS.log`
- **详细统计**: 响应时间、错误分布、性能趋势

## 故障排除

### 常见问题

1. **无法连接服务**
   ```
   ⚠️ 警告: 无法连接到服务
   ```
   - 检查ljwx-bigscreen服务是否运行
   - 确认端口配置正确（5225本地，5001 Docker）

2. **依赖包缺失**
   ```
   ❌ 缺少必要的依赖包
   ```
   - 运行 `pip3 install aiohttp`
   - 或使用启动脚本自动安装

3. **性能不达预期**
   ```
   ⚠️ QPS未达标，当前: 200, 目标: 500+
   ```
   - 检查系统资源使用情况
   - 确认异步处理器已正常启动
   - 查看系统统计接口状态

### 调试建议

1. 先运行快速验证测试确认基本功能
2. 检查异步系统统计接口是否返回正常数据
3. 从小规模测试开始，逐步增加并发数
4. 查看详细日志文件分析具体错误

## 示例输出

```
🚀 异步健康数据处理系统压力测试
==================================
🎯 目标: 测试1000台手表并发上传健康数据

📊 测试进度 - 总请求: 15420, 成功: 15398, 失败: 22, 
成功率: 99.9%, QPS: 514.2, 平均响应时间: 0.156s

📊 1000台手表并发压力测试报告
=====================================
⏱️  测试时长: 0:10:12
🚀 整体QPS: 514.25 请求/秒  
💪 处理能力: 30855 请求/分钟
✅ 成功率: 99.86%
⚡ 平均响应时间: 0.156秒
🎯 性能等级: 优秀
```

这套测试工具将帮助你全面验证异步健康数据处理系统的性能优化效果！
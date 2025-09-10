# Redis Stream 架构迁移完整指南

## 概述

本文档提供了 ljwx-bigscreen 系统从传统处理架构向 Redis Stream 架构迁移的完整指南。新架构能够将系统性能从 1,400 QPS 提升至 5,000+ QPS，并支持 10,000+ 并发设备。

## 🏗️ 架构对比

### 传统架构
```
Client → Flask API → 同步处理 → 数据库 → 响应
```

### Stream架构
```
Client → Flask API → Redis Stream → 异步消费者 → 批处理 → 数据库
                  ↓
               立即响应
```

## 📦 新增组件

### 1. 核心模块
- **`redis_stream_manager.py`** - Redis Stream 生产者和管理器
- **`stream_consumers.py`** - Stream 消费者和批处理逻辑
- **`stream_gradual_switch_manager.py`** - 灰度切换管理器
- **`stream_monitoring_dashboard.py`** - 监控仪表板
- **`stream_rollback_plan.py`** - 回滚预案管理器

### 2. 验证工具
- **`stream_validation_tool.py`** - 双写验证工具
- **`database_consistency_checker.py`** - 数据一致性检查器

## 🚀 部署步骤

### 阶段 1: 基础设施准备

#### 1.1 Redis 配置验证
```bash
# 检查 Redis 版本 (需要 5.0+)
redis-cli INFO | grep redis_version

# 检查 Stream 功能
redis-cli XADD test_stream * field1 value1
redis-cli XLEN test_stream
redis-cli DEL test_stream
```

#### 1.2 配置更新
确保 `config.py` 包含正确的 Redis 配置：
```python
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_PASSWORD = None  # 如果有密码
REDIS_DB = 0
```

### 阶段 2: 代码部署

#### 2.1 部署新模块
确保所有新增的 Python 模块已正确部署到 bigScreen 目录：
```bash
cd ljwx-bigscreen/bigscreen/bigScreen/
ls -la redis_stream_manager.py
ls -la stream_consumers.py
ls -la stream_gradual_switch_manager.py
ls -la stream_monitoring_dashboard.py
ls -la stream_rollback_plan.py
```

#### 2.2 重启应用
```bash
cd ljwx-bigscreen/bigscreen/bigScreen/
python run_bigscreen.py
```

启动成功后应该看到以下日志：
```
🌊 Redis Stream管理器已初始化
🔄 Stream消费者已启动
🎛️  灰度切换管理器已初始化
💾 迁移备份已创建: backup_xxxxx
🚀 Redis Stream系统初始化完成
📊 监控仪表板: http://localhost:5225/stream_monitor/
```

### 阶段 3: 系统验证

#### 3.1 访问监控仪表板
```bash
# 打开浏览器访问
http://localhost:5225/stream_monitor/
```

监控仪表板提供：
- 实时流量分配控制
- 系统健康监控
- Stream 指标展示
- 灰度切换计划管理

#### 3.2 基础功能测试
```bash
# 测试传统接口（默认配置）
curl -X POST http://localhost:5225/upload_health_data \
  -H "Content-Type: application/json" \
  -d '{"data":{"deviceSn":"TEST001","heart_rate":75,"timestamp":1640995200}}'

# 测试 Stream 接口
curl -X POST http://localhost:5225/upload_health_data_v2 \
  -H "Content-Type: application/json" \
  -d '{"data":{"deviceSn":"TEST001","heart_rate":75,"timestamp":1640995200}}'
```

#### 3.3 数据一致性验证
```python
# 在 Python 控制台中运行
from bigScreen.database_consistency_checker import DatabaseConsistencyChecker

checker = DatabaseConsistencyChecker()
result = checker.run_comprehensive_check(time_window_minutes=60)
print(f"一致性检查结果: {result}")
```

## 🔄 灰度切换流程

### 阶段 4: 逐步切换

#### 4.1 创建切换计划
通过监控仪表板或 API 创建切换计划：

```bash
curl -X POST http://localhost:5225/stream_monitor/api/create_switch_plan \
  -H "Content-Type: application/json" \
  -d '{
    "target_percentage": 100,
    "step_size": 10,
    "step_interval_minutes": 30,
    "auto_execute": false
  }'
```

#### 4.2 推荐切换时间表

**第一阶段 - 小流量验证 (1-3天)**
- 0% → 5% → 10%
- 观察时间：每步 2 小时
- 重点关注：错误率、数据一致性

**第二阶段 - 中等流量 (3-7天)**
- 10% → 30% → 50%
- 观察时间：每步 6-12 小时
- 重点关注：系统负载、处理延迟

**第三阶段 - 大流量切换 (7-14天)**
- 50% → 75% → 100%
- 观察时间：每步 24 小时
- 重点关注：峰值处理能力

#### 4.3 关键监控指标

**必须监控的指标：**
- 数据一致性率 > 99%
- 错误率 < 1%
- Stream 队列长度 < 1000
- 系统 CPU 使用率 < 80%
- 响应时间 < 3 秒

**告警阈值：**
- 数据一致性率 < 95% → 暂停切换
- 错误率 > 5% → 立即回滚
- 队列积压 > 5000 → 增加消费者
- CPU 使用率 > 90% → 暂停切换

## 📊 监控和管理

### 5.1 实时监控
访问 `http://localhost:5225/stream_monitor/` 可以：

- **流量控制**: 手动调整 Stream 处理百分比
- **健康监控**: 查看系统健康状态和关键指标
- **切换计划**: 创建和执行自动化切换计划
- **历史数据**: 查看切换历史和性能趋势

### 5.2 API 监控
```bash
# 获取系统状态
curl http://localhost:5225/stream_monitor/api/status

# 获取实时指标
curl http://localhost:5225/stream_monitor/api/metrics

# 手动切换流量
curl -X POST http://localhost:5225/stream_monitor/api/switch_traffic \
  -H "Content-Type: application/json" \
  -d '{"percentage": 20, "reason": "测试切换"}'
```

### 5.3 数据验证
```bash
# 运行数据一致性检查
curl http://localhost:5225/stream_monitor/api/validation/run_check

# 查看验证历史
curl http://localhost:5225/stream_monitor/api/validation/history
```

## 🚨 应急处理

### 6.1 紧急回滚

**通过监控仪表板：**
1. 访问 http://localhost:5225/stream_monitor/
2. 点击"紧急回滚"按钮
3. 输入回滚原因
4. 确认执行

**通过 API：**
```bash
curl -X POST http://localhost:5225/stream_monitor/api/emergency_rollback \
  -H "Content-Type: application/json" \
  -d '{"reason": "系统异常紧急回滚"}'
```

**手动回滚：**
```python
from bigScreen.stream_rollback_plan import get_rollback_plan

rollback_plan = get_rollback_plan()
result = rollback_plan.execute_rollback('immediate', '手动紧急回滚')
print(f"回滚结果: {result}")
```

### 6.2 常见问题处理

#### 问题 1: Stream 队列积压
**症状**: 队列长度持续增长
**处理**:
```bash
# 增加消费者实例
from bigScreen.stream_consumers import get_consumer_manager
manager = get_consumer_manager()
# 手动启动额外消费者...
```

#### 问题 2: 数据一致性异常
**症状**: 一致性率低于 95%
**处理**:
1. 暂停新流量切换
2. 运行数据修复工具
3. 分析不一致原因
4. 修复后重新验证

#### 问题 3: 系统过载
**症状**: CPU/内存使用率过高
**处理**:
1. 立即将流量切换到 0%
2. 检查消费者处理效率
3. 优化批处理大小
4. 增加系统资源

## 📋 切换检查清单

### 切换前检查
- [ ] Redis Stream 功能正常
- [ ] 所有新模块已部署
- [ ] 监控仪表板可访问
- [ ] 备份已创建
- [ ] 数据一致性验证工具正常
- [ ] 告警系统配置完成

### 切换中监控
- [ ] 数据一致性率 > 99%
- [ ] 错误率 < 1%
- [ ] Stream 队列长度正常
- [ ] 系统资源使用率正常
- [ ] 响应时间符合要求

### 切换后验证
- [ ] 所有功能正常工作
- [ ] 数据完整性验证通过
- [ ] 性能提升达到预期
- [ ] 用户体验无异常
- [ ] 监控告警正常

## 🔧 配置调优

### Redis 配置优化
```redis
# redis.conf 推荐配置
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000

# Stream 相关配置
stream-node-max-bytes 4096
stream-node-max-entries 100
```

### 消费者配置调优
```python
# 根据系统负载调整
BATCH_SIZE = 200          # 批处理大小
CONSUMER_COUNT = 3        # 消费者数量
PROCESSING_TIMEOUT = 30   # 处理超时时间
MAX_RETRIES = 3          # 最大重试次数
```

## 📈 性能期望

### 性能目标
- **QPS提升**: 1,400 → 5,000+
- **响应时间**: < 3 秒 (99th percentile)
- **并发支持**: 10,000+ 设备
- **数据一致性**: > 99.9%
- **系统可用性**: > 99.95%

### 压力测试
```bash
# 使用提供的性能测试工具
python stream_validation_tool.py
python database_consistency_checker.py
```

## 🎯 最佳实践

### 1. 监控建议
- 设置自动化监控告警
- 定期运行一致性检查
- 保持切换历史记录
- 监控关键业务指标

### 2. 维护建议
- 定期清理过期 Stream 数据
- 监控 Redis 内存使用
- 定期备份配置和数据
- 保持系统资源充足

### 3. 安全建议
- 限制监控面板访问
- 配置 Redis 访问控制
- 记录所有切换操作
- 定期更新安全补丁

## 📞 支持联系

如果在迁移过程中遇到问题，请联系技术支持团队，并提供：
- 错误日志信息
- 监控仪表板截图
- 系统配置信息
- 问题复现步骤

---

**重要提醒**: 
1. 在生产环境实施前，请在测试环境完整验证
2. 确保有完整的回滚预案
3. 建议在业务低峰期进行切换
4. 保持技术支持团队待命
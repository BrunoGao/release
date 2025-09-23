# ljwx-boot 健康数据上传接口性能测试方案

## 测试目标
对 `/health/upload` 接口进行全面性能测试，识别性能瓶颈并提供优化建议。

## 测试场景设计

### 场景1: 基线性能测试 (Baseline Test)
**目的**: 建立性能基线，了解系统基本响应能力
- **并发用户数**: 10
- **持续时间**: 5分钟
- **Ramp-up时间**: 30秒
- **循环次数**: 10次/用户
- **预期响应时间**: < 500ms
- **预期吞吐量**: > 20 TPS

### 场景2: 负载测试 (Load Test)
**目的**: 模拟正常业务负载，验证系统稳定性
- **并发用户数**: 100
- **持续时间**: 10分钟
- **Ramp-up时间**: 60秒
- **循环次数**: 50次/用户
- **预期响应时间**: < 1000ms
- **预期成功率**: > 95%
- **预期吞吐量**: > 100 TPS

### 场景3: 压力测试 (Stress Test)
**目的**: 找到系统性能极限点
- **并发用户数**: 500
- **持续时间**: 15分钟
- **Ramp-up时间**: 120秒
- **循环次数**: 20次/用户
- **关注指标**: 响应时间、错误率、系统资源使用率

### 场景4: 峰值测试 (Spike Test)
**目的**: 测试系统突发流量处理能力
- **并发用户数**: 从50瞬间增加到1000
- **持续时间**: 5分钟峰值 + 5分钟恢复
- **关注指标**: 系统恢复能力、错误率

### 场景5: 容量测试 (Volume Test)
**目的**: 测试大数据量处理能力
- **数据特征**: 
  - 基础JSON: 1KB
  - 包含复杂嵌套数据: 2-3KB
  - 测试不同数据大小的影响
- **并发用户数**: 200
- **持续时间**: 20分钟

## 数据变化策略

### 动态数据生成
1. **设备标识随机化**
   - deviceSn: 使用线程号+随机数
   - userId: 动态生成用户ID
   - customerId/orgId: 保持固定（模拟同租户）

2. **健康数据随机化**
   - heart_rate: 60-100 bpm
   - blood_oxygen: 95-100%
   - body_temperature: 36.0-37.5°C
   - step: 5000-15000步
   - blood_pressure: 110-140/70-90 mmHg
   - stress: 30-80

3. **时间戳动态化**
   - timestamp: 当前时间
   - 历史数据时间戳: 相对偏移

4. **复杂数据结构**
   - sleepData: 动态睡眠时间段
   - exerciseData: 变化的运动数据
   - workoutData: 随机锻炼记录

## 性能指标监控

### 响应时间指标
- **平均响应时间** (Average Response Time)
- **90%分位数响应时间** (90th Percentile)
- **95%分位数响应时间** (95th Percentile)  
- **99%分位数响应时间** (99th Percentile)
- **最大响应时间** (Max Response Time)

### 吞吐量指标
- **每秒事务数** (TPS - Transactions Per Second)
- **每秒请求数** (RPS - Requests Per Second)
- **每分钟处理数据量** (MB/min)

### 错误率指标
- **错误百分比** (Error %)
- **HTTP状态码分布**
- **超时请求数**
- **连接失败数**

### 系统资源指标
- **CPU使用率**
- **内存使用率**
- **磁盘I/O**
- **网络I/O**
- **数据库连接数**
- **JVM堆内存使用**

## 测试环境要求

### JMeter配置
```bash
# JVM参数优化
export HEAP="-Xms1g -Xmx1g -XX:MaxMetaspaceSize=256m"
export JVM_ARGS="-server -XX:+UseG1GC -XX:MaxGCPauseMillis=100"

# 启动JMeter
jmeter -n -t health-upload-test.jmx -l results.jtl -e -o dashboard/
```

### 服务器监控
1. **应用层监控**
   ```bash
   # JVM监控
   jstat -gc [PID] 1s
   jmap -histo [PID]
   
   # 应用指标
   curl http://localhost:8080/actuator/metrics
   ```

2. **系统监控**
   ```bash
   # CPU和内存
   top -p [PID]
   htop
   
   # 磁盘I/O
   iotop -p [PID]
   
   # 网络监控
   netstat -tulpn | grep 8080
   ss -tulpn | grep 8080
   ```

3. **数据库监控**
   ```sql
   -- MySQL性能监控
   SHOW PROCESSLIST;
   SHOW STATUS LIKE 'Threads%';
   SHOW STATUS LIKE 'Connections';
   SHOW STATUS LIKE 'Slow_queries';
   ```

## 预期性能基准

### 健康数据上传接口基准
| 场景 | 并发数 | 平均响应时间 | 95%响应时间 | TPS | 错误率 |
|------|--------|--------------|-------------|-----|--------|
| 基线测试 | 10 | <500ms | <800ms | >20 | <1% |
| 负载测试 | 100 | <1000ms | <2000ms | >100 | <2% |
| 压力测试 | 500 | <3000ms | <5000ms | >200 | <5% |

### 系统资源使用基准
| 资源 | 正常负载 | 高负载 | 告警阈值 |
|------|----------|--------|----------|
| CPU | <50% | <80% | >90% |
| 内存 | <60% | <80% | >90% |
| 数据库连接 | <20 | <50 | >80 |
| 响应时间 | <1s | <3s | >5s |

## 测试执行步骤

### 1. 环境准备
```bash
# 创建测试目录
mkdir -p performance-test/results
cd performance-test

# 启动被测服务
cd ljwx-boot
./run-local.sh start

# 验证服务状态
curl http://localhost:8080/actuator/health
```

### 2. 基线测试
```bash
# 执行基线测试
jmeter -n -t health-upload-test.jmx -l results/baseline.jtl

# 生成报告
jmeter -g results/baseline.jtl -o results/baseline-dashboard/
```

### 3. 负载测试
```bash
# 启用负载测试场景
# 在JMX文件中启用 "2. Load Test" ThreadGroup

jmeter -n -t health-upload-test.jmx -l results/load-test.jtl
jmeter -g results/load-test.jtl -o results/load-test-dashboard/
```

### 4. 压力测试
```bash
# 启用压力测试场景  
# 在JMX文件中启用 "3. Stress Test" ThreadGroup

jmeter -n -t health-upload-test.jmx -l results/stress-test.jtl
jmeter -g results/stress-test.jtl -o results/stress-test-dashboard/
```

## 故障排查清单

### 常见性能问题
1. **响应时间过长**
   - 检查数据库查询性能
   - 检查JSON解析性能
   - 检查网络延迟
   - 检查GC频率

2. **吞吐量不足**
   - 检查线程池配置
   - 检查数据库连接池
   - 检查CPU/内存资源
   - 检查磁盘I/O

3. **错误率过高**
   - 检查异常日志
   - 检查数据库连接
   - 检查内存溢出
   - 检查超时配置

### 监控命令速查
```bash
# 快速性能检查
./performance-check.sh [PID]

# 详细性能报告
./performance-report.sh [duration_minutes]

# 实时监控
watch -n 1 'curl -s http://localhost:8080/actuator/metrics/jvm.memory.used | jq .'
```
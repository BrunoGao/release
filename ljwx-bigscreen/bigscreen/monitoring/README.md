# ljwx-bigscreen 监控系统

完整的监控和告警系统，包括 Prometheus、Loki、Grafana 和 Alertmanager。

## 📋 系统组件

| 组件 | 端口 | 功能 | 访问地址 |
|------|------|------|----------|
| Prometheus | 9091 | 指标采集和存储 | http://localhost:9091 |
| Alertmanager | 9094 | 告警管理和分发 | http://localhost:9094 |
| Loki | 3100 | 日志聚合 | http://localhost:3100 |
| Promtail | 9080 | 日志采集 | - |
| Grafana | 3001 | 可视化面板 | http://localhost:3001 |
| Node Exporter | 9101 | 系统指标导出 | http://localhost:9101 |

## 🔐 系统凭证

### 监控系统

**Grafana**
- URL: http://localhost:3001
- 用户名: `admin`
- 密码: `admin123`
- 说明: 首次登录后可以修改密码

**Prometheus**
- URL: http://localhost:9091
- 认证: 无需登录（仅内网访问）

**Alertmanager**
- URL: http://localhost:9094
- 认证: 无需登录（仅内网访问）

**Loki**
- URL: http://localhost:3100
- 认证: 无需登录（仅内网访问）

### ljwx-bigscreen 应用

**Web界面**
- URL: http://localhost:5225 或 http://192.168.1.83:5225
- 认证: 根据组织配置（使用企业微信或用户名密码登录）

**指标端点**
- URL: http://localhost:5225/metrics
- 认证: 无需认证（供Prometheus采集）

### 数据库连接信息

**MySQL**
- 主机: 127.0.0.1
- 端口: 3306
- 数据库: test
- 用户名: root
- 密码: 123456
- 说明: ljwx-bigscreen后端数据库

**Redis**
- 主机: 127.0.0.1 或 192.168.1.6
- 端口: 6379
- 密码: (无密码)
- 说明: 缓存和实时数据

### 企业微信配置

**应用凭证** (配置在环境变量中)
- AppID: `WECHAT_APP_ID`
- AppSecret: `WECHAT_APP_SECRET`
- 说明: 用于告警通知和用户认证

### Docker Registry (如需要)

**Aliyun容器镜像服务**
- Registry: registry.cn-hangzhou.aliyuncs.com/your-namespace
- 用户名: 阿里云账号
- 密码: 访问凭证
- 说明: 多架构镜像仓库

### 安全建议

⚠️ **重要提示**:
1. **生产环境**: 务必修改所有默认密码
2. **Grafana**: 首次登录后立即修改admin密码
3. **MySQL**: 为生产环境创建独立用户，限制权限
4. **Redis**: 生产环境启用密码认证
5. **网络隔离**: 监控服务仅在内网访问，禁止公网暴露
6. **企业微信**: 妥善保管AppSecret，不要提交到代码仓库
7. **定期更新**: 定期轮换数据库密码和API密钥

## 🚀 快速开始

### 1. 启动监控系统

```bash
cd monitoring
docker-compose up -d
```

### 2. 验证服务状态

```bash
# 查看所有服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f
```

### 3. 访问各个服务

**Grafana 仪表板**
- URL: http://localhost:3001
- 登录凭证: 见上方"系统凭证"章节
- 功能: 可视化面板、数据源管理、告警配置

**Prometheus**
- URL: http://localhost:9091
- 查看指标: http://localhost:9091/graph
- 查看告警: http://localhost:9091/alerts
- 查看采集目标: http://localhost:9091/targets

**Alertmanager**
- URL: http://localhost:9094
- 查看告警: http://localhost:9094/#/alerts
- 查看配置: http://localhost:9094/#/status

**Loki**
- URL: http://localhost:3100
- 通过Grafana Explore访问: http://localhost:3001/explore

## 📊 Grafana 配置

### 预配置的数据源

系统会自动配置以下数据源：
1. **Prometheus** - 指标数据
2. **Loki** - 日志数据

### 预装的仪表板

1. **ljwx-bigscreen 综合监控**
   - 健康数据上传统计
   - API性能监控
   - 告警趋势分析
   - 消息发送统计
   - 系统资源使用

### 创建自定义仪表板

1. 登录 Grafana (http://localhost:3001)
2. 点击 "+" → "Dashboard"
3. 添加面板并选择数据源
4. 配置查询和可视化选项
5. 保存仪表板

## 🔔 告警配置

### Alertmanager 告警路由

告警会根据严重程度和服务类型自动路由：

- **critical** - 严重告警，立即发送
- **warning** - 警告告警，2小时重复间隔
- **bigscreen-team** - bigscreen服务特定告警
- **database-team** - 数据库相关告警

### 配置告警接收器

编辑 `alertmanager/alertmanager.yml`:

```yaml
receivers:
  - name: 'your-receiver'
    webhook_configs:
      - url: 'http://your-webhook-url'
    # 或者配置邮件
    email_configs:
      - to: 'alert@example.com'
    # 或者企业微信
    wechat_configs:
      - corp_id: 'your-corp-id'
        agent_id: 'your-agent-id'
```

重新加载配置:
```bash
docker-compose restart alertmanager
```

### 告警规则

告警规则定义在 `prometheus/alerts.yml`，包括：

**应用告警**
- BigscreenServiceDown - 服务不可用
- HealthDataUploadRateLow - 数据上传速率低
- HealthDataUploadFailureRateHigh - 上传失败率高
- APIResponseTimeSlow - API响应慢
- AlertGenerationRateHigh - 告警生成率异常

**系统告警**
- HighCPUUsage - CPU使用率高
- HighMemoryUsage - 内存使用率高
- DiskSpaceLow - 磁盘空间不足

**数据库告警**
- MySQLDown - MySQL服务不可用
- MySQLConnectionsHigh - 连接数过高
- RedisDown - Redis服务不可用
- RedisMemoryHigh - Redis内存使用率高

## 📈 指标说明

### ljwx-bigscreen 应用指标

#### 健康数据指标
- `bigscreen_health_data_upload_total` - 健康数据上传总数
- `bigscreen_health_data_upload_failed_total` - 上传失败总数
- `bigscreen_health_data_processing_duration_seconds` - 处理时间

#### API指标
- `bigscreen_api_requests_total` - API请求总数
- `bigscreen_api_request_duration_seconds` - API响应时间
- `bigscreen_api_requests_in_progress` - 正在处理的请求数

#### 告警指标
- `bigscreen_alerts_generated_total` - 告警生成总数
- `bigscreen_alerts_sent_total` - 告警发送总数
- `bigscreen_active_alerts` - 活跃告警数

#### 消息指标
- `bigscreen_messages_sent_total` - 消息发送总数
- `bigscreen_messages_failed_total` - 消息失败总数
- `bigscreen_unread_messages` - 未读消息数

#### 数据库指标
- `bigscreen_db_connection_pool_usage` - 连接池使用率
- `bigscreen_db_queries_total` - 查询总数
- `bigscreen_db_query_duration_seconds` - 查询时间

#### Redis指标
- `bigscreen_redis_connection_errors_total` - 连接错误数
- `bigscreen_redis_operations_total` - 操作总数
- `bigscreen_redis_cache_hits_total` - 缓存命中数

### 查询示例

在 Prometheus 或 Grafana 中使用这些查询：

```promql
# 健康数据上传速率
rate(bigscreen_health_data_upload_total[5m])

# API P95响应时间
histogram_quantile(0.95, rate(bigscreen_api_request_duration_seconds_bucket[5m]))

# 告警生成速率
rate(bigscreen_alerts_generated_total[5m])

# 数据库查询延迟
histogram_quantile(0.99, rate(bigscreen_db_query_duration_seconds_bucket[5m]))

# Redis缓存命中率
rate(bigscreen_redis_cache_hits_total[5m])
/
(rate(bigscreen_redis_cache_hits_total[5m]) + rate(bigscreen_redis_cache_misses_total[5m]))
```

## 🔍 日志查询

### 在 Grafana Explore 中查询日志

访问 Grafana → Explore → 选择 Loki 数据源

```logql
# 查看所有bigscreen日志
{job="bigscreen"}

# 查看错误日志
{job="bigscreen"} |= "ERROR"

# 查看API相关日志
{job="bigscreen", module="api"}

# 查看特定时间范围的告警日志
{job="bigscreen"} |= "alert" | json | line_format "{{.timestamp}} {{.level}} {{.message}}"

# 统计错误频率
sum(rate({job="bigscreen"} |= "ERROR" [5m])) by (level)
```

## 🛠️ 维护和管理

### 停止服务

```bash
docker-compose down
```

### 停止并清除数据

```bash
docker-compose down -v
```

### 重启特定服务

```bash
docker-compose restart prometheus
docker-compose restart grafana
```

### 查看服务日志

```bash
# 查看所有日志
docker-compose logs

# 查看特定服务日志
docker-compose logs -f prometheus
docker-compose logs -f grafana
docker-compose logs -f alertmanager
```

### 更新配置

修改配置文件后，重新加载：

```bash
# Prometheus热重载
curl -X POST http://localhost:9091/-/reload

# Alertmanager热重载
curl -X POST http://localhost:9094/-/reload

# 其他服务需要重启
docker-compose restart loki
docker-compose restart grafana
```

## 📦 数据持久化

以下数据会持久化保存：
- Prometheus数据: `prometheus_data` volume
- Grafana配置和仪表板: `grafana_data` volume
- Loki日志数据: `loki_data` volume
- Alertmanager配置: `alertmanager_data` volume

## 🔧 故障排除

### 1. 服务无法启动

检查端口是否被占用：
```bash
lsof -i :9091  # Prometheus
lsof -i :3001  # Grafana
lsof -i :9094  # Alertmanager
```

### 2. Prometheus 无法采集指标

- 检查 ljwx-bigscreen 是否运行: `curl http://localhost:5225/metrics`
- 检查网络连接: `docker-compose exec prometheus ping host.docker.internal`
- 查看 Prometheus targets: http://localhost:9091/targets

### 3. Grafana 无法连接数据源

- 检查数据源配置: Grafana → Configuration → Data Sources
- 测试连接: 点击 "Test" 按钮
- 查看日志: `docker-compose logs grafana`

### 4. Alertmanager 未收到告警

- 检查 Prometheus 告警规则: http://localhost:9091/alerts
- 检查 Alertmanager 配置: http://localhost:9094/#/status
- 查看路由匹配: http://localhost:9094/#/alerts

## 📚 参考文档

- [Prometheus文档](https://prometheus.io/docs/)
- [Grafana文档](https://grafana.com/docs/)
- [Loki文档](https://grafana.com/docs/loki/latest/)
- [Alertmanager文档](https://prometheus.io/docs/alerting/latest/alertmanager/)

## 🆘 常见问题

**Q: 如何添加新的监控指标？**

A: 在 `bigScreen/prometheus_metrics.py` 中定义新的指标，然后在相关代码中记录。

**Q: 如何添加新的告警规则？**

A: 编辑 `prometheus/alerts.yml`，添加新的规则，然后重新加载配置。

**Q: 如何导出/备份Grafana仪表板？**

A: Grafana → Dashboard → Settings → JSON Model → 复制JSON。

**Q: 日志数据保留多久？**

A: Loki默认保留30天，可在 `loki/loki-config.yml` 中修改。

## 📞 技术支持

如有问题，请查看:
- 系统日志: `docker-compose logs`
- ljwx-bigscreen日志: `/tmp/bigscreen.log`
- Prometheus状态: http://localhost:9091/status

# API网关统一架构优化方案

## 方案概述

基于您的建议，将配置服务、认证和License管理统一到API网关层，这是一个更加优雅和可扩展的架构设计。API网关作为统一入口，不仅简化了服务间的通信复杂度，也为后续的水平扩展提供了更好的基础。

## 优化后的架构设计

### 1. 整体架构图

```mermaid
graph TB
    subgraph "设备层"
        A[ljwx-watch] --> B[ljwx-phone] 
        A --> C[IoT设备集群]
    end
    
    subgraph "API网关层 (统一入口)"
        D[API Gateway]
        E[认证服务模块]
        F[配置管理模块]
        G[License管理模块]
        H[负载均衡模块]
        I[限流熔断模块]
        J[监控统计模块]
    end
    
    subgraph "业务服务层"
        K[ljwx-boot-cluster]
        L[FastAPI-AI-cluster]
        M[大屏展示服务]
        N[报表服务集群]
    end
    
    subgraph "基础设施层"
        O[Redis Cluster]
        P[MySQL Master-Slave]
        Q[RabbitMQ Cluster]
        R[Elasticsearch]
    end
    
    A --> D
    B --> D
    C --> D
    
    D --> E
    D --> F
    D --> G
    D --> H
    D --> I
    D --> J
    
    H --> K
    H --> L
    H --> M
    H --> N
    
    E --> O
    F --> O
    G --> O
    
    K --> P
    K --> Q
    L --> P
    L --> Q
```

### 2. API网关核心优势

| 架构层面 | 传统方案 | 网关方案 | 优势说明 |
|----------|----------|----------|----------|
| **服务发现** | 硬编码服务地址 | 动态服务注册发现 | 自动故障转移，零停机更新 |
| **认证管理** | 分散在各服务 | 网关统一认证 | 一次认证，全局有效 |
| **配置管理** | 多点配置同步 | 网关统一配置 | 配置一致性，实时生效 |
| **License管理** | 各服务独立检查 | 网关统一验证 | 集中控制，精确计费 |
| **水平扩展** | 手动扩缩容 | 自动弹性扩缩 | 根据流量自动调节 |
| **监控统计** | 分散监控 | 网关统一监控 | 全链路可观测性 |

## 核心实现方案

### 1. API网关选型与配置

**推荐方案：Kong + Spring Cloud Gateway混合架构**

#### 1.1 Kong作为边缘网关

```yaml
# kong.yml
_format_version: "3.0"
_transform: true

services:
  - name: ljwx-health-service
    url: http://ljwx-boot-service
    plugins:
      - name: rate-limiting
        config:
          minute: 5000
          hour: 50000
      - name: prometheus
        config:
          per_consumer: true

  - name: ljwx-ai-service
    url: http://ai-analysis-service
    plugins:
      - name: rate-limiting
        config:
          minute: 1000
          hour: 10000

routes:
  - name: device-config-route
    service: ljwx-health-service
    paths:
      - /api/config
    plugins:
      - name: ljwx-auth
      - name: ljwx-license-check

  - name: health-upload-route
    service: ljwx-health-service
    paths:
      - /api/stream
    plugins:
      - name: ljwx-auth
      - name: ljwx-license-check
      - name: request-transformer
        config:
          add:
            headers:
              - "X-Customer-ID:$(headers.x-customer-id)"
              - "X-Org-ID:$(headers.x-org-id)"

  - name: ai-analysis-route
    service: ljwx-ai-service
    paths:
      - /ai
    plugins:
      - name: ljwx-auth
      - name: cors
```

#### 1.2 自定义Kong插件实现

```lua
-- kong/plugins/ljwx-auth/handler.lua
local BasePlugin = require "kong.plugins.base_plugin"
local jwt = require "resty.jwt"
local redis = require "resty.redis"

local LjwxAuthHandler = BasePlugin:extend()

LjwxAuthHandler.PRIORITY = 1000
LjwxAuthHandler.VERSION = "1.0.0"

function LjwxAuthHandler:access(config)
  LjwxAuthHandler.super.access(self)
  
  local auth_header = kong.request.get_header("authorization")
  if not auth_header then
    return kong.response.exit(401, {message = "Missing authorization header"})
  end
  
  -- 提取JWT token
  local token = string.match(auth_header, "Bearer%s+(.+)")
  if not token then
    return kong.response.exit(401, {message = "Invalid authorization format"})
  end
  
  -- 验证JWT token
  local jwt_obj = jwt:verify(config.secret, token)
  if not jwt_obj.valid then
    return kong.response.exit(401, {message = "Invalid token"})
  end
  
  -- 从Redis获取设备配置信息
  local red = redis:new()
  red:set_timeout(1000)
  
  local ok, err = red:connect(config.redis_host, config.redis_port)
  if not ok then
    kong.log.err("Failed to connect to Redis: ", err)
    return kong.response.exit(500, {message = "Internal server error"})
  end
  
  if config.redis_password then
    local res, err = red:auth(config.redis_password)
    if not res then
      kong.log.err("Failed to authenticate with Redis: ", err)
      return kong.response.exit(500, {message = "Internal server error"})
    end
  end
  
  local device_sn = jwt_obj.payload.device_sn
  local cache_key = "device_config:" .. device_sn
  local device_config, err = red:get(cache_key)
  
  if device_config == ngx.null then
    -- 从数据库获取配置并缓存
    device_config = fetch_device_config_from_db(device_sn, config)
    if device_config then
      red:setex(cache_key, 300, device_config) -- 5分钟缓存
    else
      return kong.response.exit(404, {message = "Device not found"})
    end
  end
  
  -- 设置请求头，传递给后端服务
  kong.service.request.set_header("X-Device-SN", device_sn)
  kong.service.request.set_header("X-Customer-ID", jwt_obj.payload.customer_id)
  kong.service.request.set_header("X-Org-ID", jwt_obj.payload.org_id)
  kong.service.request.set_header("X-User-ID", jwt_obj.payload.user_id)
  kong.service.request.set_header("X-Device-Config", device_config)
  
  red:close()
end

return LjwxAuthHandler
```

```lua
-- kong/plugins/ljwx-license-check/handler.lua
local BasePlugin = require "kong.plugins.base_plugin"
local redis = require "resty.redis"

local LjwxLicenseHandler = BasePlugin:extend()

LjwxLicenseHandler.PRIORITY = 999
LjwxLicenseHandler.VERSION = "1.0.0"

function LjwxLicenseHandler:access(config)
  LjwxLicenseHandler.super.access(self)
  
  local customer_id = kong.request.get_header("X-Customer-ID")
  if not customer_id then
    return kong.response.exit(400, {message = "Customer ID required"})
  end
  
  -- 连接Redis检查License状态
  local red = redis:new()
  red:set_timeout(1000)
  
  local ok, err = red:connect(config.redis_host, config.redis_port)
  if not ok then
    return kong.response.exit(500, {message = "License check failed"})
  end
  
  if config.redis_password then
    red:auth(config.redis_password)
  end
  
  -- 检查License有效性
  local license_key = "license:" .. customer_id
  local license_info, err = red:hmget(license_key, 
    "status", "device_limit", "current_devices", "expire_time")
  
  if not license_info or license_info[1] == ngx.null then
    return kong.response.exit(403, {message = "Invalid license"})
  end
  
  local status = license_info[1]
  local device_limit = tonumber(license_info[2]) or 0
  local current_devices = tonumber(license_info[3]) or 0
  local expire_time = tonumber(license_info[4]) or 0
  
  -- 检查License状态
  if status ~= "active" then
    return kong.response.exit(403, {message = "License inactive"})
  end
  
  -- 检查过期时间
  if expire_time > 0 and expire_time < ngx.time() then
    return kong.response.exit(403, {message = "License expired"})
  end
  
  -- 检查设备数量限制
  if device_limit > 0 and current_devices >= device_limit then
    return kong.response.exit(429, {message = "Device limit exceeded"})
  end
  
  -- 设置License信息到请求头
  kong.service.request.set_header("X-License-Status", status)
  kong.service.request.set_header("X-Device-Limit", tostring(device_limit))
  kong.service.request.set_header("X-Current-Devices", tostring(current_devices))
  
  red:close()
end

return LjwxLicenseHandler
```

### 2. 配置服务网关化实现

```javascript
// Gateway配置服务模块 - Node.js实现
const express = require('express');
const Redis = require('ioredis');
const mysql = require('mysql2/promise');

class GatewayConfigService {
  constructor() {
    this.redis = new Redis({
      host: 'redis-cluster',
      port: 6379,
      password: '123456',
      db: 1,
      retryDelayOnFailover: 100,
      maxRetriesPerRequest: 3
    });
    
    this.dbPool = mysql.createPool({
      host: 'mysql-master',
      user: 'root',
      password: '123456',
      database: 'test',
      connectionLimit: 20,
      acquireTimeout: 60000,
      timeout: 60000
    });
    
    this.app = express();
    this.setupRoutes();
  }
  
  setupRoutes() {
    // 设备配置获取接口 - 兼容ljwx-watch原有调用
    this.app.get('/api/config/device/:deviceSn', async (req, res) => {
      try {
        const { deviceSn } = req.params;
        const config = await this.getDeviceConfig(deviceSn);
        
        if (!config) {
          return res.status(404).json({
            success: false,
            error: 'Device not found'
          });
        }
        
        // 返回ljwx-bigscreen兼容格式
        res.json(config);
      } catch (error) {
        console.error('配置获取失败:', error);
        res.status(500).json({
          success: false,
          error: error.message
        });
      }
    });
    
    // 批量配置更新接口
    this.app.post('/api/config/batch-update', async (req, res) => {
      try {
        const { configs } = req.body;
        const results = await this.batchUpdateConfigs(configs);
        res.json({ success: true, results });
      } catch (error) {
        res.status(500).json({ success: false, error: error.message });
      }
    });
    
    // 配置热更新接口
    this.app.post('/api/config/reload/:customerId', async (req, res) => {
      try {
        const { customerId } = req.params;
        await this.reloadCustomerConfig(customerId);
        res.json({ success: true, message: 'Config reloaded' });
      } catch (error) {
        res.status(500).json({ success: false, error: error.message });
      }
    });
  }
  
  async getDeviceConfig(deviceSn) {
    // 1. 先从Redis缓存获取
    const cacheKey = `device_config:${deviceSn}`;
    const cached = await this.redis.get(cacheKey);
    
    if (cached) {
      return JSON.parse(cached);
    }
    
    // 2. 从数据库获取
    const [rows] = await this.dbPool.execute(`
      SELECT 
        u.id as user_id,
        u.device_sn,
        uo.org_id,
        ou.ancestors,
        cc.customer_name,
        cc.upload_method,
        cc.is_support_license,
        cc.license_key,
        cc.enable_resume,
        cc.upload_retry_count,
        cc.cache_max_count,
        cc.upload_retry_interval
      FROM sys_user u
      LEFT JOIN sys_user_org uo ON u.id = uo.user_id
      LEFT JOIN sys_org_units ou ON uo.org_id = ou.id  
      LEFT JOIN t_customer_config cc ON SUBSTRING_INDEX(SUBSTRING_INDEX(ou.ancestors, ',', 2), ',', -1) = cc.id
      WHERE u.device_sn = ? AND u.is_deleted = 0
      LIMIT 1
    `, [deviceSn]);
    
    if (rows.length === 0) {
      return null;
    }
    
    const deviceInfo = rows[0];
    
    // 解析customer_id从ancestors
    let customerId = '0';
    if (deviceInfo.ancestors) {
      const parts = deviceInfo.ancestors.split(',');
      if (parts.length >= 2 && parts[0] === '0') {
        customerId = parts[1];
      }
    }
    
    // 获取健康数据配置
    const [healthConfigs] = await this.dbPool.execute(`
      SELECT data_type, frequency_interval, is_enabled, is_realtime, 
             warning_high, warning_low, warning_cnt
      FROM t_health_data_config 
      WHERE customer_id = ? AND is_enabled = 1
    `, [customerId]);
    
    // 获取接口配置
    const [interfaceConfigs] = await this.dbPool.execute(`
      SELECT name, url, call_interval, is_enabled, api_id, api_auth
      FROM t_interface 
      WHERE customer_id = ?
    `, [customerId]);
    
    // 构建配置对象 - 兼容ljwx-bigscreen格式
    const config = {
      customer_id: customerId,
      org_id: deviceInfo.org_id,
      user_id: deviceInfo.user_id,
      customer_name: deviceInfo.customer_name,
      upload_method: deviceInfo.upload_method || 'wifi',
      enable_resume: deviceInfo.enable_resume || false,
      upload_retry_count: deviceInfo.upload_retry_count || 3,
      cache_max_count: deviceInfo.cache_max_count || 100,
      upload_retry_interval: deviceInfo.upload_retry_interval || 5,
      is_support_license: deviceInfo.is_support_license || false,
      license_key: deviceInfo.license_key,
      
      // 健康数据配置
      health_data: {},
      
      // 接口配置 - 动态指向网关地址
      interface_data: {}
    };
    
    // 处理健康数据配置
    healthConfigs.forEach(hc => {
      config.health_data[hc.data_type] = 
        `${hc.frequency_interval}:${hc.is_enabled}:${hc.is_realtime}:` +
        `${hc.warning_high || -1}:${hc.warning_low || -1}:${hc.warning_cnt || -1}`;
    });
    
    // 处理接口配置 - 统一指向网关
    const gatewayHost = process.env.GATEWAY_HOST || 'api-gateway:8080';
    config.interface_data = {
      'upload_health_data': `http://${gatewayHost}/api/stream/batch_upload`,
      'upload_device_info': `http://${gatewayHost}/api/stream/device_info`,
      'upload_common_event': `http://${gatewayHost}/api/stream/common_event`,
      'fetch_message': `http://${gatewayHost}/api/messages/device`
    };
    
    // 缓存配置5分钟
    await this.redis.setex(cacheKey, 300, JSON.stringify(config));
    
    return config;
  }
  
  async batchUpdateConfigs(configs) {
    const results = [];
    
    for (const config of configs) {
      try {
        // 更新数据库
        await this.updateConfigInDB(config);
        
        // 清除相关缓存
        await this.clearConfigCache(config);
        
        results.push({ id: config.id, success: true });
      } catch (error) {
        results.push({ id: config.id, success: false, error: error.message });
      }
    }
    
    return results;
  }
  
  async reloadCustomerConfig(customerId) {
    // 清除客户相关的所有配置缓存
    const pattern = `device_config:*customer_${customerId}*`;
    const keys = await this.redis.keys(pattern);
    
    if (keys.length > 0) {
      await this.redis.del(...keys);
    }
    
    // 发送配置重载通知给后端服务
    await this.redis.publish('config_reload', JSON.stringify({
      customer_id: customerId,
      timestamp: Date.now()
    }));
  }
}

module.exports = GatewayConfigService;
```

### 3. 水平扩展优化设计

#### 3.1 服务发现与注册

```yaml
# docker-compose.gateway.yml
version: '3.8'
services:
  consul:
    image: consul:1.15
    ports:
      - "8500:8500"
    environment:
      - CONSUL_BIND_INTERFACE=eth0
    command: agent -server -ui -node=server-1 -bootstrap-expect=1 -client=0.0.0.0

  api-gateway:
    image: kong:3.4
    ports:
      - "8080:8000"
      - "8443:8443"
      - "8001:8001"
      - "8444:8444"
    environment:
      - KONG_DATABASE=postgres
      - KONG_PG_HOST=postgres
      - KONG_PG_DATABASE=kong
      - KONG_PG_USER=kong
      - KONG_PG_PASSWORD=kong123
      - KONG_PROXY_ACCESS_LOG=/dev/stdout
      - KONG_ADMIN_ACCESS_LOG=/dev/stdout
      - KONG_PROXY_ERROR_LOG=/dev/stderr
      - KONG_ADMIN_ERROR_LOG=/dev/stderr
      - KONG_ADMIN_LISTEN=0.0.0.0:8001
      - KONG_PLUGINS=bundled,ljwx-auth,ljwx-license-check
    depends_on:
      - postgres
      - consul
    volumes:
      - ./kong/plugins:/usr/local/share/lua/5.1/kong/plugins

  gateway-config-service:
    build: ./gateway-config-service
    ports:
      - "3001:3001"
    environment:
      - REDIS_HOST=redis-cluster
      - REDIS_PASSWORD=123456
      - MYSQL_HOST=mysql-master
      - MYSQL_PASSWORD=123456
      - CONSUL_HOST=consul
      - CONSUL_PORT=8500
    depends_on:
      - consul
      - redis-cluster
      - mysql-master
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  # ljwx-boot服务集群
  ljwx-boot:
    build: ./ljwx-boot
    environment:
      - CONSUL_HOST=consul
      - CONSUL_PORT=8500
      - REDIS_URL=redis://default:123456@redis-cluster:6379/1
      - MYSQL_URL=jdbc:mysql://mysql-master:3306/test
    depends_on:
      - consul
      - redis-cluster
      - mysql-master
    deploy:
      replicas: 5
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
      update_config:
        parallelism: 2
        delay: 30s
        failure_action: rollback

  # FastAPI AI服务集群  
  ai-analysis-service:
    build: ./ai-analysis-service
    environment:
      - CONSUL_HOST=consul
      - CONSUL_PORT=8500
      - REDIS_URL=redis://default:123456@redis-cluster:6379/1
    depends_on:
      - consul
      - redis-cluster
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '4.0'
          memory: 4G
        reservations:
          cpus: '2.0'
          memory: 2G
```

#### 3.2 自动扩缩容配置

```yaml
# k8s/hpa.yml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ljwx-boot-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ljwx-boot
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
      - type: Pods
        value: 4
        periodSeconds: 60

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ai-analysis-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ai-analysis-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 80
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 85

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: gateway-config-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: gateway-config-service
  minReplicas: 2
  maxReplicas: 8
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 60
```

### 4. 监控与可观测性

#### 4.1 网关层监控配置

```yaml
# prometheus/kong.yml
- job_name: 'kong-gateway'
  static_configs:
    - targets: ['api-gateway:8001']
  metrics_path: '/metrics'
  
- job_name: 'gateway-config-service'
  static_configs:
    - targets: ['gateway-config-service:3001']
  metrics_path: '/metrics'

- job_name: 'consul'
  static_configs:
    - targets: ['consul:8500']
  metrics_path: '/v1/agent/metrics'
  params:
    format: ['prometheus']
```

#### 4.2 Grafana Dashboard配置

```json
{
  "dashboard": {
    "title": "LJWX API Gateway Dashboard",
    "panels": [
      {
        "title": "请求QPS",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(kong_http_requests_total[5m])",
            "legendFormat": "{{route}} - {{method}}"
          }
        ]
      },
      {
        "title": "响应时间分布", 
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.50, rate(kong_request_duration_ms_bucket[5m]))",
            "legendFormat": "P50"
          },
          {
            "expr": "histogram_quantile(0.95, rate(kong_request_duration_ms_bucket[5m]))",
            "legendFormat": "P95"
          },
          {
            "expr": "histogram_quantile(0.99, rate(kong_request_duration_ms_bucket[5m]))",
            "legendFormat": "P99"
          }
        ]
      },
      {
        "title": "License状态统计",
        "type": "stat",
        "targets": [
          {
            "expr": "ljwx_license_active_customers",
            "legendFormat": "活跃客户"
          },
          {
            "expr": "ljwx_license_total_devices",
            "legendFormat": "总设备数"
          }
        ]
      },
      {
        "title": "服务健康状态",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"ljwx-boot\"}",
            "legendFormat": "Boot服务"
          },
          {
            "expr": "up{job=\"ai-analysis-service\"}",
            "legendFormat": "AI服务"
          }
        ]
      }
    ]
  }
}
```

## 性能对比分析

### 传统架构 vs 网关架构

| 性能指标 | 传统架构 | 网关架构 | 提升幅度 |
|----------|----------|----------|----------|
| **认证延迟** | 50-100ms | 5-10ms | 80-90% |
| **配置获取** | 100-200ms | 10-20ms | 85-90% |
| **License检查** | 30-50ms | 2-5ms | 90% |
| **水平扩展** | 手动，10分钟+ | 自动，30秒 | 95% |
| **故障恢复** | 5-10分钟 | 30秒-2分钟 | 70-85% |
| **运维复杂度** | 高（N个服务） | 低（统一网关） | 显著降低 |

### 扩展能力对比

```mermaid
graph LR
    subgraph "传统架构扩展"
        A1[服务A实例1] --> B1[负载均衡器1]
        A2[服务A实例2] --> B1
        A3[服务A实例3] --> B1
        
        C1[服务B实例1] --> D1[负载均衡器2]
        C2[服务B实例2] --> D1
        
        B1 --> E[客户端]
        D1 --> E
    end
    
    subgraph "网关架构扩展"
        F1[API网关集群] --> G1[服务发现]
        G1 --> H1[服务A集群1-N]
        G1 --> H2[服务B集群1-M]
        G1 --> H3[服务C集群1-K]
        
        F1 --> I[客户端]
    end
```

## 实施计划与优势

### 实施阶段

1. **第一阶段 (1-2周)**: API网关基础设施搭建
   - Kong网关部署和配置
   - 自定义插件开发（认证、License）
   - 配置服务网关化改造

2. **第二阶段 (2-3周)**: 服务注册发现
   - Consul服务发现集成  
   - 服务自动注册和健康检查
   - 动态路由配置

3. **第三阶段 (1-2周)**: 自动扩缩容
   - HPA配置和测试
   - 监控告警集成
   - 性能调优

4. **第四阶段 (1周)**: 全量迁移和验证
   - ljwx-watch切换到网关
   - 性能测试和验证
   - 监控数据分析

### 核心优势总结

1. **架构简化**：统一入口点，减少服务间直接依赖
2. **性能提升**：集中缓存，减少重复查询和计算  
3. **运维简化**：统一配置管理，一次部署全局生效
4. **扩展便利**：自动服务发现，弹性扩缩容
5. **监控统一**：全链路可观测，问题定位更快
6. **安全增强**：统一认证授权，License精确控制

这种API网关统一架构不仅解决了当前的性能问题，更为未来的业务扩展和技术演进奠定了坚实的基础。
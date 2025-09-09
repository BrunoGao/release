# BigScreen 系统 API 重构优化建议方案

## 概述

基于对 ljwx-bigscreen 系统的全面 API 分析，本文档提供详细的重构建议，旨在提升系统的可维护性、性能和扩展性。

## 当前问题总结

### 1. 接口命名不规范
- 存在多种命名模式混用
- 缺乏统一的RESTful设计
- 动词和资源名称混乱

### 2. 参数传递不一致
- URL参数、路径参数、请求体参数混用
- 缺乏统一的参数验证机制
- 错误处理不标准化

### 3. 架构设计问题
- 缺乏版本控制
- 接口职责不清晰
- 缺乏统一的响应格式

## 重构目标

1. **标准化**: 建立统一的RESTful API设计规范
2. **模块化**: 按业务功能组织API接口
3. **安全性**: 增强权限控制和参数验证
4. **性能**: 优化数据加载和缓存策略
5. **可维护性**: 提升代码质量和文档完整性

## 重构方案设计

### 1. API 命名规范统一化

#### 1.1 新的命名规范

**基础路径结构:**
```
/api/v1/{module}/{resource}/{action?}
```

**示例映射:**
```bash
# 旧接口 -> 新接口
/get_users_by_orgIdAndUserId -> /api/v1/organization/{orgId}/users
/get_health_data_by_deviceSn -> /api/v1/device/{deviceSn}/health
/api/health/score/comprehensive -> /api/v1/health/score/comprehensive
./dealAlert -> /api/v1/alert/{alertId}/handle
```

#### 1.2 模块化组织架构

```
/api/v1/
├── organization/           # 组织管理
│   ├── {orgId}/users      # 用户管理
│   ├── {orgId}/devices    # 设备管理
│   └── {orgId}/departments # 部门管理
├── health/                # 健康数据
│   ├── score/            # 健康评分
│   ├── analysis/         # 健康分析
│   ├── baseline/         # 健康基线
│   └── recommendations/  # 健康建议
├── device/               # 设备管理
│   ├── {deviceSn}/info   # 设备信息
│   ├── {deviceSn}/health # 设备健康数据
│   └── {deviceSn}/battery # 设备电池
├── alert/                # 告警管理
│   ├── list             # 告警列表
│   ├── {alertId}/handle # 告警处理
│   └── batch/handle     # 批量处理
├── message/              # 消息管理
│   ├── send             # 发送消息
│   └── list             # 消息列表
├── statistics/           # 统计数据
│   ├── overview         # 概览统计
│   └── realtime         # 实时统计
└── personal/             # 个人数据
    ├── profile          # 个人档案
    ├── health           # 个人健康
    └── alerts           # 个人告警
```

### 2. HTTP 方法规范化

#### 2.1 方法映射表

| 操作类型 | HTTP方法 | URL模式 | 示例 |
|---------|---------|---------|------|
| 获取列表 | GET | `/api/v1/{module}` | `GET /api/v1/organization/123/users` |
| 获取详情 | GET | `/api/v1/{module}/{id}` | `GET /api/v1/device/SN123456/info` |
| 创建资源 | POST | `/api/v1/{module}` | `POST /api/v1/message/send` |
| 更新资源 | PUT | `/api/v1/{module}/{id}` | `PUT /api/v1/alert/456/handle` |
| 部分更新 | PATCH | `/api/v1/{module}/{id}` | `PATCH /api/v1/device/SN123456` |
| 删除资源 | DELETE | `/api/v1/{module}/{id}` | `DELETE /api/v1/alert/456` |
| 批量操作 | POST | `/api/v1/{module}/batch/{action}` | `POST /api/v1/alert/batch/handle` |

#### 2.2 具体接口重构映射

**组织用户管理接口:**
```bash
# 旧接口
GET /get_users_by_orgIdAndUserId?orgId=123&userId=456
# 新接口
GET /api/v1/organization/123/users?userId=456
GET /api/v1/organization/123/users/456
```

**健康数据接口:**
```bash
# 旧接口
GET /get_health_data_by_orgIdAndUserId?orgId=123&userId=456
GET /get_health_data_by_deviceSn?deviceSn=SN123456
# 新接口
GET /api/v1/organization/123/health?userId=456
GET /api/v1/device/SN123456/health
```

**告警处理接口:**
```bash
# 旧接口
GET ./dealAlert?alertId=789
POST ./batchDealAlert
# 新接口
PUT /api/v1/alert/789/handle
POST /api/v1/alert/batch/handle
```

### 3. 统一响应格式设计

#### 3.1 标准响应结构

```json
{
    "success": true|false,
    "code": "SUCCESS|ERROR_CODE",
    "message": "操作结果描述",
    "data": {
        // 业务数据
    },
    "meta": {
        "timestamp": "2025-09-09T10:30:00Z",
        "requestId": "req_123456789",
        "pagination": {
            "page": 1,
            "size": 20,
            "total": 100,
            "totalPages": 5
        }
    }
}
```

#### 3.2 错误响应格式

```json
{
    "success": false,
    "code": "VALIDATION_ERROR",
    "message": "参数验证失败",
    "errors": [
        {
            "field": "orgId",
            "message": "组织ID不能为空"
        }
    ],
    "meta": {
        "timestamp": "2025-09-09T10:30:00Z",
        "requestId": "req_123456789"
    }
}
```

### 4. 参数传递标准化

#### 4.1 查询参数规范

```bash
# 分页参数
?page=1&size=20

# 排序参数
?sort=createTime,desc&sort=name,asc

# 过滤参数
?userId=123&status=active&createTime>=2025-01-01

# 包含关联数据
?include=device,health&expand=profile

# 字段选择
?fields=id,name,status
```

#### 4.2 路径参数规范

```bash
# 组织相关
/api/v1/organization/{orgId}/users/{userId}
/api/v1/organization/{orgId}/devices/{deviceSn}

# 设备相关
/api/v1/device/{deviceSn}/health
/api/v1/device/{deviceSn}/battery/prediction

# 告警相关
/api/v1/alert/{alertId}/handle
```

#### 4.3 请求体格式

```json
// POST /api/v1/message/send
{
    "content": "消息内容",
    "type": "SYSTEM|ALERT|NOTIFICATION",
    "receivers": [
        {
            "type": "USER",
            "id": "123"
        },
        {
            "type": "DEPARTMENT",
            "id": "456"
        }
    ],
    "priority": "LOW|MEDIUM|HIGH|URGENT",
    "scheduledAt": "2025-09-09T14:00:00Z"
}
```

### 5. 权限控制增强

#### 5.1 权限验证机制

```javascript
// 统一权限验证中间件
function validatePermission(requiredPermission) {
    return function(req, res, next) {
        const { user, organization } = req.auth;
        
        // 验证用户是否有权限访问该组织
        if (req.params.orgId && user.organizationId !== req.params.orgId) {
            return res.status(403).json({
                success: false,
                code: "PERMISSION_DENIED",
                message: "无权访问该组织数据"
            });
        }
        
        // 验证具体操作权限
        if (!user.permissions.includes(requiredPermission)) {
            return res.status(403).json({
                success: false,
                code: "INSUFFICIENT_PERMISSION",
                message: "权限不足"
            });
        }
        
        next();
    };
}
```

#### 5.2 数据过滤策略

```javascript
// 基于用户权限的数据过滤
function applyDataFilter(query, user) {
    // 普通用户只能查看自己的数据
    if (user.role === 'USER') {
        query.userId = user.id;
    }
    
    // 部门管理员只能查看本部门数据
    if (user.role === 'DEPARTMENT_ADMIN') {
        query.departmentId = user.departmentId;
    }
    
    // 组织管理员可以查看组织内所有数据
    if (user.role === 'ORGANIZATION_ADMIN') {
        query.organizationId = user.organizationId;
    }
    
    return query;
}
```

### 6. 缓存策略优化

#### 6.1 多层缓存架构

```javascript
// 缓存层次结构
const cacheConfig = {
    // L1: 浏览器缓存 (5-30秒)
    browser: {
        'GET /api/v1/organization/*/users': 30,
        'GET /api/v1/device/*/info': 60,
        'GET /api/v1/statistics/overview': 10
    },
    
    // L2: CDN缓存 (1-5分钟)
    cdn: {
        'GET /api/v1/organization/*/departments': 300,
        'GET /api/v1/health/baseline/*': 300
    },
    
    // L3: 应用缓存 (5-30分钟)
    application: {
        'GET /api/v1/health/score/*': 1800,
        'GET /api/v1/device/*/battery/prediction': 900
    },
    
    // L4: 数据库缓存 (30分钟-24小时)
    database: {
        'GET /api/v1/statistics/historical/*': 86400
    }
};
```

#### 6.2 缓存失效策略

```javascript
// 智能缓存失效
const cacheInvalidation = {
    // 数据更新时自动失效相关缓存
    patterns: {
        'POST|PUT|DELETE /api/v1/organization/*/users/*': [
            'GET /api/v1/organization/*/users',
            'GET /api/v1/statistics/overview'
        ],
        'POST /api/v1/alert/*/handle': [
            'GET /api/v1/alert/list',
            'GET /api/v1/statistics/realtime'
        ]
    }
};
```

### 7. 性能优化方案

#### 7.1 并发请求优化

```javascript
// 智能批处理API
class BatchRequestManager {
    constructor() {
        this.batchQueue = new Map();
        this.batchTimeout = 100; // 100ms批处理窗口
    }
    
    addRequest(apiCall, params) {
        const batchKey = `${apiCall.endpoint}_${JSON.stringify(apiCall.commonParams)}`;
        
        if (!this.batchQueue.has(batchKey)) {
            this.batchQueue.set(batchKey, {
                requests: [],
                timer: setTimeout(() => this.executeBatch(batchKey), this.batchTimeout)
            });
        }
        
        const batch = this.batchQueue.get(batchKey);
        batch.requests.push({ params, resolve, reject });
    }
    
    executeBatch(batchKey) {
        const batch = this.batchQueue.get(batchKey);
        // 将多个单独请求合并为一个批处理请求
        const batchParams = batch.requests.map(req => req.params);
        
        fetch(`/api/v1/batch${batch.endpoint}`, {
            method: 'POST',
            body: JSON.stringify({ requests: batchParams })
        }).then(response => {
            // 分发批处理结果到各个原始请求
            batch.requests.forEach((req, index) => {
                req.resolve(response.results[index]);
            });
        });
        
        this.batchQueue.delete(batchKey);
    }
}
```

#### 7.2 数据预加载策略

```javascript
// 智能预加载管理器
class PreloadManager {
    constructor() {
        this.preloadRules = {
            // 访问用户列表时预加载用户详情
            'GET /api/v1/organization/*/users': {
                preload: ['GET /api/v1/organization/*/users/*/profile'],
                condition: 'listSize < 10'
            },
            
            // 访问设备信息时预加载健康数据
            'GET /api/v1/device/*/info': {
                preload: ['GET /api/v1/device/*/health/latest'],
                condition: 'deviceStatus === "online"'
            }
        };
    }
    
    executePreload(apiCall, responseData) {
        const rules = this.preloadRules[apiCall];
        if (!rules) return;
        
        // 评估预加载条件
        if (this.evaluateCondition(rules.condition, responseData)) {
            rules.preload.forEach(preloadApi => {
                // 在后台异步执行预加载
                this.backgroundFetch(preloadApi, responseData);
            });
        }
    }
}
```

### 8. 错误处理增强

#### 8.1 统一错误处理中间件

```javascript
// 全局错误处理
class ApiErrorHandler {
    constructor() {
        this.errorCodes = {
            VALIDATION_ERROR: { status: 400, message: '参数验证失败' },
            PERMISSION_DENIED: { status: 403, message: '权限不足' },
            RESOURCE_NOT_FOUND: { status: 404, message: '资源不存在' },
            BUSINESS_ERROR: { status: 422, message: '业务逻辑错误' },
            SYSTEM_ERROR: { status: 500, message: '系统内部错误' }
        };
    }
    
    handleError(error, req, res) {
        const errorInfo = this.errorCodes[error.code] || this.errorCodes.SYSTEM_ERROR;
        
        // 记录错误日志
        logger.error('API Error', {
            requestId: req.requestId,
            url: req.url,
            method: req.method,
            error: error,
            user: req.user?.id,
            timestamp: new Date().toISOString()
        });
        
        // 返回标准错误响应
        res.status(errorInfo.status).json({
            success: false,
            code: error.code,
            message: error.message || errorInfo.message,
            errors: error.details || [],
            meta: {
                requestId: req.requestId,
                timestamp: new Date().toISOString()
            }
        });
    }
}
```

#### 8.2 前端错误处理优化

```javascript
// 统一API客户端
class ApiClient {
    constructor() {
        this.retryConfig = {
            maxRetries: 3,
            retryDelay: [1000, 2000, 4000], // 递增延迟
            retryConditions: [
                error => error.status >= 500,
                error => error.code === 'NETWORK_ERROR',
                error => error.code === 'TIMEOUT_ERROR'
            ]
        };
    }
    
    async request(endpoint, options = {}) {
        let lastError;
        
        for (let attempt = 0; attempt <= this.retryConfig.maxRetries; attempt++) {
            try {
                const response = await fetch(endpoint, {
                    ...options,
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Request-ID': this.generateRequestId(),
                        ...options.headers
                    }
                });
                
                if (!response.ok) {
                    throw new ApiError(response.status, await response.json());
                }
                
                return await response.json();
                
            } catch (error) {
                lastError = error;
                
                // 检查是否应该重试
                if (attempt < this.retryConfig.maxRetries && 
                    this.shouldRetry(error)) {
                    await this.delay(this.retryConfig.retryDelay[attempt]);
                    continue;
                }
                
                break;
            }
        }
        
        throw lastError;
    }
    
    shouldRetry(error) {
        return this.retryConfig.retryConditions.some(condition => condition(error));
    }
}
```

## 实施计划

### 阶段1: 基础架构搭建 (第1-2周)

1. **API网关配置**
   - 设置路由规则和版本控制
   - 实现统一的请求/响应处理
   - 配置权限验证中间件

2. **错误处理系统**
   - 实现统一错误处理中间件
   - 建立错误代码规范
   - 配置日志记录系统

### 阶段2: 核心接口重构 (第3-4周)

1. **组织用户接口**
   - 重构用户管理相关API
   - 实现新的权限控制
   - 迁移现有数据访问逻辑

2. **健康数据接口**
   - 重构健康数据获取API
   - 优化数据查询性能
   - 实现缓存策略

### 阶段3: 高级功能实现 (第5-6周)

1. **批处理和预加载**
   - 实现批处理API
   - 配置智能预加载
   - 优化前端数据加载策略

2. **缓存系统**
   - 部署多层缓存架构
   - 实现缓存失效机制
   - 监控缓存性能

### 阶段4: 测试和上线 (第7-8周)

1. **全面测试**
   - API功能测试
   - 性能压力测试
   - 安全性测试

2. **平滑迁移**
   - 实现API版本共存
   - 逐步切换前端调用
   - 监控系统稳定性

## 预期效果

### 1. 性能提升
- API响应时间减少30-50%
- 并发处理能力提升200%
- 缓存命中率达到80%以上

### 2. 开发效率
- 新接口开发时间减少60%
- 接口文档自动生成
- 代码复用率提升40%

### 3. 系统稳定性
- 接口错误率降低70%
- 系统可用性提升到99.9%
- 故障恢复时间缩短50%

### 4. 维护成本
- 代码维护工作量减少40%
- 新功能开发周期缩短30%
- 系统扩展性显著提升

## 风险控制

### 1. 向后兼容
- 保持旧版本API同时运行
- 提供迁移过渡期
- 分阶段废弃旧接口

### 2. 数据一致性
- 实施数据库事务控制
- 建立数据验证机制
- 配置数据备份策略

### 3. 性能监控
- 实时监控API性能
- 设置告警阈值
- 快速故障响应机制

## 总结

本重构方案通过系统性的API设计优化，将显著提升 ljwx-bigscreen 系统的整体质量。建议按阶段实施，确保系统稳定运行的同时逐步实现现代化升级。

---

*本方案制定时间: 2025-09-09*
*预计实施周期: 8周*
*涉及接口数量: 35+个*
*预期性能提升: 30-50%*
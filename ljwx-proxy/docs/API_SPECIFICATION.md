# LJWX FastAPI代理服务 - API接口规范

## 项目概述

LJWX FastAPI代理服务是一个基于FastAPI的中间层服务，为前端大屏和个人页面提供统一的API接口。该服务代理到后端ljwx-boot服务，并提供标准化的RESTful API。

## 技术架构

```
前端 (bigscreen_main.html/personal.html) 
  ↓ HTTP Requests
FastAPI代理服务 (Port: 8888)
  ↓ HTTP Proxy
后端ljwx-boot服务 (Port: 8080)
```

## API版本化策略

- **当前版本**: v1
- **基础路径**: `/api/v1`
- **版本控制**: URL路径版本化
- **向后兼容**: 保持旧版本API至少2个版本周期

## 通用响应格式

### 成功响应
```json
{
  "code": 200,
  "message": "success",
  "data": {
    // 具体业务数据
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 错误响应
```json
{
  "code": 400,
  "message": "Invalid request parameters", 
  "error": "INVALID_PARAMS",
  "details": "userId parameter is required",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### HTTP状态码规范
- `200 OK`: 请求成功
- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: 未认证
- `403 Forbidden`: 权限不足
- `404 Not Found`: 资源不存在
- `500 Internal Server Error`: 服务器内部错误
- `502 Bad Gateway`: 后端服务不可用
- `504 Gateway Timeout`: 后端服务超时

## API分组规范

### 1. 健康数据API (`/api/v1/health/*`)

| 端点 | 方法 | 描述 |
|------|------|------|
| `/health/scores/comprehensive` | GET | 获取健康综合评分 |
| `/health/realtime-data` | GET | 获取实时健康数据 |
| `/health/trends` | GET | 获取健康趋势数据 |
| `/health/baseline/chart` | GET | 获取基线数据图表 |
| `/health/baseline/generate` | POST | 生成基线数据 |
| `/health/data/{id}` | GET | 获取特定健康数据 |
| `/health/personal/scores` | GET | 获取个人健康评分 |
| `/health/recommendations` | GET | 获取健康建议 |
| `/health/predictions` | GET | 获取健康预测 |

### 2. 设备管理API (`/api/v1/devices/*`)

| 端点 | 方法 | 描述 |
|------|------|------|
| `/devices/user-info` | GET | 获取设备用户信息 |
| `/devices/status` | GET | 获取设备状态 |
| `/devices/user-organization` | GET | 获取设备用户组织 |

### 3. 用户管理API (`/api/v1/users/*`)

| 端点 | 方法 | 描述 |
|------|------|------|
| `/users` | GET | 获取用户列表 |
| `/users/profile` | GET | 获取用户资料 |

### 4. 组织管理API (`/api/v1/organizations/*`)

| 端点 | 方法 | 描述 |
|------|------|------|
| `/organizations/statistics` | GET | 获取组织统计信息 |

### 5. 部门管理API (`/api/v1/departments`)

| 端点 | 方法 | 描述 |
|------|------|------|
| `/departments` | GET | 获取部门列表 |

### 6. 统计分析API (`/api/v1/statistics/*`)

| 端点 | 方法 | 描述 |
|------|------|------|
| `/statistics/overview` | GET | 获取统计概览 |
| `/statistics/realtime` | GET | 获取实时统计 |

### 7. 告警管理API (`/api/v1/alerts/*`)

| 端点 | 方法 | 描述 |
|------|------|------|
| `/alerts/user` | GET | 获取用户告警 |
| `/alerts/personal` | GET | 获取个人告警 |
| `/alerts/acknowledge` | POST | 确认告警 |
| `/alerts/deal` | POST | 处理告警 |

### 8. 消息管理API (`/api/v1/messages/*`)

| 端点 | 方法 | 描述 |
|------|------|------|
| `/messages/user` | GET | 获取用户消息 |

## 参数规范

### 查询参数命名规范
- 使用`camelCase`命名: `userId`, `orgId`, `startDate`
- 布尔参数: `isActive`, `includeDeleted`
- 分页参数: `page`, `pageSize`, `limit`, `offset`
- 排序参数: `sortBy`, `sortOrder` (`asc`/`desc`)
- 过滤参数: `filter`, `search`, `status`

### 路径参数
- 资源ID使用数字或UUID: `/users/{userId}`, `/devices/{deviceId}`
- 嵌套资源: `/users/{userId}/alerts`, `/organizations/{orgId}/departments`

### 请求体规范
```json
// POST /api/v1/alerts/acknowledge
{
  "alertId": "string",
  "userId": "string", 
  "comment": "string",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 分页规范

### 请求参数
```
GET /api/v1/users?page=1&pageSize=20&sortBy=createTime&sortOrder=desc
```

### 响应格式
```json
{
  "code": 200,
  "data": {
    "items": [...],
    "pagination": {
      "page": 1,
      "pageSize": 20,
      "total": 100,
      "totalPages": 5,
      "hasNext": true,
      "hasPrevious": false
    }
  }
}
```

## 认证与授权

### 认证方式
- **开发环境**: 无认证 (当前实现)
- **生产环境**: Bearer Token 或 API Key

### 授权头格式
```
Authorization: Bearer <jwt-token>
# 或
X-API-Key: <api-key>
```

## 错误码定义

| 业务错误码 | HTTP状态码 | 描述 |
|------------|------------|------|
| `INVALID_PARAMS` | 400 | 请求参数无效 |
| `USER_NOT_FOUND` | 404 | 用户不存在 |
| `DEVICE_NOT_FOUND` | 404 | 设备不存在 |
| `UNAUTHORIZED` | 401 | 未授权访问 |
| `FORBIDDEN` | 403 | 权限不足 |
| `BACKEND_ERROR` | 502 | 后端服务错误 |
| `TIMEOUT` | 504 | 请求超时 |
| `RATE_LIMITED` | 429 | 请求频率限制 |

## 性能要求

### 响应时间标准
- **P50**: < 200ms
- **P95**: < 500ms  
- **P99**: < 1000ms

### 并发处理
- **支持并发**: 1000 QPS
- **连接池**: 最大50个连接
- **超时设置**: 30秒

## 监控与日志

### 关键指标
- API响应时间
- 成功率/错误率
- 后端服务健康状态
- 并发连接数

### 日志格式
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "method": "GET", 
  "path": "/api/v1/health/scores/comprehensive",
  "status": 200,
  "duration": 150,
  "user_id": "123",
  "request_id": "req_abc123"
}
```

## 开发规范

### 代码结构
```
main.py                 # FastAPI应用主文件
├── routers/            # API路由模块
│   ├── health.py       # 健康相关API
│   ├── devices.py      # 设备相关API  
│   └── users.py        # 用户相关API
├── models/             # 数据模型
├── services/           # 业务逻辑层
├── utils/              # 工具函数
└── config.py          # 配置文件
```

### 依赖注入
```python
from fastapi import Depends

async def get_ljwx_client() -> LjwxBootClient:
    return ljwx_client

@app.get("/api/v1/users/{user_id}")
async def get_user(
    user_id: str,
    client: LjwxBootClient = Depends(get_ljwx_client)
):
    return await client.get(f"/user/{user_id}")
```

### 异常处理
```python
from fastapi import HTTPException

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )
```

## 测试策略

### 单元测试
```python
import pytest
from fastapi.testclient import TestClient

def test_get_health_score():
    response = client.get("/api/v1/health/scores/comprehensive?userId=123")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "score" in data["data"]
```

### 集成测试
- 测试API端到端流程
- 模拟后端服务响应
- 验证错误处理逻辑

### 性能测试
- 使用locust或artillery进行压力测试
- 监控响应时间和内存使用
- 测试并发场景

## 部署配置

### 环境变量
```bash
# 后端服务配置
LJWX_BOOT_BASE_URL=http://localhost:8080

# 服务配置
PORT=8888
HOST=0.0.0.0
WORKERS=4

# 日志配置  
LOG_LEVEL=INFO
LOG_FILE=/var/log/ljwx-proxy.log

# 超时配置
REQUEST_TIMEOUT=30
KEEP_ALIVE_TIMEOUT=65
```

### Docker配置
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8888
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8888"]
```

## 版本更新日志

### v1.0.0 (2024-01-01)
- ✨ 初始版本发布
- 🔧 支持所有大屏和个人页面API
- 📚 完整的API文档
- 🚀 FastAPI框架集成
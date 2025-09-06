# LJWX FastAPI代理服务文档

## 概述

LJWX FastAPI代理服务是一个基于FastAPI框架的中间层服务，为前端大屏和个人页面提供统一、规范化的API接口。该服务作为代理层，将请求转发到后端ljwx-boot服务。

## 📊 项目状态

### ✅ 已完成阶段
- [x] **前端模板API规范化** (100% - 28个API已迁移) 
- [x] **FastAPI代理服务** (100% - 23个v1端点已实现)
- [x] **Spring Boot后端实现** (100% - BigscreenApiV1Controller已完成)
- [x] **完整文档体系** (100% - 包含实现指南和API规范)

### 🔄 当前阶段
- [ ] **集成测试** (进行中 - 测试v1 API端点)
- [ ] **性能优化** (计划中)

### 📈 总体进度: **80% 完成**

## 🚀 快速开始

### 环境要求
- Python 3.9+
- FastAPI 0.100+
- uvicorn

### 安装与运行
```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动服务
python main.py

# 或使用脚本启动
./start.sh
```

### 访问地址
- **FastAPI代理服务**: http://localhost:8888
- **FastAPI API文档**: http://localhost:8888/docs
- **主屏页面**: http://localhost:8888/main?customerId=xxx
- **个人页面**: http://localhost:8888/personal?deviceSn=xxx
- **Spring Boot后端**: http://localhost:8080 (ljwx-boot)
- **Swagger UI**: http://localhost:8080/swagger-ui.html

## 📚 文档目录

| 文档 | 描述 |
|------|------|
| [API_NAMING_STANDARDS.md](./API_NAMING_STANDARDS.md) | API命名规范和标准化建议 |
| [BIGSCREEN_APIS.md](./BIGSCREEN_APIS.md) | BigScreen主屏API接口文档 |
| [PERSONAL_APIS.md](./PERSONAL_APIS.md) | Personal个人页面API接口文档 |
| [API_SPECIFICATION.md](./API_SPECIFICATION.md) | 完整的API规范文档 |
| [MIGRATION_SUMMARY.md](./MIGRATION_SUMMARY.md) | API规范化迁移总结报告 |
| [spring-boot/](./spring-boot/) | Spring Boot实现模板和文档 |

## 🏗️ 项目结构

```
ljwx-proxy/
├── fastapi-bigscreen/
│   ├── main.py              # FastAPI应用主文件
│   ├── templates/           # HTML模板
│   │   ├── bigscreen_main.html
│   │   └── personal.html
│   ├── static/              # 静态资源
│   │   ├── js/
│   │   ├── libs/
│   │   ├── fonts/
│   │   └── css/
│   ├── requirements.txt     # Python依赖
│   ├── start.sh            # 启动脚本
│   └── README.md           # 项目说明
└── docs/                   # 文档目录
    ├── README.md           # 本文档
    ├── API_NAMING_STANDARDS.md
    ├── BIGSCREEN_APIS.md
    ├── PERSONAL_APIS.md
    └── API_SPECIFICATION.md
```

## 🔧 API版本化

### 当前版本策略
- **当前版本**: v1
- **规范化API**: `/api/v1/*`
- **兼容性API**: 保持原有API路径不变

### API分组
| 分组 | 路径前缀 | 描述 |
|------|----------|------|
| 健康数据 | `/api/v1/health/*` | 健康评分、实时数据、趋势分析 |
| 设备管理 | `/api/v1/devices/*` | 设备状态、用户绑定信息 |
| 用户管理 | `/api/v1/users/*` | 用户资料、消息管理 |
| 组织管理 | `/api/v1/organizations/*` | 组织统计、部门管理 |
| 告警系统 | `/api/v1/alerts/*` | 告警查询、处理确认 |
| 统计分析 | `/api/v1/statistics/*` | 数据统计、实时监控 |

## 📊 API使用示例

### BigScreen主屏API调用
```javascript
// 获取健康综合评分
const response = await fetch('/api/v1/health/scores/comprehensive?orgId=123&date=2024-01-01');
const data = await response.json();

// 获取部门列表  
const departments = await fetch('/api/v1/departments?orgId=123');

// 处理告警
await fetch('/api/v1/alerts/deal', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ alertId: '456' })
});
```

### Personal个人页面API调用
```javascript
// 获取设备用户信息
const userInfo = await fetch('/api/v1/devices/user-info?deviceSn=CRFTQ23409001890');

// 获取实时健康数据
const realtimeData = await fetch('/api/v1/health/realtime-data?deviceSn=CRFTQ23409001890');

// 获取个人告警
const alerts = await fetch('/api/v1/alerts/personal?deviceSn=CRFTQ23409001890');
```

## 🔄 向后兼容性

服务同时支持新旧两套API：

### 规范化API (推荐)
```
GET /api/v1/health/scores/comprehensive
GET /api/v1/devices/user-info
GET /api/v1/organizations/statistics
```

### 兼容性API (保持支持)
```
GET /api/health/score/comprehensive
GET /api/device/user_info
GET /get_total_info
```

## 🛠️ 开发指南

### 添加新API端点
```python
@app.get("/api/v1/new-endpoint")
async def new_endpoint_v1(param: str = Query(...)):
    """新端点描述"""
    result = await ljwx_client.get("/backend/endpoint", {"param": param})
    if result is None:
        raise HTTPException(status_code=500, detail="后端服务错误")
    return result
```

### 错误处理
```python
from fastapi import HTTPException

@app.get("/api/v1/example")
async def example():
    try:
        result = await ljwx_client.get("/backend/api")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务异常: {str(e)}")
```

## 📈 性能优化

### 连接池配置
```python
ljwx_client = LjwxBootClient(
    base_url=LJWX_BOOT_BASE_URL,
    timeout=30.0,
    pool_limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
)
```

### 缓存策略
对于不常变化的数据，建议实施缓存：
- 用户资料: 缓存5分钟
- 部门信息: 缓存10分钟  
- 组织统计: 缓存3分钟

## 🐛 故障排查

### 常见问题
1. **静态文件404**: 检查static目录是否存在
2. **API代理失败**: 确认ljwx-boot服务是否正常运行
3. **模板渲染错误**: 检查templates目录和文件权限

### 调试模式
```bash
# 开启调试模式
python main.py --debug

# 查看详细日志
python main.py --log-level debug
```

## 🚦 健康检查

服务提供健康检查端点：
```
GET /health
```

响应示例：
```json
{
  "status": "ok",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 📝 更新日志

### v1.1.0 (2024-01-05) - API规范化版本
- ✨ **前端模板API迁移完成**
  - 🔄 bigscreen_main.html: 15个API全部迁移到v1规范
  - 🔄 personal.html: 13个API全部迁移到v1规范
  - 📊 总计28个API调用完成标准化
- 🏗️ **Spring Boot实现指南**
  - 📋 7个完整的Controller模板
  - 📄 OpenAPI 3.0规范文档
  - 📚 详细的实现指南 (80页)
  - 🧪 测试用例和最佳实践
- 📊 **API规范化**
  - 🎯 统一使用`/api/v1/`版本前缀
  - 🔤 RESTful命名规范 (kebab-case)
  - 📝 标准化响应格式
  - ⚡ 完整的错误处理机制
- 📖 **文档系统**
  - 📑 迁移总结报告
  - 🔧 Spring Boot快速开始指南
  - 📋 API对照表和实施清单

### v1.0.0 (2024-01-01)
- ✨ 初始版本发布
- 🔧 支持所有大屏和个人页面API
- 📚 完整的API文档
- 🚀 FastAPI框架集成
- 🔄 新旧API并存，保持向后兼容
- 📊 规范化API版本v1

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目使用 MIT 许可证。详情请见 [LICENSE](LICENSE) 文件。

## 📞 联系我们

如有问题或建议，请通过以下方式联系：
- 项目Issues: [GitHub Issues](https://github.com/your-org/ljwx-proxy/issues)
- 邮箱: your-email@company.com

---

**注意**: 本服务为内部开发工具，请勿在生产环境中直接使用未经安全审核的版本。
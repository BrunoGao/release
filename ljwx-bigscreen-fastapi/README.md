# LJWX BigScreen FastAPI 重构项目

## 项目概述

基于 FastAPI 重构的高性能大屏系统，采用现代化微服务架构，解决原 Flask 项目的性能瓶颈和维护性问题。

## 架构设计

### 核心特性
- **高性能**: FastAPI + 异步编程，支持高并发
- **模块化**: 按业务领域拆分模块，降低耦合度
- **可扩展**: 支持微服务架构，易于水平扩展
- **现代化**: Python 3.9+，类型注解，自动API文档

### 技术栈
- **Web框架**: FastAPI 0.104+
- **异步支持**: asyncio + uvicorn
- **数据库**: 
  - MySQL 8.0+ (主数据库)
  - Redis 7.0+ (缓存 + 消息队列)
- **ORM**: SQLAlchemy 2.0 (异步)
- **任务队列**: Celery + Redis
- **监控**: Prometheus + Grafana
- **部署**: Docker + Kubernetes

## 项目结构

```
ljwx-bigscreen-fastapi/
├── app/                          # 应用核心目录
│   ├── main.py                   # FastAPI 应用入口
│   ├── config/                   # 配置管理
│   │   ├── __init__.py
│   │   ├── settings.py           # 应用配置
│   │   └── database.py           # 数据库配置
│   ├── core/                     # 核心基础模块
│   │   ├── __init__.py
│   │   ├── auth.py               # 认证授权
│   │   ├── cache.py              # 缓存管理
│   │   ├── database.py           # 数据库连接
│   │   ├── exceptions.py         # 异常处理
│   │   ├── logger.py             # 日志管理
│   │   └── security.py           # 安全相关
│   ├── base/                     # 基础功能模块
│   │   ├── __init__.py
│   │   ├── redis/                # Redis 操作
│   │   ├── mysql/                # MySQL 操作
│   │   ├── org/                  # 组织架构
│   │   └── user/                 # 用户管理
│   ├── business/                 # 业务功能模块
│   │   ├── __init__.py
│   │   ├── alert/                # 告警模块
│   │   ├── message/              # 消息模块
│   │   ├── health_data/          # 健康数据模块
│   │   └── device/               # 设备模块
│   ├── api/                      # API 路由
│   │   ├── __init__.py
│   │   ├── v1/                   # API v1 版本
│   │   │   ├── __init__.py
│   │   │   ├── auth.py           # 认证相关API
│   │   │   ├── bigscreen.py      # 大屏相关API
│   │   │   ├── alert.py          # 告警API
│   │   │   ├── message.py        # 消息API
│   │   │   ├── health.py         # 健康数据API
│   │   │   └── device.py         # 设备API
│   │   └── deps.py               # API 依赖注入
│   ├── models/                   # 数据模型
│   │   ├── __init__.py
│   │   ├── base.py               # 基础模型
│   │   ├── user.py               # 用户模型
│   │   ├── org.py                # 组织模型
│   │   ├── alert.py              # 告警模型
│   │   ├── message.py            # 消息模型
│   │   ├── health_data.py        # 健康数据模型
│   │   └── device.py             # 设备模型
│   ├── schemas/                  # Pydantic 数据验证
│   │   ├── __init__.py
│   │   ├── base.py               # 基础schema
│   │   ├── user.py               # 用户schema
│   │   ├── alert.py              # 告警schema
│   │   ├── message.py            # 消息schema
│   │   ├── health_data.py        # 健康数据schema
│   │   └── device.py             # 设备schema
│   ├── services/                 # 业务逻辑服务
│   │   ├── __init__.py
│   │   ├── base.py               # 基础服务
│   │   ├── auth_service.py       # 认证服务
│   │   ├── alert_service.py      # 告警服务
│   │   ├── message_service.py    # 消息服务
│   │   ├── health_service.py     # 健康数据服务
│   │   └── device_service.py     # 设备服务
│   ├── utils/                    # 工具函数
│   │   ├── __init__.py
│   │   ├── datetime.py           # 时间处理
│   │   ├── validators.py         # 数据验证
│   │   ├── formatters.py         # 数据格式化
│   │   └── performance.py        # 性能监控
│   └── tasks/                    # 异步任务
│       ├── __init__.py
│       ├── celery_app.py         # Celery 配置
│       ├── health_tasks.py       # 健康数据处理任务
│       ├── alert_tasks.py        # 告警处理任务
│       └── message_tasks.py      # 消息处理任务
├── templates/                    # 前端模板
│   ├── layouts/                  # 布局模板
│   │   ├── base.html             # 基础布局
│   │   └── dashboard.html        # 大屏布局
│   ├── components/               # 组件模板
│   │   ├── charts/               # 图表组件
│   │   ├── panels/               # 面板组件
│   │   └── widgets/              # 小部件
│   └── pages/                    # 页面模板
│       ├── main.html             # 主大屏页面
│       ├── personal.html         # 个人大屏页面
│       └── dashboard.html        # 仪表板页面
├── static/                       # 静态资源
│   ├── css/                      # 样式文件
│   │   ├── core/                 # 核心样式
│   │   ├── components/           # 组件样式
│   │   └── themes/               # 主题样式
│   ├── js/                       # JavaScript 文件
│   │   ├── core/                 # 核心JS
│   │   ├── components/           # 组件JS
│   │   └── utils/                # 工具JS
│   └── assets/                   # 静态资源
│       ├── images/               # 图片
│       ├── fonts/                # 字体
│       └── icons/                # 图标
├── tests/                        # 测试目录
│   ├── __init__.py
│   ├── conftest.py               # 测试配置
│   ├── test_auth.py              # 认证测试
│   ├── test_alert.py             # 告警测试
│   ├── test_health.py            # 健康数据测试
│   └── test_device.py            # 设备测试
├── migrations/                   # 数据库迁移
│   └── alembic/                  # Alembic 迁移文件
├── docker/                       # Docker 配置
│   ├── Dockerfile                # 应用 Dockerfile
│   ├── Dockerfile.dev            # 开发环境 Dockerfile
│   └── docker-compose.yml        # Docker Compose 配置
├── k8s/                          # Kubernetes 配置
│   ├── deployment.yaml           # 部署配置
│   ├── service.yaml              # 服务配置
│   └── ingress.yaml              # 入口配置
├── docs/                         # 项目文档
│   ├── architecture.md           # 架构文档
│   ├── api.md                    # API 文档
│   └── deployment.md             # 部署文档
├── scripts/                      # 脚本文件
│   ├── start.sh                  # 启动脚本
│   ├── deploy.sh                 # 部署脚本
│   └── migrate.sh                # 迁移脚本
├── requirements/                 # 依赖管理
│   ├── base.txt                  # 基础依赖
│   ├── dev.txt                   # 开发依赖
│   └── prod.txt                  # 生产依赖
├── .env.example                  # 环境变量示例
├── pyproject.toml                # 项目配置
├── docker-compose.yml            # Docker Compose
└── README.md                     # 项目说明
```

## 模块设计

### 基础模块 (Base Modules)

#### 1. Redis 模块
- 连接池管理
- 缓存操作封装
- 发布订阅
- 分布式锁

#### 2. MySQL 模块
- 异步数据库连接
- 连接池管理
- 事务处理
- 读写分离

#### 3. 组织架构 (Org) 模块
- 组织树结构
- 权限控制
- 多租户支持

#### 4. 用户管理 (User) 模块
- 用户认证
- 角色权限
- 会话管理

### 业务模块 (Business Modules)

#### 1. 告警模块 (Alert)
- 告警规则引擎
- 实时告警处理
- 告警升级策略
- 告警统计分析

#### 2. 消息模块 (Message)
- 消息队列处理
- 实时推送
- 消息持久化
- 消息路由

#### 3. 健康数据模块 (Health Data)
- 数据采集
- 实时分析
- 健康评分
- 趋势预测

#### 4. 设备模块 (Device)
- 设备管理
- 状态监控
- 数据同步
- 设备绑定

## 性能优化特性

### 1. 异步编程
- 全异步API设计
- 非阻塞数据库操作
- 异步任务处理

### 2. 缓存策略
- 多级缓存体系
- 智能缓存更新
- 缓存预热机制

### 3. 数据库优化
- 连接池复用
- 查询优化
- 索引策略
- 分页处理

### 4. 静态资源优化
- 资源压缩
- CDN 支持
- 浏览器缓存
- 懒加载

## 部署方案

### 开发环境
```bash
# 启动开发环境
docker-compose -f docker-compose.dev.yml up -d

# 运行应用
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 生产环境
```bash
# 构建镜像
docker build -t ljwx-bigscreen-fastapi:latest .

# Kubernetes 部署
kubectl apply -f k8s/
```

## API 文档

FastAPI 自动生成 API 文档，启动后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 迁移指南

### 从 Flask 迁移步骤
1. 数据模型迁移
2. API 路由重构
3. 业务逻辑迁移
4. 前端模板适配
5. 测试验证

### 兼容性处理
- 保持原有 API 接口兼容
- 渐进式迁移策略
- 数据库结构兼容

## 监控和运维

### 监控指标
- API 响应时间
- 数据库连接池状态
- 缓存命中率
- 内存使用情况
- CPU 使用率

### 日志管理
- 结构化日志
- 日志分级
- 日志轮转
- 日志聚合

## 开发规范

### 代码规范
- PEP 8 编码规范
- 类型注解要求
- 文档字符串规范
- 单元测试覆盖

### 提交规范
- Git 提交规范
- 代码审查流程
- 自动化测试
- 持续集成

## 性能目标

### 响应时间
- API 响应时间 < 100ms
- 页面加载时间 < 2s
- 数据库查询 < 50ms

### 并发能力
- 支持 1000+ 并发连接
- QPS > 5000
- 内存使用 < 512MB

### 可用性
- 服务可用率 > 99.9%
- 故障恢复时间 < 30s
- 零停机部署

## 安全特性

### 认证授权
- JWT 令牌认证
- RBAC 权限控制
- API 访问限制

### 数据安全
- 数据加密传输
- 敏感信息脱敏
- SQL 注入防护

### 网络安全
- CORS 跨域控制
- XSS 防护
- CSRF 防护
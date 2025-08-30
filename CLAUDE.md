# CLAUDE.md - 灵境万象健康管理系统开发指南

## 项目概述

灵境万象健康管理系统是一个基于微服务架构的企业级健康监测平台，包含设备管理、健康数据收集、告警处理、组织管理等核心功能模块。

## 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ljwx-admin    │    │   ljwx-boot     │    │ ljwx-bigscreen  │
│   Vue3管理前端   │ ←→ │   Spring Boot   │ ←→ │   Python Flask  │
│                 │    │   后端API服务    │    │   告警处理引擎   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ljwx-watch    │    │     MySQL       │    │    WebSocket    │
│   设备数据采集   │    │    数据存储      │    │    实时推送      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 开发环境设置

### 数据库配置
- **MySQL 8.0**
  - 数据库名: test
  - 连接信息: localhost:3306
  - 用户名/密码: root/123456

- **Redis 8.0**
  - 连接信息: localhost:6379
  - 密码: 123456
  - 数据库: 1
  - **重要**: Redis 8.x 使用URL连接方式避免认证问题: `redis://default:123456@localhost:6379/1`

### 服务启动命令

#### ljwx-boot (后端API服务)
```bash
cd ljwx-boot
./run-local.sh
```

**API测试登录配置**
- 登录URL: `http://192.168.1.83:3333/proxy-default/auth/user_name`
- POST请求体: 
  ```json
  {
    "userName": "admin", 
    "password": "80a3d119ee1501354755dfc3c4638d74c67c801689efbed4f25f06cb4b1cd776"
  }
  ```

#### ljwx-admin (前端管理界面)
```bash
cd ljwx-admin
pnpm dev
```

#### ljwx-bigscreen (告警处理引擎)
```bash
cd ljwx-bigscreen/bigscreen
python run_bigscreen.py
```

#### ljwx-watch (设备数据采集)
```bash
cd ljwx-watch
python main.py
```

### 构建和部署命令

#### Docker构建
```bash
# 构建boot服务镜像
LOCAL_BUILD=true PLATFORMS=linux/amd64 PUSH_TO_REGISTRY=false ./build-and-push.sh boot

# 构建admin服务镜像  
LOCAL_BUILD=true PLATFORMS=linux/amd64 PUSH_TO_REGISTRY=false ./build-and-push.sh admin

# 构建bigscreen服务镜像
LOCAL_BUILD=true PLATFORMS=linux/amd64 PUSH_TO_REGISTRY=false ./build-and-push.sh bigscreen
```

## 关键优化成果

### 1. 组织架构闭包表优化 ✅ 已完成
- **实施时间**: 2025年8月
- **性能提升**: 查询速度提升100倍 (500ms → 5ms)
- **技术方案**: 基于闭包表(Closure Table)的层级存储优化
- **核心文件**: `docs/组织架构高效存储查询优化方案.md`
- **实施状态**: 完整实施并验证，系统性能显著提升

#### 关键实现
- 新增 `sys_org_closure` 闭包关系表
- 优化组织查询SQL，支持O(1)复杂度查询
- 实现批量组织管理员查询
- 建立完善的闭包表维护机制

### 2. 消息机制与告警机制统一优化方案 📋 新制定
- **规划时间**: 2025年8月
- **核心目标**: 基于闭包表优化成果，构建高效智能告警系统
- **技术方案**: AI驱动的统一告警处理平台
- **方案文档**: `docs/消息机制与告警机制统一优化方案.md`

#### 优化重点
- **高效分发**: 基于闭包表实现毫秒级告警分发
- **智能处理**: AI算法降低误报率至8%以下
- **统一管理**: 整合消息通知和告警处理
- **实时响应**: 构建秒级响应的告警处理链路

#### 预期效果
- 告警分发延迟: 200ms → 5ms (97.5%提升)
- 并发处理能力: 100/秒 → 1000/秒 (1000%提升)  
- 误报率: 15-20% → <8% (60%改善)
- 平均响应时间: 30分钟 → <15分钟 (50%提升)

## 核心功能模块

### 告警处理系统
- **核心引擎**: `ljwx-bigscreen/bigscreen/alert.py`
- **功能特性**: 
  - 多层级告警分发 (用户 → 主管 → 管理员)
  - WebSocket实时推送
  - 微信通知集成
  - 智能告警规则匹配

### 组织架构管理
- **优化方案**: 闭包表存储结构
- **查询性能**: 毫秒级组织关系查询
- **支持功能**: 层级管理、批量查询、动态维护

### 设备数据采集
- **数据流**: 设备 → ljwx-watch → ljwx-bigscreen → 规则匹配 → 告警生成
- **支持设备**: 健康监测设备、SOS设备、摔倒检测设备

## 数据库关键表结构

### 组织架构相关
- `sys_org_units`: 组织基本信息
- `sys_org_closure`: 闭包关系表 (优化核心)
- `sys_user_org`: 用户组织关系

### 告警相关  
- `t_alert_info`: 告警信息主表
- `t_alert_rules`: 告警规则配置
- `t_alert_action_log`: 告警操作日志
- `t_device_message`: 设备消息表

### 配置相关
- `t_wechat_alarm_config`: 微信告警配置
- 其他业务配置表

## 开发规范

### 代码提交规范
- feat: 新功能实现
- fix: 问题修复
- optimization: 性能优化
- refactor: 代码重构
- docs: 文档更新

### 数据库变更规范
1. 重要变更必须先在测试环境验证
2. 提供完整的回滚方案
3. 性能影响评估和测试
4. 详细的变更文档记录

### 测试规范
- 单元测试覆盖率 >80%
- 集成测试覆盖关键业务流程
- 性能测试验证优化效果
- 回归测试确保功能完整性

## 性能监控

### 关键指标
- 告警处理延迟: <10ms
- 组织查询响应时间: <5ms  
- 系统并发处理能力: 1000+ requests/s
- 数据库连接池利用率: <80%

### 监控工具
- 应用性能监控: 集成APM工具
- 数据库监控: MySQL性能指标
- 系统资源监控: CPU、内存、磁盘、网络

## 部署环境

### 生产环境
- 服务器配置: 根据实际需求配置
- 数据库: MySQL主从配置
- 缓存: Redis集群
- 负载均衡: Nginx

### 容器化部署
- Docker镜像构建脚本: `build-and-push.sh`
- Kubernetes配置文件: `k8s/` 目录
- 环境配置管理: ConfigMap和Secret

## 故障排查

### 常见问题
1. **数据库连接问题**: 检查连接池配置和数据库状态
2. **Redis 8.x 认证失败**: 
   - **症状**: `NOAUTH HELLO must be called with the client already authenticated`
   - **解决**: 使用 URL 连接方式 `redis://default:password@host:port/db`
   - **配置**: 在 `application-*.yml` 中设置 `spring.data.redis.url`
3. **告警处理延迟**: 检查队列积压和处理性能
4. **组织查询缓慢**: 验证闭包表数据完整性
5. **WebSocket连接异常**: 检查网络配置和防火墙设置

### 日志位置
- ljwx-boot: `logs/spring.log`
- ljwx-bigscreen: `logs/bigscreen.log`
- ljwx-admin: 浏览器控制台
- ljwx-watch: `logs/watch.log`

## 联系方式

- 技术支持: 通过GitHub Issues提交问题
- 文档反馈: 直接提交PR改进文档
- 紧急故障: 联系系统管理员

---

*最后更新: 2025-08-31*
*版本: v2.1*
*更新内容: 修复Redis 8.x认证问题，更新启动脚本和API登录配置*
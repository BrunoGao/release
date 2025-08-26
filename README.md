# 灵境万象健康管理系统 (LJWX)

![Version](https://img.shields.io/badge/Version-1.3.6-blue.svg)
[![License](https://img.shields.io/badge/License-Apache%20License%202.0-B9D6AF.svg)](./LICENSE)
![Platform](https://img.shields.io/badge/Platform-Multi--architecture-green.svg)

## 📋 项目概述

灵境万象健康管理系统（LJWX）是一套完整的企业级健康监测解决方案，专为工业环境下的可穿戴设备健康数据监控而设计。系统集成了数据采集、实时分析、智能告警、可视化大屏等功能模块，为企业提供全方位的员工健康安全保障。

### 🎯 核心特性

- **🏥 健康数据监控**: 实时采集心率、血压、体温、运动数据等多维度健康指标
- **🚨 智能告警系统**: 多租户告警规则管理，支持微信、消息、大屏推送
- **📊 可视化大屏**: 专业级监控大屏，实时展示健康状态和告警信息
- **📱 移动端应用**: Flutter开发的移动APP，支持数据查看和设备管理
- **⌚ 智能手表集成**: 支持华为Watch4等智能穿戴设备数据采集
- **🏢 多租户架构**: 企业级权限管理，支持租户隔离和告警规则隔离

## 🏗️ 系统架构

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ ljwx-watch  │    │ ljwx-phone  │    │ ljwx-admin  │    │ljwx-bigscreen│
│   智能手表   │ ──▶ │   移动应用   │ ──▶ │  管理后台    │ ──▶ │   监控大屏   │
│  (HarmonyOS)│    │  (Flutter)  │    │   (Vue3)    │    │ (Python)    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │                   │
       └───────────────────┼───────────────────┼───────────────────┘
                           │                   │
                    ┌─────────────┐    ┌─────────────┐
                    │ ljwx-boot   │    │   数据存储   │
                    │  后端API    │◄──▶│ MySQL+Redis │
                    │(Spring Boot)│    │             │
                    └─────────────┘    └─────────────┘
```

## 📂 项目结构

### 🔧 后端服务 (ljwx-boot)
- **Spring Boot 3.3.2 + Java 21** - 现代化微服务架构
- **健康管理模块**: 10+健康指标实时监控、睡眠分析、运动追踪
- **系统管理模块**: 多租户架构、RBAC权限控制、组织管理
- **设备管理模块**: IoT设备生命周期管理、状态监控
- **多租户告警系统**: 智能阈值监控、多级告警处理、租户级别告警规则隔离
- **地理围栏**: 虚拟边界监控、位置告警

### 🖥️ 前端管理 (ljwx-admin)
- **Vue3 + TypeScript + Naive UI** - 现代化管理界面
- **健康数据管理**: ECharts可视化、Excel导出、时间序列分析
- **设备管理**: 电池监控、佩戴状态、设备配置
- **告警管理**: 实时告警监控、规则配置、微信集成
- **用户组织管理**: 分层权限、角色管理、部门架构
- **系统监控**: 性能指标、日志管理、缓存监控

### 📊 监控大屏 (ljwx-bigscreen)
- **Python Flask + Socket.IO** - 高性能实时监控
- **实时数据处理**: 支持1000+设备并发、QPS>1400
- **告警处理引擎**: 多渠道通知、层级分发、WebSocket推送
- **健康分析系统**: AI健康画像、个人基线、Z-score异常检测
- **地图可视化**: 实时位置追踪、告警地点标记
- **性能优化**: Redis缓存、批量查询、连接池管理

### 📱 移动应用 (ljwx-phone)
- **Flutter 3.0+ 跨平台** - 统一iOS/Android体验
- **蓝牙BLE集成**: 自动设备发现、二进制协议、实时同步
- **健康数据可视化**: FL Chart图表、雷达图健康评分
- **管理员模式**: 嵌入式Web界面、SHA认证、角色切换
- **数据同步**: 蓝牙/WiFi双模式、本地缓存、批量上传
- **告警通知**: 实时推送、声音提醒、状态指示

### ⌚ 智能手表 (ljwx-watch)
- **HarmonyOS 3.0 原生应用** - 深度系统集成
- **健康传感器**: 心率、血氧、体温、压力、步数监测
- **电源优化**: 统一定时器、15-18小时续航、智能调度
- **通信协议**: 高级TLV二进制格式、50%数据压缩
- **紧急功能**: SOS按钮、跌倒检测、一键告警
- **实时同步**: 蓝牙BLE/WiFi双通道、离线缓存

## 🚀 最新功能 v1.3.6

### 🔧 多租户告警规则系统实现 (2025-08-26)

#### **告警规则多租户隔离**
- **租户级规则隔离**: 实现告警规则基于 `customer_id` 的完全隔离，不同租户拥有独立的告警规则集
- **默认规则自动克隆**: 新建租户时自动从 `customer_id=0` 克隆默认告警规则
- **多级告警支持**: 支持同一健康指标配置多个告警级别（如心率120-140中级，140-160高级）
- **系统事件匹配**: 告警规则类型与手表系统事件完全匹配，支持直接规则匹配

#### **告警类型国际化支持**
- **英文键值系统**: 告警规则类型使用标准英文格式（如 `HEARTRATE_HIGH_ALERT`）
- **中文显示支持**: 通过数据字典实现英文→中文映射，前端显示用户友好的中文
- **完整映射体系**: 覆盖15种告警类型的完整中英文映射
- **专业化命名**: 与智能手表系统事件命名规范保持一致

#### **数据库优化**
```sql
-- 告警规则表新增字段
ALTER TABLE t_alert_rules ADD COLUMN customer_id BIGINT;

-- 支持多级告警的唯一约束
ALTER TABLE t_alert_rules ADD UNIQUE KEY uk_alert_multi_level 
(rule_type, physical_sign, severity_level, customer_id);

-- 完整的告警类型字典映射
INSERT INTO sys_dict_item (dict_code, value, zh_cn, en_us) VALUES
('alert_type', 'HEARTRATE_HIGH_ALERT', '心率过高告警', 'HEARTRATE_HIGH_ALERT'),
('alert_type', 'SOS_EVENT', 'SOS紧急求助', 'SOS_EVENT');
```

#### **系统架构升级**
- **OrgUnitsChangeListener 扩展**: 新建租户时自动触发告警规则克隆
- **多租户数据隔离**: 查询、创建、更新、删除操作均基于租户ID过滤
- **Redis 缓存优化**: 告警规则缓存键支持租户级别隔离 `alert_rules_{customerId}`
- **前端上下文传递**: 管理界面自动传递当前用户的 `customerId`

---

## 🚀 历史版本 v1.3.3

### 🔧 客户部署配置系统修复 (2025-08-20)

#### **端口配置动态化修复**
- **配置文件读取**: `generate-docker-compose.sh` 现在正确读取 `custom-config.env` 配置
- **端口配置灵活**: 支持客户完全自定义 MySQL、Redis、大屏等服务端口
- **镜像版本同步**: 自动从 `docker-compose.yml` 读取最新镜像版本标签
- **环境变量传递**: 确保所有自定义配置正确传递到生成的容器配置中

#### **修复前后对比**
```bash
# 修复前: 硬编码默认端口
ports:
  - "3306:3306"    # 固定MySQL端口
  - "8001:8001"    # 固定大屏端口

# 修复后: 动态配置端口
ports:
  - "$MYSQL_PORT:3306"     # 从custom-config.env读取
  - "$BIGSCREEN_PORT:$APP_PORT"  # 支持自定义端口映射
```

### 🐳 Docker构建系统优化修复 (2025-08-20)

#### **ljwx-boot Docker构建修复**
- **Maven镜像源优化**: 配置阿里云Maven镜像，解决`No route to host`网络连接问题
- **超时配置优化**: 增加Maven连接和读取超时时间，提高构建稳定性
- **多阶段构建**: 优化Dockerfile，支持ljwx-boot-starter依赖构建和主应用构建
- **网络连接修复**: 解决Docker构建环境中Maven依赖下载失败的问题

#### **技术改进详情**
```dockerfile
# 配置Maven阿里云镜像源
RUN mkdir -p /root/.m2 && \
    echo '<settings>...<mirror>...<url>https://maven.aliyun.com/repository/public</url>...' > /root/.m2/settings.xml

# 增加超时配置
RUN mvn clean install -DskipTests -Dmaven.wagon.http.connectTimeout=60000 -Dmaven.wagon.http.readTimeout=120000
```

### 🔧 蓝牙健康数据上传修复 (2025-08-19)

#### **移动端数据传输优化**
- **数据结构简化**: 移除ljwx-phone上传健康数据最外层的data结构，直接传输核心数据
- **蓝牙传输稳定性**: 优化BLE数据包格式，提高传输成功率和稳定性
- **数据同步效率**: 简化数据封装层次，减少传输开销，提升同步速度
- **兼容性增强**: 确保手表端和服务端数据格式完全匹配，避免解析错误

### 📋 代码分析与文档完善 (2025-08-16)

#### **完整系统分析**
- **深度模块分析**: 完成所有5个模块的详细代码分析
- **技术架构文档**: 新增完整的系统功能模块清单文档
- **API接口梳理**: 详细整理各模块核心API和功能特性
- **性能指标确认**: 验证系统性能数据和技术参数

#### **技术文档体系**
- **[系统功能模块清单](./docs/系统功能模块清单.md)**: 109KB综合技术文档
- **模块功能清单**: ljwx-boot、ljwx-admin、ljwx-bigscreen、ljwx-phone、ljwx-watch
- **架构设计说明**: 详细的技术栈和系统架构分析
- **部署运维指南**: 完整的部署和监控方案

---

## 🚀 历史版本 v1.3.2

### ✨ 告警通知系统完整升级

#### **多渠道通知**
- **企业微信**: 支持企业微信应用消息推送
- **公众号微信**: 支持微信公众号模板消息
- **系统消息**: 内置消息系统，层级分发通知
- **大屏推送**: Critical级别告警实时推送到监控大屏

#### **智能层级通知**
```
设备告警事件
      ↓
   告警规则匹配
      ↓
   ┌─────────────┐
   │ 通知分发策略 │
   └─────────────┘
      ↓         ↓         ↓
  用户通知   部门主管    租户管理员
              ↓            ↓
         (无主管时)   (最终兜底)
```

#### **实时大屏集成**
- **WebSocket实时推送**: Socket.IO支持秒级告警推送
- **专业告警界面**: 科技感弹窗设计，包含告警详情
- **交互功能**: 支持告警确认、音效提醒、ESC关闭
- **地图标记**: 可选的告警位置地图标记功能

### 🛠️ 技术亮点

- **多架构支持**: Docker支持AMD64/ARM64多架构部署
- **性能优化**: 解决N+1查询问题，响应时间从181s优化到<5s
- **高并发处理**: QPS >1400，支持2000+设备并发
- **容错设计**: 微信通知失败自动降级，确保告警可达性
- **智能手表集成**: HarmonyOS原生应用，支持15+小时续航
- **二进制协议**: TLV格式数据传输，压缩率达50%
- **AI健康分析**: 集成DeepSeek R1模型，智能健康建议

## 📋 快速开始

### 环境要求

| 组件 | 版本要求 | 说明 |
|-----|---------|------|
| Java | ≥ JDK 21 | 后端运行环境 |
| Node.js | ≥ 18.0 | 前端构建环境 |  
| Python | ≥ 3.8 | 大屏系统环境 |
| MySQL | ≥ 8.0 | 数据存储 |
| Redis | ≥ 6.0 | 缓存存储 |
| Docker | ≥ 20.10 | 容器化部署(可选) |

### 🐳 快速部署 (推荐)

```bash
# 1. 克隆项目
git clone https://github.com/your-org/ljwx-system.git
cd ljwx-system

# 2. 构建所有Docker镜像
./build-and-push.sh boot      # 构建后端服务
./build-and-push.sh admin     # 构建前端管理
./build-and-push.sh bigscreen # 构建监控大屏

# 3. 一键启动所有服务
docker-compose up -d

# 4. 初始化数据库
mysql -u root -p123456 < client-deployment/client-data.sql

# 5. 访问系统
# 管理后台: http://localhost:3000
# 监控大屏: http://localhost:5001  
# API文档: http://localhost:9998/doc.html
```

### 🔧 Docker构建说明

系统已优化Docker构建流程，解决了网络连接问题：

```bash
# 单独构建各组件
./build-and-push.sh boot      # 后端API服务 (Spring Boot)
./build-and-push.sh admin     # 前端管理系统 (Vue3)
./build-and-push.sh bigscreen # 监控大屏系统 (Python Flask)

# 构建支持多架构 (AMD64/ARM64)
# 镜像自动推送到阿里云容器镜像仓库
```

### ⚙️ 客户部署配置

系统支持完全自定义的端口和服务配置：

```bash
# 修改 custom-config.env 文件
BIGSCREEN_PORT=8002          # 自定义大屏端口
MYSQL_PORT=3307             # 自定义MySQL端口  
REDIS_PORT=6380             # 自定义Redis端口
VITE_BIGSCREEN_URL=http://192.168.1.10:8002  # 大屏访问地址

# 生成动态配置并部署
./deploy-client.sh custom-config.env
```

**特性**:
- 🔄 **动态端口配置**: 根据客户环境自动调整端口映射
- 📦 **镜像版本同步**: 自动使用最新的镜像版本标签  
- 🔧 **环境变量传递**: 完整的配置文件支持
- ✅ **向后兼容**: 保持现有部署的稳定性

### 🔧 开发环境部署

#### 后端服务
```bash
cd ljwx-boot
./run-local.sh
```

#### 前端管理
```bash
cd ljwx-admin
npm install
npm run dev
```

#### 监控大屏
```bash
cd ljwx-bigscreen/bigscreen
python run_bigscreen.py
```

## 📊 系统展示

### 管理后台
- 健康数据总览、实时设备状态监控
- 告警配置管理、用户权限控制
- 数据可视化图表、统计分析报表

### 监控大屏
- 实时健康数据地图、告警状态展示
- Critical告警弹窗、WebSocket实时推送
- 系统性能监控、设备在线状态

### 移动应用
- 个人健康档案、历史数据查询
- 设备绑定管理、消息通知中心
- 健康评分分析、趋势图表展示

## 🔧 配置说明

### 数据库配置
```yaml
# application.yml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/test
    username: root
    password: 123456
```

### 告警通知配置
```python
# 企业微信配置
WECHAT_CORP_ID = "your_corp_id"
WECHAT_AGENT_ID = "your_agent_id" 
WECHAT_SECRET = "your_secret"

# 公众号配置
WECHAT_APPID = "your_appid"
WECHAT_APPSECRET = "your_appsecret"
WECHAT_TEMPLATE_ID = "your_template_id"
```

## 📈 性能指标

- **响应时间**: <3秒 (1000设备规模)
- **并发处理**: QPS >1400 
- **系统可用性**: 99.9%
- **告警及时性**: <5秒 (Critical级别)

## 🔒 安全特性

- **多租户隔离**: 数据完全隔离，权限严格控制
- **API安全**: Sa-Token鉴权，接口权限细化
- **数据加密**: 敏感数据AES加密存储
- **SQL注入防护**: MyBatis-Plus参数化查询

## 📚 技术文档

### 核心文档
- **[系统功能模块清单](./docs/系统功能模块清单.md)** - 完整的系统功能和技术架构说明
- **[告警通知功能完整实现方案](./docs/告警通知功能完整实现方案.md)** - 告警通知系统技术方案

### 部署文档
- **[系统部署指南](./client-deployment/DEPLOY_GUIDE.md)** - Docker容器化部署
- **[离线部署完整指南](./client-deployment/离线部署完整指南.md)** - 离线环境部署

### 开发文档
- **[二次开发文档](./ljwx-bigscreen/docs/二次开发文档.md)** - 大屏系统开发指南
- **[技术架构方案文档](./ljwx-bigscreen/docs/技术架构方案文档.md)** - 系统架构设计
- **[API接口文档](http://localhost:9998/doc.html)** - 在线API文档

### 移动端文档
- **[数据监控解决方案使用指南](./ljwx-phone/数据监控解决方案使用指南.md)** - 移动端使用说明
- **[手表开发和使用指南](./ljwx-watch/手表开发和使用指南.md)** - 智能手表开发指南

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 开源协议

本项目基于 [Apache License 2.0](./LICENSE) 开源协议，仅供学习参考使用。

## 👥 联系我们

- **项目主页**: [GitHub](https://github.com/your-org/ljwx-system)
- **问题反馈**: [Issues](https://github.com/your-org/ljwx-system/issues)
- **技术支持**: support@ljwx.com

---

**© 2024 灵境万象健康管理系统 (LJWX). All rights reserved.**
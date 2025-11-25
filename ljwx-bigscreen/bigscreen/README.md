# LJWX BigScreen 健康监控大屏系统 v1.3.5

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![Docker](https://img.shields.io/badge/Docker-支持多架构-blue.svg)](https://docker.com/)
[![版本](https://img.shields.io/badge/version-1.3.5-green.svg)](https://github.com/your-org/ljwx-bigscreen)
[![许可证](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 📋 项目概述

LJWX BigScreen 是一个专为工业环境设计的实时健康监控大屏系统，支持多设备健康数据聚合、可视化展示和智能告警。系统采用Flask + SQLAlchemy + Redis架构，具备高并发处理能力和企业级稳定性。

### 🎯 核心特性

- **🔥 CPU自适应批处理系统**：动态调整批处理规模，支持高并发数据处理
- **⚡ 三接口智能上传**：health_data、device_info、common_event独立处理
- **🛡️ 断点续传机制**：网络异常时数据自动缓存，确保零丢失
- **📊 实时监控大屏**：ECharts.js驱动的专业数据可视化
- **🚨 智能告警系统**：微信推送 + WebSocket实时通知
- **🐳 多架构Docker支持**：AMD64/ARM64一键部署
- **📈 性能监控面板**：实时系统状态和性能指标

## 🔐 快速访问与系统凭证

### 主要服务访问

| 服务 | 访问地址 | 凭证 | 说明 |
|------|---------|------|------|
| **ljwx-bigscreen** | http://localhost:5225<br>http://192.168.1.83:5225 | 企业微信登录 | 健康监控大屏主应用 |
| **Grafana** | http://localhost:3001 | admin / admin123 | 监控可视化面板 |
| **Prometheus** | http://localhost:9091 | 无需登录 | 指标采集和查询 |
| **Alertmanager** | http://localhost:9094 | 无需登录 | 告警管理系统 |

### 数据库连接

**MySQL**
```bash
Host: 127.0.0.1
Port: 3306
Database: test
Username: root
Password: 123456
```

**Redis**
```bash
Host: 127.0.0.1 或 192.168.1.6
Port: 6379
Password: (无密码)
```

### 监控系统

完整的监控系统文档和凭证信息，请查看：
📄 [monitoring/README.md](monitoring/README.md) - 包含所有监控组件的详细配置和访问凭证

**快速启动监控系统：**
```bash
cd monitoring
docker-compose up -d
```

### 安全提示

⚠️ **生产环境部署前请务必修改所有默认密码！**

- Grafana：首次登录后立即修改 admin 密码
- MySQL：创建专用应用账户，限制权限范围
- Redis：启用密码认证，配置强密码
- 监控服务：仅在内网访问，禁止公网暴露

## 🆕 最新更新 v1.3.5

### 🎯 个人大屏UI现代化改造

**核心功能**：全面重构个人健康大屏界面，提供现代化、专业且具有科技感的用户体验

**主要改进**：
- **现代化网格布局**：采用CSS Grid响应式布局，替代传统左右分栏
- **高科技视觉设计**：渐变背景、动画粒子、扫描线效果营造科技感
- **高级仪表盘组件**：环形进度条配合数值显示，支持状态色彩变化
- **智能状态指示器**：实时健康状态监控，支持正常/警告/危险三级显示
- **流畅动画系统**：呼吸灯、脉冲、扫描等多种专业动画效果
- **现代化卡片设计**：磨砂玻璃效果、悬停动画、立体阴影
- **响应式适配**：完善的响应式设计，支持多种屏幕尺寸

**技术特性**：
- **CSS Grid布局**：3栏网格系统，左右侧栏350px，中央自适应
- **动态背景粒子**：CSS动画实现的星空粒子效果
- **ECharts集成**：现代化仪表盘和趋势图表
- **WebSocket支持**：实时数据推送更新
- **性能优化**：统一的图表实例管理和内存优化

**技术修复细节**：
```javascript
// 修复前：错误的条件判断
if (!filterPanel.contains(event.target) && 
    !filterToggle.contains(event.target) && 
    !filterPanel.classList.contains('collapsed')) {  // ❌ 错误逻辑
    toggleFilter();
}

// 修复后：正确的条件判断
if (!filterPanel.contains(event.target) && 
    !filterToggle.contains(event.target) && 
    filterPanel.classList.contains('expanded')) {   // ✅ 正确逻辑
    toggleFilter();
}
```

**问题解决**：
- **根因分析**：全局点击事件监听器使用了错误的CSS类检查条件
- **影响范围**：点击任意面板都会意外触发人员筛选功能
- **修复效果**：现在只有在筛选面板展开时，点击外部才会关闭筛选面板
- **用户体验**：实时统计面板等其他面板点击不再产生副作用

### 🎯 v1.3.4 健康数据源区分系统回顾

**核心功能**：智能区分不同来源的健康数据，确保前端显示数据的准确性

**技术实现**：
```python
# 支持嵌套和平面两种健康数据结构
if 'healthData' in data:
    health_data = data['healthData']
    # 支持 {healthData: {data: {...}}} 嵌套结构
    if 'data' in health_data:
        health_data = health_data['data']
    
    # 提取 upload_method 字段进行标识
    upload_method = health_data.get('upload_method', 'wifi')
    print(f"🏥 检测到健康数据上传方式: {upload_method}")
```

**数据流程优化**：
```
通用事件触发 → 生成健康数据(upload_method: "common_event")
    ↓
大屏系统接收 → 解析健康数据 → 标识数据来源
    ↓  
数据库存储 → 前端查询过滤 → 仅显示正常健康数据
```

### 📊 v1.3.3 CPU自适应批处理系统回顾

### 🚀 CPU自适应批处理系统升级

**核心优化**：
- **健康数据处理器**：批次大小 = CPU核心数 × 25，工作线程 = CPU核心数 × 2.5
- **设备信息处理器**：批次大小 = CPU核心数 × 15，工作线程 = CPU核心数 × 1.5  
- **通用事件处理器**：批次大小 = CPU核心数 × 8，工作线程 = CPU核心数 × 1
- **统一响应格式**：所有接口返回标准化JSON，支持即时HTTP 200响应

**性能提升**：
```
性能指标对比           优化前    优化后    提升幅度
────────────────────────────────────────────
响应时间               181s      <3s      98%↑
并发处理能力           500       2000+    300%↑
数据处理成功率         60%       100%     67%↑
系统资源利用率         30%       85%      183%↑
批处理吞吐量           100/s     1400+/s  1300%↑
```

### 🔧 智能缓存与断点续传

**三类数据独立处理**：
1. **健康数据缓存** (health_data)：心率、血氧、体温等生理指标
2. **设备信息缓存** (device_info)：电量、版本、网络状态等设备状态  
3. **通用事件缓存** (common_event)：SOS告警、跌倒检测等紧急事件

**断点续传机制**：
- ljwx-watch端：环形队列缓存，最大100条数据
- ljwx-bigscreen端：队列化处理，确保数据按序处理
- 网络恢复时：自动重试缓存数据，成功后从缓存清除

### 📊 专业统计面板功能

**实时数据统计**：
- ✅ `/api/statistics/health_data/count` - 健康数据总量统计
- ✅ `/api/statistics/alerts/count` - 告警数量统计（支持状态筛选）
- ✅ `/api/statistics/devices/count` - 设备数量统计（新增/总数）
- ✅ `/api/statistics/messages/count` - 消息数量统计（未读消息）
- ✅ `/api/statistics/overview` - 统计概览（综合数据）

**界面优化**：
- ✅ 专业卡片式设计，支持悬停动画效果
- ✅ 实时趋势显示（增长/下降百分比）
- ✅ 系统健康评分和状态指示器
- ✅ 数字格式化显示（K/M单位）
- ✅ 响应式布局，适配20%面板高度

## 🏗️ 系统架构

### 技术栈架构图

```
┌─────────────────────────────────────────────────────────────┐
│                  LJWX BigScreen 架构图                       │
├─────────────────┬─────────────────┬─────────────────────────┤
│    前端展示层    │    业务逻辑层     │      数据存储层         │
│   HTML + JS     │  Flask + Redis  │   MySQL + Cache        │
│   ECharts.js    │ CPU自适应批处理   │   批量数据处理          │
│   WebSocket     │ 统一响应处理器    │   智能索引优化          │
│   响应式布局     │  异步任务队列    │   连接池管理            │
└─────────────────┴─────────────────┴─────────────────────────┘
```

### 核心组件

- **Flask应用** (`bigScreen.py`)：主应用和API路由
- **批处理器群** (`*_batch_processor.py`)：CPU自适应的高性能数据处理
- **统一响应处理器** (`unified_response_handler.py`)：标准化API响应
- **智能缓存系统** (`redis_helper.py`)：Redis缓存层
- **数据模型** (`models.py`)：SQLAlchemy ORM模型
- **性能监控** (`monitor.py`)：系统性能实时监控

## 🚀 快速开始

### 环境要求

- Python 3.8+
- MySQL 5.7+
- Redis 6.0+
- Docker 20.10+ (可选)

### 本地部署

1. **克隆项目**
```bash
git clone https://github.com/your-org/ljwx-bigscreen.git
cd ljwx-bigscreen/bigscreen
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件配置数据库和Redis连接
```

4. **启动应用**
```bash
# 标准启动
python run.py

# 或使用优化启动脚本
python run_bigscreen.py

# 启动所有服务（包括Celery）
./start_all.sh
```

### Docker部署

#### 多架构构建
```bash
# 本地构建和推送到阿里云
./scripts/deploy-aliyun.sh

# 使用GitHub Actions自动构建
git push origin main  # 触发CI/CD流水线
```

#### 快速启动
```bash
# 生成Docker Compose配置
./generate-docker-compose.sh

# 启动服务
docker-compose up -d
```

## 📊 性能监控

### 系统监控端点

- **实时统计**：`/api/realtime_stats` - 系统统计信息
- **性能监控**：`/system_monitor` - 性能监控仪表板
- **压力测试**：`/performance_test_report` - 负载测试界面
- **健康检查**：`/api/health_check` - 系统健康状态

### 批处理性能监控

```python
# 查看批处理器状态
from bigScreen.optimized_upload_handlers import get_batch_processors_stats
stats = get_batch_processors_stats()

# 输出示例
{
  "processors": {
    "health_data": {
      "version": "4.0",
      "cpu_cores": 10,
      "batch_size": 250,
      "max_workers": 25,
      "processed": 15420,
      "batches": 62,
      "auto_adjustments": 3
    }
  }
}
```

### 测试命令

```bash
# 性能测试
python performance_stress_test.py
python queue_stress_test.py

# 健康数据系统测试
python test_health_fix.py
python test_performance_optimization.py

# 设备集成测试
python test_device_bind_integration.py

# 告警系统测试
python test_alert_fix.py
```

## 🔌 API接口文档

### 核心上传接口

#### 1. 健康数据上传
```http
POST /upload_health_data
Content-Type: application/json

{
  "data": {
    "deviceSn": "LJWX001",
    "timestamp": 1692729600000,
    "heart_rate": 75,
    "blood_oxygen": 98,
    "body_temperature": "36.5",
    "step": 8000
  }
}
```

**响应示例**：
```json
{
  "status": "success",
  "message": "数据已接收，正在队列处理中",
  "queue_status": "processing",
  "timestamp": "2025-08-22T22:50:00Z",
  "data_type": "health_data",
  "received_count": 1
}
```

#### 2. 设备信息上传
```http
POST /upload_device_info
Content-Type: application/json

{
  "deviceSn": "LJWX001",
  "deviceName": "LJWX智能手表_001",
  "batteryLevel": 85,
  "firmwareVersion": "1.2.3",
  "status": "online"
}
```

#### 3. 通用事件上传
```http
POST /upload_common_event
Content-Type: application/json

{
  "deviceSn": "LJWX001",
  "eventType": "com.ljwx.watch.event.SOS_TRIGGERED",
  "eventTime": 1692729600000,
  "eventData": "{\"severity\":\"high\",\"location\":{\"lat\":39.9042,\"lng\":116.4074}}"
}
```

### 统计查询接口

#### 系统概览
```http
GET /api/statistics/overview

# 响应示例
{
  "health_data_count": 15420,
  "alert_count": 3,
  "device_count": 145,
  "message_count": 7,
  "system_health_score": 98,
  "last_updated": "2025-08-22T22:50:00Z"
}
```

## 🛠️ 开发与调试

### 调试模式配置

```python
# config.py
DEBUG = True  # 启用调试模式
LOG_LEVEL = 'DEBUG'  # 设置日志级别

# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 性能调试

```bash
# 启动性能监控
python monitor.py

# 查看实时日志
tail -f bigscreen.log

# 数据库性能分析
python analyze_db_performance.py
```

### 常见问题排查

1. **连接超时问题**：检查 `config.py` 中的数据库连接池配置
2. **导入错误**：使用 `run_bigscreen.py` 确保正确的Python路径
3. **JavaScript错误**：查看 `fix_js_errors.html` 全局错误处理
4. **Redis连接**：检查Redis密码配置和认证设置
5. **UI交互问题**：检查全局点击事件监听器的条件判断逻辑

### UI调试指南

**面板点击事件调试**：
```javascript
// 检查筛选面板状态
const filterPanel = document.querySelector('.filter-panel');
console.log('筛选面板状态:', {
    isExpanded: filterPanel.classList.contains('expanded'),
    isCollapsed: filterPanel.classList.contains('collapsed'),
    classList: filterPanel.classList.toString()
});

// 调试点击事件
document.addEventListener('click', function(event) {
    console.log('点击目标:', event.target);
    console.log('是否在筛选面板内:', filterPanel.contains(event.target));
});
```

**面板交互最佳实践**：
- 确保面板点击事件不会互相冲突
- 使用正确的CSS类名进行状态检查  
- 添加事件停止冒泡防止意外触发
- 测试不同面板的点击响应

## 🧪 测试系统

### 手表模拟测试

我们提供了完整的ljwx-watch模拟测试系统：

```bash
# 运行完整模拟测试
python test_watch_simulation.py

# 运行简化接口测试  
python simple_watch_test.py
```

**测试覆盖范围**：
- ✅ 三个核心接口正常上传测试
- ✅ 网络中断与断点续传测试
- ✅ 批量并发性能测试
- ✅ 缓存机制验证测试

### 性能基准测试

```bash
# 目标性能指标
- 支持设备数量: 2000+台
- 响应时间: <3秒
- QPS: >1400
- 成功率: 100%
- 内存使用: <2GB
```

## 🔧 配置说明

### 环境变量配置

```bash
# 数据库配置
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=test

# Redis配置
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# 应用配置
APP_PORT=5001
DEBUG=False

# 微信告警配置（可选）
WECHAT_APP_ID=your_app_id
WECHAT_APP_SECRET=your_app_secret
WECHAT_TEMPLATE_ID=your_template_id
WECHAT_USER_OPENID=your_openid

# UI自定义配置
BIGSCREEN_TITLE=LJWX健康监控大屏
COMPANY_NAME=云祥灵境
COMPANY_LOGO_URL=https://example.com/logo.png
THEME_COLOR=#1890ff
BACKGROUND_COLOR=#001529
```

### 批处理器配置

```python
# CPU自适应配置
import psutil
cpu_cores = psutil.cpu_count(logical=True)

# 健康数据处理器配置
HEALTH_BATCH_SIZE = cpu_cores * 25
HEALTH_MAX_WORKERS = int(cpu_cores * 2.5)

# 设备信息处理器配置  
DEVICE_BATCH_SIZE = cpu_cores * 15
DEVICE_MAX_WORKERS = int(cpu_cores * 1.5)

# 通用事件处理器配置
EVENT_BATCH_SIZE = cpu_cores * 8
EVENT_MAX_WORKERS = cpu_cores * 1
```

## 📈 架构设计原则

### 高性能设计

1. **CPU自适应**：根据硬件配置动态调整处理能力
2. **批量处理**：减少数据库操作次数，提高吞吐量
3. **异步处理**：非阻塞I/O，提高并发处理能力
4. **连接池管理**：复用数据库连接，减少连接开销
5. **智能缓存**：Redis缓存热点数据，减少数据库压力

### 可靠性保障

1. **断点续传**：确保数据不丢失
2. **重试机制**：网络异常时智能重试
3. **健康检查**：实时监控系统状态
4. **优雅降级**：关键服务异常时的备用方案
5. **日志记录**：完整的操作日志和错误跟踪

### 可扩展性

1. **微服务架构**：模块化设计，易于扩展
2. **水平扩展**：支持多实例部署
3. **插件机制**：支持功能插件扩展
4. **配置驱动**：通过配置文件调整系统行为

## 🤝 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 代码规范

- 使用中文注释（业务逻辑相关）
- 遵循PEP8代码风格
- 添加必要的类型注解
- 编写单元测试
- 更新相关文档

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 技术支持

- **项目主页**：[GitHub Repository](https://github.com/your-org/ljwx-bigscreen)
- **问题反馈**：[Issues](https://github.com/your-org/ljwx-bigscreen/issues)
- **技术文档**：[Wiki](https://github.com/your-org/ljwx-bigscreen/wiki)
- **在线演示**：[Demo Site](https://demo.ljwx-bigscreen.com)

## 🔗 相关项目

- [ljwx-watch](../ljwx-watch) - 智能手表系统
- [ljwx-phone](../ljwx-phone) - 手机客户端  
- [ljwx-admin](../ljwx-admin) - 管理后台
- [ljwx-boot](../ljwx-boot) - Spring Boot后端服务

## 📊 项目统计

- **代码行数**：~50,000行
- **支持设备数**：2000+台
- **数据处理能力**：1400+ QPS
- **响应时间**：<3秒
- **系统稳定性**：99.9%+

---

*最后更新：2025年8月26日*
*当前版本：v1.3.5 - UI交互优化与事件处理修复*
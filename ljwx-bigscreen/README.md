# LJWX BigScreen 健康监控大屏系统

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![Docker](https://img.shields.io/badge/Docker-支持多架构-blue.svg)](https://docker.com/)
[![版本](https://img.shields.io/badge/version-1.3.5-green.svg)](https://github.com/your-org/ljwx-bigscreen)
[![许可证](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 🚀 快速开始

LJWX BigScreen 是一个专为工业环境设计的实时健康监控大屏系统，支持多设备健康数据聚合、可视化展示和智能告警。

### 启动应用

```bash
# 进入主目录
cd bigscreen

# 标准启动
python run.py

# 或使用优化启动脚本  
python bigScreen/run_bigscreen.py

# 启动所有服务（包括Celery）
./start_all.sh
```

### Docker部署

```bash
# 生成Docker Compose配置
cd bigscreen
./generate-docker-compose.sh

# 启动服务
docker-compose up -d
```

## 📊 核心功能

- **🔥 CPU自适应批处理系统**：动态调整批处理规模，支持高并发数据处理
- **⚡ 三接口智能上传**：health_data、device_info、common_event独立处理  
- **🛡️ 断点续传机制**：网络异常时数据自动缓存，确保零丢失
- **📊 实时监控大屏**：ECharts.js驱动的专业数据可视化
- **🚨 智能告警系统**：微信推送 + WebSocket实时通知
- **🐳 多架构Docker支持**：AMD64/ARM64一键部署

## 🔗 访问地址

- **主大屏**：http://localhost:5001/main?customerId=1
- **系统监控**：http://localhost:5001/system_monitor
- **性能测试**：http://localhost:5001/performance_test_report
- **健康检查**：http://localhost:5001/api/health_check

## 📋 目录结构

```
ljwx-bigscreen/
├── bigscreen/                 # 主应用目录
│   ├── bigScreen/            # Flask应用核心
│   │   ├── bigScreen.py      # 主应用文件
│   │   ├── templates/        # HTML模板
│   │   ├── static/          # 静态资源
│   │   └── *_processor.py   # 批处理器
│   ├── run.py               # 应用入口
│   ├── config.py            # 配置文件
│   ├── requirements.txt     # Python依赖
│   └── README.md           # 详细文档
├── scripts/                 # 部署脚本
├── k8s/                    # Kubernetes配置
├── tests/                  # 测试框架
└── docs/                   # 项目文档
```

## 🔧 环境要求

- Python 3.8+
- MySQL 5.7+
- Redis 6.0+
- Docker 20.10+ (可选)

## 📈 性能指标

- **支持设备数**：2000+台
- **数据处理能力**：1400+ QPS  
- **响应时间**：<3秒
- **系统稳定性**：99.9%+

## 🆕 最新更新 v1.3.5

### UI交互优化与事件处理修复

- **修复面板点击冲突**：解决实时统计面板错误触发人员筛选面板的问题
- **事件处理优化**：完善全局点击事件监听器的条件判断逻辑
- **界面响应优化**：提升面板交互的精确性和稳定性

## 📚 详细文档

完整的技术文档、API接口说明、部署指南等请查看：

**👉 [详细文档](bigscreen/README.md)**

## 🤝 技术支持

- **项目主页**：[GitHub Repository](https://github.com/your-org/ljwx-bigscreen)
- **问题反馈**：[Issues](https://github.com/your-org/ljwx-bigscreen/issues)
- **在线演示**：http://localhost:5001/main?customerId=1

## 🔗 相关项目

- [ljwx-watch](../ljwx-watch) - 智能手表系统
- [ljwx-phone](../ljwx-phone) - 手机客户端  
- [ljwx-admin](../ljwx-admin) - 管理后台
- [ljwx-boot](../ljwx-boot) - Spring Boot后端服务

---

*最后更新：2025年8月26日*
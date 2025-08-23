# CI/CD 基础服务统一构建方案

## 🎯 目标
- 解决端口冲突问题，统一使用3开头端口
- 简化架构，移除冗余配置
- 提供一键式部署体验

## 📋 端口规划

### 服务端口分配
```
服务名称          | Web端口 | 额外端口 | 说明
-----------------|---------|---------|------------------
Gitea           | 33000   | 32222   | Git服务 + SSH
Jenkins         | 38080   | 35000   | CI/CD + Agent通信  
Registry        | 35001   | -       | Docker镜像仓库
Registry UI     | 35002   | -       | 镜像仓库界面
Prometheus      | 37001   | -       | 监控(预留)
Grafana         | 37002   | -       | 监控面板(预留)
```

## 🚀 有序搭建步骤

### 阶段1: 环境准备 (5分钟)
```bash
# 1. 停止现有服务，避免冲突
./scripts/cleanup-existing.sh

# 2. 创建统一网络和目录
./scripts/init-environment.sh

# 3. 检查端口可用性
./scripts/check-ports.sh
```

### 阶段2: 基础服务部署 (10分钟)
```bash
# 1. 启动Docker Registry (最基础)
./scripts/deploy-registry.sh

# 2. 启动Gitea (代码仓库)
./scripts/deploy-gitea.sh

# 3. 验证基础服务
./scripts/verify-basic-services.sh
```

### 阶段3: CI/CD部署 (15分钟)
```bash
# 1. 启动Jenkins (完全自动化配置)
./scripts/deploy-jenkins.sh

# 2. 配置服务集成
./scripts/setup-integration.sh

# 3. 创建示例项目
./scripts/create-demo-projects.sh
```

### 阶段4: 验证和优化 (5分钟)
```bash
# 1. 完整功能测试
./scripts/run-integration-tests.sh

# 2. 性能优化
./scripts/optimize-services.sh

# 3. 创建维护计划
./scripts/setup-maintenance.sh
```

## 📂 建议的目录结构整理

```
infra/
├── configs/                 # 统一配置文件
│   ├── gitea.env           # Gitea环境变量
│   ├── jenkins.env         # Jenkins环境变量
│   └── registry.env        # Registry环境变量
├── docker/
│   └── compose/
│       ├── core-services.yml    # 核心服务组合
│       ├── gitea.yml           # Gitea独立配置
│       ├── jenkins.yml         # Jenkins独立配置
│       └── registry.yml        # Registry独立配置
├── jenkins/
│   ├── casc/               # Configuration as Code
│   ├── shared-library/    # Pipeline共享库
│   └── templates/          # 项目模板
├── scripts/                # 部署和管理脚本
│   ├── deploy/            # 部署脚本
│   ├── maintenance/       # 维护脚本
│   └── utils/            # 工具脚本
└── docs/                  # 文档
    ├── deployment.md      # 部署指南
    ├── maintenance.md     # 维护指南
    └── troubleshooting.md # 故障排查
```

## 🔧 关键配置变更

### 服务访问地址
```
原来                    →    现在
http://localhost:3000   →    http://localhost:33000    (Gitea)
http://localhost:8081   →    http://localhost:38080    (Jenkins)
http://localhost:5001   →    http://localhost:35001    (Registry)
http://localhost:5002   →    http://localhost:35002    (Registry UI)
```

### 环境变量统一
```bash
# configs/global.env
GITEA_PORT=33000
GITEA_SSH_PORT=32222
GITEA_URL=http://localhost:33000

JENKINS_PORT=38080
JENKINS_AGENT_PORT=35000
JENKINS_URL=http://localhost:38080

REGISTRY_PORT=35001
REGISTRY_UI_PORT=35002
REGISTRY_URL=localhost:35001
```

## ⚡ 一键部署命令

```bash
# 完整自动化部署
./build-infra.sh --full-auto

# 分步骤部署
./build-infra.sh --step-by-step

# 仅更新端口配置
./build-infra.sh --update-ports-only
```

## 📊 部署验证检查点

### 基础服务检查
- [ ] Docker Registry 响应正常 (http://localhost:35001/v2/)
- [ ] Registry UI 界面可访问 (http://localhost:35002)
- [ ] Gitea 服务启动正常 (http://localhost:33000)
- [ ] Gitea 健康检查通过 (http://localhost:33000/api/healthz)

### CI/CD功能检查  
- [ ] Jenkins 自动配置完成 (http://localhost:38080)
- [ ] Jenkins 管理员登录成功 (admin/admin123)
- [ ] Gitea 集成配置正确
- [ ] 多平台构建环境就绪
- [ ] 示例Pipeline创建成功

### 集成测试检查
- [ ] Gitea Webhook 触发Jenkins构建
- [ ] 多平台镜像构建成功
- [ ] 镜像推送到Registry正常
- [ ] 从Registry拉取镜像正常

## 🛡️ 安全和优化

### 安全加固
- Jenkins运行在非root用户下
- 使用环境变量管理敏感信息
- 网络隔离和访问控制
- 定期安全更新

### 性能优化
- 合理的资源限制配置
- 定期清理无用数据
- 监控服务性能指标
- 自动化备份策略

## 🔄 维护计划

### 日常维护
```bash
# 服务健康检查
./scripts/health-check.sh

# 数据备份
./scripts/backup-all.sh

# 系统清理
./scripts/cleanup-system.sh
```

### 定期维护
- 每周：服务状态检查和日志清理
- 每月：完整备份和性能优化
- 每季度：安全更新和配置审查

## 📞 技术支持

- 配置问题: 查看 docs/troubleshooting.md
- 性能优化: 查看 docs/optimization.md  
- 升级指南: 查看 docs/upgrade.md
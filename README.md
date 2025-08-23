# Mac Studio M2 企业级 CI/CD 基础设施

## 🚀 完全自动化部署 - 已验证可用 ✅

这是一套完整的企业级CI/CD基础设施，专为Mac Studio M2环境优化，支持**一键自动化部署**，无需手动配置。

### ⚡ 快速开始

```bash
# 一键自动化部署所有服务
./build-infra.sh --full-auto

# 分步骤部署（逐步确认）
./build-infra.sh --step-by-step

# 验证现有服务
./build-infra.sh --verify
```

### 🌐 服务访问地址

部署完成后，通过以下地址访问服务：

| 服务 | 地址 | 用途 | 默认账号 |
|------|------|------|----------|
| **Gitea** | http://localhost:33000 | Git代码仓库 + Actions | 需要初始化 |
| **Jenkins** | http://localhost:38080 | CI/CD平台 | admin / admin123 |
| **Registry** | http://localhost:35001 | Docker镜像仓库 | 无认证 |
| **Registry UI** | http://localhost:35002 | 镜像管理界面 | 无认证 |

**SSH访问：**
```bash
# Gitea SSH克隆 (端口32222)
git clone ssh://git@localhost:32222/username/repository.git
```

### 🎯 核心特性

- ✅ **一键部署**: 完全自动化，15分钟内完成所有配置
- ✅ **端口优化**: 统一使用3开头端口，避免冲突
- ✅ **多平台构建**: 支持 linux/amd64 + linux/arm64
- ✅ **Configuration as Code**: Jenkins零手动配置
- ✅ **企业级功能**: 完整的CI/CD流水线支持
- ✅ **健康监控**: 自动化服务状态检查
- ✅ **数据持久化**: 所有数据自动备份和恢复

### 📋 端口分配

```
服务端口分配（避免冲突）:
├── Gitea:           33000 (Web) + 32222 (SSH)
├── Jenkins:         38080 (Web) + 35000 (Agent)
├── Docker Registry: 35001 (API) + 35002 (UI)
└── 预留监控端口:    37001+ (Prometheus等)
```

### 🏗️ 架构组件

**核心服务：**
- **Jenkins LTS**: CI/CD服务器，基于JDK21
- **Gitea 1.21**: 轻量级Git服务，支持Actions
- **Docker Registry**: 本地镜像仓库
- **Registry UI**: 可视化镜像管理

**环境信息：**
- **硬件**: Mac Studio M2 Ultra (24核CPU, 76核GPU, 192GB内存)
- **系统**: macOS Sequoia 15.7
- **容器**: Docker Desktop + OrbStack优化
- **网络**: 统一cicd-network网络

### 📂 项目结构

```
infra/
├── build-infra.sh              # 🌟 一键部署脚本
├── configs/
│   └── global.env              # 统一环境配置
├── docker/compose/             # Docker编排配置
│   ├── gitea-compose.yml       # Gitea服务
│   ├── jenkins-simple.yml     # Jenkins服务
│   └── registry-simple.yml    # Registry服务
├── jenkins/
│   ├── casc/jenkins.yaml      # Jenkins自动配置
│   ├── shared-library/        # Pipeline共享库
│   └── templates/             # 项目模板
├── scripts/
│   ├── maintenance/           # 维护脚本
│   └── utils/                # 工具脚本
└── docs/                      # 文档
```

### 🔧 管理命令

```bash
# 部署管理
./build-infra.sh --full-auto      # 完全自动化部署 (推荐)
./build-infra.sh --step-by-step   # 分步骤部署
./build-infra.sh --cleanup        # 清理所有服务
./build-infra.sh --verify         # 验证服务状态

# 日常维护
./scripts/maintenance/health-check.sh  # 健康检查
./scripts/utils/show-logs.sh [service] # 查看日志

# 传统管理脚本 (保留兼容)
./jenkins-manager.sh [status|start|stop|backup|health]
```

### 🚀 CI/CD功能特性

#### Jenkins自动配置 (CasC)
- ✅ **50+插件自动安装**: Docker, Gitea, Pipeline, 多平台构建等
- ✅ **工具自动配置**: Git, Maven, Gradle, NodeJS, Docker, Python
- ✅ **凭据模板**: Gitea, Registry, SSH凭据预配置
- ✅ **云配置**: Docker和Kubernetes云支持
- ✅ **示例作业**: 多平台构建和系统监控作业

#### 多平台构建支持
```groovy
// 自动支持的构建平台
pipeline {
    environment {
        PLATFORMS = 'linux/amd64,linux/arm64'
        REGISTRY = 'localhost:35001'
    }
    stages {
        stage('多平台构建') {
            steps {
                buildMultiPlatformImage([
                    imageName: "${REGISTRY}/app:${BUILD_NUMBER}",
                    platforms: env.PLATFORMS
                ])
            }
        }
    }
}
```

### 📊 部署验证

部署完成后，系统会自动验证：

- ✅ **容器状态**: 所有服务容器正常运行
- ✅ **端口监听**: 所有端口正确绑定
- ✅ **API响应**: 所有服务API正常响应
- ✅ **健康检查**: Gitea和Registry健康检查通过
- ✅ **Web界面**: 所有Web界面可正常访问

### 🛠️ 故障排查

#### 常见问题

**端口占用：**
```bash
# 检查端口占用
lsof -i :33000,38080,35001,35002

# 清理并重新部署
./build-infra.sh --cleanup
./build-infra.sh --full-auto
```

**服务启动失败：**
```bash
# 查看服务日志
./scripts/utils/show-logs.sh [gitea|jenkins|registry|all]

# 健康检查
./scripts/maintenance/health-check.sh
```

**配置修改：**
- 主配置文件: `configs/global.env`
- Jenkins配置: `docker/compose/jenkins/casc/jenkins.yaml`
- 修改后重新部署生效

### 💡 最佳实践

#### CI/CD流程
1. **代码管理**: 在Gitea中创建仓库和组织
2. **Pipeline配置**: 使用预置模板快速创建
3. **多平台构建**: 自动支持AMD64和ARM64
4. **镜像管理**: Registry UI可视化管理镜像

#### 维护建议
- **定期备份**: 使用内置备份脚本
- **健康监控**: 定期运行健康检查
- **更新管理**: 定期更新Docker镜像
- **日志管理**: 定期清理服务日志

### 📈 性能优化

**资源配置优化：**
- Jenkins JVM: `-Xmx2g -Xms1g`
- 构建并发: 支持多个并行构建
- 镜像缓存: 本地Registry加速构建
- 网络优化: 统一Docker网络提高通信效率

### 🔄 升级和扩展

#### 监控扩展 (预留)
```bash
# 监控服务端口预留
PROMETHEUS_PORT=37001
GRAFANA_PORT=37002
```

#### Kubernetes集成
- Jenkins Kubernetes插件已预配置
- 支持K8s动态Agent
- 多环境部署支持

### 📞 技术支持

- **快速开始**: 查看 `QUICK_START.md`
- **详细规划**: 查看 `BUILD_PLAN.md`
- **配置说明**: 查看 `CLAUDE.md`
- **问题排查**: 查看 `docs/troubleshooting.md`

### 🎉 版本信息

- **当前版本**: v2.0 (统一端口版本)
- **Jenkins版本**: LTS (JDK21)
- **Gitea版本**: 1.21
- **Registry版本**: 2.x
- **最后更新**: 2025-01-23

### 📄 许可证

MIT License

---

## 🚀 立即开始

```bash
# 克隆项目
git clone <your-repo-url>
cd infra

# 一键部署所有服务
./build-infra.sh --full-auto

# 访问服务
open http://localhost:33000   # Gitea
open http://localhost:38080   # Jenkins (admin/admin123)
open http://localhost:35002   # Registry UI
```

**部署时间**: 约10-15分钟  
**服务数量**: 4个核心服务  
**支持平台**: Mac Studio M2 + Docker Desktop
# 🚀 快速开始指南

## 一键部署 (推荐)

```bash
# 进入项目目录
cd /Users/brunogao/work/infra

# 一键自动部署所有服务
./build-infra.sh --full-auto
```

## 服务访问地址

部署完成后，您可以通过以下地址访问服务：

| 服务 | 地址 | 用途 |
|------|------|------|
| **Gitea** | http://localhost:33000 | Git代码仓库 |
| **Jenkins** | http://localhost:38080 | CI/CD平台 (admin/admin123) |
| **Registry** | http://localhost:35001 | Docker镜像仓库 |
| **Registry UI** | http://localhost:35002 | 镜像仓库管理界面 |

## SSH访问

```bash
# Gitea SSH克隆 (端口32222)
git clone ssh://git@localhost:32222/username/repository.git
```

## 验证部署

```bash
# 检查所有服务健康状态
./scripts/maintenance/health-check.sh

# 查看服务日志
./scripts/utils/show-logs.sh all
```

## 常用管理命令

```bash
# 完全自动化部署
./build-infra.sh --full-auto

# 分步骤部署 (逐步确认)
./build-infra.sh --step-by-step  

# 清理所有服务
./build-infra.sh --cleanup

# 仅运行验证测试
./build-infra.sh --verify

# 健康检查
./scripts/maintenance/health-check.sh

# 查看日志
./scripts/utils/show-logs.sh [gitea|jenkins|registry|all]
```

## 故障排查

### 端口冲突
如果遇到端口占用问题：
```bash
# 检查端口占用
lsof -i :33000,38080,35001,35002,32222,35000

# 清理现有服务
./build-infra.sh --cleanup
```

### 服务启动失败
```bash
# 查看具体服务日志
./scripts/utils/show-logs.sh [服务名] -f

# 重新部署
./build-infra.sh --cleanup
./build-infra.sh --full-auto
```

### 配置修改
主要配置文件：
- `configs/global.env` - 全局环境变量
- `docker/compose/*.yml` - 服务编排配置
- `jenkins/casc/jenkins.yaml` - Jenkins自动配置

修改配置后重新部署：
```bash
./build-infra.sh --cleanup
./build-infra.sh --full-auto
```

## 下一步操作

1. **配置Gitea**
   - 访问 http://localhost:33000
   - 创建管理员账号
   - 创建组织和仓库

2. **配置Jenkins**
   - 访问 http://localhost:38080 
   - 使用 admin/admin123 登录
   - 验证自动配置是否生效

3. **测试CI/CD流程**
   - 在Gitea中推送代码
   - 观察Jenkins自动构建
   - 验证镜像推送到Registry

## 技术支持

- 部署问题: 查看 `BUILD_PLAN.md`
- 配置详情: 查看 `CLAUDE.md`
- 故障排查: 查看 `docs/troubleshooting.md`
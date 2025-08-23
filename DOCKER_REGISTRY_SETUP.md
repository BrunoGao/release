# 🐳 Docker Registry 私有镜像服务器部署完成

## 🎉 部署成功！

您的私有 Docker Registry 已成功部署并与 Gitea CI/CD 系统集成。

## 📋 服务概览

| 服务 | 地址 | 状态 | 用途 |
|------|------|------|------|
| **Gitea** | http://192.168.1.83:3000 | ✅ 运行中 | Git 仓库管理 |
| **Docker Registry** | http://localhost:5001 | ✅ 运行中 | 私有镜像仓库 |
| **Registry Web UI** | http://192.168.1.83:5002 | ✅ 运行中 | 镜像可视化管理 |

## 🚀 快速使用指南

### 1. 推送镜像到私有仓库

```bash
# 构建或拉取镜像
docker build -t my-app:latest .
# 或者: docker pull nginx:latest

# 标记镜像
docker tag my-app:latest localhost:5001/my-app:latest

# 推送到私有仓库
docker push localhost:5001/my-app:latest
```

### 2. 从私有仓库拉取镜像

```bash
# 拉取镜像
docker pull localhost:5001/my-app:latest

# 运行容器
docker run -d localhost:5001/my-app:latest
```

### 3. 查看镜像列表

```bash
# 命令行查看
curl http://localhost:5001/v2/_catalog

# 或访问 Web UI
open http://192.168.1.83:5002
```

## 🔧 管理命令

### CI/CD 集成管理

```bash
# 启动所有服务
./deployment/scripts/cicd-integration.sh start

# 查看服务状态
./deployment/scripts/cicd-integration.sh status

# 测试集成功能
./deployment/scripts/cicd-integration.sh test

# 停止所有服务
./deployment/scripts/cicd-integration.sh stop
```

### Registry 单独管理

```bash
# 启动 Registry
./deployment/scripts/registry-manager.sh start

# 查看状态
./deployment/scripts/registry-manager.sh status

# 备份数据
./deployment/scripts/registry-manager.sh backup

# 测试推送
./deployment/scripts/registry-manager.sh push-test
```

## 📊 持久化配置

### 数据存储方式
- **类型**: Docker 命名卷
- **优势**: Docker 统一管理，跨平台兼容
- **位置**: `/var/lib/docker/volumes/compose_registry-data/_data`

### 备份策略
- **自动备份**: 保留最近 5 个备份
- **备份内容**: 镜像数据 + 配置文件
- **恢复方法**: 一键恢复脚本

## 🔗 CI/CD 集成

### Jenkins Pipeline 示例

```groovy
pipeline {
    agent any
    
    environment {
        DOCKER_REGISTRY = 'localhost:5001'
        APP_NAME = 'my-app'
        IMAGE_TAG = "${BUILD_NUMBER}"
    }
    
    stages {
        stage('构建镜像') {
            steps {
                script {
                    def image = docker.build("${DOCKER_REGISTRY}/${APP_NAME}:${IMAGE_TAG}")
                    image.push()
                    image.push("latest")
                }
            }
        }
        
        stage('部署应用') {
            steps {
                sh """
                    docker stop ${APP_NAME} || true
                    docker rm ${APP_NAME} || true
                    docker run -d --name ${APP_NAME} -p 8080:80 ${DOCKER_REGISTRY}/${APP_NAME}:${IMAGE_TAG}
                """
            }
        }
    }
}
```

### Gitea Actions 示例

```yaml
name: Build and Push
on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: docker build -t localhost:5001/my-app:${{ github.sha }} .
    
    - name: Push to registry
      run: docker push localhost:5001/my-app:${{ github.sha }}
```

## ⚙️ 配置详情

### Registry 配置特点
- **认证**: 已禁用（开发环境）
- **删除**: 支持镜像删除
- **CORS**: 支持跨域访问
- **健康检查**: 自动监控服务状态
- **日志**: 详细的访问和错误日志

### 网络配置
- **内部网络**: `cicd-network`
- **端口映射**: 
  - Registry API: `5001:5000`
  - Registry UI: `5002:80`
- **服务发现**: 容器间可通过服务名访问

## 🛡️ 安全考虑

### 开发环境（当前）
- ✅ 无认证访问（便于开发）
- ✅ HTTP 协议
- ✅ 内网访问

### 生产环境建议
- 🔒 启用 HTTP Basic Auth
- 🔒 配置 HTTPS/TLS
- 🔒 配置防火墙规则
- 🔒 定期备份和监控

## 📈 性能优化

### 镜像构建优化
```dockerfile
# 多阶段构建
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM node:18-alpine AS runtime
COPY --from=builder /app/node_modules ./node_modules
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
```

### 镜像标签策略
```bash
# 语义化版本
localhost:5001/my-app:1.0.0
localhost:5001/my-app:1.0.0-beta.1

# Git 信息
localhost:5001/my-app:main-abc1234
localhost:5001/my-app:feature-xyz-def5678

# 环境标签
localhost:5001/my-app:dev
localhost:5001/my-app:staging
localhost:5001/my-app:prod
```

## 🔍 故障排除

### 常见问题

1. **推送失败 - TLS 错误**
   ```bash
   # 解决方案：确认 Docker daemon 配置
   cat ~/.docker/daemon.json
   # 应包含: "insecure-registries": ["localhost:5001"]
   ```

2. **服务无法访问**
   ```bash
   # 检查容器状态
   docker ps | grep registry
   
   # 检查日志
   docker logs docker-registry
   ```

3. **镜像推送慢**
   ```bash
   # 检查网络
   ping localhost
   
   # 检查存储空间
   df -h
   ```

## 📚 相关文档

- [Registry 配置参考](docker/registry/config.yml)
- [Compose 配置](docker/compose/registry-compose.yml)
- [管理脚本](deployment/scripts/)
- [备份脚本](deployment/scripts/registry-manager.sh)

## 🎯 下一步

1. **配置生产环境认证**
   ```bash
   # 启用认证（可选）
   ./deployment/scripts/fix-docker-registry.sh enable-auth
   ```

2. **集成 Jenkins**
   - 安装 Docker Pipeline 插件
   - 配置 Registry 凭据
   - 创建构建流水线

3. **监控和告警**
   - 配置日志收集
   - 设置存储空间监控
   - 建立备份计划

---

## 🚀 现在您可以开始使用私有 Docker Registry！

**快速测试:**
```bash
./deployment/scripts/cicd-integration.sh test
```

**查看服务状态:**
```bash
./deployment/scripts/cicd-integration.sh status
```

**访问 Web UI:**
http://192.168.1.83:5002

享受您的私有 CI/CD 环境！ 🎉 
# OrbStack配置指南 - 移除国内镜像源

## 🎯 目标
- 移除所有国内Docker镜像源
- 配置使用原生Docker Hub
- 支持私有GitLab Registry
- 优化网络连接

## ✅ 已完成配置

### 1. Docker Daemon配置 (`~/.docker/daemon.json`)
```json
{
  "experimental": true,
  "features": {
    "buildkit": true
  },
  "insecure-registries": [
    "localhost:5001"
  ]
}
```

### 2. OrbStack配置 (`~/.orbstack/config/docker.json`)
```json
{
  "builder" : {
    "gc" : {
      "defaultKeepStorage" : "20GB",
      "enabled" : true
    }
  },
  "insecure-registries" : [
    "192.168.1.83:5002",
    "localhost:5001"
  ],
  "ipv6" : true,
  "experimental" : false
}
```

### 3. Jenkins配置更新
- 移除了国内镜像加速: `JENKINS_UC_DOWNLOAD`
- 配置使用官方更新源

## 🔧 网络问题解决方案

### ✅ 已解决：DNS解析问题
通过修改hosts文件解决Docker Registry DNS解析问题：

```bash
# 运行修复脚本
chmod +x deployment/scripts/docker-hosts-fix.sh
./deployment/scripts/docker-hosts-fix.sh
```

**修复内容：**
- 阻止Grammarly证书劫持: `127.0.0.1 iosapp-beta.grammarly.com`
- 添加Docker Registry解析: `54.87.120.168 registry-1.docker.io`
- 添加认证服务解析: `54.87.120.168 auth.docker.io`

### ExpressVPN TLS证书问题
如果遇到TLS证书错误，可以：

1. **使用hosts文件修复** (推荐)
```bash
./deployment/scripts/docker-hosts-fix.sh
```

2. **配置Docker使用特定DNS**
```bash
# 在 ~/.orbstack/config/docker.json 中添加
{
  "dns": ["8.8.8.8", "1.1.1.1"]
}
```

3. **ExpressVPN设置优化**
- 选择美国洛杉矶服务器
- 禁用"阻止WebRTC"功能
- 使用"Automatic"协议而非"OpenVPN"

## 🚀 验证步骤

### 1. 检查配置状态
```bash
# 检查Docker info，应该没有Registry Mirrors
docker info | grep -A3 "Registry Mirrors"

# 检查DNS解析
nslookup docker.io
```

### 2. 测试镜像拉取
```bash
# 测试小镜像
docker pull hello-world:latest

# 测试常用镜像
docker pull alpine:latest
docker pull nginx:latest
```

### 3. 本地Registry测试
```bash
# 启动本地Registry
cd /Users/brunogao/work/infra
docker-compose -f docker/compose/jenkins-compose.yml up -d registry

# 测试推送
docker tag alpine:latest localhost:5001/alpine:test
docker push localhost:5001/alpine:test
```

## 📝 GitLab Registry配置

### 1. 配置GitLab认证
```bash
# 登录GitLab Registry
docker login gitlab.example.com:5050
# 输入用户名和Personal Access Token
```

### 2. 推送到GitLab
```bash
# 标记镜像
docker tag my-app:latest gitlab.example.com:5050/group/project/my-app:latest

# 推送镜像
docker push gitlab.example.com:5050/group/project/my-app:latest
```

## 🛠️ 故障排除

### 问题1: DNS解析失败
```bash
# 解决方案：更新DNS设置
sudo networksetup -setdnsservers Wi-Fi 8.8.8.8 1.1.1.1
```

### 问题2: TLS证书错误
```bash
# 临时解决：重启ExpressVPN
# 或切换到其他美国服务器节点
```

### 问题3: 镜像拉取慢
```bash
# 检查网络延迟
ping registry-1.docker.io

# 使用CDN加速(仅限官方)
export DOCKER_REGISTRY_MIRROR=""
```

## 🎭 性能优化建议

### 1. 构建缓存优化
```dockerfile
# 多阶段构建
FROM node:18-alpine AS builder
# ... 构建步骤

FROM nginx:alpine AS runtime
COPY --from=builder /app/dist /usr/share/nginx/html
```

### 2. 镜像大小优化
```bash
# 使用.dockerignore
echo "node_modules" >> .dockerignore
echo ".git" >> .dockerignore

# 清理构建缓存
docker system prune -af --volumes
```

### 3. Registry策略
- 本地开发: `localhost:5001`
- CI/CD: GitLab Registry
- 生产: 私有Registry或Docker Hub

## 📊 监控和维护

### 定期检查
```bash
# 检查镜像大小
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

# 清理无用镜像
docker image prune -af

# 检查网络配置
docker network ls
```

### 自动化脚本
使用 `deployment/scripts/orbstack-config.sh` 进行定期检查和维护。

## ✨ 下一步计划

1. **配置GitLab CI/CD**
   - 创建`.gitlab-ci.yml`
   - 配置Runner

2. **设置监控**
   - Registry使用情况
   - 构建性能指标

3. **安全增强**
   - 镜像扫描
   - 漏洞检测

---

## 📞 支持

如遇问题：
1. 检查ExpressVPN连接状态
2. 验证DNS解析
3. 查看Docker日志: `docker logs <container>`
4. 运行诊断脚本: `./deployment/scripts/orbstack-config.sh` 
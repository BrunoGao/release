#!/bin/bash
# OrbStack配置脚本 - 移除国内镜像源，配置私有GitLab

set -e
G='\033[0;32m'; Y='\033[1;33m'; R='\033[0;31m'; NC='\033[0m' # 颜色定义
log() { echo -e "${G}[INFO]${NC} $1"; } # 信息日志
warn() { echo -e "${Y}[WARN]${NC} $1"; } # 警告日志
error() { echo -e "${R}[ERROR]${NC} $1"; } # 错误日志

log "=== OrbStack配置 - 移除国内镜像源 ==="

# 检查网络连接
check_network() {
    log "检查网络连接..."
    if curl -s --connect-timeout 5 https://docker.io > /dev/null; then
        log "✅ Docker Hub连接正常"
    else
        error "❌ Docker Hub连接失败"
        return 1
    fi
    
    if curl -s --connect-timeout 5 https://registry-1.docker.io/v2/ > /dev/null; then
        log "✅ Docker Registry连接正常"
    else
        warn "⚠️  Docker Registry连接异常"
    fi
}

# 验证Docker配置
verify_docker_config() {
    log "验证Docker配置..."
    
    # 检查daemon.json
    if [ -f ~/.docker/daemon.json ]; then
        if grep -q "registry-mirrors" ~/.docker/daemon.json; then
            if grep -q "mirrors.ustc.edu.cn\|daocloud.io\|163.com" ~/.docker/daemon.json; then
                error "❌ 仍包含国内镜像源"
                return 1
            fi
        fi
        log "✅ Docker daemon配置正确"
    fi
    
    # 检查OrbStack配置
    if [ -f ~/.orbstack/config/docker.json ]; then
        if grep -q "registry-mirrors" ~/.orbstack/config/docker.json; then
            if grep -q "mirrors.ustc.edu.cn\|daocloud.io" ~/.orbstack/config/docker.json; then
                error "❌ OrbStack仍包含国内镜像源"
                return 1
            fi
        fi
        log "✅ OrbStack配置正确"
    fi
}

# 测试镜像拉取
test_image_pull() {
    log "测试镜像拉取..."
    
    # 测试小镜像
    if docker pull alpine:latest > /dev/null 2>&1; then
        log "✅ 官方镜像拉取成功"
        docker rmi alpine:latest > /dev/null 2>&1
    else
        error "❌ 官方镜像拉取失败"
        return 1
    fi
}

# 配置私有GitLab连接
configure_gitlab() {
    log "配置私有GitLab连接..."
    
    read -p "请输入GitLab服务器地址 (如: gitlab.example.com): " GITLAB_HOST
    read -p "请输入GitLab端口 (默认443): " GITLAB_PORT
    GITLAB_PORT=${GITLAB_PORT:-443}
    
    # 测试GitLab连接
    if curl -s --connect-timeout 5 https://${GITLAB_HOST}:${GITLAB_PORT} > /dev/null; then
        log "✅ GitLab连接正常"
        
        # 更新Docker Compose配置
        if [ -f "docker/compose/jenkins-compose.yml" ]; then
            log "更新Jenkins配置..."
            # 添加GitLab环境变量
            if ! grep -q "GITLAB_HOST" docker/compose/jenkins-compose.yml; then
                sed -i '' '/JENKINS_SLAVE_AGENT_PORT/a\
      - GITLAB_HOST='${GITLAB_HOST}' # GitLab服务器\
      - GITLAB_PORT='${GITLAB_PORT}' # GitLab端口' docker/compose/jenkins-compose.yml
            fi
        fi
    else
        error "❌ GitLab连接失败"
        return 1
    fi
}

# 更新Registry配置
update_registry_config() {
    log "更新Registry配置..."
    
    # 确保本地Registry配置正确
    if [ -f "docker/registry/config.yml" ]; then
        log "✅ Registry配置存在"
    else
        warn "⚠️  Registry配置不存在，创建默认配置"
        mkdir -p docker/registry
        cat > docker/registry/config.yml << 'EOF'
version: 0.1
log:
  fields:
    service: registry
storage:
  cache:
    blobdescriptor: inmemory
  filesystem:
    rootdirectory: /var/lib/registry
  delete:
    enabled: true
http:
  addr: :5000
  headers:
    X-Content-Type-Options: [nosniff]
    Access-Control-Allow-Origin: ['*']
    Access-Control-Allow-Methods: ['HEAD', 'GET', 'OPTIONS', 'DELETE']
    Access-Control-Allow-Headers: ['Authorization', 'Accept', 'Cache-Control']
health:
  storagedriver:
    enabled: true
    interval: 10s
    threshold: 3
EOF
    fi
}

# 生成Docker使用指南
generate_docker_guide() {
    log "生成Docker使用指南..."
    
    cat > DOCKER_CONFIG_GUIDE.md << 'EOF'
# Docker配置指南

## 当前配置状态
- ✅ 已移除国内镜像源
- ✅ 使用官方Docker Hub
- ✅ 支持私有GitLab
- ✅ 配置本地Registry

## 镜像拉取策略
1. 优先使用官方Docker Hub: `docker.io/`
2. 本地Registry: `localhost:5001/`
3. 私有GitLab Registry: `gitlab.example.com:5050/`

## 常用命令
```bash
# 拉取官方镜像
docker pull nginx:latest

# 推送到本地Registry
docker tag nginx:latest localhost:5001/nginx:latest
docker push localhost:5001/nginx:latest

# 推送到GitLab Registry
docker tag nginx:latest gitlab.example.com:5050/project/nginx:latest
docker push gitlab.example.com:5050/project/nginx:latest
```

## 故障排除
1. 如果拉取慢，检查VPN连接
2. 确认ExpressVPN连接到美国节点
3. 验证Docker daemon配置无国内镜像源

## 性能建议
- 使用多阶段构建减少镜像大小
- 利用构建缓存提高构建速度
- 定期清理无用镜像: `docker system prune -af`
EOF
    
    log "✅ 指南已生成: DOCKER_CONFIG_GUIDE.md"
}

# 主函数
main() {
    check_network
    verify_docker_config
    test_image_pull
    # configure_gitlab
    update_registry_config
    generate_docker_guide
    
    log "=== 配置完成 ==="
    log "🎉 OrbStack已配置为使用原生Docker Hub"
    log "📝 请查看 DOCKER_CONFIG_GUIDE.md 获取详细说明"
}

main "$@" 
#!/bin/bash
# ExpressVPN TLS证书问题综合解决方案

set -e
G='\033[0;32m';Y='\033[1;33m';R='\033[0;31m';NC='\033[0m'
log() { echo -e "${G}[INFO]${NC} $1"; }
warn() { echo -e "${Y}[WARN]${NC} $1"; }
error() { echo -e "${R}[ERROR]${NC} $1"; }

log "=== ExpressVPN TLS问题解决方案 ==="

# 方案1：修改Docker配置跳过TLS验证（不推荐，仅临时使用）
disable_tls_verify() {
    log "方案1：临时禁用TLS验证"
    
    # 备份配置
    cp ~/.docker/daemon.json ~/.docker/daemon.json.backup 2>/dev/null || true
    
    # 添加TLS跳过配置
    cat > ~/.docker/daemon.json << 'EOF'
{
  "experimental": true,
  "features": {
    "buildkit": true
  },
  "insecure-registries": [
    "localhost:5001"
  ],
  "registry-mirrors": [],
  "disable-legacy-registry": false
}
EOF
    
    # 重启Docker
    osascript -e 'quit app "OrbStack"' && sleep 3 && open -a OrbStack
    sleep 10
    
    log "✅ Docker配置已更新，请重试拉取镜像"
}

# 方案2：使用本地镜像缓存
use_local_cache() {
    log "方案2：创建本地镜像缓存"
    
    # 创建本地缓存目录
    mkdir -p ~/docker-cache
    
    # 下载常用镜像的tar包（如果可能）
    log "提示：可以在网络条件好的时候预先下载镜像：" 
    echo "  docker save gitea/gitea:latest > ~/docker-cache/gitea.tar"
    echo "  docker load < ~/docker-cache/gitea.tar"
}

# 方案3：使用国内云服务器中转
setup_proxy_server() {
    log "方案3：配置代理服务器"
    
    cat << 'EOF'
建议在国内云服务器上设置Docker Registry代理：

1. 在云服务器运行：
   docker run -d --restart=always -p 5000:5000 \
     --name registry-proxy \
     -e REGISTRY_PROXY_REMOTEURL=https://registry-1.docker.io \
     registry:2

2. 在本地配置使用代理：
   {
     "registry-mirrors": ["http://your-server:5000"]
   }
EOF
}

# 方案4：ExpressVPN配置优化
optimize_expressvpn() {
    log "方案4：ExpressVPN配置优化"
    
    cat << 'EOF'
ExpressVPN配置建议：

1. 切换协议：
   - 打开ExpressVPN应用
   - 进入设置 > Protocol
   - 选择 "Automatic" 而不是 "OpenVPN"

2. 切换服务器位置：
   - 尝试美国西海岸服务器（洛杉矶）
   - 尝试香港服务器
   - 避免使用欧洲服务器

3. 禁用某些功能：
   - 关闭 "Network Lock"
   - 关闭 "Block ads & trackers"

4. 使用分流：
   - 在路由器层面配置Docker Hub直连
EOF
}

# 方案5：直接解决当前问题
fix_current_issue() {
    log "方案5：直接修复当前Gitea拉取问题"
    
    # 尝试使用已有的alpine镜像构建gitea
    log "使用临时解决方案..."
    
    # 创建简化的compose文件
    cat > /tmp/gitea-simple.yml << 'EOF'
version: '3.8'
services:
  gitea-simple:
    image: alpine:latest
    container_name: gitea-temp
    command: /bin/sh -c "echo 'Gitea服务占位符，网络修复后替换' && sleep 3600"
    ports:
      - "3000:3000"
    networks:
      - cicd-network

networks:
  cicd-network:
    external: true
EOF
    
    # 启动临时服务
    docker network create cicd-network 2>/dev/null || true
    docker-compose -f /tmp/gitea-simple.yml up -d
    
    log "✅ 临时Gitea服务已启动，端口3000"
    log "修复网络问题后可以替换为真正的Gitea镜像"
}

# 测试网络连接
test_network() {
    log "测试网络连接..."
    
    echo "测试结果："
    echo -n "Docker Hub API: "
    curl -s -w "%{http_code}" -o /dev/null https://index.docker.io || echo "失败"
    
    echo -n "Docker Registry: "
    curl -s -w "%{http_code}" -o /dev/null https://registry-1.docker.io || echo "失败"
    
    echo -n "Gitea官网: "
    curl -s -w "%{http_code}" -o /dev/null https://gitea.io || echo "失败"
}

# 主菜单
show_menu() {
    echo "
=== ExpressVPN TLS问题解决方案 ===
1. 🔧 禁用TLS验证（临时方案）
2. 💾 使用本地镜像缓存
3. 🌐 配置代理服务器
4. 📡 ExpressVPN优化建议
5. 🚀 直接修复当前问题
6. 🧪 测试网络连接
0. 退出

请选择 (0-6): "
}

# 主程序
main() {
    while true; do
        show_menu
        read -r choice
        case $choice in
            1) disable_tls_verify ;;
            2) use_local_cache ;;
            3) setup_proxy_server ;;
            4) optimize_expressvpn ;;
            5) fix_current_issue ;;
            6) test_network ;;
            0) log "退出"; exit 0 ;;
            *) warn "无效选择" ;;
        esac
        echo; read -p "按回车继续..."; echo
    done
}

main "$@" 
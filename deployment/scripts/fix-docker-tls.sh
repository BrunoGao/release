#!/bin/bash
# 修复Docker TLS证书问题

log() { echo -e "\033[0;32m[INFO]\033[0m $1"; }
warn() { echo -e "\033[1;33m[WARN]\033[0m $1"; }

log "=== Docker TLS证书问题修复 ==="

# 方案1：更新DNS设置
fix_dns() {
    log "修复DNS设置..."
    cat >> ~/.docker/daemon.json.tmp << 'EOF'
{
  "experimental": true,
  "features": {
    "buildkit": true
  },
  "insecure-registries": [
    "localhost:5001"
  ],
  "dns": ["8.8.8.8", "1.1.1.1", "208.67.222.222"]
}
EOF
    mv ~/.docker/daemon.json.tmp ~/.docker/daemon.json
    log "✅ DNS设置已更新"
}

# 方案2：临时绕过证书验证
bypass_tls() {
    warn "临时绕过TLS验证 (仅用于测试)"
    export DOCKER_CLIENT_TIMEOUT=120
    export COMPOSE_HTTP_TIMEOUT=120
    
    # 创建临时配置
    mkdir -p ~/.docker/certs.d/registry-1.docker.io
    echo '{"insecure-registry": true}' > ~/.docker/certs.d/registry-1.docker.io/config.json
}

# 方案3：ExpressVPN设置提示
vpn_settings() {
    log "ExpressVPN优化建议："
    echo "1. 打开ExpressVPN应用"
    echo "2. 点击设置(⚙️)"
    echo "3. 进入'高级设置'"
    echo "4. 禁用'阻止WebRTC'"
    echo "5. 禁用'威胁管理器'"
    echo "6. 选择'自动'协议"
    echo "7. 重新连接到美国洛杉矶服务器"
    echo ""
    echo "或者临时断开VPN测试Docker："
    echo "expressvpn disconnect"
}

# 方案4：使用HTTP代理
setup_proxy() {
    log "配置HTTP代理..."
    
    # 检查是否有其他代理
    if [ -n "$HTTP_PROXY" ] || [ -n "$HTTPS_PROXY" ]; then
        log "检测到现有代理设置"
        env | grep -i proxy
    fi
    
    # 创建代理配置
    cat >> ~/.docker/config.json.tmp << 'EOF'
{
  "proxies": {
    "default": {
      "httpProxy": "",
      "httpsProxy": "",
      "noProxy": "localhost,127.0.0.1,::1"
    }
  }
}
EOF
    mv ~/.docker/config.json.tmp ~/.docker/config.json
}

# 测试连接
test_connection() {
    log "测试Docker Hub连接..."
    
    # 测试1：基本连接
    if curl -m 10 -s https://index.docker.io/v1/ > /dev/null; then
        log "✅ Docker Index连接正常"
    else
        warn "❌ Docker Index连接失败"
    fi
    
    # 测试2：Registry连接
    if timeout 10 docker info | grep -q "Registry"; then
        log "✅ Docker daemon正常"
    else
        warn "❌ Docker daemon异常"
    fi
}

# 主函数
main() {
    echo "选择修复方案："
    echo "1) 更新DNS设置"
    echo "2) 临时绕过TLS验证"
    echo "3) 显示ExpressVPN设置建议"
    echo "4) 配置代理设置"
    echo "5) 测试连接"
    echo "6) 全部执行"
    
    read -p "请选择 (1-6): " choice
    
    case $choice in
        1) fix_dns ;;
        2) bypass_tls ;;
        3) vpn_settings ;;
        4) setup_proxy ;;
        5) test_connection ;;
        6) fix_dns; bypass_tls; setup_proxy; test_connection ;;
        *) echo "无效选择" ;;
    esac
    
    log "修复完成！请重启Docker: orbctl restart -a"
}

main "$@" 
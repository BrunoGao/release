#!/bin/bash

# 修复Docker Registry配置脚本

set -e

G='\033[0;32m'; Y='\033[1;33m'; R='\033[0;31m'; NC='\033[0m'
log() { echo -e "${G}[INFO]${NC} $1"; }
warn() { echo -e "${Y}[WARN]${NC} $1"; }
error() { echo -e "${R}[ERROR]${NC} $1"; }

log "=== Docker Registry 配置修复 ==="

# 方案1: 更新Docker Desktop配置
update_docker_desktop() {
    log "方案1: 更新Docker Desktop配置"
    
    # 检查当前配置
    log "当前Docker配置:"
    docker info | grep -A10 "Insecure Registries" || true
    
    echo ""
    warn "请手动配置Docker Desktop:"
    echo "1. 打开Docker Desktop"
    echo "2. 点击设置图标 (齿轮)"
    echo "3. 选择 'Docker Engine'"
    echo "4. 在JSON配置中添加或修改:"
    cat << 'EOF'
{
  "builder": {
    "gc": {
      "defaultKeepStorage": "20GB",
      "enabled": true
    }
  },
  "experimental": false,
  "features": {
    "buildkit": true
  },
  "insecure-registries": [
    "192.168.1.83:5001",
    "localhost:5001"
  ]
}
EOF
    echo "5. 点击 'Apply & Restart'"
    echo ""
}

# 方案2: 使用localhost
use_localhost() {
    log "方案2: 使用localhost地址测试"
    
    # 测试localhost连接
    if curl -s "http://localhost:5001/v2/_catalog" >/dev/null; then
        log "✅ localhost:5001 可以访问"
        
        # 尝试登录
        echo "registry123" | docker login localhost:5001 -u admin --password-stdin
        
        if [ $? -eq 0 ]; then
            log "✅ 登录成功！使用 localhost:5001"
            return 0
        fi
    else
        error "❌ localhost:5001 无法访问"
    fi
    
    return 1
}

# 方案3: 禁用Registry认证（仅测试）
disable_auth() {
    log "方案3: 临时禁用Registry认证"
    
    warn "⚠️  这将临时禁用Registry认证，仅用于测试"
    read -p "是否继续？(y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # 修改Registry配置
        local config_file="docker/registry/config.yml"
        cp "$config_file" "$config_file.backup"
        
        # 创建无认证版本
        cat > "$config_file" << 'EOF'
version: 0.1
log:
  level: info
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
    X-Content-Type-Options: 
      - nosniff
    Access-Control-Allow-Origin: 
      - '*'
    Access-Control-Allow-Methods: 
      - 'HEAD'
      - 'GET'
      - 'OPTIONS'
      - 'DELETE'
      - 'POST'
      - 'PUT'
    Access-Control-Allow-Headers: 
      - 'Authorization'
      - 'Accept'
      - 'Cache-Control'
      - 'Content-Type'
health:
  storagedriver:
    enabled: true
    interval: 10s
    threshold: 3
EOF
        
        # 重启Registry
        cd "/Users/brunogao/work/infra/docker/compose"
        docker-compose -f registry-compose.yml restart docker-registry
        
        log "✅ Registry认证已禁用，重启完成"
        log "恢复认证: mv $config_file.backup $config_file && docker-compose restart"
    fi
}

# 方案4: 测试连接
test_connection() {
    log "方案4: 测试Registry连接"
    
    echo ""
    log "测试API访问:"
    curl -v "http://192.168.1.83:5001/v2/_catalog" 2>&1 | head -10
    
    echo ""
    log "测试localhost访问:"
    curl -v "http://localhost:5001/v2/_catalog" 2>&1 | head -10
    
    echo ""
    log "测试端口连通性:"
    nc -zv 192.168.1.83 5001 2>&1 || echo "端口不通"
    nc -zv localhost 5001 2>&1 || echo "localhost端口不通"
}

# 显示解决方案
show_solutions() {
    log "可用解决方案:"
    echo "1. update-docker    - 更新Docker Desktop配置"
    echo "2. use-localhost    - 使用localhost地址"
    echo "3. disable-auth     - 临时禁用认证"
    echo "4. test-connection  - 测试连接"
    echo ""
    echo "使用方法: $0 [solution]"
}

# 主函数
main() {
    case "${1:-help}" in
        update-docker)
            update_docker_desktop
            ;;
        use-localhost)
            use_localhost
            ;;
        disable-auth)
            disable_auth
            ;;
        test-connection)
            test_connection
            ;;
        help|--help|-h)
            show_solutions
            ;;
        *)
            show_solutions
            ;;
    esac
}

main "$@" 
#!/bin/bash

# Docker Registry 管理脚本
# 使用方法: ./registry-manager.sh [start|stop|restart|status|backup|restore|login|push-test]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
REGISTRY_URL="192.168.1.83:5001"
REGISTRY_UI_URL="http://192.168.1.83:5002"
REGISTRY_USER="admin"
REGISTRY_PASS="registry123"
COMPOSE_FILE="${PROJECT_ROOT}/docker/compose/registry-compose.yml"

# 颜色输出
G='\033[0;32m'; Y='\033[1;33m'; R='\033[0;31m'; B='\033[0;34m'; NC='\033[0m'
log() { echo -e "${G}[INFO]${NC} $1"; }
warn() { echo -e "${Y}[WARN]${NC} $1"; }
error() { echo -e "${R}[ERROR]${NC} $1"; }
info() { echo -e "${B}[INFO]${NC} $1"; }

# 检查Docker是否运行
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        error "Docker 未运行，请先启动 Docker"
        exit 1
    fi
}

# 启动Registry服务
start_registry() {
    log "启动 Docker Registry 服务..."
    
    # 确保网络存在
    docker network create cicd-network 2>/dev/null || true
    
    # 启动服务
    cd "${PROJECT_ROOT}/docker/compose"
    docker-compose -f registry-compose.yml up -d
    
    # 等待服务启动
    log "等待服务启动..."
    sleep 10
    
    # 检查服务状态
    if curl -s "http://${REGISTRY_URL}/v2/_catalog" >/dev/null; then
        log "✅ Registry 服务启动成功"
        info "🌐 Registry API: http://${REGISTRY_URL}/v2/_catalog"
        info "🎨 Registry UI: ${REGISTRY_UI_URL}"
        info "👤 用户名: ${REGISTRY_USER}"
        info "🔑 密码: ${REGISTRY_PASS}"
    else
        error "❌ Registry 服务启动失败"
        return 1
    fi
}

# 停止Registry服务
stop_registry() {
    log "停止 Docker Registry 服务..."
    cd "${PROJECT_ROOT}/docker/compose"
    docker-compose -f registry-compose.yml down
    log "✅ Registry 服务已停止"
}

# 重启Registry服务
restart_registry() {
    log "重启 Docker Registry 服务..."
    stop_registry
    sleep 3
    start_registry
}

# 查看服务状态
show_status() {
    log "Docker Registry 服务状态:"
    echo ""
    
    # 检查容器状态
    if docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(docker-registry|registry-ui)"; then
        echo ""
        
        # 检查API访问
        if curl -s "http://${REGISTRY_URL}/v2/_catalog" >/dev/null; then
            log "✅ Registry API 正常"
        else
            error "❌ Registry API 无法访问"
        fi
        
        # 显示镜像列表
        echo ""
        log "📦 Registry 中的镜像:"
        curl -s "http://${REGISTRY_URL}/v2/_catalog" | jq '.repositories[]' 2>/dev/null || echo "  (暂无镜像)"
        
    else
        warn "⚠️  Registry 服务未运行"
    fi
}

# 备份Registry数据
backup_registry() {
    local backup_name="${1:-registry-$(date +%Y%m%d-%H%M%S)}"
    local backup_dir="${PROJECT_ROOT}/backup/registry"
    local volume_name="compose_registry-data"
    
    log "开始备份 Registry 数据..."
    mkdir -p "${backup_dir}"
    
    # 使用临时容器备份卷数据
    docker run --rm \
        -v "${volume_name}:/source:ro" \
        -v "${backup_dir}:/backup" \
        busybox \
        tar -czf "/backup/${backup_name}.tar.gz" -C /source .
    
    log "✅ 备份完成: ${backup_dir}/${backup_name}.tar.gz"
    echo "📊 备份大小: $(du -h "${backup_dir}/${backup_name}.tar.gz" | cut -f1)"
    
    # 清理旧备份（保留最近5个）
    cd "${backup_dir}"
    ls -t registry-*.tar.gz 2>/dev/null | tail -n +6 | xargs rm -f 2>/dev/null || true
}

# 恢复Registry数据
restore_registry() {
    local backup_file="$1"
    local volume_name="compose_registry-data"
    
    if [ -z "$backup_file" ]; then
        error "请指定备份文件路径"
        echo "使用方法: $0 restore <backup_file.tar.gz>"
        exit 1
    fi
    
    if [ ! -f "$backup_file" ]; then
        error "备份文件不存在: $backup_file"
        exit 1
    fi
    
    log "开始恢复 Registry 数据..."
    
    # 停止服务
    stop_registry
    
    # 删除现有卷
    docker volume rm "$volume_name" 2>/dev/null || true
    
    # 创建新卷
    docker volume create "$volume_name"
    
    # 恢复数据
    docker run --rm \
        -v "${volume_name}:/target" \
        -v "$(dirname "$backup_file"):/backup:ro" \
        busybox \
        tar -xzf "/backup/$(basename "$backup_file")" -C /target
    
    log "✅ 恢复完成，重启服务..."
    start_registry
}

# 登录Registry
login_registry() {
    log "登录到 Docker Registry..."
    echo "$REGISTRY_PASS" | docker login "$REGISTRY_URL" -u "$REGISTRY_USER" --password-stdin
    log "✅ 登录成功"
}

# 测试推送镜像
test_push() {
    log "测试推送镜像到 Registry..."
    
    # 确保已登录
    login_registry
    
    # 拉取测试镜像
    docker pull alpine:latest
    
    # 标记镜像
    local test_image="${REGISTRY_URL}/alpine:test-$(date +%s)"
    docker tag alpine:latest "$test_image"
    
    # 推送镜像
    docker push "$test_image"
    
    # 验证推送
    if curl -s "http://${REGISTRY_URL}/v2/alpine/tags/list" | grep -q "test-"; then
        log "✅ 镜像推送测试成功"
        log "🔍 查看镜像: curl http://${REGISTRY_URL}/v2/alpine/tags/list"
    else
        error "❌ 镜像推送测试失败"
    fi
    
    # 清理本地镜像
    docker rmi "$test_image" alpine:latest || true
}

# 显示使用帮助
show_help() {
    echo "Docker Registry 管理脚本"
    echo ""
    echo "使用方法:"
    echo "  $0 start          # 启动 Registry 服务"
    echo "  $0 stop           # 停止 Registry 服务"
    echo "  $0 restart        # 重启 Registry 服务"
    echo "  $0 status         # 查看服务状态"
    echo "  $0 backup [name]  # 备份 Registry 数据"
    echo "  $0 restore <file> # 恢复 Registry 数据"
    echo "  $0 login          # 登录到 Registry"
    echo "  $0 push-test      # 测试推送镜像"
    echo ""
    echo "Registry 信息:"
    echo "  URL: http://${REGISTRY_URL}"
    echo "  UI:  ${REGISTRY_UI_URL}"
    echo "  用户: ${REGISTRY_USER}"
    echo "  密码: ${REGISTRY_PASS}"
}

# 主函数
main() {
    check_docker
    
    case "${1:-help}" in
        start)
            start_registry
            ;;
        stop)
            stop_registry
            ;;
        restart)
            restart_registry
            ;;
        status)
            show_status
            ;;
        backup)
            backup_registry "$2"
            ;;
        restore)
            restore_registry "$2"
            ;;
        login)
            login_registry
            ;;
        push-test)
            test_push
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@" 
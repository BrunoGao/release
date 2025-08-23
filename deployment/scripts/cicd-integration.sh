#!/bin/bash

# CI/CD 集成管理脚本
# 管理 Gitea、Jenkins 和 Docker Registry 的集成

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# 服务配置
GITEA_URL="http://192.168.1.83:3000"
REGISTRY_URL="localhost:5001"
REGISTRY_UI_URL="http://192.168.1.83:5002"
JENKINS_URL="http://localhost:8081/jenkins"

# 颜色输出
G='\033[0;32m'; Y='\033[1;33m'; R='\033[0;31m'; B='\033[0;34m'; NC='\033[0m'
log() { echo -e "${G}[INFO]${NC} $1"; }
warn() { echo -e "${Y}[WARN]${NC} $1"; }
error() { echo -e "${R}[ERROR]${NC} $1"; }
info() { echo -e "${B}[INFO]${NC} $1"; }

# 检查依赖
check_dependencies() {
    log "检查系统依赖..."
    
    if ! command -v docker >/dev/null; then
        error "❌ Docker 未安装"
        exit 1
    fi
    
    if ! command -v docker-compose >/dev/null; then
        error "❌ Docker Compose 未安装"
        exit 1
    fi
    
    if ! command -v curl >/dev/null; then
        error "❌ curl 未安装"
        exit 1
    fi
    
    if ! command -v jq >/dev/null; then
        warn "⚠️  jq 未安装，某些功能可能受限"
    fi
    
    log "✅ 依赖检查完成"
}

# 启动所有服务
start_all_services() {
    log "启动所有 CI/CD 服务..."
    
    # 创建网络
    docker network create cicd-network 2>/dev/null || true
    
    # 启动 Gitea
    log "启动 Gitea..."
    cd "${PROJECT_ROOT}/docker/compose"
    docker-compose -f gitea-compose.yml up -d
    
    # 启动 Registry
    log "启动 Docker Registry..."
    docker-compose -f registry-compose.yml up -d
    
    # 等待服务启动
    log "等待服务启动..."
    sleep 15
    
    # 检查服务状态
    check_services
}

# 停止所有服务
stop_all_services() {
    log "停止所有 CI/CD 服务..."
    
    cd "${PROJECT_ROOT}/docker/compose"
    docker-compose -f gitea-compose.yml down || true
    docker-compose -f registry-compose.yml down || true
    
    log "✅ 所有服务已停止"
}

# 检查服务状态
check_services() {
    log "检查服务状态..."
    echo ""
    
    # 检查 Gitea
    if curl -s "${GITEA_URL}/api/healthz" >/dev/null; then
        log "✅ Gitea 运行正常"
        info "🌐 Gitea: ${GITEA_URL}"
    else
        error "❌ Gitea 无法访问"
    fi
    
    # 检查 Registry
    if curl -s "http://${REGISTRY_URL}/v2/_catalog" >/dev/null; then
        log "✅ Registry 运行正常"
        info "🐳 Registry: http://${REGISTRY_URL}"
        info "🎨 Registry UI: ${REGISTRY_UI_URL}"
    else
        error "❌ Registry 无法访问"
    fi
    
    # 显示容器状态
    echo ""
    log "容器状态:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(gitea|registry)"
}

# 测试集成功能
test_integration() {
    log "测试 CI/CD 集成功能..."
    
    # 测试 Registry 推送
    log "测试 Registry 镜像推送..."
    
    # 创建测试镜像
    local test_image="${REGISTRY_URL}/test/integration:$(date +%s)"
    docker pull alpine:latest
    docker tag alpine:latest "$test_image"
    
    # 推送测试镜像
    if docker push "$test_image"; then
        log "✅ Registry 推送测试成功"
        
        # 验证镜像存在
        if curl -s "http://${REGISTRY_URL}/v2/_catalog" | grep -q "test/integration"; then
            log "✅ 镜像在 Registry 中验证成功"
        fi
    else
        error "❌ Registry 推送测试失败"
    fi
    
    # 清理测试镜像
    docker rmi "$test_image" alpine:latest || true
    
    echo ""
    log "集成测试完成"
}

# 显示 Webhook 配置指南
show_webhook_guide() {
    log "Gitea Webhook 配置指南:"
    echo ""
    echo "1. 登录 Gitea: ${GITEA_URL}"
    echo "2. 进入项目 -> 设置 -> Webhooks"
    echo "3. 添加 Webhook:"
    echo "   - 目标 URL: ${JENKINS_URL}/gitea-webhook/"
    echo "   - HTTP 方法: POST"
    echo "   - 内容类型: application/json"
    echo "   - 触发条件: Push events"
    echo ""
    echo "4. Jenkins Pipeline 示例:"
    cat << 'EOF'
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
    }
}
EOF
}

# 显示服务信息
show_service_info() {
    log "CI/CD 服务信息:"
    echo ""
    echo "🔧 Gitea (Git 仓库):"
    echo "   URL: ${GITEA_URL}"
    echo "   默认管理员: admin"
    echo ""
    echo "🐳 Docker Registry (镜像仓库):"
    echo "   URL: http://${REGISTRY_URL}"
    echo "   UI: ${REGISTRY_UI_URL}"
    echo "   认证: 已禁用 (开发环境)"
    echo ""
    echo "🔧 推送镜像示例:"
    echo "   docker tag my-app:latest ${REGISTRY_URL}/my-app:latest"
    echo "   docker push ${REGISTRY_URL}/my-app:latest"
    echo ""
    echo "🔍 查看镜像:"
    echo "   curl http://${REGISTRY_URL}/v2/_catalog"
    echo "   访问 ${REGISTRY_UI_URL}"
}

# 备份所有数据
backup_all() {
    local backup_name="${1:-cicd-backup-$(date +%Y%m%d-%H%M%S)}"
    local backup_dir="${PROJECT_ROOT}/backup/full"
    
    log "开始完整备份: $backup_name"
    mkdir -p "$backup_dir"
    
    # 备份 Gitea
    log "备份 Gitea 数据..."
    ./deployment/scripts/backup-gitea-volume.sh "gitea-$backup_name"
    
    # 备份 Registry
    log "备份 Registry 数据..."
    ./deployment/scripts/registry-manager.sh backup "registry-$backup_name"
    
    # 创建配置备份
    log "备份配置文件..."
    tar -czf "$backup_dir/configs-$backup_name.tar.gz" \
        docker/compose/ \
        docker/registry/ \
        deployment/scripts/
    
    log "✅ 完整备份完成"
    log "📁 备份位置: $backup_dir"
}

# 显示使用帮助
show_help() {
    echo "CI/CD 集成管理脚本"
    echo ""
    echo "使用方法:"
    echo "  $0 start           # 启动所有服务"
    echo "  $0 stop            # 停止所有服务"
    echo "  $0 restart         # 重启所有服务"
    echo "  $0 status          # 查看服务状态"
    echo "  $0 test            # 测试集成功能"
    echo "  $0 info            # 显示服务信息"
    echo "  $0 webhook-guide   # 显示 Webhook 配置指南"
    echo "  $0 backup [name]   # 备份所有数据"
    echo ""
    echo "服务地址:"
    echo "  Gitea:      ${GITEA_URL}"
    echo "  Registry:   http://${REGISTRY_URL}"
    echo "  Registry UI: ${REGISTRY_UI_URL}"
}

# 主函数
main() {
    check_dependencies
    
    case "${1:-help}" in
        start)
            start_all_services
            ;;
        stop)
            stop_all_services
            ;;
        restart)
            stop_all_services
            sleep 3
            start_all_services
            ;;
        status)
            check_services
            ;;
        test)
            test_integration
            ;;
        info)
            show_service_info
            ;;
        webhook-guide)
            show_webhook_guide
            ;;
        backup)
            backup_all "$2"
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
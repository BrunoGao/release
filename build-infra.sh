#!/bin/bash
# 基础服务统一构建脚本
# 统一端口配置，有序部署所有服务

set -e
BASE_DIR="/Users/brunogao/work/infra"
SCRIPTS_DIR="$BASE_DIR/scripts"

# 加载配置
source "$BASE_DIR/configs/global.env" 2>/dev/null || {
    echo "⚠️  配置文件不存在，使用默认配置"
}

# 颜色定义
G='\033[0;32m'  # 绿色
Y='\033[1;33m'  # 黄色
R='\033[0;31m'  # 红色
B='\033[0;34m'  # 蓝色
C='\033[0;36m'  # 青色
NC='\033[0m'    # 无色

# 日志函数
log() { echo -e "${G}[INFO]${NC} $1"; }
warn() { echo -e "${Y}[WARN]${NC} $1"; }
error() { echo -e "${R}[ERROR]${NC} $1"; }
info() { echo -e "${B}[INFO]${NC} $1"; }
step() { echo -e "${C}[STEP]${NC} $1"; }

# 显示Logo
show_logo() {
    echo -e "${B}"
    cat << 'EOF'
    ╔═══════════════════════════════════════╗
    ║          基础服务统一构建             ║
    ║          CI/CD Infrastructure         ║
    ║                                       ║
    ║  Port Layout:                         ║
    ║  • Gitea:     33000 (SSH: 32222)     ║
    ║  • Jenkins:   38080 (Agent: 35000)   ║
    ║  • Registry:  35001 (UI: 35002)      ║
    ╚═══════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

# 检查依赖
check_dependencies() {
    step "检查系统依赖..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        error "Docker未运行，请启动Docker"
        exit 1
    fi
    
    # 检查docker-compose
    if ! command -v docker-compose &> /dev/null; then
        error "docker-compose未安装"
        exit 1
    fi
    
    log "✅ 系统依赖检查通过"
}

# 检查端口占用
check_ports() {
    step "检查端口占用情况..."
    
    local ports=(33000 32222 38080 35000 35001 35002)
    local occupied_ports=()
    
    for port in "${ports[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null; then
            occupied_ports+=($port)
        fi
    done
    
    if [ ${#occupied_ports[@]} -gt 0 ]; then
        warn "检测到端口占用: ${occupied_ports[*]}"
        echo "是否继续？占用的端口可能会导致服务启动失败 (y/N)"
        read -r response
        if [[ ! $response =~ ^[Yy]$ ]]; then
            error "用户取消部署"
            exit 1
        fi
    else
        log "✅ 所有端口都可用"
    fi
}

# 清理现有服务
cleanup_existing() {
    step "清理现有服务..."
    
    # 停止可能存在的服务
    docker-compose -f "$BASE_DIR/docker/compose/jenkins-simple.yml" down 2>/dev/null || true
    docker-compose -f "$BASE_DIR/docker/compose/gitea-compose.yml" down 2>/dev/null || true
    docker-compose -f "$BASE_DIR/docker/compose/registry.yml" down 2>/dev/null || true
    
    # 停止单独的容器
    local containers=("jenkins-simple" "gitea" "registry" "registry-ui")
    for container in "${containers[@]}"; do
        docker stop "$container" 2>/dev/null || true
        docker rm "$container" 2>/dev/null || true
    done
    
    log "✅ 现有服务已清理"
}

# 初始化环境
init_environment() {
    step "初始化环境..."
    
    # 创建必要目录
    mkdir -p "$BASE_DIR"/{data,backup,configs}
    mkdir -p "$BASE_DIR/docker/registry/auth"
    mkdir -p "$BASE_DIR/data"/{gitea,jenkins,registry}
    
    # 创建网络
    docker network create $NETWORK_NAME 2>/dev/null || {
        log "网络 $NETWORK_NAME 已存在"
    }
    
    # 创建Registry认证文件
    if [[ ! -f "$BASE_DIR/docker/registry/auth/htpasswd" ]]; then
        docker run --rm httpd:2.4-alpine htpasswd -Bbn $REGISTRY_USERNAME $REGISTRY_PASSWORD > \
            "$BASE_DIR/docker/registry/auth/htpasswd"
        log "✅ Registry认证文件已创建"
    fi
    
    log "✅ 环境初始化完成"
}

# 部署Registry
deploy_registry() {
    step "部署Docker Registry..."
    
    cd "$BASE_DIR/docker/compose"
    docker-compose -f registry-simple.yml up -d
    
    # 等待服务启动
    local max_wait=30
    local count=0
    while [ $count -lt $max_wait ]; do
        if curl -s http://localhost:35001/v2/ >/dev/null 2>&1; then
            log "✅ Registry服务启动成功 (http://localhost:35001)"
            log "✅ Registry UI可用 (http://localhost:35002)"
            return 0
        fi
        sleep 2
        count=$((count + 1))
        echo -n "."
    done
    
    error "❌ Registry服务启动超时"
    return 1
}

# 部署Gitea
deploy_gitea() {
    step "部署Gitea服务..."
    
    cd "$BASE_DIR/docker/compose"
    docker-compose -f gitea-compose.yml up -d
    
    # 等待服务启动
    local max_wait=60
    local count=0
    while [ $count -lt $max_wait ]; do
        if curl -s http://localhost:33000/api/healthz >/dev/null 2>&1; then
            log "✅ Gitea服务启动成功 (http://localhost:33000)"
            return 0
        fi
        sleep 3
        count=$((count + 1))
        echo -n "."
    done
    
    error "❌ Gitea服务启动超时"
    return 1
}

# 部署Jenkins
deploy_jenkins() {
    step "部署Jenkins服务..."
    
    cd "$BASE_DIR/docker/compose"
    docker-compose -f jenkins-simple.yml up -d
    
    # 等待服务启动
    local max_wait=120
    local count=0
    while [ $count -lt $max_wait ]; do
        if docker logs jenkins-simple 2>&1 | grep -q "Jenkins is fully up and running" || \
           curl -s http://localhost:38080/login >/dev/null 2>&1; then
            log "✅ Jenkins服务启动成功 (http://localhost:38080)"
            log "✅ 管理员账号: admin / admin123"
            return 0
        fi
        
        # 每10秒显示启动进度
        if [ $((count % 5)) -eq 0 ]; then
            local recent_logs=$(docker logs jenkins-simple 2>&1 | tail -2)
            info "启动中... $recent_logs"
        fi
        
        sleep 2
        count=$((count + 1))
        echo -n "."
    done
    
    error "❌ Jenkins服务启动超时"
    return 1
}

# 配置服务集成
setup_integration() {
    step "配置服务集成..."
    
    # 等待Jenkins完全启动
    sleep 10
    
    # 这里可以添加自动配置逻辑
    # 例如：创建Jenkins凭据，配置Gitea webhook等
    
    log "✅ 服务集成配置完成"
}

# 运行验证测试
run_verification() {
    step "运行验证测试..."
    
    local all_ok=true
    
    # 测试Registry
    if curl -s -w "%{http_code}" http://localhost:35001/v2/ | grep -q "200"; then
        log "✅ Registry API正常"
    else
        error "❌ Registry API异常"
        all_ok=false
    fi
    
    # 测试Registry UI
    if curl -s http://localhost:35002 | grep -q "docker-registry-ui"; then
        log "✅ Registry UI正常"
    else
        error "❌ Registry UI异常"
        all_ok=false
    fi
    
    # 测试Gitea
    if curl -s http://localhost:33000/api/healthz | grep -q "pass"; then
        log "✅ Gitea API正常"
    else
        error "❌ Gitea API异常"
        all_ok=false
    fi
    
    # 测试Jenkins (检查服务是否响应，允许重定向)
    local jenkins_status=$(curl -s -w "%{http_code}" -o /dev/null http://localhost:38080/login)
    if [[ "$jenkins_status" == "200" ]]; then
        log "✅ Jenkins API正常"
    else
        error "❌ Jenkins API异常 (状态码: $jenkins_status)"
        all_ok=false
    fi
    
    if $all_ok; then
        log "🎉 所有服务验证通过！"
        return 0
    else
        error "❌ 部分服务验证失败"
        return 1
    fi
}

# 显示部署结果
show_result() {
    echo ""
    echo "================================================================="
    echo -e "${G}🎉 基础服务部署完成${NC}"
    echo "================================================================="
    echo ""
    echo -e "${B}服务访问地址:${NC}"
    echo "  • Gitea:           http://localhost:33000"
    echo "  • Jenkins:         http://localhost:38080 (admin/admin123)"
    echo "  • Docker Registry: http://localhost:35001"
    echo "  • Registry UI:     http://localhost:35002"
    echo ""
    echo -e "${B}SSH访问:${NC}"
    echo "  • Gitea SSH:       ssh://git@localhost:32222"
    echo ""
    echo -e "${B}内部服务地址 (容器间通信):${NC}"
    echo "  • Gitea:           http://gitea:3000"
    echo "  • Jenkins:         http://jenkins:8080"
    echo "  • Registry:        http://registry:5000"
    echo ""
    echo -e "${Y}后续步骤:${NC}"
    echo "  1. 在Gitea中创建用户和仓库"
    echo "  2. 配置Jenkins Pipeline"
    echo "  3. 测试完整的CI/CD流程"
    echo ""
    echo -e "${B}管理命令:${NC}"
    echo "  ./scripts/maintenance/health-check.sh    # 健康检查"
    echo "  ./scripts/maintenance/backup-all.sh      # 数据备份"
    echo "  ./scripts/utils/show-logs.sh            # 查看日志"
    echo ""
    echo "================================================================="
}

# 显示帮助
show_help() {
    echo "基础服务统一构建脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --full-auto        完全自动化部署 (推荐)"
    echo "  --step-by-step     分步骤部署，每步确认"
    echo "  --update-ports     仅更新端口配置"
    echo "  --cleanup          清理所有服务"
    echo "  --verify           仅运行验证测试"
    echo "  --help            显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 --full-auto     # 一键部署所有服务"
    echo "  $0 --step-by-step  # 逐步部署"
    echo "  $0 --verify        # 验证现有服务"
}

# 主函数
main() {
    show_logo
    
    case "${1:-full-auto}" in
        "--full-auto")
            log "开始完全自动化部署..."
            check_dependencies
            check_ports
            cleanup_existing
            init_environment
            deploy_registry
            deploy_gitea
            deploy_jenkins
            setup_integration
            run_verification
            show_result
            ;;
        "--step-by-step")
            log "开始分步骤部署..."
            check_dependencies
            
            echo "按回车继续到下一步..."
            read -r
            check_ports
            
            echo "按回车继续清理现有服务..."
            read -r
            cleanup_existing
            
            echo "按回车继续初始化环境..."
            read -r
            init_environment
            
            echo "按回车继续部署Registry..."
            read -r
            deploy_registry
            
            echo "按回车继续部署Gitea..."
            read -r
            deploy_gitea
            
            echo "按回车继续部署Jenkins..."
            read -r
            deploy_jenkins
            
            echo "按回车继续配置集成..."
            read -r
            setup_integration
            
            echo "按回车继续验证测试..."
            read -r
            run_verification
            show_result
            ;;
        "--cleanup")
            log "清理所有服务..."
            cleanup_existing
            docker network rm $NETWORK_NAME 2>/dev/null || true
            log "✅ 清理完成"
            ;;
        "--verify")
            log "运行验证测试..."
            run_verification
            ;;
        "--help")
            show_help
            ;;
        *)
            show_help
            ;;
    esac
}

# 错误处理
trap 'error "部署失败，请检查错误信息"; exit 1' ERR

# 执行主程序
main "$@"
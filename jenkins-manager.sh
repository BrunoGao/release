#!/bin/bash
# Jenkins CI/CD环境管理脚本

BASE_DIR="/Users/brunogao/work/infra"
COMPOSE_FILE="$BASE_DIR/docker/compose/jenkins-simple.yml"

# 颜色定义
G='\033[0;32m'
Y='\033[1;33m'
R='\033[0;31m'
B='\033[0;34m'
NC='\033[0m'

log() { echo -e "${G}[INFO]${NC} $1"; }
warn() { echo -e "${Y}[WARN]${NC} $1"; }
error() { echo -e "${R}[ERROR]${NC} $1"; }
info() { echo -e "${B}[INFO]${NC} $1"; }

# 显示状态
show_status() {
    echo "==================== Jenkins CI/CD 状态 ===================="
    
    echo -e "\n${B}🔧 服务状态：${NC}"
    docker-compose -f "$COMPOSE_FILE" ps
    
    echo -e "\n${B}🌐 访问地址：${NC}"
    echo "Jenkins:      http://localhost:8081"
    echo "Registry:     http://localhost:5001"
    echo "Registry UI:  http://localhost:5002"  
    echo "Gitea:        http://192.168.1.6:3000"
    
    if docker ps | grep -q jenkins-simple; then
        echo -e "\n${B}🔑 管理员密码：${NC}"
        docker exec jenkins-simple cat /var/jenkins_home/secrets/initialAdminPassword 2>/dev/null || echo "已完成初始化"
    fi
    
    echo -e "\n${B}💾 存储使用：${NC}"
    docker system df
    
    echo "========================================================="
}

# 启动服务
start_services() {
    log "启动Jenkins CI/CD环境..."
    
    # 创建网络
    docker network create cicd-network 2>/dev/null || true
    
    # 启动服务
    docker-compose -f "$COMPOSE_FILE" up -d
    
    log "等待Jenkins启动..."
    for i in {1..30}; do
        if curl -sf "http://localhost:8081" &>/dev/null; then
            log "✅ Jenkins启动成功！"
            break
        fi
        sleep 2
        echo -n "."
    done
    echo ""
    
    show_status
}

# 停止服务
stop_services() {
    log "停止Jenkins CI/CD环境..."
    docker-compose -f "$COMPOSE_FILE" down
    log "✅ 服务已停止"
}

# 重启服务
restart_services() {
    log "重启Jenkins CI/CD环境..."
    docker-compose -f "$COMPOSE_FILE" restart
    log "✅ 服务已重启"
}

# 查看日志
show_logs() {
    log "显示Jenkins日志（按Ctrl+C退出）..."
    docker logs jenkins-simple -f
}

# 备份配置
backup_config() {
    local backup_dir="$BASE_DIR/backup/jenkins"
    local backup_file="jenkins-backup-$(date +%Y%m%d_%H%M%S).tar.gz"
    
    log "备份Jenkins配置..."
    mkdir -p "$backup_dir"
    
    docker exec jenkins-simple tar czf "/tmp/$backup_file" -C /var/jenkins_home . 2>/dev/null
    docker cp "jenkins-simple:/tmp/$backup_file" "$backup_dir/"
    docker exec jenkins-simple rm "/tmp/$backup_file"
    
    log "✅ 备份完成：$backup_dir/$backup_file"
}

# 恢复配置
restore_config() {
    local backup_dir="$BASE_DIR/backup/jenkins"
    
    log "可用备份文件："
    ls -la "$backup_dir"/*.tar.gz 2>/dev/null || {
        error "没有找到备份文件"
        return 1
    }
    
    echo -n "请输入备份文件名: "
    read backup_file
    
    if [[ ! -f "$backup_dir/$backup_file" ]]; then
        error "备份文件不存在"
        return 1
    fi
    
    warn "此操作将覆盖当前配置，是否继续？(y/N)"
    read -r confirm
    if [[ $confirm != "y" && $confirm != "Y" ]]; then
        log "操作已取消"
        return 0
    fi
    
    log "恢复Jenkins配置..."
    docker cp "$backup_dir/$backup_file" jenkins-simple:/tmp/
    docker exec jenkins-simple tar xzf "/tmp/$backup_file" -C /var/jenkins_home
    docker exec jenkins-simple rm "/tmp/$backup_file"
    docker restart jenkins-simple
    
    log "✅ 配置已恢复，Jenkins正在重启..."
}

# 清理资源
cleanup() {
    log "清理Jenkins环境..."
    
    warn "此操作将删除所有Jenkins数据，是否继续？(y/N)"
    read -r confirm
    if [[ $confirm != "y" && $confirm != "Y" ]]; then
        log "操作已取消"
        return 0
    fi
    
    docker-compose -f "$COMPOSE_FILE" down -v
    docker volume prune -f
    docker system prune -f
    
    log "✅ 清理完成"
}

# 安装插件
install_plugins() {
    log "常用插件列表："
    echo "1. build-timeout"
    echo "2. docker-workflow"
    echo "3. gitea"
    echo "4. blueocean"
    echo "5. kubernetes"
    echo "6. nodejs"
    echo "7. maven-plugin"
    echo "8. generic-webhook-trigger"
    
    echo -n "请输入插件名称: "
    read plugin_name
    
    if [[ -z "$plugin_name" ]]; then
        error "插件名称不能为空"
        return 1
    fi
    
    log "安装插件: $plugin_name"
    docker exec jenkins-simple jenkins-plugin-cli --plugins "$plugin_name:latest"
    
    log "重启Jenkins以激活插件..."
    docker restart jenkins-simple
    
    log "✅ 插件安装完成"
}

# 健康检查
health_check() {
    log "执行健康检查..."
    
    local status=0
    
    # 检查Docker服务
    if ! docker info &>/dev/null; then
        error "❌ Docker服务异常"
        ((status++))
    else
        log "✅ Docker服务正常"
    fi
    
    # 检查Jenkins服务
    if ! curl -sf "http://localhost:8081" &>/dev/null; then
        error "❌ Jenkins服务异常"
        ((status++))
    else
        log "✅ Jenkins服务正常"
    fi
    
    # 检查Registry服务
    if ! curl -sf "http://localhost:5001/v2/" &>/dev/null; then
        warn "⚠️  Registry服务异常"
    else
        log "✅ Registry服务正常"
    fi
    
    # 检查Gitea服务
    if ! curl -sf "http://192.168.1.6:3000" &>/dev/null; then
        warn "⚠️  Gitea服务异常"
    else
        log "✅ Gitea服务正常"
    fi
    
    # 检查磁盘空间
    local disk_usage=$(df -h "$BASE_DIR" | awk 'NR==2{print $5}' | sed 's/%//')
    if [[ $disk_usage -gt 80 ]]; then
        warn "⚠️  磁盘使用率过高: ${disk_usage}%"
    else
        log "✅ 磁盘空间充足: ${disk_usage}%"
    fi
    
    if [[ $status -eq 0 ]]; then
        log "🎉 系统健康状态良好"
    else
        error "❌ 发现 $status 个问题，请检查"
    fi
    
    return $status
}

# 显示帮助
show_help() {
    echo "Jenkins CI/CD环境管理脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  status     显示服务状态"
    echo "  start      启动所有服务"
    echo "  stop       停止所有服务" 
    echo "  restart    重启所有服务"
    echo "  logs       查看Jenkins日志"
    echo "  backup     备份Jenkins配置"
    echo "  restore    恢复Jenkins配置"
    echo "  cleanup    清理所有数据"
    echo "  plugins    安装插件"
    echo "  health     健康检查"
    echo "  help       显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start      # 启动Jenkins环境"
    echo "  $0 status     # 查看状态"
    echo "  $0 backup     # 备份配置"
}

# 主程序
main() {
    case "${1:-help}" in
        "status")   show_status ;;
        "start")    start_services ;;
        "stop")     stop_services ;;
        "restart")  restart_services ;;
        "logs")     show_logs ;;
        "backup")   backup_config ;;
        "restore")  restore_config ;;
        "cleanup")  cleanup ;;
        "plugins")  install_plugins ;;
        "health")   health_check ;;
        "help"|*)   show_help ;;
    esac
}

# 检查Docker是否运行
if ! docker info &>/dev/null; then
    error "Docker未运行，请先启动Docker"
    exit 1
fi

# 执行主程序
main "$@" 
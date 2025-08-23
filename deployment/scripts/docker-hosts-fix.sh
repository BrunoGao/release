#!/bin/bash
# Docker Hosts文件修复脚本 - 解决DNS解析问题

G='\033[0;32m'; Y='\033[1;33m'; R='\033[0;31m'; NC='\033[0m'
log() { echo -e "${G}[INFO]${NC} $1"; }
warn() { echo -e "${Y}[WARN]${NC} $1"; }
error() { echo -e "${R}[ERROR]${NC} $1"; }

HOSTS_FILE="/etc/hosts"
DOCKER_ENTRIES="# Docker Registry Fix
127.0.0.1 iosapp-beta.grammarly.com
54.87.120.168 registry-1.docker.io
54.87.120.168 index.docker.io
54.87.120.168 auth.docker.io
54.87.120.168 production.cloudflare.docker.com
52.206.163.69 dseasb33srnds.cloudfront.net"

log "=== Docker Hosts修复脚本 ==="

# 备份hosts文件
backup_hosts() {
    log "备份hosts文件..."
    sudo cp $HOSTS_FILE ${HOSTS_FILE}.backup.$(date +%Y%m%d_%H%M%S)
    log "✅ 已备份到 ${HOSTS_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
}

# 清理旧的Docker条目
clean_old_entries() {
    log "清理旧的Docker条目..."
    sudo sed -i '' '/# Docker/d' $HOSTS_FILE
    sudo sed -i '' '/docker\.io/d' $HOSTS_FILE
    sudo sed -i '' '/grammarly\.com/d' $HOSTS_FILE
    sudo sed -i '' '/cloudfront\.net/d' $HOSTS_FILE
    sudo sed -i '' '/cloudflare\.docker\.com/d' $HOSTS_FILE
    log "✅ 旧条目已清理"
}

# 添加Docker解析条目
add_docker_entries() {
    log "添加Docker域名解析..."
    echo "$DOCKER_ENTRIES" | sudo tee -a $HOSTS_FILE > /dev/null
    log "✅ Docker域名解析已添加"
}

# 测试Docker连接
test_docker() {
    log "测试Docker连接..."
    
    if docker pull hello-world:latest > /dev/null 2>&1; then
        log "✅ Docker拉取测试成功"
        docker rmi hello-world:latest > /dev/null 2>&1
        return 0
    else
        error "❌ Docker拉取测试失败"
        return 1
    fi
}

# 显示当前配置
show_status() {
    log "当前Docker相关hosts条目："
    grep -E "(docker|grammarly)" $HOSTS_FILE || echo "未找到相关条目"
}

# 恢复备份
restore_backup() {
    local backup_file="${HOSTS_FILE}.backup.$(date +%Y%m%d)_*"
    local latest_backup=$(ls -t ${HOSTS_FILE}.backup.* 2>/dev/null | head -1)
    
    if [ -n "$latest_backup" ]; then
        log "恢复备份: $latest_backup"
        sudo cp "$latest_backup" $HOSTS_FILE
        log "✅ 已恢复备份"
    else
        error "❌ 未找到备份文件"
    fi
}

# 主菜单
main_menu() {
    echo ""
    echo "选择操作："
    echo "1) 修复Docker hosts (推荐)"
    echo "2) 清理Docker条目"
    echo "3) 显示当前状态"
    echo "4) 测试Docker连接"
    echo "5) 恢复备份"
    echo "0) 退出"
    echo ""
    
    read -p "请选择 (0-5): " choice
    
    case $choice in
        1) 
            backup_hosts
            clean_old_entries
            add_docker_entries
            test_docker
            ;;
        2) 
            clean_old_entries
            ;;
        3) 
            show_status
            ;;
        4) 
            test_docker
            ;;
        5) 
            restore_backup
            ;;
        0) 
            log "退出"
            exit 0
            ;;
        *) 
            error "无效选择"
            ;;
    esac
}

# 主函数
main() {
    # 检查权限
    if [ "$EUID" -eq 0 ]; then
        warn "请不要以root身份运行此脚本"
        exit 1
    fi
    
    # 检查Docker是否运行
    if ! docker info > /dev/null 2>&1; then
        warn "Docker未运行或不可用"
        log "请先启动Docker"
    fi
    
    while true; do
        main_menu
        echo ""
        read -p "继续操作? (y/n): " continue_choice
        if [[ $continue_choice != "y" && $continue_choice != "Y" ]]; then
            break
        fi
    done
    
    log "操作完成！"
}

main "$@" 
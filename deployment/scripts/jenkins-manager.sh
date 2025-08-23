#!/bin/bash
# Jenkins管理脚本 - 持久化配置和高效运行

set -e
BASE_DIR="/Users/brunogao/work/infra"
JENKINS_HOME="$BASE_DIR/data/jenkins"
BACKUP_DIR="$BASE_DIR/backup/jenkins"
CONFIG_DIR="$BASE_DIR/docker/compose/jenkins"

# 创建必要目录
init_dirs() {
    mkdir -p "$JENKINS_HOME" "$BACKUP_DIR" "$CONFIG_DIR"/{config,plugins,scripts}
    echo "✓ 目录初始化完成"
}

# 备份Jenkins配置
backup_jenkins() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/jenkins_backup_$timestamp.tar.gz"
    
    echo "开始备份Jenkins配置..."
    tar -czf "$backup_file" -C "$JENKINS_HOME" \
        config.xml jobs/ plugins/ secrets/ users/ \
        2>/dev/null || true
    echo "✓ 备份完成: $backup_file"
}

# 恢复Jenkins配置
restore_jenkins() {
    local backup_file="$1"
    if [[ -z "$backup_file" ]]; then
        echo "❌ 请指定备份文件路径"
        return 1
    fi
    
    echo "恢复Jenkins配置..."
    tar -xzf "$backup_file" -C "$JENKINS_HOME"
    docker-compose -f "$BASE_DIR/docker/compose/jenkins-compose.yml" restart jenkins
    echo "✓ 恢复完成"
}

# 优化Jenkins性能
optimize_jenkins() {
    echo "优化Jenkins性能..."
    
    # 清理旧构建
    find "$JENKINS_HOME/jobs" -name "builds" -type d -exec find {} -name "*" -mtime +30 -delete \; 2>/dev/null || true
    
    # 清理工作空间
    find "$JENKINS_HOME/workspace" -type d -mtime +7 -exec rm -rf {} + 2>/dev/null || true
    
    # 清理日志
    find "$JENKINS_HOME/logs" -name "*.log" -mtime +7 -delete 2>/dev/null || true
    
    echo "✓ 性能优化完成"
}

# 安装推荐插件
install_plugins() {
    local plugins=(
        "build-timeout" "credentials-binding" "timestamper" "ws-cleanup"
        "ant" "gradle" "pipeline-stage-view" "git" "gitea" "docker-plugin"
        "docker-build-step" "docker-commons" "docker-workflow"
        "configuration-as-code" "job-dsl" "blueocean"
    )
    
    echo "安装推荐插件..."
    for plugin in "${plugins[@]}"; do
        echo "$plugin:latest" >> "$CONFIG_DIR/plugins/plugins.txt"
    done
    echo "✓ 插件列表已更新"
}

# 健康检查
health_check() {
    echo "Jenkins健康检查..."
    
    # 检查服务状态
    if curl -s "http://localhost:8081/jenkins/login" > /dev/null; then
        echo "✓ Jenkins服务正常"
    else
        echo "❌ Jenkins服务异常"
        return 1
    fi
    
    # 检查磁盘空间
    local disk_usage=$(df -h "$JENKINS_HOME" | awk 'NR==2 {print $5}' | sed 's/%//')
    if [[ $disk_usage -gt 80 ]]; then
        echo "⚠️  磁盘使用率过高: ${disk_usage}%"
    else
        echo "✓ 磁盘空间充足: ${disk_usage}%"
    fi
    
    # 检查内存使用
    local memory_info=$(docker stats jenkins --no-stream --format "table {{.MemUsage}}")
    echo "✓ 内存使用: $memory_info"
}

# 启动Jenkins
start_jenkins() {
    echo "启动Jenkins服务..."
    cd "$BASE_DIR/docker/compose"
    docker-compose -f jenkins-compose.yml up -d
    
    # 等待服务启动
    echo "等待Jenkins启动..."
    for i in {1..30}; do
        if curl -s "http://localhost:8081/jenkins/login" > /dev/null; then
            echo "✓ Jenkins启动成功"
            return 0
        fi
        sleep 5
    done
    echo "❌ Jenkins启动超时"
    return 1
}

# 停止Jenkins
stop_jenkins() {
    echo "停止Jenkins服务..."
    cd "$BASE_DIR/docker/compose"
    docker-compose -f jenkins-compose.yml down
    echo "✓ Jenkins已停止"
}

# 显示菜单
show_menu() {
    echo "=== Jenkins管理工具 ==="
    echo "1. 初始化环境"
    echo "2. 启动Jenkins"
    echo "3. 停止Jenkins"
    echo "4. 备份配置"
    echo "5. 恢复配置"
    echo "6. 性能优化"
    echo "7. 安装插件"
    echo "8. 健康检查"
    echo "9. 退出"
    echo -n "选择操作: "
}

# 主程序
main() {
    while true; do
        show_menu
        read -r choice
        case $choice in
            1) init_dirs ;;
            2) start_jenkins ;;
            3) stop_jenkins ;;
            4) backup_jenkins ;;
            5) 
                echo -n "输入备份文件路径: "
                read -r backup_file
                restore_jenkins "$backup_file"
                ;;
            6) optimize_jenkins ;;
            7) install_plugins ;;
            8) health_check ;;
            9) exit 0 ;;
            *) echo "❌ 无效选择" ;;
        esac
        echo "按回车键继续..."
        read -r
    done
}

# 如果直接运行脚本
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 
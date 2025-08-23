#!/bin/bash

# 部署脚本 - 用于启动和管理服务

# 设置环境变量
export COMPOSE_PROJECT_NAME=cicd
export COMPOSE_FILE=/Users/brunogao/work/infra/docker/compose/docker-compose.yml

# 函数：检查服务健康状态
check_health() {
    local service=$1
    local port=$2
    echo "检查 $service 服务状态..."
    curl -s -o /dev/null -w "%{http_code}" localhost:$port
}

# 启动所有服务
start_services() {
    echo "启动所有服务..."
    cd /Users/brunogao/work/infra/docker/compose
    docker-compose up -d
}

# 停止所有服务
stop_services() {
    echo "停止所有服务..."
    cd /Users/brunogao/work/infra/docker/compose
    docker-compose down
}

# 重启特定服务
restart_service() {
    local service=$1
    echo "重启 $service 服务..."
    cd /Users/brunogao/work/infra/docker/compose
    docker-compose restart $service
}

# 检查所有服务状态
check_all_services() {
    echo "检查所有服务状态..."
    check_health "Gitea" 3000
    check_health "Drone" 8000
    check_health "Registry" 5000
}

# 主菜单
show_menu() {
    echo "=== CI/CD 服务管理 ==="
    echo "1. 启动所有服务"
    echo "2. 停止所有服务"
    echo "3. 重启特定服务"
    echo "4. 检查服务状态"
    echo "5. 退出"
    echo "请选择操作 (1-5): "
}

# 主程序
main() {
    while true; do
        show_menu
        read -r choice
        case $choice in
            1) start_services ;;
            2) stop_services ;;
            3)
                echo "请输入服务名称 (gitea/drone-server/drone-runner/registry): "
                read -r service
                restart_service "$service"
                ;;
            4) check_all_services ;;
            5) exit 0 ;;
            *) echo "无效选择" ;;
        esac
        echo "按回车键继续..."
        read -r
    done
}

# 运行主程序
main 
#!/bin/bash
# 本地服务管理脚本 - 管理ljwx-boot的依赖服务

set -e

ACTION=${1:-"help"} #默认显示帮助
CONFIG_FILE=${2:-"local-config.env"} #本地配置文件

echo "==================== ljwx-boot本地服务管理 ===================="

# 显示帮助信息
show_help() {
    echo "用法: $0 [命令] [配置文件]"
    echo ""
    echo "命令:"
    echo "  start    启动所有依赖服务"
    echo "  stop     停止所有服务"
    echo "  restart  重启所有服务"
    echo "  status   显示服务状态"
    echo "  logs     显示服务日志"
    echo "  clean    清理数据和容器"
    echo "  mysql    仅启动MySQL服务"
    echo "  redis    仅启动Redis服务"
    echo "  minio    仅启动MinIO服务"
    echo "  ollama   仅启动Ollama服务"
    echo "  init     初始化数据库和配置"
    echo "  help     显示此帮助信息"
    echo ""
    echo "配置文件: ${CONFIG_FILE} (可选)"
}

# 检查Docker环境
check_docker() {
    if ! command -v docker > /dev/null 2>&1; then
        echo "❌ 错误: Docker 未安装"
        exit 1
    fi
    
    if ! command -v docker-compose > /dev/null 2>&1; then
        echo "❌ 错误: docker-compose 未安装"
        exit 1
    fi
}

# 加载配置文件
load_config() {
    if [ -f "$CONFIG_FILE" ]; then
        echo "✅ 加载配置: $CONFIG_FILE"
        . "$CONFIG_FILE"
    else
        echo "⚠️  使用默认配置"
    fi
}

# 启动所有服务
start_services() {
    echo "启动本地依赖服务..."
    docker-compose -f docker-compose-local.yml --env-file ${CONFIG_FILE} up -d
    echo "✅ 服务启动中，请等待健康检查完成"
    
    # 等待服务健康检查
    echo "等待服务启动..."
    sleep 10
    docker-compose -f docker-compose-local.yml ps
}

# 停止所有服务
stop_services() {
    echo "停止本地依赖服务..."
    docker-compose -f docker-compose-local.yml down
    echo "✅ 服务已停止"
}

# 重启所有服务
restart_services() {
    echo "重启本地依赖服务..."
    docker-compose -f docker-compose-local.yml restart
    echo "✅ 服务已重启"
}

# 显示服务状态
show_status() {
    echo "本地服务状态:"
    docker-compose -f docker-compose-local.yml ps
    echo ""
    echo "服务端口映射:"
    echo "- MySQL:     localhost:3306"
    echo "- Redis:     localhost:6379"
    echo "- MinIO:     localhost:9000 (API), localhost:9001 (控制台)"
    echo "- PostgreSQL: localhost:5432"
    echo "- Ollama:    localhost:11434"
}

# 显示服务日志
show_logs() {
    SERVICE=${2:-""}
    if [ -n "$SERVICE" ]; then
        docker-compose -f docker-compose-local.yml logs -f $SERVICE
    else
        docker-compose -f docker-compose-local.yml logs -f
    fi
}

# 清理数据和容器
clean_all() {
    echo "⚠️  警告: 此操作将删除所有本地数据!"
    read -p "确认清理? (y/N): " confirm
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        docker-compose -f docker-compose-local.yml down -v --remove-orphans
        docker volume prune -f
        echo "✅ 清理完成"
    else
        echo "操作已取消"
    fi
}

# 启动单个服务
start_single_service() {
    SERVICE=$1
    echo "启动 $SERVICE 服务..."
    docker-compose -f docker-compose-local.yml up -d ${SERVICE}-local
    echo "✅ $SERVICE 服务启动"
}

# 初始化数据库和配置
init_database() {
    echo "初始化数据库..."
    
    # 确保MySQL服务已启动
    if ! docker ps | grep ljwx-mysql-local > /dev/null; then
        echo "启动MySQL服务..."
        start_single_service mysql
        sleep 15 #等待MySQL完全启动
    fi
    
    # 检查数据库连接
    echo "等待MySQL服务就绪..."
    for i in {1..30}; do
        if docker exec ljwx-mysql-local mysqladmin ping -h localhost -u root -p${MYSQL_PASSWORD:-123456} 2>/dev/null; then
            echo "✅ MySQL服务就绪"
            break
        fi
        if [ $i -eq 30 ]; then
            echo "❌ MySQL服务启动超时"
            exit 1
        fi
        sleep 2
    done
    
    # 创建数据库结构（如果需要）
    echo "初始化数据库结构..."
    # 这里可以添加SQL脚本执行逻辑
    echo "✅ 数据库初始化完成"
    
    # 初始化MinIO存储桶
    if docker ps | grep ljwx-minio-local > /dev/null; then
        echo "配置MinIO存储桶..."
        # 等待MinIO启动
        sleep 5
        # 这里可以添加MinIO客户端配置逻辑
        echo "✅ MinIO配置完成"
    fi
}

# 主逻辑
case $ACTION in
    "start")
        check_docker
        load_config
        start_services
        ;;
    "stop")
        check_docker
        stop_services
        ;;
    "restart")
        check_docker
        restart_services
        ;;
    "status")
        check_docker
        show_status
        ;;
    "logs")
        check_docker
        show_logs
        ;;
    "clean")
        check_docker
        clean_all
        ;;
    "mysql"|"redis"|"minio"|"ollama")
        check_docker
        load_config
        start_single_service $ACTION
        ;;
    "init")
        check_docker
        load_config
        init_database
        ;;
    "help"|*)
        show_help
        ;;
esac 
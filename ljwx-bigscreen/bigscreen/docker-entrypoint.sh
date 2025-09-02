#!/bin/bash

# LJWX BigScreen Docker 入口脚本
# 版本: 1.3.1

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date +'%Y-%m-%d %H:%M:%S') $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date +'%Y-%m-%d %H:%M:%S') $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date +'%Y-%m-%d %H:%M:%S') $1"
}

log_debug() {
    if [ "$LOG_LEVEL" = "DEBUG" ]; then
        echo -e "${BLUE}[DEBUG]${NC} $(date +'%Y-%m-%d %H:%M:%S') $1"
    fi
}

# 显示启动横幅
show_banner() {
    cat << 'EOF'
    
 _      _ __          __ __   ____  _            _____                          
| |    | |\ \        / /\ \ |  _ \(_)          / ____|                         
| |    | | \ \  /\  / /  \ \| |_) |_  ___  ___| |     _ __ ___  ___ _ __        
| |    | |  \ \/  \/ /    \ \|  _ <| |/ _ \/ __| |    | '__/ _ \/ _ \ '__|       
| |____| |   \  /\  /      \ \ |_) | | (_) \__ \ |____| | |  __/  __/ |          
|______|_|    \/  \/        \_\____/|_|\___/|___/\_____|_|  \___|\___|_|          
                                                                                 
                        Multi-Architecture Support                              
                            Version: 1.3.1                                     
                                                                                 
EOF
}

# 检查必需的环境变量
check_environment() {
    log_info "检查环境变量配置..."
    
    # 必需的环境变量
    REQUIRED_VARS=(
        "MYSQL_HOST"
        "MYSQL_PORT"
        "REDIS_HOST" 
        "REDIS_PORT"
    )
    
    local missing_vars=()
    for var in "${REQUIRED_VARS[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        log_error "缺少必需的环境变量: ${missing_vars[*]}"
        log_error "请设置这些环境变量后重试"
        exit 1
    fi
    
    # 显示配置信息
    log_info "数据库配置: ${MYSQL_HOST}:${MYSQL_PORT}/${MYSQL_DATABASE:-ljwx}"
    log_info "Redis配置: ${REDIS_HOST}:${REDIS_PORT}/${REDIS_DB:-0}"
    log_info "日志级别: ${LOG_LEVEL:-INFO}"
    log_info "Flask环境: ${FLASK_ENV:-production}"
}

# 等待服务就绪
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local timeout=${4:-30}
    
    log_info "等待 ${service_name} 服务就绪 (${host}:${port})..."
    
    local count=0
    while ! nc -z "$host" "$port"; do
        count=$((count + 1))
        if [ $count -ge $timeout ]; then
            log_error "${service_name} 服务在 ${timeout} 秒内未就绪"
            return 1
        fi
        log_debug "等待 ${service_name} 服务... ($count/$timeout)"
        sleep 1
    done
    
    log_info "${service_name} 服务已就绪 ✓"
    return 0
}

# 安装 netcat 用于连接检查
install_dependencies() {
    if ! command -v nc >/dev/null 2>&1; then
        log_info "安装必需的系统工具..."
        apt-get update -qq
        apt-get install -y -qq netcat-openbsd
        rm -rf /var/lib/apt/lists/*
    fi
}

# 数据库连接检查
check_database_connection() {
    log_info "检查数据库连接..."
    
    if ! wait_for_service "$MYSQL_HOST" "$MYSQL_PORT" "MySQL" 60; then
        log_error "无法连接到 MySQL 数据库"
        exit 1
    fi
    
    # 测试数据库连接
    python3 -c "
import mysql.connector
import sys
import os

try:
    conn = mysql.connector.connect(
        host=os.getenv('MYSQL_HOST'),
        port=int(os.getenv('MYSQL_PORT', 3306)),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', ''),
        database=os.getenv('MYSQL_DATABASE', 'ljwx')
    )
    conn.close()
    print('数据库连接测试成功 ✓')
except Exception as e:
    print(f'数据库连接失败: {e}', file=sys.stderr)
    sys.exit(1)
    "
}

# Redis 连接检查
check_redis_connection() {
    log_info "检查 Redis 连接..."
    
    if ! wait_for_service "$REDIS_HOST" "$REDIS_PORT" "Redis" 30; then
        log_warn "Redis 连接失败，但应用仍可继续运行"
        return 0
    fi
    
    # 测试 Redis 连接
    python3 -c "
import redis
import sys
import os

try:
    r = redis.Redis(
        host=os.getenv('REDIS_HOST'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        db=int(os.getenv('REDIS_DB', 0))
    )
    r.ping()
    print('Redis 连接测试成功 ✓')
except Exception as e:
    print(f'Redis 连接失败: {e}', file=sys.stderr)
    " || log_warn "Redis 连接失败，但应用仍可继续运行"
}

# 初始化应用
initialize_app() {
    log_info "初始化应用..."
    
    # 创建必要的目录
    mkdir -p logs static/uploads cache
    
    # 设置权限
    chmod -R 755 logs static cache
    
    # 检查应用文件
    if [ ! -f "run.py" ]; then
        log_error "找不到应用入口文件 run.py"
        exit 1
    fi
    
    log_info "应用初始化完成 ✓"
}

# 显示系统信息
show_system_info() {
    log_info "系统信息:"
    log_info "  容器架构: $(uname -m)"
    log_info "  Python版本: $(python3 --version)"
    log_info "  工作目录: $(pwd)"
    log_info "  用户: $(whoami)"
    log_info "  时区: $(cat /etc/timezone 2>/dev/null || echo 'Unknown')"
    log_info "  应用版本: ${APP_VERSION:-1.3.1}"
}

# 预检查模式
if [ "$1" = "precheck" ]; then
    show_banner
    log_info "执行预检查模式..."
    install_dependencies
    check_environment
    check_database_connection
    check_redis_connection
    log_info "✅ 所有预检查通过，应用可以正常启动"
    exit 0
fi

# 健康检查模式
if [ "$1" = "healthcheck" ]; then
    curl -f http://localhost:5001/api/health >/dev/null 2>&1
    exit $?
fi

# 版本信息模式
if [ "$1" = "version" ]; then
    echo "LJWX BigScreen v${APP_VERSION:-1.3.1}"
    exit 0
fi

# 主启动流程
main() {
    show_banner
    show_system_info
    
    # 安装必要的依赖
    install_dependencies
    
    # 环境检查
    check_environment
    
    # 服务连接检查
    check_database_connection
    check_redis_connection
    
    # 应用初始化
    initialize_app
    
    log_info "🚀 启动 LJWX BigScreen 应用..."
    log_info "监听端口: 5001"
    
    # 启动应用
    exec "$@"
}

# 信号处理
cleanup() {
    log_info "收到终止信号，正在优雅关闭..."
    # 这里可以添加清理逻辑
    exit 0
}

trap cleanup SIGTERM SIGINT

# 执行主函数
main "$@"
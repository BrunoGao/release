#!/bin/bash
# MySQL连接保活服务 - 防止长时间空置导致连接失效
# 支持跨平台运行 (macOS/Linux/CentOS)

LOG_FILE="/tmp/ljwx-mysql-keepalive.log"
MYSQL_CONTAINER="ljwx-mysql"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-123456}"

# 检测操作系统
OS=$(uname -s)

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 跨平台curl检测
check_curl() {
    if command -v curl >/dev/null 2>&1; then
        return 0
    elif command -v wget >/dev/null 2>&1; then
        return 1  # 使用wget
    else
        return 2  # 都没有
    fi
}

# 跨平台HTTP请求
http_request() {
    local url="$1"
    if check_curl; then
        curl -s "$url"
    else
        wget -qO- "$url" 2>/dev/null
    fi
}

keepalive_check() {
    # 检查MySQL连接
    if docker exec "$MYSQL_CONTAINER" mysqladmin ping -u root -p"$MYSQL_PASSWORD" >/dev/null 2>&1; then
        log "✅ MySQL连接正常"
        
        # 执行保活查询
        docker exec "$MYSQL_CONTAINER" mysql -u root -p"$MYSQL_PASSWORD" -e "SELECT 'keepalive' as status, NOW() as time;" >/dev/null 2>&1
        log "💓 保活查询已执行"
        
        # 检查连接数
        CONNECTIONS=$(docker exec "$MYSQL_CONTAINER" mysql -u root -p"$MYSQL_PASSWORD" -e "SHOW STATUS LIKE 'Threads_connected';" 2>/dev/null | tail -1 | awk '{print $2}')
        log "📊 当前连接数: $CONNECTIONS"
        
    else
        log "❌ MySQL连接失败，尝试重启服务"
        # 根据Docker Compose版本选择命令
        if command -v docker-compose >/dev/null 2>&1; then
            docker-compose restart ljwx-mysql
            sleep 30
            docker-compose restart ljwx-boot
        else
            docker compose restart ljwx-mysql
            sleep 30
            docker compose restart ljwx-boot
        fi
        log "🔄 服务重启完成"
    fi
    
    # 检查应用连接
    if http_request "http://localhost:9998/actuator/health/db" | grep -q "UP"; then
        log "✅ 应用数据源正常"
    else
        log "❌ 应用数据源异常"
        # 触发应用重连
        http_request "http://localhost:9998/actuator/refresh" >/dev/null 2>&1 || true
    fi
}

# 创建日志目录（如果需要）
case "$OS" in
    "Darwin")  # macOS
        # macOS使用/tmp，无需创建目录
        ;;
    "Linux")   # Linux
        # 尝试创建日志目录
        sudo mkdir -p /var/log 2>/dev/null || mkdir -p $(dirname "$LOG_FILE")
        ;;
esac

log "🚀 启动LJWX MySQL连接保活服务 (OS: $OS)"

# 主循环
while true; do
    keepalive_check
    sleep 300  # 每5分钟检查一次
done

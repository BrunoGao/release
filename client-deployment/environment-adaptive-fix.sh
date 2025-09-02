#!/bin/bash

# LJWX 环境自适应MySQL连接修复脚本
# 专门解决不同环境差异导致的连接问题

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔍 LJWX环境自适应修复工具${NC}"
echo "=================================="

# 环境检测函数
detect_environment() {
    echo -e "${BLUE}📊 检测当前环境特征...${NC}"
    
    # 检测操作系统
    OS=$(uname -s)
    ARCH=$(uname -m)
    echo -e "${BLUE}🖥️  操作系统: $OS $ARCH${NC}"
    
    # 检测Linux发行版（如果是Linux）
    if [ "$OS" = "Linux" ]; then
        if [ -f /etc/os-release ]; then
            DISTRO=$(grep '^ID=' /etc/os-release | cut -d'=' -f2 | tr -d '"')
            VERSION=$(grep '^VERSION_ID=' /etc/os-release | cut -d'=' -f2 | tr -d '"')
            echo -e "${BLUE}📦 Linux发行版: $DISTRO $VERSION${NC}"
        elif [ -f /etc/centos-release ]; then
            DISTRO="centos"
            VERSION=$(cat /etc/centos-release | grep -oE '[0-9]+\.[0-9]+')
            echo -e "${BLUE}📦 Linux发行版: $DISTRO $VERSION${NC}"
        fi
    fi
    
    # 检测Docker版本
    DOCKER_VERSION=$(docker --version 2>/dev/null | cut -d' ' -f3 | cut -d',' -f1)
    echo -e "${BLUE}🐳 Docker版本: $DOCKER_VERSION${NC}"
    
    # 检测当前用户
    CURRENT_USER=$(whoami)
    USER_ID=$(id -u)
    GROUP_ID=$(id -g)
    echo -e "${BLUE}👤 当前用户: $CURRENT_USER ($USER_ID:$GROUP_ID)${NC}"
    
    # 检测系统资源（跨平台）
    detect_system_resources
    
    # 检测磁盘类型（跨平台）
    detect_disk_type
    
    # 检测网络环境
    if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        NETWORK_STATUS="online"
    else
        NETWORK_STATUS="offline/restricted"
    fi
    echo -e "${BLUE}🌐 网络状态: $NETWORK_STATUS${NC}"
    
    echo ""
}

# 跨平台系统资源检测
detect_system_resources() {
    case "$OS" in
        "Darwin")  # macOS
            TOTAL_MEM=$(sysctl -n hw.memsize | awk '{print int($1/1024/1024/1024)}')
            AVAILABLE_MEM=$(vm_stat | awk '/Pages free:/{free=$3} /Pages inactive:/{inactive=$3} END{print int((free+inactive)*4096/1024/1024/1024)}')
            CPU_CORES=$(sysctl -n hw.ncpu)
            ;;
        "Linux")   # Linux (Ubuntu/CentOS等)
            if command -v free >/dev/null 2>&1; then
                TOTAL_MEM=$(free -g | awk '/^Mem:/{print $2}')
                AVAILABLE_MEM=$(free -g | awk '/^Mem:/{print $7}' 2>/dev/null || free -g | awk '/^Mem:/{print $4}')
            else
                # 备用方法（某些最小化系统可能没有free命令）
                TOTAL_MEM=$(cat /proc/meminfo | grep MemTotal | awk '{print int($2/1024/1024)}')
                AVAILABLE_MEM=$(cat /proc/meminfo | grep MemAvailable | awk '{print int($2/1024/1024)}' 2>/dev/null || echo "N/A")
            fi
            
            if command -v nproc >/dev/null 2>&1; then
                CPU_CORES=$(nproc)
            else
                CPU_CORES=$(grep -c ^processor /proc/cpuinfo)
            fi
            ;;
        *)
            TOTAL_MEM="unknown"
            AVAILABLE_MEM="unknown"
            CPU_CORES="unknown"
            ;;
    esac
    
    echo -e "${BLUE}💾 系统资源: ${CPU_CORES}核CPU, ${TOTAL_MEM}GB内存(可用${AVAILABLE_MEM}GB)${NC}"
}

# 跨平台磁盘类型检测
detect_disk_type() {
    DISK_TYPE="unknown"
    
    case "$OS" in
        "Darwin")  # macOS
            # 检测主磁盘类型
            if diskutil info / | grep -q "Solid State"; then
                DISK_TYPE="SSD"
            elif diskutil info / | grep -q "Rotational"; then
                DISK_TYPE="HDD"
            else
                # 尝试通过系统信息检测
                if system_profiler SPStorageDataType 2>/dev/null | grep -q "SSD\|Solid State"; then
                    DISK_TYPE="SSD"
                else
                    DISK_TYPE="HDD"
                fi
            fi
            ;;
        "Linux")   # Linux
            if command -v lsblk >/dev/null 2>&1; then
                # 使用lsblk检测（现代Linux系统）
                if lsblk -d -o name,rota 2>/dev/null | grep -q "0"; then
                    DISK_TYPE="SSD"
                else
                    DISK_TYPE="HDD"
                fi
            else
                # 备用方法：检查/sys/block/
                for disk in /sys/block/sd* /sys/block/nvme*; do
                    [ ! -e "$disk" ] && continue  # 跳过不存在的路径
                    if [ -f "$disk/queue/rotational" ]; then
                        if [ "$(cat $disk/queue/rotational)" = "0" ]; then
                            DISK_TYPE="SSD"
                            break
                        else
                            DISK_TYPE="HDD"
                        fi
                    fi
                done
            fi
            ;;
    esac
    
    echo -e "${BLUE}💿 存储类型: $DISK_TYPE${NC}"
}

# 环境适配配置生成
generate_adaptive_config() {
    echo -e "${BLUE}⚙️  生成环境适配配置...${NC}"
    
    # 基于环境特征调整MySQL配置
    local mysql_config=""
    
    # 内存适配（处理数字比较，兼容字符串情况）
    if [ "$TOTAL_MEM" != "unknown" ] && [ "$TOTAL_MEM" -ge 16 ] 2>/dev/null; then
        # 高内存环境
        mysql_config+="      - --innodb_buffer_pool_size=4G\n"
        mysql_config+="      - --max_connections=500\n"
        mysql_config+="      - --thread_cache_size=100\n"
        echo -e "${GREEN}✅ 高内存配置: 4GB缓冲池, 500连接${NC}"
    elif [ "$TOTAL_MEM" != "unknown" ] && [ "$TOTAL_MEM" -ge 8 ] 2>/dev/null; then
        # 中等内存环境
        mysql_config+="      - --innodb_buffer_pool_size=2G\n"
        mysql_config+="      - --max_connections=300\n"
        mysql_config+="      - --thread_cache_size=50\n"
        echo -e "${YELLOW}⚠️  中等内存配置: 2GB缓冲池, 300连接${NC}"
    else
        # 低内存环境或无法检测
        mysql_config+="      - --innodb_buffer_pool_size=512M\n"
        mysql_config+="      - --max_connections=200\n"
        mysql_config+="      - --thread_cache_size=20\n"
        echo -e "${YELLOW}⚠️  低内存/默认配置: 512MB缓冲池, 200连接${NC}"
    fi
    
    # 存储适配
    if [ "$DISK_TYPE" = "SSD" ]; then
        mysql_config+="      - --innodb_flush_log_at_trx_commit=2\n"
        mysql_config+="      - --innodb_io_capacity=2000\n"
        echo -e "${GREEN}✅ SSD优化配置${NC}"
    else
        mysql_config+="      - --innodb_flush_log_at_trx_commit=1\n"
        mysql_config+="      - --innodb_io_capacity=200\n"
        echo -e "${YELLOW}⚠️  HDD/默认保守配置${NC}"
    fi
    
    # 操作系统特定优化
    case "$OS" in
        "Darwin")  # macOS
            mysql_config+="      - --innodb_use_native_aio=0\n"  # macOS不支持native AIO
            echo -e "${BLUE}🍎 macOS特定优化: 禁用native AIO${NC}"
            ;;
        "Linux")   # Linux
            mysql_config+="      - --innodb_use_native_aio=1\n"  # Linux支持native AIO
            if [ "$DISTRO" = "centos" ] || [ "$DISTRO" = "rhel" ]; then
                # CentOS/RHEL特定优化
                mysql_config+="      - --skip-name-resolve\n"     # 跳过DNS解析
                echo -e "${BLUE}🔴 CentOS/RHEL特定优化: 跳过DNS解析${NC}"
            fi
            ;;
    esac
    
    # 长时间空置适配（核心配置）
    mysql_config+="      - --wait_timeout=86400\n"           # 24小时
    mysql_config+="      - --interactive_timeout=86400\n"    # 24小时
    mysql_config+="      - --net_read_timeout=600\n"         # 10分钟
    mysql_config+="      - --net_write_timeout=600\n"        # 10分钟
    mysql_config+="      - --connect_timeout=60\n"           # 1分钟
    mysql_config+="      - --max_connect_errors=100000\n"    # 大量连接错误容忍
    echo -e "${GREEN}✅ 长时间空置优化配置${NC}"
    
    # 生成适配的docker-compose配置
    cat > docker-compose-adaptive.yml << EOF
services:
  mysql:
    image: crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx/ljwx-mysql:1.2.4
    container_name: ljwx-mysql
    restart: unless-stopped
    user: "$USER_ID:$GROUP_ID"  # 使用当前用户权限
    environment:
      MYSQL_ROOT_PASSWORD: \${MYSQL_PASSWORD:-123456}
      MYSQL_DATABASE: lj-06
      MYSQL_CHARACTER_SET_SERVER: utf8mb4
      MYSQL_COLLATION_SERVER: utf8mb4_unicode_ci
      TZ: Asia/Shanghai
    ports:
      - "3306:3306"
    volumes:
      - ./data/mysql:/var/lib/mysql
      - ./logs/mysql:/var/log/mysql
      - ../backup/mysql:/backup/mysql
      - ./client-data.sql:/docker-entrypoint-initdb.d/client/data.sql:ro
      - ./client-admin.sql:/docker-entrypoint-initdb.d/client/admin.sql:ro
    command:
      - --default-authentication-plugin=mysql_native_password
      - --character-set-server=utf8mb4
      - --collation-server=utf8mb4_unicode_ci
      - --explicit_defaults_for_timestamp=true
      - --lower_case_table_names=1
      - --max_allowed_packet=128M
      - --sql_mode=STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO
$(echo -e "$mysql_config")
      - --log-error=/var/log/mysql/error.log
      - --slow-query-log=1
      - --slow-query-log-file=/var/log/mysql/slow.log
      - --long_query_time=2
    networks:
      - ljwx-network
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-p\${MYSQL_PASSWORD:-123456}"]
      interval: 10s  # 频繁检查
      timeout: 5s
      retries: 5
      start_period: 60s

  redis:
    image: crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx/ljwx-redis:1.1.7
    container_name: ljwx-redis
    restart: unless-stopped
    user: "$USER_ID:$GROUP_ID"  # 使用当前用户权限
    environment:
      TZ: Asia/Shanghai
    ports:
      - "6379:6379"
    volumes:
      - ./data/redis:/data
      - ./logs/redis:/var/log/redis
      - ../backup/redis:/backup/redis
    networks:
      - ljwx-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 5s
      retries: 3

  ljwx-boot:
    image: crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx/ljwx-boot:1.2.4
    container_name: ljwx-boot
    restart: unless-stopped
    env_file:
      - custom-config.env
    environment:
      SPRING_PROFILES_ACTIVE: common,docker-adaptive
      MYSQL_HOST: \${MYSQL_HOST:-mysql}
      MYSQL_PORT: \${MYSQL_PORT:-3306}
      MYSQL_USER: \${MYSQL_USER:-root}
      MYSQL_PASSWORD: \${MYSQL_PASSWORD:-123456}
      MYSQL_DATABASE: \${MYSQL_DATABASE:-lj-06}
      REDIS_HOST: \${REDIS_HOST:-redis}
      REDIS_PORT: \${REDIS_PORT:-6379}
      REDIS_PASSWORD: "123456"
      TZ: Asia/Shanghai
      # 环境自适应HikariCP配置
      SPRING_DATASOURCE_HIKARI_MAXIMUM_POOL_SIZE: $([ "$TOTAL_MEM" != "unknown" ] && [ "$TOTAL_MEM" -ge 8 ] 2>/dev/null && echo "30" || echo "15")
      SPRING_DATASOURCE_HIKARI_MINIMUM_IDLE: $([ "$TOTAL_MEM" != "unknown" ] && [ "$TOTAL_MEM" -ge 8 ] 2>/dev/null && echo "10" || echo "5")
      SPRING_DATASOURCE_HIKARI_CONNECTION_TIMEOUT: 60000
      SPRING_DATASOURCE_HIKARI_IDLE_TIMEOUT: 600000      # 10分钟空闲
      SPRING_DATASOURCE_HIKARI_MAX_LIFETIME: 3600000     # 1小时最大生命周期
      SPRING_DATASOURCE_HIKARI_KEEP_ALIVE_TIME: 60000    # 1分钟保活
      SPRING_DATASOURCE_HIKARI_VALIDATION_TIMEOUT: 5000
      SPRING_DATASOURCE_HIKARI_CONNECTION_TEST_QUERY: "SELECT 1"
      SPRING_DATASOURCE_HIKARI_LEAK_DETECTION_THRESHOLD: 30000
    ports:
      - "9998:9998"
    volumes:
      - ./logs/ljwx-boot:/app/ljwx-boot-logs
      - ./data/ljwx-boot:/app/data
      - ../backup/ljwx-boot:/backup/ljwx-boot
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - ljwx-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9998/actuator/health/db"]
      interval: 30s  # 定期检查数据源
      timeout: 10s
      retries: 5
      start_period: 120s

  ljwx-bigscreen:
    image: crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx/ljwx-bigscreen:1.2.4
    container_name: ljwx-bigscreen
    restart: unless-stopped
    env_file:
      - custom-config.env
    environment:
      MYSQL_HOST: \${MYSQL_HOST:-mysql}
      MYSQL_PORT: \${MYSQL_PORT:-3306}
      MYSQL_USER: \${MYSQL_USER:-root}
      MYSQL_PASSWORD: \${MYSQL_PASSWORD:-123456}
      MYSQL_DATABASE: \${MYSQL_DATABASE:-lj-06}
      REDIS_HOST: \${REDIS_HOST:-redis}
      REDIS_PORT: \${REDIS_PORT:-6379}
      REDIS_PASSWORD: \${REDIS_PASSWORD:-123456}
      IS_DOCKER: "true"
      APP_PORT: 8001
      TZ: Asia/Shanghai
    ports:
      - "8001:8001"
    volumes:
      - ./custom-config.py:/app/config.py:ro
      - ./custom-assets:/app/static/images:ro
      - ./logs/ljwx-bigscreen:/app/logs
      - ./data/ljwx-bigscreen:/app/data
      - ../backup/ljwx-bigscreen:/backup/ljwx-bigscreen
    depends_on:
      - mysql
      - redis
      - ljwx-boot
    networks:
      - ljwx-network

  ljwx-admin:
    image: crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx/ljwx-admin:1.2.5
    container_name: ljwx-admin
    restart: unless-stopped
    env_file:
      - custom-config.env
    environment:
      VITE_API_URL: http://ljwx-boot:9998
      VITE_BIGSCREEN_URL: \${VITE_BIGSCREEN_URL:-http://localhost:8001}
      VITE_APP_TITLE: \${VITE_APP_TITLE:-穿戴管理演示系统}
      VITE_CUSTOM_LOGO: "true"
      TZ: Asia/Shanghai
    ports:
      - "8080:80"
    volumes:
      - ./logs/ljwx-admin:/var/log/nginx
      - ./custom-logo.svg:/tmp/custom-logo.svg:ro
      - ./custom-admin-config.js:/tmp/custom-admin-config.js:ro
    depends_on:
      - ljwx-boot
      - ljwx-bigscreen
    networks:
      - ljwx-network

networks:
  ljwx-network:
    driver: bridge

EOF
    
    echo -e "${GREEN}✅ 环境适配配置已生成${NC}"
}

# 创建连接保活服务
create_keepalive_service() {
    echo -e "${BLUE}💓 创建连接保活服务...${NC}"
    
    # 根据操作系统设置日志路径
    local log_path
    case "$OS" in
        "Darwin")  # macOS
            log_path="/tmp/ljwx-mysql-keepalive.log"
            ;;
        "Linux")   # Linux
            log_path="/var/log/ljwx-mysql-keepalive.log"
            ;;
        *)
            log_path="./ljwx-mysql-keepalive.log"
            ;;
    esac
    
    cat > mysql-keepalive.sh << EOF
#!/bin/bash
# MySQL连接保活服务 - 防止长时间空置导致连接失效
# 支持跨平台运行 (macOS/Linux/CentOS)

LOG_FILE="$log_path"
MYSQL_CONTAINER="ljwx-mysql"
MYSQL_PASSWORD="\${MYSQL_PASSWORD:-123456}"

# 检测操作系统
OS=\$(uname -s)

log() {
    echo "[\$(date '+%Y-%m-%d %H:%M:%S')] \$1" | tee -a "\$LOG_FILE"
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
    local url="\$1"
    if check_curl; then
        curl -s "\$url"
    else
        wget -qO- "\$url" 2>/dev/null
    fi
}

keepalive_check() {
    # 检查MySQL连接
    if docker exec "\$MYSQL_CONTAINER" mysqladmin ping -u root -p"\$MYSQL_PASSWORD" >/dev/null 2>&1; then
        log "✅ MySQL连接正常"
        
        # 执行保活查询
        docker exec "\$MYSQL_CONTAINER" mysql -u root -p"\$MYSQL_PASSWORD" -e "SELECT 'keepalive' as status, NOW() as time;" >/dev/null 2>&1
        log "💓 保活查询已执行"
        
        # 检查连接数
        CONNECTIONS=\$(docker exec "\$MYSQL_CONTAINER" mysql -u root -p"\$MYSQL_PASSWORD" -e "SHOW STATUS LIKE 'Threads_connected';" 2>/dev/null | tail -1 | awk '{print \$2}')
        log "📊 当前连接数: \$CONNECTIONS"
        
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
case "\$OS" in
    "Darwin")  # macOS
        # macOS使用/tmp，无需创建目录
        ;;
    "Linux")   # Linux
        # 尝试创建日志目录
        sudo mkdir -p /var/log 2>/dev/null || mkdir -p \$(dirname "\$LOG_FILE")
        ;;
esac

log "🚀 启动LJWX MySQL连接保活服务 (OS: \$OS)"

# 主循环
while true; do
    keepalive_check
    sleep 300  # 每5分钟检查一次
done
EOF
    
    chmod +x mysql-keepalive.sh
    
    # 根据操作系统创建相应的服务文件
    case "$OS" in
        "Darwin")  # macOS
            # 创建launchd plist文件
            cat > com.ljwx.mysql.keepalive.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ljwx.mysql.keepalive</string>
    <key>ProgramArguments</key>
    <array>
        <string>$(pwd)/mysql-keepalive.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/ljwx-keepalive.out</string>
    <key>StandardErrorPath</key>
    <string>/tmp/ljwx-keepalive.err</string>
</dict>
</plist>
EOF
            echo -e "${GREEN}✅ macOS LaunchDaemon配置已创建${NC}"
            echo -e "${YELLOW}💡 安装服务:${NC}"
            echo -e "${YELLOW}   sudo cp com.ljwx.mysql.keepalive.plist /Library/LaunchDaemons/${NC}"
            echo -e "${YELLOW}   sudo launchctl load /Library/LaunchDaemons/com.ljwx.mysql.keepalive.plist${NC}"
            ;;
        "Linux")   # Linux
            # 创建systemd服务文件
            cat > ljwx-mysql-keepalive.service << EOF
[Unit]
Description=LJWX MySQL Connection Keepalive Service
After=docker.service
Requires=docker.service

[Service]
Type=simple
ExecStart=$(pwd)/mysql-keepalive.sh
Restart=always
RestartSec=10
User=$CURRENT_USER
WorkingDirectory=$(pwd)
Environment=PATH=/usr/local/bin:/usr/bin:/bin

[Install]
WantedBy=multi-user.target
EOF
            
            # 如果是CentOS，还创建SysV init脚本作为备用
            if [ "$DISTRO" = "centos" ] && [ "${VERSION%%.*}" -lt 7 ]; then
                cat > ljwx-mysql-keepalive.init << 'EOF'
#!/bin/bash
# ljwx-mysql-keepalive        LJWX MySQL Connection Keepalive Service
# chkconfig: 35 80 20
# description: LJWX MySQL Connection Keepalive Service

. /etc/rc.d/init.d/functions

USER="root"
DAEMON="ljwx-mysql-keepalive"
ROOT_DIR="/opt/ljwx"
SCRIPT_FILE="$ROOT_DIR/mysql-keepalive.sh"
LOCK_FILE="/var/lock/subsys/ljwx-mysql-keepalive"

start() {
    if [ -f $LOCK_FILE ]; then
        echo "$DAEMON is already running."
        exit 0
    fi
    echo -n "Starting $DAEMON: "
    runuser -l "$USER" -c "$SCRIPT_FILE" && echo_success || echo_failure
    RETVAL=$?
    echo
    [ $RETVAL -eq 0 ] && touch $LOCK_FILE
    return $RETVAL
}

stop() {
    echo -n "Shutting down $DAEMON: "
    pid=$(ps -aefw | grep "$DAEMON" | grep -v " grep " | awk '{print $2}')
    kill -9 $pid > /dev/null 2>&1
    [ $? -eq 0 ] && echo_success || echo_failure
    echo
    [ $? -eq 0 ] && rm -f $LOCK_FILE
}

restart() {
    stop
    start
}

status() {
    if [ -f $LOCK_FILE ]; then
        echo "$DAEMON is running."
    else
        echo "$DAEMON is stopped."
    fi
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    status)
        status
        ;;
    restart)
        restart
        ;;
    *)
        echo "Usage: {start|stop|status|restart}"
        exit 1
        ;;
esac

exit $?
EOF
                chmod +x ljwx-mysql-keepalive.init
                echo -e "${GREEN}✅ CentOS 6 SysV init脚本已创建${NC}"
                echo -e "${YELLOW}💡 安装服务 (CentOS 6):${NC}"
                echo -e "${YELLOW}   sudo cp ljwx-mysql-keepalive.init /etc/init.d/${NC}"
                echo -e "${YELLOW}   sudo chkconfig --add ljwx-mysql-keepalive${NC}"
                echo -e "${YELLOW}   sudo service ljwx-mysql-keepalive start${NC}"
            fi
            
            echo -e "${GREEN}✅ Linux systemd服务已创建${NC}"
            echo -e "${YELLOW}💡 安装服务 (systemd):${NC}"
            echo -e "${YELLOW}   sudo cp ljwx-mysql-keepalive.service /etc/systemd/system/${NC}"
            echo -e "${YELLOW}   sudo systemctl daemon-reload${NC}"
            echo -e "${YELLOW}   sudo systemctl enable ljwx-mysql-keepalive${NC}"
            echo -e "${YELLOW}   sudo systemctl start ljwx-mysql-keepalive${NC}"
            ;;
        *)
            echo -e "${YELLOW}⚠️  未知操作系统，仅创建了脚本文件${NC}"
            echo -e "${YELLOW}💡 手动运行: ./mysql-keepalive.sh &${NC}"
            ;;
    esac
    
    echo -e "${GREEN}✅ 连接保活服务已创建${NC}"
}

# 创建环境检测报告
create_environment_report() {
    echo -e "${BLUE}📋 生成环境检测报告...${NC}"
    
    cat > environment-report.txt << EOF
LJWX环境检测报告
生成时间: $(date)
================================

系统信息:
- 操作系统: $OS $ARCH
$([ "$OS" = "Linux" ] && [ -n "$DISTRO" ] && echo "- Linux发行版: $DISTRO $VERSION")
- Docker版本: $DOCKER_VERSION
- 当前用户: $CURRENT_USER ($USER_ID:$GROUP_ID)

硬件资源:
- CPU核心: $CPU_CORES
- 总内存: ${TOTAL_MEM}GB
- 可用内存: ${AVAILABLE_MEM}GB
- 存储类型: $DISK_TYPE

网络环境:
- 网络状态: $NETWORK_STATUS

平台特性:
$([ "$OS" = "Darwin" ] && echo "- macOS环境: 使用LaunchDaemon服务管理")
$([ "$OS" = "Linux" ] && echo "- Linux环境: 使用systemd服务管理")
$([ "$DISTRO" = "centos" ] && echo "- CentOS优化: DNS解析跳过，SysV init备用")

风险评估:
$([ "$TOTAL_MEM" != "unknown" ] && [ "$TOTAL_MEM" -lt 4 ] 2>/dev/null && echo "⚠️ 内存不足，可能影响数据库性能")
$([ "$DISK_TYPE" = "HDD" ] && echo "⚠️ 使用传统硬盘，建议SSD优化")
$([ "$NETWORK_STATUS" = "offline/restricted" ] && echo "⚠️ 网络受限，可能影响镜像拉取")
$([ "$OS" = "Darwin" ] && echo "⚠️ macOS环境：Docker性能可能不如Linux")

建议配置:
EOF
    
    # 生成建议配置（避免复杂的嵌套判断）
    local mysql_buffer_pool="512MB"
    local max_connections="200"
    
    if [ "$TOTAL_MEM" != "unknown" ] && [ "$TOTAL_MEM" -ge 16 ] 2>/dev/null; then
        mysql_buffer_pool="4GB"
        max_connections="500"
    elif [ "$TOTAL_MEM" != "unknown" ] && [ "$TOTAL_MEM" -ge 8 ] 2>/dev/null; then
        mysql_buffer_pool="2GB"
        max_connections="300"
    fi
    
    cat >> environment-report.txt << EOF
- MySQL缓冲池: $mysql_buffer_pool
- 最大连接数: $max_connections
- 健康检查间隔: 10秒（激进模式）
- 连接保活间隔: 5分钟

生成的文件:
- docker-compose-adaptive.yml (环境适配配置)
- mysql-keepalive.sh (跨平台连接保活服务)
$([ "$OS" = "Darwin" ] && echo "- com.ljwx.mysql.keepalive.plist (macOS LaunchDaemon)")
$([ "$OS" = "Linux" ] && echo "- ljwx-mysql-keepalive.service (Linux systemd服务)")
$([ "$DISTRO" = "centos" ] && [ "${VERSION%%.*}" -lt 7 ] 2>/dev/null && echo "- ljwx-mysql-keepalive.init (CentOS 6 SysV init)")

跨平台支持:
✅ macOS (Darwin) - 使用sysctl获取系统信息，diskutil检测存储
✅ Linux (Ubuntu/Debian) - 使用free/lsblk获取系统信息
✅ CentOS/RHEL - 特殊优化配置，支持旧版本SysV init
✅ 自动检测并适配Docker Compose版本 (v1/v2)
✅ 自动检测HTTP工具 (curl/wget)
EOF
    
    echo -e "${GREEN}✅ 环境报告已生成: environment-report.txt${NC}"
}

# 权限修复
fix_permissions() {
    echo -e "${BLUE}🔧 修复数据目录权限...${NC}"
    
    # 创建数据目录
    mkdir -p data/{mysql,redis,ljwx-boot,ljwx-bigscreen}
    mkdir -p logs/{mysql,redis,ljwx-boot,ljwx-bigscreen,ljwx-admin}
    
    # 设置权限为当前用户
    chown -R $USER_ID:$GROUP_ID data/ 2>/dev/null || {
        echo -e "${YELLOW}⚠️  无法设置权限，将使用Docker用户映射${NC}"
    }
    
    echo -e "${GREEN}✅ 权限修复完成${NC}"
}

# 主执行流程
main() {
    detect_environment
    generate_adaptive_config
    create_keepalive_service
    create_environment_report
    fix_permissions
    
    echo ""
    echo -e "${GREEN}🎉 跨平台环境自适应修复完成！${NC}"
    echo "=================================="
    echo -e "${YELLOW}📋 下一步操作:${NC}"
    echo "  1. 检查环境报告: cat environment-report.txt"
    echo "  2. 使用适配配置: docker-compose -f docker-compose-adaptive.yml up -d"
    echo "  3. 启动保活服务: ./mysql-keepalive.sh &"
    
    case "$OS" in
        "Darwin")  # macOS
            echo "  4. 安装macOS服务:"
            echo "     sudo cp com.ljwx.mysql.keepalive.plist /Library/LaunchDaemons/"
            echo "     sudo launchctl load /Library/LaunchDaemons/com.ljwx.mysql.keepalive.plist"
            ;;
        "Linux")   # Linux
            echo "  4. 安装Linux服务:"
            echo "     sudo cp ljwx-mysql-keepalive.service /etc/systemd/system/"
            echo "     sudo systemctl daemon-reload && sudo systemctl enable ljwx-mysql-keepalive"
            if [ "$DISTRO" = "centos" ] && [ "${VERSION%%.*}" -lt 7 ] 2>/dev/null; then
                echo "     (CentOS 6备用): sudo cp ljwx-mysql-keepalive.init /etc/init.d/"
            fi
            ;;
        *)
            echo "  4. 手动运行保活服务: ./mysql-keepalive.sh &"
            ;;
    esac
    
    echo ""
    echo -e "${BLUE}🌍 跨平台支持: macOS ✅ | Linux ✅ | CentOS ✅${NC}"
    echo -e "${BLUE}💡 这个解决方案专门针对环境差异问题，支持多平台，应该能彻底解决客户环境的连接问题${NC}"
}

# 执行主函数
main 

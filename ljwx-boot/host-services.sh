#!/bin/bash
# 宿主机服务管理脚本 - 管理MySQL和Redis服务

set -e

ACTION=${1:-"help"} #默认显示帮助
CONFIG_FILE=${2:-"host-config.env"} #宿主机配置文件

echo "==================== 宿主机服务管理 ===================="

# 显示帮助信息
show_help() {
    echo "用法: $0 [命令] [配置文件]"
    echo ""
    echo "命令:"
    echo "  check     检查MySQL和Redis服务状态"
    echo "  start     启动MySQL和Redis服务"
    echo "  stop      停止MySQL和Redis服务"
    echo "  restart   重启MySQL和Redis服务"
    echo "  status    显示服务详细状态"
    echo "  install   安装MySQL和Redis服务"
    echo "  config    配置MySQL和Redis服务"
    echo "  test      测试服务连接"
    echo ""
    echo "配置文件: ${CONFIG_FILE} (可选)"
    echo ""
    echo "支持的操作系统:"
    echo "  - Ubuntu/Debian (systemctl/service)"
    echo "  - CentOS/RHEL (systemctl/service)"
    echo "  - macOS (brew services)"
}

# 检测操作系统
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        echo "检测到操作系统: macOS"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v systemctl > /dev/null 2>&1; then
            OS="linux-systemd"
            echo "检测到操作系统: Linux (systemd)"
        else
            OS="linux-sysv"
            echo "检测到操作系统: Linux (SysV)"
        fi
    else
        OS="unknown"
        echo "⚠️  未知操作系统: $OSTYPE"
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

# 检查MySQL服务状态
check_mysql() {
    echo -n "MySQL服务状态: "
    case $OS in
        "macos")
            if brew services list | grep mysql | grep started > /dev/null; then
                echo "✅ 运行中"
                return 0
            else
                echo "❌ 未运行"
                return 1
            fi
            ;;
        "linux-systemd")
            if systemctl is-active mysql > /dev/null 2>&1 || systemctl is-active mysqld > /dev/null 2>&1; then
                echo "✅ 运行中"
                return 0
            else
                echo "❌ 未运行"
                return 1
            fi
            ;;
        "linux-sysv")
            if service mysql status > /dev/null 2>&1 || service mysqld status > /dev/null 2>&1; then
                echo "✅ 运行中"
                return 0
            else
                echo "❌ 未运行"
                return 1
            fi
            ;;
        *)
            echo "❓ 无法检测"
            return 1
            ;;
    esac
}

# 检查Redis服务状态
check_redis() {
    echo -n "Redis服务状态: "
    case $OS in
        "macos")
            if brew services list | grep redis | grep started > /dev/null; then
                echo "✅ 运行中"
                return 0
            else
                echo "❌ 未运行"
                return 1
            fi
            ;;
        "linux-systemd")
            if systemctl is-active redis > /dev/null 2>&1 || systemctl is-active redis-server > /dev/null 2>&1; then
                echo "✅ 运行中"
                return 0
            else
                echo "❌ 未运行"
                return 1
            fi
            ;;
        "linux-sysv")
            if service redis status > /dev/null 2>&1 || service redis-server status > /dev/null 2>&1; then
                echo "✅ 运行中"
                return 0
            else
                echo "❌ 未运行"
                return 1
            fi
            ;;
        *)
            echo "❓ 无法检测"
            return 1
            ;;
    esac
}

# 启动MySQL服务
start_mysql() {
    echo "启动MySQL服务..."
    case $OS in
        "macos")
            brew services start mysql
            ;;
        "linux-systemd")
            if systemctl list-unit-files | grep mysql.service > /dev/null; then
                sudo systemctl start mysql
            else
                sudo systemctl start mysqld
            fi
            ;;
        "linux-sysv")
            if [ -f /etc/init.d/mysql ]; then
                sudo service mysql start
            else
                sudo service mysqld start
            fi
            ;;
        *)
            echo "❌ 不支持的操作系统"
            return 1
            ;;
    esac
}

# 启动Redis服务
start_redis() {
    echo "启动Redis服务..."
    case $OS in
        "macos")
            brew services start redis
            ;;
        "linux-systemd")
            if systemctl list-unit-files | grep redis.service > /dev/null; then
                sudo systemctl start redis
            else
                sudo systemctl start redis-server
            fi
            ;;
        "linux-sysv")
            if [ -f /etc/init.d/redis ]; then
                sudo service redis start
            else
                sudo service redis-server start
            fi
            ;;
        *)
            echo "❌ 不支持的操作系统"
            return 1
            ;;
    esac
}

# 停止MySQL服务
stop_mysql() {
    echo "停止MySQL服务..."
    case $OS in
        "macos")
            brew services stop mysql
            ;;
        "linux-systemd")
            if systemctl list-unit-files | grep mysql.service > /dev/null; then
                sudo systemctl stop mysql
            else
                sudo systemctl stop mysqld
            fi
            ;;
        "linux-sysv")
            if [ -f /etc/init.d/mysql ]; then
                sudo service mysql stop
            else
                sudo service mysqld stop
            fi
            ;;
        *)
            echo "❌ 不支持的操作系统"
            return 1
            ;;
    esac
}

# 停止Redis服务
stop_redis() {
    echo "停止Redis服务..."
    case $OS in
        "macos")
            brew services stop redis
            ;;
        "linux-systemd")
            if systemctl list-unit-files | grep redis.service > /dev/null; then
                sudo systemctl stop redis
            else
                sudo systemctl stop redis-server
            fi
            ;;
        "linux-sysv")
            if [ -f /etc/init.d/redis ]; then
                sudo service redis stop
            else
                sudo service redis-server stop
            fi
            ;;
        *)
            echo "❌ 不支持的操作系统"
            return 1
            ;;
    esac
}

# 测试服务连接
test_connections() {
    echo "==================== 连接测试 ===================="
    
    # 测试MySQL连接
    echo -n "测试MySQL连接..."
    if command -v mysql > /dev/null 2>&1; then
        if mysql -h${MYSQL_HOST:-localhost} -P${MYSQL_PORT:-3306} -u${MYSQL_USER:-root} -p${MYSQL_PASSWORD:-123456} -e "SELECT 'MySQL连接成功' as status;" 2>/dev/null; then
            echo " ✅ 连接成功"
        else
            echo " ❌ 连接失败"
            echo "   配置: ${MYSQL_USER:-root}@${MYSQL_HOST:-localhost}:${MYSQL_PORT:-3306}"
        fi
    else
        echo " ⚠️  MySQL客户端未安装"
    fi
    
    # 测试Redis连接
    echo -n "测试Redis连接..."
    if command -v redis-cli > /dev/null 2>&1; then
        if [ -z "${REDIS_PASSWORD}" ]; then
            REDIS_CMD="redis-cli -h ${REDIS_HOST:-localhost} -p ${REDIS_PORT:-6379} ping"
        else
            REDIS_CMD="redis-cli -h ${REDIS_HOST:-localhost} -p ${REDIS_PORT:-6379} -a ${REDIS_PASSWORD} ping"
        fi
        
        if $REDIS_CMD 2>/dev/null | grep PONG > /dev/null; then
            echo " ✅ 连接成功"
        else
            echo " ❌ 连接失败"
            echo "   配置: ${REDIS_HOST:-localhost}:${REDIS_PORT:-6379}"
        fi
    else
        echo " ⚠️  Redis客户端未安装"
    fi
}

# 安装服务
install_services() {
    echo "==================== 安装服务 ===================="
    
    case $OS in
        "macos")
            echo "在macOS上使用Homebrew安装服务..."
            if ! command -v brew > /dev/null 2>&1; then
                echo "❌ Homebrew未安装，请先安装Homebrew"
                echo "安装命令: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
                return 1
            fi
            
            echo "安装MySQL..."
            brew install mysql
            echo "安装Redis..."
            brew install redis
            ;;
        "linux-systemd")
            echo "在Linux上安装服务..."
            if command -v apt-get > /dev/null 2>&1; then
                # Ubuntu/Debian
                echo "使用apt安装..."
                sudo apt-get update
                sudo apt-get install -y mysql-server redis-server
            elif command -v yum > /dev/null 2>&1; then
                # CentOS/RHEL
                echo "使用yum安装..."
                sudo yum install -y mysql-server redis
            elif command -v dnf > /dev/null 2>&1; then
                # Fedora
                echo "使用dnf安装..."
                sudo dnf install -y mysql-server redis
            else
                echo "❌ 不支持的包管理器"
                return 1
            fi
            ;;
        *)
            echo "❌ 不支持的操作系统"
            return 1
            ;;
    esac
    
    echo "✅ 服务安装完成"
}

# 主逻辑
main() {
    detect_os
    load_config
    
    case $ACTION in
        "check")
            check_mysql
            check_redis
            ;;
        "start")
            start_mysql
            start_redis
            sleep 3
            check_mysql
            check_redis
            ;;
        "stop")
            stop_mysql
            stop_redis
            ;;
        "restart")
            stop_mysql
            stop_redis
            sleep 2
            start_mysql
            start_redis
            sleep 3
            check_mysql
            check_redis
            ;;
        "status")
            check_mysql
            check_redis
            echo ""
            echo "详细状态信息:"
            case $OS in
                "macos")
                    brew services list | grep -E "(mysql|redis)"
                    ;;
                "linux-systemd")
                    systemctl status mysql mysqld redis redis-server 2>/dev/null | grep -E "(Active|Main PID)"
                    ;;
            esac
            ;;
        "install")
            install_services
            ;;
        "config")
            echo "==================== 服务配置建议 ===================="
            echo "MySQL配置文件位置:"
            case $OS in
                "macos")
                    echo "  /usr/local/etc/my.cnf (Homebrew)"
                    ;;
                "linux-systemd")
                    echo "  /etc/mysql/mysql.conf.d/mysqld.cnf (Ubuntu/Debian)"
                    echo "  /etc/my.cnf (CentOS/RHEL)"
                    ;;
            esac
            echo ""
            echo "Redis配置文件位置:"
            case $OS in
                "macos")
                    echo "  /usr/local/etc/redis.conf (Homebrew)"
                    ;;
                "linux-systemd")
                    echo "  /etc/redis/redis.conf"
                    ;;
            esac
            ;;
        "test")
            test_connections
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# 执行主逻辑
main 
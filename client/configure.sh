#!/bin/bash
# LJWX 快速配置脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 LJWX 系统配置向导${NC}"
echo ""

# 获取服务器IP
get_server_ip() {
    local ip
    ip=$(hostname -I | awk '{print $1}')
    if [ -z "$ip" ]; then
        ip=$(curl -s ipinfo.io/ip 2>/dev/null || echo "localhost")
    fi
    echo "$ip"
}

# 检查端口是否被占用
check_port() {
    local port=$1
    if netstat -tlnp 2>/dev/null | grep -q ":${port} "; then
        return 1
    fi
    return 0
}

# 配置端口
configure_ports() {
    echo -e "${YELLOW}📡 配置服务端口${NC}"
    
    # 管理后台端口
    while true; do
        read -p "请输入管理后台端口 [默认: 80]: " admin_port
        admin_port=${admin_port:-80}
        
        if check_port "$admin_port"; then
            break
        else
            echo -e "${RED}端口 ${admin_port} 已被占用，请选择其他端口${NC}"
        fi
    done
    
    # 大屏系统端口
    while true; do
        read -p "请输入大屏系统端口 [默认: 5000]: " bigscreen_port
        bigscreen_port=${bigscreen_port:-5000}
        
        if check_port "$bigscreen_port"; then
            break
        else
            echo -e "${RED}端口 ${bigscreen_port} 已被占用，请选择其他端口${NC}"
        fi
    done
    
    # 后端API端口
    while true; do
        read -p "请输入后端API端口 [默认: 9998]: " boot_port
        boot_port=${boot_port:-9998}
        
        if check_port "$boot_port"; then
            break
        else
            echo -e "${RED}端口 ${boot_port} 已被占用，请选择其他端口${NC}"
        fi
    done
    
    # MySQL端口
    while true; do
        read -p "请输入MySQL端口 [默认: 3306]: " mysql_port
        mysql_port=${mysql_port:-3306}
        
        if check_port "$mysql_port"; then
            break
        else
            echo -e "${RED}端口 ${mysql_port} 已被占用，请选择其他端口${NC}"
        fi
    done
    
    # Redis端口
    while true; do
        read -p "请输入Redis端口 [默认: 6379]: " redis_port
        redis_port=${redis_port:-6379}
        
        if check_port "$redis_port"; then
            break
        else
            echo -e "${RED}端口 ${redis_port} 已被占用，请选择其他端口${NC}"
        fi
    done
}

# 配置数据库
configure_database() {
    echo ""
    echo -e "${YELLOW}🗄️  配置数据库${NC}"
    
    read -p "请输入MySQL root密码 [默认: 123456]: " mysql_root_password
    mysql_root_password=${mysql_root_password:-123456}
    
    read -p "请输入数据库名称 [默认: test]: " mysql_database
    mysql_database=${mysql_database:-test}
    
    read -p "请输入应用数据库用户名 [默认: ljwx]: " mysql_user
    mysql_user=${mysql_user:-ljwx}
    
    read -p "请输入应用数据库密码 [默认: 123456]: " mysql_password
    mysql_password=${mysql_password:-123456}
}

# 配置镜像源
configure_registry() {
    echo ""
    echo -e "${YELLOW}🐳 配置镜像源${NC}"
    echo "1) 阿里云镜像仓库 (默认)"
    echo "2) Docker Hub"
    echo "3) 自定义镜像仓库"
    
    read -p "请选择镜像源 [1]: " registry_choice
    registry_choice=${registry_choice:-1}
    
    case $registry_choice in
        1)
            registry="crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx"
            ;;
        2)
            registry="ljwx"
            ;;
        3)
            read -p "请输入自定义镜像仓库地址: " registry
            ;;
        *)
            registry="crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx"
            ;;
    esac
}

# 生成配置文件
generate_env() {
    echo ""
    echo -e "${YELLOW}📝 生成配置文件${NC}"
    
    cat > .env << EOF
# LJWX 系统配置
LJWX_VERSION=2.0.1
REGISTRY=${registry}

# 数据库配置
MYSQL_ROOT_PASSWORD=${mysql_root_password}
MYSQL_DATABASE=${mysql_database}
MYSQL_USER=${mysql_user}
MYSQL_PASSWORD=${mysql_password}

# 服务端口配置
LJWX_BOOT_PORT=${boot_port}
LJWX_BIGSCREEN_PORT=${bigscreen_port}
LJWX_ADMIN_PORT=${admin_port}
MYSQL_PORT=${mysql_port}
REDIS_PORT=${redis_port}

# 时区配置
TZ=Asia/Shanghai

# 日志配置
LOG_LEVEL=INFO

# 配置生成时间
GENERATED_AT=$(date '+%Y-%m-%d %H:%M:%S')
CONFIGURED_BY=configure.sh
EOF
}

# 显示配置摘要
show_summary() {
    local server_ip
    server_ip=$(get_server_ip)
    
    echo ""
    echo -e "${GREEN}✅ 配置完成！${NC}"
    echo ""
    echo -e "${BLUE}📋 配置摘要:${NC}"
    echo -e "  服务器IP: ${GREEN}${server_ip}${NC}"
    echo -e "  管理后台: ${GREEN}http://${server_ip}:${admin_port}${NC}"
    echo -e "  大屏系统: ${GREEN}http://${server_ip}:${bigscreen_port}${NC}"
    echo -e "  后端API: ${GREEN}http://${server_ip}:${boot_port}${NC}"
    echo -e "  MySQL: ${GREEN}${server_ip}:${mysql_port}${NC}"
    echo -e "  Redis: ${GREEN}${server_ip}:${redis_port}${NC}"
    echo ""
    echo -e "${BLUE}🗄️  数据库配置:${NC}"
    echo -e "  数据库名: ${GREEN}${mysql_database}${NC}"
    echo -e "  用户名: ${GREEN}${mysql_user}${NC}"
    echo -e "  密码: ${GREEN}${mysql_password}${NC}"
    echo ""
    echo -e "${BLUE}🐳 镜像源:${NC}"
    echo -e "  ${GREEN}${registry}${NC}"
    echo ""
    echo -e "${YELLOW}📝 配置已保存到 .env 文件${NC}"
    echo -e "${YELLOW}🚀 现在可以运行 './start.sh' 启动系统${NC}"
}

# 交互式确认
confirm_config() {
    echo ""
    echo -e "${YELLOW}确认以上配置？${NC}"
    read -p "(yes/no) [yes]: " confirm
    confirm=${confirm:-yes}
    
    if [ "$confirm" != "yes" ] && [ "$confirm" != "y" ]; then
        echo -e "${BLUE}配置已取消${NC}"
        exit 0
    fi
}

# 主程序
main() {
    configure_ports
    configure_database
    configure_registry
    confirm_config
    generate_env
    show_summary
}

# 执行主程序
main "$@"
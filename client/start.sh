#!/bin/bash
# LJWX 灵境万象健康管理系统 - 客户服务器一键启动脚本
# 版本: 2.0.1
# 更新时间: 2025-09-06

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 版本信息
LJWX_VERSION="2.0.1"
REGISTRY="crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx"

echo -e "${BLUE}🏥 LJWX 灵境万象健康管理系统 v${LJWX_VERSION}${NC}"
echo -e "${BLUE}🚀 客户服务器一键启动脚本${NC}"
echo ""

# 检查 Docker 环境
check_docker() {
    echo -e "${YELLOW}📋 检查 Docker 环境...${NC}"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker 未安装，请先安装 Docker${NC}"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        echo -e "${RED}❌ Docker 服务未启动，请启动 Docker 服务${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${RED}❌ Docker Compose 未安装，请先安装 Docker Compose${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Docker 环境检查通过${NC}"
}

# 创建必要目录
create_directories() {
    echo -e "${YELLOW}📁 创建数据目录...${NC}"
    
    mkdir -p data/mysql
    mkdir -p data/redis
    mkdir -p logs/ljwx-boot
    mkdir -p logs/ljwx-bigscreen
    mkdir -p logs/nginx
    mkdir -p config/mysql
    mkdir -p config/redis
    mkdir -p backups
    
    echo -e "${GREEN}✅ 目录创建完成${NC}"
}

# 生成配置文件
generate_config() {
    echo -e "${YELLOW}⚙️  生成配置文件...${NC}"
    
    # 生成 MySQL 配置
    cat > config/mysql/my.cnf << 'EOF'
[mysqld]
default_authentication_plugin=mysql_native_password
sql_mode=STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO
character-set-server=utf8mb4
collation-server=utf8mb4_unicode_ci
max_connections=200
innodb_buffer_pool_size=256M
EOF

    # 生成 Redis 配置
    cat > config/redis/redis.conf << 'EOF'
bind 0.0.0.0
port 6379
timeout 300
databases 16
save 900 1
save 300 10
save 60 10000
maxmemory 256mb
maxmemory-policy allkeys-lru
appendonly yes
EOF

    # 生成环境变量配置
    if [ ! -f .env ]; then
        cat > .env << EOF
# LJWX 系统配置
LJWX_VERSION=${LJWX_VERSION}
REGISTRY=${REGISTRY}

# 数据库配置
MYSQL_ROOT_PASSWORD=123456
MYSQL_DATABASE=test
MYSQL_USER=ljwx
MYSQL_PASSWORD=123456

# 服务端口配置
LJWX_BOOT_PORT=9998
LJWX_BIGSCREEN_PORT=5000
LJWX_ADMIN_PORT=80
MYSQL_PORT=3306
REDIS_PORT=6379

# 时区配置
TZ=Asia/Shanghai

# 日志配置
LOG_LEVEL=INFO
EOF
    fi
    
    echo -e "${GREEN}✅ 配置文件生成完成${NC}"
}

# 生成 Docker Compose 文件
generate_compose() {
    echo -e "${YELLOW}🐳 生成 Docker Compose 配置...${NC}"
    
    cat > docker-compose.yml << EOF
version: '3.8'

services:
  ljwx-mysql:
    image: \${REGISTRY}/ljwx-mysql:\${LJWX_VERSION}
    container_name: ljwx-mysql
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: \${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: \${MYSQL_DATABASE}
      MYSQL_USER: \${MYSQL_USER}
      MYSQL_PASSWORD: \${MYSQL_PASSWORD}
      TZ: \${TZ}
    ports:
      - "\${MYSQL_PORT}:3306"
    volumes:
      - ./data/mysql:/var/lib/mysql
      - ./config/mysql/my.cnf:/etc/mysql/conf.d/custom.cnf
      - ./logs/mysql:/var/log/mysql
    networks:
      - ljwx-network
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-p\${MYSQL_ROOT_PASSWORD}"]
      timeout: 20s
      retries: 10

  ljwx-redis:
    image: \${REGISTRY}/ljwx-redis:\${LJWX_VERSION}
    container_name: ljwx-redis
    restart: unless-stopped
    environment:
      TZ: \${TZ}
    ports:
      - "\${REDIS_PORT}:6379"
    volumes:
      - ./data/redis:/data
      - ./config/redis/redis.conf:/usr/local/etc/redis/redis.conf
    networks:
      - ljwx-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      timeout: 5s
      retries: 5

  ljwx-boot:
    image: \${REGISTRY}/ljwx-boot:\${LJWX_VERSION}
    container_name: ljwx-boot
    restart: unless-stopped
    environment:
      TZ: \${TZ}
      SPRING_PROFILES_ACTIVE: prod
      SPRING_DATASOURCE_URL: jdbc:mysql://ljwx-mysql:3306/\${MYSQL_DATABASE}?useUnicode=true&characterEncoding=utf8&serverTimezone=Asia/Shanghai&useSSL=false&allowPublicKeyRetrieval=true
      SPRING_DATASOURCE_USERNAME: \${MYSQL_USER}
      SPRING_DATASOURCE_PASSWORD: \${MYSQL_PASSWORD}
      SPRING_DATASOURCE_DRIVER_CLASS_NAME: com.mysql.cj.jdbc.Driver
      SPRING_REDIS_HOST: ljwx-redis
      SPRING_REDIS_PORT: 6379
      SPRING_REDIS_DATABASE: 0
      SPRING_DATA_REDIS_HOST: ljwx-redis
      SPRING_DATA_REDIS_PORT: 6379
      REDIS_HOST: ljwx-redis
      REDIS_PORT: 6379
    ports:
      - "\${LJWX_BOOT_PORT}:9998"
    volumes:
      - ./logs/ljwx-boot:/app/logs
    depends_on:
      - ljwx-mysql
      - ljwx-redis
    networks:
      - ljwx-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9998/actuator/health"]
      timeout: 30s
      retries: 10
      interval: 30s
      start_period: 60s

  ljwx-bigscreen:
    image: \${REGISTRY}/ljwx-bigscreen:\${LJWX_VERSION}
    container_name: ljwx-bigscreen
    restart: unless-stopped
    environment:
      TZ: \${TZ}
      MYSQL_HOST: ljwx-mysql
      MYSQL_PORT: 3306
      MYSQL_DATABASE: \${MYSQL_DATABASE}
      MYSQL_USER: \${MYSQL_USER}
      MYSQL_PASSWORD: \${MYSQL_PASSWORD}
      REDIS_HOST: ljwx-redis
      REDIS_PORT: 6379
      BOOT_API_URL: http://ljwx-boot:9998
    ports:
      - "\${LJWX_BIGSCREEN_PORT}:5000"
    volumes:
      - ./logs/ljwx-bigscreen:/app/logs
    depends_on:
      - ljwx-mysql
      - ljwx-redis
      - ljwx-boot
    networks:
      - ljwx-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      timeout: 10s
      retries: 5

  ljwx-admin:
    image: \${REGISTRY}/ljwx-admin:\${LJWX_VERSION}
    container_name: ljwx-admin
    restart: unless-stopped
    environment:
      TZ: \${TZ}
      BACKEND_URL: http://ljwx-boot:9998
      BIGSCREEN_URL: http://ljwx-bigscreen:5000
    ports:
      - "\${LJWX_ADMIN_PORT}:80"
    volumes:
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - ljwx-boot
      - ljwx-bigscreen
    networks:
      - ljwx-network
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:80/health"]
      timeout: 10s
      retries: 3

networks:
  ljwx-network:
    driver: bridge
    ipam:
      driver: default
      config:
        - subnet: 172.20.0.0/16

volumes:
  mysql_data:
  redis_data:
EOF

    echo -e "${GREEN}✅ Docker Compose 配置生成完成${NC}"
}

# 检查镜像是否存在
check_image_exists() {
    local image=$1
    docker image inspect "$image" > /dev/null 2>&1
}

# 拉取镜像
pull_images() {
    echo -e "${YELLOW}📥 检查和拉取系统镜像...${NC}"
    
    local images=(
        "${REGISTRY}/ljwx-mysql:${LJWX_VERSION}"
        "${REGISTRY}/ljwx-redis:${LJWX_VERSION}"
        "${REGISTRY}/ljwx-boot:${LJWX_VERSION}"
        "${REGISTRY}/ljwx-bigscreen:${LJWX_VERSION}"
        "${REGISTRY}/ljwx-admin:${LJWX_VERSION}"
    )
    
    local missing_images=()
    local local_images=()
    
    # 首先检查哪些镜像缺失
    for image in "${images[@]}"; do
        if check_image_exists "$image"; then
            echo -e "${GREEN}  ✅ 本地已存在: ${image}${NC}"
            local_images+=("$image")
        else
            missing_images+=("$image")
        fi
    done
    
    # 如果有缺失的镜像，尝试拉取
    if [ ${#missing_images[@]} -gt 0 ]; then
        echo -e "${YELLOW}  需要拉取 ${#missing_images[@]} 个镜像...${NC}"
        
        for image in "${missing_images[@]}"; do
            echo -e "${BLUE}  正在拉取: ${image}${NC}"
            if docker pull "$image"; then
                echo -e "${GREEN}  ✅ 拉取成功: ${image}${NC}"
            else
                echo -e "${RED}  ❌ 拉取失败: ${image}${NC}"
                
                # 检查是否有相同名称但不同标签的本地镜像
                local base_image="${image%:*}"
                local available_tags
                available_tags=$(docker images --format "{{.Tag}}" "$base_image" 2>/dev/null | head -5)
                
                if [ -n "$available_tags" ]; then
                    echo -e "${YELLOW}  💡 发现本地可用标签: ${available_tags}${NC}"
                    echo -e "${YELLOW}  建议: 检查版本配置或使用本地标签${NC}"
                else
                    echo -e "${YELLOW}  💡 建议解决方案:${NC}"
                    echo -e "${YELLOW}     1. 检查网络连接和镜像仓库访问权限${NC}"
                    echo -e "${YELLOW}     2. 确认镜像是否已推送到仓库${NC}"
                    echo -e "${YELLOW}     3. 使用本地构建的镜像（如果有）${NC}"
                fi
                
                # 询问是否继续
                read -p "镜像拉取失败，是否继续启动？(y/N): " continue_anyway
                if [ "$continue_anyway" != "y" ] && [ "$continue_anyway" != "Y" ]; then
                    exit 1
                fi
            fi
        done
    fi
    
    echo -e "${GREEN}✅ 镜像检查完成${NC}"
}

# 清理已存在的容器
cleanup_existing_containers() {
    echo -e "${YELLOW}🧹 清理可能冲突的容器...${NC}"
    
    local containers=("ljwx-mysql" "ljwx-redis" "ljwx-boot" "ljwx-bigscreen" "ljwx-admin")
    local found_containers=false
    
    for container in "${containers[@]}"; do
        if docker ps -a --format "{{.Names}}" | grep -q "^${container}$"; then
            echo -e "${YELLOW}  发现已存在的容器: ${container}${NC}"
            found_containers=true
        fi
    done
    
    if [ "$found_containers" = true ]; then
        echo -e "${BLUE}  停止并删除已存在的容器...${NC}"
        docker stop "${containers[@]}" 2>/dev/null || true
        docker rm "${containers[@]}" 2>/dev/null || true
        echo -e "${GREEN}  ✅ 清理完成${NC}"
    else
        echo -e "${GREEN}  ✅ 无冲突容器${NC}"
    fi
}

# 启动服务
start_services() {
    echo -e "${YELLOW}🚀 启动 LJWX 系统服务...${NC}"
    
    # 清理可能冲突的容器
    cleanup_existing_containers
    
    # 使用 docker compose 或 docker-compose
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
    fi
    
    echo -e "${BLUE}  正在启动服务，请耐心等待...${NC}"
    
    # 删除可能存在的旧网络
    docker network rm client_ljwx-network 2>/dev/null || true
    
    if $COMPOSE_CMD up -d; then
        echo -e "${GREEN}✅ 服务启动成功${NC}"
    else
        echo -e "${RED}❌ 服务启动失败${NC}"
        echo -e "${YELLOW}📋 检查详细错误信息:${NC}"
        $COMPOSE_CMD logs --tail=10
        exit 1
    fi
}

# 等待服务就绪
wait_for_services() {
    echo -e "${YELLOW}⏳ 等待服务就绪...${NC}"
    
    local max_attempts=60
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -f -s http://localhost:9998/actuator/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ 服务已就绪${NC}"
            return 0
        fi
        
        attempt=$((attempt + 1))
        echo -e "${BLUE}  等待中... (${attempt}/${max_attempts})${NC}"
        sleep 5
    done
    
    echo -e "${YELLOW}⚠️  服务启动可能需要更多时间，请稍后手动检查${NC}"
}

# 显示服务状态
show_status() {
    echo ""
    echo -e "${BLUE}📊 服务状态:${NC}"
    
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
    fi
    
    $COMPOSE_CMD ps
}

# 显示访问信息
show_access_info() {
    local server_ip=$(hostname -I | awk '{print $1}')
    
    echo ""
    echo -e "${GREEN}🎉 LJWX 系统启动完成！${NC}"
    echo ""
    echo -e "${BLUE}📱 访问地址:${NC}"
    echo -e "  管理后台: ${GREEN}http://${server_ip}:${LJWX_ADMIN_PORT}${NC}"
    echo -e "  大屏系统: ${GREEN}http://${server_ip}:${LJWX_BIGSCREEN_PORT}${NC}"
    echo -e "  后端API: ${GREEN}http://${server_ip}:${LJWX_BOOT_PORT}${NC}"
    echo ""
    echo -e "${BLUE}🔧 管理命令:${NC}"
    echo -e "  查看状态: ${YELLOW}./start.sh status${NC}"
    echo -e "  停止服务: ${YELLOW}./start.sh stop${NC}"
    echo -e "  重启服务: ${YELLOW}./start.sh restart${NC}"
    echo -e "  查看日志: ${YELLOW}./start.sh logs${NC}"
    echo -e "  清理系统: ${YELLOW}./start.sh clean${NC}"
    echo ""
    echo -e "${BLUE}📋 默认账户:${NC}"
    echo -e "  用户名: ${GREEN}admin${NC}"
    echo -e "  密码: ${GREEN}admin123${NC}"
}

# 停止服务
stop_services() {
    echo -e "${YELLOW}🛑 停止 LJWX 系统服务...${NC}"
    
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
    fi
    
    $COMPOSE_CMD down
    echo -e "${GREEN}✅ 服务已停止${NC}"
}

# 重启服务
restart_services() {
    echo -e "${YELLOW}🔄 重启 LJWX 系统服务...${NC}"
    
    stop_services
    sleep 2
    start_services
    wait_for_services
    show_status
    show_access_info
}

# 查看日志
show_logs() {
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
    fi
    
    if [ -n "$2" ]; then
        $COMPOSE_CMD logs -f "$2"
    else
        $COMPOSE_CMD logs -f
    fi
}

# 清理系统
clean_system() {
    echo -e "${YELLOW}🧹 清理 LJWX 系统...${NC}"
    read -p "⚠️  这将删除所有容器、镜像和数据，确认继续？(yes/no): " confirm
    
    if [ "$confirm" = "yes" ]; then
        if docker compose version &> /dev/null; then
            COMPOSE_CMD="docker compose"
        else
            COMPOSE_CMD="docker-compose"
        fi
        
        $COMPOSE_CMD down -v --rmi all
        
        # 清理数据目录
        read -p "是否同时删除本地数据？(yes/no): " clean_data
        if [ "$clean_data" = "yes" ]; then
            rm -rf data/ logs/
            echo -e "${GREEN}✅ 本地数据已清理${NC}"
        fi
        
        echo -e "${GREEN}✅ 系统清理完成${NC}"
    else
        echo -e "${BLUE}取消清理操作${NC}"
    fi
}

# 主程序
main() {
    case "${1:-start}" in
        "start")
            check_docker
            create_directories
            generate_config
            generate_compose
            pull_images
            start_services
            wait_for_services
            show_status
            show_access_info
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            restart_services
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs "$@"
            ;;
        "clean")
            clean_system
            ;;
        "help"|"-h"|"--help")
            echo "LJWX 灵境万象健康管理系统 - 客户服务器管理脚本"
            echo ""
            echo "使用方法:"
            echo "  ./start.sh [command]"
            echo ""
            echo "命令:"
            echo "  start     启动系统 (默认)"
            echo "  stop      停止系统"
            echo "  restart   重启系统"
            echo "  status    查看状态"
            echo "  logs      查看日志"
            echo "  clean     清理系统"
            echo "  help      显示帮助"
            ;;
        *)
            echo -e "${RED}❌ 未知命令: $1${NC}"
            echo -e "${YELLOW}使用 './start.sh help' 查看帮助${NC}"
            exit 1
            ;;
    esac
}

# 执行主程序
main "$@"
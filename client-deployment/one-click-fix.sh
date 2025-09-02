#!/bin/bash

# LJWX一键修复脚本 - 客户现场部署专用
# 解决MySQL连接问题的完整自动化解决方案

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# 脚本横幅
echo -e "${PURPLE}"
cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║                    LJWX 一键修复工具                         ║
║              解决MySQL连接问题的完整解决方案                  ║
║                   支持 macOS / Linux / CentOS                ║
╚══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo -e "${BLUE}🚀 开始一键修复流程...${NC}"
echo "=================================="

# 步骤1: 跨平台兼容性检测
echo -e "${YELLOW}步骤 1/6: 跨平台兼容性检测${NC}"
if [ -f "./test-cross-platform.sh" ]; then
    chmod +x test-cross-platform.sh
    echo -e "${BLUE}📊 正在检测系统兼容性...${NC}"
    if ./test-cross-platform.sh; then
        echo -e "${GREEN}✅ 兼容性检测通过${NC}"
    else
        echo -e "${RED}❌ 兼容性检测失败，但继续执行${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  跨平台测试脚本不存在，跳过检测${NC}"
fi
echo ""

# 步骤2: 环境自适应修复
echo -e "${YELLOW}步骤 2/6: 环境自适应修复${NC}"
if [ -f "./environment-adaptive-fix.sh" ]; then
    chmod +x environment-adaptive-fix.sh
    echo -e "${BLUE}⚙️  正在执行环境自适应修复...${NC}"
    if ./environment-adaptive-fix.sh; then
        echo -e "${GREEN}✅ 环境自适应修复完成${NC}"
    else
        echo -e "${RED}❌ 环境自适应修复失败${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ 环境自适应修复脚本不存在${NC}"
    exit 1
fi
echo ""

# 步骤3: 停止现有服务
echo -e "${YELLOW}步骤 3/6: 停止现有服务${NC}"
echo -e "${BLUE}🛑 正在停止现有Docker服务...${NC}"

# 检测Docker Compose版本
if command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
elif docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    echo -e "${RED}❌ Docker Compose不可用${NC}"
    exit 1
fi

# 停止现有服务
$COMPOSE_CMD down 2>/dev/null || echo -e "${YELLOW}⚠️  没有运行中的服务需要停止${NC}"
echo -e "${GREEN}✅ 服务停止完成${NC}"
echo ""

# 步骤4: 启动适配服务
echo -e "${YELLOW}步骤 4/6: 启动环境适配服务${NC}"
echo -e "${BLUE}🚀 正在启动环境适配的Docker服务...${NC}"

# 检查是否有MySQL权限问题，如果有则先修复
if [ -d "data/mysql" ] && [ "$(ls -A data/mysql 2>/dev/null)" ]; then
    # 检查MySQL数据目录权限
    MYSQL_OWNER=$(ls -ld data/mysql | awk '{print $3":"$4}')
    CURRENT_USER="$(id -un):$(id -gn)"
    
    if [ "$MYSQL_OWNER" != "$CURRENT_USER" ] && [ "$MYSQL_OWNER" = "999:999" ]; then
        echo -e "${YELLOW}🔧 检测到MySQL权限问题，启用权限修复模式...${NC}"
        
        # 备份现有数据并使用命名卷
        BACKUP_DIR="data/mysql_backup_$(date +%Y%m%d_%H%M%S)"
        echo -e "${BLUE}📦 备份MySQL数据到: $BACKUP_DIR${NC}"
        sudo mv data/mysql "$BACKUP_DIR" 2>/dev/null || {
            echo -e "${YELLOW}⚠️  无法移动数据目录，使用命名卷模式${NC}"
        }
        
        # 使用简化的MySQL配置（命名卷）
        if [ -f "./docker-compose-mysql-simple.yml" ]; then
            echo -e "${BLUE}🚀 使用权限修复配置启动MySQL...${NC}"
            $COMPOSE_CMD -f docker-compose-mysql-simple.yml up -d mysql
            
            # 等待MySQL启动
            echo -e "${BLUE}⏳ 等待MySQL服务就绪...${NC}"
            MAX_WAIT=30
            WAIT_COUNT=0
            while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
                if docker exec ljwx-mysql mysqladmin ping -u root -p123456 >/dev/null 2>&1; then
                    echo -e "${GREEN}✅ MySQL权限修复成功${NC}"
                    break
                fi
                echo -n "."
                sleep 2
                WAIT_COUNT=$((WAIT_COUNT + 1))
            done
        fi
    fi
fi

# 启动其他服务
if [ -f "./docker-compose-adaptive.yml" ]; then
    if $COMPOSE_CMD -f docker-compose-adaptive.yml up -d; then
        echo -e "${GREEN}✅ 环境适配服务启动成功${NC}"
    else
        echo -e "${RED}❌ 环境适配服务启动失败${NC}"
        echo -e "${YELLOW}💡 尝试使用标准配置...${NC}"
        if $COMPOSE_CMD up -d; then
            echo -e "${GREEN}✅ 标准服务启动成功${NC}"
        else
            echo -e "${RED}❌ 服务启动失败${NC}"
            exit 1
        fi
    fi
else
    echo -e "${YELLOW}⚠️  适配配置不存在，使用标准配置${NC}"
    if $COMPOSE_CMD up -d; then
        echo -e "${GREEN}✅ 标准服务启动成功${NC}"
    else
        echo -e "${RED}❌ 服务启动失败${NC}"
        exit 1
    fi
fi
echo ""

# 步骤5: 等待服务就绪
echo -e "${YELLOW}步骤 5/6: 等待服务就绪${NC}"
echo -e "${BLUE}⏳ 正在等待MySQL和Redis服务启动...${NC}"

# 等待MySQL启动
MAX_WAIT=60
WAIT_COUNT=0
while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    if docker exec ljwx-mysql mysqladmin ping -u root -p"${MYSQL_PASSWORD:-123456}" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ MySQL服务已就绪${NC}"
        break
    fi
    echo -n "."
    sleep 2
    WAIT_COUNT=$((WAIT_COUNT + 1))
done

if [ $WAIT_COUNT -ge $MAX_WAIT ]; then
    echo -e "${RED}❌ MySQL服务启动超时${NC}"
    echo -e "${YELLOW}💡 请检查日志: docker logs ljwx-mysql${NC}"
else
    # 等待应用服务启动
    echo -e "${BLUE}⏳ 正在等待应用服务启动...${NC}"
    sleep 10
    
    # 检查应用健康状态
    if curl -s http://localhost:9998/actuator/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ 应用服务已就绪${NC}"
    else
        echo -e "${YELLOW}⚠️  应用服务可能需要更多时间启动${NC}"
    fi
fi
echo ""

# 步骤6: 启动保活服务
echo -e "${YELLOW}步骤 6/6: 启动连接保活服务${NC}"
if [ -f "./mysql-keepalive.sh" ]; then
    chmod +x mysql-keepalive.sh
    echo -e "${BLUE}💓 正在启动MySQL连接保活服务...${NC}"
    
    # 检查是否已有保活进程在运行
    if pgrep -f "mysql-keepalive.sh" >/dev/null; then
        echo -e "${YELLOW}⚠️  保活服务已在运行，先停止旧进程${NC}"
        pkill -f "mysql-keepalive.sh" 2>/dev/null || true
        sleep 2
    fi
    
    # 后台启动保活服务
    nohup ./mysql-keepalive.sh > mysql-keepalive.log 2>&1 &
    KEEPALIVE_PID=$!
    
    # 等待一下确认启动
    sleep 3
    if kill -0 $KEEPALIVE_PID 2>/dev/null; then
        echo -e "${GREEN}✅ 连接保活服务启动成功 (PID: $KEEPALIVE_PID)${NC}"
        echo -e "${BLUE}📋 日志文件: mysql-keepalive.log${NC}"
    else
        echo -e "${RED}❌ 连接保活服务启动失败${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  mysql-keepalive.sh不存在，跳过保活服务${NC}"
fi
echo ""

# 修复完成报告
echo -e "${GREEN}"
cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║                       🎉 修复完成！                          ║
╚══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo -e "${BLUE}📊 服务状态检查:${NC}"
echo "=================================="

# 检查Docker容器状态
echo -e "${YELLOW}Docker容器状态:${NC}"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep ljwx || echo "  无LJWX相关容器运行"

echo ""
echo -e "${YELLOW}服务访问地址:${NC}"
echo "  🌐 管理后台: http://localhost:8080"
echo "  📊 大屏展示: http://localhost:8001"  
echo "  🔧 后端API: http://localhost:9998"
echo "  🗄️  MySQL: localhost:3306"
echo "  🔴 Redis: localhost:6379"

echo ""
echo -e "${YELLOW}日志查看:${NC}"
echo "  📋 环境报告: cat environment-report.txt"
echo "  💓 保活日志: tail -f mysql-keepalive.log"
echo "  🐳 容器日志: docker logs ljwx-mysql"

echo ""
echo -e "${BLUE}💡 如果仍有问题:${NC}"
echo "  1. 检查环境报告中的风险评估"
echo "  2. 查看保活服务日志"
echo "  3. 手动重启: docker-compose restart"
echo "  4. 重新运行: ./one-click-fix.sh"

echo ""
echo -e "${GREEN}🎯 一键修复流程已完成！系统应该能够长期稳定运行。${NC}"

# 可选：安装系统服务提示
echo ""
echo -e "${PURPLE}🔧 可选：安装系统服务（重启后自动启动）${NC}"
OS=$(uname -s)
case "$OS" in
    "Darwin")  # macOS
        if [ -f "com.ljwx.mysql.keepalive.plist" ]; then
            echo -e "${YELLOW}macOS系统服务安装:${NC}"
            echo "  sudo cp com.ljwx.mysql.keepalive.plist /Library/LaunchDaemons/"
            echo "  sudo launchctl load /Library/LaunchDaemons/com.ljwx.mysql.keepalive.plist"
        fi
        ;;
    "Linux")   # Linux
        if [ -f "ljwx-mysql-keepalive.service" ]; then
            echo -e "${YELLOW}Linux系统服务安装:${NC}"
            echo "  sudo cp ljwx-mysql-keepalive.service /etc/systemd/system/"
            echo "  sudo systemctl daemon-reload"
            echo "  sudo systemctl enable ljwx-mysql-keepalive"
        fi
        ;;
esac 

#!/bin/bash

# 重置数据库脚本 - 清除旧数据，使用新的data.sql初始化
# 使用方法：./reset-database.sh [backup_first]

set -e

# 兼容CentOS - 检查终端颜色支持
if [ -t 1 ] && [ "${TERM:-}" != "" ] && tput colors >/dev/null 2>&1; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m'
else #CentOS兼容：无颜色支持时使用空值
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    NC=''
fi

echo -e "${BLUE}🔄 LJWX数据库重置工具${NC}"
echo "=============================================="

# 配置变量
MYSQL_CONTAINER="ljwx-mysql"
MYSQL_VOLUME="client-deployment_mysql_data" 
BACKUP_DIR="./backups/reset"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 检查是否需要备份
BACKUP_FIRST=${1:-"yes"}

echo -e "${YELLOW}⚠️  警告: 此操作将删除所有现有数据库数据！${NC}"
echo ""
echo "当前配置:"
echo "- MySQL容器: $MYSQL_CONTAINER"
echo "- 数据卷: $MYSQL_VOLUME"
echo "- 备份目录: $BACKUP_DIR"
echo ""

if [ "$BACKUP_FIRST" = "yes" ]; then
    echo -e "${YELLOW}📦 备份选项: 启用 (推荐)${NC}"
else
    echo -e "${RED}📦 备份选项: 跳过${NC}"
fi

echo ""
read -p "确认继续重置数据库? (y/N): " confirm
if [[ $confirm != [yY] ]]; then
    echo "操作已取消"
    exit 0
fi

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 1. 备份现有数据（如果需要）
if [ "$BACKUP_FIRST" = "yes" ]; then
    echo ""
    echo -e "${BLUE}📦 步骤1: 备份现有数据${NC}"
    echo "创建备份: $BACKUP_DIR/pre_reset_backup_$TIMESTAMP.sql.gz"
    
    if docker ps | grep $MYSQL_CONTAINER > /dev/null; then
        docker exec $MYSQL_CONTAINER mysqldump \
            -u root -p123456 \
            --single-transaction \
            --routines \
            --triggers \
            --events \
            --hex-blob \
            --databases lj-06 | gzip > "$BACKUP_DIR/pre_reset_backup_$TIMESTAMP.sql.gz"
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ 数据备份完成${NC}"
        else
            echo -e "${RED}❌ 数据备份失败，继续执行重置...${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  MySQL容器未运行，跳过备份${NC}"
    fi
fi

# 2. 停止服务
echo ""
echo -e "${BLUE}🛑 步骤2: 停止相关服务${NC}"
docker-compose down

# 3. 删除数据卷
echo ""
echo -e "${BLUE}🗑️  步骤3: 删除旧数据卷${NC}"
if docker volume ls | grep $MYSQL_VOLUME > /dev/null; then
    docker volume rm $MYSQL_VOLUME
    echo -e "${GREEN}✅ 数据卷已删除${NC}"
else
    echo -e "${YELLOW}⚠️  数据卷不存在${NC}"
fi

# 4. 清理可能存在的旧容器
echo ""
echo -e "${BLUE}🧹 步骤4: 清理旧容器${NC}"
if docker ps -a | grep $MYSQL_CONTAINER > /dev/null; then
    docker rm -f $MYSQL_CONTAINER 2>/dev/null || true
    echo -e "${GREEN}✅ 旧容器已清理${NC}"
fi

# 5. 重新启动MySQL服务
echo ""
echo -e "${BLUE}🚀 步骤5: 启动MySQL服务(使用新数据)${NC}"
docker-compose up -d mysql

# 6. 等待MySQL初始化完成
echo ""
echo -e "${BLUE}⏳ 步骤6: 等待MySQL初始化...${NC}"
echo "正在等待MySQL服务启动并初始化新数据..."

for i in {1..60}; do
    if docker logs $MYSQL_CONTAINER 2>&1 | grep -q "ready for connections"; then
        echo -e "${GREEN}✅ MySQL服务启动完成${NC}"
        break
    fi
    if [ $i -eq 60 ]; then
        echo -e "${RED}❌ MySQL启动超时${NC}"
        echo "请检查日志: docker logs $MYSQL_CONTAINER"
        exit 1
    fi
    echo -n "."
    sleep 2
done

# 7. 验证新数据
echo ""
echo -e "${BLUE}🔍 步骤7: 验证新数据库${NC}"
sleep 5

# 检查数据库是否包含新数据
table_count=$(docker exec $MYSQL_CONTAINER mysql -u root -p123456 -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='lj-06';" 2>/dev/null | tail -1)

if [ ! -z "$table_count" ] && [ "$table_count" -gt 0 ]; then
    echo -e "${GREEN}✅ 数据库初始化成功${NC}"
    echo "📊 检测到 $table_count 个数据表"
    
    # 显示一些关键表的记录数
    echo ""
    echo "关键表记录统计："
    docker exec $MYSQL_CONTAINER mysql -u root -p123456 lj-06 -e "
        SELECT 'sys_user' as table_name, COUNT(*) as record_count FROM sys_user
        UNION ALL
        SELECT 'sys_dict_data', COUNT(*) FROM sys_dict_data  
        UNION ALL
        SELECT 'sys_org_units', COUNT(*) FROM sys_org_units
        UNION ALL
        SELECT 't_interface', COUNT(*) FROM t_interface;" 2>/dev/null || echo "📊 部分表可能还在初始化中"
    
else
    echo -e "${RED}❌ 数据库初始化可能失败${NC}"
    echo "请检查MySQL日志:"
    docker logs $MYSQL_CONTAINER --tail 20
fi

# 8. 启动其他服务
echo ""
echo -e "${BLUE}🚀 步骤8: 启动所有服务${NC}"
docker-compose up -d

echo ""
echo -e "${GREEN}🎉 数据库重置完成！${NC}"
echo ""
echo "📋 操作摘要:"
echo "- 旧数据已备份到: $BACKUP_DIR/pre_reset_backup_$TIMESTAMP.sql.gz"
echo "- 数据卷已重建: $MYSQL_VOLUME"
echo "- 新数据已初始化: data.sql"
echo ""
echo "🔍 验证命令:"
echo "docker exec $MYSQL_CONTAINER mysql -u root -p123456 -e 'SHOW DATABASES;'"
echo ""
echo "📊 服务状态:"
docker-compose ps 

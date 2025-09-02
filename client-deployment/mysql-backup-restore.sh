#!/bin/bash

# MySQL数据库备份和恢复工具 - 支持命名卷和逻辑备份两种模式

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# 配置变量
MYSQL_CONTAINER="ljwx-mysql"
MYSQL_USER="root"
MYSQL_PASSWORD="123456"
MYSQL_DATABASE="lj-06"
BACKUP_DIR="./backups"
VOLUME_NAME="client-deployment_mysql_data"

echo -e "${PURPLE}"
cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║                   MySQL备份恢复工具                          ║
║              支持命名卷和逻辑备份双重保护                      ║
╚══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# 检查Docker是否运行
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker未运行，请先启动Docker${NC}"
    exit 1
fi

# 创建备份目录
mkdir -p "$BACKUP_DIR"/{sql,volume,config}

# 显示菜单
show_menu() {
    echo -e "${BLUE}📋 选择操作:${NC}"
    echo "1. 📦 创建完整备份（推荐）"
    echo "2. 💾 仅SQL逻辑备份"
    echo "3. 🗃️  仅数据卷备份"
    echo "4. 🔄 恢复数据库"
    echo "5. 📊 查看备份列表"
    echo "6. 🔍 验证备份完整性"
    echo "7. 🧹 清理旧备份"
    echo "8. ❌ 退出"
    echo ""
}

# 创建SQL逻辑备份
create_sql_backup() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/sql/ljwx_backup_${timestamp}.sql"
    
    echo -e "${BLUE}📦 正在创建SQL逻辑备份...${NC}"
    
    if docker exec $MYSQL_CONTAINER mysqldump \
        -u $MYSQL_USER -p$MYSQL_PASSWORD \
        --single-transaction \
        --routines \
        --triggers \
        --events \
        --hex-blob \
        --add-drop-database \
        --databases $MYSQL_DATABASE > "$backup_file"; then
        
        # 压缩备份文件
        gzip "$backup_file"
        backup_file="${backup_file}.gz"
        
        # 计算文件大小
        local file_size=$(ls -lh "$backup_file" | awk '{print $5}')
        
        echo -e "${GREEN}✅ SQL备份创建成功${NC}"
        echo "📁 文件: $backup_file"
        echo "📏 大小: $file_size"
        
        # 记录备份信息
        echo "$(date '+%Y-%m-%d %H:%M:%S'),SQL,$backup_file,$file_size" >> "$BACKUP_DIR/backup_log.csv"
        
        return 0
    else
        echo -e "${RED}❌ SQL备份失败${NC}"
        return 1
    fi
}

# 创建数据卷备份
create_volume_backup() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/volume/mysql_volume_${timestamp}.tar.gz"
    
    echo -e "${BLUE}🗃️  正在创建数据卷备份...${NC}"
    
    # 使用临时容器备份数据卷
    if docker run --rm \
        -v $VOLUME_NAME:/source:ro \
        -v "$(pwd)/$BACKUP_DIR/volume":/backup \
        alpine:latest \
        tar -czf "/backup/mysql_volume_${timestamp}.tar.gz" -C /source .; then
        
        # 计算文件信息
        local file_size=$(ls -lh "$backup_file" | awk '{print $5}')
        
        echo -e "${GREEN}✅ 数据卷备份创建成功${NC}"
        echo "📁 文件: $backup_file"
        echo "📏 大小: $file_size"
        
        # 记录备份信息
        echo "$(date '+%Y-%m-%d %H:%M:%S'),VOLUME,$backup_file,$file_size" >> "$BACKUP_DIR/backup_log.csv"
        
        return 0
    else
        echo -e "${RED}❌ 数据卷备份失败${NC}"
        return 1
    fi
}

# 创建完整备份
create_full_backup() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    
    echo -e "${YELLOW}🎯 开始创建完整备份 ($timestamp)${NC}"
    echo "=================================="
    
    # 1. SQL逻辑备份
    echo -e "${BLUE}步骤 1/3: SQL逻辑备份${NC}"
    if ! create_sql_backup; then
        echo -e "${RED}❌ 完整备份失败：SQL备份错误${NC}"
        return 1
    fi
    
    # 2. 数据卷备份
    echo -e "${BLUE}步骤 2/3: 数据卷备份${NC}"
    if ! create_volume_backup; then
        echo -e "${RED}❌ 完整备份失败：数据卷备份错误${NC}"
        return 1
    fi
    
    # 3. 配置文件备份
    echo -e "${BLUE}步骤 3/3: 配置文件备份${NC}"
    local config_backup="$BACKUP_DIR/config/config_${timestamp}.tar.gz"
    
    tar -czf "$config_backup" \
        docker-compose*.yml \
        custom-config.env \
        *.sh \
        2>/dev/null || echo -e "${YELLOW}⚠️  部分配置文件备份失败${NC}"
    
    echo -e "${GREEN}🎉 完整备份创建成功！${NC}"
    echo "=================================="
    echo "📊 备份统计:"
    ls -lh "$BACKUP_DIR"/{sql,volume,config}/*${timestamp}* 2>/dev/null || echo "  备份文件列表获取失败"
}

# 从SQL备份恢复
restore_from_sql() {
    echo -e "${BLUE}📋 可用的SQL备份文件:${NC}"
    if ! ls "$BACKUP_DIR/sql/"*.sql.gz 2>/dev/null | nl; then
        echo -e "${RED}❌ 没有找到SQL备份文件${NC}"
        return 1
    fi
    
    read -p "请输入备份文件编号: " file_num
    backup_file=$(ls "$BACKUP_DIR/sql/"*.sql.gz 2>/dev/null | sed -n "${file_num}p")
    
    if [ -z "$backup_file" ]; then
        echo -e "${RED}❌ 无效的文件编号${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}⚠️  警告: 此操作将完全替换现有数据库！${NC}"
    read -p "确认继续？(yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        echo -e "${BLUE}💡 操作已取消${NC}"
        return 0
    fi
    
    echo -e "${BLUE}🔄 正在从SQL备份恢复...${NC}"
    
    # 解压并恢复
    if zcat "$backup_file" | docker exec -i $MYSQL_CONTAINER mysql -u $MYSQL_USER -p$MYSQL_PASSWORD; then
        echo -e "${GREEN}✅ SQL恢复成功${NC}"
        
        # 验证恢复
        table_count=$(docker exec $MYSQL_CONTAINER mysql -u $MYSQL_USER -p$MYSQL_PASSWORD -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$MYSQL_DATABASE';" 2>/dev/null | tail -1)
        echo -e "${BLUE}📊 恢复验证: $table_count 个表${NC}"
    else
        echo -e "${RED}❌ SQL恢复失败${NC}"
        return 1
    fi
}

# 查看备份列表
list_backups() {
    echo -e "${BLUE}📊 备份文件列表:${NC}"
    echo "=================================="
    
    if [ -f "$BACKUP_DIR/backup_log.csv" ]; then
        echo -e "${YELLOW}📋 最近10次备份日志:${NC}"
        echo "时间,类型,文件,大小"
        echo "--------------------------------"
        tail -10 "$BACKUP_DIR/backup_log.csv" 2>/dev/null || echo "  备份日志为空"
        echo ""
    fi
    
    echo -e "${YELLOW}📁 SQL备份文件:${NC}"
    ls -lh "$BACKUP_DIR/sql/"*.sql.gz 2>/dev/null || echo "  无SQL备份文件"
    
    echo ""
    echo -e "${YELLOW}🗃️  数据卷备份文件:${NC}"
    ls -lh "$BACKUP_DIR/volume/"*.tar.gz 2>/dev/null || echo "  无数据卷备份文件"
    
    echo ""
    echo -e "${YELLOW}⚙️  配置备份文件:${NC}"
    ls -lh "$BACKUP_DIR/config/"*.tar.gz 2>/dev/null || echo "  无配置备份文件"
}

# 验证备份完整性
verify_backups() {
    echo -e "${BLUE}🔍 验证备份完整性...${NC}"
    
    # 验证SQL备份
    for sql_file in "$BACKUP_DIR/sql/"*.sql.gz; do
        if [ -f "$sql_file" ]; then
            echo -n "📄 $(basename "$sql_file"): "
            if zcat "$sql_file" | head -20 | grep -q "MySQL dump"; then
                echo -e "${GREEN}✅ 有效${NC}"
            else
                echo -e "${RED}❌ 损坏${NC}"
            fi
        fi
    done
    
    # 验证数据卷备份
    for vol_file in "$BACKUP_DIR/volume/"*.tar.gz; do
        if [ -f "$vol_file" ]; then
            echo -n "🗃️  $(basename "$vol_file"): "
            if tar -tzf "$vol_file" >/dev/null 2>&1; then
                echo -e "${GREEN}✅ 有效${NC}"
            else
                echo -e "${RED}❌ 损坏${NC}"
            fi
        fi
    done
}

# 主循环
while true; do
    show_menu
    read -p "请选择操作 (1-8): " choice
    
    case $choice in
        1) create_full_backup ;;
        2) create_sql_backup ;;
        3) create_volume_backup ;;
        4) restore_from_sql ;;
        5) list_backups ;;
        6) verify_backups ;;
        7) echo -e "${YELLOW}💡 清理功能待实现${NC}" ;;
        8) 
            echo -e "${GREEN}👋 再见！${NC}"
            exit 0
            ;;
        *) 
            echo -e "${RED}❌ 无效选择，请输入 1-8${NC}"
            ;;
    esac
    
    echo ""
    read -p "按回车键继续..."
    echo ""
done 

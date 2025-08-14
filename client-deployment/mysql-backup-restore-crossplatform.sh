#!/bin/bash

# MySQL数据库备份和恢复工具 - 跨平台版本
# 支持: CentOS, macOS, Ubuntu, Debian

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# 检测操作系统类型
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS_TYPE="macos"
        OS_VERSION=$(sw_vers -productVersion 2>/dev/null || echo "unknown")
    elif [[ -f /etc/centos-release ]] || [[ -f /etc/redhat-release ]]; then
        OS_TYPE="centos"
        OS_VERSION=$(cat /etc/centos-release 2>/dev/null | grep -o '[0-9]\+\.[0-9]\+' | head -1 || echo "unknown")
    elif [[ -f /etc/debian_version ]]; then
        if grep -q "Ubuntu" /etc/os-release 2>/dev/null; then
            OS_TYPE="ubuntu"
            OS_VERSION=$(grep VERSION_ID /etc/os-release | cut -d'"' -f2 || echo "unknown")
        else
            OS_TYPE="debian"
            OS_VERSION=$(cat /etc/debian_version 2>/dev/null || echo "unknown")
        fi
    else
        OS_TYPE="linux"
        OS_VERSION="unknown"
    fi
}

# 跨平台命令适配
get_compression_cmd() {
    case $OS_TYPE in
        "macos")
            echo "gunzip -c"  # macOS使用gunzip避免zcat问题
            ;;
        "centos"|"ubuntu"|"debian"|"linux")
            if command -v zcat >/dev/null 2>&1; then
                echo "zcat"  # Linux优先使用zcat
            else
                echo "gunzip -c"  # 备选gunzip
            fi
            ;;
        *)
            echo "gunzip -c"  # 默认使用gunzip
            ;;
    esac
}

# 跨平台MD5计算
get_md5_cmd() {
    case $OS_TYPE in
        "macos")
            echo "md5 -r"  # macOS使用md5命令
            ;;
        "centos"|"ubuntu"|"debian"|"linux")
            if command -v md5sum >/dev/null 2>&1; then
                echo "md5sum"  # Linux使用md5sum
            else
                echo "md5 -r"  # 备选md5
            fi
            ;;
        *)
            echo "md5sum"  # 默认使用md5sum
            ;;
    esac
}

# 初始化系统检测
detect_os
DECOMPRESS_CMD=$(get_compression_cmd)
MD5_CMD=$(get_md5_cmd)

# 配置变量
MYSQL_CONTAINER="ljwx-mysql"
MYSQL_USER="root"
MYSQL_PASSWORD="123456"
MYSQL_DATABASE="lj-06"
BACKUP_DIR="./backups"
VOLUME_NAME="client-deployment_mysql_data"

# 脚本横幅
echo -e "${PURPLE}"
cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║              MySQL备份恢复工具 - 跨平台版本                    ║
║          支持: CentOS, macOS, Ubuntu, Debian               ║
╚══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# 显示系统信息
echo -e "${BLUE}🖥️  系统信息:${NC}"
echo "   操作系统: $OS_TYPE $OS_VERSION"
echo "   解压命令: $DECOMPRESS_CMD"
echo "   MD5命令: $MD5_CMD"
echo ""

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
        --databases $MYSQL_DATABASE > "$backup_file" 2>/dev/null; then
        
        # 压缩备份文件
        gzip "$backup_file"
        backup_file="${backup_file}.gz"
        
        # 计算文件大小和MD5
        local file_size=$(ls -lh "$backup_file" | awk '{print $5}')
        local md5_hash
        case $OS_TYPE in
            "macos")
                md5_hash=$(md5 -r "$backup_file" | awk '{print $1}')
                ;;
            *)
                md5_hash=$(md5sum "$backup_file" | awk '{print $1}')
                ;;
        esac
        
        echo -e "${GREEN}✅ SQL备份创建成功${NC}"
        echo "📁 文件: $backup_file"
        echo "📏 大小: $file_size"
        echo "🔐 MD5: $md5_hash"
        
        # 记录备份信息
        echo "$(date '+%Y-%m-%d %H:%M:%S'),SQL,$backup_file,$file_size,$md5_hash" >> "$BACKUP_DIR/backup_log.csv"
        
        return 0
    else
        echo -e "${RED}❌ SQL备份失败${NC}"
        return 1
    fi
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
    echo "   使用解压命令: $DECOMPRESS_CMD"
    
    # 解压并恢复（跨平台兼容）
    if $DECOMPRESS_CMD "$backup_file" | docker exec -i $MYSQL_CONTAINER mysql -u $MYSQL_USER -p$MYSQL_PASSWORD 2>/dev/null; then
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
        echo "时间,类型,文件,大小,MD5"
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
    echo "   使用解压命令: $DECOMPRESS_CMD"
    
    # 验证SQL备份
    for sql_file in "$BACKUP_DIR/sql/"*.sql.gz; do
        if [ -f "$sql_file" ]; then
            echo -n "📄 $(basename "$sql_file"): "
            if $DECOMPRESS_CMD "$sql_file" | head -20 | grep -q "MySQL dump"; then
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
        1) echo -e "${YELLOW}💡 完整备份功能请使用 auto-backup-crossplatform.sh manual${NC}" ;;
        2) create_sql_backup ;;
        3) echo -e "${YELLOW}💡 数据卷备份功能请使用 auto-backup-crossplatform.sh${NC}" ;;
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

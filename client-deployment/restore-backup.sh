#!/bin/bash
# 数据恢复脚本 #支持SQL备份和卷备份的恢复

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' #重置颜色

echo "==================== 数据恢复工具 ===================="
echo "支持恢复类型:"
echo "1) SQL备份恢复 (auto-backup.sh生成的.sql.gz文件)"
echo "2) 卷备份恢复 (离线卷备份的.tar.gz文件)"
echo "3) 退出"
echo ""

while true; do
    read -p "请选择恢复类型 [1-3]: " restore_type
    case $restore_type in
        1)
            echo -e "${BLUE}📦 SQL备份恢复模式${NC}"
            restore_mode="sql"
            break
            ;;
        2)
            echo -e "${BLUE}📦 卷备份恢复模式${NC}"
            restore_mode="volume"
            break
            ;;
        3)
            echo "退出恢复工具"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ 无效选择，请输入 1-3${NC}"
            ;;
    esac
done

# SQL备份恢复
restore_sql_backup() {
    echo ""
    echo -e "${BLUE}🔍 查找SQL备份文件...${NC}"
    
    # 查找备份文件
    backup_files=$(find . -name "*.sql.gz" -o -name "*.sql" | sort -r)
    
    if [ -z "$backup_files" ]; then
        echo -e "${RED}❌ 未找到SQL备份文件${NC}"
        exit 1
    fi
    
    echo "发现以下备份文件:"
    i=1
    declare -a file_array
    for file in $backup_files; do
        echo "$i) $file"
        file_array[$i]=$file
        i=$((i + 1))
    done
    echo ""
    
    while true; do
        read -p "请选择要恢复的备份文件 [1-$((i-1))]: " file_choice
        if [[ "$file_choice" =~ ^[0-9]+$ ]] && [ "$file_choice" -ge 1 ] && [ "$file_choice" -lt "$i" ]; then
            selected_file=${file_array[$file_choice]}
            break
        else
            echo -e "${RED}❌ 无效选择${NC}"
        fi
    done
    
    echo ""
    echo -e "${YELLOW}⚠️  警告: 恢复操作将覆盖现有数据！${NC}"
    read -p "确认恢复 $selected_file 吗? (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "恢复已取消"
        exit 0
    fi
    
    # 检查MySQL容器状态
    if ! docker ps | grep -q ljwx-mysql; then
        echo -e "${BLUE}🚀 启动MySQL服务...${NC}"
        docker-compose up -d mysql
        
        # 等待MySQL启动
        echo "等待MySQL启动..."
        for i in {1..30}; do
            if docker exec ljwx-mysql mysqladmin ping -u root -p123456 >/dev/null 2>&1; then
                echo -e "${GREEN}✅ MySQL启动成功${NC}"
                break
            fi
            if [ $i -eq 30 ]; then
                echo -e "${RED}❌ MySQL启动超时${NC}"
                exit 1
            fi
            sleep 2
        done
    fi
    
    # 恢复数据
    echo ""
    echo -e "${BLUE}📤 恢复数据: $selected_file${NC}"
    
    if [[ "$selected_file" == *.gz ]]; then
        # 压缩文件
        gunzip -c "$selected_file" | docker exec -i ljwx-mysql mysql -u root -p123456
    else
        # 普通SQL文件
        docker exec -i ljwx-mysql mysql -u root -p123456 < "$selected_file"
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ SQL数据恢复成功${NC}"
    else
        echo -e "${RED}❌ SQL数据恢复失败${NC}"
        exit 1
    fi
}

# 卷备份恢复
restore_volume_backup() {
    echo ""
    echo -e "${BLUE}🔍 查找卷备份目录...${NC}"
    
    # 查找卷备份目录
    backup_dirs=$(find . -type d -name "volume_backup_*" | sort -r)
    
    if [ -z "$backup_dirs" ]; then
        echo -e "${RED}❌ 未找到卷备份目录${NC}"
        exit 1
    fi
    
    echo "发现以下备份目录:"
    i=1
    declare -a dir_array
    for dir in $backup_dirs; do
        echo "$i) $dir"
        dir_array[$i]=$dir
        i=$((i + 1))
    done
    echo ""
    
    while true; do
        read -p "请选择要恢复的备份目录 [1-$((i-1))]: " dir_choice
        if [[ "$dir_choice" =~ ^[0-9]+$ ]] && [ "$dir_choice" -ge 1 ] && [ "$dir_choice" -lt "$i" ]; then
            selected_dir=${dir_array[$dir_choice]}
            break
        else
            echo -e "${RED}❌ 无效选择${NC}"
        fi
    done
    
    echo ""
    echo -e "${BLUE}📋 备份目录内容: $selected_dir${NC}"
    ls -la "$selected_dir"
    
    echo ""
    echo -e "${YELLOW}⚠️  警告: 恢复操作将覆盖现有数据卷！${NC}"
    read -p "确认恢复 $selected_dir 中的卷备份吗? (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "恢复已取消"
        exit 0
    fi
    
    # 停止所有服务
    echo ""
    echo -e "${BLUE}🛑 停止服务...${NC}"
    docker-compose down
    
    # 恢复每个卷
    echo ""
    echo -e "${BLUE}📤 恢复数据卷...${NC}"
    
    for tar_file in "$selected_dir"/*.tar.gz; do
        if [ -f "$tar_file" ]; then
            volume_name=$(basename "$tar_file" .tar.gz)
            full_volume_name="client-deployment_${volume_name}"
            
            echo "恢复卷: $full_volume_name"
            
            # 删除现有卷
            docker volume rm "$full_volume_name" 2>/dev/null || true
            
            # 创建新卷并恢复数据
            docker volume create "$full_volume_name"
            docker run --rm -v "$full_volume_name:/data" -v "$(pwd)/$selected_dir:/backup" alpine sh -c "cd /data && tar xzf /backup/$(basename "$tar_file")"
            
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✅ $volume_name 恢复成功${NC}"
            else
                echo -e "${RED}❌ $volume_name 恢复失败${NC}"
            fi
        fi
    done
    
    # 重新启动服务
    echo ""
    echo -e "${BLUE}🚀 重新启动服务...${NC}"
    docker-compose up -d
    
    echo -e "${GREEN}✅ 卷备份恢复完成${NC}"
}

# 执行恢复
case $restore_mode in
    "sql")
        restore_sql_backup
        ;;
    "volume")
        restore_volume_backup
        ;;
esac

echo ""
echo -e "${GREEN}🎉 数据恢复完成！${NC}"
echo ""
echo "📊 验证恢复结果:"
echo "- 查看服务状态: docker-compose ps"
echo "- 检查MySQL数据: docker exec ljwx-mysql mysql -u root -p123456 -e 'SHOW DATABASES;'"
echo "- 检查卷状态: docker volume ls"
echo ""
echo "如有问题，请联系技术支持" 
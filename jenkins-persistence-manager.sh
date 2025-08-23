#!/bin/bash
# Jenkins完整持久化管理脚本

set -e
BASE_DIR="/Users/brunogao/work/infra"
COMPOSE_FILE="$BASE_DIR/docker/compose/jenkins-persistent.yml"
DATA_DIR="$BASE_DIR/data/jenkins"
BACKUP_DIR="$BASE_DIR/backup/jenkins"

# 颜色定义
G='\033[0;32m'
Y='\033[1;33m'
R='\033[0;31m'
B='\033[0;34m'
NC='\033[0m'

log() { echo -e "${G}[INFO]${NC} $1"; }
warn() { echo -e "${Y}[WARN]${NC} $1"; }
error() { echo -e "${R}[ERROR]${NC} $1"; }
info() { echo -e "${B}[INFO]${NC} $1"; }

# 初始化持久化目录结构
init_persistence() {
    log "初始化Jenkins持久化目录结构..."
    
    # 创建主要数据目录
    mkdir -p "$DATA_DIR"/{home,workspace,jobs,builds,plugins,secrets,users,logs,cache,tmp}
    mkdir -p "$BACKUP_DIR"/{full,incremental,config}
    
    # 设置权限
    sudo chown -R 1000:1000 "$DATA_DIR" 2>/dev/null || {
        warn "无法设置权限，请手动执行: sudo chown -R 1000:1000 $DATA_DIR"
    }
    
    chmod -R 755 "$DATA_DIR"
    
    log "✅ 持久化目录初始化完成"
    
    # 显示目录结构
    tree "$DATA_DIR" -L 2 2>/dev/null || {
        echo "目录结构:"
        find "$DATA_DIR" -type d -maxdepth 2 | sort
    }
}

# 启动持久化Jenkins
start_persistent() {
    log "启动持久化Jenkins..."
    
    # 确保网络存在
    docker network create cicd-network 2>/dev/null || true
    
    # 停止现有实例
    docker stop jenkins-simple jenkins-persistent 2>/dev/null || true
    docker rm jenkins-simple jenkins-persistent 2>/dev/null || true
    
    cd "$BASE_DIR/docker/compose"
    docker-compose -f jenkins-persistent.yml up -d
    
    # 等待启动
    log "等待Jenkins启动..."
    for i in {1..60}; do
        if curl -sf "http://localhost:8081/login" &>/dev/null; then
            log "✅ Jenkins启动成功！"
            return 0
        fi
        sleep 3
        echo -n "."
    done
    
    error "❌ Jenkins启动超时"
    return 1
}

# 完整备份
full_backup() {
    local backup_name="jenkins-full-$(date +%Y%m%d_%H%M%S)"
    local backup_path="$BACKUP_DIR/full/$backup_name"
    
    log "执行完整备份: $backup_name"
    
    # 停止Jenkins确保数据一致性
    warn "为确保数据一致性，需要短暂停止Jenkins，是否继续？(y/N)"
    read -r confirm
    if [[ $confirm != "y" && $confirm != "Y" ]]; then
        log "备份已取消"
        return 0
    fi
    
    log "停止Jenkins..."
    docker stop jenkins-persistent 2>/dev/null || true
    
    # 创建完整备份
    mkdir -p "$BACKUP_DIR/full"
    
    log "创建完整备份..."
    tar -czf "$backup_path.tar.gz" \
        -C "$BASE_DIR/data" jenkins \
        -C "$BASE_DIR/docker/compose" jenkins
    
    # 备份元数据
    cat > "$backup_path.meta" << EOF
# Jenkins备份元数据
BACKUP_TYPE=full
BACKUP_DATE=$(date)
JENKINS_VERSION=$(docker exec jenkins-persistent cat /var/jenkins_home/war/META-INF/MANIFEST.MF 2>/dev/null | grep "Jenkins-Version" || echo "unknown")
BACKUP_SIZE=$(du -h "$backup_path.tar.gz" | cut -f1)
DATA_ITEMS=$(find "$DATA_DIR" -type f | wc -l)
CONFIG_FILES=$(find "$BASE_DIR/docker/compose/jenkins" -name "*.yaml" -o -name "*.yml" -o -name "*.txt" | wc -l)
EOF
    
    # 重启Jenkins
    log "重启Jenkins..."
    start_persistent
    
    log "✅ 完整备份完成: $backup_path.tar.gz"
    log "📊 备份大小: $(du -h "$backup_path.tar.gz" | cut -f1)"
    
    # 清理旧备份(保留最近10个)
    cd "$BACKUP_DIR/full"
    ls -t jenkins-full-*.tar.gz 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null || true
}

# 增量备份
incremental_backup() {
    local backup_name="jenkins-inc-$(date +%Y%m%d_%H%M%S)"
    local backup_path="$BACKUP_DIR/incremental/$backup_name"
    local last_backup_file="$BACKUP_DIR/.last_backup_time"
    
    log "执行增量备份: $backup_name"
    
    # 获取上次备份时间
    local last_backup_time=""
    if [[ -f "$last_backup_file" ]]; then
        last_backup_time=$(cat "$last_backup_file")
        log "上次备份时间: $last_backup_time"
    else
        warn "未找到上次备份记录，将备份所有文件"
        last_backup_time="1970-01-01 00:00:00"
    fi
    
    mkdir -p "$BACKUP_DIR/incremental"
    
    # 查找修改的文件
    log "查找修改的文件..."
    find "$DATA_DIR" -newer "$last_backup_file" 2>/dev/null > /tmp/changed_files.txt || {
        find "$DATA_DIR" -type f > /tmp/changed_files.txt
    }
    
    local changed_count=$(wc -l < /tmp/changed_files.txt)
    log "发现 $changed_count 个修改的文件"
    
    if [[ $changed_count -eq 0 ]]; then
        log "没有文件需要备份"
        return 0
    fi
    
    # 创建增量备份
    tar -czf "$backup_path.tar.gz" -T /tmp/changed_files.txt
    
    # 备份元数据
    cat > "$backup_path.meta" << EOF
# Jenkins增量备份元数据
BACKUP_TYPE=incremental
BACKUP_DATE=$(date)
LAST_BACKUP=$last_backup_time
CHANGED_FILES=$changed_count
BACKUP_SIZE=$(du -h "$backup_path.tar.gz" | cut -f1)
EOF
    
    # 更新备份时间
    date > "$last_backup_file"
    
    log "✅ 增量备份完成: $backup_path.tar.gz"
    log "📊 备份文件数: $changed_count, 大小: $(du -h "$backup_path.tar.gz" | cut -f1)"
    
    # 清理旧增量备份(保留最近30个)
    cd "$BACKUP_DIR/incremental"
    ls -t jenkins-inc-*.tar.gz 2>/dev/null | tail -n +31 | xargs rm -f 2>/dev/null || true
    
    rm -f /tmp/changed_files.txt
}

# 配置备份
config_backup() {
    local backup_name="jenkins-config-$(date +%Y%m%d_%H%M%S)"
    local backup_path="$BACKUP_DIR/config/$backup_name"
    
    log "备份Jenkins配置文件..."
    
    mkdir -p "$BACKUP_DIR/config"
    
    # 备份关键配置文件
    tar -czf "$backup_path.tar.gz" \
        -C "$DATA_DIR" \
        --include="*/config.xml" \
        --include="*/credentials.xml" \
        --include="*/users/*" \
        --include="*/secrets/*" \
        . \
        2>/dev/null || true
    
    # 备份CasC配置
    if [[ -d "$BASE_DIR/docker/compose/jenkins" ]]; then
        tar -rzf "$backup_path.tar.gz" \
            -C "$BASE_DIR/docker/compose" jenkins
    fi
    
    log "✅ 配置备份完成: $backup_path.tar.gz"
    
    # 清理旧配置备份(保留最近20个)
    cd "$BACKUP_DIR/config"
    ls -t jenkins-config-*.tar.gz 2>/dev/null | tail -n +21 | xargs rm -f 2>/dev/null || true
}

# 恢复备份
restore_backup() {
    log "可用备份列表:"
    echo ""
    
    # 显示完整备份
    if ls "$BACKUP_DIR/full/"jenkins-full-*.tar.gz &>/dev/null; then
        echo -e "${B}=== 完整备份 ===${NC}"
        ls -la "$BACKUP_DIR/full/"jenkins-full-*.tar.gz | awk '{print $9, $5, $6, $7, $8}' | tail -5
        echo ""
    fi
    
    # 显示配置备份
    if ls "$BACKUP_DIR/config/"jenkins-config-*.tar.gz &>/dev/null; then
        echo -e "${B}=== 配置备份 ===${NC}"
        ls -la "$BACKUP_DIR/config/"jenkins-config-*.tar.gz | awk '{print $9, $5, $6, $7, $8}' | tail -5
        echo ""
    fi
    
    echo -n "请输入备份文件完整路径: "
    read -r backup_file
    
    if [[ ! -f "$backup_file" ]]; then
        error "备份文件不存在: $backup_file"
        return 1
    fi
    
    warn "此操作将覆盖现有Jenkins数据，是否继续？(y/N)"
    read -r confirm
    if [[ $confirm != "y" && $confirm != "Y" ]]; then
        log "恢复操作已取消"
        return 0
    fi
    
    log "停止Jenkins..."
    docker stop jenkins-persistent 2>/dev/null || true
    
    log "恢复备份数据..."
    
    # 备份当前数据
    local current_backup="$BACKUP_DIR/before-restore-$(date +%Y%m%d_%H%M%S).tar.gz"
    tar -czf "$current_backup" -C "$BASE_DIR/data" jenkins 2>/dev/null || true
    log "当前数据已备份到: $current_backup"
    
    # 恢复数据
    rm -rf "$DATA_DIR"
    mkdir -p "$DATA_DIR"
    tar -xzf "$backup_file" -C "$BASE_DIR/data" 2>/dev/null || {
        tar -xzf "$backup_file" -C "$BASE_DIR"
    }
    
    # 设置权限
    sudo chown -R 1000:1000 "$DATA_DIR" 2>/dev/null || true
    chmod -R 755 "$DATA_DIR"
    
    log "重启Jenkins..."
    start_persistent
    
    log "✅ 备份恢复完成"
}

# 数据迁移
migrate_data() {
    log "Jenkins数据迁移工具"
    
    echo "选择迁移类型:"
    echo "1. 从旧Jenkins实例迁移"
    echo "2. 从Docker卷迁移"
    echo "3. 从其他目录迁移"
    
    echo -n "请选择 (1-3): "
    read -r choice
    
    case $choice in
        1) migrate_from_old_jenkins ;;
        2) migrate_from_volume ;;
        3) migrate_from_directory ;;
        *) error "无效选择" ;;
    esac
}

# 从旧Jenkins迁移
migrate_from_old_jenkins() {
    echo -n "请输入旧Jenkins容器名称: "
    read -r old_container
    
    if ! docker ps -a --format "{{.Names}}" | grep -q "^${old_container}$"; then
        error "容器 $old_container 不存在"
        return 1
    fi
    
    log "从容器 $old_container 迁移数据..."
    
    # 停止旧容器
    docker stop "$old_container" 2>/dev/null || true
    
    # 复制数据
    docker cp "$old_container:/var/jenkins_home/." "$DATA_DIR/"
    
    # 设置权限
    sudo chown -R 1000:1000 "$DATA_DIR" 2>/dev/null || true
    
    log "✅ 迁移完成，请启动新的持久化Jenkins"
}

# 从Docker卷迁移
migrate_from_volume() {
    echo -n "请输入Docker卷名称: "
    read -r volume_name
    
    if ! docker volume inspect "$volume_name" &>/dev/null; then
        error "Docker卷 $volume_name 不存在"
        return 1
    fi
    
    log "从Docker卷 $volume_name 迁移数据..."
    
    # 使用临时容器复制数据
    docker run --rm \
        -v "$volume_name:/source:ro" \
        -v "$DATA_DIR:/target" \
        busybox \
        cp -a /source/. /target/
    
    # 设置权限
    sudo chown -R 1000:1000 "$DATA_DIR" 2>/dev/null || true
    
    log "✅ 迁移完成"
}

# 从目录迁移
migrate_from_directory() {
    echo -n "请输入源目录路径: "
    read -r source_dir
    
    if [[ ! -d "$source_dir" ]]; then
        error "目录 $source_dir 不存在"
        return 1
    fi
    
    log "从目录 $source_dir 迁移数据..."
    
    cp -a "$source_dir/." "$DATA_DIR/"
    
    # 设置权限
    sudo chown -R 1000:1000 "$DATA_DIR" 2>/dev/null || true
    
    log "✅ 迁移完成"
}

# 数据验证
verify_data() {
    log "验证Jenkins数据完整性..."
    
    local status=0
    
    # 检查关键文件
    local key_files=(
        "$DATA_DIR/home/config.xml"
        "$DATA_DIR/home/credentials.xml"
        "$DATA_DIR/users"
        "$DATA_DIR/jobs"
        "$DATA_DIR/plugins"
        "$DATA_DIR/secrets"
    )
    
    for file in "${key_files[@]}"; do
        if [[ -e "$file" ]]; then
            log "✅ $file 存在"
        else
            warn "⚠️  $file 不存在"
            ((status++))
        fi
    done
    
    # 检查权限
    local owner=$(stat -f "%Su:%Sg" "$DATA_DIR" 2>/dev/null || stat -c "%U:%G" "$DATA_DIR")
    if [[ "$owner" == "1000:1000" ]] || [[ "$owner" == "jenkins:jenkins" ]]; then
        log "✅ 文件权限正确"
    else
        warn "⚠️  文件权限可能有问题: $owner"
        ((status++))
    fi
    
    # 检查磁盘空间
    local disk_usage=$(df -h "$DATA_DIR" | awk 'NR==2{print $5}' | sed 's/%//')
    if [[ $disk_usage -gt 90 ]]; then
        warn "⚠️  磁盘使用率过高: ${disk_usage}%"
        ((status++))
    else
        log "✅ 磁盘空间充足: ${disk_usage}%"
    fi
    
    # 统计数据
    local job_count=$(find "$DATA_DIR/jobs" -maxdepth 1 -type d 2>/dev/null | wc -l)
    local plugin_count=$(find "$DATA_DIR/plugins" -name "*.jpi" 2>/dev/null | wc -l)
    local user_count=$(find "$DATA_DIR/users" -maxdepth 1 -type d 2>/dev/null | wc -l)
    
    log "📊 数据统计:"
    log "   作业数量: $job_count"
    log "   插件数量: $plugin_count"
    log "   用户数量: $user_count"
    log "   数据大小: $(du -sh "$DATA_DIR" | cut -f1)"
    
    if [[ $status -eq 0 ]]; then
        log "🎉 数据验证通过"
    else
        warn "⚠️  发现 $status 个问题"
    fi
    
    return $status
}

# 自动备份调度
setup_auto_backup() {
    log "设置自动备份调度..."
    
    # 创建备份脚本
    cat > "$BASE_DIR/auto-backup.sh" << 'EOF'
#!/bin/bash
# Jenkins自动备份脚本

BASE_DIR="/Users/brunogao/work/infra"
cd "$BASE_DIR"

# 获取星期几
DAY_OF_WEEK=$(date +%u)

if [[ $DAY_OF_WEEK -eq 7 ]]; then
    # 周日执行完整备份
    echo "$(date): 执行周度完整备份"
    ./jenkins-persistence-manager.sh full-backup
else
    # 平日执行增量备份
    echo "$(date): 执行日度增量备份"
    ./jenkins-persistence-manager.sh incremental-backup
fi

# 每日配置备份
./jenkins-persistence-manager.sh config-backup
EOF
    
    chmod +x "$BASE_DIR/auto-backup.sh"
    
    # 添加到crontab
    local cron_line="0 2 * * * $BASE_DIR/auto-backup.sh >> $BASE_DIR/backup/backup.log 2>&1"
    
    if crontab -l 2>/dev/null | grep -q "auto-backup.sh"; then
        log "自动备份任务已存在"
    else
        (crontab -l 2>/dev/null; echo "$cron_line") | crontab -
        log "✅ 自动备份任务已添加 (每日2点执行)"
    fi
    
    log "📋 备份策略:"
    log "   • 周日: 完整备份"
    log "   • 平日: 增量备份"
    log "   • 每日: 配置备份"
    log "   • 日志: $BASE_DIR/backup/backup.log"
}

# 显示存储使用情况
show_storage() {
    log "Jenkins存储使用情况:"
    
    echo ""
    echo -e "${B}=== 数据目录 ===${NC}"
    du -sh "$DATA_DIR"/* 2>/dev/null | sort -hr
    
    echo ""
    echo -e "${B}=== 备份目录 ===${NC}"
    du -sh "$BACKUP_DIR"/* 2>/dev/null | sort -hr
    
    echo ""
    echo -e "${B}=== 磁盘使用 ===${NC}"
    df -h "$DATA_DIR"
    
    echo ""
    echo -e "${B}=== 最近备份 ===${NC}"
    ls -lah "$BACKUP_DIR"/*/*.tar.gz 2>/dev/null | tail -10 || echo "无备份文件"
}

# 显示菜单
show_menu() {
    echo ""
    echo "===== Jenkins持久化管理工具 ====="
    echo "1.  初始化持久化环境"
    echo "2.  启动持久化Jenkins"
    echo "3.  完整备份"
    echo "4.  增量备份"
    echo "5.  配置备份"
    echo "6.  恢复备份"
    echo "7.  数据迁移"
    echo "8.  数据验证"
    echo "9.  设置自动备份"
    echo "10. 存储使用情况"
    echo "11. 清理旧备份"
    echo "0.  退出"
    echo ""
    echo -n "请选择操作 (0-11): "
}

# 清理旧备份
cleanup_old_backups() {
    log "清理旧备份文件..."
    
    local cleaned=0
    
    # 清理30天前的增量备份
    find "$BACKUP_DIR/incremental" -name "*.tar.gz" -mtime +30 -delete 2>/dev/null && {
        local count=$(find "$BACKUP_DIR/incremental" -name "*.tar.gz" -mtime +30 2>/dev/null | wc -l)
        cleaned=$((cleaned + count))
    }
    
    # 清理90天前的完整备份
    find "$BACKUP_DIR/full" -name "*.tar.gz" -mtime +90 -delete 2>/dev/null && {
        local count=$(find "$BACKUP_DIR/full" -name "*.tar.gz" -mtime +90 2>/dev/null | wc -l)
        cleaned=$((cleaned + count))
    }
    
    # 清理60天前的配置备份
    find "$BACKUP_DIR/config" -name "*.tar.gz" -mtime +60 -delete 2>/dev/null && {
        local count=$(find "$BACKUP_DIR/config" -name "*.tar.gz" -mtime +60 2>/dev/null | wc -l)
        cleaned=$((cleaned + count))
    }
    
    log "✅ 已清理 $cleaned 个过期备份文件"
    
    # 显示当前备份情况
    show_storage
}

# 主程序
main() {
    while true; do
        show_menu
        read -r choice
        
        case $choice in
            1) init_persistence ;;
            2) start_persistent ;;
            3) full_backup ;;
            4) incremental_backup ;;
            5) config_backup ;;
            6) restore_backup ;;
            7) migrate_data ;;
            8) verify_data ;;
            9) setup_auto_backup ;;
            10) show_storage ;;
            11) cleanup_old_backups ;;
            0) log "再见！"; exit 0 ;;
            *) error "无效选择" ;;
        esac
        
        echo ""
        echo "按回车键继续..."
        read -r
    done
}

# 命令行参数处理
if [[ $# -gt 0 ]]; then
    case $1 in
        "init") init_persistence ;;
        "start") start_persistent ;;
        "full-backup") full_backup ;;
        "incremental-backup") incremental_backup ;;
        "config-backup") config_backup ;;
        "restore") restore_backup ;;
        "migrate") migrate_data ;;
        "verify") verify_data ;;
        "auto-backup") setup_auto_backup ;;
        "storage") show_storage ;;
        "cleanup") cleanup_old_backups ;;
        *) echo "用法: $0 [init|start|full-backup|incremental-backup|config-backup|restore|migrate|verify|auto-backup|storage|cleanup]" ;;
    esac
else
    main
fi 
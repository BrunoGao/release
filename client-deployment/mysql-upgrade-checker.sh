#!/bin/bash
# MySQL升级预检查器 | 使用说明: ./mysql-upgrade-checker.sh [目标版本]

CFG="custom-config.env"; [[ -f "$CFG" ]] && source "$CFG"  #加载配置
MYSQL_CONTAINER="${MYSQL_CONTAINER:-ljwx-mysql}"; MYSQL_USER="${MYSQL_USER:-root}"; MYSQL_PASSWORD="${MYSQL_PASSWORD:-123456}"; MYSQL_DATABASE="${MYSQL_DATABASE:-lj-06}"  #数据库配置
TARGET_VERSION="${1:-1.2.15}"; CURRENT_VERSION=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep ljwx-mysql | head -1 | cut -d: -f2 2>/dev/null || echo "unknown")  #版本信息
MIN_DISK_GB=5; MIN_MEMORY_GB=2; BACKUP_SIZE_THRESHOLD=1  #最小资源要求

# 颜色和日志
G='\033[0;32m'; Y='\033[1;33m'; R='\033[0;31m'; N='\033[0m'  #颜色代码
log() { echo -e "${G}[CHECK]${N} $1"; }; warn() { echo -e "${Y}[WARN]${N} $1"; }; error() { echo -e "${R}[FAIL]${N} $1"; }  #日志函数

# 检查项计数器
pass=0; warn_count=0; fail=0  #计数器初始化

# 检查函数模板
check() { local msg="$1" cmd="$2" fix="$3"; echo -n "🔍 $msg... "; if eval "$cmd" &>/dev/null; then echo -e "${G}✅${N}"; ((pass++)); else echo -e "${R}❌${N}"; echo "   💡 修复建议: $fix"; ((fail++)); fi; }  #检查模板

# 检查Docker环境
check_docker() {
    log "检查Docker环境"
    check "Docker服务运行" "docker info" "启动Docker服务: sudo systemctl start docker"
    check "Docker Compose可用" "docker-compose --version" "安装Docker Compose: sudo apt install docker-compose"
    check "当前用户Docker权限" "docker ps" "添加用户到docker组: sudo usermod -aG docker \$USER"
}

# 检查系统资源
check_resources() {
    log "检查系统资源"
    local disk_free=$(df . | awk 'NR==2{print int($4/1024/1024)}')  #可用磁盘空间GB
    local memory_total=$(free -g | awk 'NR==2{print $2}')  #总内存GB
    local cpu_cores=$(nproc)  #CPU核心数
    
    check "磁盘空间充足(需要${MIN_DISK_GB}GB)" "[ $disk_free -ge $MIN_DISK_GB ]" "清理磁盘空间: docker system prune -af"
    check "内存充足(需要${MIN_MEMORY_GB}GB)" "[ $memory_total -ge $MIN_MEMORY_GB ]" "增加系统内存或关闭其他服务"
    check "CPU核心充足(需要2核)" "[ $cpu_cores -ge 2 ]" "升级CPU配置"
    
    echo "   📊 系统资源: ${disk_free}GB磁盘 | ${memory_total}GB内存 | ${cpu_cores}核CPU"
}

# 检查MySQL状态
check_mysql() {
    log "检查MySQL容器状态"
    check "MySQL容器运行" "docker ps --format '{{.Names}}' | grep -q '^$MYSQL_CONTAINER$'" "启动MySQL: docker-compose up -d mysql"
    check "MySQL服务响应" "docker exec $MYSQL_CONTAINER mysqladmin ping -u$MYSQL_USER -p$MYSQL_PASSWORD" "检查MySQL配置和网络"
    check "数据库连接正常" "docker exec $MYSQL_CONTAINER mysql -u$MYSQL_USER -p$MYSQL_PASSWORD -e 'SELECT 1' $MYSQL_DATABASE" "检查数据库权限和配置"
    
    # 获取数据库大小
    local db_size=$(docker exec $MYSQL_CONTAINER mysql -u$MYSQL_USER -p$MYSQL_PASSWORD -e "SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'DB_SIZE_MB' FROM information_schema.tables WHERE table_schema='$MYSQL_DATABASE';" -s -N 2>/dev/null || echo "0")
    echo "   📊 数据库大小: ${db_size}MB"
    [[ $(echo "$db_size > 1000" | bc -l 2>/dev/null || echo 0) -eq 1 ]] && warn "数据库较大,升级可能需要更长时间"
}

# 检查版本兼容性
check_version() {
    log "检查版本兼容性"
    check "当前版本有效" "[ '$CURRENT_VERSION' != 'unknown' ]" "确认MySQL容器正在运行"
    check "目标版本不同" "[ '$CURRENT_VERSION' != '$TARGET_VERSION' ]" "指定不同的目标版本"
    
    # 检查升级路径
    local current_major=$(echo $CURRENT_VERSION | cut -d. -f1)
    local current_minor=$(echo $CURRENT_VERSION | cut -d. -f2)
    local target_major=$(echo $TARGET_VERSION | cut -d. -f1)
    local target_minor=$(echo $TARGET_VERSION | cut -d. -f2)
    
    check "主版本兼容" "[ $current_major -eq $target_major ]" "跨主版本升级需要特殊处理"
    
    echo "   📊 版本路径: $CURRENT_VERSION → $TARGET_VERSION"
}

# 检查备份空间
check_backup() {
    log "检查备份配置"
    check "备份目录存在" "[ -d backup ]" "创建备份目录: mkdir -p backup/mysql"
    check "备份目录可写" "[ -w backup ]" "修改备份目录权限: chmod 755 backup"
    
    # 估算备份空间需求
    local data_size=$(docker exec $MYSQL_CONTAINER du -sm /var/lib/mysql 2>/dev/null | cut -f1 || echo "100")
    local required_space=$((data_size * 3))  #备份需要3倍数据大小空间
    local available_space=$(df backup | awk 'NR==2{print int($4/1024)}')
    
    check "备份空间充足" "[ $available_space -ge $required_space ]" "清理备份目录或增加磁盘空间"
    echo "   📊 需要空间: ${required_space}MB | 可用空间: ${available_space}MB"
}

# 检查依赖服务
check_dependencies() {
    log "检查服务依赖"
    local services=(ljwx-boot ljwx-bigscreen ljwx-admin redis)
    for svc in "${services[@]}"; do
        if docker ps --format "{{.Names}}" | grep -q "^$svc$"; then
            check "$svc 服务运行中" "true" ""
        else
            warn "$svc 服务未运行"
            ((warn_count++))
        fi
    done
}

# 检查网络连通性
check_network() {
    log "检查网络连通性"
    check "镜像仓库可达" "docker pull alpine:latest" "检查网络连接和DNS配置"
    check "容器网络正常" "docker network ls | grep -q client-deployment" "重新创建网络: docker-compose down && docker-compose up -d"
}

# 检查配置文件
check_config() {
    log "检查配置文件"
    check "docker-compose.yml存在" "[ -f docker-compose.yml ]" "确认在正确的目录下运行"
    check "custom-config.env存在" "[ -f custom-config.env ]" "复制配置模板: cp custom-config.env.example custom-config.env"
    check "MySQL配置有效" "grep -q 'MYSQL_PASSWORD' custom-config.env" "检查MySQL配置参数"
}

# 生成预检查报告
generate_report() {
    echo
    echo "======================================"
    echo "📋 MySQL升级预检查报告"
    echo "======================================"
    echo "检查时间: $(date)"
    echo "当前版本: $CURRENT_VERSION"
    echo "目标版本: $TARGET_VERSION"
    echo
    echo "检查结果:"
    echo "  ✅ 通过: $pass 项"
    echo "  ⚠️  警告: $warn_count 项"
    echo "  ❌ 失败: $fail 项"
    echo
    
    if [[ $fail -eq 0 ]]; then
        echo -e "${G}🎉 预检查通过,可以开始升级!${N}"
        echo "💡 建议执行: ./mysql-upgrade-manager.sh $TARGET_VERSION"
        echo
        echo "升级前最终确认清单:"
        echo "□ 已通知用户系统将维护"
        echo "□ 已准备足够的维护时间窗口"
        echo "□ 已确认回滚计划"
        echo "□ 已备份重要配置文件"
        return 0
    else
        echo -e "${R}❌ 预检查未通过,请修复问题后重试${N}"
        return 1
    fi
}

# 主函数
main() {
    echo "🚀 MySQL升级预检查器启动"
    echo "当前版本: $CURRENT_VERSION → 目标版本: $TARGET_VERSION"
    echo
    
    check_docker
    check_resources
    check_mysql
    check_version
    check_backup
    check_dependencies
    check_network
    check_config
    
    generate_report
}

# 执行主函数
main "$@" 

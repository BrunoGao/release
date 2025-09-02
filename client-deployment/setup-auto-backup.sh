#!/bin/bash
# 自动化备份设置脚本 - 跨平台版

# 颜色
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

# 检测操作系统
detect_os() {
    case "$(uname -s)" in
        Darwin) OS="macOS" ;;
        Linux) 
            if [ -f /etc/centos-release ]; then OS="CentOS"
            elif [ -f /etc/ubuntu-release ] || grep -q "Ubuntu" /etc/os-release 2>/dev/null; then OS="Ubuntu"
            else OS="Linux"; fi ;;
        *) OS="Unknown" ;;
    esac
}

log() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 检查依赖
check_dependencies() {
    log "🔍 检查系统依赖..."
    
    if ! command -v docker >/dev/null 2>&1; then
        error "Docker未安装或未启动"
        exit 1
    fi
    
    case "$OS" in
        macOS)
            if ! command -v launchctl >/dev/null 2>&1; then
                error "launchctl不可用"
                exit 1
            fi
            ;;
        CentOS|Ubuntu)
            if ! command -v crontab >/dev/null 2>&1; then
                error "crontab不可用"
                exit 1
            fi
            ;;
    esac
    
    log "✅ 系统依赖检查通过"
}

# macOS launchd 配置
setup_macos_schedule() {
    local plist_file="$HOME/Library/LaunchAgents/com.ljwx.backup.plist"
    local script_path="$(pwd)/backup-restore-manager.sh"
    
    log "📝 创建macOS定时任务配置..."
    
    cat > "$plist_file" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd"\>
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ljwx.backup</string>
    <key>ProgramArguments</key>
    <array>
        <string>$script_path</string>
        <string>auto-backup</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>2</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>WorkingDirectory</key>
    <string>$(pwd)</string>
    <key>StandardOutPath</key>
    <string>$(pwd)/logs/auto-backup.log</string>
    <key>StandardErrorPath</key>
    <string>$(pwd)/logs/auto-backup-error.log</string>
</dict>
</plist>
PLIST
    
    # 加载定时任务
    launchctl unload "$plist_file" 2>/dev/null || true
    launchctl load "$plist_file"
    
    log "✅ macOS定时任务已设置 (每日凌晨2点)"
    log "📋 管理命令:"
    log "   启动: launchctl load $plist_file"
    log "   停止: launchctl unload $plist_file"
    log "   查看: launchctl list | grep ljwx"
}

# Linux crontab 配置
setup_linux_schedule() {
    local script_path="$(pwd)/backup-restore-manager.sh"
    local cron_job="0 2 * * * cd $(pwd) && $script_path auto-backup >> logs/auto-backup.log 2>&1"
    
    log "📝 添加Linux定时任务..."
    
    # 备份现有crontab
    crontab -l > /tmp/ljwx_crontab_backup 2>/dev/null || true
    
    # 检查是否已存在
    if crontab -l 2>/dev/null | grep -q "backup-restore-manager.sh auto-backup"; then
        warn "定时任务已存在，正在更新..."
        crontab -l | grep -v "backup-restore-manager.sh auto-backup" | crontab -
    fi
    
    # 添加新的定时任务
    (crontab -l 2>/dev/null; echo "$cron_job") | crontab -
    
    log "✅ Linux定时任务已设置 (每日凌晨2点)"
    log "📋 管理命令:"
    log "   查看: crontab -l"
    log "   编辑: crontab -e"
    log "   删除: crontab -l | grep -v 'backup-restore-manager' | crontab -"
}

# 测试备份功能
test_backup() {
    log "🧪 测试备份功能..."
    
    if ./backup-restore-manager.sh mysql-backup; then
        log "✅ MySQL备份测试成功"
    else
        error "❌ MySQL备份测试失败"
        return 1
    fi
    
    if ./backup-restore-manager.sh redis-backup; then
        log "✅ Redis备份测试成功"
    else
        error "❌ Redis备份测试失败"
        return 1
    fi
    
    log "🎯 备份功能测试完成"
}

# 显示使用说明
show_usage() {
    echo -e "${BLUE}
╔══════════════════════════════════════╗
║      LJWX 自动化备份设置完成         ║
╠══════════════════════════════════════╣
║ 📋 手动操作命令:                     ║
║                                      ║
║ 交互式管理:                          ║
║   ./backup-restore-manager.sh        ║
║                                      ║
║ 命令行操作:                          ║
║   ./backup-restore-manager.sh mysql-backup    ║
║   ./backup-restore-manager.sh redis-backup    ║
║   ./backup-restore-manager.sh full-backup     ║
║   ./backup-restore-manager.sh mysql-restore   ║
║   ./backup-restore-manager.sh redis-restore   ║
║   ./backup-restore-manager.sh list            ║
║   ./backup-restore-manager.sh cleanup         ║
║                                      ║
║ �� 备份目录:                         ║
║   backup/mysql/ - MySQL备份文件      ║
║   backup/redis/ - Redis备份文件      ║
║   logs/ - 日志文件                   ║
╚══════════════════════════════════════╝${NC}"
}

# 主函数
main() {
    detect_os
    echo -e "${BLUE}🚀 LJWX自动化备份设置程序 (OS: $OS)${NC}"
    
    check_dependencies
    
    # 设置脚本权限
    chmod +x backup-restore-manager.sh
    
    # 创建必要目录
    mkdir -p backup/{mysql,redis} logs
    
    # 根据操作系统设置定时任务
    case "$OS" in
        macOS)
            setup_macos_schedule
            ;;
        CentOS|Ubuntu)
            setup_linux_schedule
            ;;
        *)
            error "不支持的操作系统: $OS"
            exit 1
            ;;
    esac
    
    # 测试备份功能
    read -p "是否测试备份功能? [y/N]: " test_backup_choice
    if [[ $test_backup_choice =~ ^[Yy]$ ]]; then
        test_backup
    fi
    
    show_usage
    
    log "🎉 自动化备份设置完成！"
    log "💡 定时任务将在每天凌晨2点执行备份"
    log "📝 查看日志: tail -f logs/backup-restore.log"
}

main "$@"

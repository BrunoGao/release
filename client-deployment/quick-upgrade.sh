#!/bin/bash
# 快速升级启动脚本(支持Docker命名卷) | 使用说明: ./quick-upgrade.sh [目标版本]

TARGET_VERSION="${1:-1.2.15}"  #目标版本
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"  #脚本目录

# 颜色配置
G='\033[0;32m'; Y='\033[1;33m'; R='\033[0;31m'; B='\033[0;34m'; N='\033[0m'  #颜色代码

# 显示升级横幅
show_banner() {
    echo -e "${B}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    LJWX MySQL升级工具                       ║"
    echo "║                                                              ║"
    echo "║  专业 • 安全 • 快速 • 可回滚                                ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${N}"
    echo "目标版本: ${G}$TARGET_VERSION${N}"
    echo "升级时间: $(date)"
    echo
}

# 检查必要文件和数据卷迁移状态
check_files() {
    local files=("mysql-upgrade-checker.sh" "mysql-upgrade-manager.sh" "docker-compose.yml" "custom-config.env")
    for file in "${files[@]}"; do
        [[ ! -f "$file" ]] && { echo -e "${R}❌ 缺少文件: $file${N}"; exit 1; }
    done
    chmod +x mysql-upgrade-*.sh  #设置执行权限
    
    # 检查是否需要数据迁移
    if [ -d "data" ] || [ -d "logs" ]; then
        echo -e "${Y}⚠️  检测到旧版本bind mount数据目录${N}"
        echo "建议先执行数据迁移到Docker命名卷:"
        echo "  ./upgrade-to-named-volumes.sh"
        echo ""
        read -p "是否现在执行迁移? (y/N): " migrate_now
        if [ "$migrate_now" = "y" ] || [ "$migrate_now" = "Y" ]; then
            if [ -f "upgrade-to-named-volumes.sh" ]; then
                ./upgrade-to-named-volumes.sh
                echo "迁移完成，继续升级流程..."
            else
                echo -e "${R}❌ 未找到迁移脚本 upgrade-to-named-volumes.sh${N}"
                exit 1
            fi
        fi
    fi
}

# 用户确认
confirm_upgrade() {
    echo -e "${Y}⚠️  数据库升级重要提醒:${N}"
    echo "• 升级过程将暂停所有服务"
    echo "• 建议在业务低峰期执行"
    echo "• 确保已通知相关用户"
    echo "• 升级前将自动创建完整备份"
    echo
    read -p "$(echo -e "${Y}确认继续升级? [y/N]:${N} ")" -r
    [[ ! $REPLY =~ ^[Yy]$ ]] && { echo "升级已取消"; exit 0; }
}

# 执行升级流程
execute_upgrade() {
    echo -e "${G}🚀 开始MySQL升级流程...${N}"
    echo
    
    # 步骤1: 预检查
    echo -e "${B}步骤1/2: 执行升级前检查...${N}"
    if ! ./mysql-upgrade-checker.sh "$TARGET_VERSION"; then
        echo -e "${R}❌ 预检查失败，请修复问题后重试${N}"
        exit 1
    fi
    echo -e "${G}✅ 预检查通过${N}"
    echo
    
    # 步骤2: 执行升级
    echo -e "${B}步骤2/2: 执行数据库升级...${N}"
    if ./mysql-upgrade-manager.sh "$TARGET_VERSION"; then
        echo
        echo -e "${G}🎉 MySQL升级成功完成!${N}"
        echo -e "${G}当前版本: $TARGET_VERSION${N}"
        echo
        echo "后续建议:"
        echo "• 观察系统运行5-10分钟"
        echo "• 执行功能验证测试"
        echo "• 查看升级报告: logs/upgrade_report_*.md"
        echo "• 监控应用性能指标"
        return 0
    else
        echo -e "${R}❌ 升级失败，系统已自动回滚${N}"
        echo "请查看日志文件: logs/upgrade-*.log"
        return 1
    fi
}

# 显示使用帮助
show_help() {
    echo "MySQL数据库升级工具"
    echo
    echo "用法:"
    echo "  $0 [目标版本]"
    echo
    echo "示例:"
    echo "  $0 1.2.15        # 升级到1.2.15版本"
    echo "  $0 --help        # 显示帮助信息"
    echo
    echo "相关工具:"
    echo "  • 预检查: ./mysql-upgrade-checker.sh"
    echo "  • 手动升级: ./mysql-upgrade-manager.sh"
    echo "  • 备份恢复: ./backup-restore-manager.sh"
    echo
    echo "详细文档: MYSQL_UPGRADE_GUIDE.md"
}

# 主函数
main() {
    cd "$SCRIPT_DIR" || exit 1  #切换到脚本目录
    
    # 参数处理
    case "$1" in
        --help|-h) show_help; exit 0 ;;
        "") echo -e "${Y}请指定目标版本，如: $0 1.2.15${N}"; exit 1 ;;
    esac
    
    show_banner
    check_files
    confirm_upgrade
    execute_upgrade
}

# 脚本入口
main "$@" 

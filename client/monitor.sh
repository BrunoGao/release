#!/bin/bash
# LJWX 系统监控脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取 Docker Compose 命令
get_compose_cmd() {
    if docker compose version &> /dev/null; then
        echo "docker compose"
    else
        echo "docker-compose"
    fi
}

# 检查服务状态
check_service_status() {
    local compose_cmd
    compose_cmd=$(get_compose_cmd)
    
    echo -e "${BLUE}🔍 检查服务状态...${NC}"
    echo ""
    
    # 获取所有服务状态
    local services=("ljwx-mysql" "ljwx-redis" "ljwx-boot" "ljwx-bigscreen" "ljwx-admin")
    local all_healthy=true
    
    for service in "${services[@]}"; do
        local status
        status=$(docker inspect --format='{{.State.Status}}' "$service" 2>/dev/null || echo "not found")
        local health
        health=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}no healthcheck{{end}}' "$service" 2>/dev/null || echo "not found")
        
        printf "%-15s " "$service:"
        
        case $status in
            "running")
                if [ "$health" = "healthy" ] || [ "$health" = "no healthcheck" ]; then
                    echo -e "${GREEN}✅ 运行正常${NC}"
                else
                    echo -e "${YELLOW}⚠️  运行中 (健康检查: $health)${NC}"
                    all_healthy=false
                fi
                ;;
            "exited")
                echo -e "${RED}❌ 已停止${NC}"
                all_healthy=false
                ;;
            "not found")
                echo -e "${RED}❌ 容器不存在${NC}"
                all_healthy=false
                ;;
            *)
                echo -e "${YELLOW}⚠️  状态异常: $status${NC}"
                all_healthy=false
                ;;
        esac
    done
    
    echo ""
    if [ "$all_healthy" = true ]; then
        echo -e "${GREEN}🎉 所有服务运行正常${NC}"
    else
        echo -e "${YELLOW}⚠️  部分服务存在问题${NC}"
    fi
}

# 检查端口连通性
check_ports() {
    echo ""
    echo -e "${BLUE}🌐 检查端口连通性...${NC}"
    echo ""
    
    # 从 .env 文件读取端口配置
    if [ -f .env ]; then
        source .env
    else
        echo -e "${YELLOW}⚠️  未找到 .env 文件，使用默认端口${NC}"
        LJWX_ADMIN_PORT=80
        LJWX_BIGSCREEN_PORT=5000
        LJWX_BOOT_PORT=9998
    fi
    
    local ports=(
        "管理后台:${LJWX_ADMIN_PORT}"
        "大屏系统:${LJWX_BIGSCREEN_PORT}"
        "后端API:${LJWX_BOOT_PORT}"
    )
    
    for port_info in "${ports[@]}"; do
        local name="${port_info%:*}"
        local port="${port_info#*:}"
        
        printf "%-10s " "${name}:"
        
        if curl -f -s --max-time 5 "http://localhost:${port}" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ 端口 ${port} 可访问${NC}"
        else
            echo -e "${RED}❌ 端口 ${port} 不可访问${NC}"
        fi
    done
}

# 检查资源使用情况
check_resources() {
    echo ""
    echo -e "${BLUE}📊 检查资源使用情况...${NC}"
    echo ""
    
    # 内存使用
    local mem_info
    mem_info=$(free -h | grep Mem:)
    local mem_used
    mem_used=$(echo "$mem_info" | awk '{print $3}')
    local mem_total
    mem_total=$(echo "$mem_info" | awk '{print $2}')
    echo -e "内存使用: ${GREEN}${mem_used}${NC} / ${mem_total}"
    
    # 磁盘使用
    local disk_info
    disk_info=$(df -h . | tail -1)
    local disk_used
    disk_used=$(echo "$disk_info" | awk '{print $3}')
    local disk_total
    disk_total=$(echo "$disk_info" | awk '{print $2}')
    local disk_percent
    disk_percent=$(echo "$disk_info" | awk '{print $5}')
    echo -e "磁盘使用: ${GREEN}${disk_used}${NC} / ${disk_total} (${disk_percent})"
    
    # Docker 容器资源使用
    echo ""
    echo -e "${BLUE}🐳 容器资源使用:${NC}"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" | grep ljwx || echo "未找到运行的容器"
}

# 检查日志错误
check_logs() {
    echo ""
    echo -e "${BLUE}📝 检查最近的错误日志...${NC}"
    echo ""
    
    local compose_cmd
    compose_cmd=$(get_compose_cmd)
    
    local services=("ljwx-boot" "ljwx-bigscreen" "ljwx-mysql" "ljwx-redis" "ljwx-admin")
    local found_errors=false
    
    for service in "${services[@]}"; do
        local errors
        errors=$($compose_cmd logs --tail=50 "$service" 2>/dev/null | grep -i "error\|exception\|failed" | tail -3 || true)
        
        if [ -n "$errors" ]; then
            echo -e "${YELLOW}⚠️  ${service} 最近错误:${NC}"
            echo "$errors" | sed 's/^/  /'
            echo ""
            found_errors=true
        fi
    done
    
    if [ "$found_errors" = false ]; then
        echo -e "${GREEN}✅ 未发现明显错误${NC}"
    fi
}

# 生成健康报告
generate_report() {
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    local report_file="health_report_$(date '+%Y%m%d_%H%M%S').txt"
    
    echo "LJWX 系统健康报告" > "$report_file"
    echo "生成时间: $timestamp" >> "$report_file"
    echo "=============================" >> "$report_file"
    echo "" >> "$report_file"
    
    # 服务状态
    echo "服务状态:" >> "$report_file"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep ljwx >> "$report_file" || echo "无运行的服务" >> "$report_file"
    echo "" >> "$report_file"
    
    # 资源使用
    echo "资源使用:" >> "$report_file"
    free -h >> "$report_file"
    echo "" >> "$report_file"
    df -h . >> "$report_file"
    echo "" >> "$report_file"
    
    # 容器资源
    echo "容器资源:" >> "$report_file"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep ljwx >> "$report_file" || echo "无运行的容器" >> "$report_file"
    
    echo -e "${GREEN}✅ 健康报告已生成: ${report_file}${NC}"
}

# 自动修复常见问题
auto_fix() {
    echo ""
    echo -e "${YELLOW}🔧 尝试自动修复常见问题...${NC}"
    
    local compose_cmd
    compose_cmd=$(get_compose_cmd)
    
    # 重启异常的容器
    local services=("ljwx-mysql" "ljwx-redis" "ljwx-boot" "ljwx-bigscreen" "ljwx-admin")
    
    for service in "${services[@]}"; do
        local status
        status=$(docker inspect --format='{{.State.Status}}' "$service" 2>/dev/null || echo "not found")
        
        if [ "$status" = "exited" ] || [ "$status" = "dead" ]; then
            echo -e "${BLUE}重启服务: ${service}${NC}"
            $compose_cmd restart "$service"
        fi
    done
    
    # 清理临时文件和缓存
    echo -e "${BLUE}清理Docker缓存...${NC}"
    docker system prune -f > /dev/null 2>&1 || true
    
    echo -e "${GREEN}✅ 自动修复完成${NC}"
}

# 显示实时监控
real_time_monitor() {
    echo -e "${BLUE}🔄 实时监控模式 (按 Ctrl+C 退出)${NC}"
    echo ""
    
    while true; do
        clear
        echo -e "${BLUE}LJWX 系统实时监控 - $(date '+%Y-%m-%d %H:%M:%S')${NC}"
        echo "======================================================"
        
        check_service_status
        check_ports
        
        echo ""
        echo -e "${BLUE}📊 容器状态:${NC}"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep -E "ljwx|NAMES" || echo "无运行的容器"
        
        echo ""
        echo -e "${YELLOW}等待30秒... (按 Ctrl+C 退出)${NC}"
        sleep 30
    done
}

# 主程序
main() {
    case "${1:-status}" in
        "status"|"check")
            check_service_status
            check_ports
            ;;
        "resources"|"res")
            check_resources
            ;;
        "logs")
            check_logs
            ;;
        "report")
            check_service_status
            check_ports
            check_resources
            check_logs
            generate_report
            ;;
        "fix")
            auto_fix
            ;;
        "monitor"|"watch")
            real_time_monitor
            ;;
        "help"|"-h"|"--help")
            echo "LJWX 系统监控脚本"
            echo ""
            echo "使用方法:"
            echo "  ./monitor.sh [command]"
            echo ""
            echo "命令:"
            echo "  status    检查服务状态 (默认)"
            echo "  resources 检查资源使用"
            echo "  logs      检查错误日志"
            echo "  report    生成健康报告"
            echo "  fix       自动修复问题"
            echo "  monitor   实时监控"
            echo "  help      显示帮助"
            ;;
        *)
            echo -e "${RED}❌ 未知命令: $1${NC}"
            echo -e "${YELLOW}使用 './monitor.sh help' 查看帮助${NC}"
            exit 1
            ;;
    esac
}

# 执行主程序
main "$@"
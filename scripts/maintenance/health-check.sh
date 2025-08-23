#!/bin/bash
# 系统健康检查脚本

BASE_DIR="/Users/brunogao/work/infra"
source "$BASE_DIR/configs/global.env" 2>/dev/null || true

# 颜色定义
G='\033[0;32m'
R='\033[0;31m'
Y='\033[1;33m'
NC='\033[0m'

log() { echo -e "${G}[OK]${NC} $1"; }
error() { echo -e "${R}[ERROR]${NC} $1"; }
warn() { echo -e "${Y}[WARN]${NC} $1"; }

echo "=== 基础服务健康检查 ==="
echo ""

# 检查Docker
if docker info >/dev/null 2>&1; then
    log "Docker服务正常"
else
    error "Docker服务异常"
    exit 1
fi

# 检查容器状态
echo "容器状态:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(jenkins|gitea|registry)"

echo ""

# 检查服务响应
services=(
    "Registry|http://localhost:35001/v2/"
    "Registry UI|http://localhost:35002"
    "Gitea|http://localhost:33000/api/healthz"
    "Jenkins|http://localhost:38080/api/json"
)

for service_info in "${services[@]}"; do
    IFS='|' read -r name url <<< "$service_info"
    if curl -s "$url" >/dev/null 2>&1; then
        log "$name 响应正常 ($url)"
    else
        error "$name 响应异常 ($url)"
    fi
done

echo ""

# 检查磁盘空间
disk_usage=$(df -h "$BASE_DIR" | awk 'NR==2{print $5}' | sed 's/%//')
if [ "$disk_usage" -gt 80 ]; then
    warn "磁盘使用率过高: ${disk_usage}%"
else
    log "磁盘空间充足: ${disk_usage}%"
fi

# 检查内存使用
memory_usage=$(docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}" | grep -E "(jenkins|gitea|registry)")
echo ""
echo "内存使用情况:"
echo "$memory_usage"

echo ""
log "健康检查完成"
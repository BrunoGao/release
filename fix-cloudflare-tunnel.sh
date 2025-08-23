#!/bin/bash
# Cloudflare Tunnel 自动修复脚本

set -e

# 颜色定义
G='\033[0;32m'
Y='\033[1;33m'
R='\033[0;31m'
B='\033[0;34m'
P='\033[0;35m'
NC='\033[0m'

log() { echo -e "${G}[INFO]${NC} $1"; }
warn() { echo -e "${Y}[WARN]${NC} $1"; }
error() { echo -e "${R}[ERROR]${NC} $1"; }
info() { echo -e "${B}[INFO]${NC} $1"; }
success() { echo -e "${P}[SUCCESS]${NC} $1"; }

echo ""
echo "============================================================"
echo -e "${P}🔧 Cloudflare Tunnel 自动修复工具${NC}"
echo "============================================================"
echo ""

# 检查cloudflared是否安装
if ! command -v cloudflared &> /dev/null; then
    error "cloudflared 未安装，请先安装 cloudflared"
    exit 1
fi

# 检查tunnel配置
if [ ! -f "/Users/brunogao/.cloudflared/config.yml" ]; then
    error "Cloudflare tunnel配置文件不存在"
    exit 1
fi

log "检查当前tunnel状态..."
cloudflared tunnel info mytunnel

echo ""
log "当前DNS解析状态："
dig +short omniverseai.net | head -3

echo ""
warn "❗ 重要提醒："
echo "   需要在Cloudflare Dashboard中手动删除A记录："
echo "   类型: A, 名称: omniverseai.net, 值: 104.234.227.29"
echo ""
echo "   然后才能运行DNS路由命令"
echo ""

# 询问用户是否已删除A记录
read -p "是否已在Cloudflare Dashboard中删除A记录? (y/N): " confirm
if [[ $confirm != [yY] ]]; then
    warn "请先登录 https://dash.cloudflare.com"
    warn "在DNS Records中删除A记录，然后重新运行此脚本"
    exit 1
fi

echo ""
log "设置DNS路由到tunnel..."

# 设置DNS路由
domains=(
    "omniverseai.net"
    "www.omniverseai.net" 
    "jenkins.omniverseai.net"
    "registry.omniverseai.net"
)

for domain in "${domains[@]}"; do
    echo -n "设置 $domain ... "
    if cloudflared tunnel route dns mytunnel "$domain" 2>/dev/null; then
        success "✅"
    else
        warn "⚠️ 可能已存在"
    fi
done

echo ""
log "重启tunnel服务..."

# 停止现有tunnel进程
pkill -f "cloudflared tunnel run mytunnel" 2>/dev/null || true
sleep 2

# 启动tunnel
log "启动tunnel服务..."
nohup cloudflared tunnel run mytunnel > /tmp/cloudflared.log 2>&1 &
TUNNEL_PID=$!

echo ""
log "等待tunnel连接建立..."
sleep 10

# 检查tunnel状态
if ps -p $TUNNEL_PID > /dev/null; then
    success "Tunnel进程运行中 (PID: $TUNNEL_PID)"
else
    error "Tunnel启动失败，检查日志: /tmp/cloudflared.log"
    exit 1
fi

echo ""
log "验证tunnel连接..."
cloudflared tunnel info mytunnel

echo ""
log "等待DNS传播 (30秒)..."
sleep 30

echo ""
log "测试域名访问..."

test_domains=(
    "https://omniverseai.net"
    "https://www.omniverseai.net"
    "https://jenkins.omniverseai.net" 
    "https://registry.omniverseai.net"
)

for url in "${test_domains[@]}"; do
    echo -n "测试 $url ... "
    status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url" || echo "000")
    
    case $status in
        200|301|302|403)
            success "✅ ($status)"
            ;;
        522)
            warn "⚠️ 连接超时(522) - DNS可能仍在传播"
            ;;
        000)
            error "❌ 连接失败"
            ;;
        *)
            info "ℹ️ 状态码: $status"
            ;;
    esac
done

echo ""
echo "============================================================"
info "🌐 服务地址配置"
echo "============================================================"
echo "主站点:    https://omniverseai.net"
echo "WWW:       https://www.omniverseai.net"  
echo "Jenkins:   https://jenkins.omniverseai.net"
echo "Registry:  https://registry.omniverseai.net"
echo ""
echo "本地服务映射:"
echo "localhost:3001 → omniverseai.net"
echo "localhost:8081 → jenkins.omniverseai.net"
echo "localhost:5001 → registry.omniverseai.net"

echo ""
echo "============================================================"
success "🎉 Cloudflare Tunnel配置完成！"
echo "============================================================"
echo ""
warn "注意事项："
echo "• DNS传播可能需要2-10分钟完全生效"
echo "• 如果仍有522错误，请等待更长时间"
echo "• Tunnel日志位置: /tmp/cloudflared.log"
echo "• 重启tunnel命令: cloudflared tunnel run mytunnel"

echo ""
info "📋 日常管理命令："
echo "查看tunnel状态: cloudflared tunnel info mytunnel"
echo "重启tunnel:     pkill cloudflared && cloudflared tunnel run mytunnel &"
echo "查看日志:       tail -f /tmp/cloudflared.log"
echo "测试连接:       curl -I https://omniverseai.net" 
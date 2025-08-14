#!/bin/bash
# 配置模板生成脚本 #快速生成不同环境的配置文件

set -e

echo "🔧 配置文件生成器"
echo "=================="

# 获取用户输入
read -p "请输入服务器IP地址 (默认: 192.168.1.83): " SERVER_IP
SERVER_IP=${SERVER_IP:-"192.168.1.83"}

read -p "请输入大屏端口 (默认: 8001): " BIGSCREEN_PORT
BIGSCREEN_PORT=${BIGSCREEN_PORT:-"8001"}

read -p "请输入公司名称 (默认: 智能科技有限公司): " COMPANY_NAME
COMPANY_NAME=${COMPANY_NAME:-"智能科技有限公司"}

read -p "请输入系统标题 (默认: 穿戴健康管理平台): " VITE_APP_TITLE
VITE_APP_TITLE=${VITE_APP_TITLE:-"穿戴健康管理平台"}

read -p "请输入大屏标题 (默认: 智能穿戴演示大屏): " BIGSCREEN_TITLE
BIGSCREEN_TITLE=${BIGSCREEN_TITLE:-"智能穿戴演示大屏"}

echo ""
echo "📋 配置信息:"
echo "- 服务器IP: $SERVER_IP"
echo "- 大屏端口: $BIGSCREEN_PORT"
echo "- 公司名称: $COMPANY_NAME"
echo "- 系统标题: $VITE_APP_TITLE"
echo "- 大屏标题: $BIGSCREEN_TITLE"
echo "- 大屏URL: http://$SERVER_IP:$BIGSCREEN_PORT"

echo ""
read -p "确认生成配置文件? (y/N): " confirm
if [[ $confirm != [yY] ]]; then
    echo "操作已取消"
    exit 0
fi

# 生成配置文件
CONFIG_FILE="custom-config.env"
if [ -f "$CONFIG_FILE" ]; then
    cp "$CONFIG_FILE" "${CONFIG_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    echo "✅ 已备份原配置文件"
fi

cat > "$CONFIG_FILE" << EOF
# 客户定制化配置文件 #统一配置文件管理所有变量
# 生成时间: $(date '+%Y-%m-%d %H:%M:%S')

# ==================== 网络配置 ====================
# 服务器IP地址 - 根据实际部署环境修改
SERVER_IP=$SERVER_IP
# 大屏服务端口 - 必须与docker-compose.yml中ljwx-bigscreen的端口一致
BIGSCREEN_PORT=$BIGSCREEN_PORT

# ==================== 大屏UI定制 ====================
# 大屏标题
BIGSCREEN_TITLE=$BIGSCREEN_TITLE
# 公司名称
COMPANY_NAME=$COMPANY_NAME
# 公司Logo路径(相对于static目录)
COMPANY_LOGO_URL=/static/images/logo.png
# 主题色(十六进制颜色代码)
THEME_COLOR=#1890ff
# 背景色
BACKGROUND_COLOR=#0a0e27
# 页脚文字
FOOTER_TEXT="© 2025 灵境万象"

# ==================== 管理端UI定制 ====================
# 管理端标题
VITE_APP_TITLE=$VITE_APP_TITLE
# 管理端描述
VITE_APP_DESC=$VITE_APP_TITLE
# 大屏访问地址 - ljwx-admin中跳转大屏的URL（客户端浏览器可访问）
VITE_BIGSCREEN_URL=http://$SERVER_IP:$BIGSCREEN_PORT
# 是否使用自定义Logo(true/false)
VITE_CUSTOM_LOGO=true

# ==================== 数据库配置 ====================
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=123456
MYSQL_DATABASE=lj-06

# ==================== Redis配置 ====================
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=123456
REDIS_DB=0

# ==================== 应用配置 ====================
# 大屏应用端口
APP_PORT=$BIGSCREEN_PORT
# 调试模式
DEBUG=false
# Docker环境标识
IS_DOCKER=true

# ==================== 微信配置 ====================
WECHAT_APP_ID=wx10dcc9f0235e1d77
WECHAT_APP_SECRET=b7e9088f3f5fe18a9cfb990c641138b3
WECHAT_TEMPLATE_ID=oJpIEzSJW67s-W_tDTbnB5uS1biiglLH5jcaALofujk
WECHAT_USER_OPENID=ofYhV6W_mDuDnm8lVbgVbgEMtvWc
WECHAT_ALERT_ENABLED=true
EOF

echo "✅ 配置文件已生成: $CONFIG_FILE"
echo ""
echo "📋 后续步骤:"
echo "1. 检查配置文件内容是否正确"
echo "2. 运行配置验证: ./validate-config.sh"
echo "3. 执行一键部署: ./deploy-client.sh" 

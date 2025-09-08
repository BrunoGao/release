#!/bin/bash

# ljwx-boot 健康系统API测试启动脚本
# 
# 使用方法:
# ./health_api_test.sh [options]
#
# 选项:
#   --base-url      API服务地址 (默认: http://localhost:8080)
#   --customer-id   客户ID (默认: 1)  
#   --user-id       用户ID (默认: 1001)
#   --department-id 部门ID (默认: 1)

set -e

# 默认配置
DEFAULT_BASE_URL="http://localhost:8080"
DEFAULT_AUTH_URL="http://192.168.1.83:3333/proxy-default/auth/user_name"

# 解析命令行参数
BASE_URL="$DEFAULT_BASE_URL"
AUTH_URL="$DEFAULT_AUTH_URL"

while [[ $# -gt 0 ]]; do
    case $1 in
        --base-url)
            BASE_URL="$2"
            shift 2
            ;;
        --auth-url)
            AUTH_URL="$2"
            shift 2
            ;;
        --help|-h)
            echo "ljwx-boot 健康系统API测试工具"
            echo ""
            echo "使用方法: $0 [options]"
            echo ""
            echo "选项:"
            echo "  --base-url URL        API服务地址 (默认: $DEFAULT_BASE_URL)"
            echo "  --auth-url URL        认证服务地址 (默认: $DEFAULT_AUTH_URL)"
            echo "  --help, -h            显示此帮助信息"
            echo ""
            echo "说明:"
            echo "  1. 测试工具会自动进行身份认证获取访问令牌"
            echo "  2. 自动从数据库加载真实的客户、用户、设备数据"
            echo "  3. 请确保 db_config.json 文件配置正确"
            echo ""
            echo "示例:"
            echo "  $0 --base-url http://localhost:8080"
            echo "  $0 --base-url http://192.168.1.83:8080 --auth-url http://192.168.1.83:3333/proxy-default/auth/user_name"
            exit 0
            ;;
        *)
            echo "未知参数: $1"
            echo "使用 --help 查看帮助信息"
            exit 1
            ;;
    esac
done

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 需要Python 3环境"
    exit 1
fi

# 检查必要的Python包
echo "🔍 检查Python依赖..."
if ! python3 -c "import requests" &> /dev/null; then
    echo "📦 安装requests包..."
    pip3 install requests
fi

# 显示测试配置
echo "============================================================"
echo "🚀 ljwx-boot 健康系统API测试"
echo "============================================================"
echo "🌐 API服务:  $BASE_URL"
echo "🔐 认证服务: $AUTH_URL"
echo "📊 数据源:   自动从数据库加载 (db_config.json)"
echo ""

# 检查服务可达性
echo "🔄 检查服务连接性..."
if curl -s --connect-timeout 5 "$BASE_URL" > /dev/null 2>&1; then
    echo "✅ 服务连接正常"
else
    echo "⚠️ 警告: 无法连接到服务，测试可能失败"
    read -p "是否继续测试? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ 测试已取消"
        exit 1
    fi
fi

echo ""
echo "⏱️ 开始执行测试..."

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 执行Python测试脚本
python3 "$SCRIPT_DIR/health_api_test.py" \
    --base-url "$BASE_URL" \
    --auth-url "$AUTH_URL"

echo ""
echo "🎉 测试完成！"
echo "📄 测试日志: health_api_test.log"
echo "📊 详细报告: health_api_test_report_*.json"
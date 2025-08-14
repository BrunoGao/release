#!/bin/bash
# 快速开始：一键构建和测试安全镜像

set -e

echo "🚀 LJWX BigScreen 安全镜像快速开始"
echo "=================================="

# 检查Docker环境
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker服务未启动，请启动Docker"
    exit 1
fi

echo "✅ Docker环境检查通过"

# 检查必要文件
echo ""
echo "📋 检查必要文件..."
required_files=(
    "Dockerfile.protected"
    "requirements-docker.txt"
    "run.py"
    "config.py"
    "build-secure.sh"
    "test-secure-image.sh"
)

missing_files=()
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    else
        echo "✅ $file"
    fi
done

if [ ${#missing_files[@]} -gt 0 ]; then
    echo "❌ 缺少必要文件："
    printf '  %s\n' "${missing_files[@]}"
    exit 1
fi

# 构建安全镜像
echo ""
echo "🔨 构建安全镜像..."
if ./build-secure.sh; then
    echo "✅ 镜像构建成功"
else
    echo "❌ 镜像构建失败"
    exit 1
fi

# 测试安全镜像
echo ""
echo "🧪 测试安全镜像..."
if ./test-secure-image.sh; then
    echo "✅ 安全测试通过"
else
    echo "❌ 安全测试失败"
    exit 1
fi

# 显示使用说明
echo ""
echo "🎉 安全镜像构建和测试完成！"
echo ""
echo "📋 使用说明："
echo ""
echo "1. 单独运行安全镜像："
echo "   docker run -d -p 8001:8001 --name ljwx-secure ljwx-bigscreen-secure:latest"
echo ""
echo "2. 使用安全docker-compose配置："
echo "   docker-compose -f docker-compose.secure.yml up -d"
echo ""
echo "3. 验证安全性："
echo "   # 检查源码文件（应该为0）"
echo "   docker exec ljwx-secure find /app -name '*.py' -not -path '*/__pycache__/*' -not -name 'start_app.py' | wc -l"
echo ""
echo "   # 检查运行用户"
echo "   docker exec ljwx-secure whoami"
echo ""
echo "   # 尝试查看源码（应该失败）"
echo "   docker exec ljwx-secure cat /app/config.py"
echo ""
echo "4. 推送到仓库："
echo "   docker push crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx/ljwx-bigscreen-secure:latest"
echo ""
echo "🔐 安全特性："
echo "  ✅ 源码已编译为字节码"
echo "  ✅ 原始.py文件已删除"
echo "  ✅ 使用非特权用户运行"
echo "  ✅ 只读文件系统"
echo "  ✅ 最小化权限配置"
echo ""
echo "📖 详细文档：SOURCE_PROTECTION_GUIDE.md"
echo ""
echo "⚠️  注意：保护镜像仅用于生产环境，开发调试请使用原始镜像" 
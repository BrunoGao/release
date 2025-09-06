#!/bin/bash
# 创建客户端部署包

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PACKAGE_NAME="ljwx-client-v2.0.1"
PACKAGE_DIR="${PACKAGE_NAME}"

echo -e "${BLUE}📦 创建 LJWX 客户端部署包${NC}"
echo ""

# 创建打包目录
echo -e "${YELLOW}📁 创建打包目录...${NC}"
rm -rf "$PACKAGE_DIR"
mkdir -p "$PACKAGE_DIR"

# 复制文件
echo -e "${YELLOW}📋 复制文件...${NC}"
cp start.sh "$PACKAGE_DIR/"
cp configure.sh "$PACKAGE_DIR/"
cp monitor.sh "$PACKAGE_DIR/"
cp README.md "$PACKAGE_DIR/"

# 创建示例配置文件
echo -e "${YELLOW}⚙️  创建示例配置...${NC}"
cat > "$PACKAGE_DIR/.env.example" << 'EOF'
# LJWX 系统配置示例
LJWX_VERSION=2.0.1
REGISTRY=crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx

# 数据库配置
MYSQL_ROOT_PASSWORD=123456
MYSQL_DATABASE=test
MYSQL_USER=ljwx
MYSQL_PASSWORD=123456

# 服务端口配置
LJWX_BOOT_PORT=9998
LJWX_BIGSCREEN_PORT=5000
LJWX_ADMIN_PORT=80
MYSQL_PORT=3306
REDIS_PORT=6379

# 时区配置
TZ=Asia/Shanghai

# 日志配置
LOG_LEVEL=INFO
EOF

# 创建快速开始脚本
cat > "$PACKAGE_DIR/quick-start.sh" << 'EOF'
#!/bin/bash
# LJWX 快速开始脚本

echo "🚀 LJWX 灵境万象健康管理系统 - 快速开始"
echo ""

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    echo "   安装指南: https://docs.docker.com/get-docker/"
    exit 1
fi

# 运行配置向导
if [ ! -f .env ]; then
    echo "📝 运行配置向导..."
    ./configure.sh
fi

# 启动系统
echo "🚀 启动系统..."
./start.sh

echo ""
echo "✅ 快速开始完成！"
EOF

chmod +x "$PACKAGE_DIR/quick-start.sh"

# 创建卸载脚本
cat > "$PACKAGE_DIR/uninstall.sh" << 'EOF'
#!/bin/bash
# LJWX 卸载脚本

echo "🗑️  LJWX 系统卸载"
echo ""

read -p "⚠️  这将完全删除LJWX系统和所有数据，确认继续？(yes/no): " confirm

if [ "$confirm" = "yes" ]; then
    echo "🛑 停止服务..."
    ./start.sh stop 2>/dev/null || true
    
    echo "🧹 清理系统..."
    ./start.sh clean 2>/dev/null || true
    
    echo "📁 删除配置和数据..."
    rm -rf data/ logs/ config/ backups/
    rm -f .env docker-compose.yml
    
    echo "✅ 卸载完成"
else
    echo "❌ 卸载已取消"
fi
EOF

chmod +x "$PACKAGE_DIR/uninstall.sh"

# 创建版本信息文件
cat > "$PACKAGE_DIR/VERSION" << EOF
LJWX 灵境万象健康管理系统
版本: 2.0.1
构建日期: $(date '+%Y-%m-%d')
打包时间: $(date '+%Y-%m-%d %H:%M:%S')

组件版本:
- ljwx-mysql: 2.0.1
- ljwx-redis: 2.0.1  
- ljwx-boot: 2.0.1
- ljwx-bigscreen: 2.0.1
- ljwx-admin: 2.0.1

系统要求:
- Docker 20.0+
- Docker Compose 2.0+
- 2GB+ 内存
- 10GB+ 磁盘空间
EOF

# 创建压缩包
echo -e "${YELLOW}📦 创建压缩包...${NC}"
tar -czf "${PACKAGE_NAME}.tar.gz" "$PACKAGE_DIR"

# 计算文件大小和校验和
PACKAGE_SIZE=$(du -h "${PACKAGE_NAME}.tar.gz" | cut -f1)
PACKAGE_MD5=$(md5sum "${PACKAGE_NAME}.tar.gz" | cut -d' ' -f1)

echo ""
echo -e "${GREEN}✅ 部署包创建完成！${NC}"
echo ""
echo -e "${BLUE}📦 包信息:${NC}"
echo -e "  文件名: ${GREEN}${PACKAGE_NAME}.tar.gz${NC}"
echo -e "  大小: ${GREEN}${PACKAGE_SIZE}${NC}"
echo -e "  MD5: ${GREEN}${PACKAGE_MD5}${NC}"
echo ""
echo -e "${BLUE}📋 客户部署步骤:${NC}"
echo -e "  1. 上传 ${YELLOW}${PACKAGE_NAME}.tar.gz${NC} 到客户服务器"
echo -e "  2. 解压: ${YELLOW}tar -xzf ${PACKAGE_NAME}.tar.gz${NC}"
echo -e "  3. 进入目录: ${YELLOW}cd ${PACKAGE_NAME}${NC}"
echo -e "  4. 快速开始: ${YELLOW}./quick-start.sh${NC}"
echo ""
echo -e "${BLUE}📖 详细说明请查看包内的 README.md${NC}"

# 清理临时目录
rm -rf "$PACKAGE_DIR"
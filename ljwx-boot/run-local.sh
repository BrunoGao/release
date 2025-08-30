#!/bin/bash
# LJWX Boot 本地启动脚本 - 确保使用最新代码

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

echo "==================== ljwx-boot本地启动 ===================="

# 设置数据库环境变量
export MYSQL_DATABASE=test
export MYSQL_HOST=127.0.0.1
export MYSQL_USER=root
export MYSQL_PASSWORD=123456

# 设置Redis环境变量
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_PASSWORD=123456
export REDIS_DB=1

# 强制停止现有进程
log_info "停止现有ljwx-boot进程..."
pkill -f "ljwx-boot" 2>/dev/null || true
sleep 2

# 环境检查
if ! command -v java &> /dev/null; then log_error "需要Java 21+"; exit 1; fi
if ! command -v mvn &> /dev/null; then log_error "需要Maven"; exit 1; fi

# 服务检查
log_info "检查MySQL连接..."
if ! nc -z localhost 3306 2>/dev/null; then log_error "MySQL连接失败"; exit 1; fi
log_success "MySQL连接正常"

log_info "检查Redis连接..."  
if ! nc -z localhost 6379 2>/dev/null; then log_error "Redis连接失败"; exit 1; fi
log_info "验证Redis密码..."
if ! redis-cli -a "$REDIS_PASSWORD" ping > /dev/null 2>&1; then log_error "Redis密码验证失败"; exit 1; fi
log_success "Redis连接和密码验证正常"

# 创建日志目录
mkdir -p logs

# 强制重新编译并安装到本地仓库
log_info "重新编译整个项目并安装到本地仓库（确保使用最新代码）..."
mvn clean install -DskipTests -q
log_success "项目编译完成，已安装到本地Maven仓库"

# 清理admin模块target目录确保重新编译
log_info "清理admin模块target目录..."
rm -rf ljwx-boot-admin/target
log_success "admin模块清理完成"

# 显示Maven仓库中的jar包信息
log_info "检查本地Maven仓库中的模块jar包..."
MODULES_JAR="$HOME/.m2/repository/com/ljwx/ljwx-boot-modules/1.0.6-SNAPSHOT/ljwx-boot-modules-1.0.6-SNAPSHOT.jar"
if [ -f "$MODULES_JAR" ]; then
    JAR_SIZE=$(ls -lh "$MODULES_JAR" | awk '{print $5}')
    JAR_TIME=$(ls -l "$MODULES_JAR" | awk '{print $6, $7, $8}')
    log_success "modules jar包已更新: $JAR_SIZE ($JAR_TIME)"
else
    log_warn "modules jar包不存在"
fi

# 进入admin目录并启动
cd ljwx-boot-admin

log_info "启动Spring Boot应用（使用最新代码）..."
echo ""
echo "🌟 服务地址: http://localhost:9998"
echo "📊 监控地址: http://localhost:9999/actuator/health" 
echo "📖 API文档: http://localhost:9998/doc.html"
echo "🔧 设备消息API: http://localhost:9998/t_device_message/page"
echo ""
echo "✅ 管理员过滤功能已启用 - 所有管理员消息将被过滤"
echo "🔍 调试日志已启用 - 可查看过滤详情"
echo ""
echo "按 Ctrl+C 停止服务"
echo "==================== 应用日志 ===================="

# 启动应用
mvn spring-boot:run -Dspring-boot.run.profiles=local

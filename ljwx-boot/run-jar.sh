#!/bin/bash
# ljwx-boot JAR方式运行脚本 - 使用宿主机MySQL和Redis

set -e

CONFIG_FILE=${1:-"host-config.env"} #宿主机配置文件
JAR_FILE="" #JAR文件路径

echo "==================== ljwx-boot JAR方式启动 ===================="
echo "配置文件: $CONFIG_FILE"

# 检查Java环境
check_java() {
    if ! command -v java > /dev/null 2>&1; then
        echo "❌ 错误: Java 未安装，请先安装Java 17+"
        exit 1
    fi
    
    JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2 | cut -d'.' -f1)
    if [ "$JAVA_VERSION" -lt 17 ]; then
        echo "❌ 错误: Java版本过低，需要Java 17+，当前版本: $JAVA_VERSION"
        exit 1
    fi
    echo "✅ Java版本: $JAVA_VERSION"
}

# 加载宿主机配置文件
load_config() {
    if [ -f "$CONFIG_FILE" ]; then
        echo "✅ 加载配置文件: $CONFIG_FILE"
        . "$CONFIG_FILE"
    else
        echo "⚠️  警告: 配置文件 $CONFIG_FILE 不存在，创建默认配置"
        create_default_config
        . "$CONFIG_FILE"
    fi
}

# 创建默认宿主机配置
create_default_config() {
    cat > "$CONFIG_FILE" << 'EOF'
# ljwx-boot 宿主机运行配置
export SPRING_PROFILES_ACTIVE=host

# MySQL配置 - 使用宿主机MySQL
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=123456
export MYSQL_DATABASE=lj-06

# Redis配置 - 使用宿主机Redis
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_PASSWORD=
export REDIS_DB=0

# 服务端口配置
export SERVER_PORT=9998
export MANAGEMENT_PORT=9999

# 日志配置
export LOG_LEVEL=info
export LOG_FILE=logs/ljwx-boot-host.log

# OSS配置
export OSS_NAME=local
export OSS_ENDPOINT=
export OSS_ACCESS_KEY=
export OSS_SECRET_KEY=
export OSS_BUCKET_NAME=ljwx
export OSS_LOCAL_PATH=./data/uploads

# AI服务配置（可选）
export OLLAMA_ENABLED=false
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=qwen2.5:7b

# 向量数据库配置（可选）
export PGVECTOR_USER=postgres
export PGVECTOR_PASSWORD=postgres

# JVM参数优化
export JAVA_OPTS="-Xmx2g -Xms1g -XX:MetaspaceSize=256m -XX:+UseG1GC -XX:MaxGCPauseMillis=200"
EOF
    echo "✅ 创建默认配置文件: $CONFIG_FILE"
}

# 检查宿主机服务
check_host_services() {
    echo ""
    echo "==================== 宿主机服务检查 ===================="
    
    # 检查MySQL服务
    echo -n "检查MySQL服务..."
    if command -v mysql > /dev/null 2>&1; then
        if mysql -h${MYSQL_HOST:-localhost} -P${MYSQL_PORT:-3306} -u${MYSQL_USER:-root} -p${MYSQL_PASSWORD:-123456} -e "SELECT 1;" > /dev/null 2>&1; then
            echo " ✅ MySQL连接正常"
        else
            echo " ❌ MySQL连接失败"
            echo "请确保宿主机MySQL服务已启动并配置正确"
            echo "配置: ${MYSQL_USER:-root}@${MYSQL_HOST:-localhost}:${MYSQL_PORT:-3306}/${MYSQL_DATABASE:-lj-06}"
            echo "尝试启动MySQL服务: sudo systemctl start mysql 或 brew services start mysql"
            exit 1
        fi
    else
        echo " ⚠️  MySQL客户端未安装，跳过连接检查"
    fi
    
    # 检查Redis服务
    echo -n "检查Redis服务..."
    if command -v redis-cli > /dev/null 2>&1; then
        if [ -z "${REDIS_PASSWORD}" ]; then
            REDIS_CMD="redis-cli -h ${REDIS_HOST:-localhost} -p ${REDIS_PORT:-6379} ping"
        else
            REDIS_CMD="redis-cli -h ${REDIS_HOST:-localhost} -p ${REDIS_PORT:-6379} -a ${REDIS_PASSWORD} ping"
        fi
        
        if $REDIS_CMD > /dev/null 2>&1; then
            echo " ✅ Redis连接正常"
        else
            echo " ❌ Redis连接失败"
            echo "请确保宿主机Redis服务已启动并配置正确"
            echo "配置: ${REDIS_HOST:-localhost}:${REDIS_PORT:-6379}"
            echo "尝试启动Redis服务: sudo systemctl start redis 或 brew services start redis"
            exit 1
        fi
    else
        echo " ⚠️  Redis客户端未安装，跳过连接检查"
    fi
}

# 查找JAR文件
find_jar_file() {
    echo ""
    echo "==================== 查找JAR文件 ===================="
    
    # 在target目录中查找JAR文件
    if [ -f "ljwx-boot-admin/target/ljwx-boot-admin.jar" ]; then
        JAR_FILE="ljwx-boot-admin/target/ljwx-boot-admin.jar"
    elif ls ljwx-boot-admin/target/ljwx-boot-*.jar 1> /dev/null 2>&1; then
        JAR_FILE=$(ls ljwx-boot-admin/target/ljwx-boot-*.jar | head -n 1)
    else
        echo "❌ 未找到JAR文件，开始构建..."
        build_jar
        find_jar_file
        return
    fi
    
    echo "✅ 找到JAR文件: $JAR_FILE"
}

# 构建JAR文件
build_jar() {
    echo "==================== 构建JAR文件 ===================="
    
    if ! command -v mvn > /dev/null 2>&1; then
        echo "❌ 错误: Maven 未安装，请先安装Maven"
        exit 1
    fi
    
    echo "开始Maven构建..."
    cd ljwx-boot-admin
    mvn clean package -DskipTests -q -T 1C #并行构建，跳过测试
    
    if [ $? -ne 0 ]; then
        echo "❌ Maven构建失败"
        exit 1
    fi
    
    cd ..
    echo "✅ JAR文件构建完成"
}

# 创建必要目录
create_directories() {
    echo ""
    echo "==================== 初始化环境 ===================="
    mkdir -p logs data/uploads #创建日志和上传目录
    echo "✅ 创建目录结构"
}

# 启动JAR应用
start_jar() {
    echo ""
    echo "==================== 启动应用 ===================="
    
    # 设置JVM参数
    JVM_ARGS="${JAVA_OPTS:--Xmx2g -Xms1g -XX:MetaspaceSize=256m -XX:+UseG1GC}"
    
    # 设置Spring参数
    SPRING_ARGS="-Dspring.profiles.active=${SPRING_PROFILES_ACTIVE:-host}"
    SPRING_ARGS="$SPRING_ARGS -Dserver.port=${SERVER_PORT:-9998}"
    SPRING_ARGS="$SPRING_ARGS -Dmanagement.server.port=${MANAGEMENT_PORT:-9999}"
    
    echo "JVM参数: $JVM_ARGS"
    echo "Spring参数: $SPRING_ARGS"
    echo "JAR文件: $JAR_FILE"
    echo "配置profile: ${SPRING_PROFILES_ACTIVE:-host}"
    echo ""
    echo "服务地址: http://localhost:${SERVER_PORT:-9998}"
    echo "监控地址: http://localhost:${MANAGEMENT_PORT:-9999}/actuator"
    echo "日志文件: ${LOG_FILE:-logs/ljwx-boot-host.log}"
    echo ""
    echo "按 Ctrl+C 停止服务"
    echo "==================== 应用日志 ===================="
    
    # 导出环境变量
    export SPRING_PROFILES_ACTIVE=${SPRING_PROFILES_ACTIVE:-host}
    
    # 启动应用
    java $JVM_ARGS $SPRING_ARGS -jar "$JAR_FILE"
}

# 显示帮助信息
show_help() {
    echo "用法: $0 [配置文件]"
    echo ""
    echo "参数:"
    echo "  配置文件    可选，默认为 host-config.env"
    echo ""
    echo "示例:"
    echo "  $0                    # 使用默认配置"
    echo "  $0 my-config.env      # 使用自定义配置"
    echo ""
    echo "配置文件示例变量:"
    echo "  MYSQL_HOST=localhost"
    echo "  MYSQL_PORT=3306"
    echo "  MYSQL_USER=root"
    echo "  MYSQL_PASSWORD=123456"
    echo "  REDIS_HOST=localhost"
    echo "  REDIS_PORT=6379"
}

# 主执行流程
main() {
    if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
        show_help
        exit 0
    fi
    
    check_java
    load_config
    
    echo ""
    echo "==================== 配置信息 ===================="
    echo "Spring Profile: ${SPRING_PROFILES_ACTIVE:-host}"
    echo "MySQL服务器: ${MYSQL_HOST:-localhost}:${MYSQL_PORT:-3306}"
    echo "Redis服务器: ${REDIS_HOST:-localhost}:${REDIS_PORT:-6379}"
    echo "服务端口: ${SERVER_PORT:-9998}"
    echo "监控端口: ${MANAGEMENT_PORT:-9999}"
    
    check_host_services
    create_directories
    find_jar_file
    start_jar
}

# 执行主流程
main "$@" 
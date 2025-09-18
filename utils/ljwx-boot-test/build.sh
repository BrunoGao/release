#!/bin/bash

# ljwx-boot-test 构建脚本

set -e

echo "🚀 开始构建 ljwx-boot 测试工具..."

# 检查Java环境
if ! command -v java &> /dev/null; then
    echo "❌ Java 未安装，请先安装 Java 11+"
    exit 1
fi

JAVA_VERSION=$(java -version 2>&1 | head -1 | cut -d'"' -f2 | sed '/^1\./s///' | cut -d'.' -f1)
if [ "$JAVA_VERSION" -lt 11 ]; then
    echo "❌ Java 版本过低，需要 Java 11+，当前版本: $(java -version 2>&1 | head -1)"
    exit 1
fi

# 检查Maven环境
if ! command -v mvn &> /dev/null; then
    echo "❌ Maven 未安装，请先安装 Maven"
    exit 1
fi

echo "✅ Java 版本: $(java -version 2>&1 | head -1)"
echo "✅ Maven 版本: $(mvn -version | head -1)"

# 清理之前的构建
echo "🧹 清理之前的构建..."
mvn clean

# 编译和打包
echo "🔨 编译和打包..."
mvn package -DskipTests

# 检查构建结果
JAR_FILE="target/ljwx-boot-30day-uploader.jar"
if [ -f "$JAR_FILE" ]; then
    echo "✅ 构建成功！"
    echo "📦 输出文件: $JAR_FILE"
    echo "📊 文件大小: $(ls -lh $JAR_FILE | awk '{print $5}')"
    echo ""
    echo "🚀 运行方式:"
    echo "  java -jar $JAR_FILE --help"
    echo "  java -jar $JAR_FILE --mode test"
    echo "  java -jar $JAR_FILE --mode full"
    echo ""
    
    # 创建运行脚本
    cat > run.sh << 'EOF'
#!/bin/bash
# ljwx-boot-test 运行脚本

JAR_FILE="target/ljwx-boot-30day-uploader.jar"

if [ ! -f "$JAR_FILE" ]; then
    echo "❌ JAR文件不存在，请先运行 ./build.sh"
    exit 1
fi

# 设置JVM参数
JAVA_OPTS="-Xms512m -Xmx2g -XX:+UseG1GC"

# 运行程序
echo "🚀 启动 ljwx-boot 测试工具..."
java $JAVA_OPTS -jar "$JAR_FILE" "$@"
EOF
    
    chmod +x run.sh
    echo "📝 已创建运行脚本: ./run.sh"
    echo ""
    
else
    echo "❌ 构建失败！"
    exit 1
fi

echo "🎉 构建完成！"
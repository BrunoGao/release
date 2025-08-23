#!/bin/bash
# 测试构建脚本 - 不实际部署，只检查配置

echo "🧪 测试构建脚本配置..."

BASE_DIR="/Users/brunogao/work/infra"
cd "$BASE_DIR"

# 测试1: 配置文件加载
echo "1. 测试配置文件加载..."
if source configs/global.env 2>/dev/null; then
    echo "✅ 配置文件加载成功"
    echo "   - Gitea端口: $GITEA_PORT"
    echo "   - Jenkins端口: $JENKINS_PORT"  
    echo "   - Registry端口: $REGISTRY_PORT"
else
    echo "❌ 配置文件加载失败"
    exit 1
fi

# 测试2: Docker Compose文件语法检查
echo ""
echo "2. 测试Docker Compose文件..."
compose_files=(
    "docker/compose/gitea-compose.yml"
    "docker/compose/jenkins-simple.yml"
    "docker/compose/registry.yml"
)

for file in "${compose_files[@]}"; do
    if docker-compose -f "$file" config >/dev/null 2>&1; then
        echo "✅ $file 语法正确"
    else
        echo "❌ $file 语法错误"
        docker-compose -f "$file" config 2>&1 | head -5
    fi
done

# 测试3: 端口配置检查
echo ""
echo "3. 检查端口配置..."
expected_ports=("33000:3000" "32222:22" "38080:8080" "35000:50000" "35001:5000" "35002:80")
for port_mapping in "${expected_ports[@]}"; do
    if grep -r "$port_mapping" docker/compose/ >/dev/null 2>&1; then
        echo "✅ 端口映射 $port_mapping 已配置"
    else
        echo "⚠️  端口映射 $port_mapping 未找到"
    fi
done

# 测试4: 必要目录检查
echo ""
echo "4. 检查目录结构..."
required_dirs=(
    "configs"
    "docker/compose" 
    "docker/registry/auth"
    "scripts/maintenance"
    "scripts/utils"
)

for dir in "${required_dirs[@]}"; do
    if [[ -d "$dir" ]]; then
        echo "✅ 目录 $dir 存在"
    else
        echo "❌ 目录 $dir 不存在"
    fi
done

# 测试5: 关键文件检查
echo ""
echo "5. 检查关键文件..."
required_files=(
    "build-infra.sh"
    "configs/global.env"
    "docker/compose/jenkins/casc/jenkins.yaml"
    "docker/registry/config.yml"
)

for file in "${required_files[@]}"; do
    if [[ -f "$file" ]]; then
        echo "✅ 文件 $file 存在"
    else
        echo "❌ 文件 $file 不存在"
    fi
done

echo ""
echo "🎉 配置测试完成！您现在可以运行："
echo "   ./build-infra.sh --full-auto"
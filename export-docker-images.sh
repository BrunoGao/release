#!/bin/bash

set -e

IMAGES_DIR="docker-offline-packages/docker-images"

echo "=== Docker 镜像离线导出脚本 ==="
echo ""

mkdir -p "$IMAGES_DIR"

echo "请选择导出方式:"
echo "1) 导出所有本地镜像"
echo "2) 导出指定镜像"
echo "3) 从文件导出镜像列表"
echo ""
read -p "请输入选择 (1-3): " choice

case $choice in
    1)
        echo "导出所有本地镜像..."
        images=($(docker images --format "table {{.Repository}}:{{.Tag}}" | tail -n +2 | grep -v "<none>"))
        ;;
    2)
        echo "请输入要导出的镜像名称 (多个镜像用空格分隔):"
        echo "示例: nginx:latest mysql:8.0 redis:7.0"
        read -p "镜像列表: " image_input
        images=($image_input)
        ;;
    3)
        echo "请确保存在 images.txt 文件，每行一个镜像名称"
        if [ ! -f "images.txt" ]; then
            echo "创建示例 images.txt 文件..."
            cat > images.txt << 'IMG_EOF'
# Docker镜像列表示例
# 每行一个镜像，支持注释
nginx:latest
mysql:8.0
redis:7.0
node:18-alpine
ubuntu:22.04
IMG_EOF
            echo "已创建 images.txt 示例文件，请编辑后重新运行脚本"
            exit 0
        fi
        images=($(grep -v '^#' images.txt | grep -v '^$'))
        ;;
    *)
        echo "无效选择"
        exit 1
        ;;
esac

if [ ${#images[@]} -eq 0 ]; then
    echo "没有找到要导出的镜像"
    exit 1
fi

echo ""
echo "将导出以下镜像:"
for img in "${images[@]}"; do
    echo "  - $img"
done

echo ""
read -p "确认导出? (y/N): " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "已取消"
    exit 0
fi

echo ""
echo "开始导出镜像..."

failed_images=()
success_count=0

for img in "${images[@]}"; do
    echo ""
    echo "处理镜像: $img"
    
    # 检查镜像是否存在
    if ! docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "^${img}$"; then
        echo "  警告: 镜像 $img 不存在，尝试拉取..."
        if ! docker pull "$img"; then
            echo "  错误: 无法拉取镜像 $img"
            failed_images+=("$img")
            continue
        fi
    fi
    
    # 生成文件名
    filename=$(echo "$img" | sed 's|/|_|g' | sed 's|:|_|g')
    filepath="$IMAGES_DIR/${filename}.tar"
    
    echo "  导出到: $filepath"
    if docker save "$img" > "$filepath"; then
        echo "  ✓ 导出成功"
        success_count=$((success_count + 1))
    else
        echo "  ✗ 导出失败"
        failed_images+=("$img")
        rm -f "$filepath"
    fi
done

echo ""
echo "=== 导出完成! ==="
echo "成功导出: $success_count 个镜像"

if [ ${#failed_images[@]} -gt 0 ]; then
    echo "失败镜像:"
    for img in "${failed_images[@]}"; do
        echo "  - $img"
    done
fi

echo ""
echo "导出的文件:"
ls -lh "$IMAGES_DIR"

echo ""
echo "导出文件总大小:"
du -sh "$IMAGES_DIR"

echo ""
echo "使用说明:"
echo "1. 将 docker-offline-packages 目录复制到离线服务器"
echo "2. 在离线服务器上运行: bash docker-offline-packages/import-docker-images.sh"
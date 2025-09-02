#!/bin/bash
# 设置外挂日志和数据目录脚本

echo "🚀 创建外挂目录结构..."

# 创建日志目录
mkdir -p logs/{mysql,redis,ljwx-boot,ljwx-bigscreen,ljwx-admin}

# 创建数据目录  
mkdir -p data/{mysql,redis,ljwx-boot,ljwx-bigscreen}

# 设置目录权限
chmod -R 755 logs data

echo "📁 目录结构创建完成："
echo ""
echo "logs/"
echo "├── mysql/          # MySQL日志"
echo "├── redis/          # Redis日志" 
echo "├── ljwx-boot/      # Spring Boot应用日志"
echo "├── ljwx-bigscreen/ # Python大屏应用日志"
echo "└── ljwx-admin/     # Nginx访问日志"
echo ""
echo "data/"
echo "├── mysql/          # MySQL数据文件(可选)"
echo "├── redis/          # Redis数据文件(可选)"
echo "├── ljwx-boot/      # Spring Boot应用数据"
echo "└── ljwx-bigscreen/ # Python大屏应用数据"
echo ""

echo "✅ 现在可以使用 docker-compose-enhanced.yml 启动服务"
echo "   所有日志将直接写入宿主机 ./logs 目录"
echo "   所有数据将持久化到 ./data 目录" 
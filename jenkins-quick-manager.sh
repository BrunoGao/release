#!/bin/bash

# Jenkins 快速管理脚本
# 使用方法: ./jenkins-quick-manager.sh [start|stop|restart|status|logs|test]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/docker/compose/jenkins-quick.yml"

case "${1:-help}" in
    "start")
        echo "🚀 启动 Jenkins 服务..."
        cd "${SCRIPT_DIR}/docker/compose"
        docker-compose -f jenkins-quick.yml up -d
        echo "✅ 启动完成"
        echo "📍 访问地址: http://localhost:8081"
        echo "🔐 登录信息: admin / admin123"
        ;;
        
    "stop")
        echo "⏸️ 停止 Jenkins 服务..."
        cd "${SCRIPT_DIR}/docker/compose"
        docker-compose -f jenkins-quick.yml down
        echo "✅ 停止完成"
        ;;
        
    "restart")
        echo "🔄 重启 Jenkins 服务..."
        cd "${SCRIPT_DIR}/docker/compose"
        docker-compose -f jenkins-quick.yml restart
        echo "✅ 重启完成"
        ;;
        
    "status")
        echo "📊 Jenkins 服务状态:"
        docker ps | grep jenkins-quick || echo "❌ Jenkins 服务未运行"
        echo ""
        echo "🔗 服务连接测试:"
        JENKINS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/login)
        if [ "$JENKINS_STATUS" = "200" ]; then
            echo "✅ Jenkins: 正常 (HTTP $JENKINS_STATUS)"
        else
            echo "❌ Jenkins: 异常 (HTTP $JENKINS_STATUS)"
        fi
        
        REGISTRY_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:35001/v2/)
        if [ "$REGISTRY_STATUS" = "200" ]; then
            echo "✅ Registry: 正常 (HTTP $REGISTRY_STATUS)"
        else
            echo "❌ Registry: 异常 (HTTP $REGISTRY_STATUS)"
        fi
        ;;
        
    "logs")
        echo "📋 显示 Jenkins 实时日志 (Ctrl+C 退出)..."
        docker logs jenkins-quick -f
        ;;
        
    "test")
        echo "🧪 Jenkins 自动化配置测试"
        echo ""
        echo "1️⃣ 访问 Jenkins: http://localhost:8081"
        echo "2️⃣ 使用以下凭据登录:"
        echo "   用户名: admin"
        echo "   密码:   admin123"
        echo "3️⃣ 运行预创建的 'hello-world-demo' 作业"
        echo "4️⃣ 查看作业输出验证环境配置"
        echo ""
        echo "📋 预期的测试结果:"
        echo "  ✅ Docker 版本信息显示"
        echo "  ✅ Registry 连接检查通过"
        echo "  ✅ Gitea 连接检查通过"
        echo "  ✅ 环境变量正确设置"
        ;;
        
    "health")
        echo "🏥 Jenkins 健康检查..."
        
        # 检查容器状态
        if docker ps | grep -q jenkins-quick; then
            echo "✅ Jenkins 容器运行正常"
            
            # 检查健康状态
            HEALTH=$(docker inspect jenkins-quick --format='{{.State.Health.Status}}' 2>/dev/null)
            if [ "$HEALTH" = "healthy" ]; then
                echo "✅ Jenkins 健康检查通过"
            else
                echo "⚠️ Jenkins 健康状态: $HEALTH"
            fi
        else
            echo "❌ Jenkins 容器未运行"
            return 1
        fi
        
        # 检查服务响应
        if curl -sf http://localhost:8081/login &>/dev/null; then
            echo "✅ Jenkins Web 界面正常"
        else
            echo "❌ Jenkins Web 界面无响应"
        fi
        
        # 检查磁盘使用
        DISK_USAGE=$(docker exec jenkins-quick df -h /var/jenkins_home 2>/dev/null | awk 'NR==2{print $5}' | sed 's/%//' || echo "unknown")
        if [ "$DISK_USAGE" != "unknown" ]; then
            echo "💽 Jenkins 存储使用: ${DISK_USAGE}%"
            if [ "$DISK_USAGE" -gt 80 ]; then
                echo "⚠️ 磁盘使用率较高"
            fi
        fi
        
        echo "✅ 健康检查完成"
        ;;
        
    "backup")
        echo "💾 备份 Jenkins 配置..."
        BACKUP_NAME="jenkins-quick-backup-$(date +%Y%m%d-%H%M%S)"
        BACKUP_DIR="${SCRIPT_DIR}/backup/jenkins"
        
        mkdir -p "$BACKUP_DIR"
        
        docker run --rm \
            -v compose_jenkins-quick-data:/source:ro \
            -v "$BACKUP_DIR:/backup" \
            busybox \
            tar -czf "/backup/${BACKUP_NAME}.tar.gz" -C /source .
            
        if [ $? -eq 0 ]; then
            echo "✅ 备份完成: backup/jenkins/${BACKUP_NAME}.tar.gz"
            echo "📊 备份大小: $(du -h "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" | cut -f1)"
        else
            echo "❌ 备份失败"
        fi
        ;;
        
    "help"|*)
        echo "Jenkins 快速自动化管理"
        echo ""
        echo "🚀 已成功部署 Jenkins 自动化配置！"
        echo ""
        echo "使用方法:"
        echo "  $0 start     # 启动 Jenkins 服务"
        echo "  $0 stop      # 停止 Jenkins 服务"
        echo "  $0 restart   # 重启 Jenkins 服务"
        echo "  $0 status    # 查看服务状态"
        echo "  $0 logs      # 查看实时日志"
        echo "  $0 test      # 测试说明"
        echo "  $0 health    # 健康检查"
        echo "  $0 backup    # 备份配置"
        echo ""
        echo "📍 服务访问:"
        echo "  Jenkins:   http://localhost:8081"
        echo "  Registry:  http://localhost:35001"
        echo "  Gitea:     http://192.168.1.6:3000"
        echo ""
        echo "🔐 登录信息:"
        echo "  用户名: admin"
        echo "  密码:   admin123"
        echo ""
        echo "✨ 自动化功能:"
        echo "  ✅ 跳过设置向导"
        echo "  ✅ 管理员账户自动创建"  
        echo "  ✅ Configuration as Code"
        echo "  ✅ Docker 集成配置"
        echo "  ✅ 环境变量配置"
        echo "  ✅ 示例作业预创建"
        echo "  ✅ 凭据模板配置"
        ;;
esac
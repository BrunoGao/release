#!/bin/bash
# 日志查看工具 #便捷查看各服务日志

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' #重置颜色

echo "==================== 日志查看工具 ===================="
echo "选择查看方式:"
echo "1) 容器日志 (docker logs)"
echo "2) 文件日志 (tail -f)"
echo "3) 查看所有日志目录"
echo "4) 退出"
echo ""

while true; do
    read -p "请选择查看方式 [1-4]: " log_type
    case $log_type in
        1)
            echo -e "${BLUE}📋 容器日志查看${NC}"
            echo "可用服务:"
            echo "1) ljwx-mysql"
            echo "2) ljwx-redis" 
            echo "3) ljwx-boot"
            echo "4) ljwx-bigscreen"
            echo "5) ljwx-admin"
            echo "6) 所有服务"
            echo ""
            read -p "选择服务 [1-6]: " service_choice
            case $service_choice in
                1) docker-compose logs -f ljwx-mysql ;;
                2) docker-compose logs -f ljwx-redis ;;
                3) docker-compose logs -f ljwx-boot ;;
                4) docker-compose logs -f ljwx-bigscreen ;;
                5) docker-compose logs -f ljwx-admin ;;
                6) docker-compose logs -f ;;
                *) echo -e "${RED}❌ 无效选择${NC}" ;;
            esac
            break
            ;;
        2)
            echo -e "${BLUE}📋 文件日志查看${NC}"
            echo "可用日志目录:"
            echo "1) MySQL日志: ./logs/mysql/"
            echo "2) Redis日志: ./logs/redis/"
            echo "3) 后端日志: ./logs/ljwx-boot/"
            echo "4) 大屏日志: ./logs/ljwx-bigscreen/"
            echo "5) 管理端日志: ./logs/ljwx-admin/"
            echo ""
            read -p "选择日志目录 [1-5]: " dir_choice
            case $dir_choice in
                1) 
                    if [ -d "./logs/mysql" ]; then
                        echo -e "${GREEN}📄 MySQL日志文件:${NC}"
                        ls -la ./logs/mysql/
                        echo ""
                        read -p "选择要查看的日志文件 (输入文件名或按Enter查看error.log): " mysql_log
                        mysql_log=${mysql_log:-error.log}
                        if [ -f "./logs/mysql/$mysql_log" ]; then
                            tail -f "./logs/mysql/$mysql_log"
                        else
                            echo -e "${RED}❌ 文件不存在: ./logs/mysql/$mysql_log${NC}"
                        fi
                    else
                        echo -e "${RED}❌ MySQL日志目录不存在${NC}"
                    fi
                    ;;
                2)
                    if [ -d "./logs/redis" ]; then
                        echo -e "${GREEN}📄 Redis日志文件:${NC}"
                        ls -la ./logs/redis/
                        echo ""
                        read -p "选择要查看的日志文件 (输入文件名): " redis_log
                        if [ -f "./logs/redis/$redis_log" ]; then
                            tail -f "./logs/redis/$redis_log"
                        else
                            echo -e "${RED}❌ 文件不存在: ./logs/redis/$redis_log${NC}"
                        fi
                    else
                        echo -e "${RED}❌ Redis日志目录不存在${NC}"
                    fi
                    ;;
                3)
                    if [ -d "./logs/ljwx-boot" ]; then
                        echo -e "${GREEN}📄 后端日志文件:${NC}"
                        ls -la ./logs/ljwx-boot/
                        echo ""
                        find ./logs/ljwx-boot/ -name "*.log" -type f | head -5 | while read logfile; do
                            echo "实时查看: $logfile"
                            tail -f "$logfile" &
                        done
                        wait
                    else
                        echo -e "${RED}❌ 后端日志目录不存在${NC}"
                    fi
                    ;;
                4)
                    if [ -d "./logs/ljwx-bigscreen" ]; then
                        echo -e "${GREEN}📄 大屏日志文件:${NC}"
                        ls -la ./logs/ljwx-bigscreen/
                        echo ""
                        find ./logs/ljwx-bigscreen/ -name "*.log" -type f | head -5 | while read logfile; do
                            echo "实时查看: $logfile"
                            tail -f "$logfile" &
                        done
                        wait
                    else
                        echo -e "${RED}❌ 大屏日志目录不存在${NC}"
                    fi
                    ;;
                5)
                    if [ -d "./logs/ljwx-admin" ]; then
                        echo -e "${GREEN}📄 管理端日志文件:${NC}"
                        ls -la ./logs/ljwx-admin/
                        echo ""
                        read -p "选择要查看的日志文件 (输入文件名或按Enter查看access.log): " admin_log
                        admin_log=${admin_log:-access.log}
                        if [ -f "./logs/ljwx-admin/$admin_log" ]; then
                            tail -f "./logs/ljwx-admin/$admin_log"
                        else
                            echo -e "${RED}❌ 文件不存在: ./logs/ljwx-admin/$admin_log${NC}"
                        fi
                    else
                        echo -e "${RED}❌ 管理端日志目录不存在${NC}"
                    fi
                    ;;
                *) echo -e "${RED}❌ 无效选择${NC}" ;;
            esac
            break
            ;;
        3)
            echo -e "${BLUE}📋 所有日志目录概览${NC}"
            echo ""
            for service in mysql redis ljwx-boot ljwx-bigscreen ljwx-admin; do
                if [ -d "./logs/$service" ]; then
                    echo -e "${GREEN}✅ ./logs/$service/${NC}"
                    ls -la "./logs/$service/" | head -10
                    echo ""
                else
                    echo -e "${RED}❌ ./logs/$service/ (不存在)${NC}"
                fi
            done
            echo ""
            echo "📊 磁盘使用情况:"
            du -sh ./logs/* 2>/dev/null || echo "logs目录为空"
            exit 0
            ;;
        4)
            echo "退出日志查看工具"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ 无效选择，请输入 1-4${NC}"
            ;;
    esac
done 
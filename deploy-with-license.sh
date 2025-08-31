#!/bin/bash

# LJWX 许可证系统部署脚本
# 适用于本地无外网环境

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_step "检查系统依赖..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    log_info "系统依赖检查完成"
}

# 生成硬件指纹
generate_hardware_fingerprint() {
    log_step "生成硬件指纹..."
    
    # 创建临时Java类来生成指纹
    TEMP_DIR=$(mktemp -d)
    
    cat > "$TEMP_DIR/GenerateFingerprint.java" << 'EOF'
import java.security.MessageDigest;
import java.io.BufferedReader;
import java.io.FileReader;
import java.net.NetworkInterface;
import java.util.Enumeration;

public class GenerateFingerprint {
    public static void main(String[] args) {
        try {
            StringBuilder info = new StringBuilder();
            
            // CPU信息
            try (BufferedReader br = new BufferedReader(new FileReader("/proc/cpuinfo"))) {
                String line;
                while ((line = br.readLine()) != null) {
                    if (line.startsWith("model name")) {
                        info.append(line.split(":")[1].trim());
                        break;
                    }
                }
            } catch (Exception e) {
                info.append(System.getProperty("os.arch"));
            }
            
            info.append("|");
            
            // 系统信息
            try (BufferedReader br = new BufferedReader(new FileReader("/etc/machine-id"))) {
                info.append(br.readLine().trim());
            } catch (Exception e) {
                info.append(System.getProperty("user.name"));
            }
            
            info.append("|");
            
            // MAC地址
            try {
                Enumeration<NetworkInterface> networks = NetworkInterface.getNetworkInterfaces();
                while (networks.hasMoreElements()) {
                    NetworkInterface ni = networks.nextElement();
                    byte[] mac = ni.getHardwareAddress();
                    if (mac != null && mac.length > 0) {
                        StringBuilder macStr = new StringBuilder();
                        for (byte b : mac) {
                            macStr.append(String.format("%02X", b));
                        }
                        String macAddress = macStr.toString();
                        if (!macAddress.startsWith("00505E") && !macAddress.startsWith("000C29")) {
                            info.append(macAddress);
                            break;
                        }
                    }
                }
            } catch (Exception e) {
                info.append("DEFAULT_MAC");
            }
            
            // 生成SHA256
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(info.toString().getBytes());
            StringBuilder result = new StringBuilder();
            for (byte b : hash) {
                result.append(String.format("%02X", b));
            }
            
            System.out.println(result.toString());
            
        } catch (Exception e) {
            System.err.println("生成硬件指纹失败: " + e.getMessage());
            System.exit(1);
        }
    }
}
EOF
    
    # 编译并运行
    cd "$TEMP_DIR"
    javac GenerateFingerprint.java
    HARDWARE_FINGERPRINT=$(java GenerateFingerprint)
    
    # 清理临时文件
    rm -rf "$TEMP_DIR"
    
    log_info "硬件指纹: $HARDWARE_FINGERPRINT"
    echo "$HARDWARE_FINGERPRINT" > ./hardware_fingerprint.txt
    
    log_info "硬件指纹已保存到 hardware_fingerprint.txt"
    log_warn "请将此硬件指纹提供给许可证提供商以获取许可证文件"
}

# 检查许可证文件
check_license_file() {
    log_step "检查许可证文件..."
    
    if [ ! -d "./license" ]; then
        mkdir -p ./license
        log_info "创建许可证目录: ./license"
    fi
    
    if [ ! -f "./license/ljwx.lic" ]; then
        log_error "许可证文件不存在: ./license/ljwx.lic"
        log_info "请联系供应商获取许可证文件，并将其放置在 ./license/ljwx.lic"
        
        # 创建示例��可证用于测试
        cat > "./license/ljwx.lic" << EOF
# 这是一个示例许可证文件
# 实际部署时请替换为真实的许可证文件
SAMPLE_LICENSE_FOR_TESTING
EOF
        log_warn "已创建示例许可证文件，仅用于测试目的"
        return 1
    fi
    
    log_info "许可证文件检查完成"
    return 0
}

# 配置环境变量
setup_environment() {
    log_step "配置环境变量..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.license.example" ]; then
            cp .env.license.example .env
            log_info "已复制环境变量示例文件，请编辑 .env 文件填写实际配置"
            
            # 生成随机密码
            MYSQL_ROOT_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-16)
            MYSQL_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-16)
            REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-16)
            
            # 替换密码
            sed -i "s/your_mysql_root_password/$MYSQL_ROOT_PASSWORD/g" .env
            sed -i "s/your_mysql_password/$MYSQL_PASSWORD/g" .env
            sed -i "s/your_redis_password/$REDIS_PASSWORD/g" .env
            
            log_info "已生成随机密码并配置到 .env 文件"
        else
            log_error "环境变量示例文件不存在"
            exit 1
        fi
    fi
    
    log_info "环境变量配置完成"
}

# 部署系统
deploy_system() {
    log_step "部署LJWX系统..."
    
    # 使用许可证版本的docker-compose文件
    if [ -f "docker-compose.license.yml" ]; then
        log_info "使用许可证版本配置文件..."
        docker-compose -f docker-compose.license.yml up -d
    else
        log_error "许可证配置文件不存在: docker-compose.license.yml"
        exit 1
    fi
    
    log_info "系统部署完成"
}

# 验证部署
verify_deployment() {
    log_step "验证系统部署..."
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 30
    
    # 检查容器状态
    log_info "检查容器状态..."
    docker-compose -f docker-compose.license.yml ps
    
    # 检查许可证状态
    log_info "检查许可证状态..."
    for i in {1..10}; do
        if curl -s -f http://localhost:8080/api/license/status > /dev/null; then
            log_info "许可证API响应正常"
            curl -s http://localhost:8080/api/license/status | python3 -m json.tool
            break
        else
            log_warn "等待许可证API启动... ($i/10)"
            sleep 10
        fi
    done
    
    log_info "部署验证完成"
}

# 显示使用说明
show_usage() {
    log_step "使用说明"
    echo ""
    echo "系统已成功部署，可以通过以下方式访问："
    echo ""
    echo "• 管理界面: http://localhost:3000"
    echo "• API接口: http://localhost:8080"
    echo "• 大屏系统: http://localhost:5000"
    echo ""
    echo "许可证管理API："
    echo "• 许可证状态: curl http://localhost:8080/api/license/status"
    echo "• 硬件指纹: curl http://localhost:8080/api/license/fingerprint"
    echo "• 功能检查: curl http://localhost:8080/api/license/feature/{feature_name}"
    echo ""
    echo "常用命令："
    echo "• 查看日志: docker-compose -f docker-compose.license.yml logs -f"
    echo "• 停止系统: docker-compose -f docker-compose.license.yml down"
    echo "• 重启系统: docker-compose -f docker-compose.license.yml restart"
    echo ""
}

# 主函数
main() {
    echo ""
    log_info "🚀 LJWX 许可证系统部署工具"
    echo ""
    
    # 检查参数
    case "${1:-deploy}" in
        "fingerprint")
            generate_hardware_fingerprint
            exit 0
            ;;
        "check")
            check_license_file
            exit $?
            ;;
        "deploy")
            # 执行完整部署流程
            check_dependencies
            generate_hardware_fingerprint
            
            if ! check_license_file; then
                log_error "许可证文件检查失败，请获取正式许可证后重新运行"
                exit 1
            fi
            
            setup_environment
            deploy_system
            verify_deployment
            show_usage
            ;;
        "help"|"-h"|"--help")
            echo "用法: $0 [命令]"
            echo ""
            echo "命令:"
            echo "  deploy      完整部署系统（默认）"
            echo "  fingerprint 只生成硬件指纹"
            echo "  check       只检查许可证文件"
            echo "  help        显示此帮助信息"
            echo ""
            exit 0
            ;;
        *)
            log_error "未知命令: $1"
            echo "使用 '$0 help' 查看帮助信息"
            exit 1
            ;;
    esac
    
    log_info "🎉 部署完成！"
}

# 执行主函数
main "$@"
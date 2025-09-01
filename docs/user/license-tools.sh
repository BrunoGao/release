#!/bin/bash

# 灵境万象健康管理系统 - 许可证管理工具脚本
# 版本: v1.0
# 更新时间: 2025-08-31

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目路径配置
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LICENSE_TOOL_DIR="$PROJECT_ROOT/license"
LICENSE_FILE_PATH="$PROJECT_ROOT/ljwx-boot/ljwx-boot-admin/license/ljwx.lic"
BOOT_DIR="$PROJECT_ROOT/ljwx-boot"

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

# 显示帮助信息
show_help() {
    cat << EOF
灵境万象健康管理系统 - 许可证管理工具 v1.0

使用方法:
    $0 [命令] [选项]

命令:
    generate        生成新的许可证文件
    deploy          部署许可证文件到系统目录
    verify          验证许可证文件有效性
    backup          备份当前许可证文件
    restore         从备份恢复许可证文件
    status          查看许可证状态
    fingerprint     获取当前硬件指纹
    help            显示此帮助信息

选项:
    --customer      客户名称 (默认: 灵境万象开发环境)
    --days          有效期天数 (默认: 3650, 即10年)
    --max-users     最大用户数 (默认: 1000)
    --max-devices   最大设备数 (默认: 5000)
    --max-orgs      最大组织数 (默认: 100)

示例:
    $0 generate --customer "测试客户" --days 365 --max-users 500
    $0 deploy
    $0 verify
    $0 backup
    $0 fingerprint

EOF
}

# 检查必要的目录和文件
check_prerequisites() {
    log_step "检查系统环境..."
    
    if [ ! -d "$LICENSE_TOOL_DIR" ]; then
        log_error "许可证工具目录不存在: $LICENSE_TOOL_DIR"
        exit 1
    fi
    
    if [ ! -f "$LICENSE_TOOL_DIR/LicenseGenerator.java" ]; then
        log_error "许可证生成工具不存在: $LICENSE_TOOL_DIR/LicenseGenerator.java"
        exit 1
    fi
    
    if ! command -v java &> /dev/null; then
        log_error "Java 环境未安装或未加入PATH"
        exit 1
    fi
    
    if ! command -v javac &> /dev/null; then
        log_error "Java编译器未安装或未加入PATH"
        exit 1
    fi
    
    log_info "系统环境检查通过"
}

# 获取硬件指纹
get_hardware_fingerprint() {
    log_step "获取硬件指纹..."
    
    # 切换到boot目录
    cd "$BOOT_DIR"
    
    # 启动系统获取硬件指纹（会因为许可证问题失败，但能获取指纹）
    local log_output=$(timeout 60s mvn -pl ljwx-boot-admin spring-boot:run -DskipTests -q -Dspring.profiles.active=local 2>&1 || true)
    
    # 从日志中提取硬件指纹
    local fingerprint=$(echo "$log_output" | grep -o "生成硬件指纹: [A-F0-9]\{64\}" | sed 's/生成硬件指纹: //' | head -1)
    
    if [ -z "$fingerprint" ]; then
        log_error "无法获取硬件指纹，请检查系统配置"
        log_warn "请确保MySQL和Redis服务正在运行"
        exit 1
    fi
    
    log_info "硬件指纹: $fingerprint"
    echo "$fingerprint"
}

# 生成许可证
generate_license() {
    local customer_name="${1:-灵境万象开发环境}"
    local validity_days="${2:-3650}"
    local max_users="${3:-1000}"
    local max_devices="${4:-5000}"
    local max_orgs="${5:-100}"
    
    log_step "生成许可证文件..."
    
    # 获取硬件指纹
    local fingerprint=$(get_hardware_fingerprint)
    
    # 切换到许可证工具目录
    cd "$LICENSE_TOOL_DIR"
    
    # 创建临时的生成器文件（带自定义参数）
    cat > "TempLicenseGenerator.java" << EOF
import java.io.*;
import java.net.NetworkInterface;
import java.nio.file.*;
import java.security.MessageDigest;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;
import java.util.Base64;

public class TempLicenseGenerator {
    
    public static void main(String[] args) {
        try {
            TempLicenseGenerator generator = new TempLicenseGenerator();
            
            String fingerprint = "$fingerprint";
            System.out.println("使用硬件指纹: " + fingerprint);
            
            String licenseContent = generator.generateLicenseFile(
                fingerprint, 
                "$customer_name", 
                $validity_days, 
                $max_users, 
                $max_devices, 
                $max_orgs
            );
            
            Files.write(Paths.get("ljwx.lic"), licenseContent.getBytes());
            
            System.out.println("许可证文件已生成: ljwx.lic");
            System.out.println("许可证内容长度: " + licenseContent.length());
            
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
    
    public String generateLicenseFile(String fingerprint, String customerName, int validityDays, int maxUsers, int maxDevices, int maxOrgs) throws Exception {
        
        StringBuilder licenseJson = new StringBuilder();
        licenseJson.append("{");
        licenseJson.append("\"licenseId\":\"LJWX-AUTO-").append(System.currentTimeMillis()).append("\",");
        licenseJson.append("\"customerName\":\"").append(customerName).append("\",");
        licenseJson.append("\"customerId\":\"ljwx-auto-001\",");
        licenseJson.append("\"licenseType\":\"ENTERPRISE\",");
        licenseJson.append("\"startDate\":\"").append(LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)).append("\",");
        licenseJson.append("\"endDate\":\"").append(LocalDateTime.now().plusDays(validityDays).format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)).append("\",");
        licenseJson.append("\"hardwareFingerprint\":\"").append(fingerprint).append("\",");
        licenseJson.append("\"maxUsers\":").append(maxUsers).append(",");
        licenseJson.append("\"maxDevices\":").append(maxDevices).append(",");
        licenseJson.append("\"maxOrganizations\":").append(maxOrgs).append(",");
        licenseJson.append("\"features\":[\"basic_health\",\"advanced_alert\",\"user_management\",\"device_management\",\"report_export\",\"api_access\"],");
        licenseJson.append("\"version\":\"1.0\",");
        licenseJson.append("\"createTime\":\"").append(LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)).append("\",");
        licenseJson.append("\"remarks\":\"Auto-generated License for LJWX Health Management System\"");
        licenseJson.append("}");
        
        StringBuilder containerJson = new StringBuilder();
        containerJson.append("{");
        containerJson.append("\"data\":\"").append(escapeJson(licenseJson.toString())).append("\",");
        containerJson.append("\"signature\":\"AUTO_SIGNATURE_").append(System.currentTimeMillis()).append("\",");
        containerJson.append("\"algorithm\":\"SHA256withRSA\",");
        containerJson.append("\"timestamp\":").append(System.currentTimeMillis());
        containerJson.append("}");
        
        return Base64.getEncoder().encodeToString(containerJson.toString().getBytes());
    }
    
    private String escapeJson(String str) {
        return str.replace("\\\\", "\\\\\\\\")
                  .replace("\"", "\\\\\"")
                  .replace("\n", "\\\\n")
                  .replace("\r", "\\\\r");
    }
}
EOF

    # 编译和运行生成器
    javac TempLicenseGenerator.java
    java TempLicenseGenerator
    
    # 清理临时文件
    rm -f TempLicenseGenerator.java TempLicenseGenerator.class
    
    log_info "许可证生成完成!"
    log_info "客户名称: $customer_name"
    log_info "有效期: $validity_days 天"
    log_info "最大用户数: $max_users"
    log_info "最大设备数: $max_devices"
    log_info "最大组织数: $max_orgs"
}

# 部署许可证文件
deploy_license() {
    log_step "部署许可证文件..."
    
    if [ ! -f "$LICENSE_TOOL_DIR/ljwx.lic" ]; then
        log_error "许可证文件不存在: $LICENSE_TOOL_DIR/ljwx.lic"
        log_warn "请先运行 '$0 generate' 生成许可证文件"
        exit 1
    fi
    
    # 创建目标目录
    mkdir -p "$(dirname "$LICENSE_FILE_PATH")"
    
    # 复制许可证文件
    cp "$LICENSE_TOOL_DIR/ljwx.lic" "$LICENSE_FILE_PATH"
    
    log_info "许可证文件已部署到: $LICENSE_FILE_PATH"
}

# 验证许可证
verify_license() {
    log_step "验证许可证文件..."
    
    if [ ! -f "$LICENSE_FILE_PATH" ]; then
        log_error "许可证文件不存在: $LICENSE_FILE_PATH"
        exit 1
    fi
    
    log_info "许可证文件存在"
    log_info "文件大小: $(wc -c < "$LICENSE_FILE_PATH") 字节"
    
    # 尝试启动系统进行验证
    cd "$BOOT_DIR"
    
    log_step "启动系统验证许可证..."
    timeout 60s mvn -pl ljwx-boot-admin spring-boot:run -DskipTests -q -Dspring.profiles.active=local > /tmp/license_verify.log 2>&1 || true
    
    # 检查验证结果
    if grep -q "✅ 许可证验证成功" /tmp/license_verify.log; then
        log_info "许可证验证通过!"
        grep "许可证信息:" -A 5 /tmp/license_verify.log | sed 's/^/    /'
    else
        log_error "许可证验证失败"
        if grep -q "硬件指纹不匹配" /tmp/license_verify.log; then
            log_warn "硬件指纹不匹配，请重新生成许可证"
        elif grep -q "许可证已过期" /tmp/license_verify.log; then
            log_warn "许可证已过期，请生成新的许可证"
        fi
        
        log_info "详细错误信息请查看: /tmp/license_verify.log"
    fi
}

# 备份许可证
backup_license() {
    log_step "备份许可证文件..."
    
    if [ ! -f "$LICENSE_FILE_PATH" ]; then
        log_error "许可证文件不存在，无法备份"
        exit 1
    fi
    
    local backup_dir="$PROJECT_ROOT/license/backup"
    mkdir -p "$backup_dir"
    
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_file="$backup_dir/ljwx_license_backup_$timestamp.lic"
    
    cp "$LICENSE_FILE_PATH" "$backup_file"
    
    log_info "许可证已备份到: $backup_file"
}

# 恢复许可证
restore_license() {
    local backup_dir="$PROJECT_ROOT/license/backup"
    
    log_step "恢复许可证文件..."
    
    if [ ! -d "$backup_dir" ]; then
        log_error "备份目录不存在: $backup_dir"
        exit 1
    fi
    
    # 列出可用的备份文件
    log_info "可用的备份文件:"
    local backup_files=($(ls -1t "$backup_dir"/ljwx_license_backup_*.lic 2>/dev/null || true))
    
    if [ ${#backup_files[@]} -eq 0 ]; then
        log_error "未找到备份文件"
        exit 1
    fi
    
    # 显示备份文件选项
    for i in "${!backup_files[@]}"; do
        local file_date=$(basename "${backup_files[$i]}" | sed 's/ljwx_license_backup_\(.*\)\.lic/\1/' | sed 's/_/ /')
        echo "  [$((i+1))] $file_date (${backup_files[$i]})"
    done
    
    # 用户选择
    echo -n "请选择要恢复的备份文件 [1-${#backup_files[@]}]: "
    read -r choice
    
    if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le ${#backup_files[@]} ]; then
        local selected_file="${backup_files[$((choice-1))]}"
        
        # 创建目标目录
        mkdir -p "$(dirname "$LICENSE_FILE_PATH")"
        
        # 恢复文件
        cp "$selected_file" "$LICENSE_FILE_PATH"
        
        log_info "许可证已从备份恢复: $selected_file"
    else
        log_error "无效的选择"
        exit 1
    fi
}

# 查看许可证状态
show_status() {
    log_step "查看许可证状态..."
    
    if [ ! -f "$LICENSE_FILE_PATH" ]; then
        log_warn "许可证文件不存在: $LICENSE_FILE_PATH"
        return
    fi
    
    log_info "许可证文件: $LICENSE_FILE_PATH"
    log_info "文件大小: $(wc -c < "$LICENSE_FILE_PATH") 字节"
    log_info "修改时间: $(stat -f "%Sm" "$LICENSE_FILE_PATH" 2>/dev/null || stat -c "%y" "$LICENSE_FILE_PATH" 2>/dev/null || echo "无法获取")"
    
    # 解码并显示许可证基本信息
    local decoded=$(base64 -d "$LICENSE_FILE_PATH" 2>/dev/null || echo "")
    if [ -n "$decoded" ]; then
        log_info "许可证基本信息:"
        echo "$decoded" | grep -o '"customerName":"[^"]*"' | sed 's/"customerName":"/ 客户: /' | sed 's/"$//' || echo "  无法解析客户信息"
        echo "$decoded" | grep -o '"licenseType":"[^"]*"' | sed 's/"licenseType":"/ 类型: /' | sed 's/"$//' || echo "  无法解析类型信息"
        echo "$decoded" | grep -o '"maxUsers":[0-9]*' | sed 's/"maxUsers":/ 最大用户: /' || echo "  无法解析用户限制"
        echo "$decoded" | grep -o '"maxDevices":[0-9]*' | sed 's/"maxDevices":/ 最大设备: /' || echo "  无法解析设备限制"
    fi
}

# 主函数
main() {
    case "${1:-help}" in
        generate)
            shift
            local customer_name=""
            local validity_days=""
            local max_users=""
            local max_devices=""
            local max_orgs=""
            
            while [[ $# -gt 0 ]]; do
                case $1 in
                    --customer)
                        customer_name="$2"
                        shift 2
                        ;;
                    --days)
                        validity_days="$2"
                        shift 2
                        ;;
                    --max-users)
                        max_users="$2"
                        shift 2
                        ;;
                    --max-devices)
                        max_devices="$2"
                        shift 2
                        ;;
                    --max-orgs)
                        max_orgs="$2"
                        shift 2
                        ;;
                    *)
                        log_error "未知参数: $1"
                        show_help
                        exit 1
                        ;;
                esac
            done
            
            check_prerequisites
            generate_license "$customer_name" "$validity_days" "$max_users" "$max_devices" "$max_orgs"
            ;;
        deploy)
            deploy_license
            ;;
        verify)
            verify_license
            ;;
        backup)
            backup_license
            ;;
        restore)
            restore_license
            ;;
        status)
            show_status
            ;;
        fingerprint)
            check_prerequisites
            get_hardware_fingerprint
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"
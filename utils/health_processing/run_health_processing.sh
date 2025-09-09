#!/bin/bash

# 健康数据处理执行脚本
# @Author: bruno.gao <gaojunivas@gmail.com>
# @CreateTime: 2025-01-26

set -e

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

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

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# 显示帮助信息
show_help() {
    cat << EOF
健康数据处理脚本

用法: $0 [选项]

选项:
    -h, --help              显示此帮助信息
    -c, --config FILE       指定配置文件 (默认: health_processing_config.json)
    -u, --url URL          ljwx-boot 服务地址 (默认: http://localhost:8080)
    -t, --token TOKEN      访问令牌
    -p, --personal-only    仅处理个人健康数据
    -d, --department-only  仅处理部门健康数据
    --check-env           检查环境和依赖
    --dry-run             试运行模式，仅检查配置
    --verbose             详细输出模式

示例:
    $0                                    # 使用默认配置执行完整处理
    $0 -c my_config.json                 # 使用自定义配置文件
    $0 -p                                # 仅处理个人数据
    $0 -d                                # 仅处理部门数据
    $0 -u http://192.168.1.100:8080     # 指定服务地址
    $0 --check-env                       # 检查环境
    $0 --dry-run                         # 试运行
EOF
}

# 检查Python环境
check_python() {
    log_info "检查Python环境..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装，请先安装Python3"
        return 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    log_info "Python版本: $PYTHON_VERSION"
    
    # 检查虚拟环境
    if [ ! -d "venv" ]; then
        log_warn "虚拟环境不存在，正在创建..."
        if python3 -m venv venv; then
            log_info "✅ 虚拟环境创建成功"
        else
            log_error "❌ 虚拟环境创建失败"
            return 1
        fi
    fi
    
    # 激活虚拟环境并检查模块
    if source venv/bin/activate; then
        log_info "✅ 虚拟环境激活成功"
        
        # 检查所需的Python模块
        local required_modules=("requests" "json" "logging" "datetime" "concurrent.futures")
        local missing_modules=()
        
        for module in "${required_modules[@]}"; do
            if ! python3 -c "import $module" 2>/dev/null; then
                missing_modules+=("$module")
            fi
        done
        
        if [ ${#missing_modules[@]} -ne 0 ]; then
            log_warn "缺少必需的Python模块: ${missing_modules[*]}"
            log_info "正在安装缺失模块..."
            
            if pip install requests; then
                log_info "✅ 模块安装成功"
            else
                log_error "❌ 模块安装失败"
                return 1
            fi
        fi
        
        log_info "Python环境检查通过"
        return 0
    else
        log_error "❌ 虚拟环境激活失败"
        return 1
    fi
}

# 检查ljwx-boot服务
check_ljwx_boot() {
    local base_url="$1"
    log_info "检查ljwx-boot服务: $base_url"
    
    local health_url="${base_url}/actuator/health"
    
    if curl -s --connect-timeout 10 "$health_url" > /dev/null; then
        log_info "ljwx-boot服务正常运行"
        return 0
    else
        log_warn "无法连接到ljwx-boot服务: $base_url"
        log_warn "请确保服务已启动并可访问"
        return 1
    fi
}

# 检查配置文件
check_config() {
    local config_file="$1"
    
    if [ ! -f "$config_file" ]; then
        log_error "配置文件不存在: $config_file"
        return 1
    fi
    
    # 验证JSON格式
    if ! python3 -c "import json; json.load(open('$config_file'))" 2>/dev/null; then
        log_error "配置文件格式错误: $config_file"
        return 1
    fi
    
    log_info "配置文件检查通过: $config_file"
    return 0
}

# 检查环境
check_environment() {
    local config_file="${1:-health_processing_config.json}"
    local base_url="http://localhost:8080"
    
    log_info "开始环境检查..."
    
    # 提取配置文件中的base_url
    if [ -f "$config_file" ]; then
        base_url=$(python3 -c "import json; config=json.load(open('$config_file')); print(config.get('ljwx_boot', {}).get('base_url', 'http://localhost:8080'))" 2>/dev/null || echo "http://localhost:8080")
    fi
    
    local checks_passed=0
    local total_checks=3
    
    # 1. 检查Python环境
    if check_python; then
        ((checks_passed++))
    fi
    
    # 2. 检查配置文件
    if check_config "$config_file"; then
        ((checks_passed++))
    fi
    
    # 3. 检查ljwx-boot服务
    if check_ljwx_boot "$base_url"; then
        ((checks_passed++))
    fi
    
    log_info "环境检查完成: $checks_passed/$total_checks 项通过"
    
    if [ $checks_passed -eq $total_checks ]; then
        log_info "✅ 环境检查全部通过，可以开始处理"
        return 0
    else
        log_warn "⚠️ 部分环境检查失败，建议修复后再执行"
        return 1
    fi
}

# 创建结果目录
create_output_dir() {
    local config_file="$1"
    local output_dir="./results"
    
    if [ -f "$config_file" ]; then
        output_dir=$(python3 -c "import json; config=json.load(open('$config_file')); print(config.get('output', {}).get('output_dir', './results'))" 2>/dev/null || echo "./results")
    fi
    
    if [ ! -d "$output_dir" ]; then
        mkdir -p "$output_dir"
        log_info "已创建输出目录: $output_dir"
    fi
}

# 试运行
dry_run() {
    local config_file="$1"
    shift
    local args="$@"
    
    log_info "开始试运行检查..."
    
    # 检查环境
    if ! check_environment "$config_file"; then
        log_error "环境检查失败，请修复后重试"
        return 1
    fi
    
    # 显示将要执行的命令
    log_info "将要执行的命令:"
    echo "  python3 health_processing_main.py -c '$config_file' $args"
    
    # 解析配置并显示
    if [ -f "$config_file" ]; then
        log_info "配置摘要:"
        python3 -c "
import json
config = json.load(open('$config_file'))
print(f\"  - 服务地址: {config.get('ljwx_boot', {}).get('base_url', 'N/A')}\")
print(f\"  - 个人数据处理: {'启用' if config.get('personal_processing', {}).get('enabled', False) else '禁用'}\")
print(f\"  - 部门数据处理: {'启用' if config.get('department_processing', {}).get('enabled', False) else '禁用'}\")
print(f\"  - 输出目录: {config.get('output', {}).get('output_dir', 'N/A')}\")
"
    fi
    
    log_info "✅ 试运行检查完成，配置正常"
    return 0
}

# 执行健康数据处理
run_processing() {
    local config_file="$1"
    shift
    local args="$@"
    
    log_info "开始执行健康数据处理..."
    
    # 记录开始时间
    local start_time=$(date +%s)
    
    # 创建输出目录
    create_output_dir "$config_file"
    
    # 激活虚拟环境并执行Python脚本
    if source venv/bin/activate && python3 health_processing_main.py -c "$config_file" $args; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        log_info "✅ 健康数据处理完成，耗时: ${duration}秒"
        return 0
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        log_error "❌ 健康数据处理失败，耗时: ${duration}秒"
        return 1
    fi
}

# 主函数
main() {
    local config_file="health_processing_config.json"
    local check_env_only=false
    local dry_run_only=false
    local verbose=false
    local python_args=()
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -c|--config)
                config_file="$2"
                python_args+=("-c" "$2")
                shift 2
                ;;
            -u|--url)
                python_args+=("--base-url" "$2")
                shift 2
                ;;
            -t|--token)
                python_args+=("--token" "$2")
                shift 2
                ;;
            -p|--personal-only)
                python_args+=("--personal-only")
                shift
                ;;
            -d|--department-only)
                python_args+=("--department-only")
                shift
                ;;
            --check-env)
                check_env_only=true
                shift
                ;;
            --dry-run)
                dry_run_only=true
                shift
                ;;
            --verbose)
                verbose=true
                shift
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 显示标题
    echo "=========================================="
    echo "🏥 健康数据处理系统"
    echo "=========================================="
    
    # 仅检查环境
    if [ "$check_env_only" = true ]; then
        check_environment "$config_file"
        exit $?
    fi
    
    # 试运行
    if [ "$dry_run_only" = true ]; then
        dry_run "$config_file" "${python_args[@]}"
        exit $?
    fi
    
    # 详细模式
    if [ "$verbose" = true ]; then
        set -x
    fi
    
    # 执行处理
    if ! check_environment "$config_file"; then
        log_error "环境检查失败，无法继续执行"
        exit 1
    fi
    
    if run_processing "$config_file" "${python_args[@]}"; then
        log_info "🎉 所有处理任务完成"
        exit 0
    else
        log_error "❌ 处理任务失败"
        exit 1
    fi
}

# 信号处理
trap 'log_warn "⚠️ 收到中断信号，正在清理..."; exit 130' INT TERM

# 执行主函数
main "$@"
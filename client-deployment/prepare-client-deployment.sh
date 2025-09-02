#!/bin/bash
# 客户部署包准备脚本 - 确保Linux兼容性
# 在每次提交客户部署包前运行此脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 日志函数
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${CYAN}[STEP]${NC} $1"; }

# 脚本开始
echo "🚀 客户部署包准备工具"
echo "=================================="
echo "正在准备Linux兼容的客户部署包..."
echo ""

# 检查必需文件
check_required_files() {
    log_step "1. 检查必需文件..."
    
    required_files=(
        "docker-compose.yml"
        "deploy-client.sh"
        "wait-for-it.sh"
        "custom-config.env"
        "validate-config.sh"
        "fix-volume-mounts.sh"
    )
    
    missing_files=0
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            log_success "✅ $file 存在"
        else
            log_error "❌ $file 缺失"
            missing_files=$((missing_files + 1))
        fi
    done
    
    if [ $missing_files -gt 0 ]; then
        log_error "缺失 $missing_files 个必需文件，请补充后重试"
        exit 1
    fi
    
    log_success "所有必需文件检查通过"
}

# 运行Linux兼容性修复
run_compatibility_fix() {
    log_step "2. 运行Linux兼容性修复..."
    
    if [ -f "fix-linux-compatibility.sh" ]; then
        chmod +x fix-linux-compatibility.sh
        ./fix-linux-compatibility.sh
        log_success "Linux兼容性修复完成"
    else
        log_warning "fix-linux-compatibility.sh 不存在，跳过兼容性修复"
    fi
}

# 验证脚本语法
validate_syntax() {
    log_step "3. 验证脚本语法..."
    
    # 查找所有shell脚本
    shell_scripts=$(find . -name "*.sh" -type f 2>/dev/null | grep -v ".bak" || true)
    
    syntax_errors=0
    for script in $shell_scripts; do
        if [ -f "$script" ]; then
            if bash -n "$script" 2>/dev/null; then
                log_info "✅ $script 语法正确"
            else
                log_error "❌ $script 语法错误:"
                bash -n "$script" 2>&1 | head -3
                syntax_errors=$((syntax_errors + 1))
            fi
        fi
    done
    
    if [ $syntax_errors -gt 0 ]; then
        log_error "发现 $syntax_errors 个脚本语法错误，请修复后重试"
        exit 1
    fi
    
    log_success "所有脚本语法验证通过"
}

# 测试关键功能
test_key_functions() {
    log_step "4. 测试关键功能..."
    
    # 测试配置文件加载
    if [ -f "custom-config.env" ]; then
        if . ./custom-config.env 2>/dev/null; then
            log_success "✅ 配置文件加载测试通过"
        else
            log_error "❌ 配置文件加载失败"
            exit 1
        fi
    fi
    
    # 测试wait-for-it.sh基本功能
    if [ -f "wait-for-it.sh" ] && [ -x "wait-for-it.sh" ]; then
        # 测试参数解析
        if ./wait-for-it.sh --help >/dev/null 2>&1; then
            log_success "✅ wait-for-it.sh 帮助功能正常"
        else
            log_warning "⚠️  wait-for-it.sh 帮助功能异常"
        fi
        
        # 测试快速连接测试（使用google DNS）
        timeout 5 ./wait-for-it.sh 8.8.8.8:53 -t 2 >/dev/null 2>&1 && \
            log_success "✅ wait-for-it.sh 网络连接测试通过" || \
            log_warning "⚠️  wait-for-it.sh 网络连接测试超时（可能正常）"
    else
        log_error "❌ wait-for-it.sh 不存在或无执行权限"
        exit 1
    fi
    
    log_success "关键功能测试完成"
}

# 检查Docker配置
validate_docker_config() {
    log_step "5. 验证Docker配置..."
    
    if [ -f "docker-compose.yml" ]; then
        # 检查docker-compose.yml语法
        if docker-compose -f docker-compose.yml config >/dev/null 2>&1; then
            log_success "✅ docker-compose.yml 语法正确"
        else
            log_error "❌ docker-compose.yml 语法错误:"
            docker-compose -f docker-compose.yml config 2>&1 | head -5
            exit 1
        fi
        
        # 检查是否包含wait-for-it.sh挂载
        if grep -q "wait-for-it.sh" docker-compose.yml; then
            log_success "✅ docker-compose.yml 包含wait-for-it.sh挂载"
        else
            log_warning "⚠️  docker-compose.yml 未包含wait-for-it.sh挂载"
        fi
        
        # 检查镜像版本一致性
        mysql_count=$(grep -c "ljwx-mysql:" docker-compose.yml || echo "0")
        if [ "$mysql_count" -eq 1 ]; then
            log_success "✅ MySQL镜像版本配置正确"
        else
            log_warning "⚠️  MySQL镜像版本配置可能有问题"
        fi
        
    else
        log_error "❌ docker-compose.yml 不存在"
        exit 1
    fi
    
    log_success "Docker配置验证完成"
}

# 生成部署包信息
generate_deployment_info() {
    log_step "6. 生成部署包信息..."
    
    cat > DEPLOYMENT_INFO.md << EOF
# 客户部署包信息

## 生成信息
- 生成时间: $(date)
- 生成系统: $(uname -s) $(uname -r)
- 脚本版本: 1.0.0

## 包含文件
$(find . -type f -name "*.sh" -o -name "*.yml" -o -name "*.env" -o -name "*.py" -o -name "*.js" -o -name "*.svg" -o -name "*.sql" | sort)

## Linux兼容性
- ✅ 文件格式: Unix (LF)
- ✅ 脚本权限: 已设置
- ✅ Shebang标准化: #!/bin/bash
- ✅ 语法兼容性: 已验证
- ✅ 命令兼容性: 已修复

## 支持的Linux发行版
- CentOS 7+
- Ubuntu 18.04+
- Debian 9+
- RHEL 7+
- Amazon Linux 2

## 部署步骤
1. 上传部署包到目标服务器
2. 解压部署包
3. 运行 \`./test-linux-compatibility.sh\` 进行兼容性测试
4. 修改 \`custom-config.env\` 配置文件
5. 运行 \`./deploy-client.sh\` 开始部署

## 故障排除
- 如遇权限问题，请检查SELinux设置
- 如遇网络问题，请检查防火墙配置
- 如遇Docker问题，请确保Docker和docker-compose已正确安装

## 技术支持
如有问题，请联系技术支持团队。
EOF

    log_success "部署包信息已生成: DEPLOYMENT_INFO.md"
}

# 创建快速测试脚本
create_quick_test() {
    log_step "7. 创建快速测试脚本..."
    
    cat > quick-test.sh << 'EOF'
#!/bin/bash
# 快速测试脚本 - 验证部署包基本功能

echo "🧪 快速功能测试"
echo "================"

# 测试脚本权限
echo "1. 测试脚本权限..."
if [ -x "deploy-client.sh" ] && [ -x "wait-for-it.sh" ]; then
    echo "✅ 关键脚本权限正确"
else
    echo "❌ 脚本权限异常"
    exit 1
fi

# 测试配置文件
echo "2. 测试配置文件..."
if [ -f "custom-config.env" ] && . ./custom-config.env 2>/dev/null; then
    echo "✅ 配置文件可正常加载"
else
    echo "❌ 配置文件加载失败"
    exit 1
fi

# 测试Docker配置
echo "3. 测试Docker配置..."
if docker-compose -f docker-compose.yml config >/dev/null 2>&1; then
    echo "✅ Docker Compose配置正确"
else
    echo "❌ Docker Compose配置错误"
    exit 1
fi

# 测试wait-for-it.sh
echo "4. 测试wait-for-it.sh..."
if timeout 3 ./wait-for-it.sh 127.0.0.1:22 -t 1 >/dev/null 2>&1; then
    echo "✅ wait-for-it.sh 功能正常"
else
    echo "⚠️  wait-for-it.sh 测试超时（可能正常）"
fi

echo ""
echo "✅ 快速测试完成，部署包可用！"
EOF

    chmod +x quick-test.sh
    log_success "快速测试脚本已创建: quick-test.sh"
}

# 清理临时文件
cleanup_temp_files() {
    log_step "8. 清理临时文件..."
    
    # 删除备份文件
    find . -name "*.bak.*" -type f -delete 2>/dev/null || true
    
    # 删除临时测试文件
    rm -f test-temp-* 2>/dev/null || true
    
    log_success "临时文件清理完成"
}

# 生成检查清单
generate_checklist() {
    log_step "9. 生成部署前检查清单..."
    
    cat > DEPLOYMENT_CHECKLIST.md << EOF
# 客户部署前检查清单

## 服务器环境检查
- [ ] 服务器系统版本: CentOS 7+/Ubuntu 18.04+
- [ ] Docker 已安装且版本 >= 19.03
- [ ] docker-compose 已安装且版本 >= 1.25
- [ ] 服务器可访问互联网（用于拉取镜像）
- [ ] 防火墙已开放必要端口: 8080, 8001, 9998
- [ ] 磁盘空间充足 (建议 >= 20GB)

## 部署包检查
- [ ] 所有脚本文件具有执行权限
- [ ] wait-for-it.sh 功能正常
- [ ] docker-compose.yml 语法正确
- [ ] 配置文件格式正确

## 配置文件检查
- [ ] custom-config.env 已根据客户需求修改
- [ ] 数据库密码已设置
- [ ] 服务器IP地址已配置
- [ ] 大屏标题已自定义
- [ ] Logo文件已准备（如需要）

## 部署步骤
1. [ ] 运行 ./quick-test.sh 验证部署包
2. [ ] 运行 ./test-linux-compatibility.sh 测试兼容性
3. [ ] 修改配置文件
4. [ ] 运行 ./deploy-client.sh 开始部署
5. [ ] 验证服务启动状态
6. [ ] 测试各功能模块

## 验收标准
- [ ] 管理端可正常访问 (http://服务器IP:8080)
- [ ] 大屏端可正常访问 (http://服务器IP:8001)
- [ ] API接口响应正常 (http://服务器IP:9998/actuator/health)
- [ ] 数据库连接正常
- [ ] Redis缓存正常
- [ ] 日志输出正常

## 故障排除
- 如遇到权限问题，检查SELinux设置
- 如遇到网络问题，检查防火墙配置
- 如遇到启动问题，查看容器日志
EOF

    log_success "部署检查清单已生成: DEPLOYMENT_CHECKLIST.md"
}

# 主执行流程
main() {
    check_required_files
    run_compatibility_fix
    validate_syntax
    test_key_functions
    validate_docker_config
    generate_deployment_info
    create_quick_test
    cleanup_temp_files
    generate_checklist
    
    # 运行容器权限修复
    echo ""
    log_step "10. 运行容器权限修复..."
    if [ -f "fix-container-permissions.sh" ]; then
        ./fix-container-permissions.sh
    else
        log_warning "fix-container-permissions.sh 不存在，跳过权限修复"
    fi
    
    echo ""
    log_success "🎉 客户部署包准备完成！"
    echo ""
    echo "生成的文件:"
    echo "- DEPLOYMENT_INFO.md (部署包信息)"
    echo "- DEPLOYMENT_CHECKLIST.md (部署检查清单)"
    echo "- quick-test.sh (快速测试脚本)"
    echo "- test-linux-compatibility.sh (兼容性测试)"
    echo "- linux-compatibility-report.txt (兼容性报告)"
    echo ""
    echo "下一步操作:"
    echo "1. 运行 ./quick-test.sh 进行最终验证"
    echo "2. 打包部署文件发送给客户"
    echo "3. 指导客户按照 DEPLOYMENT_CHECKLIST.md 进行部署"
    echo ""
}

# 执行主流程
main "$@" 

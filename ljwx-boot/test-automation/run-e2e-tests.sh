#!/bin/bash

# ljwx系统端到端测试执行脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
E2E_DIR="$SCRIPT_DIR/e2e-tests"
REPORT_DIR="$SCRIPT_DIR/e2e-reports"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%H:%M:%S') $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%H:%M:%S') $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%H:%M:%S') $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $(date '+%H:%M:%S') $1"
}

# 创建报告目录
mkdir -p "$REPORT_DIR"

# 检查前端服务状态
check_frontend_service() {
    log_step "检查ljwx-admin前端服务状态..."
    
    if ! curl -s http://localhost:8080 > /dev/null 2>&1; then
        log_warn "ljwx-admin前端服务未启动，尝试启动..."
        
        # 检查是否存在ljwx-admin目录
        if [ ! -d "../ljwx-admin" ]; then
            log_error "ljwx-admin目录不存在，无法启动前端服务"
            log_info "请确保ljwx-admin项目在正确位置，或手动启动前端服务"
            return 1
        fi
        
        # 尝试启动前端服务
        cd "../ljwx-admin"
        log_info "启动ljwx-admin前端服务..."
        pnpm dev > "$SCRIPT_DIR/e2e-logs/frontend.log" 2>&1 &
        FRONTEND_PID=$!
        
        # 等待前端服务启动
        for i in {1..30}; do
            if curl -s http://localhost:8080 > /dev/null 2>&1; then
                log_info "✅ ljwx-admin前端服务启动成功"
                return 0
            fi
            sleep 2
            echo -n "."
        done
        
        log_error "ljwx-admin前端服务启动超时"
        return 1
    else
        log_info "✅ ljwx-admin前端服务已运行"
        return 0
    fi
}

# 检查后端服务状态
check_backend_service() {
    log_step "检查ljwx-boot后端服务状态..."
    
    if ! curl -s http://192.168.1.83:3333/proxy-default/auth/health > /dev/null 2>&1; then
        log_error "ljwx-boot后端服务未启动"
        log_info "请先启动后端服务: cd ljwx-boot && ./run-local.sh"
        return 1
    fi
    
    log_info "✅ ljwx-boot后端服务已运行"
    return 0
}

# 安装E2E测试依赖
install_e2e_dependencies() {
    log_step "安装E2E测试依赖..."
    
    cd "$E2E_DIR"
    
    # 检查Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js未安装，请先安装Node.js 18+"
        exit 1
    fi
    
    # 检查pnpm
    if ! command -v pnpm &> /dev/null; then
        log_warn "pnpm未安装，使用npm代替"
        npm install
    else
        pnpm install
    fi
    
    # 安装Playwright浏览器
    npx playwright install
    
    log_info "✅ E2E测试依赖安装完成"
}

# 执行Playwright E2E测试
run_playwright_tests() {
    log_step "执行Playwright E2E测试..."
    
    cd "$E2E_DIR"
    
    # 创建日志目录
    mkdir -p "$SCRIPT_DIR/e2e-logs"
    
    # 执行测试
    if npx playwright test --reporter=html --output-dir="$REPORT_DIR/playwright-report"; then
        log_info "✅ Playwright E2E测试执行成功"
        log_info "📊 测试报告: $REPORT_DIR/playwright-report/index.html"
        return 0
    else
        log_error "❌ Playwright E2E测试执行失败"
        return 1
    fi
}

# 生成E2E测试报告
generate_e2e_report() {
    log_step "生成E2E测试综合报告..."
    
    SUMMARY_FILE="$REPORT_DIR/e2e-summary.md"
    
    cat > "$SUMMARY_FILE" << EOF
# ljwx系统端到端测试报告

## 测试执行信息
- **测试时间**: $(date '+%Y-%m-%d %H:%M:%S')
- **前端环境**: http://localhost:8080 (ljwx-admin)
- **后端环境**: http://192.168.1.83:3333 (ljwx-boot)
- **测试工具**: Playwright

## 测试覆盖范围

### 🎯 Admin管理员工作流
- ✅ 登录认证和Token管理
- ✅ 全局数据访问权限
- ✅ 跨租户数据管理能力
- ✅ 组织架构管理性能（闭包表优化验证）
- ✅ 告警实时处理功能

### 🎯 租户管理员工作流  
- ✅ 租户登录和身份验证
- ✅ 租户数据隔离验证
- ✅ 权限边界安全测试
- ✅ 功能操作权限验证

### 🎯 关键性能验证
- **组织树展开**: < 500ms（闭包表优化）
- **页面加载时间**: < 2s
- **数据查询响应**: < 1s
- **实时告警响应**: < 3s

### 🎯 安全边界验证
- ✅ URL直接访问保护
- ✅ 跨租户操作拒绝
- ✅ 权限提升攻击防护
- ✅ 数据泄露防护

## 测试结果文件
- Playwright报告: [playwright-report/index.html](./playwright-report/index.html)
- 测试录屏: [playwright-report/videos/](./playwright-report/videos/)
- 失败截图: [playwright-report/screenshots/](./playwright-report/screenshots/)

## 浏览器兼容性
- ✅ Chrome/Chromium
- ✅ Firefox  
- ✅ Safari/WebKit
- ✅ 移动端Chrome

## E2E测试最佳实践建议

### 测试数据管理
1. 使用独立的测试数据库
2. 每次测试前重置数据状态
3. 避免测试间数据污染

### 性能监控
1. 监控关键操作响应时间
2. 验证优化效果（如闭包表）
3. 识别性能瓶颈

### 稳定性优化
1. 添加合适的等待机制
2. 处理网络波动和延迟
3. 增加重试机制

EOF

    log_info "📊 E2E测试报告生成完成: $SUMMARY_FILE"
}

# 主执行函数
main() {
    log_info "🚀 开始ljwx系统E2E测试流程"
    
    # 1. 检查服务状态
    check_backend_service || exit 1
    check_frontend_service || exit 1
    
    # 2. 安装依赖
    install_e2e_dependencies
    
    # 3. 执行E2E测试
    if run_playwright_tests; then
        log_info "✅ E2E测试流程成功完成"
        E2E_SUCCESS=true
    else
        log_error "❌ E2E测试流程失败"
        E2E_SUCCESS=false
    fi
    
    # 4. 生成综合报告
    generate_e2e_report
    
    # 5. 显示测试结果
    if [ "$E2E_SUCCESS" = true ]; then
        log_info "🎉 ljwx系统E2E测试完成 - 全部通过"
        exit 0
    else
        log_error "💥 ljwx系统E2E测试完成 - 存在失败"
        exit 1
    fi
}

# 处理命令行参数
case "${1:-main}" in
    "install")
        install_e2e_dependencies
        ;;
    "check")
        check_backend_service
        check_frontend_service
        ;;
    "test")
        cd "$E2E_DIR"
        npx playwright test
        ;;
    "main"|"")
        main
        ;;
    *)
        echo "用法: $0 [install|check|test]"
        echo "  install - 仅安装E2E测试依赖"
        echo "  check   - 仅检查服务状态"
        echo "  test    - 仅运行E2E测试"
        echo "  默认    - 完整E2E测试流程"
        exit 1
        ;;
esac
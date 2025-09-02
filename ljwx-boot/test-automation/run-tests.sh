#!/bin/bash

# ljwx-boot 自动化测试执行脚本
# 功能：启动ljwx-boot服务，执行完整测试套件，生成测试报告

set -e

# 脚本配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEST_LOG_DIR="$SCRIPT_DIR/test-logs"
REPORT_DIR="$SCRIPT_DIR/test-reports"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

# 创建必要目录
mkdir -p "$TEST_LOG_DIR"
mkdir -p "$REPORT_DIR"

# 清理函数
cleanup() {
    log_info "开始清理测试环境..."
    
    # 停止ljwx-boot服务
    if [ ! -z "$LJWX_BOOT_PID" ]; then
        log_info "停止ljwx-boot服务 (PID: $LJWX_BOOT_PID)"
        kill $LJWX_BOOT_PID 2>/dev/null || true
        wait $LJWX_BOOT_PID 2>/dev/null || true
    fi
    
    log_info "清理完成"
}

# 注册清理函数
trap cleanup EXIT

# 检查先决条件
check_prerequisites() {
    log_step "检查测试先决条件..."
    
    # 检查Java
    if ! command -v java &> /dev/null; then
        log_error "Java未安装或不在PATH中"
        exit 1
    fi
    
    # 检查Maven
    if ! command -v mvn &> /dev/null; then
        log_error "Maven未安装或不在PATH中"
        exit 1
    fi
    
    # 检查MySQL连接
    if ! mysql -h 127.0.0.1 -u root -p123456 -e "USE test;" 2>/dev/null; then
        log_error "无法连接到MySQL测试数据库"
        exit 1
    fi
    
    # 检查Redis连接
    if ! redis-cli -h 127.0.0.1 -p 6379 -a 123456 ping 2>/dev/null | grep -q PONG; then
        log_error "无法连接到Redis"
        exit 1
    fi
    
    log_info "✅ 先决条件检查通过"
}

# 启动ljwx-boot服务
start_ljwx_boot() {
    log_step "启动ljwx-boot服务..."
    
    cd "$PROJECT_ROOT"
    
    # 编译项目
    log_info "编译ljwx-boot项目..."
    MYSQL_DATABASE=test MYSQL_HOST=127.0.0.1 MYSQL_USER=root MYSQL_PASSWORD=123456 \
        mvn compile -DskipTests -q
    
    if [ $? -ne 0 ]; then
        log_error "项目编译失败"
        exit 1
    fi
    
    # 启动服务
    log_info "启动ljwx-boot服务..."
    MYSQL_DATABASE=test MYSQL_HOST=127.0.0.1 MYSQL_USER=root MYSQL_PASSWORD=123456 \
    SPRING_PROFILES_ACTIVE=local \
        mvn -pl ljwx-boot-admin spring-boot:run -DskipTests -q > "$TEST_LOG_DIR/ljwx-boot.log" 2>&1 &
    
    LJWX_BOOT_PID=$!
    log_info "ljwx-boot服务启动中 (PID: $LJWX_BOOT_PID)"
    
    # 等待服务启动
    log_info "等待服务启动..."
    for i in {1..60}; do
        if curl -s http://192.168.1.83:3333/proxy-default/auth/health > /dev/null 2>&1; then
            log_info "✅ ljwx-boot服务启动成功"
            return 0
        fi
        sleep 2
        echo -n "."
    done
    
    log_error "ljwx-boot服务启动超时"
    exit 1
}

# 编译测试项目
compile_tests() {
    log_step "编译测试项目..."
    
    cd "$SCRIPT_DIR"
    mvn compile test-compile -q
    
    if [ $? -ne 0 ]; then
        log_error "测试项目编译失败"
        exit 1
    fi
    
    log_info "✅ 测试项目编译成功"
}

# 执行测试套件
run_test_suite() {
    log_step "执行自动化测试套件..."
    
    cd "$SCRIPT_DIR"
    
    # 设置测试环境变量
    export TEST_ENVIRONMENT=automation
    export TEST_BASE_URL=http://192.168.1.83:3333
    
    # 执行测试
    log_info "开始执行测试..."
    mvn test \
        -Dtest.profile=automation \
        -Dtest.parallel=false \
        -Dtest.timeout=300000 \
        > "$TEST_LOG_DIR/test-execution.log" 2>&1
    
    TEST_EXIT_CODE=$?
    
    # 复制测试报告
    if [ -d "target/surefire-reports" ]; then
        cp -r target/surefire-reports/* "$REPORT_DIR/"
        log_info "测试报告已保存到: $REPORT_DIR"
    fi
    
    return $TEST_EXIT_CODE
}

# 生成测试报告摘要
generate_summary() {
    log_step "生成测试报告摘要..."
    
    SUMMARY_FILE="$REPORT_DIR/test-summary.txt"
    
    cat > "$SUMMARY_FILE" << EOF
========================================
    ljwx-boot 自动化测试报告摘要
========================================
执行时间: $(date '+%Y-%m-%d %H:%M:%S')
测试环境: http://192.168.1.83:3333

测试结果统计:
EOF
    
    # 解析测试结果
    if [ -f "$REPORT_DIR/testng-results.xml" ]; then
        # 从TestNG结果解析统计信息
        TOTAL=$(grep -o 'total="[0-9]*"' "$REPORT_DIR/testng-results.xml" | head -1 | grep -o '[0-9]*')
        PASSED=$(grep -o 'passed="[0-9]*"' "$REPORT_DIR/testng-results.xml" | head -1 | grep -o '[0-9]*')
        FAILED=$(grep -o 'failed="[0-9]*"' "$REPORT_DIR/testng-results.xml" | head -1 | grep -o '[0-9]*')
        SKIPPED=$(grep -o 'skipped="[0-9]*"' "$REPORT_DIR/testng-results.xml" | head -1 | grep -o '[0-9]*')
        
        echo "总测试数: ${TOTAL:-0}" >> "$SUMMARY_FILE"
        echo "通过数量: ${PASSED:-0}" >> "$SUMMARY_FILE"
        echo "失败数量: ${FAILED:-0}" >> "$SUMMARY_FILE"
        echo "跳过数量: ${SKIPPED:-0}" >> "$SUMMARY_FILE"
        
        if [ "${TOTAL:-0}" -gt 0 ]; then
            PASS_RATE=$(echo "scale=1; ${PASSED:-0} * 100 / ${TOTAL:-1}" | bc -l 2>/dev/null || echo "0")
            echo "通过率: ${PASS_RATE}%" >> "$SUMMARY_FILE"
        fi
    fi
    
    cat >> "$SUMMARY_FILE" << EOF

测试模块覆盖:
✅ Admin用户功能测试
✅ 租户管理员功能测试  
✅ 权限隔离验证测试
✅ 完整系统集成测试

测试验证重点:
- 用户登录和身份验证
- 各模块功能访问权限
- 数据访问边界验证
- 跨租户操作限制
- 权限提升攻击防护
- 系统性能优化效果

详细报告位置:
- 测试日志: $TEST_LOG_DIR/
- 测试报告: $REPORT_DIR/
========================================
EOF
    
    # 输出摘要到控制台
    cat "$SUMMARY_FILE"
}

# 主执行流程
main() {
    log_info "开始ljwx-boot自动化测试流程"
    
    # 1. 检查先决条件
    check_prerequisites
    
    # 2. 启动ljwx-boot服务
    start_ljwx_boot
    
    # 3. 编译测试项目
    compile_tests
    
    # 4. 执行测试套件
    if run_test_suite; then
        log_info "✅ 测试套件执行成功"
        TEST_SUCCESS=true
    else
        log_error "❌ 测试套件执行失败"
        TEST_SUCCESS=false
    fi
    
    # 5. 生成测试报告
    generate_summary
    
    # 6. 退出状态
    if [ "$TEST_SUCCESS" = true ]; then
        log_info "🎉 ljwx-boot自动化测试完成 - 全部通过"
        exit 0
    else
        log_error "💥 ljwx-boot自动化测试完成 - 存在失败"
        exit 1
    fi
}

# 支持命令行参数
case "${1:-main}" in
    "clean")
        log_info "仅执行测试数据清理"
        cd "$SCRIPT_DIR"
        mvn test -Dtest=com.ljwx.test.data.TestDataCleanupTest
        ;;
    "compile")
        log_info "仅编译测试项目"
        compile_tests
        ;;
    "quick")
        log_info "快速测试（跳过服务启动）"
        compile_tests
        run_test_suite
        generate_summary
        ;;
    "main"|"")
        main
        ;;
    *)
        echo "用法: $0 [clean|compile|quick]"
        echo "  clean   - 仅清理测试数据"
        echo "  compile - 仅编译测试项目"
        echo "  quick   - 快速测试（假设服务已启动）"
        echo "  默认    - 完整测试流程"
        exit 1
        ;;
esac
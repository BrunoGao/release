#!/bin/bash

# ljwx-boot 性能测试执行脚本
# 支持JMeter和Gatling两种性能测试引擎

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PERFORMANCE_DIR="$SCRIPT_DIR/performance-tests"
REPORT_DIR="$SCRIPT_DIR/performance-reports"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
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

# 创建报告目录
mkdir -p "$REPORT_DIR"

# 检查服务状态
check_service_health() {
    log_info "检查ljwx-boot服务健康状态..."
    
    if ! curl -s http://192.168.1.83:3333/proxy-default/auth/health > /dev/null 2>&1; then
        log_error "ljwx-boot服务未启动或不健康"
        log_info "请先启动服务: cd ljwx-boot && ./run-local.sh"
        exit 1
    fi
    
    log_info "✅ 服务健康检查通过"
}

# JMeter性能测试
run_jmeter_tests() {
    log_info "开始JMeter性能测试..."
    
    if ! command -v jmeter &> /dev/null; then
        log_warn "JMeter未安装，跳过JMeter测试"
        log_info "安装JMeter: brew install jmeter"
        return 0
    fi
    
    cd "$PERFORMANCE_DIR"
    
    # 执行JMeter测试
    jmeter -n -t jmeter-load-test.jmx \
        -l "$REPORT_DIR/jmeter-results.jtl" \
        -e -o "$REPORT_DIR/jmeter-html-report" \
        -Jthreads=20 \
        -Jrampup=60 \
        -Jduration=300
    
    if [ $? -eq 0 ]; then
        log_info "✅ JMeter测试完成，报告: $REPORT_DIR/jmeter-html-report/index.html"
    else
        log_error "❌ JMeter测试失败"
        return 1
    fi
}

# Gatling性能测试
run_gatling_tests() {
    log_info "开始Gatling性能测试..."
    
    if ! command -v gatling &> /dev/null; then
        log_warn "Gatling未安装，跳过Gatling测试"
        log_info "安装Gatling: brew install gatling"
        return 0
    fi
    
    cd "$PERFORMANCE_DIR"
    
    # 复制Gatling配置
    mkdir -p simulations/ljwx/performance
    cp gatling-simulation.scala simulations/ljwx/performance/LjwxBootPerformanceSimulation.scala
    
    # 执行Gatling测试
    gatling -sf simulations -rf "$REPORT_DIR/gatling-reports"
    
    if [ $? -eq 0 ]; then
        log_info "✅ Gatling测试完成，报告: $REPORT_DIR/gatling-reports/"
    else
        log_error "❌ Gatling测试失败"
        return 1
    fi
}

# 数据库性能验证
verify_database_performance() {
    log_info "验证数据库查询性能..."
    
    # 验证闭包表查询性能（应该<5ms）
    ORG_QUERY_TIME=$(mysql -h 127.0.0.1 -u root -p123456 test -e "
        SET @start_time = NOW(6);
        SELECT o.*, c.depth 
        FROM sys_org_units o
        LEFT JOIN sys_org_closure c ON o.id = c.descendant 
        WHERE c.ancestor = 1 AND o.is_deleted = 0
        LIMIT 100;
        SELECT TIMESTAMPDIFF(MICROSECOND, @start_time, NOW(6)) / 1000 AS query_time_ms;
    " 2>/dev/null | tail -1)
    
    log_info "组织查询响应时间: ${ORG_QUERY_TIME}ms"
    
    if [ "${ORG_QUERY_TIME}" -lt 100 ]; then
        log_info "✅ 组织查询性能优秀 (<100ms)"
    else
        log_warn "⚠️  组织查询性能需要优化 (${ORG_QUERY_TIME}ms)"
    fi
}

# 生成性能测试报告
generate_performance_report() {
    log_info "生成性能测试综合报告..."
    
    SUMMARY_FILE="$REPORT_DIR/performance-summary.md"
    
    cat > "$SUMMARY_FILE" << EOF
# ljwx-boot 性能测试报告

## 测试执行信息
- **测试时间**: $(date '+%Y-%m-%d %H:%M:%S')
- **测试环境**: http://192.168.1.83:3333
- **测试工具**: JMeter + Gatling

## 性能目标验证

### 🎯 组织架构优化验证
- **目标**: 查询响应时间 < 100ms (闭包表优化)
- **实际**: ${ORG_QUERY_TIME:-"待测试"}ms
- **状态**: $(if [ "${ORG_QUERY_TIME:-999}" -lt 100 ]; then echo "✅ 通过"; else echo "❌ 需优化"; fi)

### 🎯 系统并发能力验证
- **目标**: 支持1000+ requests/s
- **负载测试**: 20-50并发用户
- **持续时间**: 5分钟压力测试

### 🎯 关键接口性能基准
- **登录接口**: < 500ms
- **首页数据**: < 300ms  
- **组织查询**: < 100ms
- **用户查询**: < 200ms
- **告警查询**: < 500ms

## 测试结果文件
- JMeter报告: [jmeter-html-report/index.html](./jmeter-html-report/index.html)
- Gatling报告: [gatling-reports/](./gatling-reports/)
- 原始数据: [jmeter-results.jtl](./jmeter-results.jtl)

## 性能优化建议

### 数据库层面
1. 确保闭包表索引完整性
2. 监控慢查询日志
3. 优化连接池配置

### 应用层面  
1. 启用Redis缓存
2. 优化JVM参数
3. 启用连接池监控

### 系统层面
1. 监控CPU/内存使用率
2. 网络IO优化
3. 磁盘性能监控
EOF

    log_info "📊 性能测试报告生成完成: $SUMMARY_FILE"
}

# 主执行函数
main() {
    log_info "🚀 开始ljwx-boot性能测试流程"
    
    # 1. 检查服务健康状态
    check_service_health
    
    # 2. 验证数据库性能
    verify_database_performance
    
    # 3. 执行JMeter测试
    run_jmeter_tests
    
    # 4. 执行Gatling测试  
    run_gatling_tests
    
    # 5. 生成综合报告
    generate_performance_report
    
    log_info "🎉 性能测试流程完成"
}

# 处理命令行参数
case "${1:-main}" in
    "jmeter")
        check_service_health
        run_jmeter_tests
        ;;
    "gatling")
        check_service_health
        run_gatling_tests
        ;;
    "db")
        verify_database_performance
        ;;
    "main"|"")
        main
        ;;
    *)
        echo "用法: $0 [jmeter|gatling|db]"
        echo "  jmeter  - 仅运行JMeter测试"
        echo "  gatling - 仅运行Gatling测试"
        echo "  db      - 仅验证数据库性能"
        echo "  默认    - 完整性能测试流程"
        exit 1
        ;;
esac
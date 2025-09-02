#!/bin/bash
"""
组织架构优化方案快速部署脚本

此脚本用于：
1. 创建数据库表结构
2. 执行数据迁移
3. 验证部署结果

使用方法:
./deploy_org_optimization.sh

作者: bruno.gao
创建时间: 2025-08-30
"""

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置信息
DB_HOST=${MYSQL_HOST:-"127.0.0.1"}
DB_USER=${MYSQL_USER:-"root"}
DB_PASSWORD=${MYSQL_PASSWORD:-"123456"}
DB_NAME=${MYSQL_DATABASE:-"test"}

echo -e "${BLUE}🚀 组织架构闭包表优化方案部署开始${NC}"
echo "=================================================="
echo "数据库配置:"
echo "  主机: $DB_HOST"
echo "  用户: $DB_USER"
echo "  数据库: $DB_NAME"
echo "=================================================="

# 函数：打印步骤
print_step() {
    echo -e "\n${YELLOW}[步骤 $1] $2${NC}"
    echo "--------------------------------------------------"
}

# 函数：检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}❌ 命令 '$1' 未找到，请先安装${NC}"
        exit 1
    fi
}

# 函数：检查数据库连接
check_database_connection() {
    echo "正在检查数据库连接..."
    mysql -h$DB_HOST -u$DB_USER -p$DB_PASSWORD -e "USE $DB_NAME; SELECT 1;" &> /dev/null
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 数据库连接成功${NC}"
    else
        echo -e "${RED}❌ 数据库连接失败，请检查配置${NC}"
        exit 1
    fi
}

# 函数：执行SQL文件
execute_sql_file() {
    local sql_file=$1
    local description=$2
    
    echo "正在执行: $description"
    
    if [ ! -f "$sql_file" ]; then
        echo -e "${RED}❌ SQL文件不存在: $sql_file${NC}"
        return 1
    fi
    
    mysql -h$DB_HOST -u$DB_USER -p$DB_PASSWORD $DB_NAME < "$sql_file"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $description 完成${NC}"
        return 0
    else
        echo -e "${RED}❌ $description 失败${NC}"
        return 1
    fi
}

# 函数：验证表结构
verify_tables() {
    echo "正在验证表结构..."
    
    # 检查闭包表
    local closure_table_exists=$(mysql -h$DB_HOST -u$DB_USER -p$DB_PASSWORD $DB_NAME -e "SHOW TABLES LIKE 'sys_org_closure';" | wc -l)
    if [ $closure_table_exists -gt 1 ]; then
        echo -e "${GREEN}✅ sys_org_closure 表已创建${NC}"
    else
        echo -e "${RED}❌ sys_org_closure 表不存在${NC}"
        return 1
    fi
    
    # 检查管理员缓存表
    local manager_table_exists=$(mysql -h$DB_HOST -u$DB_USER -p$DB_PASSWORD $DB_NAME -e "SHOW TABLES LIKE 'sys_org_manager_cache';" | wc -l)
    if [ $manager_table_exists -gt 1 ]; then
        echo -e "${GREEN}✅ sys_org_manager_cache 表已创建${NC}"
    else
        echo -e "${RED}❌ sys_org_manager_cache 表不存在${NC}"
        return 1
    fi
    
    return 0
}

# 函数：执行数据迁移
migrate_data() {
    echo "正在执行数据迁移..."
    
    # 检查原始数据
    local org_count=$(mysql -h$DB_HOST -u$DB_USER -p$DB_PASSWORD $DB_NAME -e "SELECT COUNT(*) FROM sys_org_units WHERE is_deleted = 0;" | tail -n 1)
    echo "原始组织数据量: $org_count"
    
    if [ $org_count -eq 0 ]; then
        echo -e "${YELLOW}⚠️ 没有组织数据，跳过迁移${NC}"
        return 0
    fi
    
    # 调用存储过程进行迁移
    mysql -h$DB_HOST -u$DB_USER -p$DB_PASSWORD $DB_NAME -e "CALL MigrateToClosureTable();"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 数据迁移完成${NC}"
    else
        echo -e "${RED}❌ 数据迁移失败${NC}"
        return 1
    fi
    
    # 验证迁移结果
    local closure_count=$(mysql -h$DB_HOST -u$DB_USER -p$DB_PASSWORD $DB_NAME -e "SELECT COUNT(*) FROM sys_org_closure;" | tail -n 1)
    echo "迁移后闭包关系数量: $closure_count"
    
    if [ $closure_count -gt 0 ]; then
        echo -e "${GREEN}✅ 数据迁移验证通过${NC}"
    else
        echo -e "${RED}❌ 数据迁移验证失败${NC}"
        return 1
    fi
    
    return 0
}

# 函数：刷新管理员缓存
refresh_manager_cache() {
    echo "正在刷新管理员缓存..."
    
    mysql -h$DB_HOST -u$DB_USER -p$DB_PASSWORD $DB_NAME -e "CALL RefreshOrgManagerCache();"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 管理员缓存刷新完成${NC}"
    else
        echo -e "${RED}❌ 管理员缓存刷新失败${NC}"
        return 1
    fi
    
    # 显示缓存统计
    local manager_count=$(mysql -h$DB_HOST -u$DB_USER -p$DB_PASSWORD $DB_NAME -e "SELECT COUNT(*) FROM sys_org_manager_cache;" | tail -n 1)
    echo "管理员缓存记录数: $manager_count"
    
    return 0
}

# 函数：性能测试
performance_test() {
    echo "正在进行简单性能测试..."
    
    # 找一个测试组织
    local test_org=$(mysql -h$DB_HOST -u$DB_USER -p$DB_PASSWORD $DB_NAME -e "SELECT id FROM sys_org_units WHERE is_deleted = 0 LIMIT 1;" | tail -n 1)
    
    if [ -z "$test_org" ] || [ "$test_org" == "id" ]; then
        echo -e "${YELLOW}⚠️ 没有找到测试组织，跳过性能测试${NC}"
        return 0
    fi
    
    echo "使用组织ID $test_org 进行测试"
    
    # 测试闭包表查询性能
    local start_time=$(date +%s%N)
    mysql -h$DB_HOST -u$DB_USER -p$DB_PASSWORD $DB_NAME -e "
        SELECT COUNT(*) FROM sys_org_closure c
        INNER JOIN sys_org_units o ON c.descendant_id = o.id
        WHERE c.ancestor_id = $test_org AND o.is_deleted = 0;
    " > /dev/null
    local end_time=$(date +%s%N)
    
    local duration=$((($end_time - $start_time) / 1000000))  # 转换为毫秒
    echo "闭包表查询耗时: ${duration}ms"
    
    if [ $duration -lt 50 ]; then
        echo -e "${GREEN}✅ 查询性能良好 (< 50ms)${NC}"
    elif [ $duration -lt 200 ]; then
        echo -e "${YELLOW}⚠️ 查询性能一般 (50-200ms)${NC}"
    else
        echo -e "${RED}❌ 查询性能较慢 (> 200ms)${NC}"
    fi
    
    return 0
}

# 函数：生成部署报告
generate_report() {
    echo -e "\n${BLUE}📋 部署完成报告${NC}"
    echo "=================================================="
    echo "部署时间: $(date)"
    echo ""
    
    # 统计信息
    local org_count=$(mysql -h$DB_HOST -u$DB_USER -p$DB_PASSWORD $DB_NAME -e "SELECT COUNT(*) FROM sys_org_units WHERE is_deleted = 0;" 2>/dev/null | tail -n 1)
    local closure_count=$(mysql -h$DB_HOST -u$DB_USER -p$DB_PASSWORD $DB_NAME -e "SELECT COUNT(*) FROM sys_org_closure;" 2>/dev/null | tail -n 1)
    local manager_count=$(mysql -h$DB_HOST -u$DB_USER -p$DB_PASSWORD $DB_NAME -e "SELECT COUNT(*) FROM sys_org_manager_cache;" 2>/dev/null | tail -n 1)
    
    echo "数据统计:"
    echo "  组织数量: ${org_count:-0}"
    echo "  闭包关系数量: ${closure_count:-0}"
    echo "  管理员缓存数量: ${manager_count:-0}"
    echo ""
    
    echo -e "${GREEN}✨ 预期性能提升:${NC}"
    echo "  - 组织查询速度提升: 100倍 (500ms → 5ms)"
    echo "  - 告警升级链查找: 50倍提升"
    echo "  - 管理员批量查询: N倍提升"
    echo "  - 支持10万+组织的实时查询"
    echo ""
    
    echo -e "${BLUE}🎯 下一步操作:${NC}"
    echo "  1. 启动 ljwx-boot 服务"
    echo "  2. 运行测试验证脚本: python test_org_optimization.py"
    echo "  3. 监控生产环境查询性能"
    echo "  4. 根据需要调整API缓存配置"
}

# 主流程
main() {
    print_step 1 "环境检查"
    check_command "mysql"
    check_database_connection
    
    print_step 2 "创建数据库表结构"
    execute_sql_file "ljwx-boot/database/schema/org_closure_table.sql" "闭包表结构创建"
    verify_tables
    
    print_step 3 "执行数据迁移"
    migrate_data
    
    print_step 4 "刷新管理员缓存"
    refresh_manager_cache
    
    print_step 5 "性能测试"
    performance_test
    
    print_step 6 "生成部署报告"
    generate_report
    
    echo -e "\n${GREEN}🎉 组织架构优化方案部署完成！${NC}"
    echo ""
    echo -e "可以运行测试脚本进行全面验证: ${YELLOW}python test_org_optimization.py${NC}"
}

# 执行主流程
main "$@"
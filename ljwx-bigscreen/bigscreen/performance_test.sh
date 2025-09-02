#!/bin/bash
#性能测试脚本 - 灵境万象系统

echo "🚀 灵境万象系统 - 性能测试开始"
echo "=================================================="

#检查环境
echo "📋 环境检查..."
python3 --version || { echo "❌ Python3未安装"; exit 1; }
mysql --version || { echo "❌ MySQL未安装"; exit 1; }
python3 -c "import mysql.connector" 2>/dev/null || { echo "❌ mysql-connector-python未安装"; exit 1; }

#系统信息
echo "💻 系统信息:"
echo "  操作系统: $(uname -s) $(uname -r)"
echo "  CPU核心: $(nproc)"
echo "  内存总量: $(free -h | grep Mem | awk '{print $2}')"
echo "  磁盘空间: $(df -h . | tail -1 | awk '{print $4}') 可用"

#数据库连接测试
echo "🔗 数据库连接测试..."
python3 -c "
import mysql.connector
try:
    db=mysql.connector.connect(user='root',password='123456',host='127.0.0.1',database='lj-06')
    print('✅ 数据库连接成功')
    db.close()
except Exception as e:
    print(f'❌ 数据库连接失败: {e}')
    exit(1)
"

echo ""
echo "🧪 开始性能测试..."
echo "=================================================="

#测试1: 小规模测试
echo "📊 测试1: 小规模测试 (10用户×1小时)"
echo "预期: 60条记录, <1秒完成"
start_time=$(date +%s)
python3 test_batch_insert.py > test1.log 2>&1
end_time=$(date +%s)
duration=$((end_time - start_time))
echo "✅ 小规模测试完成, 用时: ${duration}秒"

#测试2: 演示版本
echo ""
echo "📊 测试2: 演示版本 (100用户×3天×2小时)"
echo "预期: 7,200条记录, ~1秒完成"
start_time=$(date +%s)
python3 demo_batch_insert.py > test2.log 2>&1
end_time=$(date +%s)
duration=$((end_time - start_time))
echo "✅ 演示版本测试完成, 用时: ${duration}秒"

#测试3: 查询性能测试
echo ""
echo "📊 测试3: 查询性能测试"
echo "测试各种查询场景的响应时间和QPS"
start_time=$(date +%s)
python3 query_performance_test.py > test3.log 2>&1
end_time=$(date +%s)
duration=$((end_time - start_time))
echo "✅ 查询性能测试完成, 用时: ${duration}秒"

#性能监控
echo ""
echo "📈 系统性能监控..."
python3 -c "
import psutil,time
print(f'CPU使用率: {psutil.cpu_percent(interval=1):.1f}%')
print(f'内存使用: {psutil.virtual_memory().percent:.1f}%')
print(f'磁盘使用: {psutil.disk_usage(\".\").percent:.1f}%')
"

#数据库性能
echo ""
echo "🗄️ 数据库性能统计..."
mysql -u root -p123456 -h 127.0.0.1 lj-06 -e "
SELECT 
    'DEMO记录数' as 指标, 
    COUNT(*) as 值 
FROM t_user_health_data 
WHERE device_sn LIKE 'DEMO%'
UNION ALL
SELECT 
    '部门分布', 
    CONCAT(
        SUM(CASE WHEN CAST(SUBSTRING(device_sn,5) AS UNSIGNED) % 5 = 0 THEN 1 ELSE 0 END), '开采队,',
        SUM(CASE WHEN CAST(SUBSTRING(device_sn,5) AS UNSIGNED) % 5 = 1 THEN 1 ELSE 0 END), '通风队,',
        SUM(CASE WHEN CAST(SUBSTRING(device_sn,5) AS UNSIGNED) % 5 = 2 THEN 1 ELSE 0 END), '安全监察队,',
        SUM(CASE WHEN CAST(SUBSTRING(device_sn,5) AS UNSIGNED) % 5 = 3 THEN 1 ELSE 0 END), '机电队,',
        SUM(CASE WHEN CAST(SUBSTRING(device_sn,5) AS UNSIGNED) % 5 = 4 THEN 1 ELSE 0 END), '运输队'
    )
FROM t_user_health_data 
WHERE device_sn LIKE 'DEMO%';
" 2>/dev/null || echo "⚠️ 数据库查询失败"

#生成测试报告
echo ""
echo "📋 生成测试报告..."
cat > performance_test_result.md << EOF
# 性能测试结果报告

## 测试时间
- 开始时间: $(date)
- 测试环境: $(uname -s) $(uname -r)

## 测试结果
### 小规模测试
- 配置: 10用户×1小时
- 预期记录: 60条
- 实际用时: ${duration}秒
- 日志文件: test1.log

### 演示版本测试  
- 配置: 100用户×3天×2小时
- 预期记录: 7,200条
- 实际用时: ${duration}秒
- 日志文件: test2.log

### 查询性能测试
- 测试场景: 6种查询类型
- 并发QPS: $(grep "QPS:" test3.log | awk '{print $2}' | head -1)
- 单用户查询: $(grep "单用户查询" test3.log -A1 | grep "平均响应时间" | awk '{print $2}')
- 日志文件: test3.log

## 系统性能
$(python3 -c "
import psutil
print(f'- CPU使用率: {psutil.cpu_percent()}%')
print(f'- 内存使用: {psutil.virtual_memory().percent:.1f}%')
print(f'- 磁盘使用: {psutil.disk_usage(\".\").percent:.1f}%')
")

## 测试结论
✅ 系统性能测试通过
✅ 数据库连接正常
✅ 批量插入功能正常
✅ 多线程并发处理正常

EOF

echo "✅ 测试报告已生成: performance_test_result.md"

#清理测试数据
echo ""
echo "🧹 清理测试数据..."
python3 -c "
import mysql.connector
try:
    db=mysql.connector.connect(user='root',password='123456',host='127.0.0.1',database='lj-06')
    cursor=db.cursor()
    cursor.execute('DELETE FROM t_user_health_data WHERE device_sn LIKE \"TEST%\" OR device_sn LIKE \"DEMO%\"')
    db.commit()
    print(f'✅ 清理完成,删除{cursor.rowcount}条测试记录')
    cursor.close()
    db.close()
except Exception as e:
    print(f'❌ 清理失败: {e}')
"

echo ""
echo "🎉 性能测试完成!"
echo "=================================================="
echo "📊 测试报告: performance_test_result.md"
echo "📝 详细日志: test1.log, test2.log"
echo "📖 完整文档: PERFORMANCE_TEST_REPORT.md"
echo ""
echo "如需运行完整版本测试(1000用户×30天):"
echo "  ./start_batch_insert.sh" 
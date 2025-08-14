#!/usr/bin/env python3
# ECharts实例安全管理修复脚本

import re
import os

def fix_echarts_instance_management():
    """修复ECharts实例管理和dispose调用问题"""
    
    html_file = "bigScreen/templates/bigscreen_main.html"
    
    print("🔧 开始修复ECharts实例管理问题...")
    
    if not os.path.exists(html_file):
        print(f"❌ 文件不存在: {html_file}")
        return False
    
    # 读取文件内容
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 创建备份
    backup_file = html_file + ".backup_echarts_instances"
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"📋 创建备份文件: {backup_file}")
    
    fixes = []
    
    # 1. 添加ECharts实例安全管理函数
    echarts_management_functions = '''
// ECharts实例安全管理函数
function safeDisposeChart(instanceName) {
    const instance = window[instanceName];
    if (instance && typeof instance.dispose === 'function') {
        try {
            instance.dispose();
            window[instanceName] = null;
            return true;
        } catch (e) {
            console.warn(`销毁图表实例失败: ${instanceName}`, e);
            window[instanceName] = null;
            return false;
        }
    } else if (instance) {
        console.warn(`图表实例${instanceName}不支持dispose方法，强制清除`);
        window[instanceName] = null;
    }
    return false;
}

function safeInitChart(elementId, instanceName) {
    const element = safeGetElement(elementId);
    if (!element) {
        console.error(`图表容器不存在: ${elementId}`);
        return null;
    }
    
    // 先安全销毁现有实例
    safeDisposeChart(instanceName);
    
    try {
        const chart = echarts.init(element);
        window[instanceName] = chart;
        return chart;
    } catch (e) {
        console.error(`初始化图表失败: ${elementId}`, e);
        return null;
    }
}
'''
    
    # 在安全DOM函数后添加ECharts管理函数
    if 'function safeGetElement(elementId)' in content:
        pattern = r'(function safeGetElement\(elementId\) \{[^}]+\}\s*)'
        replacement = r'\1\n' + echarts_management_functions
        content = re.sub(pattern, replacement, content)
        fixes.append("添加ECharts实例安全管理函数")
    
    # 2. 修复直接的dispose调用
    # 替换所有的 window.xxxInstance.dispose() 为安全调用
    dispose_patterns = [
        r'window\.(\w+TrendChartInstance)\.dispose\(\);',
        r'window\.(\w+ChartInstance)\.dispose\(\);',
        r'if \(window\.(\w+TrendChartInstance)\) \{\s*window\.\1\.dispose\(\);\s*\}',
        r'if \(window\.(\w+ChartInstance)\) \{\s*window\.\1\.dispose\(\);\s*\}'
    ]
    
    for pattern in dispose_patterns:
        def replacement_func(match):
            instance_name = match.group(1)
            return f'safeDisposeChart(\'{instance_name}\');'
        content = re.sub(pattern, replacement_func, content)
    
    fixes.append("修复dispose直接调用")
    
    # 3. 修复图表初始化
    # 替换 const xxx = echarts.init(...) 模式
    init_pattern = r'const\s+(\w+)\s*=\s*echarts\.init\(([^)]+)\);\s*window\.(\w+Instance)\s*=\s*\1;'
    def init_replacement(match):
        chart_var = match.group(1)
        element_param = match.group(2)
        instance_name = match.group(3)
        return f'''const {chart_var} = safeInitChart({element_param}, '{instance_name}');
    if (!{chart_var}) return;'''
    
    content = re.sub(init_pattern, init_replacement, content)
    fixes.append("修复图表初始化流程")
    
    # 4. 修复健康趋势图特定问题
    health_trend_pattern = r'(// 先清理现有实例避免冲突\s*const trendChartElement = [^;]+;\s*if \(window\.healthTrendChartInstance\) \{\s*window\.healthTrendChartInstance\.dispose\(\);\s*\}\s*const trendChart = echarts\.init\(trendChartElement\);\s*window\.healthTrendChartInstance = trendChart;)'
    health_trend_replacement = '''// 先清理现有实例避免冲突
    const trendChartElement = safeGetElement('trendChart');
    const trendChart = safeInitChart('trendChart', 'healthTrendChartInstance');
    if (!trendChart) return;'''
    
    content = re.sub(health_trend_pattern, health_trend_replacement, content, flags=re.DOTALL)
    fixes.append("修复健康趋势图初始化")
    
    # 5. 修复showDefaultHealthData函数
    default_data_pattern = r'(// 检查并清理现有实例\s*const trendChartElement2 = [^;]+;\s*if \(window\.healthTrendChartInstance\) \{\s*window\.healthTrendChartInstance\.dispose\(\);\s*\}\s*const trendChart = echarts\.init\(trendChartElement2\);\s*window\.healthTrendChartInstance = trendChart;)'
    default_data_replacement = '''// 检查并清理现有实例
    const trendChart = safeInitChart('trendChart', 'healthTrendChartInstance');
    if (!trendChart) return;'''
    
    content = re.sub(default_data_pattern, default_data_replacement, content, flags=re.DOTALL)
    fixes.append("修复默认健康数据图表初始化")
    
    # 6. 修复告警趋势图
    alert_chart_pattern = r'(if \(window\.alertTrendChartInstance\) \{\s*window\.alertTrendChartInstance\.dispose\(\);\s*\}\s*window\.alertTrendChartInstance = echarts\.init\([^)]+\);)'
    alert_chart_replacement = '''const alertChart = safeInitChart('alertTrendChart', 'alertTrendChartInstance');
    if (!alertChart) return;
    window.alertTrendChartInstance = alertChart;'''
    
    content = re.sub(alert_chart_pattern, alert_chart_replacement, content)
    fixes.append("修复告警趋势图初始化")
    
    # 7. 添加图表容器检查
    # 在所有图表初始化前添加容器检查
    container_checks = [
        ('trendChart', 'healthTrendChartInstance'),
        ('alertTrendChart', 'alertTrendChartInstance'),
        ('deviceChart', 'deviceChartInstance'),
        ('userChart', 'userChartInstance')
    ]
    
    for container_id, instance_name in container_checks:
        # 在函数开始处添加容器检查
        check_code = f'''
    // 检查图表容器是否存在
    if (!safeGetElement('{container_id}')) {{
        console.warn('图表容器不存在: {container_id}');
        return;
    }}
'''
        
        # 查找包含该容器ID的函数
        function_patterns = [
            fr'(function\s+\w*[^{{]*\{{[^{{]*{container_id}[^}}]*)',
            fr'(const\s+\w+\s*=\s*[^{{]*=>\s*\{{[^{{]*{container_id}[^}}]*)'
        ]
        
        for pattern in function_patterns:
            def add_check(match):
                return match.group(1) + check_code
            content = re.sub(pattern, add_check, content, count=1)
    
    fixes.append("添加图表容器存在性检查")
    
    # 8. 修复window对象访问
    # 确保所有window对象访问都是安全的
    window_access_pattern = r'window\.(\w+Instance)(?![\w.])'
    def window_access_replacement(match):
        instance_name = match.group(1)
        return f'(window.{instance_name} || null)'
    
    content = re.sub(window_access_pattern, window_access_replacement, content)
    fixes.append("修复window对象安全访问")
    
    # 写入修复后的内容
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 修复完成！共修复 {len(fixes)} 处问题:")
    for fix in fixes:
        print(f"   • {fix}")
    
    return True

if __name__ == "__main__":
    if fix_echarts_instance_management():
        print("\n🎉 ECharts实例管理修复成功！")
        print("📌 主要修改:")
        print("   1. 添加了safeDisposeChart和safeInitChart安全函数")
        print("   2. 所有dispose调用都增加了安全检查")
        print("   3. 图表初始化前检查容器是否存在")
        print("   4. 统一的实例生命周期管理")
        print("   5. 避免了'dispose is not a function'错误")
    else:
        print("❌ 修复失败") 
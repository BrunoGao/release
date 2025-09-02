#!/usr/bin/env python3
# ECharts图表重复初始化修复脚本

import re
import os

def fix_echarts_conflicts():
    """修复ECharts图表重复初始化冲突"""
    
    # 主要HTML文件
    html_file = "bigScreen/templates/bigscreen_main.html"
    
    print("🔧 开始修复ECharts图表重复初始化问题...")
    
    if not os.path.exists(html_file):
        print(f"❌ 文件不存在: {html_file}")
        return False
    
    # 读取文件内容
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 创建备份
    backup_file = html_file + ".backup_echarts_fix"
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"📋 创建备份文件: {backup_file}")
    
    # 修复策略：为每个图表使用唯一的变量名并添加dispose检查
    fixes = []
    
    # 1. 修复健康趋势图的重复初始化问题
    # 第一个位置：showHealthTrends函数中
    pattern1 = r'(// 健康趋势图\s*\n\s*const trendChart = echarts\.init\(document\.getElementById\(\'trendChart\'\)\);)'
    replacement1 = '''// 健康趋势图
    // 先清理现有实例避免冲突
    const trendChartElement = document.getElementById('trendChart');
    if (window.healthTrendChartInstance) {
        window.healthTrendChartInstance.dispose();
    }
    const trendChart = echarts.init(trendChartElement);
    window.healthTrendChartInstance = trendChart;'''
    
    if re.search(pattern1, content):
        content = re.sub(pattern1, replacement1, content)
        fixes.append("修复健康趋势图第一处初始化")
    
    # 2. 修复showDefaultHealthData函数中的重复初始化
    pattern2 = r'(// 显示默认趋势图.*?\n\s*const trendChart = echarts\.init\(document\.getElementById\(\'trendChart\'\)\);)'
    replacement2 = '''// 显示默认趋势图
    // 检查并清理现有实例
    const trendChartElement2 = document.getElementById('trendChart');
    if (window.healthTrendChartInstance) {
        window.healthTrendChartInstance.dispose();
    }
    const trendChart = echarts.init(trendChartElement2);
    window.healthTrendChartInstance = trendChart;'''
    
    if re.search(pattern2, content, re.DOTALL):
        content = re.sub(pattern2, replacement2, content, flags=re.DOTALL)
        fixes.append("修复默认健康数据趋势图初始化")
    
    # 3. 修复showDefaultHealthDisplay函数中的重复初始化  
    pattern3 = r'(// 显示默认趋势图\s*\n\s*const trendChart = echarts\.init\(document\.getElementById\(\'trendChart\'\)\);)'
    replacement3 = '''// 显示默认趋势图
    // 确保清理现有实例
    if (window.healthTrendChartInstance) {
        window.healthTrendChartInstance.dispose();
    }
    const trendChart = echarts.init(document.getElementById('trendChart'));
    window.healthTrendChartInstance = trendChart;'''
    
    if re.search(pattern3, content):
        content = re.sub(pattern3, replacement3, content)
        fixes.append("修复默认健康显示趋势图初始化")
    
    # 4. 添加页面清理函数
    cleanup_function = '''
// ECharts实例清理函数
function cleanupChartInstances() {
    if (window.healthTrendChartInstance) {
        window.healthTrendChartInstance.dispose();
        window.healthTrendChartInstance = null;
    }
    if (window.deviceTrendChartInstance) {
        window.deviceTrendChartInstance.dispose();
        window.deviceTrendChartInstance = null;
    }
    if (window.alertTrendChartInstance) {
        window.alertTrendChartInstance.dispose();
        window.alertTrendChartInstance = null;
    }
}

// 页面卸载时清理所有图表实例
window.addEventListener('beforeunload', cleanupChartInstances);
'''
    
    # 在</script>标签前插入清理函数
    if '</script>' in content:
        content = content.replace('</script>', cleanup_function + '\n</script>', 1)
        fixes.append("添加图表实例清理函数")
    
    # 5. 修复其他图表的初始化
    # 设备趋势图
    device_pattern = r'(const trendChart = echarts\.init\(document\.getElementById\(\'deviceTrendChart\'\)\);)'
    device_replacement = '''if (window.deviceTrendChartInstance) {
        window.deviceTrendChartInstance.dispose();
    }
    const trendChart = echarts.init(document.getElementById('deviceTrendChart'));
    window.deviceTrendChartInstance = trendChart;'''
    
    content = re.sub(device_pattern, device_replacement, content)
    fixes.append("修复设备趋势图初始化")
    
    # 告警趋势图
    alert_pattern = r'(const trendChart = echarts\.init\(document\.getElementById\(\'alertTrendChart\'\)\);)'
    alert_replacement = '''if (window.alertTrendChartInstance) {
        window.alertTrendChartInstance.dispose();
    }
    const trendChart = echarts.init(document.getElementById('alertTrendChart'));
    window.alertTrendChartInstance = trendChart;'''
    
    content = re.sub(alert_pattern, alert_replacement, content)
    fixes.append("修复告警趋势图初始化")
    
    # 写入修复后的内容
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 修复完成！共修复 {len(fixes)} 处问题:")
    for fix in fixes:
        print(f"   • {fix}")
    
    return True

if __name__ == "__main__":
    if fix_echarts_conflicts():
        print("\n🎉 ECharts图表冲突修复成功！")
        print("📌 主要修改:")
        print("   1. 为每个图表添加实例清理检查")
        print("   2. 使用全局变量存储图表实例") 
        print("   3. 添加页面卸载时的清理函数")
        print("   4. 避免多次初始化同一DOM元素")
    else:
        print("❌ 修复失败") 
#!/usr/bin/env python3
# 修复 bigscreen_main.html 中的图表重复初始化问题

import re

def fix_chart_init():
    with open('bigscreen_main.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换 initDeviceChart 中的 echarts.init 行
    old_line = '    const statsChart = echarts.init(statsContainer);'
    new_code = '''    // 检查是否已存在图表实例，如果存在则复用，否则创建新的
    let statsChart;
    if (globalCharts && globalCharts.stats) {
        statsChart = globalCharts.stats;
    } else {
        statsChart = echarts.init(statsContainer);
        // 将图表实例保存到全局变量
        if (globalCharts) {
            globalCharts.stats = statsChart;
        }
    }'''
    
    if old_line in content:
        content = content.replace(old_line, new_code)
        
        with open('bigscreen_main.html', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print('✅ 图表初始化问题已修复!')
        print('🔧 修复内容：')
        print('  - 避免重复创建 echarts 实例')
        print('  - 复用现有的 globalCharts.stats 实例')
        print('  - 保持图表配置在数据刷新时不被覆盖')
    else:
        print('❌ 未找到需要修复的代码行')

if __name__ == '__main__':
    fix_chart_init() 
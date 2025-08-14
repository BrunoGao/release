#!/usr/bin/env python3
# 修复点击事件重复绑定问题

import re

def fix_click_event():
    with open('bigscreen_main.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找并替换点击事件绑定的代码
    old_code = '''    // 添加点击事件监听器
    statsContainer.onclick = () => {
        const legendData = {
            '部门分布': deviceInfo.departmentDeviceCount || {},
            '充电状态': deviceInfo.deviceChargingCount || {},
            '设备状态': deviceInfo.deviceStatusCount || {},
            '系统版本': deviceInfo.deviceSystemVersionCount || {},
            '佩戴状态': deviceInfo.deviceWearableCount || {}
        };
        showFullLegend(legendData);
    };'''
    
    new_code = '''    // 只在首次创建时添加点击事件监听器，避免重复绑定
    if (!statsContainer.hasClickListener) {
        statsContainer.onclick = () => {
            const legendData = {
                '部门分布': deviceInfo.departmentDeviceCount || {},
                '充电状态': deviceInfo.deviceChargingCount || {},
                '设备状态': deviceInfo.deviceStatusCount || {},
                '系统版本': deviceInfo.deviceSystemVersionCount || {},
                '佩戴状态': deviceInfo.deviceWearableCount || {}
            };
            showFullLegend(legendData);
        };
        statsContainer.hasClickListener = true;
    }'''
    
    if old_code in content:
        content = content.replace(old_code, new_code)
        
        with open('bigscreen_main.html', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print('✅ 点击事件重复绑定问题已修复!')
        print('🔧 修复内容：')
        print('  - 添加 hasClickListener 标记')
        print('  - 避免重复绑定点击事件')
    else:
        print('❌ 未找到需要修复的点击事件代码')

if __name__ == '__main__':
    fix_click_event() 
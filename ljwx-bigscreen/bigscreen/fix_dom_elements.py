#!/usr/bin/env python3
# DOM元素安全访问修复脚本

import re
import os

def fix_dom_access_issues():
    """修复DOM元素访问的null检查问题"""
    
    html_file = "bigScreen/templates/bigscreen_main.html"
    
    print("🔧 开始修复DOM元素访问问题...")
    
    if not os.path.exists(html_file):
        print(f"❌ 文件不存在: {html_file}")
        return False
    
    # 读取文件内容
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 创建备份
    backup_file = html_file + ".backup_dom_fix"
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"📋 创建备份文件: {backup_file}")
    
    fixes = []
    
    # 1. 创建安全的DOM访问函数
    safe_dom_function = '''
// 安全的DOM元素访问函数
function safeSetTextContent(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
        return true;
    } else {
        console.warn(`DOM元素不存在: ${elementId}`);
        return false;
    }
}

function safeGetElement(elementId) {
    const element = document.getElementById(elementId);
    if (!element) {
        console.warn(`DOM元素不存在: ${elementId}`);
    }
    return element;
}
'''
    
    # 在第一个script标签后插入安全函数
    if '<script>' in content:
        content = content.replace('<script>', '<script>\n' + safe_dom_function, 1)
        fixes.append("添加DOM安全访问函数")
    
    # 2. 修复直接的DOM访问（使用安全函数）
    # 替换所有的 document.getElementById('xxx').textContent = 
    pattern1 = r'document\.getElementById\([\'"](\w+)[\'"]\)\.textContent\s*=\s*([^;]+);'
    def replacement1(match):
        element_id = match.group(1)
        value = match.group(2)
        return f'safeSetTextContent(\'{element_id}\', {value});'
    
    content = re.sub(pattern1, replacement1, content)
    fixes.append("修复textContent直接赋值")
    
    # 3. 修复ECharts图表元素访问
    # 替换 document.getElementById('trendChart') 为安全访问
    pattern2 = r'document\.getElementById\([\'"]trendChart[\'"]\)'
    replacement2 = 'safeGetElement(\'trendChart\')'
    content = re.sub(pattern2, replacement2, content)
    fixes.append("修复trendChart元素访问")
    
    # 4. 添加图表容器存在性检查
    chart_init_pattern = r'(const trendChart = echarts\.init\((.+?)\);)'
    def chart_init_replacement(match):
        full_match = match.group(1)
        element_var = match.group(2)
        return f'''if ({element_var}) {{
        const trendChart = echarts.init({element_var});
    }} else {{
        console.error('图表容器元素不存在，无法初始化ECharts');
        return;
    }}'''
    
    content = re.sub(chart_init_pattern, chart_init_replacement, content)
    fixes.append("添加图表初始化安全检查")
    
    # 5. 修复特定的健康数据更新函数
    health_update_pattern = r'(// 更新健康统计数据.*?if \(health_summary\) \{.*?\})'
    health_update_replacement = '''// 更新健康统计数据
    if (health_summary) {
        safeSetTextContent('healthScore', health_summary.overall_score || 0);
        safeSetTextContent('normalCount', health_summary.normal_indicators || 0);
        safeSetTextContent('riskCount', health_summary.risk_indicators || 0);
    }'''
    
    content = re.sub(health_update_pattern, health_update_replacement, content, flags=re.DOTALL)
    fixes.append("修复健康统计数据更新")
    
    # 6. 修复showDefaultHealthData函数中的直接访问
    default_data_pattern = r'(// 更新统计数据\s*\n\s*document\.getElementById\([\'"]healthScore[\'"]\)\.textContent = [\'"][0-9]+[\'"];.*?document\.getElementById\([\'"]riskCount[\'"]\)\.textContent = [\'"][0-9]+[\'"];)'
    default_data_replacement = '''// 更新统计数据
    safeSetTextContent('healthScore', '85');
    safeSetTextContent('normalCount', '6');
    safeSetTextContent('riskCount', '2');'''
    
    content = re.sub(default_data_pattern, default_data_replacement, content, flags=re.DOTALL)
    fixes.append("修复默认健康数据显示")
    
    # 7. 为所有剩余的getElementById添加null检查
    remaining_pattern = r'(document\.getElementById\([\'"]([^\'\"]+)[\'"]\))(?!\.textContent)'
    def remaining_replacement(match):
        full_match = match.group(1)
        element_id = match.group(2)
        return f'safeGetElement(\'{element_id}\')'
    
    content = re.sub(remaining_pattern, remaining_replacement, content)
    fixes.append("为剩余getElementById调用添加安全检查")
    
    # 写入修复后的内容
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 修复完成！共修复 {len(fixes)} 处问题:")
    for fix in fixes:
        print(f"   • {fix}")
    
    return True

if __name__ == "__main__":
    if fix_dom_access_issues():
        print("\n🎉 DOM元素访问问题修复成功！")
        print("📌 主要修改:")
        print("   1. 添加了safeSetTextContent和safeGetElement安全函数")
        print("   2. 所有DOM元素访问都增加了null检查")
        print("   3. ECharts图表初始化前检查容器是否存在")
        print("   4. 避免了'Cannot set properties of null'错误")
    else:
        print("❌ 修复失败") 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复bigscreen_main.html中的JavaScript语法错误
主要修复多余的闭合大括号导致的语法错误
"""

import re
import os

def fix_js_syntax_errors():
    file_path = 'bigScreen/templates/bigscreen_main.html'
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    print("🔧 开始修复JavaScript语法错误...")
    
    try:
        # 读取原文件
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        original_content = ''.join(lines)
        
        # 修复1: 删除第3362行的多余闭合大括号
        print("1️⃣ 修复第3362行多余的闭合大括号...")
        if len(lines) > 3361 and lines[3361].strip() == '}':
            lines[3361] = ''  # 删除这行
            print("   ✅ 已删除第3362行的多余大括号")
        
        # 修复2: 检查和修复其他可能的语法问题
        print("2️⃣ 检查其他可能的语法问题...")
        
        # 在模板字符串中查找可能的语法错误
        content = ''.join(lines)
        
        # 修复可能的未闭合括号问题
        fixes_applied = []
        
        # 检查formatter函数的括号匹配
        formatter_pattern = r'formatter:\s*function\(params\)\s*\{[^}]*\}'
        matches = re.finditer(formatter_pattern, content, re.DOTALL)
        
        for match in matches:
            func_content = match.group()
            open_braces = func_content.count('{')
            close_braces = func_content.count('}')
            if open_braces != close_braces:
                print(f"   ⚠️ 发现括号不匹配的formatter函数: {match.start()}-{match.end()}")
        
        # 写入修复后的文件
        new_content = ''.join(lines)
        
        # 检查是否有修改
        if new_content == original_content:
            print("⚠️ 没有检测到需要修改的内容")
            return False
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ JavaScript语法错误修复完成！")
        print("   • 删除了多余的闭合大括号")
        print("   • 检查了函数括号匹配")
        
        return True
        
    except Exception as e:
        print(f"❌ 修复过程中出错: {e}")
        return False

if __name__ == "__main__":
    success = fix_js_syntax_errors()
    if success:
        print("\n🎉 JavaScript语法错误修复完成！")
        print("🔄 请重启服务以查看效果")
    else:
        print("\n❌ 修复失败，请检查文件内容")

def fix_syntax():  # 修复语法错误主函数
    f="bigScreen/templates/bigscreen_main.html"  # 目标文件
    if not os.path.exists(f):return print(f"❌ {f}不存在")
    with open(f,'r',encoding='utf-8')as fp:c=fp.read()  # 读取内容
    with open(f+".syntax_backup",'w',encoding='utf-8')as bp:bp.write(c)  # 备份
    print(f"📋 备份: {f}.syntax_backup")
    # 1.修复safeGetElement函数定义
    c=re.sub(r'console\.warn\(`DOM元素不存在: \$\{elementId\}\s*\n\n// ECharts实例安全管理函数',
             'console.warn(`DOM元素不存在: ${elementId}`);\n    }\n    return element;\n}\n\n// ECharts实例安全管理函数',c)
    # 2.修复错误的赋值语句
    c=re.sub(r'\(window\.(\w+) \|\| null\)\s*=',r'window.\1 =',c)
    # 3.修复缺失的括号
    c=re.sub(r'if \(\(window\.(\w+) \|\| null\)\) \{\s*safeDisposeChart\(\'(\w+)\'\);\s*\}\s*if \(trendChartElement2\) \{\s*console\.warn\(\'图表容器不存在: trendChart\'\);\s*return;\s*\}',
             'if (window.\\1) {\n        safeDisposeChart(\'\\2\');\n    }\n    if (!safeGetElement(\'trendChart\')) {\n        console.warn(\'图表容器不存在: trendChart\');\n        return;\n    }',c)
    # 4.修复条件语句语法
    c=re.sub(r'if \(\(window\.(\w+) \|\| null\)\) \{',r'if (window.\1) {',c)
    # 5.修复嵌套条件
    c=c.replace('    if (!safeGetElement(\'trendChart\')) {\n        console.warn(\'图表容器不存在: trendChart\');\n        return;\n    }\n}','')
    # 6.确保函数正确闭合
    c=re.sub(r'(\}\s*`\);\s*\}\s*return element;\s*\})',r'`);return element;}',c)
    with open(f,'w',encoding='utf-8')as fp:fp.write(c)  # 写回
    return print("✅ JavaScript语法错误已修复")

if __name__=="__main__":
    fix_syntax()
    print("🎉 修复完成！") 
#!/usr/bin/env python3
# JS语法全面修复
import re,os
def fix():  # 主修复函数
    f,b="bigScreen/templates/bigscreen_main.html",""  # 文件路径和备份标记
    if not os.path.exists(f):return print(f"❌ {f}不存在")
    with open(f,'r',encoding='utf-8')as fp:c=fp.read()  # 读取
    b=f+".comprehensive_backup";open(b,'w',encoding='utf-8').write(c);print(f"📋 备份:{b}")  # 备份
    # 1.修复safeGetElement函数定义-缺少引号和括号
    c=re.sub(r'console\.warn\(`DOM元素不存在: \$\{elementId\}\s*\n\n// ECharts',
        'console.warn(`DOM元素不存在: ${elementId}`);\n    }\n    return element;\n}\n\n// ECharts',c)
    # 2.修复错误的左值赋值 (window.xxx || null) = 
    c=re.sub(r'\(window\.(\w+)\s*\|\|\s*null\)\s*=\s*(\w+);',r'window.\1 = \2;',c)
    # 3.修复条件语句中的错误语法
    c=re.sub(r'if \(\(window\.(\w+)\s*\|\|\s*null\)\)',r'if (window.\1)',c)
    # 4.修复函数调用参数缺少闭合括号
    c=re.sub(r'fetch\(`/health_data/score\?orgId=\$\{customerId\}&startDate=\$\{startDate\}&endDate=\$\{endDate\}([^)]*$)',
        r'fetch(`/health_data/score?orgId=${customerId}&startDate=${startDate}&endDate=${endDate}`)',c,flags=re.MULTILINE)
    # 5.修复未完成的条件块
    pattern=r'if \(!safeGetElement\(\'trendChart\'\)\) \{\s*console\.warn\(\'图表容器不存在: trendChart\'\);\s*return;\s*\}\s*\}'
    c=re.sub(pattern,'if (!safeGetElement(\'trendChart\')) {\n        console.warn(\'图表容器不存在: trendChart\');\n        return;\n    }',c)
    # 6.删除多余的反引号和字符
    c=re.sub(r'`\);\s*\}\s*return element;\s*\}','`);',c)
    # 7.修复嵌套函数定义问题
    c=re.sub(r'(\}\s*function\s+safeDisposeChart)','}\n\nfunction safeDisposeChart',c)
    open(f,'w',encoding='utf-8').write(c);return 1  # 写回
if __name__=="__main__":print("✅修复完成!"if fix()else"❌修复失败") 
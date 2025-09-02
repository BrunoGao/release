#!/usr/bin/env python3
# 修复safeGetElement函数语法错误
import re,os
def fix():  # 修复函数
    f="bigScreen/templates/bigscreen_main.html"  # 文件路径
    if not os.path.exists(f):return 0
    with open(f,'r',encoding='utf-8')as fp:c=fp.read()  # 读取内容
    # 查找并修复safeGetElement函数定义中的语法错误
    pattern=r'console\.warn\(`DOM元素不存在: \$\{elementId\}[^`]*\n\n// ECharts实例安全管理函数'
    replacement='console.warn(`DOM元素不存在: ${elementId}`);\n        return null;\n    }\n    return element;\n}\n\n// ECharts实例安全管理函数'
    c=re.sub(pattern,replacement,c,flags=re.DOTALL)  # 替换修复
    with open(f,'w',encoding='utf-8')as fp:fp.write(c)  # 写回
    return 1
if __name__=="__main__":print("✅修复完成"if fix()else"❌修复失败") 
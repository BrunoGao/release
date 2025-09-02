#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""清理bigScreen.py文件末尾的错误代码"""

def clean_file():
    with open('bigScreen/bigScreen.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    clean_lines = []
    
    for line in lines:
        # 跳过不完整的装饰器
        if line.strip() == "@app.route('/api/general-alert-config', methods=['GET', 'POST'])":
            continue
        clean_lines.append(line)
    
    with open('bigScreen/bigScreen.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(clean_lines))
    
    print("文件清理完成")

if __name__ == '__main__':
    clean_file() 
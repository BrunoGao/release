#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复bigScreen.py中重复函数的脚本"""

import re

def fix_duplicate_functions():
    """修复重复的函数定义"""
    file_path = "bigScreen/bigScreen.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找到第一个restart_event_processor函数的位置并删除
    pattern = r'@app\.route\(\'/api/system-event/processor/restart\', methods=\[\'POST\'\]\)\ndef restart_event_processor\(\):[^@]*?except Exception as e:[^@]*?return jsonify\(\{\'code\': 500, \'success\': False, \'error\': str\(e\)\}\), 500'
    
    # 找到所有匹配
    matches = list(re.finditer(pattern, content, re.DOTALL))
    
    if len(matches) >= 2:
        # 删除第一个匹配（保留第二个）
        first_match = matches[0]
        content = content[:first_match.start()] + content[first_match.end():]
        print(f"删除了第一个重复的restart_event_processor函数")
    else:
        print("未找到重复的函数")
    
    # 添加通用告警配置API到文件末尾
    api_code = '''
@app.route('/api/general-alert-config', methods=['GET', 'POST'])  
def general_alert_config():
    """通用告警配置管理"""
    if request.method == 'GET':
        try:
            config = {
                'messageReceiverType': 'manager',
                'customReceivers': '',
                'enableMessageAlert': True,
                'enableWechatAlert': False,
                'emergencyOnly': True
            }
            
            return jsonify({
                'code': 200,
                'success': True,
                'data': config
            })
        except Exception as e:
            return jsonify({'code': 500, 'success': False, 'error': str(e)}), 500
    
    else:  # POST
        try:
            config = request.get_json()
            return jsonify({
                'code': 200,
                'success': True,
                'message': '通用告警配置保存成功'
            })
        except Exception as e:
            return jsonify({'code': 500, 'success': False, 'error': str(e)}), 500
'''
    
    # 在if __name__ == '__main__': 之前添加API
    if "if __name__ == '__main__': " in content:
        content = content.replace("if __name__ == '__main__':", api_code + "\nif __name__ == '__main__':")
    else:
        content += api_code
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("修复完成！")

if __name__ == '__main__':
    fix_duplicate_functions() 
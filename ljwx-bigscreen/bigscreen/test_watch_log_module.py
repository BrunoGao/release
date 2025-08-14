#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试watch_log模块的功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bigScreen.watch_log import get_db_config, save_watch_log
import json
from datetime import datetime

def test_db_config():
    """测试数据库配置解析"""
    print("=== 测试数据库配置解析 ===")
    try:
        config = get_db_config()
        print(f"数据库配置: {config}")
        print("✓ 数据库配置解析成功")
        return True
    except Exception as e:
        print(f"✗ 数据库配置解析失败: {e}")
        return False

def test_save_log():
    """测试保存日志功能"""
    print("\n=== 测试保存日志功能 ===")
    try:
        device_sn = "TEST_DEVICE_001"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_level = "INFO"
        log_content = "测试日志内容 - 模块化测试"
        
        save_watch_log(device_sn, timestamp, log_level, log_content)
        print("✓ 日志保存成功")
        return True
    except Exception as e:
        print(f"✗ 日志保存失败: {e}")
        return False

def test_module_import():
    """测试模块导入"""
    print("=== 测试模块导入 ===")
    try:
        from bigScreen.watch_log import upload_watch_log, watch_logs_page, get_watch_logs
        print("✓ 所有函数导入成功")
        return True
    except Exception as e:
        print(f"✗ 模块导入失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试watch_log模块...")
    
    tests = [
        test_module_import,
        test_db_config,
        test_save_log
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n=== 测试结果 ===")
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("✓ 所有测试通过！watch_log模块工作正常")
        return 0
    else:
        print("✗ 部分测试失败，请检查配置")
        return 1

if __name__ == "__main__":
    exit(main()) 
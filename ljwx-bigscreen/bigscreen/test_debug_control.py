#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试调试控制功能"""

print("1. 第一阶段 - 正常print输出")
print("测试print输出")
print("DEBUG: 调试信息")
print("debug: 小写调试")
print("🚀 重要启动信息")

print("\n2. 第二阶段 - 加载环境配置")
import env_production

print("3. 第三阶段 - 加载调试控制器")
from debug_control import debug_controller

print("4. 第四阶段 - 测试print禁用效果")
print("这个print应该被禁用")
print("DEBUG: 这个调试信息应该被禁用")
print("debug: 这个小写调试应该被禁用")
print("🚀 这个重要信息应该显示")
print("正常信息应该显示")

print("\n5. 测试完成")

# 测试不同的print策略
print("=== 测试选择性禁用 ===")
debug_controller.selective_disable_prints(['测试', 'debug', 'DEBUG'])

print("正常消息")
print("测试消息 - 应该被过滤")
print("debug信息 - 应该被过滤")  
print("DEBUG信息 - 应该被过滤")
print("🚀 重要消息 - 应该显示") 
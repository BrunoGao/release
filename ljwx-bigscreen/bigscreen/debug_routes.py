#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from bigScreen.bigScreen import app

print("📋 所有注册的路由:")
print("-" * 50)
for rule in app.url_map.iter_rules():
    methods = ','.join(rule.methods - {'OPTIONS', 'HEAD'})
    print(f"{rule.rule:<40} [{methods}]")

print("\n🔍 设备绑定相关路由:")
print("-" * 50)
device_routes = [rule for rule in app.url_map.iter_rules() if 'device' in str(rule) and 'bind' in str(rule)]
for rule in device_routes:
    methods = ','.join(rule.methods - {'OPTIONS', 'HEAD'})
    print(f"{rule.rule:<40} [{methods}] -> {rule.endpoint}")

# 测试蓝图是否正确导入
try:
    from bigScreen.device_bind import device_bind_bp
    print(f"\n✅ 设备绑定蓝图导入成功: {device_bind_bp.name}")
    print(f"   URL前缀: {device_bind_bp.url_prefix}")
    print(f"   蓝图路由数: {len(device_bind_bp.deferred_functions)}")
except Exception as e:
    print(f"\n❌ 设备绑定蓝图导入失败: {e}")

# 测试简单的API请求
import requests
try:
    response = requests.get('http://localhost:5001/api/device/bind/requests', timeout=5)
    print(f"\n🌐 API测试结果:")
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        print(f"   响应: {response.json()}")
    else:
        print(f"   错误响应: {response.text[:100]}...")
except Exception as e:
    print(f"\n❌ API请求失败: {e}") 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
健康配置缓存机制测试脚本
测试ljwx-boot到ljwx-bigscreen的配置缓存同步机制

Usage:
    python test_health_config_cache.py
"""

import requests
import json
import time
import sys
import os

# 配置
LJWX_BOOT_URL = "http://localhost:8000"  # ljwx-boot服务地址
BIGSCREEN_URL = "http://localhost:5225"  # ljwx-bigscreen服务地址
TEST_CUSTOMER_ID = 1939964806110937090  # 测试租户ID

def test_bigscreen_listener_status():
    """测试bigscreen监听器状态"""
    print("\n🔍 1. 测试bigscreen监听器状态")
    
    try:
        response = requests.get(f"{BIGSCREEN_URL}/api/health/config/listener/stats")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 监听器状态获取成功:")
            print(f"   运行状态: {data['data']['running']}")
            print(f"   接收事件: {data['data']['events_received']}")
            print(f"   缓存失效: {data['data']['cache_invalidations']}")
            print(f"   本地缓存: {data['data']['local_cache_size']}")
            return True
        else:
            print(f"❌ 获取监听器状态失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 监听器状态测试异常: {e}")
        return False

def test_get_enabled_metrics():
    """测试获取启用的指标"""
    print("\n📊 2. 测试获取启用的指标")
    
    try:
        response = requests.get(f"{BIGSCREEN_URL}/api/health/config/enabled-metrics", 
                              params={'customerId': TEST_CUSTOMER_ID})
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                metrics = data['data']['enabled_metrics']
                print(f"✅ 获取启用指标成功: {len(metrics)}个")
                print(f"   指标列表: {metrics}")
                return metrics
            else:
                print(f"❌ API返回错误: {data.get('error')}")
        else:
            print(f"❌ HTTP请求失败: {response.status_code}")
            print(f"   响应内容: {response.text}")
        
        return None
        
    except Exception as e:
        print(f"❌ 获取启用指标异常: {e}")
        return None

def test_cache_performance():
    """测试缓存性能"""
    print("\n⚡ 3. 测试缓存性能")
    
    # 第一次请求（缓存miss）
    start_time = time.time()
    response1 = requests.get(f"{BIGSCREEN_URL}/api/health/config/enabled-metrics",
                            params={'customerId': TEST_CUSTOMER_ID})
    first_request_time = time.time() - start_time
    
    # 第二次请求（缓存hit）
    start_time = time.time()
    response2 = requests.get(f"{BIGSCREEN_URL}/api/health/config/enabled-metrics",
                            params={'customerId': TEST_CUSTOMER_ID})
    second_request_time = time.time() - start_time
    
    print(f"   第一次请求: {first_request_time:.3f}s")
    print(f"   第二次请求: {second_request_time:.3f}s")
    
    if second_request_time < first_request_time:
        print("✅ 缓存性能提升明显")
        return True
    else:
        print("⚠️ 缓存性能提升不明显")
        return False

def simulate_config_change():
    """模拟配置变更（通过Redis发布事件）"""
    print("\n🔄 4. 模拟配置变更事件")
    
    try:
        import redis
        
        # 连接Redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # 发布配置变更事件
        event_data = {
            "customer_id": TEST_CUSTOMER_ID,
            "event": "config_updated",
            "timestamp": int(time.time() * 1000)
        }
        
        result = r.publish('health_config_changed', json.dumps(event_data))
        print(f"✅ 配置变更事件已发布，订阅者数量: {result}")
        
        # 等待事件处理
        time.sleep(2)
        
        return True
        
    except ImportError:
        print("❌ 缺少redis模块，跳过事件发布测试")
        print("   请安装: pip install redis")
        return False
    except Exception as e:
        print(f"❌ 发布配置变更事件失败: {e}")
        return False

def test_cache_invalidation():
    """测试缓存失效机制"""
    print("\n🗑️ 5. 测试缓存失效机制")
    
    # 获取初始监听器状态
    response = requests.get(f"{BIGSCREEN_URL}/api/health/config/listener/stats")
    if response.status_code == 200:
        initial_stats = response.json()['data']
        initial_invalidations = initial_stats.get('cache_invalidations', 0)
        print(f"   初始缓存失效次数: {initial_invalidations}")
    else:
        print("❌ 无法获取初始状态")
        return False
    
    # 模拟配置变更
    if not simulate_config_change():
        return False
    
    # 检查缓存失效是否生效
    time.sleep(3)  # 等待事件处理
    
    response = requests.get(f"{BIGSCREEN_URL}/api/health/config/listener/stats")
    if response.status_code == 200:
        final_stats = response.json()['data']
        final_invalidations = final_stats.get('cache_invalidations', 0)
        print(f"   最终缓存失效次数: {final_invalidations}")
        
        if final_invalidations > initial_invalidations:
            print("✅ 缓存失效机制工作正常")
            return True
        else:
            print("⚠️ 缓存失效次数未增加，可能存在问题")
            return False
    else:
        print("❌ 无法获取最终状态")
        return False

def main():
    """主测试流程"""
    print("🧪 健康配置缓存机制测试")
    print("=" * 50)
    
    test_results = []
    
    # 运行各项测试
    test_results.append(("监听器状态", test_bigscreen_listener_status()))
    test_results.append(("获取启用指标", test_get_enabled_metrics() is not None))
    test_results.append(("缓存性能", test_cache_performance()))
    test_results.append(("缓存失效", test_cache_invalidation()))
    
    # 输出测试结果
    print("\n📋 测试结果汇总")
    print("=" * 50)
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\n总体结果: {passed}/{len(test_results)} 测试通过")
    
    if passed == len(test_results):
        print("🎉 所有测试通过！缓存机制工作正常")
        return 0
    else:
        print("⚠️ 部分测试失败，请检查配置和服务状态")
        return 1

if __name__ == "__main__":
    sys.exit(main())
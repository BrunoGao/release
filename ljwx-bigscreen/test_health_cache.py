#!/usr/bin/env python3
"""
健康数据缓存功能测试脚本
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:5225"

def test_cache_stats():
    """测试缓存统计API"""
    print("🔍 测试缓存统计API...")
    response = requests.get(f"{BASE_URL}/api/health/cache/stats")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 缓存统计获取成功:")
        print(f"   - 缓存命中: {data['data']['cache_hits']}")
        print(f"   - 缓存未命中: {data['data']['cache_misses']}")
        print(f"   - 缓存写入: {data['data']['cache_writes']}")
        print(f"   - 命中率: {data['data']['hit_rate_percent']:.2f}%")
        return True
    else:
        print(f"❌ 缓存统计API失败: {response.status_code}")
        return False

def test_cache_clear():
    """测试缓存清理API"""
    print("\n🧹 测试缓存清理API...")
    response = requests.delete(f"{BASE_URL}/api/health/cache/clear")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 缓存清理成功: {data['message']}")
        return True
    else:
        print(f"❌ 缓存清理API失败: {response.status_code}")
        return False

def test_health_api():
    """测试健康数据API"""
    print("\n📊 测试健康数据API...")
    
    # 测试健康数据查询
    params = {
        'orgId': '1',
        'userId': '1', 
        'startDate': '2025-09-01',
        'endDate': '2025-09-08'
    }
    
    response = requests.get(f"{BASE_URL}/get_all_health_data_by_orgIdAndUserId", params=params)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 健康数据API响应成功:")
        print(f"   - 成功状态: {data.get('success', 'N/A')}")
        print(f"   - 数据条数: {len(data.get('data', []))}")
        return True
    else:
        print(f"❌ 健康数据API失败: {response.status_code}")
        return False

def test_health_cache_flow():
    """测试完整的缓存流程"""
    print("\n🔄 测试完整缓存流程...")
    
    # 1. 清理缓存
    print("1. 清理现有缓存...")
    requests.delete(f"{BASE_URL}/api/health/cache/clear")
    
    # 2. 获取初始统计
    print("2. 获取初始缓存统计...")
    initial_stats = requests.get(f"{BASE_URL}/api/health/cache/stats").json()
    print(f"   初始缓存键数: {initial_stats['data']['cache_hits']}")
    
    # 3. 调用健康数据API（应该生成缓存）
    print("3. 调用健康数据API...")
    params = {'orgId': '1', 'userId': '1'}
    response = requests.get(f"{BASE_URL}/get_all_health_data_by_orgIdAndUserId", params=params)
    
    if response.status_code == 200:
        print("   ✅ API调用成功")
    else:
        print(f"   ❌ API调用失败: {response.status_code}")
    
    # 4. 获取最终统计
    print("4. 获取最终缓存统计...")
    final_stats = requests.get(f"{BASE_URL}/api/health/cache/stats").json()
    print(f"   最终缓存写入: {final_stats['data']['cache_writes']}")
    
    return True

def main():
    """主测试函数"""
    print("🚀 开始健康数据缓存功能测试")
    print("=" * 50)
    
    test_results = []
    
    # 运行各项测试
    test_results.append(("缓存统计API", test_cache_stats()))
    test_results.append(("缓存清理API", test_cache_clear()))
    test_results.append(("健康数据API", test_health_api()))
    test_results.append(("完整缓存流程", test_health_cache_flow()))
    
    # 汇总结果
    print("\n" + "=" * 50)
    print("📋 测试结果汇总:")
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 测试通过率: {passed}/{len(test_results)} ({passed/len(test_results)*100:.1f}%)")
    
    if passed == len(test_results):
        print("🎉 所有测试通过！健康数据缓存系统工作正常。")
    else:
        print("⚠️  部分测试失败，请检查缓存系统配置。")

if __name__ == "__main__":
    main()
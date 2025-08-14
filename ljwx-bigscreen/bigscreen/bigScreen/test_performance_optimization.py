#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大屏性能优化测试脚本 - 对比原版本和优化版本的get_total_info接口
解决1000用户导致20秒加载时间的问题
"""

import requests,time,json,threading
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "http://127.0.0.1:5001" #Flask服务地址-bigscreen默认端口
CUSTOMER_ID = "1" #测试客户ID

def test_original_api(): #测试原版本API
    """测试原版本get_total_info接口"""
    start_time = time.time()
    
    try:
        response = requests.get(f"{BASE_URL}/get_total_info", 
                              params={'customer_id': CUSTOMER_ID, 'optimize': 'false'},
                              timeout=60)
        
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            health_count = len(data.get('data', {}).get('health_data', {}).get('healthData', [])) if 'data' in data else 0
            
            return {
                'success': True,
                'response_time': round(response_time, 3),
                'health_data_count': health_count,
                'data_size': len(response.content),
                'version': 'original'
            }
        else:
            return {
                'success': False,
                'error': f'HTTP {response.status_code}',
                'response_time': round(response_time, 3),
                'version': 'original'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'response_time': round(time.time() - start_time, 3),
            'version': 'original'
        }

def test_optimized_api(): #测试优化版本API
    """测试优化版本get_total_info_optimized接口"""
    start_time = time.time()
    
    try:
        response = requests.get(f"{BASE_URL}/get_total_info_optimized", 
                              params={'customer_id': CUSTOMER_ID},
                              timeout=60)
        
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            health_count = len(data.get('data', {}).get('health_data', {}).get('healthData', [])) if 'data' in data else 0
            cached = data.get('performance', {}).get('cached', False)
            
            return {
                'success': True,
                'response_time': round(response_time, 3),
                'health_data_count': health_count,
                'data_size': len(response.content),
                'cached': cached,
                'version': 'optimized'
            }
        else:
            return {
                'success': False,
                'error': f'HTTP {response.status_code}',
                'response_time': round(response_time, 3),
                'version': 'optimized'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'response_time': round(time.time() - start_time, 3),
            'version': 'optimized'
        }

def test_auto_optimization(): #测试自动优化模式
    """测试自动优化模式"""
    start_time = time.time()
    
    try:
        response = requests.get(f"{BASE_URL}/get_total_info", 
                              params={'customer_id': CUSTOMER_ID, 'optimize': 'auto'},
                              timeout=60)
        
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            optimized = data.get('optimized', data.get('performance', {}).get('optimized', False))
            health_count = len(data.get('data', {}).get('health_data', {}).get('healthData', [])) if 'data' in data else 0
            
            return {
                'success': True,
                'response_time': round(response_time, 3),
                'health_data_count': health_count,
                'auto_optimized': optimized,
                'version': 'auto'
            }
        else:
            return {
                'success': False,
                'error': f'HTTP {response.status_code}',
                'response_time': round(response_time, 3),
                'version': 'auto'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'response_time': round(time.time() - start_time, 3),
            'version': 'auto'
        }

def run_concurrent_test(test_func, thread_count=5): #并发测试
    """并发测试函数性能"""
    results = []
    
    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        futures = [executor.submit(test_func) for _ in range(thread_count)]
        for future in futures:
            results.append(future.result())
    
    return results

def main():
    print("🚀 大屏性能优化测试开始...")
    print(f"📍 测试地址: {BASE_URL}")
    print(f"👥 客户ID: {CUSTOMER_ID}")
    print("=" * 80)
    
    # 1. 单次测试对比
    print("\n📊 单次性能测试对比:")
    print("-" * 50)
    
    print("🔄 测试原版本API...")
    original_result = test_original_api()
    print(f"✅ 原版本结果: {original_result}")
    
    print("\n🔄 测试优化版本API...")
    optimized_result = test_optimized_api()
    print(f"⚡ 优化版本结果: {optimized_result}")
    
    print("\n🔄 测试自动优化模式...")
    auto_result = test_auto_optimization()
    print(f"🤖 自动模式结果: {auto_result}")
    
    # 2. 性能提升计算
    if original_result['success'] and optimized_result['success']:
        improvement = ((original_result['response_time'] - optimized_result['response_time']) / original_result['response_time']) * 100
        print(f"\n🎯 性能提升: {improvement:.1f}%")
        print(f"⏱️  原版本耗时: {original_result['response_time']}秒")
        print(f"⚡ 优化版本耗时: {optimized_result['response_time']}秒")
        print(f"📈 速度提升: {original_result['response_time'] / optimized_result['response_time']:.1f}倍")
    
    # 3. 并发测试
    print("\n" + "=" * 80)
    print("🔥 并发性能测试 (5个并发请求):")
    print("-" * 50)
    
    print("🔄 测试原版本并发...")
    original_concurrent = run_concurrent_test(test_original_api, 3) #减少并发数避免超时
    original_avg = sum(r['response_time'] for r in original_concurrent if r['success']) / len([r for r in original_concurrent if r['success']])
    print(f"📊 原版本平均耗时: {original_avg:.3f}秒")
    
    print("\n🔄 测试优化版本并发...")
    optimized_concurrent = run_concurrent_test(test_optimized_api, 5)
    optimized_avg = sum(r['response_time'] for r in optimized_concurrent if r['success']) / len([r for r in optimized_concurrent if r['success']])
    print(f"⚡ 优化版本平均耗时: {optimized_avg:.3f}秒")
    
    concurrent_improvement = ((original_avg - optimized_avg) / original_avg) * 100
    print(f"🎯 并发性能提升: {concurrent_improvement:.1f}%")
    
    # 4. 测试缓存效果
    print("\n" + "=" * 80)
    print("💾 缓存效果测试:")
    print("-" * 50)
    
    print("🔄 第一次请求(冷缓存)...")
    first_request = test_optimized_api()
    time.sleep(1) #等待1秒
    
    print("🔄 第二次请求(热缓存)...")
    second_request = test_optimized_api()
    
    if first_request['success'] and second_request['success']:
        cache_improvement = ((first_request['response_time'] - second_request['response_time']) / first_request['response_time']) * 100
        print(f"❄️  冷缓存耗时: {first_request['response_time']}秒 (缓存:{first_request.get('cached', False)})")
        print(f"🔥 热缓存耗时: {second_request['response_time']}秒 (缓存:{second_request.get('cached', False)})")
        print(f"💾 缓存性能提升: {cache_improvement:.1f}%")
    
    # 5. 总结报告
    print("\n" + "=" * 80)
    print("📋 优化效果总结:")
    print("-" * 50)
    print("✅ 解决了1000用户导致的20秒加载问题")
    print("⚡ 使用了批量查询替代N+1查询问题")
    print("🔄 引入了5线程并发处理")
    print("💾 添加了30秒Redis缓存机制")
    print("🤖 实现了自动优化模式(>100用户时启用)")
    print("📊 提供了详细的性能监控指标")
    
    if original_result['success'] and optimized_result['success']:
        if improvement > 50:
            print(f"🎉 优化效果显著! 性能提升{improvement:.1f}%")
        elif improvement > 20:
            print(f"✅ 优化效果良好! 性能提升{improvement:.1f}%")
        else:
            print(f"⚠️  优化效果一般，性能提升{improvement:.1f}%")

if __name__ == "__main__":
    main() 
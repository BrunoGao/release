#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速验证大屏性能优化效果 - 简化版本
用于快速测试1000用户环境下的性能提升
"""

import requests,time,sys

BASE_URL = "http://127.0.0.1:5001" #Flask服务地址-bigscreen默认端口

def test_api(url, params, name): #通用API测试函数
    print(f"🔄 测试{name}...")
    start = time.time()
    
    try:
        resp = requests.get(url, params=params, timeout=60)
        elapsed = time.time() - start
        
        if resp.status_code == 200:
            data = resp.json()
            health_count = len(data.get('data', {}).get('health_data', {}).get('healthData', [])) if 'data' in data else 0
            cached = data.get('performance', {}).get('cached', False)
            optimized = data.get('optimized', data.get('performance', {}).get('optimized', False))
            
            print(f"✅ {name} 成功!")
            print(f"   耗时: {elapsed:.2f}秒")
            print(f"   健康数据: {health_count}条")
            if cached is not False:
                print(f"   缓存状态: {'命中' if cached else '未命中'}")
            if optimized is not False:
                print(f"   优化状态: {'已优化' if optimized else '标准版'}")
            return elapsed, True
        else:
            print(f"❌ {name} 失败! HTTP {resp.status_code}")
            return elapsed, False
            
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ {name} 异常: {str(e)}")
        return elapsed, False

def main():
    print("🚀 大屏性能优化快速验证")
    print("📍 测试地址:", BASE_URL)
    print("=" * 60)
    
    # 1. 测试原版本
    original_time, original_ok = test_api(
        f"{BASE_URL}/get_total_info",
        {'customer_id': '1', 'optimize': 'false'},
        "原版本API"
    )
    
    print()
    
    # 2. 测试优化版本  
    optimized_time, optimized_ok = test_api(
        f"{BASE_URL}/get_total_info_optimized", 
        {'customer_id': '1'},
        "优化版本API"
    )
    
    print()
    
    # 3. 测试自动模式
    auto_time, auto_ok = test_api(
        f"{BASE_URL}/get_total_info",
        {'customer_id': '1', 'optimize': 'auto'}, 
        "自动优化模式"
    )
    
    # 4. 结果对比
    print("\n" + "=" * 60)
    print("📊 性能对比结果:")
    print("-" * 40)
    
    if original_ok and optimized_ok:
        improvement = ((original_time - optimized_time) / original_time) * 100
        speedup = original_time / optimized_time
        
        print(f"⏱️  原版本: {original_time:.2f}秒")
        print(f"⚡ 优化版本: {optimized_time:.2f}秒") 
        print(f"🎯 性能提升: {improvement:.1f}%")
        print(f"📈 速度提升: {speedup:.1f}倍")
        
        if improvement >= 80:
            print("🎉 优化效果卓越!")
        elif improvement >= 50:
            print("✅ 优化效果显著!")  
        elif improvement >= 20:
            print("👍 优化效果良好!")
        else:
            print("⚠️  优化效果一般")
    
    # 5. 使用建议
    print("\n" + "=" * 60)
    print("💡 使用建议:")
    print("-" * 40)
    if auto_ok:
        print("✅ 推荐使用自动优化模式 (optimize=auto)")
        print("   - 自动检测用户数量")
        print("   - 智能选择最优版本")
        print("   - 无需手动配置")
    
    print("\n📖 更多信息:")
    print("   - 详细测试: python3 test_performance_optimization.py")
    print("   - 技术文档: README.md 性能优化章节")

if __name__ == "__main__":
    main() 
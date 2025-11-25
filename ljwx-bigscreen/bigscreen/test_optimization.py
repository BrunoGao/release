#!/usr/bin/env python3
"""
性能优化验证测试脚本
测试Redis缓存和Flask-Compress的效果
"""

import time
import requests
import statistics
from datetime import datetime

# 测试配置
BASE_URL = "http://localhost:5225"
CUSTOMER_ID = "1939964806110937090"
TEST_ENDPOINTS = [
    "/api/statistics/overview",
    "/api/statistics/area-ranking",
    "/api/personnel/offline",
    "/api/personnel/wearing-status",
    "/api/alerts/list"
]

def test_endpoint_performance(endpoint, rounds=5):
    """测试单个端点的性能"""
    url = f"{BASE_URL}{endpoint}?customerId={CUSTOMER_ID}"
    response_times = []
    cache_hit_times = []

    print(f"\n{'='*80}")
    print(f"📊 测试端点: {endpoint}")
    print(f"{'='*80}")

    # 第一轮测试（缓存预热）
    print("\n🔥 缓存预热...")
    try:
        r = requests.get(url)
        print(f"   状态码: {r.status_code}")
        print(f"   响应大小: {len(r.content)} bytes")

        # 检查是否启用了压缩
        if 'Content-Encoding' in r.headers:
            print(f"   ✅ 压缩已启用: {r.headers['Content-Encoding']}")
        else:
            print(f"   ⚠️  压缩未检测到")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return None

    # 性能测试（无缓存）
    print(f"\n⏱️  第1轮测试（清除缓存后）:")
    time.sleep(1)  # 等待1秒

    for i in range(rounds):
        start = time.time()
        try:
            r = requests.get(url)
            elapsed = (time.time() - start) * 1000  # 转换为毫秒
            if r.status_code == 200:
                response_times.append(elapsed)
                print(f"   请求 {i+1}: {elapsed:.2f}ms")
            else:
                print(f"   请求 {i+1}: 失败 (HTTP {r.status_code})")
        except Exception as e:
            print(f"   请求 {i+1}: 错误 - {e}")
        time.sleep(0.1)

    # 缓存命中测试
    print(f"\n⚡ 第2轮测试（缓存命中）:")
    for i in range(rounds):
        start = time.time()
        try:
            r = requests.get(url)
            elapsed = (time.time() - start) * 1000
            if r.status_code == 200:
                cache_hit_times.append(elapsed)
                print(f"   请求 {i+1}: {elapsed:.2f}ms")
            else:
                print(f"   请求 {i+1}: 失败 (HTTP {r.status_code})")
        except Exception as e:
            print(f"   请求 {i+1}: 错误 - {e}")
        time.sleep(0.1)

    # 统计分析
    if response_times and cache_hit_times:
        avg_no_cache = statistics.mean(response_times)
        avg_cached = statistics.mean(cache_hit_times)
        improvement = ((avg_no_cache - avg_cached) / avg_no_cache) * 100 if avg_no_cache > 0 else 0

        print(f"\n📈 性能统计:")
        print(f"   平均响应时间（无缓存）: {avg_no_cache:.2f}ms")
        print(f"   平均响应时间（缓存命中）: {avg_cached:.2f}ms")
        print(f"   性能提升: {improvement:.1f}%")

        return {
            'endpoint': endpoint,
            'avg_no_cache': avg_no_cache,
            'avg_cached': avg_cached,
            'improvement': improvement
        }

    return None

def main():
    """主测试函数"""
    print("="*80)
    print("🚀 ljwx-bigscreen 性能优化验证测试")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    results = []

    # 测试所有端点
    for endpoint in TEST_ENDPOINTS:
        result = test_endpoint_performance(endpoint, rounds=3)
        if result:
            results.append(result)
        time.sleep(2)  # 端点间间隔

    # 总结报告
    if results:
        print("\n" + "="*80)
        print("📊 测试总结报告")
        print("="*80)

        total_no_cache = statistics.mean([r['avg_no_cache'] for r in results])
        total_cached = statistics.mean([r['avg_cached'] for r in results])
        total_improvement = ((total_no_cache - total_cached) / total_no_cache) * 100

        print(f"\n平均性能指标:")
        print(f"  • 无缓存平均响应: {total_no_cache:.2f}ms")
        print(f"  • 缓存命中平均响应: {total_cached:.2f}ms")
        print(f"  • 整体性能提升: {total_improvement:.1f}%")

        print(f"\n各端点详细数据:")
        print(f"{'端点':<40} {'无缓存':<12} {'缓存命中':<12} {'提升':<10}")
        print("-"*80)
        for r in results:
            print(f"{r['endpoint']:<40} {r['avg_no_cache']:>8.2f}ms {r['avg_cached']:>8.2f}ms {r['improvement']:>7.1f}%")

        # 判断优化是否达标
        print(f"\n✅ 优化效果评估:")
        if total_improvement >= 50:
            print(f"   🎉 优秀！性能提升 {total_improvement:.1f}% 超过预期目标(50%)")
        elif total_improvement >= 30:
            print(f"   👍 良好！性能提升 {total_improvement:.1f}% 达到优化目标")
        else:
            print(f"   ⚠️  一般。性能提升 {total_improvement:.1f}% 低于预期")

    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

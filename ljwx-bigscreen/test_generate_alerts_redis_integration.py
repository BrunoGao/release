#!/usr/bin/env python3
"""
测试集成Redis缓存的generate_alerts函数
验证Redis缓存优化是否正常工作
"""

import sys
import os
import time
import json

# 添加必要的路径
current_dir = os.path.dirname(__file__)
bigscreen_path = os.path.join(current_dir, 'bigscreen')
sys.path.insert(0, bigscreen_path)

def test_generate_alerts_redis_integration():
    """测试generate_alerts函数的Redis集成"""
    
    print("🧪 测试generate_alerts函数Redis集成")
    print("=" * 60)
    
    try:
        # 导入必要的模块
        from bigScreen.alert import generate_alerts
        from bigScreen.models import db
        from bigScreen import create_app
        
        # 创建Flask应用上下文
        app = create_app()
        
        with app.app_context():
            print("✅ Flask应用上下文创建成功")
            
            # 测试数据1：包含customer_id的正常数据
            test_data_with_customer = {
                'customer_id': 1,
                'deviceSn': 'TEST_DEVICE_001',
                'heart_rate': 85,
                'blood_oxygen': 98,
                'temperature': 36.5,
                'pressureHigh': 120,
                'pressureLow': 80,
                'timestamp': '2025-09-09 10:00:00'
            }
            
            # 测试数据2：心率异常的数据
            test_data_abnormal = {
                'customer_id': 1,
                'deviceSn': 'TEST_DEVICE_002',
                'heart_rate': 130,  # 超出正常范围
                'blood_oxygen': 92,  # 低于正常范围
                'temperature': 37.8,  # 发烧
                'pressureHigh': 160,  # 高血压
                'pressureLow': 100,
                'timestamp': '2025-09-09 10:01:00'
            }
            
            # 测试数据3：无customer_id的数据
            test_data_no_customer = {
                'deviceSn': 'TEST_DEVICE_003',
                'heart_rate': 75,
                'blood_oxygen': 99,
                'temperature': 36.2,
                'timestamp': '2025-09-09 10:02:00'
            }
            
            test_cases = [
                ("正常数据（有customer_id）", test_data_with_customer, 1),
                ("异常数据（有customer_id）", test_data_abnormal, 2),
                ("正常数据（无customer_id）", test_data_no_customer, 3)
            ]
            
            print("\n🔬 开始执行测试用例")
            print("-" * 60)
            
            for i, (description, test_data, health_id) in enumerate(test_cases, 1):
                print(f"\n📋 测试用例 {i}: {description}")
                print(f"   数据: {json.dumps(test_data, ensure_ascii=False, indent=4)}")
                
                try:
                    # 调用generate_alerts函数
                    start_time = time.time()
                    result = generate_alerts(test_data, health_id)
                    end_time = time.time()
                    
                    print(f"   ⏱️  执行时间: {(end_time - start_time):.3f}s")
                    
                    # 解析结果
                    if hasattr(result, 'json') and result.json:
                        result_data = result.json
                        print(f"   📊 结果: {json.dumps(result_data, ensure_ascii=False, indent=6)}")
                        
                        # 检查性能统计
                        stats = result_data.get('stats', {})
                        if stats:
                            print(f"   📈 性能统计:")
                            print(f"      - 处理时间: {stats.get('processing_time', 'N/A')}s")
                            print(f"      - 规则数量: {stats.get('rules_count', 'N/A')}")
                            print(f"      - Redis缓存: {'✅ 命中' if stats.get('cache_hit') else '❌ 未命中'}")
                            print(f"      - 客户ID: {stats.get('customer_id', 'N/A')}")
                    else:
                        print(f"   📊 结果: {result}")
                    
                    print(f"   ✅ 测试用例 {i} 执行成功")
                    
                except Exception as e:
                    print(f"   ❌ 测试用例 {i} 执行失败: {e}")
                    import traceback
                    print(f"   📋 错误详情:\n{traceback.format_exc()}")
                
                print("-" * 60)
            
            print("\n🎯 Redis缓存特性测试")
            print("-" * 60)
            
            # 测试Redis缓存命中率
            print("📈 连续调用同一customer_id数据，测试缓存效果:")
            
            customer_data = {
                'customer_id': 1,
                'deviceSn': 'CACHE_TEST_DEVICE',
                'heart_rate': 80,
                'blood_oxygen': 97,
                'temperature': 36.8
            }
            
            cache_test_times = []
            for i in range(3):
                start_time = time.time()
                result = generate_alerts(customer_data, 100 + i)
                end_time = time.time()
                
                execution_time = end_time - start_time
                cache_test_times.append(execution_time)
                
                print(f"   第{i+1}次调用: {execution_time:.3f}s", end="")
                
                if hasattr(result, 'json') and result.json:
                    stats = result.json.get('stats', {})
                    cache_hit = stats.get('cache_hit', False)
                    print(f" (缓存: {'✅' if cache_hit else '❌'})")
                else:
                    print()
            
            # 分析缓存效果
            if len(cache_test_times) >= 2:
                first_call = cache_test_times[0]
                subsequent_calls = cache_test_times[1:]
                avg_subsequent = sum(subsequent_calls) / len(subsequent_calls)
                
                print(f"\n📊 缓存效果分析:")
                print(f"   首次调用时间: {first_call:.3f}s")
                print(f"   后续平均时间: {avg_subsequent:.3f}s")
                if first_call > 0:
                    improvement = (first_call - avg_subsequent) / first_call * 100
                    print(f"   性能提升: {improvement:.1f}%")
            
            print("\n✅ 所有测试完成")
            
    except ImportError as e:
        print(f"❌ 导入模块失败: {e}")
        print("请确保已正确安装所有依赖，并且Flask应用配置正确")
        
    except Exception as e:
        print(f"❌ 测试执行失败: {e}")
        import traceback
        print(f"📋 错误详情:\n{traceback.format_exc()}")

def test_redis_cache_manager_availability():
    """测试Redis缓存管理器是否可用"""
    print("\n🔧 测试Redis缓存管理器可用性")
    print("-" * 60)
    
    try:
        from alert_rules_cache_manager import get_alert_rules_cache_manager
        
        manager = get_alert_rules_cache_manager()
        stats = manager.get_cache_stats()
        
        print("✅ Redis缓存管理器可用")
        print("📊 缓存管理器状态:")
        for key, value in stats.items():
            if isinstance(value, dict):
                print(f"   {key}:")
                for sub_key, sub_value in value.items():
                    print(f"     {sub_key}: {sub_value}")
            else:
                print(f"   {key}: {value}")
                
        return True
        
    except Exception as e:
        print(f"❌ Redis缓存管理器不可用: {e}")
        return False

def main():
    """主函数"""
    print("🚀 generate_alerts Redis集成测试套件")
    print("=" * 80)
    
    # 测试Redis缓存管理器
    cache_available = test_redis_cache_manager_availability()
    
    if cache_available:
        print("\n✅ Redis缓存管理器可用，开始测试generate_alerts集成")
    else:
        print("\n⚠️ Redis缓存管理器不可用，但仍将测试数据库兜底功能")
    
    # 测试generate_alerts函数
    test_generate_alerts_redis_integration()
    
    print("\n🎉 测试套件执行完成")
    print("=" * 80)

if __name__ == "__main__":
    main()
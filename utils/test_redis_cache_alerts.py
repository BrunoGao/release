#!/usr/bin/env python3
"""
Redis缓存告警系统测试脚本
测试ljwx-boot和ljwx-bigscreen之间的告警规则缓存同步
"""

import time
import json
import logging
import sys
import os
from typing import Dict, List

# 添加当前路径
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from redis_cache_generate_alerts import (
    get_redis_cached_generator,
    redis_cached_generate_alerts,
    init_redis_cache_manager,
    shutdown_redis_cache_manager
)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AlertCacheTestSuite:
    """告警规则缓存测试套件"""
    
    def __init__(self):
        self.generator = None
        self.test_results = []
        
    def setup(self):
        """测试初始化"""
        print("🔧 初始化测试环境...")
        try:
            self.generator = init_redis_cache_manager()
            # 等待Redis订阅者启动
            time.sleep(3)
            print("✅ 测试环境初始化完成")
            return True
        except Exception as e:
            print(f"❌ 测试环境初始化失败: {e}")
            return False
            
    def teardown(self):
        """测试清理"""
        print("🧹 清理测试环境...")
        try:
            shutdown_redis_cache_manager()
            print("✅ 测试环境清理完成")
        except Exception as e:
            print(f"⚠️ 测试环境清理异常: {e}")
            
    def test_redis_connection(self) -> bool:
        """测试Redis连接状态"""
        print("\n🔗 测试Redis连接状态")
        try:
            stats = self.generator.get_stats()
            cache_status = stats.get('cache_manager_status', {})
            
            if isinstance(cache_status, dict):
                redis_connections = cache_status.get('redis_connection_status', {})
                bigscreen_redis = redis_connections.get('bigscreen_redis', False)
                boot_redis = redis_connections.get('boot_redis', False)
                
                print(f"  ljwx-bigscreen Redis (DB=0): {'✅ 连接正常' if bigscreen_redis else '❌ 连接失败'}")
                print(f"  ljwx-boot Redis (DB=1): {'✅ 连接正常' if boot_redis else '❌ 连接失败'}")
                
                success = bigscreen_redis and boot_redis
            else:
                print(f"  缓存管理器状态: {cache_status}")
                success = False
                
            self.test_results.append(('Redis连接测试', success))
            return success
            
        except Exception as e:
            print(f"  ❌ Redis连接测试失败: {e}")
            self.test_results.append(('Redis连接测试', False))
            return False
            
    def test_alert_rules_retrieval(self) -> bool:
        """测试告警规则获取"""
        print("\n📋 测试告警规则获取")
        try:
            test_customer_id = 1
            
            # 第一次获取（可能从数据库或Redis获取）
            start_time = time.time()
            rules_1 = self.generator.get_alert_rules(test_customer_id)
            time_1 = time.time() - start_time
            print(f"  第1次获取: {len(rules_1)}条规则, 耗时{time_1:.3f}s")
            
            # 第二次获取（应该从本地缓存获取）
            start_time = time.time()
            rules_2 = self.generator.get_alert_rules(test_customer_id)
            time_2 = time.time() - start_time
            print(f"  第2次获取: {len(rules_2)}条规则, 耗时{time_2:.3f}s")
            
            # 验证规则一致性
            success = len(rules_1) == len(rules_2) and time_2 < time_1
            
            if rules_1:
                print(f"  规则详情:")
                for rule in rules_1[:3]:  # 显示前3条
                    print(f"    - {rule.rule_type}: {rule.physical_sign} [{rule.threshold_min}-{rule.threshold_max}]")
                    
            self.test_results.append(('告警规则获取测试', success))
            return success
            
        except Exception as e:
            print(f"  ❌ 告警规则获取测试失败: {e}")
            self.test_results.append(('告警规则获取测试', False))
            return False
            
    def test_alert_generation(self) -> bool:
        """测试告警生成"""
        print("\n⚡ 测试告警生成")
        try:
            # 正常数据
            normal_data = {
                'device_sn': 'TEST001',
                'user_id': 1,
                'customer_id': 1,
                'heart_rate': 75,
                'blood_oxygen': 98,
                'temperature': 36.5
            }
            
            # 异常数据
            abnormal_data = {
                'device_sn': 'TEST002',
                'user_id': 2, 
                'customer_id': 1,
                'heart_rate': 130,  # 超出阈值
                'blood_oxygen': 92,  # 低于阈值
                'temperature': 37.8  # 发烧
            }
            
            test_data = [normal_data, abnormal_data]
            
            # 生成告警
            start_time = time.time()
            alerts = self.generator.generate_alerts(test_data)
            processing_time = time.time() - start_time
            
            print(f"  处理数据: {len(test_data)}条")
            print(f"  生成告警: {len(alerts)}个")
            print(f"  处理时间: {processing_time:.3f}s")
            
            # 显示告警详情
            if alerts:
                print(f"  告警详情:")
                for alert in alerts:
                    print(f"    - {alert.physical_sign}: {alert.current_value} ({alert.threshold_violated}) - {alert.severity_level}")
            
            success = processing_time < 0.5  # 处理时间应该小于0.5秒
            self.test_results.append(('告警生成测试', success))
            return success
            
        except Exception as e:
            print(f"  ❌ 告警生成测试失败: {e}")
            self.test_results.append(('告警生成测试', False))
            return False
            
    def test_performance_batch(self) -> bool:
        """测试批量处理性能"""
        print("\n🚀 测试批量处理性能")
        try:
            # 生成大量测试数据
            batch_size = 100
            test_data = []
            
            for i in range(batch_size):
                data = {
                    'device_sn': f'TEST{i:03d}',
                    'user_id': i + 1,
                    'customer_id': 1,  # 使用同一个客户ID以测试缓存效果
                    'heart_rate': 70 + (i % 50),  # 70-120之间变化
                    'blood_oxygen': 95 + (i % 5),  # 95-100之间变化
                    'temperature': 36.0 + (i % 3) * 0.5  # 36.0-37.0之间变化
                }
                test_data.append(data)
                
            # 批量处理
            start_time = time.time()
            alerts = self.generator.generate_alerts(test_data)
            processing_time = time.time() - start_time
            
            # 计算性能指标
            qps = batch_size / processing_time if processing_time > 0 else 0
            avg_time_per_record = processing_time / batch_size if batch_size > 0 else 0
            
            print(f"  批量大小: {batch_size}条")
            print(f"  生成告警: {len(alerts)}个")
            print(f"  总耗时: {processing_time:.3f}s")
            print(f"  QPS: {qps:.1f} records/sec")
            print(f"  平均处理时间: {avg_time_per_record*1000:.2f}ms/record")
            
            # 性能要求：QPS > 200, 平均处理时间 < 5ms
            success = qps > 200 and avg_time_per_record < 0.005
            
            self.test_results.append(('批量处理性能测试', success))
            return success
            
        except Exception as e:
            print(f"  ❌ 批量处理性能测试失败: {e}")
            self.test_results.append(('批量处理性能测试', False))
            return False
            
    def test_cache_statistics(self) -> bool:
        """测试缓存统计"""
        print("\n📊 测试缓存统计")
        try:
            stats = self.generator.get_stats()
            
            print(f"  统计信息:")
            for key, value in stats.items():
                if isinstance(value, dict):
                    print(f"    {key}:")
                    for sub_key, sub_value in value.items():
                        print(f"      {sub_key}: {sub_value}")
                else:
                    print(f"    {key}: {value}")
                    
            # 检查关键指标
            required_keys = ['total_processed', 'cache_hits', 'db_fallbacks', 'cache_hit_rate']
            success = all(key in stats for key in required_keys)
            
            self.test_results.append(('缓存统计测试', success))
            return success
            
        except Exception as e:
            print(f"  ❌ 缓存统计测试失败: {e}")
            self.test_results.append(('缓存统计测试', False))
            return False
            
    def test_edge_cases(self) -> bool:
        """测试边界情况"""
        print("\n🔍 测试边界情况")
        try:
            success_count = 0
            total_tests = 0
            
            # 测试1: 空数据
            total_tests += 1
            try:
                alerts = self.generator.generate_alerts([])
                if len(alerts) == 0:
                    success_count += 1
                    print(f"  ✅ 空数据测试通过")
                else:
                    print(f"  ❌ 空数据测试失败")
            except Exception as e:
                print(f"  ❌ 空数据测试异常: {e}")
                
            # 测试2: 缺少customer_id
            total_tests += 1
            try:
                test_data = [{'device_sn': 'TEST', 'heart_rate': 80}]  # 缺少customer_id
                alerts = self.generator.generate_alerts(test_data)
                success_count += 1
                print(f"  ✅ 缺少customer_id测试通过")
            except Exception as e:
                print(f"  ❌ 缺少customer_id测试异常: {e}")
                
            # 测试3: 无效customer_id
            total_tests += 1
            try:
                test_data = [{'device_sn': 'TEST', 'customer_id': 999999, 'heart_rate': 80}]
                alerts = self.generator.generate_alerts(test_data)
                success_count += 1
                print(f"  ✅ 无效customer_id测试通过")
            except Exception as e:
                print(f"  ❌ 无效customer_id测试异常: {e}")
                
            # 测试4: 清理缓存
            total_tests += 1
            try:
                self.generator.clear_cache(1)
                success_count += 1
                print(f"  ✅ 缓存清理测试通过")
            except Exception as e:
                print(f"  ❌ 缓存清理测试异常: {e}")
                
            success = success_count == total_tests
            print(f"  边界测试: {success_count}/{total_tests} 通过")
            
            self.test_results.append(('边界情况测试', success))
            return success
            
        except Exception as e:
            print(f"  ❌ 边界情况测试失败: {e}")
            self.test_results.append(('边界情况测试', False))
            return False
            
    def run_all_tests(self):
        """运行所有测试"""
        print("🧪 启动Redis缓存告警系统完整测试")
        print("=" * 60)
        
        if not self.setup():
            print("❌ 测试环境初始化失败，退出测试")
            return
            
        try:
            # 运行测试
            tests = [
                self.test_redis_connection,
                self.test_alert_rules_retrieval,
                self.test_alert_generation,
                self.test_performance_batch,
                self.test_cache_statistics,
                self.test_edge_cases
            ]
            
            for test_func in tests:
                try:
                    test_func()
                except Exception as e:
                    print(f"❌ 测试{test_func.__name__}出现异常: {e}")
                    self.test_results.append((test_func.__name__, False))
                    
            # 显示测试结果
            self.show_test_results()
            
        finally:
            self.teardown()
            
    def show_test_results(self):
        """显示测试结果汇总"""
        print("\n" + "=" * 60)
        print("📋 测试结果汇总")
        print("=" * 60)
        
        passed = 0
        failed = 0
        
        for test_name, success in self.test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} - {test_name}")
            if success:
                passed += 1
            else:
                failed += 1
                
        total = passed + failed
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        print("-" * 60)
        print(f"总计: {total} | 通过: {passed} | 失败: {failed} | 通过率: {pass_rate:.1f}%")
        
        if pass_rate >= 80:
            print("🎉 测试通过！Redis缓存告警系统运行正常")
        elif pass_rate >= 60:
            print("⚠️ 测试部分通过，建议检查失败项目")
        else:
            print("❌ 测试失败，系统存在严重问题")
            
        print("=" * 60)

def main():
    """主函数"""
    test_suite = AlertCacheTestSuite()
    test_suite.run_all_tests()

if __name__ == "__main__":
    main()
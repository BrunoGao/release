# -*- coding: utf-8 -*-
# 健康数据修复验证脚本
import sys,os
sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__),'.')))

def test_health_fixes():
    """测试健康数据修复是否成功"""
    try:
        from user_health_data import get_all_health_data_optimized,fetch_health_data_by_orgIdAndUserId
        
        # 测试参数(请根据实际情况修改)
        TEST_ORG_ID = 1
        TEST_USER_ID = None  # None表示测试整个组织
        
        print("🔧 开始验证健康数据修复...")
        
        # 测试1: get_all_health_data_optimized pressure字段
        print("\n📊 测试1: get_all_health_data_optimized")
        result1 = get_all_health_data_optimized(orgId=TEST_ORG_ID, userId=TEST_USER_ID, latest_only=True)
        
        if result1.get('success'):
            health_data = result1.get('data', {}).get('healthData', [])
            if health_data:
                sample = health_data[0]
                print(f"  ✅ 查询成功，样本数据字段: {list(sample.keys())}")
                print(f"  🩺 heart_rate: {sample.get('heart_rate', '未找到')}")
                print(f"  🩸 pressure_high: {sample.get('pressure_high', '未找到')}")
                print(f"  🩸 pressure_low: {sample.get('pressure_low', '未找到')}")
                
                # 检查heart_rate启用时是否自动包含压力数据
                enabled_metrics = result1.get('data', {}).get('enabledMetrics', [])
                if 'heart_rate' in enabled_metrics:
                    if 'pressure_high' in sample and 'pressure_low' in sample:
                        print("  ✅ heart_rate启用时自动包含压力数据修复成功!")
                    else:
                        print("  ❌ heart_rate启用时压力数据仍然缺失")
                else:
                    print("  ⚠️ heart_rate未启用，无法测试自动压力数据功能")
            else:
                print("  ⚠️ 无健康数据返回")
        else:
            print(f"  ❌ 查询失败: {result1.get('error', '未知错误')}")
        
        # 测试2: fetch_health_data_by_orgIdAndUserId字段格式
        print("\n📋 测试2: fetch_health_data_by_orgIdAndUserId")
        result2 = fetch_health_data_by_orgIdAndUserId(orgId=TEST_ORG_ID, userId=TEST_USER_ID)
        
        if result2.get('success'):
            health_data = result2.get('data', {}).get('healthData', [])
            if health_data:
                sample = health_data[0]
                print(f"  ✅ 查询成功，样本数据字段: {list(sample.keys())}")
                
                # 检查字段格式是否统一
                has_new_format = 'heart_rate' in sample
                has_old_format = 'heartRate' in sample
                
                if has_new_format:
                    print("  ✅ 使用新格式字段(下划线)")
                elif has_old_format:
                    print("  ⚠️ 使用旧格式字段(驼峰)")
                else:
                    print("  ❌ 字段格式异常")
                    
                # 检查统计数据
                stats = result2.get('data', {}).get('statistics', {})
                if stats:
                    print(f"  📊 统计数据: {stats.get('averageStats', {})}")
                    print("  ✅ 统计计算修复成功!")
            else:
                print("  ⚠️ 无健康数据返回")
        else:
            print(f"  ❌ 查询失败: {result2.get('error', '未知错误')}")
        
        print("\n🎯 修复验证完成!")
        return True
        
    except Exception as e:
        print(f"❌ 验证过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_health_fixes() 
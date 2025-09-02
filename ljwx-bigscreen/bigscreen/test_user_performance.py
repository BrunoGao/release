#!/usr/bin/env python3
"""用户查询性能测试脚本"""

import time
import requests
import json

def test_user_performance():
    """测试用户查询性能优化效果"""
    print("🔧 测试用户查询性能优化效果...")
    
    # 测试优化前后的性能差异
    test_cases = [
        {
            'name': '单用户查询',
            'url': 'http://127.0.0.1:5001/get_user_info_by_orgIdAndUserId',
            'params': {'userId': 1}
        },
        {
            'name': '组织用户查询（2000用户）',
            'url': 'http://127.0.0.1:5001/get_user_info_by_orgIdAndUserId',
            'params': {'orgId': 1}
        },
        {
            'name': '总体信息查询（包含用户查询）',
            'url': 'http://127.0.0.1:5001/get_total_info',
            'params': {'customer_id': 1}
        }
    ]
    
    results = {}
    
    for test_case in test_cases:
        print(f"\n📋 测试: {test_case['name']}")
        
        # 清除缓存 - 测试冷启动性能
        try:
            requests.get('http://127.0.0.1:5001/api/cache/clear', timeout=5)
        except:
            pass
        
        # 执行测试
        start_time = time.time()
        try:
            response = requests.get(test_case['url'], params=test_case['params'], timeout=30)
            end_time = time.time()
            
            response_time = round(end_time - start_time, 3)
            
            if response.status_code == 200:
                data = response.json()
                
                # 提取关键指标
                if 'data' in data and 'user_info' in data['data']:
                    # get_total_info 响应格式
                    user_data = data['data']['user_info']
                    if isinstance(user_data, dict) and 'data' in user_data:
                        user_count = user_data['data'].get('totalUsers', 0)
                    else:
                        user_count = 0
                elif 'data' in data and 'totalUsers' in data['data']:
                    # 直接用户查询响应格式
                    user_count = data['data']['totalUsers']
                else:
                    user_count = 0
                
                print(f"✅ 响应时间: {response_time}s")
                print(f"📊 用户数量: {user_count}")
                print(f"🎯 状态: 成功")
                
                results[test_case['name']] = {
                    'response_time': response_time,
                    'user_count': user_count,
                    'status': 'success',
                    'is_cached': data.get('performance', {}).get('cached', False)
                }
                
                # 性能评估
                if response_time < 1.0:
                    performance = "优秀"
                elif response_time < 3.0:
                    performance = "良好"
                elif response_time < 5.0:
                    performance = "一般"
                else:
                    performance = "需要优化"
                
                print(f"⭐ 性能评级: {performance}")
                
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                results[test_case['name']] = {
                    'response_time': response_time,
                    'status': 'http_error',
                    'error_code': response.status_code
                }
                
        except requests.exceptions.Timeout:
            print(f"⏰ 请求超时 (>30秒)")
            results[test_case['name']] = {
                'response_time': '>30',
                'status': 'timeout'
            }
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            results[test_case['name']] = {
                'status': 'error',
                'error': str(e)
            }
    
    # 性能总结
    print(f"\n📈 性能测试总结:")
    print("=" * 60)
    
    for name, result in results.items():
        print(f"{name:25} | 响应时间: {str(result.get('response_time', 'N/A')):>8}s | 状态: {result.get('status', 'unknown')}")
    
    # 判断优化效果
    org_query_time = results.get('组织用户查询（2000用户）', {}).get('response_time', float('inf'))
    if isinstance(org_query_time, (int, float)) and org_query_time < 2.0:
        print(f"\n🎉 优化成功！2000用户查询在{org_query_time}秒内完成")
    elif isinstance(org_query_time, (int, float)) and org_query_time < 5.0:
        print(f"\n✅ 优化有效！2000用户查询时间为{org_query_time}秒，已显著改善")
    else:
        print(f"\n⚠️ 仍需优化！2000用户查询时间: {org_query_time}")
    
    return results

if __name__ == "__main__":
    test_user_performance() 
#!/usr/bin/env python3
"""最终测试 - 强制跳过缓存"""

import requests
import time
import json

def final_test():
    """最终测试API，强制跳过所有缓存"""
    print("🔧 最终测试 - 强制跳过缓存...")
    
    try:
        # 使用多种方式强制跳过缓存
        timestamp = int(time.time())
        params = {
            'orgId': 1,
            'pageSize': 1,
            'v': timestamp,
            'nocache': 'true',
            'force_refresh': 'true',
            '_t': timestamp,
            'cache_bust': timestamp
        }
        
        print(f"📋 请求参数: {params}")
        
        response = requests.get('http://127.0.0.1:5001/health_data/page', 
                              params=params, 
                              timeout=60,
                              headers={
                                  'Cache-Control': 'no-cache, no-store, must-revalidate',
                                  'Pragma': 'no-cache',
                                  'Expires': '0'
                              })
        
        print(f"HTTP状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API请求成功")
            
            # 详细检查响应数据
            enabled_metrics = data.get('data', {}).get('enabledMetrics', [])
            print(f"📊 API返回的启用指标: {enabled_metrics}")
            
            # 逐一检查pressure相关指标
            pressure_indicators = ['pressure', 'pressure_high', 'pressure_low']
            print(f"\n🩺 Pressure指标检查:")
            for indicator in pressure_indicators:
                is_present = indicator in enabled_metrics
                status = "✅" if is_present else "❌"
                print(f"   {status} {indicator}: {is_present}")
            
            # 检查实际健康数据
            health_data = data.get('data', {}).get('healthData', [])
            print(f"\n📝 健康数据检查 (共{len(health_data)}条):")
            
            if health_data:
                first_item = health_data[0]
                print(f"   第一条数据字段:")
                
                # 检查pressure相关字段
                pressure_fields = ['pressureHigh', 'pressureLow']
                for field in pressure_fields:
                    value = first_item.get(field)
                    status = "✅" if value is not None and str(value) != '0' and str(value) != 'None' else "❌"
                    print(f"      {status} {field}: {value}")
                
                # 检查其他字段作为对比
                other_fields = ['heartRate', 'bloodOxygen', 'temperature', 'userName', 'deptName']
                for field in other_fields:
                    value = first_item.get(field)
                    print(f"      ✓ {field}: {value}")
            
            # 检查查询策略和性能信息
            performance = data.get('performance', {})
            query_strategy = data.get('data', {}).get('queryStrategy', 'unknown')
            print(f"\n🔧 查询信息:")
            print(f"   查询策略: {query_strategy}")
            print(f"   响应时间: {performance.get('response_time', 'unknown')}s")
            print(f"   是否使用缓存: {performance.get('cached', False)}")
            
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except requests.RequestException as e:
        print(f"❌ 请求异常: {e}")
    except Exception as e:
        print(f"❌ 其他错误: {e}")

if __name__ == "__main__":
    final_test() 
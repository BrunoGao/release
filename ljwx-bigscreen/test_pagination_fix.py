#!/usr/bin/env python3
"""
测试分页修复是否生效
"""

import requests
import json
from datetime import datetime

def test_health_data_no_pagination():
    """测试健康数据查询是否已移除硬编码分页限制"""
    
    base_url = "http://localhost:5001"
    
    # 测试7天时间范围查询
    params = {
        'orgId': '1',
        'startDate': '2025-08-01',
        'endDate': '2025-08-07'
    }
    
    print(f"🔍 测试参数: {params}")
    print(f"📅 时间范围: {params['startDate']} 到 {params['endDate']} (7天)")
    print("🎯 期望结果: 获取完整7天范围内的所有数据，不应只限制在单日100条")
    
    try:
        response = requests.get(f"{base_url}/get_all_health_data_by_orgIdAndUserId", params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                # 检查数据结构
                if 'data' in data:
                    analysis_data = data['data']
                    
                    # 检查summary信息
                    if 'summary' in analysis_data:
                        summary = analysis_data['summary']
                        total_records = summary.get('totalRecords', 0)
                        time_range = summary.get('timeRange', {})
                        start_time = time_range.get('start', '')
                        end_time = time_range.get('end', '')
                        
                        print(f"\n📊 结果分析:")
                        print(f"   总记录数: {total_records}")
                        print(f"   数据时间范围: {start_time} 到 {end_time}")
                        
                        # 检查是否还是硬编码的100条限制
                        if total_records == 100:
                            print(f"❌ 仍然存在100条记录限制")
                        else:
                            print(f"✅ 已移除硬编码限制，获取到 {total_records} 条记录")
                        
                        # 检查时间范围是否覆盖7天
                        if start_time and end_time:
                            start_date = start_time[:10]  # 取日期部分
                            end_date = end_time[:10]
                            
                            if start_date == end_date:
                                print(f"❌ 数据仍然只覆盖单日: {start_date}")
                            else:
                                print(f"✅ 数据覆盖多日: {start_date} 到 {end_date}")
                        
                        # 检查健康分数
                        if 'healthScores' in analysis_data:
                            health_scores = analysis_data['healthScores']
                            overall_score = health_scores.get('overall', 0)
                            print(f"   健康总分: {overall_score}")
                    
                    print(f"\n📋 API响应结构:")
                    print(f"   - success: {data.get('success')}")
                    print(f"   - data keys: {list(analysis_data.keys()) if 'data' in data else 'None'}")
                    
                else:
                    print("❌ API响应缺少data字段")
            else:
                print(f"❌ API调用失败: {data.get('error', '未知错误')}")
        else:
            print(f"❌ HTTP请求失败: {response.status_code}")
            print(f"   响应内容: {response.text[:500]}...")
            
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")

if __name__ == "__main__":
    test_health_data_no_pagination()
#!/usr/bin/env python3
"""测试分区表查询的详细调试脚本"""

import requests
import json

def test_partition_query():
    url = "http://127.0.0.1:5001/health_data/page"
    
    params = {
        'orgId': 1,
        'userId': '',
        'startDate': '2025-05-01',
        'endDate': '2025-06-01',
        'page': 1,
        'pageSize': 100
    }
    
    print("🚀 开始测试分区表查询...")
    print(f"📋 请求参数: {params}")
    
    try:
        response = requests.get(url, params=params, timeout=30)
        
        print(f"📊 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 查询成功")
            print(f"📈 总记录数: {data.get('data', {}).get('totalRecords', 0)}")
            print(f"📄 返回数据条数: {len(data.get('data', {}).get('healthData', []))}")
            print(f"🔧 查询策略: {data.get('data', {}).get('queryStrategy', 'N/A')}")
            print(f"⏱️ 响应时间: {data.get('performance', {}).get('response_time', 'N/A')}s")
            print(f"💾 是否缓存: {data.get('performance', {}).get('cached', False)}")
            
            if len(data.get('data', {}).get('healthData', [])) == 0:
                print("❌ 数据为空！检查分区表查询逻辑")
            else:
                print("✅ 成功返回数据")
                # 显示第一条数据
                first_data = data['data']['healthData'][0]
                print(f"📝 第一条数据示例: {json.dumps(first_data, ensure_ascii=False, indent=2)}")
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"错误内容: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_partition_query() 
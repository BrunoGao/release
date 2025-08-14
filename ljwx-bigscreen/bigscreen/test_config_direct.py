#!/usr/bin/env python3
"""直接测试配置读取"""

import requests
import json

def test_config_direct():
    print("🔧 直接测试配置读取...")
    
    # 测试通过特定参数强制重新加载配置
    response = requests.get('http://127.0.0.1:5001/health_data/page', params={
        'orgId': 1, 
        'startDate': '2025-05-01', 
        'endDate': '2025-06-01', 
        'page': 1, 
        'pageSize': 1,
        'reload_config': 'true',  # 添加重新加载配置标志
        'v': '1733132000'  # 强制跳过缓存
    }, timeout=30)
    
    if response.status_code != 200:
        print(f"❌ API请求失败: {response.status_code}")
        return
    
    data = response.json()
    
    print("📊 配置加载测试:")
    print(f"启用指标: {data.get('data', {}).get('enabledMetrics', [])}")
    print(f"查询字段: {data.get('data', {}).get('queryFields', [])}")
    
    # 检查是否包含pressure相关配置
    enabled_metrics = data.get('data', {}).get('enabledMetrics', [])
    
    print(f"\n🩺 血压配置状态:")
    pressure_related = [m for m in enabled_metrics if 'pressure' in m]
    if pressure_related:
        print(f"✅ 找到血压相关配置: {pressure_related}")
    else:
        print("❌ 未找到血压相关配置")
        
        # 显示所有配置用于对比
        print(f"所有启用指标: {enabled_metrics}")
    
    # 直接查询数据库检查配置
    print(f"\n📋 数据库配置验证:")
    try:
        import mysql.connector
        connection = mysql.connector.connect(
            host='localhost',
            port=3306,
            database='lj-06',
            user='root',
            password='123456'
        )
        cursor = connection.cursor()
        cursor.execute("SELECT data_type, is_enabled FROM t_health_data_config WHERE customer_id = 1 AND data_type LIKE '%pressure%'")
        pressure_configs = cursor.fetchall()
        
        print("数据库中的血压配置:")
        for data_type, is_enabled in pressure_configs:
            status = "✅" if is_enabled else "❌"
            print(f"   {status} {data_type}: {is_enabled}")
            
        connection.close()
    except Exception as e:
        print(f"❌ 数据库查询失败: {e}")

if __name__ == "__main__":
    test_config_direct() 
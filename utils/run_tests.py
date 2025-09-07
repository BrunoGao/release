#!/usr/bin/env python3
from api_tester import APITester
from datetime import datetime

def main():
    print("API 接口自动化测试工具")
    print("=" * 50)
    
    tester = APITester("http://192.168.1.83:5001")
    
    print("连接数据库...")
    if not tester.db_config.connect():
        print("❌ 数据库连接失败，请检查 db_config.json 配置")
        return
    
    print("✅ 数据库连接成功")
    
    devices = tester.db_config.get_devices(20)
    users = tester.db_config.get_users(10)
    user_devices = tester.db_config.get_user_devices(15)
    
    print(f"📊 数据统计:")
    print(f"   - 设备数量: {len(devices)}")
    print(f"   - 用户数量: {len(users)}")
    print(f"   - 用户设备关联: {len(user_devices)}")
    
    if not devices:
        print("❌ 未找到设备数据，请检查数据库表 t_device_info")
        return
    
    # 优先使用有用户关联的设备
    if user_devices:
        device_sns = [ud['device_sn'] for ud in user_devices]
        print(f"✅ 获取有用户关联的设备序列号: {device_sns[:3]}...")
    else:
        device_sns = [device['device_sn'] for device in devices if device['device_sn']]
        print(f"✅ 获取设备序列号: {device_sns[:3]}...")
    
    print("\n🧪 开始功能测试...")
    functional_results = tester.functional_test(device_sns)
    
    print("\n⚡ 开始性能测试...")
    endpoints = ['upload_health_data', 'upload_device_info', 'upload_common_event']
    performance_results = {}
    
    for endpoint in endpoints:
        print(f"   测试 {endpoint}...")
        perf_results = tester.performance_test(endpoint, device_sns, 
                                             concurrent_users=3, 
                                             requests_per_user=5)
        performance_results[f"{endpoint}_performance"] = perf_results
    
    all_results = {**functional_results, **performance_results}
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"api_test_report_{timestamp}.txt"
    
    print(f"\n📋 生成测试报告: {output_file}")
    tester.generate_report(all_results, output_file)
    
    tester.db_config.disconnect()
    print("✅ 测试完成")

if __name__ == "__main__":
    main()
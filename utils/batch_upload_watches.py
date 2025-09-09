#!/usr/bin/env python3
"""
批量上传1000台手表设备信息脚本
SerialNumber 从 CRFTQ23409000000 到 CRFTQ23409001000
"""

import requests
import json
import time
import random
from datetime import datetime
import sys

def generate_device_data(serial_number):
    """生成单台设备的数据"""
    # 生成随机MAC地址
    def random_mac():
        return ':'.join(['%02x' % random.randint(0, 255) for _ in range(6)])
    
    # 生成随机IP地址 (192.168.1.x)
    def random_ip():
        return f"192.168.1.{random.randint(100, 254)}"
    
    # 生成随机IMEI (15位数字)
    def random_imei():
        return ''.join([str(random.randint(0, 9)) for _ in range(15)])
    
    return {
        "System Software Version": "GLL-AL30BCN 3.0.0.900(SP51C700E106R370P324)",
        "Wifi Address": random_mac(),
        "Bluetooth Address": random_mac().upper(),
        "IP Address": random_ip(),
        "Network Access Mode": 2,
        "SerialNumber": serial_number,
        "Device Name": "HUAWEI WATCH B7-536-BF0",
        "IMEI": random_imei(),
        "batteryLevel": random.randint(85, 100),
        "voltage": random.randint(4200, 4400),
        "chargingStatus": random.choice(["NONE", "CHARGING", "FULL"]),
        "status": "ACTIVE",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "wearState": random.randint(0, 1)
    }

def upload_device(device_data, base_url="http://localhost:5225"):
    """上传单台设备信息到 upload_device_info 接口"""
    url = f"{base_url}/upload_device_info"
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    try:
        response = requests.post(url, 
                               data=json.dumps(device_data), 
                               headers=headers, 
                               timeout=10)
        
        if response.status_code == 200:
            return True, "Success"
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
    
    except requests.exceptions.RequestException as e:
        return False, str(e)

def main():
    """主函数：批量上传1000台设备"""
    print("开始批量上传1000台手表设备信息...")
    print(f"SerialNumber 范围: CRFTQ23409000000 到 CRFTQ23409001000")
    print("-" * 50)
    
    success_count = 0
    failed_count = 0
    failed_devices = []
    
    # 生成1000台设备的序列号
    for i in range(1000):
        serial_number = f"CRFTQ23409{i:06d}"
        
        # 生成设备数据
        device_data = generate_device_data(serial_number)
        
        # 上传设备信息
        success, message = upload_device(device_data)
        
        if success:
            success_count += 1
            print(f"✓ [{i+1:4d}/1000] {serial_number} - 成功")
        else:
            failed_count += 1
            failed_devices.append((serial_number, message))
            print(f"✗ [{i+1:4d}/1000] {serial_number} - 失败: {message}")
        
        # 每10台设备暂停一下，避免服务器压力过大
        if (i + 1) % 10 == 0:
            time.sleep(0.5)
        
        # 每100台设备显示进度
        if (i + 1) % 100 == 0:
            print(f"进度: {i+1}/1000 设备已处理 (成功: {success_count}, 失败: {failed_count})")
    
    # 输出最终统计
    print("\n" + "=" * 50)
    print("批量上传完成!")
    print(f"总计: 1000 台设备")
    print(f"成功: {success_count} 台")
    print(f"失败: {failed_count} 台")
    
    # 输出失败的设备详情
    if failed_devices:
        print("\n失败的设备:")
        for serial, error in failed_devices:
            print(f"  {serial}: {error}")
    
    return success_count, failed_count

if __name__ == "__main__":
    try:
        success, failed = main()
        sys.exit(0 if failed == 0 else 1)
    except KeyboardInterrupt:
        print("\n\n用户中断上传...")
        sys.exit(1)
    except Exception as e:
        print(f"\n脚本执行出错: {e}")
        sys.exit(1)
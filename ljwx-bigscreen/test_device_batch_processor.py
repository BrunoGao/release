#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""设备信息批量处理器测试脚本"""
import requests
import json
import time
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import mysql.connector
import threading

class DeviceBatchTester:
    def __init__(self):
        self.base_url = 'http://localhost:5001'
        self.db_config = {
            'host': '127.0.0.1',
            'port': 3306,
            'user': 'root',
            'password': '123456',
            'database': 'lj-06',
            'charset': 'utf8mb4'
        }
        self.test_devices = []
        
    def generate_test_device_data(self, device_id):
        """生成测试设备数据"""
        return {
            "System Software Version": f"TEST-{device_id}CN_4.0.0.900",
            "Wifi Address": f"a8:37:59:98:4a:{device_id:02x}",
            "Bluetooth Address": f"A8:37:59:9C:A7:{device_id:02x}",
            "IP Address": f"192.168.1.{100 + (device_id % 155)}",
            "Network Access Mode": 2,
            "SerialNumber": f"TEST{device_id:06d}",
            "Device Name": f"TEST DEVICE {device_id}",
            "IMEI": f"86160007654{device_id:04d}",
            "batteryLevel": random.randint(20, 100),
            "voltage": random.randint(3500, 4200),
            "chargingStatus": random.choice(["CHARGING", "NOT_CHARGING"]),
            "status": "ACTIVE",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "wearState": random.choice([0, 1]),
            "customerId": 1
        }
    
    def upload_device_info(self, device_data):
        """上传单个设备信息"""
        try:
            response = requests.post(
                f"{self.base_url}/upload_device_info",
                json=device_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'device_sn': device_data['SerialNumber'],
                    'response': result
                }
            else:
                return {
                    'success': False,
                    'device_sn': device_data['SerialNumber'],
                    'error': f"HTTP {response.status_code}",
                    'response': response.text
                }
                
        except Exception as e:
            return {
                'success': False,
                'device_sn': device_data['SerialNumber'],
                'error': str(e)
            }
    
    def check_database_records(self, device_sns):
        """检查数据库中的记录"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor(dictionary=True)
            
            # 检查设备信息表
            device_placeholders = ','.join(['%s'] * len(device_sns))
            device_sql = f"SELECT serial_number, battery_level, charging_status, update_time FROM t_device_info WHERE serial_number IN ({device_placeholders})"
            cursor.execute(device_sql, device_sns)
            device_records = cursor.fetchall()
            
            # 检查历史表
            history_sql = f"SELECT serial_number, battery_level, charging_status, update_time FROM t_device_info_history WHERE serial_number IN ({device_placeholders}) ORDER BY update_time DESC"
            cursor.execute(history_sql, device_sns)
            history_records = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return {
                'device_records': device_records,
                'history_records': history_records
            }
            
        except Exception as e:
            print(f"❌ 数据库检查失败: {e}")
            return None
    
    def check_batch_processor_status(self):
        """检查批量处理器状态"""
        try:
            response = requests.get(f"{self.base_url}/api/batch/stats")
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            print(f"❌ 获取批量处理器状态失败: {e}")
            return None
    
    def test_single_device(self):
        """测试单个设备上传"""
        print("\n🔍 测试单个设备上传...")
        
        device_data = self.generate_test_device_data(1)
        print(f"设备数据: {device_data['SerialNumber']}")
        
        result = self.upload_device_info(device_data)
        if result['success']:
            print(f"✅ 上传成功: {result['response']}")
            
            # 等待处理
            time.sleep(3)
            
            # 检查数据库
            db_result = self.check_database_records([device_data['SerialNumber']])
            if db_result:
                print(f"📊 数据库记录:")
                print(f"  设备信息表: {len(db_result['device_records'])}条")
                print(f"  历史记录表: {len(db_result['history_records'])}条")
                
                if db_result['device_records']:
                    record = db_result['device_records'][0]
                    print(f"  最新记录: {record['serial_number']} - 电量{record['battery_level']}% - {record['update_time']}")
            
            return True
        else:
            print(f"❌ 上传失败: {result['error']}")
            return False
    
    def test_batch_upload(self, device_count=10):
        """测试批量上传"""
        print(f"\n🚀 测试批量上传 ({device_count}台设备)...")
        
        # 生成测试数据
        test_data = []
        for i in range(1, device_count + 1):
            test_data.append(self.generate_test_device_data(i))
        
        # 记录开始时间
        start_time = time.time()
        
        # 并发上传
        results = []
        with ThreadPoolExecutor(max_workers=20) as executor:
            future_to_device = {
                executor.submit(self.upload_device_info, device_data): device_data['SerialNumber']
                for device_data in test_data
            }
            
            for future in as_completed(future_to_device):
                result = future.result()
                results.append(result)
        
        # 统计结果
        success_count = sum(1 for r in results if r['success'])
        failed_count = device_count - success_count
        elapsed_time = time.time() - start_time
        
        print(f"📈 批量上传结果:")
        print(f"  成功: {success_count}/{device_count}")
        print(f"  失败: {failed_count}")
        print(f"  耗时: {elapsed_time:.2f}秒")
        print(f"  吞吐量: {success_count/elapsed_time:.1f}设备/秒")
        
        # 等待批量处理完成
        print("\n⏳ 等待批量处理完成...")
        time.sleep(5)
        
        # 检查批量处理器状态
        status = self.check_batch_processor_status()
        if status:
            print(f"📊 批量处理器状态:")
            print(f"  已处理: {status['data']['processed_total']}")
            print(f"  队列中: {status['data']['queued_current']}")
            print(f"  失败: {status['data']['failed_total']}")
        
        # 检查数据库记录
        device_sns = [data['SerialNumber'] for data in test_data]
        db_result = self.check_database_records(device_sns)
        if db_result:
            print(f"📊 数据库验证:")
            print(f"  设备信息表: {len(db_result['device_records'])}/{device_count}条")
            print(f"  历史记录表: {len(db_result['history_records'])}条")
        
        return success_count == device_count
    
    def test_concurrent_upload(self, device_count=50, concurrent_threads=10):
        """测试高并发上传"""
        print(f"\n⚡ 测试高并发上传 ({device_count}台设备, {concurrent_threads}并发)...")
        
        success_count = 0
        error_count = 0
        start_time = time.time()
        
        def upload_worker():
            nonlocal success_count, error_count
            device_data = self.generate_test_device_data(random.randint(1000, 9999))
            result = self.upload_device_info(device_data)
            
            if result['success']:
                success_count += 1
            else:
                error_count += 1
                print(f"❌ 上传失败: {result['device_sn']} - {result['error']}")
        
        # 启动并发线程
        threads = []
        for i in range(device_count):
            thread = threading.Thread(target=upload_worker)
            threads.append(thread)
            thread.start()
            
            # 控制并发数
            if len(threads) >= concurrent_threads:
                for t in threads:
                    t.join()
                threads = []
        
        # 等待剩余线程完成
        for thread in threads:
            thread.join()
        
        elapsed_time = time.time() - start_time
        
        print(f"📈 高并发测试结果:")
        print(f"  成功: {success_count}/{device_count}")
        print(f"  失败: {error_count}")
        print(f"  耗时: {elapsed_time:.2f}秒")
        print(f"  吞吐量: {success_count/elapsed_time:.1f}设备/秒")
        
        return success_count > device_count * 0.8  # 80%成功率算通过
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🧪 开始设备信息批量处理器测试")
        print("=" * 50)
        
        # 检查服务状态
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            print(f"✅ 服务状态: {response.status_code}")
        except Exception as e:
            print(f"❌ 服务连接失败: {e}")
            return False
        
        # 测试单个设备
        if not self.test_single_device():
            print("❌ 单设备测试失败")
            return False
        
        # 测试批量上传
        if not self.test_batch_upload(10):
            print("❌ 批量上传测试失败")
            return False
        
        # 测试高并发
        if not self.test_concurrent_upload(50, 10):
            print("❌ 高并发测试失败") 
            return False
        
        print("\n🎉 所有测试通过!")
        return True

if __name__ == "__main__":
    tester = DeviceBatchTester()
    tester.run_all_tests() 
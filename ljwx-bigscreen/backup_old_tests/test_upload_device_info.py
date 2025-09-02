#!/usr/bin/env python3
"""upload_device_info接口自动化测试"""
import json,time,requests,mysql.connector
from datetime import datetime,timedelta
import sys,os
sys.path.append('.')

class UploadDeviceInfoTest:
    """设备信息上传接口测试"""
    
    def __init__(self):
        self.api_url = 'http://localhost:5001/upload_device_info'
        self.db_config = {
            'host': '127.0.0.1', 'port': 3306, 'user': 'root',
            'password': '123456', 'database': 'lj-06'
        }
        self.test_device_sn = 'A5GTQ24B26000732'
        
    def get_db_connection(self):
        """获取数据库连接"""
        return mysql.connector.connect(**self.db_config)
    
    def generate_test_data(self):
        """生成测试数据"""
        return {
            'System Software Version': 'ARC-AL00CN 4.0.0.900(SP41C700E104R412P100)',
            'Wifi Address': 'f0:fa:c7:ed:6c:17',
            'Bluetooth Address': 'B0:FE:E5:8F:FD:D6',
            'IP Address': '192.168.31.192\nfe80::7d:70ff:fef5:a220',
            'Network Access Mode': 2,
            'SerialNumber': self.test_device_sn,
            'Device Name': 'HUAWEI WATCH 4-DD6',
            'IMEI': '861600078012130',
            'batteryLevel': 63,
            'voltage': 3995,
            'chargingStatus': 'NONE',
            'status': 'ACTIVE',
            'wearState': 0
        }
    
    def test_api_call(self):
        """测试API调用"""
        try:
            test_data = self.generate_test_data()
            response = requests.post(self.api_url, json=test_data, timeout=30)
            
            if response.status_code == 200:
                print("✅ API调用成功")
                return True
            else:
                print(f"❌ API调用失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ API调用异常: {e}")
            return False
    
    def test_device_registration(self):
        """测试设备注册"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # 检查设备是否注册/更新
            query = """
                SELECT COUNT(*) FROM t_device_info 
                WHERE serial_number = %s AND update_time >= %s
            """
            time_threshold = datetime.now() - timedelta(minutes=5)
            cursor.execute(query, (self.test_device_sn, time_threshold))
            count = cursor.fetchone()[0]
            
            if count > 0:
                print("✅ 设备注册/更新成功")
                return True
            else:
                print("❌ 设备注册/更新失败")
                return False
        except Exception as e:
            print(f"❌ 设备注册检查异常: {e}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()
    
    def test_device_status_update(self):
        """测试设备状态更新"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # 验证设备状态信息
            query = """
                SELECT battery_level, status, wearable_status 
                FROM t_device_info 
                WHERE serial_number = %s 
                ORDER BY update_time DESC LIMIT 1
            """
            cursor.execute(query, (self.test_device_sn,))
            result = cursor.fetchone()
            
            if result and result[0] == 63 and result[1] == 'ACTIVE':
                print("✅ 设备状态更新成功")
                return True
            else:
                print("❌ 设备状态更新失败")
                return False
        except Exception as e:
            print(f"❌ 设备状态检查异常: {e}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()
    
    def test_device_network_info(self):
        """测试设备网络信息"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # 验证网络信息
            query = """
                SELECT wifi_address, bluetooth_address, ip_address 
                FROM t_device_info 
                WHERE serial_number = %s 
                ORDER BY update_time DESC LIMIT 1
            """
            cursor.execute(query, (self.test_device_sn,))
            result = cursor.fetchone()
            
            if result and result[0] == 'f0:fa:c7:ed:6c:17':
                print("✅ 设备网络信息更新成功")
                return True
            else:
                print("❌ 设备网络信息更新失败")
                return False
        except Exception as e:
            print(f"❌ 网络信息检查异常: {e}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()
    
    def run_test(self):
        """运行完整测试"""
        print("🚀 开始upload_device_info接口测试")
        print("=" * 50)
        
        results = []
        
        # API调用测试
        api_success = self.test_api_call()
        results.append(api_success)
        
        # 等待数据处理
        time.sleep(3)
        
        # 设备注册测试
        registration_success = self.test_device_registration()
        results.append(registration_success)
        
        # 设备状态更新测试
        status_success = self.test_device_status_update()
        results.append(status_success)
        
        # 网络信息测试
        network_success = self.test_device_network_info()
        results.append(network_success)
        
        # 计算成功率
        success_rate = sum(results) / len(results) * 100
        
        print(f"\n📊 测试结果统计:")
        print(f"总测试项: {len(results)}")
        print(f"通过测试: {sum(results)}")
        print(f"成功率: {success_rate:.1f}%")
        
        if success_rate == 100:
            print("✅ upload_device_info 测试通过")
        else:
            print("❌ upload_device_info 测试失败")
        
        return success_rate == 100

if __name__ == "__main__":
    test = UploadDeviceInfoTest()
    test.run_test() 
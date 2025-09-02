#!/usr/bin/env python3
"""upload_health_data接口自动化测试"""
import json,time,requests,mysql.connector
from datetime import datetime,timedelta
import sys,os
sys.path.append('.')

class UploadHealthDataTest:
    """健康数据上传接口测试"""
    
    def __init__(self):
        self.api_url = 'http://localhost:5001/upload_health_data'
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
            'data': {
                'id': self.test_device_sn,
                'upload_method': 'wifi',
                'heart_rate': 94,
                'blood_oxygen': 98,
                'body_temperature': '37.1',
                'blood_pressure_systolic': 135,
                'blood_pressure_diastolic': 92,
                'step': 1107,
                'distance': '754.0',
                'calorie': '45615.0',
                'latitude': '34.14505564403376',
                'longitude': '117.14877354661755',
                'altitude': '0.0',
                'stress': 57,
                'sleepData': '{"code":0,"data":[{"endTimeStamp":1747440420000,"startTimeStamp":1747418280000,"type":2}],"name":"sleep","type":"history"}',
                'exerciseDailyData': '{"code":0,"data":[{"strengthTimes":2,"totalTime":5}],"name":"daily","type":"history"}',
                'exerciseWeekData': 'null',
                'scientificSleepData': 'null',
                'workoutData': '{"code":0,"data":[],"name":"workout","type":"history"}'
            }
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
    
    def test_data_storage(self):
        """测试数据存储"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # 检查健康数据是否插入
            query = """
                SELECT COUNT(*) FROM t_user_health_data 
                WHERE device_sn = %s AND timestamp >= %s
            """
            time_threshold = datetime.now() - timedelta(minutes=5)
            cursor.execute(query, (self.test_device_sn, time_threshold))
            count = cursor.fetchone()[0]
            
            if count > 0:
                print("✅ 健康数据存储成功")
                return True
            else:
                print("❌ 健康数据存储失败")
                return False
        except Exception as e:
            print(f"❌ 数据存储检查异常: {e}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()
    
    def test_data_validation(self):
        """测试数据验证"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # 验证数据完整性
            query = """
                SELECT heart_rate, blood_oxygen, temperature, step 
                FROM t_user_health_data 
                WHERE device_sn = %s 
                ORDER BY timestamp DESC LIMIT 1
            """
            cursor.execute(query, (self.test_device_sn,))
            result = cursor.fetchone()
            
            if result and result[0] == 94 and result[1] == 98:
                print("✅ 数据验证通过")
                return True
            else:
                print("❌ 数据验证失败")
                return False
        except Exception as e:
            print(f"❌ 数据验证异常: {e}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()
    
    def run_test(self):
        """运行完整测试"""
        print("🚀 开始upload_health_data接口测试")
        print("=" * 50)
        
        results = []
        
        # API调用测试
        api_success = self.test_api_call()
        results.append(api_success)
        
        # 等待数据处理
        time.sleep(3)
        
        # 数据存储测试
        storage_success = self.test_data_storage()
        results.append(storage_success)
        
        # 数据验证测试
        validation_success = self.test_data_validation()
        results.append(validation_success)
        
        # 计算成功率
        success_rate = sum(results) / len(results) * 100
        
        print(f"\n📊 测试结果统计:")
        print(f"总测试项: {len(results)}")
        print(f"通过测试: {sum(results)}")
        print(f"成功率: {success_rate:.1f}%")
        
        if success_rate == 100:
            print("✅ upload_health_data 测试通过")
        else:
            print("❌ upload_health_data 测试失败")
        
        return success_rate == 100

if __name__ == "__main__":
    test = UploadHealthDataTest()
    test.run_test() 
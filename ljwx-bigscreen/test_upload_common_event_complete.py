#!/usr/bin/env python3
"""upload_common_event接口完整自动化测试脚本"""
import requests
import json
import time
import random
from datetime import datetime, timedelta
import mysql.connector
from typing import Dict, List, Any

class CommonEventTester:
    """通用事件接口测试器"""
    
    def __init__(self, base_url="http://localhost:5001", db_config=None):
        self.base_url = base_url #API基础URL
        self.db_config = db_config or { #数据库配置
            'host': 'localhost',
            'port': 3308, 
            'user': 'ljwx',
            'password': 'ljwx123',
            'database': 'ljwx'
        }
        self.test_device_sn = f"TEST{int(time.time())}" #测试设备序列号
        self.test_results = [] #测试结果收集
        
    def get_db_connection(self):
        """获取数据库连接"""
        return mysql.connector.connect(**self.db_config)
    
    def generate_health_data(self, device_sn: str, timestamp: str = None) -> Dict:
        """生成模拟健康数据"""
        if not timestamp:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
        return {
            "deviceSn": device_sn,
            "heart_rate": random.randint(60, 120),
            "blood_oxygen": random.randint(95, 100),
            "body_temperature": f"{random.uniform(36.0, 37.5):.1f}",
            "step": random.randint(0, 10000),
            "distance": f"{random.uniform(0, 10):.1f}",
            "calorie": f"{random.uniform(0, 500):.1f}",
            "latitude": f"{random.uniform(22.5, 22.6):.6f}",
            "longitude": f"{random.uniform(114.0, 114.1):.6f}",
            "altitude": "10",
            "stress": random.randint(0, 100),
            "upload_method": "wifi",
            "blood_pressure_systolic": random.randint(90, 140),
            "blood_pressure_diastolic": random.randint(60, 90),
            "sleepData": "null",
            "exerciseDailyData": "null", 
            "exerciseWeekData": "null",
            "scientificSleepData": "null",
            "workoutData": "null",
            "timestamp": timestamp
        }
    
    def get_test_events(self) -> List[Dict]:
        """获取所有测试事件类型"""
        events = []
        
        # 紧急事件（需要微信发送）
        emergency_events = [
            {
                "name": "SOS事件",
                "eventType": "SOS_EVENT", 
                "eventValue": "1",
                "expect_wechat": True,
                "expect_platform_msg": True,
                "expect_alert": True
            },
            {
                "name": "跌倒检测",
                "eventType": "FALLDOWN_EVENT",
                "eventValue": "1", 
                "expect_wechat": True,
                "expect_platform_msg": True,
                "expect_alert": True
            },
            {
                "name": "一键报警",
                "eventType": "ONE_KEY_ALARM",
                "eventValue": "1",
                "expect_wechat": True,
                "expect_platform_msg": True, 
                "expect_alert": True
            }
        ]
        
        # 普通事件（只需平台消息）
        normal_events = [
            {
                "name": "穿戴状态变化",
                "eventType": "com.tdtech.ohos.action.WEAR_STATUS_CHANGED",
                "eventValue": "0",
                "expect_wechat": False,
                "expect_platform_msg": True,
                "expect_alert": False
            },
            {
                "name": "心率异常",
                "eventType": "HEART_RATE_ABNORMAL",
                "eventValue": "150",
                "expect_wechat": False,
                "expect_platform_msg": True,
                "expect_alert": True
            },
            {
                "name": "血压异常", 
                "eventType": "BLOOD_PRESSURE_ABNORMAL",
                "eventValue": "160/100",
                "expect_wechat": False,
                "expect_platform_msg": True,
                "expect_alert": True
            },
            {
                "name": "低电量警告",
                "eventType": "LOW_BATTERY_WARNING",
                "eventValue": "15",
                "expect_wechat": False,
                "expect_platform_msg": True,
                "expect_alert": False
            },
            {
                "name": "设备离线",
                "eventType": "DEVICE_OFFLINE", 
                "eventValue": "1",
                "expect_wechat": False,
                "expect_platform_msg": True,
                "expect_alert": False
            },
            {
                "name": "运动开始",
                "eventType": "EXERCISE_START",
                "eventValue": "running",
                "expect_wechat": False,
                "expect_platform_msg": True,
                "expect_alert": False
            },
            {
                "name": "睡眠检测",
                "eventType": "SLEEP_DETECTED",
                "eventValue": "deep_sleep",
                "expect_wechat": False,
                "expect_platform_msg": True,
                "expect_alert": False
            }
        ]
        
        return emergency_events + normal_events
    
    def send_event(self, event_data: Dict) -> Dict:
        """发送事件到API接口"""
        url = f"{self.base_url}/upload_common_event"
        headers = {'Content-Type': 'application/json'}
        
        # 构建完整的事件数据
        full_event = {
            "eventType": event_data["eventType"],
            "eventValue": event_data["eventValue"], 
            "deviceSn": self.test_device_sn,
            "heatlhData": json.dumps({"data": self.generate_health_data(self.test_device_sn)})
        }
        
        try:
            response = requests.post(url, json=full_event, headers=headers, timeout=10)
            return {
                "success": True,
                "status_code": response.status_code,
                "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                "event": full_event
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "event": full_event
            }
    
    def check_alert_record(self, device_sn: str, event_type: str, timeout: int = 5) -> bool:
        """检查t_alert_info表中的告警记录"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # 等待数据插入（异步处理可能有延迟）
        for _ in range(timeout):
            try:
                query = """
                SELECT id, alert_type, device_sn, alert_timestamp, severity_level, alert_status 
                FROM t_alert_info 
                WHERE device_sn = %s AND alert_type LIKE %s 
                ORDER BY alert_timestamp DESC LIMIT 1
                """
                cursor.execute(query, (device_sn, f"%{event_type}%"))
                result = cursor.fetchone()
                
                if result:
                    cursor.close()
                    conn.close()
                    return True
                    
                time.sleep(1)
            except Exception as e:
                print(f"检查告警记录失败: {e}")
                break
        
        cursor.close()
        conn.close()
        return False
    
    def check_health_data(self, device_sn: str, timeout: int = 5) -> bool:
        """检查t_user_health_data表中的健康数据"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        for _ in range(timeout):
            try:
                query = """
                SELECT id, device_sn, heart_rate, blood_oxygen, timestamp 
                FROM t_user_health_data 
                WHERE device_sn = %s 
                ORDER BY timestamp DESC LIMIT 1
                """
                cursor.execute(query, (device_sn,))
                result = cursor.fetchone()
                
                if result:
                    cursor.close()
                    conn.close()
                    return True
                    
                time.sleep(1)
            except Exception as e:
                print(f"检查健康数据失败: {e}")
                break
        
        cursor.close()
        conn.close()
        return False
    
    def check_platform_message(self, device_sn: str, timeout: int = 5) -> bool:
        """检查平台消息发送情况"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        for _ in range(timeout):
            try:
                query = """
                SELECT id, device_sn, message, message_type, send_time 
                FROM t_device_message 
                WHERE device_sn = %s 
                ORDER BY send_time DESC LIMIT 1
                """
                cursor.execute(query, (device_sn,))
                result = cursor.fetchone()
                
                if result:
                    cursor.close()
                    conn.close()
                    return True
                    
                time.sleep(1)
            except Exception as e:
                print(f"检查平台消息失败: {e}")
                break
        
        cursor.close()
        conn.close()
        return False
    
    def test_single_event(self, event_config: Dict) -> Dict:
        """测试单个事件"""
        print(f"\n🧪 测试事件: {event_config['name']} ({event_config['eventType']})")
        
        # 发送事件
        result = self.send_event(event_config)
        if not result["success"]:
            return {
                "event": event_config["name"],
                "success": False,
                "error": f"API调用失败: {result['error']}"
            }
        
        print(f"📡 API响应: {result['response']}")
        
        # 验证结果
        checks = {}
        
        # 检查健康数据插入
        print("🔍 检查健康数据插入...")
        checks["health_data"] = self.check_health_data(self.test_device_sn)
        print(f"   健康数据: {'✅' if checks['health_data'] else '❌'}")
        
        # 检查告警记录（如果期望的话）
        if event_config["expect_alert"]:
            print("🔍 检查告警记录...")
            checks["alert_record"] = self.check_alert_record(self.test_device_sn, event_config["eventType"])
            print(f"   告警记录: {'✅' if checks['alert_record'] else '❌'}")
        
        # 检查平台消息（如果期望的话）
        if event_config["expect_platform_msg"]:
            print("🔍 检查平台消息...")
            checks["platform_msg"] = self.check_platform_message(self.test_device_sn)
            print(f"   平台消息: {'✅' if checks['platform_msg'] else '❌'}")
        
        # 微信发送检查（紧急事件）
        if event_config["expect_wechat"]:
            print("🔍 微信发送检查...")
            # 从API响应中推断微信发送状态
            api_response = result.get("response", {})
            wechat_attempted = "微信" in str(api_response) or "wechat" in str(api_response).lower()
            checks["wechat_send"] = wechat_attempted
            print(f"   微信发送: {'✅' if checks['wechat_send'] else '❌'}")
        
        # 判断整体测试是否成功
        required_checks = ["health_data"]
        if event_config["expect_alert"]:
            required_checks.append("alert_record")
        if event_config["expect_platform_msg"]:
            required_checks.append("platform_msg")
        if event_config["expect_wechat"]:
            required_checks.append("wechat_send")
        
        overall_success = all(checks.get(check, False) for check in required_checks)
        
        return {
            "event": event_config["name"],
            "event_type": event_config["eventType"],
            "success": overall_success,
            "api_response": result["response"],
            "checks": checks,
            "expected": {
                "wechat": event_config["expect_wechat"],
                "platform_msg": event_config["expect_platform_msg"],
                "alert": event_config["expect_alert"]
            }
        }
    
    def run_complete_test(self) -> List[Dict]:
        """运行完整测试套件"""
        print("🚀 开始upload_common_event接口完整自动化测试")
        print(f"📱 测试设备序列号: {self.test_device_sn}")
        print(f"🌐 API地址: {self.base_url}")
        print("="*80)
        
        test_events = self.get_test_events()
        results = []
        
        for i, event_config in enumerate(test_events, 1):
            print(f"\n[{i}/{len(test_events)}] 测试进度...")
            result = self.test_single_event(event_config)
            results.append(result)
            self.test_results.append(result)
            
            # 每次测试后稍作延迟，避免并发问题
            time.sleep(2)
        
        return results
    
    def generate_report(self, results: List[Dict]) -> str:
        """生成测试报告"""
        total = len(results)
        passed = sum(1 for r in results if r["success"])
        failed = total - passed
        
        report = f"""
🔍 upload_common_event接口自动化测试报告
{"="*60}
📊 测试概况:
   - 总测试数: {total}
   - 通过数量: {passed} ✅
   - 失败数量: {failed} ❌
   - 成功率: {(passed/total*100):.1f}%

📱 测试设备: {self.test_device_sn}
⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📋 详细结果:
"""
        
        for i, result in enumerate(results, 1):
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            report += f"\n{i:2d}. {result['event']} ({result['event_type']}) - {status}"
            
            if result["success"]:
                checks = result["checks"]
                report += f"\n    健康数据: {'✅' if checks.get('health_data') else '❌'}"
                if result["expected"]["alert"]:
                    report += f" | 告警记录: {'✅' if checks.get('alert_record') else '❌'}"
                if result["expected"]["platform_msg"]:
                    report += f" | 平台消息: {'✅' if checks.get('platform_msg') else '❌'}"
                if result["expected"]["wechat"]:
                    report += f" | 微信发送: {'✅' if checks.get('wechat_send') else '❌'}"
            else:
                if "error" in result:
                    report += f"\n    错误: {result['error']}"

        report += f"\n\n🏁 测试完成，总用时: {len(results)*2}秒"
        return report
    
    def cleanup_test_data(self):
        """清理测试数据"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 清理告警记录
            cursor.execute("DELETE FROM t_alert_info WHERE device_sn = %s", (self.test_device_sn,))
            
            # 清理健康数据
            cursor.execute("DELETE FROM t_user_health_data WHERE device_sn = %s", (self.test_device_sn,))
            
            # 清理消息记录
            cursor.execute("DELETE FROM t_device_message WHERE device_sn = %s", (self.test_device_sn,))
            
            conn.commit()
            print(f"🧹 测试数据清理完成: {self.test_device_sn}")
            
        except Exception as e:
            print(f"❌ 清理测试数据失败: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

def main():
    """主函数"""
    print("🔧 初始化测试环境...")
    
    # 创建测试器实例
    tester = CommonEventTester()
    
    try:
        # 运行完整测试
        results = tester.run_complete_test()
        
        # 生成并显示报告
        report = tester.generate_report(results)
        print(report)
        
        # 保存报告到文件
        report_file = f"upload_common_event_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n📄 测试报告已保存: {report_file}")
        
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理测试数据
        try:
            tester.cleanup_test_data()
        except:
            pass

if __name__ == "__main__":
    main() 
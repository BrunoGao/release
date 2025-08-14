#!/usr/bin/env python3
"""upload_common_event接口完整自动化测试"""
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List
import sys
import os

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from test_framework.base_test import BaseTestFramework

# 规则ID映射
RULE_ID_MAPPING = {
    'FALLDOWN_EVENT': 1920703322679980035,
    'ONE_KEY_ALARM': 1920247213216960513,
    'SOS_EVENT': 1920703322679980034,
    'WEAR_STATUS_CHANGED': 1920703322679980036
}

class UploadCommonEventTest(BaseTestFramework):
    """upload_common_event接口自动化测试"""
    
    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.test_device_sn = self.generate_test_device_sn()
        
    def generate_health_data(self, device_sn: str) -> Dict:
        """生成模拟健康数据"""
        return {
            "deviceSn": device_sn,
            "heart_rate": 84,
            "blood_oxygen": 98,
            "body_temperature": "36.5",
            "step": 1000,
            "distance": "2.5",
            "calorie": "150.0",
            "latitude": "22.540368",
            "longitude": "114.015090",
            "altitude": "10",
            "stress": 30,
            "upload_method": "wifi",
            "blood_pressure_systolic": 125,
            "blood_pressure_diastolic": 86,
            "sleepData": "null",
            "exerciseDailyData": "null",
            "exerciseWeekData": "null",
            "scientificSleepData": "null",
            "workoutData": "null",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def get_test_events(self) -> List[Dict]:
        """获取测试事件配置"""
        return [
            {
                "name": "SOS紧急求救",
                "eventType": "SOS_EVENT",
                "eventValue": "1",
                "expect_alert": True,
                "expect_message": True,
                "expect_wechat": True,
                "priority": "emergency"
            },
            {
                "name": "跌倒检测",
                "eventType": "FALLDOWN_EVENT", 
                "eventValue": "1",
                "expect_alert": True,
                "expect_message": True,
                "expect_wechat": True,
                "priority": "emergency"
            },
            {
                "name": "一键报警",
                "eventType": "ONE_KEY_ALARM",
                "eventValue": "1",
                "expect_alert": True,
                "expect_message": True,
                "expect_wechat": True,
                "priority": "emergency"
            },
            {
                "name": "穿戴状态变化",
                "eventType": "com.tdtech.ohos.action.WEAR_STATUS_CHANGED",
                "eventValue": "0",
                "expect_alert": False,
                "expect_message": True,
                "expect_wechat": False,
                "priority": "normal"
            }
        ]
    
    def test_api_basic_functionality(self) -> bool:
        """测试API基础功能"""
        event_data = {
            "eventType": "SOS_EVENT",
            "eventValue": "1",
            "deviceSn": self.test_device_sn,
            "heatlhData": json.dumps({"data": self.generate_health_data(self.test_device_sn)})
        }
        
        result = self.make_api_request('/upload_common_event', data=event_data)
        
        success = (
            result['success'] and 
            result['status_code'] == 200 and
            isinstance(result['response'], dict) and
            result['response'].get('status') == 'success'
        )
        
        self.add_test_result(
            "API基础功能测试",
            success,
            {'api_result': result}
        )
        
        return success
    
    def test_health_data_insertion(self, device_sn: str) -> bool:
        """测试健康数据插入"""
        def check_health_data():
            query = """
                SELECT COUNT(*) FROM t_user_health_data 
                WHERE device_sn = %s AND timestamp >= %s
            """
            time_threshold = datetime.now() - timedelta(minutes=5)
            result = self.execute_db_query(query, (device_sn, time_threshold))
            return result and result[0][0] > 0
        
        success = self.wait_for_condition(check_health_data, timeout=30)
        
        self.add_test_result(
            "健康数据插入测试",
            success,
            {'device_sn': device_sn}
        )
        
        return success
    
    def test_alert_generation(self, device_sn: str, event_type: str) -> bool:
        """测试告警生成机制"""
        def check_alert_generated():
            query = """
                SELECT COUNT(*) FROM t_alert_info 
                WHERE device_sn = %s AND alert_timestamp >= %s
            """
            time_threshold = datetime.now() - timedelta(minutes=5)
            result = self.execute_db_query(query, (device_sn, time_threshold))
            return result and result[0][0] > 0
        
        success = self.wait_for_condition(check_alert_generated, timeout=60)
        
        self.add_test_result(
            f"告警生成测试-{event_type}",
            success,
            {'device_sn': device_sn, 'event_type': event_type}
        )
        
        return success
    
    def test_message_delivery(self, device_sn: str, event_type: str) -> bool:
        """测试平台消息下发"""
        def check_message_sent():
            query = """
                SELECT COUNT(*) FROM t_device_message 
                WHERE device_sn = %s AND sent_time >= %s
            """
            time_threshold = datetime.now() - timedelta(minutes=5)
            result = self.execute_db_query(query, (device_sn, time_threshold))
            return result and result[0][0] > 0
        
        success = self.wait_for_condition(check_message_sent, timeout=60)
        
        self.add_test_result(
            f"平台消息下发测试-{event_type}",
            success,
            {'device_sn': device_sn, 'event_type': event_type}
        )
        
        return success
    
    def test_wechat_notification(self, event_type: str) -> bool:
        """测试微信通知发送"""
        test_data = {
            "alert_type": event_type,
            "user_name": "测试用户",
            "severity": "high",
            "device_sn": self.test_device_sn
        }
        
        result = self.make_api_request('/api/test/wechat', data=test_data)
        
        success = False
        if result['success'] and result['status_code'] == 200:
            response_text = str(result['response'])
            wechat_indicators = ['微信', 'wechat', '企业微信', '公众号', 'corp_id', 'appid']
            success = any(indicator in response_text.lower() for indicator in wechat_indicators)
        
        self.add_test_result(
            f"微信通知测试-{event_type}",
            success,
            {'api_result': result}
        )
        
        return success
    
    def test_event_processing_workflow(self, event_config: Dict) -> Dict:
        """测试完整的事件处理工作流"""
        event_name = event_config['name']
        event_type = event_config['eventType']
        
        self.logger.info(f"开始测试事件: {event_name}")
        
        # 发送事件
        event_data = {
            "eventType": event_type,
            "eventValue": event_config['eventValue'],
            "deviceSn": self.test_device_sn,
            "heatlhData": json.dumps({"data": self.generate_health_data(self.test_device_sn)})
        }
        
        api_result = self.make_api_request('/upload_common_event', data=event_data)
        
        if not api_result['success']:
            return {'success': False, 'error': f"API调用失败: {api_result.get('error')}"}
        
        # 验证各个处理步骤
        health_success = self.test_health_data_insertion(self.test_device_sn)
        
        alert_success = True
        if event_config['expect_alert']:
            alert_success = self.test_alert_generation(self.test_device_sn, event_type)
        
        message_success = True
        if event_config['expect_message']:
            message_success = self.test_message_delivery(self.test_device_sn, event_type)
        
        wechat_success = True
        if event_config['expect_wechat']:
            wechat_success = self.test_wechat_notification(event_type)
        
        # 计算总体成功率
        checks = [health_success]
        if event_config['expect_alert']:
            checks.append(alert_success)
        if event_config['expect_message']:
            checks.append(message_success)
        if event_config['expect_wechat']:
            checks.append(wechat_success)
        
        overall_success = all(checks)
        
        result = {
            'success': overall_success,
            'event_name': event_name,
            'event_type': event_type,
            'checks': {
                'health_data': health_success,
                'alert_generation': alert_success if event_config['expect_alert'] else None,
                'message_delivery': message_success if event_config['expect_message'] else None,
                'wechat_notification': wechat_success if event_config['expect_wechat'] else None
            }
        }
        
        self.add_test_result(
            f"完整工作流测试-{event_name}",
            overall_success,
            result
        )
        
        return result
    
    def run_tests(self) -> List[Dict]:
        """运行完整测试套件"""
        self.logger.info("开始upload_common_event接口自动化测试")
        
        try:
            # 基础功能测试
            self.test_api_basic_functionality()
            
            # 事件处理工作流测试
            test_events = self.get_test_events()
            workflow_results = []
            
            for event_config in test_events:
                result = self.test_event_processing_workflow(event_config)
                workflow_results.append(result)
                time.sleep(3)  # 每个事件测试后等待
            
            # 生成综合报告
            self.generate_comprehensive_report(workflow_results)
            
            return self.test_results
            
        except Exception as e:
            self.logger.error(f"测试过程中发生异常: {e}")
            self.add_test_result("测试套件执行", False, {'error': str(e)})
            return self.test_results
        
        finally:
            if self.config['cleanup_test_data']:
                self.cleanup_test_data(self.test_device_sn)
    
    def generate_comprehensive_report(self, workflow_results: List[Dict]):
        """生成综合测试报告"""
        total_workflows = len(workflow_results)
        successful_workflows = sum(1 for r in workflow_results if r['success'])
        
        report = f"""
📊 upload_common_event接口综合测试报告
{'='*80}

🎯 工作流测试结果:
   - 总工作流数: {total_workflows}
   - 成功工作流: {successful_workflows}
   - 工作流成功率: {(successful_workflows/total_workflows*100):.1f}%

📋 详细工作流结果:
"""
        
        for i, result in enumerate(workflow_results, 1):
            status = "✅" if result['success'] else "❌"
            report += f"\n{i}. {result['event_name']} {status}"
            
            checks = result['checks']
            check_details = []
            for check_name, check_result in checks.items():
                if check_result is not None:
                    check_status = "✅" if check_result else "❌"
                    check_details.append(f"{check_name}:{check_status}")
            
            if check_details:
                report += f"\n   {' | '.join(check_details)}"
        
        self.logger.info(report)
        
        # 保存报告到文件
        report_file = f"upload_common_event_comprehensive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        self.logger.info(f"综合报告已保存: {report_file}")

def main():
    """主函数"""
    print("🚀 启动upload_common_event接口自动化测试")
    
    config = {
        'api_base_url': 'http://localhost:5001',
        'test_timeout': 30,
        'cleanup_test_data': True
    }
    
    test_suite = UploadCommonEventTest(config)
    
    try:
        results = test_suite.run_tests()
        
        basic_report = test_suite.generate_report()
        print(basic_report)
        
        report_file = f"upload_common_event_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(basic_report)
        
        print(f"\n📄 测试报告已保存: {report_file}")
        
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r['success'])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n🏆 总体测试成功率: {success_rate:.1f}%")
        
    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 
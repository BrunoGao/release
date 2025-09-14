#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
完整消息系统数据流测试脚本
测试六大核心功能：平台下发、群发、告警自动发送、手机端确认、状态跟踪、统计生命周期
"""

import requests
import json
import time
import random
import sys
from datetime import datetime, timedelta

# 测试配置
BASE_URL = "http://localhost:5225"  # 本地开发环境
TEST_DEVICE_SN = "TEST_DEVICE_001"
TEST_USER_ID = "1"
TEST_ORG_ID = "1"

class MessageSystemTester:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
    def log_result(self, test_name, success, message, details=None):
        """记录测试结果"""
        result = {
            'test_name': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'details': details
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} | {test_name}: {message}")
        
        if details:
            print(f"     详情: {details}")
    
    def test_platform_message_send(self):
        """测试1: ljwx-admin 和 ljwx-bigscreen 平台消息下发"""
        print("\n🔄 测试1: 平台消息下发功能")
        
        # 测试数据
        test_messages = [
            {
                "device_sn": TEST_DEVICE_SN,
                "message": "【安全提醒】请注意工作区域内的高温设备，避免烫伤风险。",
                "org_id": TEST_ORG_ID,
                "user_id": TEST_USER_ID,
                "message_type": "announcement",
                "sender_type": "platform",
                "receiver_type": "device"
            },
            {
                "device_sn": "all",
                "message": "【任务通知】今日安全检查任务已分配，请各部门按时完成。",
                "org_id": TEST_ORG_ID,
                "message_type": "task",
                "sender_type": "platform", 
                "receiver_type": "department"
            }
        ]
        
        sent_message_ids = []
        
        for i, message_data in enumerate(test_messages):
            try:
                response = self.session.post(
                    f"{self.base_url}/DeviceMessage/save_message",
                    json=message_data,
                    timeout=10
                )
                
                if response.status_code == 201:
                    result = response.json()
                    if result.get('status') == 'success':
                        message_id = result.get('message_id')
                        sent_message_ids.append(message_id)
                        self.log_result(
                            f"平台消息下发 #{i+1}",
                            True,
                            f"消息发送成功，ID: {message_id}",
                            message_data['message'][:50] + "..."
                        )
                    else:
                        self.log_result(
                            f"平台消息下发 #{i+1}",
                            False,
                            f"发送失败: {result.get('message', 'Unknown error')}"
                        )
                else:
                    self.log_result(
                        f"平台消息下发 #{i+1}",
                        False,
                        f"HTTP错误: {response.status_code}"
                    )
                    
            except Exception as e:
                self.log_result(
                    f"平台消息下发 #{i+1}",
                    False,
                    f"请求异常: {str(e)}"
                )
        
        return sent_message_ids
    
    def test_group_messaging(self):
        """测试2: 个人和部门群发消息"""
        print("\n🔄 测试2: 群发消息功能")
        
        # 部门群发测试
        group_message_data = {
            "device_sn": "all",
            "message": "【重要公告】明日将进行设备维护，请各位同事提前做好准备工作。维护时间：09:00-17:00",
            "org_id": TEST_ORG_ID,
            "message_type": "announcement",
            "sender_type": "admin",
            "receiver_type": "department"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/DeviceMessage/save_message",
                json=group_message_data,
                timeout=10
            )
            
            if response.status_code == 201:
                result = response.json()
                if result.get('status') == 'success':
                    self.log_result(
                        "部门群发消息",
                        True,
                        f"群发成功，消息ID: {result.get('message_id')}",
                        f"消息类型: {group_message_data['message_type']}"
                    )
                    return result.get('message_id')
                else:
                    self.log_result(
                        "部门群发消息",
                        False,
                        f"群发失败: {result.get('message', 'Unknown error')}"
                    )
            else:
                self.log_result(
                    "部门群发消息", 
                    False,
                    f"HTTP错误: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result(
                "部门群发消息",
                False,
                f"请求异常: {str(e)}"
            )
            
        return None
    
    def test_auto_alert_message(self):
        """测试3: 告警触发自动消息发送"""
        print("\n🔄 测试3: 告警自动消息发送")
        
        # 模拟健康数据上传触发告警
        alert_health_data = {
            "deviceSn": TEST_DEVICE_SN,
            "userId": TEST_USER_ID,
            "heart_rate": 120,  # 异常心率，触发告警
            "blood_oxygen": 88,  # 异常血氧，触发告警
            "temperature": 38.5,  # 异常体温，触发告警
            "timestamp": datetime.now().isoformat(),
            "location": {"latitude": 39.9042, "longitude": 116.4074}
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/upload_health_data",
                json=alert_health_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_result(
                    "告警数据上传",
                    True,
                    "健康数据上传成功，可能触发告警消息",
                    f"心率: {alert_health_data['heart_rate']}, 血氧: {alert_health_data['blood_oxygen']}"
                )
                
                # 等待告警处理
                time.sleep(3)
                
                # 检查是否生成了告警消息
                return self.verify_alert_message_generated(TEST_DEVICE_SN)
                
            else:
                self.log_result(
                    "告警数据上传",
                    False,
                    f"数据上传失败: HTTP {response.status_code}"
                )
                
        except Exception as e:
            self.log_result(
                "告警数据上传",
                False,
                f"请求异常: {str(e)}"
            )
            
        return False
    
    def verify_alert_message_generated(self, device_sn):
        """验证告警消息是否生成"""
        try:
            response = self.session.get(
                f"{self.base_url}/DeviceMessage/receive?deviceSn={device_sn}",
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    messages = result.get('data', {}).get('messages', [])
                    
                    # 查找告警类型的消息
                    alert_messages = [msg for msg in messages if msg.get('message_type') == 'warning']
                    
                    if alert_messages:
                        self.log_result(
                            "告警消息验证",
                            True,
                            f"检测到 {len(alert_messages)} 条告警消息",
                            f"最新告警: {alert_messages[0].get('message', '')[:100]}..."
                        )
                        return alert_messages[0].get('message_id')
                    else:
                        self.log_result(
                            "告警消息验证",
                            False,
                            "未检测到告警消息"
                        )
                else:
                    self.log_result(
                        "告警消息验证",
                        False,
                        f"获取消息失败: {result.get('message', 'Unknown error')}"
                    )
            else:
                self.log_result(
                    "告警消息验证",
                    False,
                    f"HTTP错误: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result(
                "告警消息验证", 
                False,
                f"验证异常: {str(e)}"
            )
            
        return None
    
    def test_mobile_message_acknowledgment(self, message_id=None):
        """测试4: 手机端消息查看和确认"""
        print("\n🔄 测试4: 手机端消息确认功能")
        
        if not message_id:
            # 先获取待确认的消息
            message_id = self.get_pending_message(TEST_DEVICE_SN)
        
        if not message_id:
            self.log_result(
                "手机端消息确认",
                False,
                "没有找到待确认的消息"
            )
            return False
        
        # 测试消息确认 API
        acknowledge_data = {
            "message_id": message_id,
            "device_sn": TEST_DEVICE_SN,
            "user_id": TEST_USER_ID,
            "acknowledgment_type": "acknowledged",
            "acknowledgment_message": "已收到消息，将按要求执行相关操作。",
            "location": {
                "latitude": 39.9042,
                "longitude": 116.4074
            }
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/DeviceMessage/acknowledge",
                json=acknowledge_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.log_result(
                        "手机端消息确认",
                        True,
                        f"消息确认成功",
                        f"消息ID: {message_id}, 确认类型: {acknowledge_data['acknowledgment_type']}"
                    )
                    return True
                else:
                    self.log_result(
                        "手机端消息确认",
                        False,
                        f"确认失败: {result.get('message', 'Unknown error')}"
                    )
            else:
                self.log_result(
                    "手机端消息确认",
                    False,
                    f"HTTP错误: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result(
                "手机端消息确认",
                False,
                f"请求异常: {str(e)}"
            )
        
        return False
    
    def get_pending_message(self, device_sn):
        """获取待确认的消息"""
        try:
            response = self.session.get(
                f"{self.base_url}/DeviceMessage/receive?deviceSn={device_sn}",
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    messages = result.get('data', {}).get('messages', [])
                    
                    # 查找未确认的消息
                    pending_messages = [msg for msg in messages if msg.get('message_status') != '2']
                    
                    if pending_messages:
                        return pending_messages[0].get('message_id')
                        
        except Exception as e:
            print(f"获取待确认消息失败: {e}")
            
        return None
    
    def test_watch_functionality(self):
        """测试手表端功能"""
        print("\n🔄 测试: 手表端专用功能")
        
        # 测试手表端消息摘要
        try:
            response = self.session.get(
                f"{self.base_url}/DeviceMessage/watch_summary?deviceSn={TEST_DEVICE_SN}",
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    data = result.get('data', {})
                    self.log_result(
                        "手表端消息摘要",
                        True,
                        f"获取成功: {data.get('total_count')} 条消息",
                        f"紧急消息: {data.get('urgent_count')} 条"
                    )
                else:
                    self.log_result(
                        "手表端消息摘要",
                        False,
                        f"获取失败: {result.get('error', 'Unknown error')}"
                    )
            else:
                self.log_result(
                    "手表端消息摘要",
                    False,
                    f"HTTP错误: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result(
                "手表端消息摘要",
                False,
                f"请求异常: {str(e)}"
            )
    
    def test_message_tracking(self):
        """测试5: 消息状态跟踪功能"""
        print("\n🔄 测试5: 消息状态跟踪")
        
        try:
            # 获取消息统计数据
            response = self.session.get(
                f"{self.base_url}/get_messages_by_orgIdAndUserId?orgId={TEST_ORG_ID}&userId={TEST_USER_ID}",
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    messages = result.get('data', [])
                    
                    # 统计消息状态
                    status_count = {}
                    for msg in messages:
                        status = msg.get('message_status', 'unknown')
                        status_count[status] = status_count.get(status, 0) + 1
                    
                    self.log_result(
                        "消息状态跟踪",
                        True,
                        f"成功获取 {len(messages)} 条消息的状态信息",
                        f"状态分布: {status_count}"
                    )
                    
                    return True
                else:
                    self.log_result(
                        "消息状态跟踪",
                        False,
                        f"获取失败: {result.get('message', 'Unknown error')}"
                    )
            else:
                self.log_result(
                    "消息状态跟踪",
                    False,
                    f"HTTP错误: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result(
                "消息状态跟踪",
                False,
                f"请求异常: {str(e)}"
            )
        
        return False
    
    def test_message_lifecycle_stats(self):
        """测试6: 消息统计和生命周期管理"""
        print("\n🔄 测试6: 消息生命周期统计")
        
        try:
            # 获取消息统计数据
            response = self.session.get(
                f"{self.base_url}/get_message_stats_by_orgIdAndUserId?orgId={TEST_ORG_ID}&userId={TEST_USER_ID}",
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    stats = result.get('data', {})
                    
                    self.log_result(
                        "消息生命周期统计",
                        True,
                        "统计数据获取成功",
                        f"响应率: {stats.get('response_rate', 0):.1%}, " +
                        f"平均响应时间: {stats.get('avg_response_time', 0):.1f}小时"
                    )
                    
                    return True
                else:
                    self.log_result(
                        "消息生命周期统计",
                        False,
                        f"获取失败: {result.get('message', 'Unknown error')}"
                    )
            else:
                self.log_result(
                    "消息生命周期统计",
                    False,
                    f"HTTP错误: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result(
                "消息生命周期统计",
                False,
                f"请求异常: {str(e)}"
            )
        
        return False
    
    def test_batch_acknowledgment(self):
        """测试批量确认功能"""
        print("\n🔄 测试: 批量消息确认")
        
        # 获取多条未确认消息
        pending_message_ids = []
        try:
            response = self.session.get(
                f"{self.base_url}/DeviceMessage/receive?deviceSn={TEST_DEVICE_SN}",
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    messages = result.get('data', {}).get('messages', [])
                    pending_message_ids = [
                        msg.get('message_id') for msg in messages[:3]
                        if msg.get('message_status') != '2'
                    ]
        except Exception as e:
            print(f"获取待确认消息失败: {e}")
        
        if not pending_message_ids:
            self.log_result(
                "批量消息确认",
                False,
                "没有找到待确认的消息进行批量操作"
            )
            return False
        
        # 执行批量确认
        batch_data = {
            "message_ids": pending_message_ids,
            "device_sn": TEST_DEVICE_SN,
            "user_id": TEST_USER_ID,
            "acknowledgment_type": "read",
            "acknowledgment_message": "批量确认消息已读"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/DeviceMessage/batch_acknowledge",
                json=batch_data,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    data = result.get('data', {})
                    self.log_result(
                        "批量消息确认",
                        True,
                        f"批量确认成功: {data.get('success_count')}/{data.get('total_count')}",
                        f"处理消息: {len(pending_message_ids)} 条"
                    )
                    return True
                else:
                    self.log_result(
                        "批量消息确认",
                        False,
                        f"批量确认失败: {result.get('message', 'Unknown error')}"
                    )
            else:
                self.log_result(
                    "批量消息确认",
                    False,
                    f"HTTP错误: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result(
                "批量消息确认",
                False,
                f"请求异常: {str(e)}"
            )
        
        return False
    
    def run_comprehensive_test(self):
        """运行完整的消息系统测试"""
        print("=" * 80)
        print("🚀 LJWX-BigScreen 消息系统完整数据流测试")
        print("=" * 80)
        print(f"测试目标: {self.base_url}")
        print(f"测试设备: {TEST_DEVICE_SN}")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # 执行六大功能测试
        sent_message_ids = self.test_platform_message_send()  # 测试1: 平台下发
        group_message_id = self.test_group_messaging()        # 测试2: 群发
        alert_message_id = self.test_auto_alert_message()     # 测试3: 告警自动发送
        
        # 使用生成的消息ID进行确认测试
        test_message_id = None
        if sent_message_ids:
            test_message_id = sent_message_ids[0]
        elif group_message_id:
            test_message_id = group_message_id
        elif alert_message_id:
            test_message_id = alert_message_id
            
        self.test_mobile_message_acknowledgment(test_message_id)  # 测试4: 手机端确认
        self.test_message_tracking()                            # 测试5: 状态跟踪
        self.test_message_lifecycle_stats()                     # 测试6: 生命周期统计
        
        # 额外功能测试
        self.test_watch_functionality()     # 手表端功能
        self.test_batch_acknowledgment()    # 批量确认
        
        self.print_test_summary()
    
    def print_test_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 80)
        print("📊 测试结果总结")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"总测试数: {total_tests}")
        print(f"通过数: {passed_tests} ✅")
        print(f"失败数: {failed_tests} ❌")
        print(f"成功率: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ 失败的测试:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['test_name']}: {result['message']}")
        
        print("\n" + "=" * 80)
        print("🎯 六大核心功能验证结果:")
        print("=" * 80)
        
        core_functions = [
            ("1. 平台消息下发", ["平台消息下发"]),
            ("2. 个人/部门群发", ["部门群发消息"]),
            ("3. 告警自动发送", ["告警数据上传", "告警消息验证"]),
            ("4. 手机端确认", ["手机端消息确认"]),
            ("5. 状态跟踪", ["消息状态跟踪"]),
            ("6. 生命周期统计", ["消息生命周期统计"])
        ]
        
        for func_name, test_names in core_functions:
            func_results = [r for r in self.test_results if any(test_name in r['test_name'] for test_name in test_names)]
            func_success = all(r['success'] for r in func_results) and len(func_results) > 0
            status = "✅ 通过" if func_success else "❌ 失败"
            print(f"{status} | {func_name}")
        
        print("\n" + "=" * 80)
        
        if success_rate >= 80:
            print("🎉 消息系统整体测试 PASSED - 数据流已完全打通！")
        else:
            print("⚠️  消息系统整体测试 FAILED - 需要修复部分问题")
        
        print("=" * 80)

def main():
    """主函数"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = BASE_URL
    
    tester = MessageSystemTester(base_url)
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()
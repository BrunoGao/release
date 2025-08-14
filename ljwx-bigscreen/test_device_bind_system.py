#!/usr/bin/env python3
"""设备绑定系统完整功能测试脚本"""

import requests
import json
import time
from datetime import datetime

# 测试配置
BASE_URL = "http://localhost:5001"
TEST_DEVICE_SN = "A5GTQ24B26000999"  #测试设备序列号
TEST_USER_ID = 1926920017289154501  #测试用户ID
TEST_ORG_ID = 1  #测试组织ID

class DeviceBindTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
    
    def log_test(self, test_name, success, message="", data=None):
        """记录测试结果"""
        status = "✅ 通过" if success else "❌ 失败"
        result = {
            'test': test_name,
            'status': status,
            'message': message,
            'data': data,
            'time': datetime.now().strftime('%H:%M:%S')
        }
        self.test_results.append(result)
        print(f"{status} {test_name}: {message}")
        if data: print(f"    返回数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    def test_qrcode_generation(self):
        """测试二维码生成"""
        print("\n🔍 测试1: 二维码生成功能")
        try:
            response = self.session.get(f"{BASE_URL}/api/device/{TEST_DEVICE_SN}/qrcode")
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 200 and 'qrcode' in data.get('data', {}):
                    self.log_test("二维码生成", True, "成功生成设备绑定二维码", data.get('data'))
                    return data.get('data', {}).get('url')
                else:
                    self.log_test("二维码生成", False, f"返回格式错误: {data}")
            else:
                self.log_test("二维码生成", False, f"HTTP状态码: {response.status_code}")
        except Exception as e:
            self.log_test("二维码生成", False, f"请求异常: {str(e)}")
        return None
    
    def test_bind_apply(self):
        """测试绑定申请"""
        print("\n🔍 测试2: 设备绑定申请")
        try:
            apply_data = {
                "sn": TEST_DEVICE_SN,
                "user_id": TEST_USER_ID,
                "org_id": TEST_ORG_ID
            }
            
            response = self.session.post(
                f"{BASE_URL}/api/device/bind/apply",
                json=apply_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 200:
                    self.log_test("绑定申请提交", True, data.get('msg'), data.get('data'))
                    return data.get('data', {}).get('id')
                else:
                    self.log_test("绑定申请提交", False, data.get('msg'))
            else:
                self.log_test("绑定申请提交", False, f"HTTP状态码: {response.status_code}")
        except Exception as e:
            self.log_test("绑定申请提交", False, f"请求异常: {str(e)}")
        return None
    
    def test_get_requests(self):
        """测试获取绑定申请列表"""
        print("\n🔍 测试3: 获取绑定申请列表")
        try:
            response = self.session.get(f"{BASE_URL}/api/device/bind/requests?status=PENDING")
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 200:
                    items = data.get('data', {}).get('items', [])
                    self.log_test("获取申请列表", True, f"获取到 {len(items)} 条待审批申请", data.get('data'))
                    return items
                else:
                    self.log_test("获取申请列表", False, data.get('msg'))
            else:
                self.log_test("获取申请列表", False, f"HTTP状态码: {response.status_code}")
        except Exception as e:
            self.log_test("获取申请列表", False, f"请求异常: {str(e)}")
        return []
    
    def test_approve_request(self, request_id):
        """测试审批绑定申请"""
        print("\n🔍 测试4: 审批绑定申请")
        if not request_id:
            self.log_test("审批绑定申请", False, "无有效申请ID")
            return False
            
        try:
            approve_data = {
                "ids": [request_id],
                "action": "APPROVED",
                "approver_id": 1,
                "comment": "自动化测试审批通过"
            }
            
            response = self.session.post(
                f"{BASE_URL}/api/device/bind/approve",
                json=approve_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 200:
                    self.log_test("审批绑定申请", True, data.get('msg'), data)
                    return True
                else:
                    self.log_test("审批绑定申请", False, data.get('msg'))
            else:
                self.log_test("审批绑定申请", False, f"HTTP状态码: {response.status_code}")
        except Exception as e:
            self.log_test("审批绑定申请", False, f"请求异常: {str(e)}")
        return False
    
    def test_manual_bind(self):
        """测试手动绑定"""
        print("\n🔍 测试5: 管理员手动绑定")
        try:
            bind_data = {
                "device_sn": f"{TEST_DEVICE_SN}_MANUAL",
                "user_id": TEST_USER_ID,
                "org_id": TEST_ORG_ID,
                "operator_id": 1
            }
            
            response = self.session.post(
                f"{BASE_URL}/api/device/bind/manual",
                json=bind_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 200:
                    self.log_test("手动绑定设备", True, data.get('msg'), data)
                    return True
                else:
                    self.log_test("手动绑定设备", False, data.get('msg'))
            else:
                self.log_test("手动绑定设备", False, f"HTTP状态码: {response.status_code}")
        except Exception as e:
            self.log_test("手动绑定设备", False, f"请求异常: {str(e)}")
        return False
    
    def test_unbind_device(self):
        """测试解绑设备"""
        print("\n🔍 测试6: 解绑设备")
        try:
            unbind_data = {
                "device_sn": TEST_DEVICE_SN,
                "operator_id": 1,
                "reason": "自动化测试解绑"
            }
            
            response = self.session.post(
                f"{BASE_URL}/api/device/unbind",
                json=unbind_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 200:
                    self.log_test("解绑设备", True, data.get('msg'), data)
                    return True
                else:
                    self.log_test("解绑设备", False, data.get('msg'))
            else:
                self.log_test("解绑设备", False, f"HTTP状态码: {response.status_code}")
        except Exception as e:
            self.log_test("解绑设备", False, f"请求异常: {str(e)}")
        return False
    
    def test_bind_logs(self):
        """测试绑定日志查询"""
        print("\n🔍 测试7: 绑定日志查询")
        try:
            response = self.session.get(f"{BASE_URL}/api/device/bind/logs?device_sn={TEST_DEVICE_SN}")
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 200:
                    items = data.get('data', {}).get('items', [])
                    self.log_test("绑定日志查询", True, f"获取到 {len(items)} 条操作日志", data.get('data'))
                    return items
                else:
                    self.log_test("绑定日志查询", False, data.get('msg'))
            else:
                self.log_test("绑定日志查询", False, f"HTTP状态码: {response.status_code}")
        except Exception as e:
            self.log_test("绑定日志查询", False, f"请求异常: {str(e)}")
        return []
    
    def test_management_page(self):
        """测试管理页面访问"""
        print("\n🔍 测试8: 管理页面访问")
        try:
            response = self.session.get(f"{BASE_URL}/device_bind_management")
            if response.status_code == 200:
                if "设备绑定管理" in response.text:
                    self.log_test("管理页面访问", True, "页面加载成功")
                    return True
                else:
                    self.log_test("管理页面访问", False, "页面内容异常")
            else:
                self.log_test("管理页面访问", False, f"HTTP状态码: {response.status_code}")
        except Exception as e:
            self.log_test("管理页面访问", False, f"请求异常: {str(e)}")
        return False
    
    def run_full_test(self):
        """执行完整测试流程"""
        print("🚀 开始设备绑定系统完整功能测试")
        print("=" * 60)
        
        # 1. 测试二维码生成
        qr_url = self.test_qrcode_generation()
        
        # 2. 测试绑定申请
        request_id = self.test_bind_apply()
        
        # 3. 测试获取申请列表  
        requests_list = self.test_get_requests()
        
        # 4. 测试审批申请
        if request_id:
            self.test_approve_request(request_id)
        
        # 5. 测试手动绑定
        self.test_manual_bind()
        
        # 6. 测试解绑设备
        self.test_unbind_device()
        
        # 7. 测试操作日志
        self.test_bind_logs()
        
        # 8. 测试管理页面
        self.test_management_page()
        
        # 生成测试报告
        self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("📊 设备绑定系统测试报告")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if "✅" in result['status'])
        failed_tests = total_tests - passed_tests
        
        print(f"📈 测试总数: {total_tests}")
        print(f"✅ 通过数量: {passed_tests}")
        print(f"❌ 失败数量: {failed_tests}")
        print(f"📊 通过率: {(passed_tests/total_tests*100):.1f}%")
        
        print("\n📋 详细结果:")
        for result in self.test_results:
            print(f"  {result['time']} {result['status']} {result['test']}")
            if result['message']:
                print(f"    💬 {result['message']}")
        
        if failed_tests == 0:
            print("\n🎉 所有测试通过! 设备绑定系统功能正常")
        else:
            print(f"\n⚠️  有 {failed_tests} 个测试失败，请检查相关功能")
        
        # 保存测试报告
        report_file = f"device_bind_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        print(f"📄 详细报告已保存至: {report_file}")

def main():
    """主函数"""
    print("🔧 设备绑定系统功能测试工具")
    print(f"🌐 测试目标: {BASE_URL}")
    print(f"📱 测试设备: {TEST_DEVICE_SN}")
    print(f"👤 测试用户: {TEST_USER_ID}")
    print(f"🏢 测试组织: {TEST_ORG_ID}")
    
    # 检查服务是否运行
    try:
        response = requests.get(BASE_URL, timeout=5)
        print("✅ 服务连接正常")
    except:
        print("❌ 无法连接到服务，请确保应用正在运行")
        return
    
    # 执行测试
    tester = DeviceBindTester()
    tester.run_full_test()

if __name__ == "__main__":
    main() 
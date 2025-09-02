#!/usr/bin/env python3
"""通用接口测试管理器"""
import json,os,time,threading,subprocess
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class TestCase:
    """测试用例定义"""
    name: str
    description: str
    test_file: str
    event_types: List[str]
    expected_results: Dict[str, bool]
    timeout: int = 300

@dataclass  
class TestResult:
    """测试结果"""
    test_name: str
    status: str  # PASS/FAIL/SKIP
    execution_time: str
    details: Dict[str, Any]
    error_message: Optional[str] = None

class UniversalTestManager:
    """通用测试管理器"""
    
    def __init__(self, config_file: str = "test_config.json"):
        self.config_file = config_file
        self.test_cases = {}
        self.test_results = []
        self.test_history = []
        self.load_config()
    
    def load_config(self):
        """加载测试配置"""
        default_config = {
            "test_cases": {
                "upload_common_event": {
                    "name": "upload_common_event接口测试",
                    "description": "验证上传通用事件接口的完整流程",
                    "test_file": "final_upload_event_test.py",
                    "event_types": ["SOS_EVENT", "FALLDOWN_EVENT", "ONE_KEY_ALARM", "WEAR_STATUS_CHANGED"],
                    "expected_results": {
                        "api_response": True,
                        "health_data": True,
                        "alert_generation": True,
                        "message_delivery": True,
                        "wechat_notification": True
                    },
                    "timeout": 300
                },
                "health_data_sync": {
                    "name": "健康数据同步测试",
                    "description": "验证健康数据同步接口",
                    "test_file": "test_health_sync.py",
                    "event_types": ["HEALTH_SYNC"],
                    "expected_results": {
                        "api_response": True,
                        "data_storage": True,
                        "data_validation": True
                    },
                    "timeout": 180
                },
                "upload_health_data": {
                    "name": "健康数据上传接口测试",
                    "description": "验证健康数据上传接口的完整流程",
                    "test_file": "test_upload_health_data.py",
                    "event_types": ["HEALTH_DATA_UPLOAD"],
                    "expected_results": {
                        "api_response": True,
                        "data_storage": True,
                        "data_validation": True
                    },
                    "timeout": 180
                },
                "upload_device_info": {
                    "name": "设备信息上传接口测试",
                    "description": "验证设备信息上传和状态更新接口",
                    "test_file": "test_upload_device_info.py",
                    "event_types": ["DEVICE_INFO_UPLOAD"],
                    "expected_results": {
                        "api_response": True,
                        "device_registration": True,
                        "status_update": True,
                        "network_info": True
                    },
                    "timeout": 120
                }
            },
            "database": {
                "host": "127.0.0.1",
                "port": 3306,
                "user": "root",
                "password": "123456",
                "database": "lj-06"
            },
            "notifications": {
                "wechat_enabled": True,
                "email_enabled": False
            }
        }
        
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            self.config = default_config
            self.save_config()
        
        # 加载测试用例
        for test_id, test_config in self.config["test_cases"].items():
            self.test_cases[test_id] = TestCase(
                name=test_config["name"],
                description=test_config["description"],
                test_file=test_config["test_file"],
                event_types=test_config["event_types"],
                expected_results=test_config["expected_results"],
                timeout=test_config.get("timeout", 300)
            )
    
    def save_config(self):
        """保存配置"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def get_test_cases(self) -> Dict[str, TestCase]:
        """获取所有测试用例"""
        return self.test_cases
    
    def run_test(self, test_id: str) -> TestResult:
        """运行单个测试"""
        if test_id not in self.test_cases:
            return TestResult(
                test_name=test_id,
                status="FAIL",
                execution_time=datetime.now().strftime("%H:%M:%S"),
                details={},
                error_message=f"测试用例 {test_id} 不存在"
            )
        
        test_case = self.test_cases[test_id]
        start_time = time.time()
        
        try:
            print(f"🚀 开始执行测试: {test_case.name}")
            
            # 检查测试文件是否存在
            if not os.path.exists(test_case.test_file):
                raise FileNotFoundError(f"测试文件不存在: {test_case.test_file}")
            
            # 执行测试
            result = subprocess.run(
                ['python', test_case.test_file],
                capture_output=True,
                text=True,
                timeout=test_case.timeout
            )
            
            # 解析结果
            test_result = self._parse_test_result(test_case, result.stdout, result.stderr, result.returncode)
            
            execution_time = time.time() - start_time
            test_result.execution_time = f"{execution_time:.2f}s"
            
            print(f"✅ 测试完成: {test_case.name} - {test_result.status}")
            
            return test_result
            
        except subprocess.TimeoutExpired:
            return TestResult(
                test_name=test_case.name,
                status="FAIL",
                execution_time=f"{time.time() - start_time:.2f}s",
                details={},
                error_message="测试超时"
            )
        except Exception as e:
            return TestResult(
                test_name=test_case.name,
                status="FAIL",
                execution_time=f"{time.time() - start_time:.2f}s",
                details={},
                error_message=str(e)
            )
    
    def _parse_test_result(self, test_case: TestCase, stdout: str, stderr: str, return_code: int) -> TestResult:
        """解析测试结果"""
        details = {}
        
        # 检查各项预期结果
        for key, expected in test_case.expected_results.items():
            if key == "api_response":
                details[key] = "API调用成功" in stdout or "200" in stdout or "成功" in stdout
            elif key == "health_data":
                details[key] = "健康数据插入成功" in stdout or "健康数据存储成功" in stdout
            elif key == "alert_generation":
                details[key] = "告警生成成功" in stdout
            elif key == "message_delivery":
                details[key] = "消息发送成功" in stdout or "设备消息发送成功" in stdout
            elif key == "wechat_notification":
                details[key] = "微信通知发送成功" in stdout
            elif key == "data_storage":
                details[key] = "数据存储成功" in stdout or "健康数据存储成功" in stdout
            elif key == "data_validation":
                details[key] = "数据验证通过" in stdout
            elif key == "device_registration":
                details[key] = "设备注册" in stdout and "成功" in stdout
            elif key == "status_update":
                details[key] = "状态更新成功" in stdout or "设备状态更新成功" in stdout
            elif key == "network_info":
                details[key] = "网络信息更新成功" in stdout
            else:
                details[key] = True  # 默认通过
        
        # 计算通过的事件类型
        passed_events = []
        for event_type in test_case.event_types:
            if f"{event_type} 测试通过" in stdout or f"✅" in stdout:
                passed_events.append(event_type)
        
        details["passed_events"] = passed_events
        details["total_events"] = len(test_case.event_types)
        
        # 判断整体状态
        if return_code == 0 and len(passed_events) > 0:
            status = "PASS"
        else:
            status = "FAIL"
        
        return TestResult(
            test_name=test_case.name,
            status=status,
            execution_time="",
            details=details,
            error_message=stderr if stderr else None
        )
    
    def run_all_tests(self) -> List[TestResult]:
        """运行所有测试"""
        results = []
        for test_id in self.test_cases.keys():
            result = self.run_test(test_id)
            results.append(result)
            self.test_results.append(result)
        
        # 添加到历史记录
        self._add_to_history(results)
        
        return results
    
    def _add_to_history(self, results: List[TestResult]):
        """添加到历史记录"""
        total = len(results)
        passed = len([r for r in results if r.status == "PASS"])
        success_rate = (passed / total * 100) if total > 0 else 0
        
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "time": datetime.now().strftime("%H:%M"),
            "total_tests": total,
            "passed_tests": passed,
            "failed_tests": total - passed,
            "success_rate": round(success_rate, 1),
            "results": [
                {
                    "test_name": r.test_name,
                    "status": r.status,
                    "execution_time": r.execution_time
                }
                for r in results
            ]
        }
        
        self.test_history.append(history_entry)
        
        # 保持最近50条记录
        if len(self.test_history) > 50:
            self.test_history = self.test_history[-50:]
    
    def get_test_results(self) -> Dict[str, Any]:
        """获取测试结果"""
        return {
            "test_results": [
                {
                    "name": r.test_name,
                    "status": r.status,
                    "execution_time": r.execution_time,
                    "details": r.details,
                    "error_message": r.error_message
                }
                for r in self.test_results[-10:]  # 最近10次结果
            ],
            "last_update": datetime.now().isoformat()
        }
    
    def get_test_history(self) -> List[Dict[str, Any]]:
        """获取测试历史"""
        return self.test_history[-20:]  # 最近20次历史
    
    def generate_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        recent_results = self.test_results[-10:] if self.test_results else []
        
        total_tests = len(recent_results)
        passed_tests = len([r for r in recent_results if r.status == "PASS"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        return {
            "report_title": "ljwx接口自动化测试报告",
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": round(success_rate, 1)
            },
            "test_cases": {
                test_id: {
                    "name": test_case.name,
                    "description": test_case.description,
                    "event_types": test_case.event_types
                }
                for test_id, test_case in self.test_cases.items()
            },
            "recent_results": [
                {
                    "test_name": r.test_name,
                    "status": r.status,
                    "execution_time": r.execution_time,
                    "details": r.details
                }
                for r in recent_results
            ],
            "test_history": self.test_history
        }
    
    def add_test_case(self, test_id: str, test_config: Dict[str, Any]):
        """添加新的测试用例"""
        self.config["test_cases"][test_id] = test_config
        self.save_config()
        self.load_config()
    
    def remove_test_case(self, test_id: str):
        """移除测试用例"""
        if test_id in self.config["test_cases"]:
            del self.config["test_cases"][test_id]
            self.save_config()
            self.load_config()

# 全局测试管理器实例
test_manager = UniversalTestManager()

if __name__ == "__main__":
    # 示例用法
    print("🧪 ljwx通用接口测试管理器")
    print("=" * 50)
    
    # 显示所有测试用例
    print("📋 可用测试用例:")
    for test_id, test_case in test_manager.get_test_cases().items():
        print(f"  - {test_id}: {test_case.name}")
    
    print("\n🚀 运行upload_common_event测试...")
    result = test_manager.run_test("upload_common_event")
    print(f"结果: {result.status}")
    print(f"详情: {result.details}")
    
    # 生成报告
    print("\n📊 生成测试报告...")
    report = test_manager.generate_report()
    print(f"总测试数: {report['summary']['total_tests']}")
    print(f"成功率: {report['summary']['success_rate']}%") 
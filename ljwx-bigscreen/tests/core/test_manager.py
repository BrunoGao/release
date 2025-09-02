#!/usr/bin/env python3
"""统一测试管理器 - 管理所有测试用例的执行和结果"""
import json,importlib,threading,time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Type
from concurrent.futures import ThreadPoolExecutor, as_completed
from .base_test import BaseTest, TestResult

class TestManager:
    """统一测试管理器"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or Path(__file__).parent.parent / "config" / "test_config.json"
        self.test_registry: Dict[str, Type[BaseTest]] = {}
        self.test_results: List[TestResult] = []
        self.test_history: List[Dict[str, Any]] = []
        self._load_test_config()
        self._discover_tests()
    
    def _load_test_config(self):
        """加载测试配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except Exception:
            self.config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "api": {"base_url": "http://localhost:5001", "timeout": 30},
            "database": {"host": "localhost", "port": 3306, "user": "root", "password": "123456", "database": "ljwx"},
            "test_suites": {
                "upload_common_event": {"name": "通用事件上传测试", "module": "tests.suites.test_upload_common_event", "class": "UploadCommonEventTest"},
                "upload_health_data": {"name": "健康数据上传测试", "module": "tests.suites.test_upload_health_data", "class": "UploadHealthDataTest"},
                "upload_device_info": {"name": "设备信息上传测试", "module": "tests.suites.test_upload_device_info", "class": "UploadDeviceInfoTest"}
            }
        }
    
    def _discover_tests(self):
        """自动发现测试用例"""
        test_suites = self.config.get("test_suites", {})
        for test_id, test_config in test_suites.items():
            try:
                module = importlib.import_module(test_config["module"])
                test_class = getattr(module, test_config["class"])
                self.test_registry[test_id] = test_class
            except Exception as e:
                print(f"⚠️  无法加载测试: {test_id} - {e}")
    
    def register_test(self, test_id: str, test_class: Type[BaseTest]):
        """手动注册测试用例"""
        self.test_registry[test_id] = test_class
    
    def get_available_tests(self) -> Dict[str, str]:
        """获取可用测试列表"""
        return {test_id: self.config["test_suites"][test_id]["name"] 
                for test_id in self.test_registry.keys() 
                if test_id in self.config.get("test_suites", {})}
    
    def run_test(self, test_id: str) -> TestResult:
        """运行单个测试"""
        if test_id not in self.test_registry:
            return TestResult(
                test_name=test_id,
                status="ERROR",
                execution_time="0.00s",
                details={},
                error_message=f"测试 {test_id} 未找到"
            )
        
        test_class = self.test_registry[test_id]
        test_instance = test_class(self.config_path)
        result = test_instance.execute()
        
        # 保存结果
        self.test_results.append(result)
        self._save_test_history(result)
        
        return result
    
    def run_all_tests(self, parallel: bool = True) -> List[TestResult]:
        """运行所有测试"""
        results = []
        
        def run_single_test(test_id):
            """运行单个测试的内部函数"""
            if test_id not in self.test_registry:
                return TestResult(test_name=test_id, status="ERROR", execution_time="0.00s", details={}, error_message=f"测试 {test_id} 未找到")
            
            test_class = self.test_registry[test_id]
            test_instance = test_class(self.config_path)
            return test_instance.execute()
        
        if parallel:
            # 并行执行
            with ThreadPoolExecutor(max_workers=3) as executor:
                future_to_test = {executor.submit(run_single_test, test_id): test_id for test_id in self.test_registry.keys()}
                
                for future in as_completed(future_to_test):
                    test_id = future_to_test[future]
                    try:
                        result = future.result()
                        results.append(result)
                        self.test_results.append(result)  # 保存到实例变量
                        self._save_test_history(result)
                    except Exception as e:
                        error_result = TestResult(test_name=test_id, status="ERROR", execution_time="0.00s", details={}, error_message=str(e))
                        results.append(error_result)
                        self.test_results.append(error_result)
                        self._save_test_history(error_result)
        else:
            # 串行执行
            for test_id in self.test_registry.keys():
                result = run_single_test(test_id)
                results.append(result)
                self.test_results.append(result)
                self._save_test_history(result)
        
        return results
    
    def get_test_results(self) -> Dict[str, Any]:
        """获取测试结果"""
        return {
            "test_results": [
                {
                    "test_name": r.test_name,
                    "status": r.status,
                    "execution_time": r.execution_time,
                    "details": r.details,
                    "error_message": r.error_message,
                    "timestamp": r.timestamp
                }
                for r in self.test_results
            ],
            "summary": self._generate_summary(),
            "last_update": datetime.now().isoformat()
        }
    
    def _generate_summary(self) -> Dict[str, Any]:
        """生成测试摘要"""
        total = len(self.test_results)
        passed = len([r for r in self.test_results if r.status == "PASS"])
        failed = len([r for r in self.test_results if r.status in ["FAIL", "ERROR"]])
        success_rate = (passed / total * 100) if total > 0 else 0
        
        return {
            "total_tests": total,
            "passed_tests": passed,
            "failed_tests": failed,
            "success_rate": round(success_rate, 2)
        }
    
    def _save_test_history(self, result: TestResult):
        """保存测试历史"""
        history_entry = {
            "test_name": result.test_name,
            "status": result.status,
            "execution_time": result.execution_time,
            "timestamp": result.timestamp,
            "details": result.details
        }
        self.test_history.append(history_entry)
        
        # 保持历史记录不超过100条
        if len(self.test_history) > 100:
            self.test_history = self.test_history[-100:]
    
    def get_test_history(self) -> List[Dict[str, Any]]:
        """获取测试历史"""
        return self.test_history
    
    def generate_report(self) -> Dict[str, Any]:
        """生成完整测试报告"""
        summary = self._generate_summary()
        
        return {
            "report_title": "ljwx自动化测试报告",
            "generated_at": datetime.now().isoformat(),
            "summary": summary,
            "test_results": [
                {
                    "test_name": r.test_name,
                    "status": r.status,
                    "execution_time": r.execution_time,
                    "details": r.details,
                    "error_message": r.error_message,
                    "timestamp": r.timestamp
                }
                for r in self.test_results
            ],
            "available_tests": self.get_available_tests(),
            "recommendations": self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """生成改进建议"""
        recommendations = []
        summary = self._generate_summary()
        
        if summary["success_rate"] < 80:
            recommendations.append("测试成功率偏低，建议检查失败用例")
        
        if summary["failed_tests"] > 0:
            recommendations.append("存在失败测试，建议优先修复")
        
        if len(self.test_results) < 3:
            recommendations.append("测试覆盖率不足，建议增加更多测试用例")
        
        return recommendations
    
    def clear_results(self):
        """清空测试结果"""
        self.test_results.clear()
    
    def export_results(self, file_path: str):
        """导出测试结果"""
        report = self.generate_report()
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

# 全局测试管理器实例
test_manager = TestManager() 
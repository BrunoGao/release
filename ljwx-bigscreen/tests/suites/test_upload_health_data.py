#!/usr/bin/env python3
"""健康数据上传测试套件"""
import json,time
from typing import Dict, Any
from ..core.base_test import BaseTest, TestResult

class UploadHealthDataTest(BaseTest):
    """健康数据上传测试"""
    
    def run_test(self) -> TestResult:
        """执行测试"""
        details = {}
        
        # 测试数据
        test_data = {
            "data": {
                "id": self.config["test_data"]["device_sn"],
                "heart_rate": 94,
                "blood_oxygen": 98,
                "body_temperature": "37.1",
                "blood_pressure_systolic": 135,
                "blood_pressure_diastolic": 92,
                "step": 1107,
                "distance": "754.0",
                "calorie": "45615.0",
                "latitude": "34.14505564403376",
                "longitude": "117.14877354661755"
            }
        }
        
        try:
            # 1. API调用测试
            response = self.api_request("/upload_health_data", data=test_data)
            api_success = self.verify_api_response(response, 200)
            details["api_response"] = api_success
            
            if api_success:
                time.sleep(2)  # 等待数据处理
                
                # 2. 数据存储验证
                data_exists = self.verify_data_exists(
                    "t_user_health_data",
                    "device_sn = %s AND heart_rate = %s AND create_time >= DATE_SUB(NOW(), INTERVAL 1 MINUTE)",
                    (self.config["test_data"]["device_sn"], 94)
                )
                details["data_storage"] = data_exists
                
                # 3. 数据完整性检查
                if data_exists:
                    health_records = self.db_query(
                        "SELECT * FROM t_user_health_data WHERE device_sn = %s AND create_time >= DATE_SUB(NOW(), INTERVAL 1 MINUTE) ORDER BY create_time DESC LIMIT 1",
                        (self.config["test_data"]["device_sn"],)
                    )
                    
                    if health_records:
                        record = health_records[0]
                        data_valid = (
                            record.get("heart_rate") == 94 and
                            record.get("blood_oxygen") == 98 and
                            record.get("step") == 1107
                        )
                        details["data_validation"] = data_valid
                    else:
                        details["data_validation"] = False
                else:
                    details["data_validation"] = False
            else:
                details["data_storage"] = False
                details["data_validation"] = False
                
        except Exception as e:
            self.logger.error(f"健康数据测试失败: {e}")
            details["api_response"] = False
            details["data_storage"] = False
            details["data_validation"] = False
        
        # 统计结果
        details["passed_events"] = ["HEALTH_DATA_UPLOAD"] if details.get("api_response") else []
        details["total_events"] = 1
        
        # 判断测试状态
        all_checks = [
            details["api_response"],
            details["data_storage"],
            details["data_validation"]
        ]
        
        status = "PASS" if all(all_checks) else "FAIL"
        
        return TestResult(
            test_name="健康数据上传接口测试",
            status=status,
            execution_time=self.get_execution_time(),
            details=details
        ) 
#!/usr/bin/env python3
"""设备信息上传测试套件"""
import json,time
from typing import Dict, Any
from ..core.base_test import BaseTest, TestResult

class UploadDeviceInfoTest(BaseTest):
    """设备信息上传测试"""
    
    def run_test(self) -> TestResult:
        """执行测试"""
        details = {}
        
        # 测试数据
        test_data = {
            "SerialNumber": self.config["test_data"]["device_sn"],
            "Device Name": "HUAWEI WATCH 4-DD6",
            "IMEI": "861600078012130",
            "batteryLevel": 63,
            "voltage": 3995,
            "chargingStatus": "NONE",
            "status": "ACTIVE",
            "wearState": 0,
            "Wifi Address": "f0:fa:c7:ed:6c:17",
            "Bluetooth Address": "B0:FE:E5:8F:FD:D6"
        }
        
        try:
            # 1. API调用测试
            response = self.api_request("/upload_device_info", data=test_data)
            api_success = self.verify_api_response(response, 200)
            details["api_response"] = api_success
            
            if api_success:
                time.sleep(2)  # 等待数据处理
                
                # 2. 设备注册/更新验证
                device_exists = self.verify_data_exists(
                    "t_device_info",
                    "serial_number = %s",
                    (self.config["test_data"]["device_sn"],)
                )
                details["device_registration"] = device_exists
                
                # 3. 设备状态更新验证
                if device_exists:
                    device_records = self.db_query(
                        "SELECT * FROM t_device_info WHERE serial_number = %s ORDER BY update_time DESC LIMIT 1",
                        (self.config["test_data"]["device_sn"],)
                    )
                    
                    if device_records:
                        record = device_records[0]
                        status_updated = (
                            record.get("battery_level") == 63 and
                            record.get("status") == "ACTIVE" and
                            record.get("wearable_status") == "NOT_WORN"
                        )
                        details["status_update"] = status_updated
                    else:
                        details["status_update"] = False
                else:
                    details["status_update"] = False
                
                # 4. 网络信息验证
                if device_exists:
                    network_info_valid = self.db_query(
                        "SELECT * FROM t_device_info WHERE serial_number = %s AND wifi_address = %s",
                        (self.config["test_data"]["device_sn"], "f0:fa:c7:ed:6c:17")
                    )
                    details["network_info"] = len(network_info_valid) > 0
                else:
                    details["network_info"] = False
                    
            else:
                details["device_registration"] = False
                details["status_update"] = False
                details["network_info"] = False
                
        except Exception as e:
            self.logger.error(f"设备信息测试失败: {e}")
            details["api_response"] = False
            details["device_registration"] = False
            details["status_update"] = False
            details["network_info"] = False
        
        # 统计结果
        details["passed_events"] = ["DEVICE_INFO_UPLOAD"] if details.get("api_response") else []
        details["total_events"] = 1
        
        # 判断测试状态
        all_checks = [
            details["api_response"],
            details["device_registration"],
            details["status_update"],
            details["network_info"]
        ]
        
        status = "PASS" if all(all_checks) else "FAIL"
        
        return TestResult(
            test_name="设备信息上传接口测试",
            status=status,
            execution_time=self.get_execution_time(),
            details=details
        ) 
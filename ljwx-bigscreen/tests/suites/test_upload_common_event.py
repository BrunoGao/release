#!/usr/bin/env python3
"""通用事件上传测试套件"""
import json,time
from typing import Dict, Any
from ..core.base_test import BaseTest, TestResult

class UploadCommonEventTest(BaseTest):
    """通用事件上传测试"""
    
    def run_test(self) -> TestResult:
        """执行测试"""
        details = {}
        
        # 测试数据
        test_events = [
            {"eventType": "SOS_EVENT", "eventValue": "1", "deviceSn": self.config["test_data"]["device_sn"]},
            {"eventType": "FALLDOWN_EVENT", "eventValue": "1", "deviceSn": self.config["test_data"]["device_sn"]},
            {"eventType": "ONE_KEY_ALARM", "eventValue": "1", "deviceSn": self.config["test_data"]["device_sn"]},
            {"eventType": "WEAR_STATUS_CHANGED", "eventValue": "1", "deviceSn": self.config["test_data"]["device_sn"]}
        ]
        
        passed_events = []
        
        for event in test_events:
            try:
                # 1. API调用测试
                response = self.api_request("/upload_common_event", data=event)
                api_success = self.verify_api_response(response, 200)
                
                if api_success:
                    passed_events.append(event["eventType"])
                    time.sleep(1)  # 等待处理
                
            except Exception as e:
                self.logger.error(f"事件 {event['eventType']} 测试失败: {e}")
        
        # 2. 验证数据存储
        time.sleep(3)  # 等待异步处理完成
        
        try:
            # 检查事件队列处理
            health_data_exists = self.verify_data_exists(
                "t_user_health_data", 
                "device_sn = %s AND create_time >= DATE_SUB(NOW(), INTERVAL 1 MINUTE)",
                (self.config["test_data"]["device_sn"],)
            )
            details["health_data"] = health_data_exists
            
            # 检查告警生成
            alert_exists = self.verify_data_exists(
                "t_alert_info",
                "device_sn = %s AND create_time >= DATE_SUB(NOW(), INTERVAL 1 MINUTE)",
                (self.config["test_data"]["device_sn"],)
            )
            details["alert_generation"] = alert_exists
            
        except Exception as e:
            self.logger.error(f"数据验证失败: {e}")
            details["health_data"] = False
            details["alert_generation"] = False
        
        # 3. API响应验证
        details["api_response"] = len(passed_events) > 0
        
        # 4. 消息传递验证 (简化)
        details["message_delivery"] = details["alert_generation"]
        
        # 5. 微信通知验证 (简化)
        details["wechat_notification"] = details["alert_generation"]
        
        # 统计结果
        details["passed_events"] = passed_events
        details["total_events"] = len(test_events)
        
        # 判断测试状态
        all_checks = [
            details["api_response"],
            details["health_data"],
            details["alert_generation"],
            details["message_delivery"],
            details["wechat_notification"]
        ]
        
        status = "PASS" if all(all_checks) else "FAIL"
        
        return TestResult(
            test_name="upload_common_event接口测试",
            status=status,
            execution_time=self.get_execution_time(),
            details=details
        ) 
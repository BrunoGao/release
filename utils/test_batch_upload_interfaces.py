#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ljwx-boot 批量上传接口测试脚本

测试三个核心接口：
1. upload_health_data - 健康数据批量上传
2. upload_device_info - 设备信息批量上传  
3. upload_common_event - 通用事件上传

兼容原 Python ljwx-bigscreen 接口格式
"""

import requests
import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
import argparse


class BatchUploadTester:
    """批量上传接口测试器"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'ljwx-batch-upload-tester/1.0'
        })
        
    def generate_health_data(self, count: int = 10) -> List[Dict[str, Any]]:
        """生成测试健康数据"""
        health_data = []
        
        for i in range(count):
            # 模拟不同设备和用户
            device_id = f"DEVICE_{i % 5:03d}"
            user_id = str(100 + (i % 20))
            org_id = str(1 + (i % 3))
            
            data = {
                "device_id": device_id,
                "user_id": user_id,
                "org_id": org_id,
                "customer_id": "8",
                
                # 健康指标数据
                "heart_rate": random.randint(60, 100),
                "blood_oxygen": random.randint(95, 100),
                "temperature": round(36.0 + random.uniform(0, 2.0), 1),
                "pressure_high": random.randint(110, 140),
                "pressure_low": random.randint(70, 90),
                "stress": random.randint(1, 10),
                "step": random.randint(1000, 15000),
                "distance": round(random.uniform(0.5, 10.0), 2),
                "calorie": round(random.uniform(200, 800), 1),
                
                # 位置信息
                "latitude": round(39.9 + random.uniform(-0.1, 0.1), 6),
                "longitude": round(116.4 + random.uniform(-0.1, 0.1), 6),
                "altitude": round(random.uniform(40, 60), 1),
                
                # 时间戳
                "create_time": (datetime.now() - timedelta(minutes=random.randint(1, 60))).strftime("%Y-%m-%d %H:%M:%S")
            }
            health_data.append(data)
            
        return health_data
    
    def generate_device_data(self, count: int = 5) -> List[Dict[str, Any]]:
        """生成测试设备数据"""
        device_data = []
        
        for i in range(count):
            data = {
                "device_id": f"DEVICE_{i:03d}",
                "device_name": f"智能手环_{i}",
                "device_type": "wearable",
                "firmware_version": f"v2.{random.randint(1, 9)}.{random.randint(0, 9)}",
                "battery_level": random.randint(10, 100),
                "signal_strength": random.randint(-80, -30),
                "customer_id": "8",
                "status": random.choice(["online", "offline", "charging"]),
                "last_sync": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            device_data.append(data)
            
        return device_data
    
    def generate_common_event_data(self) -> Dict[str, Any]:
        """生成通用事件测试数据"""
        return {
            "health_data": self.generate_health_data(5),
            "device_info": self.generate_device_data(2),
            "alert_data": [
                {
                    "alert_type": "heart_rate_abnormal",
                    "device_id": "DEVICE_001",
                    "user_id": "101",
                    "severity": "high",
                    "message": "心率异常：检测到心率持续过高",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            ]
        }
    
    def test_upload_health_data(self, data_count: int = 10) -> Dict[str, Any]:
        """测试健康数据上传接口"""
        print(f"\n🩺 测试健康数据上传接口 (数据量: {data_count})")
        
        # 生成测试数据
        health_data = self.generate_health_data(data_count)
        
        # 测试新格式接口
        url = f"{self.base_url}/batch/upload-health-data"
        result1 = self._make_request("POST", url, health_data, "upload-health-data")
        
        # 测试Python兼容接口
        url_compat = f"{self.base_url}/batch/upload_health_data"
        result2 = self._make_request("POST", url_compat, health_data, "upload_health_data (兼容)")
        
        return {"modern": result1, "compatible": result2}
    
    def test_upload_device_info(self, device_count: int = 5) -> Dict[str, Any]:
        """测试设备信息上传接口"""
        print(f"\n📱 测试设备信息上传接口 (设备数: {device_count})")
        
        # 生成测试数据
        device_data = self.generate_device_data(device_count)
        
        # 测试新格式接口
        url = f"{self.base_url}/batch/upload-device-info"
        result1 = self._make_request("POST", url, device_data, "upload-device-info")
        
        # 测试Python兼容接口
        url_compat = f"{self.base_url}/batch/upload_device_info"
        result2 = self._make_request("POST", url_compat, device_data, "upload_device_info (兼容)")
        
        return {"modern": result1, "compatible": result2}
    
    def test_upload_common_event(self) -> Dict[str, Any]:
        """测试通用事件上传接口"""
        print(f"\n🔄 测试通用事件上传接口")
        
        # 生成测试数据
        event_data = self.generate_common_event_data()
        
        # 测试新格式接口
        url = f"{self.base_url}/batch/upload-common-event"
        result1 = self._make_request("POST", url, event_data, "upload-common-event")
        
        # 测试Python兼容接口
        url_compat = f"{self.base_url}/batch/upload_common_event"
        result2 = self._make_request("POST", url_compat, event_data, "upload_common_event (兼容)")
        
        return {"modern": result1, "compatible": result2}
    
    def test_get_stats(self) -> Dict[str, Any]:
        """测试统计信息接口"""
        print(f"\n📊 测试统计信息接口")
        
        url = f"{self.base_url}/batch/stats"
        return self._make_request("GET", url, None, "stats")
    
    def test_health_check(self) -> Dict[str, Any]:
        """测试健康检查接口"""
        print(f"\n💚 测试健康检查接口")
        
        url = f"{self.base_url}/batch/health"
        return self._make_request("GET", url, None, "health")
    
    def test_performance(self, data_size: int = 1000) -> Dict[str, Any]:
        """测试性能测试接口"""
        print(f"\n⚡ 测试性能测试接口 (数据规模: {data_size})")
        
        url = f"{self.base_url}/batch/performance-test?dataSize={data_size}"
        return self._make_request("POST", url, None, "performance-test")
    
    def _make_request(self, method: str, url: str, data: Any, operation: str) -> Dict[str, Any]:
        """发送HTTP请求"""
        start_time = time.time()
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, timeout=30)
            else:
                response = self.session.post(url, json=data, timeout=30)
            
            elapsed_time = (time.time() - start_time) * 1000
            
            result = {
                "operation": operation,
                "method": method,
                "url": url,
                "status_code": response.status_code,
                "elapsed_ms": round(elapsed_time, 2),
                "success": response.status_code == 200
            }
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    result["response"] = response_data
                    print(f"   ✅ {operation}: {response.status_code} ({elapsed_time:.1f}ms)")
                    
                    # 显示关键统计信息
                    if "result" in response_data and isinstance(response_data["result"], dict):
                        stats = response_data["result"]
                        if "processed" in stats:
                            print(f"      📈 处理: {stats.get('processed', 0)} 条")
                        if "duplicates" in stats:
                            print(f"      🔄 重复: {stats.get('duplicates', 0)} 条")
                        if "processing_time_ms" in stats:
                            print(f"      ⏱️  耗时: {stats.get('processing_time_ms', 0)} ms")
                            
                except json.JSONDecodeError:
                    result["response"] = response.text
                    print(f"   ⚠️  {operation}: {response.status_code} (响应格式异常)")
                    
            else:
                result["error"] = response.text
                print(f"   ❌ {operation}: {response.status_code} - {response.text[:100]}")
                
        except Exception as e:
            elapsed_time = (time.time() - start_time) * 1000
            result = {
                "operation": operation,
                "method": method,
                "url": url,
                "error": str(e),
                "elapsed_ms": round(elapsed_time, 2),
                "success": False
            }
            print(f"   💥 {operation}: 请求异常 - {str(e)}")
            
        return result
    
    def run_all_tests(self, health_count: int = 10, device_count: int = 5, perf_size: int = 1000):
        """运行所有测试"""
        print("🚀 开始 ljwx-boot 批量上传接口测试")
        print(f"   目标服务: {self.base_url}")
        print(f"   测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        results = {}
        
        # 1. 健康检查
        results["health_check"] = self.test_health_check()
        
        # 2. 健康数据上传测试
        results["health_data"] = self.test_upload_health_data(health_count)
        
        # 3. 设备信息上传测试
        results["device_info"] = self.test_upload_device_info(device_count)
        
        # 4. 通用事件上传测试
        results["common_event"] = self.test_upload_common_event()
        
        # 5. 统计信息查询
        results["stats"] = self.test_get_stats()
        
        # 6. 性能测试
        results["performance"] = self.test_performance(perf_size)
        
        print(f"\n📋 测试完成总结:")
        self._print_test_summary(results)
        
        return results
    
    def _print_test_summary(self, results: Dict[str, Any]):
        """打印测试总结"""
        total_tests = 0
        passed_tests = 0
        
        for test_name, test_result in results.items():
            if isinstance(test_result, dict):
                if "success" in test_result:
                    # 单个测试结果
                    total_tests += 1
                    if test_result["success"]:
                        passed_tests += 1
                        print(f"   ✅ {test_name}: 通过 ({test_result.get('elapsed_ms', 0):.1f}ms)")
                    else:
                        print(f"   ❌ {test_name}: 失败")
                else:
                    # 多个测试结果 (如health_data的modern和compatible)
                    for sub_test, sub_result in test_result.items():
                        if isinstance(sub_result, dict) and "success" in sub_result:
                            total_tests += 1
                            if sub_result["success"]:
                                passed_tests += 1
                                print(f"   ✅ {test_name}.{sub_test}: 通过 ({sub_result.get('elapsed_ms', 0):.1f}ms)")
                            else:
                                print(f"   ❌ {test_name}.{sub_test}: 失败")
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"\n🎯 测试通过率: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        if success_rate == 100:
            print("🎉 所有测试通过！接口运行正常")
        elif success_rate >= 80:
            print("⚠️  大部分测试通过，部分功能可能存在问题")
        else:
            print("🚨 多个测试失败，建议检查服务状态")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="ljwx-boot 批量上传接口测试")
    parser.add_argument("--url", default="http://localhost:8080", help="服务基础URL")
    parser.add_argument("--health-count", type=int, default=10, help="健康数据测试条数")
    parser.add_argument("--device-count", type=int, default=5, help="设备信息测试条数")
    parser.add_argument("--perf-size", type=int, default=1000, help="性能测试数据规模")
    
    # 添加单独测试选项
    parser.add_argument("--test-health", action="store_true", help="仅测试健康数据接口")
    parser.add_argument("--test-device", action="store_true", help="仅测试设备信息接口")
    parser.add_argument("--test-event", action="store_true", help="仅测试通用事件接口")
    parser.add_argument("--test-stats", action="store_true", help="仅测试统计信息接口")
    parser.add_argument("--test-check", action="store_true", help="仅测试健康检查接口")
    parser.add_argument("--test-perf", action="store_true", help="仅测试性能接口")
    
    args = parser.parse_args()
    
    # 初始化测试器
    tester = BatchUploadTester(args.url)
    
    # 运行指定的测试
    if args.test_health:
        tester.test_upload_health_data(args.health_count)
    elif args.test_device:
        tester.test_upload_device_info(args.device_count)
    elif args.test_event:
        tester.test_upload_common_event()
    elif args.test_stats:
        tester.test_get_stats()
    elif args.test_check:
        tester.test_health_check()
    elif args.test_perf:
        tester.test_performance(args.perf_size)
    else:
        # 运行所有测试
        tester.run_all_tests(args.health_count, args.device_count, args.perf_size)


if __name__ == "__main__":
    main()
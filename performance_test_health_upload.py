#!/usr/bin/env python3
"""
Health Data Upload Performance Testing Tool
测试健康数据上传接口性能
"""

import json
import time
import random
import threading
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any
import statistics
import urllib.request
import urllib.parse
import concurrent.futures


class HealthDataPerformanceTester:
    def __init__(self, base_url: str = "http://192.168.1.83:5001"):
        self.base_url = base_url
        self.upload_endpoint = f"{base_url}/upload_health_data"
        self.device_sns = [f"CRFTQ2340900189{i}" for i in range(5)]  # 1890-1894 (excluding 1895 due to 404 errors)
        self.user_id = 1940034533382479873
        self.org_id = 1939964806110937090
        
    def generate_health_data(self, device_sn: str) -> Dict[str, Any]:
        """生成模拟健康数据"""
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        week_start = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
        
        # 生成随机但合理的健康数据
        heart_rate = random.randint(60, 120)
        blood_oxygen = random.randint(95, 100)
        temperature = round(random.uniform(36.0, 37.5), 1)
        pressure_high = random.randint(110, 140)
        pressure_low = random.randint(70, 90)
        stress = random.randint(0, 100)
        step = random.randint(0, 15000)
        distance = round(random.uniform(0.0, 12.0), 1)
        calorie = round(random.uniform(0.0, 800.0), 1)
        
        # GPS坐标（深圳区域）
        latitude = round(random.uniform(22.5, 22.6), 6)
        longitude = round(random.uniform(114.0, 114.1), 6)
        altitude = round(random.uniform(0.0, 50.0), 1)
        
        return {
            "data": {
                "deviceSn": device_sn,
                "heart_rate": heart_rate,
                "blood_oxygen": blood_oxygen,
                "body_temperature": str(temperature),
                "step": step,
                "distance": str(distance),
                "calorie": str(calorie),
                "latitude": str(latitude),
                "longitude": str(longitude),
                "altitude": str(altitude),
                "stress": stress,
                "upload_method": "wifi",
                "blood_pressure_systolic": pressure_high,
                "blood_pressure_diastolic": pressure_low,
                "sleepData": "null",
                "exerciseDailyData": "null",
                "exerciseWeekData": "null",
                "scientificSleepData": "null",
                "workoutData": "null",
                "timestamp": timestamp
            }
        }

    def upload_single_data(self, device_sn: str) -> Dict[str, Any]:
        """上传单条健康数据"""
        data = self.generate_health_data(device_sn)
        start_time = time.time()
        
        try:
            # 准备POST请求
            json_data = json.dumps(data).encode('utf-8')
            
            req = urllib.request.Request(
                self.upload_endpoint,
                data=json_data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # ms
                
                response_text = response.read().decode('utf-8')
                
                return {
                    "device_sn": device_sn,
                    "status_code": response.status,
                    "response_time_ms": response_time,
                    "success": response.status == 200,
                    "response_body": response_text[:200] if response_text else "",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            return {
                "device_sn": device_sn,
                "status_code": 0,
                "response_time_ms": response_time,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def run_concurrent_test(self, concurrent_requests: int, total_requests: int) -> List[Dict[str, Any]]:
        """运行并发测试"""
        results = []
        
        # 使用线程池进行并发测试
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            # 分批执行并发请求
            for batch_start in range(0, total_requests, concurrent_requests):
                batch_size = min(concurrent_requests, total_requests - batch_start)
                
                # 创建并发任务
                futures = []
                for i in range(batch_size):
                    device_sn = random.choice(self.device_sns)
                    future = executor.submit(self.upload_single_data, device_sn)
                    futures.append(future)
                
                # 等待所有任务完成
                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        results.append({
                            "device_sn": "unknown",
                            "status_code": 0,
                            "response_time_ms": 0,
                            "success": False,
                            "error": str(e),
                            "timestamp": datetime.now().isoformat()
                        })
                
                # 批次间稍作间隔
                if batch_start + concurrent_requests < total_requests:
                    time.sleep(0.1)
        
        return results

    def analyze_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析测试结果"""
        if not results:
            return {"error": "No results to analyze"}
        
        successful_requests = [r for r in results if r.get("success", False)]
        failed_requests = [r for r in results if not r.get("success", False)]
        
        response_times = [r["response_time_ms"] for r in successful_requests if "response_time_ms" in r]
        
        analysis = {
            "总体统计": {
                "总请求数": len(results),
                "成功请求数": len(successful_requests),
                "失败请求数": len(failed_requests),
                "成功率": f"{len(successful_requests)/len(results)*100:.2f}%" if results else "0%"
            },
            "响应时间统计": {},
            "错误分析": {},
            "设备统计": {}
        }
        
        if response_times:
            analysis["响应时间统计"] = {
                "平均响应时间_ms": f"{statistics.mean(response_times):.2f}",
                "最小响应时间_ms": f"{min(response_times):.2f}",
                "最大响应时间_ms": f"{max(response_times):.2f}",
                "中位数响应时间_ms": f"{statistics.median(response_times):.2f}",
                "95百分位响应时间_ms": f"{sorted(response_times)[int(len(response_times)*0.95)]:.2f}" if len(response_times) > 20 else "N/A"
            }
        
        # 错误统计
        if failed_requests:
            error_types = {}
            for req in failed_requests:
                error_key = req.get("error", f"HTTP_{req.get('status_code', 'unknown')}")
                error_types[error_key] = error_types.get(error_key, 0) + 1
            analysis["错误分析"] = error_types
        
        # 设备统计
        device_stats = {}
        for result in results:
            device_sn = result.get("device_sn", "unknown")
            if device_sn not in device_stats:
                device_stats[device_sn] = {"total": 0, "success": 0, "failed": 0}
            device_stats[device_sn]["total"] += 1
            if result.get("success", False):
                device_stats[device_sn]["success"] += 1
            else:
                device_stats[device_sn]["failed"] += 1
        analysis["设备统计"] = device_stats
        
        return analysis

    def run_performance_test(self, concurrent: int = 5, total: int = 50, duration: int = None):
        """运行性能测试"""
        print(f"🚀 开始性能测试")
        print(f"📡 目标端点: {self.upload_endpoint}")
        print(f"🔢 设备范围: {self.device_sns[0]} - {self.device_sns[-1]}")
        print(f"⚡ 并发数: {concurrent}")
        print(f"📊 总请求数: {total}")
        print("=" * 60)
        
        start_time = time.time()
        
        if duration:
            # 基于时间的测试
            print(f"⏱️  测试时长: {duration}秒")
            results = []
            end_time = start_time + duration
            
            while time.time() < end_time:
                batch_results = self.run_concurrent_test(concurrent, concurrent)
                results.extend(batch_results)
                print(f"✅ 已完成 {len(results)} 个请求...")
                time.sleep(1)  # 1秒间隔
        else:
            # 基于请求数的测试
            results = self.run_concurrent_test(concurrent, total)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 分析结果
        analysis = self.analyze_results(results)
        
        # 输出结果
        print("\n" + "=" * 60)
        print("📈 性能测试结果报告")
        print("=" * 60)
        
        print(f"⏱️  总测试时间: {total_time:.2f}秒")
        print(f"🚀 请求吞吐量: {len(results)/total_time:.2f} requests/sec")
        
        for category, data in analysis.items():
            print(f"\n📊 {category}:")
            if isinstance(data, dict):
                for key, value in data.items():
                    print(f"  {key}: {value}")
            else:
                print(f"  {data}")
        
        # 保存详细结果到文件
        report_file = f"health_upload_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "test_config": {
                    "endpoint": self.upload_endpoint,
                    "concurrent_requests": concurrent,
                    "total_requests": len(results),
                    "test_duration_seconds": total_time,
                    "devices_tested": self.device_sns
                },
                "results": results,
                "analysis": analysis
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 详细报告已保存到: {report_file}")
        return analysis

    def test_single_upload(self):
        """测试单次上传"""
        print("🧪 测试单次数据上传...")
        
        device_sn = self.device_sns[0]
        result = self.upload_single_data(device_sn)
        
        print(f"设备: {result['device_sn']}")
        print(f"状态码: {result['status_code']}")
        print(f"响应时间: {result['response_time_ms']:.2f}ms")
        print(f"成功: {result['success']}")
        
        if not result['success']:
            print(f"错误: {result.get('error', '未知错误')}")
        else:
            print(f"响应: {result.get('response_body', '')[:100]}...")
        
        return result


def main():
    parser = argparse.ArgumentParser(description='Health Data Upload Performance Tester')
    parser.add_argument('--url', default='http://192.168.1.83:5001', help='Base URL for the service')
    parser.add_argument('--concurrent', '-c', type=int, default=5, help='Concurrent requests')
    parser.add_argument('--total', '-t', type=int, default=50, help='Total requests')
    parser.add_argument('--duration', '-d', type=int, help='Test duration in seconds (overrides total)')
    parser.add_argument('--test-single', action='store_true', help='Test single upload only')
    
    args = parser.parse_args()
    
    tester = HealthDataPerformanceTester(args.url)
    
    if args.test_single:
        tester.test_single_upload()
    else:
        tester.run_performance_test(
            concurrent=args.concurrent,
            total=args.total,
            duration=args.duration
        )


if __name__ == "__main__":
    main()
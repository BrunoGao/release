#!/usr/bin/env python3
import requests
import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
from db_config import load_db_config

class APITester:
    def __init__(self, base_url: str = "http://192.168.1.83:5001"):
        self.base_url = base_url
        self.db_config = load_db_config()
        self.results = []
        
    def generate_health_data(self, device_sn: str) -> Dict[str, Any]:
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        
        return {
            "data": {
                "deviceSn": device_sn,
                "heart_rate": random.randint(60, 120),
                "blood_oxygen": random.randint(95, 100) if random.random() > 0.3 else 0,
                "body_temperature": f"{random.uniform(36.0, 37.5):.1f}",
                "step": random.randint(0, 15000),
                "distance": f"{random.uniform(0, 10):.1f}",
                "calorie": f"{random.uniform(0, 500):.1f}",
                "latitude": f"{random.uniform(22.5, 22.6):.6f}",
                "longitude": f"{random.uniform(114.0, 114.1):.6f}",
                "altitude": f"{random.uniform(0, 100):.1f}",
                "stress": random.randint(0, 100),
                "upload_method": random.choice(["wifi", "4g", "bluetooth"]),
                "blood_pressure_systolic": random.randint(110, 140),
                "blood_pressure_diastolic": random.randint(70, 90),
                "sleepData": "null",
                "exerciseDailyData": "null",
                "exerciseWeekData": "null",
                "scientificSleepData": "null",
                "workoutData": "null",
                "timestamp": timestamp
            }
        }
    
    def generate_device_info(self, device_sn: str) -> Dict[str, Any]:
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        
        return {
            "System Software Version": f"GLL-AL30BCN {random.randint(3,5)}.0.0.{random.randint(800,999)}",
            "Wifi Address": ":".join([f"{random.randint(0,255):02x}" for _ in range(6)]),
            "Bluetooth Address": ":".join([f"{random.randint(0,255):02X}" for _ in range(6)]),
            "IP Address": f"192.168.1.{random.randint(100, 254)}",
            "Network Access Mode": random.choice([1, 2, 3]),
            "SerialNumber": device_sn,
            "Device Name": f"HUAWEI WATCH B7-{random.randint(500,600)}-BF{random.randint(0,9)}",
            "IMEI": f"86615206{random.randint(10000000, 99999999)}",
            "batteryLevel": random.randint(10, 100),
            "voltage": random.randint(3500, 4500),
            "chargingStatus": random.choice(["NONE", "CHARGING", "FULL"]),
            "status": random.choice(["ACTIVE", "INACTIVE", "SLEEP"]),
            "timestamp": timestamp,
            "wearState": random.choice([0, 1])
        }
    
    def generate_common_event(self, device_sn: str) -> Dict[str, Any]:
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        health_data = self.generate_health_data(device_sn)
        
        event_types = [
            'com.tdtech.ohos.action.WEAR_STATUS_CHANGED'
        ]
        
        return {
            'eventType': random.choice(event_types),
            'eventValue': str(random.choice([0, 1])),
            'deviceSn': device_sn,
            'latitude': round(random.uniform(22.5, 22.6), 6),
            'longitude': round(random.uniform(114.0, 114.1), 6),
            'altitude': random.randint(0, 100),
            'timestamp': timestamp,
            'healthData': health_data
        }
    
    def make_request(self, endpoint: str, data: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint}"
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'API-Tester/1.0'
        }
        
        start_time = time.time()
        try:
            response = requests.post(url, json=data, headers=headers, timeout=timeout)
            end_time = time.time()
            
            result = {
                'endpoint': endpoint,
                'status_code': response.status_code,
                'response_time': round((end_time - start_time) * 1000, 2),
                'success': response.status_code == 200,
                'timestamp': datetime.now().isoformat(),
                'request_size': len(json.dumps(data).encode('utf-8')),
                'response_size': len(response.content)
            }
            
            try:
                result['response_data'] = response.json()
            except:
                result['response_data'] = response.text
            
            if response.status_code != 200:
                result['error'] = f"HTTP {response.status_code}: {response.text[:200]}"
                
            return result
            
        except requests.exceptions.Timeout:
            return {
                'endpoint': endpoint,
                'status_code': 0,
                'response_time': timeout * 1000,
                'success': False,
                'error': 'Request timeout',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'endpoint': endpoint,
                'status_code': 0,
                'response_time': 0,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def test_single_api(self, endpoint: str, device_sn: str) -> Dict[str, Any]:
        if endpoint == 'upload_health_data':
            data = self.generate_health_data(device_sn)
        elif endpoint == 'upload_device_info':
            data = self.generate_device_info(device_sn)
        elif endpoint == 'upload_common_event':
            data = self.generate_common_event(device_sn)
        else:
            raise ValueError(f"Unknown endpoint: {endpoint}")
        
        return self.make_request(endpoint, data)
    
    def performance_test(self, endpoint: str, device_sns: List[str], 
                        concurrent_users: int = 5, requests_per_user: int = 10) -> List[Dict[str, Any]]:
        results = []
        
        def worker(device_sn: str, request_count: int) -> List[Dict[str, Any]]:
            worker_results = []
            for i in range(request_count):
                result = self.test_single_api(endpoint, device_sn)
                result['user_id'] = threading.current_thread().ident
                result['request_number'] = i + 1
                worker_results.append(result)
                time.sleep(random.uniform(0.1, 0.5))
            return worker_results
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            for i in range(concurrent_users):
                device_sn = random.choice(device_sns)
                future = executor.submit(worker, device_sn, requests_per_user)
                futures.append(future)
            
            for future in as_completed(futures):
                results.extend(future.result())
        
        return results
    
    def functional_test(self, device_sns: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        endpoints = ['upload_health_data', 'upload_device_info', 'upload_common_event']
        results = {}
        
        for endpoint in endpoints:
            print(f"Testing {endpoint}...")
            endpoint_results = []
            
            for device_sn in device_sns[:5]:
                result = self.test_single_api(endpoint, device_sn)
                endpoint_results.append(result)
                time.sleep(0.1)
            
            results[endpoint] = endpoint_results
        
        return results
    
    def generate_report(self, results: Dict[str, Any], output_file: str = None):
        report = {
            'test_summary': {
                'timestamp': datetime.now().isoformat(),
                'base_url': self.base_url,
                'total_endpoints_tested': 0,
                'total_requests': 0,
                'success_rate': 0,
                'average_response_time': 0
            },
            'endpoint_details': {},
            'performance_metrics': {},
            'errors': []
        }
        
        all_results = []
        for endpoint, endpoint_results in results.items():
            if isinstance(endpoint_results, list):
                all_results.extend(endpoint_results)
                
                successful_requests = [r for r in endpoint_results if r.get('success', False)]
                response_times = [r['response_time'] for r in endpoint_results if 'response_time' in r]
                
                endpoint_stats = {
                    'total_requests': len(endpoint_results),
                    'successful_requests': len(successful_requests),
                    'success_rate': (len(successful_requests) / len(endpoint_results)) * 100 if endpoint_results else 0,
                    'average_response_time': statistics.mean(response_times) if response_times else 0,
                    'min_response_time': min(response_times) if response_times else 0,
                    'max_response_time': max(response_times) if response_times else 0,
                    'median_response_time': statistics.median(response_times) if response_times else 0,
                    'errors': [r for r in endpoint_results if not r.get('success', False)]
                }
                
                report['endpoint_details'][endpoint] = endpoint_stats
        
        if all_results:
            successful_results = [r for r in all_results if r.get('success', False)]
            all_response_times = [r['response_time'] for r in all_results if 'response_time' in r]
            
            report['test_summary'].update({
                'total_endpoints_tested': len(results),
                'total_requests': len(all_results),
                'success_rate': (len(successful_results) / len(all_results)) * 100,
                'average_response_time': statistics.mean(all_response_times) if all_response_times else 0
            })
        
        report_text = self.format_report(report)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"Report saved to: {output_file}")
        
        print(report_text)
        return report
    
    def format_report(self, report: Dict[str, Any]) -> str:
        lines = []
        lines.append("=" * 80)
        lines.append("API 测试报告")
        lines.append("=" * 80)
        lines.append(f"测试时间: {report['test_summary']['timestamp']}")
        lines.append(f"测试地址: {report['test_summary']['base_url']}")
        lines.append(f"测试接口数: {report['test_summary']['total_endpoints_tested']}")
        lines.append(f"总请求数: {report['test_summary']['total_requests']}")
        lines.append(f"成功率: {report['test_summary']['success_rate']:.2f}%")
        lines.append(f"平均响应时间: {report['test_summary']['average_response_time']:.2f}ms")
        lines.append("")
        
        lines.append("接口详情:")
        lines.append("-" * 50)
        for endpoint, stats in report['endpoint_details'].items():
            lines.append(f"\n{endpoint}:")
            lines.append(f"  总请求数: {stats['total_requests']}")
            lines.append(f"  成功请求数: {stats['successful_requests']}")
            lines.append(f"  成功率: {stats['success_rate']:.2f}%")
            lines.append(f"  平均响应时间: {stats['average_response_time']:.2f}ms")
            lines.append(f"  最小响应时间: {stats['min_response_time']:.2f}ms")
            lines.append(f"  最大响应时间: {stats['max_response_time']:.2f}ms")
            lines.append(f"  中位数响应时间: {stats['median_response_time']:.2f}ms")
            
            if stats['errors']:
                lines.append(f"  错误数: {len(stats['errors'])}")
                for i, error in enumerate(stats['errors'][:3]):
                    lines.append(f"    错误 {i+1}: {error.get('error', 'Unknown error')}")
        
        return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description='API Testing Tool')
    parser.add_argument('--url', default='http://192.168.1.83:5001', help='Base URL for API')
    parser.add_argument('--mode', choices=['functional', 'performance', 'both'], 
                       default='both', help='Test mode')
    parser.add_argument('--concurrent', type=int, default=5, help='Concurrent users for performance test')
    parser.add_argument('--requests', type=int, default=10, help='Requests per user for performance test')
    parser.add_argument('--output', help='Output file for report')
    
    args = parser.parse_args()
    
    tester = APITester(args.url)
    
    if not tester.db_config.connect():
        print("数据库连接失败，请检查配置")
        return
    
    devices = tester.db_config.get_devices(50)
    if not devices:
        print("未找到设备数据，请检查数据库")
        return
    
    device_sns = [device['device_sn'] for device in devices]
    print(f"从数据库获取到 {len(device_sns)} 个设备序列号")
    
    results = {}
    
    if args.mode in ['functional', 'both']:
        print("\n开始功能测试...")
        functional_results = tester.functional_test(device_sns)
        results.update(functional_results)
    
    if args.mode in ['performance', 'both']:
        print(f"\n开始性能测试 (并发用户: {args.concurrent}, 每用户请求: {args.requests})...")
        endpoints = ['upload_health_data', 'upload_device_info', 'upload_common_event']
        
        for endpoint in endpoints:
            print(f"Testing {endpoint} performance...")
            perf_results = tester.performance_test(endpoint, device_sns, 
                                                 args.concurrent, args.requests)
            results[f"{endpoint}_performance"] = perf_results
    
    if args.output:
        output_file = args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"api_test_report_{timestamp}.txt"
    
    tester.generate_report(results, output_file)
    tester.db_config.disconnect()

if __name__ == "__main__":
    main()
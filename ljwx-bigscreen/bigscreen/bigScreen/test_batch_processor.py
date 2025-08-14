#!/usr/bin/env python3
"""
批量处理器性能测试脚本 v1.0.34
测试400-1000台设备同时上传的场景
"""
import asyncio
import aiohttp
import time
import json
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import threading

class DeviceBatchTester:
    def __init__(self, base_url="http://localhost:8001", max_devices=1000):
        self.base_url = base_url
        self.max_devices = max_devices
        self.results = {"success": 0, "failed": 0, "total_time": 0}
        self.lock = threading.Lock()
        
    def generate_device_data(self, device_id):
        """生成模拟设备数据"""
        return {
            "data": {
                "SerialNumber": f"TEST{device_id:04d}",
                "System Software Version": "HW-X1000-V1.2.3",
                "Wifi Address": f"AA:BB:CC:DD:EE:{device_id:02X}",
                "Bluetooth Address": f"11:22:33:44:55:{device_id:02X}",
                "IP Address": f"192.168.1.{device_id % 254 + 1}",
                "Network Access Mode": "WiFi",
                "Device Name": f"TestWatch_{device_id}",
                "IMEI": f"86012345678901{device_id:03d}",
                "batteryLevel": random.randint(20, 100),
                "chargingStatus": random.choice(["CHARGING", "NOT_CHARGING"]),
                "wearState": random.choice([0, 1]),
                "voltage": random.randint(3000, 4200),
                "status": "ONLINE",
                "timestamp": int(time.time() * 1000),
                "customerId": "1"
            }
        }
    
    async def send_device_data(self, session, device_id):
        """发送单个设备数据"""
        device_data = self.generate_device_data(device_id)
        
        try:
            start_time = time.time()
            async with session.post(
                f"{self.base_url}/api/device/upload",
                json=device_data,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    result = await response.json()
                    with self.lock:
                        self.results["success"] += 1
                        self.results["total_time"] += duration
                    return True, duration, result
                else:
                    with self.lock:
                        self.results["failed"] += 1
                    return False, duration, f"HTTP {response.status}"
                    
        except Exception as e:
            with self.lock:
                self.results["failed"] += 1
            return False, 0, str(e)
    
    async def test_concurrent_upload(self, num_devices=400, concurrent_requests=100):
        """测试并发上传"""
        print(f"🚀 开始测试 {num_devices} 台设备并发上传")
        print(f"📊 并发请求数: {concurrent_requests}")
        
        connector = aiohttp.TCPConnector(limit=concurrent_requests * 2)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # 创建并发任务
            tasks = []
            for i in range(num_devices):
                task = asyncio.create_task(self.send_device_data(session, i + 1))
                tasks.append(task)
                
                # 分批发送，避免过载
                if len(tasks) >= concurrent_requests:
                    await asyncio.gather(*tasks, return_exceptions=True)
                    tasks = []
                    await asyncio.sleep(0.1)  # 短暂等待
            
            # 发送剩余任务
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    def test_sync_upload(self, num_devices=100, num_threads=10):
        """测试同步上传(多线程)"""
        print(f"🔄 开始测试 {num_devices} 台设备同步上传")
        print(f"🧵 线程数: {num_threads}")
        
        def send_sync_request(device_id):
            import requests
            device_data = self.generate_device_data(device_id)
            
            try:
                start_time = time.time()
                response = requests.post(
                    f"{self.base_url}/api/device/upload",
                    json=device_data,
                    timeout=10
                )
                duration = time.time() - start_time
                
                if response.status_code == 200:
                    with self.lock:
                        self.results["success"] += 1
                        self.results["total_time"] += duration
                    return True, duration
                else:
                    with self.lock:
                        self.results["failed"] += 1
                    return False, duration
                    
            except Exception as e:
                with self.lock:
                    self.results["failed"] += 1
                return False, 0
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(send_sync_request, i + 1) for i in range(num_devices)]
            for future in futures:
                future.result()
    
    async def get_processor_stats(self):
        """获取批量处理器统计信息"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/batch/stats") as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except Exception as e:
            print(f"获取统计信息失败: {e}")
            return None
    
    def print_results(self, test_name, start_time):
        """打印测试结果"""
        total_time = time.time() - start_time
        total_requests = self.results["success"] + self.results["failed"]
        
        print(f"\n{'='*60}")
        print(f"📊 {test_name} 测试结果")
        print(f"{'='*60}")
        print(f"总请求数: {total_requests}")
        print(f"成功请求: {self.results['success']}")
        print(f"失败请求: {self.results['failed']}")
        print(f"成功率: {(self.results['success']/total_requests*100):.2f}%")
        print(f"总耗时: {total_time:.2f}秒")
        print(f"平均TPS: {total_requests/total_time:.2f} 请求/秒")
        
        if self.results['success'] > 0:
            avg_response_time = self.results['total_time'] / self.results['success']
            print(f"平均响应时间: {avg_response_time*1000:.2f}ms")
        
        print(f"{'='*60}")

async def main():
    """主测试函数"""
    tester = DeviceBatchTester()
    
    # 测试场景1: 400台设备并发上传
    print("🎯 测试场景1: 400台设备并发上传")
    tester.results = {"success": 0, "failed": 0, "total_time": 0}
    start_time = time.time()
    await tester.test_concurrent_upload(num_devices=400, concurrent_requests=50)
    tester.print_results("400台设备并发上传", start_time)
    
    # 等待处理完成
    await asyncio.sleep(5)
    stats = await tester.get_processor_stats()
    if stats:
        print(f"📈 批量处理器状态: {json.dumps(stats['data'], indent=2, ensure_ascii=False)}")
    
    # 测试场景2: 1000台设备并发上传
    print("\n🎯 测试场景2: 1000台设备并发上传")
    tester.results = {"success": 0, "failed": 0, "total_time": 0}
    start_time = time.time()
    await tester.test_concurrent_upload(num_devices=1000, concurrent_requests=100)
    tester.print_results("1000台设备并发上传", start_time)
    
    # 等待处理完成
    await asyncio.sleep(10)
    final_stats = await tester.get_processor_stats()
    if final_stats:
        print(f"📈 最终批量处理器状态: {json.dumps(final_stats['data'], indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    print("🔬 设备批量处理器性能测试")
    print("=" * 60)
    asyncio.run(main()) 
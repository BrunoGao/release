#!/usr/bin/env python3
"""
upload_device_info 接口优化效果测试
对比优化前后的性能提升
"""

import asyncio
import aiohttp
import time
import json
import statistics
from datetime import datetime
from typing import List, Dict, Any

class DeviceUploadOptimizationTester:
    """设备上传优化测试器"""
    
    def __init__(self, base_url: str = "http://localhost:5225"):
        self.base_url = base_url
        self.test_results = {
            'single_device_tests': [],
            'batch_tests': [],
            'concurrent_tests': []
        }
    
    def generate_device_data(self, device_sn: str) -> Dict[str, Any]:
        """生成设备信息数据"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return {
            "SerialNumber": device_sn,
            "DeviceName": f"TestDevice_{device_sn[-6:]}",
            "SystemSoftwareVersion": "v2.1.0 Build 20250909",
            "WifiAddress": f"AA:BB:CC:DD:EE:{device_sn[-2:]}",
            "BluetoothAddress": f"BB:CC:DD:EE:FF:{device_sn[-2:]}",
            "IPAddress": f"192.168.1.{hash(device_sn) % 254 + 1}",
            "NetworkAccessMode": "wifi",
            "IMEI": f"86{device_sn[-13:]}",
            "batteryLevel": 75,
            "chargingStatus": "NOT_CHARGING", 
            "wearState": 1,
            "timestamp": timestamp,
            "customer_id": 1,
            "org_id": 1,
            "user_id": 1
        }
    
    async def test_single_device_upload(self, device_sn: str) -> Dict[str, Any]:
        """测试单设备上传"""
        device_data = self.generate_device_data(device_sn)
        
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            
            try:
                async with session.post(
                    f"{self.base_url}/upload_device_info",
                    json=device_data,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    response_time = time.time() - start_time
                    response_text = await response.text()
                    
                    return {
                        'device_sn': device_sn,
                        'success': response.status == 200,
                        'status_code': response.status,
                        'response_time': response_time,
                        'response': response_text
                    }
            except Exception as e:
                return {
                    'device_sn': device_sn,
                    'success': False,
                    'response_time': time.time() - start_time,
                    'error': str(e)
                }
    
    async def test_batch_upload(self, device_sns: List[str]) -> Dict[str, Any]:
        """测试批量设备上传"""
        batch_data = [self.generate_device_data(sn) for sn in device_sns]
        
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            
            try:
                async with session.post(
                    f"{self.base_url}/upload_device_info",
                    json=batch_data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response_time = time.time() - start_time
                    response_text = await response.text()
                    
                    return {
                        'batch_size': len(device_sns),
                        'success': response.status == 200,
                        'status_code': response.status,
                        'response_time': response_time,
                        'avg_time_per_device': response_time / len(device_sns),
                        'response': response_text
                    }
            except Exception as e:
                return {
                    'batch_size': len(device_sns),
                    'success': False,
                    'response_time': time.time() - start_time,
                    'error': str(e)
                }
    
    async def test_concurrent_uploads(self, device_count: int = 100, concurrent: int = 20) -> Dict[str, Any]:
        """测试并发设备上传"""
        device_sns = [f"TESTDEV{str(i).zfill(6)}" for i in range(device_count)]
        
        # 创建并发任务
        semaphore = asyncio.Semaphore(concurrent)
        
        async def upload_with_semaphore(device_sn):
            async with semaphore:
                return await self.test_single_device_upload(device_sn)
        
        start_time = time.time()
        tasks = [upload_with_semaphore(sn) for sn in device_sns]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # 统计结果
        successful = sum(1 for r in results if isinstance(r, dict) and r.get('success'))
        failed = device_count - successful
        response_times = [r['response_time'] for r in results if isinstance(r, dict) and 'response_time' in r]
        
        return {
            'device_count': device_count,
            'concurrent': concurrent,
            'total_time': total_time,
            'successful': successful,
            'failed': failed,
            'success_rate': successful / device_count * 100,
            'qps': device_count / total_time,
            'avg_response_time': statistics.mean(response_times) if response_times else 0,
            'p95_response_time': sorted(response_times)[int(len(response_times) * 0.95)] if response_times else 0
        }
    
    async def get_processor_stats(self) -> Dict[str, Any]:
        """获取处理器性能统计"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/device_processor/stats",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {"success": False, "error": f"HTTP {response.status}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def run_comprehensive_test(self):
        """运行综合性能测试"""
        print("🚀 upload_device_info 接口优化效果测试")
        print("=" * 60)
        
        # 1. 单设备上传测试
        print("\n1️⃣ 单设备上传性能测试")
        print("-" * 30)
        
        single_tests = []
        for i in range(10):
            result = await self.test_single_device_upload(f"SINGLE{str(i).zfill(3)}")
            single_tests.append(result)
            if result['success']:
                print(f"✅ 设备 {result['device_sn']}: {result['response_time']:.3f}s")
            else:
                print(f"❌ 设备 {result['device_sn']}: 失败")
        
        single_times = [r['response_time'] for r in single_tests if r['success']]
        if single_times:
            print(f"\n📊 单设备上传统计:")
            print(f"   - 成功率: {len(single_times)}/10")
            print(f"   - 平均响应时间: {statistics.mean(single_times):.3f}s")
            print(f"   - 最快: {min(single_times):.3f}s")
            print(f"   - 最慢: {max(single_times):.3f}s")
        
        # 2. 批量上传测试
        print("\n2️⃣ 批量上传性能测试")
        print("-" * 30)
        
        batch_sizes = [10, 50, 100, 200]
        batch_results = []
        
        for batch_size in batch_sizes:
            device_sns = [f"BATCH{batch_size}_{str(i).zfill(3)}" for i in range(batch_size)]
            result = await self.test_batch_upload(device_sns)
            batch_results.append(result)
            
            if result['success']:
                print(f"✅ 批量上传 {batch_size}台: {result['response_time']:.3f}s, 平均 {result['avg_time_per_device']:.3f}s/台")
            else:
                print(f"❌ 批量上传 {batch_size}台: 失败")
        
        # 3. 并发上传测试
        print("\n3️⃣ 并发上传性能测试")
        print("-" * 30)
        
        concurrent_configs = [
            (50, 10),   # 50设备，10并发
            (100, 20),  # 100设备，20并发
            (200, 50),  # 200设备，50并发
        ]
        
        concurrent_results = []
        for device_count, concurrent in concurrent_configs:
            print(f"🔄 测试 {device_count}设备 {concurrent}并发...")
            result = await self.test_concurrent_uploads(device_count, concurrent)
            concurrent_results.append(result)
            
            print(f"✅ QPS: {result['qps']:.1f}, 成功率: {result['success_rate']:.1f}%, "
                  f"平均响应: {result['avg_response_time']:.3f}s")
        
        # 4. 处理器统计
        print("\n4️⃣ 处理器性能统计")
        print("-" * 30)
        
        stats = await self.get_processor_stats()
        if stats.get('success'):
            data = stats.get('data', {})
            print(f"📊 队列状态:")
            queue_sizes = data.get('queue_sizes', {})
            for queue_name, size in queue_sizes.items():
                print(f"   - {queue_name}: {size}")
            
            processing_stats = data.get('processing_stats', {})
            if processing_stats:
                print(f"\n📈 处理统计:")
                print(f"   - 总处理: {processing_stats.get('total_processed', 0)}")
                print(f"   - 总成功: {processing_stats.get('total_success', 0)}")
                print(f"   - 总错误: {processing_stats.get('total_errors', 0)}")
                print(f"   - 平均处理时间: {processing_stats.get('avg_processing_time', 0):.3f}s")
        else:
            print(f"❌ 无法获取处理器统计: {stats.get('error', '未知错误')}")
        
        # 生成综合报告
        print("\n" + "=" * 60)
        print("📊 优化效果综合评估")
        print("=" * 60)
        
        # 性能评级
        if single_times:
            avg_single_time = statistics.mean(single_times)
            if avg_single_time < 0.05:
                single_grade = "🏆 优秀"
            elif avg_single_time < 0.1:
                single_grade = "✅ 良好"
            elif avg_single_time < 0.2:
                single_grade = "⚠️ 一般"
            else:
                single_grade = "❌ 需要优化"
            
            print(f"单设备上传性能: {single_grade} (平均 {avg_single_time:.3f}s)")
        
        if batch_results:
            successful_batches = [r for r in batch_results if r['success']]
            if successful_batches:
                avg_batch_efficiency = statistics.mean([r['avg_time_per_device'] for r in successful_batches])
                print(f"批量上传效率: 平均 {avg_batch_efficiency:.3f}s/设备")
        
        if concurrent_results:
            max_qps = max(r['qps'] for r in concurrent_results)
            best_success_rate = max(r['success_rate'] for r in concurrent_results)
            print(f"并发处理能力: 最高 {max_qps:.1f} QPS, 最佳成功率 {best_success_rate:.1f}%")
        
        print(f"\n🎯 优化目标达成情况:")
        print(f"   - 响应时间 <20ms: {'✅' if avg_single_time < 0.02 else '❌'}")
        print(f"   - QPS >2000: {'✅' if max_qps > 2000 else '❌'}")  
        print(f"   - 成功率 >99.9%: {'✅' if best_success_rate > 99.9 else '❌'}")

def main():
    """主函数"""
    import sys
    
    base_url = "http://localhost:5225"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    print(f"🎯 测试目标: {base_url}")
    print(f"💡 测试upload_device_info接口优化效果")
    
    tester = DeviceUploadOptimizationTester(base_url)
    
    try:
        asyncio.run(tester.run_comprehensive_test())
    except KeyboardInterrupt:
        print("\n⏸️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")

if __name__ == "__main__":
    main()
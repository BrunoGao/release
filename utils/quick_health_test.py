#!/usr/bin/env python3
"""
快速健康数据上传测试
用于验证异步优化系统的基本功能
"""

import asyncio
import aiohttp
import json
import time
import random
from datetime import datetime
from typing import Dict, Any

class QuickHealthTester:
    """快速健康数据测试器"""
    
    def __init__(self, base_url: str = "http://localhost:5225"):
        self.base_url = base_url
        
    def generate_sample_health_data(self, device_sn: str = None) -> Dict[str, Any]:
        """生成符合样例格式的健康数据"""
        if device_sn is None:
            device_sn = f"CRFTQ{random.randint(20000, 99999)}{random.randint(100000, 999999)}"
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return {
            "data": {
                "deviceSn": device_sn,
                "heart_rate": random.randint(60, 120),
                "blood_oxygen": random.randint(95, 100) if random.random() > 0.3 else 0,
                "body_temperature": f"{random.uniform(36.0, 37.5):.1f}",
                "step": random.randint(0, 15000),
                "distance": f"{random.uniform(0, 10):.1f}",
                "calorie": f"{random.uniform(0, 500):.1f}",
                "latitude": "22.540278",
                "longitude": "114.015232",
                "altitude": "0.0",
                "stress": random.randint(0, 100),
                "upload_method": "wifi",
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
    
    async def test_single_upload(self) -> bool:
        """测试单个健康数据上传"""
        print("🧪 测试单个健康数据上传...")
        
        health_data = self.generate_sample_health_data()
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/upload_health_data"
                
                start_time = time.time()
                async with session.post(url, json=health_data) as response:
                    response_time = time.time() - start_time
                    response_text = await response.text()
                    
                    if response.status == 200:
                        print(f"✅ 上传成功! 响应时间: {response_time:.3f}s")
                        print(f"   设备: {health_data['data']['deviceSn']}")
                        print(f"   心率: {health_data['data']['heart_rate']}")
                        print(f"   血氧: {health_data['data']['blood_oxygen']}")
                        return True
                    else:
                        print(f"❌ 上传失败: HTTP {response.status}")
                        print(f"   响应: {response_text[:200]}")
                        return False
                        
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            return False
    
    async def test_batch_upload(self, device_count: int = 10) -> bool:
        """测试批量健康数据上传"""
        print(f"🧪 测试批量健康数据上传 ({device_count}台设备)...")
        
        # 生成批量数据
        batch_data = []
        for i in range(device_count):
            health_data = self.generate_sample_health_data()
            batch_data.append(health_data["data"])
        
        payload = {"data": batch_data}
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/upload_health_data"
                
                start_time = time.time()
                async with session.post(url, json=payload) as response:
                    response_time = time.time() - start_time
                    response_text = await response.text()
                    
                    if response.status == 200:
                        print(f"✅ 批量上传成功! 响应时间: {response_time:.3f}s")
                        print(f"   设备数量: {device_count}")
                        print(f"   平均处理时间: {response_time/device_count:.3f}s/设备")
                        return True
                    else:
                        print(f"❌ 批量上传失败: HTTP {response.status}")
                        print(f"   响应: {response_text[:200]}")
                        return False
                        
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            return False
    
    async def test_concurrent_upload(self, device_count: int = 50, concurrent: int = 10) -> bool:
        """测试并发上传"""
        print(f"🧪 测试并发上传 ({device_count}台设备, {concurrent}并发)...")
        
        successful = 0
        failed = 0
        response_times = []
        
        async def upload_single_device():
            nonlocal successful, failed
            
            health_data = self.generate_sample_health_data()
            
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{self.base_url}/upload_health_data"
                    
                    start_time = time.time()
                    async with session.post(url, json=health_data) as response:
                        response_time = time.time() - start_time
                        response_times.append(response_time)
                        
                        if response.status == 200:
                            successful += 1
                        else:
                            failed += 1
                            
            except Exception:
                failed += 1
        
        # 创建并发任务
        tasks = []
        for _ in range(device_count):
            task = asyncio.create_task(upload_single_device())
            tasks.append(task)
            
            # 控制并发数
            if len(tasks) >= concurrent:
                await asyncio.gather(*tasks[:concurrent])
                tasks = tasks[concurrent:]
        
        # 等待剩余任务完成
        if tasks:
            await asyncio.gather(*tasks)
        
        # 统计结果
        total = successful + failed
        success_rate = (successful / total * 100) if total > 0 else 0
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        print(f"📊 并发测试结果:")
        print(f"   总请求: {total}")
        print(f"   成功: {successful}")
        print(f"   失败: {failed}")
        print(f"   成功率: {success_rate:.1f}%")
        print(f"   平均响应时间: {avg_response_time:.3f}s")
        
        return success_rate >= 90  # 90%以上成功率算测试通过
    
    async def test_system_status(self) -> bool:
        """测试系统状态"""
        print("🧪 测试系统状态...")
        
        endpoints = [
            "/health",
            "/api/health", 
            "/get_optimizer_stats",
            "/get_async_system_stats"
        ]
        
        system_ok = False
        
        for endpoint in endpoints:
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{self.base_url}{endpoint}"
                    async with session.get(url) as response:
                        if response.status == 200:
                            if endpoint in ["/health", "/api/health"]:
                                print(f"✅ 服务健康检查正常: {endpoint}")
                                system_ok = True
                            else:
                                response_data = await response.json()
                                print(f"✅ 系统状态接口正常: {endpoint}")
                                if endpoint == "/get_async_system_stats":
                                    system_version = response_data.get("system_overview", {}).get("version", "unknown")
                                    system_status = response_data.get("system_overview", {}).get("status", "unknown")
                                    print(f"   异步系统版本: {system_version}")
                                    print(f"   异步系统状态: {system_status}")
                        else:
                            print(f"⚠️ {endpoint}: HTTP {response.status}")
                            
            except Exception as e:
                print(f"⚠️ {endpoint}: {e}")
        
        return system_ok
    
    async def run_full_test(self):
        """运行完整测试套件"""
        print("🚀 异步健康数据处理系统快速测试")
        print("=" * 50)
        
        test_results = []
        
        # 1. 系统状态测试
        print("\n1️⃣ 系统状态检查")
        print("-" * 20)
        result1 = await self.test_system_status()
        test_results.append(("系统状态", result1))
        
        # 2. 单个上传测试
        print("\n2️⃣ 单个数据上传测试")
        print("-" * 20)
        result2 = await self.test_single_upload()
        test_results.append(("单个上传", result2))
        
        # 3. 批量上传测试
        print("\n3️⃣ 批量数据上传测试")
        print("-" * 20)
        result3 = await self.test_batch_upload(10)
        test_results.append(("批量上传", result3))
        
        # 4. 并发上传测试
        print("\n4️⃣ 并发上传测试")
        print("-" * 20)
        result4 = await self.test_concurrent_upload(50, 10)
        test_results.append(("并发上传", result4))
        
        # 测试总结
        print("\n" + "=" * 50)
        print("📊 测试结果总结")
        print("=" * 50)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name:12}: {status}")
            if result:
                passed += 1
        
        print(f"\n总计: {passed}/{total} 项测试通过")
        
        if passed == total:
            print("🎉 所有测试通过！异步系统运行正常")
        elif passed >= total * 0.8:
            print("⚠️ 大部分测试通过，系统基本正常")
        else:
            print("❌ 多项测试失败，请检查系统配置")
        
        return passed == total

def main():
    """主函数"""
    import sys
    
    # 解析命令行参数
    base_url = "http://localhost:5225"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    print(f"🎯 测试目标: {base_url}")
    print("💡 这是一个快速验证测试，用于检查异步系统基本功能")
    print()
    
    tester = QuickHealthTester(base_url)
    
    try:
        success = asyncio.run(tester.run_full_test())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏸️ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
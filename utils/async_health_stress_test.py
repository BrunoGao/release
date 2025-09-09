#!/usr/bin/env python3
"""
异步健康数据处理系统压力测试
1000台手表并发上传健康数据压测
"""

import asyncio
import aiohttp
import time
import json
import random
import logging
import sys
import signal
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import threading
from dataclasses import dataclass, asdict
import uuid
import statistics

@dataclass
class TestConfig:
    """测试配置"""
    base_url: str = "http://localhost:5225"  # ljwx-bigscreen 本地调试端口
    total_devices: int = 1000  # 总设备数
    concurrent_requests: int = 100  # 并发请求数
    test_duration_minutes: int = 10  # 测试持续时间（分钟）
    upload_interval_seconds: float = 1.0  # 每个设备上传间隔（秒）
    timeout_seconds: int = 30  # 请求超时
    enable_batch_upload: bool = True  # 启用批量上传测试

@dataclass 
class TestStats:
    """测试统计信息"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    timeout_requests: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    response_times: List[float] = None
    error_details: Dict[str, int] = None
    
    def __post_init__(self):
        if self.response_times is None:
            self.response_times = []
        if self.error_details is None:
            self.error_details = {}

class AsyncHealthStressTester:
    """异步健康数据压力测试器"""
    
    def __init__(self, config: TestConfig = None):
        self.config = config or TestConfig()
        self.stats = TestStats()
        self.running = False
        self.stats_lock = threading.Lock()
        
        # 设备列表
        self.device_list = self._generate_device_list()
        
        # 日志设置
        self._setup_logging()
        
        # 信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _generate_device_list(self) -> List[str]:
        """生成设备SN列表，使用实际创建的1000个手表序列号"""
        devices = []
        for i in range(min(self.config.total_devices, 1000)):
            # 使用实际创建的手表序列号格式：CRFTQ23409000000 到 CRFTQ23409000999
            device_sn = f"CRFTQ23409{i:06d}"
            devices.append(device_sn)
        
        # 如果需要更多设备，继续用随机序列号
        if self.config.total_devices > 1000:
            for i in range(1000, self.config.total_devices):
                device_sn = f"CRFTQ{random.randint(20000, 99999)}{random.randint(100000, 999999)}"
                devices.append(device_sn)
                
        return devices
    
    def _setup_logging(self):
        """设置日志"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = log_dir / f"async_stress_test_{timestamp}.log"
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"🚀 异步健康数据压力测试开始")
        self.logger.info(f"📝 日志文件: {log_file}")
    
    def _signal_handler(self, signum, frame):
        """信号处理"""
        self.logger.info(f"接收到信号 {signum}, 停止测试...")
        self.running = False
    
    def generate_health_data(self, device_sn: str, timestamp: datetime = None) -> Dict[str, Any]:
        """生成健康数据（符合提供的样例格式）"""
        if timestamp is None:
            timestamp = datetime.now()
        
        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        # 生成真实的健康数据变化
        heart_rate = random.randint(60, 120)
        blood_oxygen = random.randint(95, 100) if random.random() > 0.2 else 0
        body_temperature = f"{random.uniform(36.0, 37.5):.1f}"
        
        # 运动数据（模拟真实场景）
        is_active = random.random() > 0.3
        step = random.randint(0, 15000) if is_active else 0
        distance = f"{random.uniform(0, 12):.1f}" if is_active else "0.0"
        calorie = f"{random.uniform(0, 600):.1f}" if is_active else "0.0"
        
        # GPS数据（深圳地区）
        latitude = f"{random.uniform(22.5, 22.6):.6f}"
        longitude = f"{random.uniform(113.9, 114.1):.6f}" 
        altitude = f"{random.uniform(0, 100):.1f}"
        
        # 压力和血压
        stress = random.randint(0, 100)
        blood_pressure_systolic = random.randint(110, 140)
        blood_pressure_diastolic = random.randint(70, 90)
        
        # 随机睡眠数据（部分设备有）
        sleep_data = "null"
        if random.random() > 0.8:  # 20%概率有睡眠数据
            sleep_data = json.dumps({
                "code": 0,
                "data": [{
                    "endTimeStamp": int(timestamp.timestamp() * 1000),
                    "startTimeStamp": int((timestamp - timedelta(hours=8)).timestamp() * 1000),
                    "type": 2
                }],
                "name": "sleep",
                "type": "history"
            })
        
        return {
            "data": {
                "deviceSn": device_sn,
                "heart_rate": heart_rate,
                "blood_oxygen": blood_oxygen,
                "body_temperature": body_temperature,
                "step": step,
                "distance": distance,
                "calorie": calorie,
                "latitude": latitude,
                "longitude": longitude,
                "altitude": altitude,
                "stress": stress,
                "upload_method": random.choice(["wifi", "4g", "bluetooth"]),
                "blood_pressure_systolic": blood_pressure_systolic,
                "blood_pressure_diastolic": blood_pressure_diastolic,
                "sleepData": sleep_data,
                "exerciseDailyData": "null",
                "exerciseWeekData": "null", 
                "scientificSleepData": "null",
                "workoutData": "null",
                "timestamp": timestamp_str
            }
        }
    
    def generate_batch_health_data(self, device_count: int = 50) -> Dict[str, Any]:
        """生成批量健康数据"""
        timestamp = datetime.now()
        batch_data = []
        
        # 随机选择设备
        selected_devices = random.sample(self.device_list, min(device_count, len(self.device_list)))
        
        for device_sn in selected_devices:
            health_data = self.generate_health_data(device_sn, timestamp)
            batch_data.append(health_data["data"])
        
        return {"data": batch_data}
    
    async def upload_single_health_data(self, session: aiohttp.ClientSession, device_sn: str) -> Dict[str, Any]:
        """上传单个设备健康数据"""
        start_time = time.time()
        
        try:
            health_data = self.generate_health_data(device_sn)
            url = f"{self.config.base_url}/upload_health_data"
            
            async with session.post(
                url, 
                json=health_data,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            ) as response:
                response_time = time.time() - start_time
                response_text = await response.text()
                
                # 更新统计
                with self.stats_lock:
                    self.stats.total_requests += 1
                    self.stats.response_times.append(response_time)
                    
                    if response.status == 200:
                        self.stats.successful_requests += 1
                    else:
                        self.stats.failed_requests += 1
                        error_key = f"HTTP_{response.status}"
                        self.stats.error_details[error_key] = self.stats.error_details.get(error_key, 0) + 1
                
                return {
                    'device_sn': device_sn,
                    'success': response.status == 200,
                    'status_code': response.status,
                    'response_time': response_time,
                    'response_text': response_text[:200],  # 限制响应文本长度
                    'timestamp': datetime.now().isoformat()
                }
                
        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            with self.stats_lock:
                self.stats.total_requests += 1
                self.stats.timeout_requests += 1
                self.stats.response_times.append(response_time)
                self.stats.error_details['TIMEOUT'] = self.stats.error_details.get('TIMEOUT', 0) + 1
            
            return {
                'device_sn': device_sn,
                'success': False,
                'error': 'TIMEOUT',
                'response_time': response_time,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            with self.stats_lock:
                self.stats.total_requests += 1
                self.stats.failed_requests += 1
                error_key = type(e).__name__
                self.stats.error_details[error_key] = self.stats.error_details.get(error_key, 0) + 1
                self.stats.response_times.append(response_time)
            
            return {
                'device_sn': device_sn,
                'success': False,
                'error': str(e),
                'response_time': response_time,
                'timestamp': datetime.now().isoformat()
            }
    
    async def upload_batch_health_data(self, session: aiohttp.ClientSession, batch_size: int = 50) -> Dict[str, Any]:
        """上传批量健康数据"""
        start_time = time.time()
        
        try:
            batch_data = self.generate_batch_health_data(batch_size)
            url = f"{self.config.base_url}/upload_health_data"
            
            async with session.post(
                url,
                json=batch_data,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds * 2)  # 批量请求超时时间加倍
            ) as response:
                response_time = time.time() - start_time
                response_text = await response.text()
                
                # 更新统计
                with self.stats_lock:
                    self.stats.total_requests += batch_size  # 批量请求按数据条数计算
                    self.stats.response_times.append(response_time)
                    
                    if response.status == 200:
                        self.stats.successful_requests += batch_size
                    else:
                        self.stats.failed_requests += batch_size
                        error_key = f"BATCH_HTTP_{response.status}"
                        self.stats.error_details[error_key] = self.stats.error_details.get(error_key, 0) + 1
                
                return {
                    'batch_size': batch_size,
                    'success': response.status == 200,
                    'status_code': response.status,
                    'response_time': response_time,
                    'response_text': response_text[:200],
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            response_time = time.time() - start_time
            with self.stats_lock:
                self.stats.total_requests += batch_size
                self.stats.failed_requests += batch_size
                error_key = f"BATCH_{type(e).__name__}"
                self.stats.error_details[error_key] = self.stats.error_details.get(error_key, 0) + 1
                self.stats.response_times.append(response_time)
            
            return {
                'batch_size': batch_size,
                'success': False,
                'error': str(e),
                'response_time': response_time,
                'timestamp': datetime.now().isoformat()
            }
    
    async def run_concurrent_test(self):
        """运行并发压力测试"""
        self.logger.info("🔥 开始1000台手表并发压力测试")
        self.logger.info(f"📊 配置信息:")
        self.logger.info(f"   - 总设备数: {self.config.total_devices}")
        self.logger.info(f"   - 并发数: {self.config.concurrent_requests}")
        self.logger.info(f"   - 测试时长: {self.config.test_duration_minutes}分钟")
        self.logger.info(f"   - 上传间隔: {self.config.upload_interval_seconds}秒")
        self.logger.info(f"   - 目标URL: {self.config.base_url}")
        
        self.running = True
        self.stats.start_time = datetime.now()
        
        # 创建HTTP会话
        connector = aiohttp.TCPConnector(
            limit=self.config.concurrent_requests * 2,
            limit_per_host=self.config.concurrent_requests,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'AsyncHealthStressTester/1.0'
            }
        ) as session:
            # 启动监控任务
            monitor_task = asyncio.create_task(self._monitor_progress())
            
            try:
                # 创建测试任务列表
                tasks = []
                end_time = datetime.now() + timedelta(minutes=self.config.test_duration_minutes)
                
                # 混合单个和批量上传测试
                while datetime.now() < end_time and self.running:
                    # 单个设备上传（70%）
                    if random.random() < 0.7 or not self.config.enable_batch_upload:
                        # 随机选择设备进行单个上传
                        selected_devices = random.sample(
                            self.device_list, 
                            min(self.config.concurrent_requests, len(self.device_list))
                        )
                        
                        for device_sn in selected_devices:
                            if len(tasks) >= self.config.concurrent_requests:
                                # 等待部分任务完成
                                done, pending = await asyncio.wait(
                                    tasks, 
                                    timeout=0.1, 
                                    return_when=asyncio.FIRST_COMPLETED
                                )
                                tasks = list(pending)
                            
                            task = asyncio.create_task(
                                self.upload_single_health_data(session, device_sn)
                            )
                            tasks.append(task)
                    
                    else:
                        # 批量上传（30%）
                        if len(tasks) >= self.config.concurrent_requests // 2:
                            done, pending = await asyncio.wait(
                                tasks,
                                timeout=0.1,
                                return_when=asyncio.FIRST_COMPLETED
                            )
                            tasks = list(pending)
                        
                        task = asyncio.create_task(
                            self.upload_batch_health_data(session, random.randint(10, 100))
                        )
                        tasks.append(task)
                    
                    # 控制上传频率
                    await asyncio.sleep(self.config.upload_interval_seconds)
                
                # 等待所有剩余任务完成
                if tasks:
                    self.logger.info(f"等待 {len(tasks)} 个剩余任务完成...")
                    await asyncio.gather(*tasks, return_exceptions=True)
                
            finally:
                monitor_task.cancel()
                try:
                    await monitor_task
                except asyncio.CancelledError:
                    pass
        
        self.stats.end_time = datetime.now()
        self._print_final_report()
    
    async def _monitor_progress(self):
        """监控测试进度"""
        last_requests = 0
        
        while self.running:
            try:
                await asyncio.sleep(10)  # 每10秒打印一次进度
                
                with self.stats_lock:
                    current_requests = self.stats.total_requests
                    successful = self.stats.successful_requests
                    failed = self.stats.failed_requests
                    
                    # 计算QPS
                    requests_delta = current_requests - last_requests
                    qps = requests_delta / 10.0
                    
                    # 计算成功率
                    success_rate = (successful / current_requests * 100) if current_requests > 0 else 0
                    
                    # 计算平均响应时间
                    avg_response_time = 0
                    if self.stats.response_times:
                        avg_response_time = statistics.mean(self.stats.response_times[-100:])  # 最近100个请求的平均时间
                
                elapsed_time = datetime.now() - self.stats.start_time if self.stats.start_time else timedelta(0)
                
                self.logger.info(
                    f"📊 测试进度 - "
                    f"总请求: {current_requests}, "
                    f"成功: {successful}, "
                    f"失败: {failed}, "
                    f"成功率: {success_rate:.1f}%, "
                    f"QPS: {qps:.1f}, "
                    f"平均响应时间: {avg_response_time:.3f}s, "
                    f"运行时间: {str(elapsed_time).split('.')[0]}"
                )
                
                last_requests = current_requests
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"监控进度异常: {e}")
    
    def _print_final_report(self):
        """打印最终测试报告"""
        self.logger.info("=" * 80)
        self.logger.info("📊 1000台手表并发压力测试报告")
        self.logger.info("=" * 80)
        
        if self.stats.start_time and self.stats.end_time:
            duration = self.stats.end_time - self.stats.start_time
            self.logger.info(f"⏱️  测试时长: {duration}")
            
            # 计算整体性能指标
            if self.stats.total_requests > 0 and duration.total_seconds() > 0:
                qps = self.stats.total_requests / duration.total_seconds()
                self.logger.info(f"🚀 整体QPS: {qps:.2f} 请求/秒")
                self.logger.info(f"💪 处理能力: {qps * 60:.0f} 请求/分钟")
        
        # 请求统计
        self.logger.info(f"📈 请求统计:")
        self.logger.info(f"   - 总请求数: {self.stats.total_requests}")
        self.logger.info(f"   - 成功请求: {self.stats.successful_requests}")
        self.logger.info(f"   - 失败请求: {self.stats.failed_requests}")
        self.logger.info(f"   - 超时请求: {self.stats.timeout_requests}")
        
        # 成功率
        if self.stats.total_requests > 0:
            success_rate = (self.stats.successful_requests / self.stats.total_requests) * 100
            self.logger.info(f"✅ 成功率: {success_rate:.2f}%")
        
        # 响应时间统计
        if self.stats.response_times:
            response_times = self.stats.response_times
            self.logger.info(f"⚡ 响应时间统计:")
            self.logger.info(f"   - 平均响应时间: {statistics.mean(response_times):.3f}秒")
            self.logger.info(f"   - 最快响应时间: {min(response_times):.3f}秒")
            self.logger.info(f"   - 最慢响应时间: {max(response_times):.3f}秒")
            self.logger.info(f"   - 95%响应时间: {statistics.quantiles(response_times, n=20)[18]:.3f}秒")
        
        # 错误详情
        if self.stats.error_details:
            self.logger.info(f"❌ 错误详情:")
            for error_type, count in self.stats.error_details.items():
                self.logger.info(f"   - {error_type}: {count}次")
        
        # 系统性能评估
        self._evaluate_system_performance()
    
    def _evaluate_system_performance(self):
        """评估系统性能"""
        self.logger.info("🎯 系统性能评估:")
        
        if not self.stats.response_times or self.stats.total_requests == 0:
            self.logger.info("   - 数据不足，无法评估")
            return
        
        # 计算指标
        success_rate = (self.stats.successful_requests / self.stats.total_requests) * 100
        avg_response_time = statistics.mean(self.stats.response_times)
        duration = self.stats.end_time - self.stats.start_time if self.stats.start_time and self.stats.end_time else timedelta(0)
        qps = self.stats.total_requests / duration.total_seconds() if duration.total_seconds() > 0 else 0
        
        # 性能等级评估
        performance_grade = "优秀"
        issues = []
        
        if success_rate < 95:
            performance_grade = "需要优化"
            issues.append(f"成功率偏低 ({success_rate:.1f}%)")
        
        if avg_response_time > 2.0:
            performance_grade = "需要优化" if performance_grade != "需要优化" else performance_grade
            issues.append(f"响应时间偏慢 ({avg_response_time:.3f}s)")
        
        if qps < 100:
            performance_grade = "需要优化" if performance_grade != "需要优化" else performance_grade
            issues.append(f"QPS偏低 ({qps:.1f})")
        
        self.logger.info(f"   - 性能等级: {performance_grade}")
        if issues:
            self.logger.info(f"   - 发现问题:")
            for issue in issues:
                self.logger.info(f"     * {issue}")
        
        # 异步优化系统性能对比
        self.logger.info("🆚 性能对比分析:")
        self.logger.info("   预期性能指标（基于异步优化）:")
        self.logger.info("   - 目标QPS: 500+ 请求/秒")
        self.logger.info("   - 目标响应时间: <0.2秒")
        self.logger.info("   - 目标成功率: >99%")
        self.logger.info("   - 并发处理能力: 1000+ 设备")
        
        if qps >= 500:
            self.logger.info("   ✅ QPS达标！异步优化效果显著")
        else:
            self.logger.info(f"   ⚠️ QPS未达标，当前: {qps:.1f}, 目标: 500+")
        
        if avg_response_time <= 0.2:
            self.logger.info("   ✅ 响应时间优秀！")
        else:
            self.logger.info(f"   ⚠️ 响应时间需优化，当前: {avg_response_time:.3f}s, 目标: <0.2s")

    async def run_system_integration_test(self):
        """运行系统集成测试 - 测试新异步架构"""
        self.logger.info("🔧 开始异步系统集成测试")
        
        # 测试异步处理器状态
        await self._test_async_processor_status()
        
        # 测试批量处理能力
        await self._test_batch_processing()
        
        # 测试资源管理
        await self._test_resource_management()
    
    async def _test_async_processor_status(self):
        """测试异步处理器状态"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.config.base_url}/get_async_system_stats"
                async with session.get(url) as response:
                    if response.status == 200:
                        stats = await response.json()
                        self.logger.info("✅ 异步处理器状态正常")
                        self.logger.info(f"   系统版本: {stats.get('system_overview', {}).get('version', 'unknown')}")
                        self.logger.info(f"   运行状态: {stats.get('system_overview', {}).get('status', 'unknown')}")
                    else:
                        self.logger.warning(f"⚠️ 无法获取异步处理器状态: HTTP {response.status}")
        except Exception as e:
            self.logger.error(f"❌ 异步处理器状态测试失败: {e}")
    
    async def _test_batch_processing(self):
        """测试批量处理能力"""
        self.logger.info("🔄 测试批量处理能力...")
        
        batch_sizes = [10, 50, 100, 200]
        
        async with aiohttp.ClientSession() as session:
            for batch_size in batch_sizes:
                try:
                    result = await self.upload_batch_health_data(session, batch_size)
                    if result['success']:
                        self.logger.info(f"   ✅ 批量大小 {batch_size}: 成功，响应时间: {result['response_time']:.3f}s")
                    else:
                        self.logger.warning(f"   ⚠️ 批量大小 {batch_size}: 失败")
                except Exception as e:
                    self.logger.error(f"   ❌ 批量大小 {batch_size}: 异常 - {e}")
    
    async def _test_resource_management(self):
        """测试资源管理"""
        self.logger.info("📊 测试动态资源管理...")
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.config.base_url}/get_optimizer_stats"
                async with session.get(url) as response:
                    if response.status == 200:
                        stats = await response.json()
                        self.logger.info("✅ 资源管理器运行正常")
                        self.logger.info(f"   批次大小: {stats.get('batch_size', 'unknown')}")
                        self.logger.info(f"   工作线程: {stats.get('max_workers', 'unknown')}")
                        self.logger.info(f"   队列大小: {stats.get('queue_size', 'unknown')}")
                    else:
                        self.logger.warning(f"⚠️ 无法获取资源管理器状态: HTTP {response.status}")
        except Exception as e:
            self.logger.error(f"❌ 资源管理测试失败: {e}")

def main():
    """主函数"""
    print("🚀 异步健康数据处理系统压力测试")
    print("=" * 60)
    print("🎯 目标: 测试1000台手表并发上传健康数据")
    print("⚡ 验证异步优化系统性能提升效果")
    print()
    
    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description='异步健康数据压力测试')
    parser.add_argument('--devices', type=int, default=1000, help='设备数量 (默认: 1000)')
    parser.add_argument('--concurrent', type=int, default=100, help='并发数 (默认: 100)')
    parser.add_argument('--duration', type=int, default=10, help='测试时长(分钟) (默认: 10)')
    parser.add_argument('--url', type=str, default='http://localhost:5225', help='服务URL (默认: http://localhost:5225)')
    parser.add_argument('--interval', type=float, default=1.0, help='上传间隔(秒) (默认: 1.0)')
    parser.add_argument('--integration-test', action='store_true', help='运行系统集成测试')
    
    args = parser.parse_args()
    
    # 创建测试配置
    config = TestConfig(
        base_url=args.url,
        total_devices=args.devices,
        concurrent_requests=args.concurrent,
        test_duration_minutes=args.duration,
        upload_interval_seconds=args.interval
    )
    
    print(f"📊 测试配置:")
    print(f"   - 设备数量: {config.total_devices}")
    print(f"   - 并发数: {config.concurrent_requests}")
    print(f"   - 测试时长: {config.test_duration_minutes}分钟")
    print(f"   - 服务地址: {config.base_url}")
    print(f"   - 上传间隔: {config.upload_interval_seconds}秒")
    print()
    
    if not args.integration_test:
        confirm = input("确认开始压力测试? (y/N): ").strip().lower()
        if confirm != 'y':
            print("已取消")
            return
    
    # 创建测试器
    tester = AsyncHealthStressTester(config)
    
    try:
        if args.integration_test:
            asyncio.run(tester.run_system_integration_test())
        else:
            asyncio.run(tester.run_concurrent_test())
    except KeyboardInterrupt:
        print("\n⏸️ 用户中断测试")
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")

if __name__ == "__main__":
    main()
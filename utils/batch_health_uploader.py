#!/usr/bin/env python3
"""
批量健康数据上传优化器
实现批量插入优化，提高数据库写入性能
"""

import asyncio
import aiohttp
import time
import json
import random
import logging
import mysql.connector
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import statistics

@dataclass
class BatchConfig:
    """批量优化配置"""
    base_url: str = "http://localhost:5225"
    batch_size: int = 50  # 每批次上传数量
    concurrent_batches: int = 10  # 并发批次数
    test_duration_minutes: int = 3
    batch_interval_seconds: float = 0.1  # 批次间隔
    timeout_seconds: int = 30
    db_config: dict = None

@dataclass
class BatchStats:
    """批量测试统计"""
    total_batches: int = 0
    total_records: int = 0
    successful_batches: int = 0
    failed_batches: int = 0
    successful_records: int = 0
    failed_records: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    batch_response_times: List[float] = None
    error_details: Dict[str, int] = None
    
    def __post_init__(self):
        if self.batch_response_times is None:
            self.batch_response_times = []
        if self.error_details is None:
            self.error_details = {}

class BatchHealthUploader:
    """批量健康数据上传优化器"""
    
    def __init__(self, config: BatchConfig = None):
        self.config = config or BatchConfig()
        if not self.config.db_config:
            self.config.db_config = {
                'host': '127.0.0.1',
                'port': 3306,
                'database': 'test',
                'user': 'root',
                'password': '123456',
                'charset': 'utf8mb4'
            }
        
        self.stats = BatchStats()
        self.running = False
        self.user_devices = []
        
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = log_dir / f"batch_health_test_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("🚀 批量健康数据上传优化器开始")
        self.logger.info(f"📝 日志文件: {log_file}")
    
    def load_real_users_and_devices(self) -> List[Tuple[int, str, str]]:
        """从数据库加载真实的用户和设备信息"""
        self.logger.info("📊 加载真实用户和设备信息...")
        
        try:
            connection = mysql.connector.connect(**self.config.db_config)
            cursor = connection.cursor()
            
            sql = """
            SELECT id, user_name, device_sn 
            FROM sys_user 
            WHERE user_name LIKE 'CRFTQ23409%' 
            AND device_sn IS NOT NULL
            ORDER BY id
            LIMIT 1000
            """
            
            cursor.execute(sql)
            results = cursor.fetchall()
            
            user_devices = []
            for user_id, user_name, device_sn in results:
                user_devices.append((user_id, user_name, device_sn))
            
            self.logger.info(f"✅ 成功加载 {len(user_devices)} 个用户设备信息")
            
            cursor.close()
            connection.close()
            
            return user_devices
            
        except Exception as e:
            self.logger.error(f"❌ 加载用户设备信息失败: {e}")
            return []
    
    def generate_batch_health_data(self, user_devices: List[Tuple[int, str, str]]) -> List[Dict[str, Any]]:
        """生成一批健康数据"""
        timestamp = datetime.now()
        batch_data = []
        
        for user_id, user_name, device_sn in user_devices:
            # 基于用户ID生成个性化数据
            random.seed(user_id + int(timestamp.timestamp()))
            
            health_record = {
                "deviceSn": device_sn,
                "userId": user_id,
                "heart_rate": random.randint(60, 120),
                "blood_oxygen": random.randint(95, 100) if random.random() > 0.1 else 0,
                "body_temperature": f"{random.uniform(36.0, 37.5):.1f}",
                "step": random.randint(0, 15000),
                "distance": f"{random.uniform(0, 12):.1f}",
                "calorie": f"{random.uniform(0, 600):.1f}",
                "latitude": f"{random.uniform(22.5, 22.6):.6f}",
                "longitude": f"{random.uniform(113.9, 114.1):.6f}",
                "altitude": f"{random.uniform(0, 100):.1f}",
                "stress": random.randint(0, 100),
                "upload_method": random.choice(["wifi", "4g", "bluetooth"]),
                "blood_pressure_systolic": random.randint(110, 140),
                "blood_pressure_diastolic": random.randint(70, 90),
                "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            batch_data.append(health_record)
        
        return batch_data
    
    async def upload_batch_health_data(self, session: aiohttp.ClientSession, batch_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """上传一批健康数据"""
        start_time = time.time()
        batch_size = len(batch_data)
        
        try:
            # 构造批量上传的数据格式
            upload_data = {"data": batch_data}
            url = f"{self.config.base_url}/upload_health_data"
            
            async with session.post(
                url,
                json=upload_data,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            ) as response:
                response_time = time.time() - start_time
                response_text = await response.text()
                
                # 更新统计
                self.stats.total_batches += 1
                self.stats.total_records += batch_size
                self.stats.batch_response_times.append(response_time)
                
                if response.status == 200:
                    self.stats.successful_batches += 1
                    self.stats.successful_records += batch_size
                else:
                    self.stats.failed_batches += 1
                    self.stats.failed_records += batch_size
                    error_key = f"HTTP_{response.status}"
                    self.stats.error_details[error_key] = self.stats.error_details.get(error_key, 0) + 1
                
                return {
                    'batch_size': batch_size,
                    'success': response.status == 200,
                    'status_code': response.status,
                    'response_time': response_time,
                    'response_text': response_text[:100],
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            response_time = time.time() - start_time
            self.stats.total_batches += 1
            self.stats.total_records += batch_size
            self.stats.failed_batches += 1
            self.stats.failed_records += batch_size
            error_key = type(e).__name__
            self.stats.error_details[error_key] = self.stats.error_details.get(error_key, 0) + 1
            self.stats.batch_response_times.append(response_time)
            
            return {
                'batch_size': batch_size,
                'success': False,
                'error': str(e),
                'response_time': response_time,
                'timestamp': datetime.now().isoformat()
            }
    
    async def run_batch_stress_test(self):
        """运行批量压力测试"""
        self.logger.info("🔥 开始批量健康数据压力测试")
        
        # 加载真实用户设备信息
        self.user_devices = self.load_real_users_and_devices()
        if not self.user_devices:
            self.logger.error("❌ 无法加载用户设备信息，测试终止")
            return
        
        self.logger.info(f"📊 批量测试配置:")
        self.logger.info(f"   - 真实用户数: {len(self.user_devices)}")
        self.logger.info(f"   - 每批次大小: {self.config.batch_size}")
        self.logger.info(f"   - 并发批次数: {self.config.concurrent_batches}")
        self.logger.info(f"   - 测试时长: {self.config.test_duration_minutes}分钟")
        self.logger.info(f"   - 批次间隔: {self.config.batch_interval_seconds}秒")
        self.logger.info(f"   - 目标URL: {self.config.base_url}")
        
        self.running = True
        self.stats.start_time = datetime.now()
        
        # 创建HTTP会话
        connector = aiohttp.TCPConnector(
            limit=self.config.concurrent_batches * 2,
            limit_per_host=self.config.concurrent_batches,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds),
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'BatchHealthUploader/1.0'
            }
        ) as session:
            # 启动监控任务
            monitor_task = asyncio.create_task(self._monitor_progress())
            
            try:
                tasks = []
                end_time = datetime.now() + timedelta(minutes=self.config.test_duration_minutes)
                
                while datetime.now() < end_time and self.running:
                    # 随机选择用户创建批次
                    batch_users = random.sample(
                        self.user_devices,
                        min(self.config.batch_size, len(self.user_devices))
                    )
                    
                    # 生成批量数据
                    batch_data = self.generate_batch_health_data(batch_users)
                    
                    # 控制并发批次数
                    if len(tasks) >= self.config.concurrent_batches:
                        done, pending = await asyncio.wait(
                            tasks,
                            timeout=0.1,
                            return_when=asyncio.FIRST_COMPLETED
                        )
                        tasks = list(pending)
                    
                    # 创建批量上传任务
                    task = asyncio.create_task(
                        self.upload_batch_health_data(session, batch_data)
                    )
                    tasks.append(task)
                    
                    # 控制批次频率
                    await asyncio.sleep(self.config.batch_interval_seconds)
                
                # 等待剩余任务完成
                if tasks:
                    self.logger.info(f"等待 {len(tasks)} 个剩余批次完成...")
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
        last_records = 0
        
        while self.running:
            try:
                await asyncio.sleep(10)  # 每10秒报告一次
                
                current_records = self.stats.total_records
                successful_records = self.stats.successful_records
                failed_records = self.stats.failed_records
                
                # 计算记录QPS
                records_delta = current_records - last_records
                qps = records_delta / 10.0
                
                # 计算成功率
                success_rate = (successful_records / current_records * 100) if current_records > 0 else 0
                
                # 计算平均批次响应时间
                avg_batch_time = 0
                if self.stats.batch_response_times:
                    avg_batch_time = statistics.mean(self.stats.batch_response_times[-20:])
                
                elapsed_time = datetime.now() - self.stats.start_time if self.stats.start_time else timedelta(0)
                
                self.logger.info(
                    f"📊 批量测试进度 - "
                    f"总记录: {current_records}, "
                    f"成功: {successful_records}, "
                    f"失败: {failed_records}, "
                    f"成功率: {success_rate:.1f}%, "
                    f"记录QPS: {qps:.1f}, "
                    f"批次数: {self.stats.total_batches}, "
                    f"平均批次时间: {avg_batch_time:.3f}s, "
                    f"运行时间: {str(elapsed_time).split('.')[0]}"
                )
                
                last_records = current_records
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"监控进度异常: {e}")
    
    def _print_final_report(self):
        """打印最终测试报告"""
        self.logger.info("=" * 80)
        self.logger.info("📊 批量健康数据上传优化测试报告")
        self.logger.info("=" * 80)
        
        if self.stats.start_time and self.stats.end_time:
            duration = self.stats.end_time - self.stats.start_time
            self.logger.info(f"⏱️  测试时长: {duration}")
            
            if self.stats.total_records > 0 and duration.total_seconds() > 0:
                records_qps = self.stats.total_records / duration.total_seconds()
                batches_qps = self.stats.total_batches / duration.total_seconds()
                self.logger.info(f"🚀 记录QPS: {records_qps:.2f} 记录/秒")
                self.logger.info(f"📦 批次QPS: {batches_qps:.2f} 批次/秒")
                self.logger.info(f"💪 处理能力: {records_qps * 60:.0f} 记录/分钟")
        
        # 批次统计
        self.logger.info(f"📦 批次统计:")
        self.logger.info(f"   - 总批次数: {self.stats.total_batches}")
        self.logger.info(f"   - 成功批次: {self.stats.successful_batches}")
        self.logger.info(f"   - 失败批次: {self.stats.failed_batches}")
        self.logger.info(f"   - 平均批次大小: {self.stats.total_records / self.stats.total_batches:.1f}" if self.stats.total_batches > 0 else "   - 平均批次大小: 0")
        
        # 记录统计
        self.logger.info(f"📈 记录统计:")
        self.logger.info(f"   - 总记录数: {self.stats.total_records}")
        self.logger.info(f"   - 成功记录: {self.stats.successful_records}")
        self.logger.info(f"   - 失败记录: {self.stats.failed_records}")
        
        # 成功率
        if self.stats.total_records > 0:
            success_rate = (self.stats.successful_records / self.stats.total_records) * 100
            self.logger.info(f"✅ 成功率: {success_rate:.2f}%")
        
        # 批次响应时间统计
        if self.stats.batch_response_times:
            response_times = self.stats.batch_response_times
            self.logger.info(f"⚡ 批次响应时间统计:")
            self.logger.info(f"   - 平均批次时间: {statistics.mean(response_times):.3f}秒")
            self.logger.info(f"   - 最快批次时间: {min(response_times):.3f}秒")
            self.logger.info(f"   - 最慢批次时间: {max(response_times):.3f}秒")
            if len(response_times) >= 20:
                self.logger.info(f"   - 95%批次时间: {statistics.quantiles(response_times, n=20)[18]:.3f}秒")
        
        # 错误详情
        if self.stats.error_details:
            self.logger.info(f"❌ 错误详情:")
            for error_type, count in self.stats.error_details.items():
                self.logger.info(f"   - {error_type}: {count}次")
        
        self._evaluate_batch_performance()
    
    def _evaluate_batch_performance(self):
        """评估批量处理性能"""
        self.logger.info("🎯 批量处理性能评估:")
        
        if not self.stats.batch_response_times or self.stats.total_records == 0:
            self.logger.info("   - 数据不足，无法评估")
            return
        
        success_rate = (self.stats.successful_records / self.stats.total_records) * 100
        avg_batch_time = statistics.mean(self.stats.batch_response_times)
        duration = self.stats.end_time - self.stats.start_time if self.stats.start_time and self.stats.end_time else timedelta(0)
        records_qps = self.stats.total_records / duration.total_seconds() if duration.total_seconds() > 0 else 0
        
        # 批量处理优势分析
        expected_single_qps = 75  # 基于之前单个上传测试的结果
        improvement_ratio = records_qps / expected_single_qps if expected_single_qps > 0 else 0
        
        self.logger.info(f"📈 性能对比分析:")
        self.logger.info(f"   - 批量处理QPS: {records_qps:.1f}")
        self.logger.info(f"   - 单个处理QPS: {expected_single_qps}")
        self.logger.info(f"   - 性能提升倍数: {improvement_ratio:.1f}x")
        
        # 性能等级评估
        performance_grade = "优秀"
        issues = []
        
        if success_rate < 95:
            performance_grade = "需要优化"
            issues.append(f"成功率偏低 ({success_rate:.1f}%)")
        
        if records_qps < 200:
            performance_grade = "需要优化" if performance_grade != "需要优化" else performance_grade
            issues.append(f"QPS仍需提升 ({records_qps:.1f})")
        
        self.logger.info(f"   - 批量处理等级: {performance_grade}")
        if issues:
            self.logger.info(f"   - 发现问题:")
            for issue in issues:
                self.logger.info(f"     * {issue}")
        
        # 优化建议
        if improvement_ratio > 2.0:
            self.logger.info("   ✅ 批量处理优化效果显著!")
        elif improvement_ratio > 1.5:
            self.logger.info("   ✅ 批量处理有明显改善")
        else:
            self.logger.info("   ⚠️ 批量处理优化效果有限，建议进一步优化")

def main():
    """主函数"""
    print("🚀 批量健康数据上传优化测试")
    print("🎯 验证批量插入优化效果")
    print("=" * 60)
    
    import argparse
    parser = argparse.ArgumentParser(description='批量健康数据上传优化测试')
    parser.add_argument('--batch-size', type=int, default=50, help='每批次大小 (默认: 50)')
    parser.add_argument('--concurrent', type=int, default=10, help='并发批次数 (默认: 10)')
    parser.add_argument('--duration', type=int, default=3, help='测试时长(分钟) (默认: 3)')
    parser.add_argument('--url', type=str, default='http://localhost:5225', help='服务URL')
    parser.add_argument('--interval', type=float, default=0.1, help='批次间隔(秒) (默认: 0.1)')
    
    args = parser.parse_args()
    
    config = BatchConfig(
        base_url=args.url,
        batch_size=args.batch_size,
        concurrent_batches=args.concurrent,
        test_duration_minutes=args.duration,
        batch_interval_seconds=args.interval
    )
    
    print(f"📊 批量测试配置:")
    print(f"   - 每批次大小: {config.batch_size}")
    print(f"   - 并发批次数: {config.concurrent_batches}")
    print(f"   - 测试时长: {config.test_duration_minutes}分钟")
    print(f"   - 服务地址: {config.base_url}")
    print(f"   - 批次间隔: {config.batch_interval_seconds}秒")
    print()
    
    try:
        confirm = input("确认开始批量优化测试? (y/N): ").strip().lower()
        if confirm != 'y':
            print("已取消")
            return
    except EOFError:
        print("非交互模式，自动开始测试...")
    
    uploader = BatchHealthUploader(config)
    
    try:
        asyncio.run(uploader.run_batch_stress_test())
    except KeyboardInterrupt:
        print("\n⏸️ 用户中断测试")
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")

if __name__ == "__main__":
    main()
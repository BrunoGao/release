#!/usr/bin/env python3
"""
为系统真实用户生成过去一个月的健康数据
基于 enhanced_health_stress_test.py，通过API接口上传历史数据
"""

import asyncio
import aiohttp
import mysql.connector
import time
import json
import random
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

@dataclass
class DataGeneratorConfig:
    """数据生成器配置"""
    base_url: str = "http://localhost:5225"
    db_config: dict = None
    days_back: int = 30  # 生成过去30天的数据
    records_per_day_per_user: int = 480  # 每用户每天生成480条记录（1分钟间隔）
    concurrent_requests: int = 10  # 并发请求数
    request_interval: float = 0.1  # 请求间隔（秒）
    timeout_seconds: int = 30
    
class MonthlyHealthDataGenerator:
    """月度健康数据生成器"""
    
    def __init__(self, config: DataGeneratorConfig = None):
        self.config = config or DataGeneratorConfig()
        if not self.config.db_config:
            self.config.db_config = {
                'host': '127.0.0.1',
                'port': 3306,
                'database': 'test',
                'user': 'root',
                'password': '123456',
                'charset': 'utf8mb4'
            }
        
        self.user_devices = []
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = log_dir / f"monthly_health_data_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("🚀 月度健康数据API上传器启动")
        self.logger.info(f"📝 日志文件: {log_file}")
        
        # 统计信息
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
    
    def load_real_users_and_devices(self) -> List[Tuple[int, str, str, str, str]]:
        """从数据库加载真实的用户和设备信息"""
        self.logger.info("📊 从数据库加载真实用户和设备信息...")
        
        try:
            connection = mysql.connector.connect(**self.config.db_config)
            cursor = connection.cursor()
            
            # 查询所有有效设备SN的用户
            sql = """
            SELECT id, user_name, device_sn, customer_id, org_id
            FROM sys_user 
            WHERE device_sn IS NOT NULL 
            AND LENGTH(device_sn) > 3 
            ORDER BY id
            """
            
            cursor.execute(sql)
            results = cursor.fetchall()
            
            user_devices = []
            for user_id, user_name, device_sn, customer_id, org_id in results:
                # 如果customer_id或org_id为空，使用默认值
                customer_id = customer_id or "1939964806110937090"
                org_id = org_id or "1939964806110937090"
                user_devices.append((user_id, user_name, device_sn, customer_id, org_id))
            
            self.logger.info(f"✅ 成功加载 {len(user_devices)} 个用户设备信息")
            
            if len(user_devices) > 0:
                self.logger.info(f"   用户ID范围: {user_devices[0][0]} - {user_devices[-1][0]}")
                self.logger.info(f"   设备SN示例: {user_devices[0][2]}")
                self.logger.info(f"   客户ID示例: {user_devices[0][3]}")
                self.logger.info(f"   组织ID示例: {user_devices[0][4]}")
            
            cursor.close()
            connection.close()
            
            return user_devices
            
        except mysql.connector.Error as e:
            self.logger.error(f"❌ 数据库连接失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"❌ 加载用户设备信息失败: {e}")
            return []
    
    def generate_realistic_health_data(self, user_id: int, device_sn: str, customer_id: str, org_id: str, timestamp: datetime) -> Dict[str, Any]:
        """为指定用户和设备生成指定时间的真实健康数据（API格式）"""
        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        # 基于用户ID和时间生成个性化数据（保持一定一致性和时间相关性）
        random.seed(user_id + int(timestamp.timestamp()) // 3600)  # 每小时变化一次基础值
        
        # 时间相关的活动模式
        hour = timestamp.hour
        is_sleep_time = hour < 6 or hour > 22  # 睡眠时间
        is_work_time = 9 <= hour <= 18  # 工作时间
        is_exercise_time = 17 <= hour <= 20  # 运动时间
        
        # 生成真实的健康数据
        if is_sleep_time:
            # 睡眠时间：心率较低，活动量少
            heart_rate = random.randint(50, 70)
            step = random.randint(0, 100)
            stress = random.randint(0, 20)
            calorie = f"{random.uniform(1, 20):.1f}"
            distance = "0.0"
        elif is_exercise_time and random.random() > 0.6:
            # 运动时间：心率较高，活动量大
            heart_rate = random.randint(100, 160)
            step = random.randint(1000, 3000)
            stress = random.randint(20, 50)
            calorie = f"{random.uniform(50, 150):.1f}"
            distance = f"{random.uniform(0.5, 3.0):.1f}"
        elif is_work_time:
            # 工作时间：中等心率，少量活动
            heart_rate = random.randint(70, 95)
            step = random.randint(100, 800)
            stress = random.randint(30, 70)
            calorie = f"{random.uniform(10, 40):.1f}"
            distance = f"{random.uniform(0, 0.5):.1f}"
        else:
            # 其他时间：正常活动
            heart_rate = random.randint(65, 100)
            step = random.randint(200, 1200)
            stress = random.randint(15, 45)
            calorie = f"{random.uniform(20, 60):.1f}"
            distance = f"{random.uniform(0.1, 1.0):.1f}"
        
        # 血氧：大部分时间正常，偶尔无数据
        blood_oxygen = random.randint(95, 100) if random.random() > 0.15 else 0
        
        # 体温：大部分时间无数据，偶尔有正常体温
        body_temperature = "0.0" if random.random() > 0.2 else f"{random.uniform(36.0, 37.5):.1f}"
        
        # 深圳地区GPS坐标（添加一些变化模拟移动）
        base_lat = 22.5 + (user_id % 100) * 0.001  # 基于用户ID的基础位置
        base_lon = 113.9 + (user_id % 100) * 0.001
        latitude = f"{base_lat + random.uniform(-0.01, 0.01):.12f}"
        longitude = f"{base_lon + random.uniform(-0.01, 0.01):.11f}"
        altitude = "0.0" if random.random() > 0.3 else f"{random.uniform(0, 100):.1f}"
        
        # 血压数据：基于年龄和健康状况模拟
        user_base_bp_high = 110 + (user_id % 20)  # 基于用户ID的基础血压
        user_base_bp_low = 70 + (user_id % 15)
        blood_pressure_systolic = user_base_bp_high + random.randint(-10, 15)
        blood_pressure_diastolic = user_base_bp_low + random.randint(-5, 10)
        
        # 确保血压在合理范围内
        blood_pressure_systolic = max(90, min(180, blood_pressure_systolic))
        blood_pressure_diastolic = max(60, min(120, blood_pressure_diastolic))
        
        # 返回API接口格式的数据
        return {
            "data": {
                "deviceSn": device_sn,
                "customerId": customer_id,
                "orgId": org_id,
                "userId": str(user_id),
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
                "sleepData": "null",
                "exerciseDailyData": "null",
                "exerciseWeekData": "null",
                "scientificSleepData": "null",
                "workoutData": "null",
                "timestamp": timestamp_str
            }
        }
    
    async def upload_health_data(self, session: aiohttp.ClientSession, user_id: int, user_name: str, device_sn: str, customer_id: str, org_id: str, timestamp: datetime) -> Dict[str, Any]:
        """上传单个用户的健康数据到API"""
        start_time = time.time()
        
        try:
            health_data = self.generate_realistic_health_data(user_id, device_sn, customer_id, org_id, timestamp)
            url = f"{self.config.base_url}/upload_health_data"
            
            async with session.post(
                url,
                json=health_data,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            ) as response:
                response_time = time.time() - start_time
                response_text = await response.text()
                
                # 更新统计
                self.total_requests += 1
                
                if response.status == 200:
                    self.successful_requests += 1
                    return {
                        'success': True,
                        'user_id': user_id,
                        'user_name': user_name,
                        'device_sn': device_sn,
                        'timestamp': timestamp.isoformat(),
                        'response_time': response_time,
                        'status_code': response.status
                    }
                else:
                    self.failed_requests += 1
                    self.logger.warning(f"❌ 上传失败 - 用户: {user_name}, 状态码: {response.status}, 响应: {response_text[:100]}")
                    return {
                        'success': False,
                        'user_id': user_id,
                        'user_name': user_name,
                        'device_sn': device_sn,
                        'timestamp': timestamp.isoformat(),
                        'response_time': response_time,
                        'status_code': response.status,
                        'error': response_text[:100]
                    }
                
        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            self.total_requests += 1
            self.failed_requests += 1
            self.logger.warning(f"⏰ 上传超时 - 用户: {user_name}, 时间戳: {timestamp}")
            return {
                'success': False,
                'user_id': user_id,
                'user_name': user_name,
                'device_sn': device_sn,
                'timestamp': timestamp.isoformat(),
                'response_time': response_time,
                'error': 'TIMEOUT'
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            self.total_requests += 1
            self.failed_requests += 1
            self.logger.error(f"💥 上传异常 - 用户: {user_name}, 错误: {e}")
            return {
                'success': False,
                'user_id': user_id,
                'user_name': user_name,
                'device_sn': device_sn,
                'timestamp': timestamp.isoformat(),
                'response_time': response_time,
                'error': str(e)
            }
    
    async def generate_monthly_data(self):
        """生成过去一个月的健康数据并通过API上传"""
        self.logger.info("🚀 开始生成过去一个月的健康数据并上传")
        
        # 加载真实用户设备信息
        self.user_devices = self.load_real_users_and_devices()
        if not self.user_devices:
            self.logger.error("❌ 无法加载用户设备信息，生成终止")
            return
        
        self.logger.info(f"📊 生成配置:")
        self.logger.info(f"   - 用户数量: {len(self.user_devices)}")
        self.logger.info(f"   - 生成天数: {self.config.days_back} 天")
        self.logger.info(f"   - 每用户每天记录数: {self.config.records_per_day_per_user}")
        self.logger.info(f"   - 并发请求数: {self.config.concurrent_requests}")
        self.logger.info(f"   - 请求间隔: {self.config.request_interval} 秒")
        self.logger.info(f"   - API地址: {self.config.base_url}")
        
        total_records = len(self.user_devices) * self.config.days_back * self.config.records_per_day_per_user
        self.logger.info(f"   - 预计上传总记录数: {total_records:,}")
        
        # 计算时间范围
        end_time = datetime.now()
        start_time = end_time - timedelta(days=self.config.days_back)
        
        self.logger.info(f"⏰ 时间范围: {start_time.strftime('%Y-%m-%d %H:%M:%S')} 到 {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 创建HTTP会话
        connector = aiohttp.TCPConnector(
            limit=self.config.concurrent_requests * 2,
            limit_per_host=self.config.concurrent_requests,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds),
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'MonthlyHealthDataGenerator/1.0'
            }
        ) as session:
            try:
                # 生成所有需要上传的数据点
                upload_tasks = []
                
                for user_idx, (user_id, user_name, device_sn, customer_id, org_id) in enumerate(self.user_devices):
                    self.logger.info(f"👤 准备用户 {user_idx + 1}/{len(self.user_devices)}: {user_name} ({device_sn})")
                    
                    # 计算该用户的时间间隔 - 仅在8小时工作时间内生成数据
                    # 8小时 = 480分钟，每分钟1条记录 = 480条/天
                    work_start_hour = 9  # 9:00开始工作
                    work_hours = 8  # 工作8小时
                    interval_minutes = 1  # 每分钟1条记录
                    
                    # 为该用户生成工作时间内的时间戳
                    user_timestamps = []
                    current_date = start_time.date()
                    
                    while current_date <= end_time.date():
                        # 每天在工作时间内生成数据（9:00-17:00，8小时）
                        work_start = datetime.combine(current_date, datetime.min.time().replace(hour=work_start_hour))
                        work_end = work_start + timedelta(hours=work_hours)
                        
                        # 在工作时间内每分钟生成一条记录
                        current_work_time = work_start
                        while current_work_time < work_end:
                            if current_work_time >= start_time and current_work_time < end_time:
                                user_timestamps.append(current_work_time)
                            current_work_time += timedelta(minutes=interval_minutes)
                        
                        # 下一天
                        current_date += timedelta(days=1)
                    
                    self.logger.info(f"   📅 用户 {user_name} 将上传 {len(user_timestamps)} 条记录")
                    
                    # 为该用户的所有时间点创建上传任务
                    for timestamp in user_timestamps:
                        task = self.upload_health_data(session, user_id, user_name, device_sn, customer_id, org_id, timestamp)
                        upload_tasks.append(task)
                
                self.logger.info(f"🚀 开始上传 {len(upload_tasks)} 条健康数据记录...")
                
                # 启动监控任务
                monitor_task = asyncio.create_task(self._monitor_upload_progress())
                
                # 分批并发执行上传任务
                batch_size = self.config.concurrent_requests
                for i in range(0, len(upload_tasks), batch_size):
                    batch = upload_tasks[i:i + batch_size]
                    
                    # 执行当前批次
                    results = await asyncio.gather(*batch, return_exceptions=True)
                    
                    # 统计结果
                    successful_in_batch = sum(1 for r in results if isinstance(r, dict) and r.get('success', False))
                    failed_in_batch = len(batch) - successful_in_batch
                    
                    self.logger.info(f"📊 批次 {i//batch_size + 1}: 成功 {successful_in_batch}, 失败 {failed_in_batch}")
                    
                    # 控制请求频率
                    if i + batch_size < len(upload_tasks):
                        await asyncio.sleep(self.config.request_interval)
                
                # 停止监控
                monitor_task.cancel()
                try:
                    await monitor_task
                except asyncio.CancelledError:
                    pass
                
            except Exception as e:
                self.logger.error(f"❌ 上传过程异常: {e}")
        
        # 打印最终报告
        self._print_final_report()
    
    async def _monitor_upload_progress(self):
        """监控上传进度"""
        last_requests = 0
        
        while True:
            try:
                await asyncio.sleep(10)  # 每10秒报告一次
                
                current_requests = self.total_requests
                successful = self.successful_requests
                failed = self.failed_requests
                
                # 计算QPS
                requests_delta = current_requests - last_requests
                qps = requests_delta / 10.0
                
                # 计算成功率
                success_rate = (successful / current_requests * 100) if current_requests > 0 else 0
                
                self.logger.info(
                    f"📊 上传进度 - "
                    f"总请求: {current_requests}, "
                    f"成功: {successful}, "
                    f"失败: {failed}, "
                    f"成功率: {success_rate:.1f}%, "
                    f"QPS: {qps:.1f}"
                )
                
                last_requests = current_requests
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"监控进度异常: {e}")
    
    def _print_final_report(self):
        """打印最终上传报告"""
        self.logger.info("=" * 80)
        self.logger.info("🎉 月度健康数据上传完成")
        self.logger.info("=" * 80)
        
        # 用户统计
        self.logger.info(f"👥 用户统计:")
        self.logger.info(f"   - 参与用户数: {len(self.user_devices)}")
        if self.user_devices:
            self.logger.info(f"   - 用户ID范围: {self.user_devices[0][0]} - {self.user_devices[-1][0]}")
            self.logger.info(f"   - 设备SN范围: {self.user_devices[0][2]} - {self.user_devices[-1][2]}")
        
        # 请求统计
        self.logger.info(f"📈 请求统计:")
        self.logger.info(f"   - 总请求数: {self.total_requests}")
        self.logger.info(f"   - 成功请求: {self.successful_requests}")
        self.logger.info(f"   - 失败请求: {self.failed_requests}")
        
        # 成功率
        if self.total_requests > 0:
            success_rate = (self.successful_requests / self.total_requests) * 100
            self.logger.info(f"✅ 成功率: {success_rate:.2f}%")
        
        # 配置信息
        self.logger.info(f"⚙️  配置信息:")
        self.logger.info(f"   - 时间跨度: {self.config.days_back} 天")
        self.logger.info(f"   - 每用户每天记录数: {self.config.records_per_day_per_user}")
        self.logger.info(f"   - API地址: {self.config.base_url}")
        
        if success_rate >= 95:
            self.logger.info("🎯 上传质量: 优秀")
        elif success_rate >= 80:
            self.logger.info("🟡 上传质量: 良好")
        else:
            self.logger.info("⚠️ 上传质量: 需要检查")

def main():
    """主函数"""
    print("🚀 月度健康数据API上传器")
    print("🎯 为系统真实用户生成过去一个月的健康数据并通过API上传")
    print("=" * 60)
    
    import argparse
    parser = argparse.ArgumentParser(description='月度健康数据API上传器')
    parser.add_argument('--days', type=int, default=30, help='生成过去几天的数据 (默认: 30)')
    parser.add_argument('--records-per-day', type=int, default=480, help='每用户每天记录数 (默认: 480，1分钟间隔)')
    parser.add_argument('--concurrent', type=int, default=10, help='并发请求数 (默认: 10)')
    parser.add_argument('--interval', type=float, default=0.1, help='批次间隔时间(秒) (默认: 0.1)')
    parser.add_argument('--url', type=str, default='http://localhost:5225', help='API服务地址 (默认: http://localhost:5225)')
    
    args = parser.parse_args()
    
    config = DataGeneratorConfig(
        base_url=args.url,
        days_back=args.days,
        records_per_day_per_user=args.records_per_day,
        concurrent_requests=args.concurrent,
        request_interval=args.interval
    )
    
    print(f"📊 上传配置:")
    print(f"   - 生成天数: {config.days_back}")
    print(f"   - 每用户每天记录数: {config.records_per_day_per_user}")
    print(f"   - 并发请求数: {config.concurrent_requests}")
    print(f"   - 批次间隔: {config.request_interval} 秒")
    print(f"   - API地址: {config.base_url}")
    print()
    
    try:
        confirm = input("确认开始上传数据? (y/N): ").strip().lower()
        if confirm != 'y':
            print("已取消")
            return
    except EOFError:
        # 非交互模式，直接开始上传
        print("非交互模式，自动开始上传...")
        pass
    
    generator = MonthlyHealthDataGenerator(config)
    
    try:
        asyncio.run(generator.generate_monthly_data())
    except KeyboardInterrupt:
        print("\n⏸️ 用户中断上传")
    except Exception as e:
        print(f"\n❌ 上传异常: {e}")

if __name__ == "__main__":
    main()
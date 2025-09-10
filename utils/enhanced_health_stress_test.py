#!/usr/bin/env python3
"""
增强版健康数据压力测试
使用1000个真实创建的sys_user进行压力测试
"""

import asyncio
import aiohttp
import time
import json
import random
import logging
import sys
import mysql.connector
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import statistics

@dataclass
class TestConfig:
    """测试配置"""
    base_url: str = "http://localhost:5225"
    concurrent_requests: int = 100
    test_duration_minutes: int = 5
    upload_interval_seconds: float = 0.5
    timeout_seconds: int = 30
    verbose_json: bool = False  # 是否打印详细JSON数据
    db_config: dict = None

@dataclass
class TestStats:
    """测试统计"""
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

class EnhancedHealthStressTester:
    """增强版健康数据压力测试器"""
    
    def __init__(self, config: TestConfig = None):
        self.config = config or TestConfig()
        if not self.config.db_config:
            self.config.db_config = {
                'host': '127.0.0.1',
                'port': 3306,
                'database': 'test',
                'user': 'root',
                'password': '123456',
                'charset': 'utf8mb4'
            }
        
        self.stats = TestStats()
        self.running = False
        self.user_devices = []
        
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = log_dir / f"enhanced_health_test_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("🚀 增强版健康数据压力测试开始")
        self.logger.info(f"📝 日志文件: {log_file}")
    
    def load_real_users_and_devices(self) -> List[Tuple[int, str, str, str, str]]:
        """从数据库加载真实的用户和设备信息（包含customerId和orgId）"""
        self.logger.info("📊 从数据库加载真实用户和设备信息...")
        
        try:
            connection = mysql.connector.connect(**self.config.db_config)
            cursor = connection.cursor()
            
            # 查询所有创建的测试用户及其设备SN、客户ID、组织ID
            sql = """
            SELECT id, user_name, device_sn, customer_id, org_id
            FROM sys_user 
            WHERE user_name LIKE 'CRFTQ23409%' 
            AND device_sn IS NOT NULL
            ORDER BY id
            LIMIT 1000
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
    
    def generate_realistic_health_data(self, user_id: int, device_sn: str, customer_id: str, org_id: str) -> Dict[str, Any]:
        """为指定用户和设备生成真实的健康数据（新接口格式）"""
        timestamp = datetime.now()
        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        # 基于用户ID生成个性化数据（保持一定一致性）
        random.seed(user_id + int(timestamp.timestamp()) // 3600)  # 每小时变化一次
        
        # 生成真实的健康数据
        heart_rate = random.randint(60, 120)
        blood_oxygen = random.randint(95, 100) if random.random() > 0.1 else 0
        body_temperature = "0.0" if random.random() > 0.3 else f"{random.uniform(36.0, 37.5):.1f}"
        
        # 运动数据
        is_active = random.random() > 0.4
        step = random.randint(0, 15000) if is_active else random.randint(0, 3000)
        distance = f"{random.uniform(0, 12):.1f}" if is_active else "0.0"
        calorie = f"{random.uniform(100, 600):.1f}" if is_active else f"{random.uniform(50, 200):.1f}"
        
        # 深圳地区GPS坐标
        latitude = f"{random.uniform(22.5, 22.6):.12f}"
        longitude = f"{random.uniform(113.9, 114.1):.11f}"
        altitude = "0.0" if random.random() > 0.5 else f"{random.uniform(0, 100):.1f}"
        
        # 压力和血压数据
        stress = random.randint(0, 100)
        blood_pressure_systolic = random.randint(110, 140)
        blood_pressure_diastolic = random.randint(70, 90)
        
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
    
    def generate_realistic_device_info(self, user_id: int, device_sn: str, customer_id: str, org_id: str) -> Dict[str, Any]:
        """生成设备信息数据"""
        timestamp = datetime.now()
        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        # 基于设备SN生成一致的设备信息
        device_hash = hash(device_sn) % 1000000
        random.seed(device_hash)
        
        # 生成运动手表类设备信息
        mac_base = f"d4:bb:e6:{random.randint(10,99):02x}:{random.randint(10,99):02x}:{random.randint(10,99):02x}"
        bluetooth_mac = f"D4:BB:E6:{random.randint(10,99):02x}:{random.randint(10,99):02x}:{random.randint(10,99):02x}"
        ip_address = f"192.168.1.{random.randint(100,250)}"
        imei = f"86615206{random.randint(10000000,99999999)}"
        battery_level = random.randint(20, 100)
        voltage = random.randint(3800, 4200)
        
        return {
            "data": {
                "System Software Version": "GLL-AL30BCN 3.0.0.900(SP51C700E106R370P324)",
                "Wifi Address": mac_base,
                "Bluetooth Address": bluetooth_mac,
                "IP Address": ip_address,
                "Network Access Mode": random.choice([1, 2, 3]),  # 1=wifi, 2=4g, 3=bluetooth
                "SerialNumber": device_sn,
                "Device Name": "HUAWEI WATCH B7-536-BF0",
                "IMEI": imei,
                "batteryLevel": battery_level,
                "voltage": voltage,
                "chargingStatus": random.choice(["NONE", "CHARGING", "FULL"]),
                "status": "ACTIVE",
                "timestamp": timestamp_str,
                "wearState": random.choice([0, 1]),  # 0=未佩戴, 1=佩戴
                "customerId": customer_id,
                "orgId": org_id,
                "userId": str(user_id)
            }
        }
    
    async def upload_health_data(self, session: aiohttp.ClientSession, user_id: int, user_name: str, device_sn: str, customer_id: str, org_id: str) -> Dict[str, Any]:
        """上传单个用户的健康数据"""
        start_time = time.time()
        
        try:
            health_data = self.generate_realistic_health_data(user_id, device_sn, customer_id, org_id)
            url = f"{self.config.base_url}/upload_health_data"
            
            if self.config.verbose_json:
                self.logger.info(f"🏥 upload_health_data - {device_sn}: {json.dumps(health_data, indent=2, ensure_ascii=False)}")
            
            async with session.post(
                url,
                json=health_data,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            ) as response:
                response_time = time.time() - start_time
                response_text = await response.text()
                
                # 更新统计
                self.stats.total_requests += 1
                self.stats.response_times.append(response_time)
                
                if response.status == 200:
                    self.stats.successful_requests += 1
                else:
                    self.stats.failed_requests += 1
                    error_key = f"HTTP_{response.status}"
                    self.stats.error_details[error_key] = self.stats.error_details.get(error_key, 0) + 1
                
                return {
                    'user_id': user_id,
                    'user_name': user_name,
                    'device_sn': device_sn,
                    'api_type': 'health_data',
                    'success': response.status == 200,
                    'status_code': response.status,
                    'response_time': response_time,
                    'response_text': response_text[:100],
                    'timestamp': datetime.now().isoformat()
                }
                
        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            self.stats.total_requests += 1
            self.stats.timeout_requests += 1
            self.stats.response_times.append(response_time)
            self.stats.error_details['TIMEOUT'] = self.stats.error_details.get('TIMEOUT', 0) + 1
            
            return {
                'user_id': user_id,
                'user_name': user_name,
                'device_sn': device_sn,
                'api_type': 'health_data',
                'success': False,
                'error': 'TIMEOUT',
                'response_time': response_time,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            self.stats.total_requests += 1
            self.stats.failed_requests += 1
            error_key = type(e).__name__
            self.stats.error_details[error_key] = self.stats.error_details.get(error_key, 0) + 1
            self.stats.response_times.append(response_time)
            
            return {
                'user_id': user_id,
                'user_name': user_name,
                'device_sn': device_sn,
                'api_type': 'health_data',
                'success': False,
                'error': str(e),
                'response_time': response_time,
                'timestamp': datetime.now().isoformat()
            }
    
    async def upload_device_info(self, session: aiohttp.ClientSession, user_id: int, user_name: str, device_sn: str, customer_id: str, org_id: str) -> Dict[str, Any]:
        """上传单个用户的设备信息"""
        start_time = time.time()
        
        try:
            device_info = self.generate_realistic_device_info(user_id, device_sn, customer_id, org_id)
            url = f"{self.config.base_url}/upload_device_info"
            
            if self.config.verbose_json:
                self.logger.info(f"📱 upload_device_info - {device_sn}: {json.dumps(device_info, indent=2, ensure_ascii=False)}")
            
            async with session.post(
                url,
                json=device_info,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            ) as response:
                response_time = time.time() - start_time
                response_text = await response.text()
                
                # 更新统计
                self.stats.total_requests += 1
                self.stats.response_times.append(response_time)
                
                if response.status == 200:
                    self.stats.successful_requests += 1
                else:
                    self.stats.failed_requests += 1
                    error_key = f"HTTP_{response.status}"
                    self.stats.error_details[error_key] = self.stats.error_details.get(error_key, 0) + 1
                
                return {
                    'user_id': user_id,
                    'user_name': user_name,
                    'device_sn': device_sn,
                    'api_type': 'device_info',
                    'success': response.status == 200,
                    'status_code': response.status,
                    'response_time': response_time,
                    'response_text': response_text[:100],
                    'timestamp': datetime.now().isoformat()
                }
                
        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            self.stats.total_requests += 1
            self.stats.timeout_requests += 1
            self.stats.response_times.append(response_time)
            self.stats.error_details['TIMEOUT'] = self.stats.error_details.get('TIMEOUT', 0) + 1
            
            return {
                'user_id': user_id,
                'user_name': user_name,
                'device_sn': device_sn,
                'api_type': 'device_info',
                'success': False,
                'error': 'TIMEOUT',
                'response_time': response_time,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            self.stats.total_requests += 1
            self.stats.failed_requests += 1
            error_key = type(e).__name__
            self.stats.error_details[error_key] = self.stats.error_details.get(error_key, 0) + 1
            self.stats.response_times.append(response_time)
            
            return {
                'user_id': user_id,
                'user_name': user_name,
                'device_sn': device_sn,
                'api_type': 'device_info',
                'success': False,
                'error': str(e),
                'response_time': response_time,
                'timestamp': datetime.now().isoformat()
            }
    
    async def run_stress_test(self):
        """运行压力测试"""
        self.logger.info("🔥 开始1000用户真实健康数据双接口压力测试")
        
        # 加载真实用户设备信息
        self.user_devices = self.load_real_users_and_devices()
        if not self.user_devices:
            self.logger.error("❌ 无法加载用户设备信息，测试终止")
            return
        
        self.logger.info(f"📊 测试配置:")
        self.logger.info(f"   - 真实用户数: {len(self.user_devices)}")
        self.logger.info(f"   - 并发数: {self.config.concurrent_requests}")
        self.logger.info(f"   - 测试时长: {self.config.test_duration_minutes}分钟")
        self.logger.info(f"   - 上传间隔: {self.config.upload_interval_seconds}秒")
        self.logger.info(f"   - 目标URL: {self.config.base_url}")
        self.logger.info(f"   - API接口: upload_health_data + upload_device_info")
        self.logger.info(f"   - 预期QPS: {len(self.user_devices) * 2 / self.config.upload_interval_seconds:.1f} (每用户双接口)")
        
        self.running = True
        self.stats.start_time = datetime.now()
        
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
                'User-Agent': 'EnhancedHealthStressTester/1.0'
            }
        ) as session:
            # 启动监控任务
            monitor_task = asyncio.create_task(self._monitor_progress())
            
            try:
                tasks = []
                end_time = datetime.now() + timedelta(minutes=self.config.test_duration_minutes)
                
                while datetime.now() < end_time and self.running:
                    # 随机选择用户进行上传
                    selected_users = random.sample(
                        self.user_devices,
                        min(self.config.concurrent_requests // 2, len(self.user_devices))  # 每个用户需要两个请求
                    )
                    
                    for user_id, user_name, device_sn, customer_id, org_id in selected_users:
                        if len(tasks) >= self.config.concurrent_requests:
                            # 等待部分任务完成
                            done, pending = await asyncio.wait(
                                tasks,
                                timeout=0.1,
                                return_when=asyncio.FIRST_COMPLETED
                            )
                            tasks = list(pending)
                        
                        # 同时上传健康数据和设备信息
                        health_task = asyncio.create_task(
                            self.upload_health_data(session, user_id, user_name, device_sn, customer_id, org_id)
                        )
                        device_task = asyncio.create_task(
                            self.upload_device_info(session, user_id, user_name, device_sn, customer_id, org_id)
                        )
                        tasks.extend([health_task, device_task])
                    
                    # 控制上传频率
                    await asyncio.sleep(self.config.upload_interval_seconds)
                
                # 等待剩余任务完成
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
                await asyncio.sleep(10)  # 每10秒报告一次
                
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
                    avg_response_time = statistics.mean(self.stats.response_times[-100:])
                
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
        self.logger.info("📊 1000用户真实健康数据双接口压力测试报告")
        self.logger.info("=" * 80)
        
        if self.stats.start_time and self.stats.end_time:
            duration = self.stats.end_time - self.stats.start_time
            self.logger.info(f"⏱️  测试时长: {duration}")
            
            if self.stats.total_requests > 0 and duration.total_seconds() > 0:
                qps = self.stats.total_requests / duration.total_seconds()
                self.logger.info(f"🚀 整体QPS: {qps:.2f} 请求/秒")
                self.logger.info(f"💪 处理能力: {qps * 60:.0f} 请求/分钟")
        
        # 测试用户统计
        self.logger.info(f"👥 用户统计:")
        self.logger.info(f"   - 参与测试用户数: {len(self.user_devices)}")
        if self.user_devices:
            self.logger.info(f"   - 用户ID范围: {self.user_devices[0][0]} - {self.user_devices[-1][0]}")
            self.logger.info(f"   - 设备SN范围: {self.user_devices[0][2]} - {self.user_devices[-1][2]}")
            self.logger.info(f"   - 客户ID: {self.user_devices[0][3]}")
            self.logger.info(f"   - 组织ID: {self.user_devices[0][4]}")
        
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
            if len(response_times) >= 20:
                self.logger.info(f"   - 95%响应时间: {statistics.quantiles(response_times, n=20)[18]:.3f}秒")
        
        # 错误详情
        if self.stats.error_details:
            self.logger.info(f"❌ 错误详情:")
            for error_type, count in self.stats.error_details.items():
                self.logger.info(f"   - {error_type}: {count}次")
        
        self._evaluate_performance()
    
    def _evaluate_performance(self):
        """评估系统性能"""
        self.logger.info("🎯 系统性能评估:")
        
        if not self.stats.response_times or self.stats.total_requests == 0:
            self.logger.info("   - 数据不足，无法评估")
            return
        
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
        
        if avg_response_time > 1.0:
            performance_grade = "需要优化" if performance_grade != "需要优化" else performance_grade
            issues.append(f"响应时间偏慢 ({avg_response_time:.3f}s)")
        
        if qps < 400:  # 双接口模式需要更高的QPS
            performance_grade = "需要优化" if performance_grade != "需要优化" else performance_grade
            issues.append(f"QPS偏低 ({qps:.1f})")
        
        self.logger.info(f"   - 性能等级: {performance_grade}")
        if issues:
            self.logger.info(f"   - 发现问题:")
            for issue in issues:
                self.logger.info(f"     * {issue}")
        
        # 系统性能对比
        self.logger.info("🆚 性能基准对比:")
        self.logger.info("   目标性能指标（双接口模式）:")
        self.logger.info("   - 目标QPS: 600+ 请求/秒 (300+ health_data + 300+ device_info)")
        self.logger.info("   - 目标响应时间: <0.5秒")
        self.logger.info("   - 目标成功率: >98%")
        self.logger.info("   - 并发处理能力: 1000+ 真实用户 x 2接口")
        
        if qps >= 600:
            self.logger.info("   ✅ QPS达标！系统性能优秀")
        elif qps >= 300:
            self.logger.info(f"   🟡 QPS部分达标，当前: {qps:.1f}, 目标: 600+")
        else:
            self.logger.info(f"   ⚠️ QPS未达标，当前: {qps:.1f}, 目标: 600+")

def main():
    """主函数"""
    print("🚀 增强版健康数据压力测试")
    print("🎯 使用1000个真实sys_user进行压力测试")
    print("🔗 同时测试upload_health_data和upload_device_info接口")
    print("=" * 60)
    
    import argparse
    parser = argparse.ArgumentParser(description='增强版健康数据压力测试')
    parser.add_argument('--concurrent', type=int, default=100, help='并发数 (默认: 100)')
    parser.add_argument('--duration', type=int, default=5, help='测试时长(分钟) (默认: 5)')
    parser.add_argument('--url', type=str, default='http://localhost:5225', help='服务URL')
    parser.add_argument('--interval', type=float, default=0.5, help='上传间隔(秒) (默认: 0.5)')
    parser.add_argument('--verbose', action='store_true', help='打印详细JSON数据')
    
    args = parser.parse_args()
    
    config = TestConfig(
        base_url=args.url,
        concurrent_requests=args.concurrent,
        test_duration_minutes=args.duration,
        upload_interval_seconds=args.interval,
        verbose_json=args.verbose
    )
    
    print(f"📊 测试配置:")
    print(f"   - 并发数: {config.concurrent_requests}")
    print(f"   - 测试时长: {config.test_duration_minutes}分钟")
    print(f"   - 服务地址: {config.base_url}")
    print(f"   - 上传间隔: {config.upload_interval_seconds}秒")
    print()
    
    try:
        confirm = input("确认开始压力测试? (y/N): ").strip().lower()
        if confirm != 'y':
            print("已取消")
            return
    except EOFError:
        # 非交互模式，直接开始测试
        print("非交互模式，自动开始测试...")
        pass
    
    tester = EnhancedHealthStressTester(config)
    
    try:
        asyncio.run(tester.run_stress_test())
    except KeyboardInterrupt:
        print("\n⏸️ 用户中断测试")
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")

if __name__ == "__main__":
    main()
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
            AND is_deleted = 0
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

        # 获取当天开始时间和分钟数（用于累积数据）
        day_start = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
        minutes_since_midnight = int((timestamp - day_start).total_seconds() / 60)
        
        # 使用更细粒度的随机种子，但保持一定的连续性
        base_seed = user_id + int(day_start.timestamp())
        minute_seed = base_seed + minutes_since_midnight
        random.seed(minute_seed)

        # 时间相关的活动模式
        hour = timestamp.hour
        minute = timestamp.minute
        is_sleep_time = hour < 6 or hour > 22  # 睡眠时间
        is_work_time = 9 <= hour <= 18  # 工作时间
        is_exercise_time = 17 <= hour <= 20  # 运动时间
        is_commute_time = (7 <= hour <= 8) or (18 <= hour <= 19)  # 通勤时间

        # 用户个性化基础值（基于用户ID）
        user_fitness_level = (user_id % 5) + 1  # 1-5 健身水平
        user_age_factor = 1.0 - ((user_id % 50) / 200.0)  # 年龄因子 0.75-1.0
        user_base_hr = 65 + (user_id % 15)  # 基础心率 65-80

        # === 累积数据计算 (步数、卡路里、距离) ===
        # 每天累积，基于时间段和活动强度
        daily_step_increment = 0
        daily_calorie_increment = 0.0
        daily_distance_increment = 0.0

        if not is_sleep_time:  # 非睡眠时间才有活动
            if is_exercise_time:
                # 运动时间：高活动量
                step_per_minute = random.randint(80, 150) * user_fitness_level
                calorie_per_minute = random.uniform(8, 15) * user_fitness_level
                distance_per_minute = random.uniform(0.05, 0.12) * user_fitness_level
            elif is_commute_time:
                # 通勤时间：中等活动量
                step_per_minute = random.randint(40, 80)
                calorie_per_minute = random.uniform(3, 6)
                distance_per_minute = random.uniform(0.02, 0.05)
            elif is_work_time:
                # 工作时间：低活动量
                step_per_minute = random.randint(5, 25)
                calorie_per_minute = random.uniform(1, 3)
                distance_per_minute = random.uniform(0.001, 0.01)
            else:
                # 其他时间：中低活动量
                step_per_minute = random.randint(15, 50)
                calorie_per_minute = random.uniform(2, 5)
                distance_per_minute = random.uniform(0.005, 0.03)
            
            daily_step_increment = step_per_minute
            daily_calorie_increment = calorie_per_minute
            daily_distance_increment = distance_per_minute

        # 计算当日累积值
        total_minutes_active = max(0, minutes_since_midnight - 360)  # 6点后开始活动
        
        # 模拟一天中的累积增长（使用二次函数让增长更自然）
        progress_factor = min(1.0, total_minutes_active / 960.0)  # 16小时活跃时间
        
        # 当日累积步数（带随机波动）
        base_daily_steps = int(5000 + user_fitness_level * 2000 + 
                              progress_factor * progress_factor * 3000 * user_fitness_level)
        step = base_daily_steps + daily_step_increment + random.randint(-100, 100)
        step = max(0, step)

        # 当日累积卡路里（基于步数和用户特征）
        base_daily_calories = step * 0.04 * user_age_factor + daily_calorie_increment
        calorie = f"{max(0, base_daily_calories + random.uniform(-10, 10)):.1f}"

        # 当日累积距离（基于步数）
        base_daily_distance = step * 0.0006 + daily_distance_increment  # 平均步长60cm
        distance = f"{max(0, base_daily_distance + random.uniform(-0.1, 0.1)):.2f}"

        # === 瞬时生理数据 ===
        # 心率：基于活动强度和个人基础值
        if is_sleep_time:
            heart_rate = int(user_base_hr * 0.8 + random.randint(-5, 5))  # 睡眠心率
        elif is_exercise_time and random.random() > 0.3:
            heart_rate = int(user_base_hr * 1.6 + random.randint(-10, 20))  # 运动心率
        elif is_commute_time:
            heart_rate = int(user_base_hr * 1.2 + random.randint(-8, 12))  # 通勤心率
        else:
            heart_rate = int(user_base_hr + random.randint(-10, 15))  # 正常心率
        
        heart_rate = max(45, min(180, heart_rate))

        # 血氧：大部分时间正常，偶有波动
        if random.random() > 0.1:
            blood_oxygen = random.randint(96, 100)
            if is_exercise_time:
                blood_oxygen = max(94, blood_oxygen - random.randint(0, 3))
        else:
            blood_oxygen = 0  # 未测量

        # 体温：真实的体温变化模式
        if random.random() > 0.7:  # 30%概率测量体温
            base_temp = 36.5
            if is_exercise_time:
                base_temp += random.uniform(0.3, 0.8)  # 运动升温
            elif is_sleep_time:
                base_temp -= random.uniform(0.1, 0.3)  # 睡眠降温
            body_temperature = f"{base_temp + random.uniform(-0.2, 0.2):.1f}"
        else:
            body_temperature = "0.0"

        # 压力指数：基于时间和活动
        if is_sleep_time:
            stress = random.randint(10, 25)
        elif is_work_time:
            stress = random.randint(40, 70)
        elif is_exercise_time:
            stress = random.randint(20, 50)
        else:
            stress = random.randint(25, 45)

        # 血压：基于个人基础值和当前状态
        user_base_bp_high = 110 + (user_id % 20)
        user_base_bp_low = 70 + (user_id % 15)
        
        if is_exercise_time:
            bp_high_mod = random.randint(10, 25)
            bp_low_mod = random.randint(5, 15)
        elif is_sleep_time:
            bp_high_mod = random.randint(-15, -5)
            bp_low_mod = random.randint(-10, -3)
        else:
            bp_high_mod = random.randint(-5, 10)
            bp_low_mod = random.randint(-3, 8)
            
        blood_pressure_systolic = max(90, min(180, user_base_bp_high + bp_high_mod))
        blood_pressure_diastolic = max(60, min(120, user_base_bp_low + bp_low_mod))

        # GPS坐标：真实的移动轨迹模拟
        user_home_lat = 22.5 + (user_id % 50) * 0.002  # 用户家庭位置
        user_home_lon = 113.9 + (user_id % 50) * 0.002
        
        if is_sleep_time:
            # 睡眠时间：在家
            latitude = f"{user_home_lat + random.uniform(-0.001, 0.001):.6f}"
            longitude = f"{user_home_lon + random.uniform(-0.001, 0.001):.6f}"
        elif is_work_time:
            # 工作时间：在办公区域
            work_lat = user_home_lat + 0.01 + (user_id % 10) * 0.005
            work_lon = user_home_lon + 0.01 + (user_id % 10) * 0.005
            latitude = f"{work_lat + random.uniform(-0.002, 0.002):.6f}"
            longitude = f"{work_lon + random.uniform(-0.002, 0.002):.6f}"
        elif is_commute_time:
            # 通勤时间：在路上
            progress = random.random()
            lat = user_home_lat + progress * 0.01
            lon = user_home_lon + progress * 0.01
            latitude = f"{lat + random.uniform(-0.005, 0.005):.6f}"
            longitude = f"{lon + random.uniform(-0.005, 0.005):.6f}"
        else:
            # 其他时间：随机位置
            latitude = f"{user_home_lat + random.uniform(-0.02, 0.02):.6f}"
            longitude = f"{user_home_lon + random.uniform(-0.02, 0.02):.6f}"
        
        altitude = "0.0" if random.random() > 0.4 else f"{random.uniform(5, 120):.1f}"

        # === 生成复杂数据结构 ===
        # 睡眠数据 - 仿照workoutData格式，但用于睡眠
        sleep_data = self.generate_sleep_data(timestamp, is_sleep_time)
        
        # 运动日数据
        exercise_daily_data = self.generate_exercise_daily_data(timestamp, daily_calorie_increment)
        
        # 运动周数据
        exercise_week_data = self.generate_exercise_week_data(timestamp, user_fitness_level, step)
        
        # 锻炼数据
        workout_data = self.generate_workout_data(timestamp, is_exercise_time, user_fitness_level)

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
                "upload_method": random.choice(["wifi", "esim", "bluetooth"]),
                "blood_pressure_systolic": blood_pressure_systolic,
                "blood_pressure_diastolic": blood_pressure_diastolic,
                "sleepData": sleep_data,
                "exerciseDailyData": exercise_daily_data,
                "exerciseWeekData": exercise_week_data,
                "scientificSleepData": "null",
                "workoutData": workout_data,
                "timestamp": timestamp_str
            }
        }

    def generate_sleep_data(self, timestamp: datetime, is_sleep_time: bool) -> str:
        """生成睡眠数据，基于用户提供的新格式"""
        # 100%概率生成睡眠数据用于测试
        
        # 生成1-3个睡眠阶段数据
        sleep_sessions = []
        session_count = random.randint(1, 3)
        
        base_timestamp = int(timestamp.timestamp() * 1000)
        
        for i in range(session_count):
            # 睡眠时长：1-4小时
            sleep_duration_minutes = random.randint(60, 240)
            sleep_duration_ms = sleep_duration_minutes * 60 * 1000
            
            # 起始时间：在当前时间前后浮动
            start_offset = random.randint(-120, 60) * 60 * 1000  # 前2小时到后1小时
            start_timestamp = base_timestamp + start_offset + (i * sleep_duration_ms)
            end_timestamp = start_timestamp + sleep_duration_ms
            
            # 睡眠类型：1=深度睡眠, 2=浅度睡眠, 3=快速眼动睡眠
            sleep_type = random.choice([1, 2, 3])
            
            sleep_session = {
                "endTimeStamp": end_timestamp,
                "startTimeStamp": start_timestamp,
                "type": sleep_type
            }
            sleep_sessions.append(sleep_session)
        
        # 按时间排序
        sleep_sessions.sort(key=lambda x: x["startTimeStamp"])
        
        sleep_data = {
            "code": 0,
            "data": sleep_sessions,
            "name": "sleep",
            "type": "history"
        }
        
        return json.dumps(sleep_data, separators=(',', ':'))

    def generate_exercise_daily_data(self, timestamp: datetime, daily_calorie_increment: float) -> str:
        """生成运动日数据"""
        # 100%概率生成运动数据用于测试
        
        # 生成1-5个时间点的卡路里数据
        data_points = []
        point_count = random.randint(1, 5)
        
        base_timestamp = int(timestamp.timestamp() * 1000)
        
        for i in range(point_count):
            # 时间点分散在一天中
            time_offset = random.randint(-12, 12) * 60 * 60 * 1000  # 前后12小时
            point_timestamp = base_timestamp + time_offset
            
            # 卡路里数据：基于运动强度
            calorie_value = max(30, int(daily_calorie_increment * random.uniform(0.5, 2.0) + random.randint(50, 120)))
            
            data_points.append({
                "data": calorie_value,
                "timeStamp": point_timestamp
            })
        
        # 按时间戳排序
        data_points.sort(key=lambda x: x["timeStamp"])
        
        exercise_data = {
            "data": data_points,
            "name": "calorie",
            "type": "history",
            "code": 0
        }
        
        return json.dumps(exercise_data, separators=(',', ':'))

    def generate_exercise_week_data(self, timestamp: datetime, user_fitness_level: int, daily_steps: int) -> str:
        """生成运动周数据"""
        # 100%概率生成周数据用于测试
        
        # 生成一周7天的数据
        week_data = []
        base_timestamp = int(timestamp.timestamp() * 1000)
        
        # 获取本周开始时间（周一）
        days_since_monday = timestamp.weekday()
        monday_timestamp = base_timestamp - (days_since_monday * 24 * 60 * 60 * 1000)
        
        for day in range(7):
            day_timestamp = monday_timestamp + (day * 24 * 60 * 60 * 1000)
            
            if day < 5:  # 工作日有数据
                # 基于用户健身水平和当前步数生成数据
                total_steps = int(daily_steps * random.uniform(0.7, 1.3))
                strength_times = random.randint(200, 500) * user_fitness_level
                total_time = random.randint(8, 16)
                
                week_data.append({
                    "timeStamps": day_timestamp,
                    "totalSteps": total_steps,
                    "strengthTimes": strength_times,
                    "totalTime": total_time
                })
            else:  # 周末可能没有数据
                if random.random() > 0.3:  # 70%概率周末有数据
                    total_steps = int(daily_steps * random.uniform(0.5, 1.1))
                    strength_times = random.randint(100, 400) * user_fitness_level
                    total_time = random.randint(6, 14)
                    
                    week_data.append({
                        "timeStamps": day_timestamp,
                        "totalSteps": total_steps,
                        "strengthTimes": strength_times,
                        "totalTime": total_time
                    })
                else:  # 30%概率周末无数据
                    week_data.append({
                        "timeStamps": 0,
                        "totalSteps": 0,
                        "strengthTimes": 0,
                        "totalTime": 0
                    })
        
        exercise_week_data = {
            "data": week_data,
            "name": "daily",
            "type": "history",
            "code": 0
        }
        
        return json.dumps(exercise_week_data, separators=(',', ':'))

    def generate_workout_data(self, timestamp: datetime, is_exercise_time: bool, user_fitness_level: int) -> str:
        """生成锻炼数据，基于用户提供的格式"""
        # 100%概率生成锻炼数据用于测试
        
        # 生成1-3个锻炼记录
        workout_sessions = []
        session_count = random.randint(1, 3)
        
        base_timestamp = int(timestamp.timestamp() * 1000)
        
        for i in range(session_count):
            # 锻炼时长：10分钟到60分钟
            workout_duration_minutes = random.randint(10, 60)
            workout_duration_ms = workout_duration_minutes * 60 * 1000
            
            # 起始时间：在当前运动时间段内分布
            time_offset = random.randint(-30, 30) * 60 * 1000  # 前后30分钟
            start_timestamp = base_timestamp + time_offset + (i * workout_duration_ms)
            end_timestamp = start_timestamp + workout_duration_ms
            
            # 根据锻炼类型和时长计算卡路里和距离
            workout_type = random.choice([2, 10, 11, 15, 20])  # 不同锻炼类型
            
            # 基于锻炼类型和用户健身水平计算数值
            if workout_type == 2:  # 跑步
                base_calorie_per_min = 8 + user_fitness_level * 2
                base_distance_per_min = 120 + user_fitness_level * 20  # 米/分钟
            elif workout_type == 10:  # 骑行
                base_calorie_per_min = 6 + user_fitness_level * 1.5
                base_distance_per_min = 200 + user_fitness_level * 30
            elif workout_type == 11:  # 游泳
                base_calorie_per_min = 10 + user_fitness_level * 2.5
                base_distance_per_min = 50 + user_fitness_level * 10
            elif workout_type == 15:  # 健身房
                base_calorie_per_min = 7 + user_fitness_level * 1.8
                base_distance_per_min = 0  # 健身房通常无距离
            else:  # 其他运动
                base_calorie_per_min = 5 + user_fitness_level * 1.2
                base_distance_per_min = 80 + user_fitness_level * 15
            
            # 计算总卡路里和距离
            total_calories = int(base_calorie_per_min * workout_duration_minutes * random.uniform(0.8, 1.2))
            total_distance = int(base_distance_per_min * workout_duration_minutes * random.uniform(0.7, 1.3))
            
            # 确保合理的数值范围
            total_calories = max(20, min(800, total_calories))
            total_distance = max(0, min(15000, total_distance))  # 最大15km
            
            workout_session = {
                "calorie": total_calories,
                "distance": total_distance,
                "startTimeStamp": start_timestamp,
                "endTimeStamp": end_timestamp,
                "workoutType": workout_type
            }
            
            # 某些记录可能有recordId
            if random.random() > 0.7:  # 30%概率添加recordId
                workout_session["recordId"] = random.randint(1, 999)
            
            workout_sessions.append(workout_session)
        
        workout_data = {
            "code": 0,
            "data": workout_sessions,
            "name": "workout",
            "type": "history"
        }
        
        return json.dumps(workout_data, separators=(',', ':'))

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

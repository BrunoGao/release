#!/usr/bin/env python3
"""
上传过去一个月的健康数据脚本
基于提供的API格式生成真实的健康数据并批量上传
"""

import json
import requests
import time
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HealthDataUploader:
    def __init__(self, base_url: str = "http://localhost:9998", device_sn: str = "CRFTQ23409001899"):
        self.base_url = base_url
        self.device_sn = device_sn
        self.upload_url = f"{base_url}/api/health/upload"
        
        # 用户和组织信息
        self.customer_id = "1969767962803757058"
        self.org_id = "1969969505868005378"
        self.user_id = "1970007402805485569"
        
        # 健康数据范围
        self.health_ranges = {
            'heart_rate': (60, 100),
            'blood_oxygen': (95, 100),
            'body_temperature': (36.0, 37.5),
            'step': (5000, 15000),
            'distance': (3.0, 12.0),
            'calorie': (200.0, 600.0),
            'stress': (20, 80),
            'blood_pressure_systolic': (110, 140),
            'blood_pressure_diastolic': (70, 90),
            'latitude': (22.5, 22.7),
            'longitude': (113.9, 114.1),
            'altitude': (0.0, 100.0)
        }

    def generate_realistic_health_data(self, timestamp: datetime) -> Dict[str, Any]:
        """生成真实的健康数据"""
        data = {
            "deviceSn": self.device_sn,
            "customerId": self.customer_id,
            "orgId": self.org_id,
            "userId": self.user_id,
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 基础健康指标
        data["heart_rate"] = random.randint(*self.health_ranges['heart_rate'])
        data["blood_oxygen"] = random.randint(*self.health_ranges['blood_oxygen'])
        data["body_temperature"] = f"{random.uniform(*self.health_ranges['body_temperature']):.1f}"
        
        # 运动数据
        data["step"] = random.randint(*self.health_ranges['step'])
        data["distance"] = f"{random.uniform(*self.health_ranges['distance']):.2f}"
        data["calorie"] = f"{random.uniform(*self.health_ranges['calorie']):.1f}"
        
        # 压力和血压
        data["stress"] = random.randint(*self.health_ranges['stress'])
        data["blood_pressure_systolic"] = random.randint(*self.health_ranges['blood_pressure_systolic'])
        data["blood_pressure_diastolic"] = random.randint(*self.health_ranges['blood_pressure_diastolic'])
        
        # 位置信息
        data["latitude"] = f"{random.uniform(*self.health_ranges['latitude']):.6f}"
        data["longitude"] = f"{random.uniform(*self.health_ranges['longitude']):.6f}"
        data["altitude"] = f"{random.uniform(*self.health_ranges['altitude']):.1f}"
        
        # 上传方式
        data["upload_method"] = random.choice(["wifi", "cellular", "bluetooth"])
        
        # 睡眠数据 (晚上生成)
        if 22 <= timestamp.hour or timestamp.hour <= 6:
            sleep_start = int((timestamp - timedelta(hours=8)).timestamp() * 1000)
            sleep_end = int(timestamp.timestamp() * 1000)
            data["sleepData"] = json.dumps({
                "code": 0,
                "data": [{
                    "endTimeStamp": sleep_end,
                    "startTimeStamp": sleep_start,
                    "type": 2
                }],
                "name": "sleep",
                "type": "history"
            })
        else:
            data["sleepData"] = None
        
        # 运动数据 (日间生成)
        if 6 <= timestamp.hour <= 20:
            exercise_data = []
            for i in range(3):
                base_time = int((timestamp - timedelta(hours=i*2)).timestamp() * 1000)
                exercise_data.append({
                    "data": random.randint(50, 150),
                    "timeStamp": base_time
                })
            
            data["exerciseDailyData"] = json.dumps({
                "data": exercise_data,
                "name": "calorie",
                "type": "history",
                "code": 0
            })
            
            # 周运动数据
            week_data = []
            for i in range(7):
                day_time = int((timestamp - timedelta(days=i)).timestamp() * 1000)
                week_data.append({
                    "timeStamps": day_time,
                    "totalSteps": random.randint(8000, 15000),
                    "strengthTimes": random.randint(500, 1500),
                    "totalTime": random.randint(8, 18)
                })
            
            data["exerciseWeekData"] = json.dumps({
                "data": week_data,
                "name": "daily",
                "type": "history",
                "code": 0
            })
            
            # 训练数据
            workout_data = []
            for i in range(random.randint(1, 3)):
                start_time = int((timestamp - timedelta(hours=i+1)).timestamp() * 1000)
                end_time = int((timestamp - timedelta(hours=i)).timestamp() * 1000)
                workout_data.append({
                    "calorie": random.randint(150, 350),
                    "distance": random.randint(3000, 8000),
                    "startTimeStamp": start_time,
                    "endTimeStamp": end_time,
                    "workoutType": random.choice([10, 20, 30]),
                    "recordId": random.randint(1, 500)
                })
            
            data["workoutData"] = json.dumps({
                "code": 0,
                "data": workout_data,
                "name": "workout",
                "type": "history"
            })
        else:
            data["exerciseDailyData"] = None
            data["exerciseWeekData"] = None 
            data["workoutData"] = None
        
        data["scientificSleepData"] = None
        
        return data

    def upload_health_data(self, health_data: Dict[str, Any]) -> bool:
        """上传单条健康数据"""
        try:
            response = requests.post(
                self.upload_url,
                json={"data": health_data},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success", False):
                    logger.debug(f"✅ 上传成功: {health_data['timestamp']}")
                    return True
                else:
                    logger.warning(f"⚠️ 服务器返回失败: {result.get('message', 'Unknown error')}")
                    return False
            else:
                logger.error(f"❌ HTTP错误 {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 网络请求失败: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ 未知错误: {str(e)}")
            return False

    def upload_monthly_data(self, days: int = 30, interval_minutes: int = 60):
        """上传过去指定天数的健康数据"""
        logger.info(f"🚀 开始上传过去{days}天的健康数据")
        logger.info(f"📊 配置信息:")
        logger.info(f"   • 设备序列号: {self.device_sn}")
        logger.info(f"   • 用户ID: {self.user_id}")
        logger.info(f"   • 数据间隔: {interval_minutes}分钟")
        logger.info(f"   • API地址: {self.upload_url}")
        
        # 计算时间范围
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # 生成时间点列表
        timestamps = []
        current_time = start_time
        while current_time <= end_time:
            timestamps.append(current_time)
            current_time += timedelta(minutes=interval_minutes)
        
        total_records = len(timestamps)
        logger.info(f"📈 将生成 {total_records} 条记录")
        logger.info(f"⏰ 时间范围: {start_time.strftime('%Y-%m-%d %H:%M')} 到 {end_time.strftime('%Y-%m-%d %H:%M')}")
        
        # 统计信息
        success_count = 0
        failed_count = 0
        
        # 批量上传
        for i, timestamp in enumerate(timestamps, 1):
            # 生成健康数据
            health_data = self.generate_realistic_health_data(timestamp)
            
            # 上传数据
            if self.upload_health_data(health_data):
                success_count += 1
            else:
                failed_count += 1
            
            # 显示进度
            if i % 50 == 0 or i == total_records:
                progress = (i / total_records) * 100
                success_rate = (success_count / i) * 100
                logger.info(f"📊 进度: {progress:.1f}% | {i}/{total_records} | 成功率: {success_rate:.1f}%")
            
            # 控制上传速度，避免过载
            time.sleep(0.1)
        
        # 最终统计
        logger.info("=" * 60)
        logger.info("📊 上传完成统计")
        logger.info("=" * 60)
        logger.info(f"总记录数: {total_records}")
        logger.info(f"成功上传: {success_count}")
        logger.info(f"失败数量: {failed_count}")
        logger.info(f"成功率: {(success_count / total_records) * 100:.2f}%")


def main():
    """主函数"""
    print("🏥 ljwx-boot 健康数据批量上传工具")
    print("=" * 50)
    
    # 创建上传器
    uploader = HealthDataUploader()
    
    try:
        # 上传过去30天的数据，每小时一条记录
        uploader.upload_monthly_data(days=30, interval_minutes=60)
        
    except KeyboardInterrupt:
        logger.info("❌ 用户中断上传")
    except Exception as e:
        logger.error(f"❌ 程序异常: {str(e)}")


if __name__ == "__main__":
    main()
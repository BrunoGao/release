#!/usr/bin/env python3
import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import multiprocessing
import signal
import sys
import os
from pathlib import Path
from api_tester import APITester
from db_config import load_db_config
import random

class HighSpeedUploader:
    def __init__(self, base_url: str = "http://192.168.1.83:5001"):
        self.base_url = base_url
        self.api_tester = APITester(base_url)
        self.db_config = load_db_config()
        self.running = False
        
        # 高并发设置
        self.max_workers = min(50, multiprocessing.cpu_count() * 10)  # 最大并发数
        self.batch_size = 20  # 批次大小
        
        # Setup logging
        self.setup_logging()
        
        # 统计信息
        self.stats = {
            'total_uploads': 0,
            'successful_uploads': 0,
            'failed_uploads': 0,
            'start_time': None,
            'devices_count': 0,
            'time_points_completed': 0,
            'total_time_points': 0
        }
        
        # 信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def setup_logging(self):
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"high_speed_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"日志文件: {log_file}")
    
    def signal_handler(self, signum, frame):
        self.logger.info(f"接收到信号 {signum}，开始停止...")
        self.running = False
        sys.exit(0)
    
    def generate_data_for_time(self, device_sn: str, target_time: datetime) -> Dict[str, Any]:
        """为指定时间生成所有类型的数据"""
        timestamp_str = target_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 生成健康数据
        health_data = {
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
                "timestamp": timestamp_str
            }
        }
        
        # 生成设备信息
        device_info = {
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
            "timestamp": timestamp_str,
            "wearState": random.choice([0, 1])
        }
        
        # 生成通用事件
        common_event = {
            'eventType': 'com.tdtech.ohos.action.WEAR_STATUS_CHANGED',
            'eventValue': str(random.choice([0, 1])),
            'deviceSn': device_sn,
            'latitude': round(random.uniform(22.5, 22.6), 6),
            'longitude': round(random.uniform(114.0, 114.1), 6),
            'altitude': random.randint(0, 100),
            'timestamp': timestamp_str,
            'healthData': health_data
        }
        
        return {
            'health_data': health_data,
            'device_info': device_info,
            'common_event': common_event
        }
    
    def upload_single_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """上传单个请求"""
        try:
            result = self.api_tester.make_request(endpoint, data, timeout=30)
            return result
        except Exception as e:
            return {
                'endpoint': endpoint,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def process_device_batch(self, device_batch: List[Dict[str, Any]], time_point: datetime) -> List[Dict[str, Any]]:
        """并行处理一批设备的数据上传"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            
            for device in device_batch:
                device_sn = device['device_sn']
                data_set = self.generate_data_for_time(device_sn, time_point)
                
                # 为每个设备的三个接口创建任务
                endpoints = [
                    ('upload_health_data', data_set['health_data']),
                    ('upload_device_info', data_set['device_info']),
                    ('upload_common_event', data_set['common_event'])
                ]
                
                for endpoint, data in endpoints:
                    future = executor.submit(self.upload_single_request, endpoint, data)
                    futures.append((future, device_sn, endpoint))
            
            # 收集结果
            for future, device_sn, endpoint in futures:
                try:
                    result = future.result(timeout=60)
                    result['device_sn'] = device_sn
                    results.append(result)
                    
                    # 更新统计
                    self.stats['total_uploads'] += 1
                    if result.get('success', False):
                        self.stats['successful_uploads'] += 1
                    else:
                        self.stats['failed_uploads'] += 1
                        
                except Exception as e:
                    error_result = {
                        'device_sn': device_sn,
                        'endpoint': endpoint,
                        'success': False,
                        'error': f"Future error: {str(e)}",
                        'timestamp': datetime.now().isoformat()
                    }
                    results.append(error_result)
                    self.stats['total_uploads'] += 1
                    self.stats['failed_uploads'] += 1
        
        return results
    
    def upload_historical_data_fast(self, days: int = 30):
        """高速上传历史数据"""
        if not self.db_config.connect():
            self.logger.error("数据库连接失败")
            return
        
        # 获取设备数据
        user_devices = self.db_config.get_user_devices(100)
        if not user_devices:
            devices = self.db_config.get_devices(100)
            device_list = [{'device_sn': d['device_sn'], 'user_name': 'unknown'} 
                          for d in devices if d.get('device_sn')]
        else:
            device_list = [{'device_sn': ud['device_sn'], 'user_name': ud['user_name']} 
                          for ud in user_devices]
        
        if not device_list:
            self.logger.error("未找到设备数据")
            return
        
        self.stats['devices_count'] = len(device_list)
        self.logger.info(f"找到 {len(device_list)} 个设备")
        
        # 计算时间范围 - 每分钟一次
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # 生成时间点（每分钟）
        time_points = []
        current_time = start_time
        while current_time <= end_time:
            time_points.append(current_time)
            current_time += timedelta(minutes=1)  # 改为每分钟
        
        self.stats['total_time_points'] = len(time_points)
        total_operations = len(device_list) * len(time_points) * 3
        
        self.logger.info(f"时间范围: {start_time} 到 {end_time}")
        self.logger.info(f"时间点数量: {len(time_points)} (每分钟)")
        self.logger.info(f"总操作数: {total_operations}")
        self.logger.info(f"最大并发: {self.max_workers}")
        
        self.running = True
        self.stats['start_time'] = datetime.now()
        
        # 分批处理设备
        device_batches = [device_list[i:i + self.batch_size] 
                         for i in range(0, len(device_list), self.batch_size)]
        
        self.logger.info(f"设备分为 {len(device_batches)} 个批次，每批 {self.batch_size} 个")
        
        # 处理每个时间点
        for time_idx, time_point in enumerate(time_points):
            if not self.running:
                break
            
            time_str = time_point.strftime('%Y-%m-%d %H:%M:%S')
            
            # 并行处理所有设备批次
            batch_futures = []
            with ProcessPoolExecutor(max_workers=min(len(device_batches), multiprocessing.cpu_count())) as process_executor:
                for batch in device_batches:
                    if not self.running:
                        break
                    future = process_executor.submit(self.process_device_batch_worker, batch, time_point)
                    batch_futures.append(future)
                
                # 等待所有批次完成
                for future in as_completed(batch_futures):
                    if not self.running:
                        break
                    try:
                        results = future.result(timeout=120)
                        # 结果已在worker中统计，这里不需要额外处理
                    except Exception as e:
                        self.logger.error(f"批次处理错误: {e}")
            
            self.stats['time_points_completed'] += 1
            
            # 显示进度
            progress = (time_idx + 1) / len(time_points) * 100
            elapsed = datetime.now() - self.stats['start_time']
            remaining_points = len(time_points) - (time_idx + 1)
            if time_idx > 0:
                avg_time_per_point = elapsed.total_seconds() / (time_idx + 1)
                eta = timedelta(seconds=avg_time_per_point * remaining_points)
            else:
                eta = timedelta(0)
            
            if (time_idx + 1) % 10 == 0 or time_idx == 0:  # 每10个时间点显示一次
                success_rate = (self.stats['successful_uploads'] / self.stats['total_uploads'] * 100) if self.stats['total_uploads'] > 0 else 0
                self.logger.info(f"🚀 进度: {progress:.1f}% | 时间: {time_str} | "
                               f"成功: {self.stats['successful_uploads']} | 失败: {self.stats['failed_uploads']} | "
                               f"成功率: {success_rate:.1f}% | ETA: {eta}")
        
        self.db_config.disconnect()
        self.print_final_stats()
    
    def process_device_batch_worker(self, device_batch: List[Dict[str, Any]], time_point: datetime) -> List[Dict[str, Any]]:
        """工作进程中处理设备批次"""
        # 在新进程中重新初始化必要的组件
        api_tester = APITester(self.base_url)
        results = []
        
        for device in device_batch:
            device_sn = device['device_sn']
            data_set = self.generate_data_for_time(device_sn, time_point)
            
            endpoints = [
                ('upload_health_data', data_set['health_data']),
                ('upload_device_info', data_set['device_info']),
                ('upload_common_event', data_set['common_event'])
            ]
            
            for endpoint, data in endpoints:
                try:
                    result = api_tester.make_request(endpoint, data, timeout=30)
                    result['device_sn'] = device_sn
                    results.append(result)
                except Exception as e:
                    error_result = {
                        'device_sn': device_sn,
                        'endpoint': endpoint,
                        'success': False,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    }
                    results.append(error_result)
        
        return results
    
    def print_final_stats(self):
        """打印最终统计"""
        self.logger.info("=" * 80)
        self.logger.info("📊 高速上传完成统计")
        self.logger.info("=" * 80)
        
        if self.stats['start_time']:
            duration = datetime.now() - self.stats['start_time']
            self.logger.info(f"总耗时: {duration}")
            
            # 计算速度
            total_ops = self.stats['total_uploads']
            if total_ops > 0 and duration.total_seconds() > 0:
                ops_per_sec = total_ops / duration.total_seconds()
                self.logger.info(f"上传速度: {ops_per_sec:.2f} 次/秒")
        
        self.logger.info(f"设备数量: {self.stats['devices_count']}")
        self.logger.info(f"时间点完成: {self.stats['time_points_completed']}/{self.stats['total_time_points']}")
        self.logger.info(f"总上传次数: {self.stats['total_uploads']}")
        self.logger.info(f"成功次数: {self.stats['successful_uploads']}")
        self.logger.info(f"失败次数: {self.stats['failed_uploads']}")
        
        if self.stats['total_uploads'] > 0:
            success_rate = (self.stats['successful_uploads'] / self.stats['total_uploads']) * 100
            self.logger.info(f"成功率: {success_rate:.2f}%")

def main():
    print("🚀 高速历史数据上传工具")
    print("=" * 50)
    print("• 模拟客户手表每分钟上传一次数据")
    print("• 最大并发处理")
    print("• 上传过去30天的历史数据")
    print()
    
    days = 30
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except ValueError:
            print("❌ 无效的天数参数")
            return
    
    uploader = HighSpeedUploader()
    
    try:
        print(f"开始上传过去 {days} 天的数据...")
        uploader.upload_historical_data_fast(days)
    except KeyboardInterrupt:
        print("\n\n👋 用户中断操作")
        uploader.running = False
    except Exception as e:
        print(f"\n❌ 程序错误: {e}")

if __name__ == "__main__":
    main()
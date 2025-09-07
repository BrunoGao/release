#!/usr/bin/env python3
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import signal
import sys
from pathlib import Path
from api_tester import APITester
from db_config import load_db_config
import random
import queue

class FastUploader:
    def __init__(self, base_url: str = "http://192.168.1.83:5001"):
        self.base_url = base_url
        self.db_config = load_db_config()
        self.running = False
        
        # 高并发设置
        self.max_workers = 20  # 线程池大小
        self.session_pool = self._create_api_testers(self.max_workers)
        
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
        
        # 线程安全的锁
        self.stats_lock = threading.Lock()
        
        # 设置日志
        self.setup_logging()
        
        # 信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def _create_api_testers(self, count: int) -> queue.Queue:
        """创建API测试器池"""
        tester_queue = queue.Queue()
        for _ in range(count):
            tester_queue.put(APITester(self.base_url))
        return tester_queue
    
    def setup_logging(self):
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"fast_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
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
        self.logger.info(f"接收到信号 {signum}，停止上传...")
        self.running = False
        sys.exit(0)
    
    def generate_data_for_time(self, device_sn: str, target_time: datetime) -> Dict[str, Any]:
        """为指定时间生成数据"""
        timestamp_str = target_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 健康数据
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
        
        # 设备信息
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
        
        # 通用事件
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
            'upload_health_data': health_data,
            'upload_device_info': device_info,
            'upload_common_event': common_event
        }
    
    def upload_device_data(self, device_sn: str, target_time: datetime) -> List[Dict[str, Any]]:
        """上传单个设备在指定时间的所有数据"""
        # 获取API测试器
        api_tester = self.session_pool.get()
        
        try:
            data_set = self.generate_data_for_time(device_sn, target_time)
            results = []
            
            for endpoint, data in data_set.items():
                try:
                    result = api_tester.make_request(endpoint, data, timeout=30)
                    result['device_sn'] = device_sn
                    result['endpoint'] = endpoint
                    results.append(result)
                    
                    # 更新统计
                    with self.stats_lock:
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
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    }
                    results.append(error_result)
                    
                    with self.stats_lock:
                        self.stats['total_uploads'] += 1
                        self.stats['failed_uploads'] += 1
            
            return results
        
        finally:
            # 归还API测试器到池中
            self.session_pool.put(api_tester)
    
    def upload_historical_data_fast(self, days: int = 30):
        """高速上传历史数据"""
        if not self.db_config.connect():
            self.logger.error("数据库连接失败")
            return
        
        # 获取设备数据
        user_devices = self.db_config.get_user_devices(100)
        if not user_devices:
            devices = self.db_config.get_devices(100)
            device_list = [d['device_sn'] for d in devices if d.get('device_sn')]
        else:
            device_list = [ud['device_sn'] for ud in user_devices]
        
        if not device_list:
            self.logger.error("未找到设备数据")
            return
        
        self.stats['devices_count'] = len(device_list)
        
        # 计算时间范围 - 每分钟一次
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # 生成时间点（每分钟）
        time_points = []
        current_time = start_time
        while current_time <= end_time:
            time_points.append(current_time)
            current_time += timedelta(minutes=1)
        
        self.stats['total_time_points'] = len(time_points)
        total_operations = len(device_list) * len(time_points) * 3
        
        self.logger.info("🚀 高速数据上传开始")
        self.logger.info(f"设备数量: {len(device_list)}")
        self.logger.info(f"时间范围: {start_time.strftime('%Y-%m-%d %H:%M')} 到 {end_time.strftime('%Y-%m-%d %H:%M')}")
        self.logger.info(f"时间点数量: {len(time_points)} (每分钟)")
        self.logger.info(f"总操作数: {total_operations}")
        self.logger.info(f"线程池大小: {self.max_workers}")
        self.logger.info(f"预计耗时: {total_operations/100/60:.1f} 分钟 (假设100次/分钟)")
        
        self.running = True
        self.stats['start_time'] = datetime.now()
        
        # 使用线程池并行处理
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 创建所有任务
            futures = []
            for time_idx, time_point in enumerate(time_points):
                if not self.running:
                    break
                
                for device_sn in device_list:
                    if not self.running:
                        break
                    
                    future = executor.submit(self.upload_device_data, device_sn, time_point)
                    futures.append((future, time_point, device_sn, time_idx))
            
            self.logger.info(f"已创建 {len(futures)} 个上传任务")
            
            # 等待所有任务完成并显示进度
            completed_count = 0
            for future, time_point, device_sn, time_idx in futures:
                if not self.running:
                    break
                
                try:
                    results = future.result(timeout=60)
                    completed_count += 1
                    
                    # 每完成10个任务显示进度
                    if completed_count % 10 == 0 or completed_count == len(futures):
                        elapsed = datetime.now() - self.stats['start_time']
                        with self.stats_lock:
                            success_rate = (self.stats['successful_uploads'] / self.stats['total_uploads'] * 100) if self.stats['total_uploads'] > 0 else 0
                            upload_speed = self.stats['total_uploads'] / elapsed.total_seconds() if elapsed.total_seconds() > 0 else 0
                        
                        progress = completed_count / len(futures) * 100
                        time_str = time_point.strftime('%H:%M')
                        self.logger.info(f"📊 进度: {progress:.1f}% | {completed_count}/{len(futures)} | "
                                       f"时间: {time_str} | 设备: {device_sn[:15]} | "
                                       f"成功率: {success_rate:.1f}% | 速度: {upload_speed:.1f} 次/秒")
                
                except Exception as e:
                    self.logger.error(f"任务处理错误 - 设备: {device_sn}, 时间: {time_point}: {e}")
                    completed_count += 1
        
        self.db_config.disconnect()
        self.print_final_stats()
    
    def print_final_stats(self):
        """打印最终统计"""
        self.logger.info("=" * 80)
        self.logger.info("📊 高速上传完成统计")
        self.logger.info("=" * 80)
        
        if self.stats['start_time']:
            duration = datetime.now() - self.stats['start_time']
            self.logger.info(f"总耗时: {duration}")
            
            # 计算速度
            if self.stats['total_uploads'] > 0 and duration.total_seconds() > 0:
                upload_speed = self.stats['total_uploads'] / duration.total_seconds()
                self.logger.info(f"平均上传速度: {upload_speed:.2f} 次/秒")
                self.logger.info(f"峰值处理能力: {upload_speed * 60:.0f} 次/分钟")
        
        self.logger.info(f"设备数量: {self.stats['devices_count']}")
        self.logger.info(f"总操作数: {self.stats['total_uploads']}")
        self.logger.info(f"成功次数: {self.stats['successful_uploads']}")
        self.logger.info(f"失败次数: {self.stats['failed_uploads']}")
        
        if self.stats['total_uploads'] > 0:
            success_rate = (self.stats['successful_uploads'] / self.stats['total_uploads']) * 100
            self.logger.info(f"成功率: {success_rate:.2f}%")

def main():
    print("🚀 高速数据上传工具 - 模拟客户手表每分钟上传")
    print("=" * 60)
    
    days = 30
    if len(sys.argv) > 1:
        try:
            days = float(sys.argv[1])
        except ValueError:
            print("❌ 无效的天数参数")
            return
    
    print(f"📅 准备上传过去 {days} 天的数据")
    print("⚡ 使用高并发模式，最大化上传速度")
    print("💡 按 Ctrl+C 可以安全停止")
    print()
    
    confirm = input("确认开始上传? (y/N): ").strip().lower()
    if confirm != 'y':
        print("已取消")
        return
    
    uploader = FastUploader()
    
    try:
        uploader.upload_historical_data_fast(days)
    except KeyboardInterrupt:
        print("\n\n⏸️  用户中断操作")
        uploader.running = False
    except Exception as e:
        print(f"\n❌ 程序错误: {e}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import threading
import signal
import sys
import os
from pathlib import Path
from api_tester import APITester
from db_config import load_db_config
import argparse

class ContinuousUploader:
    def __init__(self, base_url: str = "http://192.168.1.83:5001", interval: int = 300):
        self.base_url = base_url
        self.interval = interval  # seconds between uploads
        self.api_tester = APITester(base_url)
        self.db_config = load_db_config()
        self.running = False
        self.upload_thread = None
        
        # Setup logging
        self.setup_logging()
        
        # Statistics
        self.stats = {
            'total_uploads': 0,
            'successful_uploads': 0,
            'failed_uploads': 0,
            'start_time': None,
            'current_date': None,
            'devices_processed': set()
        }
        
        # Signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def setup_logging(self):
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"continuous_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
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
        self.logger.info(f"接收到信号 {signum}，开始优雅关闭...")
        self.stop()
        sys.exit(0)
    
    def get_devices_with_users(self) -> List[Dict[str, Any]]:
        if not self.db_config.connect():
            self.logger.error("数据库连接失败")
            return []
        
        user_devices = self.db_config.get_user_devices(50)
        if not user_devices:
            devices = self.db_config.get_devices(50)
            return [{'device_sn': d['device_sn'], 'user_name': 'unknown'} for d in devices if d.get('device_sn')]
        
        return [{'device_sn': ud['device_sn'], 'user_name': ud['user_name']} for ud in user_devices]
    
    def generate_historical_data(self, device_sn: str, target_time: datetime) -> Dict[str, Any]:
        """为指定时间生成历史数据"""
        # 保存原来的时间生成逻辑，用指定时间替换
        original_generate_health = self.api_tester.generate_health_data
        original_generate_device = self.api_tester.generate_device_info
        original_generate_event = self.api_tester.generate_common_event
        
        timestamp_str = target_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 重写生成方法以使用指定时间
        def generate_health_with_time(device_sn):
            data = original_generate_health(device_sn)
            data['data']['timestamp'] = timestamp_str
            return data
        
        def generate_device_with_time(device_sn):
            data = original_generate_device(device_sn)
            data['timestamp'] = timestamp_str
            return data
        
        def generate_event_with_time(device_sn):
            data = original_generate_event(device_sn)
            data['timestamp'] = timestamp_str
            data['healthData']['data']['timestamp'] = timestamp_str
            return data
        
        return {
            'health_data': generate_health_with_time(device_sn),
            'device_info': generate_device_with_time(device_sn),
            'common_event': generate_event_with_time(device_sn)
        }
    
    def upload_data_for_time(self, device_sn: str, user_name: str, target_time: datetime) -> Dict[str, bool]:
        """为指定时间上传数据"""
        results = {
            'upload_health_data': False,
            'upload_device_info': False,
            'upload_common_event': False
        }
        
        historical_data = self.generate_historical_data(device_sn, target_time)
        
        endpoints = [
            ('upload_health_data', historical_data['health_data']),
            ('upload_device_info', historical_data['device_info']),
            ('upload_common_event', historical_data['common_event'])
        ]
        
        for endpoint, data in endpoints:
            try:
                result = self.api_tester.make_request(endpoint, data, timeout=30)
                success = result.get('success', False)
                results[endpoint] = success
                
                if success:
                    self.logger.debug(f"✅ {endpoint} 成功 - 设备: {device_sn}, 时间: {target_time}")
                else:
                    error_msg = result.get('error', 'Unknown error')
                    self.logger.warning(f"❌ {endpoint} 失败 - 设备: {device_sn}, 错误: {error_msg}")
                
                self.stats['total_uploads'] += 1
                if success:
                    self.stats['successful_uploads'] += 1
                else:
                    self.stats['failed_uploads'] += 1
                    
            except Exception as e:
                self.logger.error(f"❌ {endpoint} 异常 - 设备: {device_sn}, 异常: {e}")
                results[endpoint] = False
                self.stats['total_uploads'] += 1
                self.stats['failed_uploads'] += 1
        
        return results
    
    def upload_historical_data(self, days: int = 30):
        """上传过去指定天数的历史数据"""
        devices = self.get_devices_with_users()
        if not devices:
            self.logger.error("未找到设备数据")
            return
        
        self.logger.info(f"开始上传过去 {days} 天的历史数据")
        self.logger.info(f"找到 {len(devices)} 个设备")
        
        # 计算时间范围
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        self.stats['start_time'] = start_time
        
        # 每5分钟一个时间点
        time_points = []
        current_time = start_time
        while current_time <= end_time:
            time_points.append(current_time)
            current_time += timedelta(minutes=5)
        
        total_operations = len(devices) * len(time_points) * 3  # 3个接口
        self.logger.info(f"总共需要上传 {total_operations} 次数据")
        self.logger.info(f"预计耗时: {total_operations * 0.5 / 60:.1f} 分钟")
        
        # 开始上传
        completed_operations = 0
        
        for time_point in time_points:
            if not self.running:
                break
                
            self.stats['current_date'] = time_point.strftime('%Y-%m-%d %H:%M:%S')
            self.logger.info(f"📅 处理时间点: {self.stats['current_date']}")
            
            for device in devices:
                if not self.running:
                    break
                    
                device_sn = device['device_sn']
                user_name = device['user_name']
                
                results = self.upload_data_for_time(device_sn, user_name, time_point)
                
                self.stats['devices_processed'].add(device_sn)
                completed_operations += 3
                
                # 显示进度
                progress = (completed_operations / total_operations) * 100
                success_rate = (self.stats['successful_uploads'] / self.stats['total_uploads'] * 100) if self.stats['total_uploads'] > 0 else 0
                
                if completed_operations % 30 == 0:  # 每30次操作显示一次进度
                    self.logger.info(f"📊 进度: {progress:.1f}% | 成功: {self.stats['successful_uploads']} | 失败: {self.stats['failed_uploads']} | 成功率: {success_rate:.1f}%")
            
            # 每个时间点之间稍微延迟，避免过快请求
            if self.running:
                time.sleep(0.1)
        
        self.print_final_statistics()
    
    def continuous_upload(self):
        """持续上传当前数据（每5分钟）"""
        devices = self.get_devices_with_users()
        if not devices:
            self.logger.error("未找到设备数据")
            return
        
        self.logger.info(f"开始持续数据上传，间隔: {self.interval}秒")
        self.logger.info(f"找到 {len(devices)} 个设备")
        
        while self.running:
            current_time = datetime.now()
            self.stats['current_date'] = current_time.strftime('%Y-%m-%d %H:%M:%S')
            
            self.logger.info(f"🔄 开始上传数据 - 时间: {self.stats['current_date']}")
            
            for device in devices:
                if not self.running:
                    break
                
                device_sn = device['device_sn']
                user_name = device['user_name']
                
                results = self.upload_data_for_time(device_sn, user_name, current_time)
                
                self.stats['devices_processed'].add(device_sn)
                
                # 显示结果
                success_count = sum(1 for v in results.values() if v)
                self.logger.info(f"📱 设备 {device_sn} - 成功: {success_count}/3")
            
            # 显示统计
            success_rate = (self.stats['successful_uploads'] / self.stats['total_uploads'] * 100) if self.stats['total_uploads'] > 0 else 0
            self.logger.info(f"📊 累计 - 总上传: {self.stats['total_uploads']}, 成功: {self.stats['successful_uploads']}, 失败: {self.stats['failed_uploads']}, 成功率: {success_rate:.1f}%")
            
            # 等待下次上传
            if self.running:
                self.logger.info(f"⏰ 等待 {self.interval} 秒后进行下次上传...")
                time.sleep(self.interval)
    
    def print_final_statistics(self):
        """打印最终统计信息"""
        self.logger.info("=" * 60)
        self.logger.info("📊 最终统计报告")
        self.logger.info("=" * 60)
        
        if self.stats['start_time']:
            duration = datetime.now() - self.stats['start_time']
            self.logger.info(f"运行时长: {duration}")
        
        self.logger.info(f"总上传次数: {self.stats['total_uploads']}")
        self.logger.info(f"成功次数: {self.stats['successful_uploads']}")
        self.logger.info(f"失败次数: {self.stats['failed_uploads']}")
        
        if self.stats['total_uploads'] > 0:
            success_rate = (self.stats['successful_uploads'] / self.stats['total_uploads']) * 100
            self.logger.info(f"成功率: {success_rate:.2f}%")
        
        self.logger.info(f"处理设备数: {len(self.stats['devices_processed'])}")
        self.logger.info(f"设备列表: {list(self.stats['devices_processed'])}")
    
    def start_historical(self, days: int = 30):
        """启动历史数据上传"""
        self.running = True
        self.stats['start_time'] = datetime.now()
        self.logger.info("🚀 开始历史数据上传...")
        
        try:
            self.upload_historical_data(days)
        except Exception as e:
            self.logger.error(f"历史数据上传出错: {e}")
        finally:
            self.running = False
    
    def start_continuous(self):
        """启动持续上传"""
        self.running = True
        self.stats['start_time'] = datetime.now()
        self.logger.info("🚀 开始持续数据上传...")
        
        self.upload_thread = threading.Thread(target=self.continuous_upload)
        self.upload_thread.daemon = True
        self.upload_thread.start()
        
        try:
            self.upload_thread.join()
        except KeyboardInterrupt:
            self.logger.info("收到中断信号，正在停止...")
            self.stop()
    
    def stop(self):
        """停止上传"""
        self.logger.info("🛑 正在停止数据上传...")
        self.running = False
        
        if self.upload_thread and self.upload_thread.is_alive():
            self.upload_thread.join(timeout=5)
        
        self.db_config.disconnect()
        self.print_final_statistics()
        self.logger.info("✅ 上传已停止")

def main():
    parser = argparse.ArgumentParser(description='持续数据上传工具')
    parser.add_argument('--url', default='http://192.168.1.83:5001', help='API基础地址')
    parser.add_argument('--mode', choices=['historical', 'continuous', 'both'], 
                       default='historical', help='运行模式')
    parser.add_argument('--days', type=int, default=30, help='历史数据天数')
    parser.add_argument('--interval', type=int, default=300, help='持续上传间隔（秒）')
    
    args = parser.parse_args()
    
    uploader = ContinuousUploader(args.url, args.interval)
    
    try:
        if args.mode == 'historical':
            uploader.start_historical(args.days)
        elif args.mode == 'continuous':
            uploader.start_continuous()
        elif args.mode == 'both':
            print("先执行历史数据上传...")
            uploader.start_historical(args.days)
            print("\n开始持续上传...")
            uploader.start_continuous()
            
    except KeyboardInterrupt:
        uploader.logger.info("收到中断信号")
        uploader.stop()
    except Exception as e:
        uploader.logger.error(f"程序异常: {e}")
        uploader.stop()

if __name__ == "__main__":
    main()
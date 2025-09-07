#!/usr/bin/env python3
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from continuous_uploader import ContinuousUploader

class BackgroundUploader(ContinuousUploader):
    def __init__(self, base_url: str = "http://192.168.1.83:5001", interval: int = 300):
        super().__init__(base_url, interval)
        self.progress_file = Path("progress_state.json")
        self.state = self.load_progress()
    
    def load_progress(self) -> dict:
        """加载进度状态"""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    # 转换时间字符串回datetime对象
                    if 'last_completed_time' in state and state['last_completed_time']:
                        state['last_completed_time'] = datetime.fromisoformat(state['last_completed_time'])
                    if 'start_time' in state and state['start_time']:
                        state['start_time'] = datetime.fromisoformat(state['start_time'])
                    return state
            except Exception as e:
                self.logger.warning(f"加载进度文件失败: {e}")
        
        return {
            'mode': None,
            'total_days': 30,
            'completed_times': [],
            'last_completed_time': None,
            'start_time': None,
            'total_operations': 0,
            'completed_operations': 0
        }
    
    def save_progress(self):
        """保存进度状态"""
        try:
            state_to_save = self.state.copy()
            # 转换datetime对象为字符串
            if state_to_save.get('last_completed_time'):
                state_to_save['last_completed_time'] = state_to_save['last_completed_time'].isoformat()
            if state_to_save.get('start_time'):
                state_to_save['start_time'] = state_to_save['start_time'].isoformat()
            
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(state_to_save, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"保存进度失败: {e}")
    
    def resume_historical_upload(self, days: int = 30):
        """恢复历史数据上传"""
        devices = self.get_devices_with_users()
        if not devices:
            self.logger.error("未找到设备数据")
            return
        
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # 检查是否有进度可以恢复
        resume_from = None
        if self.state.get('mode') == 'historical' and self.state.get('last_completed_time'):
            resume_from = self.state['last_completed_time'] + timedelta(minutes=5)
            self.logger.info(f"🔄 恢复上传，从时间点: {resume_from}")
        else:
            resume_from = start_time
            self.state.update({
                'mode': 'historical',
                'total_days': days,
                'start_time': datetime.now(),
                'completed_times': [],
                'completed_operations': 0
            })
            self.logger.info(f"🚀 开始新的历史数据上传")
        
        # 计算需要处理的时间点
        time_points = []
        current_time = resume_from
        while current_time <= end_time:
            time_points.append(current_time)
            current_time += timedelta(minutes=5)
        
        total_operations = len(devices) * len(time_points) * 3
        self.state['total_operations'] = len(devices) * ((end_time - start_time).total_seconds() / 300) * 3
        
        self.logger.info(f"剩余时间点: {len(time_points)}")
        self.logger.info(f"剩余操作数: {total_operations}")
        
        # 开始处理
        for i, time_point in enumerate(time_points):
            if not self.running:
                break
            
            self.logger.info(f"📅 处理时间点: {time_point.strftime('%Y-%m-%d %H:%M:%S')} ({i+1}/{len(time_points)})")
            
            for device in devices:
                if not self.running:
                    break
                
                device_sn = device['device_sn']
                user_name = device['user_name']
                
                self.upload_data_for_time(device_sn, user_name, time_point)
                self.state['completed_operations'] += 3
            
            # 更新进度
            self.state['last_completed_time'] = time_point
            self.state['completed_times'].append(time_point.isoformat())
            
            # 每10个时间点保存一次进度
            if (i + 1) % 10 == 0:
                self.save_progress()
                progress = ((i + 1) / len(time_points)) * 100
                self.logger.info(f"📊 进度: {progress:.1f}% - 已保存检查点")
            
            if self.running:
                time.sleep(0.1)  # 避免过快请求
        
        # 完成后清理进度文件
        if self.running:  # 正常完成
            self.state['mode'] = 'completed'
            self.save_progress()
            self.logger.info("🎉 历史数据上传完成！")
        else:  # 被中断
            self.save_progress()
            self.logger.info("⏸️  上传已暂停，进度已保存")

def main():
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "start":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            print(f"🚀 开始/恢复历史数据上传 ({days}天)")
            
            uploader = BackgroundUploader()
            uploader.running = True
            
            try:
                uploader.resume_historical_upload(days)
            except KeyboardInterrupt:
                uploader.logger.info("收到中断信号，保存进度...")
                uploader.running = False
                uploader.save_progress()
        
        elif command == "status":
            uploader = BackgroundUploader()
            state = uploader.state
            
            print("📊 当前状态:")
            print(f"模式: {state.get('mode', 'None')}")
            
            if state.get('start_time'):
                print(f"开始时间: {state['start_time']}")
            
            if state.get('last_completed_time'):
                print(f"最后完成时间: {state['last_completed_time']}")
            
            if state.get('total_operations', 0) > 0:
                completed = state.get('completed_operations', 0)
                total = state['total_operations']
                progress = (completed / total) * 100
                print(f"进度: {completed}/{total} ({progress:.1f}%)")
        
        elif command == "reset":
            progress_file = Path("progress_state.json")
            if progress_file.exists():
                progress_file.unlink()
                print("🗑️  进度已重置")
            else:
                print("ℹ️  没有进度文件需要重置")
        
        elif command == "continuous":
            print("🔄 开始持续上传模式")
            uploader = BackgroundUploader()
            uploader.start_continuous()
        
        else:
            print("用法:")
            print("  python background_uploader.py start [天数]  - 开始/恢复历史数据上传")
            print("  python background_uploader.py status      - 查看进度状态")
            print("  python background_uploader.py reset       - 重置进度")
            print("  python background_uploader.py continuous  - 持续上传模式")
    
    else:
        print("📋 后台数据上传工具")
        print("==================")
        print("用法:")
        print("  python background_uploader.py start [天数]  - 开始/恢复历史数据上传")
        print("  python background_uploader.py status      - 查看进度状态")
        print("  python background_uploader.py reset       - 重置进度")
        print("  python background_uploader.py continuous  - 持续上传模式")

if __name__ == "__main__":
    main()
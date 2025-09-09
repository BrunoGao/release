#!/usr/bin/env python3
"""
系统性能监控脚本
实时监控系统资源和应用性能指标
"""

import time
import json
import subprocess
import threading
import signal
import sys
from datetime import datetime
from pathlib import Path
import requests
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional

@dataclass
class SystemMetrics:
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_usage_percent: float
    network_connections: int
    load_average: List[float]

@dataclass
class ApplicationMetrics:
    timestamp: str
    response_time: float
    request_count: int
    success_rate: float
    queue_size: int
    worker_threads: int
    processed_total: int
    errors: int

class SystemMonitor:
    """系统性能监控器"""
    
    def __init__(self, app_url: str = "http://localhost:5225", 
                 interval: float = 2.0, output_file: str = None):
        self.app_url = app_url
        self.interval = interval
        self.running = False
        
        # 输出文件
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.output_file = f"logs/system_monitor_{timestamp}.log"
        else:
            self.output_file = output_file
        
        # 确保日志目录存在
        Path(self.output_file).parent.mkdir(exist_ok=True)
        
        # 数据存储
        self.system_metrics_history = []
        self.app_metrics_history = []
        
        # 信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        print(f"📊 系统监控器初始化完成")
        print(f"📝 监控日志: {self.output_file}")
        print(f"🎯 应用URL: {app_url}")
        print(f"⏱️  监控间隔: {interval}秒")
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        print(f"\n收到信号 {signum}, 停止监控...")
        self.running = False
    
    def get_system_metrics(self) -> SystemMetrics:
        """获取系统指标"""
        try:
            # CPU使用率
            cpu_cmd = "top -l 1 -n 0 | grep 'CPU usage' | awk '{print $3}' | sed 's/%//'"
            cpu_result = subprocess.run(cpu_cmd, shell=True, capture_output=True, text=True)
            cpu_percent = float(cpu_result.stdout.strip()) if cpu_result.stdout.strip() else 0.0
            
            # 内存使用情况
            vm_stat = subprocess.run(['vm_stat'], capture_output=True, text=True)
            if vm_stat.returncode == 0:
                lines = vm_stat.stdout.split('\n')
                page_size = 4096  # macOS页面大小
                
                free_pages = 0
                inactive_pages = 0
                speculative_pages = 0
                wired_pages = 0
                active_pages = 0
                
                for line in lines:
                    if 'Pages free:' in line:
                        free_pages = int(line.split(':')[1].strip().rstrip('.'))
                    elif 'Pages inactive:' in line:
                        inactive_pages = int(line.split(':')[1].strip().rstrip('.'))
                    elif 'Pages speculative:' in line:
                        speculative_pages = int(line.split(':')[1].strip().rstrip('.'))
                    elif 'Pages wired down:' in line:
                        wired_pages = int(line.split(':')[1].strip().rstrip('.'))
                    elif 'Pages active:' in line:
                        active_pages = int(line.split(':')[1].strip().rstrip('.'))
                
                # 计算内存使用情况
                total_pages = free_pages + inactive_pages + speculative_pages + wired_pages + active_pages
                used_pages = wired_pages + active_pages
                
                memory_total_gb = (total_pages * page_size) / (1024**3)
                memory_used_gb = (used_pages * page_size) / (1024**3)
                memory_percent = (used_pages / total_pages * 100) if total_pages > 0 else 0
            else:
                memory_total_gb = memory_used_gb = memory_percent = 0.0
            
            # 磁盘使用率
            df_result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
            disk_usage_percent = 0.0
            if df_result.returncode == 0:
                lines = df_result.stdout.split('\n')
                if len(lines) > 1:
                    fields = lines[1].split()
                    if len(fields) >= 5:
                        disk_usage_percent = float(fields[4].rstrip('%'))
            
            # 网络连接数
            netstat_result = subprocess.run(['netstat', '-an'], capture_output=True, text=True)
            network_connections = len([line for line in netstat_result.stdout.split('\n') 
                                     if 'ESTABLISHED' in line]) if netstat_result.returncode == 0 else 0
            
            # 负载平均值
            uptime_result = subprocess.run(['uptime'], capture_output=True, text=True)
            load_average = [0.0, 0.0, 0.0]
            if uptime_result.returncode == 0:
                try:
                    uptime_line = uptime_result.stdout.strip()
                    load_part = uptime_line.split('load averages: ')[1]
                    load_values = [float(x.strip()) for x in load_part.split()]
                    load_average = load_values[:3]
                except:
                    pass
            
            return SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_gb=memory_used_gb,
                memory_total_gb=memory_total_gb,
                disk_usage_percent=disk_usage_percent,
                network_connections=network_connections,
                load_average=load_average
            )
            
        except Exception as e:
            print(f"❌ 获取系统指标失败: {e}")
            return SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=0, memory_percent=0, memory_used_gb=0, memory_total_gb=0,
                disk_usage_percent=0, network_connections=0, load_average=[0, 0, 0]
            )
    
    def get_application_metrics(self) -> ApplicationMetrics:
        """获取应用指标"""
        try:
            # 测试响应时间
            start_time = time.time()
            health_response = requests.get(f"{self.app_url}/health", timeout=5)
            response_time = time.time() - start_time
            
            # 获取优化器统计
            stats_response = requests.get(f"{self.app_url}/get_optimizer_stats", timeout=5)
            optimizer_stats = stats_response.json() if stats_response.status_code == 200 else {}
            
            # 尝试获取异步系统统计
            async_stats = {}
            try:
                async_response = requests.get(f"{self.app_url}/get_async_system_stats", timeout=5)
                if async_response.status_code == 200:
                    async_stats = async_response.json()
            except:
                pass
            
            return ApplicationMetrics(
                timestamp=datetime.now().isoformat(),
                response_time=response_time,
                request_count=optimizer_stats.get('processed', 0),
                success_rate=100.0 if health_response.status_code == 200 else 0.0,
                queue_size=optimizer_stats.get('queue_size', 0),
                worker_threads=optimizer_stats.get('max_workers', 0),
                processed_total=optimizer_stats.get('processed', 0),
                errors=optimizer_stats.get('errors', 0)
            )
            
        except Exception as e:
            print(f"❌ 获取应用指标失败: {e}")
            return ApplicationMetrics(
                timestamp=datetime.now().isoformat(),
                response_time=0, request_count=0, success_rate=0,
                queue_size=0, worker_threads=0, processed_total=0, errors=0
            )
    
    def log_metrics(self, system_metrics: SystemMetrics, app_metrics: ApplicationMetrics):
        """记录指标到日志文件"""
        try:
            with open(self.output_file, 'a') as f:
                log_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'system': asdict(system_metrics),
                    'application': asdict(app_metrics)
                }
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            print(f"❌ 写入日志失败: {e}")
    
    def display_metrics(self, system_metrics: SystemMetrics, app_metrics: ApplicationMetrics):
        """在控制台显示指标"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        print(f"\r📊 [{timestamp}] "
              f"CPU: {system_metrics.cpu_percent:5.1f}% | "
              f"MEM: {system_metrics.memory_percent:5.1f}% "
              f"({system_metrics.memory_used_gb:.1f}GB/{system_metrics.memory_total_gb:.1f}GB) | "
              f"DISK: {system_metrics.disk_usage_percent:4.1f}% | "
              f"NET: {system_metrics.network_connections:3d} | "
              f"LOAD: {system_metrics.load_average[0]:.2f} | "
              f"APP_RT: {app_metrics.response_time*1000:6.1f}ms | "
              f"QUEUE: {app_metrics.queue_size:4d} | "
              f"PROC: {app_metrics.processed_total:6d} | "
              f"ERR: {app_metrics.errors:3d}", end='', flush=True)
    
    def start_monitoring(self):
        """开始监控"""
        print(f"\n🔍 开始系统监控 (按 Ctrl+C 停止)")
        print("=" * 120)
        print("时间     | CPU%  | 内存使用        | 磁盘% | 连接数 | 负载  | 应用RT(ms) | 队列 | 处理数 | 错误")
        print("-" * 120)
        
        self.running = True
        
        try:
            while self.running:
                # 获取指标
                system_metrics = self.get_system_metrics()
                app_metrics = self.get_application_metrics()
                
                # 存储历史数据
                self.system_metrics_history.append(system_metrics)
                self.app_metrics_history.append(app_metrics)
                
                # 保持历史记录数量（最近500个数据点）
                if len(self.system_metrics_history) > 500:
                    self.system_metrics_history.pop(0)
                if len(self.app_metrics_history) > 500:
                    self.app_metrics_history.pop(0)
                
                # 记录日志
                self.log_metrics(system_metrics, app_metrics)
                
                # 显示指标
                self.display_metrics(system_metrics, app_metrics)
                
                # 等待下次采集
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            print(f"\n\n⏸️  监控已停止")
        
        self.generate_summary_report()
    
    def generate_summary_report(self):
        """生成监控总结报告"""
        if not self.system_metrics_history or not self.app_metrics_history:
            print("📊 无足够数据生成报告")
            return
        
        print(f"\n" + "=" * 80)
        print("📊 监控总结报告")
        print("=" * 80)
        
        # 系统指标统计
        cpu_values = [m.cpu_percent for m in self.system_metrics_history]
        memory_values = [m.memory_percent for m in self.system_metrics_history]
        load_values = [m.load_average[0] for m in self.system_metrics_history]
        
        print(f"🖥️  系统指标:")
        print(f"   CPU使用率     - 平均: {sum(cpu_values)/len(cpu_values):5.1f}%  "
              f"最高: {max(cpu_values):5.1f}%  最低: {min(cpu_values):5.1f}%")
        print(f"   内存使用率    - 平均: {sum(memory_values)/len(memory_values):5.1f}%  "
              f"最高: {max(memory_values):5.1f}%  最低: {min(memory_values):5.1f}%")
        print(f"   系统负载      - 平均: {sum(load_values)/len(load_values):5.2f}  "
              f"最高: {max(load_values):5.2f}")
        
        # 应用指标统计
        response_times = [m.response_time * 1000 for m in self.app_metrics_history]  # 转换为毫秒
        queue_sizes = [m.queue_size for m in self.app_metrics_history]
        
        print(f"\n📱 应用指标:")
        print(f"   响应时间(ms)  - 平均: {sum(response_times)/len(response_times):6.1f}  "
              f"最高: {max(response_times):6.1f}  最低: {min(response_times):6.1f}")
        print(f"   队列深度      - 平均: {sum(queue_sizes)/len(queue_sizes):6.1f}  "
              f"最高: {max(queue_sizes):6d}")
        
        # 性能趋势分析
        latest_metrics = self.app_metrics_history[-10:]  # 最近10个数据点
        if len(latest_metrics) >= 10:
            recent_avg_rt = sum(m.response_time * 1000 for m in latest_metrics) / len(latest_metrics)
            print(f"   最近10次平均响应时间: {recent_avg_rt:.1f}ms")
        
        print(f"\n📝 详细日志已保存到: {self.output_file}")
        print(f"📊 总监控时间: {len(self.system_metrics_history) * self.interval:.1f}秒")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='系统性能监控工具')
    parser.add_argument('--url', default='http://localhost:5225', 
                       help='应用服务URL (默认: http://localhost:5225)')
    parser.add_argument('--interval', type=float, default=2.0,
                       help='监控间隔秒数 (默认: 2.0)')
    parser.add_argument('--output', help='输出日志文件路径')
    
    args = parser.parse_args()
    
    print("🚀 系统性能监控工具")
    print("=" * 50)
    
    # 创建监控器
    monitor = SystemMonitor(
        app_url=args.url,
        interval=args.interval,
        output_file=args.output
    )
    
    # 启动监控
    monitor.start_monitoring()

if __name__ == "__main__":
    main()
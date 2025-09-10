#!/usr/bin/env python3
"""
告警规则缓存性能监控脚本
实时监控Redis缓存告警系统的性能指标
"""

import time
import json
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import threading

# 添加当前路径
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from redis_cache_generate_alerts import get_redis_cached_generator

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AlertCacheMonitor:
    """告警缓存性能监控器"""
    
    def __init__(self, interval: int = 10):
        self.interval = interval  # 监控间隔（秒）
        self.running = False
        self.monitor_thread = None
        self.generator = None
        self.history = []  # 历史数据
        self.max_history = 100  # 最大历史记录数
        
    def start_monitoring(self):
        """开始监控"""
        if self.running:
            logger.warning("监控器已在运行中")
            return
            
        print("🔍 启动告警缓存性能监控器")
        try:
            self.generator = get_redis_cached_generator()
            self.running = True
            
            self.monitor_thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True,
                name="AlertCacheMonitor"
            )
            self.monitor_thread.start()
            
            print(f"✅ 监控器已启动，监控间隔: {self.interval}秒")
            
        except Exception as e:
            print(f"❌ 监控器启动失败: {e}")
            self.running = False
            
    def stop_monitoring(self):
        """停止监控"""
        self.running = False
        print("🛑 监控器已停止")
        
    def _monitor_loop(self):
        """监控主循环"""
        print("📊 开始性能监控...")
        print("-" * 80)
        
        while self.running:
            try:
                # 收集性能数据
                metrics = self._collect_metrics()
                
                # 保存历史数据
                self._save_metrics(metrics)
                
                # 显示实时数据
                self._display_metrics(metrics)
                
                # 检查告警
                self._check_alerts(metrics)
                
                # 等待下一次监控
                time.sleep(self.interval)
                
            except Exception as e:
                logger.error(f"监控循环异常: {e}")
                time.sleep(self.interval)
                
    def _collect_metrics(self) -> Dict[str, Any]:
        """收集性能指标"""
        try:
            # 获取基础统计
            stats = self.generator.get_stats()
            
            # 获取当前时间
            timestamp = datetime.now()
            
            # 构建指标数据
            metrics = {
                'timestamp': timestamp,
                'total_processed': stats.get('total_processed', 0),
                'cache_hits': stats.get('cache_hits', 0),
                'db_fallbacks': stats.get('db_fallbacks', 0),
                'cache_hit_rate': stats.get('cache_hit_rate', '0.00%'),
                'alerts_generated': stats.get('alerts_generated', 0),
                'avg_processing_time': stats.get('avg_processing_time', '0.000s'),
            }
            
            # Redis连接状态
            cache_manager_status = stats.get('cache_manager_status', {})
            if isinstance(cache_manager_status, dict):
                redis_status = cache_manager_status.get('redis_connection_status', {})
                metrics['bigscreen_redis_ok'] = redis_status.get('bigscreen_redis', False)
                metrics['boot_redis_ok'] = redis_status.get('boot_redis', False)
                metrics['local_cache_size'] = cache_manager_status.get('local_cache_size', 0)
                metrics['subscriber_running'] = cache_manager_status.get('subscriber_running', False)
            else:
                metrics['bigscreen_redis_ok'] = False
                metrics['boot_redis_ok'] = False
                metrics['local_cache_size'] = 0
                metrics['subscriber_running'] = False
                
            return metrics
            
        except Exception as e:
            logger.error(f"收集指标失败: {e}")
            return {'timestamp': datetime.now(), 'error': str(e)}
            
    def _save_metrics(self, metrics: Dict[str, Any]):
        """保存历史指标"""
        self.history.append(metrics)
        
        # 保持历史记录数量限制
        if len(self.history) > self.max_history:
            self.history.pop(0)
            
    def _display_metrics(self, metrics: Dict[str, Any]):
        """显示实时指标"""
        timestamp = metrics.get('timestamp', datetime.now())
        
        print(f"\n⏰ {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 处理统计: 总计={metrics.get('total_processed', 0)}, 告警={metrics.get('alerts_generated', 0)}")
        print(f"🔥 缓存性能: 命中={metrics.get('cache_hits', 0)}, 兜底={metrics.get('db_fallbacks', 0)}, 命中率={metrics.get('cache_hit_rate', 'N/A')}")
        print(f"⚡ 处理时间: 平均={metrics.get('avg_processing_time', 'N/A')}")
        
        # Redis连接状态
        bigscreen_ok = metrics.get('bigscreen_redis_ok', False)
        boot_ok = metrics.get('boot_redis_ok', False)
        subscriber_ok = metrics.get('subscriber_running', False)
        
        bigscreen_status = "✅" if bigscreen_ok else "❌"
        boot_status = "✅" if boot_ok else "❌"
        subscriber_status = "✅" if subscriber_ok else "❌"
        
        print(f"🔗 连接状态: bigscreen-redis={bigscreen_status}, boot-redis={boot_status}, 订阅者={subscriber_status}")
        print(f"📋 本地缓存: {metrics.get('local_cache_size', 0)}个客户")
        print("-" * 80)
        
    def _check_alerts(self, metrics: Dict[str, Any]):
        """检查性能告警"""
        alerts = []
        
        # 检查Redis连接
        if not metrics.get('bigscreen_redis_ok', True):
            alerts.append("❌ ljwx-bigscreen Redis连接异常")
        if not metrics.get('boot_redis_ok', True):
            alerts.append("❌ ljwx-boot Redis连接异常")
            
        # 检查订阅者状态
        if not metrics.get('subscriber_running', True):
            alerts.append("⚠️ Redis订阅者未运行")
            
        # 检查缓存命中率
        cache_hit_rate_str = metrics.get('cache_hit_rate', '0.00%')
        try:
            cache_hit_rate = float(cache_hit_rate_str.replace('%', ''))
            if cache_hit_rate < 80:
                alerts.append(f"⚠️ 缓存命中率过低: {cache_hit_rate_str}")
        except:
            pass
            
        # 检查数据库兜底频率
        db_fallbacks = metrics.get('db_fallbacks', 0)
        cache_hits = metrics.get('cache_hits', 0)
        total_queries = db_fallbacks + cache_hits
        
        if total_queries > 0:
            fallback_rate = db_fallbacks / total_queries * 100
            if fallback_rate > 20:
                alerts.append(f"⚠️ 数据库兜底频率过高: {fallback_rate:.1f}%")
                
        # 显示告警
        if alerts:
            print("🚨 性能告警:")
            for alert in alerts:
                print(f"  {alert}")
                
    def get_performance_report(self) -> Dict[str, Any]:
        """生成性能报告"""
        if not self.history:
            return {"error": "无历史数据"}
            
        # 计算统计指标
        total_records = len(self.history)
        recent_records = self.history[-10:] if len(self.history) >= 10 else self.history
        
        # 最新状态
        latest = self.history[-1]
        
        # 处理量趋势
        if len(self.history) >= 2:
            first = self.history[0]
            last = self.history[-1]
            processed_growth = last.get('total_processed', 0) - first.get('total_processed', 0)
        else:
            processed_growth = 0
            
        # Redis连接稳定性
        redis_stability = sum(1 for m in recent_records if m.get('bigscreen_redis_ok') and m.get('boot_redis_ok')) / len(recent_records) * 100
        
        return {
            'report_time': datetime.now().isoformat(),
            'monitoring_duration': f"{total_records * self.interval}秒",
            'total_records': total_records,
            'latest_status': {
                'total_processed': latest.get('total_processed', 0),
                'cache_hit_rate': latest.get('cache_hit_rate', 'N/A'),
                'local_cache_size': latest.get('local_cache_size', 0),
                'redis_connections_ok': latest.get('bigscreen_redis_ok', False) and latest.get('boot_redis_ok', False)
            },
            'performance_trends': {
                'processed_growth': processed_growth,
                'redis_stability': f"{redis_stability:.1f}%",
            },
            'recommendations': self._generate_recommendations(recent_records)
        }
        
    def _generate_recommendations(self, recent_records: List[Dict]) -> List[str]:
        """生成性能建议"""
        recommendations = []
        
        if not recent_records:
            return recommendations
            
        # 检查缓存命中率
        avg_cache_hits = sum(r.get('cache_hits', 0) for r in recent_records) / len(recent_records)
        avg_db_fallbacks = sum(r.get('db_fallbacks', 0) for r in recent_records) / len(recent_records)
        
        if avg_db_fallbacks > avg_cache_hits:
            recommendations.append("建议检查Redis缓存配置，数据库兜底频率过高")
            
        # 检查Redis连接稳定性
        disconnection_count = sum(1 for r in recent_records 
                                if not (r.get('bigscreen_redis_ok', True) and r.get('boot_redis_ok', True)))
        if disconnection_count > 0:
            recommendations.append("发现Redis连接不稳定，建议检查网络和Redis服务状态")
            
        # 检查订阅者状态
        subscriber_down_count = sum(1 for r in recent_records if not r.get('subscriber_running', True))
        if subscriber_down_count > 0:
            recommendations.append("Redis订阅者存在中断，建议检查订阅者服务状态")
            
        # 检查本地缓存大小
        latest_cache_size = recent_records[-1].get('local_cache_size', 0)
        if latest_cache_size == 0:
            recommendations.append("本地缓存为空，可能需要预加载常用客户的告警规则")
        elif latest_cache_size > 100:
            recommendations.append("本地缓存过大，建议优化缓存策略或增加内存限制")
            
        if not recommendations:
            recommendations.append("系统运行正常，无特殊建议")
            
        return recommendations
        
    def save_report_to_file(self, filename: str = None):
        """保存性能报告到文件"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"alert_cache_performance_report_{timestamp}.json"
            
        report = self.get_performance_report()
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            print(f"📄 性能报告已保存: {filename}")
        except Exception as e:
            print(f"❌ 保存报告失败: {e}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="告警规则缓存性能监控")
    parser.add_argument('-i', '--interval', type=int, default=10, help='监控间隔（秒）')
    parser.add_argument('-d', '--duration', type=int, default=0, help='监控时长（秒），0表示持续监控')
    parser.add_argument('-r', '--report', action='store_true', help='生成性能报告文件')
    
    args = parser.parse_args()
    
    monitor = AlertCacheMonitor(interval=args.interval)
    
    try:
        # 启动监控
        monitor.start_monitoring()
        
        if args.duration > 0:
            # 定时监控
            print(f"⏱️ 将监控{args.duration}秒后自动停止")
            time.sleep(args.duration)
            monitor.stop_monitoring()
            
            # 生成报告
            if args.report:
                monitor.save_report_to_file()
        else:
            # 持续监控
            print("⌨️ 按 Ctrl+C 停止监控")
            try:
                while monitor.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n⏹️ 收到停止信号")
                monitor.stop_monitoring()
                
                if args.report:
                    monitor.save_report_to_file()
                    
    except Exception as e:
        print(f"❌ 监控过程出现异常: {e}")
        monitor.stop_monitoring()
    
    print("👋 监控结束")

if __name__ == "__main__":
    main()
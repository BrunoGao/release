#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""1000台设备性能监控工具"""
import time,requests,json,threading
from datetime import datetime,timedelta
import mysql.connector
from logging_config import system_logger

class PerformanceMonitor:#性能监控器
    """1000台设备性能监控工具"""
    def __init__(self,db_config=None):
        self.db_config=db_config or {
            'host':'127.0.0.1',
            'port':3306,
            'user':'root',
            'password':'123456',
            'database':'lj-06',
            'charset':'utf8mb4'
        }
        self.running=False
        self.stats={
            'total_uploads':0,
            'success_rate':0,
            'avg_response_time':0,
            'db_connections':0,
            'memory_usage':0,
            'cpu_usage':0
        }
        
    def get_db_stats(self):#获取数据库统计
        """获取数据库性能统计"""
        try:
            conn=mysql.connector.connect(**self.db_config)
            cursor=conn.cursor()
            
            # 查询健康数据总量
            cursor.execute("SELECT COUNT(*) FROM t_user_health_data WHERE DATE(create_time) = CURDATE()")
            today_health_count=cursor.fetchone()[0]
            
            # 查询最近10分钟的数据量
            cursor.execute("SELECT COUNT(*) FROM t_user_health_data WHERE create_time >= DATE_SUB(NOW(), INTERVAL 10 MINUTE)")
            recent_count=cursor.fetchone()[0]
            
            # 查询数据库连接数
            cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
            connections=cursor.fetchone()[1]
            
            # 查询慢查询数量
            cursor.execute("SHOW STATUS LIKE 'Slow_queries'")
            slow_queries=cursor.fetchone()[1]
            
            cursor.close()
            conn.close()
            
            return {
                'today_health_count':today_health_count,
                'recent_10min_count':recent_count,
                'db_connections':int(connections),
                'slow_queries':int(slow_queries)
            }
            
        except Exception as e:
            system_logger.error('获取数据库统计失败',extra={'error':str(e)})
            return {}
            
    def get_api_stats(self):#获取API统计
        """获取大屏API性能统计"""
        try:
            start_time=time.time()
            response=requests.get('http://localhost:5001/optimizer_stats',timeout=5)
            response_time=time.time()-start_time
            
            if response.status_code==200:
                data=response.json()
                data['api_response_time']=response_time
                return data
            else:
                return {'error':'API响应异常','status':response.status_code}
                
        except Exception as e:
            return {'error':str(e),'api_response_time':999}
            
    def get_system_metrics(self):#获取系统指标
        """获取系统性能指标"""
        try:
            import psutil
            
            # CPU使用率
            cpu_percent=psutil.cpu_percent(interval=1)
            
            # 内存使用率
            memory=psutil.virtual_memory()
            
            # 磁盘I/O
            disk_io=psutil.disk_io_counters()
            
            # 网络连接数
            try:
                connections=len(psutil.net_connections())
            except:
                connections=0
                
            return {
                'cpu_percent':cpu_percent,
                'memory_percent':memory.percent,
                'memory_used_gb':round(memory.used/1024/1024/1024,2),
                'memory_total_gb':round(memory.total/1024/1024/1024,2),
                'disk_read_mb':round(disk_io.read_bytes/1024/1024,2) if disk_io else 0,
                'disk_write_mb':round(disk_io.write_bytes/1024/1024,2) if disk_io else 0,
                'network_connections':connections
            }
            
        except ImportError:
            system_logger.warning('psutil未安装，使用模拟数据')
            return {
                'cpu_percent':0,
                'memory_percent':0,
                'memory_used_gb':0,
                'memory_total_gb':0,
                'disk_read_mb':0,
                'disk_write_mb':0,
                'network_connections':0
            }
        except Exception as e:
            system_logger.error('获取系统指标失败',extra={'error':str(e)})
            return {}
            
    def generate_report(self):#生成报告
        """生成性能监控报告"""
        print("\n" + "="*80)
        print(f"📊 1000台设备性能监控报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # 数据库统计
        db_stats=self.get_db_stats()
        if db_stats:
            print(f"📊 数据库统计:")
            print(f"   今日健康数据总量: {db_stats.get('today_health_count',0):,} 条")
            print(f"   最近10分钟数据: {db_stats.get('recent_10min_count',0):,} 条")
            print(f"   数据库连接数: {db_stats.get('db_connections',0)}")
            print(f"   慢查询数量: {db_stats.get('slow_queries',0)}")
            
        # API统计
        api_stats=self.get_api_stats()
        if 'error' not in api_stats:
            print(f"\n🚀 API性能统计:")
            print(f"   响应时间: {api_stats.get('api_response_time',0):.3f} 秒")
            if 'data' in api_stats:
                optimizer_data=api_stats['data']
                print(f"   总处理请求: {optimizer_data.get('total_requests',0):,}")
                print(f"   成功处理数: {optimizer_data.get('success_count',0):,}")
                print(f"   处理错误数: {optimizer_data.get('error_count',0)}")
                print(f"   平均处理时间: {optimizer_data.get('avg_processing_time',0):.3f} 秒")
        else:
            print(f"\n❌ API统计获取失败: {api_stats.get('error','未知错误')}")
            
        # 系统指标
        sys_metrics=self.get_system_metrics()
        if sys_metrics:
            print(f"\n💻 系统性能指标:")
            print(f"   CPU使用率: {sys_metrics.get('cpu_percent',0):.1f}%")
            print(f"   内存使用率: {sys_metrics.get('memory_percent',0):.1f}%")
            print(f"   内存使用量: {sys_metrics.get('memory_used_gb',0):.2f}GB / {sys_metrics.get('memory_total_gb',0):.2f}GB")
            print(f"   磁盘读取: {sys_metrics.get('disk_read_mb',0):.2f}MB")
            print(f"   磁盘写入: {sys_metrics.get('disk_write_mb',0):.2f}MB")
            print(f"   网络连接数: {sys_metrics.get('network_connections',0)}")
            
        # 性能建议
        self.generate_recommendations(db_stats,api_stats,sys_metrics)
        
        print("="*80)
        
    def generate_recommendations(self,db_stats,api_stats,sys_metrics):#生成建议
        """生成性能优化建议"""
        print(f"\n💡 性能优化建议:")
        
        recommendations=[]
        
        # 数据库建议
        if db_stats.get('slow_queries',0)>10:
            recommendations.append("- 数据库出现慢查询，建议优化索引")
            
        if db_stats.get('db_connections',0)>100:
            recommendations.append("- 数据库连接数较高，建议优化连接池配置")
            
        # API建议
        if api_stats.get('api_response_time',0)>1:
            recommendations.append("- API响应时间超过1秒，建议检查服务性能")
            
        # 系统建议
        if sys_metrics.get('cpu_percent',0)>80:
            recommendations.append("- CPU使用率过高，建议减少并发量或扩容")
            
        if sys_metrics.get('memory_percent',0)>85:
            recommendations.append("- 内存使用率过高，建议检查内存泄漏或扩容")
            
        if not recommendations:
            recommendations.append("- 系统运行正常，性能表现良好")
            
        for rec in recommendations:
            print(f"  {rec}")
            
    def start_monitoring(self,interval=30):#开始监控
        """开始性能监控"""
        self.running=True
        system_logger.info(f"开始性能监控，间隔{interval}秒")
        
        try:
            while self.running:
                self.generate_report()
                time.sleep(interval)
                
        except KeyboardInterrupt:
            system_logger.info("收到中断信号，停止监控")
            self.stop_monitoring()
            
    def stop_monitoring(self):#停止监控
        """停止性能监控"""
        self.running=False
        system_logger.info("性能监控已停止")

def main():#主函数
    """主函数"""
    import argparse
    
    parser=argparse.ArgumentParser(description='1000台设备性能监控工具')
    parser.add_argument('--interval',type=int,default=30,help='监控间隔(秒)')
    parser.add_argument('--once',action='store_true',help='仅生成一次报告')
    
    args=parser.parse_args()
    
    monitor=PerformanceMonitor()
    
    if args.once:
        monitor.generate_report()
    else:
        monitor.start_monitoring(args.interval)

if __name__=="__main__":
    main() 
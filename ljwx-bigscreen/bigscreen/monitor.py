#!/usr/bin/env python3
import psutil,pymysql,time,sys,os
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import MYSQL_CONFIG

class SystemMonitor:#系统监控类
    def __init__(self):
        self.mysql_config=MYSQL_CONFIG#MySQL配置
        self.prev_net=psutil.net_io_counters()#上次网络IO
        self.prev_disk=psutil.disk_io_counters()#上次磁盘IO
        
    def get_mysql_metrics(self):#获取MySQL详细指标
        try:
            conn=pymysql.connect(**self.mysql_config,autocommit=True)
            with conn.cursor() as c:
                c.execute("SHOW GLOBAL STATUS")#获取全局状态
                status=dict(c.fetchall())
                c.execute("SHOW PROCESSLIST")#获取进程列表
                processes=c.fetchall();conn.close()
                
                return {
                    'connections':int(status.get('Threads_connected',0)),#连接数
                    'queries':int(status.get('Queries',0)),#查询总数
                    'slow_queries':int(status.get('Slow_queries',0)),#慢查询
                    'buffer_reads':int(status.get('Innodb_buffer_pool_reads',0)),#物理读
                    'buffer_requests':int(status.get('Innodb_buffer_pool_read_requests',0)),#逻辑读
                    'lock_waits':int(status.get('Table_locks_waited',0)),#锁等待
                    'processes':len(processes),#活跃进程
                    'uptime':int(status.get('Uptime',0))#运行时间
                }
        except Exception as e:
            print(f"❌MySQL连接失败: {e}")
            return {}
            
    def get_system_metrics(self):#获取系统详细指标
        cpu=psutil.cpu_percent(interval=1,percpu=True)#各CPU核心使用率
        mem=psutil.virtual_memory()#内存信息
        swap=psutil.swap_memory()#交换内存
        curr_net=psutil.net_io_counters()#当前网络IO
        curr_disk=psutil.disk_io_counters()#当前磁盘IO
        
        net_speed_recv=(curr_net.bytes_recv-self.prev_net.bytes_recv)/1024/1024#网络接收速度MB/s
        net_speed_sent=(curr_net.bytes_sent-self.prev_net.bytes_sent)/1024/1024#网络发送速度MB/s
        disk_read_speed=(curr_disk.read_bytes-self.prev_disk.read_bytes)/1024/1024#磁盘读速度MB/s
        disk_write_speed=(curr_disk.write_bytes-self.prev_disk.write_bytes)/1024/1024#磁盘写速度MB/s
        
        self.prev_net,self.prev_disk=curr_net,curr_disk#更新上次数据
        
        return {
            'cpu_avg':sum(cpu)/len(cpu),#平均CPU使用率
            'cpu_cores':cpu,#各核心使用率
            'mem_percent':mem.percent,#内存使用率
            'mem_used':mem.used/1024/1024/1024,#已用内存GB
            'mem_total':mem.total/1024/1024/1024,#总内存GB
            'swap_percent':swap.percent,#交换内存使用率
            'disk_read_speed':disk_read_speed,#磁盘读速度
            'disk_write_speed':disk_write_speed,#磁盘写速度
            'net_recv_speed':net_speed_recv,#网络接收速度
            'net_sent_speed':net_speed_sent,#网络发送速度
            'load_avg':os.getloadavg()#系统负载
        }
        
    def print_metrics(self,sys_metrics,mysql_metrics):#打印监控指标
        now=datetime.now().strftime('%H:%M:%S')
        print(f'\n⏰ {now} 系统监控')
        print('='*60)
        
        #系统指标
        print(f'🖥️  CPU: {sys_metrics["cpu_avg"]:.1f}% | 负载: {sys_metrics["load_avg"][0]:.2f}')
        print(f'🧠 内存: {sys_metrics["mem_percent"]:.1f}% ({sys_metrics["mem_used"]:.1f}GB/{sys_metrics["mem_total"]:.1f}GB)')
        print(f'💾 交换: {sys_metrics["swap_percent"]:.1f}%')
        print(f'📊 磁盘: 读{sys_metrics["disk_read_speed"]:.1f}MB/s 写{sys_metrics["disk_write_speed"]:.1f}MB/s')
        print(f'🌐 网络: 收{sys_metrics["net_recv_speed"]:.1f}MB/s 发{sys_metrics["net_sent_speed"]:.1f}MB/s')
        
        #MySQL指标
        if mysql_metrics:
            hit_rate=(1-mysql_metrics["buffer_reads"]/max(mysql_metrics["buffer_requests"],1))*100
            print(f'🗄️  MySQL连接: {mysql_metrics["connections"]} | 进程: {mysql_metrics["processes"]}')
            print(f'📈 查询: {mysql_metrics["queries"]} | 慢查询: {mysql_metrics["slow_queries"]}')
            print(f'💿 缓存命中率: {hit_rate:.1f}% | 锁等待: {mysql_metrics["lock_waits"]}')
            print(f'⏱️  运行时间: {mysql_metrics["uptime"]//3600}小时{(mysql_metrics["uptime"]%3600)//60}分钟')
            
    def run(self,interval=5):#运行监控
        print('🚀启动系统监控，每{}秒刷新一次，按Ctrl+C停止'.format(interval))
        try:
            while True:
                sys_metrics=self.get_system_metrics()
                mysql_metrics=self.get_mysql_metrics()
                self.print_metrics(sys_metrics,mysql_metrics)
                time.sleep(interval)
        except KeyboardInterrupt:
            print('\n🛑监控已停止')

if __name__=='__main__':
    monitor=SystemMonitor()
    monitor.run(interval=3)#每3秒监控一次 
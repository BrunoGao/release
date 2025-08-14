#!/usr/bin/env python3
import requests,json,time,threading,random,psutil,pymysql,sys,os
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from collections import defaultdict
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import STRESS_TEST_CONFIG,MYSQL_CONFIG,HEALTH_DATA_RANGES

class StressTest:#压力测试类
    def __init__(self):
        self.url=STRESS_TEST_CONFIG['URL']#目标接口
        self.base_id=STRESS_TEST_CONFIG['BASE_ID']#基础设备ID
        self.device_count=STRESS_TEST_CONFIG['DEVICE_COUNT']#设备数量
        self.interval=STRESS_TEST_CONFIG['INTERVAL']#上传间隔秒数
        self.max_workers=STRESS_TEST_CONFIG['MAX_WORKERS']#线程数
        self.timeout=STRESS_TEST_CONFIG['TIMEOUT']#超时时间
        self.stats={'total':0,'success':0,'error':0,'times':[],'backlog':0}#统计数据
        self.mysql_config=MYSQL_CONFIG#MySQL配置
        self.last_batch_time=0#上次批次耗时
        self.adaptive_mode=True#自适应模式
        
    def gen_device_id(self,idx):#生成设备ID
        return f'A5GTQ24B{int(self.base_id[-8:])+idx:08d}'
        
    def gen_health_data(self,device_id):#生成健康数据
        r=HEALTH_DATA_RANGES#简化配置引用
        return {'data':{
            'id':device_id,'upload_method':'wifi',
            'heart_rate':random.randint(*r['heart_rate']),#心率
            'blood_oxygen':random.randint(*r['blood_oxygen']),#血氧
            'body_temperature':f'{random.uniform(*r["body_temperature"]):.1f}',#体温
            'blood_pressure_systolic':random.randint(*r['blood_pressure_systolic']),#收缩压
            'blood_pressure_diastolic':random.randint(*r['blood_pressure_diastolic']),#舒张压
            'step':random.randint(*r['step']),#步数
            'distance':f'{random.uniform(*r["distance"]):.1f}',#距离
            'calorie':f'{random.uniform(*r["calorie"]):.1f}',#卡路里
            'latitude':f'{random.uniform(*r["latitude"]):.14f}',#纬度
            'longitude':f'{random.uniform(*r["longitude"]):.14f}',#经度
            'altitude':'0.0','stress':random.randint(*r['stress']),#压力
            'sleepData':'{"code":0,"data":[{"endTimeStamp":1747440420000,"startTimeStamp":1747418280000,"type":2}],"name":"sleep","type":"history"}',
            'exerciseDailyData':'{"code":0,"data":[{"strengthTimes":2,"totalTime":5}],"name":"daily","type":"history"}',
            'exerciseWeekData':'null','scientificSleepData':'null',
            'workoutData':'{"code":0,"data":[],"name":"workout","type":"history"}'}}
            
    def upload_data(self,device_id):#上传单个设备数据
        start=time.time()
        try:
            data=self.gen_health_data(device_id)
            resp=requests.post(self.url,json=data,timeout=self.timeout)
            elapsed=time.time()-start;self.stats['times'].append(elapsed)
            return 1 if resp.status_code==200 else 0,resp.status_code
        except Exception as e:
            return 0,f'ERROR-{str(e)[:15]}'
            
    def get_system_stats(self):#获取系统指标
        cpu=psutil.cpu_percent(interval=1);mem=psutil.virtual_memory()
        disk=psutil.disk_io_counters();net=psutil.net_io_counters()
        return {'cpu':cpu,'mem':mem.percent,'disk_r':disk.read_bytes,'disk_w':disk.write_bytes,'net_r':net.bytes_recv,'net_s':net.bytes_sent}
        
    def get_mysql_stats(self):#获取MySQL指标
        try:
            conn=pymysql.connect(**self.mysql_config,autocommit=True)
            with conn.cursor() as cursor:
                cursor.execute("SHOW GLOBAL STATUS WHERE Variable_name IN ('Threads_connected','Queries','Innodb_buffer_pool_reads','Innodb_buffer_pool_read_requests')")
                stats=dict(cursor.fetchall());conn.close()
                return {'conn':int(stats.get('Threads_connected',0)),'queries':int(stats.get('Queries',0)),'reads':int(stats.get('Innodb_buffer_pool_reads',0)),'requests':int(stats.get('Innodb_buffer_pool_read_requests',0))}
        except:return {'conn':0,'queries':0,'reads':0,'requests':0}
            
    def auto_adjust_params(self,elapsed):#自动调整参数
        if not self.adaptive_mode:return
        
        backlog_seconds=max(0,elapsed-self.interval)#积压时间
        self.stats['backlog']+=backlog_seconds
        
        if elapsed>self.interval*2:#严重积压
            self.device_count=max(100,int(self.device_count*0.7))#减少设备数
            self.max_workers=min(100,int(self.max_workers*1.2))#增加线程
            print(f'⚠️严重积压！调整参数: 设备数→{self.device_count} 线程数→{self.max_workers}')
        elif elapsed>self.interval*1.5:#中度积压
            self.device_count=max(200,int(self.device_count*0.8))
            print(f'⚠️中度积压！调整设备数→{self.device_count}')
        elif elapsed<self.interval*0.5 and self.device_count<STRESS_TEST_CONFIG['DEVICE_COUNT']:#性能富余
            self.device_count=min(STRESS_TEST_CONFIG['DEVICE_COUNT'],int(self.device_count*1.1))
            print(f'✅性能富余！恢复设备数→{self.device_count}')
            
    def batch_upload(self):#批量上传
        device_ids=[self.gen_device_id(i) for i in range(self.device_count)]
        sys_before=self.get_system_stats();mysql_before=self.get_mysql_stats();start_time=time.time()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:#线程并发
            results=list(executor.map(self.upload_data,device_ids))
            
        elapsed=time.time()-start_time;self.last_batch_time=elapsed;self.auto_adjust_params(elapsed)
        sys_after=self.get_system_stats();mysql_after=self.get_mysql_stats()
        success_count=sum(r[0] for r in results);error_count=self.device_count-success_count
        self.stats['total']+=self.device_count;self.stats['success']+=success_count;self.stats['error']+=error_count
        
        avg_time=sum(self.stats['times'][-self.device_count:])/len(self.stats['times'][-self.device_count:]) if self.stats['times'] else 0
        success_rate=success_count/self.device_count*100;mysql_qps=(mysql_after['queries']-mysql_before['queries'])/elapsed if elapsed>0 else 0
        
        backlog_status='🔥积压' if elapsed>self.interval else '✅正常'
        print(f'{backlog_status} 批次完成: {success_count}/{self.device_count}成功({success_rate:.1f}%) 耗时:{elapsed:.2f}s 平均:{avg_time*1000:.0f}ms')
        print(f'💻系统: CPU:{sys_after["cpu"]:.1f}% 内存:{sys_after["mem"]:.1f}% 网络:{(sys_after["net_r"]+sys_after["net_s"])/1024/1024:.1f}MB')
        print(f'🗄️MySQL: 连接数:{mysql_after["conn"]} QPS:{mysql_qps:.0f} 缓存命中率:{(1-mysql_after["reads"]/max(mysql_after["requests"],1))*100:.1f}%')
        if self.stats['backlog']>0:print(f'📈积压时间: {self.stats["backlog"]:.1f}秒')
        
    def print_summary(self):#打印测试总结
        if self.stats['total']>0:
            total_rate=self.stats['success']/self.stats['total']*100
            avg_response=sum(self.stats['times'])/len(self.stats['times'])*1000 if self.stats['times'] else 0
            print(f'\n📊测试总结:')
            print(f'总请求: {self.stats["total"]} | 成功: {self.stats["success"]} | 失败: {self.stats["error"]} | 成功率: {total_rate:.2f}%')
            print(f'平均响应时间: {avg_response:.0f}ms | 最快: {min(self.stats["times"])*1000:.0f}ms | 最慢: {max(self.stats["times"])*1000:.0f}ms')
            print(f'总积压时间: {self.stats["backlog"]:.1f}秒 | 最终设备数: {self.device_count} | 最终线程数: {self.max_workers}')
            
    def smart_wait(self):#智能等待避免积压
        wait_time=max(0,self.interval-self.last_batch_time)#计算实际等待时间
        if wait_time>0:
            print(f'⏰等待{wait_time:.1f}秒...')
            time.sleep(wait_time)
        else:
            print(f'🔥无等待时间，立即开始下批')
            
    def run(self):#运行压力测试
        print(f'🚀开始自适应压力测试: {self.device_count}设备, 目标间隔{self.interval}秒')
        print(f'🎯自适应模式: {"开启" if self.adaptive_mode else "关闭"}')
        batch_num=1
        
        try:
            while True:
                print(f'\n📡第{batch_num}批上传开始...')
                self.batch_upload()
                self.smart_wait()
                batch_num+=1
        except KeyboardInterrupt:
            print('\n🛑压力测试已停止')
            self.print_summary()

if __name__=='__main__':
    StressTest().run()#启动测试 
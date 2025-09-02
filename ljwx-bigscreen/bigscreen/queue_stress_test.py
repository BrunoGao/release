#!/usr/bin/env python3
import requests,json,time,threading,random,psutil,pymysql,sys,os,queue
from concurrent.futures import ThreadPoolExecutor,as_completed
from decimal import Decimal
from collections import defaultdict
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import STRESS_TEST_CONFIG,MYSQL_CONFIG,HEALTH_DATA_RANGES

class QueueStressTest:#基于队列的压力测试类
    def __init__(self):
        self.url=STRESS_TEST_CONFIG['URL']#目标接口
        self.base_id=STRESS_TEST_CONFIG['BASE_ID']#基础设备ID
        self.target_qps=200#目标QPS
        self.max_workers=100#最大线程数
        self.timeout=STRESS_TEST_CONFIG['TIMEOUT']#超时时间
        self.task_queue=queue.Queue(maxsize=10000)#任务队列
        self.result_queue=queue.Queue()#结果队列
        self.stats={'total':0,'success':0,'error':0,'times':[],'qps_history':[]}#统计数据
        self.mysql_config=MYSQL_CONFIG#MySQL配置
        self.running=False#运行状态
        
    def gen_device_id(self,idx):#生成设备ID
        return f'A5GTQ24B{int(self.base_id[-8:])+idx:08d}'
        
    def gen_health_data(self,device_id):#生成健康数据
        r=HEALTH_DATA_RANGES
        return {'data':{
            'id':device_id,'upload_method':'wifi',
            'heart_rate':random.randint(*r['heart_rate']),
            'blood_oxygen':random.randint(*r['blood_oxygen']),
            'body_temperature':f'{random.uniform(*r["body_temperature"]):.1f}',
            'blood_pressure_systolic':random.randint(*r['blood_pressure_systolic']),
            'blood_pressure_diastolic':random.randint(*r['blood_pressure_diastolic']),
            'step':random.randint(*r['step']),
            'distance':f'{random.uniform(*r["distance"]):.1f}',
            'calorie':f'{random.uniform(*r["calorie"]):.1f}',
            'latitude':f'{random.uniform(*r["latitude"]):.14f}',
            'longitude':f'{random.uniform(*r["longitude"]):.14f}',
            'altitude':'0.0','stress':random.randint(*r['stress']),
            'sleepData':'{"code":0,"data":[],"name":"sleep","type":"history"}',
            'exerciseDailyData':'{"code":0,"data":[],"name":"daily","type":"history"}',
            'exerciseWeekData':'null','scientificSleepData':'null',
            'workoutData':'{"code":0,"data":[],"name":"workout","type":"history"}'}}
            
    def worker(self):#工作线程
        while self.running:
            try:
                device_id=self.task_queue.get(timeout=1)
                start=time.time()
                data=self.gen_health_data(device_id)
                resp=requests.post(self.url,json=data,timeout=self.timeout)
                elapsed=time.time()-start
                success=1 if resp.status_code==200 else 0
                self.result_queue.put((success,elapsed,resp.status_code))
                self.task_queue.task_done()
            except queue.Empty:continue
            except Exception as e:
                self.result_queue.put((0,0,f'ERROR-{str(e)[:15]}'))
                self.task_queue.task_done()
                
    def producer(self):#生产者线程
        device_idx=0
        while self.running:
            try:
                device_id=self.gen_device_id(device_idx)
                self.task_queue.put(device_id,timeout=1)
                device_idx+=1
                time.sleep(1.0/self.target_qps)#控制QPS
            except queue.Full:
                print('⚠️队列已满，降低QPS')
                time.sleep(0.1)
                
    def monitor(self):#监控线程
        last_total=0;start_time=time.time()
        while self.running:
            time.sleep(5)#每5秒统计一次
            current_total=self.stats['total']
            current_qps=(current_total-last_total)/5
            self.stats['qps_history'].append(current_qps)
            
            queue_size=self.task_queue.qsize()
            success_rate=self.stats['success']/max(self.stats['total'],1)*100
            avg_time=sum(self.stats['times'][-100:])/len(self.stats['times'][-100:])*1000 if self.stats['times'] else 0
            
            print(f'📊实时监控: QPS:{current_qps:.1f} 队列:{queue_size} 成功率:{success_rate:.1f}% 平均响应:{avg_time:.0f}ms')
            
            #自动调节QPS
            if queue_size>5000:#队列积压严重
                self.target_qps=max(50,self.target_qps*0.8)
                print(f'⚠️队列积压，降低目标QPS→{self.target_qps:.0f}')
            elif queue_size<1000 and success_rate>95:#性能富余
                self.target_qps=min(500,self.target_qps*1.1)
                print(f'✅性能富余，提高目标QPS→{self.target_qps:.0f}')
                
            last_total=current_total
            
    def collector(self):#结果收集线程
        while self.running:
            try:
                success,elapsed,status=self.result_queue.get(timeout=1)
                self.stats['total']+=1
                if success:self.stats['success']+=1
                else:self.stats['error']+=1
                if elapsed>0:self.stats['times'].append(elapsed)
                self.result_queue.task_done()
            except queue.Empty:continue
            
    def get_mysql_stats(self):#获取MySQL指标
        try:
            conn=pymysql.connect(**self.mysql_config,autocommit=True)
            with conn.cursor() as c:
                c.execute("SHOW GLOBAL STATUS WHERE Variable_name IN ('Threads_connected','Queries')")
                stats=dict(c.fetchall());conn.close()
                return {'conn':int(stats.get('Threads_connected',0)),'queries':int(stats.get('Queries',0))}
        except:return {'conn':0,'queries':0}
        
    def print_summary(self):#打印测试总结
        if self.stats['total']>0:
            total_rate=self.stats['success']/self.stats['total']*100
            avg_response=sum(self.stats['times'])/len(self.stats['times'])*1000 if self.stats['times'] else 0
            max_qps=max(self.stats['qps_history']) if self.stats['qps_history'] else 0
            avg_qps=sum(self.stats['qps_history'])/len(self.stats['qps_history']) if self.stats['qps_history'] else 0
            
            print(f'\n📊队列压力测试总结:')
            print(f'总请求: {self.stats["total"]} | 成功: {self.stats["success"]} | 失败: {self.stats["error"]} | 成功率: {total_rate:.2f}%')
            print(f'平均响应: {avg_response:.0f}ms | 最快: {min(self.stats["times"])*1000:.0f}ms | 最慢: {max(self.stats["times"])*1000:.0f}ms')
            print(f'平均QPS: {avg_qps:.1f} | 峰值QPS: {max_qps:.1f} | 目标QPS: {self.target_qps:.0f}')
            
    def run(self,duration=300):#运行测试
        print(f'🚀启动队列压力测试，目标QPS:{self.target_qps}，运行{duration}秒')
        self.running=True
        
        #启动工作线程
        workers=[threading.Thread(target=self.worker,daemon=True) for _ in range(self.max_workers)]
        for w in workers:w.start()
        
        #启动其他线程
        threading.Thread(target=self.producer,daemon=True).start()
        threading.Thread(target=self.monitor,daemon=True).start()
        threading.Thread(target=self.collector,daemon=True).start()
        
        try:
            time.sleep(duration)
            print('\n🛑时间到，停止测试...')
        except KeyboardInterrupt:
            print('\n🛑手动停止测试...')
        finally:
            self.running=False
            self.task_queue.join()
            self.result_queue.join()
            self.print_summary()

if __name__=='__main__':
    test=QueueStressTest()
    test.run(duration=60)#运行60秒 
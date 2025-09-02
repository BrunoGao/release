#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""1000台手表批量数据模拟器"""
import requests,json,time,random,threading,queue
from datetime import datetime,timedelta
from concurrent.futures import ThreadPoolExecutor
import mysql.connector
from logging_config import system_logger,device_logger,db_logger

class DeviceBatchSimulator:#批量设备模拟器
    """1000台手表批量数据模拟器"""
    def __init__(self,base_url='http://localhost:5001',db_config=None):
        self.base_url=base_url
        self.device_count=1000#设备数量
        self.upload_interval=10#上传间隔(秒)
        self.running=False
        self.devices=[]#设备列表
        self.db_config=db_config or {
            'host':'127.0.0.1',
            'port':3306,
            'user':'root', 
            'password':'123456',
            'database':'lj-06',
            'charset':'utf8mb4'
        }
        
    def generate_device_info(self,index):#生成设备信息
        """生成单个设备信息"""
        serial_base='BBBTQ24B26'
        serial_number=f"{serial_base}{index:06d}"#6位数字补齐
        
        # 生成变化的设备参数
        wifi_mac=':'.join([f'{random.randint(0,255):02x}' for _ in range(6)])
        bt_mac=':'.join([f'{random.randint(0,255):02x}' for _ in range(6)])
        ip_last=random.randint(100,254)
        imei=f"86{random.randint(1000000000000,9999999999999)}"
        battery=random.randint(20,95)
        voltage=random.randint(3500,4200)
        
        return {
            'System Software Version':'ARC-AL00CN 4.0.0.900(SP41C700E104R412P100)',
            'Wifi Address':wifi_mac,
            'Bluetooth Address':bt_mac,
            'IP Address':f'192.168.31.{ip_last}\\nfe80::7d:70ff:fef5:a220',
            'Network Access Mode':2,
            'SerialNumber':serial_number,
            'Device Name':f'HUAWEI WATCH 4-{index:03d}',
            'IMEI':imei,
            'batteryLevel':battery,
            'voltage':voltage,
            'chargingStatus':random.choice(['NONE','CHARGING']),
            'status':'ACTIVE',
            'wearState':random.choice([0,1])
        }
        
    def register_device(self,device_info):#注册设备
        """向数据库注册单个设备"""
        try:
            response=requests.post(f"{self.base_url}/upload_device_info",json=device_info,timeout=30)
            if response.status_code==200:
                device_logger.info('设备注册成功',extra={'device_sn':device_info['SerialNumber']})
                return True
            else:
                device_logger.error('设备注册失败',extra={'device_sn':device_info['SerialNumber'],'status':response.status_code})
                return False
        except Exception as e:
            device_logger.error('设备注册异常',extra={'device_sn':device_info['SerialNumber'],'error':str(e)})
            return False
            
    def batch_register_devices(self):#批量注册设备
        """批量注册1000台设备"""
        system_logger.info(f"开始批量注册{self.device_count}台设备")
        
        with ThreadPoolExecutor(max_workers=20) as executor:#并发注册
            futures=[]
            
            for i in range(1,self.device_count+1):
                device_info=self.generate_device_info(i)
                self.devices.append(device_info['SerialNumber'])
                future=executor.submit(self.register_device,device_info)
                futures.append(future)
                
                if i%100==0:#每100台显示进度
                    system_logger.info(f"已提交{i}台设备注册任务")
                    
            # 等待所有注册完成
            success_count=sum(1 for future in futures if future.result())
            system_logger.info(f"设备注册完成: 成功{success_count}/{self.device_count}台")
            
    def create_users_in_db(self):#在数据库创建用户
        """批量创建用户记录"""
        try:
            conn=mysql.connector.connect(**self.db_config)
            cursor=conn.cursor()
            
            # 获取当前最大ID
            cursor.execute("SELECT COALESCE(MAX(id), 0) FROM sys_user")
            max_id=cursor.fetchone()[0]
            
            # 批量插入用户数据
            user_data=[]
            for i,device_sn in enumerate(self.devices,1):
                user_id=max_id+i+int(time.time())%1000000  # 生成唯一ID
                user_data.append((
                    user_id,#id
                    f"user_BBB{i:06d}",#user_name
                    "123456",#password
                    f"员工BBB{i:03d}",#real_name  
                    f"admin_{i:06d}@ljwx.com",#email
                    f"1380000{i:04d}",#phone
                    "admin",#create_user
                    1,#create_user_id
                    datetime.now(),#create_time
                    device_sn,#device_sn
                    1,#customer_id
                    "1"#status
                ))
                
            insert_sql="""
            INSERT INTO sys_user (id,user_name,password,real_name,email,phone,create_user,create_user_id,create_time,device_sn,customer_id,status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """
            
            cursor.executemany(insert_sql,user_data)
            conn.commit()
            
            # 获取新插入的用户ID  
            user_ids=[(data[0],data[9]) for data in user_data] # (id, device_sn)
            
            db_logger.info(f"用户创建完成: {len(user_ids)}条记录")
            
            # 批量插入用户组织关系
            org_data=[]
            for user_id,_ in user_ids:
                org_id=max_id+user_id+int(time.time())%1000000  # 生成唯一org ID
                org_data.append((org_id,user_id,1,"admin",1,datetime.now()))
            
            org_sql="INSERT INTO sys_user_org (id,user_id,org_id,create_user,create_user_id,create_time) VALUES (%s,%s,%s,%s,%s,%s)"
            cursor.executemany(org_sql,org_data)
            conn.commit()
            
            db_logger.info(f"用户组织关系创建完成: {len(org_data)}条记录")
            
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            db_logger.error('用户创建失败',extra={'error':str(e)},exc_info=True)
            return False
            
    def generate_health_data(self,device_sn):#生成健康数据
        """生成单个设备的健康数据"""
        return {
            'data':{
                'id':device_sn,
                'upload_method':'wifi',
                'heart_rate':random.randint(60,120),
                'blood_oxygen':random.randint(95,100),
                'body_temperature':f"{random.uniform(36.0,37.5):.1f}",
                'blood_pressure_systolic':random.randint(110,150),
                'blood_pressure_diastolic':random.randint(70,100),
                'step':random.randint(500,15000),
                'distance':f"{random.uniform(300,8000):.1f}",
                'calorie':f"{random.uniform(20000,60000):.1f}",
                'latitude':f"{random.uniform(34.0,34.3):.14f}",
                'longitude':f"{random.uniform(117.0,117.3):.14f}",
                'altitude':f"{random.uniform(0,100):.1f}",
                'stress':random.randint(30,80),
                'sleepData':'{"code":0,"data":[{"endTimeStamp":1747440420000,"startTimeStamp":1747418280000,"type":2}],"name":"sleep","type":"history"}',
                'exerciseDailyData':'{"code":0,"data":[{"strengthTimes":2,"totalTime":5}],"name":"daily","type":"history"}',
                'exerciseWeekData':'null',
                'scientificSleepData':'null',
                'workoutData':'{"code":0,"data":[],"name":"workout","type":"history"}'
            }
        }
        
    def upload_health_data(self,device_sn):#上传健康数据
        """上传单个设备的健康数据"""
        try:
            health_data=self.generate_health_data(device_sn)
            response=requests.post(f"{self.base_url}/upload_health_data",json=health_data,timeout=30)
            
            if response.status_code==200:
                return True
            else:
                device_logger.warning('健康数据上传失败',extra={'device_sn':device_sn,'status':response.status_code})
                return False
                
        except Exception as e:
            device_logger.error('健康数据上传异常',extra={'device_sn':device_sn,'error':str(e)})
            return False
            
    def continuous_upload(self):#持续上传
        """持续上传健康数据"""
        system_logger.info(f"开始持续上传健康数据，间隔{self.upload_interval}秒")
        
        upload_count=0
        error_count=0
        
        while self.running:
            start_time=time.time()
            
            # 使用线程池并发上传
            with ThreadPoolExecutor(max_workers=50) as executor:
                futures=[executor.submit(self.upload_health_data,device_sn) for device_sn in self.devices]
                
                # 统计结果
                batch_success=sum(1 for future in futures if future.result())
                batch_error=self.device_count-batch_success
                
                upload_count+=1
                error_count+=batch_error
                
                elapsed=time.time()-start_time
                system_logger.info(f"第{upload_count}轮上传完成",extra={
                    'success_count':batch_success,
                    'error_count':batch_error,
                    'elapsed_time':f"{elapsed:.2f}s",
                    'total_uploads':upload_count*self.device_count
                })
                
            # 等待下次上传
            time.sleep(max(0,self.upload_interval-elapsed))
            
    def start_simulation(self):#开始模拟
        """启动完整模拟流程"""
        try:
            system_logger.info("🚀 开始1000台手表批量模拟")
            
            # 1. 批量注册设备
            system_logger.info("📱 步骤1: 批量注册设备")
            self.batch_register_devices()
            
            # 2. 创建用户记录  
            system_logger.info("👥 步骤2: 创建用户记录")
            if not self.create_users_in_db():
                system_logger.error("用户创建失败，模拟终止")
                return
                
            # 3. 开始持续上传
            system_logger.info("📊 步骤3: 开始持续上传健康数据")
            self.running=True
            self.continuous_upload()
            
        except KeyboardInterrupt:
            system_logger.info("收到中断信号，停止模拟")
            self.stop_simulation()
        except Exception as e:
            system_logger.error('模拟执行失败',extra={'error':str(e)},exc_info=True)
            
    def stop_simulation(self):#停止模拟
        """停止模拟"""
        self.running=False
        system_logger.info("📴 模拟已停止")
        
def main():#主函数
    """主函数"""
    import argparse
    
    parser=argparse.ArgumentParser(description='1000台手表批量数据模拟器')
    parser.add_argument('--url',default='http://localhost:5001',help='大屏服务地址')
    parser.add_argument('--count',type=int,default=1000,help='设备数量')
    parser.add_argument('--interval',type=int,default=10,help='上传间隔(秒)')
    parser.add_argument('--skip-register',action='store_true',help='跳过设备注册')
    parser.add_argument('--skip-users',action='store_true',help='跳过用户创建')
    parser.add_argument('--upload-only',action='store_true',help='仅上传数据')
    
    args=parser.parse_args()
    
    simulator=DeviceBatchSimulator(base_url=args.url)
    simulator.device_count=args.count
    simulator.upload_interval=args.interval
    
    if args.upload_only:
        # 仅上传模式，从数据库加载设备列表
        try:
            conn=mysql.connector.connect(**simulator.db_config)
            cursor=conn.cursor()
            cursor.execute("SELECT device_sn FROM sys_user WHERE device_sn LIKE 'A5GTQ24B26%' LIMIT %s",(args.count,))
            simulator.devices=[row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            
            if simulator.devices:
                system_logger.info(f"从数据库加载了{len(simulator.devices)}台设备")
                simulator.running=True
                simulator.continuous_upload()
            else:
                system_logger.error("未找到已注册的设备")
                
        except Exception as e:
            system_logger.error('加载设备失败',extra={'error':str(e)})
    else:
        # 完整模拟流程
        if args.skip_register:
            system_logger.info("跳过设备注册")
            simulator.devices=[f"A5GTQ24B26{i:06d}" for i in range(1,args.count+1)]
            
        if args.skip_users:
            system_logger.info("跳过用户创建")
            
        simulator.start_simulation()

if __name__=="__main__":
    main() 
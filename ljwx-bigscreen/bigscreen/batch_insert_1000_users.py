#!/usr/bin/env python3
import random,mysql.connector,time,threading
from datetime import datetime,timedelta
from decimal import Decimal,ROUND_HALF_UP
from concurrent.futures import ThreadPoolExecutor
import queue,sys,os
from batch_config import * #导入配置

def dr(v,p=DECIMAL_PLACES):#精度转换
    try:return Decimal(str(v)).quantize(Decimal('0.'+'0'*p),rounding=ROUND_HALF_UP)
    except:return Decimal('0.'+'0'*p)

class MoveSim:#移动模拟器
    def __init__(self,lat,lng,dept):
        self.lat,self.lng,self.dept=float(lat),float(lng),dept
        self.route=ROUTES.get(dept,ROUTES['开采队'])
        self.idx,self.prog=0,0.0
        
    def next_pos(self):
        try:
            if len(self.route)>1:
                cp,np=self.route[self.idx],self.route[(self.idx+1)%len(self.route)]
                self.prog+=0.02
                if self.prog>=1.0:self.prog,self.idx=0.0,(self.idx+1)%len(self.route)
                self.lat=cp[0]+(np[0]-cp[0])*self.prog
                self.lng=cp[1]+(np[1]-cp[1])*self.prog
            speed=random.uniform(*HEALTH_RANGES['speed'])
            return {'lat':dr(self.lat),'lng':dr(self.lng),'alt':dr(random.uniform(*HEALTH_RANGES['altitude'])),'dist':dr(speed*0.017),'speed':dr(speed)}
        except:return {'lat':dr(BASE_LAT),'lng':dr(BASE_LNG),'alt':dr(10.0),'dist':dr(0.001),'speed':dr(1.2)}

def gen_health(move,dept):#生成健康数据
    try:
        base_hr=DEPT_BASE_HR.get(dept,70)
        hr=random.randint(base_hr,base_hr+20)
        return {'hr':hr,'ph':random.randint(*HEALTH_RANGES['pressure_high']),'pl':random.randint(*HEALTH_RANGES['pressure_low']),'bo':random.randint(*HEALTH_RANGES['blood_oxygen']),'temp':dr(random.uniform(*HEALTH_RANGES['temperature'])),'stress':random.randint(*HEALTH_RANGES['stress']),'step':random.randint(*HEALTH_RANGES['step']),'dist':move['dist'],'cal':dr(float(move['speed'])*0.8),'lat':move['lat'],'lng':move['lng'],'alt':move['alt']}
    except:return {'hr':70,'ph':120,'pl':80,'bo':98,'temp':dr(36.5),'stress':50,'step':100,'dist':dr(0.001),'cal':dr(1.0),'lat':dr(BASE_LAT),'lng':dr(BASE_LNG),'alt':dr(10.0)}

def gen_users():#生成1000个用户
    users=[]
    for i in range(TOTAL_USERS):
        dept=DEPARTMENTS[i%len(DEPARTMENTS)]
        name=random.choice(SURNAMES)+random.choice(GIVEN_NAMES)
        lat_base,lng_base=BASE_LAT+random.uniform(-COORD_RANGE,COORD_RANGE),BASE_LNG+random.uniform(-COORD_RANGE,COORD_RANGE)
        users.append({'phone':f'189{i:08d}','name':name,'device':f'A5GTQ24{i:08d}','dept':dept,'sim':MoveSim(lat_base,lng_base,dept)})
    return users

def clear_table():#清空表
    try:
        db=mysql.connector.connect(**DB_CONFIG)
        cursor=db.cursor()
        cursor.execute("TRUNCATE TABLE t_user_health_data")
        db.commit()
        print(f"✅已清空t_user_health_data表")
        cursor.close()
        db.close()
    except Exception as e:print(f"❌清空表失败:{e}")

def batch_insert(data_batch):#批量插入
    try:
        db=mysql.connector.connect(**DB_CONFIG)
        cursor=db.cursor()
        sql="INSERT INTO t_user_health_data(phone_number,heart_rate,pressure_high,pressure_low,blood_oxygen,temperature,stress,step,timestamp,user_name,latitude,longitude,altitude,device_sn,distance,calorie,create_time,update_time)VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        cursor.executemany(sql,data_batch)
        db.commit()
        cursor.close()
        db.close()
        return len(data_batch)
    except Exception as e:
        print(f"❌批量插入失败:{e}")
        return 0

def process_batch(users_batch,timestamp):#处理批次
    data_batch=[]
    for user in users_batch:
        move=user['sim'].next_pos()
        health=gen_health(move,user['dept'])
        data_batch.append((user['phone'],health['hr'],health['ph'],health['pl'],health['bo'],health['temp'],health['stress'],health['step'],timestamp,user['name'],health['lat'],health['lng'],health['alt'],user['device'],health['dist'],health['cal'],timestamp,timestamp))
    return batch_insert(data_batch)

def simulate_day(users,day_num):#模拟一天
    start_time=datetime.now().replace(hour=WORK_START_HOUR,minute=0,second=0,microsecond=0)-timedelta(days=DAYS_TO_SIMULATE-day_num)
    total_inserted=0
    
    print(f"📅开始模拟第{day_num}天({start_time.strftime('%Y-%m-%d')})")
    
    for hour in range(WORK_HOURS):
        for minute in range(60):
            current_time=start_time+timedelta(hours=hour,minutes=minute)
            
            #分批处理用户
            with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
                futures=[]
                for i in range(0,TOTAL_USERS,BATCH_SIZE):
                    batch=users[i:i+BATCH_SIZE]
                    futures.append(executor.submit(process_batch,batch,current_time))
                
                #收集结果
                for future in futures:
                    total_inserted+=future.result()
            
            if minute%PROGRESS_INTERVAL==0:print(f"⏰{current_time.strftime('%H:%M')} 已插入{total_inserted}条记录")
    
    print(f"✅第{day_num}天完成,共插入{total_inserted}条记录")
    return total_inserted

def main():
    print("🚀开始批量数据模拟")
    print(f"📊配置:用户{TOTAL_USERS}个,每天{WORK_HOURS}小时,共{DAYS_TO_SIMULATE}天")
    print(f"⚙️批处理大小:{BATCH_SIZE},线程数:{THREAD_COUNT}")
    
    #清空表
    clear_table()
    
    #生成用户
    print("👥生成用户数据...")
    users=gen_users()
    print(f"✅生成{len(users)}个用户")
    
    #开始模拟
    total_records=0
    start_time=time.time()
    
    for day in range(1,DAYS_TO_SIMULATE+1):
        day_records=simulate_day(users,day)
        total_records+=day_records
        
        #显示进度
        progress=day/DAYS_TO_SIMULATE*100
        elapsed=time.time()-start_time
        eta=(elapsed/day)*(DAYS_TO_SIMULATE-day)
        print(f"📈进度:{progress:.1f}% 已用时:{elapsed/60:.1f}分钟 预计剩余:{eta/60:.1f}分钟")
    
    total_time=time.time()-start_time
    print(f"\n🎉模拟完成!")
    print(f"📊总记录数:{total_records:,}")
    print(f"⏱️总用时:{total_time/60:.1f}分钟")
    print(f"🚀平均速度:{total_records/(total_time/60):.0f}条/分钟")

if __name__=="__main__":
    try:main()
    except KeyboardInterrupt:print("\n❌用户中断")
    except Exception as e:print(f"❌程序异常:{e}") 
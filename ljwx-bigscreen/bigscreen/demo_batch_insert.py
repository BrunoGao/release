#!/usr/bin/env python3
#演示版批量插入 - 100用户×3天×2小时=36,000条记录
import random,mysql.connector,time,threading
from datetime import datetime,timedelta
from decimal import Decimal,ROUND_HALF_UP
from concurrent.futures import ThreadPoolExecutor
from batch_config import * #导入配置

#演示配置覆盖
TOTAL_USERS=100 #演示用户数
WORK_HOURS=2 #演示2小时
DAYS_TO_SIMULATE=3 #演示3天
BATCH_SIZE=50 #批处理大小
THREAD_COUNT=5 #线程数

def dr(v,p=DECIMAL_PLACES):return Decimal(str(v)).quantize(Decimal('0.'+'0'*p),rounding=ROUND_HALF_UP) #精度转换

class DemoMoveSim:#演示移动模拟器
    def __init__(self,lat,lng,dept):
        self.lat,self.lng,self.dept=float(lat),float(lng),dept
        self.route=ROUTES.get(dept,ROUTES['开采队'])
        self.idx,self.prog=0,0.0
        
    def next_pos(self):
        try:
            if len(self.route)>1:
                cp,np=self.route[self.idx],self.route[(self.idx+1)%len(self.route)]
                self.prog+=0.05
                if self.prog>=1.0:self.prog,self.idx=0.0,(self.idx+1)%len(self.route)
                self.lat=cp[0]+(np[0]-cp[0])*self.prog
                self.lng=cp[1]+(np[1]-cp[1])*self.prog
            speed=random.uniform(*HEALTH_RANGES['speed'])
            return {'lat':dr(self.lat),'lng':dr(self.lng),'alt':dr(random.uniform(*HEALTH_RANGES['altitude'])),'dist':dr(speed*0.017),'speed':dr(speed)}
        except:return {'lat':dr(BASE_LAT),'lng':dr(BASE_LNG),'alt':dr(10.0),'dist':dr(0.001),'speed':dr(1.2)}

def demo_gen_health(move,dept):#演示健康数据生成
    try:
        base_hr=DEPT_BASE_HR.get(dept,70)
        hr=random.randint(base_hr,base_hr+15)
        return {'hr':hr,'ph':random.randint(*HEALTH_RANGES['pressure_high']),'pl':random.randint(*HEALTH_RANGES['pressure_low']),'bo':random.randint(*HEALTH_RANGES['blood_oxygen']),'temp':dr(random.uniform(*HEALTH_RANGES['temperature'])),'stress':random.randint(*HEALTH_RANGES['stress']),'step':random.randint(*HEALTH_RANGES['step']),'dist':move['dist'],'cal':dr(float(move['speed'])*0.8),'lat':move['lat'],'lng':move['lng'],'alt':move['alt']}
    except:return {'hr':70,'ph':120,'pl':80,'bo':98,'temp':dr(36.5),'stress':50,'step':100,'dist':dr(0.001),'cal':dr(1.0),'lat':dr(BASE_LAT),'lng':dr(BASE_LNG),'alt':dr(10.0)}

def demo_gen_users():#演示用户生成
    users=[]
    for i in range(TOTAL_USERS):
        dept=DEPARTMENTS[i%len(DEPARTMENTS)]
        name=f'演示{random.choice(SURNAMES)}{random.choice(GIVEN_NAMES)}'
        lat_base,lng_base=BASE_LAT+random.uniform(-COORD_RANGE/2,COORD_RANGE/2),BASE_LNG+random.uniform(-COORD_RANGE/2,COORD_RANGE/2)
        users.append({'phone':f'138{i:08d}','name':name,'device':f'DEMO{i:08d}','dept':dept,'sim':DemoMoveSim(lat_base,lng_base,dept)})
    return users

def demo_clear_table():#清空演示数据
    try:
        db=mysql.connector.connect(**DB_CONFIG)
        cursor=db.cursor()
        cursor.execute("DELETE FROM t_user_health_data WHERE device_sn LIKE 'DEMO%'")
        db.commit()
        print(f"✅已清空演示数据,删除{cursor.rowcount}条记录")
        cursor.close()
        db.close()
    except Exception as e:print(f"❌清空演示数据失败:{e}")

def demo_batch_insert(data_batch):#演示批量插入
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

def demo_process_batch(users_batch,timestamp):#演示处理批次
    data_batch=[]
    for user in users_batch:
        move=user['sim'].next_pos()
        health=demo_gen_health(move,user['dept'])
        data_batch.append((user['phone'],health['hr'],health['ph'],health['pl'],health['bo'],health['temp'],health['stress'],health['step'],timestamp,user['name'],health['lat'],health['lng'],health['alt'],user['device'],health['dist'],health['cal'],timestamp,timestamp))
    return demo_batch_insert(data_batch)

def demo_simulate_day(users,day_num):#演示模拟一天
    start_time=datetime.now().replace(hour=WORK_START_HOUR,minute=0,second=0,microsecond=0)-timedelta(days=DAYS_TO_SIMULATE-day_num)
    total_inserted=0
    
    print(f"📅演示第{day_num}天({start_time.strftime('%Y-%m-%d')})")
    
    for hour in range(WORK_HOURS):
        for minute in range(0,60,5): #每5分钟插入一次
            current_time=start_time+timedelta(hours=hour,minutes=minute)
            
            #分批处理用户
            with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
                futures=[]
                for i in range(0,TOTAL_USERS,BATCH_SIZE):
                    batch=users[i:i+BATCH_SIZE]
                    futures.append(executor.submit(demo_process_batch,batch,current_time))
                
                #收集结果
                for future in futures:
                    total_inserted+=future.result()
            
            if minute%15==0:print(f"⏰{current_time.strftime('%H:%M')} 已插入{total_inserted}条记录")
    
    print(f"✅第{day_num}天完成,共插入{total_inserted}条记录")
    return total_inserted

def demo_main():#演示主函数
    print("🎬开始演示批量数据模拟")
    print(f"📊配置:用户{TOTAL_USERS}个,每天{WORK_HOURS}小时,共{DAYS_TO_SIMULATE}天")
    print(f"📈预计记录数:{TOTAL_USERS*WORK_HOURS*12*DAYS_TO_SIMULATE:,}条")
    
    #清空演示数据
    demo_clear_table()
    
    #生成用户
    print("👥生成演示用户...")
    users=demo_gen_users()
    print(f"✅生成{len(users)}个演示用户")
    
    #开始模拟
    total_records=0
    start_time=time.time()
    
    for day in range(1,DAYS_TO_SIMULATE+1):
        day_records=demo_simulate_day(users,day)
        total_records+=day_records
        
        #显示进度
        progress=day/DAYS_TO_SIMULATE*100
        elapsed=time.time()-start_time
        print(f"📈进度:{progress:.1f}% 已用时:{elapsed:.1f}秒")
    
    total_time=time.time()-start_time
    print(f"\n🎉演示完成!")
    print(f"📊总记录数:{total_records:,}")
    print(f"⏱️总用时:{total_time:.1f}秒")
    print(f"🚀平均速度:{total_records/total_time:.0f}条/秒")
    
    #验证数据
    try:
        db=mysql.connector.connect(**DB_CONFIG)
        cursor=db.cursor()
        cursor.execute("SELECT COUNT(*) FROM t_user_health_data WHERE device_sn LIKE 'DEMO%'")
        count=cursor.fetchone()[0]
        cursor.execute("SELECT dept.dept_name,COUNT(*) FROM t_user_health_data h LEFT JOIN (SELECT DISTINCT device_sn,CASE WHEN device_sn LIKE 'DEMO%' THEN CASE (CAST(SUBSTRING(device_sn,5) AS UNSIGNED) % 5) WHEN 0 THEN '开采队' WHEN 1 THEN '通风队' WHEN 2 THEN '安全监察队' WHEN 3 THEN '机电队' ELSE '运输队' END ELSE '其他' END AS dept_name FROM t_user_health_data WHERE device_sn LIKE 'DEMO%') dept ON h.device_sn=dept.device_sn WHERE h.device_sn LIKE 'DEMO%' GROUP BY dept.dept_name")
        dept_stats=cursor.fetchall()
        cursor.close()
        db.close()
        
        print(f"\n📊数据验证:数据库中共有{count}条演示记录")
        print("📝部门分布:")
        for dept_stat in dept_stats:
            print(f"  {dept_stat[0]}: {dept_stat[1]}条")
            
    except Exception as e:print(f"❌数据验证失败:{e}")

if __name__=="__main__":
    try:demo_main()
    except KeyboardInterrupt:print("\n❌演示中断")
    except Exception as e:print(f"❌演示异常:{e}") 
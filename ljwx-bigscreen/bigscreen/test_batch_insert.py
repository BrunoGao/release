#!/usr/bin/env python3
#小规模批量插入测试 - 10用户×1天×1小时=600条记录
import random,mysql.connector,time
from datetime import datetime,timedelta
from decimal import Decimal,ROUND_HALF_UP
from concurrent.futures import ThreadPoolExecutor

#测试配置
DB_CONFIG={'user':'root','password':'123456','host':'127.0.0.1','database':'lj-06','raise_on_warnings':True}
TOTAL_USERS=10 #测试用户数
BATCH_SIZE=5 #批处理大小
WORK_HOURS=1 #测试1小时
DAYS_TO_SIMULATE=1 #测试1天
THREAD_COUNT=2 #线程数

def dr(v,p=6):return Decimal(str(v)).quantize(Decimal('0.'+'0'*p),rounding=ROUND_HALF_UP) #精度转换

class TestMoveSim:#测试移动模拟器
    def __init__(self,lat,lng,dept):
        self.lat,self.lng,self.dept=float(lat),float(lng),dept
        self.routes={'开采队':[(22.543100,114.045000),(22.543300,114.045200)],'通风队':[(22.544000,114.046000),(22.544200,114.046200)]}
        self.route=self.routes.get(dept,self.routes['开采队'])
        self.idx,self.prog=0,0.0
        
    def next_pos(self):
        try:
            if len(self.route)>1:
                cp,np=self.route[self.idx],self.route[(self.idx+1)%len(self.route)]
                self.prog+=0.1
                if self.prog>=1.0:self.prog,self.idx=0.0,(self.idx+1)%len(self.route)
                self.lat=cp[0]+(np[0]-cp[0])*self.prog
                self.lng=cp[1]+(np[1]-cp[1])*self.prog
            return {'lat':dr(self.lat),'lng':dr(self.lng),'alt':dr(random.uniform(10,50)),'dist':dr(0.001),'speed':dr(1.0)}
        except:return {'lat':dr(22.543100),'lng':dr(114.045000),'alt':dr(10.0),'dist':dr(0.001),'speed':dr(1.0)}

def gen_test_health(move,dept):#生成测试健康数据
    return {'hr':random.randint(70,90),'ph':random.randint(100,130),'pl':random.randint(70,85),'bo':random.randint(96,99),'temp':dr(random.uniform(36.5,37.0)),'stress':random.randint(20,60),'step':random.randint(80,120),'dist':move['dist'],'cal':dr(1.0),'lat':move['lat'],'lng':move['lng'],'alt':move['alt']}

def gen_test_users():#生成测试用户
    depts=['开采队','通风队']
    users=[]
    for i in range(TOTAL_USERS):
        dept=depts[i%len(depts)]
        name=f'测试用户{i+1:02d}'
        lat_base,lng_base=22.543+random.uniform(-0.001,0.001),114.045+random.uniform(-0.001,0.001)
        users.append({'phone':f'139{i:07d}','name':name,'device':f'TEST{i:07d}','dept':dept,'sim':TestMoveSim(lat_base,lng_base,dept)})
    return users

def test_clear_table():#清空测试数据
    try:
        db=mysql.connector.connect(**DB_CONFIG)
        cursor=db.cursor()
        cursor.execute("DELETE FROM t_user_health_data WHERE device_sn LIKE 'TEST%'")
        db.commit()
        print(f"✅已清空测试数据,删除{cursor.rowcount}条记录")
        cursor.close()
        db.close()
    except Exception as e:print(f"❌清空测试数据失败:{e}")

def test_batch_insert(data_batch):#测试批量插入
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

def test_process_batch(users_batch,timestamp):#测试处理批次
    data_batch=[]
    for user in users_batch:
        move=user['sim'].next_pos()
        health=gen_test_health(move,user['dept'])
        data_batch.append((user['phone'],health['hr'],health['ph'],health['pl'],health['bo'],health['temp'],health['stress'],health['step'],timestamp,user['name'],health['lat'],health['lng'],health['alt'],user['device'],health['dist'],health['cal'],timestamp,timestamp))
    return test_batch_insert(data_batch)

def test_simulate():#测试模拟
    print("🧪开始小规模测试")
    print(f"📊配置:用户{TOTAL_USERS}个,{WORK_HOURS}小时,共{DAYS_TO_SIMULATE}天")
    
    #清空测试数据
    test_clear_table()
    
    #生成测试用户
    users=gen_test_users()
    print(f"✅生成{len(users)}个测试用户")
    
    #开始测试
    start_time=datetime.now().replace(hour=8,minute=0,second=0,microsecond=0)
    total_inserted=0
    
    for hour in range(WORK_HOURS):
        for minute in range(0,60,10): #每10分钟插入一次
            current_time=start_time+timedelta(hours=hour,minutes=minute)
            
            #分批处理
            with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
                futures=[]
                for i in range(0,TOTAL_USERS,BATCH_SIZE):
                    batch=users[i:i+BATCH_SIZE]
                    futures.append(executor.submit(test_process_batch,batch,current_time))
                
                for future in futures:
                    total_inserted+=future.result()
            
            print(f"⏰{current_time.strftime('%H:%M')} 已插入{total_inserted}条记录")
    
    print(f"✅测试完成,共插入{total_inserted}条记录")
    
    #验证数据
    try:
        db=mysql.connector.connect(**DB_CONFIG)
        cursor=db.cursor()
        cursor.execute("SELECT COUNT(*) FROM t_user_health_data WHERE device_sn LIKE 'TEST%'")
        count=cursor.fetchone()[0]
        cursor.execute("SELECT user_name,device_sn,timestamp FROM t_user_health_data WHERE device_sn LIKE 'TEST%' ORDER BY timestamp LIMIT 5")
        samples=cursor.fetchall()
        cursor.close()
        db.close()
        
        print(f"📊数据验证:数据库中共有{count}条测试记录")
        print("📝样本数据:")
        for sample in samples:
            print(f"  {sample[0]} | {sample[1]} | {sample[2]}")
            
    except Exception as e:print(f"❌数据验证失败:{e}")

if __name__=="__main__":
    try:test_simulate()
    except KeyboardInterrupt:print("\n❌测试中断")
    except Exception as e:print(f"❌测试异常:{e}") 
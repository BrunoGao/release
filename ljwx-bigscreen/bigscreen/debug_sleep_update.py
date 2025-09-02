#!/usr/bin/env python3
import sys,os,json
sys.path.append('../..')

from config import MYSQL_HOST,MYSQL_PORT,MYSQL_USER,MYSQL_PASSWORD,MYSQL_DATABASE
import pymysql

def parse_sleep_data(sleep_data_json):#复制解析函数用于调试
    """解析sleepData JSON，计算睡眠时长(小时)"""
    print(f"原始数据: {sleep_data_json}")
    print(f"数据类型: {type(sleep_data_json)}")
    
    if not sleep_data_json or sleep_data_json in ['null',None,'NULL']:
        print("数据为空或null")
        return None
    
    try:
        if isinstance(sleep_data_json,str):
            if sleep_data_json.lower()=='null':
                print("字符串null")
                return None
            sleep_data_json=sleep_data_json.replace('"0"data"','"0","data"')
            sleep_data=json.loads(sleep_data_json)
        elif isinstance(sleep_data_json,dict):
            sleep_data=sleep_data_json
        elif isinstance(sleep_data_json,list):
            print("数据是空数组")
            return None
        else:
            print(f"未知数据类型: {type(sleep_data_json)}")
            return None
            
        print(f"解析后数据: {sleep_data}")
        
        if not isinstance(sleep_data,dict):
            print("解析后不是字典")
            return None
        
        code=sleep_data.get('code')
        print(f"code值: {code}")
        if code==-1 or code=='-1' or str(code)=='-1':
            print("code为-1")
            return None
        
        data_list=sleep_data.get('data',[])
        print(f"data_list: {data_list}, 长度: {len(data_list) if isinstance(data_list,list) else 'not_list'}")
        
        if not isinstance(data_list,list) or len(data_list)==0:
            print("data为空或不是列表")
            return None
        
        total_sleep_seconds=0
        
        for i,sleep_period in enumerate(data_list):
            print(f"处理第{i+1}个睡眠段: {sleep_period}")
            if not isinstance(sleep_period,dict):
                print(f"睡眠段{i+1}不是字典")
                continue
            
            start_time=sleep_period.get('startTimeStamp')
            end_time=sleep_period.get('endTimeStamp')
            print(f"开始时间: {start_time}, 结束时间: {end_time}")
            
            if start_time is None or end_time is None:
                print(f"睡眠段{i+1}缺少时间戳")
                continue
            
            try:
                start_seconds=int(start_time)/1000 if int(start_time)>9999999999 else int(start_time)
                end_seconds=int(end_time)/1000 if int(end_time)>9999999999 else int(end_time)
                print(f"转换后时间: {start_seconds} - {end_seconds}")
                
                if end_seconds>start_seconds:
                    duration=end_seconds-start_seconds
                    total_sleep_seconds+=duration
                    print(f"睡眠段{i+1}时长: {duration}秒")
                else:
                    print(f"睡眠段{i+1}时间无效")
                    
            except (ValueError,TypeError) as e:
                print(f"睡眠段{i+1}时间转换失败: {e}")
                continue
                
        print(f"总睡眠秒数: {total_sleep_seconds}")
        if total_sleep_seconds>0:
            hours=round(total_sleep_seconds/3600,2)
            print(f"总睡眠小时数: {hours}")
            return hours
        else:
            print("总睡眠时间为0")
            return None
            
    except (json.JSONDecodeError,Exception) as e:
        print(f"解析失败: {e}")
        return None

def debug_sample_records():
    """调试抽样记录"""
    conn=pymysql.connect(host=MYSQL_HOST,port=MYSQL_PORT,user=MYSQL_USER,password=MYSQL_PASSWORD,database=MYSQL_DATABASE,charset='utf8mb4')
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT d.device_sn, d.date, d.sleep_data, h.id
                FROM t_user_health_data_daily d
                JOIN t_user_health_data h ON BINARY d.device_sn = BINARY h.device_sn 
                    AND DATE(h.timestamp) = d.date
                WHERE d.sleep_data IS NOT NULL 
                    AND JSON_LENGTH(d.sleep_data) > 0
                    AND (h.sleep IS NULL OR h.sleep = 0)
                LIMIT 5
            """)
            
            records=cursor.fetchall()
            print(f"调试前5条记录:")
            
            for i,record in enumerate(records):
                device_sn,date,sleep_data_json,health_id=record
                print(f"\n=== 记录 {i+1} ===")
                print(f"设备: {device_sn}")
                print(f"日期: {date}")
                print(f"健康数据ID: {health_id}")
                
                sleep_hours=parse_sleep_data(sleep_data_json)
                print(f"最终结果: {sleep_hours}")
                print(f"是否会更新: {'是' if sleep_hours is not None and sleep_hours > 0 else '否'}")
                print("-"*50)
                
    except Exception as e:
        print(f"调试失败: {e}")
    finally:
        conn.close()

if __name__=="__main__":
    debug_sample_records() 
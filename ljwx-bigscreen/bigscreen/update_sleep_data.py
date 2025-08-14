#!/usr/bin/env python3
import sys,os,json
sys.path.append('../..')

from config import MYSQL_HOST,MYSQL_PORT,MYSQL_USER,MYSQL_PASSWORD,MYSQL_DATABASE
import pymysql
from datetime import datetime

def parse_sleep_data(sleep_data_json):#解析睡眠数据
    """解析sleepData JSON，计算睡眠时长(小时)"""
    if not sleep_data_json or sleep_data_json in ['null',None,'NULL']:
        return None
    
    try:
        if isinstance(sleep_data_json,str):
            if sleep_data_json.lower()=='null':return None
            sleep_data_json=sleep_data_json.replace('"0"data"','"0","data"')#修复格式错误
            sleep_data=json.loads(sleep_data_json)
        elif isinstance(sleep_data_json,dict):
            sleep_data=sleep_data_json
        else:
            return None
            
        if not isinstance(sleep_data,dict):return None
        
        code=sleep_data.get('code')
        if code==-1 or code=='-1' or str(code)=='-1':return None
        
        data_list=sleep_data.get('data',[])
        if not isinstance(data_list,list) or len(data_list)==0:return None
        
        total_sleep_seconds=0
        
        for sleep_period in data_list:
            if not isinstance(sleep_period,dict):continue
            
            start_time=sleep_period.get('startTimeStamp')
            end_time=sleep_period.get('endTimeStamp')
            
            if start_time is None or end_time is None:continue
            
            try:
                start_seconds=int(start_time)/1000 if int(start_time)>9999999999 else int(start_time)
                end_seconds=int(end_time)/1000 if int(end_time)>9999999999 else int(end_time)
                
                if end_seconds>start_seconds:
                    total_sleep_seconds+=(end_seconds-start_seconds)
                    
            except (ValueError,TypeError):continue
                
        if total_sleep_seconds>0:
            return round(total_sleep_seconds/3600,2)
        else:
            return None
            
    except (json.JSONDecodeError,Exception) as e:
        print(f"解析sleepData错误: {e}, 数据: {sleep_data_json}")
        return None

def update_sleep_from_daily_table():
    """从每日表读取sleepData更新主表sleep字段"""
    conn=pymysql.connect(host=MYSQL_HOST,port=MYSQL_PORT,user=MYSQL_USER,password=MYSQL_PASSWORD,database=MYSQL_DATABASE,autocommit=False,charset='utf8mb4')
    
    try:
        with conn.cursor() as cursor:
            print("开始从每日表查询sleepData...")
            
            #查询真正有效的sleep_data记录
            cursor.execute("""
                SELECT d.device_sn, d.date, d.sleep_data, h.id as health_id
                FROM t_user_health_data_daily d
                JOIN t_user_health_data h ON BINARY d.device_sn = BINARY h.device_sn 
                    AND DATE(h.timestamp) = d.date
                WHERE d.sleep_data IS NOT NULL 
                    AND d.sleep_data != 'null'
                    AND d.sleep_data != ''
                    AND JSON_VALID(d.sleep_data) = 1
                    AND JSON_EXTRACT(d.sleep_data, '$.data') IS NOT NULL
                    AND JSON_LENGTH(JSON_EXTRACT(d.sleep_data, '$.data')) > 0
                    AND (h.sleep IS NULL OR h.sleep = 0)
                ORDER BY d.device_sn, d.date
                LIMIT 10000
            """)
            
            records=cursor.fetchall()
            total_count=len(records)
            print(f"找到{total_count}条需要更新的记录")
            
            if total_count==0:
                print("没有需要更新的记录")
                return
            
            updated_count=0
            error_count=0
            skip_count=0
            
            for i,record in enumerate(records):
                device_sn,date,sleep_data_json,health_id=record
                
                try:
                    sleep_hours=parse_sleep_data(sleep_data_json)
                    
                    if sleep_hours is not None and sleep_hours>0:
                        cursor.execute("""
                            UPDATE t_user_health_data 
                            SET sleep = %s 
                            WHERE id = %s
                        """,(sleep_hours,health_id))
                        
                        affected_rows=cursor.rowcount
                        
                        if affected_rows>0:
                            updated_count+=1
                        
                        if updated_count%100==0:
                            conn.commit()#每100条提交一次
                            print(f"已更新{updated_count}/{total_count}条记录...")
                    else:
                        skip_count+=1
                    
                except Exception as e:
                    error_count+=1
                    print(f"处理记录失败 设备:{device_sn} 日期:{date} 错误:{e}")
                    continue
            
            conn.commit()#最终提交
            print(f"\n更新完成:")
            print(f"- 总记录数: {total_count}")
            print(f"- 成功更新: {updated_count}")
            print(f"- 跳过记录: {skip_count}")
            print(f"- 错误记录: {error_count}")
            print(f"- 更新率: {updated_count/total_count*100:.1f}%")
            
    except Exception as e:
        print(f"批量更新失败: {e}")
        conn.rollback()
    finally:
        conn.close()

def check_sleep_data_status():
    """检查睡眠数据状态"""
    conn=pymysql.connect(host=MYSQL_HOST,port=MYSQL_PORT,user=MYSQL_USER,password=MYSQL_PASSWORD,database=MYSQL_DATABASE,charset='utf8mb4')
    
    try:
        with conn.cursor() as cursor:
            #统计主表sleep字段情况
            cursor.execute("SELECT COUNT(*) FROM t_user_health_data")
            total_main_records=cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM t_user_health_data WHERE sleep IS NOT NULL AND sleep > 0")
            main_with_sleep=cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM t_user_health_data WHERE sleep IS NULL OR sleep = 0")
            main_without_sleep=cursor.fetchone()[0]
            
            #统计每日表sleep_data情况
            cursor.execute("SELECT COUNT(*) FROM t_user_health_data_daily WHERE sleep_data IS NOT NULL")
            daily_with_sleepdata=cursor.fetchone()[0]
            
            #可更新的记录数-使用BINARY解决字符集冲突
            cursor.execute("""
                SELECT COUNT(DISTINCT h.id)
                FROM t_user_health_data_daily d
                JOIN t_user_health_data h ON BINARY d.device_sn = BINARY h.device_sn 
                    AND DATE(h.timestamp) = d.date
                WHERE d.sleep_data IS NOT NULL 
                    AND d.sleep_data != 'null'
                    AND d.sleep_data != ''
                    AND JSON_LENGTH(d.sleep_data) > 0
                    AND (h.sleep IS NULL OR h.sleep = 0)
            """)
            updatable_records=cursor.fetchone()[0]
            
            print(f"睡眠数据状态统计:")
            print(f"- 主表总记录数: {total_main_records:,}")
            print(f"- 主表已有sleep值: {main_with_sleep:,}")
            print(f"- 主表缺少sleep值: {main_without_sleep:,}")
            print(f"- 每日表有sleep_data: {daily_with_sleepdata:,}")
            print(f"- 可更新记录数: {updatable_records:,}")
            print(f"- 完成率: {(main_with_sleep/total_main_records*100):.1f}%")
            
    except Exception as e:
        print(f"状态检查失败: {e}")
    finally:
        conn.close()

def sample_check_daily():
    """抽样检查每日表数据"""
    conn=pymysql.connect(host=MYSQL_HOST,port=MYSQL_PORT,user=MYSQL_USER,password=MYSQL_PASSWORD,database=MYSQL_DATABASE,charset='utf8mb4')
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT d.device_sn, d.date, d.sleep_data, h.sleep, h.timestamp
                FROM t_user_health_data_daily d
                JOIN t_user_health_data h ON BINARY d.device_sn = BINARY h.device_sn 
                    AND DATE(h.timestamp) = d.date
                WHERE d.sleep_data IS NOT NULL 
                ORDER BY RAND() 
                LIMIT 3
            """)
            
            samples=cursor.fetchall()
            print(f"抽样检查每日表数据:")
            
            for device_sn,date,sleep_data_json,sleep_value,timestamp in samples:
                calculated_sleep=parse_sleep_data(sleep_data_json)
                print(f"设备: {device_sn}")
                print(f"日期: {date}")
                print(f"时间戳: {timestamp}")
                print(f"sleep_data: {str(sleep_data_json)[:200]}..." if len(str(sleep_data_json))>200 else f"sleep_data: {sleep_data_json}")
                print(f"主表sleep值: {sleep_value}")
                print(f"计算sleep值: {calculated_sleep}")
                print(f"匹配: {'✓' if sleep_value==calculated_sleep else '✗'}")
                print("-"*60)
                
    except Exception as e:
        print(f"抽样检查失败: {e}")
    finally:
        conn.close()

if __name__=="__main__":
    print("睡眠数据更新工具 - 从每日表更新主表")
    print("="*60)
    
    if len(sys.argv)>1:
        action=sys.argv[1]
        if action=="check":
            check_sleep_data_status()
        elif action=="sample":
            sample_check_daily()
        elif action=="update":
            print("开始从每日表更新主表sleep字段...")
            update_sleep_from_daily_table()
        else:
            print("用法: python update_sleep_data.py [check|sample|update]")
    else:
        print("首先检查数据状态...")
        check_sleep_data_status()
        print()
        response=input("是否开始更新？(y/N): ")
        if response.lower()=='y':
            update_sleep_from_daily_table()
            print("\n更新后状态:")
            check_sleep_data_status() 
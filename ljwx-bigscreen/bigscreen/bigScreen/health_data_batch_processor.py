#!/usr/bin/env python3
from flask import jsonify,request
from datetime import datetime,timedelta,date
from .models import db,UserHealthData,UserHealthDataDaily,UserHealthDataWeekly,HealthDataConfig
from .redis_helper import RedisHelper
from .alert import generate_alerts
import json,threading,queue,time
from sqlalchemy import text,and_,or_
from concurrent.futures import ThreadPoolExecutor
from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
import pymysql

#导入专业日志系统
from logging_config import health_logger,db_logger,redis_logger,log_health_data_processing

redis=RedisHelper()
logger=health_logger#使用健康数据专用记录器

class HealthDataOptimizer:#健康数据性能优化器V4.0 - CPU自适应版本
    def __init__(self):
        # CPU自适应配置
        import psutil
        self.cpu_cores = psutil.cpu_count(logical=True)
        self.memory_gb = psutil.virtual_memory().total / (1024**3)
        
        # 动态批次配置：CPU核心数 × 25
        self.batch_size = max(50, min(500, self.cpu_cores * 25))  # 限制在50-500之间
        self.batch_timeout=2#批处理超时秒数
        
        # 动态线程池配置：CPU核心数 × 2.5 (I/O密集型)
        max_workers = max(4, min(32, int(self.cpu_cores * 2.5)))
        
        self.batch_queue=queue.Queue(maxsize=5000)#批处理队列
        self.executor=ThreadPoolExecutor(max_workers=max_workers)#线程池
        self.running=True#运行状态
        self.stats={'processed':0,'batches':0,'errors':0,'duplicates':0,'auto_adjustments':0}#统计信息
        self.processed_keys=set()#已处理记录键值集合
        
        # 性能监控
        self.performance_window = []
        self.last_adjustment_time = time.time()
        
        logger.info(f'🚀 HealthDataOptimizer V4.0 初始化:')
        logger.info(f'   CPU核心: {self.cpu_cores}, 内存: {self.memory_gb:.1f}GB')
        logger.info(f'   批次大小: {self.batch_size}, 工作线程: {max_workers}')
        self.field_mapping={#数据库字段到API字段映射
            'heart_rate':'heart_rate','blood_oxygen':'blood_oxygen','temperature':'body_temperature',
            'pressure_high':'blood_pressure_systolic','pressure_low':'blood_pressure_diastolic','stress':'stress',
            'step':'step','distance':'distance','calorie':'calorie','latitude':'latitude',
            'longitude':'longitude','altitude':'altitude','sleep':'sleepData',
            'sleep_data':'sleepData','workout_data':'workoutData','exercise_daily_data':'exerciseDailyData',
            'exercise_week_data':'exerciseWeekData','scientific_sleep_data':'scientificSleepData'
        }
        self.app=None#应用实例
        self.processor_started=False#批处理器启动状态
        
    def _ensure_processor_started(self):#确保批处理器已启动
        if not self.processor_started:
            try:
                from flask import current_app
                self.app=current_app._get_current_object()#获取应用实例
                threading.Thread(target=self._batch_processor,daemon=True).start()
                self._schedule_cleanup()#启动定时清理
                self.processor_started=True
                logger.info('批处理器和定时清理已启动')
            except RuntimeError:
                logger.warning('应用上下文不可用，延迟启动批处理器')
        
    def _batch_processor(self):#批处理器
        batch_data=[]
        last_flush=time.time()
        
        while self.running:
            try:
                timeout=max(0.1,self.batch_timeout-(time.time()-last_flush))
                item=self.batch_queue.get(timeout=timeout)
                
                # 移除批处理器中的重复检测，因为在add_data中已经通过数据库查询进行了准确的重复检测
                # key=f"{item['device_sn']}:{item['main_data']['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"
                # if key in self.processed_keys:
                #     self.stats['duplicates']+=1
                #     logger.warning(f'跳过重复记录: {key}')
                #     continue
                    
                batch_data.append(item)
                # self.processed_keys.add(key)  # 不再维护内存中的重复检测集合
                
                # 性能监控：记录批次处理时间
                if len(batch_data) == 1:
                    batch_start_time = time.time()
                
                if len(batch_data)>=self.batch_size or (time.time()-last_flush)>=self.batch_timeout:
                    if batch_data:
                        processing_start = time.time()
                        if self.app:
                            with self.app.app_context():#确保在应用上下文中执行
                                self._flush_batch(batch_data)
                        else:
                            self._flush_batch(batch_data)#直接执行
                        
                        # 记录性能数据并尝试自动调优
                        processing_time = time.time() - processing_start
                        self._record_performance(len(batch_data), processing_time)
                        
                        batch_data=[]
                        last_flush=time.time()
                        
            except queue.Empty:
                if batch_data and (time.time()-last_flush)>=self.batch_timeout:
                    if self.app:
                        with self.app.app_context():#确保在应用上下文中执行
                            self._flush_batch(batch_data)
                    else:
                        self._flush_batch(batch_data)#直接执行
                    batch_data=[]
                    last_flush=time.time()
                    
    def _flush_batch(self,batch_data):#刷新批次到数据库
        try:
            if not batch_data:return
            
            db_logger.info('批处理开始',extra={'batch_size':len(batch_data),'data_count':len(batch_data)})
            
            #分离不同类型的数据
            main_records=[]
            daily_records=[]
            weekly_records=[]
            
            for item in batch_data:
                main_records.append(item['main_data'])
                if item.get('daily_data'):
                    daily_records.append(item['daily_data'])
                    db_logger.debug('每日数据分离',extra={'device_sn':item['device_sn'],'data_count':1})
                if item.get('weekly_data'):
                    weekly_records.append(item['weekly_data'])
                    db_logger.debug('每周数据分离',extra={'device_sn':item['device_sn'],'data_count':1})
            
            db_logger.info('数据分离完成',extra={'main_count':len(main_records),'daily_count':len(daily_records),'weekly_count':len(weekly_records)})
            
            # 使用pymysql直接连接
            conn = pymysql.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE,
                autocommit=False
            )
            
            try:
                with conn.cursor() as cursor:
                    #批量插入主表
                    if main_records:
                        try:
                            insert_sql = """
                                INSERT INTO t_user_health_data 
                                (device_sn, user_id, org_id, heart_rate, blood_oxygen, temperature, 
                                 pressure_high, pressure_low, stress, step, distance, calorie, 
                                 latitude, longitude, altitude, sleep, timestamp, upload_method, create_time)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                            """
                            
                            for record in main_records:
                                cursor.execute(insert_sql, (
                                    record.get('device_sn'),
                                    record.get('user_id'),
                                    record.get('org_id'),
                                    record.get('heart_rate'),
                                    record.get('blood_oxygen'),
                                    record.get('temperature'),
                                    record.get('pressure_high'),
                                    record.get('pressure_low'),
                                    record.get('stress'),
                                    record.get('step'),
                                    record.get('distance'),
                                    record.get('calorie'),
                                    record.get('latitude'),
                                    record.get('longitude'),
                                    record.get('altitude'),
                                    record.get('sleep'),
                                    record.get('timestamp'),
                                    record.get('upload_method')
                                ))
                            
                            conn.commit()
                            db_logger.info('主表批量插入成功',extra={'data_count':len(main_records)})
                        except Exception as e:
                            db_logger.error('主表插入失败',extra={'error':str(e),'data_count':len(main_records)})
                            conn.rollback()
                    
                    #批量处理每日表
                    if daily_records:
                        try:
                            for record in daily_records:
                                db_logger.debug('处理每日记录',extra={'device_sn':record['device_sn'],'date':record['date']})
                                
                                # 检查是否存在
                                cursor.execute("""
                                    SELECT id FROM t_user_health_data_daily 
                                    WHERE device_sn = %s AND date = %s
                                """, (record['device_sn'], record['date']))
                                
                                existing = cursor.fetchone()
                                
                                if existing:
                                    cursor.execute("""
                                        UPDATE t_user_health_data_daily 
                                        SET sleep_data = %s, exercise_daily_data = %s, workout_data = %s, update_time = NOW()
                                        WHERE id = %s
                                    """, (
                                        record.get('sleep_data'),
                                        record.get('exercise_daily_data'),
                                        record.get('workout_data'),
                                        existing[0]
                                    ))
                                else:
                                    cursor.execute("""
                                        INSERT INTO t_user_health_data_daily 
                                        (device_sn, user_id, org_id, date, sleep_data, exercise_daily_data, workout_data, create_time, update_time)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                                    """, (
                                        record['device_sn'],
                                        record['user_id'],
                                        record['org_id'],
                                        record['date'],
                                        record.get('sleep_data'),
                                        record.get('exercise_daily_data'),
                                        record.get('workout_data')
                                    ))
                            
                            conn.commit()
                            db_logger.info('每日表批量处理成功',extra={'data_count':len(daily_records)})
                        except Exception as e:
                            db_logger.error('每日表处理失败',extra={'error':str(e),'data_count':len(daily_records)})
                            conn.rollback()
                    
                    #批量处理每周表
                    if weekly_records:
                        try:
                            for record in weekly_records:
                                db_logger.debug('处理每周记录',extra={'device_sn':record['device_sn'],'week_start':record['week_start']})
                                
                                # 检查是否存在
                                cursor.execute("""
                                    SELECT id FROM t_user_health_data_weekly 
                                    WHERE device_sn = %s AND week_start = %s
                                """, (record['device_sn'], record['week_start']))
                                
                                existing = cursor.fetchone()
                                
                                if existing:
                                    cursor.execute("""
                                        UPDATE t_user_health_data_weekly 
                                        SET exercise_week_data = %s, update_time = NOW()
                                        WHERE id = %s
                                    """, (
                                        record.get('exercise_week_data'),
                                        existing[0]
                                    ))
                                else:
                                    cursor.execute("""
                                        INSERT INTO t_user_health_data_weekly 
                                        (device_sn, user_id, org_id, week_start, exercise_week_data, create_time, update_time)
                                        VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                                    """, (
                                        record['device_sn'],
                                        record['user_id'],
                                        record['org_id'],
                                        record['week_start'],
                                        record.get('exercise_week_data')
                                    ))
                            
                            conn.commit()
                            db_logger.info('每周表批量处理成功',extra={'data_count':len(weekly_records)})
                        except Exception as e:
                            db_logger.error('每周表处理失败',extra={'error':str(e),'data_count':len(weekly_records)})
                            conn.rollback()
                            
            finally:
                conn.close()
            
            #异步处理Redis和告警
            try:
                for item in batch_data:
                    if not self.executor._shutdown:  #检查线程池是否已关闭
                        self.executor.submit(self._async_process,item)
                    else:
                        #如果线程池已关闭，直接同步处理
                        self._async_process(item)
            except RuntimeError as re:
                if 'cannot schedule new futures after shutdown' in str(re):
                    #线程池已关闭，改为同步处理
                    for item in batch_data:
                        self._async_process(item)
                else:
                    raise re
                
            self.stats['processed']+=len(batch_data)
            self.stats['batches']+=1
            health_logger.info('批处理完成',extra={'data_count':len(batch_data),'batch_id':self.stats['batches']})
            
        except Exception as e:
            self.stats['errors']+=1
            health_logger.error('批处理失败',extra={'error':str(e),'data_count':len(batch_data) if batch_data else 0},exc_info=True)
            
    def _insert_main_one_by_one(self,main_records):#单条插入主表处理重复
        success_count=0
        for record in main_records:
            try:
                existing=db.session.query(UserHealthData.id).filter(
                    and_(UserHealthData.device_sn==record['device_sn'],
                        UserHealthData.timestamp==record['timestamp'])
                ).first()
                
                if existing:
                    self.stats['duplicates']+=1
                    continue
                    
                health_record=UserHealthData(**record)
                db.session.add(health_record)
                db.session.commit()
                success_count+=1
                
            except Exception as e:
                try:
                    db.session.rollback()
                except:
                    pass#忽略回滚错误
                if 'Duplicate entry' not in str(e):
                    logger.error(f'单条插入失败: {e}')
                else:
                    self.stats['duplicates']+=1
                    
        logger.info(f'主表单条插入完成: {success_count}条成功')
            
    def _async_process(self,item):#异步处理Redis和告警
        try:
            device_sn=item['device_sn']
            redis_logger.info('Redis数据更新开始',extra={'device_sn':device_sn})
            
            redis.hset_data(f"health_data:{device_sn}",mapping=item['redis_data'])
            redis.publish(f"health_data_channel:{device_sn}",device_sn)
            redis_logger.info('Redis数据更新完成',extra={'device_sn':device_sn,'data_count':len(item['redis_data'])})
            
            if item.get('enable_alerts',True):
                from logging_config import alert_logger
                alert_logger.info('告警检测开始',extra={'device_sn':device_sn})
                
                if self.app:
                    with self.app.app_context():#确保在应用上下文中调用generate_alerts
                        generate_alerts(item['redis_data'],item.get('health_data_id'))
                else:
                    generate_alerts(item['redis_data'],item.get('health_data_id'))
                    
                alert_logger.info('告警检测完成',extra={'device_sn':device_sn})
                
        except Exception as e:
            health_logger.error('异步处理失败',extra={'device_sn':item.get('device_sn','unknown'),'error':str(e)},exc_info=True)
            
    def get_health_config_fields(self,customer_id):#获取健康数据配置字段
        """根据客户ID获取配置的健康数据字段"""
        try:
            configs=HealthDataConfig.query.filter_by(customer_id=customer_id,is_enabled=True).all()
            if not configs:
                return self._get_default_config()
                
            fields=[config.data_type for config in configs]
            weights={config.data_type:float(config.weight) if config.weight else 1.0 for config in configs}
            
            return {'fields':fields,'weights':weights,'config_source':'customer','customer_id':customer_id}
            
        except Exception as e:
            logger.error(f'获取健康配置字段失败: {e}')
            return self._get_default_config()
    
    def _get_default_config(self):#默认配置
        """返回默认的健康数据配置"""
        default_fields=list(self.field_mapping.keys())
        return {'fields':default_fields,'weights':{field:1.0 for field in default_fields},'config_source':'default','customer_id':None}

    def _get_week_start(self,date_obj):#获取周开始日期
        """获取指定日期所在周的周一日期"""
        if isinstance(date_obj,datetime):
            date_obj=date_obj.date()
        days_since_monday=date_obj.weekday()
        return date_obj-timedelta(days=days_since_monday)

    def _get_user_org_info(self,device_sn):#获取用户组织信息
        """根据设备SN获取用户和组织信息"""
        print(f"🔍 开始查询用户组织信息: device_sn={device_sn}")
        try:
            # 直接使用pymysql连接，避免SQLAlchemy的URL解析问题
            conn = pymysql.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE
            )
            print(f"✅ 数据库连接成功: {MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}")
            
            try:
                with conn.cursor() as cursor:
                    query_sql = """
                        SELECT u.id as user_id, uo.org_id
                        FROM sys_user u 
                        LEFT JOIN sys_user_org uo ON u.id = uo.user_id
                        WHERE u.device_sn = %s AND u.is_deleted = 0
                        LIMIT 1
                    """
                    print(f"🔍 执行用户查询SQL: {query_sql} with device_sn={device_sn}")
                    cursor.execute(query_sql, (device_sn,))
                    result = cursor.fetchone()
                    print(f"🔍 用户查询结果: {result}")
                    
                    if result:
                        user_id, org_id = result[0], result[1]
                        customer_id = None
                        print(f"✅ 找到用户: user_id={user_id}, org_id={org_id}")
                        
                        # 通过org_id查找sys_org_units的ancestors获取租户ID
                        if org_id:
                            org_query_sql = """
                                SELECT ancestors FROM sys_org_units 
                                WHERE id = %s AND is_deleted = 0
                                LIMIT 1
                            """
                            print(f"🔍 执行组织查询SQL: {org_query_sql} with org_id={org_id}")
                            cursor.execute(org_query_sql, (org_id,))
                            org_result = cursor.fetchone()
                            print(f"🔍 组织查询结果: {org_result}")
                            
                            if org_result and org_result[0]:
                                ancestors = org_result[0]
                                print(f"🔍 组织ancestors: {ancestors}")
                                # 解析ancestors格式(0,X,Y...)，获取第二个数字X作为租户ID
                                parts = ancestors.split(',')
                                if len(parts) >= 2 and parts[0] == '0':
                                    try:
                                        customer_id = int(parts[1])
                                        print(f"✅ 解析出customer_id: {customer_id}")
                                    except ValueError:
                                        print(f"❌ ancestors格式异常: {ancestors}")
                                        logger.warning(f'ancestors格式异常: {ancestors}')
                                else:
                                    print(f"⚠️ ancestors格式不符合预期: {ancestors}")
                            else:
                                print(f"⚠️ 未找到组织信息或ancestors为空")
                        else:
                            print(f"⚠️ org_id为空")
                        
                        # 创建类似SQLAlchemy结果的对象
                        class UserOrgInfo:
                            def __init__(self, user_id, org_id, customer_id):
                                self.user_id = user_id
                                self.org_id = org_id
                                self.customer_id = customer_id
                        
                        user_org_info = UserOrgInfo(user_id, org_id, customer_id)
                        print(f"✅ 用户组织信息构建完成: user_id={user_org_info.user_id}, org_id={user_org_info.org_id}, customer_id={user_org_info.customer_id}")
                        return user_org_info
                    else:
                        print(f"❌ 未找到设备对应的用户: {device_sn}")
                        return None
            finally:
                conn.close()
                print(f"✅ 数据库连接已关闭")
                
        except Exception as e:
            print(f"❌ 获取用户组织信息异常: {e}")
            print(f"❌ 异常详情: {type(e).__name__} - {str(e)}")
            import traceback
            print(f"❌ 完整异常堆栈: {traceback.format_exc()}")
            logger.error(f'获取用户组织信息失败: {e}')
            return None

    def add_data(self,raw_data,device_sn,enable_alerts=True):#添加数据到队列
        """配置化处理健康数据上传"""
        print(f"🔧 优化器添加数据开始: device_sn={device_sn}, raw_data={json.dumps(raw_data, ensure_ascii=False)}")
        try:
            #确保批处理器已启动
            self._ensure_processor_started()
            
            # 优先使用直接传递的客户信息参数
            user_id = raw_data.get("user_id")
            org_id = raw_data.get("org_id") 
            customer_id = raw_data.get("customer_id")
            
            print(f"🔍 直接传入的客户信息: user_id={user_id}, org_id={org_id}, customer_id={customer_id}")
            
            # 如果没有直接传递客户信息，通过deviceSn查询获取（兼容旧版本）
            if not user_id or not org_id or not customer_id:
                print(f"🔍 客户信息不完整，通过deviceSn查询获取")
                user_org_info=self._get_user_org_info(device_sn)
                if not user_org_info:
                    print(f"❌ 未找到设备对应用户: {device_sn}")
                    logger.warning(f'未找到设备对应用户: {device_sn}')
                    return {'success':False,'reason':'user_not_found','message':'设备对应用户未找到'}
                    
                user_id = user_id or user_org_info.user_id
                org_id = org_id or user_org_info.org_id
                customer_id = customer_id or user_org_info.customer_id
                print(f"✅ 补充后的客户信息: user_id={user_id}, org_id={org_id}, customer_id={customer_id}")
            else:
                print(f"✅ 使用直接传递的客户信息")
            
            #获取配置字段
            config_info=self.get_health_config_fields(customer_id) if customer_id else self._get_default_config()
            config_fields=config_info['fields']
            print(f"🔍 健康数据配置字段: {config_fields}")
            
            #时间戳处理
            timestamp=raw_data.get("timestamp") or raw_data.get("cjsj") or datetime.now()
            print(f"🔍 原始时间戳: {timestamp}")
            if isinstance(timestamp,str):
                try:
                    timestamp=datetime.strptime(timestamp,'%Y-%m-%d %H:%M:%S')
                except:
                    timestamp=datetime.now()
            print(f"🔍 处理后时间戳: {timestamp}")
            
            #正确的重复检测：只用device_sn+timestamp，查询数据库而非内存
            duplicate_key=f"{device_sn}:{timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
            print(f"🔍 重复检测键: {duplicate_key}")
            
            #直接查询数据库检查是否重复，而不是依赖内存缓存
            try:
                conn = pymysql.connect(host=MYSQL_HOST,port=MYSQL_PORT,user=MYSQL_USER,password=MYSQL_PASSWORD,database=MYSQL_DATABASE)
                try:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT id FROM t_user_health_data WHERE device_sn = %s AND timestamp = %s LIMIT 1",(device_sn,timestamp))
                        existing_record = cursor.fetchone()
                        if existing_record:
                            print(f"⚠️ 数据库中已存在相同记录: {duplicate_key}, id={existing_record[0]}")
                            logger.info(f'跳过重复数据(数据库已存在): {duplicate_key}')
                            return {'success':True,'reason':'duplicate','message':'数据库中已存在相同时间戳数据'}
                        else:
                            print(f"✅ 数据库重复检查通过: {duplicate_key}")
                finally:
                    conn.close()
            except Exception as e:
                print(f"❌ 重复检查失败，继续处理: {e}")
                logger.warning(f'重复检查失败，继续处理: {e}')
                #如果数据库查询失败，继续处理数据
            
            #分离字段类型
            fast_fields=['heart_rate','blood_oxygen','temperature','pressure_high','pressure_low','stress','step','distance','calorie','latitude','longitude','altitude','sleep']
            slow_daily_fields=['sleep_data','exercise_daily_data','workout_data','scientific_sleep_data']
            slow_weekly_fields=['exercise_week_data']
            print(f"🔍 字段分离: fast_fields={fast_fields}")
            
            #构建主表数据(只包含配置支持的快更新字段)
            main_data={'device_sn':device_sn,'user_id':user_id,'org_id':org_id,'customer_id':customer_id,'timestamp':timestamp,'upload_method':raw_data.get("upload_method","wifi")}
            print(f"🔍 初始主表数据: {main_data}")
            
            for field in fast_fields:
                if field in config_fields:
                    if field == 'sleep':
                        # 专门处理睡眠数据解析
                        sleep_data_raw = raw_data.get('sleepData') or raw_data.get('smData')
                        value = parse_sleep_data(sleep_data_raw)
                        print(f"🔍 睡眠数据解析: raw={sleep_data_raw} -> value={value}")
                    else:
                        value=raw_data.get(self.field_mapping.get(field,field))
                        print(f"🔍 字段映射: {field} -> {self.field_mapping.get(field,field)} = {value}")
                    if value is not None:
                        main_data[field]=value
            print(f"✅ 完整主表数据: {main_data}")
            
            #构建每日数据(只包含配置支持的每日字段)
            daily_data=None
            daily_fields_in_config=[f for f in slow_daily_fields if f in config_fields]
            if daily_fields_in_config:
                daily_data={'device_sn':device_sn,'user_id':user_id,'org_id':org_id,'customer_id':customer_id,'date':timestamp.date()}
                for field in daily_fields_in_config:
                    value=raw_data.get(self.field_mapping.get(field,field))
                    if value is not None:
                        daily_data[field]=value
                print(f"✅ 每日数据: {daily_data}")
            else:
                print(f"⚠️ 无每日数据字段")
                        
            #构建每周数据(只包含配置支持的每周字段)
            weekly_data=None
            weekly_fields_in_config=[f for f in slow_weekly_fields if f in config_fields]
            if weekly_fields_in_config:
                week_start=self._get_week_start(timestamp)
                weekly_data={'device_sn':device_sn,'user_id':user_id,'org_id':org_id,'customer_id':customer_id,'week_start':week_start}
                for field in weekly_fields_in_config:
                    value=raw_data.get(self.field_mapping.get(field,field))
                    if value is not None:
                        weekly_data[field]=value
                print(f"✅ 每周数据: {weekly_data}")
            else:
                print(f"⚠️ 无每周数据字段")
            
            #构建Redis数据(只包含配置字段)
            redis_data={}
            for field in config_fields:
                if field in self.field_mapping:
                    api_field=self.field_mapping[field]
                    value=raw_data.get(api_field)
                    if value is not None:
                        redis_data[api_field]=str(value)
            redis_data['deviceSn']=device_sn
            print(f"✅ Redis数据: {redis_data}")
                
            item={'device_sn':device_sn,'main_data':main_data,'daily_data':daily_data,'weekly_data':weekly_data,'redis_data':redis_data,'enable_alerts':enable_alerts,'config_info':config_info}
            print(f"🔧 准备加入队列的数据项: {json.dumps(item, ensure_ascii=False, default=str)}")
            self.batch_queue.put(item,timeout=1)
            print(f"✅ 数据已成功加入处理队列: {device_sn}")
            # 不再维护内存中的processed_keys，因为重复检测已在数据库层面完成
            # self.processed_keys.add(duplicate_key)
            return {'success':True,'reason':'queued','message':'数据已加入处理队列'}
            
        except queue.Full:
            print(f"❌ 批处理队列已满")
            logger.warning('批处理队列已满')
            return {'success':False,'reason':'queue_full','message':'处理队列已满，请稍后重试'}
        except Exception as e:
            print(f"❌ 添加数据异常: {e}")
            print(f"❌ 异常详情: {type(e).__name__} - {str(e)}")
            import traceback
            print(f"❌ 完整异常堆栈: {traceback.format_exc()}")
            logger.error(f'添加数据失败: {e}')
            return {'success':False,'reason':'error','message':f'数据处理失败: {str(e)}'}
            
    def _record_performance(self, batch_size, processing_time):
        """记录性能数据并尝试自动调优"""
        throughput = batch_size / processing_time if processing_time > 0 else 0
        
        self.performance_window.append({
            'batch_size': batch_size,
            'processing_time': processing_time,
            'throughput': throughput,
            'timestamp': time.time()
        })
        
        # 保持性能窗口大小
        if len(self.performance_window) > 50:
            self.performance_window.pop(0)
        
        # 每30秒检查一次是否需要调优
        current_time = time.time()
        if current_time - self.last_adjustment_time > 30 and len(self.performance_window) >= 10:
            self._auto_adjust_batch_size()
            self.last_adjustment_time = current_time
    
    def _auto_adjust_batch_size(self):
        """自动调整批次大小"""
        import psutil
        
        # 计算最近性能指标
        recent_performance = self.performance_window[-10:]
        avg_throughput = sum(p['throughput'] for p in recent_performance) / len(recent_performance)
        avg_processing_time = sum(p['processing_time'] for p in recent_performance) / len(recent_performance)
        
        # 系统资源检查
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory_percent = psutil.virtual_memory().percent
        queue_size = self.batch_queue.qsize()
        
        old_batch_size = self.batch_size
        
        # 调优逻辑
        if cpu_percent < 50 and avg_throughput < 100:
            # CPU利用率低，吞吐量低，增加批次大小
            self.batch_size = min(500, int(self.batch_size * 1.2))
        elif cpu_percent > 90 or memory_percent > 85:
            # 资源压力大，减少批次大小
            self.batch_size = max(50, int(self.batch_size * 0.8))
        elif queue_size > 2000:
            # 队列堆积严重，增加处理能力
            self.batch_size = min(500, int(self.batch_size * 1.1))
        
        # 记录调整
        if old_batch_size != self.batch_size:
            self.stats['auto_adjustments'] += 1
            logger.info(f"📊 HealthData批次大小自动调整: {old_batch_size} → {self.batch_size} "
                       f"(CPU: {cpu_percent:.1f}%, 内存: {memory_percent:.1f}%, "
                       f"队列: {queue_size}, 吞吐量: {avg_throughput:.1f}/秒)")
    
    def get_stats(self):#获取统计信息
        stats=self.stats.copy()
        stats['cpu_cores'] = getattr(self, 'cpu_cores', 'N/A')
        stats['batch_size'] = self.batch_size
        stats['max_workers'] = self.executor._max_workers
        stats['queue_size']=self.batch_queue.qsize()
        stats['performance_window_size'] = len(getattr(self, 'performance_window', []))
        # 不再统计processed_keys_count，因为已移除内存重复检测
        # stats['processed_keys_count']=len(self.processed_keys)
        return stats
        
    def clear_processed_keys(self):#清理已处理键值
        """智能清理过期的处理键值"""
        if len(self.processed_keys)>10000:
            # 只保留最近1小时的记录
            import time
            current_time=time.time()
            new_keys=set()
            
            for key in self.processed_keys:
                try:
                    # 从键值中提取时间戳，格式：device_sn:YYYY-MM-DD HH:MM:SS
                    parts=key.split(':',1)  # 只分割一次，防止时间戳中的冒号被误分
                    if len(parts)==2:
                        device_sn,timestamp_str=parts
                        key_timestamp=datetime.strptime(timestamp_str,'%Y-%m-%d %H:%M:%S').timestamp()
                        # 保留1小时内的记录
                        if current_time-key_timestamp<3600:
                            new_keys.add(key)
                except:
                    continue
                    
            self.processed_keys=new_keys
            logger.info(f'智能清理processed_keys缓存，保留{len(new_keys)}条记录')
        
    def _schedule_cleanup(self):#定时清理任务
        """定时清理过期键值"""
        import threading
        def cleanup_worker():
            while self.running:
                time.sleep(1800)#每30分钟清理一次
                self.clear_processed_keys()
        
        threading.Thread(target=cleanup_worker,daemon=True).start()

#全局优化器实例
optimizer=HealthDataOptimizer()

def optimized_upload_health_data(health_data):#优化的健康数据上传V3.1
    """配置化健康数据上传处理"""
    print(f"🏥 健康数据上传开始 - 原始数据: {json.dumps(health_data, ensure_ascii=False, indent=2)}")
    try:
        # 在Flask路由上下文中获取应用实例并传递给优化器
        try:
            from flask import current_app
            if current_app and not optimizer.app:
                optimizer.app = current_app._get_current_object()
        except RuntimeError:
            pass  # 忽略应用上下文不可用的错误
            
        data=health_data.get("data",{})
        
        # 提取顶级的客户信息参数
        customer_id = health_data.get("customer_id")
        org_id = health_data.get("org_id") 
        user_id = health_data.get("user_id")
        print(f"🔍 提取客户信息: customer_id={customer_id}, org_id={org_id}, user_id={user_id}")
        print(f"🔍 解析data字段: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        if isinstance(data,list):
            print(f"🔍 检测到批量数据，数量: {len(data)}")
            if len(data)>10:#大批量使用队列
                print(f"🏥 大批量处理模式: {len(data)}条数据")
                results=[]
                success_count=0
                duplicate_count=0
                error_count=0
                
                for i, item in enumerate(data):
                    # 优先从直接字段获取设备SN
                    device_sn = item.get("deviceSn") or item.get("id")
                    
                    # 如果没找到，检查嵌套的data字段
                    if not device_sn and 'data' in item:
                        nested_data = item['data']
                        if isinstance(nested_data, dict):
                            device_sn = nested_data.get('deviceSn') or nested_data.get('id')
                        elif isinstance(nested_data, list) and len(nested_data) > 0:
                            device_sn = nested_data[0].get('deviceSn') or nested_data[0].get('id')
                    
                    # 将客户信息添加到每个数据项中，优先使用顶级参数
                    if customer_id is not None:
                        item['customer_id'] = customer_id
                    if org_id is not None:
                        item['org_id'] = org_id
                    if user_id is not None:
                        item['user_id'] = user_id
                    
                    print(f"🔍 处理第{i+1}条数据: device_sn={device_sn}, 数据={json.dumps(item, ensure_ascii=False)}")
                    if device_sn:
                        result=optimizer.add_data(item,device_sn)
                        results.append(result)
                        print(f"🔍 处理结果: {result}")
                        
                        if result.get('success'):
                            if result.get('reason')=='duplicate':
                                duplicate_count+=1
                            else:
                                success_count+=1
                        else:
                            error_count+=1
                    else:
                        print(f"❌ 第{i+1}条数据缺少设备SN")
                        error_count+=1
                
                response_msg=f"批量处理完成，成功{success_count}条"
                if duplicate_count>0:
                    response_msg+=f"，重复{duplicate_count}条"
                if error_count>0:
                    response_msg+=f"，失败{error_count}条"
                
                print(f"✅ 大批量处理完成: {response_msg}")
                return jsonify({"status":"success","message":response_msg,"details":{"success":success_count,"duplicate":duplicate_count,"error":error_count}})
            else:#小批量直接处理
                print(f"🏥 小批量处理模式: {len(data)}条数据")
                return _process_batch_direct(data)
        else:
            # 优先从直接字段获取设备SN
            device_sn = data.get("deviceSn") or data.get("id")
            
            # 如果没找到，检查嵌套的data字段（针对data.data.id的情况）
            if not device_sn and 'data' in data:
                nested_data = data['data']
                if isinstance(nested_data, dict):
                    device_sn = nested_data.get('deviceSn') or nested_data.get('id')
                    print(f"🔍 从嵌套data对象提取device_sn: {device_sn}")
                elif isinstance(nested_data, list) and len(nested_data) > 0:
                    device_sn = nested_data[0].get('deviceSn') or nested_data[0].get('id')
                    print(f"🔍 从嵌套data数组提取device_sn: {device_sn}")
            
            print(f"🔍 单条数据处理: device_sn={device_sn}")
            if not device_sn:
                print(f"❌ 设备ID为空")
                return jsonify({"status":"error","message":"设备ID不能为空"})
            
            # 将客户信息添加到数据项中，优先使用顶级参数
            if customer_id is not None:
                data['customer_id'] = customer_id
            if org_id is not None:
                data['org_id'] = org_id
            if user_id is not None:
                data['user_id'] = user_id
            
            print(f"🔍 单条数据详情: {json.dumps(data, ensure_ascii=False, indent=2)}")
            #单条数据使用队列处理
            result=optimizer.add_data(data,device_sn)
            print(f"🔍 单条处理结果: {result}")
            if result.get('success'):
                if result.get('reason')=='duplicate':
                    print(f"⚠️ 数据重复: {device_sn}")
                    return jsonify({"status":"success","message":"数据重复，已跳过处理","reason":"duplicate"})
                else:
                    print(f"✅ 单条数据处理成功: {device_sn}")
                    return jsonify({"status":"success","message":result.get('message','数据处理成功')})
            else:
                print(f"❌ 单条数据处理失败: {result}")
                # 根据失败原因返回不同的状态码
                if result.get('reason')=='user_not_found':
                    return jsonify({"status":"error","message":result.get('message')}),404
                elif result.get('reason')=='queue_full':
                    return jsonify({"status":"error","message":result.get('message')}),503
                else:
                    return jsonify({"status":"error","message":result.get('message')}),500
            
    except Exception as e:
        print(f"❌ 健康数据上传异常: {e}")
        print(f"❌ 异常详情: {type(e).__name__} - {str(e)}")
        import traceback
        print(f"❌ 完整异常堆栈: {traceback.format_exc()}")
        logger.error(f'数据上传失败: {e}')
        return jsonify({"status":"error","message":str(e)}),500

def _process_batch_direct(data_list):#小批量直接处理
    """小批量数据直接同步处理"""
    print(f"🏥 小批量直接处理开始，数据量: {len(data_list)}")
    try:
        success_count=0
        duplicate_count=0
        error_count=0
        
        for i, data in enumerate(data_list):
            # 优先从直接字段获取设备SN
            device_sn = data.get("deviceSn") or data.get("id")
            
            # 如果没找到，检查嵌套的data字段
            if not device_sn and 'data' in data:
                nested_data = data['data']
                if isinstance(nested_data, dict):
                    device_sn = nested_data.get('deviceSn') or nested_data.get('id')
                elif isinstance(nested_data, list) and len(nested_data) > 0:
                    device_sn = nested_data[0].get('deviceSn') or nested_data[0].get('id')
            
            print(f"🔍 小批量处理第{i+1}条: device_sn={device_sn}, 数据={json.dumps(data, ensure_ascii=False)}")
            if device_sn:
                result=optimizer.add_data(data,device_sn)
                print(f"🔍 小批量处理结果: {result}")
                if result.get('success'):
                    if result.get('reason')=='duplicate':
                        duplicate_count+=1
                    else:
                        success_count+=1
                else:
                    error_count+=1
            else:
                print(f"❌ 第{i+1}条数据缺少设备SN")
                error_count+=1
        
        response_msg=f"批量处理完成，成功{success_count}条"
        if duplicate_count>0:
            response_msg+=f"，重复{duplicate_count}条"
        if error_count>0:
            response_msg+=f"，失败{error_count}条"
        
        print(f"✅ 小批量直接处理完成: {response_msg}")
        return jsonify({"status":"success","message":response_msg,"details":{"success":success_count,"duplicate":duplicate_count,"error":error_count}})
        
    except Exception as e:
        print(f"❌ 小批量直接处理异常: {e}")
        print(f"❌ 异常详情: {type(e).__name__} - {str(e)}")
        import traceback
        print(f"❌ 完整异常堆栈: {traceback.format_exc()}")
        logger.error(f'小批量直接处理失败: {e}')
        return jsonify({"status":"error","message":f"批量处理失败: {str(e)}"}),500

def get_optimizer_stats():#获取优化器统计
    """获取优化器运行统计信息"""
    return jsonify(optimizer.get_stats())

def save_health_data_fast(*args,**kwargs):#快速保存(兼容原接口)
    """兼容原有接口的快速保存方法"""
    try:
        #构建数据字典
        data={
            'heartRate':args[0] if len(args)>0 else kwargs.get('heartRate'),
            'pressureHigh':args[1] if len(args)>1 else kwargs.get('pressureHigh'),
            'pressureLow':args[2] if len(args)>2 else kwargs.get('pressureLow'),
            'bloodOxygen':args[3] if len(args)>3 else kwargs.get('bloodOxygen'),
            'temperature':args[4] if len(args)>4 else kwargs.get('temperature'),
            'stress':args[5] if len(args)>5 else kwargs.get('stress'),
            'step':args[6] if len(args)>6 else kwargs.get('step'),
            'timestamp':args[7] if len(args)>7 else kwargs.get('timestamp',datetime.now()),
            'deviceSn':args[8] if len(args)>8 else kwargs.get('deviceSn'),
            'distance':args[9] if len(args)>9 else kwargs.get('distance'),
            'calorie':args[10] if len(args)>10 else kwargs.get('calorie'),
            'latitude':args[11] if len(args)>11 else kwargs.get('latitude'),
            'longitude':args[12] if len(args)>12 else kwargs.get('longitude'),
            'altitude':args[13] if len(args)>13 else kwargs.get('altitude'),
            'sleepData':args[14] if len(args)>14 else kwargs.get('sleepData'),
            'exerciseDailyData':args[15] if len(args)>15 else kwargs.get('exerciseDailyData'),
            'exerciseWeekData':args[16] if len(args)>16 else kwargs.get('exerciseWeekData'),
            'scientificSleepData':args[17] if len(args)>17 else kwargs.get('scientificSleepData'),
            'workoutData':args[18] if len(args)>18 else kwargs.get('workoutData'),
            'uploadMethod':args[19] if len(args)>19 else kwargs.get('uploadMethod','wifi')
        }
        
        device_sn=data.get('deviceSn')
        if not device_sn:
            logger.error('快速保存缺少设备SN')
            return None
            
        #使用优化器处理
        result=optimizer.add_data(data,device_sn)
        if result.get('success'):
            return True
        else:
            logger.warning(f'快速保存失败: {result.get("message","未知错误")}')
            return None
        
    except Exception as e:
        logger.error(f'快速保存失败: {e}')
        return None 
def parse_sleep_data(sleep_data_json):
    """
    解析sleepData JSON，计算睡眠时长(小时)
    支持的格式：
    1. '{"code":0,"data":[{"endTimeStamp":1747440420000,"startTimeStamp":1747418280000,"type":2}],"name":"sleep","type":"history"}'
    2. null, "null", '{"code":-1,"data":[],"name":"sleep","type":"history"}'
    3. '{"code":"0","data":[],"name":"sleep","type":"history"}'
    
    返回: 睡眠时长(小时)，出错时返回None
    """
    if not sleep_data_json or sleep_data_json in ['null', None]:
        return None
    
    try:
        if isinstance(sleep_data_json, str):
            # 处理JSON字符串格式错误的情况，如'{"code":"0"data":[]}'
            sleep_data_json = sleep_data_json.replace('"0"data"', '"0","data"')
            sleep_data = json.loads(sleep_data_json)
        elif isinstance(sleep_data_json, dict):
            sleep_data = sleep_data_json
        else:
            return None
            
        # 检查数据有效性
        if not isinstance(sleep_data, dict):
            return None
            
        code = sleep_data.get('code')
        if code == -1 or code == '-1' or str(code) == '-1':
            return None
            
        data_list = sleep_data.get('data', [])
        if not isinstance(data_list, list) or len(data_list) == 0:
            return None
            
        total_sleep_seconds = 0
        
        # 遍历所有睡眠时间段，不管type，按照endTimeStamp-startTimeStamp计算
        for sleep_period in data_list:
            if not isinstance(sleep_period, dict):
                continue
                
            start_time = sleep_period.get('startTimeStamp')
            end_time = sleep_period.get('endTimeStamp')
            
            if start_time is None or end_time is None:
                continue
                
            try:
                # 时间戳转换为秒
                start_seconds = int(start_time) / 1000 if int(start_time) > 9999999999 else int(start_time)
                end_seconds = int(end_time) / 1000 if int(end_time) > 9999999999 else int(end_time)
                
                # 计算时间差(秒)
                if end_seconds > start_seconds:
                    total_sleep_seconds += (end_seconds - start_seconds)
                    
            except (ValueError, TypeError):
                continue
                
        # 转换为小时，保留2位小数
        if total_sleep_seconds > 0:
            total_sleep_hours = round(total_sleep_seconds / 3600, 2)
            return total_sleep_hours
        else:
            return None
            
    except (json.JSONDecodeError, Exception) as e:
        print(f"解析sleepData时出错: {e}, 原始数据: {sleep_data_json}")
        return None
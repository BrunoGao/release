#!/usr/bin/env python3
from flask import jsonify,request
from datetime import datetime,timedelta,date
from .models import db,UserHealthData,UserHealthDataDaily,UserHealthDataWeekly,HealthDataConfig
from .redis_helper import RedisHelper
from .alert import generate_alerts
import json,threading,queue,time,asyncio
from sqlalchemy import text,and_,or_
from concurrent.futures import ThreadPoolExecutor
from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
import pymysql
import psutil
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import uuid

#导入专业日志系统
from logging_config import health_logger,db_logger,redis_logger,log_health_data_processing

redis=RedisHelper()
logger=health_logger#使用健康数据专用记录器

class HealthDataOptimizer:#健康数据性能优化器V5.0 - 多队列分片版本
    def __init__(self):
        # CPU自适应配置
        import psutil
        self.cpu_cores = psutil.cpu_count(logical=True)
        self.memory_gb = psutil.virtual_memory().total / (1024**3)
        
        # 初始化分片批处理器
        from .sharded_batch_processor import ShardedBatchProcessor
        self.sharded_processor = ShardedBatchProcessor()
        # 设置批处理回调，让分片处理器使用现有的数据库处理逻辑
        self.sharded_processor.set_batch_callback(self._flush_batch)
        
        # 保持兼容性的统计信息接口
        self._legacy_stats = {'processed':0,'batches':0,'errors':0,'duplicates':0,'auto_adjustments':0}
        
        # 性能监控
        self.performance_window = []
        self.last_adjustment_time = time.time()
        
        logger.info(f'🚀 HealthDataOptimizer V5.0 初始化 - 多队列分片版本:')
        logger.info(f'   CPU核心: {self.cpu_cores}, 内存: {self.memory_gb:.1f}GB')
        logger.info(f'   分片数量: {self.sharded_processor.shard_count}, 批次大小: {self.sharded_processor.batch_size}')
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
        
        # 异步处理线程池
        self.executor = ThreadPoolExecutor(max_workers=max(4, self.cpu_cores), thread_name_prefix='health-async')
        self.running = True
        
        # 兼容性属性，用于现有统计和调优代码
        self.batch_size = 200  # 默认批次大小
        self.batch_queue = queue.Queue(maxsize=5000)  # 虚拟队列，用于兼容性
        self.processed_keys = set()  # 兼容性属性，用于遗留清理代码
    
    @property
    def stats(self):
        """统计信息接口，兼容现有代码"""
        if hasattr(self.sharded_processor, 'get_overall_stats'):
            sharded_stats = self.sharded_processor.get_overall_stats()
            return {
                'processed': sharded_stats.get('total_processed', 0),
                'batches': sharded_stats.get('total_batches', 0), 
                'errors': sharded_stats.get('total_errors', 0),
                'duplicates': self._legacy_stats['duplicates'],
                'auto_adjustments': self._legacy_stats['auto_adjustments']
            }
        return self._legacy_stats
        
    def _ensure_processor_started(self):#确保分片批处理器已启动
        if not self.processor_started:
            try:
                from flask import current_app
                self.app=current_app._get_current_object()#获取应用实例
                self.sharded_processor.start()  # 启动分片批处理器
                self._schedule_cleanup()#启动定时清理
                self.processor_started=True
                print(f"✅ 分片批处理器和定时清理已启动，分片数: {self.sharded_processor.shard_count}")
                logger.info('分片批处理器和定时清理已启动')
            except RuntimeError as e:
                print(f"❌ 应用上下文不可用，延迟启动批处理器: {e}")
                logger.warning('应用上下文不可用，延迟启动批处理器')
        
    # 批处理器功能已迁移到 ShardedBatchProcessor
        
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
                                (device_sn, user_id, org_id, customer_id, heart_rate, blood_oxygen, temperature, 
                                 pressure_high, pressure_low, stress, step, distance, calorie, 
                                 latitude, longitude, altitude, sleep, timestamp, upload_method, create_time)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                            """
                            
                            for record in main_records:
                                cursor.execute(insert_sql, (
                                    record.get('device_sn'),
                                    record.get('user_id'),
                                    record.get('org_id'),
                                    record.get('customer_id'),
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
                            print(f"❌ 主表批量插入失败详细错误: {str(e)}")
                            print(f"❌ 错误类型: {type(e).__name__}")
                            import traceback
                            print(f"❌ 错误堆栈: {traceback.format_exc()}")
                            db_logger.error('主表批量插入失败，尝试单条插入处理重复',extra={'error':str(e),'data_count':len(main_records)})
                            conn.rollback()
                            # 批量插入失败时，使用单条插入处理重复记录
                            try:
                                for record in main_records:
                                    cursor.execute("""
                                        SELECT id FROM t_user_health_data 
                                        WHERE device_sn = %s AND timestamp = %s
                                    """, (record.get('device_sn'), record.get('timestamp')))
                                    
                                    existing = cursor.fetchone()
                                    if not existing:
                                        cursor.execute(insert_sql, (
                                            record.get('device_sn'),
                                            record.get('user_id'),
                                            record.get('org_id'),
                                            record.get('customer_id'),
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
                                    else:
                                        self.stats['duplicates'] += 1
                                        db_logger.debug('跳过重复记录',extra={'device_sn':record.get('device_sn'),'timestamp':record.get('timestamp')})
                                
                                conn.commit()
                                db_logger.info('主表单条插入完成',extra={'data_count':len(main_records)})
                            except Exception as fallback_error:
                                print(f"❌ 主表单条插入失败详细错误: {str(fallback_error)}")
                                print(f"❌ 单条插入错误类型: {type(fallback_error).__name__}")
                                import traceback
                                print(f"❌ 单条插入错误堆栈: {traceback.format_exc()}")
                                db_logger.error('主表单条插入也失败',extra={'error':str(fallback_error),'data_count':len(main_records)})
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
                                        (device_sn, user_id, org_id, customer_id, date, sleep_data, exercise_daily_data, workout_data, create_time, update_time)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                                    """, (
                                        record['device_sn'],
                                        record['user_id'],
                                        record['org_id'],
                                        record.get('customer_id'),
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
                                        (device_sn, user_id, org_id, customer_id, week_start, exercise_week_data, create_time, update_time)
                                        VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                                    """, (
                                        record['device_sn'],
                                        record['user_id'],
                                        record['org_id'],
                                        record.get('customer_id'),
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
            
            # 确保核心字段包含在配置中，即使数据库配置中没有
            # heart_rate 是基础字段，pressure_high 和 pressure_low 根据 heart_rate 模拟生成
            # latitude, longitude, altitude 是位置信息，也是基础字段
            essential_fields = ['heart_rate', 'pressure_high', 'pressure_low', 'latitude', 'longitude', 'altitude']
            for field in essential_fields:
                if field not in fields:
                    fields.append(field)
                    weights[field] = 1.0
            
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
            
            # 优先使用直接传递的客户信息参数 - 支持两种字段名格式
            user_id = raw_data.get("user_id") or raw_data.get("userId")
            org_id = raw_data.get("org_id") or raw_data.get("orgId")
            customer_id = raw_data.get("customer_id") or raw_data.get("customerId")
            
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
            # 处理upload_method字段，将4g映射为esim
            upload_method = raw_data.get("upload_method", "wifi")
            if upload_method == "4g":
                upload_method = "esim"
            main_data={'device_sn':device_sn,'user_id':user_id,'org_id':org_id,'customer_id':customer_id,'timestamp':timestamp,'upload_method':upload_method}
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
                else:
                    print(f"⚠️ 字段 {field} 不在配置字段中，跳过处理")
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
            
            #构建Redis数据(包含配置字段和客户信息)
            redis_data={}
            for field in config_fields:
                if field in self.field_mapping:
                    api_field=self.field_mapping[field]
                    value=raw_data.get(api_field)
                    if value is not None:
                        redis_data[api_field]=str(value)
            redis_data['deviceSn']=device_sn
            # 添加客户信息用于告警规则缓存
            redis_data['customer_id']=customer_id
            redis_data['customerId']=customer_id  # 兼容性字段名
            redis_data['org_id']=org_id
            redis_data['user_id']=user_id
            print(f"✅ Redis数据(含客户信息): {redis_data}")
                
            item={'device_sn':device_sn,'main_data':main_data,'daily_data':daily_data,'weekly_data':weekly_data,'redis_data':redis_data,'enable_alerts':enable_alerts,'config_info':config_info}
            print(f"🔧 准备加入分片队列的数据项: {json.dumps(item, ensure_ascii=False, default=str)}")
            success = self.sharded_processor.add_data(item, device_sn)
            if success:
                print(f"✅ 数据已成功加入分片处理队列: {device_sn}")
            else:
                print(f"❌ 数据加入分片处理队列失败: {device_sn}")
                return {'success': False, 'reason': 'queue_full', 'message': '分片处理队列已满'}
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
        queue_size = self.sharded_processor.get_queue_size()
        
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
        stats['queue_size']=self.sharded_processor.get_queue_size()
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
        
        # 提取顶级的客户信息参数 - 支持两种字段名格式
        customer_id = health_data.get("customer_id") or health_data.get("customerId")
        org_id = health_data.get("org_id") or health_data.get("orgId")
        user_id = health_data.get("user_id") or health_data.get("userId")
        
        # 如果顶级没有，从data字段中提取
        if not customer_id and isinstance(data, dict):
            customer_id = data.get("customer_id") or data.get("customerId")
        if not org_id and isinstance(data, dict):
            org_id = data.get("org_id") or data.get("orgId")
        if not user_id and isinstance(data, dict):
            user_id = data.get("user_id") or data.get("userId")
        
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

# ================================ 异步处理框架 ================================

@dataclass
class AsyncTaskConfig:
    """异步任务配置"""
    parsing_queue_size: int = 1000
    alert_queue_size: int = 500
    aggregation_queue_size: int = 300
    notification_queue_size: int = 200
    parsing_workers: int = 8
    alert_workers: int = 12
    aggregation_workers: int = 6
    notification_workers: int = 4
    batch_timeout: float = 2.0
    max_retry_attempts: int = 3
    notification_timeout: float = 10.0

class AsyncHealthDataProcessor:
    """异步健康数据处理器 - 多阶段流水线处理架构"""
    
    def __init__(self, config: Optional[AsyncTaskConfig] = None):
        self.config = config or AsyncTaskConfig()
        
        # CPU自适应配置
        self.cpu_cores = psutil.cpu_count(logical=True)
        self.memory_gb = psutil.virtual_memory().total / (1024**3)
        
        # 动态调整工作者数量
        self._adjust_workers_by_resources()
        
        # 多阶段异步队列
        self.parsing_queue = asyncio.Queue(maxsize=self.config.parsing_queue_size)
        self.alert_queue = asyncio.Queue(maxsize=self.config.alert_queue_size)
        self.aggregation_queue = asyncio.Queue(maxsize=self.config.aggregation_queue_size)
        self.notification_queue = asyncio.Queue(maxsize=self.config.notification_queue_size)
        
        # 专用异步工作池
        self.parsing_workers = []
        self.alert_workers = []
        self.aggregation_workers = []
        self.notification_workers = []
        
        # 状态管理
        self.running = False
        self.stats = {
            'processed_total': 0,
            'parsing_processed': 0,
            'alerts_generated': 0,
            'aggregations_processed': 0,
            'notifications_sent': 0,
            'errors': {'parsing': 0, 'alerts': 0, 'aggregation': 0, 'notification': 0},
            'performance': {'avg_parsing_time': 0, 'avg_alert_time': 0, 'avg_aggregation_time': 0}
        }
        
        logger.info(f"🚀 AsyncHealthDataProcessor 初始化完成:")
        logger.info(f"   CPU核心: {self.cpu_cores}, 内存: {self.memory_gb:.1f}GB")
        logger.info(f"   工作者配置 - 解析: {self.config.parsing_workers}, "
                   f"告警: {self.config.alert_workers}, "
                   f"聚合: {self.config.aggregation_workers}, "
                   f"通知: {self.config.notification_workers}")
    
    def _adjust_workers_by_resources(self):
        """根据系统资源动态调整工作者数量"""
        # 解析工作者: CPU核心数 × 1，处理CPU密集型的JSON解析
        self.config.parsing_workers = max(4, min(16, self.cpu_cores))
        
        # 告警工作者: CPU核心数 × 1.5，平衡计算和I/O
        self.config.alert_workers = max(6, min(20, int(self.cpu_cores * 1.5)))
        
        # 聚合工作者: CPU核心数 × 0.75，数据库密集型
        self.config.aggregation_workers = max(3, min(12, int(self.cpu_cores * 0.75)))
        
        # 通知工作者: 固定数量，避免过多网络连接
        self.config.notification_workers = max(2, min(8, int(self.cpu_cores * 0.5)))
    
    async def start(self):
        """启动异步处理器"""
        if self.running:
            return
            
        self.running = True
        logger.info("🔄 启动异步健康数据处理器...")
        
        # 启动解析工作者
        for i in range(self.config.parsing_workers):
            worker = asyncio.create_task(self._parsing_worker(f"parser-{i}"))
            self.parsing_workers.append(worker)
        
        # 启动告警工作者
        for i in range(self.config.alert_workers):
            worker = asyncio.create_task(self._alert_worker(f"alert-{i}"))
            self.alert_workers.append(worker)
        
        # 启动聚合工作者
        for i in range(self.config.aggregation_workers):
            worker = asyncio.create_task(self._aggregation_worker(f"aggregation-{i}"))
            self.aggregation_workers.append(worker)
        
        # 启动通知工作者
        for i in range(self.config.notification_workers):
            worker = asyncio.create_task(self._notification_worker(f"notification-{i}"))
            self.notification_workers.append(worker)
        
        logger.info(f"✅ 异步处理器启动完成，总计 {len(self.parsing_workers + self.alert_workers + self.aggregation_workers + self.notification_workers)} 个工作者")
    
    async def stop(self):
        """停止异步处理器"""
        if not self.running:
            return
            
        self.running = False
        logger.info("🛑 停止异步健康数据处理器...")
        
        # 取消所有工作者
        all_workers = self.parsing_workers + self.alert_workers + self.aggregation_workers + self.notification_workers
        for worker in all_workers:
            worker.cancel()
        
        # 等待工作者完成
        await asyncio.gather(*all_workers, return_exceptions=True)
        
        # 清空工作者列表
        self.parsing_workers.clear()
        self.alert_workers.clear()
        self.aggregation_workers.clear()
        self.notification_workers.clear()
        
        logger.info("✅ 异步处理器已停止")
    
    async def process_health_data(self, health_data: dict) -> dict:
        """异步流水线入口"""
        task_id = str(uuid.uuid4())
        
        # 快速响应，立即将数据放入解析队列
        await self.parsing_queue.put({
            'task_id': task_id,
            'health_data': health_data,
            'timestamp': datetime.now()
        })
        
        self.stats['processed_total'] += 1
        
        return {
            "success": True,
            "task_id": task_id,
            "status": "processing",
            "message": "数据已进入异步处理管道"
        }
    
    async def _parsing_worker(self, worker_name: str):
        """数据解析工作者"""
        logger.info(f"🔍 {worker_name} 启动")
        
        while self.running:
            try:
                # 从解析队列获取任务
                task = await asyncio.wait_for(
                    self.parsing_queue.get(),
                    timeout=self.config.batch_timeout
                )
                
                start_time = time.time()
                
                # 解析健康数据
                parsed_data = await self._parse_health_data_async(task)
                
                if parsed_data:
                    # 将解析结果放入告警队列
                    await self.alert_queue.put(parsed_data)
                    
                    # 更新统计
                    processing_time = time.time() - start_time
                    self.stats['parsing_processed'] += 1
                    self._update_avg_time('avg_parsing_time', processing_time)
                
            except asyncio.TimeoutError:
                continue  # 超时继续等待
            except Exception as e:
                self.stats['errors']['parsing'] += 1
                logger.error(f"❌ {worker_name} 处理失败: {e}")
        
        logger.info(f"🔍 {worker_name} 已停止")
    
    async def _alert_worker(self, worker_name: str):
        """告警检测工作者"""
        logger.info(f"⚠️ {worker_name} 启动")
        
        while self.running:
            try:
                # 从告警队列获取任务
                parsed_data = await asyncio.wait_for(
                    self.alert_queue.get(),
                    timeout=self.config.batch_timeout
                )
                
                start_time = time.time()
                
                # 并行检测告警
                alert_results = await self._generate_alerts_async(parsed_data)
                
                # 将结果放入聚合队列
                aggregation_data = {**parsed_data, 'alert_results': alert_results}
                await self.aggregation_queue.put(aggregation_data)
                
                # 如果有告警，放入通知队列
                if alert_results:
                    await self.notification_queue.put({
                        'alerts': alert_results,
                        'device_sn': parsed_data.get('device_sn'),
                        'task_id': parsed_data.get('task_id')
                    })
                
                # 更新统计
                processing_time = time.time() - start_time
                self.stats['alerts_generated'] += len(alert_results) if alert_results else 0
                self._update_avg_time('avg_alert_time', processing_time)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.stats['errors']['alerts'] += 1
                logger.error(f"❌ {worker_name} 处理失败: {e}")
        
        logger.info(f"⚠️ {worker_name} 已停止")
    
    async def _aggregation_worker(self, worker_name: str):
        """聚合计算工作者"""
        logger.info(f"📊 {worker_name} 启动")
        
        while self.running:
            try:
                # 从聚合队列获取任务
                aggregation_data = await asyncio.wait_for(
                    self.aggregation_queue.get(),
                    timeout=self.config.batch_timeout
                )
                
                start_time = time.time()
                
                # 异步处理聚合数据
                await self._save_daily_weekly_data_async(aggregation_data)
                
                # 更新统计
                processing_time = time.time() - start_time
                self.stats['aggregations_processed'] += 1
                self._update_avg_time('avg_aggregation_time', processing_time)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.stats['errors']['aggregation'] += 1
                logger.error(f"❌ {worker_name} 处理失败: {e}")
        
        logger.info(f"📊 {worker_name} 已停止")
    
    async def _notification_worker(self, worker_name: str):
        """通知发送工作者"""
        logger.info(f"📱 {worker_name} 启动")
        
        while self.running:
            try:
                # 从通知队列获取任务
                notification_data = await asyncio.wait_for(
                    self.notification_queue.get(),
                    timeout=self.config.batch_timeout
                )
                
                # 并行发送通知
                await self._send_notifications_async(notification_data)
                
                # 更新统计
                self.stats['notifications_sent'] += len(notification_data.get('alerts', []))
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.stats['errors']['notification'] += 1
                logger.error(f"❌ {worker_name} 处理失败: {e}")
        
        logger.info(f"📱 {worker_name} 已停止")
    
    async def _parse_health_data_async(self, task: dict) -> Optional[dict]:
        """异步解析健康数据"""
        try:
            loop = asyncio.get_event_loop()
            
            # 使用线程池处理CPU密集型的JSON解析
            with ThreadPoolExecutor(max_workers=4) as parsing_pool:
                parsed_data = await loop.run_in_executor(
                    parsing_pool,
                    self._parse_health_data_sync,
                    task
                )
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"❌ 异步解析健康数据失败: {e}")
            return None
    
    def _parse_health_data_sync(self, task: dict) -> Optional[dict]:
        """同步解析健康数据（在线程池中执行）"""
        try:
            health_data = task['health_data']
            task_id = task['task_id']
            timestamp = task['timestamp']
            
            # 提取设备信息
            data = health_data.get("data", {})
            if isinstance(data, list) and len(data) > 0:
                data = data[0]  # 取第一个数据项
            
            device_sn = data.get("deviceSn") or data.get("id")
            if not device_sn:
                return None
            
            # 解析睡眠数据（CPU密集型任务）- 使用增强版解析器
            sleep_data = data.get('sleepData')
            parsed_sleep_duration = parse_sleep_data_enhanced(sleep_data) if sleep_data else None
            
            # 构建解析结果
            parsed_result = {
                'task_id': task_id,
                'device_sn': device_sn,
                'timestamp': timestamp,
                'original_data': health_data,
                'parsed_data': data,
                'sleep_duration': parsed_sleep_duration,
                'user_id': data.get('user_id'),
                'org_id': data.get('org_id'),
                'customer_id': data.get('customer_id')
            }
            
            return parsed_result
            
        except Exception as e:
            logger.error(f"❌ 同步解析健康数据失败: {e}")
            return None
    
    async def _generate_alerts_async(self, parsed_data: dict) -> List[dict]:
        """异步并行告警检测 - 使用专业告警处理器"""
        try:
            health_data = parsed_data.get('parsed_data', {})
            health_data_id = parsed_data.get('health_data_id')
            
            # 使用全局告警处理器进行并行告警检测
            active_alerts = await alert_processor.generate_alerts_async(health_data, health_data_id)
            
            return active_alerts
            
        except Exception as e:
            logger.error(f"❌ 异步告警生成失败: {e}")
            return []
    
    
    async def _save_daily_weekly_data_async(self, aggregation_data: dict):
        """异步保存每日和每周聚合数据 - 使用专业聚合处理器"""
        try:
            # 构建健康记录列表格式
            health_records = [{
                'device_sn': aggregation_data.get('device_sn'),
                'timestamp': aggregation_data.get('timestamp', datetime.now()),
                'user_id': aggregation_data.get('parsed_data', {}).get('user_id'),
                'org_id': aggregation_data.get('parsed_data', {}).get('org_id'),
                **aggregation_data.get('parsed_data', {})
            }]
            
            # 使用全局聚合处理器进行并行聚合
            result = await aggregation_processor.save_daily_weekly_data_async(health_records)
            
            logger.info(f"📊 聚合数据处理完成: {result}")
            
        except Exception as e:
            logger.error(f"❌ 异步保存聚合数据失败: {e}")
    
    async def _send_notifications_async(self, notification_data: dict):
        """异步发送通知"""
        try:
            alerts = notification_data.get('alerts', [])
            device_sn = notification_data.get('device_sn')
            
            if not alerts:
                return
            
            # 并行发送不同类型的通知
            notification_tasks = []
            
            for alert in alerts:
                # 微信通知
                if alert.get('level') in ['warning', 'critical']:
                    task = self._send_wechat_notification(alert, device_sn)
                    notification_tasks.append(task)
                
                # 邮件通知（critical级别）
                if alert.get('level') == 'critical':
                    task = self._send_email_notification(alert, device_sn)
                    notification_tasks.append(task)
            
            # 并行发送所有通知
            if notification_tasks:
                await asyncio.gather(*notification_tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"❌ 异步发送通知失败: {e}")
    
    async def _send_wechat_notification(self, alert: dict, device_sn: str):
        """发送微信通知"""
        try:
            # 模拟微信通知发送
            await asyncio.sleep(0.1)  # 模拟网络延迟
            
            message = f"[健康告警] 设备{device_sn}: {alert.get('message', '')}"
            logger.info(f"📱 微信通知已发送: {message}")
            
        except Exception as e:
            logger.error(f"❌ 微信通知发送失败: {e}")
    
    async def _send_email_notification(self, alert: dict, device_sn: str):
        """发送邮件通知"""
        try:
            # 模拟邮件通知发送
            await asyncio.sleep(0.2)  # 模拟网络延迟
            
            message = f"[紧急健康告警] 设备{device_sn}: {alert.get('message', '')}"
            logger.info(f"📧 邮件通知已发送: {message}")
            
        except Exception as e:
            logger.error(f"❌ 邮件通知发送失败: {e}")
    
    def _update_avg_time(self, metric_key: str, new_time: float):
        """更新平均处理时间"""
        current_avg = self.stats['performance'].get(metric_key, 0)
        # 简单的移动平均算法
        self.stats['performance'][metric_key] = (current_avg * 0.9) + (new_time * 0.1)
    
    def get_async_stats(self) -> dict:
        """获取异步处理器统计信息"""
        return {
            'config': {
                'cpu_cores': self.cpu_cores,
                'memory_gb': round(self.memory_gb, 1),
                'workers': {
                    'parsing': self.config.parsing_workers,
                    'alert': self.config.alert_workers,
                    'aggregation': self.config.aggregation_workers,
                    'notification': self.config.notification_workers
                }
            },
            'runtime': {
                'running': self.running,
                'total_workers': len(self.parsing_workers + self.alert_workers + 
                                   self.aggregation_workers + self.notification_workers)
            },
            'queues': {
                'parsing_queue_size': self.parsing_queue.qsize(),
                'alert_queue_size': self.alert_queue.qsize(),
                'aggregation_queue_size': self.aggregation_queue.qsize(),
                'notification_queue_size': self.notification_queue.qsize()
            },
            'statistics': self.stats
        }

# 全局异步处理器实例
async_processor = None

async def get_async_processor() -> AsyncHealthDataProcessor:
    """获取全局异步处理器实例"""
    global async_processor
    if async_processor is None:
        async_processor = AsyncHealthDataProcessor()
        await async_processor.start()
    return async_processor

# ================================ 异步睡眠数据解析器 ================================

class AsyncSleepDataParser:
    """异步睡眠数据解析器 - CPU密集型任务优化"""
    
    def __init__(self, max_workers: int = 8):
        self.max_workers = max_workers
        self.parser_pool = ThreadPoolExecutor(max_workers=max_workers)
        self.stats = {
            'parsed_total': 0,
            'parse_errors': 0,
            'avg_parse_time': 0.0,
            'batch_processed': 0
        }
        
        logger.info(f"🛏️ AsyncSleepDataParser 初始化 - 工作线程: {max_workers}")
    
    async def parse_sleep_data_async(self, sleep_data_json) -> Optional[float]:
        """异步解析单个睡眠数据"""
        try:
            loop = asyncio.get_event_loop()
            start_time = time.time()
            
            # CPU密集型任务使用线程池
            result = await loop.run_in_executor(
                self.parser_pool, 
                self._parse_sleep_data_sync, 
                sleep_data_json
            )
            
            # 更新统计
            parse_time = time.time() - start_time
            self.stats['parsed_total'] += 1
            self._update_avg_parse_time(parse_time)
            
            return result
            
        except Exception as e:
            self.stats['parse_errors'] += 1
            logger.error(f"❌ 异步睡眠数据解析失败: {e}")
            return None
    
    def _parse_sleep_data_sync(self, sleep_data_json) -> Optional[float]:
        """同步解析逻辑（在线程池中执行）"""
        # 复用现有的parse_sleep_data函数逻辑，但优化性能
        return parse_sleep_data(sleep_data_json)
    
    async def batch_parse_sleep_data(self, batch_data: List[dict]) -> List[Optional[float]]:
        """批量异步解析睡眠数据"""
        try:
            start_time = time.time()
            
            # 创建并行解析任务
            parse_tasks = []
            for item in batch_data:
                sleep_data = item.get('sleepData') or item.get('sleep_data')
                if sleep_data:
                    task = self.parse_sleep_data_async(sleep_data)
                    parse_tasks.append(task)
                else:
                    # 对于没有睡眠数据的项，直接返回None
                    parse_tasks.append(asyncio.coroutine(lambda: None)())
            
            # 并行执行所有解析任务
            results = await asyncio.gather(*parse_tasks, return_exceptions=True)
            
            # 处理异常结果
            processed_results = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"❌ 批量睡眠数据解析异常: {result}")
                    processed_results.append(None)
                else:
                    processed_results.append(result)
            
            # 更新批次统计
            batch_time = time.time() - start_time
            self.stats['batch_processed'] += 1
            
            logger.info(f"🛏️ 批量睡眠数据解析完成: {len(batch_data)}条, 耗时: {batch_time:.2f}秒")
            
            return processed_results
            
        except Exception as e:
            logger.error(f"❌ 批量睡眠数据解析失败: {e}")
            return [None] * len(batch_data)
    
    def _update_avg_parse_time(self, new_time: float):
        """更新平均解析时间"""
        current_avg = self.stats['avg_parse_time']
        # 移动平均算法
        self.stats['avg_parse_time'] = (current_avg * 0.9) + (new_time * 0.1)
    
    def get_parser_stats(self) -> dict:
        """获取解析器统计信息"""
        return {
            'config': {
                'max_workers': self.max_workers,
                'pool_active': not self.parser_pool._shutdown
            },
            'performance': {
                'parsed_total': self.stats['parsed_total'],
                'parse_errors': self.stats['parse_errors'],
                'avg_parse_time': round(self.stats['avg_parse_time'], 4),
                'batch_processed': self.stats['batch_processed'],
                'success_rate': round((self.stats['parsed_total'] - self.stats['parse_errors']) / 
                                    max(1, self.stats['parsed_total']) * 100, 2)
            }
        }
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'parser_pool') and not self.parser_pool._shutdown:
            self.parser_pool.shutdown(wait=True)

# 全局睡眠数据解析器实例
sleep_parser = AsyncSleepDataParser()

# ================================ 异步告警处理器 ================================

class AsyncAlertProcessor:
    """异步告警处理器 - 并行告警检测与通知发送"""
    
    def __init__(self, max_workers: int = 12, notification_workers: int = 4):
        self.alert_executor = ThreadPoolExecutor(max_workers=max_workers)
        self.notification_executor = ThreadPoolExecutor(max_workers=notification_workers)
        
        self.stats = {
            'alerts_processed': 0,
            'alerts_generated': 0,
            'notifications_sent': 0,
            'processing_errors': 0,
            'notification_errors': 0,
            'avg_alert_time': 0.0,
            'avg_notification_time': 0.0
        }
        
        logger.info(f"⚠️ AsyncAlertProcessor 初始化 - 告警线程: {max_workers}, 通知线程: {notification_workers}")
    
    async def generate_alerts_async(self, health_data: dict, health_data_id: Optional[int] = None) -> List[dict]:
        """异步告警检测主入口"""
        try:
            start_time = time.time()
            
            # 🚀 规则检测并行化
            detection_tasks = [
                self._detect_heart_rate_alert(health_data),
                self._detect_blood_oxygen_alert(health_data),
                self._detect_temperature_alert(health_data),
                self._detect_blood_pressure_alert(health_data),
                self._detect_step_alert(health_data),
                self._detect_stress_alert(health_data),
                self._detect_sleep_alert(health_data),
                self._detect_calorie_alert(health_data),
                self._detect_distance_alert(health_data)
            ]
            
            # 并行执行所有告警检测
            alert_results = await asyncio.gather(*detection_tasks, return_exceptions=True)
            
            # 过滤有效告警
            active_alerts = []
            for result in alert_results:
                if isinstance(result, dict) and result:
                    active_alerts.append(result)
                elif isinstance(result, Exception):
                    logger.error(f"❌ 告警检测异常: {result}")
                    self.stats['processing_errors'] += 1
            
            if active_alerts:
                # 🎯 数据库写入与通知发送并行
                db_task = self._save_alerts_to_db_async(active_alerts, health_data_id)
                notify_task = self._send_notifications_async(active_alerts, health_data.get('deviceSn', 'unknown'))
                
                # 并行执行数据库保存和通知发送
                await asyncio.gather(db_task, notify_task, return_exceptions=True)
            
            # 更新统计
            processing_time = time.time() - start_time
            self.stats['alerts_processed'] += 1
            self.stats['alerts_generated'] += len(active_alerts)
            self._update_avg_alert_time(processing_time)
            
            return active_alerts
            
        except Exception as e:
            self.stats['processing_errors'] += 1
            logger.error(f"❌ 异步告警生成失败: {e}")
            return []
    
    async def _detect_heart_rate_alert(self, health_data: dict) -> Optional[dict]:
        """心率告警检测"""
        try:
            heart_rate = self._extract_numeric_value(health_data, ['heart_rate', 'heartRate'])
            if not heart_rate:
                return None
            
            if heart_rate > 120:
                return self._create_alert('heart_rate_critical', heart_rate, 120, 
                                        f'心率危险: {heart_rate} bpm', 'critical')
            elif heart_rate > 100:
                return self._create_alert('heart_rate_high', heart_rate, 100, 
                                        f'心率偏高: {heart_rate} bpm', 'warning')
            elif heart_rate < 50:
                return self._create_alert('heart_rate_low', heart_rate, 50, 
                                        f'心率过低: {heart_rate} bpm', 'warning')
            
            return None
        except Exception as e:
            logger.error(f"心率告警检测失败: {e}")
            return None
    
    async def _detect_blood_oxygen_alert(self, health_data: dict) -> Optional[dict]:
        """血氧告警检测"""
        try:
            blood_oxygen = self._extract_numeric_value(health_data, ['blood_oxygen', 'bloodOxygen'])
            if not blood_oxygen:
                return None
            
            if blood_oxygen < 90:
                return self._create_alert('blood_oxygen_critical', blood_oxygen, 90,
                                        f'血氧危险: {blood_oxygen}%', 'critical')
            elif blood_oxygen < 95:
                return self._create_alert('blood_oxygen_low', blood_oxygen, 95,
                                        f'血氧偏低: {blood_oxygen}%', 'warning')
            
            return None
        except Exception as e:
            logger.error(f"血氧告警检测失败: {e}")
            return None
    
    async def _detect_temperature_alert(self, health_data: dict) -> Optional[dict]:
        """体温告警检测"""
        try:
            temperature = self._extract_numeric_value(health_data, ['temperature', 'body_temperature'])
            if not temperature:
                return None
            
            if temperature > 38.5:
                return self._create_alert('temperature_critical', temperature, 38.5,
                                        f'体温危险: {temperature}°C', 'critical')
            elif temperature > 37.5:
                return self._create_alert('temperature_high', temperature, 37.5,
                                        f'体温偏高: {temperature}°C', 'warning')
            elif temperature < 35.5:
                return self._create_alert('temperature_low', temperature, 35.5,
                                        f'体温过低: {temperature}°C', 'warning')
            
            return None
        except Exception as e:
            logger.error(f"体温告警检测失败: {e}")
            return None
    
    async def _detect_blood_pressure_alert(self, health_data: dict) -> Optional[dict]:
        """血压告警检测"""
        try:
            systolic = self._extract_numeric_value(health_data, ['pressure_high', 'blood_pressure_systolic'])
            diastolic = self._extract_numeric_value(health_data, ['pressure_low', 'blood_pressure_diastolic'])
            
            # 收缩压检测
            if systolic:
                if systolic > 160:
                    return self._create_alert('blood_pressure_critical', systolic, 160,
                                            f'收缩压危险: {systolic} mmHg', 'critical')
                elif systolic > 140:
                    return self._create_alert('blood_pressure_high', systolic, 140,
                                            f'收缩压偏高: {systolic} mmHg', 'warning')
            
            # 舒张压检测
            if diastolic:
                if diastolic > 100:
                    return self._create_alert('blood_pressure_critical', diastolic, 100,
                                            f'舒张压危险: {diastolic} mmHg', 'critical')
                elif diastolic > 90:
                    return self._create_alert('blood_pressure_high', diastolic, 90,
                                            f'舒张压偏高: {diastolic} mmHg', 'warning')
            
            return None
        except Exception as e:
            logger.error(f"血压告警检测失败: {e}")
            return None
    
    async def _detect_step_alert(self, health_data: dict) -> Optional[dict]:
        """步数告警检测"""
        try:
            steps = self._extract_numeric_value(health_data, ['step', 'steps'])
            if not steps:
                return None
            
            # 根据时间判断步数目标（每日目标）
            current_hour = datetime.now().hour
            expected_steps = max(500, int(6000 * current_hour / 24))  # 动态目标
            
            if steps < expected_steps and current_hour > 18:  # 晚上6点后检测
                return self._create_alert('steps_low', steps, expected_steps,
                                        f'今日步数不足: {steps}步，建议增加运动', 'info')
            
            return None
        except Exception as e:
            logger.error(f"步数告警检测失败: {e}")
            return None
    
    async def _detect_stress_alert(self, health_data: dict) -> Optional[dict]:
        """压力告警检测"""
        try:
            stress = self._extract_numeric_value(health_data, ['stress'])
            if not stress:
                return None
            
            if stress > 80:
                return self._create_alert('stress_critical', stress, 80,
                                        f'压力过大: {stress}%，请立即休息', 'critical')
            elif stress > 70:
                return self._create_alert('stress_high', stress, 70,
                                        f'压力偏高: {stress}%，建议放松', 'warning')
            
            return None
        except Exception as e:
            logger.error(f"压力告警检测失败: {e}")
            return None
    
    async def _detect_sleep_alert(self, health_data: dict) -> Optional[dict]:
        """睡眠告警检测"""
        try:
            # 检查是否有睡眠数据
            sleep_data = health_data.get('sleepData') or health_data.get('sleep_data')
            if not sleep_data:
                return None
            
            # 使用异步睡眠解析器
            sleep_duration = await sleep_parser.parse_sleep_data_async(sleep_data)
            if not sleep_duration:
                return None
            
            if sleep_duration < 5:
                return self._create_alert('sleep_insufficient', sleep_duration, 7,
                                        f'睡眠不足: {sleep_duration}小时', 'warning')
            elif sleep_duration > 10:
                return self._create_alert('sleep_excessive', sleep_duration, 10,
                                        f'睡眠过多: {sleep_duration}小时', 'info')
            
            return None
        except Exception as e:
            logger.error(f"睡眠告警检测失败: {e}")
            return None
    
    async def _detect_calorie_alert(self, health_data: dict) -> Optional[dict]:
        """卡路里告警检测"""
        try:
            calorie = self._extract_numeric_value(health_data, ['calorie', 'calories'])
            if not calorie:
                return None
            
            # 根据时间判断卡路里目标
            current_hour = datetime.now().hour
            expected_calorie = max(200, int(1800 * current_hour / 24))
            
            if calorie < expected_calorie and current_hour > 18:
                return self._create_alert('calorie_low', calorie, expected_calorie,
                                        f'今日消耗不足: {calorie}卡路里', 'info')
            
            return None
        except Exception as e:
            logger.error(f"卡路里告警检测失败: {e}")
            return None
    
    async def _detect_distance_alert(self, health_data: dict) -> Optional[dict]:
        """距离告警检测"""
        try:
            distance = self._extract_numeric_value(health_data, ['distance'])
            if not distance:
                return None
            
            # 距离目标检测（公里）
            if distance < 2 and datetime.now().hour > 18:
                return self._create_alert('distance_low', distance, 5,
                                        f'今日运动距离不足: {distance}公里', 'info')
            
            return None
        except Exception as e:
            logger.error(f"距离告警检测失败: {e}")
            return None
    
    def _extract_numeric_value(self, health_data: dict, field_names: List[str]) -> Optional[float]:
        """从健康数据中提取数值"""
        for field in field_names:
            value = health_data.get(field)
            if value is not None:
                try:
                    return float(value)
                except (ValueError, TypeError):
                    continue
        return None
    
    def _create_alert(self, alert_type: str, value: float, threshold: float, message: str, level: str) -> dict:
        """创建告警对象"""
        return {
            'type': alert_type,
            'value': value,
            'threshold': threshold,
            'message': message,
            'level': level,
            'timestamp': datetime.now().isoformat(),
            'device_sn': None  # 将在上层设置
        }
    
    async def _save_alerts_to_db_async(self, alerts: List[dict], health_data_id: Optional[int]):
        """异步保存告警到数据库"""
        try:
            if not alerts:
                return
            
            loop = asyncio.get_event_loop()
            
            # 使用线程池执行数据库操作
            await loop.run_in_executor(
                self.alert_executor,
                self._save_alerts_to_db_sync,
                alerts, health_data_id
            )
            
        except Exception as e:
            logger.error(f"❌ 异步保存告警失败: {e}")
    
    def _save_alerts_to_db_sync(self, alerts: List[dict], health_data_id: Optional[int]):
        """同步保存告警到数据库"""
        try:
            # 这里应该调用现有的generate_alerts函数或直接操作数据库
            # 为了集成现有系统，可以调用原有的告警生成逻辑
            from .alert import generate_alerts
            
            # 构造兼容的数据格式
            for alert in alerts:
                # 调用现有的告警生成函数
                generate_alerts({
                    'deviceSn': alert.get('device_sn', 'unknown'),
                    'alert_type': alert['type'],
                    'alert_level': alert['level'],
                    'alert_message': alert['message'],
                    'alert_value': alert['value'],
                    'alert_threshold': alert['threshold']
                }, health_data_id)
            
            logger.info(f"📝 告警数据库保存完成: {len(alerts)}条告警")
            
        except Exception as e:
            logger.error(f"❌ 同步保存告警失败: {e}")
    
    async def _send_notifications_async(self, alerts: List[dict], device_sn: str):
        """异步通知发送（微信、邮件等）"""
        try:
            if not alerts:
                return
            
            start_time = time.time()
            notification_tasks = []
            
            for alert in alerts:
                alert['device_sn'] = device_sn  # 设置设备SN
                
                # 根据告警级别决定通知方式
                if alert.get('level') in ['warning', 'critical']:
                    # 微信通知
                    task = self._send_wechat_notification_async(alert)
                    notification_tasks.append(task)
                
                # 紧急告警发送邮件
                if alert.get('level') == 'critical':
                    task = self._send_email_notification_async(alert)
                    notification_tasks.append(task)
                
                # 短信通知（critical级别）
                if alert.get('level') == 'critical':
                    task = self._send_sms_notification_async(alert)
                    notification_tasks.append(task)
            
            # 🚀 并行发送所有通知
            if notification_tasks:
                results = await asyncio.gather(*notification_tasks, return_exceptions=True)
                
                # 统计发送结果
                success_count = sum(1 for r in results if not isinstance(r, Exception))
                error_count = len(results) - success_count
                
                self.stats['notifications_sent'] += success_count
                self.stats['notification_errors'] += error_count
            
            # 更新通知时间统计
            notification_time = time.time() - start_time
            self._update_avg_notification_time(notification_time)
            
        except Exception as e:
            self.stats['notification_errors'] += 1
            logger.error(f"❌ 异步通知发送失败: {e}")
    
    async def _send_wechat_notification_async(self, alert: dict):
        """异步发送微信通知"""
        try:
            # 模拟网络I/O延迟
            await asyncio.sleep(0.1)
            
            message = f"[健康告警] 设备{alert.get('device_sn')}: {alert.get('message', '')}"
            logger.info(f"📱 微信通知: {message}")
            
            return {"status": "success", "type": "wechat"}
            
        except Exception as e:
            logger.error(f"❌ 微信通知发送失败: {e}")
            raise e
    
    async def _send_email_notification_async(self, alert: dict):
        """异步发送邮件通知"""
        try:
            # 模拟网络I/O延迟
            await asyncio.sleep(0.2)
            
            message = f"[紧急健康告警] 设备{alert.get('device_sn')}: {alert.get('message', '')}"
            logger.info(f"📧 邮件通知: {message}")
            
            return {"status": "success", "type": "email"}
            
        except Exception as e:
            logger.error(f"❌ 邮件通知发送失败: {e}")
            raise e
    
    async def _send_sms_notification_async(self, alert: dict):
        """异步发送短信通知"""
        try:
            # 模拟网络I/O延迟
            await asyncio.sleep(0.15)
            
            message = f"[健康紧急告警] {alert.get('device_sn')}: {alert.get('message', '')}"
            logger.info(f"📲 短信通知: {message}")
            
            return {"status": "success", "type": "sms"}
            
        except Exception as e:
            logger.error(f"❌ 短信通知发送失败: {e}")
            raise e
    
    def _update_avg_alert_time(self, new_time: float):
        """更新平均告警处理时间"""
        current_avg = self.stats['avg_alert_time']
        self.stats['avg_alert_time'] = (current_avg * 0.9) + (new_time * 0.1)
    
    def _update_avg_notification_time(self, new_time: float):
        """更新平均通知发送时间"""
        current_avg = self.stats['avg_notification_time']
        self.stats['avg_notification_time'] = (current_avg * 0.9) + (new_time * 0.1)
    
    def get_alert_stats(self) -> dict:
        """获取告警处理器统计信息"""
        return {
            'config': {
                'alert_workers': self.alert_executor._max_workers,
                'notification_workers': self.notification_executor._max_workers,
                'alert_pool_active': not self.alert_executor._shutdown,
                'notification_pool_active': not self.notification_executor._shutdown
            },
            'performance': {
                'alerts_processed': self.stats['alerts_processed'],
                'alerts_generated': self.stats['alerts_generated'],
                'notifications_sent': self.stats['notifications_sent'],
                'processing_errors': self.stats['processing_errors'],
                'notification_errors': self.stats['notification_errors'],
                'avg_alert_time': round(self.stats['avg_alert_time'], 4),
                'avg_notification_time': round(self.stats['avg_notification_time'], 4),
                'alert_success_rate': round((self.stats['alerts_processed'] - self.stats['processing_errors']) / 
                                          max(1, self.stats['alerts_processed']) * 100, 2),
                'notification_success_rate': round((self.stats['notifications_sent']) / 
                                                  max(1, self.stats['notifications_sent'] + self.stats['notification_errors']) * 100, 2)
            }
        }
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'alert_executor') and not self.alert_executor._shutdown:
            self.alert_executor.shutdown(wait=True)
        if hasattr(self, 'notification_executor') and not self.notification_executor._shutdown:
            self.notification_executor.shutdown(wait=True)

# 全局告警处理器实例
alert_processor = AsyncAlertProcessor()

# ================================ 异步聚合计算处理器 ================================

class AsyncAggregationProcessor:
    """异步聚合计算处理器 - 并行处理每日/每周数据聚合"""
    
    def __init__(self, max_workers: int = 6):
        self.aggregation_executor = ThreadPoolExecutor(max_workers=max_workers)
        
        self.stats = {
            'daily_processed': 0,
            'weekly_processed': 0,
            'aggregation_errors': 0,
            'avg_daily_time': 0.0,
            'avg_weekly_time': 0.0,
            'device_groups_processed': 0
        }
        
        logger.info(f"📊 AsyncAggregationProcessor 初始化 - 聚合线程: {max_workers}")
    
    async def save_daily_weekly_data_async(self, health_records: List[dict]) -> dict:
        """异步聚合数据计算主入口"""
        try:
            start_time = time.time()
            
            # 🚀 按设备分组，并行处理
            device_groups = self._group_by_device(health_records)
            
            if not device_groups:
                return {'status': 'success', 'processed': 0, 'message': '没有需要聚合的数据'}
            
            # 创建并行聚合任务
            aggregation_tasks = []
            for device_sn, records in device_groups.items():
                task = self._process_device_aggregation_async(device_sn, records)
                aggregation_tasks.append(task)
            
            # 并行执行所有设备的聚合计算
            results = await asyncio.gather(*aggregation_tasks, return_exceptions=True)
            
            # 统计处理结果
            success_count = 0
            error_count = 0
            daily_count = 0
            weekly_count = 0
            
            for result in results:
                if isinstance(result, dict) and result.get('success'):
                    success_count += 1
                    daily_count += result.get('daily_processed', 0)
                    weekly_count += result.get('weekly_processed', 0)
                elif isinstance(result, Exception):
                    error_count += 1
                    logger.error(f"❌ 设备聚合计算异常: {result}")
                else:
                    error_count += 1
            
            # 更新统计
            processing_time = time.time() - start_time
            self.stats['device_groups_processed'] += len(device_groups)
            self.stats['daily_processed'] += daily_count
            self.stats['weekly_processed'] += weekly_count
            self.stats['aggregation_errors'] += error_count
            
            logger.info(f"📊 聚合计算完成: {len(device_groups)}个设备组, "
                       f"每日记录: {daily_count}, 每周记录: {weekly_count}, "
                       f"耗时: {processing_time:.2f}秒")
            
            return {
                'status': 'success',
                'device_groups': len(device_groups),
                'daily_processed': daily_count,
                'weekly_processed': weekly_count,
                'errors': error_count,
                'processing_time': processing_time
            }
            
        except Exception as e:
            self.stats['aggregation_errors'] += 1
            logger.error(f"❌ 异步聚合计算失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _group_by_device(self, health_records: List[dict]) -> Dict[str, List[dict]]:
        """按设备SN分组健康记录"""
        device_groups = {}
        
        for record in health_records:
            device_sn = record.get('device_sn')
            if device_sn:
                if device_sn not in device_groups:
                    device_groups[device_sn] = []
                device_groups[device_sn].append(record)
        
        return device_groups
    
    async def _process_device_aggregation_async(self, device_sn: str, records: List[dict]) -> dict:
        """处理单设备聚合计算"""
        try:
            loop = asyncio.get_event_loop()
            
            # 并行计算每日和每周统计
            daily_task = loop.run_in_executor(
                self.aggregation_executor,
                self._calculate_daily_statistics,
                device_sn, records
            )
            
            weekly_task = loop.run_in_executor(
                self.aggregation_executor,
                self._calculate_weekly_statistics,
                device_sn, records
            )
            
            # 等待计算完成
            daily_stats, weekly_stats = await asyncio.gather(daily_task, weekly_task)
            
            # 🎯 并行保存到数据库
            if daily_stats or weekly_stats:
                save_tasks = []
                
                if daily_stats:
                    save_tasks.append(
                        loop.run_in_executor(
                            self.aggregation_executor,
                            self._save_daily_data_sync,
                            device_sn, daily_stats
                        )
                    )
                
                if weekly_stats:
                    save_tasks.append(
                        loop.run_in_executor(
                            self.aggregation_executor,
                            self._save_weekly_data_sync,
                            device_sn, weekly_stats
                        )
                    )
                
                # 并行保存
                if save_tasks:
                    await asyncio.gather(*save_tasks, return_exceptions=True)
            
            return {
                'success': True,
                'device_sn': device_sn,
                'daily_processed': len(daily_stats) if daily_stats else 0,
                'weekly_processed': len(weekly_stats) if weekly_stats else 0
            }
            
        except Exception as e:
            logger.error(f"❌ 设备{device_sn}聚合计算失败: {e}")
            return {'success': False, 'device_sn': device_sn, 'error': str(e)}
    
    def _calculate_daily_statistics(self, device_sn: str, records: List[dict]) -> List[dict]:
        """计算每日统计数据"""
        try:
            daily_stats = []
            
            # 按日期分组记录
            date_groups = {}
            for record in records:
                timestamp = record.get('timestamp')
                if timestamp:
                    if isinstance(timestamp, str):
                        date_obj = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).date()
                    else:
                        date_obj = timestamp.date() if hasattr(timestamp, 'date') else timestamp
                    
                    date_key = date_obj.strftime('%Y-%m-%d')
                    if date_key not in date_groups:
                        date_groups[date_key] = []
                    date_groups[date_key].append(record)
            
            # 计算每日聚合数据
            for date_str, date_records in date_groups.items():
                daily_data = self._aggregate_daily_data(device_sn, date_str, date_records)
                if daily_data:
                    daily_stats.append(daily_data)
            
            return daily_stats
            
        except Exception as e:
            logger.error(f"❌ 设备{device_sn}每日统计计算失败: {e}")
            return []
    
    def _calculate_weekly_statistics(self, device_sn: str, records: List[dict]) -> List[dict]:
        """计算每周统计数据"""
        try:
            weekly_stats = []
            
            # 按周分组记录
            week_groups = {}
            for record in records:
                timestamp = record.get('timestamp')
                if timestamp:
                    if isinstance(timestamp, str):
                        date_obj = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).date()
                    else:
                        date_obj = timestamp.date() if hasattr(timestamp, 'date') else timestamp
                    
                    # 获取周开始日期（周一）
                    week_start = date_obj - timedelta(days=date_obj.weekday())
                    week_key = week_start.strftime('%Y-%m-%d')
                    
                    if week_key not in week_groups:
                        week_groups[week_key] = []
                    week_groups[week_key].append(record)
            
            # 计算每周聚合数据
            for week_start_str, week_records in week_groups.items():
                weekly_data = self._aggregate_weekly_data(device_sn, week_start_str, week_records)
                if weekly_data:
                    weekly_stats.append(weekly_data)
            
            return weekly_stats
            
        except Exception as e:
            logger.error(f"❌ 设备{device_sn}每周统计计算失败: {e}")
            return []
    
    def _aggregate_daily_data(self, device_sn: str, date_str: str, records: List[dict]) -> Optional[dict]:
        """聚合每日数据"""
        try:
            if not records:
                return None
            
            # 提取聚合字段
            sleep_data_list = []
            exercise_data_list = []
            workout_data_list = []
            
            # 基础健康指标聚合
            heart_rates = []
            blood_oxygens = []
            temperatures = []
            steps = []
            calories = []
            distances = []
            
            for record in records:
                # 提取复合数据
                if record.get('sleepData'):
                    sleep_data_list.append(record['sleepData'])
                if record.get('exerciseDailyData'):
                    exercise_data_list.append(record['exerciseDailyData'])
                if record.get('workoutData'):
                    workout_data_list.append(record['workoutData'])
                
                # 提取基础指标
                if record.get('heart_rate'):
                    heart_rates.append(float(record['heart_rate']))
                if record.get('blood_oxygen'):
                    blood_oxygens.append(float(record['blood_oxygen']))
                if record.get('temperature'):
                    temperatures.append(float(record['temperature']))
                if record.get('step'):
                    steps.append(int(record['step']))
                if record.get('calorie'):
                    calories.append(float(record['calorie']))
                if record.get('distance'):
                    distances.append(float(record['distance']))
            
            # 构建每日聚合数据
            daily_data = {
                'device_sn': device_sn,
                'date': date_str,
                'record_count': len(records),
                'user_id': records[0].get('user_id'),
                'org_id': records[0].get('org_id')
            }
            
            # 复合数据处理
            if sleep_data_list:
                daily_data['sleep_data'] = json.dumps(sleep_data_list[-1])  # 使用最新的睡眠数据
            if exercise_data_list:
                daily_data['exercise_daily_data'] = json.dumps(exercise_data_list[-1])
            if workout_data_list:
                daily_data['workout_data'] = json.dumps(workout_data_list[-1])
            
            # 基础指标统计
            if heart_rates:
                daily_data['avg_heart_rate'] = round(sum(heart_rates) / len(heart_rates), 1)
                daily_data['max_heart_rate'] = max(heart_rates)
                daily_data['min_heart_rate'] = min(heart_rates)
            
            if blood_oxygens:
                daily_data['avg_blood_oxygen'] = round(sum(blood_oxygens) / len(blood_oxygens), 1)
                daily_data['min_blood_oxygen'] = min(blood_oxygens)
            
            if temperatures:
                daily_data['avg_temperature'] = round(sum(temperatures) / len(temperatures), 1)
                daily_data['max_temperature'] = max(temperatures)
            
            if steps:
                daily_data['total_steps'] = sum(steps)
                daily_data['max_steps'] = max(steps)
            
            if calories:
                daily_data['total_calories'] = round(sum(calories), 1)
            
            if distances:
                daily_data['total_distance'] = round(sum(distances), 2)
            
            return daily_data
            
        except Exception as e:
            logger.error(f"❌ 每日数据聚合失败: {e}")
            return None
    
    def _aggregate_weekly_data(self, device_sn: str, week_start_str: str, records: List[dict]) -> Optional[dict]:
        """聚合每周数据"""
        try:
            if not records:
                return None
            
            # 提取运动数据
            exercise_week_data_list = []
            
            # 基础指标聚合
            total_steps = 0
            total_calories = 0
            total_distance = 0
            heart_rate_sum = 0
            heart_rate_count = 0
            
            for record in records:
                if record.get('exerciseWeekData'):
                    exercise_week_data_list.append(record['exerciseWeekData'])
                
                # 累计指标
                if record.get('step'):
                    total_steps += int(record['step'])
                if record.get('calorie'):
                    total_calories += float(record['calorie'])
                if record.get('distance'):
                    total_distance += float(record['distance'])
                if record.get('heart_rate'):
                    heart_rate_sum += float(record['heart_rate'])
                    heart_rate_count += 1
            
            # 构建每周聚合数据
            weekly_data = {
                'device_sn': device_sn,
                'week_start': week_start_str,
                'record_count': len(records),
                'user_id': records[0].get('user_id'),
                'org_id': records[0].get('org_id'),
                'total_steps': total_steps,
                'total_calories': round(total_calories, 1),
                'total_distance': round(total_distance, 2)
            }
            
            # 运动数据
            if exercise_week_data_list:
                weekly_data['exercise_week_data'] = json.dumps(exercise_week_data_list[-1])
            
            # 平均心率
            if heart_rate_count > 0:
                weekly_data['avg_heart_rate'] = round(heart_rate_sum / heart_rate_count, 1)
            
            return weekly_data
            
        except Exception as e:
            logger.error(f"❌ 每周数据聚合失败: {e}")
            return None
    
    def _save_daily_data_sync(self, device_sn: str, daily_stats: List[dict]):
        """同步保存每日数据"""
        try:
            for daily_data in daily_stats:
                # 这里应该调用数据库操作
                # 可以集成现有的保存逻辑，或直接操作数据库
                logger.info(f"📅 保存每日数据: 设备{device_sn}, 日期{daily_data.get('date')}, "
                           f"记录数: {daily_data.get('record_count', 0)}")
                
                # 模拟数据库保存操作
                # 实际实现中应该调用 UserHealthDataDaily.create() 或类似方法
            
            self.stats['daily_processed'] += len(daily_stats)
            
        except Exception as e:
            logger.error(f"❌ 保存每日数据失败: {e}")
    
    def _save_weekly_data_sync(self, device_sn: str, weekly_stats: List[dict]):
        """同步保存每周数据"""
        try:
            for weekly_data in weekly_stats:
                # 这里应该调用数据库操作
                logger.info(f"📊 保存每周数据: 设备{device_sn}, 周开始{weekly_data.get('week_start')}, "
                           f"记录数: {weekly_data.get('record_count', 0)}")
                
                # 模拟数据库保存操作
                # 实际实现中应该调用 UserHealthDataWeekly.create() 或类似方法
            
            self.stats['weekly_processed'] += len(weekly_stats)
            
        except Exception as e:
            logger.error(f"❌ 保存每周数据失败: {e}")
    
    def _update_avg_daily_time(self, new_time: float):
        """更新平均每日处理时间"""
        current_avg = self.stats['avg_daily_time']
        self.stats['avg_daily_time'] = (current_avg * 0.9) + (new_time * 0.1)
    
    def _update_avg_weekly_time(self, new_time: float):
        """更新平均每周处理时间"""
        current_avg = self.stats['avg_weekly_time']
        self.stats['avg_weekly_time'] = (current_avg * 0.9) + (new_time * 0.1)
    
    def get_aggregation_stats(self) -> dict:
        """获取聚合处理器统计信息"""
        return {
            'config': {
                'max_workers': self.aggregation_executor._max_workers,
                'pool_active': not self.aggregation_executor._shutdown
            },
            'performance': {
                'daily_processed': self.stats['daily_processed'],
                'weekly_processed': self.stats['weekly_processed'],
                'device_groups_processed': self.stats['device_groups_processed'],
                'aggregation_errors': self.stats['aggregation_errors'],
                'avg_daily_time': round(self.stats['avg_daily_time'], 4),
                'avg_weekly_time': round(self.stats['avg_weekly_time'], 4),
                'success_rate': round((self.stats['daily_processed'] + self.stats['weekly_processed']) / 
                                    max(1, self.stats['daily_processed'] + self.stats['weekly_processed'] + 
                                    self.stats['aggregation_errors']) * 100, 2)
            }
        }
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'aggregation_executor') and not self.aggregation_executor._shutdown:
            self.aggregation_executor.shutdown(wait=True)

# 全局聚合处理器实例
aggregation_processor = AsyncAggregationProcessor()

# ================================ 动态资源管理系统 ================================

class DynamicResourceManager:
    """动态资源管理器 - 实时监控系统资源并动态调整处理器配置"""
    
    def __init__(self, monitoring_interval: float = 30.0):
        self.monitoring_interval = monitoring_interval
        self.running = False
        self.monitor_task = None
        
        self.stats = {
            'adjustments_made': 0,
            'cpu_readings': [],
            'memory_readings': [],
            'queue_depth_readings': [],
            'last_adjustment_time': 0,
            'performance_trend': 'stable'  # 'improving', 'degrading', 'stable'
        }
        
        # 调整阈值
        self.cpu_high_threshold = 85.0
        self.cpu_low_threshold = 30.0
        self.memory_high_threshold = 80.0
        self.queue_depth_threshold = 1000
        self.min_adjustment_interval = 60.0  # 最小调整间隔60秒
        
        logger.info(f"📊 DynamicResourceManager 初始化 - 监控间隔: {monitoring_interval}秒")
    
    async def start_monitoring(self):
        """启动资源监控"""
        if self.running:
            return
            
        self.running = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("🔍 动态资源监控已启动")
    
    async def stop_monitoring(self):
        """停止资源监控"""
        if not self.running:
            return
            
        self.running = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("🛑 动态资源监控已停止")
    
    async def _monitoring_loop(self):
        """资源监控循环"""
        while self.running:
            try:
                # 收集系统指标
                cpu_percent = psutil.cpu_percent(interval=1.0)
                memory_info = psutil.virtual_memory()
                memory_percent = memory_info.percent
                
                # 收集队列深度信息
                queue_depths = self._get_queue_depths()
                
                # 记录指标
                self._record_metrics(cpu_percent, memory_percent, queue_depths)
                
                # 判断是否需要调整
                adjustment_needed = self._analyze_adjustment_need(
                    cpu_percent, memory_percent, queue_depths
                )
                
                if adjustment_needed:
                    await self._perform_dynamic_adjustment(
                        cpu_percent, memory_percent, queue_depths
                    )
                
                # 等待下次监控
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"❌ 资源监控循环异常: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    def _get_queue_depths(self) -> dict:
        """获取所有队列深度"""
        queue_depths = {
            'total_depth': 0,
            'parsing_queue': 0,
            'alert_queue': 0,
            'aggregation_queue': 0,
            'notification_queue': 0
        }
        
        try:
            # 获取异步处理器队列深度
            if async_processor and async_processor.running:
                queue_depths['parsing_queue'] = async_processor.parsing_queue.qsize()
                queue_depths['alert_queue'] = async_processor.alert_queue.qsize()
                queue_depths['aggregation_queue'] = async_processor.aggregation_queue.qsize()
                queue_depths['notification_queue'] = async_processor.notification_queue.qsize()
                
                queue_depths['total_depth'] = (
                    queue_depths['parsing_queue'] + 
                    queue_depths['alert_queue'] + 
                    queue_depths['aggregation_queue'] + 
                    queue_depths['notification_queue']
                )
            
            # 获取传统优化器队列深度
            if hasattr(optimizer, 'batch_queue'):
                queue_depths['batch_queue'] = optimizer.batch_queue.qsize()
                queue_depths['total_depth'] += queue_depths['batch_queue']
        
        except Exception as e:
            logger.error(f"❌ 获取队列深度失败: {e}")
        
        return queue_depths
    
    def _record_metrics(self, cpu_percent: float, memory_percent: float, queue_depths: dict):
        """记录系统指标"""
        current_time = time.time()
        
        # 保留最近100个读数
        max_readings = 100
        
        self.stats['cpu_readings'].append({
            'value': cpu_percent,
            'timestamp': current_time
        })
        self.stats['memory_readings'].append({
            'value': memory_percent,
            'timestamp': current_time
        })
        self.stats['queue_depth_readings'].append({
            'value': queue_depths['total_depth'],
            'timestamp': current_time
        })
        
        # 保持记录数量限制
        for readings_key in ['cpu_readings', 'memory_readings', 'queue_depth_readings']:
            if len(self.stats[readings_key]) > max_readings:
                self.stats[readings_key] = self.stats[readings_key][-max_readings:]
    
    def _analyze_adjustment_need(self, cpu_percent: float, memory_percent: float, 
                               queue_depths: dict) -> bool:
        """分析是否需要进行动态调整"""
        current_time = time.time()
        
        # 检查调整间隔
        if (current_time - self.stats['last_adjustment_time']) < self.min_adjustment_interval:
            return False
        
        # CPU压力检查
        cpu_pressure = cpu_percent > self.cpu_high_threshold
        cpu_idle = cpu_percent < self.cpu_low_threshold
        
        # 内存压力检查
        memory_pressure = memory_percent > self.memory_high_threshold
        
        # 队列积压检查
        queue_backlog = queue_depths['total_depth'] > self.queue_depth_threshold
        
        # 性能趋势分析
        performance_degrading = self._analyze_performance_trend()
        
        # 需要调整的条件
        adjustment_conditions = [
            cpu_pressure and queue_backlog,  # CPU高且队列积压
            memory_pressure,  # 内存压力过大
            cpu_idle and not queue_backlog,  # CPU空闲且没有积压
            performance_degrading and queue_backlog,  # 性能下降且有积压
        ]
        
        return any(adjustment_conditions)
    
    def _analyze_performance_trend(self) -> bool:
        """分析性能趋势"""
        if len(self.stats['cpu_readings']) < 10:
            return False
        
        # 分析最近的CPU和队列趋势
        recent_cpu = [r['value'] for r in self.stats['cpu_readings'][-10:]]
        recent_queues = [r['value'] for r in self.stats['queue_depth_readings'][-10:]]
        
        # 简单趋势分析：检查是否呈上升趋势
        cpu_trend_up = recent_cpu[-1] > recent_cpu[0] + 10  # CPU上升超过10%
        queue_trend_up = recent_queues[-1] > recent_queues[0] + 100  # 队列深度上升超过100
        
        if cpu_trend_up and queue_trend_up:
            self.stats['performance_trend'] = 'degrading'
            return True
        elif not cpu_trend_up and not queue_trend_up:
            self.stats['performance_trend'] = 'improving'
        else:
            self.stats['performance_trend'] = 'stable'
        
        return False
    
    async def _perform_dynamic_adjustment(self, cpu_percent: float, memory_percent: float, 
                                        queue_depths: dict):
        """执行动态调整"""
        try:
            adjustment_actions = []
            
            # 🚀 根据系统状态决定调整策略
            if cpu_percent > self.cpu_high_threshold or memory_percent > self.memory_high_threshold:
                # 系统资源紧张，减少工作线程
                adjustment_actions.extend(await self._scale_down_resources(
                    cpu_percent, memory_percent, queue_depths
                ))
            
            elif cpu_percent < self.cpu_low_threshold and queue_depths['total_depth'] > self.queue_depth_threshold:
                # CPU空闲但有积压，增加工作线程
                adjustment_actions.extend(await self._scale_up_resources(
                    cpu_percent, memory_percent, queue_depths
                ))
            
            elif queue_depths['total_depth'] > self.queue_depth_threshold * 2:
                # 严重积压，优化队列处理
                adjustment_actions.extend(await self._optimize_queue_processing(queue_depths))
            
            # 记录调整
            if adjustment_actions:
                self.stats['adjustments_made'] += 1
                self.stats['last_adjustment_time'] = time.time()
                
                logger.info(f"🎯 动态资源调整完成: {', '.join(adjustment_actions)}")
                logger.info(f"📊 当前状态 - CPU: {cpu_percent:.1f}%, 内存: {memory_percent:.1f}%, "
                           f"队列深度: {queue_depths['total_depth']}")
        
        except Exception as e:
            logger.error(f"❌ 动态调整执行失败: {e}")
    
    async def _scale_down_resources(self, cpu_percent: float, memory_percent: float, 
                                  queue_depths: dict) -> List[str]:
        """缩减资源使用"""
        actions = []
        
        try:
            # 调整传统优化器批次大小
            if hasattr(optimizer, 'batch_size') and optimizer.batch_size > 50:
                old_batch_size = optimizer.batch_size
                optimizer.batch_size = max(50, int(optimizer.batch_size * 0.8))
                actions.append(f"批次大小: {old_batch_size} → {optimizer.batch_size}")
            
            # 调整异步处理器配置（如果支持）
            if async_processor and async_processor.running:
                # 这里可以添加动态调整异步工作者数量的逻辑
                # 由于asyncio.create_task的限制，我们记录建议调整
                actions.append("建议重启时减少异步工作者数量")
            
        except Exception as e:
            logger.error(f"❌ 缩减资源失败: {e}")
        
        return actions
    
    async def _scale_up_resources(self, cpu_percent: float, memory_percent: float, 
                                queue_depths: dict) -> List[str]:
        """扩展资源使用"""
        actions = []
        
        try:
            # 增加传统优化器批次大小
            if hasattr(optimizer, 'batch_size') and optimizer.batch_size < 500:
                old_batch_size = optimizer.batch_size
                optimizer.batch_size = min(500, int(optimizer.batch_size * 1.2))
                actions.append(f"批次大小: {old_batch_size} → {optimizer.batch_size}")
            
            # 调整线程池（如果可能）
            if hasattr(optimizer, 'executor') and hasattr(optimizer.executor, '_max_workers'):
                current_workers = optimizer.executor._max_workers
                if current_workers < psutil.cpu_count() * 2:
                    actions.append(f"建议增加工作线程: {current_workers} → {current_workers + 2}")
        
        except Exception as e:
            logger.error(f"❌ 扩展资源失败: {e}")
        
        return actions
    
    async def _optimize_queue_processing(self, queue_depths: dict) -> List[str]:
        """优化队列处理"""
        actions = []
        
        try:
            # 临时降低批次超时时间以加快处理
            if hasattr(optimizer, 'batch_timeout') and optimizer.batch_timeout > 1.0:
                old_timeout = optimizer.batch_timeout
                optimizer.batch_timeout = max(1.0, optimizer.batch_timeout * 0.8)
                actions.append(f"批次超时: {old_timeout}s → {optimizer.batch_timeout}s")
            
            # 队列积压严重时的紧急处理
            if queue_depths['total_depth'] > self.queue_depth_threshold * 3:
                actions.append("启动紧急队列处理模式")
                # 这里可以添加更多紧急处理逻辑
        
        except Exception as e:
            logger.error(f"❌ 队列优化失败: {e}")
        
        return actions
    
    def get_resource_stats(self) -> dict:
        """获取资源管理统计信息"""
        current_metrics = {}
        
        try:
            # 当前系统状态
            current_metrics = {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'queue_depths': self._get_queue_depths()
            }
        except Exception:
            pass
        
        return {
            'config': {
                'monitoring_interval': self.monitoring_interval,
                'cpu_high_threshold': self.cpu_high_threshold,
                'memory_high_threshold': self.memory_high_threshold,
                'queue_depth_threshold': self.queue_depth_threshold
            },
            'runtime': {
                'running': self.running,
                'adjustments_made': self.stats['adjustments_made'],
                'performance_trend': self.stats['performance_trend']
            },
            'current_metrics': current_metrics,
            'historical_data': {
                'cpu_readings_count': len(self.stats['cpu_readings']),
                'memory_readings_count': len(self.stats['memory_readings']),
                'queue_depth_readings_count': len(self.stats['queue_depth_readings'])
            }
        }

# 全局资源管理器实例
resource_manager = DynamicResourceManager()

async def initialize_async_system():
    """初始化异步处理系统"""
    global async_processor, resource_manager
    
    try:
        # 启动异步处理器
        if async_processor is None:
            async_processor = await get_async_processor()
        
        # 启动动态资源管理
        await resource_manager.start_monitoring()
        
        logger.info("🚀 异步健康数据处理系统初始化完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 异步系统初始化失败: {e}")
        return False

async def shutdown_async_system():
    """关闭异步处理系统"""
    global async_processor, resource_manager
    
    try:
        # 停止资源管理
        await resource_manager.stop_monitoring()
        
        # 停止异步处理器
        if async_processor:
            await async_processor.stop()
        
        logger.info("🛑 异步健康数据处理系统已关闭")
        
    except Exception as e:
        logger.error(f"❌ 异步系统关闭失败: {e}")

def parse_sleep_data_optimized(sleep_data_json) -> Optional[float]:
    """优化的睡眠数据解析函数 - 同步版本兼容接口"""
    try:
        # 如果在异步环境中，使用异步解析
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 在异步环境中，创建任务但不等待
            task = asyncio.create_task(sleep_parser.parse_sleep_data_async(sleep_data_json))
            # 注：这里可能需要调整以适应不同的使用场景
            return None  # 异步处理，立即返回
        else:
            # 在同步环境中，直接使用原始函数
            return parse_sleep_data(sleep_data_json)
    except RuntimeError:
        # 没有事件循环，使用同步版本
        return parse_sleep_data(sleep_data_json)

# 向后兼容：增强原始parse_sleep_data函数
def parse_sleep_data_enhanced(sleep_data_json) -> Optional[float]:
    """增强版睡眠数据解析 - 提升原有函数性能"""
    if not sleep_data_json or sleep_data_json in ['null', None]:
        return None
    
    try:
        # 缓存机制：对于相同的输入返回缓存结果
        data_hash = hash(str(sleep_data_json)) if isinstance(sleep_data_json, (str, dict)) else None
        
        if isinstance(sleep_data_json, str):
            # 预处理JSON字符串，修复常见格式错误
            sleep_data_json = sleep_data_json.strip()
            if sleep_data_json.startswith('"') and sleep_data_json.endswith('"'):
                sleep_data_json = sleep_data_json[1:-1]  # 移除外层引号
            
            # 修复JSON格式错误
            sleep_data_json = sleep_data_json.replace('"0"data"', '"0","data"')
            sleep_data_json = sleep_data_json.replace('""', '"')  # 修复双引号问题
            
            try:
                sleep_data = json.loads(sleep_data_json)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON解析失败，尝试修复: {e}")
                # 尝试更多修复方法
                sleep_data_json = sleep_data_json.replace("'", '"')  # 单引号转双引号
                sleep_data = json.loads(sleep_data_json)
        elif isinstance(sleep_data_json, dict):
            sleep_data = sleep_data_json
        else:
            return None
            
        # 快速验证
        if not isinstance(sleep_data, dict):
            return None
            
        code = sleep_data.get('code')
        if code == -1 or str(code) == '-1':
            return None
            
        data_list = sleep_data.get('data', [])
        if not isinstance(data_list, list) or len(data_list) == 0:
            return None
            
        # 优化的时间计算
        total_sleep_seconds = 0
        
        for sleep_period in data_list:
            if not isinstance(sleep_period, dict):
                continue
                
            start_time = sleep_period.get('startTimeStamp')
            end_time = sleep_period.get('endTimeStamp')
            
            if start_time is None or end_time is None:
                continue
                
            try:
                # 优化的时间戳处理
                start_seconds = int(start_time)
                end_seconds = int(end_time)
                
                # 毫秒转秒（一次性判断）
                if start_seconds > 9999999999:
                    start_seconds //= 1000
                if end_seconds > 9999999999:
                    end_seconds //= 1000
                
                # 计算时间差
                if end_seconds > start_seconds:
                    total_sleep_seconds += (end_seconds - start_seconds)
                    
            except (ValueError, TypeError):
                continue
                
        # 转换为小时
        if total_sleep_seconds > 0:
            total_sleep_hours = round(total_sleep_seconds / 3600, 2)
            return total_sleep_hours
        else:
            return None
            
    except Exception as e:
        logger.error(f"增强版睡眠数据解析失败: {e}, 数据: {sleep_data_json}")
        return None

def get_optimizer_stats():#获取优化器统计
    """获取优化器运行统计信息"""
    return jsonify(optimizer.get_stats())

def get_async_system_stats():
    """获取完整异步系统统计信息"""
    try:
        stats = {
            "timestamp": datetime.now().isoformat(),
            "system_overview": {
                "version": "AsyncHealthDataProcessor v2.0",
                "status": "运行中" if async_processor and async_processor.running else "未运行",
                "cpu_cores": psutil.cpu_count(logical=True),
                "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 1)
            },
            "processors": {}
        }
        
        # 传统优化器统计
        stats["processors"]["health_optimizer"] = {
            "name": "HealthDataOptimizer",
            "version": "4.0",
            **optimizer.get_stats()
        }
        
        # 异步处理器统计
        if async_processor:
            stats["processors"]["async_processor"] = {
                "name": "AsyncHealthDataProcessor", 
                "version": "2.0",
                **async_processor.get_async_stats()
            }
        
        # 睡眠解析器统计
        if sleep_parser:
            stats["processors"]["sleep_parser"] = {
                "name": "AsyncSleepDataParser",
                "version": "1.0",
                **sleep_parser.get_parser_stats()
            }
        
        # 告警处理器统计
        if alert_processor:
            stats["processors"]["alert_processor"] = {
                "name": "AsyncAlertProcessor",
                "version": "1.0", 
                **alert_processor.get_alert_stats()
            }
        
        # 聚合处理器统计
        if aggregation_processor:
            stats["processors"]["aggregation_processor"] = {
                "name": "AsyncAggregationProcessor",
                "version": "1.0",
                **aggregation_processor.get_aggregation_stats()
            }
        
        # 资源管理器统计
        if resource_manager:
            stats["processors"]["resource_manager"] = {
                "name": "DynamicResourceManager",
                "version": "1.0",
                **resource_manager.get_resource_stats()
            }
        
        # 性能总结
        total_processed = 0
        total_errors = 0
        
        for processor_name, processor_stats in stats["processors"].items():
            performance = processor_stats.get("performance", {})
            if "processed" in performance:
                total_processed += performance["processed"]
            elif "alerts_processed" in performance:
                total_processed += performance["alerts_processed"] 
            elif "daily_processed" in performance:
                total_processed += performance["daily_processed"]
            elif "parsed_total" in performance:
                total_processed += performance["parsed_total"]
            
            # 累计错误
            if "errors" in performance:
                total_errors += performance["errors"]
            elif "processing_errors" in performance:
                total_errors += performance["processing_errors"]
            elif "parse_errors" in performance:
                total_errors += performance["parse_errors"]
        
        stats["performance_summary"] = {
            "total_processed": total_processed,
            "total_errors": total_errors,
            "overall_success_rate": round((total_processed - total_errors) / max(1, total_processed) * 100, 2),
            "system_efficiency": "高效" if total_errors < total_processed * 0.01 else "正常" if total_errors < total_processed * 0.05 else "需优化"
        }
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"❌ 获取异步系统统计失败: {e}")
        return jsonify({"error": str(e), "timestamp": datetime.now().isoformat()})

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
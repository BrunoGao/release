#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""健康画像管理模块 - 集成到bigscreen服务"""
import json,logging,traceback,uuid,time
from datetime import datetime,timedelta
import mysql.connector,threading
from statistics import mean,stdev
from concurrent.futures import ThreadPoolExecutor,as_completed
from flask import request,jsonify
from .models import db
from sqlalchemy import text

logging.basicConfig(level=logging.INFO,format='%(asctime)s [%(levelname)s] %(message)s')
logger=logging.getLogger(__name__)

class HealthProfileService:
    def __init__(self,db_config=None): # 初始化数据库连接
        self.db_config=db_config or self._get_default_db_config()
        self.indicator_weights={'heartrate':0.3,'temperature':0.25,'blood_pressure':0.25,'sleep_duration':0.2} # 指标权重
        
    def _get_default_db_config(self): # 获取默认数据库配置
        from config import SQLALCHEMY_DATABASE_URI
        import re
        match=re.match(r'mysql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)',SQLALCHEMY_DATABASE_URI)
        if match:
            return {'user':match.group(1),'password':match.group(2),'host':match.group(3),'port':int(match.group(4)),'database':match.group(5)}
        return {'host':'localhost','port':3306,'user':'root','password':'123456','database':'ljwx'}
        
    def get_db_connection(self): # 获取数据库连接
        return mysql.connector.connect(**self.db_config,autocommit=True)
        
    def get_all_health_data_optimized(self,customer_id,user_id=None,days=30): # 获取健康数据
        """复用现有get_all_health_data_optimized接口"""
        try:
            with self.get_db_connection() as conn:
                cursor=conn.cursor(dictionary=True)
                where_clause="customer_id=%s AND DATE(create_time)>=DATE_SUB(CURDATE(),INTERVAL %s DAY)"
                params=[customer_id,days]
                if user_id:where_clause+=" AND user_id=%s";params.append(user_id)
                
                cursor.execute(f"SELECT user_id,heartrate,temperature,blood_pressure,sleep_duration,create_time FROM t_user_health_data WHERE {where_clause} ORDER BY create_time DESC",params)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"获取健康数据失败: {str(e)}")
            return []
    
    def calculate_baseline(self,data,indicator_type): # 计算健康基线
        """计算指标基线(均值±2倍标准差)"""
        if not data:return None
        values=[d[indicator_type] for d in data if d.get(indicator_type) and d[indicator_type]>0]
        if len(values)<3:return None
        
        avg_val=mean(values)
        std_val=stdev(values) if len(values)>1 else 0
        return {
            'min':round(avg_val-2*std_val,2),
            'max':round(avg_val+2*std_val,2),
            'avg':round(avg_val,2),
            'std':round(std_val,2),
            'count':len(values),
            'confidence':min(95.0,len(values)/30*100)
        }
    
    def calculate_score(self,current_value,baseline,indicator_type): # 计算健康评分
        """基于基线偏离程度计算评分(0-100)"""
        if not baseline or not current_value:return {'score':50,'level':'unknown','deviation':'unknown'}
        
        min_val,max_val,avg_val=baseline['min'],baseline['max'],baseline['avg']
        
        if min_val<=current_value<=max_val: # 正常范围
            score=95-abs(current_value-avg_val)/avg_val*10 if avg_val>0 else 95
            return {'score':min(100,max(80,score)),'level':'normal','deviation':'normal'}
        
        # 计算偏离程度
        if current_value<min_val:
            deviation_ratio=(min_val-current_value)/avg_val if avg_val>0 else 1
        else:
            deviation_ratio=(current_value-max_val)/avg_val if avg_val>0 else 1
            
        if deviation_ratio<=0.1:level,score='mild',70
        elif deviation_ratio<=0.25:level,score='moderate',50
        else:level,score='severe',20
        
        return {'score':max(0,score),'level':level,'deviation':f'{deviation_ratio:.1%}'}
    
    def generate_personal_baseline(self,customer_id,user_id): # 生成个人基线
        """生成个人基线"""
        health_data=self.get_all_health_data_optimized(customer_id,user_id,30)
        baselines={}
        
        for indicator in self.indicator_weights.keys():
            baseline=self.calculate_baseline(health_data,indicator)
            if baseline:baselines[indicator]=baseline
                
        return baselines
    
    def save_baseline(self,user_id,customer_id,org_id,baseline_type,baselines): # 保存基线数据
        """保存基线到t_health_data_baseline表"""
        with self.get_db_connection() as conn:
            cursor=conn.cursor()
            for indicator,data in baselines.items():
                cursor.execute("""
                    INSERT INTO t_health_data_baseline 
                    (user_id,customer_id,org_id,baseline_type,indicator_type,baseline_min,baseline_max,baseline_avg,std_deviation,sample_count,confidence_level,last_calculated)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON DUPLICATE KEY UPDATE
                    baseline_min=%s,baseline_max=%s,baseline_avg=%s,std_deviation=%s,sample_count=%s,confidence_level=%s,last_calculated=%s
                """,(user_id,customer_id,org_id,baseline_type,indicator,data['min'],data['max'],data['avg'],data['std'],data['count'],data['confidence'],datetime.now(),
                     data['min'],data['max'],data['avg'],data['std'],data['count'],data['confidence'],datetime.now()))
    
    def calculate_health_scores(self,customer_id,user_id,baselines): # 计算健康评分
        """计算用户健康评分"""
        recent_data=self.get_all_health_data_optimized(customer_id,user_id,7) # 最近7天数据
        if not recent_data:return {}
        
        latest_data=recent_data[0] # 最新数据
        scores={}
        total_weighted_score=0
        total_weight=0
        
        for indicator,weight in self.indicator_weights.items():
            if indicator in baselines and indicator in latest_data:
                score_info=self.calculate_score(latest_data[indicator],baselines[indicator],indicator)
                score_info['weight']=weight
                score_info['weighted_score']=score_info['score']*weight
                scores[indicator]=score_info
                total_weighted_score+=score_info['weighted_score']
                total_weight+=weight
        
        overall_score=total_weighted_score/total_weight if total_weight>0 else 50
        return {'indicators':scores,'overall_score':round(overall_score,2)}
    
    def save_scores(self,user_id,customer_id,org_id,score_type,scores): # 保存评分数据
        """保存评分到t_health_data_score表"""
        with self.get_db_connection() as conn:
            cursor=conn.cursor()
            for indicator,data in scores['indicators'].items():
                cursor.execute("""
                    INSERT INTO t_health_data_score
                    (user_id,customer_id,org_id,score_type,indicator_type,indicator_score,indicator_weight,weighted_score,deviation_level,risk_level,score_detail,calculated_time,data_range_start,data_range_end)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON DUPLICATE KEY UPDATE
                    indicator_score=%s,weighted_score=%s,deviation_level=%s,risk_level=%s,score_detail=%s,calculated_time=%s
                """,(user_id,customer_id,org_id,score_type,indicator,data['score'],data['weight'],data['weighted_score'],data['level'],
                     'high' if data['score']<60 else 'medium' if data['score']<80 else 'low',json.dumps(data),datetime.now(),
                     datetime.now()-timedelta(days=7),datetime.now(),
                     data['score'],data['weighted_score'],data['level'],'high' if data['score']<60 else 'medium' if data['score']<80 else 'low',json.dumps(data),datetime.now()))
    
    def generate_health_profile(self,customer_id,user_id): # 生成用户健康画像
        """生成单个用户健康画像"""
        try:
            # 1.生成个人基线
            personal_baselines=self.generate_personal_baseline(customer_id,user_id)
            
            # 2.获取部门信息
            with self.get_db_connection() as conn:
                cursor=conn.cursor(dictionary=True)
                cursor.execute("SELECT org_id FROM t_user WHERE user_id=%s AND customer_id=%s",(user_id,customer_id))
                result=cursor.fetchone()
                org_id=result['org_id'] if result else None
            
            # 3.保存个人基线
            if personal_baselines:
                self.save_baseline(user_id,customer_id,org_id,'personal',personal_baselines)
            
            # 4.计算健康评分
            scores=self.calculate_health_scores(customer_id,user_id,personal_baselines)
            if scores:
                self.save_scores(user_id,customer_id,org_id,'personal',scores)
            
            # 5.生成健康画像
            overall_score=scores.get('overall_score',50)
            health_level='优秀' if overall_score>=90 else '良好' if overall_score>=75 else '一般' if overall_score>=60 else '差'
            deviation_count=sum(1 for s in scores.get('indicators',{}).values() if s.get('level')!='normal')
            risk_indicators=[k for k,v in scores.get('indicators',{}).items() if v.get('level') in ['moderate','severe']]
            
            # 6.保存健康画像
            with self.get_db_connection() as conn:
                cursor=conn.cursor()
                cursor.execute("""
                    INSERT INTO t_health_profile
                    (user_id,customer_id,org_id,health_score,health_level,baseline_deviation_count,risk_indicators,profile_data,generated_time,data_range_start,data_range_end)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON DUPLICATE KEY UPDATE
                    health_score=%s,health_level=%s,baseline_deviation_count=%s,risk_indicators=%s,profile_data=%s,generated_time=%s
                """,(user_id,customer_id,org_id,overall_score,health_level,deviation_count,json.dumps(risk_indicators),json.dumps(scores),datetime.now(),datetime.now()-timedelta(days=30),datetime.now(),
                     overall_score,health_level,deviation_count,json.dumps(risk_indicators),json.dumps(scores),datetime.now()))
            
            return {'success':True,'score':overall_score,'level':health_level}
            
        except Exception as e:
            logger.error(f"生成用户{user_id}健康画像失败: {str(e)}")
            return {'success':False,'error':str(e)}
    
    def batch_generate_profiles(self,customer_id,user_ids=None,task_id=None,operator_id=None): # 批量生成健康画像
        """批量生成健康画像"""
        task_id=task_id or str(uuid.uuid4())
        start_time=datetime.now()
        
        # 获取目标用户列表
        if not user_ids:
            with self.get_db_connection() as conn:
                cursor=conn.cursor(dictionary=True)
                cursor.execute("SELECT user_id FROM t_user WHERE customer_id=%s AND status=1",(customer_id,))
                user_ids=[r['user_id'] for r in cursor.fetchall()]
        
        total_users=len(user_ids)
        success_count=0
        failed_users=[]
        
        # 记录任务开始
        self.log_task(task_id,'manual' if operator_id else 'scheduled',customer_id,'user',user_ids,total_users,0,0,[],'running',None,start_time,None,operator_id)
        
        # 并行处理用户
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures={executor.submit(self.generate_health_profile,customer_id,uid):uid for uid in user_ids}
            
            for future in as_completed(futures):
                user_id=futures[future]
                try:
                    result=future.result()
                    if result.get('success'):success_count+=1
                    else:failed_users.append({'user_id':user_id,'error':result.get('error','未知错误')})
                except Exception as e:
                    failed_users.append({'user_id':user_id,'error':str(e)})
        
        end_time=datetime.now()
        duration_ms=int((end_time-start_time).total_seconds()*1000)
        status='success' if failed_users==[] else 'partial' if success_count>0 else 'failed'
        
        # 更新任务状态
        self.log_task(task_id,'manual' if operator_id else 'scheduled',customer_id,'user',user_ids,total_users,success_count,len(failed_users),failed_users,status,None,start_time,end_time,operator_id,duration_ms)
        
        logger.info(f"批量生成画像完成: 总数{total_users}, 成功{success_count}, 失败{len(failed_users)}, 耗时{duration_ms}ms")
        return {'task_id':task_id,'total':total_users,'success':success_count,'failed':len(failed_users),'duration_ms':duration_ms}
    
    def log_task(self,task_id,task_type,customer_id,target_type,target_ids,total_users,success_count,failed_count,failed_users,status,error_message,start_time,end_time=None,operator_id=None,duration_ms=None): # 记录任务日志
        """记录任务执行日志"""
        with self.get_db_connection() as conn:
            cursor=conn.cursor()
            cursor.execute("""
                INSERT INTO t_health_profile_task_log
                (task_id,task_type,customer_id,target_type,target_ids,total_users,success_count,failed_count,failed_users,start_time,end_time,duration_ms,status,error_message,operator_id)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE
                total_users=%s,success_count=%s,failed_count=%s,failed_users=%s,end_time=%s,duration_ms=%s,status=%s,error_message=%s
            """,(task_id,task_type,customer_id,target_type,json.dumps(target_ids) if target_ids else None,total_users,success_count,failed_count,json.dumps(failed_users) if failed_users else None,start_time,end_time,duration_ms,status,error_message,operator_id,
                 total_users,success_count,failed_count,json.dumps(failed_users) if failed_users else None,end_time,duration_ms,status,error_message))

# 全局服务实例
health_profile_service=HealthProfileService()

def get_profile_monitor(customer_id=1): # 获取画像生成监控信息
    """获取用户画像生命周期监控数据"""
    try:
        with health_profile_service.get_db_connection() as conn:
            cursor=conn.cursor(dictionary=True)
            
            # 获取最近一次任务执行情况
            cursor.execute("""
                SELECT task_id,task_type,total_users,success_count,failed_count,start_time,end_time,duration_ms,status,failed_users
                FROM t_health_profile_task_log 
                WHERE customer_id=%s AND status IN ('success','failed','partial')
                ORDER BY start_time DESC LIMIT 1
            """,(customer_id,))
            last_task=cursor.fetchone()
            
            # 获取当前有效用户总数
            cursor.execute("SELECT COUNT(*) as total FROM t_user WHERE customer_id=%s AND status=1",(customer_id,))
            total_users=cursor.fetchone()['total']
            
            # 获取当前运行中的任务
            cursor.execute("""
                SELECT task_id,start_time,total_users 
                FROM t_health_profile_task_log 
                WHERE customer_id=%s AND status='running'
                ORDER BY start_time DESC LIMIT 1
            """,(customer_id,))
            running_task=cursor.fetchone()
            
            # 构建监控数据
            monitor_data={
                'last_execution_time':last_task['end_time'].strftime('%Y-%m-%d %H:%M:%S') if last_task and last_task['end_time'] else '未执行',
                'total_users':total_users,
                'success_count':last_task['success_count'] if last_task else 0,
                'failed_count':last_task['failed_count'] if last_task else 0,
                'failed_details':json.loads(last_task['failed_users']) if last_task and last_task['failed_users'] else [],
                'duration_ms':last_task['duration_ms'] if last_task else 0,
                'next_execution_time':'每天 01:00',
                'current_status':'正常' if not running_task else '执行中' if last_task and last_task['status']=='success' else '异常',
                'running_task':running_task
            }
            
        return {'code':200,'data':monitor_data,'message':'获取成功'}
        
    except Exception as e:
        logger.error(f"获取监控数据失败: {str(e)}")
        return {'code':500,'message':f'获取失败: {str(e)}'}

def manual_generate_profiles(customer_id=1,user_ids=None,org_id=None,operator_id=1): # 手动生成健康画像
    """手动生成用户健康画像"""
    try:
        # 如果指定了部门ID，获取部门下所有用户
        if org_id and not user_ids:
            with health_profile_service.get_db_connection() as conn:
                cursor=conn.cursor(dictionary=True)
                cursor.execute("SELECT user_id FROM t_user WHERE customer_id=%s AND org_id=%s AND status=1",(customer_id,org_id))
                user_ids=[r['user_id'] for r in cursor.fetchall()]
        
        if not user_ids:
            return {'code':400,'message':'未指定目标用户或部门'}
        
        # 执行批量生成
        result=health_profile_service.batch_generate_profiles(customer_id,user_ids,operator_id=operator_id)
        
        return {
            'code':200,
            'data':{
                'task_id':result['task_id'],
                'total_users':result['total'],
                'success_count':result['success'],
                'failed_count':result['failed'],
                'duration_ms':result['duration_ms']
            },
            'message':'画像生成完成'
        }
        
    except Exception as e:
        logger.error(f"手动生成画像失败: {str(e)}")
        return {'code':500,'message':f'生成失败: {str(e)}'}

def get_health_profiles(customer_id=1,org_id=None,user_name='',health_level='',page=1,size=20): # 获取健康画像列表
    """获取健康画像展示列表"""
    try:
        with health_profile_service.get_db_connection() as conn:
            cursor=conn.cursor(dictionary=True)
            
            # 构建查询条件
            where_conditions=["p.customer_id=%s","p.status=1"]
            params=[customer_id]
            
            if org_id:where_conditions.append("u.org_id=%s");params.append(org_id)
            if user_name:where_conditions.append("u.real_name LIKE %s");params.append(f'%{user_name}%')
            if health_level:where_conditions.append("p.health_level=%s");params.append(health_level)
            
            where_clause=" AND ".join(where_conditions)
            
            # 获取总数
            cursor.execute(f"""
                SELECT COUNT(*) as total 
                FROM t_health_profile p 
                LEFT JOIN t_user u ON p.user_id=u.user_id AND p.customer_id=u.customer_id 
                WHERE {where_clause}
            """,params)
            total=cursor.fetchone()['total']
            
            # 获取分页数据
            offset=(page-1)*size
            cursor.execute(f"""
                SELECT p.*,u.real_name,u.avatar,o.org_name,
                       (SELECT COUNT(*) FROM t_user_health_data h WHERE h.user_id=p.user_id AND h.customer_id=p.customer_id AND DATE(h.create_time)=CURDATE()) as today_data_count
                FROM t_health_profile p
                LEFT JOIN t_user u ON p.user_id=u.user_id AND p.customer_id=u.customer_id
                LEFT JOIN t_org o ON u.org_id=o.org_id AND u.customer_id=o.customer_id
                WHERE {where_clause}
                ORDER BY p.generated_time DESC
                LIMIT %s OFFSET %s
            """,params+[size,offset])
            
            profiles=cursor.fetchall()
            
            # 处理JSON字段
            for profile in profiles:
                if profile['profile_data']:
                    profile['profile_data']=json.loads(profile['profile_data'])
                if profile['risk_indicators']:
                    profile['risk_indicators']=json.loads(profile['risk_indicators'])
                # 格式化时间
                if profile['generated_time']:
                    profile['generated_time']=profile['generated_time'].strftime('%Y-%m-%d %H:%M:%S')
            
        return {
            'code':200,
            'data':{
                'profiles':profiles,
                'total':total,
                'page':page,
                'size':size,
                'pages':(total+size-1)//size
            },
            'message':'获取成功'
        }
        
    except Exception as e:
        logger.error(f"获取画像列表失败: {str(e)}")
        return {'code':500,'message':f'获取失败: {str(e)}'}

def get_profile_statistics(customer_id=1,org_id=None): # 获取画像统计数据
    """获取健康画像统计数据(用于大屏展示)"""
    try:
        with health_profile_service.get_db_connection() as conn:
            cursor=conn.cursor(dictionary=True)
            
            where_condition="customer_id=%s AND status=1"
            params=[customer_id]
            if org_id:where_condition+=" AND org_id=%s";params.append(org_id)
            
            # 健康等级分布
            cursor.execute(f"""
                SELECT health_level,COUNT(*) as count 
                FROM t_health_profile 
                WHERE {where_condition}
                GROUP BY health_level
            """,params)
            level_distribution=cursor.fetchall()
            
            # 平均健康评分
            cursor.execute(f"SELECT AVG(health_score) as avg_score FROM t_health_profile WHERE {where_condition}",params)
            avg_score=round(cursor.fetchone()['avg_score'] or 0,2)
            
            # 风险用户数量
            cursor.execute(f"SELECT COUNT(*) as risk_count FROM t_health_profile WHERE {where_condition} AND health_level IN ('一般','差')",params)
            risk_count=cursor.fetchone()['risk_count']
            
            # 基线偏离情况
            cursor.execute(f"""
                SELECT 
                    SUM(CASE WHEN baseline_deviation_count=0 THEN 1 ELSE 0 END) as normal_count,
                    SUM(CASE WHEN baseline_deviation_count BETWEEN 1 AND 2 THEN 1 ELSE 0 END) as mild_count,
                    SUM(CASE WHEN baseline_deviation_count>=3 THEN 1 ELSE 0 END) as severe_count
                FROM t_health_profile WHERE {where_condition}
            """,params)
            deviation_stats=cursor.fetchone()
            
        return {
            'code':200,
            'data':{
                'level_distribution':level_distribution,
                'avg_score':avg_score,
                'risk_count':risk_count,
                'deviation_stats':deviation_stats
            },
            'message':'获取成功'
        }
        
    except Exception as e:
        logger.error(f"获取统计数据失败: {str(e)}")
        return {'code':500,'message':f'获取失败: {str(e)}'}

# 定时任务线程类
class HealthProfileScheduler:
    def __init__(self): # 初始化
        self.is_running=False
        self.thread=None
        
    def run_scheduled_task(self): # 运行定时任务
        """定时任务：每天凌晨1点生成健康画像"""
        while self.is_running:
            now=datetime.now()
            # 检查是否为凌晨1点
            if now.hour==1 and now.minute==0:
                logger.info("开始执行定时健康画像生成任务")
                try:
                    # 获取所有客户
                    with health_profile_service.get_db_connection() as conn:
                        cursor=conn.cursor(dictionary=True)
                        cursor.execute("SELECT DISTINCT customer_id FROM t_user WHERE status=1")
                        customer_ids=[r['customer_id'] for r in cursor.fetchall()]
                    
                    for customer_id in customer_ids:
                        result=health_profile_service.batch_generate_profiles(customer_id)
                        logger.info(f"客户{customer_id}画像生成完成: {result}")
                        
                except Exception as e:
                    logger.error(f"定时画像生成失败: {str(e)}")
                
                # 等待1小时，避免重复执行
                time.sleep(3600)
            else:
                time.sleep(60) # 每分钟检查一次
    
    def start(self): # 启动调度器
        """启动定时任务调度器"""
        if not self.is_running:
            self.is_running=True
            self.thread=threading.Thread(target=self.run_scheduled_task,daemon=True)
            self.thread.start()
            logger.info("健康画像定时任务已启动")
    
    def stop(self): # 停止调度器
        """停止定时任务调度器"""
        self.is_running=False
        if self.thread:
            self.thread.join()
        logger.info("健康画像定时任务已停止")

# 全局调度器实例 - 已禁用自动启动
scheduler=HealthProfileScheduler()
# scheduler.start() # 自动启动定时任务 - 已禁用 
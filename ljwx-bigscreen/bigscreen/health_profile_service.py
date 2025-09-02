#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""健康画像生成服务 - 专业级实现"""
import json,logging,traceback,uuid,time
from datetime import datetime,timedelta
import mysql.connector,schedule
from statistics import mean,stdev
from concurrent.futures import ThreadPoolExecutor,as_completed

logging.basicConfig(level=logging.INFO,format='%(asctime)s [%(levelname)s] %(message)s')
logger=logging.getLogger(__name__)

class HealthProfileService:
    def __init__(self,db_config): # 初始化数据库连接
        self.db_config=db_config
        self.indicator_weights={'heartrate':0.3,'temperature':0.25,'blood_pressure':0.25,'sleep_quality':0.2} # 指标权重配置
        
    def get_db_connection(self): # 获取数据库连接
        return mysql.connector.connect(**self.db_config,autocommit=True)
        
    def get_all_health_data_optimized(self,customer_id,user_id=None,days=30): # 获取优化后的健康数据
        """获取用户健康数据(复用现有优化接口)"""
        with self.get_db_connection() as conn:
            cursor=conn.cursor(dictionary=True)
            where_clause="customer_id=%s AND DATE(create_time)>=DATE_SUB(CURDATE(),INTERVAL %s DAY)"
            params=[customer_id,days]
            if user_id:where_clause+=" AND user_id=%s";params.append(user_id)
            
            cursor.execute(f"SELECT user_id,heartrate,temperature,blood_pressure,sleep_duration,create_time FROM t_user_health_data WHERE {where_clause} ORDER BY create_time DESC",params)
            return cursor.fetchall()
    
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
            'confidence':min(95.0,len(values)/30*100) # 置信度基于样本量
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
    
    def generate_personal_baseline(self,customer_id,user_id): # 生成个人健康基线
        """生成个人基线"""
        health_data=self.get_all_health_data_optimized(customer_id,user_id,30)
        baselines={}
        
        for indicator in self.indicator_weights.keys():
            if indicator=='blood_pressure':continue # 血压需特殊处理
            baseline=self.calculate_baseline(health_data,indicator)
            if baseline:baselines[indicator]=baseline
                
        return baselines
    
    def generate_department_baseline(self,customer_id,org_id): # 生成部门健康基线
        """生成部门基线"""
        with self.get_db_connection() as conn:
            cursor=conn.cursor(dictionary=True)
            cursor.execute("SELECT user_id FROM t_user WHERE customer_id=%s AND org_id=%s AND status=1",(customer_id,org_id))
            user_ids=[r['user_id'] for r in cursor.fetchall()]
            
        if not user_ids:return {}
        
        all_data=self.get_all_health_data_optimized(customer_id)
        dept_data=[d for d in all_data if d['user_id'] in user_ids]
        
        baselines={}
        for indicator in self.indicator_weights.keys():
            if indicator=='blood_pressure':continue
            baseline=self.calculate_baseline(dept_data,indicator)
            if baseline:baselines[indicator]=baseline
                
        return baselines
    
    def save_baseline(self,user_id,customer_id,org_id,baseline_type,baselines): # 保存基线数据
        """保存基线到数据库"""
        with self.get_db_connection() as conn:
            cursor=conn.cursor()
            for indicator,data in baselines.items():
                cursor.execute("""
                    INSERT INTO t_health_baseline 
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
        """保存评分到数据库"""
        with self.get_db_connection() as conn:
            cursor=conn.cursor()
            for indicator,data in scores['indicators'].items():
                cursor.execute("""
                    INSERT INTO t_health_score
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
        with ThreadPoolExecutor(max_workers=5) as executor:
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

# 定时任务调度器
class HealthProfileScheduler:
    def __init__(self,service,customer_ids=[1]): # 初始化调度器
        self.service=service
        self.customer_ids=customer_ids
        
    def scheduled_generate_all(self): # 定时生成所有客户的健康画像
        """定时任务: 生成所有客户健康画像"""
        logger.info("开始执行定时健康画像生成任务")
        for customer_id in self.customer_ids:
            try:
                result=self.service.batch_generate_profiles(customer_id)
                logger.info(f"客户{customer_id}画像生成完成: {result}")
            except Exception as e:
                logger.error(f"客户{customer_id}画像生成失败: {str(e)}")
        logger.info("定时健康画像生成任务完成")
    
    def start_scheduler(self): # 启动调度器
        """启动定时任务调度器"""
        schedule.every().day.at("01:00").do(self.scheduled_generate_all) # 每天凌晨1点执行
        logger.info("健康画像定时任务已启动 (每天01:00)")
        
        while True:
            schedule.run_pending()
            time.sleep(60) # 每分钟检查一次

# 配置和启动
if __name__=='__main__':
    DB_CONFIG={'host':'localhost','port':3306,'user':'root','password':'123456','database':'ljwx'}
    service=HealthProfileService(DB_CONFIG)
    scheduler=HealthProfileScheduler(service,[1,2,3]) # 支持多客户
    
    # 测试单个用户画像生成
    # result=service.generate_health_profile(1,1)
    # print(f"单用户画像生成结果: {result}")
    
    # 启动定时任务
    try:scheduler.start_scheduler()
    except KeyboardInterrupt:logger.info("定时任务调度器已停止") 
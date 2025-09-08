#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""健康画像生成服务 - 专业级实现"""
import json,logging,traceback,uuid,time
from datetime import datetime,timedelta
import mysql.connector,schedule
from statistics import mean,stdev
from concurrent.futures import ThreadPoolExecutor,as_completed
from .health_cache_manager import health_cache, cache_result

logging.basicConfig(level=logging.INFO,format='%(asctime)s [%(levelname)s] %(message)s')
logger=logging.getLogger(__name__)

class HealthProfileQueryService:
    def __init__(self,db_config): # 初始化数据库连接
        self.db_config=db_config
        self.cache = health_cache
        logger.info("健康画像查询服务初始化完成，已集成Redis缓存策略")
        
    def get_db_connection(self): # 获取数据库连接
        return mysql.connector.connect(**self.db_config,autocommit=True)
        
    def get_all_health_data_optimized(self,org_id,user_id=None,days=30): # 获取优化后的健康数据
        """获取用户健康数据(复用现有优化接口)"""
        with self.get_db_connection() as conn:
            cursor=conn.cursor(dictionary=True)
            where_clause="org_id=%s AND DATE(create_time)>=DATE_SUB(CURDATE(),INTERVAL %s DAY)"
            params=[org_id,days]
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
    
    def query_personal_baseline(self,org_id,user_id): # 查询个人健康基线
        """查询个人基线 - 从 ljwx-boot 获取生成好的基线数据"""
        logger.info(f"查询用户{user_id}的个人基线数据")
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT feature_name, mean_value, std_deviation, baseline_date, sample_count
                    FROM t_health_baseline 
                    WHERE user_id = %s AND customer_id = %s 
                    AND baseline_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                    ORDER BY baseline_date DESC, feature_name
                """, (user_id, org_id))
                
                baselines = cursor.fetchall()
                baseline_dict = {}
                for baseline in baselines:
                    feature = baseline['feature_name']
                    if feature not in baseline_dict:
                        baseline_dict[feature] = []
                    baseline_dict[feature].append(baseline)
                
                return baseline_dict
        except Exception as e:
            logger.error(f"查询个人基线失败: {e}")
            return {}
    
    def query_department_baseline(self,org_id): # 查询部门健康基线
        """查询部门基线 - 从 ljwx-boot 获取生成好的基线数据"""
        logger.info(f"查询组织{org_id}的部门基线数据")
        # TODO: 调用 ljwx-boot 的基线查询 API
        return {}
    
    # 保存功能已禁用 - 由 ljwx-boot 后端处理
    
    def query_health_scores(self,org_id,user_id): # 查询健康评分
        """查询用户健康评分 - 从 ljwx-boot 获取"""
        logger.info(f"查询用户{user_id}的健康评分")
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT feature_name, score_value, z_score, avg_value, score_date
                    FROM t_health_score 
                    WHERE user_id = %s AND org_id = %s 
                    AND score_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                    ORDER BY score_date DESC, feature_name
                """, (user_id, org_id))
                
                scores = cursor.fetchall()
                
                # 计算综合评分
                if scores:
                    latest_scores = {}
                    for score in scores:
                        feature = score['feature_name']
                        if feature not in latest_scores:
                            latest_scores[feature] = score
                    
                    # 计算加权平均分
                    total_score = sum(score['score_value'] for score in latest_scores.values())
                    avg_score = total_score / len(latest_scores) if latest_scores else 0
                    
                    return {
                        'overall_score': round(avg_score, 2),
                        'feature_scores': latest_scores,
                        'score_count': len(latest_scores),
                        'last_update': max(score['score_date'].isoformat() for score in latest_scores.values())
                    }
                else:
                    return {'overall_score': 0, 'feature_scores': {}, 'score_count': 0}
                    
        except Exception as e:
            logger.error(f"查询健康评分失败: {e}")
            return {}
    
    # 保存评分功能已禁用 - 由 ljwx-boot 后端处理
    
    def query_health_profile(self,org_id,user_id): # 查询用户健康画像
        """查询单个用户健康画像 - 集成缓存优化"""
        try:
            # 尝试从缓存获取健康画像
            cached_profile = self.cache.get_health_profile(user_id, org_id)
            if cached_profile:
                logger.info(f"命中健康画像缓存: user_id={user_id}, org_id={org_id}")
                return {'success': True, 'data': cached_profile, 'cached': True}
            
            logger.info(f"查询用户{user_id}的健康画像数据")
            
            with self.get_db_connection() as conn:
                cursor=conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT health_score, health_level, baseline_deviation_count, 
                           risk_indicators, profile_data, generated_time
                    FROM t_health_profile 
                    WHERE user_id=%s AND customer_id=%s
                    ORDER BY generated_time DESC LIMIT 1
                """,(user_id,org_id))
                result=cursor.fetchone()
                
            if result:
                # 缓存查询结果
                profile_data = result
                profile_data['cached'] = False
                profile_data['query_time'] = datetime.now().isoformat()
                
                self.cache.cache_health_profile(user_id, org_id, profile_data)
                logger.info(f"健康画像已缓存: user_id={user_id}")
                
                return {'success':True,'data':profile_data}
            else:
                return {'success':False,'error':'未找到健康画像数据'}
                
        except Exception as e:
            logger.error(f"查询用户{user_id}健康画像失败: {str(e)}")
            return {'success':False,'error':str(e)}
    
    def query_batch_profiles(self,org_id,user_ids=None): # 批量查询健康画像
        """批量查询健康画像 - 集成缓存优化"""
        try:
            # 尝试从缓存获取批量画像数据
            cached_profiles = self.cache.get_health_profile_list(org_id)
            if cached_profiles and not user_ids:
                logger.info(f"命中批量健康画像缓存: org_id={org_id}")
                return {'success': True, 'data': cached_profiles, 'cached': True}
            
            logger.info(f"批量查询组织{org_id}的健康画像数据")
            
            with self.get_db_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                if user_ids:
                    placeholders = ','.join(['%s'] * len(user_ids))
                    cursor.execute(f"""
                        SELECT user_id, health_score, health_level, baseline_deviation_count, 
                               risk_indicators, profile_data, generated_time
                        FROM t_health_profile 
                        WHERE user_id IN ({placeholders}) AND customer_id = %s
                        ORDER BY generated_time DESC
                    """, user_ids + [org_id])
                else:
                    cursor.execute("""
                        SELECT user_id, health_score, health_level, baseline_deviation_count, 
                               risk_indicators, profile_data, generated_time
                        FROM t_health_profile 
                        WHERE customer_id = %s
                        ORDER BY generated_time DESC
                    """, (org_id,))
                
                results = cursor.fetchall()
            
            if results:
                # 处理结果并缓存
                profiles = []
                for result in results:
                    result['cached'] = False
                    result['query_time'] = datetime.now().isoformat()
                    profiles.append(result)
                
                # 如果是查询所有用户，则缓存批量结果
                if not user_ids:
                    self.cache.cache_health_profile_list(org_id, profiles)
                    logger.info(f"批量健康画像已缓存: org_id={org_id}, count={len(profiles)}")
                
                return {'success': True, 'data': profiles, 'count': len(profiles)}
            else:
                return {'success': False, 'error': '未找到健康画像数据', 'data': []}
                
        except Exception as e:
            logger.error(f"批量查询健康画像失败: {str(e)}")
            return {'success': False, 'error': str(e), 'data': []}
    
    def log_task(self,task_id,task_type,org_id,target_type,target_ids,total_users,success_count,failed_count,failed_users,status,error_message,start_time,end_time=None,operator_id=None,duration_ms=None): # 记录任务日志
        """记录任务执行日志"""
        with self.get_db_connection() as conn:
            cursor=conn.cursor()
            cursor.execute("""
                INSERT INTO t_health_profile_task_log
                (task_id,task_type,org_id,target_type,target_ids,total_users,success_count,failed_count,failed_users,start_time,end_time,duration_ms,status,error_message,operator_id)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE
                total_users=%s,success_count=%s,failed_count=%s,failed_users=%s,end_time=%s,duration_ms=%s,status=%s,error_message=%s
            """,(task_id,task_type,org_id,target_type,json.dumps(target_ids) if target_ids else None,total_users,success_count,failed_count,json.dumps(failed_users) if failed_users else None,start_time,end_time,duration_ms,status,error_message,operator_id,
                 total_users,success_count,failed_count,json.dumps(failed_users) if failed_users else None,end_time,duration_ms,status,error_message))

# 定时任务已禁用 - 迁移至 ljwx-boot
class HealthProfileScheduler:
    def __init__(self,service,org_ids=[1]):
        self.service=service
        self.org_ids=org_ids
        logger.warning("健康画像生成定时任务已禁用，请使用ljwx-boot后端")
        
    def scheduled_generate_all(self):
        logger.warning("定时生成任务已禁用，请使用ljwx-boot后端的定时任务")
    
    def start_scheduler(self):
        logger.warning("定时任务调度器已禁用，请使用ljwx-boot后端的定时任务")

# 配置和启动
if __name__=='__main__':
    DB_CONFIG={'host':'localhost','port':3306,'user':'root','password':'123456','database':'ljwx'}
    service=HealthProfileQueryService(DB_CONFIG)
    
    logger.info("健康画像查询服务启动完成，生成功能已迁移至ljwx-boot")
    logger.info("请使用ljwx-boot后端的定时任务进行健康画像生成") 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""健康画像管理API - Flask RESTful接口"""
from flask import Flask,request,jsonify,render_template
import json,logging,mysql.connector
from datetime import datetime,timedelta
from health_profile_service import HealthProfileService

app=Flask(__name__)
app.config['JSON_AS_ASCII']=False # 支持中文JSON
logging.basicConfig(level=logging.INFO)

DB_CONFIG={'host':'localhost','port':3306,'user':'root','password':'123456','database':'ljwx'}
health_service=HealthProfileService(DB_CONFIG)

def get_db_connection(): # 获取数据库连接
    return mysql.connector.connect(**DB_CONFIG,autocommit=True)

@app.route('/health-profile')
def health_profile_page(): # 健康画像管理页面
    """健康画像管理中心主页"""
    return render_template('health_profile_management.html')

@app.route('/api/health-profile/monitor',methods=['GET'])
def get_profile_monitor(): # 获取画像生成监控信息
    """获取用户画像生命周期监控数据"""
    try:
        customer_id=request.args.get('customerId',1,type=int)
        
        with get_db_connection() as conn:
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
                'next_execution_time':'每天 01:00', # 固定时间
                'current_status':'正常' if not running_task else '执行中' if last_task and last_task['status']=='success' else '异常',
                'running_task':running_task
            }
            
        return jsonify({'code':200,'data':monitor_data,'message':'获取成功'})
        
    except Exception as e:
        logging.error(f"获取监控数据失败: {str(e)}")
        return jsonify({'code':500,'message':f'获取失败: {str(e)}'})

@app.route('/api/health-profile/generate',methods=['POST'])
def manual_generate_profiles(): # 手动生成健康画像
    """手动生成用户健康画像"""
    try:
        data=request.get_json()
        customer_id=data.get('customerId',1)
        user_ids=data.get('userIds',[]) # 指定用户ID列表
        org_id=data.get('orgId') # 部门ID(可选)
        operator_id=data.get('operatorId',1) # 操作人ID
        
        # 如果指定了部门ID，获取部门下所有用户
        if org_id and not user_ids:
            with get_db_connection() as conn:
                cursor=conn.cursor(dictionary=True)
                cursor.execute("SELECT user_id FROM t_user WHERE customer_id=%s AND org_id=%s AND status=1",(customer_id,org_id))
                user_ids=[r['user_id'] for r in cursor.fetchall()]
        
        if not user_ids:
            return jsonify({'code':400,'message':'未指定目标用户或部门'})
        
        # 执行批量生成
        result=health_service.batch_generate_profiles(customer_id,user_ids,operator_id=operator_id)
        
        return jsonify({
            'code':200,
            'data':{
                'task_id':result['task_id'],
                'total_users':result['total'],
                'success_count':result['success'],
                'failed_count':result['failed'],
                'duration_ms':result['duration_ms']
            },
            'message':'画像生成完成'
        })
        
    except Exception as e:
        logging.error(f"手动生成画像失败: {str(e)}")
        return jsonify({'code':500,'message':f'生成失败: {str(e)}'})

@app.route('/api/health-profile/list',methods=['GET'])
def get_health_profiles(): # 获取健康画像列表
    """获取健康画像展示列表"""
    try:
        customer_id=request.args.get('customerId',1,type=int)
        org_id=request.args.get('orgId',type=int)
        user_name=request.args.get('userName','')
        health_level=request.args.get('healthLevel','')
        page=request.args.get('page',1,type=int)
        size=request.args.get('size',20,type=int)
        
        with get_db_connection() as conn:
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
            
        return jsonify({
            'code':200,
            'data':{
                'profiles':profiles,
                'total':total,
                'page':page,
                'size':size,
                'pages':(total+size-1)//size
            },
            'message':'获取成功'
        })
        
    except Exception as e:
        logging.error(f"获取画像列表失败: {str(e)}")
        return jsonify({'code':500,'message':f'获取失败: {str(e)}'})

@app.route('/api/health-profile/detail/<int:user_id>',methods=['GET'])
def get_profile_detail(user_id): # 获取用户画像详情
    """获取用户健康画像详情"""
    try:
        customer_id=request.args.get('customerId',1,type=int)
        
        with get_db_connection() as conn:
            cursor=conn.cursor(dictionary=True)
            
            # 获取画像详情
            cursor.execute("""
                SELECT p.*,u.real_name,u.avatar,o.org_name
                FROM t_health_profile p
                LEFT JOIN t_user u ON p.user_id=u.user_id AND p.customer_id=u.customer_id
                LEFT JOIN t_org o ON u.org_id=o.org_id AND u.customer_id=o.customer_id
                WHERE p.user_id=%s AND p.customer_id=%s AND p.status=1
            """,(user_id,customer_id))
            profile=cursor.fetchone()
            
            if not profile:
                return jsonify({'code':404,'message':'用户画像不存在'})
            
            # 获取基线数据
            cursor.execute("""
                SELECT indicator_type,baseline_min,baseline_max,baseline_avg,confidence_level,last_calculated
                FROM t_health_baseline 
                WHERE user_id=%s AND customer_id=%s AND baseline_type='personal' AND status=1
            """,(user_id,customer_id))
            baselines={row['indicator_type']:row for row in cursor.fetchall()}
            
            # 获取评分数据
            cursor.execute("""
                SELECT indicator_type,indicator_score,deviation_level,risk_level,score_detail,calculated_time
                FROM t_health_score
                WHERE user_id=%s AND customer_id=%s AND score_type='personal' AND status=1
            """,(user_id,customer_id))
            scores={row['indicator_type']:row for row in cursor.fetchall()}
            
            # 处理JSON字段
            if profile['profile_data']:profile['profile_data']=json.loads(profile['profile_data'])
            if profile['risk_indicators']:profile['risk_indicators']=json.loads(profile['risk_indicators'])
            
            # 格式化时间
            for key in ['generated_time','data_range_start','data_range_end']:
                if profile[key]:profile[key]=profile[key].strftime('%Y-%m-%d %H:%M:%S')
            
            return jsonify({
                'code':200,
                'data':{
                    'profile':profile,
                    'baselines':baselines,
                    'scores':scores
                },
                'message':'获取成功'
            })
            
    except Exception as e:
        logging.error(f"获取画像详情失败: {str(e)}")
        return jsonify({'code':500,'message':f'获取失败: {str(e)}'})

@app.route('/api/health-profile/task-logs',methods=['GET'])
def get_task_logs(): # 获取任务执行日志
    """获取画像生成任务日志"""
    try:
        customer_id=request.args.get('customerId',1,type=int)
        page=request.args.get('page',1,type=int)
        size=request.args.get('size',10,type=int)
        
        with get_db_connection() as conn:
            cursor=conn.cursor(dictionary=True)
            
            # 获取总数
            cursor.execute("SELECT COUNT(*) as total FROM t_health_profile_task_log WHERE customer_id=%s",(customer_id,))
            total=cursor.fetchone()['total']
            
            # 获取分页日志
            offset=(page-1)*size
            cursor.execute("""
                SELECT task_id,task_type,total_users,success_count,failed_count,start_time,end_time,duration_ms,status,
                       (SELECT real_name FROM t_user u WHERE u.user_id=l.operator_id LIMIT 1) as operator_name
                FROM t_health_profile_task_log l
                WHERE customer_id=%s
                ORDER BY start_time DESC
                LIMIT %s OFFSET %s
            """,(customer_id,size,offset))
            
            logs=cursor.fetchall()
            
            # 格式化时间
            for log in logs:
                if log['start_time']:log['start_time']=log['start_time'].strftime('%Y-%m-%d %H:%M:%S')
                if log['end_time']:log['end_time']=log['end_time'].strftime('%Y-%m-%d %H:%M:%S')
                log['duration_seconds']=round(log['duration_ms']/1000,2) if log['duration_ms'] else 0
            
        return jsonify({
            'code':200,
            'data':{
                'logs':logs,
                'total':total,
                'page':page,
                'size':size
            },
            'message':'获取成功'
        })
        
    except Exception as e:
        logging.error(f"获取任务日志失败: {str(e)}")
        return jsonify({'code':500,'message':f'获取失败: {str(e)}'})

@app.route('/api/health-profile/statistics',methods=['GET'])
def get_profile_statistics(): # 获取画像统计数据
    """获取健康画像统计数据(用于大屏展示)"""
    try:
        customer_id=request.args.get('customerId',1,type=int)
        org_id=request.args.get('orgId',type=int)
        
        with get_db_connection() as conn:
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
            
        return jsonify({
            'code':200,
            'data':{
                'level_distribution':level_distribution,
                'avg_score':avg_score,
                'risk_count':risk_count,
                'deviation_stats':deviation_stats
            },
            'message':'获取成功'
        })
        
    except Exception as e:
        logging.error(f"获取统计数据失败: {str(e)}")
        return jsonify({'code':500,'message':f'获取失败: {str(e)}'})

if __name__=='__main__':
    app.run(host='0.0.0.0',port=5003,debug=True) # 健康画像管理服务端口 
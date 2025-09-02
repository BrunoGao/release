# -*- coding: utf-8 -*-
import sys,os,json,time
sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__),'.')))
from models import *
from cache_config import redis
from user_health_data import get_all_health_data_optimized,get_health_data_config_by_org

def debug_log(msg,force_write=False): #调试日志输出-写入文件#
    try:
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        log_msg=f"[{timestamp}] {msg}\n"
        
        #写入调试日志文件#
        log_file=os.path.join(os.path.dirname(__file__),'debug_health.log')
        with open(log_file,'a',encoding='utf-8') as f:
            f.write(log_msg)
            
        #同时输出到控制台(如果允许)#
        if force_write:
            print(msg)
    except:pass

def test_health_config(org_id): #测试健康数据配置#
    debug_log(f"🔧 测试组织{org_id}的健康数据配置")
    config=get_health_data_config_by_org(org_id)
    debug_log(f"配置结果:{json.dumps(config,ensure_ascii=False)}")
    return config

def test_raw_data_query(org_id,user_id=None,limit=3): #测试原始数据查询#
    debug_log(f"📊 测试原始数据查询 org_id:{org_id} user_id:{user_id}")
    
    try:
        #获取用户设备信息#
        if user_id:
            users=db.session.query(UserInfo,OrgInfo.name.label('dept_name')).join(UserOrg,UserInfo.id==UserOrg.user_id).join(OrgInfo,UserOrg.org_id==OrgInfo.id).filter(UserInfo.id==user_id,UserInfo.is_deleted==False).all()
        else:
            from org import fetch_users_by_orgId
            all_users=fetch_users_by_orgId(org_id)
            debug_log(f"组织用户总数:{len(all_users)}")
            
        #查询原始健康数据#
        if user_id:
            device_sns=[u[0].device_sn for u in users if u[0].device_sn and u[0].device_sn!='-']
        else:
            device_sns=[u['device_sn'] for u in all_users[:5] if u['device_sn'] and u['device_sn']!='-'] #限制5个设备测试#
            
        debug_log(f"测试设备:{device_sns}")
        
        if device_sns:
            #查询最新数据#
            from sqlalchemy import func,text
            subq=db.session.query(UserHealthData.device_sn,func.max(UserHealthData.timestamp).label('max_ts')).filter(UserHealthData.device_sn.in_(device_sns)).group_by(UserHealthData.device_sn).subquery()
            
            latest_data=db.session.query(UserHealthData).join(subq,(UserHealthData.device_sn==subq.c.device_sn)&(UserHealthData.timestamp==subq.c.max_ts)).limit(limit).all()
            
            debug_log(f"查询到{len(latest_data)}条最新数据")
            
            for i,r in enumerate(latest_data):
                debug_log(f"记录{i+1}:")
                debug_log(f"  device_sn:{r.device_sn}")
                debug_log(f"  heart_rate:{getattr(r,'heart_rate',None)} (hasattr:{hasattr(r,'heart_rate')})")
                debug_log(f"  pressure_high:{getattr(r,'pressure_high',None)} (hasattr:{hasattr(r,'pressure_high')})")
                debug_log(f"  pressure_low:{getattr(r,'pressure_low',None)} (hasattr:{hasattr(r,'pressure_low')})")
                debug_log(f"  blood_oxygen:{getattr(r,'blood_oxygen',None)} (hasattr:{hasattr(r,'blood_oxygen')})")
                debug_log(f"  temperature:{getattr(r,'temperature',None)} (hasattr:{hasattr(r,'temperature')})")
                debug_log(f"  timestamp:{r.timestamp}")
                
                #检查数据库字段#
                debug_log(f"  所有属性:{[attr for attr in dir(r) if not attr.startswith('_')]}")
                
        return True
    except Exception as e:
        debug_log(f"❌ 原始数据查询失败:{e}")
        return False

def test_optimized_query(org_id,user_id=None): #测试优化查询接口#
    debug_log(f"🚀 测试优化查询接口 org_id:{org_id} user_id:{user_id}")
    
    try:
        result=get_all_health_data_optimized(orgId=org_id,userId=user_id,latest_only=True)
        
        debug_log(f"查询结果success:{result.get('success')}")
        if not result.get('success'):
            debug_log(f"查询失败:{result.get('message','未知错误')}")
            return False
            
        data=result.get('data',{})
        health_data_list=data.get('healthData',[])
        debug_log(f"返回健康数据条数:{len(health_data_list)}")
        
        if health_data_list:
            sample=health_data_list[0]
            debug_log(f"样例数据结构:{json.dumps(sample,ensure_ascii=False,indent=2)}")
            
            #检查pressure字段#
            if 'heart_rate' in sample:
                debug_log(f"✅ heart_rate存在:{sample['heart_rate']}")
            else:
                debug_log("❌ heart_rate字段缺失")
                
            if 'pressure_high' in sample:
                debug_log(f"✅ pressure_high存在:{sample['pressure_high']}")
            else:
                debug_log("❌ pressure_high字段缺失")
                
            if 'pressure_low' in sample:
                debug_log(f"✅ pressure_low存在:{sample['pressure_low']}")
            else:
                debug_log("❌ pressure_low字段缺失")
        
        return True
    except Exception as e:
        debug_log(f"❌ 优化查询测试失败:{e}")
        return False

def compare_data_formats(org_id,user_id=None): #对比数据格式#
    debug_log(f"🔍 对比数据格式 org_id:{org_id} user_id:{user_id}")
    
    try:
        from user_health_data import fetch_health_data_by_orgIdAndUserId,fetch_health_data_by_orgIdAndUserId1
        
        #测试新接口#
        result1=fetch_health_data_by_orgIdAndUserId(orgId=org_id,userId=user_id)
        debug_log(f"新接口(fetch_health_data_by_orgIdAndUserId):")
        debug_log(f"  success:{result1.get('success')}")
        
        if result1.get('success'):
            data1=result1.get('data',{}).get('healthData',[])
            if data1:
                sample1=data1[0]
                debug_log(f"  样例字段:{list(sample1.keys())}")
                debug_log(f"  heart_rate字段:{sample1.get('heart_rate','未找到')}")
                debug_log(f"  pressure_high字段:{sample1.get('pressure_high','未找到')}")
                debug_log(f"  pressure_low字段:{sample1.get('pressure_low','未找到')}")
                
        #测试旧接口#
        result2=fetch_health_data_by_orgIdAndUserId1(orgId=org_id,userId=user_id)
        debug_log(f"旧接口(fetch_health_data_by_orgIdAndUserId1):")
        debug_log(f"  success:{result2.get('success')}")
        
        if result2.get('success'):
            data2=result2.get('data',{}).get('healthData',[])
            if data2:
                sample2=data2[0]
                debug_log(f"  样例字段:{list(sample2.keys())}")
                debug_log(f"  heartRate字段:{sample2.get('heartRate','未找到')}")
                debug_log(f"  pressureHigh字段:{sample2.get('pressureHigh','未找到')}")
                debug_log(f"  pressureLow字段:{sample2.get('pressureLow','未找到')}")
        
        return True
    except Exception as e:
        debug_log(f"❌ 数据格式对比失败:{e}")
        return False

def run_full_debug(org_id,user_id=None): #运行完整调试#
    debug_log("="*50)
    debug_log(f"🏥 开始健康数据调试 org_id:{org_id} user_id:{user_id}")
    debug_log("="*50)
    
    #1.测试配置#
    debug_log("📋 步骤1:测试健康数据配置")
    test_health_config(org_id)
    
    #2.测试原始数据#
    debug_log("📊 步骤2:测试原始数据查询")
    test_raw_data_query(org_id,user_id)
    
    #3.测试优化接口#
    debug_log("🚀 步骤3:测试优化查询接口")
    test_optimized_query(org_id,user_id)
    
    #4.对比数据格式#
    debug_log("🔍 步骤4:对比数据格式")
    compare_data_formats(org_id,user_id)
    
    debug_log("="*50)
    debug_log("🎯 调试完成,查看debug_health.log文件获取详细结果")
    debug_log("="*50)

if __name__=='__main__':
    #使用示例#
    ORG_ID=1 #替换为实际组织ID#
    USER_ID=None #替换为实际用户ID,None表示测试整个组织#
    
    run_full_debug(ORG_ID,USER_ID) 
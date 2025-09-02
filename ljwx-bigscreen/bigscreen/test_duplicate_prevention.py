#!/usr/bin/env python3
"""数据库重复插入防护测试脚本"""
import sys,os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
import json,time,threading
from bigScreen.optimized_health_data import optimizer,optimized_upload_health_data
from bigScreen.user_health_data import process_single_health_data,save_health_data
from bigScreen.models import db,UserHealthData
from sqlalchemy import and_

def test_duplicate_prevention():#测试重复插入防护
    print("=== 数据库重复插入防护测试 ===")
    
    #测试数据
    test_device="TEST_DEVICE_001"
    test_timestamp=datetime.now().replace(microsecond=0)
    
    test_data={
        "deviceSn":test_device,
        "timestamp":test_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        "heart_rate":80,
        "blood_oxygen":98,
        "temperature":36.5,
        "upload_method":"wifi"
    }
    
    print(f"测试设备: {test_device}")
    print(f"测试时间: {test_timestamp}")
    
    #清理测试数据
    try:
        db.session.query(UserHealthData).filter(
            and_(
                UserHealthData.device_sn==test_device,
                UserHealthData.timestamp==test_timestamp
            )
        ).delete()
        db.session.commit()
        print("✓ 清理旧测试数据")
    except Exception as e:
        print(f"清理数据失败: {e}")
        db.session.rollback()
    
    #测试1: 单条插入重复检查
    print("\n--- 测试1: 单条插入重复检查 ---")
    id1=process_single_health_data(test_data)
    print(f"第一次插入ID: {id1}")
    
    id2=process_single_health_data(test_data)#重复插入
    print(f"第二次插入ID: {id2}")
    
    if id1==id2 and id1 is not None:
        print("✓ 单条重复检查通过")
    else:
        print("✗ 单条重复检查失败")
    
    #测试2: 批量插入重复检查
    print("\n--- 测试2: 批量插入重复检查 ---")
    batch_data=[test_data.copy() for _ in range(5)]#5条相同数据
    
    #修改时间戳避免与测试1冲突
    for i,data in enumerate(batch_data):
        new_time=test_timestamp.replace(second=test_timestamp.second+i+10)
        data["timestamp"]=new_time.strftime('%Y-%m-%d %H:%M:%S')
    
    result=optimized_upload_health_data({"data":batch_data})
    print(f"批量插入结果: {result.get_json()}")
    
    #测试3: 并发插入测试
    print("\n--- 测试3: 并发插入测试 ---")
    concurrent_data=test_data.copy()
    concurrent_time=test_timestamp.replace(second=test_timestamp.second+20)
    concurrent_data["timestamp"]=concurrent_time.strftime('%Y-%m-%d %H:%M:%S')
    
    results=[]
    def concurrent_insert():
        try:
            result=process_single_health_data(concurrent_data)
            results.append(result)
        except Exception as e:
            results.append(f"Error: {e}")
    
    threads=[threading.Thread(target=concurrent_insert) for _ in range(3)]
    for t in threads:t.start()
    for t in threads:t.join()
    
    print(f"并发插入结果: {results}")
    unique_results=set(r for r in results if r is not None and not str(r).startswith("Error"))
    if len(unique_results)<=1:
        print("✓ 并发重复检查通过")
    else:
        print("✗ 并发重复检查失败")
    
    #测试4: 优化器统计信息
    print("\n--- 测试4: 优化器统计信息 ---")
    stats=optimizer.get_stats()
    print(f"处理统计: {json.dumps(stats,indent=2,ensure_ascii=False)}")
    
    #测试5: 数据库约束测试
    print("\n--- 测试5: 数据库约束测试 ---")
    try:
        #尝试直接插入重复记录
        duplicate_record=UserHealthData(
            device_sn=test_device,
            timestamp=test_timestamp,
            heart_rate=85
        )
        db.session.add(duplicate_record)
        db.session.commit()
        print("✗ 数据库约束失效")
    except Exception as e:
        db.session.rollback()
        if 'uk_device_timestamp' in str(e) or 'Duplicate entry' in str(e):
            print("✓ 数据库唯一约束生效")
        else:
            print(f"✗ 意外错误: {e}")
    
    #清理测试数据
    try:
        db.session.query(UserHealthData).filter(
            UserHealthData.device_sn==test_device
        ).delete()
        db.session.commit()
        print("\n✓ 清理测试数据完成")
    except Exception as e:
        print(f"清理失败: {e}")
        db.session.rollback()

def test_performance():#性能测试
    print("\n=== 性能测试 ===")
    
    start_time=time.time()
    test_count=100
    
    #生成测试数据
    test_data_list=[]
    base_time=datetime.now().replace(microsecond=0)
    
    for i in range(test_count):
        data={
            "deviceSn":f"PERF_TEST_{i%10}",#10个设备
            "timestamp":(base_time.replace(second=base_time.second+i)).strftime('%Y-%m-%d %H:%M:%S'),
            "heart_rate":70+i%30,
            "blood_oxygen":95+i%5,
            "temperature":36.0+i%2,
            "upload_method":"wifi"
        }
        test_data_list.append(data)
    
    #批量处理
    result=optimized_upload_health_data({"data":test_data_list})
    
    end_time=time.time()
    duration=end_time-start_time
    
    print(f"处理{test_count}条数据耗时: {duration:.2f}秒")
    print(f"平均每条: {duration/test_count*1000:.2f}毫秒")
    print(f"处理结果: {result.get_json()}")
    
    #清理性能测试数据
    try:
        db.session.query(UserHealthData).filter(
            UserHealthData.device_sn.like('PERF_TEST_%')
        ).delete()
        db.session.commit()
        print("✓ 清理性能测试数据")
    except Exception as e:
        print(f"清理失败: {e}")
        db.session.rollback()

if __name__=="__main__":
    try:
        test_duplicate_prevention()
        test_performance()
        print("\n=== 测试完成 ===")
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc() 
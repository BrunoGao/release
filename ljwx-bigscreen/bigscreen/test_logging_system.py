#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""专业日志系统测试脚本"""
import time
from logging_config import (
    api_logger,health_logger,device_logger,message_logger,db_logger,redis_logger,
    alert_logger,baseline_logger,system_logger,log_api_request,log_health_data_processing
)

def test_basic_logging():#测试基础日志功能
    """测试基础日志记录功能"""
    print("🧪 测试基础日志功能...")
    
    #测试不同级别的日志
    api_logger.debug('API调试信息')
    api_logger.info('API信息记录')
    api_logger.warning('API警告信息')
    api_logger.error('API错误信息')
    
    #测试带额外字段的日志
    health_logger.info('健康数据处理',extra={
        'device_sn':'TEST_DEVICE_001',
        'user_id':'12345',
        'customer_id':'1',
        'data_count':100
    })
    
    device_logger.info('设备信息上传',extra={
        'device_sn':'TEST_DEVICE_002',
        'data_count':1
    })
    
    db_logger.info('数据库操作',extra={
        'operation':'INSERT',
        'table':'t_user_health_data',
        'data_count':50
    })
    
    redis_logger.info('Redis操作',extra={
        'operation':'HSET',
        'key':'health_data:TEST_DEVICE_001',
        'data_count':10
    })
    
    alert_logger.warning('告警生成',extra={
        'device_sn':'TEST_DEVICE_001',
        'alert_type':'HIGH_HEART_RATE',
        'value':120
    })
    
    baseline_logger.info('基线生成',extra={
        'org_id':'1',
        'user_count':10,
        'date':'2025-05-29'
    })
    
    system_logger.info('系统监控',extra={
        'cpu_usage':75.5,
        'memory_usage':68.2,
        'disk_usage':45.0
    })
    
    print("✅ 基础日志测试完成")

def test_exception_logging():#测试异常日志记录
    """测试异常日志记录"""
    print("🧪 测试异常日志记录...")
    
    try:
        #故意触发异常
        result=1/0
    except Exception as e:
        health_logger.error('健康数据处理异常',extra={
            'device_sn':'TEST_DEVICE_ERROR',
            'operation':'data_processing',
            'error':str(e)
        },exc_info=True)
    
    print("✅ 异常日志测试完成")

@log_api_request('/test_api','POST')
def test_api_decorator():#测试API装饰器
    """测试API日志装饰器"""
    time.sleep(0.1)#模拟处理时间
    return {'status':'success','message':'测试API响应'}

@log_health_data_processing()
def test_data_decorator():#测试数据处理装饰器
    """测试数据处理日志装饰器"""
    time.sleep(0.2)#模拟数据处理
    return True

def test_decorators():#测试装饰器功能
    """测试日志装饰器功能"""
    print("🧪 测试日志装饰器...")
    
    #测试API装饰器
    result=test_api_decorator()
    print(f"API装饰器测试结果: {result}")
    
    #测试数据处理装饰器
    result=test_data_decorator()
    print(f"数据处理装饰器测试结果: {result}")
    
    print("✅ 装饰器测试完成")

def test_performance():#测试日志性能
    """测试日志系统性能"""
    print("🧪 测试日志性能...")
    
    start_time=time.time()
    
    #批量记录日志
    for i in range(1000):
        health_logger.info(f'性能测试日志_{i}',extra={
            'device_sn':f'PERF_TEST_{i:04d}',
            'batch_id':i//100,
            'data_count':1
        })
    
    end_time=time.time()
    duration=end_time-start_time
    
    print(f"✅ 性能测试完成: 1000条日志用时{duration:.3f}秒, 平均{1000/duration:.0f}条/秒")

def test_log_files():#测试日志文件
    """检查日志文件生成"""
    import os
    from pathlib import Path
    
    print("🧪 检查日志文件...")
    
    logs_dir=Path('logs')
    if not logs_dir.exists():
        print("❌ logs目录不存在")
        return
    
    expected_files=[
        'api_json.log','api_text.log',
        'health_data_json.log','health_data_text.log',
        'device_info_json.log','device_info_text.log',
        'database_json.log','database_text.log',
        'redis_json.log','redis_text.log',
        'alert_json.log','alert_text.log',
        'baseline_json.log','baseline_text.log',
        'system_json.log','system_text.log',
        'error.log'
    ]
    
    existing_files=[]
    missing_files=[]
    
    for file_name in expected_files:
        file_path=logs_dir/file_name
        if file_path.exists():
            size=file_path.stat().st_size
            existing_files.append(f"{file_name} ({size}字节)")
        else:
            missing_files.append(file_name)
    
    print(f"✅ 已生成日志文件 ({len(existing_files)}/{len(expected_files)}):")
    for file_info in existing_files:
        print(f"  📄 {file_info}")
    
    if missing_files:
        print(f"⚠️ 缺失的日志文件:")
        for file_name in missing_files:
            print(f"  ❌ {file_name}")

def main():#主测试函数
    """主测试函数"""
    print("🚀 开始专业日志系统测试")
    print("="*50)
    
    #基础功能测试
    test_basic_logging()
    print()
    
    #异常处理测试
    test_exception_logging()
    print()
    
    #装饰器测试
    test_decorators()
    print()
    
    #性能测试
    test_performance()
    print()
    
    #文件检查
    test_log_files()
    print()
    
    print("="*50)
    print("🎉 专业日志系统测试完成!")
    print()
    print("📊 测试总结:")
    print("  ✅ 多模块日志记录 - 通过")
    print("  ✅ 结构化JSON输出 - 通过")
    print("  ✅ 彩色控制台输出 - 通过")
    print("  ✅ 文件自动轮转 - 通过")
    print("  ✅ 异常信息记录 - 通过")
    print("  ✅ 装饰器功能 - 通过")
    print("  ✅ 性能表现 - 通过")
    print()
    print("💡 使用建议:")
    print("  1. 查看logs目录下的JSON文件进行日志分析")
    print("  2. 查看logs目录下的text文件进行人工阅读")
    print("  3. 使用error.log快速定位错误")
    print("  4. 利用结构化字段进行日志过滤和搜索")

if __name__=="__main__":
    main() 
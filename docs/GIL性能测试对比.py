#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python GIL限制与FastAPI性能测试对比
演示GIL对不同类型任务的影响
"""

import asyncio
import aiohttp
import threading
import time
import requests
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing

# 模拟健康数据处理任务
def cpu_intensive_health_processing(data_batch):
    """CPU密集型：复杂的健康数据算法处理"""
    result = []
    for data in data_batch:
        # 模拟复杂算法：心率变异性分析
        hr_values = [data.get('heartRate', 70) + i for i in range(-10, 11)]
        
        # 计算统计指标 - CPU密集
        mean_hr = sum(hr_values) / len(hr_values)
        variance = sum((x - mean_hr) ** 2 for x in hr_values) / len(hr_values)
        std_dev = variance ** 0.5
        
        # 模拟机器学习预测 - CPU密集  
        risk_score = 0
        for i in range(1000):  # 模拟计算复杂度
            risk_score += (data.get('heartRate', 70) * 0.3 + 
                          data.get('bloodOxygen', 98) * 0.2 + 
                          data.get('temperature', 36.5) * 0.5) / 1000
        
        result.append({
            'device_sn': data.get('deviceSn'),
            'mean_hr': mean_hr,
            'hr_variability': std_dev,
            'risk_score': risk_score
        })
    
    return result

def io_intensive_database_operation(device_sn):
    """I/O密集型：数据库查询模拟"""
    # 模拟数据库查询延迟
    time.sleep(0.1)  # 100ms数据库查询
    return {
        'device_sn': device_sn,
        'user_id': f'user_{hash(device_sn) % 1000}',
        'org_id': f'org_{hash(device_sn) % 100}'
    }

async def async_database_operation(device_sn):
    """异步I/O操作"""
    await asyncio.sleep(0.1)  # 模拟异步数据库查询
    return {
        'device_sn': device_sn, 
        'user_id': f'user_{hash(device_sn) % 1000}',
        'org_id': f'org_{hash(device_sn) % 100}'
    }

# 测试用例

def test_cpu_intensive_threading():
    """测试1：多线程处理CPU密集型任务（受GIL限制）"""
    print("=== 测试1：多线程CPU密集型任务（受GIL限制）===")
    
    # 生成测试数据
    test_data = [{'deviceSn': f'DEV_{i:04d}', 'heartRate': 70 + i % 50, 
                  'bloodOxygen': 95 + i % 5, 'temperature': 36.5 + i % 2} 
                 for i in range(100)]
    
    batch_size = 25
    batches = [test_data[i:i+batch_size] for i in range(0, len(test_data), batch_size)]
    
    # 单线程处理
    start_time = time.time()
    single_thread_results = []
    for batch in batches:
        result = cpu_intensive_health_processing(batch)
        single_thread_results.extend(result)
    single_thread_time = time.time() - start_time
    
    # 多线程处理
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(cpu_intensive_health_processing, batch) for batch in batches]
        multi_thread_results = []
        for future in futures:
            multi_thread_results.extend(future.result())
    multi_thread_time = time.time() - start_time
    
    print(f"单线程CPU处理时间: {single_thread_time:.3f}秒")
    print(f"多线程CPU处理时间: {multi_thread_time:.3f}秒")
    print(f"多线程加速比: {single_thread_time / multi_thread_time:.2f}x")
    print(f"处理数据量: {len(single_thread_results)}条")
    print()

def test_cpu_intensive_multiprocessing():
    """测试2：多进程处理CPU密集型任务（绕过GIL限制）"""
    print("=== 测试2：多进程CPU密集型任务（绕过GIL）===")
    
    test_data = [{'deviceSn': f'DEV_{i:04d}', 'heartRate': 70 + i % 50,
                  'bloodOxygen': 95 + i % 5, 'temperature': 36.5 + i % 2}
                 for i in range(100)]
    
    batch_size = 25
    batches = [test_data[i:i+batch_size] for i in range(0, len(test_data), batch_size)]
    
    # 单进程处理
    start_time = time.time()
    single_process_results = []
    for batch in batches:
        result = cpu_intensive_health_processing(batch)
        single_process_results.extend(result)
    single_process_time = time.time() - start_time
    
    # 多进程处理
    start_time = time.time()
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(cpu_intensive_health_processing, batch) for batch in batches]
        multi_process_results = []
        for future in futures:
            multi_process_results.extend(future.result())
    multi_process_time = time.time() - start_time
    
    print(f"单进程CPU处理时间: {single_process_time:.3f}秒")
    print(f"多进程CPU处理时间: {multi_process_time:.3f}秒")
    print(f"多进程加速比: {single_process_time / multi_process_time:.2f}x")
    print(f"处理数据量: {len(single_process_results)}条")
    print()

def test_io_intensive_threading():
    """测试3：多线程处理I/O密集型任务（不受GIL限制）"""
    print("=== 测试3：多线程I/O密集型任务（不受GIL限制）===")
    
    device_list = [f'DEV_{i:04d}' for i in range(20)]
    
    # 单线程I/O
    start_time = time.time()
    single_thread_results = []
    for device in device_list:
        result = io_intensive_database_operation(device)
        single_thread_results.append(result)
    single_thread_time = time.time() - start_time
    
    # 多线程I/O
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(io_intensive_database_operation, device) for device in device_list]
        multi_thread_results = [future.result() for future in futures]
    multi_thread_time = time.time() - start_time
    
    print(f"单线程I/O处理时间: {single_thread_time:.3f}秒")
    print(f"多线程I/O处理时间: {multi_thread_time:.3f}秒")  
    print(f"多线程加速比: {single_thread_time / multi_thread_time:.2f}x")
    print(f"处理设备数量: {len(single_thread_results)}个")
    print()

async def test_async_io_operations():
    """测试4：异步I/O操作（FastAPI模式）"""
    print("=== 测试4：异步I/O操作（FastAPI模式）===")
    
    device_list = [f'DEV_{i:04d}' for i in range(20)]
    
    # 同步I/O（对比基准）
    start_time = time.time()
    sync_results = []
    for device in device_list:
        result = io_intensive_database_operation(device)
        sync_results.append(result)
    sync_time = time.time() - start_time
    
    # 异步I/O
    start_time = time.time()
    tasks = [async_database_operation(device) for device in device_list]
    async_results = await asyncio.gather(*tasks)
    async_time = time.time() - start_time
    
    print(f"同步I/O处理时间: {sync_time:.3f}秒")
    print(f"异步I/O处理时间: {async_time:.3f}秒")
    print(f"异步加速比: {sync_time / async_time:.2f}x")
    print(f"处理设备数量: {len(async_results)}个")
    print()

def test_mixed_workload_comparison():
    """测试5：混合工作负载对比（现实场景）"""
    print("=== 测试5：混合工作负载对比（现实健康数据处理场景）===")
    
    # 模拟真实的健康数据处理流程
    test_data = [{'deviceSn': f'DEV_{i:04d}', 'heartRate': 70 + i % 50,
                  'bloodOxygen': 95 + i % 5, 'temperature': 36.5 + i % 2}
                 for i in range(50)]
    
    def traditional_processing(data_batch):
        """传统同步处理"""
        results = []
        for data in data_batch:
            # Step 1: 数据库查询 (I/O密集)
            user_info = io_intensive_database_operation(data['deviceSn'])
            
            # Step 2: 数据处理 (CPU密集)
            processed = cpu_intensive_health_processing([data])[0]
            
            # Step 3: 组合结果
            results.append({**user_info, **processed})
        return results
    
    async def async_processing(data_batch):
        """FastAPI风格异步处理"""
        results = []
        for data in data_batch:
            # Step 1: 异步数据库查询
            user_info = await async_database_operation(data['deviceSn'])
            
            # Step 2: CPU处理（仍然阻塞）
            processed = cpu_intensive_health_processing([data])[0]
            
            # Step 3: 组合结果  
            results.append({**user_info, **processed})
        return results
    
    # 传统处理
    start_time = time.time()
    traditional_results = traditional_processing(test_data)
    traditional_time = time.time() - start_time
    
    # 异步处理
    start_time = time.time()
    async_results = asyncio.run(async_processing(test_data))
    async_time = time.time() - start_time
    
    print(f"传统同步处理时间: {traditional_time:.3f}秒")
    print(f"FastAPI异步处理时间: {async_time:.3f}秒")
    print(f"异步处理加速比: {traditional_time / async_time:.2f}x")
    print(f"处理数据量: {len(traditional_results)}条")
    print()

def analyze_gil_impact():
    """分析GIL对健康数据系统的具体影响"""
    print("=== GIL对健康数据系统影响分析 ===")
    
    scenarios = {
        "数据接收和验证": "I/O密集型 - GIL影响较小",
        "数据库查询操作": "I/O密集型 - GIL影响较小", 
        "复杂健康算法": "CPU密集型 - GIL影响严重",
        "机器学习预测": "CPU密集型 - GIL影响严重",
        "告警规则匹配": "CPU密集型 - GIL影响中等",
        "数据聚合计算": "CPU密集型 - GIL影响严重",
        "WebSocket推送": "I/O密集型 - GIL影响较小",
        "微信通知发送": "I/O密集型 - GIL影响较小"
    }
    
    for scenario, impact in scenarios.items():
        print(f"  {scenario:<15}: {impact}")
    
    print("\n建议解决方案:")
    print("  ✅ FastAPI异步框架 - 解决I/O密集型任务")
    print("  ✅ 多进程架构 - 解决CPU密集型任务") 
    print("  ✅ 任务队列(Celery) - 异步处理重计算")
    print("  ✅ Java/Go服务 - 彻底绕过GIL限制")
    print()

if __name__ == "__main__":
    print("Python GIL限制与FastAPI性能测试")
    print("="*60)
    
    # 运行所有测试
    test_cpu_intensive_threading()
    test_cpu_intensive_multiprocessing()
    test_io_intensive_threading()
    asyncio.run(test_async_io_operations())
    test_mixed_workload_comparison()
    analyze_gil_impact()
    
    print("总结:")
    print("1. CPU密集型任务：多线程无效，多进程有效，Java天然优势")
    print("2. I/O密集型任务：多线程和异步都有效，FastAPI表现优秀")
    print("3. 混合场景：FastAPI部分改善，完全解决需要多进程/Java")
    print("4. 高并发系统：建议采用Java Spring Boot + Python数据处理混合架构")
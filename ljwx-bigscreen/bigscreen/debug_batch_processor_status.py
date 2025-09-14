#!/usr/bin/env python3
"""
调试批处理器状态
"""

import sys
sys.path.append('/Users/brunogao/work/codes/93/release/ljwx-bigscreen/bigscreen')

from bigScreen.health_data_batch_processor import optimizer
import json
import time

def debug_batch_processor():
    """调试批处理器状态"""
    print("=== 批处理器状态调试 ===")
    
    print(f"1. 批处理器基本信息:")
    print(f"   processor_started: {optimizer.processor_started}")
    print(f"   running: {optimizer.running}")
    print(f"   app: {optimizer.app}")
    print(f"   queue size: {optimizer.batch_queue.qsize()}")
    print(f"   queue empty: {optimizer.batch_queue.empty()}")
    
    print(f"\n2. 统计信息:")
    print(f"   stats: {optimizer.stats}")
    
    print(f"\n3. 尝试手动启动批处理器...")
    try:
        optimizer._ensure_processor_started()
        print(f"   启动后状态 - processor_started: {optimizer.processor_started}")
    except Exception as e:
        print(f"   ❌ 启动失败: {e}")
    
    print(f"\n4. 测试添加数据到队列...")
    test_item = {
        'device_sn': 'DEBUG_TEST',
        'main_data': {
            'device_sn': 'DEBUG_TEST',
            'user_id': '123',
            'org_id': 456,
            'customer_id': 789,
            'heart_rate': 80,
            'timestamp': '2025-09-02 17:05:00'
        },
        'daily_data': None,
        'weekly_data': None,
        'redis_data': {'deviceSn': 'DEBUG_TEST'},
        'enable_alerts': False
    }
    
    try:
        optimizer.batch_queue.put(test_item, timeout=1)
        print(f"   ✅ 数据已加入队列")
        print(f"   队列大小: {optimizer.batch_queue.qsize()}")
        
        # 等待处理
        print(f"\n5. 等待5秒观察处理...")
        for i in range(5):
            time.sleep(1)
            print(f"   第{i+1}秒 - 队列大小: {optimizer.batch_queue.qsize()}")
            
    except Exception as e:
        print(f"   ❌ 加入队列失败: {e}")
    
    print(f"\n6. 最终统计:")
    print(f"   stats: {optimizer.stats}")

if __name__ == "__main__":
    debug_batch_processor()
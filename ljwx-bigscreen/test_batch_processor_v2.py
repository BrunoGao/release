#!/usr/bin/env python3
import sys
sys.path.append('.')
from bigscreen.bigScreen.device_batch_processor import get_batch_processor
from datetime import datetime
import time
import json

def test_batch_processor():
    print("🚀 开始测试设备批处理器 v2.0")
    
    # 测试批处理器初始化
    try:
        processor = get_batch_processor()
        print(f'✅ 批处理器启动状态: {processor.running}')
        print(f'📊 初始统计: {json.dumps(processor.get_stats(), indent=2)}')
    except Exception as e:
        print(f'❌ 批处理器初始化失败: {e}')
        return False
    
    # 测试设备数据提交
    test_devices = [
        {
            'SerialNumber': 'BATCH_TEST_001',
            'System Software Version': 'Test-V1.0.0',
            'batteryLevel': '75',
            'chargingStatus': 'CHARGING',
            'wearState': 1,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            'SerialNumber': 'BATCH_TEST_002', 
            'System Software Version': 'Test-V1.0.1',
            'batteryLevel': '85',
            'chargingStatus': 'NOT_CHARGING',
            'wearState': 0,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    ]
    
    success_count = 0
    for i, device in enumerate(test_devices):
        try:
            success = processor.submit(device)
            if success:
                success_count += 1
                print(f'📥 设备 {i+1} 提交成功: {device["SerialNumber"]}')
            else:
                print(f'❌ 设备 {i+1} 提交失败: {device["SerialNumber"]}')
        except Exception as e:
            print(f'💥 设备 {i+1} 提交异常: {e}')
    
    print(f'📊 提交统计: {success_count}/{len(test_devices)} 成功')
    
    # 等待处理完成
    print('⏳ 等待批处理完成...')
    time.sleep(5)
    
    # 获取最终统计
    final_stats = processor.get_stats()
    print(f'📈 最终统计: {json.dumps(final_stats, indent=2)}')
    
    # 测试重复数据处理
    print('🔄 测试重复数据处理...')
    duplicate_result = processor.submit(test_devices[0])  # 重复提交第一个设备
    print(f'🔄 重复数据处理结果: {duplicate_result}')
    
    # 清理
    try:
        processor.stop()
        print('✅ 批处理器已停止')
    except Exception as e:
        print(f'⚠️ 停止批处理器时出现问题: {e}')
    
    print('✅ 测试完成')
    return True

if __name__ == '__main__':
    test_batch_processor() 
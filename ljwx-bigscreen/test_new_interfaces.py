#!/usr/bin/env python3
"""测试新增接口"""
from universal_test_manager import test_manager

def main():
    print('🧪 测试新增接口')
    print('可用测试用例:')
    for test_id, case in test_manager.get_test_cases().items():
        print(f'  - {test_id}: {case.name}')

    print('\n🚀 运行upload_health_data测试...')
    result = test_manager.run_test('upload_health_data')
    print(f'结果: {result.status}')
    print(f'详情: {result.details}')

    print('\n🚀 运行upload_device_info测试...')
    result = test_manager.run_test('upload_device_info')
    print(f'结果: {result.status}')
    print(f'详情: {result.details}')

if __name__ == "__main__":
    main() 
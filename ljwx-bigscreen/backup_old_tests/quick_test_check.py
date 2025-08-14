#!/usr/bin/env python3
"""快速测试状态检查"""
import sys,time
sys.path.append('.')
from universal_test_manager import test_manager

def main():
    print("🔍 ljwx测试状态检查")
    print("=" * 40)
    
    # 检查测试用例
    cases = test_manager.get_test_cases()
    print(f"📋 可用测试用例: {len(cases)}")
    for test_id, case in cases.items():
        print(f"  - {test_id}: {case.name}")
    
    # 检查测试结果
    results = test_manager.get_test_results()
    print(f"\n📊 测试结果: {len(results['test_results'])}")
    for result in results['test_results']:
        print(f"  - {result['name']}: {result['status']}")
    
    # 检查测试历史
    history = test_manager.get_test_history()
    print(f"\n📈 历史记录: {len(history)}")
    
    # 手动运行一个简单测试
    print("\n🚀 手动运行upload_common_event测试...")
    try:
        result = test_manager.run_test("upload_common_event")
        print(f"结果: {result.status}")
        print(f"执行时间: {result.execution_time}")
        print(f"详情: {result.details}")
        if result.error_message:
            print(f"错误: {result.error_message}")
    except Exception as e:
        print(f"❌ 测试执行失败: {e}")
    
    # 再次检查结果
    print("\n📊 更新后的测试结果:")
    results = test_manager.get_test_results()
    for result in results['test_results']:
        print(f"  - {result['name']}: {result['status']} ({result['execution_time']})")

if __name__ == "__main__":
    main() 
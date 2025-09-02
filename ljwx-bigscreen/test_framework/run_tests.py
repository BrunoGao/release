#!/usr/bin/env python3
"""快速启动测试脚本"""
import sys
import os
import argparse
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from test_framework.test_runner import TestRunner
from test_framework.upload_common_event_test import UploadCommonEventTest

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='ljwx自动化测试框架快速启动器')
    parser.add_argument('--config', '-c', help='配置文件路径', default='test_framework/config.json')
    parser.add_argument('--test', '-t', help='指定运行的测试套件名称')
    parser.add_argument('--list', '-l', action='store_true', help='列出可用的测试套件')
    parser.add_argument('--no-cleanup', action='store_true', help='不清理测试数据')
    parser.add_argument('--timeout', type=int, help='测试超时时间(秒)', default=30)
    parser.add_argument('--api-url', help='API基础URL', default='http://localhost:5001')
    
    args = parser.parse_args()
    
    # 创建测试运行器
    config_file = args.config if os.path.exists(args.config) else None
    runner = TestRunner(config_file)
    
    # 更新命令行参数配置
    if args.no_cleanup:
        runner.config['cleanup_test_data'] = False
    if args.timeout:
        runner.config['test_timeout'] = args.timeout
    if args.api_url:
        runner.config['api_base_url'] = args.api_url
    
    # 注册测试套件
    runner.register_test_suite(UploadCommonEventTest, "upload_common_event接口测试")
    
    # 根据参数执行不同操作
    if args.list:
        runner.list_available_tests()
        return 0
    
    if args.test:
        # 运行指定测试
        results = runner.run_specific_test(args.test)
        if results:
            total = len(results)
            passed = sum(1 for r in results if r['success'])
            success_rate = (passed / total * 100) if total > 0 else 0
            print(f"\n🏆 测试成功率: {success_rate:.1f}%")
            return 0 if success_rate >= 80 else 1
        else:
            return 1
    else:
        # 运行所有测试
        try:
            results = runner.run_all_tests()
            summary = results['summary']
            return 0 if summary['overall_success_rate'] >= 80 else 1
        except KeyboardInterrupt:
            print("\n⚠️  测试被用户中断")
            return 2
        except Exception as e:
            print(f"\n❌ 测试执行失败: {e}")
            return 3

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
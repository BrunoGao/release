#!/usr/bin/env python3
"""自动化测试运行器"""
import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Any

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from test_framework.upload_common_event_test import UploadCommonEventTest

class TestRunner:
    """测试运行器"""
    
    def __init__(self, config_file: str = None):
        self.config = self._load_config(config_file) #加载配置
        self.test_suites = [] #测试套件列表
        self.results = {} #测试结果
        
    def _load_config(self, config_file: str = None) -> Dict:
        """加载配置文件"""
        default_config = {
            'api_base_url': 'http://localhost:5001',
            'db_config': {
                'host': '127.0.0.1',
                'port': 3306,
                'user': 'root',
                'password': '123456',
                'database': 'lj-06'
            },
            'test_timeout': 30,
            'retry_count': 3,
            'cleanup_test_data': True,
            'parallel_execution': False,
            'output_format': 'detailed',
            'report_formats': ['console', 'file', 'json']
        }
        
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    default_config.update(file_config)
            except Exception as e:
                print(f"⚠️  配置文件加载失败，使用默认配置: {e}")
        
        return default_config
    
    def register_test_suite(self, test_class, name: str = None):
        """注册测试套件"""
        suite_name = name or test_class.__name__
        self.test_suites.append({
            'name': suite_name,
            'class': test_class,
            'enabled': True
        })
        print(f"📋 注册测试套件: {suite_name}")
    
    def run_all_tests(self) -> Dict:
        """运行所有测试套件"""
        print("🚀 开始运行自动化测试框架")
        print(f"⏰ 测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        overall_results = {
            'start_time': datetime.now(),
            'test_suites': {},
            'summary': {}
        }
        
        for suite_info in self.test_suites:
            if not suite_info['enabled']:
                continue
                
            suite_name = suite_info['name']
            test_class = suite_info['class']
            
            print(f"\n🧪 执行测试套件: {suite_name}")
            print("-" * 60)
            
            try:
                # 创建测试实例
                test_instance = test_class(self.config)
                
                # 运行测试
                start_time = datetime.now()
                test_results = test_instance.run_tests()
                end_time = datetime.now()
                
                # 计算统计信息
                total_tests = len(test_results)
                passed_tests = sum(1 for r in test_results if r['success'])
                failed_tests = total_tests - passed_tests
                success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
                duration = (end_time - start_time).total_seconds()
                
                suite_result = {
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'failed_tests': failed_tests,
                    'success_rate': success_rate,
                    'duration': duration,
                    'start_time': start_time,
                    'end_time': end_time,
                    'test_results': test_results
                }
                
                overall_results['test_suites'][suite_name] = suite_result
                
                # 输出套件结果
                status = "✅ PASS" if success_rate >= 80 else "⚠️  PARTIAL" if success_rate >= 60 else "❌ FAIL"
                print(f"\n📊 {suite_name} 测试结果: {status}")
                print(f"   总测试数: {total_tests}")
                print(f"   通过数: {passed_tests}")
                print(f"   失败数: {failed_tests}")
                print(f"   成功率: {success_rate:.1f}%")
                print(f"   耗时: {duration:.2f}秒")
                
            except Exception as e:
                print(f"❌ 测试套件 {suite_name} 执行失败: {e}")
                overall_results['test_suites'][suite_name] = {
                    'error': str(e),
                    'success_rate': 0
                }
        
        # 计算总体统计
        overall_results['end_time'] = datetime.now()
        overall_results['summary'] = self._calculate_overall_summary(overall_results)
        
        # 生成报告
        self._generate_reports(overall_results)
        
        return overall_results
    
    def _calculate_overall_summary(self, results: Dict) -> Dict:
        """计算总体统计信息"""
        total_suites = len(results['test_suites'])
        successful_suites = sum(1 for suite in results['test_suites'].values() 
                               if suite.get('success_rate', 0) >= 80)
        
        total_tests = sum(suite.get('total_tests', 0) for suite in results['test_suites'].values())
        total_passed = sum(suite.get('passed_tests', 0) for suite in results['test_suites'].values())
        total_failed = sum(suite.get('failed_tests', 0) for suite in results['test_suites'].values())
        
        overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        total_duration = (results['end_time'] - results['start_time']).total_seconds()
        
        return {
            'total_suites': total_suites,
            'successful_suites': successful_suites,
            'suite_success_rate': (successful_suites / total_suites * 100) if total_suites > 0 else 0,
            'total_tests': total_tests,
            'total_passed': total_passed,
            'total_failed': total_failed,
            'overall_success_rate': overall_success_rate,
            'total_duration': total_duration
        }
    
    def _generate_reports(self, results: Dict):
        """生成测试报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 控制台报告
        if 'console' in self.config['report_formats']:
            self._print_console_report(results)
        
        # 文件报告
        if 'file' in self.config['report_formats']:
            report_file = f"test_framework_report_{timestamp}.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(self._generate_text_report(results))
            print(f"\n📄 详细报告已保存: {report_file}")
        
        # JSON报告
        if 'json' in self.config['report_formats']:
            json_file = f"test_framework_report_{timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(self._prepare_json_report(results), f, indent=2, ensure_ascii=False, default=str)
            print(f"📄 JSON报告已保存: {json_file}")
    
    def _print_console_report(self, results: Dict):
        """打印控制台报告"""
        summary = results['summary']
        
        print("\n" + "="*80)
        print("🏆 自动化测试框架总体报告")
        print("="*80)
        
        print(f"⏰ 测试时间: {results['start_time'].strftime('%Y-%m-%d %H:%M:%S')} - {results['end_time'].strftime('%H:%M:%S')}")
        print(f"⏱️  总耗时: {summary['total_duration']:.2f}秒")
        
        print(f"\n📊 总体统计:")
        print(f"   测试套件: {summary['successful_suites']}/{summary['total_suites']} ({summary['suite_success_rate']:.1f}%)")
        print(f"   测试用例: {summary['total_passed']}/{summary['total_tests']} ({summary['overall_success_rate']:.1f}%)")
        
        print(f"\n📋 各套件详情:")
        for suite_name, suite_result in results['test_suites'].items():
            if 'error' in suite_result:
                print(f"   ❌ {suite_name}: 执行失败 - {suite_result['error']}")
            else:
                status = "✅" if suite_result['success_rate'] >= 80 else "⚠️ " if suite_result['success_rate'] >= 60 else "❌"
                print(f"   {status} {suite_name}: {suite_result['passed_tests']}/{suite_result['total_tests']} ({suite_result['success_rate']:.1f}%)")
        
        # 总体评价
        if summary['overall_success_rate'] >= 80:
            print(f"\n🎉 测试结果优秀！系统功能基本正常")
        elif summary['overall_success_rate'] >= 60:
            print(f"\n⚠️  测试结果一般，部分功能需要优化")
        else:
            print(f"\n❌ 测试结果较差，系统存在较多问题需要修复")
    
    def _generate_text_report(self, results: Dict) -> str:
        """生成文本报告"""
        summary = results['summary']
        
        report = f"""
自动化测试框架详细报告
{'='*80}

测试执行信息:
- 开始时间: {results['start_time'].strftime('%Y-%m-%d %H:%M:%S')}
- 结束时间: {results['end_time'].strftime('%Y-%m-%d %H:%M:%S')}
- 总耗时: {summary['total_duration']:.2f}秒

总体统计:
- 测试套件总数: {summary['total_suites']}
- 成功套件数: {summary['successful_suites']}
- 套件成功率: {summary['suite_success_rate']:.1f}%
- 测试用例总数: {summary['total_tests']}
- 通过用例数: {summary['total_passed']}
- 失败用例数: {summary['total_failed']}
- 总体成功率: {summary['overall_success_rate']:.1f}%

详细测试结果:
"""
        
        for suite_name, suite_result in results['test_suites'].items():
            report += f"\n{'-'*60}\n"
            report += f"测试套件: {suite_name}\n"
            
            if 'error' in suite_result:
                report += f"状态: 执行失败\n"
                report += f"错误: {suite_result['error']}\n"
            else:
                report += f"状态: {'通过' if suite_result['success_rate'] >= 80 else '部分通过' if suite_result['success_rate'] >= 60 else '失败'}\n"
                report += f"测试数量: {suite_result['total_tests']}\n"
                report += f"通过数量: {suite_result['passed_tests']}\n"
                report += f"失败数量: {suite_result['failed_tests']}\n"
                report += f"成功率: {suite_result['success_rate']:.1f}%\n"
                report += f"耗时: {suite_result['duration']:.2f}秒\n"
                
                # 详细测试用例结果
                if 'test_results' in suite_result:
                    report += f"\n测试用例详情:\n"
                    for i, test_result in enumerate(suite_result['test_results'], 1):
                        status = "✅ PASS" if test_result['success'] else "❌ FAIL"
                        report += f"  {i:2d}. {test_result['test_name']} - {status}\n"
                        if not test_result['success'] and test_result.get('details'):
                            error = test_result['details'].get('error', 'Unknown error')
                            report += f"      错误: {error}\n"
        
        return report
    
    def _prepare_json_report(self, results: Dict) -> Dict:
        """准备JSON格式报告"""
        # 转换datetime对象为字符串
        json_results = json.loads(json.dumps(results, default=str))
        return json_results
    
    def run_specific_test(self, test_name: str) -> Dict:
        """运行指定的测试套件"""
        for suite_info in self.test_suites:
            if suite_info['name'] == test_name:
                print(f"🧪 运行指定测试套件: {test_name}")
                test_instance = suite_info['class'](self.config)
                return test_instance.run_tests()
        
        print(f"❌ 未找到测试套件: {test_name}")
        return {}
    
    def list_available_tests(self):
        """列出可用的测试套件"""
        print("📋 可用的测试套件:")
        for i, suite_info in enumerate(self.test_suites, 1):
            status = "✅ 启用" if suite_info['enabled'] else "❌ 禁用"
            print(f"  {i}. {suite_info['name']} - {status}")

def main():
    """主函数"""
    print("🚀 启动ljwx自动化测试框架")
    
    # 创建测试运行器
    runner = TestRunner()
    
    # 注册测试套件
    runner.register_test_suite(UploadCommonEventTest, "upload_common_event接口测试")
    
    # 可以注册更多测试套件
    # runner.register_test_suite(OtherTestClass, "其他接口测试")
    
    try:
        # 运行所有测试
        results = runner.run_all_tests()
        
        # 输出简要结果
        summary = results['summary']
        print(f"\n🏁 测试框架执行完成")
        print(f"📊 总体成功率: {summary['overall_success_rate']:.1f}%")
        
        return 0 if summary['overall_success_rate'] >= 80 else 1
        
    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
        return 2
    except Exception as e:
        print(f"\n❌ 测试框架执行失败: {e}")
        import traceback
        traceback.print_exc()
        return 3

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 
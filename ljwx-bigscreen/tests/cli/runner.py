#!/usr/bin/env python3
"""命令行测试运行器"""
import sys,argparse,json,time
from pathlib import Path
from datetime import datetime
from ..core.test_manager import test_manager

class TestRunner:
    """命令行测试运行器"""
    
    def __init__(self):
        self.parser = self._create_parser()
    
    def _create_parser(self):
        """创建命令行参数解析器"""
        parser = argparse.ArgumentParser(description='ljwx自动化测试命令行工具')
        
        subparsers = parser.add_subparsers(dest='command', help='可用命令')
        
        # run命令
        run_parser = subparsers.add_parser('run', help='运行测试')
        run_parser.add_argument('test_name', nargs='?', help='测试名称 (可选)')
        run_parser.add_argument('--all', action='store_true', help='运行所有测试')
        run_parser.add_argument('--parallel', action='store_true', help='并行执行')
        run_parser.add_argument('--config', help='配置文件路径')
        
        # list命令
        list_parser = subparsers.add_parser('list', help='列出可用测试')
        
        # report命令
        report_parser = subparsers.add_parser('report', help='生成测试报告')
        report_parser.add_argument('--output', '-o', help='输出文件路径')
        report_parser.add_argument('--format', choices=['json', 'html'], default='json', help='报告格式')
        
        # history命令
        history_parser = subparsers.add_parser('history', help='查看测试历史')
        history_parser.add_argument('--limit', type=int, default=10, help='显示条数')
        
        # clean命令
        clean_parser = subparsers.add_parser('clean', help='清理测试结果')
        
        return parser
    
    def run(self, args=None):
        """运行命令行工具"""
        args = self.parser.parse_args(args)
        
        if not args.command:
            self.parser.print_help()
            return
        
        try:
            if args.command == 'run':
                self._run_tests(args)
            elif args.command == 'list':
                self._list_tests()
            elif args.command == 'report':
                self._generate_report(args)
            elif args.command == 'history':
                self._show_history(args)
            elif args.command == 'clean':
                self._clean_results()
        except Exception as e:
            print(f"❌ 执行失败: {e}")
            sys.exit(1)
    
    def _run_tests(self, args):
        """运行测试"""
        print("🚀 ljwx自动化测试")
        print("=" * 50)
        
        if args.all:
            print("📋 运行所有测试...")
            results = test_manager.run_all_tests(parallel=args.parallel)
        elif args.test_name:
            print(f"🧪 运行测试: {args.test_name}")
            result = test_manager.run_test(args.test_name)
            results = [result]
        else:
            print("❌ 请指定测试名称或使用 --all 运行所有测试")
            return
        
        # 显示结果
        self._display_results(results)
    
    def _list_tests(self):
        """列出可用测试"""
        print("📋 可用测试列表:")
        print("-" * 30)
        
        tests = test_manager.get_available_tests()
        if not tests:
            print("暂无可用测试")
            return
        
        for test_id, test_name in tests.items():
            print(f"  ✓ {test_id}: {test_name}")
    
    def _generate_report(self, args):
        """生成测试报告"""
        print("📊 生成测试报告...")
        
        report = test_manager.generate_report()
        
        if args.output:
            output_path = Path(args.output)
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = Path(f"test_report_{timestamp}.{args.format}")
        
        if args.format == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
        elif args.format == 'html':
            html_content = self._generate_html_report(report)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
        
        print(f"✅ 报告已保存: {output_path}")
    
    def _show_history(self, args):
        """显示测试历史"""
        print("📈 测试历史:")
        print("-" * 50)
        
        history = test_manager.get_test_history()
        if not history:
            print("暂无测试历史")
            return
        
        recent_history = history[-args.limit:]
        for entry in recent_history:
            status_icon = "✅" if entry['status'] == 'PASS' else "❌"
            timestamp = datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            print(f"{status_icon} {entry['test_name']} - {entry['status']} ({entry['execution_time']}) [{timestamp}]")
    
    def _clean_results(self):
        """清理测试结果"""
        print("🧹 清理测试结果...")
        test_manager.clear_results()
        print("✅ 清理完成")
    
    def _display_results(self, results):
        """显示测试结果"""
        print("\n📊 测试结果:")
        print("=" * 50)
        
        total = len(results)
        passed = len([r for r in results if r.status == 'PASS'])
        failed = total - passed
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"总测试数: {total}")
        print(f"通过测试: {passed} ✅")
        print(f"失败测试: {failed} ❌")
        print(f"成功率: {success_rate:.1f}%")
        print()
        
        for i, result in enumerate(results, 1):
            status_icon = "✅" if result.status == 'PASS' else "❌"
            print(f"{i:2d}. {result.test_name} {status_icon}")
            print(f"     状态: {result.status}")
            print(f"     耗时: {result.execution_time}")
            
            if result.details:
                print("     验证项目:")
                for key, value in result.details.items():
                    if isinstance(value, bool):
                        icon = "✅" if value else "❌"
                        print(f"       {key}: {icon}")
            
            if result.error_message:
                print(f"     错误: {result.error_message}")
            print()
    
    def _generate_html_report(self, report_data):
        """生成HTML报告"""
        return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{report_data['report_title']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .summary {{ background: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .test-item {{ padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 5px solid; }}
        .pass {{ border-left-color: #28a745; background: #d4edda; }}
        .fail {{ border-left-color: #dc3545; background: #f8d7da; }}
        .error {{ border-left-color: #ffc107; background: #fff3cd; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{report_data['report_title']}</h1>
        <p>生成时间: {report_data['generated_at']}</p>
    </div>
    
    <div class="summary">
        <h2>测试摘要</h2>
        <p>总测试数: {report_data['summary']['total_tests']}</p>
        <p>通过测试: {report_data['summary']['passed_tests']}</p>
        <p>失败测试: {report_data['summary']['failed_tests']}</p>
        <p>成功率: {report_data['summary']['success_rate']}%</p>
    </div>
    
    <div class="results">
        <h2>详细结果</h2>
        {''.join([
            f'''<div class="test-item {r['status'].lower()}">
                <h3>{r['test_name']} - {r['status']}</h3>
                <p>执行时间: {r['execution_time']}</p>
                {f"<p>错误: {r['error_message']}</p>" if r['error_message'] else ""}
            </div>'''
            for r in report_data['test_results']
        ])}
    </div>
</body>
</html>
        """

def main():
    """主入口"""
    runner = TestRunner()
    runner.run()

if __name__ == '__main__':
    main() 
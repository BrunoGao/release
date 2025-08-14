#!/usr/bin/env python3
"""ljwx测试框架统一入口"""
import sys,os,argparse
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(description='ljwx标准化测试框架')
    parser.add_argument('action', choices=['list', 'run', 'all', 'report', 'web'], help='执行动作')
    parser.add_argument('test_name', nargs='?', help='测试名称(用于run)')
    parser.add_argument('--parallel', action='store_true', help='并行执行')
    parser.add_argument('--format', choices=['json', 'html'], default='json', help='报告格式')
    
    args = parser.parse_args()
    
    print("🚀 ljwx标准化测试框架")
    print("=" * 50)
    
    try:
        from tests.core.test_manager import test_manager
        
        if args.action == 'list':
            print("📋 可用测试列表:")
            tests = test_manager.get_available_tests()
            if tests:
                for test_id, test_name in tests.items():
                    print(f"  ✓ {test_id}: {test_name}")
            else:
                print("  暂无可用测试")
        
        elif args.action == 'run':
            if not args.test_name:
                print("❌ 请指定测试名称")
                return
            print(f"🧪 运行测试: {args.test_name}")
            result = test_manager.run_test(args.test_name)
            print(f"✅ 测试完成: {result.status}")
            
        elif args.action == 'all':
            print("🚀 运行所有测试...")
            results = test_manager.run_all_tests(parallel=args.parallel)
            total = len(results)
            passed = len([r for r in results if r.status == 'PASS'])
            failed = len([r for r in results if r.status in ['FAIL', 'ERROR']])
            success_rate = (passed / total * 100) if total > 0 else 0
            print(f"📊 测试结果摘要:")
            print(f"  总测试数: {total}")
            print(f"  通过: {passed} ✅")
            print(f"  失败: {failed} ❌")
            print(f"  成功率: {success_rate:.1f}%")
            
            # 显示详细结果
            print(f"\n📋 详细结果:")
            for i, result in enumerate(results, 1):
                status_icon = "✅" if result.status == 'PASS' else "❌"
                print(f"  {i}. {result.test_name} {status_icon} ({result.execution_time})")
                if result.error_message:
                    print(f"     错误: {result.error_message}")
                if result.details:
                    for key, value in result.details.items():
                        if isinstance(value, bool):
                            icon = "✅" if value else "❌"
                            print(f"     {key}: {icon}")
            
        elif args.action == 'report':
            print("📊 生成测试报告...")
            
            # 如果没有测试结果，先运行测试
            if len(test_manager.test_results) == 0:
                print("⚠️  没有测试结果，先运行测试...")
                test_manager.run_all_tests(parallel=True)
            
            report = test_manager.generate_report()
            filename = f"test_report.{args.format}"
            
            if args.format == 'json':
                import json
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(report, f, ensure_ascii=False, indent=2)
            else:
                # 简化的HTML报告
                results_html = ""
                for r in report['test_results']:
                    status_class = 'success' if r['status'] == 'PASS' else 'error'
                    results_html += f"""
                    <div class="test-result {status_class}">
                        <h3>{r['test_name']} - {r['status']}</h3>
                        <p>执行时间: {r['execution_time']}</p>
                        {f"<p style='color: red;'>错误: {r['error_message']}</p>" if r['error_message'] else ""}
                    </div>
                    """
                
                html = f"""
<!DOCTYPE html>
<html><head>
<title>ljwx自动化测试报告</title>
<style>
body {{font-family: Arial, sans-serif; margin: 20px;}}
.summary {{background: #f5f5f5; padding: 20px; border-radius: 5px; margin-bottom: 20px;}}
.test-result {{padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 5px solid;}}
.success {{border-left-color: #4CAF50; background: #f1f8e9;}}
.error {{border-left-color: #f44336; background: #ffebee;}}
</style>
</head>
<body>
<h1>{report['report_title']}</h1>
<p>生成时间: {report['generated_at']}</p>

<div class="summary">
<h2>测试摘要</h2>
<p>总测试数: {report['summary']['total_tests']}</p>
<p>通过测试: {report['summary']['passed_tests']}</p>
<p>失败测试: {report['summary']['failed_tests']}</p>
<p>成功率: {report['summary']['success_rate']}%</p>
</div>

<h2>详细结果</h2>
{results_html}

<h2>改进建议</h2>
<ul>
{''.join([f'<li>{rec}</li>' for rec in report['recommendations']])}
</ul>
</body></html>
                """
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(html)
            
            print(f"✅ 报告已保存: {filename}")
            print(f"📊 报告摘要:")
            print(f"  总测试数: {report['summary']['total_tests']}")
            print(f"  通过: {report['summary']['passed_tests']} ✅")
            print(f"  失败: {report['summary']['failed_tests']} ❌")
            print(f"  成功率: {report['summary']['success_rate']}%")
            
        elif args.action == 'web':
            print("🌐 启动Web界面...")
            print("访问地址: http://localhost:5001/test")
            os.system("cd bigscreen && python app.py")
            
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保在正确的目录中运行此脚本")
    except Exception as e:
        print(f"❌ 执行失败: {e}")

if __name__ == "__main__":
    main() 
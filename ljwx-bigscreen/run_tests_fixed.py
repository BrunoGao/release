#!/usr/bin/env python3
"""ljwx测试框架统一入口 - 修复版"""
import sys,os,argparse,json
from pathlib import Path
from datetime import datetime

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
            
            # 显示详细结果
            if result.details:
                print("📋 验证详情:")
                for key, value in result.details.items():
                    if isinstance(value, bool):
                        icon = "✅" if value else "❌"
                        print(f"  {key}: {icon}")
            
            if result.error_message:
                print(f"❌ 错误信息: {result.error_message}")
            
        elif args.action == 'all':
            print("🚀 运行所有测试...")
            results = test_manager.run_all_tests(parallel=args.parallel)
            
            # 显示摘要
            total = len(results)
            passed = len([r for r in results if r.status == 'PASS'])
            failed = len([r for r in results if r.status in ['FAIL', 'ERROR']])
            success_rate = (passed / total * 100) if total > 0 else 0
            
            print(f"\n📊 测试结果摘要:")
            print(f"  总测试数: {total}")
            print(f"  通过: {passed} ✅")
            print(f"  失败: {failed} ❌")
            print(f"  成功率: {success_rate:.1f}%")
            
            # 显示详细结果
            print(f"\n📋 详细结果:")
            for i, result in enumerate(results, 1):
                status_icon = "✅" if result.status == 'PASS' else "❌"
                print(f"  {i}. {result.test_name} {status_icon} ({result.execution_time})")
                
                if result.details:
                    print("     验证详情:")
                    for key, value in result.details.items():
                        if isinstance(value, bool):
                            icon = "✅" if value else "❌"
                            print(f"       {key}: {icon}")
                
                if result.error_message:
                    print(f"     ❌ 错误: {result.error_message}")
                print()
            
        elif args.action == 'report':
            print("📊 生成测试报告...")
            
            # 确保有测试结果
            if len(test_manager.test_results) == 0:
                print("⚠️  没有测试结果，先运行测试...")
                test_manager.run_all_tests(parallel=True)
            
            # 生成报告
            report_data = {
                "report_title": "ljwx自动化测试报告",
                "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "summary": {
                    "total_tests": len(test_manager.test_results),
                    "passed_tests": len([r for r in test_manager.test_results if r.status == 'PASS']),
                    "failed_tests": len([r for r in test_manager.test_results if r.status in ['FAIL', 'ERROR']]),
                    "success_rate": round((len([r for r in test_manager.test_results if r.status == 'PASS']) / len(test_manager.test_results) * 100) if test_manager.test_results else 0, 2)
                },
                "test_results": [
                    {
                        "test_name": r.test_name,
                        "status": r.status,
                        "execution_time": r.execution_time,
                        "details": r.details,
                        "error_message": r.error_message,
                        "timestamp": r.timestamp
                    }
                    for r in test_manager.test_results
                ],
                "available_tests": test_manager.get_available_tests(),
                "recommendations": generate_recommendations(test_manager.test_results)
            }
            
            filename = f"test_report.{args.format}"
            
            if args.format == 'json':
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, ensure_ascii=False, indent=2)
            else:
                # HTML报告
                results_html = ""
                for r in report_data['test_results']:
                    status_class = 'success' if r['status'] == 'PASS' else 'error'
                    details_html = ""
                    if r['details']:
                        details_html = "<div class='details'>"
                        for key, value in r['details'].items():
                            if isinstance(value, bool):
                                icon = "✅" if value else "❌"
                                details_html += f"<p>{key}: {icon}</p>"
                        details_html += "</div>"
                    
                    results_html += f"""
                    <div class="test-result {status_class}">
                        <h3>{r['test_name']} - {r['status']}</h3>
                        <p><strong>执行时间:</strong> {r['execution_time']}</p>
                        <p><strong>时间戳:</strong> {r['timestamp']}</p>
                        {details_html}
                        {f"<p class='error'><strong>错误:</strong> {r['error_message']}</p>" if r['error_message'] else ""}
                    </div>
                    """
                
                html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{report_data['report_title']}</title>
    <style>
        body {{font-family: 'Microsoft YaHei', Arial, sans-serif; margin: 20px; background: #f5f5f5;}}
        .container {{max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);}}
        h1 {{color: #333; text-align: center; margin-bottom: 30px;}}
        .summary {{background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin-bottom: 30px;}}
        .summary h2 {{margin-top: 0; color: white;}}
        .stats {{display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px;}}
        .stat {{background: rgba(255,255,255,0.2); padding: 15px; border-radius: 5px; text-align: center;}}
        .stat-number {{font-size: 2em; font-weight: bold; margin-bottom: 5px;}}
        .test-result {{padding: 20px; margin: 15px 0; border-radius: 8px; border-left: 5px solid;}}
        .success {{border-left-color: #4CAF50; background: #f1f8e9;}}
        .error {{border-left-color: #f44336; background: #ffebee;}}
        .details {{margin-top: 10px; padding: 10px; background: rgba(0,0,0,0.05); border-radius: 5px;}}
        .error {{color: #d32f2f; font-weight: bold;}}
        .recommendations {{background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 8px; margin-top: 30px;}}
        .recommendations h2 {{color: #856404; margin-top: 0;}}
        .recommendations ul {{color: #856404;}}
    </style>
</head>
<body>
    <div class="container">
        <h1>{report_data['report_title']}</h1>
        <p style="text-align: center; color: #666;">生成时间: {report_data['generated_at']}</p>
        
        <div class="summary">
            <h2>测试摘要</h2>
            <div class="stats">
                <div class="stat">
                    <div class="stat-number">{report_data['summary']['total_tests']}</div>
                    <div>总测试数</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{report_data['summary']['passed_tests']}</div>
                    <div>通过测试</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{report_data['summary']['failed_tests']}</div>
                    <div>失败测试</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{report_data['summary']['success_rate']}%</div>
                    <div>成功率</div>
                </div>
            </div>
        </div>
        
        <h2>详细测试结果</h2>
        {results_html}
        
        <div class="recommendations">
            <h2>改进建议</h2>
            <ul>
                {''.join([f'<li>{rec}</li>' for rec in report_data['recommendations']])}
            </ul>
        </div>
    </div>
</body>
</html>
                """
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(html)
            
            print(f"✅ 报告已保存: {filename}")
            print(f"📊 报告摘要:")
            print(f"  总测试数: {report_data['summary']['total_tests']}")
            print(f"  通过: {report_data['summary']['passed_tests']} ✅")
            print(f"  失败: {report_data['summary']['failed_tests']} ❌")
            print(f"  成功率: {report_data['summary']['success_rate']}%")
            
        elif args.action == 'web':
            print("🌐 启动Web界面...")
            print("访问地址: http://localhost:5001/test")
            os.system("cd bigscreen && python app.py")
            
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保在正确的目录中运行此脚本")
    except Exception as e:
        print(f"❌ 执行失败: {e}")

def generate_recommendations(test_results):
    """生成改进建议"""
    recommendations = []
    
    if not test_results:
        recommendations.append("暂无测试结果，建议先运行测试")
        return recommendations
    
    total = len(test_results)
    passed = len([r for r in test_results if r.status == 'PASS'])
    failed = len([r for r in test_results if r.status in ['FAIL', 'ERROR']])
    success_rate = (passed / total * 100) if total > 0 else 0
    
    if success_rate < 80:
        recommendations.append("测试成功率偏低，建议检查失败用例的根本原因")
    
    if failed > 0:
        recommendations.append(f"存在{failed}个失败测试，建议优先修复这些问题")
    
    # 分析具体失败原因
    error_messages = [r.error_message for r in test_results if r.error_message]
    if error_messages:
        if any("数据库" in msg for msg in error_messages):
            recommendations.append("检测到数据库相关错误，建议检查数据库连接和配置")
        if any("API" in msg or "请求" in msg for msg in error_messages):
            recommendations.append("检测到API请求相关错误，建议检查服务状态和网络连接")
        if any("超时" in msg for msg in error_messages):
            recommendations.append("检测到超时错误，建议优化性能或增加超时时间")
    
    if total < 5:
        recommendations.append("测试覆盖率不足，建议增加更多测试用例")
    
    if success_rate == 100:
        recommendations.append("所有测试通过！建议定期运行测试以确保持续稳定")
    
    return recommendations

if __name__ == "__main__":
    main() 
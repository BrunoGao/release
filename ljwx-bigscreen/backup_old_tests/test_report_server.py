#!/usr/bin/env python3
"""测试报告Web服务器"""
from flask import Flask, render_template_string, jsonify, request, send_file
import json,threading,time
from datetime import datetime
from pathlib import Path
from universal_test_manager import test_manager

app = Flask(__name__)

def get_available_tests():
    """获取可用测试列表"""
    return test_manager.get_test_cases()

def load_html_template():
    """加载HTML模板"""
    template_path = Path(__file__).parent / 'templates' / 'test_report.html'
    if template_path.exists():
        return template_path.read_text(encoding='utf-8')
    else:
        # 内嵌简化版模板
        return """
<!DOCTYPE html>
<html>
<head>
    <title>ljwx测试报告</title>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; text-align: center; }
        .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 20px; }
        .stat-card { background: white; padding: 20px; border-radius: 10px; text-align: center; }
        .stat-number { font-size: 2em; font-weight: bold; margin-bottom: 10px; }
        .controls { background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; text-align: center; }
        .btn { padding: 10px 20px; margin: 5px; border: none; border-radius: 5px; cursor: pointer; }
        .btn-primary { background: #007bff; color: white; }
        .results { background: white; padding: 20px; border-radius: 10px; }
        .test-item { padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 5px solid; }
        .success { border-left-color: #28a745; background: #d4edda; }
        .error { border-left-color: #dc3545; background: #f8d7da; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>ljwx接口自动化测试报告</h1>
            <p>upload_common_event 接口完整性验证</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number" id="total-tests">0</div>
                <div>总测试数</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color: #28a745;" id="passed-tests">0</div>
                <div>通过测试</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color: #dc3545;" id="failed-tests">0</div>
                <div>失败测试</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color: #ffc107;" id="success-rate">0%</div>
                <div>成功率</div>
            </div>
        </div>
        
        <div class="controls">
            <button class="btn btn-primary" onclick="runTest()">运行测试</button>
            <button class="btn btn-primary" onclick="refreshReport()">刷新报告</button>
        </div>
        
        <div class="results">
            <h2>测试结果</h2>
            <div id="test-results">
                <p>点击"运行测试"开始测试</p>
            </div>
        </div>
    </div>
    
    <script>
        async function runTest() {
            const response = await fetch('/api/test/run', { method: 'POST' });
            const data = await response.json();
            if (data.success) {
                setTimeout(refreshReport, 2000);
            }
        }
        
        async function refreshReport() {
            const response = await fetch('/api/test/results');
            const data = await response.json();
            if (data.success) {
                updateResults(data.data);
            }
        }
        
        function updateResults(data) {
            const results = data.test_results || [];
            const total = results.length;
            const passed = results.filter(r => r.status === 'PASS').length;
            const failed = total - passed;
            const rate = total > 0 ? Math.round((passed / total) * 100) : 0;
            
            document.getElementById('total-tests').textContent = total;
            document.getElementById('passed-tests').textContent = passed;
            document.getElementById('failed-tests').textContent = failed;
            document.getElementById('success-rate').textContent = rate + '%';
            
            const html = results.map(r => `
                <div class="test-item ${r.status === 'PASS' ? 'success' : 'error'}">
                    <strong>${r.name}</strong> - ${r.status}
                    <br><small>事件类型: ${r.event_type}</small>
                </div>
            `).join('');
            
            document.getElementById('test-results').innerHTML = html || '<p>暂无测试结果</p>';
        }
        
        // 页面加载时刷新
        document.addEventListener('DOMContentLoaded', refreshReport);
    </script>
</body>
</html>
        """

@app.route('/')
def index():
    """主页重定向"""
    from flask import redirect
    return redirect('/test/upload_common_event.html')

@app.route('/test/upload_common_event.html')
def upload_common_event_report():
    """upload_common_event测试报告页面"""
    template = load_html_template()
    return render_template_string(template)

@app.route('/test/report.html')
def general_report():
    """通用测试报告页面"""
    template = load_html_template()
    return render_template_string(template)

@app.route('/api/test/run', methods=['POST'])
def run_test():
    """运行测试API"""
    try:
        data = request.get_json() or {}
        test_name = data.get('test_name', 'upload_common_event')
        
        # 在后台线程运行测试
        thread = threading.Thread(target=lambda: test_manager.run_test(test_name))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "success": True,
            "message": f"测试 {test_name} 已开始执行",
            "test_name": test_name
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"启动测试失败: {str(e)}"
        })

@app.route('/api/test/run_all', methods=['POST'])
def run_all_tests():
    """运行所有测试API"""
    try:
        # 在后台线程运行所有测试
        thread = threading.Thread(target=test_manager.run_all_tests)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "success": True,
            "message": "所有测试已开始执行"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"启动测试失败: {str(e)}"
        })

@app.route('/api/test/results')
def get_test_results():
    """获取测试结果API"""
    try:
        return jsonify({
            "success": True,
            "data": test_manager.get_test_results()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"获取结果失败: {str(e)}"
        })

@app.route('/api/test/history')
def get_test_history():
    """获取测试历史API"""
    try:
        return jsonify({
            "success": True,
            "data": test_manager.get_test_history()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"获取历史失败: {str(e)}"
        })

@app.route('/api/test/download_report')
def download_report():
    """下载测试报告API"""
    try:
        # 生成测试报告
        report_data = test_manager.generate_report()
        
        # 保存到临时文件
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        return send_file(report_file, as_attachment=True, download_name=report_file)
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"生成报告失败: {str(e)}"
        })

@app.route('/api/test/cases')
def get_test_cases():
    """获取所有测试用例API"""
    try:
        cases = get_available_tests()
        return jsonify({
            "success": True,
            "data": {
                test_id: {
                    "name": case.name,
                    "description": case.description,
                    "event_types": case.event_types,
                    "timeout": case.timeout
                }
                for test_id, case in cases.items()
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"获取测试用例失败: {str(e)}"
        })

@app.route('/api/test/add_case', methods=['POST'])
def add_test_case():
    """添加测试用例API"""
    try:
        data = request.get_json()
        test_id = data.get('test_id')
        test_config = data.get('config')
        
        test_manager.add_test_case(test_id, test_config)
        
        return jsonify({
            "success": True,
            "message": f"测试用例 {test_id} 添加成功"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"添加测试用例失败: {str(e)}"
        })

if __name__ == '__main__':
    print("🚀 启动ljwx测试报告服务器...")
    print("📊 访问地址: http://localhost:5002/test/upload_common_event.html")
    print("🔧 API地址: http://localhost:5002/api/test/")
    
    app.run(host='0.0.0.0', port=5002, debug=True) 
#!/usr/bin/env python3
"""统一Web测试服务器 - 集成到主应用的测试模块"""
from flask import Blueprint, jsonify, request, render_template_string
import json,threading,time
from datetime import datetime
from pathlib import Path
from ..core.test_manager import test_manager

# 创建测试蓝图，集成到主应用
test_bp = Blueprint('test', __name__, url_prefix='/api/test')

def create_test_routes(app):
    """将测试路由集成到主应用"""
    
    @app.route('/test')
    @app.route('/test/')
    def test_dashboard():
        """测试仪表板"""
        return render_template_string(get_dashboard_template())
    
    @test_bp.route('/run', methods=['POST'])
    def run_test():
        """运行单个测试"""
        try:
            data = request.get_json() or {}
            test_name = data.get('test_name', 'upload_common_event')
            
            # 后台运行测试
            thread = threading.Thread(target=lambda: test_manager.run_test(test_name))
            thread.daemon = True
            thread.start()
            
            return jsonify({
                "success": True,
                "message": f"测试 {test_name} 已开始执行",
                "test_name": test_name
            })
        except Exception as e:
            return jsonify({"success": False, "message": f"启动测试失败: {str(e)}"})
    
    @test_bp.route('/run_all', methods=['POST'])
    def run_all_tests():
        """运行所有测试"""
        try:
            parallel = request.get_json().get('parallel', True) if request.get_json() else True
            thread = threading.Thread(target=lambda: test_manager.run_all_tests(parallel))
            thread.daemon = True
            thread.start()
            
            return jsonify({"success": True, "message": "所有测试已开始执行"})
        except Exception as e:
            return jsonify({"success": False, "message": f"启动测试失败: {str(e)}"})
    
    @test_bp.route('/results')
    def get_test_results():
        """获取测试结果"""
        try:
            return jsonify({"success": True, "data": test_manager.get_test_results()})
        except Exception as e:
            return jsonify({"success": False, "message": f"获取结果失败: {str(e)}"})
    
    @test_bp.route('/cases')
    def get_test_cases():
        """获取测试用例"""
        try:
            return jsonify({"success": True, "data": test_manager.get_available_tests()})
        except Exception as e:
            return jsonify({"success": False, "message": f"获取测试用例失败: {str(e)}"})
    
    @test_bp.route('/history')
    def get_test_history():
        """获取测试历史"""
        try:
            return jsonify({"success": True, "data": test_manager.get_test_history()})
        except Exception as e:
            return jsonify({"success": False, "message": f"获取历史失败: {str(e)}"})
    
    @test_bp.route('/report')
    def download_report():
        """生成测试报告"""
        try:
            report = test_manager.generate_report()
            return jsonify({"success": True, "data": report})
        except Exception as e:
            return jsonify({"success": False, "message": f"生成报告失败: {str(e)}"})
    
    # 注册蓝图
    app.register_blueprint(test_bp)

def get_dashboard_template():
    """获取测试仪表板模板"""
    return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ljwx自动化测试仪表板</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Microsoft YaHei', Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; color: white; margin-bottom: 30px; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: white; border-radius: 15px; padding: 25px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.2); transition: transform 0.3s; }
        .stat-card:hover { transform: translateY(-5px); }
        .stat-number { font-size: 2.5em; font-weight: bold; margin-bottom: 10px; }
        .stat-label { color: #666; font-size: 1.1em; }
        .controls { background: white; border-radius: 15px; padding: 25px; margin-bottom: 30px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .btn { background: linear-gradient(45deg, #667eea, #764ba2); color: white; border: none; padding: 12px 25px; margin: 8px; border-radius: 25px; cursor: pointer; font-size: 1em; transition: all 0.3s; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.3); }
        .btn:disabled { opacity: 0.6; cursor: not-allowed; }
        .results { background: white; border-radius: 15px; padding: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .test-item { padding: 15px; margin: 10px 0; border-radius: 10px; border-left: 5px solid; transition: all 0.3s; }
        .test-item:hover { transform: translateX(5px); }
        .success { border-left-color: #28a745; background: linear-gradient(90deg, #d4edda, #f8fff8); }
        .fail { border-left-color: #dc3545; background: linear-gradient(90deg, #f8d7da, #fff8f8); }
        .error { border-left-color: #ffc107; background: linear-gradient(90deg, #fff3cd, #fffef8); }
        .loading { text-align: center; color: #666; padding: 20px; }
        .test-details { margin-top: 10px; font-size: 0.9em; color: #666; }
        .status-badge { display: inline-block; padding: 4px 12px; border-radius: 12px; color: white; font-size: 0.8em; margin-left: 10px; }
        .status-pass { background: #28a745; }
        .status-fail { background: #dc3545; }
        .status-error { background: #ffc107; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 ljwx自动化测试仪表板</h1>
            <p>统一、可维护、可扩展的测试系统</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number" style="color: #667eea;" id="total-tests">0</div>
                <div class="stat-label">总测试数</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color: #28a745;" id="passed-tests">0</div>
                <div class="stat-label">通过测试</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color: #dc3545;" id="failed-tests">0</div>
                <div class="stat-label">失败测试</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color: #ffc107;" id="success-rate">0%</div>
                <div class="stat-label">成功率</div>
            </div>
        </div>
        
        <div class="controls">
            <h3 style="margin-bottom: 20px;">测试控制面板</h3>
            <button class="btn" onclick="runSingleTest('upload_common_event')">通用事件测试</button>
            <button class="btn" onclick="runSingleTest('upload_health_data')">健康数据测试</button>
            <button class="btn" onclick="runSingleTest('upload_device_info')">设备信息测试</button>
            <button class="btn" onclick="runAllTests()">运行所有测试</button>
            <button class="btn" onclick="refreshResults()">刷新结果</button>
            <button class="btn" onclick="downloadReport()">下载报告</button>
        </div>
        
        <div class="results">
            <h3>测试结果</h3>
            <div id="test-results">
                <div class="loading">点击上方按钮开始测试...</div>
            </div>
        </div>
    </div>
    
    <script>
        let isRunning = false;
        
        async function runSingleTest(testName) {
            if (isRunning) return;
            isRunning = true;
            updateButtons(true);
            
            try {
                const response = await fetch('/api/test/run', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({test_name: testName})
                });
                const data = await response.json();
                
                if (data.success) {
                    showMessage('测试已开始，请稍候...', 'info');
                    setTimeout(() => refreshResults(), 3000);
                } else {
                    showMessage('启动测试失败: ' + data.message, 'error');
                }
            } catch (error) {
                showMessage('请求失败: ' + error.message, 'error');
            } finally {
                setTimeout(() => { isRunning = false; updateButtons(false); }, 5000);
            }
        }
        
        async function runAllTests() {
            if (isRunning) return;
            isRunning = true;
            updateButtons(true);
            
            try {
                const response = await fetch('/api/test/run_all', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({parallel: true})
                });
                const data = await response.json();
                
                if (data.success) {
                    showMessage('所有测试已开始，请稍候...', 'info');
                    setTimeout(() => refreshResults(), 5000);
                } else {
                    showMessage('启动测试失败: ' + data.message, 'error');
                }
            } catch (error) {
                showMessage('请求失败: ' + error.message, 'error');
            } finally {
                setTimeout(() => { isRunning = false; updateButtons(false); }, 10000);
            }
        }
        
        async function refreshResults() {
            try {
                const response = await fetch('/api/test/results');
                const data = await response.json();
                
                if (data.success) {
                    updateDashboard(data.data);
                } else {
                    showMessage('获取结果失败: ' + data.message, 'error');
                }
            } catch (error) {
                showMessage('请求失败: ' + error.message, 'error');
            }
        }
        
        async function downloadReport() {
            try {
                const response = await fetch('/api/test/report');
                const data = await response.json();
                
                if (data.success) {
                    const blob = new Blob([JSON.stringify(data.data, null, 2)], {type: 'application/json'});
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `test_report_${new Date().toISOString().slice(0,19).replace(/:/g,'-')}.json`;
                    a.click();
                    URL.revokeObjectURL(url);
                    showMessage('报告下载成功', 'success');
                } else {
                    showMessage('生成报告失败: ' + data.message, 'error');
                }
            } catch (error) {
                showMessage('请求失败: ' + error.message, 'error');
            }
        }
        
        function updateDashboard(data) {
            const summary = data.summary || {};
            document.getElementById('total-tests').textContent = summary.total_tests || 0;
            document.getElementById('passed-tests').textContent = summary.passed_tests || 0;
            document.getElementById('failed-tests').textContent = summary.failed_tests || 0;
            document.getElementById('success-rate').textContent = (summary.success_rate || 0) + '%';
            
            const results = data.test_results || [];
            const html = results.map(r => {
                const statusClass = r.status === 'PASS' ? 'success' : (r.status === 'FAIL' ? 'fail' : 'error');
                const badgeClass = r.status === 'PASS' ? 'status-pass' : (r.status === 'FAIL' ? 'status-fail' : 'status-error');
                
                let detailsHtml = '';
                if (r.details) {
                    const details = Object.entries(r.details)
                        .filter(([key, value]) => typeof value === 'boolean')
                        .map(([key, value]) => `${key}: ${value ? '✅' : '❌'}`)
                        .join(' | ');
                    if (details) detailsHtml = `<div class="test-details">${details}</div>`;
                }
                
                return `
                    <div class="test-item ${statusClass}">
                        <strong>${r.test_name}</strong>
                        <span class="status-badge ${badgeClass}">${r.status}</span>
                        <div style="margin-top: 5px;">
                            <small>执行时间: ${r.execution_time} | 时间: ${new Date(r.timestamp).toLocaleString()}</small>
                        </div>
                        ${detailsHtml}
                        ${r.error_message ? `<div style="color: #dc3545; margin-top: 5px;"><small>错误: ${r.error_message}</small></div>` : ''}
                    </div>
                `;
            }).join('');
            
            document.getElementById('test-results').innerHTML = html || '<div class="loading">暂无测试结果</div>';
        }
        
        function updateButtons(disabled) {
            const buttons = document.querySelectorAll('.btn');
            buttons.forEach(btn => btn.disabled = disabled);
        }
        
        function showMessage(message, type) {
            const colors = {info: '#17a2b8', success: '#28a745', error: '#dc3545'};
            const div = document.createElement('div');
            div.style.cssText = `position: fixed; top: 20px; right: 20px; background: ${colors[type]}; color: white; padding: 15px 20px; border-radius: 5px; z-index: 1000; box-shadow: 0 5px 15px rgba(0,0,0,0.3);`;
            div.textContent = message;
            document.body.appendChild(div);
            setTimeout(() => div.remove(), 3000);
        }
        
        // 页面加载时刷新数据
        document.addEventListener('DOMContentLoaded', refreshResults);
        
        // 定期刷新
        setInterval(refreshResults, 30000);
    </script>
</body>
</html>
    """ 
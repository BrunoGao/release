#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
前端调试脚本 - 检查健康数据分析页面的问题
"""

import requests
import json
import time

def test_frontend_access():
    """测试前端页面访问"""
    print("=== 测试前端页面访问 ===")
    
    base_url = "http://localhost:5001"
    
    # 测试主要页面
    pages = [
        "/user_health_data_analysis?customerId=1",
        "/get_all_health_data_by_orgIdAndUserId?orgId=1&startDate=2025-05-28&endDate=2025-06-03"
    ]
    
    for page in pages:
        url = base_url + page
        try:
            print(f"\n测试页面: {page}")
            response = requests.get(url, timeout=10)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                if page.endswith('.html') or 'user_health_data_analysis' in page:
                    print(f"页面大小: {len(response.text)} 字符")
                    # 检查关键元素
                    if 'echarts' in response.text.lower():
                        print("✓ ECharts已引入")
                    else:
                        print("✗ ECharts未引入")
                        
                    if 'initCharts' in response.text:
                        print("✓ initCharts函数存在")
                    else:
                        print("✗ initCharts函数不存在")
                        
                    if 'fetchData' in response.text:
                        print("✓ fetchData函数存在")
                    else:
                        print("✗ fetchData函数不存在")
                else:
                    # API响应
                    try:
                        data = response.json()
                        print(f"API响应成功: {data.get('success')}")
                        if data.get('data'):
                            print(f"数据字段: {list(data['data'].keys())}")
                    except:
                        print("非JSON响应")
            else:
                print(f"请求失败: {response.status_code}")
                
        except Exception as e:
            print(f"请求异常: {e}")

def generate_debug_html():
    """生成调试版本的HTML页面"""
    print("\n=== 生成调试版本HTML ===")
    
    debug_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>健康数据分析 - 调试版</title>
    <script src="{{ url_for('static', filename='js/echarts.min.js') }}"></script>
    <style>
        body { margin: 0; padding: 20px; background: #001529; color: #fff; font-family: Arial, sans-serif; }
        .debug-panel { background: rgba(0,15,29,0.9); border: 1px solid #00f0ff; border-radius: 8px; padding: 20px; margin: 20px 0; }
        .chart-container { width: 100%; height: 400px; background: rgba(0,15,29,0.8); border: 1px solid rgba(0,240,255,0.2); margin: 10px 0; }
        .status { padding: 10px; margin: 5px 0; border-radius: 4px; }
        .status.success { background: rgba(46,213,115,0.2); border: 1px solid #2ed573; }
        .status.error { background: rgba(255,71,87,0.2); border: 1px solid #ff4757; }
        .status.info { background: rgba(0,240,255,0.2); border: 1px solid #00f0ff; }
    </style>
</head>
<body>
    <h1>健康数据分析 - 调试版</h1>
    
    <div class="debug-panel">
        <h3>系统检查</h3>
        <div id="systemStatus"></div>
    </div>
    
    <div class="debug-panel">
        <h3>图表容器</h3>
        <div class="chart-container" id="healthScoreChart"></div>
        <div class="chart-container" id="timeSeriesChart"></div>
    </div>
    
    <div class="debug-panel">
        <h3>调试日志</h3>
        <div id="debugLog" style="background: #000; color: #0f0; padding: 10px; font-family: monospace; height: 200px; overflow-y: auto;"></div>
    </div>

    <script>
        // 重写console.log，同时显示在页面上
        const originalLog = console.log;
        const originalError = console.error;
        const originalWarn = console.warn;
        
        function addLogEntry(message, type = 'log') {
            const debugLog = document.getElementById('debugLog');
            const time = new Date().toLocaleTimeString();
            const entry = document.createElement('div');
            entry.style.color = type === 'error' ? '#ff4757' : type === 'warn' ? '#ffa502' : '#0f0';
            entry.textContent = `[${time}] ${type.toUpperCase()}: ${message}`;
            debugLog.appendChild(entry);
            debugLog.scrollTop = debugLog.scrollHeight;
        }
        
        console.log = function(...args) {
            originalLog.apply(console, args);
            addLogEntry(args.join(' '), 'log');
        };
        
        console.error = function(...args) {
            originalError.apply(console, args);
            addLogEntry(args.join(' '), 'error');
        };
        
        console.warn = function(...args) {
            originalWarn.apply(console, args);
            addLogEntry(args.join(' '), 'warn');
        };

        // 系统检查
        function systemCheck() {
            const statusDiv = document.getElementById('systemStatus');
            let html = '';
            
            // 检查ECharts
            if (typeof echarts !== 'undefined') {
                html += '<div class="status success">✓ ECharts已加载</div>';
                console.log('ECharts版本:', echarts.version);
            } else {
                html += '<div class="status error">✗ ECharts未加载</div>';
                console.error('ECharts未加载');
            }
            
            // 检查图表容器
            const containers = ['healthScoreChart', 'timeSeriesChart'];
            containers.forEach(id => {
                const container = document.getElementById(id);
                if (container) {
                    html += `<div class="status success">✓ 图表容器 ${id} 存在</div>`;
                    console.log(`图表容器 ${id} 尺寸:`, container.offsetWidth, 'x', container.offsetHeight);
                } else {
                    html += `<div class="status error">✗ 图表容器 ${id} 不存在</div>`;
                    console.error(`图表容器 ${id} 不存在`);
                }
            });
            
            statusDiv.innerHTML = html;
        }
        
        // 图表初始化测试
        function testChartInit() {
            console.log('开始测试图表初始化...');
            
            if (typeof echarts === 'undefined') {
                console.error('ECharts未加载，无法测试');
                return;
            }
            
            try {
                const healthChart = echarts.init(document.getElementById('healthScoreChart'));
                healthChart.setOption({
                    title: { text: '健康评分测试', textStyle: { color: '#fff' } },
                    series: [{
                        type: 'gauge',
                        data: [{ value: 75, name: '测试分数' }]
                    }]
                });
                console.log('健康评分图表初始化成功');
                
                const timeChart = echarts.init(document.getElementById('timeSeriesChart'));
                timeChart.setOption({
                    title: { text: '时间序列测试', textStyle: { color: '#fff' } },
                    xAxis: { type: 'category', data: ['Mon', 'Tue', 'Wed'] },
                    yAxis: { type: 'value' },
                    series: [{ type: 'line', data: [120, 200, 150] }]
                });
                console.log('时间序列图表初始化成功');
                
            } catch (error) {
                console.error('图表初始化失败:', error);
            }
        }
        
        // API测试
        async function testAPI() {
            console.log('开始测试API...');
            
            try {
                const url = './get_all_health_data_by_orgIdAndUserId?orgId=1&startDate=2025-05-28&endDate=2025-06-03';
                console.log('请求URL:', url);
                
                const response = await fetch(url);
                console.log('响应状态:', response.status);
                
                if (response.ok) {
                    const data = await response.json();
                    console.log('API响应成功:', data.success);
                    console.log('数据字段:', data.data ? Object.keys(data.data) : 'null');
                    
                    if (data.data && data.data.healthScores) {
                        console.log('健康评分数据存在');
                    }
                    if (data.data && data.data.timeSeriesData) {
                        console.log('时间序列数据存在');
                    }
                } else {
                    console.error('API请求失败:', response.status);
                }
                
            } catch (error) {
                console.error('API测试失败:', error);
            }
        }
        
        // 页面加载完成后执行测试
        document.addEventListener('DOMContentLoaded', function() {
            console.log('页面加载完成，开始调试检查...');
            
            systemCheck();
            
            setTimeout(() => {
                testChartInit();
            }, 100);
            
            setTimeout(() => {
                testAPI();
            }, 500);
        });
    </script>
</body>
</html>
    """
    
    # 保存调试HTML文件
    debug_file = 'bigScreen/templates/health_debug.html'
    try:
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(debug_html)
        print(f"调试页面已生成: {debug_file}")
        print("访问地址: http://localhost:5001/health_debug")
    except Exception as e:
        print(f"生成调试页面失败: {e}")

if __name__ == "__main__":
    test_frontend_access()
    generate_debug_html() 
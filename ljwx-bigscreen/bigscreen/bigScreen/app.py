from flask import request, jsonify, render_template
from .user_health_data import fetch_all_health_data_by_orgIdAndUserId
from .bigScreen import app
import json
import math

def sanitize_for_json(obj):
    """递归清理对象中的NaN和Infinity值，使其JSON兼容"""
    if isinstance(obj, dict):
        return {key: sanitize_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return 0
        return obj
    else:
        return obj

@app.route('/user_health_data_analyze')
def user_health_data_analyze():
    return render_template('user_health_data_analyze.html')

@app.route('/user_health_data_analysis')
def user_health_data_analysis():
    # 创建默认的健康状态数据
    default_health_status = {
        'score': 0,
        'level': '暂无数据',
        'summary': '请选择日期范围查看健康分析',
        'insights': []
    }
    
    return render_template('user_health_data_analysis.html', health_status=default_health_status)

@app.route('/get_all_health_data_by_orgIdAndUserId')
def get_all_health_data():
    try:
        org_id = request.args.get('orgId')
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        
        print(f"🔍 API接收参数: orgId={org_id}, startDate={start_date}, endDate={end_date}")
        
        # 获取健康数据分析结果（已经包含完整分析）
        result = fetch_all_health_data_by_orgIdAndUserId(org_id, start_date, end_date)
        
        # 清理NaN值以确保JSON兼容
        sanitized_result = sanitize_for_json(result)
        
        return jsonify(sanitized_result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }) 
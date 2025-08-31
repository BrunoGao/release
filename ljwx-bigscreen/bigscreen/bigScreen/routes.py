from flask import jsonify, render_template, request, Response
from .models import UserInfo, UserOrg, OrgInfo, DeviceInfo
from .redis_helper import RedisHelper
from .knowledge_base import KnowledgeBase
from .alert_v2_service import get_alerts_by_conditions, acknowledge_alert_by_id, generate_alert_statistics
from . import app
import json
import os
from datetime import datetime

redis = RedisHelper()
kb = KnowledgeBase()

# 知识库相关路由
@app.route('/api/upload_knowledge', methods=['POST'])
def upload_knowledge():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    file.save(file_path)
    
    try:
        chunks_count = kb.add_single_file(file_path)
        return jsonify({
            "message": f"Successfully added document to knowledge base. Created {chunks_count} chunks."
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 告警系统V2 API路由
@app.route('/api/v2/alert/realtime', methods=['GET'])
def get_realtime_alerts():
    """获取实时告警数据"""
    try:
        customer_id = request.args.get('customerId')
        status = request.args.get('status')
        level = request.args.get('level')
        
        if not customer_id:
            return jsonify({"error": "customerId参数是必需的"}), 400
        
        # 构建查询条件
        conditions = {"customer_id": customer_id, "is_deleted": 0}
        if status:
            conditions["status"] = status
        if level:
            conditions["level"] = level
            
        alerts = get_alerts_by_conditions(conditions, limit=50)
        
        return jsonify({
            "success": True,
            "data": alerts,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/v2/alert/acknowledge', methods=['POST'])
def acknowledge_alert_v2():
    """确认告警"""
    try:
        data = request.get_json()
        alert_id = data.get('alertId')
        user_id = data.get('userId')
        
        if not alert_id:
            return jsonify({"error": "alertId参数是必需的"}), 400
            
        success = acknowledge_alert_by_id(alert_id, user_id)
        
        return jsonify({
            "success": success,
            "message": "告警确认成功" if success else "告警确认失败"
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/v2/alert/statistics', methods=['GET'])
def get_alert_statistics_v2():
    """获取告警统计数据"""
    try:
        customer_id = request.args.get('customerId')
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        
        if not customer_id:
            return jsonify({"error": "customerId参数是必需的"}), 400
            
        stats = generate_alert_statistics(customer_id, start_date, end_date)
        
        return jsonify({
            "success": True,
            "data": stats
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/query_knowledge', methods=['POST'])
def query_knowledge():
    data = request.get_json()
    query = data.get('query')
    
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    try:
        results = kb.search(query)
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/chat')
def chat_page():
    return render_template('chat.html')

@app.route('/api/health/stats')
def get_health_stats():
    dimension = request.args.get('dimension', 'day')
    org_id = request.args.get('orgId')
    user_id = request.args.get('userId')
    return jsonify(fetch_health_stats_by_dimension(org_id, user_id, dimension)) 
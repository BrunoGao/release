from flask import jsonify, render_template, request, Response
from .models import UserInfo, UserOrg, OrgInfo, DeviceInfo
from .redis_helper import RedisHelper
from .knowledge_base import KnowledgeBase
from . import app
import json
import os

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
from flask import Blueprint, render_template, request, jsonify
from .realtime_stats_api import realtime_stats_bp

main_bp = Blueprint('main', __name__)

@main_bp.route('/main')
def main_dashboard():
    """大屏主页面"""
    customer_id = request.args.get('customerId', '1939964806110937090')
    return render_template('main_dashboard.html', customer_id=customer_id)

@main_bp.route('/')
def index():
    """首页重定向到主页面"""
    return main_dashboard()
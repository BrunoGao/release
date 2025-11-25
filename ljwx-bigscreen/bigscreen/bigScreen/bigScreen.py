# =============================================================================
# bigScreen.py - 健康监控大屏系统主应用
# 功能模块化组织：org、user、device、alert、message、health_data
# =============================================================================

from random import uniform
from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
from flask import request, jsonify
from datetime import datetime, timedelta
import json
from .device import gather_device_info as device_gather_device_info, upload_device_info, fetch_devices_by_customer_id as device_fetch_devices_by_customer_id, fetch_device_info as device_fetch_device_info, generate_device_stats as device_generate_device_stats, fetch_devices_by_orgIdAndUserId, fetch_customer_id_by_deviceSn
from .user_health_data import generate_health_json as user_generate_health_json, upload_health_data, fetch_health_data as user_fetch_health_data, get_health_data as user_get_health_data, fetch_user_locations as user_fetch_user_locations, fetch_health_data_by_id as user_fetch_health_data_by_id, fetch_health_data_by_orgIdAndUserId, fetch_health_stats_by_dimension, get_health_data_by_date as user_get_health_data_by_date, fetch_all_health_data_by_orgIdAndUserId, fetch_health_profile_by_orgIdAndUserId, get_page_health_data_by_orgIdAndUserId, get_all_health_data_optimized
from .system_event_alert import get_processor
from .alert import fetch_alerts as alert_fetch_alerts, upload_alerts as alert_upload_alerts, upload_common_event as alert_upload_common_event
from .alert import test_wechat_alert as alert_test_wechat_alert, generate_alert_json as alert_generate_alert_json, gather_deal_alert as alert_gather_deal_alert
from .alert import generate_alert_chart as alert_generate_alert_chart, deal_alert as alert_deal_alert, generate_alert_stats as alert_generate_alert_stats, generate_alert_chart_by_type
from .alert import acknowledge_alert as alert_acknowledge_alert
from .alert import fetch_alerts_by_orgIdAndUserId as alert_fetch_alerts_by_orgIdAndUserId
from .message import fetch_messages as message_fetch_messages, send_message as message_send_message, received_messages as message_received_messages, generate_message_stats as message_generate_message_stats, fetch_messages_by_orgIdAndUserId as message_fetch_messages_by_orgIdAndUserId
from .user import get_user_info as user_get_user_info, get_all_users as user_get_all_users, get_user_deviceSn as user_get_user_deviceSn, get_user_id as user_get_user_id
from .org import fetch_departments_by_orgId, fetch_departments, fetch_users_stats_by_orgId
from .org import fetch_users_by_orgId
from .util import check_license as util_check_license
from .fetchConfig import copy_health_data_config as fetch_config_copy_health_data_config, fetch_health_data_config as fetch_config_fetch_health_data_config, config_bp
from .wechat import send_message as wechat_send_message
from .user import get_user_info_by_orgIdAndUserId as user_get_user_info_by_orgIdAndUserId, fetch_device_info_by_phone
from .fetchConfig import get_interface_config as fetch_config_get_interface_config, get_health_config as fetch_config_get_health_config, get_customer_config as fetch_config_get_customer_config, get_optimal_config as fetch_config_get_optimal_config, save_interface_config as fetch_config_save_interface_config, save_health_config as fetch_config_save_health_config, save_customer_config as fetch_config_save_customer_config
from .user_health_data import get_health_trends, get_health_baseline, get_baseline_for_trend, get_basic_health_data_by_orgIdAndUserId
from .health_baseline import HealthBaselineQuery, generate_baseline_task
from .watch_log import upload_watch_log as watch_log_upload_watch_log, watch_logs_page as watch_log_watch_logs_page, get_watch_logs as watch_log_get_watch_logs, get_watch_log_stats as watch_log_get_watch_log_stats
from .health_profile import get_profile_monitor, manual_generate_profiles, get_health_profiles, get_profile_statistics
# from .weight_calculator import WeightCalculator  # 模块不存在，暂时注释
# from .health_baseline_manager import HealthBaselineManager  # 模块不存在，暂时注释
# from .recommendation_tracker import RecommendationTracker  # 模块不存在，暂时注释
# from .health_recommendation_engine import RealTimeHealthRecommendationEngine  # 模块不存在，暂时注释
# from .health_cache_integration import health_data_cache_integration, cache_health_data, cache_health_chart, cache_health_stats  # 模块不存在，暂时注释
from redis import Redis
# from .health_data_batch_processor import optimized_upload_health_data, save_health_data_fast, get_optimizer_stats  # 模块有依赖问题，暂时注释
# from .health_config_cache_listener import get_health_config_listener, get_enabled_metrics, get_listener_stats  # 模块不存在，暂时注释
# from .redis_stream_manager import get_stream_manager  # 模块不存在，暂时注释
# from .stream_consumers import get_consumer_manager  # 模块不存在，暂时注释
# from .stream_gradual_switch_manager import get_switch_manager, should_use_stream_processing  # 模块不存在，暂时注释
# from .stream_monitoring_dashboard import monitoring_bp  # 模块不存在，暂时注释
# from .stream_rollback_plan import get_rollback_plan  # 模块不存在，暂时注释
# from .statistics_module import get_realtime_stats_data, get_statistics_overview_data  # 模块不存在，暂时注释
from .message import save_device_message_data, send_device_message_data, receive_device_messages_data
from .device import get_device_analysis_data
# from .health_analysis import get_customer_comprehensive_analysis, get_health_trends_analysis_data  # 模块不存在，暂时注释
# from .license_manager import get_license_manager, license_required, check_device_license, get_license_dashboard_data  # 模块不存在，暂时注释
# V2消息系统已移除
V2_SYSTEM_AVAILABLE = False
import requests  # 用于发送HTTP请求
import json
import threading
import time
from .models import db, DeviceMessage, UserHealthData, AlertInfo, DeviceInfo, UserInfo, OrgInfo
from flask_socketio import SocketIO, emit
from decimal import Decimal
from sqlalchemy import func, and_
from .redis_helper import RedisHelper
import logging
import sys
import os
import random
from dotenv import load_dotenv
# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SQLALCHEMY_DATABASE_URI, REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD, APP_HOST, APP_PORT, DEBUG, BIGSCREEN_TITLE, COMPANY_NAME, COMPANY_LOGO_URL, THEME_COLOR, BACKGROUND_COLOR, FOOTER_TEXT, WECHAT_APP_ID, WECHAT_APP_SECRET, WECHAT_TEMPLATE_ID, WECHAT_USER_OPENID, WECHAT_API_URL, WECHAT_ALERT_ENABLED, PERSONAL_SCREEN_VERSION, BIGSCREEN_VERSION, SYSTEM_VERSION
# Load environment variables
load_dotenv()

# 配置日志 - 同时输出到控制台和文件
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # 输出到控制台
        logging.FileHandler('bigscreen.log'),  # 输出到文件
        logging.FileHandler('system.log')  # 系统日志文件
    ]
)

# 创建不同的日志记录器
api_logger = logging.getLogger('api')
system_logger = logging.getLogger('system')
query_logger = logging.getLogger('query')

# 导入消息功能
try:
    from .message import acknowledge_message, batch_acknowledge_messages, get_watch_message_summary, mark_message_as_read_on_watch
    MESSAGE_FEATURES_AVAILABLE = True
    system_logger.info("✅ 消息功能导入成功")
except ImportError as e:
    MESSAGE_FEATURES_AVAILABLE = False
    system_logger.warning(f"⚠️  消息功能导入失败: {e}")
    # 创建占位函数以避免运行时错误
    def acknowledge_message(data):
        return {'success': False, 'message': '功能不可用'}, 503
    def batch_acknowledge_messages(data):
        return {'success': False, 'message': '功能不可用'}, 503
    def get_watch_message_summary(device_sn):
        return {'success': False, 'message': '功能不可用'}
    def mark_message_as_read_on_watch(message_id, device_sn):
        return {'success': False, 'message': '功能不可用'}

app = Flask(__name__, static_folder='../static')
socketio = SocketIO(app, cors_allowed_origins="*")

# =============================================================================
# Prometheus监控集成
# =============================================================================
try:
    from .prometheus_metrics import (
        metrics_endpoint, init_app_info,
        record_health_data_upload, record_api_request,
        record_alert_generated, record_message_sent
    )

    # 注册/metrics端点
    @app.route('/metrics')
    def prometheus_metrics():
        return metrics_endpoint()

    # 初始化应用信息
    init_app_info(version=BIGSCREEN_VERSION, environment='production')
    system_logger.info("✅ Prometheus监控集成成功")
except Exception as e:
    system_logger.warning(f"⚠️  Prometheus监控集成失败: {e}")
    # 提供空实现避免错误
    def record_health_data_upload(*args, **kwargs): pass
    def record_api_request(*args, **kwargs): pass
    def record_alert_generated(*args, **kwargs): pass
    def record_message_sent(*args, **kwargs): pass

# =============================================================================
# 系统初始化和配置
# =============================================================================

def normalize_param(param_value):
    """将字符串'null'转换为None，其他值保持不变"""
    if param_value == 'null' or param_value == 'undefined':
        return None
    return param_value

app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# 注册蓝图
app.register_blueprint(config_bp, url_prefix='/api')

# 注册Stream监控仪表板蓝图
# app.register_blueprint(monitoring_bp)  # monitoring_bp未定义，暂时注释

# 注册健康系统API蓝图
# Temporarily disable health_api blueprint to use simplified route
try:
    from .health_api import health_api
    app.register_blueprint(health_api)
    system_logger.info("✅ 健康系统API模块加载成功")
except ImportError as e:
    system_logger.warning(f"⚠️  健康系统API模块加载失败: {e}")
except Exception as e:
    system_logger.error(f"❌ 健康系统API模块加载异常: {e}")

# 注册优化后的健康分析API蓝图 V2.0
try:
    from .health_analysis_api import health_analysis_api
    app.register_blueprint(health_analysis_api, url_prefix='/api/health/v2')
    system_logger.info("✅ 健康分析API V2.0模块加载成功")
except ImportError as e:
    system_logger.warning(f"⚠️  健康分析API V2.0模块加载失败: {e}")
except Exception as e:
    system_logger.error(f"❌ 健康分析API V2.0模块加载异常: {e}")

# V2消息系统已移除，使用V1消息系统
system_logger.info("✅ 使用V1消息系统")

# 实时统计API - 重构后使用模块化实现
@app.route('/api/realtime_stats', methods=['GET'])
def get_realtime_stats():
    """获取实时统计数据API - 支持日期对比"""
    result, status_code = get_realtime_stats_data()
    return jsonify(result), status_code

system_logger.info('实时统计API直接路由注册成功')

# =============================================================================
# API性能监控钩子
# =============================================================================
from flask import g
import time

@app.before_request
def before_request():
    """记录请求开始时间"""
    g.start_time = time.time()

@app.after_request
def after_request(response):
    """记录API请求性能指标"""
    if hasattr(g, 'start_time'):
        duration = time.time() - g.start_time

        # 只记录API请求，忽略静态文件
        if request.path.startswith('/api/') or request.path.startswith('/upload_'):
            try:
                record_api_request(
                    method=request.method,
                    endpoint=request.path,
                    status_code=response.status_code,
                    duration=duration
                )
            except Exception as e:
                # 静默失败，不影响正常请求
                pass

    return response

# 原来的实时统计蓝图导入已被上面的直接路由替代
# try:
#     from .realtime_stats_api import realtime_stats_bp
#     app.register_blueprint(realtime_stats_bp)
#     system_logger.info('实时统计API蓝图注册成功')
# except ImportError as e:
#     system_logger.warning(f'实时统计API蓝图导入失败: {e}')

# 主路由模块已删除，不再需要导入
# 主路由功能已集成到其他模块中

# 设备绑定模块已禁用
# try:
#     from .device_bind import device_bind_bp
#     app.register_blueprint(device_bind_bp)
#     system_logger.info('设备绑定模块注册成功')
# except ImportError as e:
#     system_logger.warning(f'设备绑定模块导入失败，使用兼容版本: {e}')
#     from .device_bind_compatible import device_bind_bp
#     app.register_blueprint(device_bind_bp)
#     system_logger.info('设备绑定兼容模块注册成功')
system_logger.info('设备绑定模块已禁用')

# 注册监控蓝图
try:
    import sys
    import os
    # 修正导入路径，指向上级目录的metrics模块
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from metrics import metrics_bp, start_metrics_collector
    app.register_blueprint(metrics_bp)
    start_metrics_collector()  # 启动后台指标收集器
    system_logger.info('监控指标模块初始化成功')
except ImportError as e:
    system_logger.warning(f'监控指标模块导入失败: {e}')
    system_logger.info(f'当前Python路径: {sys.path[:3]}')  # 显示前3个路径用于调试

# 注册告警webhook蓝图
try:
    from alert_webhook import alert_webhook_bp
    app.register_blueprint(alert_webhook_bp)
    system_logger.info('告警webhook模块初始化成功')
except ImportError as e:
    system_logger.warning(f'告警webhook模块导入失败: {e}')

CORS(app)

# 全局模板变量
@app.context_processor
def inject_global_vars():
    return {
        'BIGSCREEN_TITLE': BIGSCREEN_TITLE,
        'COMPANY_NAME': COMPANY_NAME,
        'COMPANY_LOGO_URL': COMPANY_LOGO_URL,
        'THEME_COLOR': THEME_COLOR,
        'BACKGROUND_COLOR': BACKGROUND_COLOR,
        'FOOTER_TEXT': FOOTER_TEXT
    }

# Configure logging
from logging_config import api_logger,health_logger,device_logger,db_logger,log_api_request,log_data_processing,system_logger,alert_logger #添加system_logger和alert_logger导入

# 初始化logger
logger = api_logger  # 使用API专用记录器

# 安全的Redis连接初始化 - 避免递归错误
try:
    from .redis_helper import RedisHelper
    redis = RedisHelper(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, password=REDIS_PASSWORD)
    # 简单测试连接，避免复杂操作
    redis.ping()
    system_logger.info('Redis连接成功',extra={'host':REDIS_HOST,'port':REDIS_PORT,'db':REDIS_DB})
except Exception as e:
    system_logger.error('Redis连接初始化失败，使用降级模式',extra={'error':str(e)})
    # 创建一个简单的Redis替代品，避免递归错误
    class SimpleRedis:
        def get(self, key): return None
        def setex(self, key, ttl, value): pass
        def ping(self): return True
    redis = SimpleRedis()

# 导入调试控制模块，批量禁用print调试输出
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from debug_control import debug_controller

# 🔥关键修复：在模块加载时就初始化系统事件处理器
print("🔧Redis监听器已临时禁用，避免认证错误")

# 初始化系统事件处理器 - 确保在应用上下文中进行
with app.app_context():
    try:
        from .system_event_alert import get_processor
        processor = get_processor()
        if not processor.is_running:
            processor.start(worker_count=3)
            print("✅系统事件处理器已自动启动")
        else:
            print("ℹ️系统事件处理器已在运行")
    except Exception as e:
        print(f"⚠️系统事件处理器启动失败: {e}")
        import traceback
        traceback.print_exc()

# Redis Stream系统已禁用
stream_manager = None
consumer_manager = None

# 全局性能指标收集器 (在初始化函数中声明和赋值)
# metrics_collector 将在 initialize_metrics_collector() 中初始化

def initialize_stream_system():
    """Stream系统已禁用"""
    global stream_manager, consumer_manager
    
    # Stream系统已禁用，不进行初始化
    logger.info("Stream系统已禁用")
    return False

# Stream系统初始化已禁用
# with app.app_context():
#     initialize_stream_system()

# logger已在前面定义

# =============================================================================
# 系统状态和健康检查接口
# =============================================================================

# 健康检查端点
@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    try:
        # 检查数据库连接
        db.session.execute('SELECT 1')
        
        # 检查Redis连接
        from .redis_helper import RedisHelper
        redis_helper = RedisHelper()
        redis_helper.redis_client.ping()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'ljwx-bigscreen',
            'port': APP_PORT,
            'checks': {
                'database': 'ok',
                'redis': 'ok'
            }
        }), 200
    except Exception as e:
        system_logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'ljwx-bigscreen',
            'port': APP_PORT,
            'error': str(e),
            'checks': {
                'database': 'error',
                'redis': 'error'
            }
        }), 500

# API健康检查端点（符合标准API路径）
@app.route('/api/health', methods=['GET'])
def api_health_check():
    """API健康检查端点"""
    return health_check()

# 新增监控API端点
@app.route('/api/monitoring/metrics', methods=['GET'])
def api_monitoring_metrics():
    """获取系统性能指标"""
    try:
        if not metrics_collector:
            return jsonify({
                'error': '指标收集器未初始化',
                'message': 'MetricsCollector not initialized'
            }), 503
        
        latest_metrics = metrics_collector.get_latest_metrics()
        return jsonify({
            'status': 'success',
            'data': latest_metrics
        }), 200
        
    except Exception as e:
        system_logger.error(f"获取监控指标失败: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/monitoring/metrics/history', methods=['GET'])
def api_monitoring_metrics_history():
    """获取指标历史数据"""
    try:
        if not metrics_collector:
            return jsonify({
                'error': '指标收集器未初始化'
            }), 503
        
        hours = request.args.get('hours', 1, type=int)
        hours = min(max(hours, 1), 24)  # 限制在1-24小时之间
        
        history_metrics = metrics_collector.get_metrics_history(hours=hours)
        return jsonify({
            'status': 'success', 
            'data': history_metrics
        }), 200
        
    except Exception as e:
        system_logger.error(f"获取指标历史失败: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/monitoring/health', methods=['GET'])  
def api_monitoring_health():
    """获取系统健康状态评估"""
    try:
        if not metrics_collector:
            return jsonify({
                'overall_health': 'unknown',
                'status': 'metrics_collector_unavailable',
                'message': '指标收集器未可用'
            }), 503
        
        health_status = metrics_collector.get_health_status()
        
        # 根据健康状态设置HTTP状态码
        http_code = 200
        if health_status.get('overall_health') == 'poor':
            http_code = 503
        elif health_status.get('overall_health') == 'fair':
            http_code = 200
            
        return jsonify(health_status), http_code
        
    except Exception as e:
        system_logger.error(f"获取健康状态失败: {e}")
        return jsonify({
            'overall_health': 'error',
            'status': 'evaluation_failed', 
            'error': str(e)
        }), 500

@app.route('/api/monitoring/shards', methods=['GET'])
def api_monitoring_shards():
    """获取分片处理器状态"""
    try:
        from .health_data_batch_processor import health_data_optimizer
        
        if not health_data_optimizer or not hasattr(health_data_optimizer, 'sharded_processor'):
            return jsonify({
                'error': '分片处理器未初始化'
            }), 503
        
        sharded_processor = health_data_optimizer.sharded_processor
        overall_stats = sharded_processor.get_overall_stats()
        
        # 获取各分片详细信息
        shard_details = []
        for i, shard_metric in enumerate(sharded_processor.shard_metrics):
            shard_info = {
                'shard_id': shard_metric.shard_id,
                'processed_count': shard_metric.processed_count,
                'batch_count': shard_metric.batch_count,
                'error_count': shard_metric.error_count,
                'avg_processing_time_ms': shard_metric.avg_processing_time * 1000,
                'is_active': shard_metric.is_active,
                'queue_size': sharded_processor.shard_queues[i].qsize() if i < len(sharded_processor.shard_queues) else 0
            }
            shard_details.append(shard_info)
        
        return jsonify({
            'status': 'success',
            'overall_stats': overall_stats,
            'shard_details': shard_details,
            'total_shards': sharded_processor.shard_count
        }), 200
        
    except Exception as e:
        system_logger.error(f"获取分片状态失败: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/monitoring/export', methods=['GET'])
def api_monitoring_export():
    """导出监控指标数据"""
    try:
        if not metrics_collector:
            return jsonify({
                'error': '指标收集器未初始化'
            }), 503
        
        format_type = request.args.get('format', 'json').lower()
        
        if format_type != 'json':
            return jsonify({
                'error': f'不支持的导出格式: {format_type}'
            }), 400
        
        exported_data = metrics_collector.export_metrics(format=format_type)
        
        response = make_response(exported_data)
        response.headers['Content-Type'] = 'application/json'
        response.headers['Content-Disposition'] = f'attachment; filename=metrics_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        return response
        
    except Exception as e:
        system_logger.error(f"导出监控数据失败: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/track_view')
def track_view():
    return render_template('track_view.html')

@app.route('/api/tracks')
def get_tracks():
    # 模拟轨迹数据
    tracks = [
        {
            'name': '轨迹1',
            'color': '#00ff00',
            'coordinates': [
                [114.025246, 22.543721],
                [114.028293, 22.545632],
                [114.031876, 22.547891],
                [114.035234, 22.549012],
                [114.038765, 22.551234]
            ],
            'stats': {
                'distance': 5.2,
                'time': 45,
                'speed': 6.9
            }
        },
        {
            'name': '轨迹2',
            'color': '#ff00ff',
            'coordinates': [
                [114.027246, 22.541721],
                [114.029293, 22.543632],
                [114.032876, 22.545891],
                [114.036234, 22.547012],
                [114.039765, 22.549234]
            ],
            'stats': {
                'distance': 3.8,
                'time': 30,
                'speed': 7.6
            }
        }
    ]
    return jsonify(tracks)

def generate_track_points():
    # 生成模拟轨迹点
    base_lon = 114.02
    base_lat = 22.54
    points = []
    for i in range(10):
        points.append([
            base_lon + random.uniform(-0.02, 0.02),
            base_lat + random.uniform(-0.02, 0.02)
        ])
    return points

@app.route("/test_body")
def test_body():
    return render_template("personal_body.html")

# =============================================================================
# 页面路由 (Page Routes)
# =============================================================================

@app.route("/health_table")
def health_table():
    return render_template("health_table.html")
@app.route("/health_trends")
def health_trends():
    return render_template("health_trends.html")
@app.route("/health_main")
def health_main():
    return render_template("health_main.html")

# 新增健康分析页面路由
@app.route("/health_score_view")
def health_score_view():
    """健康评分分析页面"""
    return render_template("health_score_view.html")

@app.route("/health_prediction_view")
def health_prediction_view():
    """健康预测分析页面"""
    return render_template("health_prediction_view.html")

@app.route("/health_recommendation_view")
def health_recommendation_view():
    """健康建议分析页面"""
    return render_template("health_recommendation_view.html")

@app.route("/health_profile_view")
def health_profile_view():
    """健康画像分析页面"""
    return render_template("health_profile_view.html")

@app.route("/health_baseline")
def health_baseline():
    return render_template('health_baseline.html')

@app.route("/user_health_data_analysis")  # 添加健康数据分析页面路由
def user_health_data_analysis():
    default_health_status = {'score': 0, 'level': '暂无数据', 'summary': '请选择日期范围查看健康分析', 'insights': []}
    return render_template('user_health_data_analysis.html', health_status=default_health_status)

@app.route("/health_profile")  # 健康画像管理页面路由
def health_profile():
    """健康画像管理中心"""
    return render_template("health_profile.html")


@app.route("/config_management")
def config_management():
    return render_template('config_management.html')

# 设备绑定管理页面已禁用
# @app.route("/device_bind")  # 设备绑定管理页面路由
# def device_bind():
#     return render_template('device_bind_management.html')

@app.route("/get_interface_config", methods=['GET'])
def get_interface_config():
    return fetch_config_get_interface_config()

@app.route("/get_health_config", methods=['GET'])
def get_health_config():
    return fetch_config_get_health_config()

@app.route("/get_customer_config", methods=['GET'])
def get_customer_config():
    return fetch_config_get_customer_config()

@app.route("/get_optimal_config", methods=['GET'])
def get_optimal_config():
    return fetch_config_get_optimal_config()

@app.route("/save_interface_config", methods=['POST'])
def save_interface_config():
    return fetch_config_save_interface_config()

@app.route("/save_health_config", methods=['POST'])
def save_health_config():
    return fetch_config_save_health_config()

@app.route("/save_customer_config", methods=['POST'])
def save_customer_config():
    return fetch_config_save_customer_config()

@app.route("/test")
def test_index():
    return render_template("test.html")

@app.route("/filter_test")
def filter_test():
    return render_template("filter_test.html")

@app.route("/personal_health_data")
def personal_health_data():
    return render_template("personal_health_data.html")

@app.route("/personal")
def bigscreen_index():
    deviceSn = request.args.get('deviceSn')  # Get the deviceSn from query parameters
    logger.info(f"deviceSn: {deviceSn}")
    #personalInfo = get_personal_info(deviceSn)  # Get the userName from query parameters
    #print("deviceSn", deviceSn)
    #print("personalInfo", personalInfo)
    # You can now use deviceSn in your logic or pass it to the template
    #return render_template("bigscreen_new.html", deviceSn=deviceSn, userName=userName)
    return render_template("personal.html", 
                         deviceSn=deviceSn,
                         PERSONAL_SCREEN_VERSION=PERSONAL_SCREEN_VERSION)
@app.route("/personal_new")
def personal_new():
    deviceSn = request.args.get('deviceSn')  # Get the deviceSn from query parameters
    logger.info(f"deviceSn: {deviceSn}")
    #personalInfo = get_personal_info(deviceSn)  # Get the userName from query parameters
    #print("deviceSn", deviceSn)
    #print("personalInfo", personalInfo)
    # You can now use deviceSn in your logic or pass it to the template
    #return render_template("bigscreen_new.html", deviceSn=deviceSn, userName=userName)
    return render_template("personal_new.html", deviceSn=deviceSn)
@app.route("/personal_cool")
def personal_cool():
    deviceSn = request.args.get('deviceSn')  # Get the deviceSn from query parameters
    #personalInfo = get_personal_info(deviceSn)  # Get the userName from query parameters
    logger.info(f"deviceSn: {deviceSn}")
    #print("personalInfo", personalInfo)
    # You can now use deviceSn in your logic or pass it to the template
    #return render_template("bigscreen_new.html", deviceSn=deviceSn, userName=userName)
    return render_template("bigscreen_new.html", deviceSn=deviceSn)

@app.route("/personal_modern")
def personal_modern():
    """现代化个人大屏 v2.0 - 全新设计界面"""
    deviceSn = request.args.get('deviceSn')
    logger.info(f"Personal Modern V2.0 - deviceSn: {deviceSn}")
    return render_template("personal_modern_v2.html", deviceSn=deviceSn)

@app.route("/main")
def main_index():
    customerId = request.args.get('customerId')  # Get the customerId from query parameters
    logger.info(f"customerId: {customerId}")
    return render_template("main.html", 
                         customerId=customerId,
                         BIGSCREEN_TITLE=BIGSCREEN_TITLE,
                         BIGSCREEN_VERSION=BIGSCREEN_VERSION,
                         COMPANY_NAME=COMPANY_NAME)

@app.route("/main_dashboard")
def main_dashboard():
    customerId = request.args.get('customerId', '1')  # Get the customerId from query parameters
    logger.info(f"customerId: {customerId}")
    return render_template("main_dashboard.html", customerId=customerId)

@app.route("/main_optimized_v2")
def main_optimized_v2():
    """优化版大屏V2 - 三层架构设计"""
    customerId = request.args.get('customerId', '1939964806110937090')
    logger.info(f"加载优化版大屏V2 - customerId: {customerId}")
    return render_template("main_optimized_v2.html",
                         customerId=customerId,
                         BIGSCREEN_TITLE=BIGSCREEN_TITLE,
                         BIGSCREEN_VERSION="V2.0 优化版",
                         COMPANY_NAME=COMPANY_NAME)

@app.route("/test_realtime_stats")
def test_realtime_stats():
    """测试实时统计API的页面"""
    return render_template("test_realtime_stats.html")

@app.route('/api/debug_stats', methods=['GET'])
def debug_stats():
    """调试统计数据接口"""
    try:
        from datetime import date, timedelta
        from sqlalchemy import func
        
        customer_id = request.args.get('customerId')
        if not customer_id:
            return jsonify({"success": False, "error": "customerId参数是必需的"}), 400
        
        target_date_str = request.args.get('date')
        if target_date_str:
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        else:
            target_date = date.today()
        
        # 检查设备信息
        devices_by_customer_id = db.session.query(DeviceInfo).filter(
            DeviceInfo.customer_id == customer_id
        ).all()
        
        devices_by_org_id = db.session.query(DeviceInfo).filter(
            DeviceInfo.org_id == customer_id
        ).all()
        
        # 选择有效的查询方式
        devices = devices_by_customer_id if devices_by_customer_id else devices_by_org_id
        device_filter_field = 'customer_id' if devices_by_customer_id else 'org_id'
        
        if not devices:
            return jsonify({
                "success": False,
                "error": "未找到任何设备",
                "debug_info": {
                    "customer_id": customer_id,
                    "devices_by_customer_id": 0,
                    "devices_by_org_id": 0
                }
            })
        
        # 检查健康数据
        if device_filter_field == 'customer_id':
            health_count = db.session.query(func.count(UserHealthData.id)).join(
                DeviceInfo, UserHealthData.device_sn == DeviceInfo.serial_number
            ).filter(
                DeviceInfo.customer_id == customer_id,
                func.date(UserHealthData.timestamp) == target_date
            ).scalar() or 0
            
            recent_health = db.session.query(UserHealthData).join(
                DeviceInfo, UserHealthData.device_sn == DeviceInfo.serial_number
            ).filter(
                DeviceInfo.customer_id == customer_id
            ).order_by(UserHealthData.timestamp.desc()).limit(3).all()
        else:
            health_count = db.session.query(func.count(UserHealthData.id)).join(
                DeviceInfo, UserHealthData.device_sn == DeviceInfo.serial_number
            ).filter(
                DeviceInfo.org_id == customer_id,
                func.date(UserHealthData.timestamp) == target_date
            ).scalar() or 0
            
            recent_health = db.session.query(UserHealthData).join(
                DeviceInfo, UserHealthData.device_sn == DeviceInfo.serial_number
            ).filter(
                DeviceInfo.org_id == customer_id
            ).order_by(UserHealthData.timestamp.desc()).limit(3).all()
        
        # 检查告警数据
        if device_filter_field == 'customer_id':
            alert_count = db.session.query(func.count(AlertInfo.id)).join(
                DeviceInfo, AlertInfo.device_sn == DeviceInfo.serial_number
            ).filter(
                DeviceInfo.customer_id == customer_id,
                func.date(AlertInfo.alert_timestamp) == target_date
            ).scalar() or 0
            
            total_alerts = db.session.query(func.count(AlertInfo.id)).join(
                DeviceInfo, AlertInfo.device_sn == DeviceInfo.serial_number
            ).filter(
                DeviceInfo.customer_id == customer_id
            ).scalar() or 0
        else:
            alert_count = db.session.query(func.count(AlertInfo.id)).join(
                DeviceInfo, AlertInfo.device_sn == DeviceInfo.serial_number
            ).filter(
                DeviceInfo.org_id == customer_id,
                func.date(AlertInfo.alert_timestamp) == target_date
            ).scalar() or 0
            
            total_alerts = db.session.query(func.count(AlertInfo.id)).join(
                DeviceInfo, AlertInfo.device_sn == DeviceInfo.serial_number
            ).filter(
                DeviceInfo.org_id == customer_id
            ).scalar() or 0
        
        return jsonify({
            "success": True,
            "debug_info": {
                "customer_id": customer_id,
                "target_date": target_date.strftime('%Y-%m-%d'),
                "device_filter_field": device_filter_field,
                "devices_count": len(devices),
                "device_serials": [d.serial_number for d in devices[:3]],  # 前3个
                "health_data": {
                    "today_count": health_count,
                    "recent_timestamps": [h.timestamp.strftime('%Y-%m-%d %H:%M:%S') for h in recent_health]
                },
                "alerts": {
                    "today_count": alert_count,
                    "total_count": total_alerts
                },
                "analysis": {
                    "health_status": "正常" if health_count > 0 else "无数据",
                    "alert_status": "异常" if total_alerts > 100000 else "正常" if alert_count > 0 else "无数据"
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False, 
            "error": str(e),
            "debug_info": {"exception": str(e)}
        }), 500
@app.route("/optimize")
def optimize_index():
    customerId = request.args.get('customerId')  # Get the deviceSn from query parameters
    logger.info(f"customerId: {customerId}")
    return render_template("bigscreen_optimized.html", customerId=customerId)
@app.route("/index")
def index_index():
    customerId = request.args.get('customerId')  # Get the deviceSn from query parameters
    logger.info(f"customerId: {customerId}")
    return render_template("index.html", customerId=customerId)
@app.route("/alert")
def alert_index():
    return render_template("alert.html")

@app.route("/message")
def message_index():
    return render_template("message.html")

@app.route("/map")
def map_index(deviceSn=None, date_str=None, customerId=None):
    if deviceSn is None:
        deviceSn = request.args.get('deviceSn')
    if date_str is None:
        date_str = request.args.get('date_str')
    customerId = request.args.get('customerId')  # Get the deviceSn from query parameters
    logger.info(f"customerId: {customerId}")
    return render_template("map.html", deviceSn=deviceSn, date_str=date_str, customerId=customerId)

@app.route("/chart")
def chart_index():
    return render_template("chart.html")

@app.route('/chat')
def chat_page():
    return render_template('chat.html')
@app.route('/get_customer_id_by_deviceSn', methods=['GET'])
def get_customer_id_by_deviceSn():
    deviceSn = request.args.get('deviceSn')
    return fetch_customer_id_by_deviceSn(deviceSn)

# =============================================================================
# 用户管理接口 (User Management APIs)
# =============================================================================

@app.route('/getUserInfo', methods=['GET'])
def get_user_info(deviceSn=None):
    if deviceSn is None:
        deviceSn = request.args.get('deviceSn')
    return user_get_user_info(deviceSn)

@app.route('/getUserDeviceSn', methods=['GET'])
def get_user_deviceSn(phone=None):
    if phone is None:
        phone = request.args.get('phone')
    return user_get_user_deviceSn(phone)

@app.route('/getUserId', methods=['GET'])
def get_user_id(phone=None):
    if phone is None:
        phone = request.args.get('phone')
    return user_get_user_id(phone)
@app.route('/get_all_users', methods=['GET'])
def get_all_users():
    return user_get_all_users()

# =============================================================================
# 消息管理接口 (Message Management APIs)
# =============================================================================

@app.route('/DeviceMessage/save_message', methods=['POST'])
def save_message():
    """保存设备消息 - 重构后使用模块化实现"""
    data = request.get_json()
    result, status_code = save_device_message_data(data)
    return jsonify(result), status_code
@app.route('/DeviceMessage/send', methods=['POST'])
@log_api_request('/DeviceMessage/send','POST')
def send_device_message(data=None):
    """发送设备消息 - 重构后使用模块化实现"""
    if data is None:
        data = request.get_json()
    return send_device_message_data(data)

@app.route('/DeviceMessage/receive', methods=['GET'])
@log_api_request('/DeviceMessage/receive','GET')
def received_messages(deviceSn=None):
    """接收设备消息 - 重构后使用模块化实现"""
    if deviceSn is None:
        deviceSn = request.args.get('deviceSn')
    return receive_device_messages_data(deviceSn)

@app.route('/DeviceMessage/acknowledge', methods=['POST'])
@log_api_request('/DeviceMessage/acknowledge','POST')
def acknowledge_device_message():
    """手机端消息确认API - 完善消息数据流"""
    try:
        if not MESSAGE_FEATURES_AVAILABLE:
            return jsonify({
                'success': False,
                'message': '消息V2增强功能不可用'
            }), 503
        
        data = request.get_json()
        result, status_code = acknowledge_message(data)
        return jsonify(result), status_code
    except Exception as e:
        api_logger.error(f'消息确认失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'消息确认失败: {str(e)}'
        }), 500

@app.route('/DeviceMessage/batch_acknowledge', methods=['POST'])
@log_api_request('/DeviceMessage/batch_acknowledge','POST')
def batch_acknowledge_device_messages():
    """批量消息确认API"""
    try:
        if not MESSAGE_FEATURES_AVAILABLE:
            return jsonify({
                'success': False,
                'message': '消息V2增强功能不可用'
            }), 503
        
        data = request.get_json()
        result, status_code = batch_acknowledge_messages(data)
        return jsonify(result), status_code
    except Exception as e:
        api_logger.error(f'批量消息确认失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'批量消息确认失败: {str(e)}'
        }), 500

@app.route('/DeviceMessage/watch_summary', methods=['GET'])
@log_api_request('/DeviceMessage/watch_summary','GET')
def get_watch_message_summary_api():
    """手表端消息摘要API"""
    try:
        if not MESSAGE_FEATURES_AVAILABLE:
            return jsonify({
                'success': False,
                'message': '消息V2增强功能不可用'
            }), 503
        
        device_sn = request.args.get('deviceSn')
        if not device_sn:
            return jsonify({
                'success': False,
                'message': '缺少设备序列号参数'
            }), 400
        
        result = get_watch_message_summary(device_sn)
        return jsonify(result)
    except Exception as e:
        api_logger.error(f'获取手表消息摘要失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'获取摘要失败: {str(e)}'
        }), 500

@app.route('/DeviceMessage/watch_read', methods=['POST'])
@log_api_request('/DeviceMessage/watch_read','POST')
def mark_message_read_on_watch_api():
    """手表端标记消息已读API"""
    try:
        if not MESSAGE_FEATURES_AVAILABLE:
            return jsonify({
                'success': False,
                'message': '消息V2增强功能不可用'
            }), 503
        
        data = request.get_json()
        message_id = data.get('message_id')
        device_sn = data.get('device_sn')
        
        if not message_id or not device_sn:
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            }), 400
        
        result = mark_message_as_read_on_watch(message_id, device_sn)
        return jsonify(result)
    except Exception as e:
        api_logger.error(f'手表端标记已读失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'标记已读失败: {str(e)}'
        }), 500

# Initialize the heart_rate_timestamps list

# =============================================================================
# 组织管理接口 (Organization Management APIs)
# =============================================================================

@app.route("/get_departments_by_orgId", methods=['GET'])
def get_departments_by_orgId():
    orgId = request.args.get('orgId')
    customerId = request.args.get('customerId')
    return fetch_departments_by_orgId(orgId, customerId)
@app.route("/fetch_users", methods=['GET'])
def fetch_users():
    orgId = request.args.get('orgId')
    customerId = request.args.get('customerId')
    return fetch_users_by_orgId(orgId, customerId)
@app.route("/get_users_by_orgIdAndUserId", methods=['GET'])
def get_users_by_orgIdAndUserId():
    orgId = request.args.get('orgId')
    userId = request.args.get('userId')
    # 使用最快版本的用户查询函数
    
    return user_get_user_info_by_orgIdAndUserId(orgId=orgId, userId=userId)
@app.route("/fetch_users_stats", methods=['GET'])
def fetch_users_stats():
    orgId = request.args.get('orgId')
    return fetch_users_stats_by_orgId(orgId)

# =============================================================================
# 设备管理接口 (Device Management APIs)
# =============================================================================

@app.route("/upload_device_info", methods=['POST'])
@log_api_request('/upload_device_info','POST')
def handle_device_info():
    """优化版设备信息上传接口 - 使用异步处理器"""
    device_info = request.get_json()
    
    # 快速参数验证
    if not device_info:
        return jsonify({"status": "error", "message": "请求体不能为空"}), 400
    
    # 提取设备标识用于日志
    if isinstance(device_info, list):
        device_count = len(device_info)
        first_device_sn = "unknown"
        if device_count > 0 and isinstance(device_info[0], dict):
            first_device_sn = (device_info[0].get('SerialNumber') or 
                              device_info[0].get('serial_number') or 
                              device_info[0].get('deviceSn') or "unknown")
        
        device_logger.info('批量设备信息上传',extra={'device_sn':first_device_sn,'data_count':device_count})
        print(f"📱 批量设备上传: {device_count}台, 首个设备: {first_device_sn}")
    else:
        device_sn = (device_info.get('SerialNumber') or 
                    device_info.get('serial_number') or 
                    device_info.get('deviceSn') or "unknown")
        device_logger.info('设备信息上传',extra={'device_sn':device_sn,'data_count':1})
        print(f"📱 单设备上传: {device_sn}")
    
    try:
        # 使用优化的异步处理器
        from .optimized_device_processor import get_optimized_device_processor
        from flask import current_app
        
        processor = get_optimized_device_processor(current_app._get_current_object())
        
        # 快速提交到异步队列
        import asyncio
        
        # 检查是否有运行的事件循环
        try:
            loop = asyncio.get_running_loop()
            # 如果有运行的循环，创建任务
            task = loop.create_task(processor.submit_fast(device_info))
            # 注意：这里不等待任务完成，立即返回响应
            success = True
        except RuntimeError:
            # 没有运行的事件循环，使用同步方式
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                success = loop.run_until_complete(processor.submit_fast(device_info))
                loop.close()
            except Exception as e:
                print(f"❌ 异步处理器提交失败: {e}")
                success = False
        
        if success:
            return jsonify({
                "status": "success", 
                "message": "设备信息已接收，正在异步处理"
            })
        else:
            # 降级到原有处理方式
            print(f"📱 降级到原有处理方式")
            result = upload_device_info(device_info, current_app._get_current_object())
            return result
            
    except Exception as e:
        print(f"❌ 优化处理器异常: {e}")
        # 降级到原有处理方式
        try:
            from flask import current_app
            result = upload_device_info(device_info, current_app._get_current_object())
            return result
        except Exception as fallback_error:
            print(f"❌ 降级处理也失败: {fallback_error}")
            return jsonify({"status": "error", "message": "设备信息处理失败"}), 500

@app.route("/api/device_processor/stats", methods=['GET'])
def get_device_processor_stats():
    """获取优化设备处理器性能统计"""
    try:
        from .optimized_device_processor import get_device_processor_stats
        stats = get_device_processor_stats()
        if stats:
            return jsonify({"success": True, "data": stats})
        else:
            return jsonify({"success": False, "message": "设备处理器未初始化"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# =============================================================================
# 健康数据管理接口 (Health Data Management APIs)
# =============================================================================

@app.route("/upload_health_data", methods=['POST'])
@log_api_request('/upload_health_data','POST')
def handle_health_data():
    health_data = request.get_json()
    print(f"🏥 /upload_health_data 接口收到请求")
    print(f"🏥 请求头: {dict(request.headers)}")
    print(f"🏥 请求体大小: {len(str(health_data)) if health_data else 0} 字符")
    print(f"🏥 原始JSON数据: {json.dumps(health_data, ensure_ascii=False, indent=2) if health_data else 'None'}")
    
    if not health_data:
        print(f"❌ 请求体为空")
        return jsonify({"status": "error", "message": "请求体不能为空"}), 400
    
    # 修复data字段处理-支持数组和对象格式
    data_field = health_data.get('data', {})
    print(f"🔍 data字段类型: {type(data_field)}, 内容: {data_field}")
    
    device_sn = None
    
    if isinstance(data_field, list) and len(data_field) > 0:
        # data是数组，取第一个元素获取deviceSn
        device_sn = data_field[0].get('deviceSn') or data_field[0].get('id')
        print(f"🔍 从数组第一个元素提取device_sn: {device_sn}")
    elif isinstance(data_field, dict):
        # data是对象，先检查直接的deviceSn/id字段
        device_sn = data_field.get('deviceSn') or data_field.get('id')
        
        # 如果没找到，检查嵌套的data字段（针对data.data.id的情况）
        if not device_sn and 'data' in data_field:
            nested_data = data_field['data']
            if isinstance(nested_data, dict):
                device_sn = nested_data.get('deviceSn') or nested_data.get('id')
                print(f"🔍 从嵌套data对象提取device_sn: {device_sn}")
            elif isinstance(nested_data, list) and len(nested_data) > 0:
                device_sn = nested_data[0].get('deviceSn') or nested_data[0].get('id')
                print(f"🔍 从嵌套data数组提取device_sn: {device_sn}")
        
        if device_sn:
            print(f"🔍 从对象提取device_sn: {device_sn}")
    
    if not device_sn:
        print(f"⚠️ 无法从data字段提取device_sn，data类型: {type(data_field)}")
    
    print(f"🏥 最终提取的设备SN: {device_sn}")
    health_logger.info('健康数据上传开始',extra={'device_sn':device_sn,'data_size':len(str(health_data))})

    # License验证已禁用 - 不再检查设备许可和并发限制
    # if device_sn:
    #     license_check = check_device_license(device_sn)
    #     if not license_check.get('allowed', False):
    #         error_message = license_check.get('reason', 'License验证失败')
    #         error_code = license_check.get('code', 4000)
    #         print(f"❌ License验证失败: {error_message}")
    #         health_logger.warning('健康数据上传License验证失败', extra={
    #             'device_sn': device_sn,
    #             'error_code': error_code,
    #             'error_message': error_message
    #         })
    #         return jsonify({
    #             "status": "error",
    #             "message": error_message,
    #             "error_code": error_code
    #         }), 403
    #     else:
    #         print(f"✅ License验证通过: {device_sn}")

    # Stream处理已禁用，直接使用传统处理
    # try:
    #     use_stream = should_use_stream_processing(device_sn)
    #     if use_stream:
    #         print(f"🌊 设备 {device_sn} 使用Stream处理")
    #         return jsonify({"status": "error", "message": "Stream系统已禁用"}), 503
    #     else:
    #         print(f"🔄 设备 {device_sn} 使用传统处理")
    # except Exception as stream_error:
    #     print(f"⚠️ Stream切换检查失败，回退到传统处理: {stream_error}")
    
    print(f"🔄 设备 {device_sn} 使用传统处理")

    print(f"🏥 调用upload_health_data处理函数")
    import time
    start_time = time.time()

    try:
        result = upload_health_data(health_data)
        duration = time.time() - start_time

        # 记录成功的健康数据上传指标
        upload_method = 'wifi'  # 默认值
        if isinstance(health_data.get('data'), dict):
            data_dict = health_data.get('data')
            if isinstance(data_dict.get('data'), dict):
                upload_method = data_dict.get('data', {}).get('upload_method', 'wifi')
            else:
                upload_method = data_dict.get('upload_method', 'wifi')

        record_health_data_upload(
            device_sn=device_sn or 'unknown',
            upload_method=upload_method,
            success=True,
            duration=duration
        )

        print(f"📊 记录健康数据指标: device_sn={device_sn}, upload_method={upload_method}, duration={duration:.3f}s")
        print(f"🏥 upload_health_data处理结果: {result.get_json() if hasattr(result, 'get_json') else result}")
        return result

    except Exception as e:
        duration = time.time() - start_time
        # 记录失败的健康数据上传指标
        record_health_data_upload(
            device_sn=device_sn or 'unknown',
            upload_method='unknown',
            success=False,
            duration=duration
        )
        print(f"❌ 健康数据处理失败: {e}")
        raise

@app.route("/upload_health_data_optimized", methods=['POST'])
@log_api_request('/upload_health_data_optimized','POST')
def handle_health_data_optimized():
    """优化版健康数据上传接口"""
    health_data = request.get_json()
    # 修复data字段处理-支持数组和对象格式
    data_field = health_data.get('data', {})
    if isinstance(data_field, list) and len(data_field) > 0:
        # data是数组，取第一个元素获取deviceSn
        device_sn = data_field[0].get('deviceSn') or data_field[0].get('id')
    elif isinstance(data_field, dict):
        # data是对象，直接获取deviceSn
        device_sn = data_field.get('deviceSn') or data_field.get('id')
    else:
        device_sn = None
    
    health_logger.info('优化版健康数据上传',extra={'device_sn':device_sn})
    
    return user_upload_health_data(health_data)

# ============= Stream版本API接口 =============




# ============= Stream监控接口已禁用 =============

# @app.route("/api/stream_stats", methods=['GET'])
# def get_stream_stats():
#     """获取Stream统计信息 - 已禁用"""
#     return jsonify({"error": "Stream系统已禁用"}), 503

# @app.route("/api/stream_health", methods=['GET'])
# def check_stream_health():
#     """Stream健康检查 - 已禁用"""
#     return jsonify({
#         "healthy": False,
#         "error": "Stream系统已禁用"
#     }), 503

@app.route("/optimizer_stats", methods=['GET'])
def get_optimizer_stats():
    """获取优化器统计信息 - 已禁用"""
    return jsonify({"error": "优化器模块已禁用"}), 503

@app.route('/fetch_health_data', methods=['GET'])
def fetch_health_data(deviceSn=None):
    if deviceSn is None:
        deviceSn = request.args.get('deviceSn')
    return user_fetch_health_data(deviceSn)

@app.route('/api/phone/alerts/process', methods=['POST'])
def phone_process_alert():
    """手机端告警确认处理接口"""
    try:
        return alert_acknowledge_alert()
    except Exception as e:
        api_logger.error(f"手机端告警处理失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'告警处理失败: {str(e)}'
        }), 500

# =============================================================================
# 告警管理接口 (Alert Management APIs)
# =============================================================================

@app.route('/dealAlert', methods=['GET'])
def deal_alert(alertId=None):
    if alertId is None:
        alertId = request.args.get('alertId')
    return alert_deal_alert(alertId)

@app.route('/batchDealAlert', methods=['POST'])
def batch_deal_alert():
    """批量处理告警接口"""
    try:
        data = request.get_json()
        if not data or 'alertIds' not in data:
            return jsonify({'success': False, 'message': '缺少alertIds参数'})
        
        alert_ids = data['alertIds']
        if not isinstance(alert_ids, list) or not alert_ids:
            return jsonify({'success': False, 'message': 'alertIds必须是非空数组'})
        
        success_count = 0
        failed_count = 0
        failed_alerts = []
        
        for alert_id in alert_ids:
            try:
                result = alert_deal_alert(alert_id)
                # 检查result的类型和内容
                if hasattr(result, 'get_json'):
                    result_data = result.get_json()
                elif isinstance(result, dict):
                    result_data = result
                else:
                    result_data = {'success': False}
                
                if result_data.get('success', False):
                    success_count += 1
                else:
                    failed_count += 1
                    failed_alerts.append({'alertId': alert_id, 'error': result_data.get('message', '处理失败')})
            except Exception as e:
                failed_count += 1
                failed_alerts.append({'alertId': alert_id, 'error': str(e)})
        
        return jsonify({
            'success': failed_count == 0,
            'message': f'批量处理完成：成功{success_count}条，失败{failed_count}条',
            'successCount': success_count,
            'failedCount': failed_count,
            'failedAlerts': failed_alerts
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'批量处理失败：{str(e)}'})

@app.route('/fetch_health_data_config', methods=['GET'])
@log_api_request('/fetch_health_data_config','GET')
def fetch_health_data_config(customer_id=None,deviceSn=None):
    try:
        if customer_id is None:
            customer_id = request.args.get('customer_id')
        if deviceSn is None:
            deviceSn = request.args.get('deviceSn')
        
        # 记录配置查询日志
        from logging_config import db_logger
        db_logger.info('健康数据配置查询',extra={
            'customer_id':customer_id,
            'device_sn':deviceSn,
            'operation':'FETCH_CONFIG'
        })
        
        result = fetch_config_fetch_health_data_config(customer_id,deviceSn)
        
        # 记录查询结果
        if hasattr(result,'get_json'):
            result_data = result.get_json()
            if isinstance(result_data,dict) and 'data' in result_data:
                config_count = len(result_data['data']) if isinstance(result_data['data'],list) else 1
                db_logger.info('健康数据配置查询完成',extra={
                    'customer_id':customer_id,
                    'device_sn':deviceSn,
                    'config_count':config_count
                })
        
        return result
    except Exception as e:
        db_logger.error('健康数据配置查询失败',extra={
            'customer_id':customer_id,
            'device_sn':deviceSn,
            'error':str(e)
        },exc_info=True)
        raise

@app.route('/get_health_data', methods=['GET'])
def get_health_data(deviceSn=None, date=None):
    if deviceSn is None:
        deviceSn = request.args.get('deviceSn')
    if date is None:
        date = request.args.get('date')
    return user_get_health_data(deviceSn, date)

@app.route('/fetch_device_info', methods=['GET'])
def fetch_device_info(serial_number=None):
    if serial_number is None:
        serial_number = request.args.get('serial_number')
    return device_fetch_device_info(serial_number)

@app.route('/fetch_alertType_stats', methods=['GET'])

@app.route('/copy_health_data_config', methods=['GET'])
def copy_health_data_config():
    old_customer_id = request.args.get('old_customer_id')
    new_customer_id = request.args.get('new_customer_id')
    return fetch_config_copy_health_data_config(old_customer_id, new_customer_id)

@app.route('/fetch_personal_user_info', methods=['GET'])
def fetch_user_info(deviceSn=None):
    if deviceSn is None:
        deviceSn = request.args.get('deviceSn')
    return user_get_user_info(deviceSn)

@app.route('/fetch_user_locations', methods=['GET'])
def fetch_user_locations(deviceSn=None, date_str=None):
    if deviceSn is None:
        deviceSn = request.args.get('deviceSn')
    if date_str is None:
        date_str = request.args.get('date_str')
    return user_fetch_user_locations(deviceSn, date_str)

@app.route('/fetch_alerts', methods=['GET'])
def fetch_alerts(deviceSn=None, customerId=None):
    if deviceSn is None:
        deviceSn = request.args.get('deviceSn')
    if customerId is None:
        customerId = request.args.get('customerId')
    return alert_fetch_alerts(deviceSn, customerId)

@app.route('/upload_alerts', methods=['POST'])
def upload_alerts():
    return alert_upload_alerts()

@app.route('/fetch_health_metrics', methods=['GET'])

@app.route('/test_wechat_alert', methods=['GET'])
def test_wechat_alert():
    return alert_test_wechat_alert()

@app.route('/checkLicense', methods=['GET'])
def check_license():
    return util_check_license()

@app.route('/upload_common_event', methods=['POST'])
@log_api_request('/upload_common_event','POST')
def upload_common_event():
    return alert_upload_common_event()

# 优化版本接口
@app.route('/upload_common_event_v3', methods=['POST'])
@log_api_request('/upload_common_event_v3','POST')
def upload_common_event_v3():
    from .alert import upload_common_event_v3
    return upload_common_event_v3()

@app.route('/api/event_processor_stats', methods=['GET'])
def event_processor_stats():
    from .alert import get_event_processor_stats
    return get_event_processor_stats()

@app.route("/upload_watch_log", methods=['POST'])
def upload_watch_log():
    return watch_log_upload_watch_log()

@app.route('/watch_logs')
def watch_logs_page():
    return watch_log_watch_logs_page()

@app.route('/api/watch_logs', methods=['GET'])
def get_watch_logs():
    return watch_log_get_watch_logs()

@app.route('/api/watch_logs/stats', methods=['GET'])
def get_watch_log_stats():
    return watch_log_get_watch_log_stats()

@app.route('/generateAlertTypeChart', methods=['GET'])
def generate_alert_type_chart(customerId=None):
    if customerId is None:
        customerId = request.args.get('customerId')
    return generate_alert_chart_by_type(customerId)

import time
from functools import wraps
from datetime import datetime, timedelta

# 简单内存缓存实现
_cache = {}

def cache_result(ttl_hours=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            now = time.time()
            
            if key in _cache:
                data, expire_time = _cache[key]
                if now < expire_time:
                    return data
            
            result = func(*args, **kwargs)
            _cache[key] = (result, now + ttl_hours * 3600)
            return result
        return wrapper
    return decorator

# 在generateHealthJson路由上添加缓存
@app.route('/generateHealthJson')
# TODO: Add caching decorator when needed
def generate_health_json():
    customerId = request.args.get('customerId')
    userId = request.args.get('userId')
    
    # 优化参数处理逻辑
    if not customerId:
        return jsonify({'success': False, 'error': '缺少customerId参数'}), 400
    
    # 处理userId参数：
    # - 如果没有提供userId参数，则查询customerId下的所有用户
    # - 如果提供了具体的userId，则只查询该用户
    # - 如果userId='-1' 或 'all'，也视为查询所有用户
    if userId in [None, '', '-1', 'all']:
        userId = None  # 查询所有用户
    else:
        try:
            userId = int(userId)  # 验证userId是有效的数字
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'userId参数必须是有效的数字'}), 400
    
    # 性能优化：检查是否启用优化模式
    optimize = request.args.get('optimize', 'auto') #支持auto/true/false
    
    # 检查是否仅请求地图数据（减少数据量）
    map_only = request.args.get('map_only', 'false') == 'true'
    
    # 添加缓存机制 - 增加缓存时间到300秒（5分钟）
    import time
    start_time = time.time()
    cache_suffix = '_map' if map_only else '_full'
    cache_key = f"health_json_cache:{customerId}:{userId or 'all'}{cache_suffix}"
    
    try:
        cached_data = redis.get(cache_key)
        if cached_data:
            health_logger.info('从缓存获取健康JSON数据',extra={'customer_id':customerId,'user_id':userId,'map_only':map_only,'response_time':time.time()-start_time})
            response = json.loads(cached_data)
            response['performance'] = {'cached': True, 'response_time': round(time.time()-start_time, 3), 'map_only': map_only}
            return jsonify(response)
    except Exception as e:
        health_logger.warning('健康JSON缓存读取失败',extra={'error':str(e)})
    
    # 自动优化模式：超过100用户时启用优化
    if optimize == 'auto':
        try:
            from .org import fetch_users_by_orgId
            print(f"🔍 检查用户数量以决定是否优化: customerId={customerId}")
            users = fetch_users_by_orgId(customerId)
            user_count = len(users) if users else 0
            print(f"🔍 找到 {user_count} 个用户")
            if user_count > 100:
                health_logger.info('健康JSON自动启用优化模式',extra={'customer_id':customerId,'user_count':user_count})
                optimize = 'true'
            else:
                print(f"🔍 用户数量 {user_count} <= 100，使用原版本")
        except Exception as e:
            print(f"❌ 用户数量检测失败: {e}")
            health_logger.warning('用户数量检测失败',extra={'error':str(e)})
    
    # 执行查询
    if optimize == 'true':
        # 使用优化版本，直接返回GeoJSON格式
        from .user_health_data import fetch_health_data_by_orgIdAndUserId
        print(f"🔍 调用fetch_health_data_by_orgIdAndUserId: customerId={customerId}, userId={userId}")
        result = fetch_health_data_by_orgIdAndUserId(orgId=customerId, userId=userId)
        print(f"🔍 查询结果: success={result.get('success')}, data_keys={list(result.get('data', {}).keys()) if result.get('data') else None}")
        health_logger.info('使用优化版本生成健康JSON',extra={'customer_id':customerId,'user_id':userId,'map_only':map_only})
        
        # 如果优化版本返回的不是GeoJSON格式，转换为GeoJSON
        if result and result.get('success') and 'data' in result:
            health_data = result['data']
            features = []
            
            # 转换为GeoJSON格式
            for data in health_data.get('healthData', []):
                try:
                    longitude = float(data.get('longitude', 0))
                    latitude = float(data.get('latitude', 0))
                    
                    # 验证坐标范围和有效性
                    if (longitude != 0 and latitude != 0 and
                        -180 <= longitude <= 180 and
                        -90 <= latitude <= 90):
                        
                        altitude = float(data.get('altitude', 0)) if data.get('altitude') else 0
                        
                        feature = {
                            "type": "Feature",
                            "geometry": {
                                "type": "Point",
                                "coordinates": [longitude, latitude, altitude]
                            },
                            "properties": {
                                "deviceSn": data.get('deviceSn'),
                                "userName": data.get('userName'),
                                "deptName": data.get('deptName'),
                                "heartRate": float(data.get('heartRate', 0)) if data.get('heartRate') not in (None, 'None', '0') else 0,
                                "pressureHigh": float(data.get('pressureHigh', 0)) if data.get('pressureHigh') not in (None, 'None', '0') else 0,
                                "pressureLow": float(data.get('pressureLow', 0)) if data.get('pressureLow') not in (None, 'None', '0') else 0,
                                "bloodOxygen": float(data.get('bloodOxygen', 0)) if data.get('bloodOxygen') not in (None, 'None', '0') else 0,
                                "temperature": float(data.get('temperature', 0)) if data.get('temperature') not in (None, 'None', '0.0') else 0,
                                "stress": float(data.get('stress', 0)) if data.get('stress') not in (None, 'None', '0') else 0,
                                "timestamp": data.get('timestamp'),
                                "step": data.get('step', '0'),
                                "distance": data.get('distance', 0),
                                "calorie": data.get('calorie', 0),
                                "label": f"{data.get('deptName', '未知部门')}-{data.get('userName', '未知用户')}",
                            }
                        }
                        features.append(feature)
                except (ValueError, TypeError, OverflowError) as e:
                    print(f"坐标转换错误 - 设备 {data.get('deviceSn')}: {e}")
                    continue
            
            # 构造GeoJSON响应，安全地访问统计数据
            geojson_result = {
                "type": "FeatureCollection",
                "features": features,
                "statistics": {
                    "deviceCount": health_data.get('deviceCount', len(features)),
                    "totalRecords": health_data.get('totalRecords', len(features)),
                    "optimized": True
                }
            }
            result = geojson_result
        else:
            # 如果没有数据或查询失败，返回空的GeoJSON结构
            result = {
                "type": "FeatureCollection",
                "features": [],
                "statistics": {
                    "deviceCount": 0,
                    "totalRecords": 0,
                    "optimized": True
                },
                "error": result.get('error', '查询失败') if result else '查询失败'
            }
        
    else:
        # 使用原版本
        print(f"🔍 使用原版本生成健康JSON: customerId={customerId}, userId={userId}")
        flask_response = user_generate_health_json(customerId,userId)
        print(f"🔍 原版本结果类型: {type(flask_response)}")
        
        # Flask响应是tuple (response, status_code)，需要提取数据
        if isinstance(flask_response, tuple) and len(flask_response) == 2:
            response_obj, status_code = flask_response
            if hasattr(response_obj, 'get_json'):
                result = response_obj.get_json()
            else:
                result = {"type": "FeatureCollection", "features": [], "error": "无法解析原版本响应"}
        elif hasattr(flask_response, 'get_json'):
            result = flask_response.get_json()
        else:
            result = {"type": "FeatureCollection", "features": [], "error": "未知的响应格式"}
        
        print(f"🔍 提取后的结果类型: {type(result)}")
    
    # 缓存结果3600秒（1小时） - 与装饰器保持一致
    try:
        import decimal
        def json_serial(obj):
            if isinstance(obj, decimal.Decimal):
                return str(obj)
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object {obj} is not JSON serializable")
        
        # 添加性能信息
        if hasattr(result, 'get_json'):
            result_data = result.get_json()
        elif isinstance(result, dict):
            result_data = result
        else:
            result_data = {'data': result}
        
        result_data['performance'] = {
            'cached': False,
            'optimized': optimize == 'true',
            'map_only': map_only,
            'response_time': round(time.time() - start_time, 3)
        }
        
        # 确保所有响应都有必要的字段
        if 'statistics' not in result_data:
            result_data['statistics'] = {}
        if 'deviceCount' not in result_data['statistics']:
            # 从features数量推断设备数量
            feature_count = len(result_data.get('features', []))
            result_data['statistics']['deviceCount'] = feature_count
        if 'totalRecords' not in result_data['statistics']:
            result_data['statistics']['totalRecords'] = result_data['statistics']['deviceCount']
        
        cache_data = json.dumps(result_data, default=json_serial, ensure_ascii=False)
        # 统一缓存时间为3600秒（1小时）
        redis.setex(cache_key, 3600, cache_data)
        health_logger.info('健康JSON数据已缓存',extra={'customer_id':customerId,'user_id':userId,'map_only':map_only,'response_time':result_data['performance']['response_time'],'cache_size':len(cache_data),'cache_ttl':3600})
        
        return jsonify(result_data)
    except Exception as e:
        health_logger.warning('健康JSON缓存写入失败',extra={'error':str(e),'customer_id':customerId})
        return result

@app.route('/fetchHealthDataById', methods=['GET'])
def fetch_health_data_by_id(id=None):
    if id is None:
        id = request.args.get('id')
    return user_fetch_health_data_by_id(id)

@app.route('/get_departments', methods=['GET'])
def get_departments(orgId=None):
    if orgId is None:
        orgId = request.args.get('orgId')
    customerId = request.args.get('customerId')
    return fetch_departments(orgId, customerId)

@app.route('/generateAlertJson', methods=['GET'])
def generate_alert_json(customerId=None,userId=None,severityLevel=None):
    if customerId is None:
        customerId = request.args.get('customerId')
    if userId is None:
        userId = request.args.get('userId')
    if userId == '-1' or userId == 'all':
        userId = None
    if severityLevel is None:
        severityLevel = request.args.get('severityLevel')
    return alert_generate_alert_json(customerId,userId,severityLevel)

@app.route('/generateAlertChart', methods=['GET'])
def generate_alert_chart():
    return alert_generate_alert_chart()

@app.route('/gatherDealAlert', methods=['GET'])
def gather_deal_alert(customerId=None):
    if customerId is None:
        customerId = request.args.get('customerId')
    return alert_gather_deal_alert(customerId)

# Start the Redis change listener in a separate thread
# 临时禁用Redis监听器，避免认证错误
# threading.Thread(target=total_redis_change_listener, daemon=True).start()
# threading.Thread(target=personal_redis_change_listener, daemon=True).start()

print("🔧 Redis监听器已临时禁用，避免认证错误")  # 添加日志说明
@app.route('/get_personal_info', methods=['GET'])
def get_personal_info(deviceSn=None):
    try:
        if deviceSn is None:
            deviceSn = request.args.get('deviceSn')
            
        if not deviceSn:
            return jsonify({
                'success': False,
                'error': 'deviceSn is required'
            })
            
        print("get_personal_info::deviceSn:", deviceSn)
        user = UserInfo.query.filter_by(device_sn=deviceSn, is_deleted=False).first()
        if user:
            userId = user.id
            # Get alerts without relying on request context
            alert_info = alert_fetch_alerts_by_orgIdAndUserId(orgId=None, userId=userId)
            # Get messages without relying on request context
            message_info = message_fetch_messages_by_orgIdAndUserId(orgId=None, userId=userId)
            # Get health data without relying on request context
            health_info = fetch_health_data_by_orgIdAndUserId(orgId=None, userId=userId)
            logger.info("health_info:",health_info)
            # Get device info without relying on request context
            device_info = fetch_devices_by_orgIdAndUserId(orgId=None, userId=userId)
            
            # Get user info without relying on request context
            user_info = user_get_user_info_by_orgIdAndUserId(orgId=None, userId=userId)
            
            
            # Extract data from responses if they are Response objects
            def extract_data(response):
                if hasattr(response, 'get_json'):
                    return response.get_json()
                return response
                
            return {
                        'success': True,
                        'data': {
                            'alert_info': extract_data(alert_info),
                            'message_info': extract_data(message_info),
                            'device_info': extract_data(device_info),
                            'health_data': extract_data(health_info),
                            'user_info': extract_data(user_info)
                        }
                    }
        return {
            'success': False,
            'error': 'User not found',
            'data': None
        }
    except Exception as e:
        print("Error in get_personal_info:", str(e))
        return {
            'success': False,
            'error': f'Failed to get personal info: {str(e)}',
            'data': None
        }
@app.route('/get_personal_info_old', methods=['GET'])
def get_personal_info_old(deviceSn=None):
    if not deviceSn:
        deviceSn = request.args.get('deviceSn')
    if not deviceSn:
        return jsonify({'success': False, 'error': 'Missing deviceSn parameter'}), 400

    # Strip any leading or trailing whitespace from deviceSn
    deviceSn = deviceSn.strip()

    def fetch_or_update_data(key_prefix, fetch_function, *args):
        data = redis.hgetall_data(f"{key_prefix}:{deviceSn}")
        if not data:
            fetch_function(*args)
            data = redis.hgetall_data(f"{key_prefix}:{deviceSn}")
        return data

    # Fetch data using the helper function
    logger.info("health_data:")
    health_data = fetch_or_update_data("health_data", fetch_health_data, deviceSn)
    logger.info("device_info:")
    device_info = fetch_or_update_data("device_info", fetch_device_info, deviceSn)
    logger.info("user_info:")
    user_info = fetch_or_update_data("user_info", get_user_info, deviceSn)
    logger.info("message_info:")
    message_info = fetch_or_update_data("message_info", fetch_messages_direct, deviceSn, None, 1)  # Pass None for messageType
    logger.info("alert_info:")
    alert_info = fetch_or_update_data("alert_info", fetch_alerts, deviceSn)

    return {
        'success': True,
        'data': {
            'health_data': health_data,
            'device_info': device_info,
            'user_info': user_info,
            'message_info': message_info,
            'alert_info': alert_info
        }
    }
@app.route('/fetch_messages', methods=['GET'])
def fetch_messages(deviceSn=None, messageType=None, customerId=None):
    if deviceSn is None:
        deviceSn = request.args.get('deviceSn')
    if messageType is None:
        messageType = request.args.get('messageType')
    if customerId is None:
        customerId = request.args.get('customerId')
        print("fetch_messages::customerId:", customerId)
    return message_fetch_messages(deviceSn, messageType, customerId)

def fetch_messages_direct(deviceSn, messageType=None, customerId=1):
    # Directly call the message_fetch_messages function without relying on request
    return message_fetch_messages(deviceSn, messageType, customerId)

@app.route('/gather_device_info', methods=['GET'])
def gather_device_info(customer_id=None):
    if customer_id is None:
        customer_id = request.args.get('customer_id')
    return device_gather_device_info(customer_id)

@app.route('/fetch_devices_by_customer_id', methods=['GET'])
def fetch_devices_by_customer_id(customer_id=None):
    if customer_id is None:
        customer_id = request.args.get('customer_id')
    return device_fetch_devices_by_customer_id(customer_id)

@app.route('/get_health_stats')
def get_health_stats():
    dimension = request.args.get('dimension', 'day')
    org_id = request.args.get('orgId')
    user_id = request.args.get('userId')
    return jsonify(fetch_health_stats_by_dimension(org_id, user_id, dimension))

@app.route('/get_devices_by_orgIdAndUserId', methods=['GET'])
def get_devices_by_orgIdAndUserId(orgId=None, userId=None, customerId=None):
    if orgId is None:
        orgId = request.args.get('orgId')
    if userId is None:
        userId = normalize_param(request.args.get('userId'))
    if customerId is None:
        customerId = request.args.get('customerId')
    return fetch_devices_by_orgIdAndUserId(orgId, userId, customerId)
@app.route('/get_alerts_by_orgIdAndUserId', methods=['GET'])
def get_alerts_by_orgIdAndUserId(orgId=None, userId=None, severityLevel=None, customerId=None):
    try:
        # Only try to get from request.args if we're in a request context
        if request and hasattr(request, 'args'):
            if orgId is None:
                orgId = request.args.get('orgId')
            if userId is None:
                userId = normalize_param(request.args.get('userId'))
            if severityLevel is None:
                severityLevel = normalize_param(request.args.get('severityLevel'))
            if customerId is None:
                customerId = request.args.get('customerId')
        return alert_fetch_alerts_by_orgIdAndUserId(orgId, userId, severityLevel, customerId)
    except RuntimeError as e:
        # If we're outside a request context, just use the provided parameters
        return alert_fetch_alerts_by_orgIdAndUserId(orgId, userId, severityLevel)

@app.route('/api/alerts', methods=['GET'])
@log_api_request('/api/alerts', 'GET')
def api_get_alerts():
    """获取告警数据API - 标准格式
    
    查询优先级:
    1. user_id - 个人告警 (baseline, score, prediction, recommendation, profile)
    2. org_id - 部门级别汇总 
    3. customer_id - 租户级别汇总
    """
    try:
        # 获取查询参数
        user_id = request.args.get('userId') or request.args.get('user_id')
        org_id = request.args.get('orgId') or request.args.get('org_id')
        customer_id = request.args.get('customerId') or request.args.get('customer_id')
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        severity_level = request.args.get('severityLevel') or request.args.get('severity_level')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('pageSize', 20)) if request.args.get('pageSize') else None
        latest_only = request.args.get('latestOnly', '').lower() == 'true'
        
        # 查询优先级逻辑
        if user_id:
            # 个人级别告警查询
            result = alert_fetch_alerts_by_orgIdAndUserId(None, user_id, severity_level, customer_id)
            logger.info(f"基于userId查询告警数据: user_id={user_id}")
        elif org_id:
            # 部门级别告警查询
            result = alert_fetch_alerts_by_orgIdAndUserId(org_id, None, severity_level, customer_id)  
            logger.info(f"基于orgId查询告警数据: org_id={org_id}")
        elif customer_id:
            # 租户级别告警查询
            result = alert_fetch_alerts_by_orgIdAndUserId(customer_id, None, severity_level, customer_id)
            logger.info(f"基于customerId查询告警数据: customer_id={customer_id}")
        else:
            return jsonify({
                'success': False,
                'error': 'user_id, org_id 或 customer_id 参数至少需要提供一个'
            }), 400
        
        return result
        
    except Exception as e:
        logger.error(f"获取告警数据失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {'alerts': [], 'totalAlerts': 0}
        }), 500

@app.route('/api/devices', methods=['GET'])
@log_api_request('/api/devices', 'GET')  
def api_get_devices():
    """获取设备数据API - 标准格式
    
    查询优先级:
    1. user_id - 个人设备 (baseline, score, prediction, recommendation, profile)
    2. org_id - 部门级别汇总
    3. customer_id - 租户级别汇总
    """
    try:
        # 获取查询参数
        user_id = request.args.get('userId') or request.args.get('user_id')
        org_id = request.args.get('orgId') or request.args.get('org_id')
        customer_id = request.args.get('customerId') or request.args.get('customer_id')
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        device_type = request.args.get('deviceType')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('pageSize', 20)) if request.args.get('pageSize') else None
        latest_only = request.args.get('latestOnly', '').lower() == 'true'
        
        # 查询优先级逻辑
        if user_id:
            # 个人级别设备查询
            result = fetch_devices_by_orgIdAndUserId(None, user_id, customer_id)
            logger.info(f"基于userId查询设备数据: user_id={user_id}")
        elif org_id:
            # 部门级别设备查询
            result = fetch_devices_by_orgIdAndUserId(org_id, None, customer_id)
            logger.info(f"基于orgId查询设备数据: org_id={org_id}")
        elif customer_id:
            # 租户级别设备查询
            result = fetch_devices_by_orgIdAndUserId(customer_id, None, customer_id)
            logger.info(f"基于customerId查询设备数据: customer_id={customer_id}")
        else:
            return jsonify({
                'success': False,
                'error': 'user_id, org_id 或 customer_id 参数至少需要提供一个'
            }), 400
        
        return result
        
    except Exception as e:
        logger.error(f"获取设备数据失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {'devices': [], 'totalDevices': 0}
        }), 500

@app.route('/api/messages', methods=['GET'])
@log_api_request('/api/messages', 'GET')
def api_get_messages():
    """获取消息数据API - 标准格式
    
    查询优先级:
    1. user_id - 个人消息 (baseline, score, prediction, recommendation, profile)
    2. org_id - 部门级别汇总
    3. customer_id - 租户级别汇总
    """
    try:
        # 获取查询参数
        user_id = request.args.get('userId') or request.args.get('user_id')
        org_id = request.args.get('orgId') or request.args.get('org_id')  
        customer_id = request.args.get('customerId') or request.args.get('customer_id')
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        message_type = request.args.get('messageType')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('pageSize', 20)) if request.args.get('pageSize') else None
        latest_only = request.args.get('latestOnly', '').lower() == 'true'
        
        # 直接使用现有的消息查询函数
        result = message_fetch_messages_by_orgIdAndUserId(org_id, user_id, message_type, customer_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"获取消息数据失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {'messages': [], 'totalMessages': 0}
        }), 500

@app.route('/get_health_data_by_orgIdAndUserId', methods=['GET'])
def get_health_data_by_orgIdAndUserId(orgId=None, userId=None, customerId=None):
    if orgId is None:
        orgId = request.args.get('orgId')
    if userId is None:
        userId = request.args.get('userId')
    if customerId is None:
        customerId = request.args.get('customerId')
    return fetch_health_data_by_orgIdAndUserId(orgId, userId, customerId)
@app.route('/get_health_data_by_date', methods=['GET'])
def get_health_data_by_date(date=None,orgId=None,userId=None):
    if date is None:
        date = request.args.get('date')
    if orgId is None:
        orgId = request.args.get('orgId')
    if userId is None:
        userId = request.args.get('userId')
    return user_get_health_data_by_date(date, orgId, userId)
@app.route('/get_total_info', methods=['GET'])
def get_total_info(customer_id=None):
    """统一总数据获取接口-极致优化单一逻辑"""
    import time,concurrent.futures,json
    from datetime import datetime
    from flask import current_app
    
    start_time=time.time()
    customer_id=customer_id or request.args.get('customerId') or request.args.get('customer_id')
    if not customer_id:return jsonify({'success':False,'error':'缺少customer_id参数'}),400
    
    #缓存检查
    cache_key=f"total_unified:{customer_id}"
    try:
        if redis:  # 检查Redis是否可用
            cached=redis.get(cache_key)
            if cached:
                result=json.loads(cached)
                result['performance']['cached']=True
                result['performance']['response_time']=round(time.time()-start_time,3)
                api_logger.info('统一缓存命中',extra={'customer_id':customer_id})
                return jsonify(result)
    except Exception as e:
        system_logger.warning('缓存读取失败',extra={'error':str(e)})
    
    #统一并发查询-始终使用优化策略
    system_logger.info('统一并发查询模式',extra={'customer_id':customer_id})
    app_context=current_app._get_current_object()
    
    #导入底层函数
    from .alert import fetch_alerts_by_orgIdAndUserId as fetch_alerts
    from .message import fetch_messages_by_orgIdAndUserId as fetch_messages
    from .device import fetch_devices_by_orgIdAndUserId as fetch_devices
    from .user import get_user_info_by_orgIdAndUserId as fetch_users
    from .user_health_data import fetch_health_data_by_orgIdAndUserId as fetch_health_data
    
    #定义查询函数
    def query_with_context(name,func,**kwargs):
        with app_context.app_context():
            try:
                return func(orgId=customer_id,userId=None,**kwargs)
            except Exception as e:
                system_logger.error(f'{name}查询失败',extra={'customer_id':customer_id,'error':str(e)})
                return None
    
    def query_health():
        with app_context.app_context():
            try:
                return fetch_health_data(orgId=customer_id,userId=None)
            except Exception as e:
                system_logger.error('健康数据查询失败',extra={'customer_id':customer_id,'error':str(e)})
                return None
    
    def query_users():
        with app_context.app_context():
            try:
                #调用修复后的用户查询函数，添加customer_id参数
                print(f"🔍 get_total_info查询用户: orgId={customer_id}, userId=None")
                response = fetch_users(orgId=customer_id, userId=None, customer_id=customer_id)
                
                # 处理返回的响应格式
                if isinstance(response, dict) and response.get('success'):
                    users_data = response.get('data', {})
                    users_list = users_data.get('users', [])
                    
                    # 提取前端需要的统计数据
                    result_data = {
                        "users": users_list,
                        "totalUsers": users_data.get('totalUsers', len(users_list)),
                        "totalDevices": users_data.get('totalDevices', 0),
                        "departmentCount": users_data.get('departmentCount', {}),
                        "statusCount": users_data.get('statusCount', {}),
                        "deviceCount": users_data.get('deviceCount', {}),
                        "departmentStats": users_data.get('departmentStats', {})
                    }
                    
                    return {
                        "success": True,
                        "data": result_data
                    }
                elif isinstance(response, list):
                    # 兼容旧格式，直接是用户列表，需要计算统计信息
                    users_list = response
                    
                    # 简单统计处理
                    device_count = {}
                    dept_count = {}
                    
                    for user in users_list:
                        device_sn = user.get('device_sn', '')
                        if device_sn and device_sn != '-' and device_sn.strip():
                            device_count[device_sn] = 1
                        
                        dept_name = user.get('department_name') or user.get('dept_name')
                        if dept_name:
                            dept_count[dept_name] = dept_count.get(dept_name, 0) + 1
                    
                    result_data = {
                        "users": users_list,
                        "totalUsers": len(users_list),
                        "totalDevices": len(device_count),
                        "departmentCount": dept_count,
                        "statusCount": {},
                        "deviceCount": device_count,
                        "departmentStats": {}
                    }
                    
                    return {
                        "success": True,
                        "data": result_data
                    }
                else:
                    system_logger.warning('用户查询返回格式异常', extra={'customer_id': customer_id, 'response_type': type(response)})
                    return {"success": False, "error": "返回格式异常", "data": {"users": [], "totalUsers": 0, "totalDevices": 0, "departmentCount": {}, "statusCount": {}, "deviceCount": {}, "departmentStats": {}}}
                    
            except Exception as e:
                system_logger.error('用户查询失败', extra={'customer_id': customer_id, 'error': str(e)})
                return {"success": False, "error": str(e), "data": {"users": [], "totalUsers": 0, "totalDevices": 0, "departmentCount": {}, "statusCount": {}, "deviceCount": {}, "departmentStats": {}}}
    
    #并发执行所有查询
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures={
                'alert_info':executor.submit(query_with_context,'告警',fetch_alerts,severityLevel=None),
                'message_info':executor.submit(query_with_context,'消息',fetch_messages,messageType=None),
                'device_info':executor.submit(query_with_context,'设备',fetch_devices),
                'health_data':executor.submit(query_health),
                'user_info':executor.submit(query_users)
            }
            
            results,errors={},{}
            for key,future in futures.items():
                try:
                    results[key]=future.result(timeout=3)#3秒超时
                    system_logger.info(f'{key}查询完成',extra={'customer_id':customer_id,'has_data':results[key] is not None})
                except Exception as e:
                    errors[key]=str(e)
                    results[key]=None
                    system_logger.error(f'{key}查询异常',extra={'customer_id':customer_id,'error':str(e)})
    except Exception as e:
        system_logger.error('并发查询失败，降级为空结果',extra={'customer_id':customer_id,'error':str(e)})
        results={'alert_info':None,'message_info':None,'device_info':None,'health_data':None,'user_info':None}
        errors={'executor_error':str(e)}
    
    #统一数据提取
    def extract(data):
        if not data:return None
        if hasattr(data,'get_json'):return data.get_json().get('data')
        if isinstance(data,dict):return data.get('data',data)
        return data
    
    response_data={
        'success':True,
        'data':{k:extract(v) for k,v in results.items()},
        'performance':{
            'cached':False,
            'response_time':round(time.time()-start_time,3),
            'unified_approach':True,#标记使用统一方法
            'errors':errors if errors else None
        }
    }
    
    #缓存结果
    try:
        if redis:  # 检查Redis是否可用
            redis.setex(cache_key,30,json.dumps(response_data,default=str))
            api_logger.info('统一缓存已保存',extra={'customer_id':customer_id,'ttl':30})
        else:
            system_logger.info('Redis不可用，跳过缓存',extra={'customer_id':customer_id})
    except Exception as e:
        system_logger.warning('缓存保存失败',extra={'error':str(e)})
    
    return jsonify(response_data)

@app.route('/api/cache/status', methods=['GET']) #缓存状态检查接口
def cache_status():
    try:
        customer_id = request.args.get('customer_id', '1')
        
        cache_status_dict = {}
        
        # 检查各类缓存状态
        cache_keys = [
            f"total_info_simple:{customer_id}",  # 更新为新的缓存键
            f"users_by_org:{customer_id}",
            f"departments_by_org:{customer_id}",
            f"health_data_opt:{customer_id}:all"
        ]
        
        cache_names = [
            "总览数据缓存",
            "用户数据缓存", 
            "部门数据缓存",
            "健康数据缓存"
        ]
        
        for i, cache_key in enumerate(cache_keys):
            try:
                cached_data = redis.get(cache_key)
                # 修复TTL方法调用
                try:
                    if hasattr(redis, 'redis_client'):
                        ttl = redis.redis_client.ttl(cache_key)
                    else:
                        ttl = -1  # 无法获取TTL时返回-1
                except:
                    ttl = -1
                
                cache_status_dict[cache_names[i]] = {
                    'key': cache_key,
                    'exists': cached_data is not None,
                    'ttl': ttl if ttl > 0 else None,
                    'size': len(cached_data) if cached_data else 0
                }
            except Exception as e:
                cache_status_dict[cache_names[i]] = {
                    'key': cache_key,
                    'exists': False,
                    'error': str(e)
                }
        
        # 统计缓存效果
        total_caches = len(cache_status_dict)
        active_caches = sum(1 for status in cache_status_dict.values() if status.get('exists', False))
        cache_hit_rate = round((active_caches / total_caches) * 100, 1) if total_caches > 0 else 0
        
        return jsonify({
            'success': True,
            'customer_id': customer_id,
            'cache_status': cache_status_dict,
            'summary': {
                'total_caches': total_caches,
                'active_caches': active_caches,
                'cache_hit_rate': f"{cache_hit_rate}%",
                'redis_connected': True
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '缓存状态检查失败'
        }), 500

@app.route("/device_analysis")  # 新增设备分析页面路由
def device_analysis():
    """设备分析系统页面"""
    customerId = request.args.get('customerId', '1')
    orgId = request.args.get('orgId', customerId)
    userId = request.args.get('userId', '')
    return render_template("device_view.html", customerId=customerId, orgId=orgId, userId=userId)

@app.route("/device_dashboard")  # 专业设备监控大屏路由
def device_dashboard():
    """智能手表设备实时监控大屏"""
    customerId = request.args.get('customerId', '1')
    orgId = request.args.get('orgId', customerId)
    return render_template("device_dashboard.html", customerId=customerId, orgId=orgId)

@app.route('/api/devices/analysis', methods=['GET'])  # 设备分析数据接口
def api_get_device_analysis():
    """设备分析数据接口 - 重构后使用模块化实现"""
    try:
        orgId = request.args.get('orgId', '1')
        userId = request.args.get('userId', '')
        timeRange = request.args.get('timeRange', '24h')
        
        result, status_code = get_device_analysis_data(orgId, userId, timeRange)
        return jsonify(result), status_code
        
    except Exception as e:
        api_logger.error(f"设备分析数据获取失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def generate_device_analysis_data(devices, timeRange):
    """生成设备分析数据"""
    import random
    from datetime import datetime, timedelta
    
    # 基础统计
    total_devices = len(devices)
    online_devices = len([d for d in devices if d.get('status') == 'ACTIVE'])
    charging_devices = len([d for d in devices if d.get('charging_status') == 'CHARGING'])
    worn_devices = len([d for d in devices if d.get('wearable_status') == 'WORN'])
    low_battery_devices = len([d for d in devices if int(d.get('battery_level', 0)) <= 20])
    
    # 状态分布
    status_distribution = {
        'online': online_devices,
        'offline': total_devices - online_devices,
        'standby': random.randint(0, total_devices // 10),
        'error': random.randint(0, total_devices // 20)
    }
    
    # 生成时间序列数据
    time_points = generate_time_points(timeRange)
    
    # 电池趋势数据
    battery_trends = []
    for i, time_point in enumerate(time_points):
        avg_battery = 75 + random.randint(-20, 20) - (i * 2)  # 模拟电量下降趋势
        avg_battery = max(20, min(100, avg_battery))
        
        battery_trends.append({
            'time': time_point,
            'avgBattery': avg_battery,
            'lowBatteryCount': random.randint(0, low_battery_devices + 5)
        })
    
    # 充电行为分析（按小时统计）
    charging_analysis = []
    for hour in range(24):
        # 充电高峰期一般在晚上和凌晨
        peak_factor = 1.5 if 22 <= hour or hour <= 6 else 1.0
        charging_count = int(charging_devices * peak_factor * random.uniform(0.3, 1.2))
        
        charging_analysis.append({
            'hour': f"{hour:02d}:00",
            'chargingCount': charging_count,
            'completedCount': random.randint(charging_count // 3, charging_count)
        })
    
    # 佩戴状态趋势
    wearing_trends = []
    for i, time_point in enumerate(time_points):
        # 工作时间佩戴率较高
        base_worn_rate = 70 if 8 <= datetime.now().hour <= 18 else 40
        worn_rate = base_worn_rate + random.randint(-15, 15)
        active_rate = worn_rate * random.uniform(0.6, 0.9)
        
        wearing_trends.append({
            'time': time_point,
            'wornRate': max(0, min(100, worn_rate)),
            'activeRate': max(0, min(100, active_rate))
        })
    
    # 系统版本分布
    version_distribution = {}
    version_templates = [
        "v2.1.0", "v2.0.8", "v2.0.6", "v1.9.2", "v1.8.5",
        "v2.1.1", "v2.0.9", "v1.9.0", "v1.8.8", "v1.7.3"
    ]
    
    for device in devices:
        version = device.get('system_software_version', random.choice(version_templates))
        # 简化版本号
        short_version = version.split(' ')[0] if ' ' in version else version[:10]
        version_distribution[short_version] = version_distribution.get(short_version, 0) + 1
    
    # 如果没有设备数据，生成模拟版本分布
    if not version_distribution:
        for version in version_templates[:5]:
            version_distribution[version] = random.randint(50, 200)
    
    # 计算趋势数据
    trends = {
        'deviceChange': f"+{random.randint(1, 10)}台" if random.random() > 0.3 else f"-{random.randint(1, 5)}台",
        'onlineRate': f"{(online_devices / total_devices * 100):.1f}%" if total_devices > 0 else "0%",
        'batteryHealth': f"{random.randint(75, 95)}%" if total_devices > 0 else "0%",
        'chargingRate': f"{(charging_devices / total_devices * 100):.1f}%" if total_devices > 0 else "0%",
        'wearRate': f"{(worn_devices / total_devices * 100):.1f}%" if total_devices > 0 else "0%",
        'alertTrend': "稳定" if low_battery_devices < 5 else "上升" if low_battery_devices > 20 else "轻微上升"
    }
    
    # 设备详情列表（添加更多字段）
    device_details = []
    for device in devices[:50]:  # 限制显示前50台设备
        device_details.append({
            'deviceSn': device.get('serial_number', device.get('device_sn', '未知')),
            'status': device.get('status', 'OFFLINE'),
            'batteryLevel': device.get('battery_level', random.randint(20, 100)),
            'chargingStatus': device.get('charging_status', 'NOT_CHARGING'),
            'wearableStatus': device.get('wearable_status', 'NOT_WORN'),
            'lastSeen': device.get('last_seen', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            'version': device.get('system_software_version', random.choice(version_templates))
        })
    
    return {
        'devices': device_details,
        'statistics': {
            'totalDevices': total_devices,
            'onlineDevices': online_devices,
            'chargingDevices': charging_devices,
            'wornDevices': worn_devices,
            'lowBatteryDevices': low_battery_devices,
            'alertCount': low_battery_devices + (total_devices - online_devices)
        },
        'trends': trends,
        'statusDistribution': status_distribution,
        'batteryTrends': battery_trends,
        'chargingAnalysis': charging_analysis,
        'wearingTrends': wearing_trends,
        'versionDistribution': version_distribution,
        'timeRange': timeRange,
        'generatedAt': datetime.now().isoformat()
    }

def generate_time_points(timeRange):
    """根据时间范围生成时间点"""
    from datetime import datetime, timedelta
    
    now = datetime.now()
    time_points = []
    
    if timeRange == '1h':
        # 每5分钟一个点
        for i in range(12):
            time_point = (now - timedelta(minutes=i*5)).strftime('%H:%M')
            time_points.insert(0, time_point)
    elif timeRange == '6h':
        # 每30分钟一个点
        for i in range(12):
            time_point = (now - timedelta(minutes=i*30)).strftime('%H:%M')
            time_points.insert(0, time_point)
    elif timeRange == '24h':
        # 每2小时一个点
        for i in range(12):
            time_point = (now - timedelta(hours=i*2)).strftime('%m-%d %H:%M')
            time_points.insert(0, time_point)
    elif timeRange == '7d':
        # 每天一个点
        for i in range(7):
            time_point = (now - timedelta(days=i)).strftime('%m-%d')
            time_points.insert(0, time_point)
    
    return time_points

@app.route("/device_detailed_analysis")  # 设备详细分析页面路由
def device_detailed_analysis():
    """设备详细分析页面"""
    customerId = request.args.get('customerId', '1')
    orgId = request.args.get('orgId', '1')
    return render_template("device_detailed_analysis.html", customerId=customerId, orgId=orgId)

@app.route('/<template>')
def render_template_view(template):
    if template in ['alert_view.html', 'message_view.html', 'device_view.html',
                   'health_view.html', 'user_view.html', 'user_profile.html', 'user_health_data.html', 'user_health_data_analysis.html']:
        return render_template(template)
    return "Template not found", 404

# 添加缺失的健康数据接口
@app.route('/health_data/score', methods=['GET'])  #健康评分接口 - 支持deviceSn直接获取
def health_data_score():
    try:
        orgId = request.args.get('orgId')
        startDate = request.args.get('startDate')
        endDate = request.args.get('endDate')
        userId = request.args.get('userId')
        deviceSn = request.args.get('deviceSn')  # 新增deviceSn参数支持
        
        # 优先使用deviceSn获取userId，避免多次网络请求
        if deviceSn and not userId:
            api_logger.info(f"🔍 通过deviceSn获取健康评分: {deviceSn}")
            try:
                from .user import get_user_id_by_deviceSn
                userId = get_user_id_by_deviceSn(deviceSn)
                if not userId:
                    api_logger.warning(f"⚠️ 设备{deviceSn}未找到对应用户")
                    return jsonify({'success': False, 'error': f'设备{deviceSn}未找到对应用户'}), 404
                api_logger.info(f"✅ 设备{deviceSn}对应用户ID: {userId}")
            except Exception as e:
                api_logger.error(f"❌ 获取设备用户信息失败: {e}")
                return jsonify({'success': False, 'error': f'获取设备用户信息失败: {str(e)}'}), 500
        
        # 主屏支持只提供orgId，个人屏需要userId或deviceSn
        if not userId and not orgId:
            api_logger.error("❌ 缺少orgId或userId/deviceSn参数")
            return jsonify({'success': False, 'error': '缺少orgId或userId/deviceSn参数'}), 400
            
        api_logger.info(f"📊 调用健康评分计算: orgId={orgId}, userId={userId}, deviceSn={deviceSn}")
        result = fetch_health_profile_by_orgIdAndUserId(orgId, userId, startDate, endDate)
        
        # 在返回数据中添加设备信息
        if result.get('success') and deviceSn:
            result['data']['deviceSn'] = deviceSn
            api_logger.info(f"✅ 健康评分计算完成，设备: {deviceSn}")
            
        return jsonify(result)  # 保持jsonify因为函数返回字典
    except Exception as e:
        api_logger.error(f"健康评分接口错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get_all_health_data_by_orgIdAndUserId', methods=['GET'])  #全量健康数据接口
def get_all_health_data_by_orgIdAndUserId_route():
    try:
        orgId = request.args.get('orgId')
        startDate = request.args.get('startDate')
        endDate = request.args.get('endDate')
        userId = request.args.get('userId')
        result = fetch_all_health_data_by_orgIdAndUserId(orgId, userId, startDate, endDate)
        return jsonify(result)  # 保持jsonify因为函数返回字典
    except Exception as e:
        api_logger.error(f"全量健康数据接口错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/device/user_org', methods=['GET'])  #根据deviceSn获取用户orgId和userId的API接口
def get_user_org_by_device():
    try:
        deviceSn = request.args.get('deviceSn')
        if not deviceSn:
            return jsonify({'success': False, 'error': 'deviceSn参数必需'})
            
        from .device import fetch_user_org_by_deviceSn
        userId, orgId = fetch_user_org_by_deviceSn(deviceSn)
        
        if userId and orgId:
            return jsonify({
                'success': True,
                'userId': str(userId),  # 转为字符串避免JavaScript精度丢失
                'orgId': str(orgId),    # 保持一致性
                'deviceSn': deviceSn
            })
        else:
            return jsonify({
                'success': False,
                'error': '未找到设备绑定的用户信息',
                'deviceSn': deviceSn
            })
    except Exception as e:
        print(f"获取用户组织信息API错误: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/health_data/trends', methods=['GET'])  #健康趋势接口
def health_data_trends():
    try:
        orgId = request.args.get('orgId')
        startDate = request.args.get('startDate')
        endDate = request.args.get('endDate')
        userId = request.args.get('userId')
        result = get_health_trends(orgId, userId, startDate, endDate)  #添加userId参数并获取返回值
        return result  #直接返回，因为get_health_trends已经返回了jsonify结果
    except Exception as e:
        api_logger.error(f"健康趋势接口错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/health_data/chart/baseline', methods=['GET'])  #健康基线图表接口
def health_data_chart_baseline():
    try:
        orgId = request.args.get('orgId')
        startDate = request.args.get('startDate')
        endDate = request.args.get('endDate')
        userId = request.args.get('userId')
        result = get_health_baseline(orgId, userId, startDate, endDate)
        return result  # 直接返回，因为get_health_baseline已经返回了jsonify结果
    except Exception as e:
        api_logger.error(f"健康基线图表接口错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health/analysis/comprehensive', methods=['GET'])
def get_comprehensive_health_analysis():
    """综合健康分析接口 - 支持多种查询参数"""
    try:
        device_sn = request.args.get('deviceSn')
        customer_id = request.args.get('customerId')
        user_id = request.args.get('userId')
        days = int(request.args.get('days', 7))
        
        # 支持多种参数组合
        if not device_sn and not customer_id and not user_id:
            return jsonify({
                'success': False,
                'error': '需要提供 deviceSn 或 customerId 或 userId 参数'
            }), 400
            
        # 如果提供customerId，返回租户级别的分析数据
        if customer_id and not device_sn and not user_id:
            return get_customer_comprehensive_analysis(customer_id, days)
        
        # 获取用户信息
        from .user import get_user_id_by_deviceSn
        user_id = get_user_id_by_deviceSn(device_sn)
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': f'设备{device_sn}未找到对应用户'
            }), 404
        
        # 获取用户组织信息
        from .device import get_device_user_org_info
        org_info = get_device_user_org_info(device_sn)
        
        if not org_info or not org_info.get('success'):
            return jsonify({
                'success': False,
                'error': f'设备{device_sn}未找到对应组织: {org_info.get("message", "未知错误") if org_info else "查询失败"}'
            }), 404
            
        org_id = org_info.get('org_id')
        
        # 计算日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        api_logger.info(f"📊 综合健康分析: deviceSn={device_sn}, userId={user_id}, orgId={org_id}, days={days}")
        
        # 获取健康数据
        health_result = get_all_health_data_optimized(
            orgId=org_id,
            userId=user_id,
            startDate=start_date_str,
            endDate=end_date_str,
            latest_only=False
        )
        
        if not health_result.get('success'):
            return jsonify({
                'success': False,
                'error': '获取健康数据失败'
            }), 500
            
        health_data = health_result.get('data', {}).get('healthData', [])
        
        # 分析健康数据并生成预测、评分和建议
        analysis_result = analyze_health_comprehensive(health_data, days)
        
        return jsonify({
            'success': True,
            'data': {
                'deviceSn': device_sn,
                'userId': str(user_id),
                'orgId': str(org_id),
                'analysisDate': datetime.now().isoformat(),
                'dataPoints': len(health_data),
                'analysisPeriod': f'{days}天',
                'dateRange': {
                    'startDate': start_date_str,
                    'endDate': end_date_str
                },
                **analysis_result
            }
        })
        
    except Exception as e:
        api_logger.error(f"❌ 综合健康分析失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'综合健康分析失败: {str(e)}'
        }), 500

def get_customer_comprehensive_analysis(customer_id, days=7):
    """按租户ID获取综合健康分析数据"""
    try:
        from .models import UserInfo
        from datetime import datetime, timedelta
        import statistics
        
        # 获取租户下所有用户
        users = UserInfo.query.filter_by(
            customer_id=customer_id, 
            is_deleted=False, 
            status='1'
        ).all()
        
        if not users:
            return jsonify({
                'success': False,
                'error': f'租户{customer_id}下未找到有效用户'
            }), 404
        
        # 计算日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # 汇总分析数据
        all_health_data = []
        user_analyses = []
        aggregated_stats = {
            'total_users': len(users),
            'active_users': 0,
            'avg_heart_rate': 0,
            'avg_blood_oxygen': 0,
            'avg_temperature': 0,
            'total_steps': 0,
            'health_scores': [],
            'health_distribution': {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0}
        }
        
        for user in users:
            try:
                # 获取用户健康数据
                user_health_result = get_all_health_data_optimized(
                    orgId=user.org_id or customer_id,  # 使用用户的组织ID或customer_id
                    userId=user.id,
                    startDate=start_date_str,
                    endDate=end_date_str,
                    latest_only=False
                )
                
                if user_health_result.get('success'):
                    user_health_data = user_health_result.get('data', {}).get('healthData', [])
                    if user_health_data:
                        aggregated_stats['active_users'] += 1
                        all_health_data.extend(user_health_data)
                        
                        # 分析单个用户数据
                        user_analysis = analyze_health_comprehensive(user_health_data, days)
                        user_analysis['user_info'] = {
                            'user_id': user.id,
                            'user_name': user.user_name,
                            'device_sn': user.device_sn
                        }
                        user_analyses.append(user_analysis)
                        
                        # 汇总健康评分
                        if user_analysis.get('healthScore', {}).get('overall'):
                            score = user_analysis['healthScore']['overall']
                            aggregated_stats['health_scores'].append(score)
                            
                            # 统计健康等级分布
                            if score >= 90:
                                aggregated_stats['health_distribution']['excellent'] += 1
                            elif score >= 80:
                                aggregated_stats['health_distribution']['good'] += 1
                            elif score >= 70:
                                aggregated_stats['health_distribution']['fair'] += 1
                            else:
                                aggregated_stats['health_distribution']['poor'] += 1
                        
            except Exception as user_error:
                api_logger.warning(f"分析用户{user.id}健康数据失败: {user_error}")
                continue
        
        # 计算租户级别的整体分析
        if all_health_data:
            tenant_analysis = analyze_health_comprehensive(all_health_data, days)
            
            # 计算统计数据
            if aggregated_stats['health_scores']:
                aggregated_stats['avg_health_score'] = round(statistics.mean(aggregated_stats['health_scores']), 1)
                aggregated_stats['median_health_score'] = round(statistics.median(aggregated_stats['health_scores']), 1)
                aggregated_stats['max_health_score'] = max(aggregated_stats['health_scores'])
                aggregated_stats['min_health_score'] = min(aggregated_stats['health_scores'])
        else:
            tenant_analysis = {
                'healthScore': {'overall': 60, 'category': '数据不足'},
                'healthPrediction': {'trend': '数据不足', 'confidence': 'low'},
                'healthAdvice': ['请确保设备正常佩戴', '定期同步健康数据']
            }
        
        return jsonify({
            'success': True,
            'data': {
                'customerId': customer_id,
                'analysisDate': datetime.now().isoformat(),
                'dataPoints': len(all_health_data),
                'analysisPeriod': f'{days}天',
                'dateRange': {
                    'startDate': start_date_str,
                    'endDate': end_date_str
                },
                'aggregatedStats': aggregated_stats,
                'tenantAnalysis': tenant_analysis,
                'userAnalyses': user_analyses[:10]  # 限制返回前10个用户的详细分析
            }
        })
        
    except Exception as e:
        api_logger.error(f"租户综合健康分析失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def analyze_health_comprehensive(health_data, analysis_days):
    """分析健康数据并生成预测、评分和建议"""
    if not health_data:
        return {
            'healthScore': {'overall': 60, 'category': '一般'},
            'healthPrediction': {'trend': '数据不足', 'confidence': 'low'},
            'healthAdvice': ['请保持正常作息', '定期进行健康检查']
        }
    
    # 计算各项健康指标的统计数据
    heart_rates = [float(item.get('heart_rate', 0)) for item in health_data if item.get('heart_rate')]
    blood_oxygen = [float(item.get('blood_oxygen', 0)) for item in health_data if item.get('blood_oxygen')]
    temperatures = [float(item.get('temperature', 0)) for item in health_data if item.get('temperature')]
    steps = [int(item.get('step', 0)) for item in health_data if item.get('step')]
    
    # 计算健康评分
    health_score = calculate_health_score(heart_rates, blood_oxygen, temperatures, steps)
    
    # 生成健康预测
    health_prediction = generate_health_prediction(heart_rates, blood_oxygen, temperatures, analysis_days)
    
    # 生成健康建议
    health_advice = generate_health_advice(heart_rates, blood_oxygen, temperatures, steps)
    
    return {
        'healthScore': health_score,
        'healthPrediction': health_prediction,
        'healthAdvice': health_advice
    }

def calculate_health_score(heart_rates, blood_oxygen, temperatures, steps):
    """计算综合健康评分"""
    score = 0
    factors = []
    
    # 心率评分 (30分)
    if heart_rates:
        avg_hr = sum(heart_rates) / len(heart_rates)
        if 60 <= avg_hr <= 100:
            hr_score = 30
        elif 50 <= avg_hr < 60 or 100 < avg_hr <= 110:
            hr_score = 25
        else:
            hr_score = 15
        score += hr_score
        factors.append(f'心率: {avg_hr:.1f}bpm')
    
    # 血氧评分 (25分)
    if blood_oxygen:
        avg_spo2 = sum(blood_oxygen) / len(blood_oxygen)
        if avg_spo2 >= 95:
            spo2_score = 25
        elif avg_spo2 >= 90:
            spo2_score = 20
        else:
            spo2_score = 10
        score += spo2_score
        factors.append(f'血氧: {avg_spo2:.1f}%')
    
    # 体温评分 (20分)
    if temperatures:
        avg_temp = sum(temperatures) / len(temperatures)
        if 36.0 <= avg_temp <= 37.5:
            temp_score = 20
        else:
            temp_score = 15
        score += temp_score
        factors.append(f'体温: {avg_temp:.1f}°C')
    
    # 运动评分 (25分)
    if steps:
        avg_steps = sum(steps) / len(steps)
        if avg_steps >= 8000:
            step_score = 25
        elif avg_steps >= 5000:
            step_score = 20
        elif avg_steps >= 3000:
            step_score = 15
        else:
            step_score = 10
        score += step_score
        factors.append(f'日均步数: {avg_steps:.0f}步')
    
    # 确定健康等级
    if score >= 85:
        category = '优秀'
    elif score >= 70:
        category = '良好'
    elif score >= 55:
        category = '一般'
    else:
        category = '需关注'
    
    return {
        'overall': min(100, score),
        'category': category,
        'factors': factors
    }

def generate_health_prediction(heart_rates, blood_oxygen, temperatures, days):
    """生成健康趋势预测"""
    if not heart_rates or len(heart_rates) < 3:
        return {
            'trend': '数据不足',
            'confidence': 'low',
            'details': '需要更多数据进行趋势分析'
        }
    
    # 简单的趋势分析
    recent_data = heart_rates[-7:] if len(heart_rates) >= 7 else heart_rates
    early_data = heart_rates[:7] if len(heart_rates) >= 14 else heart_rates[:len(heart_rates)//2]
    
    if not early_data:
        early_data = recent_data[:len(recent_data)//2]
    
    recent_avg = sum(recent_data) / len(recent_data)
    early_avg = sum(early_data) / len(early_data)
    
    if recent_avg > early_avg + 5:
        trend = '心率呈上升趋势'
        confidence = 'medium'
    elif recent_avg < early_avg - 5:
        trend = '心率呈下降趋势'
        confidence = 'medium'
    else:
        trend = '心率保持稳定'
        confidence = 'high'
    
    return {
        'trend': trend,
        'confidence': confidence,
        'details': f'基于{days}天数据分析，共{len(heart_rates)}个数据点'
    }

def generate_health_advice(heart_rates, blood_oxygen, temperatures, steps):
    """生成个性化健康建议"""
    advice = []
    
    # 心率建议
    if heart_rates:
        avg_hr = sum(heart_rates) / len(heart_rates)
        if avg_hr > 100:
            advice.append('您的平均心率偏高，建议减少剧烈运动，保持放松心态')
        elif avg_hr < 60:
            advice.append('您的心率偏低，建议适当增加有氧运动')
        else:
            advice.append('您的心率正常，请继续保持良好的运动习惯')
    
    # 血氧建议
    if blood_oxygen:
        avg_spo2 = sum(blood_oxygen) / len(blood_oxygen)
        if avg_spo2 < 95:
            advice.append('血氧饱和度偏低，建议多做深呼吸练习，必要时咨询医生')
        else:
            advice.append('血氧水平良好，请保持规律的呼吸练习')
    
    # 运动建议
    if steps:
        avg_steps = sum(steps) / len(steps)
        if avg_steps < 5000:
            advice.append('日常活动量不足，建议每天至少步行8000步')
        elif avg_steps > 15000:
            advice.append('运动量很充足，注意适度休息避免过度疲劳')
        else:
            advice.append('运动量适中，请继续保持')
    
    # 通用建议
    advice.extend([
        '保持规律作息，确保充足睡眠',
        '注意饮食均衡，多吃蔬菜水果',
        '定期监测健康数据，及时发现异常'
    ])
    
    return advice[:5]  # 最多返回5条建议

@app.route('/api/health/trends/analysis', methods=['GET'])
def get_health_trends_analysis():
    """健康数据趋势分析接口：提供前端图表所需的结构化数据"""
    try:
        deviceSn = request.args.get('deviceSn')
        timeRange = request.args.get('timeRange', '24h')  # 1h, 6h, 24h, 7d, 30d
        
        if not deviceSn:
            return jsonify({
                'success': False,
                'error': 'deviceSn参数是必需的'
            }), 400
            
        # 获取用户ID和组织ID
        from .device import fetch_user_org_by_deviceSn
        userId, orgId = fetch_user_org_by_deviceSn(deviceSn)
        
        if not userId or not orgId:
            return jsonify({
                'success': False,
                'error': '未找到设备对应的用户信息'
            }), 404
            
        # 根据时间范围计算起止时间
        end_date = datetime.now()
        time_ranges = {
            '1h': timedelta(hours=1),
            '6h': timedelta(hours=6), 
            '24h': timedelta(hours=24),
            '7d': timedelta(days=7),
            '30d': timedelta(days=30)
        }
        
        start_date = end_date - time_ranges.get(timeRange, timedelta(hours=24))
        
        # 使用get_all_health_data_optimized获取健康数据
        health_result = get_all_health_data_optimized(
            orgId=orgId,
            userId=userId,
            startDate=start_date.strftime('%Y-%m-%d %H:%M:%S'),
            endDate=end_date.strftime('%Y-%m-%d %H:%M:%S'),
            latest_only=False
        )
        
        if not health_result.get('success'):
            return jsonify({
                'success': False,
                'error': '获取健康数据失败'
            }), 500
            
        health_data = health_result.get('data', {}).get('healthData', [])
        
        # 进行趋势分析并格式化为前端所需的数据结构
        trends_analysis = analyze_health_trends_comprehensive(health_data, timeRange)
        
        return jsonify({
            'success': True,
            'data': {
                'deviceSn': deviceSn,
                'timeRange': timeRange,
                'startDate': start_date.isoformat(),
                'endDate': end_date.isoformat(),
                'dataPoints': len(health_data),
                **trends_analysis
            }
        })
        
    except Exception as e:
        api_logger.error(f"健康趋势分析接口错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def analyze_health_trends_comprehensive(health_data, timeRange):
    """综合健康趋势分析算法"""
    if not health_data:
        return generate_fallback_trends_data(timeRange)
    
    # 按时间排序数据
    health_data.sort(key=lambda x: x.get('timestamp', ''))
    
    # 提取各项指标的时间序列数据
    heart_rates = []
    blood_oxygen = []
    temperatures = []
    blood_pressure_high = []
    blood_pressure_low = []
    steps = []
    timestamps = []
    
    for item in health_data:
        timestamp = item.get('timestamp')
        if timestamp:
            timestamps.append(timestamp)
            heart_rates.append(float(item.get('heart_rate', 0)) if item.get('heart_rate') else None)
            blood_oxygen.append(float(item.get('blood_oxygen', 0)) if item.get('blood_oxygen') else None)
            temperatures.append(float(item.get('temperature', 0)) if item.get('temperature') else None)
            blood_pressure_high.append(float(item.get('pressure_high', 0)) if item.get('pressure_high') else None)
            blood_pressure_low.append(float(item.get('pressure_low', 0)) if item.get('pressure_low') else None)
            steps.append(int(item.get('step', 0)) if item.get('step') else None)
    
    # 执行趋势分析算法
    trends_result = calculate_health_trends(
        timestamps, heart_rates, blood_oxygen, temperatures,
        blood_pressure_high, blood_pressure_low, steps, timeRange
    )
    
    return trends_result

def calculate_health_trends(timestamps, heart_rates, blood_oxygen, temperatures, 
                          bp_high, bp_low, steps, timeRange):
    """标准健康数据趋势分析算法"""
    
    # 1. 数据预处理和清洗
    def clean_data(values):
        """清洗数据，移除None值并进行异常值检测"""
        clean_values = [v for v in values if v is not None and v > 0]
        if len(clean_values) < 2:
            return clean_values
            
        # 使用四分位数方法检测异常值
        clean_values.sort()
        q1 = clean_values[len(clean_values)//4]
        q3 = clean_values[3*len(clean_values)//4]
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        return [v for v in clean_values if lower_bound <= v <= upper_bound]
    
    # 清洗各项数据
    clean_hr = clean_data(heart_rates)
    clean_spo2 = clean_data(blood_oxygen)
    clean_temp = clean_data(temperatures)
    clean_bp_h = clean_data(bp_high)
    clean_bp_l = clean_data(bp_low)
    clean_steps = clean_data(steps)
    
    # 2. 时间序列数据格式化（ECharts格式）
    def format_time_series(timestamps, values, default_value=0):
        """格式化为ECharts时间序列数据"""
        series_data = []
        for i, timestamp in enumerate(timestamps):
            if i < len(values) and values[i] is not None:
                series_data.append([timestamp, values[i]])
            else:
                series_data.append([timestamp, default_value])
        return series_data
    
    chart_data = {
        'heartRate': format_time_series(timestamps, heart_rates, 75),
        'bloodOxygen': format_time_series(timestamps, blood_oxygen, 98),
        'temperature': format_time_series(timestamps, temperatures, 36.5),
        'bloodPressureHigh': format_time_series(timestamps, bp_high, 120),
        'bloodPressureLow': format_time_series(timestamps, bp_low, 80),
        'steps': format_time_series(timestamps, steps, 0)
    }
    
    # 3. 统计分析
    def calculate_stats(values):
        """计算基本统计指标"""
        if not values:
            return {'avg': 0, 'min': 0, 'max': 0, 'trend': 'stable', 'change': 0}
            
        avg = sum(values) / len(values)
        min_val = min(values)
        max_val = max(values)
        
        # 趋势计算：比较前半段和后半段的平均值
        if len(values) >= 4:
            mid_point = len(values) // 2
            first_half_avg = sum(values[:mid_point]) / mid_point
            second_half_avg = sum(values[mid_point:]) / (len(values) - mid_point)
            change_percent = ((second_half_avg - first_half_avg) / first_half_avg) * 100
            
            if change_percent > 5:
                trend = 'rising'
            elif change_percent < -5:
                trend = 'falling'
            else:
                trend = 'stable'
        else:
            trend = 'stable'
            change_percent = 0
            
        return {
            'avg': round(avg, 2),
            'min': min_val,
            'max': max_val,
            'trend': trend,
            'change': round(change_percent, 2)
        }
    
    # 计算各项指标的统计信息
    stats = {
        'heartRate': calculate_stats(clean_hr),
        'bloodOxygen': calculate_stats(clean_spo2),
        'temperature': calculate_stats(clean_temp),
        'bloodPressureHigh': calculate_stats(clean_bp_h),
        'bloodPressureLow': calculate_stats(clean_bp_l),
        'steps': calculate_stats(clean_steps)
    }
    
    # 4. 健康状态评估
    def assess_health_status(stats):
        """根据统计数据评估健康状态"""
        score = 100
        warnings = []
        
        # 心率评估
        hr_avg = stats['heartRate']['avg']
        if hr_avg > 100 or hr_avg < 60:
            score -= 15
            warnings.append(f"心率异常: 平均{hr_avg}bpm")
        
        # 血氧评估
        spo2_avg = stats['bloodOxygen']['avg']
        if spo2_avg < 95:
            score -= 20
            warnings.append(f"血氧偏低: 平均{spo2_avg}%")
            
        # 体温评估
        temp_avg = stats['temperature']['avg']
        if temp_avg > 37.5 or temp_avg < 36.0:
            score -= 10
            warnings.append(f"体温异常: 平均{temp_avg}°C")
            
        # 血压评估
        bp_h_avg = stats['bloodPressureHigh']['avg']
        bp_l_avg = stats['bloodPressureLow']['avg']
        if bp_h_avg > 140 or bp_l_avg > 90:
            score -= 15
            warnings.append(f"血压偏高: {bp_h_avg}/{bp_l_avg}mmHg")
            
        # 运动评估
        steps_avg = stats['steps']['avg']
        if steps_avg < 5000:
            score -= 10
            warnings.append(f"运动不足: 日均{steps_avg}步")
            
        return {
            'overallScore': max(0, score),
            'status': 'excellent' if score >= 90 else 'good' if score >= 75 else 'fair' if score >= 60 else 'poor',
            'warnings': warnings
        }
    
    health_assessment = assess_health_status(stats)
    
    # 5. 趋势预测（简单线性回归）
    def predict_trends(values, periods=5):
        """使用简单线性回归预测未来趋势"""
        if len(values) < 3:
            return []
            
        # 简单的线性回归预测
        n = len(values)
        x_vals = list(range(n))
        y_vals = values
        
        # 计算回归系数
        x_mean = sum(x_vals) / n
        y_mean = sum(y_vals) / n
        
        numerator = sum((x_vals[i] - x_mean) * (y_vals[i] - y_mean) for i in range(n))
        denominator = sum((x_vals[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
            
        intercept = y_mean - slope * x_mean
        
        # 预测未来值
        predictions = []
        for i in range(periods):
            pred_x = n + i
            pred_y = slope * pred_x + intercept
            predictions.append(round(pred_y, 2))
            
        return predictions
    
    predictions = {
        'heartRate': predict_trends(clean_hr),
        'bloodOxygen': predict_trends(clean_spo2),
        'temperature': predict_trends(clean_temp)
    }
    
    return {
        'chartData': chart_data,
        'statistics': stats,
        'healthAssessment': health_assessment,
        'predictions': predictions,
        'timeRange': timeRange,
        'analysisTimestamp': datetime.now().isoformat()
    }

def generate_fallback_trends_data(timeRange):
    """生成备用趋势数据"""
    import random
    from datetime import datetime, timedelta
    
    # 根据时间范围生成相应数量的数据点
    data_points = {
        '1h': 12,   # 每5分钟一个点
        '6h': 36,   # 每10分钟一个点
        '24h': 48,  # 每30分钟一个点
        '7d': 168,  # 每小时一个点
        '30d': 720  # 每小时一个点
    }
    
    points = data_points.get(timeRange, 48)
    now = datetime.now()
    
    # 生成模拟时间序列数据
    chart_data = {
        'heartRate': [],
        'bloodOxygen': [],
        'temperature': [],
        'bloodPressureHigh': [],
        'bloodPressureLow': [],
        'steps': []
    }
    
    for i in range(points):
        timestamp = (now - timedelta(minutes=30*i)).isoformat()
        chart_data['heartRate'].append([timestamp, random.randint(65, 90)])
        chart_data['bloodOxygen'].append([timestamp, random.randint(96, 100)])
        chart_data['temperature'].append([timestamp, round(random.uniform(36.2, 37.0), 1)])
        chart_data['bloodPressureHigh'].append([timestamp, random.randint(110, 130)])
        chart_data['bloodPressureLow'].append([timestamp, random.randint(70, 85)])
        chart_data['steps'].append([timestamp, random.randint(100, 500)])
    
    return {
        'chartData': chart_data,
        'statistics': {
            'heartRate': {'avg': 75, 'min': 65, 'max': 90, 'trend': 'stable', 'change': 0},
            'bloodOxygen': {'avg': 98, 'min': 96, 'max': 100, 'trend': 'stable', 'change': 0},
            'temperature': {'avg': 36.6, 'min': 36.2, 'max': 37.0, 'trend': 'stable', 'change': 0}
        },
        'healthAssessment': {
            'overallScore': 85,
            'status': 'good',
            'warnings': []
        },
        'predictions': {
            'heartRate': [75, 76, 74, 75, 77],
            'bloodOxygen': [98, 98, 99, 98, 98],
            'temperature': [36.6, 36.7, 36.5, 36.6, 36.8]
        }
    }

@app.route('/health_data/page', methods=['GET'])  #健康数据分页接口
def health_data_page():
    try:
        orgId = request.args.get('orgId')
        userId = request.args.get('userId') if request.args.get('userId') else None
        startDate = request.args.get('startDate')
        endDate = request.args.get('endDate')
        page = request.args.get('page', 1)
        pageSize = request.args.get('pageSize', 100)
        result = get_page_health_data_by_orgIdAndUserId(orgId, userId, startDate, endDate, page, pageSize)
        return jsonify(result)
    except Exception as e:
        api_logger.error(f"健康数据分页接口错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

def get_comprehensive_statistics_data(customer_id, user_id=None, target_date=None):
    """获取综合统计数据"""
    try:
        from datetime import date
        if target_date is None:
            target_date = date.today()
        
        target_date_str = target_date.strftime('%Y-%m-%d')
        
        # 初始化统计数据
        stats = {
            'health_count': 0,
            'alert_count': 0,
            'message_count': 0,
            'device_count': 0,
            'user_count': 0,
            'org_count': 0,
            'active_devices': 0,
            'pending_alerts': 0,
            'unread_messages': 0,
            'tenant_name': '未知租户'
        }
        
        # 健康数据统计
        try:
            health_query = db.session.query(func.count(UserHealthData.id))
            if user_id:
                health_query = health_query.filter(UserHealthData.user_id == user_id)
            else:
                health_query = health_query.filter(UserHealthData.customer_id == customer_id)
            health_query = health_query.filter(func.date(UserHealthData.timestamp) == target_date)
            stats['health_count'] = health_query.scalar() or 0
        except Exception as e:
            logger.warning(f"健康数据统计失败: {e}")
        
        # 告警数据统计
        try:
            alert_query = db.session.query(func.count(AlertInfo.id))
            if user_id:
                alert_query = alert_query.filter(AlertInfo.user_id == user_id)
            else:
                alert_query = alert_query.filter(AlertInfo.customer_id == customer_id)
            alert_query = alert_query.filter(func.date(AlertInfo.alert_timestamp) == target_date)
            stats['alert_count'] = alert_query.scalar() or 0
            
            # 待处理告警统计
            pending_alert_query = alert_query.filter(AlertInfo.alert_status == 'pending')
            stats['pending_alerts'] = pending_alert_query.scalar() or 0
        except Exception as e:
            logger.warning(f"告警数据统计失败: {e}")
        
        # 消息数据统计
        try:
            from .models import DeviceMessage
            message_query = db.session.query(func.count(DeviceMessage.id))
            if user_id:
                message_query = message_query.filter(DeviceMessage.user_id == user_id)
            else:
                message_query = message_query.filter(DeviceMessage.customer_id == customer_id)
            message_query = message_query.filter(func.date(DeviceMessage.create_time) == target_date)
            stats['message_count'] = message_query.scalar() or 0
            
            # 未读消息统计
            unread_message_query = message_query.filter(DeviceMessage.message_status == 1)
            stats['unread_messages'] = unread_message_query.scalar() or 0
        except Exception as e:
            logger.warning(f"消息数据统计失败: {e}")
        
        # 设备数据统计
        try:
            device_query = db.session.query(func.count(DeviceInfo.id))
            if user_id:
                device_query = device_query.filter(DeviceInfo.user_id == user_id)
            else:
                device_query = device_query.filter(DeviceInfo.customer_id == customer_id)
            stats['device_count'] = device_query.scalar() or 0
            
            # 活跃设备统计（在线或最近24小时有数据的设备）
            from datetime import datetime, timedelta
            recent_time = datetime.now() - timedelta(hours=24)
            active_device_query = device_query.filter(
                db.or_(
                    DeviceInfo.status == 'ACTIVE',
                    DeviceInfo.update_time >= recent_time
                )
            )
            stats['active_devices'] = active_device_query.scalar() or 0
        except Exception as e:
            logger.warning(f"设备数据统计失败: {e}")
        
        # 用户数据统计
        try:
            if user_id:
                stats['user_count'] = 1
            else:
                user_query = db.session.query(func.count(UserInfo.id)).filter(UserInfo.customer_id == customer_id)
                stats['user_count'] = user_query.scalar() or 0
        except Exception as e:
            logger.warning(f"用户数据统计失败: {e}")
        
        # 组织数据统计 - 使用 findAllDescendants 获取客户下所有组织数量
        try:
            if not user_id:
                from .org import findAllDescendants
                org_list = findAllDescendants(customer_id)
                stats['org_count'] = len(org_list) if org_list else 0
        except Exception as e:
            logger.warning(f"组织数据统计失败: {e}")
        
        # 获取租户名称 - 根据 customer_id 查询对应的组织名称
        try:
            from .models import OrgInfo
            logger.info(f"开始查询租户名称，customer_id={customer_id}")
            tenant_query = db.session.query(OrgInfo.name).filter(
                OrgInfo.id == customer_id
            ).first()
            if tenant_query:
                stats['tenant_name'] = tenant_query.name
                logger.info(f"成功获取租户名称: {tenant_query.name}")
            else:
                logger.warning(f"未找到customer_id={customer_id}对应的组织信息")
                # 额外调试：查看是否有该ID的记录（不管删除状态）
                debug_query = db.session.query(OrgInfo.name, OrgInfo.is_deleted).filter(
                    OrgInfo.id == customer_id
                ).first()
                if debug_query:
                    logger.info(f"调试：找到记录但可能被过滤，name={debug_query.name}, is_deleted={debug_query.is_deleted}")
        except Exception as e:
            logger.warning(f"租户名称获取失败: {e}")
            import traceback
            logger.warning(f"详细错误: {traceback.format_exc()}")
        
        return stats
        
    except Exception as e:
        logger.error(f"综合统计数据获取失败: {e}")
        return stats

@app.route('/api/statistics/overview', methods=['GET'])
@log_api_request('/api/statistics/overview', 'GET')
def statistics_overview():
    """统计概览接口 - 提供前端所需的所有统计数据"""
    try:
        # 获取查询参数 - 支持多种参数格式
        customer_id = request.args.get('customerId') or request.args.get('customer_id')
        org_id = request.args.get('orgId') or request.args.get('org_id') 
        user_id = request.args.get('userId') or request.args.get('user_id')
        date_str = request.args.get('date')
        
        # 参数兼容处理：orgId 可作为 customerId 使用
        if org_id and not customer_id:
            customer_id = org_id
            
        if not customer_id:
            return jsonify({
                'success': False,
                'error': 'customerId 参数是必需的'
            }), 400
        
        # 解析日期参数
        from datetime import datetime, date, timedelta
        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                target_date = date.today()
        else:
            target_date = date.today()
            
        # 计算对比日期（前一天）
        compare_date = target_date - timedelta(days=1)
        
        # 获取统计数据
        current_stats = get_comprehensive_statistics_data(customer_id, user_id, target_date)
        compare_stats = get_comprehensive_statistics_data(customer_id, user_id, compare_date)
        
        # 计算变化趋势
        def calculate_change(current, previous):
            if previous == 0:
                return "+100%" if current > 0 else "0%"
            change = ((current - previous) / previous) * 100
            return f"{'+' if change >= 0 else ''}{change:.1f}%"
        
        # 构建返回数据
        result = {
            'success': True,
            'data': {
                # 当前统计数据
                'current': {
                    'date': target_date.strftime('%Y-%m-%d'),
                    'health_count': current_stats['health_count'],
                    'alert_count': current_stats['alert_count'],
                    'message_count': current_stats['message_count'],
                    'device_count': current_stats['device_count'],
                    'user_count': current_stats['user_count'],
                    'org_count': current_stats['org_count'],
                    'active_devices': current_stats['active_devices'],
                    'pending_alerts': current_stats['pending_alerts'],
                    'unread_messages': current_stats['unread_messages']
                },
                
                # 对比数据
                'compare': {
                    'date': compare_date.strftime('%Y-%m-%d'),
                    'health_count': compare_stats['health_count'],
                    'alert_count': compare_stats['alert_count'],
                    'message_count': compare_stats['message_count'],
                    'device_count': compare_stats['device_count']
                },
                
                # 变化趋势
                'changes': {
                    'health_count': calculate_change(current_stats['health_count'], compare_stats['health_count']),
                    'alert_count': calculate_change(current_stats['alert_count'], compare_stats['alert_count']),
                    'message_count': calculate_change(current_stats['message_count'], compare_stats['message_count']),
                    'device_count': calculate_change(current_stats['device_count'], compare_stats['device_count'])
                },
                
                # 租户信息
                'tenant_info': {
                    'customer_id': customer_id,
                    'tenant_name': current_stats.get('tenant_name', '智能科技有限公司'),
                    'system_status': 'normal'
                },
                
                # 实时状态
                'realtime_status': {
                    'last_update': datetime.now().isoformat(),
                    'data_freshness': 'realtime',
                    'api_response_time': f"{datetime.now().timestamp():.3f}s"
                }
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"统计概览接口错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {
                'current': {
                    'health_count': 0,
                    'alert_count': 0,
                    'message_count': 0,
                    'device_count': 0,
                    'user_count': 0,
                    'org_count': 0
                }
            }
        }), 500


# ============================================================================
# 优化版大屏V2 专用API端点
# ============================================================================

@app.route('/api/statistics/kpi', methods=['GET'])
def statistics_kpi():
    """KPI统计数据 - 优化版大屏V2专用"""
    try:
        customer_id = request.args.get('customerId', '1939964806110937090')

        # 获取在线设备数
        from sqlalchemy import func
        online_devices = db.session.query(func.count(DeviceInfo.id)).filter(
            DeviceInfo.customer_id == customer_id,
            DeviceInfo.status == 'online'
        ).scalar() or 0

        # 获取异常设备数(假设是离线或故障设备)
        abnormal_devices = db.session.query(func.count(DeviceInfo.id)).filter(
            DeviceInfo.customer_id == customer_id,
            DeviceInfo.status.in_(['offline', 'error'])
        ).scalar() or 0

        # 获取今日告警数
        from datetime import date
        today_alerts = db.session.query(func.count(AlertInfo.id)).filter(
            AlertInfo.customer_id == customer_id,
            func.date(AlertInfo.create_time) == date.today()
        ).scalar() or 0

        # 获取监测用户数
        monitored_users = db.session.query(func.count(func.distinct(DeviceInfo.user_id))).filter(
            DeviceInfo.customer_id == customer_id,
            DeviceInfo.user_id.isnot(None)
        ).scalar() or 0

        # 计算趋势(模拟数据,实际应从历史数据计算)
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'onlineDevices': online_devices,
                'abnormalDevices': abnormal_devices,
                'todayAlerts': today_alerts,
                'monitoredUsers': monitored_users,
                'trends': {
                    'online': 5.2,
                    'abnormal': -12.5,
                    'alerts': 15.3,
                    'users': 0
                }
            }
        })
    except Exception as e:
        logger.error(f"KPI统计数据获取失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': {
                'onlineDevices': 0,
                'abnormalDevices': 0,
                'todayAlerts': 0,
                'monitoredUsers': 0,
                'trends': {'online': 0, 'abnormal': 0, 'alerts': 0, 'users': 0}
            }
        }), 500


@app.route('/api/health/risk-index', methods=['GET'])
def health_risk_index():
    """健康风险指数 - 优化版大屏V2专用"""
    try:
        customer_id = request.args.get('customerId', '1939964806110937090')

        # 计算健康风险指数(基于告警数量、异常设备等)
        # 这里使用简化算法,实际应基于更复杂的健康评分系统
        from sqlalchemy import func
        from datetime import date, timedelta

        # 获取最近7天的告警数
        recent_alerts = db.session.query(func.count(AlertInfo.id)).filter(
            AlertInfo.customer_id == customer_id,
            AlertInfo.create_time >= date.today() - timedelta(days=7)
        ).scalar() or 0

        # 计算风险指数(100分制,分数越高越安全)
        # 假设0告警=100分,每个告警-2分
        risk_index = max(60, 100 - (recent_alerts * 2))

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'index': risk_index,
                'level': 'good' if risk_index >= 80 else 'warning' if risk_index >= 60 else 'danger',
                'recentAlerts': recent_alerts
            }
        })
    except Exception as e:
        logger.error(f"健康风险指数获取失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': {'index': 82, 'level': 'good'}
        }), 500


@app.route('/api/ai/summary', methods=['GET'])
def ai_summary():
    """AI智能总结 - 优化版大屏V2专用"""
    try:
        customer_id = request.args.get('customerId', '1939964806110937090')

        # 获取关键统计数据
        from sqlalchemy import func
        from datetime import date

        total_devices = db.session.query(func.count(DeviceInfo.id)).filter(
            DeviceInfo.customer_id == customer_id
        ).scalar() or 0

        online_devices = db.session.query(func.count(DeviceInfo.id)).filter(
            DeviceInfo.customer_id == customer_id,
            DeviceInfo.status == 'online'
        ).scalar() or 0

        today_alerts = db.session.query(func.count(AlertInfo.id)).filter(
            AlertInfo.customer_id == customer_id,
            func.date(AlertInfo.create_time) == date.today()
        ).scalar() or 0

        high_alerts = db.session.query(func.count(AlertInfo.id)).filter(
            AlertInfo.customer_id == customer_id,
            func.date(AlertInfo.create_time) == date.today(),
            AlertInfo.severity_level == 'high'
        ).scalar() or 0

        # 生成AI总结
        if high_alerts > 0:
            summary = f"当前 {online_devices}/{total_devices} 台设备在线,今日 {today_alerts} 条异常,其中高危 {high_alerts} 条。需要重点关注!"
            status = "需关注"
        elif today_alerts > 5:
            summary = f"当前 {online_devices}/{total_devices} 台设备在线,今日 {today_alerts} 条异常均为轻微,高危事件为 0。运行基本稳定。"
            status = "基本正常"
        else:
            summary = f"当前 {online_devices}/{total_devices} 台设备在线,今日 {today_alerts} 条异常均为轻微,高危事件为 0。整体运行稳定。"
            status = "运行正常"

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'summary': summary,
                'status': status,
                'timestamp': datetime.now().isoformat()
            }
        })
    except Exception as e:
        logger.error(f"AI总结生成失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': {
                'summary': '系统运行正常,数据加载中...',
                'status': '运行正常'
            }
        }), 500


@app.route('/api/ai/risk-prediction', methods=['GET'])
def ai_risk_prediction():
    """AI风险预测 - 优化版大屏V2专用"""
    try:
        customer_id = request.args.get('customerId', '1939964806110937090')

        # 这里应该实现真实的AI风险预测算法
        # 目前返回模拟数据
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'predictions': [
                    {
                        'type': 'main_risk',
                        'content': '主要风险来源: 血压波动 (占 62%)',
                        'level': 'medium'
                    },
                    {
                        'type': 'key_personnel',
                        'content': '关键人群: 张三、李四 (佩戴不规范)',
                        'level': 'low'
                    },
                    {
                        'type': 'future_alert',
                        'content': '预测异常: 未来 12 小时可能出现 2 条轻微异常',
                        'level': 'low'
                    }
                ],
                'update_time': '未来12小时',
                'confidence': 0.85
            }
        })
    except Exception as e:
        logger.error(f"AI风险预测失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': {'predictions': []}
        }), 500


@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    """AI对话接口 - 集成OpenRouter Claude Sonnet 4.5"""
    try:
        data = request.json
        customer_id = data.get('customerId', '1939964806110937090')
        message = data.get('message', '')

        if not message:
            return jsonify({
                'code': 400,
                'message': '消息不能为空',
                'data': {'response': '请输入您的问题。'}
            }), 400

        # 获取系统上下文数据
        context_data = get_ai_context_data(customer_id)

        # 构建系统提示词
        system_prompt = f"""你是灵境万象健康监测系统的AI助手。你的任务是帮助用户分析健康数据和回答问题。

当前系统状态:
- 在线设备: {context_data.get('online_devices', 0)}台
- 异常设备: {context_data.get('abnormal_devices', 0)}台
- 今日告警: {context_data.get('today_alerts', 0)}条
- 监测用户: {context_data.get('monitored_users', 0)}人

请基于以上数据回答用户问题,给出专业、简洁、有价值的建议。回答要点:
1. 直接回答问题,不要重复用户的问题
2. 提供具体的数据支持
3. 给出可操作的建议
4. 保持专业和友好的语气
5. 回答控制在150字以内"""

        # 调用OpenRouter API
        try:
            import requests

            openrouter_response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": "Bearer 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",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "anthropic/claude-3.5-sonnet",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ],
                    "max_tokens": 500,
                    "temperature": 0.7
                },
                timeout=30
            )

            if openrouter_response.status_code == 200:
                ai_result = openrouter_response.json()
                ai_response = ai_result['choices'][0]['message']['content']

                return jsonify({
                    'code': 200,
                    'message': 'success',
                    'data': {
                        'response': ai_response,
                        'timestamp': datetime.now().isoformat(),
                        'model': 'claude-3.5-sonnet'
                    }
                })
            else:
                logger.error(f"OpenRouter API错误: {openrouter_response.status_code} - {openrouter_response.text}")
                # 回退到关键词匹配
                return get_fallback_response(message, customer_id)

        except requests.exceptions.Timeout:
            logger.error("OpenRouter API超时")
            return get_fallback_response(message, customer_id)
        except Exception as api_error:
            logger.error(f"OpenRouter API调用失败: {str(api_error)}")
            return get_fallback_response(message, customer_id)

    except Exception as e:
        logger.error(f"AI对话处理失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': {'response': '抱歉,我遇到了一些问题,请稍后再试。'}
        }), 500


def get_ai_context_data(customer_id):
    """获取AI对话的上下文数据"""
    try:
        from sqlalchemy import func
        from datetime import date

        online_devices = db.session.query(func.count(DeviceInfo.id)).filter(
            DeviceInfo.customer_id == customer_id,
            DeviceInfo.status == 'online'
        ).scalar() or 0

        abnormal_devices = db.session.query(func.count(DeviceInfo.id)).filter(
            DeviceInfo.customer_id == customer_id,
            DeviceInfo.status.in_(['offline', 'error'])
        ).scalar() or 0

        today_alerts = db.session.query(func.count(AlertInfo.id)).filter(
            AlertInfo.customer_id == customer_id,
            func.date(AlertInfo.create_time) == date.today()
        ).scalar() or 0

        monitored_users = db.session.query(func.count(func.distinct(DeviceInfo.user_id))).filter(
            DeviceInfo.customer_id == customer_id,
            DeviceInfo.user_id.isnot(None)
        ).scalar() or 0

        return {
            'online_devices': online_devices,
            'abnormal_devices': abnormal_devices,
            'today_alerts': today_alerts,
            'monitored_users': monitored_users
        }
    except Exception as e:
        logger.error(f"获取AI上下文数据失败: {str(e)}")
        return {
            'online_devices': 0,
            'abnormal_devices': 0,
            'today_alerts': 0,
            'monitored_users': 0
        }


def get_fallback_response(message, customer_id):
    """AI API失败时的回退响应 - 基于关键词匹配"""
    response = "我正在为您分析数据..."

    # 关键词匹配
    if '血压' in message:
        response = "根据最近的数据分析,血压异常主要集中在生产部门,建议加强该部门的健康监测频率。可以通过增加测量频次、关注高风险时段等方式改善。"
    elif '趋势' in message or '分析' in message:
        response = "根据最近7天的健康数据趋势,整体健康指标保持稳定。心率平均值在正常范围内,血氧饱和度良好。建议继续保持当前的监测频率。"
    elif '人员' in message or '排名' in message:
        response = "当前告警次数较多的人员建议重点关注。可以通过人员管理模块查看详细的异常排名,针对性地进行健康干预。"
    elif '区域' in message or '地图' in message or '分布' in message:
        response = "可以通过地图查看人员分布情况。建议关注告警集中的区域,分析是否存在环境因素影响健康指标。"
    elif '设备' in message:
        response = "当前大部分设备运行正常。如有离线设备,建议及时检查电量和网络连接。可通过设备管理模块查看详细状态。"
    elif '帮助' in message or '功能' in message or '怎么' in message:
        response = "我可以帮您:\n1. 分析健康数据趋势\n2. 查询异常人员排名\n3. 解读告警信息\n4. 提供健康建议\n\n您可以问我具体的问题,比如'显示血压异常最多的区域'。"
    else:
        response = f"关于'{message}'的问题,建议您查看相关数据面板获取详细信息。如需特定分析,请告诉我您关注的具体指标。"

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'response': response,
            'timestamp': datetime.now().isoformat(),
            'model': 'fallback'
        }
    })


@app.route('/api/alerts/list', methods=['GET'])
def alerts_list():
    """告警列表 - 优化版大屏V2专用"""
    try:
        customer_id = request.args.get('customerId', '1939964806110937090')

        from sqlalchemy import func, desc
        from datetime import date, datetime

        # 获取今日告警,按级别分类
        today = date.today()

        high_count = db.session.query(func.count(AlertInfo.id)).filter(
            AlertInfo.customer_id == customer_id,
            func.date(AlertInfo.create_time) == today,
            AlertInfo.severity_level == 'high'
        ).scalar() or 0

        medium_count = db.session.query(func.count(AlertInfo.id)).filter(
            AlertInfo.customer_id == customer_id,
            func.date(AlertInfo.create_time) == today,
            AlertInfo.severity_level == 'medium'
        ).scalar() or 0

        low_count = db.session.query(func.count(AlertInfo.id)).filter(
            AlertInfo.customer_id == customer_id,
            func.date(AlertInfo.create_time) == today,
            AlertInfo.severity_level == 'low'
        ).scalar() or 0

        # 获取最近的告警列表
        alerts = db.session.query(AlertInfo).filter(
            AlertInfo.customer_id == customer_id,
            func.date(AlertInfo.create_time) == today
        ).order_by(desc(AlertInfo.create_time)).limit(10).all()

        alert_list = []
        for alert in alerts:
            # 计算时间差
            time_diff = datetime.now() - alert.create_time
            if time_diff.seconds < 60:
                time_str = "刚刚"
            elif time_diff.seconds < 3600:
                time_str = f"{time_diff.seconds // 60}分钟前"
            else:
                time_str = f"{time_diff.seconds // 3600}小时前"

            alert_list.append({
                'id': alert.id,
                'level': alert.severity_level or 'medium',
                'title': alert.alert_type or '健康异常',
                'user': alert.assigned_user or '未知用户',
                'time': time_str,
                'status': alert.alert_status or 'pending'
            })

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'high': high_count,
                'medium': medium_count,
                'low': low_count,
                'list': alert_list
            }
        })
    except Exception as e:
        logger.error(f"告警列表获取失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': {
                'high': 0,
                'medium': 0,
                'low': 0,
                'list': []
            }
        }), 500


@app.route('/api/personnel/ranking', methods=['GET'])
def personnel_ranking():
    """人员异常排名 - 优化版大屏V2专用"""
    try:
        customer_id = request.args.get('customerId', '1939964806110937090')

        from sqlalchemy import func
        from datetime import date, timedelta

        # 获取最近7天每个用户的告警次数
        recent_date = date.today() - timedelta(days=7)

        # 查询告警次数统计 - 简化版本,不包含部门信息
        ranking_query = db.session.query(
            AlertInfo.user_id,
            AlertInfo.assigned_user,
            func.count(AlertInfo.id).label('alert_count')
        ).filter(
            AlertInfo.customer_id == customer_id,
            AlertInfo.create_time >= recent_date,
            AlertInfo.user_id.isnot(None)
        ).group_by(
            AlertInfo.user_id,
            AlertInfo.assigned_user
        ).order_by(
            func.count(AlertInfo.id).desc()
        ).limit(10).all()

        ranking_list = []
        for idx, item in enumerate(ranking_query, 1):
            # 尝试获取用户所属部门
            dept_name = '未知部门'
            try:
                user = db.session.query(UserInfo).filter(UserInfo.id == item.user_id).first()
                if user:
                    # 检查UserInfo是否有org_name或dept_name字段
                    if hasattr(user, 'org_name') and user.org_name:
                        dept_name = user.org_name
                    elif hasattr(user, 'dept_name') and user.dept_name:
                        dept_name = user.dept_name
                    else:
                        # 尝试通过org_id获取组织名称
                        if hasattr(user, 'org_id') and user.org_id:
                            org = db.session.query(OrgInfo).filter(OrgInfo.id == user.org_id).first()
                            if org and hasattr(org, 'org_name'):
                                dept_name = org.org_name
            except Exception as e:
                logger.debug(f"获取用户部门信息失败: {str(e)}")

            ranking_list.append({
                'rank': idx,
                'name': item.assigned_user or f'用户{item.user_id}',
                'dept': dept_name,
                'value': item.alert_count
            })

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': ranking_list
        })
    except Exception as e:
        logger.error(f"人员排名获取失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': []
        }), 500


@app.route('/api/statistics/area-ranking', methods=['GET'])
def area_ranking():
    """区域健康排行API"""
    try:
        customer_id = request.args.get('customerId', '1939964806110937090')

        # 查询各组织的健康数据汇总
        from sqlalchemy import func

        # 获取各组织的设备和告警统计
        org_stats = db.session.query(
            OrgInfo.name,
            OrgInfo.id,
            func.count(DeviceInfo.id).label('device_count')
        ).outerjoin(
            UserInfo, UserInfo.org_id == OrgInfo.id
        ).outerjoin(
            DeviceInfo, DeviceInfo.user_id == UserInfo.id
        ).filter(
            OrgInfo.customer_id == customer_id
        ).group_by(
            OrgInfo.id, OrgInfo.name
        ).all()

        ranking = []
        for org in org_stats:
            # 查询该组织的告警数
            alert_count = db.session.query(func.count(AlertInfo.id)).join(
                UserInfo, UserInfo.id == AlertInfo.user_id
            ).filter(
                UserInfo.org_id == org.id
            ).scalar() or 0

            # 查询异常人员数
            abnormal_count = db.session.query(func.count(func.distinct(AlertInfo.user_id))).join(
                UserInfo, UserInfo.id == AlertInfo.user_id
            ).filter(
                UserInfo.org_id == org.id,
                AlertInfo.alert_status == 'pending'
            ).scalar() or 0

            # 计算健康评分（简化算法）
            score = 100 - min(alert_count * 2 + abnormal_count * 5, 50)

            ranking.append({
                'name': org.name or f'组织{org.id}',
                'score': score,
                'alerts': alert_count,
                'abnormal': abnormal_count
            })

        # 按评分排序
        ranking.sort(key=lambda x: x['score'], reverse=True)

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'ranking': ranking
            }
        })
    except Exception as e:
        logger.error(f"区域排行获取失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': {'ranking': []}
        }), 500


@app.route('/api/personnel/offline', methods=['GET'])
def personnel_offline():
    """离线人员列表API"""
    try:
        customer_id = request.args.get('customerId', '1939964806110937090')

        from datetime import datetime, timedelta

        # 查询最近24小时无数据上传的设备
        cutoff_time = datetime.now() - timedelta(hours=24)

        offline_devices = db.session.query(
            UserInfo.user_name,
            UserInfo.org_name,
            DeviceInfo.update_time
        ).join(
            DeviceInfo, DeviceInfo.user_id == UserInfo.id
        ).filter(
            UserInfo.customer_id == customer_id,
            DeviceInfo.update_time < cutoff_time
        ).order_by(
            DeviceInfo.update_time.desc()
        ).limit(50).all()

        offline_list = []
        for device in offline_devices:
            # 计算离线时长
            if device.update_time:
                offline_hours = (datetime.now() - device.update_time).total_seconds() / 3600
                if offline_hours < 24:
                    offline_time = f'{int(offline_hours)}小时前'
                else:
                    offline_time = f'{int(offline_hours / 24)}天前'
            else:
                offline_time = '未知'

            offline_list.append({
                'name': device.user_name or '未知用户',
                'dept': device.org_name or '未分配部门',
                'offlineTime': offline_time
            })

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': offline_list
        })
    except Exception as e:
        logger.error(f"离线人员获取失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': []
        }), 500


@app.route('/api/personnel/wearing-status', methods=['GET'])
def personnel_wearing_status():
    """佩戴状态统计API"""
    try:
        customer_id = request.args.get('customerId', '1939964806110937090')

        from datetime import datetime, timedelta

        # 总设备数
        total_devices = db.session.query(func.count(DeviceInfo.id)).join(
            UserInfo, UserInfo.id == DeviceInfo.user_id
        ).filter(
            UserInfo.customer_id == customer_id
        ).scalar() or 0

        # 在线设备（最近1小时有数据）
        recent_time = datetime.now() - timedelta(hours=1)
        online_devices = db.session.query(func.count(DeviceInfo.id)).join(
            UserInfo, UserInfo.id == DeviceInfo.user_id
        ).filter(
            UserInfo.customer_id == customer_id,
            DeviceInfo.update_time >= recent_time
        ).scalar() or 0

        # 离线设备（24小时无数据）
        offline_time = datetime.now() - timedelta(hours=24)
        offline_devices = db.session.query(func.count(DeviceInfo.id)).join(
            UserInfo, UserInfo.id == DeviceInfo.user_id
        ).filter(
            UserInfo.customer_id == customer_id,
            DeviceInfo.update_time < offline_time
        ).scalar() or 0

        # 异常佩戴（有告警的在线设备）
        abnormal_devices = db.session.query(func.count(func.distinct(AlertInfo.user_id))).join(
            UserInfo, UserInfo.id == AlertInfo.user_id
        ).join(
            DeviceInfo, DeviceInfo.user_id == UserInfo.id
        ).filter(
            UserInfo.customer_id == customer_id,
            AlertInfo.alert_status == 'pending',
            DeviceInfo.update_time >= recent_time
        ).scalar() or 0

        # 正常佩戴 = 在线设备 - 异常设备
        normal_devices = max(online_devices - abnormal_devices, 0)

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'normal': normal_devices,
                'abnormal': abnormal_devices,
                'offline': offline_devices
            }
        })
    except Exception as e:
        logger.error(f"佩戴状态获取失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': {
                'normal': 0,
                'abnormal': 0,
                'offline': 0
            }
        }), 500


@app.route('/api/baseline/generate', methods=['POST'])  #baseline生成API接口
def api_generate_baseline():
    """手动触发baseline生成API接口"""
    try:
        data = request.get_json() or {}
        orgId = data.get('orgId', '1')
        days = int(data.get('days', 7))
        
        from datetime import datetime, timedelta
        from .health_baseline import HealthBaselineQuery
        
        generator = HealthBaselineQuery()
        
        # 生成最近N天的baseline
        results = []
        for i in range(days):
            target_date = (datetime.now() - timedelta(days=i+1)).date()
            
            try:
                # 生成用户baseline
                user_result = generator.generate_daily_user_baseline(target_date)
                # 生成组织baseline  
                org_result = generator.generate_daily_org_baseline(target_date)
                
                results.append({
                    'date': str(target_date),
                    'user_baseline': user_result,
                    'org_baseline': org_result
                })
            except Exception as e:
                results.append({
                    'date': str(target_date),
                    'error': str(e)
                })
        
        api_logger.info(f"Baseline生成完成，orgId: {orgId}, 处理天数: {days}")
        
        return jsonify({
            'success': True,
            'message': f'Baseline生成完成，处理 {days} 天数据',
            'results': results,
            'orgId': orgId
        })
        
    except Exception as e:
        api_logger.error(f"Baseline生成失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Baseline生成失败'
        }), 500

@app.route('/api/baseline/status', methods=['GET'])  #baseline状态检查接口
def api_baseline_status():
    """检查baseline数据状态"""
    try:
        orgId = request.args.get('orgId', '1')
        
        from .models import HealthBaseline, OrgHealthBaseline
        from datetime import datetime, timedelta
        
        # 检查最近7天的baseline数据
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        user_baseline_count = db.session.query(HealthBaseline).filter(
            HealthBaseline.baseline_time >= seven_days_ago
        ).count()
        
        org_baseline_count = db.session.query(OrgHealthBaseline).filter(
            OrgHealthBaseline.baseline_date >= seven_days_ago.date()
        ).count()
        
        # 获取最新baseline记录
        latest_user_baseline = db.session.query(HealthBaseline).order_by(
            HealthBaseline.baseline_time.desc()
        ).first()
        
        latest_org_baseline = db.session.query(OrgHealthBaseline).order_by(
            OrgHealthBaseline.baseline_date.desc()
        ).first()
        
        return jsonify({
            'success': True,
            'data': {
                'user_baseline_count_7days': user_baseline_count,
                'org_baseline_count_7days': org_baseline_count,
                'latest_user_baseline': {
                    'date': latest_user_baseline.baseline_date.strftime('%Y-%m-%d') if latest_user_baseline else None,
                    'time': latest_user_baseline.baseline_time.strftime('%Y-%m-%d %H:%M:%S') if latest_user_baseline else None,
                    'feature': latest_user_baseline.feature_name if latest_user_baseline else None,
                    'device_sn': latest_user_baseline.device_sn if latest_user_baseline else None
                } if latest_user_baseline else None,
                'latest_org_baseline': {
                    'date': latest_org_baseline.baseline_date.strftime('%Y-%m-%d') if latest_org_baseline else None,
                    'org_id': latest_org_baseline.org_id if latest_org_baseline else None,
                    'feature': latest_org_baseline.feature_name if latest_org_baseline else None
                } if latest_org_baseline else None
            }
        })
        
    except Exception as e:
        api_logger.error(f"Baseline状态检查失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/wechat/config/test', methods=['GET'])
def test_wechat_config():
    """测试微信告警配置"""
    try:
        # 导入微信配置管理模块
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from wechat_config import get_wechat_config
        
        wechat_config = get_wechat_config()
        test_result = wechat_config.test_config()
        
        return jsonify({
            'success': True,
            'data': test_result,
            'message': '微信配置测试完成'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '微信配置测试失败'
        }), 500

@app.route('/api/wechat/config/template', methods=['GET'])
def get_wechat_config_template():
    """获取微信配置模板"""
    try:
        # 导入微信配置管理模块
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from wechat_config import get_wechat_config
        
        wechat_config = get_wechat_config()
        template = wechat_config.get_env_template()
        
        return jsonify({
            'success': True,
            'data': {
                'template': template,
                'current_config': {
                    'enabled': wechat_config.enabled,
                    'app_id': f"{wechat_config.app_id[:6]}***" if wechat_config.app_id else "未配置",
                    'template_id': f"{wechat_config.template_id[:10]}***" if wechat_config.template_id else "未配置",
                    'user_openid': f"{wechat_config.user_openid[:8]}***" if wechat_config.user_openid else "未配置"
                }
            },
            'message': '微信配置模板获取成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '获取微信配置模板失败'
        }), 500

@app.route('/api/wechat/alert/send', methods=['POST'])
def send_test_wechat_alert():
    """发送测试微信告警"""
    try:
        data = request.get_json() or {}
        alert_type = data.get('alert_type', '测试告警')
        user_name = data.get('user_name', '测试用户')
        severity_level = data.get('severity_level', '高')
        user_openid = data.get('user_openid')
        
        # 导入微信配置管理模块
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from wechat_config import get_wechat_config
        
        wechat_config = get_wechat_config()
        result = wechat_config.send_alert(alert_type, user_name, severity_level, user_openid)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '发送测试告警失败'
        }), 500

@app.route('/api/corp_wechat/config/test', methods=['GET'])
def test_corp_wechat_config():
    """测试企业微信配置"""
    try:
        from .wechat import corp_wechat_config
        
        # 测试配置完整性
        configured, msg = corp_wechat_config.is_configured()
        enabled = corp_wechat_config.is_enabled()
        
        # 测试AccessToken获取
        token_test = False
        token_msg = ""
        if configured and enabled:
            try:
                token = corp_wechat_config.get_access_token()
                if token:
                    token_test = True
                    token_msg = "AccessToken获取成功"
                else:
                    token_msg = "AccessToken获取失败"
            except Exception as e:
                token_msg = f"AccessToken测试异常: {str(e)}"
        else:
            token_msg = "配置不完整或未启用，跳过Token测试"
        
        test_result = {
            'config_check': {
                'configured': configured,
                'message': msg,
                'enabled': enabled
            },
            'token_test': {
                'success': token_test,
                'message': token_msg
            },
            'current_config': {
                'corp_id': f"{corp_wechat_config.corp_id[:8]}***" if corp_wechat_config.corp_id else "未配置",
                'agent_id': corp_wechat_config.agent_id if corp_wechat_config.agent_id else "未配置",
                'api_url': corp_wechat_config.api_url,
                'touser': corp_wechat_config.touser,
                'enabled': enabled
            }
        }
        
        return jsonify({
            'success': True,
            'data': test_result,
            'message': '企业微信配置测试完成'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '企业微信配置测试失败'
        }), 500

@app.route('/api/corp_wechat/config/template', methods=['GET'])
def get_corp_wechat_config_template():
    """获取企业微信配置模板"""
    try:
        template = """
# ==================== 企业微信配置 ====================
# 企业微信企业ID
CORP_ID=your_corp_id_here
# 企业微信应用Secret
CORP_SECRET=your_corp_secret_here
# 企业微信应用AgentID
CORP_AGENT_ID=your_agent_id_here
# 企业微信API地址(一般不需要修改)
CORP_API_URL=https://qyapi.weixin.qq.com
# 是否启用企业微信告警(true/false)
CORP_WECHAT_ENABLED=true
# 企业微信消息接收用户(默认@all为全员)
CORP_WECHAT_TOUSER=@all
"""
        
        from .wechat import corp_wechat_config
        
        return jsonify({
            'success': True,
            'data': {
                'template': template.strip(),
                'current_config': {
                    'enabled': corp_wechat_config.enabled,
                    'corp_id': f"{corp_wechat_config.corp_id[:8]}***" if corp_wechat_config.corp_id else "未配置",
                    'agent_id': corp_wechat_config.agent_id if corp_wechat_config.agent_id else "未配置",
                    'api_url': corp_wechat_config.api_url,
                    'touser': corp_wechat_config.touser
                }
            },
            'message': '企业微信配置模板获取成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '获取企业微信配置模板失败'
        }), 500

@app.route('/api/corp_wechat/alert/send', methods=['POST'])
def send_test_corp_wechat_alert():
    """发送测试企业微信告警"""
    try:
        data = request.get_json() or {}
        alert_type = data.get('alert_type', '测试告警')
        user_name = data.get('user_name', '测试用户')
        severity = data.get('severity', '高')
        time_str = data.get('time_str')
        
        from .wechat import corp_wechat_config
        result = corp_wechat_config.send_alert(alert_type, user_name, severity, time_str)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '发送测试企业微信告警失败'
        }), 500

@app.route('/api/health/trends/<metric>', methods=['GET']) # 单个体征趋势接口
def get_health_metric_trends(metric):
    try:
        deviceSn=request.args.get('deviceSn')
        orgId=request.args.get('orgId')
        userId=request.args.get('userId')
        days=int(request.args.get('days',7)) # 默认7天
        
        if not deviceSn and not (orgId and userId):
            return jsonify({'success':False,'message':'需要deviceSn或orgId+userId参数'})
        
        # 获取用户信息-修复数据类型处理
        if deviceSn and not userId:
            user_result=user_get_user_info(deviceSn)
            # 处理不同返回类型-get_user_info返回JSON字符串
            if isinstance(user_result,str) and user_result!="No user found":
                try:
                    user_info=json.loads(user_result)
                    userId=user_info.get('user_id')
                    orgId=user_info.get('customer_id',1) # customer_id作为orgId
                except json.JSONDecodeError:
                    return jsonify({'success':False,'message':'用户信息解析失败'})
            elif hasattr(user_result,'get_json'):
                user_data=user_result.get_json()
                if user_data and user_data.get('success'):
                    user_info=user_data.get('data',{})
                    userId=user_info.get('id') or user_info.get('user_id')
                    orgId=user_info.get('org_id',1)
                else:
                    return jsonify({'success':False,'message':'未找到用户信息'})
            elif isinstance(user_result,dict):
                user_info=user_result
                userId=user_info.get('id') or user_info.get('user_id')
                orgId=user_info.get('org_id',1)
            else:
                return jsonify({'success':False,'message':'未找到用户信息'})
        
        # 计算日期范围
        end_date=datetime.now()
        start_date=end_date-timedelta(days=days)
        
        # 使用get_all_health_data_optimized获取数据
        health_result=get_all_health_data_optimized(
            orgId=orgId,
            userId=userId,
            startDate=start_date.strftime('%Y-%m-%d'),
            endDate=end_date.strftime('%Y-%m-%d'),
            latest_only=False
        )
        
        # 处理健康数据返回格式
        if isinstance(health_result,str):
            try:
                health_data=json.loads(health_result)
            except json.JSONDecodeError as e:
                return jsonify({'success':False,'message':'健康数据解析失败'})
        elif hasattr(health_result,'get_json'):
            health_data=health_result.get_json()
        elif isinstance(health_result,dict):
            health_data=health_result
        else:
            health_data=None
        
        if not health_data or not health_data.get('success'):
            return jsonify({'success':False,'message':'未找到健康数据'})
        
        # 提取指定体征的数据
        records=health_data.get('data',{}).get('healthData',[])
        trend_data=[]
        
        for record in records:
            timestamp=record.get('timestamp')
            value=record.get(metric)
            if timestamp and value is not None:
                try:
                    float_value=float(value)
                    trend_data.append({
                        'timestamp':timestamp,
                        'value':float_value,
                        'date':timestamp.split(' ')[0] if ' ' in timestamp else timestamp
                    })
                except ValueError:
                    continue
        
        # 按时间排序
        trend_data.sort(key=lambda x:x['timestamp'])
        
        # 计算统计信息
        values=[item['value'] for item in trend_data]
        if values:
            avg_value=sum(values)/len(values)
            min_value=min(values)
            max_value=max(values)
        else:
            avg_value=min_value=max_value=0
        
        # 获取正常范围
        normal_ranges={
            'heart_rate':[60,100],
            'blood_oxygen':[95,100],
            'temperature':[36.0,37.5],
            'stress':[0,50],
            'step':[8000,12000],
            'distance':[3,10],
            'calorie':[1500,3000],
            'sleep':[6,9]
        }
        normal_range=normal_ranges.get(metric,[0,100])
        
        return jsonify({
            'success':True,
            'data':{
                'metric':metric,
                'trend_data':trend_data,
                'statistics':{
                    'count':len(trend_data),
                    'average':round(avg_value,2),
                    'min':min_value,
                    'max':max_value,
                    'normal_range':normal_range
                },
                'chart_config':{
                    'title':f'{metric}趋势图',
                    'unit':get_metric_unit(metric),
                    'color':get_metric_color(metric)
                }
            }
        })
        
    except Exception as e:
        api_logger.error(f'获取{metric}趋势数据失败:{str(e)}')
        return jsonify({'success':False,'message':f'获取趋势数据失败:{str(e)}'})

def get_metric_unit(metric): # 获取体征单位
    units={
        'heart_rate':'次/分',
        'blood_oxygen':'%',
        'temperature':'°C',
        'stress':'',
        'step':'步',
        'distance':'km',
        'calorie':'卡',
        'sleep':'小时'
    }
    return units.get(metric,'')

def get_metric_color(metric): # 获取体征颜色
    colors={
        'heart_rate':'#ff6b6b',
        'blood_oxygen':'#4ecdc4',
        'temperature':'#45b7d1',
        'stress':'#96ceb4',
        'step':'#ffeaa7',
        'distance':'#dda0dd',
        'calorie':'#fab1a0',
        'sleep':'#6c5ce7'
    }
    return colors.get(metric,'#00e4ff')

@app.route('/api/health/scores', methods=['GET'])  # 健康评分查询接口
def get_health_scores():
    """获取用户健康评分数据"""
    try:
        from .models import HealthScore
        from sqlalchemy import func, text
        from datetime import datetime, timedelta
        
        customer_id = request.args.get('customerId', 1, type=int)
        device_sns = request.args.getlist('deviceSns')  # 支持批量查询
        user_ids = request.args.getlist('userIds')      # 支持批量查询
        
        # 计算7天前的日期
        date_threshold = datetime.now().date() - timedelta(days=7)
        
        # 构建查询条件
        query = db.session.query(
            HealthScore.device_sn,
            HealthScore.user_id,
            func.avg(HealthScore.score_value).label('avg_score'),
            func.max(HealthScore.score_date).label('latest_date')
        ).filter(
            HealthScore.score_date >= date_threshold  # 最近7天
        ).group_by(HealthScore.device_sn, HealthScore.user_id)
        
        # 添加过滤条件
        if device_sns:
            query = query.filter(HealthScore.device_sn.in_(device_sns))
        if user_ids:
            query = query.filter(HealthScore.user_id.in_(user_ids))
            
        results = query.all()
        
        # 格式化返回数据
        health_scores = {}
        for result in results:
            device_sn = result.device_sn
            user_id = result.user_id
            avg_score = float(result.avg_score) if result.avg_score else 0
            
            health_scores[device_sn] = {
                'device_sn': device_sn,
                'user_id': user_id,
                'health_score': round(avg_score, 1),
                'latest_date': result.latest_date.isoformat() if result.latest_date else None,
                'color': get_health_color_by_score(avg_score)
            }
        
        return jsonify({
            'success': True,
            'data': health_scores,
            'count': len(health_scores)
        })
        
    except Exception as e:
        api_logger.error(f'获取健康评分失败: {str(e)}')
        return jsonify({'success': False, 'message': f'获取健康评分失败: {str(e)}'})

def get_health_color_by_score(score):
    """根据健康评分获取颜色"""
    if score >= 80:
        return '#52c41a'  # 绿色-健康
    elif score >= 60:
        return '#faad14'  # 黄色-注意  
    elif score >= 40:
        return '#fa8c16'  # 橙色-轻度异常
    elif score > 0:
        return '#ff4d4f'  # 红色-重度异常
    else:
        return '#d9d9d9'  # 灰色-离线/无数据

@app.route('/api/health/baseline/<metric>', methods=['GET']) # 单个体征基线接口
def get_health_metric_baseline(metric):
    try:
        deviceSn=request.args.get('deviceSn')
        orgId=request.args.get('orgId')
        userId=request.args.get('userId')
        startDate = request.args.get('startDate')
        endDate = request.args.get('endDate')
        
        # 修复参数验证逻辑：支持只有orgId的情况（部门数据）
        if not deviceSn and not orgId:
            return jsonify({'success':False,'message':'需要deviceSn或orgId参数'})
        
        # 获取用户信息-修复数据类型处理
        if deviceSn and not userId:
            user_result=user_get_user_info(deviceSn)
            # 处理不同返回类型-get_user_info返回JSON字符串
            if isinstance(user_result,str) and user_result!="No user found":
                try:
                    user_info=json.loads(user_result)
                    userId=user_info.get('user_id')
                    orgId=user_info.get('customer_id',1) # customer_id作为orgId
                except json.JSONDecodeError:
                    return jsonify({'success':False,'message':'用户信息解析失败'})
            elif hasattr(user_result,'get_json'):
                user_data=user_result.get_json()
                if user_data and user_data.get('success'):
                    user_info=user_data.get('data',{})
                    userId=user_info.get('id') or user_info.get('user_id')
                    orgId=user_info.get('org_id',1)
                else:
                    return jsonify({'success':False,'message':'未找到用户信息'})
            elif isinstance(user_result,dict):
                user_info=user_result
                userId=user_info.get('id') or user_info.get('user_id')
                orgId=user_info.get('org_id',1)
            else:
                return jsonify({'success':False,'message':'未找到用户信息'})
        
        # 如果userId为空字符串，设为None以获取部门数据
        if userId == '':
            userId = None
        
        # 获取30天数据计算基线
        if not startDate:
            startDate = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not endDate:
            endDate = datetime.now().strftime('%Y-%m-%d')
        
        health_result=get_all_health_data_optimized(
            orgId=orgId,
            userId=userId,
            startDate=startDate,
            endDate=endDate,
            latest_only=False
        )
        
        # 处理健康数据返回格式
        if isinstance(health_result,str):
            try:
                health_data=json.loads(health_result)
            except json.JSONDecodeError as e:
                return jsonify({'success':False,'message':'健康数据解析失败'})
        elif hasattr(health_result,'get_json'):
            health_data=health_result.get_json()
        elif isinstance(health_result,dict):
            health_data=health_result
        else:
            health_data=None
        
        if not health_data or not health_data.get('success'):
            return jsonify({'success':False,'message':'未找到健康数据'})
        
        # 提取数据计算基线
        records=health_data.get('data',{}).get('healthData',[])
        values=[]
        for record in records:
            value=record.get(metric)
            if value is not None and str(value).replace('.','').replace('-','').isdigit():
                try:
                    values.append(float(value))
                except ValueError:
                    continue
        
        if not values:
            return jsonify({'success':False,'message':'无足够数据计算基线'})
        
        # 计算基线统计
        avg=sum(values)/len(values)
        std_dev=(sum([(x-avg)**2 for x in values])/len(values))**0.5
        
        baseline={
            'metric':metric,
            'average':round(avg,2),
            'std_deviation':round(std_dev,2),
            'min':min(values),
            'max':max(values),
            'percentile_25':sorted(values)[int(len(values)*0.25)],
            'percentile_75':sorted(values)[int(len(values)*0.75)],
            'data_points':len(values),
            'date_range':f'{startDate} ~ {endDate}'
        }
        
        return jsonify({'success':True,'data':baseline})
        
    except Exception as e:
        api_logger.error(f'获取{metric}基线数据失败:{str(e)}')
        return jsonify({'success':False,'message':f'获取基线数据失败:{str(e)}'})

@app.route('/personal_3d') # 3D人体模型页面路由
def personal_3d():
    deviceSn=request.args.get('deviceSn','')
    return render_template('personal_3d.html',deviceSn=deviceSn,BIGSCREEN_TITLE=BIGSCREEN_TITLE)

@app.route('/personal_advanced') # 高级3D人体模型页面路由
def personal_advanced():
    deviceSn=request.args.get('deviceSn','')
    return render_template('personal_advanced.html',deviceSn=deviceSn,BIGSCREEN_TITLE=BIGSCREEN_TITLE)

# 批量处理器管理和监控API v1.0.34
@app.route("/api/batch/stats", methods=['GET'])
@log_api_request('/api/batch/stats','GET')
def get_batch_stats():
    """获取批量处理器统计信息"""
    from .device import get_batch_processor_stats
    device_logger.info('批量处理器状态查询')
    return get_batch_processor_stats()

@app.route("/api/batch/restart", methods=['POST'])
@log_api_request('/api/batch/restart','POST')
def restart_batch():
    """重启批量处理器"""
    from .device import restart_batch_processor
    device_logger.info('批量处理器重启请求')
    return restart_batch_processor()

@app.route("/api/batch/config", methods=['POST'])
@log_api_request('/api/batch/config','POST')
def config_batch():
    """配置批量处理器参数"""
    from .device import configure_batch_processor
    config_data = request.get_json() or {}
    device_logger.info('批量处理器配置更新',extra={'config':config_data})
    return configure_batch_processor(
        batch_size=config_data.get('batch_size'),
        max_wait_time=config_data.get('max_wait_time'),
        max_workers=config_data.get('max_workers')
    )

# 批量处理器管理和监控API路由 v1.0.34
@app.route('/api/batch/stats', methods=['GET'])
@log_api_request('/api/batch/stats','GET')
def api_get_batch_processor_stats():
    """获取批量处理器统计信息"""
    from .device import get_batch_processor_stats
    return get_batch_processor_stats()

@app.route('/api/batch/restart', methods=['POST'])
@log_api_request('/api/batch/restart','POST')
def api_restart_batch_processor():
    """重启批量处理器"""
    from .device import restart_batch_processor
    return restart_batch_processor()

@app.route('/api/batch/config', methods=['POST'])
@log_api_request('/api/batch/config','POST')
def api_configure_batch_processor():
    """配置批量处理器参数"""
    from .device import configure_batch_processor
    config = request.get_json() or {}
    return configure_batch_processor(
        batch_size=config.get('batch_size'),
        max_wait_time=config.get('max_wait_time'),
        max_workers=config.get('max_workers')
    )

@app.route('/api/device/history/timeline', methods=['GET']) #设备历史记录时序图接口
@log_api_request('/api/device/history/timeline','GET')
def api_get_device_history_timeline():
    """获取设备历史记录时序图数据"""
    from .device import get_device_history_timeline
    serial_number = request.args.get('serial_number')
    limit = request.args.get('limit', 60, type=int)
    
    if not serial_number:
        return jsonify({"status": "error", "message": "设备序列号不能为空"}), 400
    
    return get_device_history_timeline(serial_number, limit)

@app.route('/api/device/history/trends', methods=['GET'])
@log_api_request('/api/device/history/trends','GET')
def api_get_device_history_trends():
    """获取设备历史趋势分析数据"""
    from .device import get_device_history_trends
    
    org_id = request.args.get('orgId')
    user_id = request.args.get('userId')
    days = request.args.get('days', 7, type=int)
    metrics = request.args.getlist('metrics') or ['battery_level', 'wearable_status', 'charging_status']
    
    if not org_id:
        return jsonify({"success": False, "message": "组织ID不能为空"}), 400
    
    return get_device_history_trends(org_id, user_id, days, metrics)

@app.route('/api/device/battery/prediction', methods=['GET'])
@log_api_request('/api/device/battery/prediction','GET')
def api_get_device_battery_prediction():
    """获取设备电池使用预测"""
    from .device import get_device_battery_prediction
    
    org_id = request.args.get('orgId')
    user_id = request.args.get('userId')
    days = request.args.get('days', 30, type=int)
    
    if not org_id:
        return jsonify({"success": False, "message": "组织ID不能为空"}), 400
    
    return get_device_battery_prediction(org_id, user_id, days)

@app.route('/api/device/analysis/comprehensive', methods=['GET'])
@log_api_request('/api/device/analysis/comprehensive','GET')
def api_get_comprehensive_device_analysis():
    """获取设备综合分析数据"""
    from .device import get_device_history_trends, get_device_battery_prediction, fetch_devices_by_orgIdAndUserId
    
    org_id = request.args.get('orgId')
    user_id = request.args.get('userId')
    days = request.args.get('days', 7, type=int)
    
    if not org_id:
        return jsonify({"success": False, "message": "组织ID不能为空"}), 400
    
    try:
        # 获取基础设备信息
        devices_result = fetch_devices_by_orgIdAndUserId(org_id, user_id)
        if not devices_result.get('success'):
            return jsonify({"success": False, "message": "获取设备信息失败"})
        
        # 获取历史趋势数据
        trends_result = get_device_history_trends(org_id, user_id, days)
        
        # 获取电池预测数据
        prediction_result = get_device_battery_prediction(org_id, user_id, days)
        
        # 合并所有数据
        comprehensive_data = {
            "success": True,
            "data": {
                "devices": devices_result.get('data', {}),
                "trends": trends_result.get('data', {}) if trends_result.get('success') else {},
                "predictions": prediction_result.get('data', {}) if prediction_result.get('success') else {},
                "analysis_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "time_range_days": days
            }
        }
        
        return jsonify(comprehensive_data)
        
    except Exception as e:
        return jsonify({"success": False, "message": f"综合分析失败: {str(e)}"}), 500

# 健康画像管理API路由 #健康画像API
@app.route('/api/health-profile/monitor', methods=['GET'])  # 健康画像监控接口
def api_health_profile_monitor():
    """获取健康画像生命周期监控数据"""
    customer_id = request.args.get('customerId', 1, type=int)
    return jsonify(get_profile_monitor(customer_id))

@app.route('/api/health-profile/generate', methods=['POST'])  # 手动生成健康画像接口
def api_health_profile_generate():
    """手动生成用户健康画像"""
    data = request.get_json()
    customer_id = data.get('customerId', 1)
    user_ids = data.get('userIds', [])
    org_id = data.get('orgId')
    operator_id = data.get('operatorId', 1)
    
    return jsonify(manual_generate_profiles(customer_id, user_ids, org_id, operator_id))

@app.route('/api/health-profile/list', methods=['GET'])  # 健康画像列表接口
def api_health_profile_list():
    """获取健康画像展示列表"""
    customer_id = request.args.get('customerId', 1, type=int)
    org_id = request.args.get('orgId', type=int)
    user_name = request.args.get('userName', '')
    health_level = request.args.get('healthLevel', '')
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 20, type=int)
    
    return jsonify(get_health_profiles(customer_id, org_id, user_name, health_level, page, size))

@app.route('/api/health-profile/statistics', methods=['GET'])  # 健康画像统计接口
def api_health_profile_statistics():
    """获取健康画像统计数据"""
    customer_id = request.args.get('customerId', 1, type=int)
    org_id = request.args.get('orgId', type=int)
    
    return jsonify(get_profile_statistics(customer_id, org_id))

# 手机端登录和个人信息相关路由 #手机端API
@app.route('/phone_login', methods=['GET'])
def phone_login():
    """登录接口"""
    try:
        phone = request.args.get('phone')
        password = request.args.get('password')

        if not phone or not password:
            return jsonify({
                'success': False,
                'error': '手机号和密码不能为空'
            })

        from .user import login_user
        result = login_user(phone, password)
        print("result:", result)
        return jsonify(result)

    except Exception as e:
        print(f"Login error: {str(e)}")  # 添加错误日志
        return jsonify({
            'success': False,
            'error': f'登录失败: {str(e)}'
        })

@app.route('/phone_get_personal_info', methods=['GET'])
def phone_get_personal_info():
    """手机端获取个人信息接口"""
    try:
        phone = request.args.get('phone')
        if not phone:
            return jsonify({
                'success': False,
                'error': 'phone is required'
            })

        from .user import get_user_info_by_phone
        user = get_user_info_by_phone(phone)
        print("user:", user)

        if user and user.device_sn:
            return get_personal_info(user.device_sn)
        else:
            return jsonify({
                'success': False,
                'error': 'User not found or no device associated with this user',
                'data': {
                    'phone': phone,
                    'user': user.to_dict() if user else None
                }
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取个人信息失败: {str(e)}'
        })

# 个人大屏实时数据API v1.3.5+
@app.route('/api/personal/realtime_health', methods=['GET'])
def get_personal_realtime_health():
    """获取个人实时健康数据API"""
    try:
        device_sn = request.args.get('deviceSn')
        if not device_sn:
            return jsonify({
                'success': False,
                'error': 'deviceSn参数是必需的'
            }), 400
        
        # 获取用户信息
        from .user import get_user_id_by_deviceSn
        user_id = get_user_id_by_deviceSn(device_sn)
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': '未找到对应的用户信息'
            }), 404
        
        # 获取最新健康数据
        from .user_health_data import get_latest_health_data_by_device
        health_data = get_latest_health_data_by_device(device_sn)
        
        if not health_data:
            # 返回默认数据结构
            return jsonify({
                'success': True,
                'data': {
                    'deviceSn': device_sn,
                    'heartRate': 0,
                    'bloodOxygen': 0,
                    'temperature': '0.0',
                    'systolic': 0,
                    'diastolic': 0,
                    'stepCount': 0,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'no_data'
                }
            })
        
        # 格式化返回数据
        result = {
            'success': True,
            'data': {
                'deviceSn': device_sn,
                'heartRate': int(health_data.get('heartRate', 0)),
                'bloodOxygen': int(health_data.get('bloodOxygen', 0)),
                'temperature': str(health_data.get('temperature', '0.0')),
                'systolic': int(health_data.get('pressureHigh', 0)),
                'diastolic': int(health_data.get('pressureLow', 0)),
                'stepCount': int(health_data.get('step', 0)),
                'distance': float(health_data.get('distance', 0.0)),
                'calorie': float(health_data.get('calorie', 0.0)),
                'stress': int(health_data.get('stress', 0)),
                'timestamp': health_data.get('timestamp', datetime.now()).isoformat(),
                'status': 'active'
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        api_logger.error(f"获取个人实时健康数据失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取健康数据失败: {str(e)}'
        }), 500

@app.route('/api/personal/alerts', methods=['GET'])
def get_personal_alerts():
    """获取个人告警数据API"""
    try:
        device_sn = request.args.get('deviceSn')
        if not device_sn:
            return jsonify({
                'success': False,
                'error': 'deviceSn参数是必需的'
            }), 400
        
        # 获取用户信息
        from .user import get_user_id_by_deviceSn
        user_id = get_user_id_by_deviceSn(device_sn)
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': '未找到对应的用户信息'
            }), 404
        
        # 获取个人告警数据
        from .alert import fetch_alerts_by_orgIdAndUserId
        alert_result = fetch_alerts_by_orgIdAndUserId(None, user_id, None)
        
        if not alert_result:
            return jsonify({
                'success': True,
                'data': {
                    'alerts': [],
                    'totalCount': 0,
                    'pendingCount': 0
                }
            })
        
        # 处理告警数据
        alert_data = alert_result.get_json() if hasattr(alert_result, 'get_json') else alert_result
        alerts = alert_data.get('data', {}).get('alerts', []) if isinstance(alert_data, dict) else []
        
        # 统计告警
        pending_alerts = [alert for alert in alerts if alert.get('alert_status') == 'pending']
        
        # 格式化告警数据
        formatted_alerts = []
        for alert in pending_alerts[:5]:  # 只返回最新5条
            # 处理时间戳格式
            alert_timestamp = alert.get('alert_timestamp')
            if isinstance(alert_timestamp, str):
                try:
                    # 尝试解析字符串时间
                    from datetime import datetime
                    parsed_time = datetime.fromisoformat(alert_timestamp.replace('Z', '+00:00'))
                    time_str = parsed_time.strftime('%H:%M')
                except:
                    # 如果解析失败，直接使用字符串的前5个字符
                    time_str = alert_timestamp[:5] if len(alert_timestamp) >= 5 else alert_timestamp
            elif hasattr(alert_timestamp, 'strftime'):
                time_str = alert_timestamp.strftime('%H:%M')
            else:
                time_str = datetime.now().strftime('%H:%M')
                
            formatted_alerts.append({
                'id': alert.get('id'),
                'level': alert.get('alert_type', 'warning'),
                'content': alert.get('alert_info', '健康异常'),
                'time': time_str,
                'status': alert.get('alert_status', 'pending')
            })
        
        return jsonify({
            'success': True,
            'data': {
                'alerts': formatted_alerts,
                'totalCount': len(alerts),
                'pendingCount': len(pending_alerts)
            }
        })
        
    except Exception as e:
        api_logger.error(f"获取个人告警数据失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取告警数据失败: {str(e)}'
        }), 500

@app.route('/api/personal/messages', methods=['GET'])
def get_personal_messages():
    """获取个人消息数据API"""
    try:
        device_sn = request.args.get('deviceSn')
        if not device_sn:
            return jsonify({
                'success': False,
                'error': 'deviceSn参数是必需的'
            }), 400
        
        # 获取用户信息
        from .user import get_user_id_by_deviceSn
        user_id = get_user_id_by_deviceSn(device_sn)
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': '未找到对应的用户信息'
            }), 404
        
        # 获取个人消息数据
        from .message import fetch_messages_by_orgIdAndUserId
        msg_result = fetch_messages_by_orgIdAndUserId(None, user_id, None)
        
        if not msg_result:
            return jsonify({
                'success': True,
                'data': {
                    'messages': [],
                    'totalCount': 0,
                    'unreadCount': 0
                }
            })
        
        # 处理消息数据
        msg_data = msg_result.get_json() if hasattr(msg_result, 'get_json') else msg_result
        messages = msg_data.get('data', {}).get('messages', []) if isinstance(msg_data, dict) else []
        
        # 统计消息
        unread_messages = [msg for msg in messages if msg.get('message_status') == 1 or msg.get('message_status') == '1']
        
        # 格式化消息数据
        formatted_messages = []
        for msg in messages[:10]:  # 只返回最新10条
            # 处理时间戳格式
            create_time = msg.get('create_time')
            if isinstance(create_time, str):
                try:
                    # 尝试解析字符串时间
                    parsed_time = datetime.fromisoformat(create_time.replace('Z', '+00:00'))
                    time_str = parsed_time.strftime('%H:%M')
                except:
                    # 如果解析失败，直接使用字符串的前5个字符
                    time_str = create_time[:5] if len(create_time) >= 5 else create_time
            elif hasattr(create_time, 'strftime'):
                time_str = create_time.strftime('%H:%M')
            else:
                time_str = datetime.now().strftime('%H:%M')
                
            formatted_messages.append({
                'id': msg.get('id'),
                'type': msg.get('message_type', 'system'),
                'content': msg.get('message_info', '系统消息'),
                'time': time_str,
                'status': 'unread' if msg.get('message_status') == 1 else 'read'
            })
        
        return jsonify({
            'success': True,
            'data': {
                'messages': formatted_messages,
                'totalCount': len(messages),
                'unreadCount': len(unread_messages)
            }
        })
        
    except Exception as e:
        api_logger.error(f"获取个人消息数据失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取消息数据失败: {str(e)}'
        }), 500

@app.route('/api/personal/device_status', methods=['GET'])
def get_personal_device_status():
    """获取个人设备状态API"""
    try:
        device_sn = request.args.get('deviceSn')
        if not device_sn:
            return jsonify({
                'success': False,
                'error': 'deviceSn参数是必需的'
            }), 400
        
        # 获取设备信息
        from .device import fetch_device_info
        device_result = fetch_device_info(device_sn)
        
        if not device_result:
            return jsonify({
                'success': True,
                'data': {
                    'deviceSn': device_sn,
                    'status': 'unknown',
                    'batteryLevel': 0,
                    'lastUpdate': None
                }
            })
        
        # 处理设备数据
        device_data = device_result.get_json() if hasattr(device_result, 'get_json') else device_result
        device_info = device_data.get('data', {}) if isinstance(device_data, dict) else {}
        
        return jsonify({
            'success': True,
            'data': {
                'deviceSn': device_sn,
                'status': device_info.get('status', 'unknown'),
                'batteryLevel': int(device_info.get('battery_level', 0)),
                'deviceName': device_info.get('device_name', 'LJWX智能手表'),
                'firmwareVersion': device_info.get('firmware_version', '1.0.0'),
                'lastUpdate': device_info.get('last_update', datetime.now()).isoformat()
            }
        })
        
    except Exception as e:
        api_logger.error(f"获取个人设备状态失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取设备状态失败: {str(e)}'
        }), 500

@app.route('/api/personal/health_history', methods=['GET'])
def get_personal_health_history():
    """获取个人健康历史数据API"""
    try:
        device_sn = request.args.get('deviceSn')
        time_range = request.args.get('timeRange', '1h')  # 1h, 6h, 1d, 7d
        
        if not device_sn:
            return jsonify({
                'success': False,
                'error': 'deviceSn参数是必需的'
            }), 400
        
        # 计算时间范围
        now = datetime.now()
        if time_range == '1h':
            start_time = now - timedelta(hours=1)
        elif time_range == '6h':
            start_time = now - timedelta(hours=6)
        elif time_range == '1d':
            start_time = now - timedelta(days=1)
        elif time_range == '7d':
            start_time = now - timedelta(days=7)
        else:
            start_time = now - timedelta(hours=1)
        
        # 获取历史数据
        from .user_health_data import get_health_data_by_date_range
        history_data = get_health_data_by_date_range(device_sn, start_time, now)
        
        if not history_data:
            return jsonify({
                'success': True,
                'data': {
                    'heartRate': [],
                    'bloodOxygen': [],
                    'temperature': [],
                    'timeRange': time_range
                }
            })
        
        # 格式化历史数据
        heart_rate_data = []
        blood_oxygen_data = []
        temperature_data = []
        
        for record in history_data:
            timestamp = record.get('timestamp', now)
            heart_rate_data.append([timestamp.isoformat(), record.get('heartRate', 0)])
            blood_oxygen_data.append([timestamp.isoformat(), record.get('bloodOxygen', 0)])
            temperature_data.append([timestamp.isoformat(), float(record.get('temperature', 0))])
        
        return jsonify({
            'success': True,
            'data': {
                'heartRate': heart_rate_data,
                'bloodOxygen': blood_oxygen_data,
                'temperature': temperature_data,
                'timeRange': time_range,
                'totalRecords': len(history_data)
            }
        })
        
    except Exception as e:
        api_logger.error(f"获取个人健康历史数据失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取历史数据失败: {str(e)}'
        }), 500

@app.route('/api/personal/health_trends', methods=['GET'])
def get_personal_health_trends():
    """获取个人健康数据趋势API - 支持deviceSn参数"""
    try:
        device_sn = request.args.get('deviceSn')
        days = int(request.args.get('days', 30))  # 默认30天趋势
        
        if not device_sn:
            return jsonify({
                'success': False,
                'error': 'deviceSn参数是必需的'
            }), 400
        
        # 获取用户ID
        from .user import get_user_id_by_deviceSn
        user_id = get_user_id_by_deviceSn(device_sn)
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': f'设备{device_sn}未找到对应用户'
            }), 404
        
        # 获取用户组织信息
        from .device import get_device_user_org_info
        org_info = get_device_user_org_info(device_sn)
        org_id = org_info.get('orgId') if org_info else None
        
        # 计算日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        api_logger.info(f"📈 获取个人健康趋势: deviceSn={device_sn}, userId={user_id}, days={days}")
        
        # 调用现有的健康趋势函数
        trends_result = get_health_trends(orgId=org_id, userId=user_id, startDate=start_date_str, endDate=end_date_str)
        
        # 如果get_health_trends返回的是Response对象，需要转换
        if hasattr(trends_result, 'get_json'):
            trends_data = trends_result.get_json()
        elif hasattr(trends_result, 'json'):
            trends_data = trends_result.json
        else:
            trends_data = trends_result
        
        # 添加设备信息到返回数据
        if trends_data and trends_data.get('success'):
            if 'data' not in trends_data:
                trends_data['data'] = {}
            trends_data['data']['deviceSn'] = device_sn
            trends_data['data']['userId'] = user_id
            trends_data['data']['orgId'] = org_id
            trends_data['data']['timeRange'] = f'{days}天'
            
        api_logger.info(f"✅ 个人健康趋势获取完成: deviceSn={device_sn}")
        return jsonify(trends_data)
        
    except Exception as e:
        api_logger.error(f"❌ 获取个人健康趋势失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取个人健康趋势失败: {str(e)}'
        }), 500

@app.route('/api/device/info', methods=['GET'])
def get_device_info():
    """获取设备信息API"""
    try:
        device_sn = request.args.get('deviceSn')
        org_id = request.args.get('orgId')
        user_id = request.args.get('userId')
        
        if not device_sn and not (org_id or user_id):
            return jsonify({
                'success': False,
                'error': '需要deviceSn或orgId/userId参数'
            }), 400
        
        # 获取用户信息
        if device_sn and not user_id:
            from .user import get_user_id_by_deviceSn
            user_id = get_user_id_by_deviceSn(device_sn)
            
        from .device import get_all_device_data_optimized
        device_result = get_all_device_data_optimized(
            orgId=org_id,
            userId=user_id,
            latest_only=True,
            include_alerts=False
        )
        
        return jsonify(device_result)
        
    except Exception as e:
        api_logger.error(f"获取设备信息失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取设备信息失败: {str(e)}'
        }), 500

@app.route('/api/health_data/latest', methods=['GET'])
def get_latest_health_data_api():
    """获取最新健康数据API"""
    try:
        device_sn = request.args.get('deviceSn')
        
        if not device_sn:
            return jsonify({
                'success': False,
                'error': 'deviceSn参数是必需的'
            }), 400
        
        from .user_health_data import get_latest_health_data_by_device
        health_data = get_latest_health_data_by_device(device_sn)
        
        if health_data is None:
            return jsonify({
                'success': True,
                'data': {
                    'deviceSn': device_sn,
                    'heartRate': 0,
                    'bloodOxygen': 0,
                    'temperature': '0.0',
                    'pressureHigh': 0,
                    'pressureLow': 0,
                    'step': 0,
                    'distance': 0.0,
                    'calorie': 0.0,
                    'stress': 0,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'no_data'
                }
            })
        
        # 添加deviceSn和状态信息
        health_data['deviceSn'] = device_sn
        health_data['status'] = 'active'
        
        return jsonify({
            'success': True,
            'data': health_data
        })
        
    except Exception as e:
        api_logger.error(f"获取最新健康数据失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取最新健康数据失败: {str(e)}'
        }), 500

    except Exception as e:
        print(f"Error in phone_get_personal_info: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get personal info: {str(e)}'
        })

@app.route('/phone/reset_password', methods=['POST'])
def phone_reset_password():
    """重置密码接口"""
    try:
        data = request.get_json()
        user_id = data.get('userId')

        if not user_id:
            return jsonify({
                'success': False,
                'error': '用户ID不能为空'
            })
        from .user import reset_password
        result = reset_password(user_id)
        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'密码重置失败: {str(e)}'
        })

@app.route('/phone/reset_password_by_phone', methods=['POST'])
def phone_reset_password_by_phone():
    """通过手机号重置密码接口 #手机号重置密码"""
    try:
        data = request.get_json()
        phone = data.get('phone')

        if not phone:
            return jsonify({
                'success': False,
                'error': '手机号不能为空'
            })
        from .user import reset_password_by_phone
        result = reset_password_by_phone(phone)
        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'密码重置失败: {str(e)}'
        })

@app.route("/get_all_health_data_by_orgIdAndUserId_mobile")
def get_all_health_data_by_orgIdAndUserId_mobile():
    """移动端优化的健康数据分析接口"""
    phone = request.args.get('phone')
    startDate = request.args.get('startDate') or time.strftime('%Y-%m-%d', time.localtime(time.time() - 30 * 24 * 60 * 60))
    endDate = request.args.get('endDate') or time.strftime('%Y-%m-%d', time.localtime(time.time()))
    print("get_all_health_data_by_orgIdAndUserId_mobile.phone:", phone)
    print("get_all_health_data_by_orgIdAndUserId_mobile.startDate:", startDate)
    print("get_all_health_data_by_orgIdAndUserId_mobile.endDate:", endDate)

    from .user_health_data import fetch_all_health_data_by_orgIdAndUserId_mobile
    result = fetch_all_health_data_by_orgIdAndUserId_mobile(phone, startDate, endDate)
    return jsonify(result)

@app.route('/get_device_info_by_phone', methods=['GET'])
def get_device_info_by_phone():
    """根据手机号获取设备信息"""
    phone = request.args.get('phone')
    from .user import fetch_device_info_by_phone
    return jsonify(fetch_device_info_by_phone(phone))

# ==================== 系统事件告警管理API ====================

@app.route('/api/system-event/rules', methods=['GET'])
def get_system_event_rules():
    """获取系统事件规则列表"""
    try:
        from .models import SystemEventRule
        
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        rule_type = request.args.get('rule_type')
        is_emergency = request.args.get('is_emergency')
        
        query = SystemEventRule.query.filter_by(tenant_id=1)
        
        if rule_type:
            query = query.filter(SystemEventRule.rule_type.like(f'%{rule_type}%'))
        if is_emergency is not None:
            query = query.filter_by(is_emergency=is_emergency.lower() == 'true')
        
        rules = query.order_by(SystemEventRule.create_time.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'code': 200,
            'success': True,
            'data': [rule.to_dict() for rule in rules.items],
            'total': rules.total,
            'page': page,
            'per_page': per_page,
            'pages': rules.pages
        })
    except Exception as e:
        return jsonify({'code': 500, 'success': False, 'error': str(e)}), 500

@app.route('/api/system-event/rules', methods=['POST'])
def create_system_event_rule():
    """创建系统事件规则"""
    try:
        from .models import SystemEventRule
        
        data = request.json
        rule = SystemEventRule(
            event_type=data['event_type'],
            rule_type=data['rule_type'],
            severity_level=data['severity_level'],
            alert_message=data['alert_message'],
            is_emergency=data.get('is_emergency', False),
            notification_type=data.get('notification_type', 'message'),
            retry_count=data.get('retry_count', 3),
            is_active=data.get('is_active', True),
            tenant_id=1
        )
        
        db.session.add(rule)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'success': True,
            'data': rule.to_dict(),
            'message': '规则创建成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'success': False, 'error': str(e)}), 500

@app.route('/api/system-event/rules/<int:rule_id>', methods=['GET'])
def get_system_event_rule(rule_id):
    """获取单个系统事件规则"""
    try:
        from .models import SystemEventRule
        
        rule = SystemEventRule.query.get_or_404(rule_id)
        
        return jsonify({
            'code': 200,
            'success': True,
            'data': rule.to_dict()
        })
    except Exception as e:
        return jsonify({'code': 500, 'success': False, 'error': str(e)}), 500

@app.route('/api/system-event/rules/<int:rule_id>', methods=['PUT'])
def update_system_event_rule(rule_id):
    """更新系统事件规则"""
    try:
        from .models import SystemEventRule
        
        rule = SystemEventRule.query.get_or_404(rule_id)
        data = request.json
        
        rule.event_type = data.get('event_type', rule.event_type)
        rule.rule_type = data.get('rule_type', rule.rule_type)
        rule.severity_level = data.get('severity_level', rule.severity_level)
        rule.alert_message = data.get('alert_message', rule.alert_message)
        rule.is_emergency = data.get('is_emergency', rule.is_emergency)
        rule.notification_type = data.get('notification_type', rule.notification_type)
        rule.retry_count = data.get('retry_count', rule.retry_count)
        rule.is_active = data.get('is_active', rule.is_active)
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'success': True,
            'data': rule.to_dict(),
            'message': '规则更新成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'success': False, 'error': str(e)}), 500

@app.route('/api/system-event/rules/<int:rule_id>', methods=['DELETE'])
def delete_system_event_rule(rule_id):
    """删除系统事件规则"""
    try:
        from .models import SystemEventRule
        
        rule = SystemEventRule.query.get_or_404(rule_id)
        
        db.session.delete(rule)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'success': True,
            'message': '规则删除成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'success': False, 'error': str(e)}), 500

@app.route('/api/system-event/queue/stats', methods=['GET'])
def get_event_queue_stats():
    """获取事件队列统计"""
    try:
        from .models import EventAlarmQueue, AlertInfo
        from sqlalchemy import func, desc
        from datetime import datetime, timedelta
        
        # 获取是否需要详细信息
        detail = request.args.get('detail', 'false').lower() == 'true'
        
        # 今日统计
        today = datetime.now().date()
        today_events = EventAlarmQueue.query.filter(
            func.date(EventAlarmQueue.create_time) == today
        ).count()
        
        # 按状态统计
        status_stats = db.session.query(
            EventAlarmQueue.processing_status,
            func.count(EventAlarmQueue.id).label('count')
        ).group_by(EventAlarmQueue.processing_status).all()
        
        # 计算各状态数量
        pending_count = sum(s[1] for s in status_stats if s[0] == 'pending')
        processing_count = sum(s[1] for s in status_stats if s[0] == 'processing')
        completed_count = sum(s[1] for s in status_stats if s[0] == 'completed')
        failed_count = sum(s[1] for s in status_stats if s[0] == 'failed')
        
        total_processed = completed_count + failed_count
        success_rate = (completed_count / total_processed * 100) if total_processed > 0 else 0
        
        # 紧急事件统计
        emergency_events = AlertInfo.query.filter(
            func.date(AlertInfo.alert_timestamp) == today,
            AlertInfo.severity_level == 'critical'
        ).count()
        
        result = {
            'total_events': today_events,
            'emergency_events': emergency_events,
            'pending_count': pending_count,
            'processing_count': processing_count,
            'completed_count': completed_count,
            'failed_count': failed_count,
            'success_rate': round(success_rate, 1)
        }
        
        # 如果需要详细信息，添加队列项目
        if detail:
            queue_items = EventAlarmQueue.query.order_by(
                EventAlarmQueue.create_time.desc()
            ).limit(20).all()
            
            result['queue_items'] = [{
                'id': item.id,
                'event_type': item.event_type or 'UNKNOWN',
                'device_sn': item.device_sn,
                'event_value': item.event_value,
                'processing_status': item.processing_status,
                'retry_count': item.retry_count,
                'create_time': item.create_time.strftime('%Y-%m-%d %H:%M:%S') if item.create_time else None,
                'error_message': item.error_message
            } for item in queue_items]
        
        return jsonify({
            'code': 200,
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({'code': 500, 'success': False, 'error': str(e)}), 500

@app.route('/api/wechat-alarm/config/clean', methods=['POST'])
def clean_duplicate_configs():
    """清理重复的微信配置"""
    try:
        from .models import WeChatAlarmConfig
        # 统计重复配置
        enterprise_configs = WeChatAlarmConfig.query.filter_by(type='enterprise').all()
        official_configs = WeChatAlarmConfig.query.filter_by(type='official').all()
        
        deleted_count = 0
        # 保留最新的有效配置，删除其他的
        for config_type, configs in [('enterprise', enterprise_configs), ('official', official_configs)]:
            if len(configs) > 1:
                # 按创建时间排序，保留最新的有配置内容的
                valid_configs = [c for c in configs if (
                    c.corp_id and c.secret if config_type == 'enterprise' 
                    else c.appid and c.appsecret
                )]
                
                if valid_configs:
                    # 保留最新的有效配置
                    latest_config = max(valid_configs, key=lambda x: x.create_time)
                    to_delete = [c for c in configs if c.id != latest_config.id]
                else:
                    # 如果没有有效配置，保留最新创建的
                    latest_config = max(configs, key=lambda x: x.create_time)
                    to_delete = [c for c in configs if c.id != latest_config.id]
                
                # 删除重复配置
                for config in to_delete:
                    db.session.delete(config)
                    deleted_count += 1
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'success': True,
            'message': f'清理完成，删除{deleted_count}个重复配置'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'success': False, 'error': str(e)}), 500

@app.route('/api/wechat-alarm/config', methods=['GET'])
def get_wechat_alarm_config():
    """获取微信告警配置"""
    try:
        from .models import WeChatAlarmConfig
        
        configs = WeChatAlarmConfig.query.filter_by(enabled=True).all()
        
        result = []
        for config in configs:
            result.append({
                'id': config.id,
                'type': config.type,
                'enabled': config.enabled,
                'corp_id': config.corp_id,
                'agent_id': config.agent_id,
                'secret': config.secret,
                'appid': config.appid,
                'appsecret': config.appsecret,
                'template_id': config.template_id,
                'create_time': config.create_time.strftime('%Y-%m-%d %H:%M:%S') if config.create_time else None
            })
        
        return jsonify({
            'code': 200,
            'data': result,
            'success': True
        })
    except Exception as e:
        return jsonify({'code': 500, 'success': False, 'error': str(e)}), 500

@app.route('/api/wechat-alarm/config', methods=['POST'])
def update_wechat_alarm_config():
    """更新微信告警配置"""
    try:
        from .models import WeChatAlarmConfig
        
        data = request.json
        config_type = data['type']
        
        # 删除该类型的所有旧配置，避免重复(兼容tenant_id为None的情况)
        from sqlalchemy import or_
        WeChatAlarmConfig.query.filter(
            WeChatAlarmConfig.type==config_type,
            or_(WeChatAlarmConfig.tenant_id==1, WeChatAlarmConfig.tenant_id.is_(None))
        ).delete()
        
        # 创建新配置
        config = WeChatAlarmConfig(tenant_id=1, type=config_type)
        db.session.add(config)
        
        config.enabled = data.get('enabled', True)
        
        if config_type == 'enterprise':
            config.corp_id = data.get('corp_id')
            config.agent_id = data.get('agent_id')
            config.secret = data.get('secret')
        elif config_type == 'official':
            config.appid = data.get('appid')
            config.appsecret = data.get('appsecret')
            config.template_id = data.get('template_id')
        
        db.session.commit()
        
        # 清除微信通知器缓存
        try:
            from .system_event_alert import get_processor
            processor = get_processor()
            if hasattr(processor, 'wechat_notifier'):
                processor.wechat_notifier.clear_cache()
        except:
            pass
        
        return jsonify({
            'code': 200,
            'success': True,
            'message': '微信告警配置更新成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'success': False, 'error': str(e)}), 500

@app.route('/api/wechat-alarm/test', methods=['POST'])
def test_wechat_alarm():
    """测试微信告警"""
    try:
        from .system_event_alert import WeChatNotifier
        
        data = request.json
        notifier = WeChatNotifier()
        
        result = notifier.send_alert(
            alert_type=data.get('alert_type', 'TEST_ALERT'),
            user_name=data.get('user_name', '测试用户'),
            severity=data.get('severity', 'high'),
            device_sn=data.get('device_sn', 'TEST_DEVICE')
        )
        
        return jsonify({
            'success': result.get('success', False),
            'message': result.get('message', '测试完成'),
            'data': result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system-event/processor/init', methods=['POST'])
def init_event_processor():
    """初始化事件处理器"""
    try:
        from .system_event_alert import init_processor, get_processor
        
        # 强制初始化
        init_processor()
        
        # 获取处理器状态
        processor = get_processor()
        
        return jsonify({
            'code': 200,
            'success': True,
            'message': f'事件处理器初始化成功，工作线程数: {len(processor.workers)}',
            'data': {
                'is_running': processor.is_running,
                'worker_count': len(processor.workers)
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'code': 500, 'success': False, 'error': str(e)}), 500

# 系统事件告警大屏展示页面
@app.route('/system_event_alert')
def system_event_alert_page():
    """系统事件告警大屏页面"""
    return render_template('system_event_alert.html')

@app.route('/api/test/wechat', methods=['POST'])
def test_wechat_send():
    """直接测试微信发送API - 根据界面设置选择配置类型"""
    debug_info = []
    
    try:
        # 添加诊断信息收集
        from sqlalchemy import text
        
        # 检查数据库连接
        db_info = db.session.execute(text("SELECT DATABASE() as current_db")).fetchone()
        debug_info.append(f"当前数据库: {db_info[0]}")
        
        # 检查表是否存在
        table_check = db.session.execute(text("SHOW TABLES LIKE 't_wechat_alarm_config'")).fetchone()
        debug_info.append(f"表存在: {bool(table_check)}")
        
        # 查询记录数
        count_result = db.session.execute(text("SELECT COUNT(*) FROM t_wechat_alarm_config")).fetchone()
        debug_info.append(f"表中记录数: {count_result[0]}")
        
        # 查询启用的配置
        enabled_count = db.session.execute(text("SELECT COUNT(*) FROM t_wechat_alarm_config WHERE enabled=1")).fetchone()
        debug_info.append(f"启用的配置数: {enabled_count[0]}")
        
        # 检查具体配置类型和完整性
        configs_query = db.session.execute(text("SELECT id, type, enabled, corp_id, appid, appsecret, secret FROM t_wechat_alarm_config WHERE enabled=1")).fetchall()
        
        official_config = None
        enterprise_config = None
        
        for config in configs_query:
            config_id, config_type, enabled, corp_id, appid, appsecret, secret = config
            debug_info.append(f"配置 ID={config_id}: type={config_type}, corp_id={'有' if corp_id else '无'}, appid={'有' if appid else '无'}, appsecret={'有' if appsecret else '无'}, secret={'有' if secret else '无'}")
            
            if config_type == 'official':
                official_config = config
            elif config_type == 'enterprise':
                enterprise_config = config
        
        # 优先级判断逻辑：根据界面设置和配置完整性
        preferred_type = "official"  # 根据界面设置，用户勾选了"启用公众号告警"
        debug_info.append(f"界面设置偏好: {preferred_type}")
        
        from .system_event_alert import WeChatNotifier
        notifier = WeChatNotifier()
        
        # 根据配置完整性和界面设置决定发送方式
        if preferred_type == "official" and official_config:
            config_id, config_type, enabled, corp_id, appid, appsecret, secret = official_config
            if appid and appsecret:
                debug_info.append("✅ 使用公众号配置发送")
                # 直接调用公众号发送方法
                result = notifier._send_official_wechat_raw(appid, appsecret, "界面测试", "测试用户", "high", "TEST_DEVICE")
            else:
                debug_info.append("❌ 公众号配置不完整，降级使用企业微信")
                result = notifier.send_alert("API_TEST", "测试用户", "high", "TEST_API")
        else:
            debug_info.append("📤 使用默认逻辑（优先公众号）")
            result = notifier.send_alert("API_TEST", "测试用户", "high", "TEST_API")
        
        return jsonify({'success': True, 'result': result, 'debug': debug_info})
    except Exception as e:
        import traceback
        debug_info.append(f"异常: {str(e)}")
        return jsonify({'success': False, 'error': str(e), 'debug': debug_info, 'traceback': traceback.format_exc()})

def main():#应用启动入口
    """应用启动入口"""
    import os
    port=int(os.environ.get('APP_PORT',5225))#支持环境变量配置端口 - 本地调试默认5225
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'  # 通过环境变量控制调试模式
    socketio.run(app,host='0.0.0.0',port=port,debug=debug_mode,allow_unsafe_werkzeug=True)

if __name__ == "__main__":
    # 在应用启动后初始化系统事件处理器
    with app.app_context():
        try:
            from .system_event_alert import init_processor
            init_processor()
            print("🚀系统事件处理器已初始化")
        except Exception as e:
            print(f"⚠️系统事件处理器初始化失败:{e}")
        
        # 初始化健康配置缓存监听器
        try:
            health_config_listener = get_health_config_listener()
            print("🎧 健康配置缓存监听器已初始化")
        except Exception as e:
            print(f"⚠️健康配置监听器初始化失败:{e}")
        
        # 初始化性能指标收集器
        try:
            from .metrics_collector import MetricsCollector
            global metrics_collector
            metrics_collector = MetricsCollector(retention_hours=24, collection_interval=30)
            # 注册健康数据优化器作为数据源
            from .health_data_batch_processor import health_data_optimizer
            if health_data_optimizer:
                metrics_collector.register_data_source('health_optimizer', health_data_optimizer.sharded_processor)
            metrics_collector.start()
            print("📊 性能指标收集器已初始化")
        except Exception as e:
            print(f"⚠️性能指标收集器初始化失败:{e}")
            metrics_collector = None
        
        # 初始化健康基线和评分定时任务调度器
        try:
            from .health_baseline_scheduler import init_health_baseline_scheduler
            scheduler = init_health_baseline_scheduler(app)
            print("🏥健康基线调度器已初始化")
        except Exception as e:
            print(f"⚠️健康基线调度器初始化失败:{e}")
        
        # 初始化健康系统缓存服务
        try:
            import asyncio
            from .health_cache_service import health_cache_service
            
            # 创建异步任务初始化缓存服务
            async def init_health_cache():
                await health_cache_service.initialize()
                print("💾健康数据缓存服务已初始化")
            
            # 在新的事件循环中运行初始化
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(init_health_cache())
            loop.close()
            
        except Exception as e:
            print(f"⚠️健康缓存服务初始化失败:{e}")
        
        # 初始化Redis Stream系统
        try:
            # 初始化Stream管理器
            # stream_manager = get_stream_manager()  # Stream系统已禁用
            print("Redis Stream系统已禁用")
            print("🌊 Redis Stream管理器已初始化")
            
            # 初始化消费者管理器
            # consumer_manager = get_consumer_manager()  # Stream系统已禁用
            consumer_manager.start_all_consumers()
            print("🔄 Stream消费者已启动")
            
            # 初始化灰度切换管理器
            # switch_manager = get_switch_manager()  # Stream系统已禁用
            print("🎛️  灰度切换管理器已初始化")
            
            # 初始化回滚预案
            # rollback_plan = get_rollback_plan()  # Stream系统已禁用
            backup_result = rollback_plan.create_migration_backup()
            if 'error' not in backup_result:
                print(f"💾 迁移备份已创建: {backup_result['backup_id']}")
            else:
                print(f"⚠️ 迁移备份创建失败: {backup_result['error']}")
            
            print("🚀 Redis Stream系统初始化完成")
            print("📊 监控仪表板: http://localhost:5225/stream_monitor/")
            
        except Exception as e:
            print(f"⚠️ Redis Stream系统初始化失败:{e}")
            import traceback
            print(f"详细错误: {traceback.format_exc()}")
            
        except Exception as e:
            print(f"⚠️健康基线调度器初始化失败:{e}")
            import traceback
            print(f"详细错误: {traceback.format_exc()}")
    
    main()

# 健康基线管理API
@app.route('/api/health-baseline/generate', methods=['POST'])
@log_api_request('/api/health-baseline/generate', 'POST')
def manual_generate_baseline():
    """手动触发健康基线生成"""
    try:
        data = request.get_json() or {}
        user_id = data.get('userId')
        org_id = data.get('orgId')
        start_date = data.get('startDate')
        end_date = data.get('endDate')
        
        from .health_baseline_scheduler import get_health_baseline_scheduler
        scheduler = get_health_baseline_scheduler(app)
        
        result = scheduler.manual_generate_baseline(
            user_id=user_id,
            org_id=org_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'手动生成基线失败: {str(e)}'
        }), 500

@app.route('/api/health-baseline/status', methods=['GET'])
@log_api_request('/api/health-baseline/status', 'GET')
def get_baseline_status():
    """获取健康基线生成状态"""
    try:
        from .health_baseline_scheduler import get_health_baseline_scheduler
        
        scheduler = get_health_baseline_scheduler()
        
        # 获取基线统计信息
        from .models import HealthBaseline, OrgHealthBaseline
        
        personal_count = db.session.query(func.count(HealthBaseline.baseline_id)).filter(
            HealthBaseline.is_current == True
        ).scalar()
        
        org_count = db.session.query(func.count(OrgHealthBaseline.id)).scalar()
        
        latest_personal = db.session.query(
            func.max(HealthBaseline.baseline_time)
        ).scalar()
        
        latest_org = db.session.query(
            func.max(OrgHealthBaseline.update_time)
        ).scalar()
        
        return jsonify({
            'success': True,
            'data': {
                'scheduler_running': scheduler.running if scheduler else False,
                'personal_baselines': personal_count,
                'org_baselines': org_count,
                'latest_personal_baseline': latest_personal.strftime('%Y-%m-%d %H:%M:%S') if latest_personal else None,
                'latest_org_baseline': latest_org.strftime('%Y-%m-%d %H:%M:%S') if latest_org else None,
                'schedule_info': {
                    'daily_personal': '02:00',
                    'daily_org': '03:00', 
                    'daily_score': '04:00',
                    'weekly': 'Sunday 01:00'
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取基线状态失败: {str(e)}'
        }), 500

@app.route('/api/system-event/queue/retry/<int:queue_id>', methods=['POST'])
def retry_queue_item(queue_id):
    """重试失败队列项"""
    try:
        from .models import EventAlarmQueue
        from .system_event_alert import get_processor, parse_common_event
        
        queue_item = EventAlarmQueue.query.get_or_404(queue_id)
        
        if queue_item.processing_status != 'failed':
            return jsonify({
                'code': 400,
                'success': False,
                'message': f'只能重试失败状态的队列项，当前状态: {queue_item.processing_status}'
            }), 400
        
        # 重建事件数据
        raw_data = queue_item.event_data or {}
        if isinstance(raw_data, str):
            import json
            raw_data = json.loads(raw_data)
        
        # 构建标准事件数据
        event_data_dict = {
            'eventType': queue_item.event_type,
            'deviceSn': queue_item.device_sn,
            'eventValue': queue_item.event_value or '',
            **raw_data
        }
        
        # 重新解析并加入处理队列
        event_data = parse_common_event(event_data_dict)
        processor = get_processor()
        
        # 重置队列状态
        queue_item.processing_status = 'pending'
        queue_item.error_message = None
        queue_item.retry_count += 1
        db.session.commit()
        
        # 重新加入处理队列
        if processor.add_event(event_data):
            return jsonify({
                'code': 200,
                'success': True,
                'message': f'队列项 {queue_id} 已重新加入处理队列'
            })
        else:
            return jsonify({
                'code': 500,
                'success': False,
                'message': '重新加入处理队列失败'
            }), 500
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'success': False, 'error': str(e)}), 500

@app.route('/api/system-event/queue/retry-all-failed', methods=['POST'])
def retry_all_failed_queue():
    """重试所有失败队列项"""
    try:
        from .models import EventAlarmQueue
        from .system_event_alert import get_processor, parse_common_event
        
        failed_items = EventAlarmQueue.query.filter_by(processing_status='failed').all()
        
        if not failed_items:
            return jsonify({
                'code': 200,
                'success': True,
                'message': '没有失败的队列项需要重试'
            })
        
        processor = get_processor()
        success_count = 0
        failed_count = 0
        
        for queue_item in failed_items:
            try:
                # 重建事件数据
                raw_data = queue_item.event_data or {}
                if isinstance(raw_data, str):
                    import json
                    raw_data = json.loads(raw_data)
                
                # 构建标准事件数据
                event_data_dict = {
                    'eventType': queue_item.event_type,
                    'deviceSn': queue_item.device_sn,
                    'eventValue': queue_item.event_value or '',
                    **raw_data
                }
                
                # 重新解析并加入处理队列
                event_data = parse_common_event(event_data_dict)
                
                # 重置队列状态
                queue_item.processing_status = 'pending'
                queue_item.error_message = None
                queue_item.retry_count += 1
                
                # 重新加入处理队列
                if processor.add_event(event_data):
                    success_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                print(f"重试队列项 {queue_item.id} 失败: {e}")
                failed_count += 1
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'success': True,
            'message': f'批量重试完成: 成功 {success_count} 项，失败 {failed_count} 项',
            'data': {
                'total': len(failed_items),
                'success': success_count,
                'failed': failed_count
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'success': False, 'error': str(e)}), 500

@app.route('/api/system-event/processor/restart', methods=['POST'])
def restart_event_processor():
    """重启事件处理器"""
    try:
        # 导入全局处理器并重启
        from .system_event_alert import get_processor
        import sys
        
        # 查找并重置全局处理器
        for module_name in sys.modules:
            if 'system_event_alert' in module_name:
                module = sys.modules[module_name]
                if hasattr(module, '_processor') and module._processor:
                    module._processor.stop()
                    module._processor = None
                    break
        
        # 重新获取处理器
        processor = get_processor()
        
        # 处理积压的pending事件
        from .models import EventAlarmQueue
        pending_count = EventAlarmQueue.query.filter_by(processing_status='pending').count()
        
        return jsonify({
            'code': 200,
            'success': True,
            'message': f'事件处理器重启成功，发现{pending_count}个待处理事件',
            'data': {
                'pending_count': pending_count,
                'is_running': processor.is_running,
                'worker_count': len(processor.workers)
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'success': False, 'error': str(e)}), 500

def general_alert_config():
    """通用告警配置管理"""
    if request.method == 'GET':
        try:
            from .models import db
            from sqlalchemy import text
            
            # 简化配置存储，直接使用默认值
            config = {
                'messageReceiverType': 'manager',
                'customReceivers': '',
                'enableMessageAlert': True,
                'enableWechatAlert': False,
                'emergencyOnly': True
            }
            
            return jsonify({
                'code': 200,
                'success': True,
                'data': config
            })
        except Exception as e:
            return jsonify({'code': 500, 'success': False, 'error': str(e)}), 500
    
    else:  # POST
        try:
            config = request.get_json()
            # 简化实现，只返回成功
            return jsonify({
                'code': 200,
                'success': True,
                'message': '通用告警配置保存成功'
            })
        except Exception as e:
            return jsonify({'code': 500, 'success': False, 'error': str(e)}), 500

@app.route('/api/system-event/process-logs', methods=['GET'])
def get_system_event_process_logs():
    """获取系统事件处理日志"""
    try:
        from .models import SystemEventProcessLog
        
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        device_sn = request.args.get('device_sn')
        process_status = request.args.get('process_status')
        event_type = request.args.get('event_type')
        
        query = SystemEventProcessLog.query
        
        if device_sn:
            query = query.filter(SystemEventProcessLog.device_sn.like(f'%{device_sn}%'))
        if process_status:
            query = query.filter_by(process_status=process_status)
        if event_type:
            query = query.filter(SystemEventProcessLog.event_type.like(f'%{event_type}%'))
        
        logs = query.order_by(SystemEventProcessLog.create_time.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'code': 200,
            'success': True,
            'data': {
                'logs': [log.to_dict() for log in logs.items],
                'total': logs.total,
                'page': page,
                'per_page': per_page,
                'pages': logs.pages
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'success': False, 'error': str(e)}), 500

@app.route('/api/system-event/process-logs/stats', methods=['GET'])
def get_process_logs_stats():
    """获取处理日志统计"""
    try:
        from .models import SystemEventProcessLog
        from sqlalchemy import func, text
        
        # 24小时内统计
        stats = db.session.execute(text("""
            SELECT 
                process_status,
                COUNT(*) as count,
                AVG(process_duration) as avg_duration,
                MAX(process_duration) as max_duration,
                SUM(message_count) as total_messages
            FROM t_system_event_process_log 
            WHERE create_time >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            GROUP BY process_status
        """)).fetchall()
        
        # 设备处理排行
        device_stats = db.session.execute(text("""
            SELECT 
                device_sn,
                COUNT(*) as event_count,
                AVG(process_duration) as avg_duration
            FROM t_system_event_process_log 
            WHERE create_time >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            GROUP BY device_sn 
            ORDER BY event_count DESC 
            LIMIT 10
        """)).fetchall()
        
        return jsonify({
            'code': 200,
            'success': True,
            'data': {
                'status_stats': [
                    {
                        'status': row[0],
                        'count': row[1],
                        'avg_duration': float(row[2]) if row[2] else 0,
                        'max_duration': row[3] or 0,
                        'total_messages': row[4] or 0
                    } for row in stats
                ],
                'device_stats': [
                    {
                        'device_sn': row[0],
                        'event_count': row[1],
                        'avg_duration': float(row[2]) if row[2] else 0
                    } for row in device_stats
                ]
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'success': False, 'error': str(e)}), 500
# 在 bigscreen_main.py 中添加紧急告警获取接口
@app.route('/api/emergency_alerts')
def get_emergency_alerts():
    """获取紧急告警列表-供大屏使用"""
    try:
        redis_helper = RedisHelper()
        
        # 从Redis获取紧急告警
        emergency_alerts = []
        alert_keys = redis_helper.lrange("emergency_alerts", 0, -1)
        
        for alert_key in alert_keys:
            try:
                alert_data = json.loads(alert_key)
                alert_id = alert_data['alert_id']
                
                # 从数据库获取详细信息
                alert_info = AlertInfo.query.get(alert_id)
                if alert_info and alert_info.alert_status == 'pending':
                    emergency_alerts.append({
                        'alert_id': alert_info.id,
                        'alert_type': alert_info.alert_type,
                        'device_sn': alert_info.device_sn,
                        'alert_desc': alert_info.alert_desc,
                        'severity_level': alert_info.severity_level,
                        'alert_timestamp': alert_info.alert_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        'latitude': float(alert_info.latitude),
                        'longitude': float(alert_info.longitude),
                        'user_id': alert_info.user_id,
                        'org_id': alert_info.org_id
                    })
            except Exception as e:
                logger.error(f"解析紧急告警失败:{e}")
                continue
        
        return jsonify({
            'success': True,
            'data': emergency_alerts,
            'count': len(emergency_alerts)
        })
        
    except Exception as e:
        logger.error(f"获取紧急告警失败:{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/handle_emergency_alert', methods=['POST'])
def handle_emergency_alert():
    """处理紧急告警-人工确认"""
    try:
        data = request.json
        alert_id = data.get('alert_id')
        action = data.get('action', 'acknowledged')  # acknowledged, resolved
        handler = data.get('handler', 'system')
        
        # 更新告警状态
        alert_info = AlertInfo.query.get(alert_id)
        if alert_info:
            alert_info.alert_status = 'responded' if action == 'acknowledged' else 'resolved'
            alert_info.responded_time = datetime.now()
            alert_info.assigned_user = handler
            
            db.session.commit()
            
            # 从Redis中移除
            redis_helper = RedisHelper()
            redis_helper.lrem("emergency_alerts", 0, json.dumps({
                'alert_id': alert_id,
                'timestamp': alert_info.alert_timestamp.isoformat(),
                'status': 'new'
            }))
            
            return jsonify({
                'success': True,
                'message': f'紧急告警已{action}',
                'alert_id': alert_id
            })
        
        return jsonify({
            'success': False,
            'message': '告警记录不存在'
        }), 404
        
    except Exception as e:
        logger.error(f"处理紧急告警失败:{e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
@app.route('/api/alert_system_status')
def get_alert_system_status():
    """获取告警系统状态"""
    try:
        from .unified_alert_processor import get_unified_processor
        processor = get_unified_processor()
        
        stats = processor.get_stats()
        
        return jsonify({
            'success': True,
            'data': {
                'system_status': 'running' if processor.running else 'stopped',
                'worker_count': len(processor.workers),
                'queue_stats': stats['queue_stats'],
                'processing_stats': stats['processing_stats'],
                'uptime': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
# ========== 健康系统API接口 ==========

@app.route('/api/health/profile/generate', methods=['POST'])
def api_health_profile_generate_v2():
    """健康画像生成接口"""
    try:
        data = request.get_json()
        device_sn = data.get('deviceSn')
        include_health_data = data.get('includeHealthData', True)
        include_user_info = data.get('includeUserInfo', True)
        
        if not device_sn:
            return jsonify({
                'success': False,
                'message': '设备序列号不能为空'
            }), 400
        
        # 获取用户信息
        from .user import get_user_info_by_deviceSn
        user_info = get_user_info_by_deviceSn(device_sn)
        
        if not user_info:
            return jsonify({
                'success': False,
                'message': '未找到设备对应的用户'
            }), 404
        
        # 生成健康画像
        from .health_profile_engine import RealTimeHealthProfileEngine
        profile_engine = RealTimeHealthProfileEngine()
        
        profile_data = profile_engine.generate_personal_profile(
            user_id=user_info.get('id'),
            device_sn=device_sn,
            include_health_data=include_health_data,
            include_user_info=include_user_info
        )
        
        return jsonify({
            'success': True,
            'data': profile_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"健康画像生成失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health/baseline/personal', methods=['POST'])
def api_health_baseline_personal():
    """个人健康基线查询接口"""
    try:
        data = request.get_json()
        device_sn = data.get('deviceSn')
        date_range = data.get('dateRange', 7)  # 默认7天
        metrics = data.get('metrics', ['heart_rate', 'blood_oxygen', 'temperature'])
        
        if not device_sn:
            return jsonify({
                'success': False,
                'message': '设备序列号不能为空'
            }), 400
        
        # 获取用户信息
        from .user import get_user_info_by_deviceSn
        user_info = get_user_info_by_deviceSn(device_sn)
        
        if not user_info:
            return jsonify({
                'success': False,
                'message': '未找到设备对应的用户'
            }), 404
        
        # 获取个人基线数据
        from .health_baseline_engine import RealTimeHealthBaselineEngine
        baseline_engine = RealTimeHealthBaselineEngine()
        
        baseline_data = baseline_engine.get_personal_baseline(
            user_id=user_info.get('id'),
            device_sn=device_sn,
            metrics=metrics,
            date_range=date_range
        )
        
        return jsonify({
            'success': True,
            'data': baseline_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"个人基线查询失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health/realtime/vitals', methods=['GET'])
def api_health_realtime_vitals():
    """实时生命体征数据接口"""
    try:
        device_sn = request.args.get('deviceSn')
        if not device_sn:
            return jsonify({
                'success': False,
                'message': '设备序列号不能为空'
            }), 400
        
        # 获取最新的健康数据
        from .user_health_data import get_latest_health_data
        latest_data = get_latest_health_data(device_sn)
        
        if not latest_data:
            return jsonify({
                'success': True,
                'data': {
                    'heart_rate': {'current': 0, 'min': 0, 'max': 0, 'avg': 0, 'status': 'unknown'},
                    'blood_oxygen': {'current': 0, 'min': 0, 'max': 0, 'avg': 0, 'status': 'unknown'},
                    'temperature': {'current': 0, 'min': 0, 'max': 0, 'avg': 0, 'status': 'unknown'},
                    'timestamp': datetime.now().isoformat()
                }
            })
        
        # 计算24小时内的统计数据
        from datetime import datetime, timedelta
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        from .user_health_data import get_health_data_stats
        stats = get_health_data_stats(device_sn, start_time, end_time)
        
        vitals_data = {
            'heart_rate': {
                'current': latest_data.get('heart_rate', 0),
                'min': stats.get('heart_rate', {}).get('min', 0),
                'max': stats.get('heart_rate', {}).get('max', 0),
                'avg': stats.get('heart_rate', {}).get('avg', 0),
                'status': get_vital_status('heart_rate', latest_data.get('heart_rate', 0))
            },
            'blood_oxygen': {
                'current': latest_data.get('blood_oxygen', 0),
                'min': stats.get('blood_oxygen', {}).get('min', 0),
                'max': stats.get('blood_oxygen', {}).get('max', 0),
                'avg': stats.get('blood_oxygen', {}).get('avg', 0),
                'status': get_vital_status('blood_oxygen', latest_data.get('blood_oxygen', 0))
            },
            'temperature': {
                'current': latest_data.get('temperature', 0),
                'min': stats.get('temperature', {}).get('min', 0),
                'max': stats.get('temperature', {}).get('max', 0),
                'avg': stats.get('temperature', {}).get('avg', 0),
                'status': get_vital_status('temperature', latest_data.get('temperature', 0))
            },
            'timestamp': latest_data.get('timestamp', datetime.now().isoformat())
        }
        
        return jsonify({
            'success': True,
            'data': vitals_data
        })
        
    except Exception as e:
        logger.error(f"获取实时生命体征失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health/comprehensive/score', methods=['POST'])
def api_health_comprehensive_score():
    """健康综合评分接口"""
    try:
        data = request.get_json()
        device_sn = data.get('deviceSn')
        include_prediction = data.get('includePrediction', True)
        include_factors = data.get('includeFactors', True)
        
        if not device_sn:
            return jsonify({
                'success': False,
                'message': '设备序列号不能为空'
            }), 400
        
        # 获取用户信息
        from .user import get_user_info_by_deviceSn
        user_info = get_user_info_by_deviceSn(device_sn)
        
        if not user_info:
            return jsonify({
                'success': False,
                'message': '未找到设备对应的用户'
            }), 404
        
        # 计算综合健康评分
        from .health_score_engine import RealTimeHealthScoreEngine
        score_engine = RealTimeHealthScoreEngine()
        
        comprehensive_score = score_engine.calculate_comprehensive_score(
            user_id=user_info.get('id'),
            device_sn=device_sn,
            include_prediction=include_prediction,
            include_factors=include_factors
        )
        
        return jsonify({
            'success': True,
            'data': comprehensive_score,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        api_logger.error(f"综合健康评分计算失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health/recommendations', methods=['GET'])
def api_health_recommendations():
    """健康建议查询接口 - 支持多种参数模式"""
    try:
        device_sn = request.args.get('deviceSn')
        analysis_type = request.args.get('analysisType', 'comprehensive')
        days = int(request.args.get('days', 7))
        
        # 支持不同的调用模式
        if device_sn:
            # 基于设备的个人健康建议
            # 获取用户信息
            from .user import get_user_id_by_deviceSn
            user_id = get_user_id_by_deviceSn(device_sn)
            
            if not user_id:
                return jsonify({
                    'success': False,
                    'error': f'设备{device_sn}未找到对应用户'
                }), 404
        else:
            # 通用健康建议（无需特定设备）
            return jsonify({
                'success': True,
                'data': {
                    'recommendations': generate_default_health_recommendations(),
                    'analysisType': analysis_type,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            })
        
        # 获取用户信息
        from .user import get_user_id_by_deviceSn
        user_id = get_user_id_by_deviceSn(device_sn)
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': f'设备{device_sn}未找到对应用户'
            }), 404
        
        # 获取用户组织信息
        from .device import get_device_user_org_info
        org_info = get_device_user_org_info(device_sn)
        
        if not org_info or not org_info.get('success'):
            return jsonify({
                'success': False,
                'error': f'设备{device_sn}未找到对应组织: {org_info.get("message", "未知错误") if org_info else "查询失败"}'
            }), 404
            
        org_id = org_info.get('org_id')
        
        # 计算日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        api_logger.info(f"💡 获取健康建议: deviceSn={device_sn}, userId={user_id}, orgId={org_id}, days={days}")
        
        # 获取健康数据用于生成建议
        health_result = get_all_health_data_optimized(
            orgId=org_id,
            userId=user_id,
            startDate=start_date_str,
            endDate=end_date_str,
            latest_only=False
        )
        
        if not health_result.get('success'):
            # 如果没有健康数据，返回通用建议
            recommendations = generate_default_health_recommendations()
        else:
            health_data = health_result.get('data', {}).get('healthData', [])
            recommendations = generate_health_recommendations_from_data(health_data, days)
        
        return jsonify({
            'success': True,
            'data': {
                'deviceSn': device_sn,
                'userId': str(user_id),
                'orgId': str(org_id),
                'recommendationDate': datetime.now().isoformat(),
                'analysisPeriod': f'{days}天',
                'dateRange': {
                    'startDate': start_date_str,
                    'endDate': end_date_str
                },
                'recommendations': recommendations
            }
        })
        
    except Exception as e:
        api_logger.error(f"❌ 获取健康建议失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取健康建议失败: {str(e)}'
        }), 500
        
        # 获取用户信息
        from .user import get_user_info_by_deviceSn
        user_info = get_user_info_by_deviceSn(device_sn)
        
        if not user_info:
            return jsonify({
                'success': False,
                'message': '未找到设备对应的用户'
            }), 404
        
        # 生成健康建议
        from .health_recommendation_engine import RealTimeHealthRecommendationEngine
        recommendation_engine = RealTimeHealthRecommendationEngine()
        
        recommendations = recommendation_engine.generate_recommendations(
            user_id=user_info.get('id'),
            device_sn=device_sn,
            recommendation_type=recommendation_type
        )
        
        return jsonify({
            'success': True,
            'data': recommendations,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"健康建议生成失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health/waveform', methods=['GET'])
def api_health_waveform():
    """实时波形数据接口"""
    try:
        device_sn = request.args.get('deviceSn')
        metric = request.args.get('metric', 'heart_rate')  # heart_rate, blood_oxygen, temperature
        time_range = int(request.args.get('timeRange', 300))  # 默认5分钟
        
        if not device_sn:
            return jsonify({
                'success': False,
                'message': '设备序列号不能为空'
            }), 400
        
        # 获取波形数据
        from datetime import datetime, timedelta
        end_time = datetime.now()
        start_time = end_time - timedelta(seconds=time_range)
        
        from .user_health_data import get_waveform_data
        waveform_data = get_waveform_data(device_sn, metric, start_time, end_time)
        
        return jsonify({
            'success': True,
            'data': {
                'metric': metric,
                'timeRange': time_range,
                'points': waveform_data,
                'startTime': start_time.isoformat(),
                'endTime': end_time.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"获取波形数据失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health/trends/comprehensive', methods=['POST'])
def api_health_trends_comprehensive():
    """健康数据趋势分析接口"""
    try:
        data = request.get_json()
        device_sn = data.get('deviceSn')
        time_range = data.get('timeRange', '7d')  # 7d, 30d, 90d
        metrics = data.get('metrics', ['heart_rate', 'blood_oxygen', 'temperature', 'step'])
        
        if not device_sn:
            return jsonify({
                'success': False,
                'message': '设备序列号不能为空'
            }), 400
        
        # 解析时间范围
        time_map = {'1d': 1, '7d': 7, '30d': 30, '90d': 90}
        days = time_map.get(time_range, 7)
        
        from datetime import datetime, timedelta
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # 获取趋势数据
        from .user_health_data import get_health_trends_comprehensive
        trends_data = get_health_trends_comprehensive(device_sn, metrics, start_time, end_time)
        
        return jsonify({
            'success': True,
            'data': trends_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"健康趋势分析失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ========== 健康数据智能分析系统 API 端点 ==========

# 权重管理 API
@app.route('/api/weight/user/all', methods=['GET'])
def api_get_user_weights():
    """获取用户所有体征权重配置"""
    try:
        user_id = request.args.get('userId')
        customer_id = request.args.get('customerId')
        
        if not user_id or not customer_id:
            return jsonify({
                'success': False,
                'message': '用户ID和租户ID不能为空'
            }), 400
        
        weight_calculator = WeightCalculator()
        weights = weight_calculator.get_all_user_weights(int(user_id), int(customer_id))
        
        return jsonify({
            'success': True,
            'data': weights,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取用户权重配置失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/weight/metric/update', methods=['POST'])
def api_update_metric_weight():
    """更新体征权重"""
    try:
        data = request.get_json()
        customer_id = data.get('customerId')
        metric_name = data.get('metricName')
        new_weight = data.get('newWeight')
        
        if not all([customer_id, metric_name, new_weight]):
            return jsonify({
                'success': False,
                'message': '必填参数不能为空'
            }), 400
        
        weight_calculator = WeightCalculator()
        success = weight_calculator.update_metric_weight(
            int(customer_id), metric_name, float(new_weight)
        )
        
        return jsonify({
            'success': success,
            'message': '权重更新成功' if success else '权重更新失败',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"更新体征权重失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/weight/position/update', methods=['POST'])
def api_update_position_weight():
    """更新岗位权重"""
    try:
        data = request.get_json()
        position_id = data.get('positionId')
        new_weight = data.get('newWeight')
        
        if not all([position_id, new_weight]):
            return jsonify({
                'success': False,
                'message': '岗位ID和权重值不能为空'
            }), 400
        
        weight_calculator = WeightCalculator()
        success = weight_calculator.update_position_weight(
            int(position_id), float(new_weight)
        )
        
        return jsonify({
            'success': success,
            'message': '岗位权重更新成功' if success else '岗位权重更新失败',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"更新岗位权重失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/weight/statistics', methods=['GET'])
def api_get_weight_statistics():
    """获取权重配置统计信息"""
    try:
        customer_id = request.args.get('customerId')
        
        if not customer_id:
            return jsonify({
                'success': False,
                'message': '租户ID不能为空'
            }), 400
        
        weight_calculator = WeightCalculator()
        statistics = weight_calculator.get_weight_statistics(int(customer_id))
        
        return jsonify({
            'success': True,
            'data': statistics,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取权重统计信息失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/weight/validation', methods=['GET'])
def api_validate_weight_configuration():
    """验证权重配置合理性"""
    try:
        customer_id = request.args.get('customerId')
        
        if not customer_id:
            return jsonify({
                'success': False,
                'message': '租户ID不能为空'
            }), 400
        
        weight_calculator = WeightCalculator()
        validation_result = weight_calculator.validate_weight_configuration(int(customer_id))
        
        return jsonify({
            'success': True,
            'data': validation_result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"验证权重配置失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 健康基线管理 API
@app.route('/api/baseline/user/generate', methods=['POST'])
def api_generate_user_baseline():
    """生成用户个人健康基线"""
    try:
        data = request.get_json()
        user_id = data.get('userId')
        customer_id = data.get('customerId')
        days_back = data.get('daysBack', 90)
        force_update = data.get('forceUpdate', False)
        
        if not user_id or not customer_id:
            return jsonify({
                'success': False,
                'message': '用户ID和租户ID不能为空'
            }), 400
        
        baseline_manager = HealthBaselineManager()
        result = baseline_manager.generate_user_baseline(
            int(user_id), int(customer_id), int(days_back), force_update
        )
        
        return jsonify({
            'success': True,
            'data': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"生成用户基线失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/baseline/population/generate', methods=['POST'])
def api_generate_population_baseline():
    """生成人群健康基线"""
    try:
        data = request.get_json()
        customer_id = data.get('customerId')
        age_group = data.get('ageGroup')
        gender = data.get('gender')
        days_back = data.get('daysBack', 90)
        force_update = data.get('forceUpdate', False)
        
        if not customer_id:
            return jsonify({
                'success': False,
                'message': '租户ID不能为空'
            }), 400
        
        baseline_manager = HealthBaselineManager()
        result = baseline_manager.generate_population_baseline(
            int(customer_id), age_group, gender, int(days_back), force_update
        )
        
        return jsonify({
            'success': True,
            'data': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"生成人群基线失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/baseline/user/get', methods=['GET'])
def api_get_user_baseline():
    """获取用户健康基线"""
    try:
        user_id = request.args.get('userId')
        metric_name = request.args.get('metricName')
        
        if not user_id:
            return jsonify({
                'success': False,
                'message': '用户ID不能为空'
            }), 400
        
        baseline_manager = HealthBaselineManager()
        baseline = baseline_manager.get_user_baseline(int(user_id), metric_name)
        
        return jsonify({
            'success': True,
            'data': baseline,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取用户基线失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/baseline/compare', methods=['GET'])
def api_compare_with_baseline():
    """与基线对比分析"""
    try:
        user_id = request.args.get('userId')
        customer_id = request.args.get('customerId')
        days_back = request.args.get('daysBack', 30)
        
        if not user_id or not customer_id:
            return jsonify({
                'success': False,
                'message': '用户ID和租户ID不能为空'
            }), 400
        
        baseline_manager = HealthBaselineManager()
        comparison = baseline_manager.compare_user_with_baseline(
            int(user_id), int(customer_id), int(days_back)
        )
        
        return jsonify({
            'success': True,
            'data': comparison,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"基线对比分析失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 健康建议管理 API
@app.route('/api/recommendation/generate', methods=['POST'])
def api_generate_recommendations():
    """查询个性化健康建议 - ljwx-bigscreen只负责查询ljwx-boot生成的建议"""
    try:
        data = request.get_json()
        user_id = data.get('userId')
        customer_id = data.get('customerId')
        
        if not user_id or not customer_id:
            return jsonify({
                'success': False,
                'message': '用户ID和租户ID不能为空'
            }), 400
        
        recommendation_engine = RealTimeHealthRecommendationEngine()
        recommendations = recommendation_engine.generate_personalized_recommendations(
            int(user_id), int(customer_id)
        )
        
        return jsonify({
            'success': True,
            'data': recommendations,
            'count': len(recommendations),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"生成健康建议失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/recommendation/user/list', methods=['GET'])
def api_get_user_recommendations():
    """获取用户建议列表"""
    try:
        user_id = request.args.get('userId')
        status = request.args.get('status')
        limit = request.args.get('limit', 10)
        
        if not user_id:
            return jsonify({
                'success': False,
                'message': '用户ID不能为空'
            }), 400
        
        recommendation_engine = RealTimeHealthRecommendationEngine()
        recommendations = recommendation_engine.get_user_recommendations(
            int(user_id), status, int(limit)
        )
        
        return jsonify({
            'success': True,
            'data': recommendations,
            'count': len(recommendations),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取用户建议列表失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/recommendation/progress/update', methods=['POST'])
def api_update_recommendation_progress():
    """更新建议执行进度"""
    try:
        data = request.get_json()
        recommendation_id = data.get('recommendationId')
        user_feedback = data.get('userFeedback')
        progress_data = data.get('progressData', {})
        
        if not recommendation_id:
            return jsonify({
                'success': False,
                'message': '建议ID不能为空'
            }), 400
        
        recommendation_engine = RealTimeHealthRecommendationEngine()
        success = recommendation_engine.update_recommendation_progress(
            int(recommendation_id), user_feedback, progress_data
        )
        
        return jsonify({
            'success': success,
            'message': '进度更新成功' if success else '进度更新失败',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"更新建议进度失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/recommendation/effectiveness/evaluate', methods=['GET'])
def api_evaluate_recommendation_effectiveness():
    """评估建议执行效果"""
    try:
        recommendation_id = request.args.get('recommendationId')
        
        if not recommendation_id:
            return jsonify({
                'success': False,
                'message': '建议ID不能为空'
            }), 400
        
        recommendation_engine = RealTimeHealthRecommendationEngine()
        effectiveness = recommendation_engine.evaluate_recommendation_effectiveness(
            int(recommendation_id)
        )
        
        if effectiveness is None:
            return jsonify({
                'success': False,
                'message': '无法评估建议效果，可能是建议未完成或数据不足'
            }), 404
        
        return jsonify({
            'success': True,
            'data': effectiveness,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"评估建议效果失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 建议跟踪系统 API
@app.route('/api/tracking/daily/check', methods=['GET'])
def api_daily_recommendation_check():
    """每日建议检查和提醒"""
    try:
        customer_id = request.args.get('customerId')
        
        if not customer_id:
            return jsonify({
                'success': False,
                'message': '租户ID不能为空'
            }), 400
        
        from .recommendation_tracker import RecommendationTracker
        tracker = RecommendationTracker()
        check_result = tracker.daily_recommendation_check(int(customer_id))
        
        return jsonify({
            'success': True,
            'data': check_result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"每日建议检查失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tracking/followup/generate', methods=['POST'])
def api_generate_followup_recommendations():
    """自动生成后续建议"""
    try:
        data = request.get_json()
        user_id = data.get('userId')
        customer_id = data.get('customerId')
        
        if not user_id or not customer_id:
            return jsonify({
                'success': False,
                'message': '用户ID和租户ID不能为空'
            }), 400
        
        from .recommendation_tracker import RecommendationTracker
        tracker = RecommendationTracker()
        follow_up_recommendations = tracker.auto_generate_follow_up_recommendations(
            int(user_id), int(customer_id)
        )
        
        return jsonify({
            'success': True,
            'data': follow_up_recommendations,
            'count': len(follow_up_recommendations),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"生成后续建议失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tracking/recommendation/effects', methods=['GET'])
def api_get_recommendation_effects():
    """获取建议执行效果"""
    try:
        recommendation_id = request.args.get('recommendationId')
        
        if not recommendation_id:
            return jsonify({
                'success': False,
                'message': '建议ID不能为空'
            }), 400
        
        tracker = RecommendationTracker()
        effects = tracker.get_recommendation_effects(int(recommendation_id))
        
        return jsonify({
            'success': True,
            'data': effects,
            'count': len(effects) if effects else 0,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取建议效果失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 综合健康评分 API（已集成权重系统）
@app.route('/api/health/score/comprehensive', methods=['GET'])
def api_get_comprehensive_health_score():
    """获取综合健康评分（已集成权重系统）- 支持多种查询方式"""
    try:
        # 支持多种参数组合
        user_id = request.args.get('userId')
        org_id = request.args.get('orgId')
        customer_id = request.args.get('customerId')
        device_sn = request.args.get('deviceSn')
        date_range = request.args.get('dateRange', 30)
        days = request.args.get('days', 7)
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        include_factors = request.args.get('includeFactors', 'false').lower() == 'true'
        
        # 参数验证和处理逻辑 - 按照粒度层级处理
        if device_sn:
            # 通过deviceSn获取用户信息
            from .user import get_user_info_by_deviceSn
            user_info = get_user_info_by_deviceSn(device_sn)
            if not user_info:
                return jsonify({
                    'success': False,
                    'error': f'设备{device_sn}未找到对应用户'
                }), 404
            user_id = user_info.get('id')
            org_id = user_info.get('org_id')
            customer_id = user_info.get('customer_id')
            
        # 使用统一的健康评分引擎
        from .health_score_engine import get_health_score_unified
        
        api_logger.info(f"🔍 综合健康评分请求: userId={user_id}, orgId={org_id}, customerId={customer_id}, deviceSn={device_sn}")
        
        # 构建查询参数
        query_kwargs = {}
        if user_id:
            query_kwargs['user_id'] = user_id
        if org_id:
            query_kwargs['org_id'] = org_id
        if customer_id:
            query_kwargs['customer_id'] = customer_id
        if start_date:
            query_kwargs['startDate'] = start_date
        if end_date:
            query_kwargs['endDate'] = end_date
            
        # 参数验证 - 至少需要一个标识符
        if not any([user_id, org_id, customer_id]):
            return jsonify({
                'success': False,
                'message': '缺少必需参数：userId、orgId、customerId 至少需要提供一个',
                'code': 400
            }), 400
        
        # 调用统一的健康评分方法
        score_result = get_health_score_unified(**query_kwargs)
        
        if score_result.get('success'):
            return jsonify({
                'success': True,
                'data': score_result.get('data'),
                'timestamp': datetime.now().isoformat(),
                'query_params': query_kwargs
            })
        else:
            return jsonify({
                'success': False,
                'message': score_result.get('error', '健康评分计算失败'),
                'code': 500
            }), 500
        
    except Exception as e:
        logger.error(f"获取综合健康评分失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def get_all_users_health_score_by_customer(customer_id, days=7):
    """按租户ID获取所有用户的健康评分统计"""
    try:
        from .models import UserInfo
        from .health_score_engine import RealTimeHealthScoreEngine
        from datetime import datetime, timedelta
        import statistics
        
        # 获取租户下所有用户
        users = UserInfo.query.filter_by(
            customer_id=customer_id, 
            is_deleted=False, 
            status='1'
        ).all()
        
        if not users:
            return jsonify({
                'success': False,
                'error': f'租户{customer_id}下未找到有效用户'
            }), 404
        
        score_engine = RealTimeHealthScoreEngine()
        all_scores = []
        user_scores = []
        health_distribution = {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0}
        
        for user in users:
            try:
                score_detail = score_engine.calculate_comprehensive_health_score(
                    user.id, customer_id, days
                )
                if score_detail and score_detail.get('overall_score'):
                    score = score_detail['overall_score']
                    all_scores.append(score)
                    
                    user_scores.append({
                        'user_id': user.id,
                        'user_name': user.user_name,
                        'device_sn': user.device_sn,
                        'score': score,
                        'level': get_health_level_by_score(score)
                    })
                    
                    # 统计健康等级分布
                    if score >= 90:
                        health_distribution['excellent'] += 1
                    elif score >= 80:
                        health_distribution['good'] += 1
                    elif score >= 70:
                        health_distribution['fair'] += 1
                    else:
                        health_distribution['poor'] += 1
                        
            except Exception as user_error:
                logger.warning(f"计算用户{user.id}健康评分失败: {user_error}")
                continue
        
        if not all_scores:
            return jsonify({
                'success': False,
                'error': '租户下所有用户都无法计算健康评分，可能是数据不足'
            }), 404
        
        # 计算统计数据
        stats = {
            'average_score': round(statistics.mean(all_scores), 1),
            'median_score': round(statistics.median(all_scores), 1),
            'max_score': max(all_scores),
            'min_score': min(all_scores),
            'total_users': len(user_scores),
            'score_distribution': health_distribution
        }
        
        return jsonify({
            'success': True,
            'data': {
                'customer_id': customer_id,
                'statistics': stats,
                'user_scores': sorted(user_scores, key=lambda x: x['score'], reverse=True),
                'date_range_days': days
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"按租户获取健康评分失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def get_health_level_by_score(score):
    """根据分数获取健康等级"""
    if score >= 90:
        return '优秀'
    elif score >= 80:
        return '良好'
    elif score >= 70:
        return '一般'
    else:
        return '需改善'

@app.route('/api/health/score/trend', methods=['GET'])
def api_get_health_score_trend():
    """获取健康评分趋势"""
    try:
        user_id = request.args.get('userId')
        days_back = request.args.get('daysBack', 90)
        
        if not user_id:
            return jsonify({
                'success': False,
                'message': '用户ID不能为空'
            }), 400
        
        from .health_score_engine import RealTimeHealthScoreEngine
        score_engine = RealTimeHealthScoreEngine()
        trends = score_engine.get_user_score_trend(int(user_id), int(days_back))
        
        return jsonify({
            'success': True,
            'data': trends,
            'count': len(trends),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取健康评分趋势失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health/score/analysis', methods=['GET'])
def api_analyze_health_score():
    """健康评分因素分析"""
    try:
        user_id = request.args.get('userId')
        customer_id = request.args.get('customerId')
        
        if not user_id or not customer_id:
            return jsonify({
                'success': False,
                'message': '用户ID和租户ID不能为空'
            }), 400
        
        from .health_score_engine import realtime_score_engine
        # Use the optimized score engine instance
        result = realtime_score_engine.calculate_user_health_score_realtime(int(user_id))
        analysis = result.get('data') if result.get('success') else None
        
        if analysis is None:
            return jsonify({
                'success': False,
                'message': '无法分析健康评分，可能是数据不足'
            }), 404
        
        return jsonify({
            'success': True,
            'data': analysis,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"健康评分分析失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ========== 健康分析系统API - 基于组织架构的完整分析 ==========

@app.route('/api/health/analysis/run', methods=['POST'])
def api_run_health_analysis():
    """运行健康分析 - 支持全客户或指定客户分析"""
    try:
        from .health_analysis_orchestrator import run_health_analysis_for_all_customers, run_health_analysis_for_customer
        
        data = request.get_json() or {}
        customer_id = data.get('customerId') or request.args.get('customerId')
        
        if customer_id:
            # 分析指定客户
            result = run_health_analysis_for_customer(int(customer_id))
            return jsonify(result)
        else:
            # 分析所有客户
            result = run_health_analysis_for_all_customers()
            return jsonify(result)
            
    except Exception as e:
        logger.error(f"健康分析失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '健康分析系统异常'
        }), 500

@app.route('/api/health/analysis/customer/<int:customer_id>/summary', methods=['GET'])
def api_get_customer_health_summary(customer_id):
    """获取客户健康分析汇总"""
    try:
        from .health_analysis_orchestrator import get_customer_health_summary
        
        result = get_customer_health_summary(customer_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"获取客户 {customer_id} 健康汇总失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health/analysis/customers', methods=['GET'])
def api_get_all_customers():
    """获取所有客户列表"""
    try:
        from .org import findTopLevelOrganizations
        
        customers = findTopLevelOrganizations()
        return jsonify({
            'success': True,
            'data': customers,
            'count': len(customers)
        })
        
    except Exception as e:
        logger.error(f"获取客户列表失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health/analysis/customer/<int:customer_id>/orgs', methods=['GET'])
def api_get_customer_orgs(customer_id):
    """获取客户下的所有部门"""
    try:
        from .org import findAllDescendants
        
        org_ids = findAllDescendants(customer_id)
        return jsonify({
            'success': True,
            'data': org_ids,
            'customer_id': customer_id,
            'count': len(org_ids)
        })
        
    except Exception as e:
        logger.error(f"获取客户 {customer_id} 部门失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health/analysis/org/<int:org_id>/users', methods=['GET'])
def api_get_org_users(org_id):
    """获取部门下的所有用户"""
    try:
        from .org import getUserIdsByOrgId
        
        user_ids = getUserIdsByOrgId(org_id)
        return jsonify({
            'success': True,
            'data': user_ids,
            'org_id': org_id,
            'count': len(user_ids)
        })
        
    except Exception as e:
        logger.error(f"获取部门 {org_id} 用户失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health/analysis/orchestrator/stats', methods=['GET'])
def api_get_analysis_stats():
    """获取健康分析编排器统计信息"""
    try:
        from .health_analysis_orchestrator import get_health_analysis_orchestrator
        
        orchestrator = get_health_analysis_orchestrator()
        stats = orchestrator.get_analysis_stats()
        
        return jsonify({
            'success': True,
            'data': stats,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取分析统计失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ========== 健康数据缓存管理API ==========

@app.route('/api/health/cache/stats', methods=['GET'])
def api_health_cache_stats():
    """获取健康数据缓存统计信息"""
    try:
        stats = health_data_cache_integration.get_cache_health_stats()
        return jsonify({
            'success': True,
            'data': stats,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"获取健康缓存统计失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health/cache/clear', methods=['DELETE'])
def api_health_cache_clear():
    """清理健康数据缓存"""
    try:
        user_id = request.args.get('userId')
        org_id = request.args.get('orgId')
        
        if user_id:
            # 清理指定用户缓存
            result = health_data_cache_integration.invalidate_user_cache(
                int(user_id), int(org_id) if org_id else None
            )
            return jsonify({
                'success': True,
                'message': '用户缓存清理完成',
                'data': result
            })
        elif org_id:
            # 清理指定组织缓存
            result = health_data_cache_integration.cache.clear_org_cache(int(org_id))
            return jsonify({
                'success': result,
                'message': '组织缓存清理完成' if result else '组织缓存清理失败'
            })
        else:
            # 清理过期缓存
            deleted_count = health_data_cache_integration.cache.clear_expired_cache()
            return jsonify({
                'success': True,
                'message': f'清理过期缓存完成，删除 {deleted_count} 个键'
            })
    except Exception as e:
        logger.error(f"清理健康缓存失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health/cache/preload', methods=['POST'])
def api_health_cache_preload():
    """预加载健康数据缓存"""
    try:
        data = request.get_json() or {}
        org_id = data.get('orgId')
        user_ids = data.get('userIds', [])
        days_back = data.get('daysBack', 7)
        
        if not org_id:
            return jsonify({
                'success': False,
                'message': '组织ID不能为空'
            }), 400
        
        result = health_data_cache_integration.preload_user_data_cache(
            int(org_id), user_ids, days_back
        )
        
        return jsonify({
            'success': True,
            'message': '缓存预加载完成',
            'data': result
        })
        
    except Exception as e:
        logger.error(f"预加载健康缓存失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ========== 辅助函数 ==========

def get_vital_status(metric, value):
    """根据生命体征数值判断状态"""
    try:
        if not value or value == 0:
            return 'unknown'
        
        if metric == 'heart_rate':
            if 60 <= value <= 100:
                return 'normal'
            elif value < 60:
                return 'low'
            else:
                return 'high'
        elif metric == 'blood_oxygen':
            if value >= 95:
                return 'normal'
            elif value >= 90:
                return 'warning'
            else:
                return 'critical'
        elif metric == 'temperature':
            if 36.0 <= value <= 37.5:
                return 'normal'
            elif value < 36.0:
                return 'low'
            else:
                return 'high'
        else:
            return 'normal'
            
    except Exception:
        return 'unknown'

def generate_default_health_recommendations():
    """生成默认健康建议"""
    return [
        {
            'category': '运动健康',
            'priority': 'high',
            'title': '保持适量运动',
            'content': '建议每天步行8000-10000步，进行30分钟中等强度运动',
            'icon': '🏃'
        },
        {
            'category': '生活作息',
            'priority': 'high', 
            'title': '规律作息',
            'content': '保持规律的睡眠时间，每晚7-8小时充足睡眠',
            'icon': '😴'
        },
        {
            'category': '健康监测',
            'priority': 'medium',
            'title': '定期健康检查',
            'content': '建议定期监测血压、心率等生命体征指标',
            'icon': '📊'
        },
        {
            'category': '饮食营养',
            'priority': 'medium',
            'title': '均衡饮食',
            'content': '保持营养均衡，多食用蔬菜水果，控制高油高糖摄入',
            'icon': '🥗'
        }
    ]

def generate_health_recommendations_from_data(health_data, days):
    """基于健康数据生成个性化建议"""
    if not health_data:
        return generate_default_health_recommendations()
    
    recommendations = []
    
    # 分析健康数据
    heart_rates = [float(item.get('heart_rate', 0)) for item in health_data if item.get('heart_rate')]
    blood_oxygen = [float(item.get('blood_oxygen', 0)) for item in health_data if item.get('blood_oxygen')]
    temperatures = [float(item.get('temperature', 0)) for item in health_data if item.get('temperature')]
    steps = [int(item.get('step', 0)) for item in health_data if item.get('step')]
    
    # 心率建议
    if heart_rates:
        avg_hr = sum(heart_rates) / len(heart_rates)
        if avg_hr > 100:
            recommendations.append({
                'category': '心率监测',
                'priority': 'high',
                'title': '心率偏高提醒',
                'content': f'近{days}天平均心率{avg_hr:.1f}bpm，建议放松心情，避免剧烈运动',
                'icon': '❤️'
            })
        elif avg_hr < 60:
            recommendations.append({
                'category': '心率监测', 
                'priority': 'medium',
                'title': '心率偏低提醒',
                'content': f'近{days}天平均心率{avg_hr:.1f}bpm，建议适度运动增强心肺功能',
                'icon': '❤️'
            })
    
    # 血氧建议
    if blood_oxygen:
        avg_spo2 = sum(blood_oxygen) / len(blood_oxygen)
        if avg_spo2 < 95:
            recommendations.append({
                'category': '血氧监测',
                'priority': 'high', 
                'title': '血氧偏低提醒',
                'content': f'近{days}天平均血氧{avg_spo2:.1f}%，建议进行深呼吸训练，保持室内空气流通',
                'icon': '🫁'
            })
    
    # 体温建议
    if temperatures:
        avg_temp = sum(temperatures) / len(temperatures)
        if avg_temp > 37.3:
            recommendations.append({
                'category': '体温监测',
                'priority': 'high',
                'title': '体温偏高提醒', 
                'content': f'近{days}天平均体温{avg_temp:.1f}°C，请注意休息，如持续发热请就医',
                'icon': '🌡️'
            })
    
    # 运动建议
    if steps:
        avg_steps = sum(steps) / len(steps) if steps else 0
        if avg_steps < 6000:
            recommendations.append({
                'category': '运动健康',
                'priority': 'medium',
                'title': '增加运动量',
                'content': f'近{days}天平均步数{avg_steps:.0f}步，建议增加日常活动，目标每日8000-10000步',
                'icon': '🏃'
            })
        elif avg_steps > 15000:
            recommendations.append({
                'category': '运动健康',
                'priority': 'low',
                'title': '运动量充足',
                'content': f'近{days}天平均步数{avg_steps:.0f}步，运动量很好，注意劳逸结合',
                'icon': '🏃'
            })
    
    # 如果没有特殊建议，添加通用建议
    if not recommendations:
        recommendations = generate_default_health_recommendations()
    else:
        # 添加一般性建议
        recommendations.extend([
            {
                'category': '生活作息',
                'priority': 'low',
                'title': '保持规律作息',
                'content': '建议保持规律的作息时间，充足的睡眠对健康很重要',
                'icon': '😴'
            },
            {
                'category': '定期检查',
                'priority': 'low', 
                'title': '持续健康监测',
                'content': '继续佩戴设备监测健康状况，关注数据变化趋势',
                'icon': '📱'
            }
        ])
    
    return recommendations

@app.route('/api/debug/device/<device_sn>', methods=['GET'])
def debug_device_info(device_sn):
    """调试端点 - 检查设备绑定信息"""
    try:
        api_logger.info(f"🔍 调试设备信息: deviceSn={device_sn}")
        
        # 1. 检查用户ID
        from .user import get_user_id_by_deviceSn
        user_id = get_user_id_by_deviceSn(device_sn)
        
        # 2. 检查组织信息
        from .device import get_device_user_org_info
        org_info = get_device_user_org_info(device_sn)
        
        # 3. 直接查询数据库
        from .models import UserInfo, UserOrg, OrgInfo
        
        db_user = UserInfo.query.filter_by(device_sn=device_sn, is_deleted=False).first()
        
        debug_info = {
            'deviceSn': device_sn,
            'user_id_from_function': user_id,
            'org_info_from_function': org_info,
            'db_user_info': {
                'exists': db_user is not None,
                'user_id': db_user.id if db_user else None,
                'user_name': db_user.user_name if db_user else None,
                'is_deleted': db_user.is_deleted if db_user else None
            } if db_user else None
        }
        
        if db_user:
            # 查询用户组织关系
            user_org = UserOrg.query.filter_by(user_id=db_user.id).first()
            if user_org:
                org = OrgInfo.query.filter_by(id=user_org.org_id, is_deleted=False).first()
                debug_info['db_org_info'] = {
                    'user_org_exists': True,
                    'org_id': user_org.org_id,
                    'org_exists': org is not None,
                    'org_name': org.name if org else None,
                    'org_is_deleted': org.is_deleted if org else None
                }
            else:
                debug_info['db_org_info'] = {'user_org_exists': False}
        
        return jsonify({
            'success': True,
            'debug': debug_info
        })
        
    except Exception as e:
        api_logger.error(f"❌ 调试设备信息失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'deviceSn': device_sn
        }), 500

# =============================================================================
# 标准化API路由别名 - 与前端 API_MAPPINGS 保持一致
# =============================================================================

# 健康评分标准化路由
@app.route('/api/health/scores/comprehensive', methods=['GET'])
def api_health_scores_comprehensive():
    """标准化健康评分路由 - 别名，参数映射处理"""
    try:
        # 参数映射：将 orgId 映射为 customerId
        org_id = request.args.get('orgId')
        if org_id and not request.args.get('customerId'):
            # 创建新的请求参数字典，将 orgId 映射为 customerId
            new_args = request.args.to_dict()
            new_args['customerId'] = org_id
            
            # 临时修改 request.args（通过创建新的查询字符串）
            from werkzeug.datastructures import ImmutableMultiDict
            request.args = ImmutableMultiDict(new_args)
        
        return api_get_comprehensive_health_score()
    except Exception as e:
        api_logger.error(f"标准化健康评分路由错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# 健康图表基线标准化路由
@app.route('/api/health/charts/baseline', methods=['GET'])
def api_health_charts_baseline():
    """标准化健康图表基线路由 - 别名"""
    return health_data_chart_baseline()

# 健康建议标准化路由（别名）
@app.route('/api/health/recommendations/list', methods=['GET'])
def api_health_recommendations_list():
    """标准化健康建议路由 - 别名，重定向到主路由"""
    return api_health_recommendations()

# 实时统计标准化路由
@app.route('/api/statistics/realtime', methods=['GET'])
def api_statistics_realtime():
    """标准化实时统计路由 - 别名"""
    return get_realtime_stats()

# 用户列表标准化路由
@app.route('/api/users/list', methods=['GET'])
def api_users_list():
    """标准化用户列表路由 - 别名"""
    return fetch_users()

# 用户信息标准化路由
@app.route('/api/users/info', methods=['GET'])
def api_users_info():
    """标准化用户信息路由 - 别名"""
    return get_user_info()

# 告警处理标准化路由
@app.route('/api/alerts/handle', methods=['GET'])
def api_alerts_handle():
    """标准化告警处理路由 - 别名"""
    return deal_alert()

# 告警确认标准化路由
@app.route('/api/alerts/acknowledge', methods=['POST'])
def api_alerts_acknowledge():
    """标准化告警确认路由"""
    try:
        data = request.get_json()
        alert_id = data.get('alertId')
        
        if alert_id:
            # 调用现有的告警处理逻辑
            result = deal_alert(alert_id)
            return result
        else:
            return jsonify({'success': False, 'error': '缺少alertId参数'}), 400
            
    except Exception as e:
        api_logger.error(f"告警确认接口错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# 健康基线生成标准化路由
@app.route('/api/health/baseline/generate', methods=['POST'])
def api_health_baseline_generate():
    """标准化健康基线生成路由 - 别名"""
    return api_generate_baseline()

# 健康基线状态标准化路由
@app.route('/api/health/baseline/status', methods=['GET'])
def api_health_baseline_status():
    """标准化健康基线状态路由 - 别名"""
    return api_baseline_status()

# 健康数据详情标准化路由
@app.route('/api/health/data/detail', methods=['GET'])
def api_health_data_detail():
    """标准化健康数据详情路由 - 别名"""
    return fetch_health_data_by_id()

# 健康配置监听器状态API
@app.route('/api/health/config/listener/stats', methods=['GET'])
def api_health_config_listener_stats():
    """获取健康配置监听器状态"""
    try:
        stats = get_listener_stats()
        return jsonify({
            'success': True,
            'data': stats,
            'message': '健康配置监听器状态获取成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取监听器状态失败: {str(e)}'
        }), 500

# 租户启用指标查询API
@app.route('/api/health/config/enabled-metrics', methods=['GET'])
def api_health_config_enabled_metrics():
    """获取租户启用的指标"""
    try:
        customer_id = request.args.get('customerId', request.args.get('customer_id'))
        if not customer_id:
            return jsonify({
                'success': False,
                'error': '缺少customerId参数'
            }), 400
            
        metrics = get_enabled_metrics(int(customer_id))
        return jsonify({
            'success': True,
            'data': {
                'customer_id': int(customer_id),
                'enabled_metrics': metrics,
                'metrics_count': len(metrics)
            },
            'message': '租户启用指标获取成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取启用指标失败: {str(e)}'
        }), 500

# =============================================================================
# License管理接口 (License Management APIs)
# =============================================================================

@app.route('/api/license/status', methods=['GET'])
def api_license_status():
    """获取License状态信息"""
    try:
        license_manager = get_license_manager()
        status = license_manager.get_license_status()
        return jsonify({
            'success': True,
            'data': status,
            'message': 'License状态获取成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取License状态失败: {str(e)}'
        }), 500

@app.route('/api/license/dashboard', methods=['GET'])
def api_license_dashboard():
    """获取License仪表板数据"""
    try:
        dashboard_data = get_license_dashboard_data()
        return jsonify({
            'success': True,
            'data': dashboard_data,
            'message': 'License仪表板数据获取成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取License仪表板数据失败: {str(e)}'
        }), 500

@app.route('/api/license/device/check', methods=['POST'])
def api_license_device_check():
    """检查设备License权限 - 已禁用，始终返回允许"""
    try:
        data = request.get_json()
        device_sn = data.get('device_sn') or data.get('deviceSn')
        customer_id = data.get('customer_id') or data.get('customerId')

        if not device_sn:
            return jsonify({
                'success': False,
                'error': '设备SN不能为空'
            }), 400

        # License功能已禁用，始终返回允许
        # result = check_device_license(device_sn, customer_id)
        return jsonify({
            'success': True,
            'data': {
                'allowed': True,
                'reason': 'License检查已禁用，所有设备均可使用',
                'device_sn': device_sn,
                'customer_id': customer_id
            },
            'message': 'License检查已禁用'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'License设备检查失败: {str(e)}'
        }), 500

@app.route('/license/dashboard')
def license_dashboard_page():
    """License管理仪表板页面"""
    return render_template('license_dashboard.html')

@app.route('/api/test/simple', methods=['GET'])
def test_simple_route():
    """测试简单路由是否存在async问题"""
    return jsonify({
        'success': True,
        'message': 'Simple route test successful',
        'timestamp': datetime.now().isoformat()
    })

system_logger.info('✅ 标准化API路由别名注册完成')
system_logger.info('🔐 License管理接口注册完成')

def create_app():
    """
    Application factory function for creating Flask app instances
    Creates and configures the Flask application with proper SQLAlchemy initialization
    """
    global app, db, socketio
    
    # Return the existing configured app instance
    if app is not None:
        return app
    
    # This should not happen as the app is created globally above,
    # but this provides a fallback for testing scenarios
    from flask import Flask
    from flask_socketio import SocketIO
    
    new_app = Flask(__name__, static_folder='../static')
    new_app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    new_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database with the new app
    db.init_app(new_app)
    
    # Initialize SocketIO
    socketio = SocketIO(new_app, cors_allowed_origins="*")
    
    return new_app

if __name__ == '__main__':
    main()

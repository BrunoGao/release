# -*- coding: utf-8 -*-
"""
LJWX大屏应用Prometheus监控指标模块
提供Python Flask应用的监控指标收集
"""
from flask import Blueprint, Response, request, g
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CollectorRegistry, CONTENT_TYPE_LATEST
import time
import psutil
import threading
import os
import functools

# 创建蓝图
metrics_bp = Blueprint('metrics', __name__)

# 创建独立的指标注册表
registry = CollectorRegistry()

# 应用级指标
REQUEST_COUNT = Counter('flask_http_requests_total', 'HTTP请求总数', ['method', 'endpoint', 'status'], registry=registry)
REQUEST_DURATION = Histogram('flask_http_request_duration_seconds', 'HTTP请求处理时间', ['method', 'endpoint'], registry=registry)
ACTIVE_REQUESTS = Gauge('flask_http_active_requests', '当前活跃请求数', registry=registry)

# 系统级指标
SYSTEM_CPU_USAGE = Gauge('system_cpu_usage_percent', 'CPU使用率', registry=registry)
SYSTEM_MEMORY_USAGE = Gauge('system_memory_usage_bytes', '内存使用量', registry=registry)
SYSTEM_MEMORY_TOTAL = Gauge('system_memory_total_bytes', '总内存', registry=registry)
SYSTEM_DISK_USAGE = Gauge('system_disk_usage_bytes', '磁盘使用量', registry=registry)
SYSTEM_DISK_TOTAL = Gauge('system_disk_total_bytes', '总磁盘空间', registry=registry)

# Python进程指标
PYTHON_INFO = Gauge('python_info', 'Python版本信息', ['version'], registry=registry)
PYTHON_THREADS = Gauge('python_threads_active', 'Python活跃线程数', registry=registry)

# Flask应用指标
FLASK_INFO = Gauge('flask_info', 'Flask应用信息', ['version', 'app_name'], registry=registry)
FLASK_UPTIME = Gauge('flask_uptime_seconds', 'Flask应用运行时间', registry=registry)

# 业务指标
BIGSCREEN_USERS = Gauge('bigscreen_active_users', '大屏活跃用户数', registry=registry)
BIGSCREEN_DASHBOARD_VIEWS = Counter('bigscreen_dashboard_views_total', '大屏仪表板浏览次数', ['dashboard'], registry=registry)
BIGSCREEN_DATA_REFRESH = Counter('bigscreen_data_refresh_total', '数据刷新次数', ['data_type'], registry=registry)

# 关键接口监控指标
API_REQUEST_COUNT = Counter('bigscreen_api_requests_total', '关键API请求总数', ['endpoint', 'method', 'status'], registry=registry)
API_REQUEST_DURATION = Histogram('bigscreen_api_request_duration_seconds', '关键API请求处理时间', ['endpoint', 'method'], 
                                  buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0], registry=registry)
API_ACTIVE_REQUESTS = Gauge('bigscreen_api_active_requests', '当前活跃API请求数', ['endpoint'], registry=registry)

# 新增专业级监控指标
ERROR_COUNT = Counter('bigscreen_errors_total', '错误总数', ['error_type', 'endpoint'], registry=registry)
SLOW_REQUESTS = Counter('bigscreen_slow_requests_total', '慢请求统计', ['endpoint', 'threshold'], registry=registry)
CACHE_OPERATIONS = Counter('bigscreen_cache_operations_total', '缓存操作统计', ['operation', 'result'], registry=registry)
DATABASE_CONNECTIONS = Gauge('bigscreen_db_connections', '数据库连接数', ['state'], registry=registry)
EXTERNAL_API_CALLS = Counter('bigscreen_external_api_calls_total', '外部API调用', ['service', 'status'], registry=registry)
CONCURRENT_USERS = Gauge('bigscreen_concurrent_users', '并发用户数', registry=registry)
DATA_PROCESSING_TIME = Histogram('bigscreen_data_processing_seconds', '数据处理时间', ['data_type'], 
                                  buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0], registry=registry)

# 应用启动时间
app_start_time = time.time()

def init_static_metrics():
    """初始化静态指标"""
    import sys
    import flask
    
    # Python版本信息
    PYTHON_INFO.labels(version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}").set(1)
    
    # Flask应用信息
    FLASK_INFO.labels(version=flask.__version__, app_name='ljwx-bigscreen').set(1)

def update_system_metrics():
    """更新系统级指标"""
    try:
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        SYSTEM_CPU_USAGE.set(cpu_percent)
        
        # 内存使用情况
        memory = psutil.virtual_memory()
        SYSTEM_MEMORY_USAGE.set(memory.used)
        SYSTEM_MEMORY_TOTAL.set(memory.total)
        
        # 磁盘使用情况
        disk = psutil.disk_usage('/')
        SYSTEM_DISK_USAGE.set(disk.used)
        SYSTEM_DISK_TOTAL.set(disk.total)
        
        # Python线程数
        PYTHON_THREADS.set(threading.active_count())
        
        # 应用运行时间
        FLASK_UPTIME.set(time.time() - app_start_time)
        
    except Exception as e:
        print(f"更新系统指标时出错: {e}")
        ERROR_COUNT.labels(error_type='system_metrics', endpoint='metrics_update').inc()

def start_metrics_collector():
    """启动后台指标收集器"""
    def collect_metrics():
        while True:
            update_system_metrics()
            time.sleep(30)  # 每30秒更新一次系统指标
    
    thread = threading.Thread(target=collect_metrics, daemon=True)
    thread.start()

@metrics_bp.before_app_request
def before_request():
    """请求开始前记录指标"""
    g.start_time = time.time()
    ACTIVE_REQUESTS.inc()
    
    # 监控关键API
    endpoint = request.endpoint or 'unknown'
    if is_monitored_endpoint(endpoint):
        API_ACTIVE_REQUESTS.labels(endpoint=endpoint).inc()

@metrics_bp.after_app_request
def after_request(response):
    """请求结束后记录指标"""
    try:
        ACTIVE_REQUESTS.dec()
        
        # 记录请求指标
        method = request.method
        endpoint = request.endpoint or 'unknown'
        status = str(response.status_code)
        
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
        
        # 记录响应时间
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
            
            # 慢请求统计
            if duration > 1.0:
                SLOW_REQUESTS.labels(endpoint=endpoint, threshold='1s').inc()
            if duration > 5.0:
                SLOW_REQUESTS.labels(endpoint=endpoint, threshold='5s').inc()
            
        # 监控关键API
        if is_monitored_endpoint(endpoint):
            API_ACTIVE_REQUESTS.labels(endpoint=endpoint).dec()
            API_REQUEST_COUNT.labels(endpoint=endpoint, method=method, status=status).inc()
            if hasattr(g, 'start_time'):
                duration = time.time() - g.start_time
                API_REQUEST_DURATION.labels(endpoint=endpoint, method=method).observe(duration)
        
        # 错误统计
        if response.status_code >= 400:
            error_type = 'client_error' if response.status_code < 500 else 'server_error'
            ERROR_COUNT.labels(error_type=error_type, endpoint=endpoint).inc()
            
    except Exception as e:
        print(f"记录请求指标时出错: {e}")
        ERROR_COUNT.labels(error_type='metrics_error', endpoint='after_request').inc()
    
    return response

@metrics_bp.route('/metrics')
def metrics():
    """Prometheus指标端点"""
    try:
        # 更新实时指标
        update_system_metrics()
        
        # 生成Prometheus格式指标
        data = generate_latest(registry)
        return Response(data, mimetype=CONTENT_TYPE_LATEST)
    except Exception as e:
        print(f"生成指标时出错: {e}")
        ERROR_COUNT.labels(error_type='metrics_generation', endpoint='metrics').inc()
        return Response(f"# 指标生成失败: {e}\n", mimetype=CONTENT_TYPE_LATEST, status=500)

@metrics_bp.route('/health')
def health():
    """健康检查端点"""
    return {
        'status': 'healthy',
        'timestamp': time.time(),
        'uptime': time.time() - app_start_time,
        'version': '1.0.0'
    }

# 业务监控装饰器
def monitor_data_processing(data_type):
    """数据处理监控装饰器"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                ERROR_COUNT.labels(error_type='data_processing', endpoint=func.__name__).inc()
                raise
            finally:
                duration = time.time() - start_time
                DATA_PROCESSING_TIME.labels(data_type=data_type).observe(duration)
        return wrapper
    return decorator

def increment_dashboard_view(dashboard_name):
    """记录仪表板浏览"""
    BIGSCREEN_DASHBOARD_VIEWS.labels(dashboard=dashboard_name).inc()

def increment_data_refresh(data_type):
    """记录数据刷新"""
    BIGSCREEN_DATA_REFRESH.labels(data_type=data_type).inc()

def set_active_users(count):
    """设置活跃用户数"""
    BIGSCREEN_USERS.set(count)

def set_concurrent_users(count):
    """设置并发用户数"""
    CONCURRENT_USERS.set(count)

def record_cache_operation(operation, result='hit'):
    """记录缓存操作"""
    CACHE_OPERATIONS.labels(operation=operation, result=result).inc()

def record_external_api_call(service, status):
    """记录外部API调用"""
    EXTERNAL_API_CALLS.labels(service=service, status=status).inc()

def set_database_connections(active=0, idle=0):
    """设置数据库连接数"""
    DATABASE_CONNECTIONS.labels(state='active').set(active)
    DATABASE_CONNECTIONS.labels(state='idle').set(idle)

def is_monitored_endpoint(endpoint):
    """判断是否为需要监控的关键接口"""
    if not endpoint:
        return False
    
    monitored_endpoints = [
        'get_personal_info',
        'get_devices_by_orgIdAndUserId', 
        'get_alerts_by_orgIdAndUserId',
        'get_users_by_orgIdAndUserId',
        'get_health_data_by_orgIdAndUserId',
        'get_messages_by_orgIdAndUserId',
        'upload_health_data',
        'upload_device_info',
        'fetch_health_data_config'
    ]
    
    return any(monitored in endpoint for monitored in monitored_endpoints)

# 初始化静态指标
init_static_metrics() 
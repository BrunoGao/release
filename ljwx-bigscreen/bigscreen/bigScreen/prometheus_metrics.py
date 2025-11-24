#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Prometheus指标导出模块
为ljwx-bigscreen提供监控指标
"""

from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, REGISTRY
from prometheus_client.core import CollectorRegistry
from flask import Response
import logging

logger = logging.getLogger(__name__)

# 创建指标注册表
registry = CollectorRegistry()

# =============================================================================
# 应用信息指标
# =============================================================================
app_info = Info(
    'bigscreen_app',
    'ljwx-bigscreen应用信息',
    registry=registry
)

# =============================================================================
# 健康数据上传指标
# =============================================================================

# 健康数据上传总数
health_data_upload_total = Counter(
    'bigscreen_health_data_upload_total',
    '健康数据上传总数',
    ['device_sn', 'upload_method'],
    registry=registry
)

# 健康数据上传失败总数
health_data_upload_failed_total = Counter(
    'bigscreen_health_data_upload_failed_total',
    '健康数据上传失败总数',
    ['device_sn', 'reason'],
    registry=registry
)

# 健康数据处理时间
health_data_processing_duration = Histogram(
    'bigscreen_health_data_processing_duration_seconds',
    '健康数据处理时间（秒）',
    ['device_sn'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
    registry=registry
)

# =============================================================================
# API请求指标
# =============================================================================

# API请求总数
api_requests_total = Counter(
    'bigscreen_api_requests_total',
    'API请求总数',
    ['method', 'endpoint', 'status'],
    registry=registry
)

# API请求持续时间
api_request_duration_seconds = Histogram(
    'bigscreen_api_request_duration_seconds',
    'API请求持续时间（秒）',
    ['method', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0),
    registry=registry
)

# 当前正在处理的API请求数
api_requests_in_progress = Gauge(
    'bigscreen_api_requests_in_progress',
    '当前正在处理的API请求数',
    ['method', 'endpoint'],
    registry=registry
)

# =============================================================================
# 告警指标
# =============================================================================

# 告警生成总数
alerts_generated_total = Counter(
    'bigscreen_alerts_generated_total',
    '告警生成总数',
    ['alert_type', 'severity', 'device_sn'],
    registry=registry
)

# 告警发送总数
alerts_sent_total = Counter(
    'bigscreen_alerts_sent_total',
    '告警发送总数',
    ['channel', 'status'],
    registry=registry
)

# 当前活跃告警数
active_alerts = Gauge(
    'bigscreen_active_alerts',
    '当前活跃告警数',
    ['severity'],
    registry=registry
)

# =============================================================================
# 消息指标
# =============================================================================

# 消息发送总数
messages_sent_total = Counter(
    'bigscreen_messages_sent_total',
    '消息发送总数',
    ['message_type', 'channel'],
    registry=registry
)

# 消息发送失败总数
messages_failed_total = Counter(
    'bigscreen_messages_failed_total',
    '消息发送失败总数',
    ['message_type', 'reason'],
    registry=registry
)

# 未读消息数
unread_messages = Gauge(
    'bigscreen_unread_messages',
    '未读消息数',
    ['org_id'],
    registry=registry
)

# =============================================================================
# 数据库指标
# =============================================================================

# 数据库连接池使用率
db_connection_pool_usage = Gauge(
    'bigscreen_db_connection_pool_usage',
    '数据库连接池使用率',
    registry=registry
)

# 数据库查询总数
db_queries_total = Counter(
    'bigscreen_db_queries_total',
    '数据库查询总数',
    ['query_type'],
    registry=registry
)

# 数据库查询持续时间
db_query_duration_seconds = Histogram(
    'bigscreen_db_query_duration_seconds',
    '数据库查询持续时间（秒）',
    ['query_type'],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
    registry=registry
)

# =============================================================================
# Redis指标
# =============================================================================

# Redis连接错误总数
redis_connection_errors_total = Counter(
    'bigscreen_redis_connection_errors_total',
    'Redis连接错误总数',
    registry=registry
)

# Redis操作总数
redis_operations_total = Counter(
    'bigscreen_redis_operations_total',
    'Redis操作总数',
    ['operation', 'status'],
    registry=registry
)

# Redis缓存命中率
redis_cache_hits_total = Counter(
    'bigscreen_redis_cache_hits_total',
    'Redis缓存命中总数',
    registry=registry
)

redis_cache_misses_total = Counter(
    'bigscreen_redis_cache_misses_total',
    'Redis缓存未命中总数',
    registry=registry
)

# =============================================================================
# 设备指标
# =============================================================================

# 活跃设备数
active_devices = Gauge(
    'bigscreen_active_devices',
    '活跃设备数',
    ['org_id'],
    registry=registry
)

# 在线设备数
online_devices = Gauge(
    'bigscreen_online_devices',
    '在线设备数',
    registry=registry
)

# =============================================================================
# 系统指标
# =============================================================================

# 系统启动时间
app_start_time = Gauge(
    'bigscreen_app_start_time_seconds',
    '应用启动时间戳',
    registry=registry
)

# Python GC统计
python_gc_collections_total = Counter(
    'bigscreen_python_gc_collections_total',
    'Python GC回收次数',
    ['generation'],
    registry=registry
)


# =============================================================================
# 指标导出函数
# =============================================================================

def get_metrics():
    """获取Prometheus格式的指标"""
    try:
        return generate_latest(registry)
    except Exception as e:
        logger.error(f"获取Prometheus指标失败: {e}")
        return b""


def metrics_endpoint():
    """Prometheus指标端点"""
    try:
        metrics_data = get_metrics()
        return Response(metrics_data, mimetype='text/plain; charset=utf-8')
    except Exception as e:
        logger.error(f"Prometheus指标端点错误: {e}")
        return Response("Error generating metrics", status=500)


def init_app_info(version='1.0.0', environment='production'):
    """初始化应用信息"""
    try:
        app_info.info({
            'version': version,
            'environment': environment,
            'application': 'ljwx-bigscreen'
        })

        import time
        app_start_time.set(time.time())

        logger.info("Prometheus指标初始化完成")
    except Exception as e:
        logger.error(f"初始化Prometheus指标失败: {e}")


# =============================================================================
# 辅助函数
# =============================================================================

def record_health_data_upload(device_sn, upload_method='wifi', success=True, duration=0):
    """记录健康数据上传"""
    try:
        if success:
            health_data_upload_total.labels(
                device_sn=device_sn,
                upload_method=upload_method
            ).inc()
        else:
            health_data_upload_failed_total.labels(
                device_sn=device_sn,
                reason='processing_error'
            ).inc()

        if duration > 0:
            health_data_processing_duration.labels(device_sn=device_sn).observe(duration)
    except Exception as e:
        logger.error(f"记录健康数据上传指标失败: {e}")


def record_api_request(method, endpoint, status_code, duration):
    """记录API请求"""
    try:
        api_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=status_code
        ).inc()

        api_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    except Exception as e:
        logger.error(f"记录API请求指标失败: {e}")


def record_alert_generated(alert_type, severity, device_sn=''):
    """记录告警生成"""
    try:
        alerts_generated_total.labels(
            alert_type=alert_type,
            severity=severity,
            device_sn=device_sn
        ).inc()
    except Exception as e:
        logger.error(f"记录告警指标失败: {e}")


def record_message_sent(message_type, channel, success=True):
    """记录消息发送"""
    try:
        if success:
            messages_sent_total.labels(
                message_type=message_type,
                channel=channel
            ).inc()
        else:
            messages_failed_total.labels(
                message_type=message_type,
                reason='send_error'
            ).inc()
    except Exception as e:
        logger.error(f"记录消息指标失败: {e}")

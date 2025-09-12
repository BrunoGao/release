#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
消息系统V2监控指标和告警系统

主要功能:
1. Prometheus指标收集
2. 自定义业务指标
3. 实时告警规则
4. 性能监控面板
5. 健康检查端点
6. 告警通知集成

监控指标:
- API响应时间和错误率
- 数据库查询性能
- 缓存命中率
- 消息处理吞吐量
- 资源使用情况

@Author: brunoGao
@CreateTime: 2025-09-11
@Version: 2.0-Fixed
"""

import time
import logging
import json
import threading
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
from functools import wraps
import queue
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import redis
from redis import Redis
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine
import psutil

# Prometheus metrics (如果可用)
try:
    from prometheus_client import Counter, Histogram, Gauge, Summary, CollectorRegistry, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logging.warning("⚠️ Prometheus client未安装，将使用简化监控")

# 导入服务层（用于健康检查）
from services.message_service_v2_fixed import MessageServiceV2Fixed

logger = logging.getLogger(__name__)


# ==================== 监控指标定义 ====================

class MetricType:
    """指标类型"""
    COUNTER = "counter"      # 计数器
    GAUGE = "gauge"         # 仪表盘
    HISTOGRAM = "histogram"  # 直方图
    SUMMARY = "summary"     # 摘要


@dataclass
class MetricDefinition:
    """指标定义"""
    name: str
    metric_type: str
    description: str
    labels: List[str] = field(default_factory=list)
    buckets: Optional[List[float]] = None  # 用于histogram


@dataclass
class AlertRule:
    """告警规则"""
    name: str
    condition: str           # 告警条件表达式
    threshold: float         # 阈值
    duration: int           # 持续时间（秒）
    severity: str           # 严重程度: critical, warning, info
    description: str        # 告警描述
    notification_channels: List[str] = field(default_factory=list)  # 通知渠道
    enabled: bool = True
    
    # 内部状态
    triggered_at: Optional[datetime] = None
    last_check: Optional[datetime] = None


@dataclass
class AlertNotification:
    """告警通知"""
    alert_id: str
    rule_name: str
    severity: str
    message: str
    current_value: float
    threshold: float
    triggered_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


# ==================== 核心监控类 ====================

class MessageSystemMetrics:
    """消息系统指标收集器"""
    
    def __init__(self, registry: Optional['CollectorRegistry'] = None):
        self.registry = registry or (CollectorRegistry() if PROMETHEUS_AVAILABLE else None)
        self.metrics = {}
        self.custom_metrics = defaultdict(lambda: defaultdict(int))
        
        # 初始化指标定义
        self.metric_definitions = self._define_metrics()
        
        # 创建Prometheus指标（如果可用）
        if PROMETHEUS_AVAILABLE and self.registry:
            self._create_prometheus_metrics()
        
        # 内存中的时序数据（用于简单监控）
        self.time_series_data = defaultdict(lambda: deque(maxlen=1440))  # 24小时数据
        
        logger.info("✅ 消息系统指标收集器初始化完成")
    
    def _define_metrics(self) -> List[MetricDefinition]:
        """定义监控指标"""
        return [
            # API指标
            MetricDefinition(
                name="message_api_requests_total",
                metric_type=MetricType.COUNTER,
                description="API请求总数",
                labels=["method", "endpoint", "status_code"]
            ),
            MetricDefinition(
                name="message_api_request_duration_seconds",
                metric_type=MetricType.HISTOGRAM,
                description="API请求耗时",
                labels=["method", "endpoint"],
                buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
            ),
            
            # 消息处理指标
            MetricDefinition(
                name="message_created_total",
                metric_type=MetricType.COUNTER,
                description="创建消息总数",
                labels=["customer_id", "message_type", "priority"]
            ),
            MetricDefinition(
                name="message_acknowledged_total",
                metric_type=MetricType.COUNTER,
                description="确认消息总数",
                labels=["customer_id", "device_type"]
            ),
            MetricDefinition(
                name="message_processing_duration_seconds",
                metric_type=MetricType.HISTOGRAM,
                description="消息处理耗时",
                labels=["operation"],
                buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
            ),
            
            # 数据库指标
            MetricDefinition(
                name="database_query_duration_seconds",
                metric_type=MetricType.HISTOGRAM,
                description="数据库查询耗时",
                labels=["query_type", "table"],
                buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
            ),
            MetricDefinition(
                name="database_connections_active",
                metric_type=MetricType.GAUGE,
                description="活跃数据库连接数"
            ),
            
            # 缓存指标
            MetricDefinition(
                name="cache_operations_total",
                metric_type=MetricType.COUNTER,
                description="缓存操作总数",
                labels=["operation", "result"]
            ),
            MetricDefinition(
                name="cache_hit_rate",
                metric_type=MetricType.GAUGE,
                description="缓存命中率"
            ),
            
            # 系统资源指标
            MetricDefinition(
                name="system_cpu_usage_percent",
                metric_type=MetricType.GAUGE,
                description="CPU使用率"
            ),
            MetricDefinition(
                name="system_memory_usage_bytes",
                metric_type=MetricType.GAUGE,
                description="内存使用量"
            ),
            
            # 业务指标
            MetricDefinition(
                name="message_queue_size",
                metric_type=MetricType.GAUGE,
                description="消息队列大小",
                labels=["queue_name"]
            ),
            MetricDefinition(
                name="user_active_sessions",
                metric_type=MetricType.GAUGE,
                description="活跃用户会话数",
                labels=["customer_id"]
            )
        ]
    
    def _create_prometheus_metrics(self):
        """创建Prometheus指标对象"""
        for metric_def in self.metric_definitions:
            if metric_def.metric_type == MetricType.COUNTER:
                self.metrics[metric_def.name] = Counter(
                    metric_def.name,
                    metric_def.description,
                    metric_def.labels,
                    registry=self.registry
                )
            elif metric_def.metric_type == MetricType.GAUGE:
                self.metrics[metric_def.name] = Gauge(
                    metric_def.name,
                    metric_def.description,
                    metric_def.labels,
                    registry=self.registry
                )
            elif metric_def.metric_type == MetricType.HISTOGRAM:
                self.metrics[metric_def.name] = Histogram(
                    metric_def.name,
                    metric_def.description,
                    metric_def.labels,
                    buckets=metric_def.buckets,
                    registry=self.registry
                )
            elif metric_def.metric_type == MetricType.SUMMARY:
                self.metrics[metric_def.name] = Summary(
                    metric_def.name,
                    metric_def.description,
                    metric_def.labels,
                    registry=self.registry
                )
    
    # 指标记录方法
    def increment_counter(self, metric_name: str, labels: Dict[str, str] = None, value: float = 1):
        """增加计数器"""
        labels = labels or {}
        
        if PROMETHEUS_AVAILABLE and metric_name in self.metrics:
            if labels:
                self.metrics[metric_name].labels(**labels).inc(value)
            else:
                self.metrics[metric_name].inc(value)
        
        # 内存指标
        key = f"{metric_name}:{':'.join(f'{k}={v}' for k, v in sorted(labels.items()))}"
        self.custom_metrics[metric_name][key] += value
        
        # 时序数据
        self.time_series_data[key].append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'value': value
        })
    
    def set_gauge(self, metric_name: str, value: float, labels: Dict[str, str] = None):
        """设置仪表盘值"""
        labels = labels or {}
        
        if PROMETHEUS_AVAILABLE and metric_name in self.metrics:
            if labels:
                self.metrics[metric_name].labels(**labels).set(value)
            else:
                self.metrics[metric_name].set(value)
        
        # 内存指标
        key = f"{metric_name}:{':'.join(f'{k}={v}' for k, v in sorted(labels.items()))}"
        self.custom_metrics[metric_name][key] = value
        
        # 时序数据
        self.time_series_data[key].append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'value': value
        })
    
    def observe_histogram(self, metric_name: str, value: float, labels: Dict[str, str] = None):
        """记录直方图观测值"""
        labels = labels or {}
        
        if PROMETHEUS_AVAILABLE and metric_name in self.metrics:
            if labels:
                self.metrics[metric_name].labels(**labels).observe(value)
            else:
                self.metrics[metric_name].observe(value)
        
        # 时序数据
        key = f"{metric_name}:{':'.join(f'{k}={v}' for k, v in sorted(labels.items()))}"
        self.time_series_data[key].append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'value': value
        })
    
    def get_metrics_snapshot(self) -> Dict[str, Any]:
        """获取指标快照"""
        if PROMETHEUS_AVAILABLE and self.registry:
            # 返回Prometheus格式
            return generate_latest(self.registry).decode('utf-8')
        else:
            # 返回自定义格式
            return {
                'metrics': dict(self.custom_metrics),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def get_time_series_data(self, metric_name: str, duration_minutes: int = 60) -> List[Dict[str, Any]]:
        """获取时序数据"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=duration_minutes)
        
        result = []
        for key, data_points in self.time_series_data.items():
            if key.startswith(metric_name):
                filtered_points = [
                    point for point in data_points
                    if datetime.fromisoformat(point['timestamp']) > cutoff_time
                ]
                if filtered_points:
                    result.append({
                        'metric': key,
                        'data_points': filtered_points
                    })
        
        return result


# ==================== 指标装饰器 ====================

def monitor_api_request(metrics_collector: MessageSystemMetrics):
    """API请求监控装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            method = "unknown"
            endpoint = func.__name__
            status_code = "200"
            
            try:
                # 尝试从Flask request获取信息
                from flask import request
                method = request.method
                endpoint = request.endpoint or func.__name__
            except:
                pass
            
            try:
                result = func(*args, **kwargs)
                
                # 检查返回结果获取状态码
                if isinstance(result, tuple) and len(result) >= 2:
                    status_code = str(result[1])
                
                return result
                
            except Exception as e:
                status_code = "500"
                raise
            finally:
                duration = time.time() - start_time
                
                # 记录指标
                metrics_collector.increment_counter(
                    "message_api_requests_total",
                    {"method": method, "endpoint": endpoint, "status_code": status_code}
                )
                
                metrics_collector.observe_histogram(
                    "message_api_request_duration_seconds",
                    duration,
                    {"method": method, "endpoint": endpoint}
                )
        
        return wrapper
    return decorator


def monitor_database_query(metrics_collector: MessageSystemMetrics, query_type: str = "select", table: str = "unknown"):
    """数据库查询监控装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                
                metrics_collector.observe_histogram(
                    "database_query_duration_seconds",
                    duration,
                    {"query_type": query_type, "table": table}
                )
        
        return wrapper
    return decorator


def monitor_cache_operation(metrics_collector: MessageSystemMetrics, operation: str):
    """缓存操作监控装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                
                # 判断操作结果
                cache_result = "hit" if result is not None else "miss"
                if operation in ["set", "delete"]:
                    cache_result = "success" if result else "failed"
                
                metrics_collector.increment_counter(
                    "cache_operations_total",
                    {"operation": operation, "result": cache_result}
                )
                
                return result
                
            except Exception as e:
                metrics_collector.increment_counter(
                    "cache_operations_total",
                    {"operation": operation, "result": "error"}
                )
                raise
        
        return wrapper
    return decorator


# ==================== 告警系统 ====================

class AlertManager:
    """告警管理器"""
    
    def __init__(self, metrics_collector: MessageSystemMetrics, notification_config: Dict[str, Any] = None):
        self.metrics = metrics_collector
        self.notification_config = notification_config or {}
        
        # 告警规则
        self.alert_rules = {}
        self.active_alerts = {}
        
        # 通知队列
        self.notification_queue = queue.Queue()
        
        # 初始化默认规则
        self._setup_default_alert_rules()
        
        # 启动告警检查线程
        self.check_thread = None
        self.notification_thread = None
        self.running = False
        
        logger.info("✅ 告警管理器初始化完成")
    
    def _setup_default_alert_rules(self):
        """设置默认告警规则"""
        default_rules = [
            AlertRule(
                name="high_api_error_rate",
                condition="api_error_rate > threshold",
                threshold=0.05,  # 5%
                duration=300,    # 5分钟
                severity="critical",
                description="API错误率过高",
                notification_channels=["email", "slack"]
            ),
            AlertRule(
                name="slow_api_response",
                condition="api_p95_latency > threshold",
                threshold=5.0,   # 5秒
                duration=180,    # 3分钟
                severity="warning",
                description="API响应时间过慢",
                notification_channels=["slack"]
            ),
            AlertRule(
                name="low_cache_hit_rate",
                condition="cache_hit_rate < threshold",
                threshold=0.7,   # 70%
                duration=600,    # 10分钟
                severity="warning",
                description="缓存命中率过低",
                notification_channels=["email"]
            ),
            AlertRule(
                name="database_slow_query",
                condition="db_p95_latency > threshold",
                threshold=1.0,   # 1秒
                duration=300,    # 5分钟
                severity="critical",
                description="数据库查询过慢",
                notification_channels=["email", "slack"]
            ),
            AlertRule(
                name="high_memory_usage",
                condition="memory_usage_percent > threshold",
                threshold=0.85,  # 85%
                duration=300,    # 5分钟
                severity="warning",
                description="内存使用率过高",
                notification_channels=["slack"]
            ),
            AlertRule(
                name="message_queue_backlog",
                condition="message_queue_size > threshold",
                threshold=1000,  # 1000条消息
                duration=180,    # 3分钟
                severity="critical",
                description="消息队列积压严重",
                notification_channels=["email", "slack"]
            )
        ]
        
        for rule in default_rules:
            self.add_alert_rule(rule)
    
    def add_alert_rule(self, rule: AlertRule):
        """添加告警规则"""
        self.alert_rules[rule.name] = rule
        logger.info(f"📏 添加告警规则: {rule.name}")
    
    def remove_alert_rule(self, rule_name: str):
        """移除告警规则"""
        if rule_name in self.alert_rules:
            del self.alert_rules[rule_name]
            logger.info(f"🗑️ 移除告警规则: {rule_name}")
    
    def start(self):
        """启动告警系统"""
        if not self.running:
            self.running = True
            
            # 启动告警检查线程
            self.check_thread = threading.Thread(target=self._alert_check_loop, daemon=True)
            self.check_thread.start()
            
            # 启动通知处理线程
            self.notification_thread = threading.Thread(target=self._notification_loop, daemon=True)
            self.notification_thread.start()
            
            logger.info("🚀 告警系统已启动")
    
    def stop(self):
        """停止告警系统"""
        self.running = False
        
        if self.check_thread:
            self.check_thread.join(timeout=5)
        if self.notification_thread:
            self.notification_thread.join(timeout=5)
        
        logger.info("⏹️ 告警系统已停止")
    
    def _alert_check_loop(self):
        """告警检查循环"""
        while self.running:
            try:
                current_time = datetime.now(timezone.utc)
                
                for rule_name, rule in self.alert_rules.items():
                    if not rule.enabled:
                        continue
                    
                    try:
                        # 检查告警条件
                        should_alert = self._evaluate_alert_condition(rule)
                        
                        if should_alert:
                            if rule_name not in self.active_alerts:
                                # 新告警
                                rule.triggered_at = current_time
                                self.active_alerts[rule_name] = rule
                                
                                # 发送通知
                                self._queue_alert_notification(rule)
                                
                                logger.warning(f"🚨 告警触发: {rule_name}")
                            else:
                                # 持续告警
                                active_rule = self.active_alerts[rule_name]
                                duration = (current_time - active_rule.triggered_at).total_seconds()
                                
                                # 每30分钟重复通知
                                if duration > 1800:  
                                    self._queue_alert_notification(rule, is_repeat=True)
                                    active_rule.triggered_at = current_time
                        else:
                            if rule_name in self.active_alerts:
                                # 告警恢复
                                del self.active_alerts[rule_name]
                                rule.triggered_at = None
                                
                                # 发送恢复通知
                                self._queue_recovery_notification(rule)
                                
                                logger.info(f"✅ 告警恢复: {rule_name}")
                        
                        rule.last_check = current_time
                        
                    except Exception as e:
                        logger.error(f"❌ 告警规则检查失败: {rule_name}, 错误: {e}")
                
                time.sleep(30)  # 30秒检查一次
                
            except Exception as e:
                logger.error(f"❌ 告警检查循环异常: {e}")
                time.sleep(60)
    
    def _evaluate_alert_condition(self, rule: AlertRule) -> bool:
        """评估告警条件"""
        try:
            # 获取相关指标数据
            metric_value = self._get_metric_value_for_rule(rule)
            
            if metric_value is None:
                return False
            
            # 评估条件
            if ">" in rule.condition:
                return metric_value > rule.threshold
            elif "<" in rule.condition:
                return metric_value < rule.threshold
            elif "==" in rule.condition:
                return metric_value == rule.threshold
            else:
                logger.warning(f"⚠️ 不支持的告警条件: {rule.condition}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 告警条件评估失败: {rule.name}, 错误: {e}")
            return False
    
    def _get_metric_value_for_rule(self, rule: AlertRule) -> Optional[float]:
        """获取规则对应的指标值"""
        try:
            if rule.name == "high_api_error_rate":
                return self._calculate_api_error_rate()
            elif rule.name == "slow_api_response":
                return self._calculate_api_p95_latency()
            elif rule.name == "low_cache_hit_rate":
                return self._get_cache_hit_rate()
            elif rule.name == "database_slow_query":
                return self._calculate_db_p95_latency()
            elif rule.name == "high_memory_usage":
                return self._get_memory_usage_percent()
            elif rule.name == "message_queue_backlog":
                return self._get_message_queue_size()
            else:
                logger.warning(f"⚠️ 未知的告警规则: {rule.name}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 获取指标值失败: {rule.name}, 错误: {e}")
            return None
    
    def _calculate_api_error_rate(self) -> float:
        """计算API错误率"""
        try:
            # 从时序数据计算最近5分钟的错误率
            time_series = self.metrics.get_time_series_data("message_api_requests_total", 5)
            
            total_requests = 0
            error_requests = 0
            
            for series in time_series:
                if "status_code=5" in series['metric'] or "status_code=4" in series['metric']:
                    error_requests += sum(point['value'] for point in series['data_points'])
                
                total_requests += sum(point['value'] for point in series['data_points'])
            
            return (error_requests / max(total_requests, 1)) if total_requests > 0 else 0.0
            
        except Exception as e:
            logger.error(f"❌ 计算API错误率失败: {e}")
            return 0.0
    
    def _calculate_api_p95_latency(self) -> float:
        """计算API P95延迟"""
        try:
            # 简化实现：返回最近5分钟的平均延迟
            time_series = self.metrics.get_time_series_data("message_api_request_duration_seconds", 5)
            
            if not time_series:
                return 0.0
            
            all_values = []
            for series in time_series:
                all_values.extend([point['value'] for point in series['data_points']])
            
            if not all_values:
                return 0.0
            
            # 简化P95计算
            all_values.sort()
            p95_index = int(len(all_values) * 0.95)
            return all_values[p95_index] if p95_index < len(all_values) else all_values[-1]
            
        except Exception as e:
            logger.error(f"❌ 计算API P95延迟失败: {e}")
            return 0.0
    
    def _get_cache_hit_rate(self) -> float:
        """获取缓存命中率"""
        try:
            # 从Redis获取统计信息
            import redis
            
            # 这里应该使用实际的Redis连接
            # 简化实现：返回模拟值
            return 0.75  # 75%
            
        except Exception as e:
            logger.error(f"❌ 获取缓存命中率失败: {e}")
            return 0.0
    
    def _calculate_db_p95_latency(self) -> float:
        """计算数据库P95延迟"""
        try:
            time_series = self.metrics.get_time_series_data("database_query_duration_seconds", 5)
            
            if not time_series:
                return 0.0
            
            all_values = []
            for series in time_series:
                all_values.extend([point['value'] for point in series['data_points']])
            
            if not all_values:
                return 0.0
            
            all_values.sort()
            p95_index = int(len(all_values) * 0.95)
            return all_values[p95_index] if p95_index < len(all_values) else all_values[-1]
            
        except Exception as e:
            logger.error(f"❌ 计算数据库P95延迟失败: {e}")
            return 0.0
    
    def _get_memory_usage_percent(self) -> float:
        """获取内存使用率"""
        try:
            memory = psutil.virtual_memory()
            return memory.percent / 100.0
            
        except Exception as e:
            logger.error(f"❌ 获取内存使用率失败: {e}")
            return 0.0
    
    def _get_message_queue_size(self) -> float:
        """获取消息队列大小"""
        try:
            # 这里应该获取实际的消息队列大小
            # 简化实现：返回模拟值
            return 50.0
            
        except Exception as e:
            logger.error(f"❌ 获取消息队列大小失败: {e}")
            return 0.0
    
    def _queue_alert_notification(self, rule: AlertRule, is_repeat: bool = False):
        """队列告警通知"""
        try:
            current_value = self._get_metric_value_for_rule(rule) or 0.0
            
            notification = AlertNotification(
                alert_id=f"{rule.name}_{int(time.time())}",
                rule_name=rule.name,
                severity=rule.severity,
                message=f"{'[重复告警] ' if is_repeat else ''}{rule.description}",
                current_value=current_value,
                threshold=rule.threshold,
                triggered_at=rule.triggered_at or datetime.now(timezone.utc),
                metadata={
                    'condition': rule.condition,
                    'is_repeat': is_repeat
                }
            )
            
            self.notification_queue.put(('alert', notification))
            
        except Exception as e:
            logger.error(f"❌ 队列告警通知失败: {e}")
    
    def _queue_recovery_notification(self, rule: AlertRule):
        """队列恢复通知"""
        try:
            current_value = self._get_metric_value_for_rule(rule) or 0.0
            
            notification = AlertNotification(
                alert_id=f"{rule.name}_recovery_{int(time.time())}",
                rule_name=rule.name,
                severity="info",
                message=f"[告警恢复] {rule.description}",
                current_value=current_value,
                threshold=rule.threshold,
                triggered_at=datetime.now(timezone.utc),
                metadata={
                    'condition': rule.condition,
                    'is_recovery': True
                }
            )
            
            self.notification_queue.put(('recovery', notification))
            
        except Exception as e:
            logger.error(f"❌ 队列恢复通知失败: {e}")
    
    def _notification_loop(self):
        """通知处理循环"""
        while self.running:
            try:
                # 获取通知（超时1秒）
                notification_type, notification = self.notification_queue.get(timeout=1)
                
                # 发送通知
                self._send_notification(notification_type, notification)
                
                self.notification_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"❌ 通知处理失败: {e}")
    
    def _send_notification(self, notification_type: str, notification: AlertNotification):
        """发送通知"""
        try:
            rule = self.alert_rules.get(notification.rule_name)
            if not rule:
                return
            
            for channel in rule.notification_channels:
                if channel == "email":
                    self._send_email_notification(notification_type, notification)
                elif channel == "slack":
                    self._send_slack_notification(notification_type, notification)
                else:
                    logger.warning(f"⚠️ 不支持的通知渠道: {channel}")
                    
        except Exception as e:
            logger.error(f"❌ 发送通知失败: {e}")
    
    def _send_email_notification(self, notification_type: str, notification: AlertNotification):
        """发送邮件通知"""
        try:
            email_config = self.notification_config.get('email', {})
            if not email_config.get('enabled', False):
                return
            
            # 构建邮件内容
            subject = f"[{notification.severity.upper()}] {notification.message}"
            
            body = f"""
            告警详情:
            - 规则名称: {notification.rule_name}
            - 告警级别: {notification.severity}
            - 当前值: {notification.current_value}
            - 阈值: {notification.threshold}
            - 触发时间: {notification.triggered_at.strftime('%Y-%m-%d %H:%M:%S')}
            
            请及时处理！
            """
            
            # 发送邮件（需要配置SMTP）
            # 这里是示例代码，需要根据实际配置调整
            logger.info(f"📧 发送邮件通知: {subject}")
            
        except Exception as e:
            logger.error(f"❌ 发送邮件通知失败: {e}")
    
    def _send_slack_notification(self, notification_type: str, notification: AlertNotification):
        """发送Slack通知"""
        try:
            slack_config = self.notification_config.get('slack', {})
            if not slack_config.get('enabled', False):
                return
            
            # 构建Slack消息
            color = {
                'critical': 'danger',
                'warning': 'warning',
                'info': 'good'
            }.get(notification.severity, 'warning')
            
            message = {
                'text': f"[{notification.severity.upper()}] {notification.message}",
                'attachments': [{
                    'color': color,
                    'fields': [
                        {'title': '当前值', 'value': str(notification.current_value), 'short': True},
                        {'title': '阈值', 'value': str(notification.threshold), 'short': True},
                        {'title': '时间', 'value': notification.triggered_at.strftime('%Y-%m-%d %H:%M:%S'), 'short': True}
                    ]
                }]
            }
            
            # 发送到Slack（需要配置Webhook）
            logger.info(f"💬 发送Slack通知: {notification.message}")
            
        except Exception as e:
            logger.error(f"❌ 发送Slack通知失败: {e}")
    
    def get_active_alerts(self) -> Dict[str, AlertRule]:
        """获取活跃告警"""
        return self.active_alerts.copy()
    
    def get_alert_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """获取告警历史"""
        # 这里可以实现从数据库或日志文件读取告警历史
        # 简化实现
        return []


# ==================== 系统资源监控 ====================

class SystemResourceMonitor:
    """系统资源监控器"""
    
    def __init__(self, metrics_collector: MessageSystemMetrics):
        self.metrics = metrics_collector
        self.running = False
        self.monitor_thread = None
    
    def start(self):
        """启动资源监控"""
        if not self.running:
            self.running = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            logger.info("🖥️ 系统资源监控已启动")
    
    def stop(self):
        """停止资源监控"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("⏹️ 系统资源监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                # CPU使用率
                cpu_percent = psutil.cpu_percent(interval=1)
                self.metrics.set_gauge("system_cpu_usage_percent", cpu_percent)
                
                # 内存使用情况
                memory = psutil.virtual_memory()
                self.metrics.set_gauge("system_memory_usage_bytes", memory.used)
                
                # 磁盘使用情况
                disk = psutil.disk_usage('/')
                self.metrics.set_gauge("system_disk_usage_bytes", disk.used)
                
                # 网络统计
                network = psutil.net_io_counters()
                self.metrics.set_gauge("system_network_bytes_sent", network.bytes_sent)
                self.metrics.set_gauge("system_network_bytes_recv", network.bytes_recv)
                
                time.sleep(30)  # 30秒收集一次
                
            except Exception as e:
                logger.error(f"❌ 系统资源监控失败: {e}")
                time.sleep(60)


# ==================== 健康检查端点 ====================

class HealthCheckEndpoint:
    """健康检查端点"""
    
    def __init__(
        self, 
        message_service: Optional[MessageServiceV2Fixed] = None,
        redis_client: Optional[Redis] = None,
        db_engine: Optional[Engine] = None
    ):
        self.message_service = message_service
        self.redis_client = redis_client
        self.db_engine = db_engine
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        status = {
            'service': 'MessageSystemV2Fixed',
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'version': '2.0-Fixed',
            'components': {}
        }
        
        # 检查消息服务
        if self.message_service:
            try:
                service_health = self.message_service.get_service_health()
                status['components']['message_service'] = service_health
                
                if service_health['status'] != 'healthy':
                    status['status'] = 'degraded'
                    
            except Exception as e:
                status['components']['message_service'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
                status['status'] = 'unhealthy'
        
        # 检查Redis
        if self.redis_client:
            try:
                self.redis_client.ping()
                status['components']['redis'] = {
                    'status': 'healthy',
                    'info': self.redis_client.info('server')
                }
            except Exception as e:
                status['components']['redis'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
                status['status'] = 'unhealthy'
        
        # 检查数据库
        if self.db_engine:
            try:
                with self.db_engine.connect() as conn:
                    conn.execute(text('SELECT 1'))
                
                status['components']['database'] = {
                    'status': 'healthy',
                    'pool_size': self.db_engine.pool.size(),
                    'checked_out': self.db_engine.pool.checkedout()
                }
            except Exception as e:
                status['components']['database'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
                status['status'] = 'unhealthy'
        
        # 添加系统资源信息
        try:
            status['system'] = {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent
            }
        except:
            pass
        
        return status
    
    def get_readiness_status(self) -> Dict[str, Any]:
        """获取就绪状态（用于Kubernetes readiness probe）"""
        # 就绪检查更严格，所有组件都必须健康
        health = self.get_health_status()
        
        is_ready = health['status'] == 'healthy'
        
        return {
            'ready': is_ready,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'details': health
        }
    
    def get_liveness_status(self) -> Dict[str, Any]:
        """获取存活状态（用于Kubernetes liveness probe）"""
        # 存活检查较宽松，只要主服务能响应即可
        return {
            'alive': True,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'uptime': self._get_uptime()
        }
    
    def _get_uptime(self) -> str:
        """获取运行时间"""
        try:
            uptime_seconds = time.time() - psutil.boot_time()
            uptime_str = str(timedelta(seconds=int(uptime_seconds)))
            return uptime_str
        except:
            return "unknown"


# ==================== 主监控管理器 ====================

class MessageSystemMonitor:
    """消息系统主监控管理器"""
    
    def __init__(
        self,
        message_service: Optional[MessageServiceV2Fixed] = None,
        redis_client: Optional[Redis] = None,
        db_engine: Optional[Engine] = None,
        notification_config: Dict[str, Any] = None
    ):
        # 创建组件
        self.metrics_collector = MessageSystemMetrics()
        self.alert_manager = AlertManager(self.metrics_collector, notification_config)
        self.resource_monitor = SystemResourceMonitor(self.metrics_collector)
        self.health_check = HealthCheckEndpoint(message_service, redis_client, db_engine)
        
        self.running = False
        
        logger.info("✅ 消息系统监控管理器初始化完成")
    
    def start(self):
        """启动所有监控组件"""
        if not self.running:
            self.running = True
            
            # 启动组件
            self.alert_manager.start()
            self.resource_monitor.start()
            
            logger.info("🚀 消息系统监控已全面启动")
    
    def stop(self):
        """停止所有监控组件"""
        if self.running:
            self.running = False
            
            # 停止组件
            self.alert_manager.stop()
            self.resource_monitor.stop()
            
            logger.info("⏹️ 消息系统监控已停止")
    
    def get_monitor_dashboard(self) -> Dict[str, Any]:
        """获取监控面板数据"""
        return {
            'health': self.health_check.get_health_status(),
            'metrics': self.metrics_collector.get_metrics_snapshot(),
            'active_alerts': self.alert_manager.get_active_alerts(),
            'alert_rules': {name: rule.__dict__ for name, rule in self.alert_manager.alert_rules.items()},
            'timestamp': datetime.now(timezone.utc).isoformat()
        }


# ==================== 使用示例 ====================

if __name__ == "__main__":
    # 示例配置
    notification_config = {
        'email': {
            'enabled': False,
            'smtp_server': 'smtp.example.com',
            'smtp_port': 587,
            'username': 'alerts@example.com',
            'password': 'password',
            'recipients': ['admin@example.com']
        },
        'slack': {
            'enabled': False,
            'webhook_url': 'https://hooks.slack.com/services/...',
            'channel': '#alerts'
        }
    }
    
    # 创建监控系统
    monitor = MessageSystemMonitor(notification_config=notification_config)
    
    try:
        # 启动监控
        monitor.start()
        
        # 模拟运行
        print("✅ 监控系统运行中...")
        print("监控特性:")
        print("1. 📊 Prometheus指标收集")
        print("2. 🚨 实时告警监控")
        print("3. 🖥️ 系统资源监控")
        print("4. 💚 健康检查端点")
        print("5. 📧 多渠道告警通知")
        
        # 获取监控面板
        dashboard = monitor.get_monitor_dashboard()
        print(f"\n监控面板数据: {json.dumps(dashboard, indent=2, default=str, ensure_ascii=False)}")
        
        time.sleep(10)
        
    finally:
        # 停止监控
        monitor.stop()
        print("⏹️ 监控系统已停止")
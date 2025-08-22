#!/usr/bin/env python3
"""
健康数据批处理器管理器 v2.0
集成三个批处理器和统一响应格式，专注批处理性能优化
"""

from flask import request, current_app
from .unified_response_handler import UnifiedResponseHandler, monitor_api_performance
from .health_data_batch_processor import get_health_optimizer
from .device_batch_processor import get_device_processor
from .common_event_batch_processor import get_common_event_processor
import json
import logging

logger = logging.getLogger(__name__)

# 全局处理器实例
_health_processor = None
_device_processor = None  
_event_processor = None

def init_all_batch_processors(app):
    """初始化所有批处理器"""
    global _health_processor, _device_processor, _event_processor
    
    try:
        # 初始化健康数据优化器
        _health_processor = get_health_optimizer()
        
        # 初始化设备信息处理器  
        from .device_batch_processor import DeviceBatchProcessor
        _device_processor = DeviceBatchProcessor(app=app)
        _device_processor.start()
        
        # 初始化通用事件处理器
        _event_processor = get_common_event_processor(app=app)
        
        logger.info("✅ 所有批处理器初始化完成")
        
    except Exception as e:
        logger.error(f"❌ 批处理器初始化失败: {e}")
        raise

def get_all_batch_processors():
    """获取所有批处理器实例"""
    return _health_processor, _device_processor, _event_processor

@monitor_api_performance("HealthDataBatchUpload")
def batch_handle_health_data():
    """健康数据批处理上传器"""
    try:
        health_data = request.get_json()
        logger.info(f"🏥 健康数据上传请求，大小: {len(str(health_data)) if health_data else 0} 字符")
        
        if not health_data:
            return UnifiedResponseHandler.create_error_response(
                "请求体不能为空", 
                error_code=400
            )
        
        # 获取健康数据优化器
        health_processor = _health_processor
        if not health_processor:
            return UnifiedResponseHandler.create_error_response(
                "健康数据处理器未初始化",
                error_code=503
            )
        
        # 使用统一响应处理器
        return UnifiedResponseHandler.handle_health_data_upload(
            health_data, 
            health_processor
        )
        
    except Exception as e:
        logger.error(f"❌ 健康数据处理异常: {e}")
        return UnifiedResponseHandler.create_error_response(
            f"健康数据处理失败: {str(e)}",
            error_code=500
        )

@monitor_api_performance("DeviceInfoBatchUpload")  
def batch_handle_device_info():
    """设备信息批处理上传器"""
    try:
        device_info = request.get_json()
        logger.info(f"📱 设备信息上传请求，大小: {len(str(device_info)) if device_info else 0} 字符")
        
        if not device_info:
            return UnifiedResponseHandler.create_error_response(
                "请求体不能为空",
                error_code=400
            )
        
        # 获取设备信息处理器
        device_processor = _device_processor
        if not device_processor:
            return UnifiedResponseHandler.create_error_response(
                "设备信息处理器未初始化",
                error_code=503
            )
        
        # 使用统一响应处理器
        return UnifiedResponseHandler.handle_device_info_upload(
            device_info,
            device_processor
        )
        
    except Exception as e:
        logger.error(f"❌ 设备信息处理异常: {e}")
        return UnifiedResponseHandler.create_error_response(
            f"设备信息处理失败: {str(e)}",
            error_code=500
        )

@monitor_api_performance("CommonEventBatchUpload")
def batch_handle_common_event():
    """通用事件批处理上传器"""
    try:
        event_data = request.get_json()
        logger.info(f"⚡ 通用事件上传请求: {event_data.get('eventType', 'Unknown')} "
                   f"from {event_data.get('deviceSn', 'Unknown')}")
        
        if not event_data:
            return UnifiedResponseHandler.create_error_response(
                "请求体不能为空",
                error_code=400
            )
        
        # 获取通用事件处理器
        event_processor = _event_processor
        if not event_processor:
            return UnifiedResponseHandler.create_error_response(
                "通用事件处理器未初始化", 
                error_code=503
            )
        
        # 使用统一响应处理器
        return UnifiedResponseHandler.handle_common_event_upload(
            event_data,
            event_processor
        )
        
    except Exception as e:
        logger.error(f"❌ 通用事件处理异常: {e}")
        return UnifiedResponseHandler.create_error_response(
            f"通用事件处理失败: {str(e)}",
            error_code=500
        )

def get_batch_processors_stats():
    """获取所有批处理器的统计信息"""
    try:
        stats = {
            "timestamp": "2025-08-22T12:00:00Z",
            "processors": {}
        }
        
        # 健康数据处理器统计
        if _health_processor:
            health_stats = _health_processor.get_stats()
            stats["processors"]["health_data"] = {
                "name": "HealthDataOptimizer",
                "version": "4.0",
                "cpu_cores": health_stats.get('cpu_cores', 'N/A'),
                "batch_size": health_stats.get('batch_size', 'N/A'),
                "max_workers": health_stats.get('max_workers', 'N/A'),
                "processed": health_stats.get('processed', 0),
                "batches": health_stats.get('batches', 0),
                "queue_size": health_stats.get('queue_size', 0),
                "auto_adjustments": health_stats.get('auto_adjustments', 0)
            }
        
        # 设备信息处理器统计
        if _device_processor:
            device_stats = _device_processor.get_stats()
            stats["processors"]["device_info"] = {
                "name": "DeviceBatchProcessor", 
                "version": "2.1",
                "cpu_cores": getattr(_device_processor, 'cpu_cores', 'N/A'),
                "batch_size": getattr(_device_processor, 'batch_size', 'N/A'),
                "max_workers": getattr(_device_processor, 'max_workers', 'N/A'),
                "processed": device_stats.get('processed', 0),
                "failed": device_stats.get('failed', 0),
                "queued": device_stats.get('queued', 0)
            }
        
        # 通用事件处理器统计
        if _event_processor:
            event_stats = _event_processor.get_stats()
            stats["processors"]["common_event"] = event_stats
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ 获取处理器统计失败: {e}")
        return {"error": str(e)}

def get_performance_report():
    """获取性能报告"""
    try:
        report = {
            "title": "ljwx-bigscreen 批处理性能报告",
            "generated_at": "2025-08-22T12:00:00Z",
            "summary": {}
        }
        
        # 健康数据性能
        if _health_processor:
            health_stats = _health_processor.get_stats()
            report["summary"]["health_data"] = {
                "处理总量": health_stats.get('processed', 0),
                "批次数": health_stats.get('batches', 0),
                "当前批次大小": health_stats.get('batch_size', 'N/A'),
                "自动调整次数": health_stats.get('auto_adjustments', 0),
                "队列长度": health_stats.get('queue_size', 0)
            }
        
        # 设备信息性能  
        if _device_processor:
            device_stats = _device_processor.get_stats()
            report["summary"]["device_info"] = {
                "处理总量": device_stats.get('processed', 0),
                "失败数量": device_stats.get('failed', 0),
                "队列数量": device_stats.get('queued', 0),
                "批次大小": getattr(_device_processor, 'batch_size', 'N/A'),
                "工作线程": getattr(_device_processor, 'max_workers', 'N/A')
            }
        
        # 通用事件性能
        if _event_processor:
            event_stats = _event_processor.get_stats()
            report["summary"]["common_event"] = {
                "处理总量": event_stats.get('processed_total', 0),
                "批次数": event_stats.get('batch_count', 0),
                "失败数量": event_stats.get('failed_count', 0),
                "平均处理时间": f"{event_stats.get('avg_processing_time', 0):.2f}秒",
                "队列长度": event_stats.get('queue_size', 0)
            }
        
        return report
        
    except Exception as e:
        logger.error(f"❌ 生成性能报告失败: {e}")
        return {"error": str(e)}

# 兼容性包装函数
def legacy_upload_health_data(health_data):
    """兼容老版本的健康数据上传接口"""
    logger.warning("⚠️ 使用了legacy健康数据上传接口，建议升级到批处理版本")
    
    # 模拟Flask request
    class MockRequest:
        @staticmethod
        def get_json():
            return health_data
    
    # 临时替换request对象
    original_request = request
    try:
        import sys
        current_module = sys.modules[__name__]
        current_module.request = MockRequest()
        return batch_handle_health_data()
    finally:
        current_module.request = original_request

def legacy_upload_device_info(device_info):
    """兼容老版本的设备信息上传接口"""
    logger.warning("⚠️ 使用了legacy设备信息上传接口，建议升级到批处理版本")
    
    # 类似的兼容处理...
    class MockRequest:
        @staticmethod
        def get_json():
            return device_info
            
    original_request = request
    try:
        import sys
        current_module = sys.modules[__name__]
        current_module.request = MockRequest()
        return batch_handle_device_info()
    finally:
        current_module.request = original_request
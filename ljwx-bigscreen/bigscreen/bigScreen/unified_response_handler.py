#!/usr/bin/env python3
"""
统一响应处理器
为三个上传接口提供标准化的快速响应机制
"""

from flask import jsonify
from datetime import datetime
import time
import logging

logger = logging.getLogger(__name__)

class UnifiedResponseHandler:
    """统一响应处理器 - 确保所有上传接口快速响应"""
    
    # 标准成功响应模板
    STANDARD_SUCCESS_RESPONSE = {
        "status": "success",
        "message": "数据已接收，正在队列处理中",
        "queue_status": "processing"
    }
    
    # 标准错误响应模板
    STANDARD_ERROR_RESPONSE = {
        "status": "error", 
        "message": "队列繁忙，请稍后重试",
        "queue_status": "overloaded"
    }
    
    @staticmethod
    def create_success_response(data_type: str = "", count: int = 1, **kwargs):
        """创建标准成功响应"""
        response = UnifiedResponseHandler.STANDARD_SUCCESS_RESPONSE.copy()
        
        # 添加具体信息
        response.update({
            "timestamp": datetime.now().isoformat(),
            "data_type": data_type,
            "received_count": count,
            **kwargs
        })
        
        return jsonify(response), 200
    
    @staticmethod  
    def create_error_response(error_msg: str = "", error_code: int = 503, **kwargs):
        """创建标准错误响应"""
        response = UnifiedResponseHandler.STANDARD_ERROR_RESPONSE.copy()
        
        if error_msg:
            response["message"] = error_msg
            
        response.update({
            "timestamp": datetime.now().isoformat(),
            "error_code": error_code,
            **kwargs
        })
        
        return jsonify(response), error_code
    
    @staticmethod
    def handle_health_data_upload(health_data, health_processor):
        """处理健康数据上传 - 统一响应格式"""
        try:
            # 快速提交到队列
            success = health_processor.submit(health_data)
            
            if success:
                # 提取数据信息用于响应
                data_count = 1
                device_sn = ""
                
                try:
                    data_field = health_data.get('data', {})
                    if isinstance(data_field, list):
                        data_count = len(data_field)
                        if data_count > 0:
                            device_sn = data_field[0].get('deviceSn', '')
                    elif isinstance(data_field, dict):
                        device_sn = data_field.get('deviceSn', '')
                except:
                    pass
                
                return UnifiedResponseHandler.create_success_response(
                    data_type="health_data",
                    count=data_count,
                    device_sn=device_sn
                )
            else:
                return UnifiedResponseHandler.create_error_response(
                    "健康数据队列已满，请稍后重试"
                )
                
        except Exception as e:
            logger.error(f"❌ 健康数据处理异常: {e}")
            return UnifiedResponseHandler.create_error_response(
                f"健康数据处理失败: {str(e)}",
                error_code=500
            )
    
    @staticmethod
    def handle_device_info_upload(device_info, device_processor):
        """处理设备信息上传 - 统一响应格式"""
        try:
            # 快速提交到队列
            success = device_processor.submit(device_info)
            
            if success:
                # 提取设备信息
                data_count = 1
                device_sn = ""
                
                try:
                    if isinstance(device_info, list):
                        data_count = len(device_info)
                        if data_count > 0:
                            device_sn = device_info[0].get('deviceSn', '')
                    elif isinstance(device_info, dict):
                        device_sn = device_info.get('deviceSn', '')
                except:
                    pass
                
                return UnifiedResponseHandler.create_success_response(
                    data_type="device_info",
                    count=data_count,
                    device_sn=device_sn
                )
            else:
                return UnifiedResponseHandler.create_error_response(
                    "设备信息队列已满，请稍后重试"
                )
                
        except Exception as e:
            logger.error(f"❌ 设备信息处理异常: {e}")
            return UnifiedResponseHandler.create_error_response(
                f"设备信息处理失败: {str(e)}",
                error_code=500
            )
    
    @staticmethod
    def handle_common_event_upload(event_data, event_processor):
        """处理通用事件上传 - 统一响应格式"""
        try:
            # 快速提交到队列
            success = event_processor.submit(event_data)
            
            if success:
                # 提取事件信息
                device_sn = event_data.get('deviceSn', '')
                event_type = event_data.get('eventType', '').split('.')[-1]
                
                return UnifiedResponseHandler.create_success_response(
                    data_type="common_event",
                    count=1,
                    device_sn=device_sn,
                    event_type=event_type
                )
            else:
                return UnifiedResponseHandler.create_error_response(
                    "通用事件队列已满，请稍后重试"
                )
                
        except Exception as e:
            logger.error(f"❌ 通用事件处理异常: {e}")
            return UnifiedResponseHandler.create_error_response(
                f"通用事件处理失败: {str(e)}",
                error_code=500
            )

def create_fast_response_handler():
    """创建快速响应处理器实例"""
    return UnifiedResponseHandler()

# 导出便捷函数
def success_response(data_type="", count=1, **kwargs):
    """快速创建成功响应"""
    return UnifiedResponseHandler.create_success_response(data_type, count, **kwargs)

def error_response(error_msg="", error_code=503, **kwargs):
    """快速创建错误响应"""  
    return UnifiedResponseHandler.create_error_response(error_msg, error_code, **kwargs)

# API性能监控装饰器
def monitor_api_performance(api_name: str):
    """API性能监控装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                processing_time = time.time() - start_time
                
                # 记录成功请求
                logger.info(f"✅ {api_name} 处理成功，耗时: {processing_time:.3f}秒")
                return result
                
            except Exception as e:
                processing_time = time.time() - start_time
                logger.error(f"❌ {api_name} 处理失败，耗时: {processing_time:.3f}秒，错误: {e}")
                raise
                
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator
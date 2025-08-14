#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""专业日志系统配置"""
import os,sys,time,logging,json,functools
from datetime import datetime
from logging.handlers import RotatingFileHandler,TimedRotatingFileHandler
from pathlib import Path
from typing import Dict,Any
from flask import request,g

class JsonFormatter(logging.Formatter):#JSON格式化器
    """结构化JSON日志格式化器"""
    def format(self,record:logging.LogRecord)->str:
        log_obj={
            'timestamp':datetime.fromtimestamp(record.created).isoformat(),#时间戳
            'level':record.levelname,#日志级别
            'logger':record.name,#记录器名称
            'module':getattr(record,'module','unknown'),#模块名
            'function':record.funcName,#函数名
            'line':record.lineno,#行号
            'message':record.getMessage(),#消息
            'thread_id':record.thread,#线程ID
            'process_id':record.process,#进程ID
        }
        
        #添加自定义字段
        if hasattr(record,'user_id'):log_obj['user_id']=record.user_id
        if hasattr(record,'device_sn'):log_obj['device_sn']=record.device_sn
        if hasattr(record,'customer_id'):log_obj['customer_id']=record.customer_id
        if hasattr(record,'request_id'):log_obj['request_id']=record.request_id
        if hasattr(record,'api_endpoint'):log_obj['api_endpoint']=record.api_endpoint
        if hasattr(record,'processing_time'):log_obj['processing_time']=record.processing_time
        if hasattr(record,'data_count'):log_obj['data_count']=record.data_count
        if hasattr(record,'data_size'):log_obj['data_size']=record.data_size
        if hasattr(record,'message_type'):log_obj['message_type']=record.message_type
        if hasattr(record,'message_id'):log_obj['message_id']=record.message_id
        if hasattr(record,'operation'):log_obj['operation']=record.operation
        if hasattr(record,'status'):log_obj['status']=record.status
        if hasattr(record,'response_code'):log_obj['response_code']=record.response_code
        
        #异常信息
        if record.exc_info:
            log_obj['exception']={
                'type':record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message':str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback':self.formatException(record.exc_info)
            }
            
        return json.dumps(log_obj,ensure_ascii=False,separators=(',',':'))

class ColoredFormatter(logging.Formatter):#彩色控制台格式化器
    """彩色控制台日志格式化器"""
    COLORS={'DEBUG':'\033[36m','INFO':'\033[32m','WARNING':'\033[33m','ERROR':'\033[31m','CRITICAL':'\033[35m'}#颜色映射
    RESET='\033[0m'#重置颜色
    
    def format(self,record:logging.LogRecord)->str:
        color=self.COLORS.get(record.levelname,self.RESET)
        record.levelname=f"{color}{record.levelname}{self.RESET}"
        return super().format(record)

class LoggerManager:#日志管理器
    """专业日志管理器"""
    def __init__(self,log_dir:str='logs',max_file_size:int=50*1024*1024,backup_count:int=5):
        self.log_dir=Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)#创建日志目录
        self.max_file_size=max_file_size#最大文件大小50MB
        self.backup_count=backup_count#备份文件数
        self.loggers:Dict[str,logging.Logger]={}#记录器缓存
        self._setup_root_logger()#设置根记录器
        
    def _setup_root_logger(self):#设置根记录器
        """配置根记录器"""
        root=logging.getLogger()
        root.setLevel(logging.DEBUG)
        root.handlers.clear()#清除默认处理器
        
    def get_logger(self,name:str,module:str='general')->logging.Logger:#获取记录器
        """获取专业日志记录器"""
        if name in self.loggers:return self.loggers[name]
        
        logger=logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.propagate=False#不向上传播
        
        #控制台处理器(彩色输出)
        console_handler=logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter=ColoredFormatter('%(asctime)s [%(levelname)s] %(name)s.%(funcName)s:%(lineno)d - %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        #JSON文件处理器(结构化日志)
        json_file=self.log_dir/f"{module}_json.log"
        json_handler=RotatingFileHandler(json_file,maxBytes=self.max_file_size,backupCount=self.backup_count,encoding='utf-8')
        json_handler.setLevel(logging.DEBUG)
        json_formatter=JsonFormatter()
        json_handler.setFormatter(json_formatter)
        logger.addHandler(json_handler)
        
        #文本文件处理器(可读格式)
        text_file=self.log_dir/f"{module}_text.log"
        text_handler=RotatingFileHandler(text_file,maxBytes=self.max_file_size,backupCount=self.backup_count,encoding='utf-8')
        text_handler.setLevel(logging.INFO)
        text_formatter=logging.Formatter('%(asctime)s [%(levelname)s] %(name)s.%(funcName)s:%(lineno)d - %(message)s')
        text_handler.setFormatter(text_formatter)
        logger.addHandler(text_handler)
        
        #错误文件处理器(只记录错误)
        error_file=self.log_dir/"error.log"
        error_handler=RotatingFileHandler(error_file,maxBytes=self.max_file_size,backupCount=self.backup_count,encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_formatter=logging.Formatter('%(asctime)s [%(levelname)s] %(name)s.%(funcName)s:%(lineno)d - %(message)s\n%(pathname)s\nTraceback:\n%(exc_text)s')
        error_handler.setFormatter(error_formatter)
        logger.addHandler(error_handler)
        
        #为logger添加模块标识
        def log_with_module(level,msg,*args,**kwargs):
            extra=kwargs.setdefault('extra',{})
            extra['module']=module
            return getattr(logger,level)(msg,*args,**kwargs)
            
        #添加便捷方法
        logger.log_debug=lambda msg,**kw:log_with_module('debug',msg,**kw)
        logger.log_info=lambda msg,**kw:log_with_module('info',msg,**kw)
        logger.log_warning=lambda msg,**kw:log_with_module('warning',msg,**kw)
        logger.log_error=lambda msg,**kw:log_with_module('error',msg,**kw)
        logger.log_critical=lambda msg,**kw:log_with_module('critical',msg,**kw)
        
        self.loggers[name]=logger
        return logger
        
    def get_api_logger(self)->logging.Logger:#获取API记录器
        """获取API专用记录器"""
        return self.get_logger('ljwx.api','api')
        
    def get_health_logger(self)->logging.Logger:#获取健康数据记录器
        """获取健康数据处理记录器"""
        return self.get_logger('ljwx.health','health_data')
        
    def get_device_logger(self)->logging.Logger:#获取设备记录器
        """获取设备信息记录器"""
        return self.get_logger('ljwx.device','device_info')
        
    def get_message_logger(self)->logging.Logger:#获取消息记录器
        """获取设备消息记录器"""
        return self.get_logger('ljwx.message','device_message')
        
    def get_db_logger(self)->logging.Logger:#获取数据库记录器
        """获取数据库操作记录器"""
        return self.get_logger('ljwx.database','database')
        
    def get_redis_logger(self)->logging.Logger:#获取Redis记录器
        """获取Redis操作记录器"""
        return self.get_logger('ljwx.redis','redis')
        
    def get_alert_logger(self)->logging.Logger:#获取告警记录器
        """获取告警处理记录器"""
        return self.get_logger('ljwx.alert','alert')
        
    def get_baseline_logger(self)->logging.Logger:#获取基线记录器
        """获取基线生成记录器"""
        return self.get_logger('ljwx.baseline','baseline')
        
    def get_system_logger(self)->logging.Logger:#获取系统记录器
        """获取系统监控记录器"""
        return self.get_logger('ljwx.system','system')

#全局日志管理器实例
log_manager=LoggerManager()

def log_api_request(endpoint:str,method:str='GET'):#API请求日志装饰器
    """API请求日志记录装饰器"""
    def decorator(func):
        @functools.wraps(func)#保持原函数元数据
        def wrapper(*args,**kwargs):
            start_time=time.time()
            request_id=f"{int(start_time*1000000)}"#请求ID
            logger=log_manager.get_api_logger()
            
            #从请求中提取设备信息
            device_sn=None
            user_id=None
            data_size=0
            
            try:
                if hasattr(request,'get_json') and request.get_json():
                    data=request.get_json()
                    device_sn=extract_device_sn(data)
                    user_id=extract_user_id(data)
                    data_size=len(str(data))
                elif hasattr(request,'args'):
                    device_sn=request.args.get('deviceSn') or request.args.get('serial_number')
                    user_id=request.args.get('userId') or request.args.get('user_id')
            except:pass
            
            try:
                logger.info('API请求开始',extra={'api_endpoint':endpoint,'request_id':request_id,'user_id':user_id,'device_sn':device_sn,'data_size':data_size})
                result=func(*args,**kwargs)
                end_time=time.time()
                proc_time=round(end_time-start_time,4)
                
                #提取响应状态
                status='success'
                if hasattr(result,'get_json'):
                    response_data=result.get_json()
                    if isinstance(response_data,dict) and not response_data.get('success',True):
                        status='failed'
                        
                logger.info('API请求完成',extra={'api_endpoint':endpoint,'request_id':request_id,'processing_time':proc_time,'status':status})
                return result
            except Exception as e:
                end_time=time.time()
                proc_time=round(end_time-start_time,4)
                logger.error('API请求失败',extra={'api_endpoint':endpoint,'request_id':request_id,'processing_time':proc_time,'status':'error'},exc_info=True)
                raise
        return wrapper
    return decorator

def log_health_data_processing():#健康数据处理装饰器
    """健康数据处理专用日志装饰器"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args,**kwargs):
            start_time=time.time()
            logger=log_manager.get_health_logger()
            
            #提取健康数据信息
            device_sn=None
            data_count=0
            data_size=0
            
            try:
                if hasattr(request,'get_json') and request.get_json():
                    data=request.get_json()
                    device_sn=extract_device_sn(data)
                    data_count=extract_data_count(data)
                    data_size=len(str(data))
            except:pass
            
            try:
                logger.info('健康数据上传开始',extra={'device_sn':device_sn,'data_count':data_count,'data_size':data_size,'operation':'UPLOAD_START'})
                result=func(*args,**kwargs)
                end_time=time.time()
                proc_time=round(end_time-start_time,4)
                logger.info('健康数据上传完成',extra={'device_sn':device_sn,'data_count':data_count,'processing_time':proc_time,'operation':'UPLOAD_COMPLETE'})
                return result
            except Exception as e:
                end_time=time.time()
                proc_time=round(end_time-start_time,4)
                logger.error('健康数据上传失败',extra={'device_sn':device_sn,'data_count':data_count,'processing_time':proc_time,'operation':'UPLOAD_FAILED'},exc_info=True)
                raise
        return wrapper
    return decorator

def log_device_info_processing():#设备信息处理装饰器
    """设备信息处理专用日志装饰器"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args,**kwargs):
            start_time=time.time()
            logger=log_manager.get_device_logger()
            
            #提取设备信息
            device_sn=None
            data_size=0
            
            try:
                if hasattr(request,'get_json') and request.get_json():
                    data=request.get_json()
                    device_sn=extract_device_sn(data,'DeviceInfo')
                    data_size=len(str(data))
            except:pass
            
            try:
                logger.info('设备信息上传开始',extra={'device_sn':device_sn,'data_size':data_size,'operation':'DEVICE_UPLOAD_START'})
                result=func(*args,**kwargs)
                end_time=time.time()
                proc_time=round(end_time-start_time,4)
                logger.info('设备信息上传完成',extra={'device_sn':device_sn,'processing_time':proc_time,'operation':'DEVICE_UPLOAD_COMPLETE'})
                return result
            except Exception as e:
                end_time=time.time()
                proc_time=round(end_time-start_time,4)
                logger.error('设备信息上传失败',extra={'device_sn':device_sn,'processing_time':proc_time,'operation':'DEVICE_UPLOAD_FAILED'},exc_info=True)
                raise
        return wrapper
    return decorator

def log_message_processing():#设备消息处理装饰器
    """设备消息处理专用日志装饰器"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args,**kwargs):
            start_time=time.time()
            logger=log_manager.get_message_logger()
            
            #提取消息信息
            device_sn=None
            message_type=None
            message_id=None
            operation=None
            
            try:
                if hasattr(request,'get_json') and request.get_json():
                    data=request.get_json()
                    device_sn=data.get('device_sn') or data.get('deviceSn')
                    message_type=data.get('message_type') or data.get('messageType')
                    message_id=data.get('message_id') or data.get('messageId')
                    operation='MESSAGE_SEND'
                elif hasattr(request,'args'):
                    device_sn=request.args.get('deviceSn')
                    message_type=request.args.get('messageType')
                    operation='MESSAGE_RECEIVE'
            except:pass
            
            try:
                logger.info(f'设备消息{operation}开始',extra={'device_sn':device_sn,'message_type':message_type,'message_id':message_id,'operation':operation})
                result=func(*args,**kwargs)
                end_time=time.time()
                proc_time=round(end_time-start_time,4)
                logger.info(f'设备消息{operation}完成',extra={'device_sn':device_sn,'message_type':message_type,'processing_time':proc_time,'operation':f'{operation}_COMPLETE'})
                return result
            except Exception as e:
                end_time=time.time()
                proc_time=round(end_time-start_time,4)
                logger.error(f'设备消息{operation}失败',extra={'device_sn':device_sn,'message_type':message_type,'processing_time':proc_time,'operation':f'{operation}_FAILED'},exc_info=True)
                raise
        return wrapper
    return decorator

def extract_device_sn(data,data_type='HealthData'):#提取设备序列号
    """从数据中提取设备序列号"""
    if not data:return None
    
    if data_type=='DeviceInfo':
        #设备信息数据结构
        if isinstance(data,dict):
            device_data=data.get('data',data)
            return device_data.get('SerialNumber') or device_data.get('serial_number')
    else:
        #健康数据结构
        if isinstance(data,dict):
            data_field=data.get('data')
            if isinstance(data_field,list) and len(data_field)>0:
                return data_field[0].get('deviceSn') or data_field[0].get('id')
            elif isinstance(data_field,dict):
                return data_field.get('deviceSn') or data_field.get('id')
            else:
                return data.get('deviceSn') or data.get('device_sn')
    return None

def extract_data_count(data):#提取数据条数
    """从健康数据中提取数据条数"""
    if not data:return 0
    
    data_field=data.get('data')
    if isinstance(data_field,list):
        return len(data_field)
    elif isinstance(data_field,dict):
        return 1
    return 0

def extract_user_id(data):#提取用户ID
    """从数据中提取用户ID"""
    if not data:return None
    
    data_field=data.get('data')
    if isinstance(data_field,list) and len(data_field)>0:
        return data_field[0].get('user_id')
    elif isinstance(data_field,dict):
        return data_field.get('user_id')
    return data.get('user_id')

def log_data_processing(data_type:str,count:int=None,device_sn:str=None):#数据处理日志装饰器
    """数据处理日志记录装饰器"""
    def decorator(func):
        @functools.wraps(func)#保持原函数元数据
        def wrapper(*args,**kwargs):
            start_time=time.time()
            logger=log_manager.get_health_logger()
            
            try:
                logger.info(f'{data_type}数据处理开始',extra={'device_sn':device_sn,'data_count':count})
                result=func(*args,**kwargs)
                end_time=time.time()
                proc_time=round(end_time-start_time,4)
                logger.info(f'{data_type}数据处理完成',extra={'device_sn':device_sn,'data_count':count,'processing_time':proc_time})
                return result
            except Exception as e:
                end_time=time.time()
                proc_time=round(end_time-start_time,4)
                logger.error(f'{data_type}数据处理失败',extra={'device_sn':device_sn,'data_count':count,'processing_time':proc_time},exc_info=True)
                raise
        return wrapper
    return decorator

#便捷接口
def get_logger(name:str,module:str='general')->logging.Logger:return log_manager.get_logger(name,module)#获取记录器
api_logger=log_manager.get_api_logger()#API记录器
health_logger=log_manager.get_health_logger()#健康数据记录器
device_logger=log_manager.get_device_logger()#设备记录器
message_logger=log_manager.get_message_logger()#消息记录器
db_logger=log_manager.get_db_logger()#数据库记录器
redis_logger=log_manager.get_redis_logger()#Redis记录器
alert_logger=log_manager.get_alert_logger()#告警记录器
baseline_logger=log_manager.get_baseline_logger()#基线记录器
system_logger=log_manager.get_system_logger()#系统记录器 
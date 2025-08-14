#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""调试输出控制模块"""
import os,sys,builtins
from logging_config import system_logger

class DebugController:#调试控制器
    """批量控制调试输出的控制器"""
    def __init__(self):
        self.original_print=builtins.print#保存原始print函数
        self.debug_enabled=os.getenv('DEBUG_PRINT','false').lower()=='true'#环境变量控制
        self.log_prints=os.getenv('LOG_PRINTS','false').lower()=='true'#是否记录到日志
        
    def disable_all_prints(self):#禁用所有print
        """完全禁用所有print输出"""
        builtins.print=lambda *args,**kwargs:None
        system_logger.info('已禁用所有print调试输出')
        
    def enable_all_prints(self):#启用所有print
        """恢复所有print输出"""
        builtins.print=self.original_print
        system_logger.info('已启用所有print调试输出')
        
    def redirect_prints_to_log(self):#重定向print到日志
        """将print输出重定向到专业日志系统"""
        def log_print(*args,**kwargs):
            if self.debug_enabled:
                message=' '.join(str(arg) for arg in args)
                system_logger.debug(f'PRINT: {message}')
            if self.log_prints:
                self.original_print(*args,**kwargs)
                
        builtins.print=log_print
        system_logger.info('已重定向print到专业日志系统')
        
    def selective_disable_prints(self,keywords=None):#选择性禁用print
        """选择性禁用包含特定关键词的print"""
        if keywords is None:
            keywords=['debug','DEBUG','测试','test','临时','temp']
            
        def selective_print(*args,**kwargs):
            message=' '.join(str(arg) for arg in args)
            if any(keyword in message for keyword in keywords):
                if self.log_prints:
                    system_logger.debug(f'FILTERED_PRINT: {message}')
                return#过滤掉包含关键词的输出
            self.original_print(*args,**kwargs)
            
        builtins.print=selective_print
        system_logger.info(f'已启用选择性print过滤，关键词: {keywords}')

def disable_debug_prints():#快速禁用调试print
    """快速禁用调试相关的print输出"""
    controller=DebugController()
    
    # 根据环境变量决定策略
    strategy=os.getenv('PRINT_STRATEGY','selective')#selective/disable/redirect
    
    if strategy=='disable':
        controller.disable_all_prints()
    elif strategy=='redirect':
        controller.redirect_prints_to_log()
    else:
        controller.selective_disable_prints()
        
    return controller

#全局调试控制器
debug_controller = DebugController()
debug_controller.enable_all_prints()  # 直接启用所有print 
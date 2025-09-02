#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生产环境配置"""
import os

def setup_production_env():#设置生产环境
    """配置生产环境，禁用调试输出"""
    os.environ['DEBUG_PRINT']='false'
    os.environ['LOG_PRINTS']='false'  
    os.environ['PRINT_STRATEGY']='disable'
    os.environ['LOG_LEVEL']='INFO'
    os.environ['CONSOLE_LOG_LEVEL']='WARNING'
    os.environ['DISABLE_DEBUG_LOGGING']='true'
    
    print("🚀 生产环境配置已加载 - 调试输出已禁用")

def setup_debug_env():#设置调试环境
    """配置调试环境，启用详细输出"""
    os.environ['DEBUG_PRINT']='true'
    os.environ['LOG_PRINTS']='true'
    os.environ['PRINT_STRATEGY']='selective'
    os.environ['LOG_LEVEL']='DEBUG'
    os.environ['CONSOLE_LOG_LEVEL']='DEBUG'
    os.environ['DISABLE_DEBUG_LOGGING']='false'
    
    print("🔧 调试环境配置已加载 - 详细输出已启用")

def setup_test_env():#设置测试环境
    """配置测试环境，重定向输出到日志"""
    os.environ['DEBUG_PRINT']='false'
    os.environ['LOG_PRINTS']='true'
    os.environ['PRINT_STRATEGY']='redirect'
    os.environ['LOG_LEVEL']='INFO'
    os.environ['CONSOLE_LOG_LEVEL']='INFO'
    os.environ['DISABLE_DEBUG_LOGGING']='false'
    
    print("🧪 测试环境配置已加载 - 输出重定向到日志")

# 根据环境变量自动配置
env_mode=os.getenv('ENV_MODE','production')#默认生产环境

if env_mode=='production':
    setup_production_env()
elif env_mode=='debug':
    setup_debug_env()
elif env_mode=='test':
    setup_test_env()
else:
    setup_production_env()#默认生产环境 
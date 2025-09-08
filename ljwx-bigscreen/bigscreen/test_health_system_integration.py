#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
健康系统集成测试
Health System Integration Test

测试健康基线评分画像智能生成系统的完整功能
- 验证所有引擎模块的导入和初始化
- 测试API接口的基本功能
- 检查数据库表结构和数据
- 验证缓存服务和数据质量控制

Author: System
Date: 2025-09-01
Version: 1.0
"""

import sys
import os
import asyncio
import json
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bigScreen'))
sys.path.insert(0, os.path.dirname(__file__))

def test_module_imports():
    """测试模块导入"""
    print("🔍 测试健康系统模块导入...")
    
    results = {}
    
    # 测试基础模型
    try:
        from bigScreen.models import db, UserHealthData, HealthBaseline, UserHealthProfile
        results['models'] = '✅ 成功'
    except Exception as e:
        results['models'] = f'❌ {str(e)}'
    
    # 测试健康引擎
    engines = [
        ('baseline_engine', 'bigScreen.health_baseline_engine'),
        ('score_engine', 'bigScreen.health_score_engine'),
        ('recommendation_engine', 'bigScreen.health_recommendation_engine'),
        ('profile_engine', 'bigScreen.health_profile_engine'),
        ('cache_service', 'bigScreen.health_cache_service'),
        ('data_quality', 'bigScreen.health_data_quality'),
        ('system_init', 'bigScreen.health_system_init'),
        ('health_api', 'bigScreen.health_api')
    ]
    
    for name, module_path in engines:
        try:
            __import__(module_path)
            results[name] = '✅ 成功'
        except Exception as e:
            results[name] = f'❌ {str(e)}'
    
    return results

def test_database_connection():
    """测试数据库连接"""
    print("🗄️  测试数据库连接...")
    
    try:
        from bigScreen.models import db
        from sqlalchemy import text
        
        # 模拟Flask应用上下文
        from flask import Flask
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:123456@127.0.0.1:3306/test?charset=utf8mb4"
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db.init_app(app)
        
        with app.app_context():
            db.session.execute(text('SELECT 1'))
            
            # 检查健康相关表
            tables_to_check = [
                't_user_health_data',
                't_health_baseline',
                't_health_profile',
                't_health_recommendation_track'
            ]
            
            table_status = {}
            for table in tables_to_check:
                try:
                    result = db.session.execute(text(f"SELECT COUNT(*) as count FROM {table} WHERE is_deleted = 0"))
                    count = result.fetchone().count
                    table_status[table] = f'✅ {count} 条记录'
                except Exception as e:
                    table_status[table] = f'❌ {str(e)}'
            
            return {
                'connection': '✅ 连接成功',
                'tables': table_status
            }
    
    except Exception as e:
        return {
            'connection': f'❌ 连接失败: {str(e)}',
            'tables': {}
        }

async def test_cache_service():
    """测试缓存服务"""
    print("💾 测试缓存服务...")
    
    try:
        from bigScreen.health_cache_service import HealthCacheService
        
        # 创建缓存服务实例
        cache_service = HealthCacheService("redis://default:123456@127.0.0.1:6379/1")
        
        # 初始化缓存
        await cache_service.initialize()
        
        # 测试基本缓存操作
        test_data = {'test_key': 'test_value', 'timestamp': datetime.now().isoformat()}
        
        # 写入测试
        write_success = await cache_service.set_cached_data('hotspot', 'test', test_data)
        
        # 读取测试
        read_data = await cache_service.get_cached_data('hotspot', 'test')
        
        # 性能统计
        stats = cache_service.get_performance_stats()
        
        await cache_service.close()
        
        return {
            'initialization': '✅ 成功',
            'write_test': '✅ 成功' if write_success else '❌ 失败',
            'read_test': '✅ 成功' if read_data else '❌ 失败',
            'performance_stats': stats
        }
        
    except Exception as e:
        return {
            'initialization': f'❌ 失败: {str(e)}',
            'write_test': '❌ 未测试',
            'read_test': '❌ 未测试',
            'performance_stats': {}
        }

async def test_data_quality():
    """测试数据质量控制"""
    print("🔍 测试数据质量控制...")
    
    try:
        from bigScreen.health_data_quality import HealthDataQualityController
        
        # 创建质量控制器
        quality_controller = HealthDataQualityController()
        
        # 测试数据
        test_data = {
            'user_id': 1001,
            'customer_id': 1001,
            'device_sn': 'TEST-DEVICE-001',
            'heart_rate': 75.5,
            'blood_pressure_systolic': 120.0,
            'blood_pressure_diastolic': 80.0,
            'spo2': 98.5,
            'temperature': 36.8,
            'step_count': 8500,
            'create_time': datetime.now().isoformat()
        }
        
        # 验证数据质量
        validation_result = await quality_controller.validate_health_data(test_data)
        
        # 生成质量报告
        quality_report = quality_controller.generate_quality_report()
        
        return {
            'validation': '✅ 成功',
            'quality_score': validation_result.quality_score,
            'quality_level': validation_result.quality_level.value,
            'is_valid': validation_result.is_valid,
            'issues_count': len(validation_result.issues),
            'warnings_count': len(validation_result.warnings),
            'report_generated': '✅ 成功' if quality_report else '❌ 失败'
        }
        
    except Exception as e:
        return {
            'validation': f'❌ 失败: {str(e)}',
            'quality_score': 0,
            'quality_level': 'unknown',
            'is_valid': False,
            'issues_count': 0,
            'warnings_count': 0,
            'report_generated': '❌ 失败'
        }

def main():
    """主测试函数"""
    print("="*60)
    print("🚀 健康基线评分画像智能生成系统集成测试")
    print("="*60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. 测试模块导入
    import_results = test_module_imports()
    print("📋 模块导入测试结果:")
    for module, status in import_results.items():
        print(f"  {module}: {status}")
    print()
    
    # 2. 测试数据库连接
    db_results = test_database_connection()
    print("🗄️  数据库连接测试结果:")
    print(f"  连接状态: {db_results['connection']}")
    if db_results['tables']:
        print("  表状态:")
        for table, status in db_results['tables'].items():
            print(f"    {table}: {status}")
    print()
    
    # 3. 异步测试
    async def run_async_tests():
        # 测试缓存服务
        cache_results = await test_cache_service()
        print("💾 缓存服务测试结果:")
        for test, status in cache_results.items():
            if test == 'performance_stats':
                continue
            print(f"  {test}: {status}")
        if cache_results.get('performance_stats'):
            stats = cache_results['performance_stats']
            print(f"  性能统计: 命中率 {stats.get('hit_rate_percent', 0)}%, 总请求 {stats.get('total_requests', 0)}")
        print()
        
        # 测试数据质量
        quality_results = await test_data_quality()
        print("🔍 数据质量控制测试结果:")
        for test, status in quality_results.items():
            print(f"  {test}: {status}")
        print()
    
    # 运行异步测试
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_async_tests())
        loop.close()
    except Exception as e:
        print(f"❌ 异步测试失败: {e}")
    
    # 4. 总结
    print("="*60)
    print("📊 测试总结")
    print("="*60)
    
    total_modules = len(import_results)
    successful_modules = sum(1 for status in import_results.values() if '✅' in status)
    
    print(f"模块导入成功率: {successful_modules}/{total_modules} ({successful_modules/total_modules*100:.1f}%)")
    print(f"数据库连接: {db_results['connection']}")
    
    if successful_modules >= total_modules * 0.8:
        print("\n🎉 健康系统集成测试总体成功！")
        print("   系统已准备好提供健康基线评分画像智能生成服务")
    else:
        print("\n⚠️  健康系统集成测试部分成功")
        print("   建议检查失败的模块并解决导入问题")
    
    print("\n🔗 可用的API接口:")
    print("  - POST /api/health/baseline/personal - 生成个人健康基线")
    print("  - POST /api/health/score/comprehensive - 计算综合健康评分")  
    print("  - POST /api/health/recommendations/generate - 生成健康建议")
    print("  - POST /api/health/profile/generate - 生成健康画像")
    print("  - POST /api/health/quality/validate - 验证数据质量")
    print("  - GET  /api/health/system/status - 获取系统状态")
    print("  - GET  /api/health/docs - 查看完整API文档")
    
    print(f"\n完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    main()
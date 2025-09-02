#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
健康系统初始化脚本
Health System Initialization Script

负责健康管理系统的完整初始化，包括：
- 数据库连接验证
- 缓存服务初始化
- 健康引擎初始化
- 数据预热
- 系统状态检查

Author: System
Date: 2025-09-01
Version: 1.0
"""

import logging
import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .models import db
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from sqlalchemy import text

logger = logging.getLogger(__name__)

class HealthSystemInitializer:
    """健康系统初始化器"""
    
    def __init__(self):
        """初始化"""
        self.initialization_status = {
            'database': False,
            'cache_service': False,
            'engines': False,
            'data_warmup': False,
            'system_check': False
        }
        
        self.errors = []
        self.warnings = []

    async def initialize_complete_system(self) -> Dict[str, Any]:
        """完整系统初始化"""
        logger.info("🚀 开始健康系统完整初始化...")
        
        try:
            # 1. 验证数据库连接
            await self._verify_database_connection()
            
            # 2. 初始化缓存服务
            await self._initialize_cache_service()
            
            # 3. 初始化健康引擎
            await self._initialize_health_engines()
            
            # 4. 执行数据预热
            await self._perform_data_warmup()
            
            # 5. 系统状态检查
            await self._perform_system_check()
            
            logger.info("✅ 健康系统初始化完成")
            
            return {
                'success': True,
                'initialization_status': self.initialization_status,
                'errors': self.errors,
                'warnings': self.warnings,
                'initialization_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ 健康系统初始化失败: {e}")
            self.errors.append(f"系统初始化异常: {str(e)}")
            
            return {
                'success': False,
                'initialization_status': self.initialization_status,
                'errors': self.errors,
                'warnings': self.warnings,
                'initialization_time': datetime.now().isoformat()
            }

    async def _verify_database_connection(self):
        """验证数据库连接"""
        try:
            logger.info("🔍 验证数据库连接...")
            
            # 执行简单查询验证连接
            db.session.execute(text('SELECT 1'))
            
            # 检查健康相关表是否存在
            required_tables = [
                't_user_health_data',
                't_health_baseline', 
                't_user_health_profile',
                't_health_recommendation_track',
                'sys_user',
                'sys_position'
            ]
            
            for table in required_tables:
                result = db.session.execute(text(f"SHOW TABLES LIKE '{table}'"))
                if not result.fetchone():
                    self.warnings.append(f"表 {table} 不存在")
            
            self.initialization_status['database'] = True
            logger.info("✅ 数据库连接验证成功")
            
        except Exception as e:
            logger.error(f"❌ 数据库连接验证失败: {e}")
            self.errors.append(f"数据库连接失败: {str(e)}")
            raise

    async def _initialize_cache_service(self):
        """初始化缓存服务"""
        try:
            logger.info("💾 初始化缓存服务...")
            
            from .health_cache_service import health_cache_service
            
            # 初始化缓存连接
            await health_cache_service.initialize()
            
            # 测试缓存操作
            test_key = 'health:system:init_test'
            test_data = {'init_time': datetime.now().isoformat()}
            
            success = await health_cache_service.set_cached_data('hotspot', 'init_test', test_data)
            if not success:
                raise Exception("缓存写入测试失败")
            
            cached_data = await health_cache_service.get_cached_data('hotspot', 'init_test')
            if not cached_data:
                raise Exception("缓存读取测试失败")
            
            self.initialization_status['cache_service'] = True
            logger.info("✅ 缓存服务初始化成功")
            
        except Exception as e:
            logger.error(f"❌ 缓存服务初始化失败: {e}")
            self.errors.append(f"缓存服务初始化失败: {str(e)}")
            raise

    async def _initialize_health_engines(self):
        """初始化健康引擎"""
        try:
            logger.info("🏥 初始化健康引擎...")
            
            # 导入健康引擎
            engines = {}
            
            try:
                from .health_baseline_engine import HealthBaselineEngine
                engines['baseline'] = HealthBaselineEngine()
                logger.info("  ✅ 基线生成引擎初始化成功")
            except Exception as e:
                self.warnings.append(f"基线引擎初始化失败: {str(e)}")
            
            try:
                from .health_score_engine import HealthScoreEngine
                engines['score'] = HealthScoreEngine()
                logger.info("  ✅ 健康评分引擎初始化成功")
            except Exception as e:
                self.warnings.append(f"评分引擎初始化失败: {str(e)}")
            
            try:
                from .health_recommendation_engine import HealthRecommendationEngine
                engines['recommendation'] = HealthRecommendationEngine()
                logger.info("  ✅ 健康建议引擎初始化成功")
            except Exception as e:
                self.warnings.append(f"建议引擎初始化失败: {str(e)}")
            
            try:
                from .health_profile_engine import HealthProfileEngine
                engines['profile'] = HealthProfileEngine()
                logger.info("  ✅ 健康画像引擎初始化成功")
            except Exception as e:
                self.warnings.append(f"画像引擎初始化失败: {str(e)}")
            
            try:
                from .health_data_quality import health_data_quality
                logger.info("  ✅ 数据质量控制器初始化成功")
            except Exception as e:
                self.warnings.append(f"数据质量控制器初始化失败: {str(e)}")
            
            if len(engines) == 0:
                raise Exception("所有健康引擎初始化失败")
            
            self.initialization_status['engines'] = True
            logger.info(f"✅ 健康引擎初始化完成 ({len(engines)}/5 个引擎)")
            
        except Exception as e:
            logger.error(f"❌ 健康引擎初始化失败: {e}")
            self.errors.append(f"健康引擎初始化失败: {str(e)}")
            raise

    async def _perform_data_warmup(self):
        """执行数据预热"""
        try:
            logger.info("🔥 执行数据预热...")
            
            from .health_cache_service import health_cache_service
            
            # 获取活跃用户列表（最近3天有数据的用户）
            three_days_ago = datetime.now() - timedelta(days=3)
            
            active_users_query = db.session.execute(text("""
                SELECT DISTINCT user_id, customer_id 
                FROM t_user_health_data 
                WHERE create_time >= :start_time 
                    AND is_deleted = 0 
                    AND user_id IS NOT NULL 
                    AND customer_id IS NOT NULL
                ORDER BY create_time DESC 
                LIMIT 50
            """), {'start_time': three_days_ago})
            
            active_users = active_users_query.fetchall()
            
            if active_users:
                # 限制并发预热数量
                semaphore = asyncio.Semaphore(5)
                
                async def warmup_with_semaphore(user_info):
                    async with semaphore:
                        try:
                            return await health_cache_service.warmup_user_cache(
                                user_info.user_id, user_info.customer_id
                            )
                        except Exception as e:
                            logger.warning(f"用户 {user_info.user_id} 预热失败: {e}")
                            return False
                
                warmup_tasks = [warmup_with_semaphore(user) for user in active_users[:20]]  # 限制前20个活跃用户
                results = await asyncio.gather(*warmup_tasks, return_exceptions=True)
                
                success_count = sum(1 for result in results if result is True)
                logger.info(f"  ✅ 数据预热完成: {success_count}/{len(warmup_tasks)} 用户预热成功")
                
                if success_count == 0:
                    self.warnings.append("没有成功预热任何用户数据")
            else:
                logger.info("  ⚠️  没有找到活跃用户，跳过数据预热")
                self.warnings.append("没有找到活跃用户进行预热")
            
            self.initialization_status['data_warmup'] = True
            
        except Exception as e:
            logger.error(f"❌ 数据预热失败: {e}")
            self.warnings.append(f"数据预热失败: {str(e)}")
            # 预热失败不应中断初始化流程
            self.initialization_status['data_warmup'] = False

    async def _perform_system_check(self):
        """执行系统状态检查"""
        try:
            logger.info("🔍 执行系统状态检查...")
            
            # 检查数据库表状态
            table_stats = {}
            
            try:
                # 健康数据表统计
                health_data_count = db.session.execute(text(
                    "SELECT COUNT(*) as count FROM t_user_health_data WHERE is_deleted = 0"
                )).fetchone()
                table_stats['health_data_count'] = health_data_count.count if health_data_count else 0
                
                # 基线数据统计
                baseline_count = db.session.execute(text(
                    "SELECT COUNT(*) as count FROM t_health_baseline WHERE is_deleted = 0"
                )).fetchone()
                table_stats['baseline_count'] = baseline_count.count if baseline_count else 0
                
                # 用户健康画像统计
                profile_count = db.session.execute(text(
                    "SELECT COUNT(*) as count FROM t_user_health_profile WHERE is_deleted = 0"
                )).fetchone()
                table_stats['profile_count'] = profile_count.count if profile_count else 0
                
                logger.info(f"  📊 数据表统计: {table_stats}")
                
            except Exception as e:
                self.warnings.append(f"数据表统计失败: {str(e)}")
            
            # 检查缓存服务状态
            try:
                from .health_cache_service import health_cache_service
                cache_info = await health_cache_service.get_cache_info()
                logger.info(f"  💾 缓存状态: 已连接客户端 {cache_info.get('connected_clients', 0)} 个")
                
            except Exception as e:
                self.warnings.append(f"缓存状态检查失败: {str(e)}")
            
            # 检查最近24小时的数据活动
            try:
                yesterday = datetime.now() - timedelta(days=1)
                recent_activity = db.session.execute(text("""
                    SELECT 
                        COUNT(*) as total_records,
                        COUNT(DISTINCT user_id) as active_users,
                        COUNT(DISTINCT device_sn) as active_devices
                    FROM t_user_health_data 
                    WHERE create_time >= :start_time AND is_deleted = 0
                """), {'start_time': yesterday}).fetchone()
                
                activity_stats = {
                    'total_records': recent_activity.total_records if recent_activity else 0,
                    'active_users': recent_activity.active_users if recent_activity else 0,
                    'active_devices': recent_activity.active_devices if recent_activity else 0
                }
                
                logger.info(f"  📈 24小时活动统计: {activity_stats}")
                
                if activity_stats['total_records'] == 0:
                    self.warnings.append("最近24小时没有健康数据活动")
                
            except Exception as e:
                self.warnings.append(f"活动统计检查失败: {str(e)}")
            
            self.initialization_status['system_check'] = True
            logger.info("✅ 系统状态检查完成")
            
        except Exception as e:
            logger.error(f"❌ 系统状态检查失败: {e}")
            self.warnings.append(f"系统状态检查失败: {str(e)}")
            self.initialization_status['system_check'] = False

    def get_initialization_summary(self) -> Dict[str, Any]:
        """获取初始化摘要"""
        total_components = len(self.initialization_status)
        successful_components = sum(1 for status in self.initialization_status.values() if status)
        
        success_rate = (successful_components / total_components) * 100 if total_components > 0 else 0
        
        return {
            'overall_success': successful_components >= 3,  # 至少3个组件成功
            'success_rate': round(success_rate, 2),
            'successful_components': successful_components,
            'total_components': total_components,
            'component_status': self.initialization_status,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'errors': self.errors,
            'warnings': self.warnings
        }

    async def quick_health_check(self) -> Dict[str, Any]:
        """快速健康检查（用于API健康检查）"""
        try:
            checks = {}
            
            # 数据库检查
            try:
                db.session.execute(text('SELECT 1'))
                checks['database'] = 'healthy'
            except Exception as e:
                checks['database'] = f'unhealthy: {str(e)}'
            
            # 缓存检查
            try:
                from .health_cache_service import health_cache_service
                await health_cache_service.redis_client.ping()
                checks['cache'] = 'healthy'
            except Exception as e:
                checks['cache'] = f'unhealthy: {str(e)}'
            
            # 数据检查（最近1小时是否有数据）
            try:
                one_hour_ago = datetime.now() - timedelta(hours=1)
                recent_data = db.session.execute(text("""
                    SELECT COUNT(*) as count 
                    FROM t_user_health_data 
                    WHERE create_time >= :start_time AND is_deleted = 0
                """), {'start_time': one_hour_ago}).fetchone()
                
                data_count = recent_data.count if recent_data else 0
                checks['recent_data'] = f'healthy: {data_count} records in last hour' if data_count > 0 else 'low_activity: no recent data'
                
            except Exception as e:
                checks['recent_data'] = f'check_failed: {str(e)}'
            
            overall_health = 'healthy' if all('healthy' in status for status in checks.values()) else 'degraded'
            
            return {
                'overall_health': overall_health,
                'components': checks,
                'check_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"快速健康检查失败: {e}")
            return {
                'overall_health': 'unhealthy',
                'components': {'system': f'check_failed: {str(e)}'},
                'check_time': datetime.now().isoformat()
            }


# 全局初始化器实例
health_system_initializer = HealthSystemInitializer()


async def initialize_health_system() -> Dict[str, Any]:
    """初始化健康系统（外部调用接口）"""
    return await health_system_initializer.initialize_complete_system()


async def health_system_status_check() -> Dict[str, Any]:
    """健康系统状态检查（外部调用接口）"""
    return await health_system_initializer.quick_health_check()


def init_health_system_sync():
    """同步版本的健康系统初始化（用于Flask应用启动）"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(initialize_health_system())
            logger.info(f"健康系统初始化结果: {result}")
            return result
        finally:
            loop.close()
    except Exception as e:
        logger.error(f"同步健康系统初始化失败: {e}")
        return {
            'success': False,
            'error': str(e),
            'initialization_time': datetime.now().isoformat()
        }


if __name__ == "__main__":
    # 独立运行初始化脚本
    import logging
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    
    async def run_initialization():
        """运行初始化"""
        print("🚀 开始健康系统初始化...")
        
        result = await initialize_health_system()
        
        print("\n" + "="*60)
        print("📋 健康系统初始化报告")
        print("="*60)
        
        summary = health_system_initializer.get_initialization_summary()
        
        print(f"总体状态: {'✅ 成功' if summary['overall_success'] else '❌ 失败'}")
        print(f"成功率: {summary['success_rate']}%")
        print(f"成功组件: {summary['successful_components']}/{summary['total_components']}")
        
        print("\n📊 组件状态:")
        for component, status in summary['component_status'].items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {component}: {'成功' if status else '失败'}")
        
        if summary['errors']:
            print(f"\n❌ 错误 ({len(summary['errors'])}):")
            for error in summary['errors']:
                print(f"  - {error}")
        
        if summary['warnings']:
            print(f"\n⚠️  警告 ({len(summary['warnings'])}):")
            for warning in summary['warnings']:
                print(f"  - {warning}")
        
        print("\n" + "="*60)
        
        return result
    
    # 运行初始化
    asyncio.run(run_initialization())
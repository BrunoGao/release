#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ljwx-boot任务系统处理器
基于已有的任务管理系统触发健康数据处理

@Author: bruno.gao <gaojunivas@gmail.com>
@ProjectName: ljwx-boot
@CreateTime: 2025-01-26
"""

import requests
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from database_helper import DatabaseHelper
from auth_manager import AuthManager

@dataclass
class TaskProcessingResult:
    """任务处理结果"""
    task_type: str
    success: bool = False
    data: Optional[Dict] = None
    message: str = ""
    execution_time: float = 0.0
    
class LjwxBootTaskProcessor:
    """ljwx-boot任务系统处理器"""
    
    def __init__(self, base_url: str, auth_manager: AuthManager):
        self.base_url = base_url.rstrip('/')
        self.auth_manager = auth_manager
        self.session = auth_manager.get_authenticated_session()
        self.db_helper = DatabaseHelper()
        
        # 配置日志
        self.logger = logging.getLogger(f"{__name__}.LjwxBootTaskProcessor")
        
        # 可用的API端点
        self.endpoints = {
            'task_status': '/api/health/task/status',
            'task_statistics': '/api/health/task/statistics', 
            'task_tables': '/api/health/task/tables',
            'cache_statistics': '/api/health/task/cache/statistics',
            'cache_clear': '/api/health/task/cache/clear',
            'cache_warmup': '/api/health/task/cache/warmup',
            'department_overview': '/api/health/task/department/{departmentId}/overview',
            'department_ranking': '/api/health/task/department/ranking'
        }
    
    def get_task_status(self) -> Dict:
        """获取任务状态"""
        try:
            response = self.session.get(f"{self.base_url}{self.endpoints['task_status']}")
            response.raise_for_status()
            
            result = response.json()
            self.logger.info("✅ 任务状态获取成功")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 获取任务状态失败: {str(e)}")
            return {}
    
    def get_task_statistics(self) -> Dict:
        """获取任务统计信息"""
        try:
            response = self.session.get(f"{self.base_url}{self.endpoints['task_statistics']}")
            response.raise_for_status()
            
            result = response.json()
            self.logger.info("✅ 任务统计信息获取成功")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 获取任务统计信息失败: {str(e)}")
            return {}
    
    def get_cache_statistics(self) -> Dict:
        """获取缓存统计信息"""
        try:
            response = self.session.get(f"{self.base_url}{self.endpoints['cache_statistics']}")
            response.raise_for_status()
            
            result = response.json()
            self.logger.info("✅ 缓存统计信息获取成功")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 获取缓存统计信息失败: {str(e)}")
            return {}
    
    def clear_cache(self, user_id: Optional[int] = None) -> bool:
        """清理缓存"""
        try:
            if user_id:
                url = f"{self.base_url}/api/health/task/cache/clear/{user_id}"
            else:
                url = f"{self.base_url}{self.endpoints['cache_clear']}"
                
            response = self.session.post(url)
            response.raise_for_status()
            
            result = response.json()
            self.logger.info(f"✅ 缓存清理成功: user_id={user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 缓存清理失败: {str(e)}")
            return False
    
    def warmup_cache(self) -> bool:
        """预热缓存"""
        try:
            response = self.session.post(f"{self.base_url}{self.endpoints['cache_warmup']}")
            response.raise_for_status()
            
            result = response.json()
            self.logger.info("✅ 缓存预热成功")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 缓存预热失败: {str(e)}")
            return False
    
    def get_department_overview(self, department_id: int) -> Dict:
        """获取部门概览"""
        try:
            url = f"{self.base_url}/api/health/task/department/{department_id}/overview"
            response = self.session.get(url)
            response.raise_for_status()
            
            result = response.json()
            self.logger.info(f"✅ 部门{department_id}概览获取成功")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 获取部门{department_id}概览失败: {str(e)}")
            return {}
    
    def get_department_ranking(self) -> Dict:
        """获取部门排名"""
        try:
            response = self.session.get(f"{self.base_url}{self.endpoints['department_ranking']}")
            response.raise_for_status()
            
            result = response.json()
            self.logger.info("✅ 部门排名获取成功")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 获取部门排名失败: {str(e)}")
            return {}
    
    def analyze_current_data_status(self) -> Dict:
        """分析当前数据状态"""
        self.logger.info("🔍 开始分析当前数据状态...")
        
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'task_status': {},
            'task_statistics': {},
            'cache_statistics': {},
            'database_status': {},
            'active_users': [],
            'recommendations': []
        }
        
        # 1. 获取任务状态
        task_status = self.get_task_status()
        analysis['task_status'] = task_status
        
        # 2. 获取任务统计
        task_stats = self.get_task_statistics()
        analysis['task_statistics'] = task_stats
        
        # 3. 获取缓存统计
        cache_stats = self.get_cache_statistics()
        analysis['cache_statistics'] = cache_stats
        
        # 4. 获取数据库状态
        db_status = self.db_helper.check_health_tables()
        analysis['database_status'] = db_status
        
        # 5. 获取活跃用户
        active_users = self.db_helper.get_active_users(30)
        analysis['active_users'] = active_users[:10]  # 只显示前10个
        
        # 6. 生成建议
        recommendations = self.generate_recommendations(task_stats, db_status, active_users)
        analysis['recommendations'] = recommendations
        
        self.logger.info("✅ 数据状态分析完成")
        return analysis
    
    def generate_recommendations(self, task_stats: Dict, db_status: Dict, active_users: List) -> List[str]:
        """生成处理建议"""
        recommendations = []
        
        # 分析基线数据状态
        baseline_stats = task_stats.get('baselineStats', [])
        if baseline_stats:
            latest_date = max([stat.get('latest_date', '1970-01-01') for stat in baseline_stats])
            today = datetime.now().strftime('%Y-%m-%d')
            
            if latest_date < today:
                days_behind = (datetime.strptime(today, '%Y-%m-%d') - 
                             datetime.strptime(latest_date, '%Y-%m-%d')).days
                recommendations.append(f"🔄 基线数据已过期{days_behind}天，建议立即执行基线生成任务")
        
        # 分析评分数据状态
        score_stats = task_stats.get('scoreStats', [])
        if not score_stats:
            recommendations.append("💯 评分数据为空，建议执行健康评分计算任务")
        
        # 分析活跃用户数量
        if len(active_users) > 0:
            recommendations.append(f"👥 发现{len(active_users)}个活跃用户，可以进行个人健康数据处理")
        else:
            recommendations.append("⚠️ 没有找到活跃用户，请检查健康数据是否正常上传")
        
        # 分析表结构
        missing_tables = [name for name, info in db_status.items() 
                         if not info.get('exists', False)]
        if missing_tables:
            recommendations.append(f"🗄️ 缺失数据表: {', '.join(missing_tables)}，建议检查数据库结构")
        
        return recommendations
    
    def trigger_data_processing_tasks(self) -> List[TaskProcessingResult]:
        """触发数据处理任务"""
        self.logger.info("🚀 开始触发数据处理任务...")
        
        results = []
        
        # 1. 清理缓存
        start_time = time.time()
        cache_cleared = self.clear_cache()
        results.append(TaskProcessingResult(
            task_type="cache_clear",
            success=cache_cleared,
            message="缓存清理" + ("成功" if cache_cleared else "失败"),
            execution_time=time.time() - start_time
        ))
        
        # 2. 获取当前状态（这会触发内部的数据检查）
        start_time = time.time()
        analysis = self.analyze_current_data_status()
        results.append(TaskProcessingResult(
            task_type="data_analysis",
            success=bool(analysis),
            data=analysis,
            message="数据状态分析" + ("完成" if analysis else "失败"),
            execution_time=time.time() - start_time
        ))
        
        # 3. 预热缓存
        start_time = time.time()
        cache_warmed = self.warmup_cache()
        results.append(TaskProcessingResult(
            task_type="cache_warmup", 
            success=cache_warmed,
            message="缓存预热" + ("成功" if cache_warmed else "失败"),
            execution_time=time.time() - start_time
        ))
        
        # 4. 获取部门排名（如果支持）
        try:
            start_time = time.time()
            dept_ranking = self.get_department_ranking()
            results.append(TaskProcessingResult(
                task_type="department_ranking",
                success=bool(dept_ranking),
                data=dept_ranking,
                message="部门排名获取" + ("成功" if dept_ranking else "失败"),
                execution_time=time.time() - start_time
            ))
        except:
            pass  # 如果不支持部门功能，跳过
        
        # 统计结果
        successful_tasks = sum(1 for result in results if result.success)
        total_time = sum(result.execution_time for result in results)
        
        self.logger.info(f"🎉 数据处理任务完成: {successful_tasks}/{len(results)} 成功, 总耗时: {total_time:.2f}秒")
        
        return results
    
    def generate_health_insights(self) -> Dict:
        """生成健康洞察报告"""
        self.logger.info("🔍 开始生成健康洞察报告...")
        
        insights = {
            'timestamp': datetime.now().isoformat(),
            'summary': {},
            'user_insights': [],
            'system_health': {},
            'recommendations': []
        }
        
        try:
            # 获取任务统计
            task_stats = self.get_task_statistics()
            
            # 获取活跃用户
            active_users = self.db_helper.get_active_users(30)
            
            # 系统健康状况
            baseline_stats = task_stats.get('baselineStats', [])
            score_stats = task_stats.get('scoreStats', [])
            
            insights['summary'] = {
                'active_users': len(active_users),
                'baseline_features': len(baseline_stats),
                'score_features': len(score_stats),
                'archive_tables': task_stats.get('archiveTableCount', 0)
            }
            
            # 特征分析
            feature_analysis = {}
            for stat in baseline_stats:
                feature = stat['feature_name']
                feature_analysis[feature] = {
                    'baseline_count': stat['count'],
                    'device_count': stat['device_count'],
                    'latest_date': stat['latest_date']
                }
            
            insights['system_health'] = feature_analysis
            
            # 用户健康洞察
            for user in active_users[:5]:  # 前5个用户
                user_stats = self.db_helper.get_user_health_data_stats(user['user_id'], 30)
                if user_stats:
                    insights['user_insights'].append({
                        'user_id': user['user_id'],
                        'user_name': user['user_name'],
                        'total_records': user_stats.get('total_records', 0),
                        'features_available': {
                            'heart_rate': user_stats.get('heart_rate_count', 0),
                            'blood_oxygen': user_stats.get('blood_oxygen_count', 0),
                            'temperature': user_stats.get('temperature_count', 0),
                            'pressure': user_stats.get('pressure_count', 0),
                            'stress': user_stats.get('stress_count', 0),
                            'step': user_stats.get('step_count', 0)
                        }
                    })
            
            self.logger.info("✅ 健康洞察报告生成完成")
            
        except Exception as e:
            self.logger.error(f"❌ 生成健康洞察报告失败: {str(e)}")
            insights['error'] = str(e)
        
        return insights

def test_ljwx_boot_task_processor():
    """测试ljwx-boot任务系统处理器"""
    import json
    from auth_manager import create_auth_manager
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # 加载配置
    try:
        with open('health_processing_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ 无法加载配置文件: {e}")
        return False
    
    # 创建认证管理器
    auth_manager = create_auth_manager(config)
    if not auth_manager or not auth_manager.login():
        print("❌ 认证失败")
        return False
    
    # 创建处理器
    processor = LjwxBootTaskProcessor(
        config['ljwx_boot']['base_url'],
        auth_manager
    )
    
    print("🔍 测试任务系统API...")
    
    # 测试各种功能
    task_status = processor.get_task_status()
    print(f"任务状态: {'✅' if task_status else '❌'}")
    
    task_stats = processor.get_task_statistics()
    print(f"任务统计: {'✅' if task_stats else '❌'}")
    
    # 数据状态分析
    print("\n📊 数据状态分析...")
    analysis = processor.analyze_current_data_status()
    
    if analysis.get('recommendations'):
        print("建议:")
        for rec in analysis['recommendations']:
            print(f"  - {rec}")
    
    # 生成健康洞察
    print("\n🔍 生成健康洞察...")
    insights = processor.generate_health_insights()
    
    print(f"活跃用户: {insights['summary'].get('active_users', 0)}")
    print(f"基线特征: {insights['summary'].get('baseline_features', 0)}")
    
    print("\n✅ 测试完成")
    return True

if __name__ == "__main__":
    test_ljwx_boot_task_processor()
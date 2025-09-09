#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
健康系统API接口
Health System API Endpoints

提供完整的健康管理系统API接口，整合所有健康引擎模块
- 基线生成API：个人、群体、职位风险基线
- 健康评分API：多维度健康评分计算
- 健康建议API：个性化智能建议生成
- 健康画像API：综合健康画像生成与查询
- 数据质量API：数据质量检查与报告
- 缓存管理API：缓存状态监控与管理

Author: System
Date: 2025-09-01
Version: 1.0
"""

import logging
import json
import asyncio
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any
from flask import Blueprint, request, jsonify, g
from functools import wraps
import traceback

# 导入健康引擎模块
from .health_baseline_engine import RealTimeHealthBaselineEngine
from .health_score_engine import RealTimeHealthScoreEngine  
from .health_recommendation_engine import RealTimeHealthRecommendationEngine
from .health_profile_engine import RealTimeHealthProfileEngine
from .health_cache_service import health_cache_service
from .health_data_quality import health_data_quality

from .models import db, UserHealthData, UserHealthProfile, HealthBaseline, AlertInfo

logger = logging.getLogger(__name__)

# 创建API蓝图
health_api = Blueprint('health_api', __name__, url_prefix='/api/health')

# 全局引擎实例
baseline_engine = None
score_engine = None
recommendation_engine = None
profile_engine = None

# ==================== 工具函数 ====================

def async_route(f):
    """异步路由装饰器"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            # 创建新的事件循环用于API调用
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(f(*args, **kwargs))
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"异步路由执行失败: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    wrapper.__name__ = f.__name__
    return wrapper

def validate_request_params(required_params: List[str]):
    """验证请求参数装饰器"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                # 获取请求数据
                if request.method == 'GET':
                    data = request.args.to_dict()
                else:
                    data = request.get_json() or {}
                
                # 检查必需参数
                missing_params = [param for param in required_params if param not in data]
                if missing_params:
                    return jsonify({
                        'success': False,
                        'error': f'缺少必需参数: {", ".join(missing_params)}',
                        'timestamp': datetime.now().isoformat()
                    }), 400
                
                # 将数据传递给视图函数
                return f(data, *args, **kwargs)
                
            except Exception as e:
                logger.error(f"参数验证失败: {e}")
                return jsonify({
                    'success': False,
                    'error': '参数验证失败',
                    'timestamp': datetime.now().isoformat()
                }), 400
        
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

def init_engines():
    """初始化所有引擎"""
    global baseline_engine, score_engine, recommendation_engine, profile_engine
    
    try:
        if not baseline_engine:
            baseline_engine = RealTimeHealthBaselineEngine()
        if not score_engine:
            score_engine = RealTimeHealthScoreEngine()
        if not recommendation_engine:
            recommendation_engine = RealTimeHealthRecommendationEngine()
        if not profile_engine:
            profile_engine = RealTimeHealthProfileEngine()
        
        logger.info("✅ 健康引擎初始化成功")
        
    except Exception as e:
        logger.error(f"❌ 健康引擎初始化失败: {e}")
        raise

# ==================== 基线生成API ====================

@health_api.route('/baseline/personal', methods=['POST'])
@validate_request_params(['user_id', 'customer_id'])
@async_route
async def generate_personal_baseline(data):
    """生成个人健康基线"""
    try:
        init_engines()
        
        user_id = int(data['user_id'])
        customer_id = int(data['customer_id'])
        days_back = int(data.get('days_back', 30))
        
        # 检查缓存
        cached_baseline = await health_cache_service.get_cached_baseline(user_id, customer_id, "personal")
        if cached_baseline:
            return jsonify({
                'success': True,
                'data': cached_baseline,
                'source': 'cache',
                'timestamp': datetime.now().isoformat()
            })
        
        # 生成基线
        baseline_result = await baseline_engine.generate_personal_baseline(user_id, customer_id, days_back)
        
        if baseline_result['success']:
            # 缓存结果
            await health_cache_service.cache_health_baseline(user_id, customer_id, baseline_result['data'], "personal")
            
            return jsonify({
                'success': True,
                'data': baseline_result['data'],
                'metadata': baseline_result['metadata'],
                'source': 'computed',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': baseline_result['error'],
                'timestamp': datetime.now().isoformat()
            }), 500
    
    except Exception as e:
        logger.error(f"个人基线生成失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@health_api.route('/baseline/population', methods=['POST'])
@validate_request_params(['customer_id'])
@async_route
async def generate_population_baseline(data):
    """生成群体基线"""
    try:
        init_engines()
        
        customer_id = int(data['customer_id'])
        age_group = data.get('age_group')
        gender = data.get('gender')
        
        # 生成群体基线
        baseline_result = await baseline_engine.generate_population_baseline(customer_id, age_group, gender)
        
        if baseline_result['success']:
            return jsonify({
                'success': True,
                'data': baseline_result['data'],
                'metadata': baseline_result['metadata'],
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': baseline_result['error'],
                'timestamp': datetime.now().isoformat()
            }), 500
    
    except Exception as e:
        logger.error(f"群体基线生成失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@health_api.route('/baseline/position-risk', methods=['POST'])
@validate_request_params(['customer_id', 'risk_level'])
@async_route
async def generate_position_risk_baseline(data):
    """生成职位风险基线"""
    try:
        init_engines()
        
        customer_id = int(data['customer_id'])
        risk_level = data['risk_level']
        
        baseline_result = await baseline_engine.generate_position_risk_baseline(customer_id, risk_level)
        
        if baseline_result['success']:
            return jsonify({
                'success': True,
                'data': baseline_result['data'],
                'metadata': baseline_result['metadata'],
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': baseline_result['error'],
                'timestamp': datetime.now().isoformat()
            }), 500
    
    except Exception as e:
        logger.error(f"职位风险基线生成失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# ==================== 健康评分API ====================

@health_api.route('/score/comprehensive', methods=['POST'])
@validate_request_params(['user_id', 'customer_id'])
@async_route
async def calculate_comprehensive_health_score(data):
    """计算综合健康评分"""
    try:
        init_engines()
        
        user_id = int(data['user_id'])
        customer_id = int(data['customer_id'])
        date_range = int(data.get('date_range', 30))
        
        # 检查缓存
        today = datetime.now().strftime("%Y-%m-%d")
        cached_score = await health_cache_service.get_cached_health_score(user_id, customer_id, today)
        if cached_score:
            return jsonify({
                'success': True,
                'data': cached_score,
                'source': 'cache',
                'timestamp': datetime.now().isoformat()
            })
        
        # 计算健康评分
        score_result = await score_engine.calculate_comprehensive_health_score(user_id, customer_id, date_range)
        
        if score_result['success']:
            # 缓存结果
            await health_cache_service.cache_health_score(user_id, customer_id, score_result['data'], today)
            
            return jsonify({
                'success': True,
                'data': score_result['data'],
                'visualization': score_result.get('visualization', {}),
                'source': 'computed',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': score_result['error'],
                'timestamp': datetime.now().isoformat()
            }), 500
    
    except Exception as e:
        logger.error(f"综合健康评分计算失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@health_api.route('/score/trend', methods=['POST'])
@validate_request_params(['user_id', 'customer_id'])
@async_route
async def get_health_score_trend(data):
    """获取健康评分趋势"""
    try:
        init_engines()
        
        user_id = int(data['user_id'])
        customer_id = int(data['customer_id'])
        days = int(data.get('days', 30))
        
        trend_result = await score_engine.get_health_score_trend(user_id, customer_id, days)
        
        if trend_result['success']:
            return jsonify({
                'success': True,
                'data': trend_result['data'],
                'visualization': trend_result.get('visualization', {}),
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': trend_result['error'],
                'timestamp': datetime.now().isoformat()
            }), 500
    
    except Exception as e:
        logger.error(f"健康评分趋势获取失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# ==================== 健康建议API ====================

@health_api.route('/recommendations/generate', methods=['POST'])
@validate_request_params(['user_id', 'customer_id'])
@async_route
async def generate_health_recommendations(data):
    """生成健康建议"""
    try:
        init_engines()
        
        user_id = int(data['user_id'])
        customer_id = int(data['customer_id'])
        
        recommendation_result = await recommendation_engine.generate_personalized_recommendations(user_id, customer_id)
        
        if recommendation_result['success']:
            return jsonify({
                'success': True,
                'data': recommendation_result['data'],
                'metadata': recommendation_result.get('metadata', {}),
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': recommendation_result['error'],
                'timestamp': datetime.now().isoformat()
            }), 500
    
    except Exception as e:
        logger.error(f"健康建议生成失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@health_api.route('/recommendations/track', methods=['POST'])
@validate_request_params(['user_id', 'recommendation_id', 'status'])
@async_route
async def track_recommendation_execution(data):
    """跟踪建议执行状态"""
    try:
        init_engines()
        
        user_id = int(data['user_id'])
        recommendation_id = data['recommendation_id']
        status = data['status']
        feedback = data.get('feedback', '')
        
        track_result = await recommendation_engine.track_recommendation_execution(
            user_id, recommendation_id, status, feedback
        )
        
        if track_result['success']:
            return jsonify({
                'success': True,
                'data': track_result['data'],
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': track_result['error'],
                'timestamp': datetime.now().isoformat()
            }), 500
    
    except Exception as e:
        logger.error(f"建议执行跟踪失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# ==================== 健康画像API ====================

@health_api.route('/profile/generate', methods=['POST'])
@validate_request_params(['user_id', 'customer_id'])
@async_route
async def generate_health_profile(data):
    """生成健康画像"""
    try:
        init_engines()
        
        user_id = int(data['user_id'])
        customer_id = int(data['customer_id'])
        
        # 检查缓存
        cached_profile = await health_cache_service.get_cached_health_profile(user_id, customer_id)
        if cached_profile:
            return jsonify({
                'success': True,
                'data': cached_profile,
                'source': 'cache',
                'timestamp': datetime.now().isoformat()
            })
        
        # 生成健康画像
        profile_result = await profile_engine.generate_comprehensive_health_profile(user_id, customer_id)
        
        if profile_result['success']:
            # 缓存结果
            await health_cache_service.cache_health_profile(user_id, customer_id, profile_result['data'])
            
            return jsonify({
                'success': True,
                'data': profile_result['data'],
                'visualization': profile_result.get('visualization', {}),
                'source': 'computed',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': profile_result['error'],
                'timestamp': datetime.now().isoformat()
            }), 500
    
    except Exception as e:
        logger.error(f"健康画像生成失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@health_api.route('/profile/batch', methods=['POST'])
@validate_request_params(['user_ids', 'customer_id'])
@async_route
async def batch_generate_health_profiles(data):
    """批量生成健康画像"""
    try:
        init_engines()
        
        user_ids = data['user_ids']
        customer_id = int(data['customer_id'])
        
        if not isinstance(user_ids, list):
            return jsonify({
                'success': False,
                'error': 'user_ids 必须是数组',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # 限制批量处理数量
        if len(user_ids) > 100:
            return jsonify({
                'success': False,
                'error': '批量处理数量不能超过100个用户',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        batch_result = await profile_engine.batch_generate_health_profiles(user_ids, customer_id)
        
        if batch_result['success']:
            return jsonify({
                'success': True,
                'data': batch_result['data'],
                'metadata': batch_result.get('metadata', {}),
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': batch_result['error'],
                'timestamp': datetime.now().isoformat()
            }), 500
    
    except Exception as e:
        logger.error(f"批量健康画像生成失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# ==================== 数据质量API ====================

@health_api.route('/quality/validate', methods=['POST'])
@validate_request_params(['data'])
@async_route
async def validate_health_data_quality(data):
    """验证健康数据质量"""
    try:
        health_data = data['data']
        
        validation_result = await health_data_quality.validate_health_data(health_data)
        
        return jsonify({
            'success': True,
            'data': {
                'is_valid': validation_result.is_valid,
                'quality_score': validation_result.quality_score,
                'quality_level': validation_result.quality_level.value,
                'issues': validation_result.issues,
                'warnings': validation_result.warnings,
                'cleaned_data': validation_result.cleaned_data,
                'metadata': validation_result.metadata
            },
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"数据质量验证失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@health_api.route('/quality/report', methods=['GET'])
@async_route
async def get_quality_report():
    """获取数据质量报告"""
    try:
        customer_id = request.args.get('customer_id')
        if customer_id:
            customer_id = int(customer_id)
        
        report = health_data_quality.generate_quality_report(customer_id)
        
        return jsonify({
            'success': True,
            'data': report,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"质量报告生成失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@health_api.route('/quality/batch-validate', methods=['POST'])
@validate_request_params(['data_list'])
@async_route
async def batch_validate_health_data(data):
    """批量验证健康数据质量"""
    try:
        data_list = data['data_list']
        
        if not isinstance(data_list, list):
            return jsonify({
                'success': False,
                'error': 'data_list 必须是数组',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # 限制批量处理数量
        if len(data_list) > 1000:
            return jsonify({
                'success': False,
                'error': '批量处理数量不能超过1000条数据',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        validation_results = await health_data_quality.batch_validate_health_data(data_list)
        
        # 转换结果格式
        formatted_results = []
        for result in validation_results:
            formatted_results.append({
                'is_valid': result.is_valid,
                'quality_score': result.quality_score,
                'quality_level': result.quality_level.value,
                'issues': result.issues,
                'warnings': result.warnings,
                'cleaned_data': result.cleaned_data,
                'metadata': result.metadata
            })
        
        return jsonify({
            'success': True,
            'data': formatted_results,
            'summary': {
                'total_count': len(validation_results),
                'valid_count': sum(1 for r in validation_results if r.is_valid),
                'invalid_count': sum(1 for r in validation_results if not r.is_valid),
                'average_quality_score': sum(r.quality_score for r in validation_results) / len(validation_results) if validation_results else 0
            },
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"批量数据质量验证失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# ==================== 缓存管理API ====================

@health_api.route('/cache/info', methods=['GET'])
@async_route
async def get_cache_info():
    """获取缓存信息"""
    try:
        cache_info = await health_cache_service.get_cache_info()
        
        return jsonify({
            'success': True,
            'data': cache_info,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"获取缓存信息失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@health_api.route('/cache/stats', methods=['GET'])
@async_route
async def get_cache_performance_stats():
    """获取缓存性能统计"""
    try:
        stats = health_cache_service.get_performance_stats()
        
        return jsonify({
            'success': True,
            'data': stats,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"获取缓存统计失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@health_api.route('/cache/warmup', methods=['POST'])
@validate_request_params(['user_id', 'customer_id'])
@async_route
async def warmup_user_cache(data):
    """预热用户缓存"""
    try:
        user_id = int(data['user_id'])
        customer_id = int(data['customer_id'])
        
        success = await health_cache_service.warmup_user_cache(user_id, customer_id)
        
        return jsonify({
            'success': success,
            'message': f"用户 {user_id} 缓存预热{'成功' if success else '失败'}",
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"缓存预热失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@health_api.route('/cache/invalidate', methods=['POST'])
@validate_request_params(['cache_type'])
@async_route
async def invalidate_cache(data):
    """失效缓存"""
    try:
        cache_type = data['cache_type']
        pattern = data.get('pattern', '*')
        
        deleted_count = await health_cache_service.invalidate_cache(cache_type, pattern)
        
        return jsonify({
            'success': True,
            'data': {
                'cache_type': cache_type,
                'pattern': pattern,
                'deleted_count': deleted_count
            },
            'message': f"已失效 {deleted_count} 个缓存键",
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"缓存失效失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# ==================== 系统状态API ====================

@health_api.route('/system/status', methods=['GET'])
@async_route
async def get_system_status():
    """获取系统状态"""
    try:
        # 检查各组件状态
        components_status = {}
        
        # 检查数据库连接
        try:
            db.session.execute(text('SELECT 1'))
            components_status['database'] = 'healthy'
        except Exception as e:
            components_status['database'] = f'unhealthy: {str(e)}'
        
        # 检查Redis连接
        try:
            await health_cache_service.redis_client.ping()
            components_status['redis'] = 'healthy'
        except Exception as e:
            components_status['redis'] = f'unhealthy: {str(e)}'
        
        # 检查引擎状态
        components_status['engines'] = {
            'baseline_engine': 'healthy' if baseline_engine else 'not_initialized',
            'score_engine': 'healthy' if score_engine else 'not_initialized',
            'recommendation_engine': 'healthy' if recommendation_engine else 'not_initialized',
            'profile_engine': 'healthy' if profile_engine else 'not_initialized'
        }
        
        # 系统性能指标
        cache_stats = health_cache_service.get_performance_stats()
        quality_stats = health_data_quality.quality_stats
        
        return jsonify({
            'success': True,
            'data': {
                'system_time': datetime.now().isoformat(),
                'components_status': components_status,
                'performance_metrics': {
                    'cache_hit_rate': cache_stats.get('hit_rate_percent', 0),
                    'cache_error_rate': cache_stats.get('error_rate_percent', 0),
                    'total_cache_requests': cache_stats.get('total_requests', 0),
                    'quality_validation_count': quality_stats.get('total_validated', 0),
                    'quality_pass_rate': (quality_stats.get('total_passed', 0) / max(quality_stats.get('total_validated', 1), 1)) * 100
                }
            },
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"系统状态检查失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@health_api.route('/system/initialize', methods=['POST'])
@async_route
async def initialize_system():
    """初始化系统"""
    try:
        # 初始化缓存服务
        await health_cache_service.initialize()
        
        # 初始化引擎
        init_engines()
        
        return jsonify({
            'success': True,
            'message': '健康系统初始化成功',
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"系统初始化失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# ==================== 错误处理 ====================

@health_api.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({
        'success': False,
        'error': 'API接口不存在',
        'timestamp': datetime.now().isoformat()
    }), 404

@health_api.errorhandler(405)
def method_not_allowed(error):
    """405错误处理"""
    return jsonify({
        'success': False,
        'error': '请求方法不允许',
        'timestamp': datetime.now().isoformat()
    }), 405

@health_api.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    logger.error(f"内部服务器错误: {error}")
    return jsonify({
        'success': False,
        'error': '内部服务器错误',
        'timestamp': datetime.now().isoformat()
    }), 500


# ==================== API文档路由 ====================

@health_api.route('/docs', methods=['GET'])
def get_api_docs():
    """获取API文档"""
    docs = {
        'title': '健康管理系统API文档',
        'version': '1.0',
        'description': '提供完整的健康数据分析和管理功能',
        'base_url': '/api/health',
        'endpoints': {
            'baseline': {
                'personal': 'POST /baseline/personal - 生成个人健康基线',
                'population': 'POST /baseline/population - 生成群体基线',
                'position-risk': 'POST /baseline/position-risk - 生成职位风险基线'
            },
            'score': {
                'comprehensive': 'POST /score/comprehensive - 计算综合健康评分',
                'trend': 'POST /score/trend - 获取健康评分趋势'
            },
            'recommendations': {
                'generate': 'POST /recommendations/generate - 生成健康建议',
                'track': 'POST /recommendations/track - 跟踪建议执行状态'
            },
            'profile': {
                'generate': 'POST /profile/generate - 生成健康画像',
                'batch': 'POST /profile/batch - 批量生成健康画像'
            },
            'quality': {
                'validate': 'POST /quality/validate - 验证数据质量',
                'report': 'GET /quality/report - 获取质量报告',
                'batch-validate': 'POST /quality/batch-validate - 批量验证数据质量'
            },
            'cache': {
                'info': 'GET /cache/info - 获取缓存信息',
                'stats': 'GET /cache/stats - 获取缓存统计',
                'warmup': 'POST /cache/warmup - 预热用户缓存',
                'invalidate': 'POST /cache/invalidate - 失效缓存'
            },
            'system': {
                'status': 'GET /system/status - 获取系统状态',
                'initialize': 'POST /system/initialize - 初始化系统'
            }
        },
        'response_format': {
            'success': True,
            'data': '响应数据',
            'timestamp': '响应时间戳'
        }
    }
    
    return jsonify(docs)


if __name__ == "__main__":
    # API测试代码
    from flask import Flask
    
    app = Flask(__name__)
    app.register_blueprint(health_api)
    
    @app.route('/test')
    def test():
        return jsonify({'message': '健康API服务正常运行'})
    
    print("健康API服务启动...")
    print("API文档: http://localhost:5000/api/health/docs")
    app.run(debug=True, host='0.0.0.0', port=5000)
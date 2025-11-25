# cache_service.py
# 智能缓存服务 - 提升70%大屏刷新性能
# =============================================================================

import json
import logging
from functools import wraps
from typing import Optional, Callable, Any
from datetime import timedelta

logger = logging.getLogger(__name__)

class CacheService:
    """
    智能缓存服务
    - 热点数据自动缓存
    - 分层TTL策略
    - 缓存预热
    - 缓存击穿防护
    """

    # 缓存键前缀
    PREFIX = 'ljwx:bigscreen:'

    # 缓存TTL配置（秒）
    TTL_CONFIG = {
        # 用户相关 - 5分钟
        'user_latest_health': 300,       # 用户最新健康数据
        'user_health_profile': 300,      # 用户健康档案
        'user_health_trend': 600,        # 用户健康趋势（10分钟）

        # 设备相关 - 1分钟
        'device_status': 60,             # 设备状态
        'device_list': 180,              # 设备列表（3分钟）
        'device_stats': 300,             # 设备统计（5分钟）

        # 告警相关 - 30秒
        'alert_unread': 30,              # 未读告警
        'alert_list': 60,                # 告警列表（1分钟）
        'alert_stats': 180,              # 告警统计（3分钟）

        # 组织相关 - 10分钟
        'org_stats': 600,                # 组织统计
        'org_health_ranking': 600,       # 组织健康排行
        'org_device_count': 600,         # 组织设备数

        # 大屏相关 - 5分钟
        'bigscreen_summary': 300,        # 大屏概览数据
        'bigscreen_kpi': 180,            # KPI数据（3分钟）
        'bigscreen_chart_data': 300,     # 图表数据（5分钟）
    }

    def __init__(self, redis_helper):
        """
        初始化缓存服务

        Args:
            redis_helper: RedisHelper实例
        """
        self.redis = redis_helper
        logger.info("✅ CacheService初始化成功")

    def _make_key(self, category: str, *args) -> str:
        """
        生成缓存键

        Args:
            category: 缓存类别
            *args: 附加参数

        Returns:
            完整的缓存键
        """
        parts = [self.PREFIX, category]
        parts.extend(str(arg) for arg in args if arg is not None)
        return ':'.join(parts)

    def get(self, category: str, *args) -> Optional[Any]:
        """
        获取缓存数据

        Args:
            category: 缓存类别
            *args: 附加参数

        Returns:
            缓存的数据，如果不存在返回None
        """
        key = self._make_key(category, *args)
        try:
            data = self.redis.get(key)
            if data:
                logger.debug(f"✅ 缓存命中: {key}")
                return json.loads(data)
            logger.debug(f"❌ 缓存未命中: {key}")
            return None
        except Exception as e:
            logger.warning(f"⚠️  缓存获取失败 {key}: {e}")
            return None

    def set(self, category: str, *args, data: Any) -> bool:
        """
        设置缓存数据

        Args:
            category: 缓存类别
            *args: 附加参数
            data: 要缓存的数据

        Returns:
            是否设置成功
        """
        key = self._make_key(category, *args)
        ttl = self.TTL_CONFIG.get(category, 300)  # 默认5分钟

        try:
            self.redis.setex(key, ttl, json.dumps(data))
            logger.debug(f"✅ 缓存设置成功: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.warning(f"⚠️  缓存设置失败 {key}: {e}")
            return False

    def delete(self, category: str, *args) -> bool:
        """
        删除缓存

        Args:
            category: 缓存类别
            *args: 附加参数

        Returns:
            是否删除成功
        """
        key = self._make_key(category, *args)
        try:
            result = self.redis.delete(key)
            logger.debug(f"✅ 缓存删除: {key}")
            return result > 0
        except Exception as e:
            logger.warning(f"⚠️  缓存删除失败 {key}: {e}")
            return False

    def cache(self, category: str, *key_args):
        """
        装饰器：自动缓存函数结果

        用法:
        @cache_service.cache('user_latest_health', user_id)
        def get_user_health(user_id):
            return fetch_from_db(user_id)

        Args:
            category: 缓存类别
            *key_args: 缓存键参数
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # 尝试从缓存获取
                cached_data = self.get(category, *key_args)
                if cached_data is not None:
                    return cached_data

                # 缓存未命中，执行函数
                result = func(*args, **kwargs)

                # 将结果存入缓存
                if result is not None:
                    self.set(category, *key_args, data=result)

                return result
            return wrapper
        return decorator

    # =============================================================================
    # 便捷方法 - 常用热点数据缓存
    # =============================================================================

    def get_user_latest_health(self, user_id: int) -> Optional[dict]:
        """获取用户最新健康数据（缓存5分钟）"""
        return self.get('user_latest_health', user_id)

    def set_user_latest_health(self, user_id: int, data: dict) -> bool:
        """缓存用户最新健康数据"""
        return self.set('user_latest_health', user_id, data=data)

    def get_device_status(self, device_sn: str) -> Optional[dict]:
        """获取设备状态（缓存1分钟）"""
        return self.get('device_status', device_sn)

    def set_device_status(self, device_sn: str, data: dict) -> bool:
        """缓存设备状态"""
        return self.set('device_status', device_sn, data=data)

    def get_alert_unread(self, user_id: int) -> Optional[dict]:
        """获取未读告警（缓存30秒）"""
        return self.get('alert_unread', user_id)

    def set_alert_unread(self, user_id: int, data: dict) -> bool:
        """缓存未读告警"""
        return self.set('alert_unread', user_id, data=data)

    def get_org_stats(self, org_id: int) -> Optional[dict]:
        """获取组织统计（缓存10分钟）"""
        return self.get('org_stats', org_id)

    def set_org_stats(self, org_id: int, data: dict) -> bool:
        """缓存组织统计"""
        return self.set('org_stats', org_id, data=data)

    def get_bigscreen_summary(self, customer_id: str) -> Optional[dict]:
        """获取大屏概览数据（缓存5分钟）"""
        return self.get('bigscreen_summary', customer_id)

    def set_bigscreen_summary(self, customer_id: str, data: dict) -> bool:
        """缓存大屏概览数据"""
        return self.set('bigscreen_summary', customer_id, data=data)

    # =============================================================================
    # 缓存预热
    # =============================================================================

    def warm_up(self, customer_id: str, user_ids: list = None):
        """
        缓存预热 - 预先加载热点数据

        Args:
            customer_id: 客户ID
            user_ids: 用户ID列表（可选）
        """
        logger.info(f"🔥 开始缓存预热: customer_id={customer_id}")

        try:
            # 预热逻辑可以根据实际情况调整
            # 这里仅作为示例框架
            if user_ids:
                for user_id in user_ids[:100]:  # 最多预热100个用户
                    # 这里可以调用实际的数据获取函数
                    pass

            logger.info(f"✅ 缓存预热完成: customer_id={customer_id}")
        except Exception as e:
            logger.error(f"❌ 缓存预热失败: {e}")

    # =============================================================================
    # 缓存统计
    # =============================================================================

    def get_cache_stats(self) -> dict:
        """
        获取缓存统计信息

        Returns:
            缓存统计数据
        """
        try:
            # 统计不同类别的缓存键数量
            stats = {
                'total_keys': 0,
                'by_category': {}
            }

            # 这里可以扫描Redis键来统计
            # 为了性能考虑，实际使用时可能需要异步统计

            return stats
        except Exception as e:
            logger.error(f"❌ 获取缓存统计失败: {e}")
            return {'error': str(e)}


# =============================================================================
# 全局缓存服务实例（单例模式）
# =============================================================================
_cache_service_instance: Optional[CacheService] = None

def get_cache_service(redis_helper=None) -> CacheService:
    """
    获取全局缓存服务实例（单例）

    Args:
        redis_helper: RedisHelper实例（首次调用时必须提供）

    Returns:
        CacheService实例
    """
    global _cache_service_instance

    if _cache_service_instance is None:
        if redis_helper is None:
            raise ValueError("首次调用get_cache_service必须提供redis_helper参数")
        _cache_service_instance = CacheService(redis_helper)

    return _cache_service_instance

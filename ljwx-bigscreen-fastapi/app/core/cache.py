"""
Redis 缓存管理
支持连接池、分布式锁、发布订阅
"""

import redis.asyncio as redis
from redis.asyncio import ConnectionPool
from typing import Any, Optional, Union, Dict, List
import json
import pickle
import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Redis 连接池
redis_pool: Optional[ConnectionPool] = None
redis_client: Optional[redis.Redis] = None


async def init_redis_pool():
    """初始化 Redis 连接池"""
    global redis_pool, redis_client
    
    redis_pool = ConnectionPool.from_url(
        settings.REDIS_URL,
        max_connections=settings.REDIS_POOL_SIZE,
        retry_on_timeout=True,
        health_check_interval=30
    )
    
    redis_client = redis.Redis(connection_pool=redis_pool)
    
    # 测试连接
    try:
        await redis_client.ping()
        logger.info("Redis 连接池初始化完成")
    except Exception as e:
        logger.error(f"Redis 连接失败: {e}")
        raise


async def close_redis_pool():
    """关闭 Redis 连接池"""
    global redis_pool, redis_client
    
    if redis_client:
        await redis_client.close()
        logger.info("Redis 客户端已关闭")
    
    if redis_pool:
        await redis_pool.disconnect()
        logger.info("Redis 连接池已关闭")


def get_cache_key(key: str, prefix: Optional[str] = None) -> str:
    """生成缓存键"""
    prefix = prefix or settings.CACHE_KEY_PREFIX
    return f"{prefix}{key}"


class RedisCache:
    """Redis 缓存操作类"""
    
    def __init__(self, client: Optional[redis.Redis] = None):
        self.client = client or redis_client
        if not self.client:
            raise RuntimeError("Redis 客户端未初始化")
    
    async def get(self, key: str, default: Any = None) -> Any:
        """获取缓存值"""
        try:
            cache_key = get_cache_key(key)
            value = await self.client.get(cache_key)
            
            if value is None:
                return default
            
            # 尝试 JSON 解析
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # JSON 解析失败，尝试 pickle
                try:
                    return pickle.loads(value)
                except (pickle.PickleError, TypeError):
                    # 都失败，返回原始字符串
                    return value.decode('utf-8') if isinstance(value, bytes) else value
                    
        except Exception as e:
            logger.error(f"Redis GET 操作失败: {key}, {e}")
            return default
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        serializer: str = "json"
    ) -> bool:
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None 表示不过期
            serializer: 序列化方式 json|pickle|raw
        """
        try:
            cache_key = get_cache_key(key)
            ttl = ttl or settings.CACHE_TTL
            
            # 序列化值
            if serializer == "json":
                serialized_value = json.dumps(value, ensure_ascii=False, default=str)
            elif serializer == "pickle":
                serialized_value = pickle.dumps(value)
            else:  # raw
                serialized_value = value
            
            if ttl > 0:
                return await self.client.setex(cache_key, ttl, serialized_value)
            else:
                return await self.client.set(cache_key, serialized_value)
                
        except Exception as e:
            logger.error(f"Redis SET 操作失败: {key}, {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            cache_key = get_cache_key(key)
            result = await self.client.delete(cache_key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis DELETE 操作失败: {key}, {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        try:
            cache_key = get_cache_key(key)
            return await self.client.exists(cache_key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS 操作失败: {key}, {e}")
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """设置缓存过期时间"""
        try:
            cache_key = get_cache_key(key)
            return await self.client.expire(cache_key, ttl)
        except Exception as e:
            logger.error(f"Redis EXPIRE 操作失败: {key}, {e}")
            return False
    
    async def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """递增计数器"""
        try:
            cache_key = get_cache_key(key)
            return await self.client.incrby(cache_key, amount)
        except Exception as e:
            logger.error(f"Redis INCR 操作失败: {key}, {e}")
            return None
    
    async def decr(self, key: str, amount: int = 1) -> Optional[int]:
        """递减计数器"""
        try:
            cache_key = get_cache_key(key)
            return await self.client.decrby(cache_key, amount)
        except Exception as e:
            logger.error(f"Redis DECR 操作失败: {key}, {e}")
            return None
    
    async def sadd(self, key: str, *members) -> int:
        """集合添加元素"""
        try:
            cache_key = get_cache_key(key)
            return await self.client.sadd(cache_key, *members)
        except Exception as e:
            logger.error(f"Redis SADD 操作失败: {key}, {e}")
            return 0
    
    async def srem(self, key: str, *members) -> int:
        """集合删除元素"""
        try:
            cache_key = get_cache_key(key)
            return await self.client.srem(cache_key, *members)
        except Exception as e:
            logger.error(f"Redis SREM 操作失败: {key}, {e}")
            return 0
    
    async def smembers(self, key: str) -> set:
        """获取集合所有成员"""
        try:
            cache_key = get_cache_key(key)
            members = await self.client.smembers(cache_key)
            return {member.decode('utf-8') if isinstance(member, bytes) else member 
                    for member in members}
        except Exception as e:
            logger.error(f"Redis SMEMBERS 操作失败: {key}, {e}")
            return set()
    
    async def hset(self, key: str, field: str, value: Any) -> bool:
        """哈希表设置字段"""
        try:
            cache_key = get_cache_key(key)
            serialized_value = json.dumps(value, ensure_ascii=False, default=str)
            return await self.client.hset(cache_key, field, serialized_value) > 0
        except Exception as e:
            logger.error(f"Redis HSET 操作失败: {key}.{field}, {e}")
            return False
    
    async def hget(self, key: str, field: str, default: Any = None) -> Any:
        """哈希表获取字段"""
        try:
            cache_key = get_cache_key(key)
            value = await self.client.hget(cache_key, field)
            
            if value is None:
                return default
            
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value.decode('utf-8') if isinstance(value, bytes) else value
                
        except Exception as e:
            logger.error(f"Redis HGET 操作失败: {key}.{field}, {e}")
            return default
    
    async def hmget(self, key: str, *fields) -> Dict[str, Any]:
        """哈希表批量获取字段"""
        try:
            cache_key = get_cache_key(key)
            values = await self.client.hmget(cache_key, *fields)
            
            result = {}
            for field, value in zip(fields, values):
                if value is not None:
                    try:
                        result[field] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        result[field] = value.decode('utf-8') if isinstance(value, bytes) else value
                        
            return result
            
        except Exception as e:
            logger.error(f"Redis HMGET 操作失败: {key}, {e}")
            return {}
    
    async def hgetall(self, key: str) -> Dict[str, Any]:
        """哈希表获取所有字段"""
        try:
            cache_key = get_cache_key(key)
            hash_data = await self.client.hgetall(cache_key)
            
            result = {}
            for field, value in hash_data.items():
                field_name = field.decode('utf-8') if isinstance(field, bytes) else field
                try:
                    result[field_name] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    result[field_name] = value.decode('utf-8') if isinstance(value, bytes) else value
                    
            return result
            
        except Exception as e:
            logger.error(f"Redis HGETALL 操作失败: {key}, {e}")
            return {}


class DistributedLock:
    """分布式锁"""
    
    def __init__(
        self, 
        key: str, 
        timeout: int = 30, 
        client: Optional[redis.Redis] = None
    ):
        self.key = get_cache_key(f"lock:{key}")
        self.timeout = timeout
        self.client = client or redis_client
        self.identifier = None
    
    async def acquire(self) -> bool:
        """获取锁"""
        try:
            import uuid
            self.identifier = str(uuid.uuid4())
            
            result = await self.client.set(
                self.key, 
                self.identifier, 
                ex=self.timeout, 
                nx=True
            )
            return result is not None
            
        except Exception as e:
            logger.error(f"获取分布式锁失败: {self.key}, {e}")
            return False
    
    async def release(self) -> bool:
        """释放锁"""
        try:
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            result = await self.client.eval(lua_script, 1, self.key, self.identifier)
            return result == 1
            
        except Exception as e:
            logger.error(f"释放分布式锁失败: {self.key}, {e}")
            return False
    
    @asynccontextmanager
    async def lock(self):
        """上下文管理器方式使用锁"""
        acquired = await self.acquire()
        if not acquired:
            raise RuntimeError(f"无法获取锁: {self.key}")
        
        try:
            yield
        finally:
            await self.release()


class CacheDecorator:
    """缓存装饰器"""
    
    def __init__(
        self, 
        key_pattern: str, 
        ttl: int = None, 
        cache_client: Optional[RedisCache] = None
    ):
        self.key_pattern = key_pattern
        self.ttl = ttl or settings.CACHE_TTL
        self.cache = cache_client or RedisCache()
    
    def __call__(self, func):
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = self.key_pattern.format(*args, **kwargs)
            
            # 尝试从缓存获取
            cached_result = await self.cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 缓存结果
            await self.cache.set(cache_key, result, self.ttl)
            
            return result
        
        return wrapper


# 全局缓存实例
cache = None


def get_cache() -> RedisCache:
    """获取缓存实例"""
    global cache
    if not cache:
        cache = RedisCache()
    return cache


# Redis 健康检查
async def check_redis_health() -> dict:
    """检查 Redis 连接健康状态"""
    try:
        await redis_client.ping()
        return {
            "status": "healthy",
            "error": None
        }
    except Exception as e:
        logger.error(f"Redis 健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
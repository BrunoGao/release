"""
Redis 客户端封装
提供高级 Redis 操作接口
"""

import json
import pickle
from typing import Any, Optional, Union, Dict, List
import redis.asyncio as redis
from contextlib import asynccontextmanager
import logging

from app.core.cache import get_cache, redis_client
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RedisClient:
    """Redis 客户端高级封装"""
    
    def __init__(self, client: Optional[redis.Redis] = None):
        self.client = client or redis_client
        if not self.client:
            raise RuntimeError("Redis 客户端未初始化")
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            await self.client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis 健康检查失败: {e}")
            return False
    
    # String 操作
    async def set_string(
        self, 
        key: str, 
        value: str, 
        ttl: Optional[int] = None
    ) -> bool:
        """设置字符串值"""
        try:
            if ttl:
                return await self.client.setex(key, ttl, value)
            else:
                return await self.client.set(key, value)
        except Exception as e:
            logger.error(f"设置字符串失败 {key}: {e}")
            return False
    
    async def get_string(self, key: str, default: str = None) -> Optional[str]:
        """获取字符串值"""
        try:
            value = await self.client.get(key)
            if value is None:
                return default
            return value.decode('utf-8') if isinstance(value, bytes) else value
        except Exception as e:
            logger.error(f"获取字符串失败 {key}: {e}")
            return default
    
    # JSON 操作
    async def set_json(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """设置 JSON 值"""
        try:
            json_value = json.dumps(value, ensure_ascii=False, default=str)
            return await self.set_string(key, json_value, ttl)
        except Exception as e:
            logger.error(f"设置JSON失败 {key}: {e}")
            return False
    
    async def get_json(self, key: str, default: Any = None) -> Any:
        """获取 JSON 值"""
        try:
            value = await self.get_string(key)
            if value is None:
                return default
            return json.loads(value)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"解析JSON失败 {key}: {e}")
            return default
    
    # Hash 操作
    async def hset_json(self, key: str, field: str, value: Any) -> bool:
        """设置哈希表 JSON 字段"""
        try:
            json_value = json.dumps(value, ensure_ascii=False, default=str)
            result = await self.client.hset(key, field, json_value)
            return result > 0
        except Exception as e:
            logger.error(f"设置哈希JSON失败 {key}.{field}: {e}")
            return False
    
    async def hget_json(self, key: str, field: str, default: Any = None) -> Any:
        """获取哈希表 JSON 字段"""
        try:
            value = await self.client.hget(key, field)
            if value is None:
                return default
            
            value_str = value.decode('utf-8') if isinstance(value, bytes) else value
            return json.loads(value_str)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"解析哈希JSON失败 {key}.{field}: {e}")
            return default
    
    async def hmset_json(self, key: str, mapping: Dict[str, Any]) -> bool:
        """批量设置哈希表 JSON 字段"""
        try:
            json_mapping = {
                field: json.dumps(value, ensure_ascii=False, default=str)
                for field, value in mapping.items()
            }
            return await self.client.hmset(key, json_mapping)
        except Exception as e:
            logger.error(f"批量设置哈希JSON失败 {key}: {e}")
            return False
    
    async def hgetall_json(self, key: str) -> Dict[str, Any]:
        """获取哈希表所有 JSON 字段"""
        try:
            hash_data = await self.client.hgetall(key)
            result = {}
            
            for field, value in hash_data.items():
                field_name = field.decode('utf-8') if isinstance(field, bytes) else field
                value_str = value.decode('utf-8') if isinstance(value, bytes) else value
                
                try:
                    result[field_name] = json.loads(value_str)
                except (json.JSONDecodeError, TypeError):
                    result[field_name] = value_str
                    
            return result
        except Exception as e:
            logger.error(f"获取哈希表JSON失败 {key}: {e}")
            return {}
    
    # List 操作
    async def lpush_json(self, key: str, *values: Any) -> int:
        """从左侧推入 JSON 值到列表"""
        try:
            json_values = [
                json.dumps(value, ensure_ascii=False, default=str)
                for value in values
            ]
            return await self.client.lpush(key, *json_values)
        except Exception as e:
            logger.error(f"列表推入JSON失败 {key}: {e}")
            return 0
    
    async def rpop_json(self, key: str, default: Any = None) -> Any:
        """从右侧弹出 JSON 值"""
        try:
            value = await self.client.rpop(key)
            if value is None:
                return default
            
            value_str = value.decode('utf-8') if isinstance(value, bytes) else value
            return json.loads(value_str)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"解析列表JSON失败 {key}: {e}")
            return default
    
    async def lrange_json(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        """获取列表范围内的 JSON 值"""
        try:
            values = await self.client.lrange(key, start, end)
            result = []
            
            for value in values:
                value_str = value.decode('utf-8') if isinstance(value, bytes) else value
                try:
                    result.append(json.loads(value_str))
                except (json.JSONDecodeError, TypeError):
                    result.append(value_str)
                    
            return result
        except Exception as e:
            logger.error(f"获取列表JSON失败 {key}: {e}")
            return []
    
    # Set 操作
    async def sadd_json(self, key: str, *values: Any) -> int:
        """添加 JSON 值到集合"""
        try:
            json_values = [
                json.dumps(value, ensure_ascii=False, default=str)
                for value in values
            ]
            return await self.client.sadd(key, *json_values)
        except Exception as e:
            logger.error(f"集合添加JSON失败 {key}: {e}")
            return 0
    
    async def smembers_json(self, key: str) -> List[Any]:
        """获取集合所有 JSON 成员"""
        try:
            members = await self.client.smembers(key)
            result = []
            
            for member in members:
                member_str = member.decode('utf-8') if isinstance(member, bytes) else member
                try:
                    result.append(json.loads(member_str))
                except (json.JSONDecodeError, TypeError):
                    result.append(member_str)
                    
            return result
        except Exception as e:
            logger.error(f"获取集合JSON失败 {key}: {e}")
            return []
    
    # 通用操作
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"检查键存在失败 {key}: {e}")
            return False
    
    async def delete(self, *keys: str) -> int:
        """删除键"""
        try:
            return await self.client.delete(*keys)
        except Exception as e:
            logger.error(f"删除键失败 {keys}: {e}")
            return 0
    
    async def expire(self, key: str, ttl: int) -> bool:
        """设置键过期时间"""
        try:
            return await self.client.expire(key, ttl)
        except Exception as e:
            logger.error(f"设置过期时间失败 {key}: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """获取键剩余过期时间"""
        try:
            return await self.client.ttl(key)
        except Exception as e:
            logger.error(f"获取过期时间失败 {key}: {e}")
            return -1
    
    # 批量操作
    async def mget_json(self, *keys: str) -> Dict[str, Any]:
        """批量获取 JSON 值"""
        try:
            values = await self.client.mget(*keys)
            result = {}
            
            for key, value in zip(keys, values):
                if value is not None:
                    value_str = value.decode('utf-8') if isinstance(value, bytes) else value
                    try:
                        result[key] = json.loads(value_str)
                    except (json.JSONDecodeError, TypeError):
                        result[key] = value_str
                        
            return result
        except Exception as e:
            logger.error(f"批量获取JSON失败 {keys}: {e}")
            return {}
    
    async def mset_json(self, mapping: Dict[str, Any]) -> bool:
        """批量设置 JSON 值"""
        try:
            json_mapping = {
                key: json.dumps(value, ensure_ascii=False, default=str)
                for key, value in mapping.items()
            }
            return await self.client.mset(json_mapping)
        except Exception as e:
            logger.error(f"批量设置JSON失败: {e}")
            return False
    
    # 计数器操作
    async def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """递增计数器"""
        try:
            return await self.client.incrby(key, amount)
        except Exception as e:
            logger.error(f"递增计数器失败 {key}: {e}")
            return None
    
    async def decr(self, key: str, amount: int = 1) -> Optional[int]:
        """递减计数器"""
        try:
            return await self.client.decrby(key, amount)
        except Exception as e:
            logger.error(f"递减计数器失败 {key}: {e}")
            return None
    
    # 事务操作
    @asynccontextmanager
    async def pipeline(self):
        """Redis 管道操作上下文管理器"""
        pipe = self.client.pipeline()
        try:
            yield pipe
            await pipe.execute()
        except Exception as e:
            logger.error(f"管道操作失败: {e}")
            await pipe.reset()
            raise
    
    # 模式匹配
    async def keys(self, pattern: str) -> List[str]:
        """按模式获取键名"""
        try:
            keys = await self.client.keys(pattern)
            return [key.decode('utf-8') if isinstance(key, bytes) else key for key in keys]
        except Exception as e:
            logger.error(f"获取键名失败 {pattern}: {e}")
            return []
    
    async def scan_keys(self, pattern: str, count: int = 100) -> List[str]:
        """使用 SCAN 安全获取键名"""
        try:
            keys = []
            cursor = 0
            
            while True:
                cursor, batch_keys = await self.client.scan(cursor, match=pattern, count=count)
                keys.extend([key.decode('utf-8') if isinstance(key, bytes) else key for key in batch_keys])
                
                if cursor == 0:
                    break
                    
            return keys
        except Exception as e:
            logger.error(f"扫描键名失败 {pattern}: {e}")
            return []
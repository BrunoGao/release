# redis_helper.py
from redis import Redis, ConnectionPool
import json
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

class RedisHelper:
    def __init__(self, host=None, port=None, db=None, password=None):
        # 配置连接池参数
        pool_config = {
            'host': host or os.getenv('REDIS_HOST', '127.0.0.1'),
            'port': port or int(os.getenv('REDIS_PORT', 6379)),
            'db': db or int(os.getenv('REDIS_DB', 0)),
            'decode_responses': True,
            'max_connections': 20,  # 连接池最大连接数
            'socket_connect_timeout': 5,  # 连接超时
            'socket_timeout': 5,  # 读写超时
            'retry_on_timeout': True,  # 超时重试
            'health_check_interval': 30,  # 健康检查间隔
        }
        
        # 只有当密码存在且不为空时才添加密码配置
        redis_password = password or os.getenv('REDIS_PASSWORD')
        if redis_password and redis_password.strip():
            pool_config['password'] = redis_password
        
        # 创建连接池
        self.pool = ConnectionPool(**pool_config)
        self.client = Redis(connection_pool=self.pool)
        self.redis_client = self.client  # 兼容性别名

    def set_data(self, key, data, expire=None):
        """设置数据（带异常处理）"""
        try:
            return self.client.set(key, json.dumps(data), ex=expire)
        except Exception as e:
            logging.warning(f"Redis set_data 失败: {e}")
            return False

    def get_data(self, key):
        """获取数据（带异常处理）"""
        try:
            data = self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logging.warning(f"Redis get_data 失败: {e}")
            return None

    def hset_data(self, key, mapping):
        """设置哈希数据（带异常处理和NoneType安全处理）"""
        try:
            # 🔧 修复：过滤和转换NoneType值
            safe_mapping = {}
            for k, v in mapping.items():
                if v is not None:
                    if isinstance(v, (str, int, float, bytes)):
                        safe_mapping[k] = v
                    else:
                        safe_mapping[k] = str(v)  # 转换为字符串
                else:
                    safe_mapping[k] = ''  # None值转为空字符串
            
            return self.client.hset(key, mapping=safe_mapping)
        except Exception as e:
            logging.warning(f"Redis hset_data 失败: {e}：")
            return False

    def hgetall_data(self, key):
        """获取哈希数据（带异常处理）"""
        try:
            return self.client.hgetall(key)
        except Exception as e:
            logging.warning(f"Redis hgetall_data 失败: {e}")
            return {}

    def publish(self, channel, message):
        """发布消息（带异常处理）"""
        try:
            return self.client.publish(channel, message)
        except Exception as e:
            logging.warning(f"Redis publish 失败: {e}")
            return 0
        
    def pubsub(self):
        """创建订阅对象"""
        return self.client.pubsub()
    
    def exists(self, key):
        """检查键是否存在（带异常处理）"""
        try:
            return self.client.exists(key)
        except Exception as e:
            logging.warning(f"Redis exists 失败: {e}")
            return False
    
    def delete(self, key):
        """删除键（带异常处理）"""
        try:
            return self.client.delete(key)
        except Exception as e:
            logging.warning(f"Redis delete 失败: {e}")
            return 0
    
    def type(self, key):
        """获取键类型（带异常处理）"""
        try:
            return self.client.type(key)
        except Exception as e:
            logging.warning(f"Redis type 失败: {e}")
            return 'none'
    
    def hgetall(self, key):
        """获取哈希所有字段（带异常处理）"""
        try:
            return self.client.hgetall(key)
        except Exception as e:
            logging.warning(f"Redis hgetall 失败: {e}")
            return {}
    
    def set(self, key, value, ex=None):
        """设置键值（带异常处理）"""
        try:
            return self.client.set(key, value, ex=ex)
        except Exception as e:
            logging.warning(f"Redis set 失败: {e}")
            return False
    
    def get(self, key):
        """获取键值（带异常处理）"""
        try:
            return self.client.get(key)
        except Exception as e:
            logging.warning(f"Redis get 失败: {e}")
            return None
    
    def hset(self, key, mapping):
        """设置哈希字段（带异常处理）"""
        try:
            return self.client.hset(key, mapping=mapping)
        except Exception as e:
            logging.warning(f"Redis hset 失败: {e}")
            return False
    
    def setex(self, name, time, value):
        """设置键值对并指定过期时间（秒）（带异常处理）"""
        try:
            return self.client.setex(name, time, value)
        except Exception as e:
            logging.warning(f"Redis setex 失败: {e}")
            return False
    
    def ping(self):
        """检查连接状态"""
        try:
            return self.client.ping()
        except Exception as e:
            logging.error(f"Redis ping 失败: {e}")
            return False
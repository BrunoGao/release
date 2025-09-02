#!/usr/bin/env python3
"""Redis统一配置管理"""
import os
from redis import Redis
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class RedisConfig:
    """Redis配置类 - 统一管理Redis连接参数"""
    
    def __init__(self):
        # 从环境变量或配置文件获取Redis配置
        self.host = os.getenv('REDIS_HOST', '127.0.0.1')
        self.port = int(os.getenv('REDIS_PORT', 6379))
        self.db = int(os.getenv('REDIS_DB', 0))
        self.password = os.getenv('REDIS_PASSWORD', '123456')
        self.decode_responses = True
        self.socket_timeout = 30
        self.socket_connect_timeout = 30
        self.retry_on_timeout = True
        
    def get_client(self):
        """获取Redis客户端实例"""
        return Redis(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password,
            decode_responses=self.decode_responses,
            socket_timeout=self.socket_timeout,
            socket_connect_timeout=self.socket_connect_timeout,
            retry_on_timeout=self.retry_on_timeout
        )
    
    def get_pubsub_client(self):
        """获取Redis PubSub客户端实例"""
        client = self.get_client()
        return client.pubsub()
    
    def test_connection(self):
        """测试Redis连接"""
        try:
            client = self.get_client()
            client.ping()
            return True, "Redis连接成功"
        except Exception as e:
            return False, f"Redis连接失败: {str(e)}"
    
    def __str__(self):
        return f"Redis({self.host}:{self.port}/{self.db})"

# 全局Redis配置实例
redis_config = RedisConfig()

def get_redis_client():
    """获取Redis客户端的便捷函数"""
    return redis_config.get_client()

def get_redis_pubsub():
    """获取Redis PubSub客户端的便捷函数"""
    return redis_config.get_pubsub_client()

def test_redis_connection():
    """测试Redis连接的便捷函数"""
    return redis_config.test_connection()

if __name__ == "__main__":
    # 测试脚本
    print("🔧 Redis配置测试")
    print(f"配置: {redis_config}")
    
    success, message = test_redis_connection()
    if success:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}") 
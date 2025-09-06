#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LJWX系统配置加载器
统一配置管理，支持YAML配置文件和环境变量覆盖
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class LJWXConfigLoader:
    """LJWX配置加载器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置加载器
        
        Args:
            config_path: 配置文件路径，默认为当前目录下的ljwx-config.yaml
        """
        if config_path is None:
            # 尝试多个可能的配置文件位置
            possible_paths = [
                "/app/config/ljwx-config.yaml",  # 容器内路径
                "/client/config/ljwx-config.yaml",  # 挂载路径
                os.path.join(os.path.dirname(__file__), "ljwx-config.yaml"),  # 同级目录
                "client/config/ljwx-config.yaml",  # 相对路径
                "config/ljwx-config.yaml"  # 简化路径
            ]
            
            config_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    config_path = path
                    break
            
            if config_path is None:
                raise FileNotFoundError("配置文件未找到，请确保ljwx-config.yaml存在")
        
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 环境变量覆盖
            config = self._apply_env_overrides(config)
            
            return config
        except Exception as e:
            raise Exception(f"加载配置文件失败: {e}")
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """应用环境变量覆盖"""
        # 数据库配置覆盖
        if 'MYSQL_HOST' in os.environ:
            config['database']['mysql']['host'] = os.environ['MYSQL_HOST']
        if 'MYSQL_PORT' in os.environ:
            config['database']['mysql']['port'] = int(os.environ['MYSQL_PORT'])
        if 'MYSQL_DATABASE' in os.environ:
            config['database']['mysql']['database'] = os.environ['MYSQL_DATABASE']
        if 'MYSQL_USERNAME' in os.environ:
            config['database']['mysql']['username'] = os.environ['MYSQL_USERNAME']
        if 'MYSQL_PASSWORD' in os.environ:
            config['database']['mysql']['password'] = os.environ['MYSQL_PASSWORD']
        
        if 'REDIS_HOST' in os.environ:
            config['database']['redis']['host'] = os.environ['REDIS_HOST']
        if 'REDIS_PORT' in os.environ:
            config['database']['redis']['port'] = int(os.environ['REDIS_PORT'])
        if 'REDIS_PASSWORD' in os.environ:
            config['database']['redis']['password'] = os.environ['REDIS_PASSWORD']
        
        # 服务端口覆盖
        if 'SERVER_PORT' in os.environ:
            service_name = os.environ.get('SERVICE_NAME', 'ljwx-boot')
            if service_name in config['services']:
                config['services'][service_name]['port'] = int(os.environ['SERVER_PORT'])
        
        return config
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值，支持点号分隔的嵌套键
        
        Args:
            key: 配置键，如 'database.mysql.host'
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_database_config(self, db_type: str = 'mysql') -> Dict[str, Any]:
        """获取数据库配置"""
        return self.get(f'database.{db_type}', {})
    
    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """获取服务配置"""
        return self.get(f'services.{service_name}', {})
    
    def get_image_config(self) -> Dict[str, str]:
        """获取镜像配置"""
        return self.get('images', {})
    
    def get_database_url(self, db_type: str = 'mysql') -> str:
        """获取数据库连接URL"""
        db_config = self.get_database_config(db_type)
        
        if db_type == 'mysql':
            return f"mysql+pymysql://{db_config['username']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}?charset={db_config.get('charset', 'utf8mb4')}"
        elif db_type == 'redis':
            password_part = f":{db_config['password']}@" if db_config.get('password') else ""
            return f"redis://{password_part}{db_config['host']}:{db_config['port']}/{db_config.get('db', 0)}"
        
        return ""
    
    def reload(self):
        """重新加载配置"""
        self.config = self._load_config()


# 全局配置实例
_config_loader = None

def get_config() -> LJWXConfigLoader:
    """获取全局配置实例"""
    global _config_loader
    if _config_loader is None:
        _config_loader = LJWXConfigLoader()
    return _config_loader

def reload_config():
    """重新加载全局配置"""
    global _config_loader
    if _config_loader is not None:
        _config_loader.reload()

# 便捷函数
def get_database_config(db_type: str = 'mysql') -> Dict[str, Any]:
    """获取数据库配置"""
    return get_config().get_database_config(db_type)

def get_service_config(service_name: str) -> Dict[str, Any]:
    """获取服务配置"""
    return get_config().get_service_config(service_name)

def get_database_url(db_type: str = 'mysql') -> str:
    """获取数据库连接URL"""
    return get_config().get_database_url(db_type)


if __name__ == "__main__":
    # 测试配置加载
    config = get_config()
    
    print("=== LJWX配置测试 ===")
    print(f"系统名称: {config.get('system.name')}")
    print(f"系统版本: {config.get('system.version')}")
    print()
    
    print("=== 数据库配置 ===")
    mysql_config = get_database_config('mysql')
    print(f"MySQL: {mysql_config}")
    print(f"MySQL URL: {get_database_url('mysql')}")
    print()
    
    redis_config = get_database_config('redis')  
    print(f"Redis: {redis_config}")
    print(f"Redis URL: {get_database_url('redis')}")
    print()
    
    print("=== 服务配置 ===")
    for service in ['ljwx-admin', 'ljwx-bigscreen', 'ljwx-boot']:
        service_config = get_service_config(service)
        print(f"{service}: {service_config}")
    print()
    
    print("=== 镜像配置 ===")
    image_config = config.get_image_config()
    print(f"镜像仓库: {image_config.get('registry')}")
    print(f"Admin镜像: {image_config.get('ljwx-admin')}")
    print(f"Bigscreen镜像: {image_config.get('ljwx-bigscreen')}")
    print(f"Boot镜像: {image_config.get('ljwx-boot')}")
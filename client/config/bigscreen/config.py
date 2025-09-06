# ljwx-bigscreen配置文件
# 由generate-config.sh自动生成

# 从统一配置加载
import sys
import os
sys.path.append('/app/config')
sys.path.append('/client/config')

try:
    from config_loader import get_database_config, get_service_config, get_config
    
    # 数据库配置
    MYSQL_CONFIG = get_database_config('mysql')
    REDIS_CONFIG = get_database_config('redis')
    
    # 服务配置
    SERVICE_CONFIG = get_service_config('ljwx-bigscreen')
    
    # 应用配置
    APP_CONFIG = {
        'HOST': '0.0.0.0',
        'PORT': SERVICE_CONFIG.get('port', 8001),
        'DEBUG': False,
        'SECRET_KEY': get_config().get('security.jwt_secret', 'ljwx-secret'),
    }
    
except ImportError:
    # 备用静态配置
    MYSQL_CONFIG = {
        'host': 'ljwx-mysql',
        'port': 3306,
        'database': 'test',
        'username': 'ljwx',
        'password': '123456'
    }
    
    REDIS_CONFIG = {
        'host': 'ljwx-redis',
        'port': 6379,
        'password': '',
        'db': 0
    }
    
    APP_CONFIG = {
        'HOST': '0.0.0.0',
        'PORT': 8001,
        'DEBUG': False,
        'SECRET_KEY': 'ljwx-secret',
    }

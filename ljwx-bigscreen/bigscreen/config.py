import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Load environment variables
load_dotenv()

# Determine if running in Docker
IS_DOCKER = os.getenv('IS_DOCKER', 'false').lower() == 'true'

# Database configuration
MYSQL_HOST = os.getenv('MYSQL_HOST', 'ljwx-mysql')  #统一使用ljwx-mysql
MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'Ljwx2024!@#')  #正确密码
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'lj-06')  #正确数据库名

# Redis configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'ljwx-redis')  #统一使用ljwx-redis
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '123456')  # 添加Redis密码配置

# Application configuration
APP_HOST = os.getenv('APP_HOST', '0.0.0.0')
APP_PORT = int(os.getenv('APP_PORT', 5001))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# UI定制化配置 - 客户可通过环境变量或配置文件定制
BIGSCREEN_TITLE = os.getenv('BIGSCREEN_TITLE', '智能穿戴演示大屏')  # 大屏标题
COMPANY_NAME = os.getenv('COMPANY_NAME', '智能科技有限公司')  # 公司名称
COMPANY_LOGO_URL = os.getenv('COMPANY_LOGO_URL', '/static/images/logo.png')  # 公司Logo路径
THEME_COLOR = os.getenv('THEME_COLOR', '#1890ff')  # 主题色
BACKGROUND_COLOR = os.getenv('BACKGROUND_COLOR', '#0a0e27')  # 背景色
FOOTER_TEXT = os.getenv('FOOTER_TEXT', '© 2024 智能科技有限公司 版权所有')  # 页脚文字

# ==================== 微信告警配置 ====================
# 微信配置 - 客户可通过环境变量定制
WECHAT_APP_ID = os.getenv('WECHAT_APP_ID', 'your_app_id_here')
WECHAT_APP_SECRET = os.getenv('WECHAT_APP_SECRET', 'your_app_secret_here')
WECHAT_TEMPLATE_ID = os.getenv('WECHAT_TEMPLATE_ID', 'your_template_id_here')
WECHAT_USER_OPENID = os.getenv('WECHAT_USER_OPENID', 'your_openid_here')
WECHAT_API_URL = os.getenv('WECHAT_API_URL', 'https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={ACCESS_TOKEN}')
WECHAT_ALERT_ENABLED = os.getenv('WECHAT_ALERT_ENABLED', 'false').lower() == 'true'  # 默认禁用微信告警

# ==================== 企业微信配置 ====================
# 企业微信配置 - 客户可通过环境变量定制
CORP_ID = os.getenv('CORP_ID', 'your_corp_id_here')
CORP_SECRET = os.getenv('CORP_SECRET', 'your_corp_secret_here')
CORP_AGENT_ID = int(os.getenv('CORP_AGENT_ID', '0'))
CORP_API_URL = os.getenv('CORP_API_URL', 'https://qyapi.weixin.qq.com')
CORP_WECHAT_ENABLED = os.getenv('CORP_WECHAT_ENABLED', 'false').lower() == 'true'  # 默认禁用企业微信告警
CORP_WECHAT_TOUSER = os.getenv('CORP_WECHAT_TOUSER', '@all')  # 企业微信消息接收用户

# Build database URI with proper password encoding
encoded_password = quote_plus(MYSQL_PASSWORD)
SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI', 
    f"mysql+pymysql://{MYSQL_USER}:{encoded_password}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}")

# 压力测试配置文件
STRESS_TEST_CONFIG = {
    'URL': 'http://localhost:5001/upload_health_data',  # 目标接口
    'BASE_ID': 'A5GTQ24B26000732',  # 基础设备ID
    'DEVICE_COUNT': 500,  # 设备数量(降低避免积压)
    'INTERVAL': 5,  # 上传间隔秒数
    'MAX_WORKERS': 50,  # 并发线程数
    'TIMEOUT': 10,  # 请求超时时间
    'TARGET_QPS': 200,  # 目标QPS
    'QUEUE_SIZE': 10000,  # 队列最大长度
}

# MySQL监控配置
MYSQL_CONFIG = {
    'host': MYSQL_HOST,
    'user': MYSQL_USER, 
    'password': MYSQL_PASSWORD,
    'db': MYSQL_DATABASE,
    'port': MYSQL_PORT,
    'charset': 'utf8mb4'
}

# 数据库连接池配置
DB_POOL_CONFIG = {
    'pool_size': 30,  # 增加连接池大小
    'max_overflow': 50,  # 增加最大溢出连接
    'pool_timeout': 30,  # 连接超时
    'pool_recycle': 3600,  # 连接回收时间
    'pool_pre_ping': True,  # 预检查连接
    'echo': False,  # 关闭SQL日志
}

# 性能优化配置
PERFORMANCE_CONFIG = {
    'batch_size': 200,  # 增加批处理大小
    'batch_timeout': 3,  # 批处理超时
    'async_workers': 20,  # 增加异步工作线程
    'redis_pipeline_size': 100,  # 增加Redis管道大小
    'enable_compression': True,  # 启用压缩
    'connection_retry': 3,  # 连接重试次数
    'operation_timeout': 10,  # 操作超时时间
}

# 健康数据范围配置
HEALTH_DATA_RANGES = {
    'heart_rate': (60, 120),  # 心率范围
    'blood_oxygen': (95, 100),  # 血氧范围
    'body_temperature': (36.0, 37.5),  # 体温范围
    'blood_pressure_systolic': (110, 140),  # 收缩压
    'blood_pressure_diastolic': (70, 90),  # 舒张压
    'step': (800, 1500),  # 步数范围
    'distance': (500, 1000),  # 距离范围
    'calorie': (40000, 50000),  # 卡路里范围
    'latitude': (22.5, 22.6),  # 纬度范围(深圳)
    'longitude': (114.0, 114.3),  # 经度范围(深圳)
    'stress': (30, 80),  # 压力值范围
}

# Redis URL配置 - 支持Redis 8.x认证
REDIS_URL = f"redis://default:{quote_plus(REDIS_PASSWORD)}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# SQLAlchemy连接字符串
SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{quote_plus(MYSQL_PASSWORD)}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"

class Config:
    """应用配置类"""
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Redis配置
    REDIS_URL = REDIS_URL
    REDIS_HOST = REDIS_HOST
    REDIS_PORT = REDIS_PORT
    REDIS_DB = REDIS_DB
    REDIS_PASSWORD = REDIS_PASSWORD
    
    # 应用配置
    APP_HOST = APP_HOST
    APP_PORT = APP_PORT
    DEBUG = DEBUG
    
    # 微信配置
    WECHAT_APP_ID = WECHAT_APP_ID
    WECHAT_APP_SECRET = WECHAT_APP_SECRET
    WECHAT_ALERT_ENABLED = WECHAT_ALERT_ENABLED
    
    # 性能配置
    PERFORMANCE_CONFIG = PERFORMANCE_CONFIG
    DB_POOL_CONFIG = DB_POOL_CONFIG
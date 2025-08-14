import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Load environment variables
load_dotenv()

# Determine if running in Docker
IS_DOCKER = os.getenv('IS_DOCKER', 'false').lower() == 'true'

# Database configuration
MYSQL_HOST = os.getenv('MYSQL_HOST', 'mysql' if IS_DOCKER else '127.0.0.1')
MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '123456')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'lj-06')

# Redis configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'redis' if IS_DOCKER else '127.0.0.1')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '123456')  # 添加Redis密码配置

# Application configuration
APP_HOST = os.getenv('APP_HOST', '0.0.0.0')
APP_PORT = int(os.getenv('APP_PORT', 8001))  # 默认端口改为8001
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# UI configuration - 可配置的大屏标题
BIGSCREEN_TITLE = os.getenv('BIGSCREEN_TITLE', '智能穿戴演示大屏')  # 大屏标题可配置
COMPANY_NAME = os.getenv('COMPANY_NAME', '智能科技有限公司')  # 公司名称
COMPANY_LOGO_URL = os.getenv('COMPANY_LOGO_URL', '/static/images/logo.png')  # 公司Logo路径
THEME_COLOR = os.getenv('THEME_COLOR', '#1890ff')  # 主题色
BACKGROUND_COLOR = os.getenv('BACKGROUND_COLOR', '#0a0e27')  # 背景色
FOOTER_TEXT = os.getenv('FOOTER_TEXT', '© 2024 智能科技有限公司 版权所有')  # 页脚文字

# Build database URI with proper password encoding
encoded_password = quote_plus(MYSQL_PASSWORD)
SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI', 
    f"mysql+pymysql://{MYSQL_USER}:{encoded_password}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}")

# 压力测试配置文件
STRESS_TEST_CONFIG = {
    'URL': f'http://localhost:{APP_PORT}/upload_health_data',  # 使用动态端口
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
    'pool_size': 20,  # 连接池大小
    'max_overflow': 30,  # 最大溢出连接
    'pool_timeout': 30,  # 连接超时
    'pool_recycle': 3600,  # 连接回收时间
    'pool_pre_ping': True,  # 预检查连接
}

# 性能优化配置
PERFORMANCE_CONFIG = {
    'batch_size': 100,  # 批处理大小
    'batch_timeout': 2,  # 批处理超时
    'async_workers': 10,  # 异步工作线程
    'redis_pipeline_size': 50,  # Redis管道大小
    'enable_compression': True,  # 启用压缩
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

# 微信企业号配置
CORP_ID = os.getenv('CORP_ID', 'your_corp_id')
CORP_SECRET = os.getenv('CORP_SECRET', 'your_corp_secret')
CORP_AGENT_ID = os.getenv('CORP_AGENT_ID', 'your_agent_id')
CORP_API_URL = os.getenv('CORP_API_URL', 'https://qyapi.weixin.qq.com')
CORP_WECHAT_ENABLED = os.getenv('CORP_WECHAT_ENABLED', 'false').lower() == 'true'
CORP_WECHAT_TOUSER = os.getenv('CORP_WECHAT_TOUSER', '@all')

# 微信公众号配置
WECHAT_APP_ID = os.getenv('WECHAT_APP_ID', 'your_app_id')
WECHAT_APP_SECRET = os.getenv('WECHAT_APP_SECRET', 'your_app_secret')
WECHAT_TEMPLATE_ID = os.getenv('WECHAT_TEMPLATE_ID', 'your_template_id')
WECHAT_USER_OPENID = os.getenv('WECHAT_USER_OPENID', 'your_openid')
WECHAT_API_URL = os.getenv('WECHAT_API_URL', 'https://api.weixin.qq.com')
WECHAT_ALERT_ENABLED = os.getenv('WECHAT_ALERT_ENABLED', 'false').lower() == 'true' 
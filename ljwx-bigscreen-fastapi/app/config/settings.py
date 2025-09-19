"""
应用配置管理
支持多环境配置，环境变量覆盖
"""

from pydantic import BaseSettings, Field, validator
from typing import List, Optional
import os


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基础配置
    APP_NAME: str = "LJWX BigScreen FastAPI"
    VERSION: str = "2.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    WORKERS: int = Field(default=4, env="WORKERS")
    
    # 安全配置
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # CORS 配置
    ALLOWED_HOSTS: List[str] = Field(
        default=["*"], 
        env="ALLOWED_HOSTS"
    )
    
    @validator("ALLOWED_HOSTS", pre=True)
    def parse_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split(",")]
        return v
    
    # 数据库配置
    # MySQL 主库
    DB_HOST: str = Field(..., env="DB_HOST")
    DB_PORT: int = Field(default=3306, env="DB_PORT")
    DB_USER: str = Field(..., env="DB_USER")
    DB_PASSWORD: str = Field(..., env="DB_PASSWORD")
    DB_NAME: str = Field(..., env="DB_NAME")
    DB_CHARSET: str = Field(default="utf8mb4", env="DB_CHARSET")
    
    # MySQL 从库 (读写分离)
    DB_READ_HOST: Optional[str] = Field(default=None, env="DB_READ_HOST")
    DB_READ_PORT: Optional[int] = Field(default=None, env="DB_READ_PORT")
    DB_READ_USER: Optional[str] = Field(default=None, env="DB_READ_USER")
    DB_READ_PASSWORD: Optional[str] = Field(default=None, env="DB_READ_PASSWORD")
    
    # 数据库连接池配置
    DB_POOL_SIZE: int = Field(default=20, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=30, env="DB_MAX_OVERFLOW")
    DB_POOL_TIMEOUT: int = Field(default=30, env="DB_POOL_TIMEOUT")
    DB_POOL_RECYCLE: int = Field(default=3600, env="DB_POOL_RECYCLE")
    
    @property
    def DATABASE_URL(self) -> str:
        """主数据库连接URL"""
        return (
            f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?charset={self.DB_CHARSET}"
        )
    
    @property
    def DATABASE_READ_URL(self) -> Optional[str]:
        """从数据库连接URL"""
        if not self.DB_READ_HOST:
            return None
        
        read_user = self.DB_READ_USER or self.DB_USER
        read_password = self.DB_READ_PASSWORD or self.DB_PASSWORD
        read_port = self.DB_READ_PORT or self.DB_PORT
        
        return (
            f"mysql+aiomysql://{read_user}:{read_password}"
            f"@{self.DB_READ_HOST}:{read_port}/{self.DB_NAME}"
            f"?charset={self.DB_CHARSET}"
        )
    
    # Redis 配置
    REDIS_HOST: str = Field(..., env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    REDIS_POOL_SIZE: int = Field(default=20, env="REDIS_POOL_SIZE")
    
    # Redis 缓存配置
    CACHE_TTL: int = Field(default=300, env="CACHE_TTL")  # 5分钟
    CACHE_KEY_PREFIX: str = Field(default="ljwx:bigscreen:", env="CACHE_KEY_PREFIX")
    
    @property
    def REDIS_URL(self) -> str:
        """Redis 连接URL"""
        auth_part = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth_part}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # Celery 任务队列配置
    CELERY_BROKER_URL: str = Field(..., env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(..., env="CELERY_RESULT_BACKEND")
    
    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: Optional[str] = Field(default=None, env="LOG_FILE")
    LOG_MAX_SIZE: int = Field(default=100*1024*1024, env="LOG_MAX_SIZE")  # 100MB
    LOG_BACKUP_COUNT: int = Field(default=5, env="LOG_BACKUP_COUNT")
    
    # 监控配置
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    METRICS_PORT: int = Field(default=9090, env="METRICS_PORT")
    
    # 文件上传配置
    UPLOAD_DIR: str = Field(default="uploads", env="UPLOAD_DIR")
    MAX_UPLOAD_SIZE: int = Field(default=10*1024*1024, env="MAX_UPLOAD_SIZE")  # 10MB
    ALLOWED_EXTENSIONS: List[str] = Field(
        default=["jpg", "jpeg", "png", "gif", "pdf", "doc", "docx", "xls", "xlsx"],
        env="ALLOWED_EXTENSIONS"
    )
    
    @validator("ALLOWED_EXTENSIONS", pre=True)
    def parse_allowed_extensions(cls, v):
        if isinstance(v, str):
            return [x.strip().lower() for x in v.split(",")]
        return v
    
    # API 限流配置
    RATE_LIMIT_PER_MINUTE: int = Field(default=100, env="RATE_LIMIT_PER_MINUTE")
    RATE_LIMIT_BURST: int = Field(default=20, env="RATE_LIMIT_BURST")
    
    # 健康数据处理配置
    HEALTH_DATA_BATCH_SIZE: int = Field(default=1000, env="HEALTH_DATA_BATCH_SIZE")
    HEALTH_DATA_PROCESS_INTERVAL: int = Field(default=60, env="HEALTH_DATA_PROCESS_INTERVAL")
    
    # 告警配置
    ALERT_PROCESS_INTERVAL: int = Field(default=30, env="ALERT_PROCESS_INTERVAL")
    ALERT_MAX_RETRIES: int = Field(default=3, env="ALERT_MAX_RETRIES")
    
    # 消息推送配置
    MESSAGE_PUSH_ENABLED: bool = Field(default=True, env="MESSAGE_PUSH_ENABLED")
    MESSAGE_BATCH_SIZE: int = Field(default=100, env="MESSAGE_BATCH_SIZE")
    
    # 微信配置
    WECHAT_APP_ID: Optional[str] = Field(default=None, env="WECHAT_APP_ID")
    WECHAT_APP_SECRET: Optional[str] = Field(default=None, env="WECHAT_APP_SECRET")
    WECHAT_TOKEN: Optional[str] = Field(default=None, env="WECHAT_TOKEN")
    
    # 邮件配置
    SMTP_HOST: Optional[str] = Field(default=None, env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USER: Optional[str] = Field(default=None, env="SMTP_USER")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    SMTP_TLS: bool = Field(default=True, env="SMTP_TLS")
    
    # 外部服务配置
    EXTERNAL_API_TIMEOUT: int = Field(default=30, env="EXTERNAL_API_TIMEOUT")
    EXTERNAL_API_RETRIES: int = Field(default=3, env="EXTERNAL_API_RETRIES")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


class DevelopmentSettings(Settings):
    """开发环境配置"""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    
    class Config(Settings.Config):
        env_file = ".env.dev"


class ProductionSettings(Settings):
    """生产环境配置"""
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    class Config(Settings.Config):
        env_file = ".env.prod"


class TestingSettings(Settings):
    """测试环境配置"""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    DB_NAME: str = "ljwx_test"
    
    class Config(Settings.Config):
        env_file = ".env.test"


def get_settings() -> Settings:
    """获取当前环境配置"""
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    if environment == "production":
        return ProductionSettings()
    elif environment == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()


# 全局配置实例
settings = get_settings()
"""
数据库连接管理
支持异步操作、连接池、读写分离
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession, 
    create_async_engine, 
    async_sessionmaker
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import QueuePool
from sqlalchemy import event
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
import logging

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# SQLAlchemy Base
Base = declarative_base()

# 数据库引擎
write_engine = None
read_engine = None
SessionLocal = None
ReadSessionLocal = None


def create_engine_with_config(database_url: str, is_read_only: bool = False):
    """创建数据库引擎"""
    engine_config = {
        "poolclass": QueuePool,
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_timeout": settings.DB_POOL_TIMEOUT,
        "pool_recycle": settings.DB_POOL_RECYCLE,
        "pool_pre_ping": True,  # 连接前预检查
        "echo": settings.DEBUG,  # 开发环境下显示SQL
    }
    
    engine = create_async_engine(database_url, **engine_config)
    
    # 监听连接事件
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        """连接时设置数据库参数"""
        if not is_read_only:
            # 主库设置
            cursor = dbapi_connection.cursor()
            cursor.execute("SET SESSION sql_mode='STRICT_TRANS_TABLES'")
            cursor.execute("SET SESSION time_zone='+08:00'")
            cursor.close()
        else:
            # 从库设置
            cursor = dbapi_connection.cursor()
            cursor.execute("SET SESSION sql_mode='STRICT_TRANS_TABLES'")
            cursor.execute("SET SESSION time_zone='+08:00'")
            cursor.execute("SET SESSION transaction_read_only=1")
            cursor.close()
    
    return engine


async def init_db_pool():
    """初始化数据库连接池"""
    global write_engine, read_engine, SessionLocal, ReadSessionLocal
    
    # 创建写库引擎
    write_engine = create_engine_with_config(settings.DATABASE_URL)
    SessionLocal = async_sessionmaker(
        write_engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    # 创建读库引擎（如果配置了读写分离）
    if settings.DATABASE_READ_URL:
        read_engine = create_engine_with_config(
            settings.DATABASE_READ_URL, 
            is_read_only=True
        )
        ReadSessionLocal = async_sessionmaker(
            read_engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        logger.info("数据库读写分离已启用")
    else:
        # 没有配置读库，使用写库
        read_engine = write_engine
        ReadSessionLocal = SessionLocal
        logger.info("数据库读写分离未启用，使用单库模式")
    
    logger.info("数据库连接池初始化完成")


async def close_db_pool():
    """关闭数据库连接池"""
    global write_engine, read_engine
    
    if write_engine:
        await write_engine.dispose()
        logger.info("写库连接池已关闭")
    
    if read_engine and read_engine != write_engine:
        await read_engine.dispose()
        logger.info("读库连接池已关闭")


@asynccontextmanager
async def get_db_session(read_only: bool = False) -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话
    
    Args:
        read_only: 是否为只读操作，True时使用读库
    """
    session_maker = ReadSessionLocal if read_only else SessionLocal
    
    if not session_maker:
        raise RuntimeError("数据库连接池未初始化")
    
    async with session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


class DatabaseManager:
    """数据库管理器"""
    
    @staticmethod
    async def get_write_session() -> AsyncGenerator[AsyncSession, None]:
        """获取写数据库会话"""
        async with get_db_session(read_only=False) as session:
            yield session
    
    @staticmethod
    async def get_read_session() -> AsyncGenerator[AsyncSession, None]:
        """获取读数据库会话"""
        async with get_db_session(read_only=True) as session:
            yield session
    
    @staticmethod
    async def execute_in_transaction(func, *args, **kwargs):
        """在事务中执行函数"""
        async with get_db_session(read_only=False) as session:
            try:
                async with session.begin():
                    result = await func(session, *args, **kwargs)
                    return result
            except Exception:
                await session.rollback()
                raise


# 数据库依赖注入
async def get_write_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖注入 - 写数据库"""
    async with get_db_session(read_only=False) as session:
        yield session


async def get_read_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖注入 - 读数据库"""
    async with get_db_session(read_only=True) as session:
        yield session


# 数据库健康检查
async def check_database_health() -> dict:
    """检查数据库连接健康状态"""
    result = {
        "write_db": False,
        "read_db": False,
        "error": None
    }
    
    try:
        # 检查写库
        async with get_db_session(read_only=False) as session:
            await session.execute("SELECT 1")
            result["write_db"] = True
        
        # 检查读库
        async with get_db_session(read_only=True) as session:
            await session.execute("SELECT 1")
            result["read_db"] = True
            
    except Exception as e:
        result["error"] = str(e)
        logger.error(f"数据库健康检查失败: {e}")
    
    return result


# 数据库迁移辅助函数
async def create_tables():
    """创建所有表"""
    from app.models import *  # 导入所有模型
    
    async with write_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("数据库表创建完成")


async def drop_tables():
    """删除所有表"""
    async with write_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    logger.info("数据库表删除完成")
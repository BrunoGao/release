"""
MySQL 客户端封装
提供高级数据库操作接口
"""

from typing import Any, Dict, List, Optional, Union, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, insert, update, delete
from sqlalchemy.sql import Select, Insert, Update, Delete
from contextlib import asynccontextmanager
import logging

from app.core.database import get_db_session, DatabaseManager

logger = logging.getLogger(__name__)


class MySQLClient:
    """MySQL 客户端高级封装"""
    
    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session
    
    @asynccontextmanager
    async def get_session(self, read_only: bool = False):
        """获取数据库会话上下文管理器"""
        if self.session:
            yield self.session
        else:
            async with get_db_session(read_only=read_only) as session:
                yield session
    
    async def execute_query(
        self, 
        query: Union[str, Select], 
        params: Optional[Dict[str, Any]] = None,
        read_only: bool = True
    ) -> List[Dict[str, Any]]:
        """执行查询并返回结果"""
        try:
            async with self.get_session(read_only=read_only) as session:
                if isinstance(query, str):
                    result = await session.execute(text(query), params or {})
                else:
                    result = await session.execute(query, params or {})
                
                # 获取列名
                columns = result.keys()
                
                # 转换为字典列表
                rows = []
                for row in result.fetchall():
                    rows.append(dict(zip(columns, row)))
                
                return rows
                
        except Exception as e:
            logger.error(f"查询执行失败: {e}")
            raise
    
    async def execute_scalar(
        self, 
        query: Union[str, Select], 
        params: Optional[Dict[str, Any]] = None,
        read_only: bool = True
    ) -> Any:
        """执行查询并返回单个值"""
        try:
            async with self.get_session(read_only=read_only) as session:
                if isinstance(query, str):
                    result = await session.execute(text(query), params or {})
                else:
                    result = await session.execute(query, params or {})
                
                return result.scalar()
                
        except Exception as e:
            logger.error(f"标量查询失败: {e}")
            raise
    
    async def execute_first(
        self, 
        query: Union[str, Select], 
        params: Optional[Dict[str, Any]] = None,
        read_only: bool = True
    ) -> Optional[Dict[str, Any]]:
        """执行查询并返回第一行"""
        results = await self.execute_query(query, params, read_only)
        return results[0] if results else None
    
    async def execute_insert(
        self, 
        query: Union[str, Insert], 
        params: Optional[Dict[str, Any]] = None
    ) -> int:
        """执行插入并返回插入的 ID"""
        try:
            async with self.get_session(read_only=False) as session:
                if isinstance(query, str):
                    result = await session.execute(text(query), params or {})
                else:
                    result = await session.execute(query, params or {})
                
                await session.commit()
                return result.lastrowid
                
        except Exception as e:
            logger.error(f"插入执行失败: {e}")
            raise
    
    async def execute_update(
        self, 
        query: Union[str, Update], 
        params: Optional[Dict[str, Any]] = None
    ) -> int:
        """执行更新并返回影响的行数"""
        try:
            async with self.get_session(read_only=False) as session:
                if isinstance(query, str):
                    result = await session.execute(text(query), params or {})
                else:
                    result = await session.execute(query, params or {})
                
                await session.commit()
                return result.rowcount
                
        except Exception as e:
            logger.error(f"更新执行失败: {e}")
            raise
    
    async def execute_delete(
        self, 
        query: Union[str, Delete], 
        params: Optional[Dict[str, Any]] = None
    ) -> int:
        """执行删除并返回删除的行数"""
        try:
            async with self.get_session(read_only=False) as session:
                if isinstance(query, str):
                    result = await session.execute(text(query), params or {})
                else:
                    result = await session.execute(query, params or {})
                
                await session.commit()
                return result.rowcount
                
        except Exception as e:
            logger.error(f"删除执行失败: {e}")
            raise
    
    async def batch_insert(
        self, 
        table_name: str, 
        records: List[Dict[str, Any]]
    ) -> int:
        """批量插入数据"""
        if not records:
            return 0
        
        try:
            async with self.get_session(read_only=False) as session:
                # 构建批量插入语句
                columns = list(records[0].keys())
                placeholders = ', '.join([f':{col}' for col in columns])
                query = f"""
                    INSERT INTO {table_name} ({', '.join(columns)})
                    VALUES ({placeholders})
                """
                
                await session.execute(text(query), records)
                await session.commit()
                
                return len(records)
                
        except Exception as e:
            logger.error(f"批量插入失败: {e}")
            raise
    
    async def batch_update(
        self, 
        table_name: str, 
        records: List[Dict[str, Any]],
        key_column: str = 'id'
    ) -> int:
        """批量更新数据"""
        if not records:
            return 0
        
        try:
            async with self.get_session(read_only=False) as session:
                updated_count = 0
                
                for record in records:
                    # 分离主键和更新字段
                    key_value = record.pop(key_column)
                    update_fields = ', '.join([f'{col} = :{col}' for col in record.keys()])
                    
                    query = f"""
                        UPDATE {table_name} 
                        SET {update_fields}
                        WHERE {key_column} = :key_value
                    """
                    
                    params = {**record, 'key_value': key_value}
                    result = await session.execute(text(query), params)
                    updated_count += result.rowcount
                
                await session.commit()
                return updated_count
                
        except Exception as e:
            logger.error(f"批量更新失败: {e}")
            raise
    
    async def upsert(
        self, 
        table_name: str, 
        record: Dict[str, Any],
        unique_columns: List[str]
    ) -> str:
        """插入或更新数据"""
        try:
            async with self.get_session(read_only=False) as session:
                # 构建 ON DUPLICATE KEY UPDATE 语句
                columns = list(record.keys())
                placeholders = ', '.join([f':{col}' for col in columns])
                update_assignments = ', '.join([
                    f'{col} = VALUES({col})' 
                    for col in columns 
                    if col not in unique_columns
                ])
                
                query = f"""
                    INSERT INTO {table_name} ({', '.join(columns)})
                    VALUES ({placeholders})
                    ON DUPLICATE KEY UPDATE {update_assignments}
                """
                
                result = await session.execute(text(query), record)
                await session.commit()
                
                # 返回操作类型
                return "updated" if result.rowcount == 2 else "inserted"
                
        except Exception as e:
            logger.error(f"Upsert失败: {e}")
            raise
    
    async def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """获取表结构信息"""
        try:
            query = """
                SELECT 
                    COLUMN_NAME as column_name,
                    DATA_TYPE as data_type,
                    IS_NULLABLE as is_nullable,
                    COLUMN_DEFAULT as column_default,
                    COLUMN_KEY as column_key,
                    EXTRA as extra
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = :table_name
                AND TABLE_SCHEMA = DATABASE()
                ORDER BY ORDINAL_POSITION
            """
            
            columns = await self.execute_query(query, {'table_name': table_name})
            
            # 获取表统计信息
            stats_query = """
                SELECT 
                    TABLE_ROWS as row_count,
                    DATA_LENGTH as data_size,
                    INDEX_LENGTH as index_size,
                    CREATE_TIME as create_time,
                    UPDATE_TIME as update_time
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_NAME = :table_name
                AND TABLE_SCHEMA = DATABASE()
            """
            
            stats = await self.execute_first(stats_query, {'table_name': table_name})
            
            return {
                'table_name': table_name,
                'columns': columns,
                'statistics': stats
            }
            
        except Exception as e:
            logger.error(f"获取表信息失败: {e}")
            raise
    
    async def optimize_table(self, table_name: str) -> bool:
        """优化表"""
        try:
            query = f"OPTIMIZE TABLE {table_name}"
            await self.execute_query(query, read_only=False)
            return True
        except Exception as e:
            logger.error(f"优化表失败: {e}")
            return False
    
    async def analyze_table(self, table_name: str) -> bool:
        """分析表"""
        try:
            query = f"ANALYZE TABLE {table_name}"
            await self.execute_query(query, read_only=False)
            return True
        except Exception as e:
            logger.error(f"分析表失败: {e}")
            return False
    
    async def check_connection(self) -> bool:
        """检查数据库连接"""
        try:
            await self.execute_scalar("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"数据库连接检查失败: {e}")
            return False
    
    async def get_connection_info(self) -> Dict[str, Any]:
        """获取连接信息"""
        try:
            queries = {
                'version': "SELECT VERSION() as version",
                'current_user': "SELECT CURRENT_USER() as current_user",
                'database': "SELECT DATABASE() as database",
                'charset': "SELECT @@character_set_database as charset",
                'timezone': "SELECT @@time_zone as timezone"
            }
            
            info = {}
            for key, query in queries.items():
                result = await self.execute_first(query)
                info[key] = result[list(result.keys())[0]] if result else None
            
            return info
            
        except Exception as e:
            logger.error(f"获取连接信息失败: {e}")
            return {}
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
消息系统V2数据库迁移脚本

主要功能:
1. 数据库表结构升级
2. 数据迁移和转换
3. 索引优化和分区修复
4. 约束添加和验证
5. 备份和回滚支持
6. 版本管理

迁移内容:
- 修复分区函数问题
- 添加缺失的关键索引
- 创建新的V2表结构
- 数据平滑迁移
- 性能验证

@Author: brunoGao
@CreateTime: 2025-09-11
@Version: 2.0-Fixed
"""

import os
import sys
import json
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import traceback
from pathlib import Path

from sqlalchemy import create_engine, text, MetaData, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import pymysql

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from models.message_v2_fixed_model import (
    create_fixed_tables, 
    Base,
    DatabaseFixGenerator,
    validate_database_performance
)

logger = logging.getLogger(__name__)


# ==================== 迁移配置 ====================

class MigrationConfig:
    """迁移配置"""
    
    def __init__(self, config_dict: Dict[str, Any]):
        # 数据库配置
        self.database_url = config_dict.get('database_url', 'mysql://localhost:3306/ljwx')
        self.backup_enabled = config_dict.get('backup_enabled', True)
        self.backup_directory = config_dict.get('backup_directory', './backups')
        
        # 迁移配置
        self.batch_size = config_dict.get('batch_size', 1000)
        self.timeout_seconds = config_dict.get('timeout_seconds', 3600)  # 1小时
        self.dry_run = config_dict.get('dry_run', False)
        self.force_migration = config_dict.get('force_migration', False)
        
        # 验证配置
        self.skip_validation = config_dict.get('skip_validation', False)
        self.performance_check = config_dict.get('performance_check', True)
        
        # 日志配置
        self.log_level = config_dict.get('log_level', 'INFO')
        self.log_file = config_dict.get('log_file', 'migration.log')


# ==================== 迁移状态管理 ====================

class MigrationTracker:
    """迁移状态跟踪器"""
    
    def __init__(self, engine: Engine):
        self.engine = engine
        self.session_factory = sessionmaker(bind=engine)
        self._ensure_migration_table()
    
    def _ensure_migration_table(self):
        """确保迁移表存在"""
        create_sql = """
        CREATE TABLE IF NOT EXISTS migration_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            migration_name VARCHAR(255) NOT NULL UNIQUE,
            migration_version VARCHAR(50) NOT NULL,
            status ENUM('started', 'completed', 'failed', 'rolled_back') NOT NULL,
            start_time DATETIME NOT NULL,
            end_time DATETIME NULL,
            error_message TEXT NULL,
            metadata JSON NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        with self.engine.connect() as conn:
            conn.execute(text(create_sql))
            conn.commit()
    
    def start_migration(self, migration_name: str, migration_version: str, metadata: Dict[str, Any] = None):
        """记录迁移开始"""
        with self.session_factory() as session:
            session.execute(
                text("""
                    INSERT INTO migration_history 
                    (migration_name, migration_version, status, start_time, metadata)
                    VALUES (:name, :version, 'started', :start_time, :metadata)
                    ON DUPLICATE KEY UPDATE
                    status = 'started',
                    start_time = :start_time,
                    end_time = NULL,
                    error_message = NULL,
                    metadata = :metadata,
                    updated_at = CURRENT_TIMESTAMP
                """),
                {
                    'name': migration_name,
                    'version': migration_version,
                    'start_time': datetime.now(timezone.utc),
                    'metadata': json.dumps(metadata or {})
                }
            )
            session.commit()
    
    def complete_migration(self, migration_name: str, metadata: Dict[str, Any] = None):
        """记录迁移完成"""
        with self.session_factory() as session:
            session.execute(
                text("""
                    UPDATE migration_history 
                    SET status = 'completed',
                        end_time = :end_time,
                        metadata = :metadata,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE migration_name = :name
                """),
                {
                    'name': migration_name,
                    'end_time': datetime.now(timezone.utc),
                    'metadata': json.dumps(metadata or {})
                }
            )
            session.commit()
    
    def fail_migration(self, migration_name: str, error_message: str, metadata: Dict[str, Any] = None):
        """记录迁移失败"""
        with self.session_factory() as session:
            session.execute(
                text("""
                    UPDATE migration_history 
                    SET status = 'failed',
                        end_time = :end_time,
                        error_message = :error_message,
                        metadata = :metadata,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE migration_name = :name
                """),
                {
                    'name': migration_name,
                    'end_time': datetime.now(timezone.utc),
                    'error_message': error_message,
                    'metadata': json.dumps(metadata or {})
                }
            )
            session.commit()
    
    def is_migration_completed(self, migration_name: str) -> bool:
        """检查迁移是否已完成"""
        with self.session_factory() as session:
            result = session.execute(
                text("SELECT status FROM migration_history WHERE migration_name = :name"),
                {'name': migration_name}
            ).fetchone()
            
            return result and result[0] == 'completed'
    
    def get_migration_history(self) -> List[Dict[str, Any]]:
        """获取迁移历史"""
        with self.session_factory() as session:
            result = session.execute(
                text("SELECT * FROM migration_history ORDER BY created_at DESC")
            ).fetchall()
            
            return [dict(row._mapping) for row in result]


# ==================== 数据库备份管理器 ====================

class DatabaseBackupManager:
    """数据库备份管理器"""
    
    def __init__(self, config: MigrationConfig):
        self.config = config
        self.backup_dir = Path(config.backup_directory)
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self, backup_name: str = None) -> str:
        """创建数据库备份"""
        if not self.config.backup_enabled:
            logger.info("⚠️ 备份功能已禁用，跳过备份")
            return ""
        
        if not backup_name:
            backup_name = f"migration_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        
        backup_path = self.backup_dir / backup_name
        
        try:
            # 解析数据库URL
            db_config = self._parse_database_url()
            
            # 构建mysqldump命令
            cmd = [
                'mysqldump',
                f"-h{db_config['host']}",
                f"-P{db_config['port']}",
                f"-u{db_config['username']}",
                f"-p{db_config['password']}",
                '--single-transaction',
                '--routines',
                '--triggers',
                '--events',
                '--set-gtid-purged=OFF',
                db_config['database']
            ]
            
            # 执行备份
            import subprocess
            with open(backup_path, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
            
            if result.returncode != 0:
                raise Exception(f"mysqldump failed: {result.stderr}")
            
            logger.info(f"✅ 数据库备份创建成功: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"❌ 数据库备份失败: {e}")
            raise
    
    def restore_backup(self, backup_path: str):
        """恢复数据库备份"""
        backup_file = Path(backup_path)
        
        if not backup_file.exists():
            raise FileNotFoundError(f"备份文件不存在: {backup_path}")
        
        try:
            # 解析数据库URL
            db_config = self._parse_database_url()
            
            # 构建mysql命令
            cmd = [
                'mysql',
                f"-h{db_config['host']}",
                f"-P{db_config['port']}",
                f"-u{db_config['username']}",
                f"-p{db_config['password']}",
                db_config['database']
            ]
            
            # 执行恢复
            import subprocess
            with open(backup_path, 'r') as f:
                result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, text=True)
            
            if result.returncode != 0:
                raise Exception(f"mysql restore failed: {result.stderr}")
            
            logger.info(f"✅ 数据库恢复成功: {backup_path}")
            
        except Exception as e:
            logger.error(f"❌ 数据库恢复失败: {e}")
            raise
    
    def _parse_database_url(self) -> Dict[str, str]:
        """解析数据库URL"""
        from urllib.parse import urlparse
        
        parsed = urlparse(self.config.database_url)
        
        return {
            'host': parsed.hostname or 'localhost',
            'port': str(parsed.port or 3306),
            'username': parsed.username or 'root',
            'password': parsed.password or '',
            'database': parsed.path.lstrip('/') or 'ljwx'
        }


# ==================== 主迁移器 ====================

class MessageV2Migrator:
    """消息系统V2主迁移器"""
    
    def __init__(self, config: MigrationConfig):
        self.config = config
        self.engine = create_engine(config.database_url)
        self.session_factory = sessionmaker(bind=self.engine)
        
        # 初始化组件
        self.tracker = MigrationTracker(self.engine)
        self.backup_manager = DatabaseBackupManager(config)
        self.fix_generator = DatabaseFixGenerator()
        
        # 迁移步骤定义
        self.migration_steps = [
            {
                'name': 'pre_migration_check',
                'description': '迁移前检查',
                'function': self._pre_migration_check,
                'required': True
            },
            {
                'name': 'create_backup',
                'description': '创建数据库备份',
                'function': self._create_backup,
                'required': False
            },
            {
                'name': 'fix_partition_functions',
                'description': '修复分区函数',
                'function': self._fix_partition_functions,
                'required': True
            },
            {
                'name': 'add_missing_indexes',
                'description': '添加缺失索引',
                'function': self._add_missing_indexes,
                'required': True
            },
            {
                'name': 'create_v2_tables',
                'description': '创建V2表结构',
                'function': self._create_v2_tables,
                'required': True
            },
            {
                'name': 'migrate_existing_data',
                'description': '迁移现有数据',
                'function': self._migrate_existing_data,
                'required': True
            },
            {
                'name': 'add_constraints',
                'description': '添加约束',
                'function': self._add_constraints,
                'required': True
            },
            {
                'name': 'validate_migration',
                'description': '验证迁移结果',
                'function': self._validate_migration,
                'required': True
            },
            {
                'name': 'performance_check',
                'description': '性能检查',
                'function': self._performance_check,
                'required': False
            },
            {
                'name': 'cleanup',
                'description': '清理临时数据',
                'function': self._cleanup,
                'required': False
            }
        ]
        
        logger.info("✅ MessageV2迁移器初始化完成")
    
    def run_migration(self) -> bool:
        """运行完整迁移"""
        migration_name = "message_system_v2_migration"
        migration_version = "2.0-Fixed"
        
        logger.info(f"🚀 开始消息系统V2迁移: {migration_name}")
        
        # 检查是否已完成
        if self.tracker.is_migration_completed(migration_name) and not self.config.force_migration:
            logger.info("✅ 迁移已完成，跳过执行")
            return True
        
        # 开始迁移
        start_time = time.time()
        self.tracker.start_migration(migration_name, migration_version, {
            'config': vars(self.config),
            'steps': [step['name'] for step in self.migration_steps]
        })
        
        backup_path = ""
        success = False
        
        try:
            # 逐步执行迁移
            for i, step in enumerate(self.migration_steps):
                step_name = step['name']
                step_desc = step['description']
                step_func = step['function']
                is_required = step['required']
                
                logger.info(f"📋 执行迁移步骤 {i+1}/{len(self.migration_steps)}: {step_desc}")
                
                try:
                    if self.config.dry_run and step_name not in ['pre_migration_check', 'validate_migration']:
                        logger.info(f"🔍 DRY RUN模式: 跳过步骤 {step_name}")
                        continue
                    
                    # 执行步骤
                    step_result = step_func()
                    
                    # 保存备份路径
                    if step_name == 'create_backup' and step_result:
                        backup_path = step_result
                    
                    logger.info(f"✅ 步骤完成: {step_desc}")
                    
                except Exception as e:
                    logger.error(f"❌ 步骤失败: {step_desc}, 错误: {e}")
                    
                    if is_required:
                        # 必需步骤失败，中止迁移
                        raise Exception(f"必需步骤失败: {step_name}, 错误: {e}")
                    else:
                        # 可选步骤失败，继续执行
                        logger.warning(f"⚠️ 可选步骤失败，继续执行: {step_name}")
            
            # 所有步骤完成
            duration = time.time() - start_time
            
            self.tracker.complete_migration(migration_name, {
                'duration_seconds': duration,
                'backup_path': backup_path,
                'dry_run': self.config.dry_run
            })
            
            logger.info(f"🎉 消息系统V2迁移完成! 耗时: {duration:.2f}秒")
            success = True
            
            return True
            
        except Exception as e:
            # 迁移失败
            duration = time.time() - start_time
            error_msg = f"迁移失败: {str(e)}\n{traceback.format_exc()}"
            
            self.tracker.fail_migration(migration_name, error_msg, {
                'duration_seconds': duration,
                'backup_path': backup_path,
                'dry_run': self.config.dry_run
            })
            
            logger.error(f"❌ 消息系统V2迁移失败: {e}")
            
            # 如果有备份，询问是否回滚
            if backup_path and not self.config.dry_run:
                logger.info(f"💡 可使用备份回滚: python {__file__} --rollback {backup_path}")
            
            return False
    
    # ==================== 迁移步骤实现 ====================
    
    def _pre_migration_check(self) -> bool:
        """迁移前检查"""
        logger.info("🔍 执行迁移前检查...")
        
        checks = []
        
        try:
            # 检查数据库连接
            with self.engine.connect() as conn:
                conn.execute(text('SELECT 1'))
            checks.append(("数据库连接", True, ""))
            
            # 检查表是否存在
            inspector = inspect(self.engine)
            existing_tables = inspector.get_table_names()
            
            required_tables = ['t_device_message', 't_device_message_v2']
            missing_tables = [table for table in required_tables if table not in existing_tables]
            
            if missing_tables:
                checks.append(("必需表检查", False, f"缺失表: {missing_tables}"))
            else:
                checks.append(("必需表检查", True, ""))
            
            # 检查磁盘空间
            import shutil
            free_space = shutil.disk_usage('/').free
            free_gb = free_space / (1024**3)
            
            if free_gb < 1.0:  # 至少1GB空闲空间
                checks.append(("磁盘空间", False, f"空闲空间不足: {free_gb:.1f}GB"))
            else:
                checks.append(("磁盘空间", True, f"空闲空间: {free_gb:.1f}GB"))
            
            # 检查权限
            try:
                with self.engine.connect() as conn:
                    conn.execute(text('CREATE TEMPORARY TABLE test_permissions (id INT)'))
                    conn.execute(text('DROP TEMPORARY TABLE test_permissions'))
                checks.append(("数据库权限", True, ""))
            except Exception as e:
                checks.append(("数据库权限", False, str(e)))
            
            # 输出检查结果
            all_passed = True
            for check_name, passed, message in checks:
                status = "✅" if passed else "❌"
                logger.info(f"{status} {check_name}: {message}")
                if not passed:
                    all_passed = False
            
            if not all_passed:
                raise Exception("迁移前检查失败，无法继续迁移")
            
            logger.info("✅ 迁移前检查通过")
            return True
            
        except Exception as e:
            logger.error(f"❌ 迁移前检查失败: {e}")
            raise
    
    def _create_backup(self) -> str:
        """创建数据库备份"""
        if not self.config.backup_enabled:
            logger.info("⚠️ 备份功能已禁用")
            return ""
        
        logger.info("💾 创建数据库备份...")
        backup_path = self.backup_manager.create_backup()
        logger.info(f"✅ 备份创建完成: {backup_path}")
        
        return backup_path
    
    def _fix_partition_functions(self) -> bool:
        """修复分区函数"""
        logger.info("🔧 修复分区函数...")
        
        try:
            partition_sql = self.fix_generator.generate_partition_fix_sql()
            
            if self.config.dry_run:
                logger.info(f"🔍 DRY RUN - 分区修复SQL:\n{partition_sql}")
                return True
            
            # 执行分区修复
            with self.engine.connect() as conn:
                # 分批执行SQL语句
                statements = [stmt.strip() for stmt in partition_sql.split(';') if stmt.strip()]
                
                for stmt in statements:
                    if stmt:
                        logger.debug(f"执行SQL: {stmt[:100]}...")
                        conn.execute(text(stmt))
                
                conn.commit()
            
            logger.info("✅ 分区函数修复完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 分区函数修复失败: {e}")
            raise
    
    def _add_missing_indexes(self) -> bool:
        """添加缺失索引"""
        logger.info("📊 添加缺失索引...")
        
        try:
            index_sql = self.fix_generator.generate_index_fix_sql()
            
            if self.config.dry_run:
                logger.info(f"🔍 DRY RUN - 索引修复SQL:\n{index_sql}")
                return True
            
            # 执行索引添加
            with self.engine.connect() as conn:
                statements = [stmt.strip() for stmt in index_sql.split(';') if stmt.strip()]
                
                for stmt in statements:
                    if stmt:
                        try:
                            logger.debug(f"执行SQL: {stmt[:100]}...")
                            conn.execute(text(stmt))
                        except SQLAlchemyError as e:
                            # 索引可能已存在，记录但不中断
                            logger.warning(f"⚠️ 索引添加警告: {e}")
                
                conn.commit()
            
            logger.info("✅ 缺失索引添加完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 添加缺失索引失败: {e}")
            raise
    
    def _create_v2_tables(self) -> bool:
        """创建V2表结构"""
        logger.info("🏗️ 创建V2表结构...")
        
        try:
            if self.config.dry_run:
                logger.info("🔍 DRY RUN - 跳过V2表创建")
                return True
            
            # 创建V2表
            create_fixed_tables(self.engine)
            
            logger.info("✅ V2表结构创建完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ V2表结构创建失败: {e}")
            raise
    
    def _migrate_existing_data(self) -> bool:
        """迁移现有数据"""
        logger.info("🔄 迁移现有数据...")
        
        try:
            if self.config.dry_run:
                logger.info("🔍 DRY RUN - 跳过数据迁移")
                return True
            
            # 检查是否有数据需要迁移
            with self.engine.connect() as conn:
                # 检查旧表数据量
                result = conn.execute(text("""
                    SELECT COUNT(*) as count 
                    FROM information_schema.tables 
                    WHERE table_schema = DATABASE() 
                    AND table_name = 't_device_message'
                """)).fetchone()
                
                if not result or result[0] == 0:
                    logger.info("📭 未找到需要迁移的数据")
                    return True
                
                # 获取旧数据总数
                old_count = conn.execute(text("SELECT COUNT(*) FROM t_device_message")).scalar()
                logger.info(f"📊 发现待迁移数据: {old_count}条")
                
                if old_count == 0:
                    logger.info("📭 无数据需要迁移")
                    return True
                
                # 分批迁移数据
                migrated_count = 0
                batch_size = self.config.batch_size
                
                while migrated_count < old_count:
                    # 获取一批数据
                    batch_data = conn.execute(text(f"""
                        SELECT * FROM t_device_message 
                        WHERE id > :offset 
                        ORDER BY id 
                        LIMIT :limit
                    """), {'offset': migrated_count, 'limit': batch_size}).fetchall()
                    
                    if not batch_data:
                        break
                    
                    # 转换并插入到V2表
                    for row in batch_data:
                        self._migrate_single_message(conn, row)
                    
                    migrated_count += len(batch_data)
                    progress = (migrated_count / old_count) * 100
                    
                    logger.info(f"📈 数据迁移进度: {migrated_count}/{old_count} ({progress:.1f}%)")
                
                conn.commit()
            
            logger.info(f"✅ 数据迁移完成，共迁移 {migrated_count} 条记录")
            return True
            
        except Exception as e:
            logger.error(f"❌ 数据迁移失败: {e}")
            raise
    
    def _migrate_single_message(self, conn, old_row):
        """迁移单条消息数据"""
        try:
            # 转换数据格式（根据实际表结构调整）
            new_data = {
                'customer_id': old_row.customer_id if hasattr(old_row, 'customer_id') else 1,
                'department_id': old_row.department_id if hasattr(old_row, 'department_id') else 1,
                'user_id': old_row.user_id if hasattr(old_row, 'user_id') else None,
                'device_sn': old_row.device_sn if hasattr(old_row, 'device_sn') else '',
                'title': old_row.title if hasattr(old_row, 'title') else '',
                'message': old_row.message if hasattr(old_row, 'message') else '',
                'message_type': old_row.message_type if hasattr(old_row, 'message_type') else 'notification',
                'sender_type': old_row.sender_type if hasattr(old_row, 'sender_type') else 'system',
                'receiver_type': old_row.receiver_type if hasattr(old_row, 'receiver_type') else 'user',
                'priority_level': old_row.priority_level if hasattr(old_row, 'priority_level') else 3,
                'urgency': 'medium',  # 默认值
                'message_status': old_row.message_status if hasattr(old_row, 'message_status') else 'pending',
                'create_time': old_row.create_time if hasattr(old_row, 'create_time') else datetime.now(timezone.utc),
                'channels': '["message"]',  # JSON格式
                'require_ack': False,
                'metadata': '{}'  # JSON格式
            }
            
            # 插入到V2表
            conn.execute(text("""
                INSERT INTO t_device_message_v2 
                (customer_id, department_id, user_id, device_sn, title, message, 
                 message_type, sender_type, receiver_type, priority_level, urgency,
                 message_status, create_time, channels, require_ack, metadata)
                VALUES 
                (:customer_id, :department_id, :user_id, :device_sn, :title, :message,
                 :message_type, :sender_type, :receiver_type, :priority_level, :urgency,
                 :message_status, :create_time, :channels, :require_ack, :metadata)
            """), new_data)
            
        except Exception as e:
            logger.error(f"❌ 单条消息迁移失败: {e}, 数据: {old_row}")
            # 可以选择跳过或中断
            raise
    
    def _add_constraints(self) -> bool:
        """添加约束"""
        logger.info("🔗 添加约束...")
        
        try:
            constraint_sql = self.fix_generator.generate_constraint_fix_sql()
            
            if self.config.dry_run:
                logger.info(f"🔍 DRY RUN - 约束SQL:\n{constraint_sql}")
                return True
            
            # 执行约束添加
            with self.engine.connect() as conn:
                statements = [stmt.strip() for stmt in constraint_sql.split(';') if stmt.strip()]
                
                for stmt in statements:
                    if stmt:
                        try:
                            logger.debug(f"执行SQL: {stmt[:100]}...")
                            conn.execute(text(stmt))
                        except SQLAlchemyError as e:
                            # 约束可能已存在
                            logger.warning(f"⚠️ 约束添加警告: {e}")
                
                conn.commit()
            
            logger.info("✅ 约束添加完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 添加约束失败: {e}")
            raise
    
    def _validate_migration(self) -> bool:
        """验证迁移结果"""
        logger.info("🔍 验证迁移结果...")
        
        if self.config.skip_validation:
            logger.info("⚠️ 跳过迁移验证")
            return True
        
        try:
            validation_results = []
            
            with self.engine.connect() as conn:
                # 1. 检查表结构
                inspector = inspect(self.engine)
                v2_tables = [
                    't_device_message_v2',
                    't_device_message_detail_v2',
                    't_message_lifecycle_v2'
                ]
                
                for table_name in v2_tables:
                    if table_name in inspector.get_table_names():
                        validation_results.append((f"表存在检查: {table_name}", True, ""))
                    else:
                        validation_results.append((f"表存在检查: {table_name}", False, "表不存在"))
                
                # 2. 检查索引
                for table_name in v2_tables:
                    try:
                        indexes = inspector.get_indexes(table_name)
                        index_count = len(indexes)
                        validation_results.append((f"索引检查: {table_name}", index_count > 0, f"索引数量: {index_count}"))
                    except:
                        validation_results.append((f"索引检查: {table_name}", False, "获取索引信息失败"))
                
                # 3. 数据一致性检查
                if 't_device_message' in inspector.get_table_names():
                    old_count = conn.execute(text("SELECT COUNT(*) FROM t_device_message")).scalar()
                    new_count = conn.execute(text("SELECT COUNT(*) FROM t_device_message_v2")).scalar()
                    
                    data_consistent = old_count == new_count
                    validation_results.append((
                        "数据一致性检查", 
                        data_consistent, 
                        f"旧表: {old_count}条, 新表: {new_count}条"
                    ))
                
                # 4. 基本查询测试
                try:
                    conn.execute(text("SELECT * FROM t_device_message_v2 LIMIT 1")).fetchone()
                    validation_results.append(("查询测试", True, ""))
                except Exception as e:
                    validation_results.append(("查询测试", False, str(e)))
            
            # 输出验证结果
            all_passed = True
            for check_name, passed, message in validation_results:
                status = "✅" if passed else "❌"
                logger.info(f"{status} {check_name}: {message}")
                if not passed:
                    all_passed = False
            
            if not all_passed:
                raise Exception("迁移验证失败")
            
            logger.info("✅ 迁移验证通过")
            return True
            
        except Exception as e:
            logger.error(f"❌ 迁移验证失败: {e}")
            raise
    
    def _performance_check(self) -> bool:
        """性能检查"""
        logger.info("⚡ 执行性能检查...")
        
        if not self.config.performance_check:
            logger.info("⚠️ 跳过性能检查")
            return True
        
        try:
            with self.session_factory() as session:
                # 执行性能验证
                performance_results = validate_database_performance(session)
                
                # 输出结果
                for test_name, result in performance_results.items():
                    if isinstance(result, dict):
                        status = "✅" if result.get('status') == 'PASS' else "❌"
                        query_time = result.get('query_time_ms', 0)
                        expected = result.get('expected_max_ms', 0)
                        
                        logger.info(f"{status} {test_name}: {query_time:.2f}ms (期望: <{expected}ms)")
                    else:
                        logger.info(f"📊 {test_name}: {result}")
                
                logger.info("✅ 性能检查完成")
                return True
                
        except Exception as e:
            logger.error(f"❌ 性能检查失败: {e}")
            # 性能检查失败不中断迁移
            return True
    
    def _cleanup(self) -> bool:
        """清理临时数据"""
        logger.info("🧹 清理临时数据...")
        
        try:
            if self.config.dry_run:
                logger.info("🔍 DRY RUN - 跳过清理")
                return True
            
            # 这里可以添加清理逻辑
            # 例如：删除临时表、清理日志等
            
            logger.info("✅ 清理完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 清理失败: {e}")
            # 清理失败不影响迁移结果
            return True
    
    # ==================== 回滚功能 ====================
    
    def rollback_migration(self, backup_path: str) -> bool:
        """回滚迁移"""
        logger.info(f"🔄 开始回滚迁移: {backup_path}")
        
        try:
            # 恢复备份
            self.backup_manager.restore_backup(backup_path)
            
            # 更新迁移状态
            self.tracker.fail_migration(
                "message_system_v2_migration",
                "手动回滚",
                {'rollback_backup': backup_path}
            )
            
            logger.info("✅ 迁移回滚完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 迁移回滚失败: {e}")
            return False
    
    def get_migration_status(self) -> Dict[str, Any]:
        """获取迁移状态"""
        history = self.tracker.get_migration_history()
        
        return {
            'migration_history': history,
            'latest_migration': history[0] if history else None,
            'database_url': self.config.database_url,
            'backup_directory': self.config.backup_directory
        }


# ==================== 命令行工具 ====================

def main():
    """命令行主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='消息系统V2数据库迁移工具')
    parser.add_argument('--config', type=str, default='migration_config.json', help='配置文件路径')
    parser.add_argument('--database-url', type=str, help='数据库连接URL')
    parser.add_argument('--dry-run', action='store_true', help='预演模式（不执行实际操作）')
    parser.add_argument('--force', action='store_true', help='强制迁移（即使已完成）')
    parser.add_argument('--rollback', type=str, help='回滚到指定备份')
    parser.add_argument('--status', action='store_true', help='查看迁移状态')
    parser.add_argument('--log-level', type=str, default='INFO', help='日志级别')
    
    args = parser.parse_args()
    
    # 配置日志
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('migration.log')
        ]
    )
    
    # 加载配置
    config_dict = {}
    if os.path.exists(args.config):
        with open(args.config, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
    
    # 命令行参数覆盖配置文件
    if args.database_url:
        config_dict['database_url'] = args.database_url
    if args.dry_run:
        config_dict['dry_run'] = True
    if args.force:
        config_dict['force_migration'] = True
    
    config = MigrationConfig(config_dict)
    
    # 创建迁移器
    migrator = MessageV2Migrator(config)
    
    try:
        if args.status:
            # 查看迁移状态
            status = migrator.get_migration_status()
            print("🔍 迁移状态:")
            print(json.dumps(status, indent=2, default=str, ensure_ascii=False))
            
        elif args.rollback:
            # 执行回滚
            success = migrator.rollback_migration(args.rollback)
            sys.exit(0 if success else 1)
            
        else:
            # 执行迁移
            success = migrator.run_migration()
            sys.exit(0 if success else 1)
            
    except KeyboardInterrupt:
        logger.info("⏹️ 迁移被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 迁移工具执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
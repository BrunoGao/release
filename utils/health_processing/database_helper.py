#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库辅助工具
用于直接查询数据库获取用户和健康数据

@Author: bruno.gao <gaojunivas@gmail.com>
@ProjectName: ljwx-boot
@CreateTime: 2025-01-26
"""

import mysql.connector
from mysql.connector import Error
import json
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

class DatabaseHelper:
    """数据库辅助工具"""
    
    def __init__(self, config_file: str = "../db_config.json"):
        self.config = self.load_config(config_file)
        self.connection = None
        self.logger = logging.getLogger(f"{__name__}.DatabaseHelper")
        
    def load_config(self, config_file: str) -> Dict:
        """加载数据库配置"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), config_file)
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"加载数据库配置失败: {e}")
            # 返回默认配置
            return {
                "host": "127.0.0.1",
                "port": 3306,
                "database": "test",
                "user": "root",
                "password": "123456"
            }
    
    def connect(self) -> bool:
        """连接数据库"""
        try:
            if self.connection and self.connection.is_connected():
                return True
                
            self.connection = mysql.connector.connect(
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password'],
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
            
            self.logger.info(f"✅ 数据库连接成功: {self.config['database']}")
            return True
            
        except Error as e:
            self.logger.error(f"❌ 数据库连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开数据库连接"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            self.logger.debug("数据库连接已关闭")
    
    def get_active_users(self, days: int = 30) -> List[Dict[str, Any]]:
        """获取有健康数据的活跃用户"""
        if not self.connect():
            return []
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # 先查看sys_user表结构
            cursor.execute("DESCRIBE sys_user")
            columns = [col['Field'] for col in cursor.fetchall()]
            self.logger.debug(f"sys_user表字段: {columns}")
            
            # 构建查询语句，动态包含存在的字段
            select_fields = ["u.id as user_id", "u.user_name", "COUNT(h.id) as health_data_count"]
            group_fields = ["u.id", "u.user_name"]
            
            if 'phone' in columns:
                select_fields.append("u.phone")
                group_fields.append("u.phone")
            
            if 'customer_id' in columns:
                select_fields.append("u.customer_id")
                group_fields.append("u.customer_id")
            else:
                # 默认customer_id为1
                select_fields.append("1 as customer_id")
            
            if 'org_id' in columns:
                select_fields.append("u.org_id")
                group_fields.append("u.org_id")
            else:
                # 默认org_id为1
                select_fields.append("1 as org_id")
            
            query = f"""
            SELECT DISTINCT 
                {', '.join(select_fields)}
            FROM sys_user u
            INNER JOIN t_user_health_data h ON u.id = h.user_id
            WHERE u.is_deleted = 0 
                AND h.create_time >= DATE_SUB(NOW(), INTERVAL %s DAY)
                AND (h.heart_rate > 0 OR h.blood_oxygen > 0 OR h.temperature > 0)
            GROUP BY {', '.join(group_fields)}
            HAVING health_data_count >= 5
            ORDER BY health_data_count DESC
            LIMIT 100
            """
            
            cursor.execute(query, (days,))
            users = cursor.fetchall()
            cursor.close()
            
            self.logger.info(f"📊 找到 {len(users)} 个活跃用户（最近{days}天）")
            return users
            
        except Error as e:
            self.logger.error(f"❌ 查询活跃用户失败: {e}")
            return []
    
    def get_active_organizations(self, days: int = 30) -> List[Dict[str, Any]]:
        """获取有健康数据的活跃组织"""
        if not self.connect():
            return []
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # 检查sys_org表是否存在
            try:
                cursor.execute("SHOW TABLES LIKE 'sys_org'")
                org_table_exists = cursor.fetchone() is not None
            except Error:
                org_table_exists = False
            
            if not org_table_exists:
                self.logger.warning("⚠️ sys_org表不存在，跳过组织查询")
                cursor.close()
                return []
            
            # 检查sys_user是否有org_id字段
            cursor.execute("DESCRIBE sys_user")
            user_columns = [col['Field'] for col in cursor.fetchall()]
            
            if 'org_id' not in user_columns:
                self.logger.warning("⚠️ sys_user表没有org_id字段，跳过组织查询")
                cursor.close()
                return []
            
            # 查询最近N天有健康数据的组织
            query = """
            SELECT DISTINCT 
                o.id as org_id,
                o.org_name,
                COALESCE(u.customer_id, 1) as customer_id,
                COUNT(DISTINCT u.id) as user_count,
                COUNT(h.id) as health_data_count
            FROM sys_org o
            INNER JOIN sys_user u ON o.id = u.org_id
            INNER JOIN t_user_health_data h ON u.id = h.user_id
            WHERE o.is_deleted = 0 
                AND u.is_deleted = 0
                AND h.create_time >= DATE_SUB(NOW(), INTERVAL %s DAY)
                AND (h.heart_rate > 0 OR h.blood_oxygen > 0 OR h.temperature > 0)
            GROUP BY o.id, o.org_name, u.customer_id
            HAVING user_count >= 2 AND health_data_count >= 20
            ORDER BY user_count DESC
            LIMIT 50
            """
            
            cursor.execute(query, (days,))
            organizations = cursor.fetchall()
            cursor.close()
            
            self.logger.info(f"📊 找到 {len(organizations)} 个活跃组织（最近{days}天）")
            return organizations
            
        except Error as e:
            self.logger.error(f"❌ 查询活跃组织失败: {e}")
            return []
    
    def get_user_health_data_stats(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """获取用户健康数据统计"""
        if not self.connect():
            return {}
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # 查询用户健康数据统计
            query = """
            SELECT 
                COUNT(*) as total_records,
                COUNT(CASE WHEN heart_rate > 0 THEN 1 END) as heart_rate_count,
                COUNT(CASE WHEN blood_oxygen > 0 THEN 1 END) as blood_oxygen_count,
                COUNT(CASE WHEN temperature > 0 THEN 1 END) as temperature_count,
                COUNT(CASE WHEN pressure_high > 0 THEN 1 END) as pressure_count,
                COUNT(CASE WHEN stress > 0 THEN 1 END) as stress_count,
                COUNT(CASE WHEN step > 0 THEN 1 END) as step_count,
                MIN(create_time) as earliest_data,
                MAX(create_time) as latest_data
            FROM t_user_health_data 
            WHERE user_id = %s 
                AND create_time >= DATE_SUB(NOW(), INTERVAL %s DAY)
            """
            
            cursor.execute(query, (user_id, days))
            stats = cursor.fetchone()
            cursor.close()
            
            return stats or {}
            
        except Error as e:
            self.logger.error(f"❌ 查询用户{user_id}健康数据统计失败: {e}")
            return {}
    
    def check_health_tables(self) -> Dict[str, Any]:
        """检查健康相关表的状态"""
        if not self.connect():
            return {}
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            tables_info = {}
            
            # 检查主要健康表
            health_tables = [
                't_user_health_data',
                't_health_baseline', 
                't_health_score',
                't_org_health_baseline',
                't_org_health_score',
                'sys_user',
                'sys_org'
            ]
            
            for table in health_tables:
                try:
                    # 检查表是否存在
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    result = cursor.fetchone()
                    
                    # 检查表结构
                    cursor.execute(f"DESCRIBE {table}")
                    columns = cursor.fetchall()
                    
                    tables_info[table] = {
                        'exists': True,
                        'record_count': result['count'],
                        'columns': [col['Field'] for col in columns]
                    }
                    
                except Error as e:
                    tables_info[table] = {
                        'exists': False,
                        'error': str(e)
                    }
            
            cursor.close()
            
            self.logger.info("📋 健康表检查完成")
            return tables_info
            
        except Error as e:
            self.logger.error(f"❌ 检查健康表失败: {e}")
            return {}

def test_database_helper():
    """测试数据库辅助工具"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    db = DatabaseHelper()
    
    print("🔍 测试数据库连接...")
    if not db.connect():
        print("❌ 数据库连接失败")
        return
    
    print("\n📊 检查健康表状态...")
    tables_info = db.check_health_tables()
    for table, info in tables_info.items():
        if info.get('exists'):
            print(f"✅ {table}: {info['record_count']} 条记录")
        else:
            print(f"❌ {table}: 表不存在")
    
    print("\n👥 获取活跃用户...")
    users = db.get_active_users(30)
    for user in users[:5]:  # 显示前5个用户
        print(f"  用户 {user['user_id']}: {user['user_name']} ({user['health_data_count']} 条数据)")
    
    print("\n🏢 获取活跃组织...")
    orgs = db.get_active_organizations(30)
    for org in orgs[:3]:  # 显示前3个组织
        print(f"  组织 {org['org_id']}: {org['org_name']} ({org['user_count']} 个用户)")
    
    db.disconnect()
    print("✅ 数据库测试完成")

if __name__ == "__main__":
    test_database_helper()
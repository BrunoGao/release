import mysql.connector
from mysql.connector import Error
import json
import os
from typing import List, Dict, Any, Optional

class DatabaseConfig:
    def __init__(self, host: str = 'localhost', port: int = 3306, 
                 database: str = 'ljwx', user: str = 'root', password: str = ''):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.connection = None
    
    def connect(self) -> bool:
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
            return True
        except Error as e:
            print(f"数据库连接错误: {e}")
            return False
    
    def disconnect(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
    
    def get_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                return []
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT id, user_name, phone FROM sys_user WHERE is_deleted = 0 LIMIT %s"
            cursor.execute(query, (limit,))
            users = cursor.fetchall()
            cursor.close()
            return users
        except Error as e:
            print(f"查询用户错误: {e}")
            return []
    
    def get_devices(self, limit: int = 10) -> List[Dict[str, Any]]:
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                return []
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT serial_number as device_sn, device_name, user_id FROM t_device_info WHERE is_deleted = 0 LIMIT %s"
            cursor.execute(query, (limit,))
            devices = cursor.fetchall()
            cursor.close()
            return devices
        except Error as e:
            print(f"查询设备错误: {e}")
            return []
    
    def get_user_devices(self, limit: int = 10) -> List[Dict[str, Any]]:
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                return []
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT u.id as user_id, u.user_name, u.phone, d.serial_number as device_sn, d.device_name
            FROM sys_user u 
            INNER JOIN t_device_info d ON u.id = d.user_id 
            WHERE u.is_deleted = 0 AND d.is_deleted = 0 AND d.user_id IS NOT NULL
            LIMIT %s
            """
            cursor.execute(query, (limit,))
            user_devices = cursor.fetchall()
            cursor.close()
            return user_devices
        except Error as e:
            print(f"查询用户设备关联错误: {e}")
            return []
    
    def get_departments(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取部门数据"""
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                return []
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT id, name FROM sys_org_units WHERE is_deleted = 0 LIMIT %s"
            cursor.execute(query, (limit,))
            departments = cursor.fetchall()
            cursor.close()
            return departments
        except Error as e:
            print(f"查询部门错误: {e}")
            return []

def load_db_config() -> DatabaseConfig:
    config_file = os.path.join(os.path.dirname(__file__), 'db_config.json')
    
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return DatabaseConfig(**config)
    else:
        default_config = {
            "host": "localhost",
            "port": 3306,
            "database": "ljwx",
            "user": "root",
            "password": ""
        }
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        print(f"已创建默认数据库配置文件: {config_file}")
        print("请根据实际情况修改数据库连接参数")
        return DatabaseConfig(**default_config)
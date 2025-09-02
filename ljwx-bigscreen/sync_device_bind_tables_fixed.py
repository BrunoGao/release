#!/usr/bin/env python3
"""设备绑定数据库表同步脚本 - 修正版本"""

import pymysql
import sys
from datetime import datetime

# 数据库配置
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root', 
    'password': '123456',
    'database': 'lj-06',
    'charset': 'utf8mb4'
}

def get_db_connection():
    try:
        return pymysql.connect(**DB_CONFIG)
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        sys.exit(1)

def execute_sql_safe(cursor, sql, desc):
    try:
        cursor.execute(sql)
        print(f"✅ {desc}")
        return True
    except Exception as e:
        if "Duplicate column name" in str(e) or "Duplicate key name" in str(e):
            print(f"✅ {desc} (已存在)")
            return True
        print(f"❌ {desc} 失败: {e}")
        return False

def sync_device_bind_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("🚀 开始同步设备绑定数据库表...")
        
        # 添加字段
        execute_sql_safe(cursor, "ALTER TABLE t_device_info ADD COLUMN user_id BIGINT COMMENT '绑定用户ID'", "添加user_id字段")
        execute_sql_safe(cursor, "ALTER TABLE t_device_info ADD COLUMN org_id BIGINT COMMENT '绑定组织ID'", "添加org_id字段")
        
        # 创建申请表
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS t_device_bind_request (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            device_sn VARCHAR(100) NOT NULL,
            user_id BIGINT NOT NULL,
            org_id BIGINT NOT NULL,
            status ENUM('PENDING', 'APPROVED', 'REJECTED') DEFAULT 'PENDING',
            apply_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            approve_time DATETIME NULL,
            approver_id BIGINT NULL,
            comment VARCHAR(255) NULL,
            is_deleted TINYINT(1) DEFAULT 0,
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
        execute_sql_safe(cursor, create_table_sql, "创建申请表")
        
        # 添加索引
        execute_sql_safe(cursor, "ALTER TABLE t_device_bind_request ADD INDEX idx_device_sn (device_sn)", "添加设备序列号索引")
        execute_sql_safe(cursor, "ALTER TABLE t_device_info ADD INDEX idx_user_id (user_id)", "添加用户ID索引") 
        execute_sql_safe(cursor, "ALTER TABLE t_device_info ADD INDEX idx_org_id (org_id)", "添加组织ID索引")
        
        # 同步数据 - 修复字符集问题
        print("\n📊 同步现有绑定数据...")
        try:
            # 先查询有哪些绑定记录
            cursor.execute("""
                SELECT DISTINCT device_sn, user_id 
                FROM t_device_user 
                WHERE status = 'BIND' AND (is_deleted = 0 OR is_deleted IS NULL)
                ORDER BY operate_time DESC
            """)
            bind_records = cursor.fetchall()
            
            updated = 0
            for device_sn, user_id in bind_records:
                # 逐条更新避免字符集问题
                cursor.execute("""
                    UPDATE t_device_info 
                    SET user_id = %s 
                    WHERE serial_number = %s AND user_id IS NULL
                """, (user_id, device_sn))
                if cursor.rowcount > 0:
                    updated += 1
            
            print(f"✅ 同步了 {updated} 条绑定记录")
        except Exception as e:
            print(f"⚠️  数据同步跳过: {e}")
            print("ℹ️  可以稍后手动同步数据")
        
        # 统计信息
        cursor.execute("SELECT COUNT(*) FROM t_device_info WHERE user_id IS NOT NULL")
        bound = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM t_device_info")
        total = cursor.fetchone()[0]
        print(f"\n📈 统计: {bound}/{total} 设备已绑定")
        
        conn.commit()
        print(f"\n🎉 同步完成! {datetime.now()}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 同步失败: {e}")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("=" * 50)
    print("🔧 LJWX 设备绑定数据库同步工具")
    print("=" * 50)
    sync_device_bind_tables()
    print("✨ 现在可以访问: http://localhost:5001/device_bind_management")
    print("=" * 50) 
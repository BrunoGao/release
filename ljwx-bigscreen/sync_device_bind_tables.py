#!/usr/bin/env python3
"""设备绑定数据库表同步脚本 - 创建和更新设备绑定相关表结构"""

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
    """获取数据库连接"""
    try:
        return pymysql.connect(**DB_CONFIG)
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        sys.exit(1)

def execute_sql(cursor, sql, description):
    """执行SQL语句"""
    try:
        cursor.execute(sql)
        print(f"✅ {description}")
        return True
    except Exception as e:
        print(f"❌ {description} 失败: {e}")
        return False

def sync_device_bind_tables():
    """同步设备绑定相关表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("🚀 开始同步设备绑定数据库表...")
        
        # 1. 为 t_device_info 表添加用户和组织绑定字段
        try:
            cursor.execute("ALTER TABLE t_device_info ADD COLUMN user_id BIGINT COMMENT '绑定用户ID'")
            print("✅ 添加 user_id 字段")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("✅ user_id 字段已存在")
            else:
                print(f"❌ 添加 user_id 字段失败: {e}")
        
        try:
            cursor.execute("ALTER TABLE t_device_info ADD COLUMN org_id BIGINT COMMENT '绑定组织ID'")
            print("✅ 添加 org_id 字段")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("✅ org_id 字段已存在")
            else:
                print(f"❌ 添加 org_id 字段失败: {e}")
        
        # 2. 创建设备绑定申请表
        create_bind_request_sql = """
        CREATE TABLE IF NOT EXISTS t_device_bind_request (
            id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
            device_sn VARCHAR(100) NOT NULL COMMENT '设备序列号',
            user_id BIGINT NOT NULL COMMENT '申请用户ID',
            org_id BIGINT NOT NULL COMMENT '申请组织ID',
            status ENUM('PENDING', 'APPROVED', 'REJECTED') DEFAULT 'PENDING' NOT NULL COMMENT '申请状态',
            apply_time DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL COMMENT '申请时间',
            approve_time DATETIME NULL COMMENT '审批时间',
            approver_id BIGINT NULL COMMENT '审批人ID',
            comment VARCHAR(255) NULL COMMENT '审批备注',
            is_deleted TINYINT(1) DEFAULT 0 NOT NULL COMMENT '是否删除',
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL COMMENT '创建时间',
            update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL COMMENT '更新时间',
            INDEX idx_device_sn (device_sn),
            INDEX idx_user_status (user_id, status),
            INDEX idx_apply_time (apply_time)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='设备绑定申请表'
        """
        execute_sql(cursor, create_bind_request_sql, "创建设备绑定申请表")
        
        # 3. 为 t_device_user 表添加索引优化
        try:
            cursor.execute("ALTER TABLE t_device_user ADD INDEX idx_device_user_status (device_sn, user_id, status)")
            print("✅ 添加设备用户状态复合索引")
        except Exception as e:
            if "Duplicate key name" in str(e):
                print("✅ 设备用户状态复合索引已存在")
            else:
                print(f"❌ 添加设备用户状态复合索引失败: {e}")
        
        try:
            cursor.execute("ALTER TABLE t_device_user ADD INDEX idx_operate_time (operate_time)")
            print("✅ 添加操作时间索引")
        except Exception as e:
            if "Duplicate key name" in str(e):
                print("✅ 操作时间索引已存在")
            else:
                print(f"❌ 添加操作时间索引失败: {e}")
        
        # 4. 为 t_device_info 表添加绑定相关索引
        try:
            cursor.execute("ALTER TABLE t_device_info ADD INDEX idx_user_id (user_id)")
            print("✅ 添加用户ID索引")
        except Exception as e:
            if "Duplicate key name" in str(e):
                print("✅ 用户ID索引已存在")
            else:
                print(f"❌ 添加用户ID索引失败: {e}")
        
        try:
            cursor.execute("ALTER TABLE t_device_info ADD INDEX idx_org_id (org_id)")
            print("✅ 添加组织ID索引")
        except Exception as e:
            if "Duplicate key name" in str(e):
                print("✅ 组织ID索引已存在")
            else:
                print(f"❌ 添加组织ID索引失败: {e}")
        
        try:
            cursor.execute("ALTER TABLE t_device_info ADD INDEX idx_user_org (user_id, org_id)")
            print("✅ 添加用户组织复合索引")
        except Exception as e:
            if "Duplicate key name" in str(e):
                print("✅ 用户组织复合索引已存在")
            else:
                print(f"❌ 添加用户组织复合索引失败: {e}")
        
        # 5. 同步现有设备绑定数据
        print("\n📊 开始同步现有设备绑定数据...")
        
        # 检查表是否存在
        cursor.execute("SHOW TABLES LIKE 't_user_info'")
        if not cursor.fetchone():
            print("⚠️  t_user_info 表不存在，跳过数据同步")
        else:
            # 查询现有绑定关系并更新到设备表
            sync_existing_binds_sql = """
            UPDATE t_device_info di 
            JOIN (
                SELECT device_sn, user_id, 
                       ROW_NUMBER() OVER (PARTITION BY device_sn ORDER BY operate_time DESC) as rn
                FROM t_device_user 
                WHERE status = 'BIND' AND is_deleted = 0
            ) du ON di.serial_number = du.device_sn AND du.rn = 1
            LEFT JOIN t_user_info ui ON du.user_id = ui.id
            SET di.user_id = du.user_id,
                di.org_id = ui.org_id
            WHERE di.user_id IS NULL
            """
            
            cursor.execute(sync_existing_binds_sql)
            updated_count = cursor.rowcount
            print(f"✅ 同步现有绑定数据: {updated_count} 条设备绑定关系")
        
        # 6. 统计和验证
        print("\n📈 数据统计和验证:")
        
        cursor.execute("SELECT COUNT(*) FROM t_device_info WHERE user_id IS NOT NULL")
        bound_devices = cursor.fetchone()[0]
        print(f"📱 已绑定设备数量: {bound_devices}")
        
        cursor.execute("SELECT COUNT(*) FROM t_device_bind_request")
        request_count = cursor.fetchone()[0]
        print(f"📋 绑定申请记录: {request_count}")
        
        cursor.execute("SELECT COUNT(*) FROM t_device_user WHERE status = 'BIND'")
        bind_logs = cursor.fetchone()[0]
        print(f"📝 绑定操作日志: {bind_logs}")
        
        # 7. 验证表结构
        cursor.execute("SHOW CREATE TABLE t_device_bind_request")
        print(f"✅ 设备绑定申请表结构验证完成")
        
        conn.commit()
        print(f"\n🎉 设备绑定数据库表同步完成! 时间: {datetime.now()}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 同步过程中发生错误: {e}")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

def verify_tables():
    """验证表结构"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("\n🔍 验证设备绑定相关表结构...")
        
        # 验证 t_device_info 表字段
        cursor.execute("DESCRIBE t_device_info")
        device_fields = [row[0] for row in cursor.fetchall()]
        
        required_fields = ['user_id', 'org_id']
        missing_fields = [field for field in required_fields if field not in device_fields]
        
        if missing_fields:
            print(f"❌ t_device_info 表缺少字段: {missing_fields}")
        else:
            print("✅ t_device_info 表字段验证通过")
        
        # 验证 t_device_bind_request 表是否存在
        cursor.execute("SHOW TABLES LIKE 't_device_bind_request'")
        if cursor.fetchone():
            print("✅ t_device_bind_request 表存在")
        else:
            print("❌ t_device_bind_request 表不存在")
        
        print("🎯 表结构验证完成")
        
    except Exception as e:
        print(f"❌ 验证过程发生错误: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 LJWX 设备绑定数据库同步工具")
    print("=" * 60)
    
    # 执行同步
    sync_device_bind_tables()
    
    # 验证结果
    verify_tables()
    
    print("\n" + "=" * 60)
    print("✨ 同步完成! 现在可以使用设备绑定功能了")
    print("🌐 管理页面: http://localhost:5001/device_bind_management") 
    print("=" * 60) 
#!/usr/bin/env python3
"""同步现有设备绑定数据到新字段"""

import pymysql

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': '123456',
    'database': 'lj-06',
    'charset': 'utf8mb4'
}

def sync_bind_data():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # 查询所有有效绑定记录
        cursor.execute("""
            SELECT device_sn, user_id, operate_time
            FROM t_device_user 
            WHERE status = 'BIND' AND (is_deleted = 0 OR is_deleted IS NULL)
            ORDER BY device_sn, operate_time DESC
        """)
        
        bind_records = {}
        for device_sn, user_id, operate_time in cursor.fetchall():
            if device_sn not in bind_records:
                bind_records[device_sn] = user_id  # 只保留最新的绑定
        
        print(f"📱 找到 {len(bind_records)} 个设备的绑定记录")
        
        # 逐个更新设备信息
        updated = 0
        for device_sn, user_id in bind_records.items():
            cursor.execute("""
                UPDATE t_device_info 
                SET user_id = %s 
                WHERE serial_number = %s
            """, (user_id, device_sn))
            if cursor.rowcount > 0:
                updated += 1
        
        conn.commit()
        print(f"✅ 成功同步 {updated} 条设备绑定数据")
        
        # 验证结果
        cursor.execute("SELECT COUNT(*) FROM t_device_info WHERE user_id IS NOT NULL")
        bound_count = cursor.fetchone()[0]
        print(f"📊 当前已绑定设备数量: {bound_count}")
        
    except Exception as e:
        print(f"❌ 同步失败: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("🔄 开始同步现有设备绑定数据...")
    sync_bind_data()
    print("🎉 同步完成!") 
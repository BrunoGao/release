#!/usr/bin/env python3
"""AlertInfo数据诊断脚本"""
import pymysql

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
    return pymysql.connect(**DB_CONFIG)

def diagnose_alert_data():
    """诊断AlertInfo数据状态"""
    print("🔍 AlertInfo数据诊断")
    print("="*50)
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 1. 检查AlertInfo表结构
        print("1. 检查表结构:")
        cursor.execute("DESCRIBE t_alert_info")
        columns = cursor.fetchall()
        
        has_org_id = False
        has_user_id = False
        for col in columns:
            if col['Field'] == 'org_id':
                has_org_id = True
                print(f"  ✅ org_id字段: {col['Type']}, 可空: {col['Null']}")
            elif col['Field'] == 'user_id':
                has_user_id = True
                print(f"  ✅ user_id字段: {col['Type']}, 可空: {col['Null']}")
        
        if not has_org_id:
            print("  ❌ 缺少org_id字段")
        if not has_user_id:
            print("  ❌ 缺少user_id字段")
        
        # 2. 统计数据分布
        print("\n2. 数据分布统计:")
        
        cursor.execute("SELECT COUNT(*) as total FROM t_alert_info")
        total = cursor.fetchone()['total']
        print(f"  总告警数: {total}")
        
        if has_org_id:
            cursor.execute("SELECT COUNT(*) as count FROM t_alert_info WHERE org_id IS NOT NULL")
            org_count = cursor.fetchone()['count']
            print(f"  有org_id: {org_count} ({org_count/total*100:.1f}%)")
        
        if has_user_id:
            cursor.execute("SELECT COUNT(*) as count FROM t_alert_info WHERE user_id IS NOT NULL")
            user_count = cursor.fetchone()['count']
            print(f"  有user_id: {user_count} ({user_count/total*100:.1f}%)")
        
        # 3. 检查设备关联情况
        print("\n3. 设备关联情况:")
        cursor.execute("""
        SELECT DISTINCT device_sn 
        FROM t_alert_info 
        WHERE org_id IS NULL OR user_id IS NULL
        LIMIT 10
        """)
        missing_devices = cursor.fetchall()
        
        print(f"  缺少org_id/user_id的设备数: {len(missing_devices)}")
        for device in missing_devices[:5]:
            device_sn = device['device_sn']
            
            # 检查该设备是否有对应用户
            cursor.execute("""
            SELECT u.id as user_id, u.user_name, uo.org_id
            FROM sys_user u
            LEFT JOIN sys_user_org uo ON u.id = uo.user_id
            WHERE u.device_sn = %s AND u.is_deleted = 0
            """, (device_sn,))
            
            user_info = cursor.fetchone()
            if user_info:
                print(f"    设备{device_sn}: 用户ID={user_info['user_id']}, 组织ID={user_info['org_id']}")
            else:
                print(f"    设备{device_sn}: ❌ 未找到对应用户")
        
        # 4. 检查最近的告警
        print("\n4. 最近告警检查:")
        cursor.execute("""
        SELECT id, device_sn, org_id, user_id, alert_timestamp
        FROM t_alert_info 
        ORDER BY alert_timestamp DESC 
        LIMIT 5
        """)
        recent_alerts = cursor.fetchall()
        
        for alert in recent_alerts:
            print(f"  告警ID={alert['id']}: 设备={alert['device_sn']}, org_id={alert['org_id']}, user_id={alert['user_id']}")
        
        # 5. 检查org_id分布
        if has_org_id:
            print("\n5. org_id分布:")
            cursor.execute("""
            SELECT org_id, COUNT(*) as count 
            FROM t_alert_info 
            WHERE org_id IS NOT NULL 
            GROUP BY org_id 
            ORDER BY count DESC 
            LIMIT 10
            """)
            org_distribution = cursor.fetchall()
            
            for item in org_distribution:
                cursor.execute("SELECT name FROM sys_org_units WHERE id = %s", (item['org_id'],))
                org_name = cursor.fetchone()
                org_name = org_name['name'] if org_name else '未知组织'
                print(f"  组织ID={item['org_id']} ({org_name}): {item['count']}条告警")
        
    except Exception as e:
        print(f"❌ 诊断失败: {e}")
    finally:
        conn.close()

def test_device_user_mapping():
    """测试设备用户映射"""
    print("\n🔍 测试设备用户映射")
    print("="*50)
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 获取一些测试设备
        cursor.execute("""
        SELECT DISTINCT device_sn 
        FROM t_alert_info 
        WHERE device_sn IS NOT NULL 
        LIMIT 5
        """)
        test_devices = cursor.fetchall()
        
        for device in test_devices:
            device_sn = device['device_sn']
            print(f"\n设备: {device_sn}")
            
            # 查询用户信息
            cursor.execute("""
            SELECT u.id as user_id, u.user_name, u.real_name, uo.org_id, o.name as org_name
            FROM sys_user u
            LEFT JOIN sys_user_org uo ON u.id = uo.user_id
            LEFT JOIN sys_org_units o ON uo.org_id = o.id
            WHERE u.device_sn = %s AND u.is_deleted = 0
            """, (device_sn,))
            
            user_info = cursor.fetchone()
            if user_info:
                print(f"  ✅ 用户ID: {user_info['user_id']}")
                print(f"  ✅ 用户名: {user_info['user_name']}")
                print(f"  ✅ 真实姓名: {user_info['real_name']}")
                print(f"  ✅ 组织ID: {user_info['org_id']}")
                print(f"  ✅ 组织名: {user_info['org_name']}")
            else:
                print(f"  ❌ 未找到对应用户")
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    diagnose_alert_data()
    test_device_user_mapping() 
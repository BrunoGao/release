#!/usr/bin/env python3
"""AlertInfo表org_id和user_id字段数据同步脚本（简化版）"""
import pymysql
import json

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

def get_device_user_org_info(device_sn):
    """根据设备序列号获取用户和组织信息"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 查询用户信息
        user_query = """
        SELECT u.id as user_id, u.user_name, uo.org_id
        FROM sys_user u
        LEFT JOIN sys_user_org uo ON u.id = uo.user_id
        WHERE u.device_sn = %s AND u.is_deleted = 0
        LIMIT 1
        """
        
        cursor.execute(user_query, (device_sn,))
        result = cursor.fetchone()
        
        if result:
            return {
                'success': True,
                'user_id': result['user_id'],
                'user_name': result['user_name'],
                'org_id': result['org_id']
            }
        else:
            return {'success': False, 'message': f'设备{device_sn}未找到对应用户'}
            
    except Exception as e:
        return {'success': False, 'message': str(e)}
    finally:
        conn.close()

def sync_alert_org_user_ids():
    """同步AlertInfo表的org_id和user_id字段"""
    print("🔄 开始同步AlertInfo表的org_id和user_id字段...")
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 查询所有缺少org_id或user_id的AlertInfo记录
        query = """
        SELECT id, device_sn, org_id, user_id 
        FROM t_alert_info 
        WHERE org_id IS NULL OR user_id IS NULL
        """
        
        cursor.execute(query)
        alerts_to_update = cursor.fetchall()
        
        print(f"📊 找到{len(alerts_to_update)}条需要更新的记录")
        
        updated_count = 0
        error_count = 0
        
        for alert in alerts_to_update:
            try:
                # 根据device_sn获取用户和组织信息
                device_info = get_device_user_org_info(alert['device_sn'])
                
                if device_info.get('success'):
                    # 构建更新SQL
                    updates = []
                    params = []
                    
                    if not alert['org_id'] and device_info.get('org_id'):
                        updates.append("org_id = %s")
                        params.append(device_info.get('org_id'))
                    
                    if not alert['user_id'] and device_info.get('user_id'):
                        updates.append("user_id = %s")
                        params.append(device_info.get('user_id'))
                    
                    if updates:
                        update_sql = f"UPDATE t_alert_info SET {', '.join(updates)} WHERE id = %s"
                        params.append(alert['id'])
                        
                        cursor.execute(update_sql, params)
                        updated_count += 1
                        
                        if updated_count % 100 == 0:
                            print(f"⏳ 已处理{updated_count}条记录...")
                            conn.commit()  # 批量提交
                else:
                    print(f"⚠️ 设备{alert['device_sn']}未找到对应用户信息")
                    error_count += 1
                    
            except Exception as e:
                print(f"❌ 处理告警ID={alert['id']}失败: {e}")
                error_count += 1
                
        # 最终提交
        conn.commit()
        print(f"✅ 同步完成!")
        print(f"📈 成功更新: {updated_count}条")
        print(f"❌ 失败: {error_count}条")
        
    except Exception as e:
        print(f"❌ 同步失败: {e}")
        conn.rollback()
    finally:
        conn.close()

def verify_sync_result():
    """验证同步结果"""
    print("\n🔍 验证同步结果...")
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # 统计有org_id和user_id的记录数
        cursor.execute("SELECT COUNT(*) FROM t_alert_info")
        total_alerts = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM t_alert_info WHERE org_id IS NOT NULL")
        alerts_with_org = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM t_alert_info WHERE user_id IS NOT NULL")
        alerts_with_user = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM t_alert_info WHERE org_id IS NOT NULL AND user_id IS NOT NULL")
        alerts_with_both = cursor.fetchone()[0]
        
        print(f"📊 告警记录统计:")
        print(f"  总记录数: {total_alerts}")
        if total_alerts > 0:
            print(f"  有org_id: {alerts_with_org} ({alerts_with_org/total_alerts*100:.1f}%)")
            print(f"  有user_id: {alerts_with_user} ({alerts_with_user/total_alerts*100:.1f}%)")
            print(f"  两者都有: {alerts_with_both} ({alerts_with_both/total_alerts*100:.1f}%)")
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
    finally:
        conn.close()

def create_indexes():
    """为新字段创建索引以优化查询性能"""
    print("\n🔧 创建索引优化查询性能...")
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # 为org_id创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alert_org_id ON t_alert_info(org_id)")
        
        # 为user_id创建索引  
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alert_user_id ON t_alert_info(user_id)")
        
        # 为org_id+user_id组合创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alert_org_user ON t_alert_info(org_id, user_id)")
        
        conn.commit()
        print("✅ 索引创建完成")
        
    except Exception as e:
        print(f"⚠️ 索引创建失败(可能已存在): {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 AlertInfo表org_id和user_id字段同步工具（简化版）")
    print("="*60)
    
    # 1. 同步数据
    sync_alert_org_user_ids()
    
    # 2. 验证结果
    verify_sync_result()
    
    # 3. 创建索引
    create_indexes()
    
    print("\n🎉 同步任务完成!") 
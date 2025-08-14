#!/usr/bin/env python3
"""
健康数据检查脚本 - 诊断为什么健康数据返回为空
"""

import pymysql
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_health_data():
    """检查健康数据情况"""
    try:
        # 数据库连接
        conn = pymysql.connect(
            host='127.0.0.1',
            port=3306,
            user='root',
            password='123456',
            database='lj-06',
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        
        print("🔍 健康数据诊断报告")
        print("=" * 60)
        
        # 1. 检查健康数据表是否存在
        print("\n📋 1. 检查健康数据表:")
        cursor.execute("SHOW TABLES LIKE '%health%'")
        health_tables = cursor.fetchall()
        for table in health_tables:
            print(f"  ✅ 表: {table[0]}")
        
        # 2. 检查主要健康数据表的记录数
        tables_to_check = ['t_user_health_data_new', 't_user_health_data', 'user_health_data']
        
        print("\n📊 2. 检查健康数据记录数:")
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  📈 {table}: {count:,} 条记录")
                
                if count > 0:
                    # 检查最新记录
                    cursor.execute(f"SELECT * FROM {table} ORDER BY id DESC LIMIT 1")
                    latest = cursor.fetchone()
                    print(f"    🕐 最新记录ID: {latest[0] if latest else 'N/A'}")
                    
                    # 检查组织1的记录
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE org_id = 1")
                        org_count = cursor.fetchone()[0]
                        print(f"    🏢 组织1记录: {org_count:,} 条")
                    except:
                        print(f"    ⚠️  组织1记录: 无org_id字段")
                    
                    # 检查设备关联
                    try:
                        cursor.execute(f"SELECT COUNT(DISTINCT device_sn) FROM {table}")
                        device_count = cursor.fetchone()[0] 
                        print(f"    📱 关联设备: {device_count:,} 台")
                    except:
                        print(f"    ⚠️  关联设备: 无device_sn字段")
                        
            except Exception as e:
                print(f"  ❌ {table}: 表不存在 ({e})")
        
        # 3. 检查设备信息
        print("\n📱 3. 检查设备信息:")
        try:
            cursor.execute("SELECT COUNT(*) FROM t_device_info")
            device_total = cursor.fetchone()[0]
            print(f"  📈 设备总数: {device_total:,} 台")
            
            cursor.execute("SELECT COUNT(*) FROM t_device_info WHERE org_id = 1")
            org_devices = cursor.fetchone()[0]
            print(f"  🏢 组织1设备: {org_devices:,} 台")
            
            # 检查设备SN样例
            cursor.execute("SELECT serial_number FROM t_device_info WHERE org_id = 1 LIMIT 5")
            device_sns = cursor.fetchall()
            print(f"  📋 设备SN样例: {[d[0] for d in device_sns]}")
            
        except Exception as e:
            print(f"  ❌ 设备信息检查失败: {e}")
        
        # 4. 检查用户信息
        print("\n👤 4. 检查用户信息:")
        try:
            cursor.execute("SELECT COUNT(*) FROM sys_user")
            user_total = cursor.fetchone()[0]
            print(f"  📈 用户总数: {user_total:,} 人")
            
            # 检查用户设备关联
            cursor.execute("SELECT COUNT(*) FROM sys_user WHERE device_sn IS NOT NULL AND device_sn != ''")
            users_with_device = cursor.fetchone()[0]
            print(f"  📱 有设备用户: {users_with_device:,} 人")
            
        except Exception as e:
            print(f"  ❌ 用户信息检查失败: {e}")
        
        # 5. 检查数据配置
        print("\n⚙️  5. 检查健康数据配置:")
        try:
            cursor.execute("SELECT COUNT(*) FROM t_health_data_config WHERE customer_id = 1")
            config_count = cursor.fetchone()[0]
            print(f"  📈 组织1配置: {config_count:,} 条")
            
            if config_count > 0:
                cursor.execute("SELECT data_type, is_enabled FROM t_health_data_config WHERE customer_id = 1")
                configs = cursor.fetchall()
                enabled_types = [c[0] for c in configs if c[1] == 1]
                print(f"  ✅ 启用指标: {enabled_types}")
                
        except Exception as e:
            print(f"  ❌ 配置检查失败: {e}")
        
        # 6. 检查最近的健康数据
        print("\n🕐 6. 检查最近健康数据:")
        main_table = 't_user_health_data_new'
        try:
            # 检查最近一天的数据
            cursor.execute(f"""
                SELECT COUNT(*), MIN(timestamp), MAX(timestamp) 
                FROM {main_table} 
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 1 DAY)
            """)
            recent_data = cursor.fetchone()
            print(f"  📈 最近24小时: {recent_data[0]:,} 条记录")
            print(f"  🕐 时间范围: {recent_data[1]} 到 {recent_data[2]}")
            
            # 检查组织1的最近数据
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM {main_table} 
                WHERE org_id = 1 AND timestamp >= DATE_SUB(NOW(), INTERVAL 1 DAY)
            """)
            org_recent = cursor.fetchone()[0]
            print(f"  🏢 组织1最近24小时: {org_recent:,} 条记录")
            
        except Exception as e:
            print(f"  ❌ 最近数据检查失败: {e}")
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("🎯 诊断建议:")
        
        if org_recent == 0:
            print("❌ 问题: 组织1最近24小时没有健康数据")
            print("💡 建议: 检查数据上传或org_id匹配问题")
        elif device_total > 0 and users_with_device == 0:
            print("❌ 问题: 有设备但用户没有关联设备")
            print("💡 建议: 检查用户设备关联配置")
        else:
            print("✅ 数据库状态正常，可能是查询逻辑问题")
            
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")

if __name__ == "__main__":
    check_health_data() 
#!/usr/bin/env python3
import pymysql

conn = pymysql.connect(host='127.0.0.1', user='root', password='123456', database='lj-06')
cursor = conn.cursor()

print("🔍 检查最近健康数据:")

# 检查最近24小时数据
cursor.execute('SELECT COUNT(*) FROM t_user_health_data WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 1 DAY)')
recent = cursor.fetchone()[0]
print(f'📈 最近24小时数据: {recent:,} 条')

# 检查组织1的数据 - 通过user_id关联
cursor.execute('''
    SELECT COUNT(*) FROM t_user_health_data h
    JOIN sys_user u ON h.user_id = u.id 
    WHERE u.customer_id = 1 AND h.timestamp >= DATE_SUB(NOW(), INTERVAL 1 DAY)
''')
org_recent = cursor.fetchone()[0] 
print(f'🏢 组织1最近24小时: {org_recent:,} 条')

# 检查数据表字段结构
cursor.execute('DESCRIBE t_user_health_data')
fields = cursor.fetchall()
print(f"\n📋 t_user_health_data 表字段:")
for field in fields[:10]:  # 显示前10个字段
    print(f"  - {field[0]} ({field[1]})")

# 检查是否有org_id字段
has_org_id = any(field[0] == 'org_id' for field in fields)
print(f"\n🔍 是否有org_id字段: {'✅ 是' if has_org_id else '❌ 否'}")

if has_org_id:
    cursor.execute('SELECT COUNT(*) FROM t_user_health_data WHERE org_id = 1 AND timestamp >= DATE_SUB(NOW(), INTERVAL 1 DAY)')
    org_direct = cursor.fetchone()[0]
    print(f'🏢 通过org_id查询组织1最近24小时: {org_direct:,} 条')

# 检查最新的几条记录
cursor.execute('SELECT id, user_id, device_sn, timestamp FROM t_user_health_data ORDER BY id DESC LIMIT 3')
latest_records = cursor.fetchall()
print(f"\n🕐 最新3条记录:")
for record in latest_records:
    print(f"  ID: {record[0]}, 用户: {record[1]}, 设备: {record[2]}, 时间: {record[3]}")

conn.close() 
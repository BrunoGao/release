#!/usr/bin/env python3
import mysql.connector
import sys

DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root', 
    'password': '123456',
    'database': 'test',
    'port': 3306
}

def query_dept_users(dept_id):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        print('✅ 数据库连接成功')
        
        # 查看是否有该部门
        cursor.execute('SELECT id, name FROM sys_org_units WHERE id = %s', (dept_id,))
        dept = cursor.fetchone()
        
        if dept:
            print(f'📋 找到部门: {dept["name"]} (ID: {dept["id"]})')
            
            # 查询该部门下的员工（过滤管理员）
            sql = '''
            SELECT DISTINCT u.id, u.user_name, u.device_sn
            FROM sys_user u 
            JOIN sys_user_org uo ON u.id = uo.user_id 
            WHERE uo.org_id = %s 
            AND u.device_sn IS NOT NULL 
            AND u.device_sn != '' 
            AND u.device_sn != '-' 
            AND u.is_deleted = 0
            AND NOT EXISTS (
                SELECT 1 FROM sys_user_role ur 
                JOIN sys_role r ON ur.role_id = r.id 
                WHERE ur.user_id = u.id AND r.is_admin = 1
            )
            ORDER BY u.user_name
            '''
            
            cursor.execute(sql, (dept_id,))
            users = cursor.fetchall()
            
            print(f'👥 部门员工列表 (共{len(users)}人):')
            for user in users:
                print(f'  - {user["user_name"]} (ID: {user["id"]}, 设备: {user["device_sn"]})')
                
            cursor.close()
            conn.close()
            return users
            
        else:
            print('⚠️ 未找到指定部门，查看现有部门:')
            cursor.execute('SELECT id, name FROM sys_org_units ORDER BY id LIMIT 10')
            depts = cursor.fetchall()
            for d in depts:
                print(f'  - {d["name"]} (ID: {d["id"]})')
            
            cursor.close()
            conn.close()
            return []
        
    except Exception as e:
        print(f'❌ 操作失败: {e}')
        import traceback
        traceback.print_exc()
        return []

if __name__ == '__main__':
    dept_id = 1923231005240295439
    users = query_dept_users(dept_id) 
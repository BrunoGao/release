#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据库检查脚本"""
import mysql.connector

try:
    conn=mysql.connector.connect(
        host='127.0.0.1',
        port=3306,
        user='root',
        password='123456',
        database='lj-06',
        charset='utf8mb4'
    )
    cursor=conn.cursor()
    
    print("✅ 数据库连接成功")
    
    # 检查sys_user表结构
    cursor.execute("DESCRIBE sys_user")
    print("\n📋 sys_user表结构:")
    for row in cursor.fetchall():
        print(f"  {row[0]} - {row[1]} - {'NULL' if row[2]=='YES' else 'NOT NULL'}")
        
    # 检查sys_user_org表结构  
    cursor.execute("DESCRIBE sys_user_org")
    print("\n📋 sys_user_org表结构:")
    for row in cursor.fetchall():
        print(f"  {row[0]} - {row[1]} - {'NULL' if row[2]=='YES' else 'NOT NULL'}")
        
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ 数据库检查失败: {e}") 
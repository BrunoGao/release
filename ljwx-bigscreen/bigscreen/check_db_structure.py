#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pymysql
import os

def check_baseline_table():
    """检查t_health_baseline表结构"""
    try:
        # 数据库连接配置
        connection = pymysql.connect(
            host=os.environ.get('MYSQL_HOST', '127.0.0.1'),
            port=int(os.environ.get('MYSQL_PORT', '3306')),
            user=os.environ.get('MYSQL_USER', 'root'),
            password=os.environ.get('MYSQL_PASSWORD', '123456'),
            database=os.environ.get('MYSQL_DATABASE', 'lj-06'),
            charset='utf8mb4'
        )
        
        print("=== 检查t_health_baseline表结构 ===")
        
        with connection.cursor() as cursor:
            # 检查表是否存在
            cursor.execute("SHOW TABLES LIKE 't_health_baseline'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                print("❌ t_health_baseline表不存在")
                return
            
            print("✅ t_health_baseline表存在")
            
            # 获取表结构
            cursor.execute("DESCRIBE t_health_baseline")
            columns = cursor.fetchall()
            
            print("\n表字段结构:")
            print("-" * 60)
            print(f"{'字段名':<20} {'类型':<15} {'是否为空':<8} {'键':<8} {'默认值':<10}")
            print("-" * 60)
            
            for column in columns:
                field, type_, null, key, default, extra = column
                print(f"{field:<20} {type_:<15} {null:<8} {key:<8} {str(default):<10}")
            
            # 检查记录数
            cursor.execute("SELECT COUNT(*) FROM t_health_baseline")
            count = cursor.fetchone()[0]
            print(f"\n当前记录数: {count}")
            
            # 检查最近的记录
            if count > 0:
                cursor.execute("SELECT * FROM t_health_baseline ORDER BY create_time DESC LIMIT 3")
                recent_records = cursor.fetchall()
                print(f"\n最近3条记录:")
                for i, record in enumerate(recent_records, 1):
                    print(f"记录{i}: {record}")
            
        connection.close()
        
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")

if __name__ == "__main__":
    check_baseline_table() 
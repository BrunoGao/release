#!/usr/bin/env python3
from db_config import load_db_config

def check_table_structure():
    db_config = load_db_config()
    
    if not db_config.connect():
        print("数据库连接失败")
        return
    
    try:
        cursor = db_config.connection.cursor()
        
        # 查看所有表
        print("=== 查看数据库中的所有表 ===")
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"找到 {len(tables)} 个表:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # 查看 sys_user 表结构（如果存在）
        user_table = None
        device_table = None
        
        for table in tables:
            table_name = table[0]
            if 'user' in table_name.lower():
                user_table = table_name
                print(f"\n=== {table_name} 表结构 ===")
                cursor.execute(f"DESCRIBE {table_name}")
                columns = cursor.fetchall()
                for col in columns:
                    print(f"  {col[0]} - {col[1]} - {col[2]} - {col[3]}")
            
            if 'device' in table_name.lower():
                device_table = table_name
                print(f"\n=== {table_name} 表结构 ===")
                cursor.execute(f"DESCRIBE {table_name}")
                columns = cursor.fetchall()
                for col in columns:
                    print(f"  {col[0]} - {col[1]} - {col[2]} - {col[3]}")
        
        # 查看表中的数据量
        if user_table:
            cursor.execute(f"SELECT COUNT(*) FROM {user_table}")
            count = cursor.fetchone()[0]
            print(f"\n{user_table} 表中有 {count} 条记录")
            
            if count > 0:
                cursor.execute(f"SELECT * FROM {user_table} LIMIT 3")
                rows = cursor.fetchall()
                print("前3条记录:")
                for row in rows:
                    print(f"  {row}")
        
        if device_table:
            cursor.execute(f"SELECT COUNT(*) FROM {device_table}")
            count = cursor.fetchone()[0]
            print(f"\n{device_table} 表中有 {count} 条记录")
            
            if count > 0:
                cursor.execute(f"SELECT * FROM {device_table} LIMIT 3")
                rows = cursor.fetchall()
                print("前3条记录:")
                for row in rows:
                    print(f"  {row}")
        
        cursor.close()
        
    except Exception as e:
        print(f"查询错误: {e}")
    finally:
        db_config.disconnect()

if __name__ == "__main__":
    check_table_structure()
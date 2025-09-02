#!/usr/bin/env python3
"""
用户查询性能优化 - 数据库索引添加脚本
针对2000用户查询优化，目标1秒内返回
"""

import pymysql
import time

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
        conn = pymysql.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return None

def check_existing_indexes():
    """检查现有索引"""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        tables = ['sys_user', 'sys_user_org', 'sys_org_units', 't_device_info', 'sys_user_position', 'sys_position']
        
        print("📊 当前索引状态:")
        print("=" * 80)
        
        for table in tables:
            print(f"\n🔍 {table} 表索引:")
            cursor.execute(f"SHOW INDEX FROM {table}")
            indexes = cursor.fetchall()
            
            if indexes:
                for idx in indexes:
                    print(f"   {idx[2]} -> {idx[4]} ({'UNIQUE' if not idx[1] else 'NORMAL'})")
            else:
                print("   无索引")
                
    except Exception as e:
        print(f"❌ 检查索引失败: {e}")
    finally:
        conn.close()

def check_table_sizes():
    """检查表大小"""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        tables = ['sys_user', 'sys_user_org', 'sys_org_units', 't_device_info', 'sys_user_position', 'sys_position']
        
        print("\n📈 表数据量统计:")
        print("=" * 50)
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"{table:20} | {count:8} 条记录")
            
    except Exception as e:
        print(f"❌ 检查表大小失败: {e}")
    finally:
        conn.close()

def create_optimized_indexes():
    """创建优化索引"""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # 用户查询核心索引
        indexes_to_create = [
            # sys_user表核心索引
            {
                'table': 'sys_user',
                'name': 'idx_user_customer_deleted_status',
                'columns': 'customer_id, is_deleted, status',
                'purpose': '组织用户查询核心索引'
            },
            {
                'table': 'sys_user',
                'name': 'idx_user_device_sn',
                'columns': 'device_sn',
                'purpose': '设备关联查询'
            },
            
            # sys_user_org表关联索引
            {
                'table': 'sys_user_org',
                'name': 'idx_user_org_user_id',
                'columns': 'user_id',
                'purpose': '用户组织关联'
            },
            {
                'table': 'sys_user_org',
                'name': 'idx_user_org_org_id',
                'columns': 'org_id',
                'purpose': '组织用户关联'
            },
            
            # sys_org表层级查询索引
            {
                'table': 'sys_org_units',
                'name': 'idx_org_ancestors',
                'columns': 'ancestors(100)',  # 前缀索引
                'purpose': '组织层级查询'
            },
            {
                'table': 'sys_org_units',
                'name': 'idx_org_id_status',
                'columns': 'id, status',
                'purpose': '组织状态查询'
            },
            
            # t_device_info表设备关联索引  
            {
                'table': 't_device_info',
                'name': 'idx_device_serial_status',
                'columns': 'serial_number, status',
                'purpose': '设备状态查询'
            },
            
            # sys_user_position表职位关联索引
            {
                'table': 'sys_user_position',
                'name': 'idx_user_pos_user_id',
                'columns': 'user_id',
                'purpose': '用户职位关联'
            },
            {
                'table': 'sys_user_position', 
                'name': 'idx_user_pos_position_id',
                'columns': 'position_id',
                'purpose': '职位用户关联'
            }
        ]
        
        print("\n🚀 创建优化索引:")
        print("=" * 80)
        
        created_count = 0
        skipped_count = 0
        
        for idx_info in indexes_to_create:
            try:
                # 检查索引是否已存在
                cursor.execute(f"SHOW INDEX FROM {idx_info['table']} WHERE Key_name = '{idx_info['name']}'")
                existing = cursor.fetchone()
                
                if existing:
                    print(f"⏭️  {idx_info['name']} 已存在，跳过")
                    skipped_count += 1
                    continue
                
                # 创建索引
                sql = f"CREATE INDEX {idx_info['name']} ON {idx_info['table']} ({idx_info['columns']})"
                print(f"📝 创建: {idx_info['name']} -> {idx_info['purpose']}")
                
                start_time = time.time()
                cursor.execute(sql)
                conn.commit()
                create_time = round(time.time() - start_time, 2)
                
                print(f"✅ 完成: {idx_info['name']} ({create_time}s)")
                created_count += 1
                
            except Exception as e:
                print(f"❌ 创建索引失败 {idx_info['name']}: {e}")
        
        print(f"\n📊 索引创建完成: 新建 {created_count} 个, 跳过 {skipped_count} 个")
        
    except Exception as e:
        print(f"❌ 创建索引失败: {e}")
    finally:
        conn.close()

def test_query_performance():
    """测试查询性能"""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # 测试用户查询性能
        test_queries = [
            {
                'name': '用户基础查询',
                'sql': "SELECT COUNT(*) FROM sys_user WHERE customer_id = 1 AND is_deleted = 0"
            },
            {
                'name': '用户组织关联查询',
                'sql': """
                SELECT COUNT(DISTINCT u.id)
                FROM sys_user u
                LEFT JOIN sys_user_org uo ON u.id = uo.user_id
                LEFT JOIN sys_org_units o ON uo.org_id = o.id
                WHERE (o.id = 1 OR o.ancestors LIKE '%,1,%')
                AND u.is_deleted = 0
                """
            },
            {
                'name': '完整用户查询(前100条)',
                'sql': """
                SELECT DISTINCT u.id, u.user_name, u.device_sn, u.status,
                       o.name as dept_name, d.status as device_status
                FROM sys_user u
                LEFT JOIN sys_user_org uo ON u.id = uo.user_id
                LEFT JOIN sys_org_units o ON uo.org_id = o.id
                LEFT JOIN t_device_info d ON u.device_sn = d.serial_number
                WHERE (o.id = 1 OR o.ancestors LIKE '%,1,%')
                AND u.is_deleted = 0
                ORDER BY u.id
                LIMIT 100
                """
            }
        ]
        
        print("\n⚡ 查询性能测试:")
        print("=" * 60)
        
        for query in test_queries:
            print(f"\n🔍 {query['name']}")
            
            start_time = time.time()
            cursor.execute(query['sql'])
            results = cursor.fetchall()
            query_time = round(time.time() - start_time, 3)
            
            result_count = len(results) if isinstance(results, (list, tuple)) else results[0][0] if results else 0
            
            status = "🟢 优秀" if query_time < 0.1 else "🟡 良好" if query_time < 0.5 else "🟠 需优化" if query_time < 2.0 else "🔴 慢"
            
            print(f"   耗时: {query_time}s | 结果: {result_count} | {status}")
            
    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
    finally:
        conn.close()

def main():
    """主函数"""
    print("🔧 用户查询性能优化工具")
    print("目标: 2000用户查询 < 1秒")
    print("=" * 80)
    
    # 1. 检查当前状态
    check_table_sizes()
    check_existing_indexes()
    
    # 2. 创建优化索引
    create_optimized_indexes()
    
    # 3. 性能测试
    test_query_performance()
    
    print("\n🎯 优化建议:")
    print("1. 使用组合索引加速多表JOIN查询")
    print("2. 为ancestors字段创建前缀索引支持LIKE查询")
    print("3. 避免SELECT *，只查询必要字段")
    print("4. 考虑分页查询大数据集")
    print("5. 适当增加Redis缓存时间")

if __name__ == "__main__":
    main() 
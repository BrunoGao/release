#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""设备查询诊断脚本-针对500规模优化"""

import sys,os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from bigScreen.models import db,DeviceInfo,UserInfo,UserOrg,OrgInfo
from config import SQLALCHEMY_DATABASE_URI
from sqlalchemy import create_engine,text
import json

def diagnose_device_query():
    """诊断设备查询问题"""
    print("🔍 开始诊断设备查询问题...")
    
    # 创建数据库连接
    engine = create_engine(SQLALCHEMY_DATABASE_URI)
    
    try:
        # 1. 检查各表的数据量
        print("\n📊 检查各表数据量:")
        tables = ['sys_user', 'sys_user_org', 'sys_org_units', 't_device_info']
        
        with engine.connect() as conn:
            for table in tables:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) as count FROM {table}"))
                    count = result.fetchone()[0]
                    print(f"   {table}: {count} 条记录")
                except Exception as e:
                    print(f"   {table}: 查询失败 - {e}")
            
            # 2. 检查关键字段
            print("\n🔗 检查关键关联字段:")
            
            # 检查用户表中有device_sn的用户数量
            try:
                result = conn.execute(text("""
                    SELECT COUNT(*) as count 
                    FROM sys_user 
                    WHERE device_sn IS NOT NULL 
                    AND device_sn != '' 
                    AND is_deleted = 0
                """))
                user_with_device = result.fetchone()[0]
                print(f"   有设备序列号的用户: {user_with_device} 个")
            except Exception as e:
                print(f"   用户设备关联检查失败: {e}")
            
            # 检查设备表中的设备数量
            try:
                result = conn.execute(text("""
                    SELECT COUNT(*) as count 
                    FROM t_device_info 
                    WHERE is_deleted = 0
                """))
                active_devices = result.fetchone()[0]
                print(f"   活跃设备数量: {active_devices} 个")
            except Exception as e:
                print(f"   设备数量检查失败: {e}")
            
            # 3. 检查device_sn关联情况
            print("\n🔍 检查device_sn关联情况:")
            try:
                result = conn.execute(text("""
                    SELECT COUNT(*) as matched_count
                    FROM sys_user u
                    INNER JOIN t_device_info d ON u.device_sn = d.serial_number
                    WHERE u.is_deleted = 0 AND d.is_deleted = 0
                """))
                matched = result.fetchone()[0]
                print(f"   成功关联的用户-设备对: {matched} 对")
            except Exception as e:
                print(f"   关联检查失败: {e}")
            
            # 4. 针对orgId=1进行具体查询测试
            print("\n🎯 测试orgId=1的查询:")
            try:
                # 查询组织下的用户
                result = conn.execute(text("""
                    SELECT u.id, u.user_name, u.device_sn, o.name as org_name
                    FROM sys_user u
                    INNER JOIN sys_user_org uo ON u.id = uo.user_id
                    INNER JOIN sys_org_units o ON uo.org_id = o.id
                    WHERE uo.org_id = 1 
                    AND u.is_deleted = 0 
                    AND uo.is_deleted = 0
                    AND o.is_deleted = 0
                    LIMIT 10
                """))
                users = result.fetchall()
                print(f"   组织1下的用户数量: {len(users)} (显示前10个)")
                for user in users:
                    print(f"     用户: {user[1]}, 设备序列号: {user[2]}, 部门: {user[3]}")
            except Exception as e:
                print(f"   组织用户查询失败: {e}")
            
            # 5. 优化查询测试(适合500规模)
            print("\n⚡ 测试优化查询(500规模):")
            try:
                # 方案1: 先获取设备序列号，再批量查询设备
                result = conn.execute(text("""
                    SELECT DISTINCT u.device_sn
                    FROM sys_user u
                    INNER JOIN sys_user_org uo ON u.id = uo.user_id
                    WHERE uo.org_id = 1 
                    AND u.device_sn IS NOT NULL 
                    AND u.device_sn != ''
                    AND u.is_deleted = 0 
                    AND uo.is_deleted = 0
                    LIMIT 20
                """))
                device_sns = [row[0] for row in result.fetchall()]
                print(f"   获取到设备序列号: {len(device_sns)} 个")
                
                if device_sns:
                    # 查询对应的设备信息
                    device_sns_str = "'" + "','".join(device_sns[:10]) + "'"
                    result = conn.execute(text(f"""
                        SELECT serial_number, status, battery_level, charging_status
                        FROM t_device_info
                        WHERE serial_number IN ({device_sns_str})
                        AND is_deleted = 0
                    """))
                    devices = result.fetchall()
                    print(f"   找到对应设备: {len(devices)} 个")
                    for device in devices[:5]:
                        print(f"     设备: {device[0]}, 状态: {device[1]}, 电量: {device[2]}%, 充电: {device[3]}")
                        
                    # 检查未找到设备的序列号
                    found_sns = [d[0] for d in devices]
                    missing_sns = [sn for sn in device_sns[:10] if sn not in found_sns]
                    if missing_sns:
                        print(f"   未找到设备的序列号: {missing_sns}")
                        
            except Exception as e:
                print(f"   优化查询测试失败: {e}")
            
            # 6. 检查表结构
            print("\n🏗️ 检查表结构:")
            try:
                # 检查sys_user表结构
                result = conn.execute(text("DESCRIBE sys_user"))
                user_columns = [row[0] for row in result.fetchall()]
                print(f"   sys_user表字段: {user_columns}")
                
                # 检查t_device_info表结构
                result = conn.execute(text("DESCRIBE t_device_info"))
                device_columns = [row[0] for row in result.fetchall()]
                print(f"   t_device_info表字段: {device_columns}")
                
            except Exception as e:
                print(f"   表结构检查失败: {e}")
    
    except Exception as e:
        print(f"❌ 诊断过程出错: {e}")
    finally:
        engine.dispose()
    
    # 性能分析建议
    print("\n📈 性能优化建议(500规模):")
    print("   1. 添加索引: CREATE INDEX idx_user_device_sn ON sys_user(device_sn)")
    print("   2. 添加索引: CREATE INDEX idx_user_org_orgid ON sys_user_org(org_id, user_id)")
    print("   3. 使用分页查询，每页50-100条记录")
    print("   4. 启用Redis缓存，缓存时间5-10分钟")
    print("   5. 考虑读写分离，查询使用只读副本")

def create_optimized_query():
    """创建500规模优化查询函数"""
    print("\n🚀 生成优化查询代码...")
    
    optimized_code = '''
def fetch_devices_by_orgId_optimized(orgId, userId=None, page=1, page_size=50):
    """针对500规模优化的设备查询-分页+缓存+索引优化"""
    import time
    from sqlalchemy import text
    
    start_time = time.time()
    cache_key = f"devices_org_{orgId}_user_{userId or 'all'}_page_{page}"
    
    # 1. 检查Redis缓存(5分钟)
    try:
        cached = redis.get(cache_key)
        if cached:
            print(f"缓存命中: {cache_key}")
            return json.loads(cached)
    except: pass
    
    try:
        # 2. 分步查询策略(适合500规模)
        if userId:
            # 单用户模式
            user_device_query = text("""
                SELECT u.device_sn, u.user_name, o.name as dept_name, u.id as user_id
                FROM sys_user u
                LEFT JOIN sys_user_org uo ON u.id = uo.user_id
                LEFT JOIN sys_org_units o ON uo.org_id = o.id
                WHERE u.id = :user_id AND u.is_deleted = 0
            """)
            user_devices = db.session.execute(user_device_query, {"user_id": userId}).fetchall()
        else:
            # 组织模式-使用LIMIT分页
            offset = (page - 1) * page_size
            org_device_query = text("""
                SELECT u.device_sn, u.user_name, o.name as dept_name, u.id as user_id
                FROM sys_user u
                INNER JOIN sys_user_org uo ON u.id = uo.user_id
                INNER JOIN sys_org_units o ON uo.org_id = o.id
                WHERE uo.org_id = :org_id 
                AND u.device_sn IS NOT NULL 
                AND u.device_sn != ''
                AND u.is_deleted = 0 
                AND uo.is_deleted = 0
                ORDER BY u.id
                LIMIT :limit OFFSET :offset
            """)
            user_devices = db.session.execute(org_device_query, {
                "org_id": orgId, "limit": page_size, "offset": offset
            }).fetchall()
        
        # 3. 批量查询设备信息
        device_sns = [ud[0] for ud in user_devices if ud[0]]
        if not device_sns:
            return {"success": True, "data": {"devices": [], "total": 0}}
        
        # 使用IN查询(500个设备可以一次查询)
        device_query = text("""
            SELECT serial_number, status, battery_level, charging_status, 
                   wearable_status, system_software_version, timestamp,
                   create_time, update_time
            FROM t_device_info
            WHERE serial_number IN :device_sns AND is_deleted = 0
        """)
        devices = db.session.execute(device_query, {"device_sns": tuple(device_sns)}).fetchall()
        
        # 4. 组装结果数据
        device_map = {d[0]: d for d in devices}
        result_devices = []
        
        for ud in user_devices:
            device_sn, user_name, dept_name, user_id = ud
            if device_sn in device_map:
                device = device_map[device_sn]
                result_devices.append({
                    "serial_number": device_sn,
                    "user_name": user_name,
                    "department_name": dept_name or "未分配",
                    "user_id": user_id,
                    "status": device[1],
                    "battery_level": device[2],
                    "charging_status": device[3],
                    "wearable_status": device[4],
                    "system_software_version": device[5],
                    "timestamp": device[6].strftime("%Y-%m-%d %H:%M:%S") if device[6] else None
                })
        
        # 5. 统计信息
        stats = {"total_devices": len(result_devices)}
        
        result = {
            "success": True,
            "data": {
                "devices": result_devices,
                "totalDevices": len(result_devices),
                "statistics": stats,
                "page": page,
                "pageSize": page_size,
                "performance": {
                    "query_time": round(time.time() - start_time, 3),
                    "optimized": True,
                    "cached": False
                }
            }
        }
        
        # 6. 缓存结果(5分钟)
        try:
            redis.setex(cache_key, 300, json.dumps(result, default=str))
        except: pass
        
        return result
        
    except Exception as e:
        print(f"优化查询失败: {e}")
        return {"success": False, "error": str(e)}
'''
    
    print("✅ 优化查询代码已生成")
    return optimized_code

if __name__ == "__main__":
    diagnose_device_query()
    create_optimized_query() 
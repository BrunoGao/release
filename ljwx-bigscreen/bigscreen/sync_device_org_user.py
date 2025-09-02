#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""设备组织用户信息同步脚本"""

import sys,os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def sync_device_org_user():
    """同步设备的org_id和user_id信息"""
    try:
        from bigScreen.bigScreen import app
        with app.app_context():
            from bigScreen.models import db
            from sqlalchemy import text
            
            print("🔄 开始同步设备组织用户信息...")
            
            # 查找需要同步的设备（缺少org_id或user_id的设备）
            devices_need_sync = db.session.execute(text("""
                SELECT CONVERT(d.serial_number USING utf8mb4) as device_sn, du.user_id, du.user_name, o.org_id
                FROM t_device_info d 
                LEFT JOIN t_device_user du ON CONVERT(d.serial_number USING utf8mb4) = CONVERT(du.device_sn USING utf8mb4) 
                    AND du.status = 'BIND' AND du.is_deleted = 0
                LEFT JOIN sys_user_org o ON du.user_id = o.user_id AND o.principal IN ('0','1')
                WHERE (d.org_id IS NULL OR d.user_id IS NULL) AND du.user_id IS NOT NULL
            """)).fetchall()
            
            print(f"📊 找到{len(devices_need_sync)}个需要同步的设备")
            
            sync_count = 0
            for device in devices_need_sync:
                device_sn = device[0]
                user_id = device[1] 
                user_name = device[2]
                org_id = device[3]
                
                print(f"   处理设备: {device_sn}")
                print(f"     用户: {user_name} (ID: {user_id})")
                print(f"     组织: {org_id}")
                
                # 更新设备的org_id和user_id
                if user_id and org_id:
                    update_sql = text("""
                        UPDATE t_device_info 
                        SET org_id = :org_id, user_id = :user_id, update_time = NOW()
                        WHERE CONVERT(serial_number USING utf8mb4) = :device_sn
                    """)
                    result = db.session.execute(update_sql, {
                        'org_id': org_id,
                        'user_id': user_id, 
                        'device_sn': device_sn
                    })
                    
                    if result.rowcount > 0:
                        print(f"     ✅ 同步成功")
                        sync_count += 1
                    else:
                        print(f"     ⚠️ 更新失败")
                elif user_id and not org_id:
                    # 只有用户没有组织，只更新user_id
                    update_sql = text("""
                        UPDATE t_device_info 
                        SET user_id = :user_id, update_time = NOW()
                        WHERE CONVERT(serial_number USING utf8mb4) = :device_sn
                    """)
                    result = db.session.execute(update_sql, {
                        'user_id': user_id,
                        'device_sn': device_sn
                    })
                    
                    if result.rowcount > 0:
                        print(f"     ✅ 同步用户成功（无组织信息）")
                        sync_count += 1
                    else:
                        print(f"     ⚠️ 更新失败")
                else:
                    print(f"     ❌ 缺少必要的关联信息")
            
            # 提交事务
            db.session.commit()
            
            print(f"\n📈 同步统计:")
            print(f"   需要同步: {len(devices_need_sync)} 个设备")
            print(f"   成功同步: {sync_count} 个设备")
            print(f"   失败数量: {len(devices_need_sync) - sync_count} 个设备")
            
            # 验证特定设备
            print(f"\n🔍 验证设备 A5GTQ24A17000135:")
            device_check = db.session.execute(text("""
                SELECT CONVERT(d.serial_number USING utf8mb4), d.org_id, d.user_id, du.user_name
                FROM t_device_info d
                LEFT JOIN t_device_user du ON CONVERT(d.serial_number USING utf8mb4) = CONVERT(du.device_sn USING utf8mb4) 
                    AND du.status = 'BIND'
                WHERE CONVERT(d.serial_number USING utf8mb4) = 'A5GTQ24A17000135'
            """)).fetchone()
            
            if device_check:
                print(f"   设备SN: {device_check[0]}")
                print(f"   组织ID: {device_check[1]}")
                print(f"   用户ID: {device_check[2]}")
                print(f"   用户名: {device_check[3]}")
                
                if device_check[1] and device_check[2]:
                    print(f"   ✅ 设备已正确绑定组织和用户")
                else:
                    print(f"   ⚠️ 设备仍缺少绑定信息")
            else:
                print(f"   ❌ 未找到该设备记录")
                
            print(f"\n✅ 设备组织用户同步完成!")
            
    except Exception as e:
        print(f"❌ 同步失败: {e}")

if __name__ == '__main__':
    sync_device_org_user() 
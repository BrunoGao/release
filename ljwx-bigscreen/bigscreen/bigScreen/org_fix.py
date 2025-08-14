# 用户组织管理模块修复版
from .models import db,UserInfo,OrgUnits
from sqlalchemy import text,func
import json

def fetch_users_by_orgId(orgId):
    """获取组织下的所有用户并生成部门统计"""
    try:
        # 获取用户列表
        sql = text("""
            SELECT DISTINCT
                u.id as user_id,
                u.user_name,u.nick_name as real_name,
                u.phone,u.email,u.avatar,
                u.device_sn,u.status,
                u.user_card_number,u.working_years,
                u.create_time,u.update_time,
                o.id as dept_id,o.name as dept_name,
                p.name as position_name
            FROM sys_user u
            LEFT JOIN sys_user_org uo ON u.id = uo.user_id
            LEFT JOIN sys_org_units o ON uo.org_id = o.id
            LEFT JOIN sys_user_position up ON u.id = up.user_id
            LEFT JOIN sys_position p ON up.position_id = p.id
            WHERE (o.id = :org_id OR o.ancestors LIKE :pattern)
            AND u.is_deleted = 0
            ORDER BY u.id
        """)
        
        results = db.session.execute(sql, {
            'org_id': orgId,
            'pattern': f'%,{orgId},%'
        }).fetchall()
        
        # 构建用户列表和部门统计
        users = []
        dept_count = {}
        device_count = 0
        
        for result in results:
            user = {
                'user_id': str(result.user_id),
                'user_name': result.user_name,
                'real_name': result.real_name or result.user_name,
                'phone_number': result.phone,
                'email': result.email,
                'avatar': result.avatar,
                'device_sn': result.device_sn,
                'status': result.status,
                'dept_id': str(result.dept_id) if result.dept_id else None,
                'dept_name': result.dept_name or '未分配部门',
                'position': result.position_name,
                'user_card_number': result.user_card_number,
                'working_years': result.working_years or 0,
                'create_time': result.create_time.strftime("%Y-%m-%d %H:%M:%S") if result.create_time else None,
                'update_time': result.update_time.strftime("%Y-%m-%d %H:%M:%S") if result.update_time else None
            }
            users.append(user)
            
            # 统计部门人数
            dept_name = user['dept_name']
            dept_count[dept_name] = dept_count.get(dept_name, 0) + 1
            
            # 统计设备数
            if result.device_sn and result.device_sn != '-':
                device_count += 1
        
        return {
            "users": users,
            "totalUsers": len(users),
            "departmentCount": dept_count,  # 添加部门统计
            "totalDevices": device_count
        }
        
    except Exception as e:
        print(f"❌ 用户查询失败: {e}")
        return {
            "users": [],
            "totalUsers": 0,
            "departmentCount": {},
            "totalDevices": 0
        }

from flask import jsonify, render_template, request, Response
from .models import UserInfo, UserOrg, OrgInfo, DeviceInfo, AlertInfo, Position, UserPosition, db
from .redis_helper import RedisHelper
import json  # Import json module

import os
from . import app  # 从 __init__.py 导入 app

redis = RedisHelper()


def get_user_info(deviceSn):
    # 从查询参数获取 deviceSn
    print("get_user_info:deviceSn", deviceSn)
    user = UserInfo.query.filter_by(device_sn=deviceSn).first()
    print("get_user_info:user:", user)
    if user:
        # Convert user object to dictionary with specific fields
        user_dict = {
            "user_name": user.user_name,
            "user_id": user.id,
            "device_sn": user.device_sn,
            "customer_id": user.customer_id,
            "phone": user.phone
        }
        # Convert dictionary to JSON
        user_json = json.dumps(user_dict)
        print("get_user_info:user_json:", user_json)
        # Store dictionary in Redis
        redis.hset(f"user_info:{deviceSn}", mapping=user_dict)
        redis.publish(f"user_info_channel:{deviceSn}", user_json)
        return user_json
    else:
        return "No user found"

def get_all_users():
    # Retrieve all users from the database
    users = UserInfo.query.all()
    if users:
        # Convert each user object to a dictionary
        users_list = [
            user.to_dict()
            for user in users
        ]
        # Convert list of dictionaries to JSON
        users_json = json.dumps(users_list, indent=4)
        print("get_all_users:users_json:", users_json)
        return users_json
    else:
        return "No users found"
    
    
def get_user_name(deviceSn):
    user = UserInfo.query.filter_by(device_sn=deviceSn).first()
    return user.user_name if user else None
    
def get_user_deviceSn(phone):
    user = UserInfo.query.filter_by(
        phone=phone,
        is_deleted=False,
        status='1'
    ).first()
    if user:
        return jsonify({"deviceSn": user.device_sn})
    else:
        return jsonify({"error": "User not found"}), 404
def get_user_info_by_phone(phone):
    """通过手机号获取用户信息"""
    try:
        user = UserInfo.query.filter_by(
            phone=phone,
            is_deleted=False,
            status='1'
        ).first()
        
        print(f"get_user_info_by_phone.phone: {phone}")
        print(f"get_user_info_by_phone.user: {user}")
        
        return user
        
    except Exception as e:
        print(f"Error in get_user_info_by_phone: {e}")
        return None
def get_user_id(phone):
    user = UserInfo.query.filter_by(
        phone=phone,
        is_deleted=False,
        status='1'
    ).first()
    if user:
        return jsonify({"userId": user.id})
    else:
        return jsonify({"error": "User not found"}), 404   
def get_user_id_mobile(phone):
    user = UserInfo.query.filter_by(
        phone=phone,
        is_deleted=False,
        status='1'
    ).first()
    if user:
        return user.id
    else:
        return None   
def get_departments(ids=None):
    # Initialize a list to hold all departments
    departments = []

    if ids is None:
        # If no IDs are provided, fetch all departments
        departments = OrgInfo.query.filter_by(is_deleted=0, status='1').all()
    else:
        # If IDs are provided, iterate over each ID
        for id in ids:
            # Initialize a list to hold all department IDs to be fetched
            department_ids = [id]

            # While there are department IDs to process
            while department_ids:
                # Fetch departments with the current IDs
                current_departments = OrgInfo.query.filter(
                    OrgInfo.id.in_(department_ids),
                    OrgInfo.is_deleted == 0,
                    OrgInfo.status == '1'
                ).all()
                departments.extend(current_departments)

                # Prepare for the next iteration: find sub-departments
                department_ids = [dept.id for dept in current_departments]
                sub_departments = OrgInfo.query.filter(
                    OrgInfo.parent_id.in_(department_ids),
                    OrgInfo.is_deleted == 0,
                    OrgInfo.status == '1'
                ).all()
                department_ids = [dept.id for dept in sub_departments]

    users_dict = {}  # Use a dictionary instead of a list to store unique users

    for department in departments:
        # Query the UserOrg model to get user IDs for the department
        user_orgs = UserOrg.query.filter_by(org_id=department.id).all()
        user_ids = [user_org.user_id for user_org in user_orgs]

        # Fetch user names from UserInfo using user IDs and filter by device_sn in DeviceInfo
        users = UserInfo.query.join(DeviceInfo, UserInfo.device_sn == DeviceInfo.serial_number)\
                              .filter(UserInfo.id.in_(user_ids)).all()
        # Add user_id: user_name pairs to the dictionary
        for user in users:
            users_dict[str(user.id)] = user.user_name

    # Return the dictionary as JSON
    return jsonify(users_dict)


def get_org_info_by_user_id(user_id):
    user_org = UserOrg.query.filter_by(user_id=user_id).first()
    if user_org:
        org_info = OrgInfo.query.filter_by(id=user_org.org_id).first()
        return org_info
    else:
        return None


def get_user_info_by_orgIdAndUserId(orgId=None, userId=None): #极致优化用户查询-解决N+1问题#
    """极致优化的用户查询，专门解决2000用户的性能问题"""
    try:
        from sqlalchemy import text
        from .redis_helper import RedisHelper
        from .models import db  # 在函数开始就导入db，避免局部变量问题
        from .admin_helper import admin_helper  # 导入admin判断工具
        import json
        
        redis = RedisHelper()
        cache_key = f"user_info_ultra_fast:{orgId}:{userId}"
        
        # 缓存检查
        try:
            cached = redis.get_data(cache_key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass  # 缓存失败继续执行
        
        if userId:
            # 单用户查询 - 修复多职位重复问题和软删除
            sql = text("""
                SELECT DISTINCT
                    u.id as user_id,
                    u.user_name,
                    u.phone,
                    u.device_sn,
                    u.status,
                    u.avatar,
                    u.user_card_number,
                    u.working_years,
                    u.create_time,
                    u.update_time,
                    o.id as dept_id,
                    o.name as dept_name,
                    o.ancestors,
                    d.status as device_status,
                    d.charging_status,
                    d.wearable_status,
                    (SELECT p.name FROM sys_user_position up 
                     JOIN sys_position p ON up.position_id = p.id 
                     WHERE up.user_id = u.id AND up.is_deleted = 0 AND p.is_deleted = 0
                     LIMIT 1) as position_name
                FROM sys_user u
                LEFT JOIN sys_user_org uo ON u.id = uo.user_id AND uo.is_deleted = 0
                LEFT JOIN sys_org_units o ON uo.org_id = o.id AND o.is_deleted = 0
                LEFT JOIN t_device_info d ON u.device_sn = d.serial_number
                WHERE u.id = :user_id AND u.is_deleted = 0
                LIMIT 1
            """)
            
            result = db.session.execute(sql, {'user_id': userId}).fetchone()
            
            if not result:
                return {"success": False, "message": "用户不存在", "data": {"users": [], "totalUsers": 0}}
            
            # 构建部门层级
            dept_hierarchy = []
            if result.ancestors:
                ancestor_ids = [int(x.strip()) for x in result.ancestors.split(',') if x.strip()]
                if ancestor_ids:
                    ancestor_sql = text("SELECT name FROM sys_org_units WHERE id IN :ids ORDER BY FIELD(id, :ordered_ids)")
                    ancestors = db.session.execute(ancestor_sql, {'ids': tuple(ancestor_ids), 'ordered_ids': ','.join(map(str, ancestor_ids))}).fetchall()
                    dept_hierarchy = [a.name for a in ancestors]
            if result.dept_name:
                dept_hierarchy.append(result.dept_name)
            
            user_dict = {
                'user_id': str(result.user_id),
                'user_name': result.user_name,
                'phone_number': result.phone,
                'avatar': result.avatar,
                'user_card_number': result.user_card_number,
                'device_sn': result.device_sn,
                'status': result.status,
                'dept_id': str(result.dept_id) if result.dept_id else None,
                'dept_name': result.dept_name,
                'dept_hierarchy': dept_hierarchy,
                'device_status': result.device_status,
                'charging_status': result.charging_status,
                'wearable_status': result.wearable_status,
                'create_time': result.create_time.strftime("%Y-%m-%d %H:%M:%S") if result.create_time else None,
                'update_time': result.update_time.strftime("%Y-%m-%d %H:%M:%S") if result.update_time else None,
                'working_years': result.working_years,
                'position': result.position_name
            }
            
            response_data = {
                'success': True,
                'data': {
                    'users': [user_dict],
                    'totalUsers': 1,
                    'statusCount': {result.status: 1},
                    'deviceCount': {result.device_sn: 1} if result.device_sn and result.device_sn != '-' else {},
                    'departmentCount': {result.dept_name: 1} if result.dept_name else {},
                    'totalDevices': 1 if result.device_sn and result.device_sn != '-' else 0,
                    'orgId': str(orgId) if orgId else None,
                    'departmentStats': {}
                }
            }
        
        elif orgId:
            # 批量用户查询 - 改用与org.py一致的查询逻辑，避免ROW_NUMBER()导致用户遗漏
            # 获取管理员用户ID集合，构建排除条件
            admin_ids = admin_helper.get_admin_user_ids()
            admin_exclude_condition = ""
            if admin_ids:
                admin_ids_str = ",".join(admin_ids)
                admin_exclude_condition = f"AND u.id NOT IN ({admin_ids_str})"
            
            sql = text(f"""
                SELECT DISTINCT
                    u.id as user_id,
                    u.user_name,
                    u.phone,
                    u.device_sn,
                    u.status,
                    u.avatar,
                    u.user_card_number,
                    u.working_years,
                    u.create_time,
                    u.update_time,
                    o.id as dept_id,
                    o.name as dept_name,
                    o.ancestors,
                    d.status as device_status,
                    d.charging_status,
                    d.wearable_status
                FROM sys_user u
                INNER JOIN sys_user_org uo ON u.id = uo.user_id AND uo.is_deleted = 0
                INNER JOIN sys_org_units o ON uo.org_id = o.id AND o.is_deleted = 0
                LEFT JOIN t_device_info d ON u.device_sn = d.serial_number
                WHERE (o.id = :org_id OR o.ancestors LIKE :ancestors_pattern1 OR o.ancestors LIKE :ancestors_pattern2 OR o.ancestors LIKE :ancestors_pattern3 OR o.ancestors = :org_id_str)
                AND u.is_deleted = 0 AND u.status = '1'
                {admin_exclude_condition}
                ORDER BY u.id
                LIMIT 3000
            """)
            
            # 支持多种ancestors格式: %,1,% (中间位置), 1,% (开头位置), %,1 (结尾位置), 1 (单独值)
            ancestors_pattern1 = f"%,{orgId},%"  # 中间位置，如 0,1,7
            ancestors_pattern2 = f"{orgId},%"    # 开头位置，如 1,2
            ancestors_pattern3 = f"%,{orgId}"    # 结尾位置，如 0,1
            org_id_str = str(orgId)               # 单独值，如 1
            results = db.session.execute(sql, {
                'org_id': orgId, 
                'ancestors_pattern1': ancestors_pattern1,
                'ancestors_pattern2': ancestors_pattern2,
                'ancestors_pattern3': ancestors_pattern3,
                'org_id_str': org_id_str
            }).fetchall()
            
            if not results:
                return {"success": True, "data": {"users": [], "totalUsers": 0, "statusCount": {}, "deviceCount": {}, "departmentCount": {}, "totalDevices": 0, "orgId": str(orgId), "departmentStats": {}}}
            
            # 使用字典去重，确保每个用户只出现一次，与org.py逻辑一致
            users_dict = {}
            for result in results:
                user_id = str(result.user_id)
                if user_id not in users_dict:
                    users_dict[user_id] = result
            
            # 批量获取职位信息
            user_ids = list(users_dict.keys())
            position_sql = text("""
                SELECT up.user_id, p.name as position_name
                FROM sys_user_position up
                JOIN sys_position p ON up.position_id = p.id
                WHERE up.user_id IN :user_ids AND up.is_deleted = 0 AND p.is_deleted = 0
                ORDER BY up.user_id, up.id
            """)
            position_results = db.session.execute(position_sql, {'user_ids': tuple(map(int, user_ids))}).fetchall()
            
            # 应用层去重，每用户取第一个职位
            position_dict = {}
            for p in position_results:
                user_id_str = str(p.user_id)
                if user_id_str not in position_dict:
                    position_dict[user_id_str] = p.position_name
            
            # 批量处理部门层级 - 一次性获取所有祖先部门
            all_ancestor_ids = set()
            for result in users_dict.values():
                if result.ancestors:
                    ancestor_ids = [int(x.strip()) for x in result.ancestors.split(',') if x.strip()]
                    all_ancestor_ids.update(ancestor_ids)
            
            ancestor_names = {}
            if all_ancestor_ids:
                ancestor_sql = text("SELECT id, name FROM sys_org_units WHERE id IN :ids")
                ancestor_results = db.session.execute(ancestor_sql, {'ids': tuple(all_ancestor_ids)}).fetchall()
                ancestor_names = {r.id: r.name for r in ancestor_results}
            
            # 构建用户列表和统计
            result_list = []
            status_count = {}
            device_count = {}
            dept_count = {}
            department_stats = {}
            
            for result in users_dict.values():
                # 构建部门层级
                dept_hierarchy = []
                if result.ancestors:
                    ancestor_ids = [int(x.strip()) for x in result.ancestors.split(',') if x.strip()]
                    dept_hierarchy = [ancestor_names.get(aid, f'部门{aid}') for aid in ancestor_ids if aid in ancestor_names]
                if result.dept_name:
                    dept_hierarchy.append(result.dept_name)
                
                user_dict = {
                    'user_id': str(result.user_id),
                    'user_name': result.user_name,
                    'phone_number': result.phone,
                    'avatar': result.avatar,
                    'user_card_number': result.user_card_number,
                    'device_sn': result.device_sn,
                    'status': result.status,
                    'dept_id': str(result.dept_id) if result.dept_id else None,
                    'dept_name': result.dept_name,
                    'dept_hierarchy': dept_hierarchy,
                    'device_status': result.device_status,
                    'charging_status': result.charging_status,
                    'wearable_status': result.wearable_status,
                    'create_time': result.create_time.strftime("%Y-%m-%d %H:%M:%S") if result.create_time else None,
                    'update_time': result.update_time.strftime("%Y-%m-%d %H:%M:%S") if result.update_time else None,
                    'working_years': result.working_years,
                    'position': position_dict.get(str(result.user_id))
                }
                result_list.append(user_dict)
                
                # 统计处理
                status_count[result.status] = status_count.get(result.status, 0) + 1
                if result.device_sn and result.device_sn != '-':
                    device_count[result.device_sn] = 1  # 设备唯一性
                if result.dept_name:
                    dept_count[result.dept_name] = dept_count.get(result.dept_name, 0) + 1
                
                # 部门统计
                dept_key = str(result.dept_id) if result.dept_id else 'unknown'
                if dept_key not in department_stats:
                    department_stats[dept_key] = {
                        'name': result.dept_name or 'Unknown Department',
                        'total_users': 0,
                        'status_stats': {'active': 0, 'inactive': 0},
                        'device_stats': {
                            'total': 0,
                            'status': {'active': 0, 'inactive': 0},
                            'charging': {'charging': 0, 'not_charging': 0},
                            'wearing': {'wearing': 0, 'not_wearing': 0}
                        }
                    }
                
                dept_stat = department_stats[dept_key]
                dept_stat['total_users'] += 1
                dept_stat['status_stats'][result.status] = dept_stat['status_stats'].get(result.status, 0) + 1
                if result.device_sn and result.device_sn != '-':
                    dept_stat['device_stats']['total'] += 1
                    if result.device_status:
                        dept_stat['device_stats']['status'][result.device_status] = dept_stat['device_stats']['status'].get(result.device_status, 0) + 1
                    if result.charging_status:
                        dept_stat['device_stats']['charging'][result.charging_status] = dept_stat['device_stats']['charging'].get(result.charging_status, 0) + 1
                    if result.wearable_status:
                        dept_stat['device_stats']['wearing'][result.wearable_status] = dept_stat['device_stats']['wearing'].get(result.wearable_status, 0) + 1
            
            response_data = {
                'success': True,
                'data': {
                    'users': result_list,
                    'totalUsers': len(result_list),
                    'statusCount': status_count,
                    'deviceCount': device_count,
                    'departmentCount': dept_count,
                    'totalDevices': len(device_count),
                    'orgId': str(orgId),
                    'departmentStats': department_stats
                }
            }
        
        else:
            return {"success": False, "message": "缺少orgId或userId参数", "data": {"users": [], "totalUsers": 0}}
        
        # 缓存结果 - 用户信息变化不频繁，可以缓存较长时间
        try:
            redis.set_data(cache_key, json.dumps(response_data, default=str), 300)  # 5分钟缓存
        except Exception:
            pass  # 缓存失败不影响返回结果
        
        return response_data
        
    except Exception as e:
        print(f"优化用户查询错误: {e}")
        # 避免递归调用，直接返回错误响应
        return {
            "success": False, 
            "message": f"用户查询失败: {str(e)}", 
            "data": {
                "users": [], 
                "totalUsers": 0,
                "statusCount": {},
                "deviceCount": {},
                "departmentCount": {},
                "totalDevices": 0,
                "orgId": str(orgId) if orgId else None,
                "departmentStats": {}
            }
        }

def fetch_device_info_by_phone(phone):
    user = UserInfo.query.filter_by(
        phone=phone,
        is_deleted=False,
        status='1'
    ).first()
    
    if user:
        device_info = DeviceInfo.query.filter_by(serial_number=user.device_sn).first()
        if device_info:
            return device_info.to_dict()
        else:
            return None
    else:
        return None

def login_user(phone, password):
    """用户登录 #密码验证登录"""
    try:
        user = UserInfo.query.filter_by(
            phone=phone,
            is_deleted=False,  # 确保用户未被删除
            status='1'         # 确保用户状态正常
        ).first()
        
        if not user:
            return {
                'success': False,
                'error': '用户不存在或已被禁用'
            }
        
        # 验证密码
        if not user.verify_password(password):
            return {
                'success': False,
                'error': '密码错误'
            }
        
        from .admin_helper import admin_helper
            
        return {
            'success': True,
            'data': {
                'user_id': user.id,
                'user_name': user.user_name,
                'device_sn': user.device_sn,
                'phone': user.phone,
                'is_admin': admin_helper.is_admin_user(user.id),
                'token': user.device_sn  # 使用device_sn作为token
            }
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'登录失败: {str(e)}'
        }

def reset_password(user_id):
    """重置用户密码"""
    try:
        user = UserInfo.query.get(user_id)
        if not user:
            return {
                'success': False,
                'error': '用户不存在'
            }
        
        # 生成新密码
        pwd_info = UserInfo.generate_password()
        
        # 更新用户密码信息
        user.salt = pwd_info['salt']
        user.password = pwd_info['password']
        from datetime import datetime
        user.update_password_time = datetime.now()
        
        db.session.commit()
        
        return {
            'success': True,
            'data': {
                'password': pwd_info['random_pwd']  # 返回新生成的随机密码
            }
        }
        
    except Exception as e:
        db.session.rollback()
        return {
            'success': False,
            'error': f'密码重置失败: {str(e)}'
        }

def reset_password_by_phone(phone):
    """通过手机号重置密码 #手机号重置密码"""
    try:
        user = UserInfo.query.filter_by(
            phone=phone,
            is_deleted=False,
            status='1'
        ).first()
        if not user:
            return {
                'success': False,
                'error': '用户不存在或已被禁用'
            }
        
        # 生成新密码
        pwd_info = UserInfo.generate_password()
        
        # 更新用户密码信息
        user.salt = pwd_info['salt']
        user.password = pwd_info['password']
        from datetime import datetime
        user.update_password_time = datetime.now()
        
        db.session.commit()
        
        return {
            'success': True,
            'data': {
                'password': pwd_info['random_pwd'],  # 返回新生成的随机密码
                'user_id': user.id,
                'user_name': user.user_name,
                'phone': user.phone
            }
        }
        
    except Exception as e:
        db.session.rollback()
        return {
            'success': False,
            'error': f'密码重置失败: {str(e)}'
        }

def get_user_id_by_deviceSn(deviceSn):  #根据设备序列号获取用户ID
    try:
        user = UserInfo.query.filter_by(device_sn=deviceSn, is_deleted=False, status='1').first()
        return user.id if user else None
    except Exception as e:
        print(f"获取用户ID失败 deviceSn={deviceSn}: {e}")
        return None
from flask import jsonify, render_template, request, Response
from .models import UserInfo, UserOrg, OrgInfo, DeviceInfo, AlertInfo, Position, UserPosition, db
from .redis_helper import RedisHelper
# tenant_context removed - customerId now passed as parameter
import json  # Import json module
from typing import List, Dict, Optional, Tuple
import logging

import os
from . import app  # 从 __init__.py 导入 app

logger = logging.getLogger(__name__)

redis = RedisHelper()


def get_user_info(deviceSn):
    # 从查询参数获取 deviceSn
    print("get_user_info:deviceSn", deviceSn)
    user = UserInfo.query.filter_by(device_sn=deviceSn, is_deleted=False).first()
    print("get_user_info:user:", user)
    if user:
        # Convert user object to dictionary with specific fields - 🚀 优化：直接包含组织信息
        user_dict = {
            "user_name": user.user_name,
            "user_id": user.id,
            "device_sn": user.device_sn,
            "customer_id": user.customer_id,
            "phone": user.phone,
            # 🚀 新增：组织信息直接获取，无需JOIN查询
            "org_id": str(user.org_id) if user.org_id else None,
            "org_name": user.org_name or "未分配"
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
    # Retrieve all users from the database with tenant filtering
    customer_id = request.args.get('customerId', 0, type=int)
    
    if customer_id == 0:
        # 超级管理员，查看所有用户
        users = UserInfo.query.all()
    else:
        # 租户用户，只查看本租户的用户
        users = UserInfo.query.filter_by(customer_id=customer_id).all()
    
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


def get_user_info_by_orgIdAndUserId(orgId=None, userId=None, customer_id=None): #极致优化用户查询-解决N+1问题#
    """极致优化的用户查询，专门解决2000用户的性能问题，支持多租户隔离"""
    try:
        from sqlalchemy import text
        from .redis_helper import RedisHelper
        from .models import db  # 在函数开始就导入db，避免局部变量问题
        from .admin_helper import admin_helper  # 导入admin判断工具
        import json
        
        # 确保有customer_id参数
        if customer_id is None:
            customer_id = request.args.get('customerId', 0, type=int)
        
        redis = RedisHelper()
        cache_key = f"user_info_ultra_fast:{orgId}:{userId}:{customer_id}"
        
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
                AND (:customer_id = 0 OR u.customer_id = :customer_id)
                LIMIT 1
            """)
            
            result = db.session.execute(sql, {'user_id': userId, 'customer_id': customer_id}).fetchone()
            
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
                AND (:customer_id = 0 OR u.customer_id = :customer_id)
                AND (:customer_id = 0 OR o.customer_id = :customer_id)
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
                'org_id_str': org_id_str,
                'customer_id': customer_id
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

def get_user_info_by_deviceSn(deviceSn):
    """根据设备序列号获取完整用户信息"""
    try:
        user = UserInfo.query.filter_by(device_sn=deviceSn, is_deleted=False, status='1').first()
        if not user:
            return None
        
        return {
            'id': user.id,
            'user_name': user.user_name,
            'real_name': user.real_name,
            'phone': user.phone,
            'device_sn': user.device_sn,
            'customer_id': user.customer_id,
            'create_time': user.create_time.isoformat() if user.create_time else None,
            'update_time': user.update_time.isoformat() if user.update_time else None
        }
        
    except Exception as e:
        print(f"获取用户信息失败 deviceSn={deviceSn}: {e}")
        return None

def get_all_user_data_optimized(orgId=None, userId=None, startDate=None, endDate=None, latest_only=False, page=1, pageSize=None, status=None, include_details=False):
    """
    统一的用户数据查询接口，支持分页和优化查询
    
    Args:
        orgId: 组织ID
        userId: 用户ID  
        startDate: 开始日期
        endDate: 结束日期
        latest_only: 是否只查询最新记录
        page: 页码
        pageSize: 每页大小
        status: 用户状态
        include_details: 是否包含详细信息
    
    Returns:
        dict: 包含用户数据和分页信息的字典
    """
    try:
        import time
        from datetime import datetime, timedelta
        from typing import List, Dict, Optional, Tuple
        import logging
        
        logger = logging.getLogger(__name__)
        start_time = time.time()
        
        # 参数验证和缓存键构建
        page = max(1, int(page or 1))
        if pageSize is not None:
            pageSize = min(int(pageSize), 1000)
        else:
            pageSize = None
        mode = 'latest' if latest_only else 'range'
        cache_key = f"user_opt_v1:{orgId}:{userId}:{startDate}:{endDate}:{mode}:{page}:{pageSize}:{status}:{include_details}"
        
        # 缓存检查
        cached = redis.get_data(cache_key)
        if cached:
            result = json.loads(cached)
            result['performance'] = {'cached': True, 'response_time': round(time.time() - start_time, 3)}
            return result
        
        # 构建查询条件
        query = db.session.query(
            UserInfo.id,
            UserInfo.user_name,
            UserInfo.real_name,
            UserInfo.phone,
            UserInfo.device_sn,
            UserInfo.status,
            UserInfo.avatar,
            UserInfo.user_card_number,
            UserInfo.working_years,
            UserInfo.create_time,
            UserInfo.update_time,
            UserInfo.customer_id,
            OrgInfo.id.label('org_id'),
            OrgInfo.name.label('org_name')
        ).outerjoin(
            UserOrg, UserInfo.id == UserOrg.user_id
        ).outerjoin(
            OrgInfo, UserOrg.org_id == OrgInfo.id
        ).filter(
            UserInfo.is_deleted == False
        )
        
        if userId:
            # 单用户查询
            from .admin_helper import is_admin_user
            if is_admin_user(userId):
                return {"success": True, "data": {"userData": [], "totalRecords": 0, "pagination": {"currentPage": page, "pageSize": pageSize, "totalCount": 0, "totalPages": 0}}}
            
            query = query.filter(UserInfo.id == userId)
            
        elif orgId:
            # 组织查询 - 获取组织下所有用户
            from .org import fetch_users_by_orgId
            users = fetch_users_by_orgId(orgId)
            if not users:
                return {"success": True, "data": {"userData": [], "totalRecords": 0, "pagination": {"currentPage": page, "pageSize": pageSize, "totalCount": 0, "totalPages": 0}}}
            
            user_ids = [int(user['id']) for user in users]
            query = query.filter(UserInfo.id.in_(user_ids))
            
        else:
            return {"success": False, "message": "缺少orgId或userId参数", "data": {"userData": [], "totalRecords": 0}}
        
        # 时间范围过滤
        if startDate:
            query = query.filter(UserInfo.create_time >= startDate)
        if endDate:
            query = query.filter(UserInfo.create_time <= endDate)
        
        # 状态过滤
        if status:
            query = query.filter(UserInfo.status == status)
        
        # 统计总数
        total_count = query.count()
        
        # 排序
        query = query.order_by(UserInfo.create_time.desc())
        
        # 分页处理
        if pageSize is not None:
            offset = (page - 1) * pageSize
            query = query.offset(offset).limit(pageSize)
        
        if latest_only and not pageSize:
            query = query.limit(1)
        
        # 执行查询
        users = query.all()
        
        # 格式化数据
        user_data_list = []
        for user in users:
            user_dict = {
                'id': user.id,
                'user_name': user.user_name,
                'real_name': user.real_name,
                'phone': user.phone,
                'device_sn': user.device_sn,
                'status': user.status,
                'avatar': user.avatar,
                'user_card_number': user.user_card_number,
                'working_years': user.working_years,
                'create_time': user.create_time.strftime('%Y-%m-%d %H:%M:%S') if user.create_time else None,
                'update_time': user.update_time.strftime('%Y-%m-%d %H:%M:%S') if user.update_time else None,
                'customer_id': user.customer_id,
                'org_id': user.org_id,
                'org_name': user.org_name,
                'dept_name': user.org_name,  # 兼容字段
                'dept_id': user.org_id
            }
            
            # 如果需要包含详细信息
            if include_details:
                # 获取设备信息
                device_info = DeviceInfo.query.filter_by(serial_number=user.device_sn).first()
                if device_info:
                    user_dict['device_info'] = {
                        'status': device_info.status,
                        'charging_status': device_info.charging_status,
                        'wearable_status': device_info.wearable_status
                    }
            
            user_data_list.append(user_dict)
        
        # 构建分页信息
        pagination = {
            'currentPage': page,
            'pageSize': pageSize,
            'totalCount': total_count,
            'totalPages': (total_count + pageSize - 1) // pageSize if pageSize else 1
        }
        
        # 构建结果
        result = {
            'success': True,
            'data': {
                'userData': user_data_list,
                'totalRecords': len(user_data_list),
                'pagination': pagination
            },
            'performance': {
                'cached': False,
                'response_time': round(time.time() - start_time, 3),
                'query_time': round(time.time() - start_time, 3)
            }
        }
        
        # 缓存结果
        redis.set_data(cache_key, json.dumps(result, default=str), 300)
        
        return result
        
    except Exception as e:
        logger.error(f"用户查询失败: {e}")
        return {
            'success': False,
            'error': str(e),
            'data': {'userData': [], 'totalRecords': 0}
        }

class UserService:
    """用户管理统一服务封装类 - 基于userId的查询和汇总"""
    
    def __init__(self):
        self.redis = redis
    
    def get_users_by_common_params(self, customer_id: int = None, org_id: int = None,
                                  user_id: int = None, start_date: str = None, 
                                  end_date: str = None, status: str = None,
                                  page: int = 1, page_size: int = None,
                                  latest_only: bool = False, include_details: bool = False) -> Dict:
        """
        基于统一参数获取用户信息 - 整合现有get_all_user_data_optimized接口
        
        Args:
            customer_id: 客户ID (映射到orgId)
            org_id: 组织ID
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期
            status: 用户状态
            page: 页码
            page_size: 每页大小
            latest_only: 是否只查询最新记录
            include_details: 是否包含详细信息
            
        Returns:
            用户信息字典
        """
        try:
            # 参数映射和优先级处理
            if user_id:
                result = get_all_user_data_optimized(
                    orgId=None,
                    userId=user_id, 
                    startDate=start_date,
                    endDate=end_date,
                    latest_only=latest_only,
                    page=page,
                    pageSize=page_size,
                    status=status,
                    include_details=include_details
                )
                logger.info(f"基于userId查询用户数据: user_id={user_id}")
                
            elif org_id:
                # 组织查询 - 获取组织下所有用户
                result = get_all_user_data_optimized(
                    orgId=org_id,
                    userId=None,
                    startDate=start_date,
                    endDate=end_date,
                    latest_only=latest_only,
                    page=page,
                    pageSize=page_size,
                    status=status,
                    include_details=include_details
                )
                logger.info(f"基于orgId查询用户数据: org_id={org_id}")
                
            elif customer_id:
                # 客户查询 - 将customer_id作为orgId处理
                result = get_all_user_data_optimized(
                    orgId=customer_id,
                    userId=None,
                    startDate=start_date,
                    endDate=end_date,
                    latest_only=latest_only,
                    page=page,
                    pageSize=page_size,
                    status=status,
                    include_details=include_details
                )
                logger.info(f"基于customerId查询用户数据: customer_id={customer_id}")
                
            else:
                return {
                    'success': False,
                    'error': 'Missing required parameters: customer_id, org_id, or user_id',
                    'data': {'users': [], 'total_count': 0}
                }
            
            # 统一返回格式，兼容新的服务接口
            if result.get('success', True):
                user_data = result.get('data', {}).get('userData', [])
                
                unified_result = {
                    'success': True,
                    'data': {
                        'users': user_data,
                        'total_count': result.get('data', {}).get('totalRecords', len(user_data)),
                        'pagination': result.get('data', {}).get('pagination', {}),
                        'query_params': {
                            'customer_id': customer_id,
                            'org_id': org_id,
                            'user_id': user_id,
                            'start_date': start_date,
                            'end_date': end_date,
                            'status': status,
                            'page': page,
                            'page_size': page_size,
                            'latest_only': latest_only,
                            'include_details': include_details
                        }
                    },
                    'performance': result.get('performance', {}),
                    'from_cache': result.get('performance', {}).get('cached', False)
                }
                
                return unified_result
            else:
                return result
                
        except Exception as e:
            logger.error(f"用户查询失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': {'users': [], 'total_count': 0}
            }
    
    def get_user_statistics_by_common_params(self, customer_id: int = None,
                                           org_id: int = None, user_id: int = None,
                                           start_date: str = None, end_date: str = None) -> Dict:
        """基于统一参数获取用户统计"""
        try:
            cache_key = f"user_stats_v2:{customer_id}:{org_id}:{user_id}:{start_date}:{end_date}"
            
            # 缓存检查
            cached = self.redis.get_data(cache_key)
            if cached:
                return json.loads(cached)
            
            # 获取用户数据
            users_result = self.get_users_by_common_params(
                customer_id, org_id, user_id, start_date, end_date
            )
            
            if not users_result.get('success'):
                return users_result
            
            users = users_result['data']['users']
            
            # 计算统计数据
            total_users = len(users)
            status_stats = {'active': 0, 'inactive': 0, 'suspended': 0}
            device_stats = {'bound': 0, 'unbound': 0}
            org_stats = {}
            
            for user in users:
                # 状态统计
                user_status = user.get('status', 'inactive')
                if user_status == '1':
                    status_stats['active'] += 1
                elif user_status == '0':
                    status_stats['inactive'] += 1
                else:
                    status_stats['suspended'] += 1
                
                # 设备绑定统计
                if user.get('device_sn') and user.get('device_sn') != '-':
                    device_stats['bound'] += 1
                else:
                    device_stats['unbound'] += 1
                
                # 按组织统计
                org_name = user.get('org_name', '未知组织')
                if org_name not in org_stats:
                    org_stats[org_name] = {
                        'total': 0,
                        'active': 0,
                        'device_bound': 0
                    }
                
                org_stats[org_name]['total'] += 1
                if user_status == '1':
                    org_stats[org_name]['active'] += 1
                if user.get('device_sn') and user.get('device_sn') != '-':
                    org_stats[org_name]['device_bound'] += 1
            
            result = {
                'success': True,
                'data': {
                    'overview': {
                        'total_users': total_users,
                        'status_stats': status_stats,
                        'device_stats': device_stats,
                        'active_rate': round(status_stats['active'] / total_users * 100, 2) if total_users > 0 else 0,
                        'device_bound_rate': round(device_stats['bound'] / total_users * 100, 2) if total_users > 0 else 0
                    },
                    'org_statistics': org_stats,
                    'query_params': {
                        'customer_id': customer_id,
                        'org_id': org_id,
                        'user_id': user_id,
                        'start_date': start_date,
                        'end_date': end_date
                    }
                }
            }
            
            # 缓存结果
            self.redis.set_data(cache_key, json.dumps(result, default=str), 180)
            
            return result
            
        except Exception as e:
            logger.error(f"用户统计计算失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': {'overview': {}, 'org_statistics': {}}
            }

# 全局实例
_user_service_instance = None

def get_unified_user_service() -> UserService:
    """获取统一用户服务实例"""
    global _user_service_instance
    if _user_service_instance is None:
        _user_service_instance = UserService()
    return _user_service_instance

# 向后兼容的函数，供现有代码使用
def get_users_unified(customer_id: int = None, org_id: int = None,
                     user_id: int = None, start_date: str = None,
                     end_date: str = None, status: str = None,
                     page: int = 1, page_size: int = None,
                     latest_only: bool = False, include_details: bool = False) -> Dict:
    """统一的用户查询接口 - 整合现有get_all_user_data_optimized接口"""
    service = get_unified_user_service()
    return service.get_users_by_common_params(
        customer_id, org_id, user_id, start_date, end_date, status,
        page, page_size, latest_only, include_details
    )

def get_user_statistics_unified(customer_id: int = None, org_id: int = None,
                               user_id: int = None, start_date: str = None,
                               end_date: str = None) -> Dict:
    """统一的用户统计接口"""
    service = get_unified_user_service()
    return service.get_user_statistics_by_common_params(customer_id, org_id, user_id, start_date, end_date)

# ===============================================================================
# 🚀 sys_user表增加org_id和org_name字段后的优化函数
# ===============================================================================

def get_user_with_org_info_optimized(user_id):
    """获取用户及组织信息 - 优化后的单表查询"""
    try:
        user = UserInfo.query.filter_by(
            id=user_id,
            is_deleted=False
        ).first()
        
        if user:
            return {
                'success': True,
                'data': {
                    'id': user.id,
                    'user_name': user.user_name,
                    'device_sn': user.device_sn,
                    'org_id': user.org_id,
                    'org_name': user.org_name,
                    'customer_id': user.customer_id,
                    'phone': user.phone,
                    'status': user.status
                }
            }
        return {'success': False, 'error': 'User not found'}
    except Exception as e:
        logger.error(f"获取用户组织信息失败: {e}")
        return {'success': False, 'error': str(e)}

def get_users_by_org_optimized(org_id, customer_id=None):
    """通过组织ID获取用户列表 - 优化后的单表查询"""
    try:
        query = UserInfo.query.filter(
            UserInfo.org_id == org_id,
            UserInfo.is_deleted.is_(False),
            UserInfo.status == '1'
        )
        
        if customer_id:
            query = query.filter(UserInfo.customer_id == customer_id)
        
        users = query.all()
        return {
            'success': True,
            'data': {
                'users': [user.to_dict() for user in users],
                'total': len(users)
            }
        }
    except Exception as e:
        logger.error(f"按组织查询用户失败: {e}")
        return {'success': False, 'error': str(e)}

def sync_user_org_info(org_id):
    """组织信息变更时同步用户表中的org_name字段"""
    try:
        from .models import OrgInfo  # 避免循环导入
        org = OrgInfo.query.get(org_id)
        if org:
            updated_count = UserInfo.query.filter_by(org_id=org_id).update({
                'org_name': org.name
            })
            db.session.commit()
            logger.info(f"同步组织信息成功: org_id={org_id}, 更新用户数={updated_count}")
            return {'success': True, 'updated_count': updated_count}
        else:
            return {'success': False, 'error': 'Organization not found'}
    except Exception as e:
        db.session.rollback()
        logger.error(f"同步组织信息失败: {e}")
        return {'success': False, 'error': str(e)}
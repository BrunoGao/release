import logging
from flask import jsonify, session, request, abort, json
from werkzeug.exceptions import NotFound
from .models import db, OrgInfo, UserOrg, UserInfo, Position, UserPosition, DeviceInfo
from collections import defaultdict
from sqlalchemy import text

# Configure logging
logging.basicConfig(filename='org.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s: %(message)s')

logger = logging.getLogger(__name__)

def fetch_departments_by_orgId(org_id):
    """递归获取组织下的所有部门信息，包括当前组织"""
    try:
        def get_child_departments(parent_id):
            departments = db.session.query(OrgInfo)\
                .filter(OrgInfo.parent_id == parent_id)\
                .all()
            
            departments_data = []
            for dept in departments:
                dept_data = {
                    'id': str(dept.id),
                    'name': dept.name,
                    'parent_id': str(dept.parent_id),
                    'create_time': dept.create_time.strftime('%Y-%m-%d %H:%M:%S') if dept.create_time else None
                }
                
                # 递归获取子部门
                child_departments = get_child_departments(dept.id)
                if child_departments:
                    dept_data['children'] = child_departments
                
                departments_data.append(dept_data)
            
            return departments_data

        # 先获取当前组织的信息
        current_org = db.session.query(OrgInfo)\
            .filter(OrgInfo.id == org_id)\
            .first()

        if not current_org:
            return {
                'success': False,
                'error': f'Organization not found: {org_id}'
            }

        # 构建包含当前组织的树结构
        root_data = {
            'id': str(current_org.id),
            'name': current_org.name,
            'parent_id': str(current_org.parent_id) if current_org.parent_id else None,
            'create_time': current_org.create_time.strftime('%Y-%m-%d %H:%M:%S') if current_org.create_time else None,
            'children': get_child_departments(org_id)
        }

        return {
            'success': True,
            'data': [root_data]  # 返回包含根节点的数组
        }
            
    except Exception as e:
        logger.error(f"Error in fetch_departments_by_orgId: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def fetch_users_by_orgId(org_id):
    """获取组织及其所有子部门下的用户信息"""
    try:
        from .admin_helper import admin_helper  # 导入admin判断工具
        
        # 获取组织及其所有子部门
        org_response = fetch_departments_by_orgId(org_id)
        #logger.info(f"fetch_users_by_orgId:org_response: {org_response}")
        #print("fetch_users_by_orgId:org_response:", org_response)
        if not org_response.get('success'):
            logger.error(f"Failed to fetch departments for org {org_id}")
            return []

        # 收集所有部门ID（包括子部门）
        department_ids = set()
        def collect_dept_ids(dept_data):
            department_ids.add(dept_data['id'])
            for child in dept_data.get('children', []):
                collect_dept_ids(child)

        # 处理根组织
        department_ids.add(org_id)
        # 处理所有子部门
        for dept in org_response.get('data', []):
            collect_dept_ids(dept)

        #print(f"Found departments: {department_ids}")

        # 查询所有部门下的用户
        users = db.session.query(
            UserInfo, UserOrg, OrgInfo
        ).join(
            UserOrg, UserInfo.id == UserOrg.user_id
        ).join(
            OrgInfo, UserOrg.org_id == OrgInfo.id
        ).filter(
            UserOrg.org_id.in_(department_ids),
            UserInfo.is_deleted.is_(False),
            UserInfo.status == '1'
        ).all()

        # 使用字典来存储唯一的用户信息，以用户ID为键
        user_dict = {}
        for user_info, user_org, org_info in users:
            user_id = str(user_info.id)
            if user_id not in user_dict:
                # 获取职位信息
                position_info = db.session.query(Position.name).join(
                    UserPosition, Position.id == UserPosition.position_id
                ).filter(UserPosition.user_id == user_info.id).first()
                
                position_name = position_info.name if position_info else None
                
                user_dict[user_id] = {
                    'id': user_id,
                    'user_name': user_info.user_name,
                    'nick_name': user_info.nick_name,
                    'real_name': user_info.real_name,
                    'email': user_info.email,
                    'phone': user_info.phone,
                    'avatar': user_info.avatar,
                    'user_card_number': user_info.user_card_number,
                    'device_sn': user_info.device_sn,
                    'customer_id': user_info.customer_id,
                    'status': user_info.status,
                    'department_id': org_info.id,
                    'department_name': org_info.name,
                    'create_time': user_info.create_time.strftime('%Y-%m-%d %H:%M:%S') if user_info.create_time else None,
                    'update_time': user_info.update_time.strftime('%Y-%m-%d %H:%M:%S') if user_info.update_time else None,
                    'working_years': user_info.working_years,
                    'position': position_name
                }

        # 将字典转换为列表
        user_list = list(user_dict.values())
        print(f"Found {len(user_list)} unique users in total for org {org_id} and its subdepartments")
        
        # 过滤掉管理员用户，只返回员工
        filtered_user_list = admin_helper.filter_non_admin_users(user_list, 'id')
        print(f"After filtering admin users: {len(filtered_user_list)} employee users remaining")
        
        return filtered_user_list

    except Exception as e:
        print(f"Error in fetch_users_by_orgId: {str(e)}")
        return []

def getCustomers():
    """获取所有顶级组织（客户）"""
    try:
        customers = db.session.query(OrgInfo)\
            .filter(OrgInfo.parent_id == 0)\
            .all()

        customer_list = []
        for customer in customers:
            customer_list.append({
                'id': customer.id,
                'name': customer.name,
                'code': customer.code,
                'status': customer.status,
                'create_time': customer.create_time.strftime('%Y-%m-%d %H:%M:%S') if customer.create_time else None,
                'update_time': customer.update_time.strftime('%Y-%m-%d %H:%M:%S') if customer.update_time else None
            })

        logger.info(f"Found {len(customer_list)} customers")
        return customer_list

    except Exception as e:
        logger.error(f"Error in getCustomers: {str(e)}")
        return []

def fetch_departments(orgId):
    try:
        # 直接使用递归获取的部门数据
        response = fetch_departments_by_orgId(orgId)
        if not response['success']:
            return response

        return {
            'success': True,
            'data': response['data']
        }

    except Exception as e:
        print(f"Error in fetch_departments: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def fetch_users_stats_by_orgId(org_id):
    """获取用户统计信息"""
    try:
        users = fetch_users_by_orgId(org_id)
        if not users:
            return {
                'success': False,
                'error': 'No users found'
            }

        # 部门统计
        department_stats = {}
        for user in users:
            dept_id = user['department_id']
            dept_name = user['department_name']
            if dept_id not in department_stats:
                department_stats[dept_id] = {
                    'name': dept_name,
                    'total': 0,
                    'with_device': 0,
                    'without_device': 0
                }
            
            stats = department_stats[dept_id]
            stats['total'] += 1
            if user['device_sn'] and user['device_sn'].strip() not in ['', '-']:
                stats['with_device'] += 1
            else:
                stats['without_device'] += 1

        # 用户增长趋势（按月统计）
        monthly_stats = defaultdict(lambda: {'total': 0, 'with_device': 0})
        
        for user in users:
            if user['create_time']:
                month = user['create_time'][:7]  # 获取年月 (YYYY-MM)
                monthly_stats[month]['total'] += 1
                if user['device_sn'] and user['device_sn'].strip() not in ['', '-']:
                    monthly_stats[month]['with_device'] += 1

        # 整体设备佩戴统计
        total_users = len(users)
        users_with_device = sum(1 for user in users 
                              if user['device_sn'] and user['device_sn'].strip() not in ['', '-'])

        return {
            'success': True,
            'data': {
                'department_stats': [
                    {
                        'name': stats['name'],
                        'total': stats['total'],
                        'with_device': stats['with_device'],
                        'without_device': stats['without_device']
                    }
                    for stats in department_stats.values()
                ],
                'monthly_stats': [
                    {
                        'month': month,
                        'total': stats['total'],
                        'with_device': stats['with_device']
                    }
                    for month, stats in sorted(monthly_stats.items())
                ],
                'overall_stats': {
                    'total_users': total_users,
                    'users_with_device': users_with_device,
                    'users_without_device': total_users - users_with_device
                }
            }
        }

    except Exception as e:
        logger.error(f"Error in fetch_users_stats_by_orgId: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def fetch_root_departments():
    """获取根部门"""
    departments = OrgInfo.query.filter_by(parent_id=0, is_deleted=False).order_by(OrgInfo.sort).all()
    
    formatted_departments = []
    for dept in departments:
        formatted_departments.append({
            'id': dept.id,
            'name': dept.name,
            'code': dept.code,
            'parentId': dept.parent_id,
            'ancestors': dept.ancestors,
            'sort': dept.sort
        })
    
    return jsonify({
        'success': True,
        'data': formatted_departments
    })

def get_org_descendants(org_id):
    """获取组织及其所有子组织的ID列表"""
    try:
        org_ids = [int(org_id)]  # 包含当前组织ID#
        
        def collect_child_org_ids(parent_id):
            """递归收集子组织ID"""
            children = db.session.query(OrgInfo.id).filter(
                OrgInfo.parent_id == parent_id,
                OrgInfo.is_deleted.is_(False)
            ).all()
            
            for child in children:
                child_id = child[0]
                org_ids.append(child_id)
                collect_child_org_ids(child_id)  # 递归获取子组织的子组织#
        
        collect_child_org_ids(int(org_id))
        return org_ids
        
    except Exception as e:
        print(f"Error in get_org_descendants: {e}")
        return [int(org_id)]  # 发生错误时至少返回当前组织ID#

def get_top_level_org_id(org_id):
    """根据org_id获取顶级组织(租户)ID - 通过ancestors字段解析"""
    # 不需要获取租户ID，直接返回org_id
    return org_id







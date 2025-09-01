import logging
from flask import jsonify, session, request, abort, json
from werkzeug.exceptions import NotFound
from .models import db, OrgInfo, UserOrg, UserInfo, Position, UserPosition, DeviceInfo
# tenant_context removed - customerId now passed as parameter
from collections import defaultdict
from sqlalchemy import text

# 导入组织架构优化查询服务
from .org_optimized import get_org_service
from .org_service import get_unified_org_service

# Configure logging
logging.basicConfig(filename='org.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s: %(message)s')

logger = logging.getLogger(__name__)

def fetch_departments_by_orgId(org_id, customer_id=None):
    """递归获取组织下的所有部门信息，包括当前组织，支持多租户隔离 - 统一优化版本"""
    try:
        # 如果没有提供customer_id，尝试从请求获取
        if customer_id is None:
            try:
                customer_id = request.args.get('customerId', 0, type=int)
            except RuntimeError:
                # 在没有Flask上下文时，使用默认值0
                customer_id = 0
                logger.warning("无Flask上下文，使用默认customer_id=0")
        
        # 🔧 修复：增加统一服务可用性检查
        org_service = get_unified_org_service()
        if org_service is None:
            logger.warning(f"统一组织服务不可用，回退到legacy方法")
            return fetch_departments_by_orgId_legacy(org_id, customer_id)
        
        try:
            result = org_service.get_org_tree(org_id, customer_id)
            
            # 🔧 修复：验证结果有效性
            if not result or not result.get('success'):
                logger.warning(f"统一服务返回无效结果，回退到legacy方法")
                return fetch_departments_by_orgId_legacy(org_id, customer_id)
                
            logger.info(f"使用统一服务成功获取组织{org_id}的部门树")
            return result
            
        except Exception as service_error:
            logger.error(f"统一服务调用失败: {service_error}，回退到legacy方法")
            return fetch_departments_by_orgId_legacy(org_id, customer_id)
            
    except Exception as e:
        logger.error(f"Error in fetch_departments_by_orgId: {str(e)}")
        # 🔧 修复：最终回退到legacy方法
        return fetch_departments_by_orgId_legacy(org_id, customer_id)

def fetch_departments_by_orgId_legacy(org_id, customer_id=None):
    """原始递归查询方式 - 作为回退方案"""
    try:
        if customer_id is None:
            try:
                customer_id = request.args.get('customerId', 0, type=int)
            except RuntimeError:
                # 在没有Flask上下文时，使用默认值0
                customer_id = 0
                logger.warning("无Flask上下文，使用默认customer_id=0")
            
        def get_child_departments(parent_id, customer_id=None):
            query = db.session.query(OrgInfo)\
                .filter(OrgInfo.parent_id == parent_id)\
                .filter(OrgInfo.is_deleted == 0)
            
            # 添加租户隔离
            if customer_id is not None:
                query = query.filter(OrgInfo.customer_id == customer_id)
                
            departments = query.all()
            
            departments_data = []
            for dept in departments:
                dept_data = {
                    'id': str(dept.id),
                    'name': dept.name,
                    'parent_id': str(dept.parent_id),
                    'create_time': dept.create_time.strftime('%Y-%m-%d %H:%M:%S') if dept.create_time else None
                }
                
                # 递归获取子部门
                child_departments = get_child_departments(dept.id, customer_id)
                if child_departments:
                    dept_data['children'] = child_departments
                
                departments_data.append(dept_data)
            
            return departments_data

        # 先获取当前组织的信息，支持租户隔离
        query = db.session.query(OrgInfo)\
            .filter(OrgInfo.id == org_id)\
            .filter(OrgInfo.is_deleted == 0)
        
        if customer_id is not None:
            query = query.filter(OrgInfo.customer_id == customer_id)
            
        current_org = query.first()

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
            'children': get_child_departments(org_id, customer_id)
        }

        return {
            'success': True,
            'data': [root_data]  # 返回包含根节点的数组
        }
            
    except Exception as e:
        logger.error(f"Error in fetch_departments_by_orgId_legacy: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def fetch_users_by_orgId(org_id, customer_id=None):
    """获取组织及其所有子部门下的用户信息，支持多租户隔离 - 增强回退版本"""
    try:
        from .admin_helper import admin_helper  # 导入admin判断工具
        
        # 🔧 修复：增加多重查询策略
        # 方法1：使用统一服务查询部门
        org_response = fetch_departments_by_orgId(org_id, customer_id)
        if not org_response.get('success'):
            logger.warning(f"统一服务查询部门失败，尝试直接数据库查询用户")
            return fetch_users_by_orgId_direct(org_id, customer_id)
        
        # 方法2：基于部门结果查询用户
        users = _fetch_users_from_departments(org_response, org_id, customer_id)
        if users and len(users) > 0:
            logger.info(f"基于部门树查询成功: 组织{org_id}找到{len(users)}个用户")
            return users
            
        # 方法3：直接数据库查询（绕过统一服务）
        logger.warning(f"部门树查询无用户结果，尝试直接数据库查询")
        users_direct = fetch_users_by_orgId_direct(org_id, customer_id)
        if users_direct and len(users_direct) > 0:
            logger.info(f"直接数据库查询成功: 组织{org_id}找到{len(users_direct)}个用户")
            return users_direct
            
        # 方法4：扩大查询范围（包含子组织）
        logger.warning(f"直接查询也无结果，尝试查询子组织")
        users_expanded = fetch_users_with_descendants(org_id, customer_id)
        logger.info(f"扩展查询结果: 组织{org_id}及子组织找到{len(users_expanded)}个用户")
        return users_expanded
        
    except Exception as e:
        logger.error(f"所有用户查询方法均失败: {str(e)}")
        return []

def _fetch_users_from_departments(org_response, org_id, customer_id):
    """基于部门树结果查询用户"""
    try:
        from .admin_helper import admin_helper
        
        # 获取组织及其所有子部门
        #logger.info(f"fetch_users_by_orgId:org_response: {org_response}")
        #print("fetch_users_by_orgId:org_response:", org_response)

        # 收集所有部门ID（包括子部门）
        department_ids = set()
        def collect_dept_ids(dept_data):
            department_ids.add(dept_data['id'])
            for child in dept_data.get('children', []):
                collect_dept_ids(child)

        # 处理根组织
        department_ids.add(str(org_id))
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
        logger.error(f"Error in _fetch_users_from_departments: {str(e)}")
        return []

def fetch_users_by_orgId_direct(org_id, customer_id=None):
    """直接数据库查询用户（绕过服务层）"""
    try:
        from .admin_helper import admin_helper
        
        # 直接查询，不依赖组织服务
        users = db.session.query(
            UserInfo, UserOrg, OrgInfo
        ).join(
            UserOrg, UserInfo.id == UserOrg.user_id
        ).join(
            OrgInfo, UserOrg.org_id == OrgInfo.id
        ).filter(
            UserOrg.org_id == org_id,
            UserInfo.is_deleted.is_(False),
            UserInfo.status == '1'
        )
        
        if customer_id is not None:
            users = users.filter(UserInfo.customer_id == customer_id)
        
        users_result = users.all()
        
        # 格式化返回结果
        user_list = []
        for user_info, user_org, org_info in users_result:
            # 获取职位信息
            position_info = db.session.query(Position.name).join(
                UserPosition, Position.id == UserPosition.position_id
            ).filter(UserPosition.user_id == user_info.id).first()
            
            position_name = position_info.name if position_info else None
            
            user_list.append({
                'id': str(user_info.id),
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
            })
        
        # 过滤掉管理员用户，只返回员工
        filtered_user_list = admin_helper.filter_non_admin_users(user_list, 'id')
        logger.info(f"直接数据库查询: 组织{org_id}找到{len(filtered_user_list)}个员工用户")
        
        return filtered_user_list
        
    except Exception as e:
        logger.error(f"直接数据库查询用户失败: {str(e)}")
        return []

def fetch_users_with_descendants(org_id, customer_id=None):
    """查询组织及其所有子组织的用户（扩展查询）"""
    try:
        from .admin_helper import admin_helper
        
        # 查询所有可能的子组织
        descendant_orgs = db.session.query(OrgInfo.id).filter(
            OrgInfo.is_deleted == 0,
            db.or_(
                OrgInfo.id == org_id,
                OrgInfo.parent_id == org_id,
                OrgInfo.ancestors.like(f'%,{org_id},%') if hasattr(OrgInfo, 'ancestors') else True
            )
        ).all()
        
        org_ids = [org.id for org in descendant_orgs]
        
        if not org_ids:
            # 如果没有找到子组织，至少查询当前组织
            org_ids = [org_id]
        
        # 查询这些组织下的所有用户
        users = db.session.query(
            UserInfo, UserOrg, OrgInfo
        ).join(
            UserOrg, UserInfo.id == UserOrg.user_id
        ).join(
            OrgInfo, UserOrg.org_id == OrgInfo.id
        ).filter(
            UserOrg.org_id.in_(org_ids),
            UserInfo.is_deleted.is_(False),
            UserInfo.status == '1'
        )
        
        if customer_id is not None:
            users = users.filter(UserInfo.customer_id == customer_id)
        
        users_result = users.all()
        
        # 使用字典来存储唯一的用户信息
        user_dict = {}
        for user_info, user_org, org_info in users_result:
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
        
        # 过滤掉管理员用户，只返回员工
        filtered_user_list = admin_helper.filter_non_admin_users(user_list, 'id')
        logger.info(f"扩展查询: 组织{org_id}及子组织找到{len(filtered_user_list)}个员工用户")
        
        return filtered_user_list
        
    except Exception as e:
        logger.error(f"扩展查询用户失败: {str(e)}")
        return []

def getCustomers():
    """获取所有顶级组织（客户）"""
    try:
        customers = db.session.query(OrgInfo)\
            .filter(OrgInfo.parent_id == 0)\
            .filter(OrgInfo.is_deleted == 0)\
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
    """获取根部门 - 移除ancestors字段依赖"""
    try:
        org_service = get_unified_org_service()
        departments = org_service.get_root_departments()
        
        return jsonify({
            'success': True,
            'data': departments
        })
        
    except Exception as e:
        logger.error(f"Error in fetch_root_departments: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

def get_org_descendants(org_id, customer_id=None):
    """获取组织及其所有子组织的ID列表 - 使用统一服务"""
    try:
        org_service = get_unified_org_service()
        return org_service.get_org_descendants_ids(int(org_id), customer_id)
        
    except Exception as e:
        logger.error(f"Error in get_org_descendants: {e}")
        return [int(org_id)]  # 发生错误时至少返回当前组织ID

def get_top_level_org_id(org_id):
    """根据org_id获取顶级组织(租户)ID - 通过ancestors字段解析"""
    # 不需要获取租户ID，直接返回org_id
    return org_id







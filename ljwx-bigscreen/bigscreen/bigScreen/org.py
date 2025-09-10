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
    """递归获取组织下的所有部门信息，包括当前组织，支持多租户隔离"""
    try:
        # 如果没有提供customer_id，尝试从请求获取
        if customer_id is None:
            try:
                customer_id = request.args.get('customerId', None, type=int)
            except RuntimeError:
                # 在没有Flask上下文时，不设置默认customer_id，让查询逻辑根据org_id自动处理
                customer_id = None
                logger.info("无Flask上下文，不设置默认customer_id，将根据org_id查询")
        
        logger.info(f"查询组织部门: org_id={org_id}, customer_id={customer_id}")
        
        def get_child_departments(parent_id, customer_id=None):
            query = db.session.query(OrgInfo)\
                .filter(OrgInfo.parent_id == parent_id)\
                .filter(OrgInfo.is_deleted.is_(False))
            
            # 🔧 修复：简化子部门查询逻辑
            if customer_id is not None:
                # 如果提供了customer_id，先尝试严格匹配
                strict_departments = query.filter(OrgInfo.customer_id == customer_id).all()
                if strict_departments:
                    departments = strict_departments
                else:
                    # 如果严格匹配没有结果，可能是组织结构层次问题，获取所有子部门但验证有效性
                    all_departments = query.all()
                    departments = []
                    for dept in all_departments:
                        # 检查该部门是否属于指定客户（通过ID或customer_id字段）
                        if (str(dept.id) == str(customer_id) or 
                            (dept.customer_id and str(dept.customer_id) == str(customer_id)) or
                            str(parent_id) == str(customer_id)):
                            departments.append(dept)
                    
                    # 如果仍然没有结果，为了兼容性，返回所有子部门
                    if not departments:
                        departments = all_departments
            else:
                # customer_id为None时，直接查询所有子部门，不做customer_id过滤
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
            .filter(OrgInfo.is_deleted.is_(False))
        
        logger.info(f"🔍 查询组织: org_id={org_id}, customer_id={customer_id}")
        
        # 🔧 修复：简化查询逻辑，优先根据org_id查询
        if customer_id is not None:
            # 尝试多种查询策略
            # 策略1：直接customer_id匹配
            current_org = query.filter(OrgInfo.customer_id == customer_id).first()
            
            # 策略2：如果没找到，可能该组织本身就是客户根组织
            if not current_org:
                current_org = query.first()
                # 验证是否为该客户的根组织或子组织
                if current_org and str(current_org.id) == str(customer_id):
                    # 该组织ID就是客户ID，这是有效的
                    pass
                elif current_org:
                    # 检查是否为该客户下的子组织（通过parent_id链条）
                    temp_org = current_org
                    is_valid_org = False
                    depth = 0
                    while temp_org and depth < 10:  # 防止死循环
                        if str(temp_org.id) == str(customer_id) or (temp_org.customer_id and str(temp_org.customer_id) == str(customer_id)):
                            is_valid_org = True
                            break
                        if temp_org.parent_id:
                            temp_org = db.session.query(OrgInfo).filter(OrgInfo.id == temp_org.parent_id, OrgInfo.is_deleted.is_(False)).first()
                        else:
                            break
                        depth += 1
                    
                    if not is_valid_org:
                        current_org = None
        else:
            # customer_id为None时，直接根据org_id查询，不做customer_id过滤
            current_org = query.first()
            logger.info(f"🔍 customer_id为None，直接根据org_id查询: org_id={org_id}, found_org={current_org.name if current_org else 'None'}")
            
        if not current_org:
            logger.warning(f"❌ Organization not found: {org_id}, customer_id: {customer_id}")
            # 添加更详细的调试信息
            all_orgs = db.session.query(OrgInfo).filter(OrgInfo.id == org_id).all()
            logger.info(f"🔍 所有匹配ID的组织（包括已删除）: {len(all_orgs)}")
            for org in all_orgs:
                logger.info(f"  - ID: {org.id}, Name: {org.name}, is_deleted: {org.is_deleted}, customer_id: {getattr(org, 'customer_id', 'N/A')}")
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
        logger.error(f"Error in fetch_departments_by_orgId: {str(e)}")
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
            OrgInfo.is_deleted.is_(False),
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
            .filter(OrgInfo.is_deleted.is_(False))\
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

def fetch_departments(orgId, customerId=None):
    try:
        logger.info(f"🔍 fetch_departments调用: orgId={orgId}, customerId={customerId}")
        
        # 🔧 修复：处理多种情况
        # 情况1: orgId为None但有customerId，查找该客户的根组织
        if orgId is None and customerId:
            root_orgs = db.session.query(OrgInfo)\
                .filter(OrgInfo.customer_id == customerId)\
                .filter(OrgInfo.is_deleted.is_(False))\
                .filter(db.or_(OrgInfo.parent_id.is_(None), OrgInfo.parent_id == 0))\
                .all()
            
            if root_orgs:
                orgId = root_orgs[0].id  # 使用第一个根组织
                logger.info(f"自动找到customerId {customerId} 的根组织ID: {orgId}")
            else:
                return {
                    'success': False,
                    'error': f'No root organization found for customer: {customerId}'
                }
        
        # 情况2: 有orgId但没有customerId，需要检查orgId的真实含义
        elif orgId and not customerId:
            # 先尝试作为orgId直接查询
            org_exists = db.session.query(OrgInfo).filter(
                OrgInfo.id == orgId, 
                OrgInfo.is_deleted.is_(False)
            ).first()
            
            if org_exists:
                # 找到了组织，但需要设置正确的customerId
                customerId = org_exists.customer_id
                logger.info(f"✅ 直接找到组织: {orgId}, 设置customerId={customerId}")
            else:
                logger.info(f"🔍 orgId {orgId} 不存在，尝试多种映射策略")
                
                # 策略1: 尝试将orgId作为customerId查找根组织
                root_orgs = db.session.query(OrgInfo)\
                    .filter(OrgInfo.customer_id == orgId)\
                    .filter(OrgInfo.is_deleted.is_(False))\
                    .filter(db.or_(OrgInfo.parent_id.is_(None), OrgInfo.parent_id == 0))\
                    .all()
                
                if root_orgs:
                    customerId = orgId  # 原来的orgId实际上是customerId
                    orgId = root_orgs[0].id  # 使用根组织的ID
                    logger.info(f"✅ 策略1成功: 将 {customerId} 作为customerId，找到根组织ID: {orgId}")
                else:
                    # 策略2: 检查是否存在某个租户组织，其ID本身就是租户ID（可能是租户顶级组织）
                    tenant_org = db.session.query(OrgInfo).filter(
                        OrgInfo.id == orgId
                    ).first()  # 不加is_deleted过滤，因为可能状态字段不同
                    
                    if tenant_org:
                        logger.info(f"✅ 策略2成功: {orgId} 是有效的组织ID，name={tenant_org.name}, is_deleted={tenant_org.is_deleted}")
                        customerId = tenant_org.customer_id if hasattr(tenant_org, 'customer_id') else orgId
                        # 如果找到的是租户本身，直接使用它
                        if tenant_org.is_deleted is False or tenant_org.is_deleted == 0:
                            # 组织可用，直接使用
                            pass
                        else:
                            logger.info(f"⚠️ 组织{orgId}已被删除，但仍然尝试使用")
                    else:
                        # 策略3: 查找是否有组织的customer_id字段等于这个ID（反向查找）
                        orgs_with_customer = db.session.query(OrgInfo)\
                            .filter(OrgInfo.customer_id == orgId)\
                            .filter(OrgInfo.is_deleted.is_(False))\
                            .all()
                        
                        if orgs_with_customer:
                            # 找到第一个根组织（parent_id为0或None）
                            root_org = None
                            for org in orgs_with_customer:
                                if not org.parent_id or org.parent_id == 0:
                                    root_org = org
                                    break
                            
                            if not root_org:
                                root_org = orgs_with_customer[0]  # 如果没有根组织，使用第一个
                            
                            customerId = orgId
                            orgId = root_org.id
                            logger.info(f"✅ 策略3成功: 找到customer_id={customerId}的组织，使用orgId={orgId}")
                        else:
                            logger.warning(f"❌ 所有策略都失败: {orgId} 既不是有效的orgId也不是有效的customerId")
                            return {
                                'success': False,
                                'error': f'Organization not found for ID: {orgId}. Please check if this ID exists in sys_org_units table.'
                            }
        
        # 直接使用递归获取的部门数据
        response = fetch_departments_by_orgId(orgId, customerId)
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







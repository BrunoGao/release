"""
组织架构统一服务封装 - ljwx-bigscreen专用
整合闭包表查询和传统查询，提供统一的API接口
"""

import logging
from flask import request
from typing import List, Dict, Optional, Tuple
from .models import db, OrgInfo, UserOrg, UserInfo
# tenant_context removed - customerId now passed as parameter
from .org_optimized import get_org_service
from collections import defaultdict
from sqlalchemy import text

logger = logging.getLogger(__name__)

class OrgService:
    """统一组织服务封装类"""
    
    def __init__(self):
        self.org_optimized = get_org_service()
    
    def get_org_tree(self, org_id: int, customer_id: int = None) -> Dict:
        """
        获取组织树结构 - 统一接口
        优先使用闭包表查询，失败时回退到传统查询
        
        Args:
            org_id: 组织ID
            customer_id: 租户ID (必需，避免Flask上下文依赖)
            
        Returns:
            组织树结构
        """
        if customer_id is None:
            try:
                customer_id = request.args.get('customerId', None, type=int)
            except RuntimeError:
                # 在没有Flask上下文时，不设置默认customer_id，让查询逻辑根据org_id自动处理
                customer_id = None
                logger.info("无Flask上下文，不设置默认customer_id，将根据org_id查询")
        
        try:
            # 优先使用闭包表查询
            query = db.session.query(OrgInfo)\
                .filter(OrgInfo.id == org_id)\
                .filter(OrgInfo.is_deleted == 0)
            
            # 仅在customer_id不为None时添加customer_id过滤
            if customer_id is not None:
                current_org = query.filter(OrgInfo.customer_id == customer_id).first()
            else:
                current_org = query.first()
            
            if not current_org:
                return {
                    'success': False,
                    'error': f'Organization not found: {org_id}'
                }
            
            # 使用闭包表查询所有子部门
            child_orgs = self.org_optimized.find_all_descendants(org_id, customer_id)
            
            # 构建树形结构
            org_dict = {str(current_org.id): {
                'id': str(current_org.id),
                'name': current_org.name,
                'code': current_org.code,
                'parent_id': str(current_org.parent_id) if current_org.parent_id else None,
                'level': current_org.level,
                'create_time': current_org.create_time.strftime('%Y-%m-%d %H:%M:%S') if current_org.create_time else None,
                'children': []
            }}
            
            # 添加所有子部门到字典
            for child in child_orgs:
                org_dict[str(child['id'])] = {
                    'id': str(child['id']),
                    'name': child['name'],
                    'code': child.get('code', ''),
                    'parent_id': str(child['parent_id']),
                    'level': child.get('level', 0),
                    'create_time': child.get('create_time', ''),
                    'children': []
                }
            
            # 构建父子关系
            for child in child_orgs:
                parent_id = str(child['parent_id'])
                if parent_id in org_dict:
                    org_dict[parent_id]['children'].append(org_dict[str(child['id'])])
            
            logger.info(f"使用闭包表成功获取组织{org_id}的部门树，子部门数量: {len(child_orgs)}")
            return {
                'success': True,
                'data': [org_dict[str(org_id)]]
            }
            
        except Exception as e:
            logger.warning(f"闭包表查询失败，回退到传统查询: {str(e)}")
            return self._get_org_tree_legacy(org_id, customer_id)
    
    def _get_org_tree_legacy(self, org_id: int, customer_id: int) -> Dict:
        """传统递归查询 - 作为回退方案"""
        try:
            def get_child_departments(parent_id, customer_id):
                query = db.session.query(OrgInfo)\
                    .filter(OrgInfo.parent_id == parent_id)\
                    .filter(OrgInfo.is_deleted == 0)
                
                if customer_id is not None:
                    query = query.filter(OrgInfo.customer_id == customer_id)
                    
                departments = query.all()
                
                departments_data = []
                for dept in departments:
                    dept_data = {
                        'id': str(dept.id),
                        'name': dept.name,
                        'code': dept.code,
                        'parent_id': str(dept.parent_id),
                        'level': dept.level,
                        'create_time': dept.create_time.strftime('%Y-%m-%d %H:%M:%S') if dept.create_time else None
                    }
                    
                    # 递归获取子部门
                    child_departments = get_child_departments(dept.id, customer_id)
                    if child_departments:
                        dept_data['children'] = child_departments
                    
                    departments_data.append(dept_data)
                
                return departments_data

            # 获取当前组织
            query = db.session.query(OrgInfo)\
                .filter(OrgInfo.id == org_id)\
                .filter(OrgInfo.is_deleted == 0)
            
            # 仅在customer_id不为None时添加customer_id过滤
            if customer_id is not None:
                current_org = query.filter(OrgInfo.customer_id == customer_id).first()
            else:
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
                'code': current_org.code,
                'parent_id': str(current_org.parent_id) if current_org.parent_id else None,
                'level': current_org.level,
                'create_time': current_org.create_time.strftime('%Y-%m-%d %H:%M:%S') if current_org.create_time else None,
                'children': get_child_departments(org_id, customer_id)
            }

            return {
                'success': True,
                'data': [root_data]
            }
                
        except Exception as e:
            logger.error(f"传统查询也失败了: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_org_descendants_ids(self, org_id: int, customer_id: int = None) -> List[int]:
        """
        获取组织及其所有子组织的ID列表 - 统一接口
        
        Args:
            org_id: 组织ID  
            customer_id: 租户ID
            
        Returns:
            组织ID列表
        """
        if customer_id is None:
            try:
                customer_id = request.args.get('customerId', None, type=int)
            except RuntimeError:
                # 在没有Flask上下文时，不设置默认customer_id，让查询逻辑根据org_id自动处理
                customer_id = None
                logger.info("无Flask上下文，不设置默认customer_id，将根据org_id查询")
        
        try:
            # 优先使用闭包表查询
            child_orgs = self.org_optimized.find_all_descendants(org_id, customer_id)
            org_ids = [int(org_id)]  # 包含当前组织
            org_ids.extend([child['id'] for child in child_orgs])
            return org_ids
            
        except Exception as e:
            logger.warning(f"闭包表查询失败，使用传统递归查询: {str(e)}")
            return self._get_org_descendants_ids_legacy(org_id)
    
    def _get_org_descendants_ids_legacy(self, org_id: int) -> List[int]:
        """传统递归查询子组织ID"""
        try:
            org_ids = [int(org_id)]
            
            def collect_child_org_ids(parent_id):
                children = db.session.query(OrgInfo.id).filter(
                    OrgInfo.parent_id == parent_id,
                    OrgInfo.is_deleted.is_(False)
                ).all()
                
                for child in children:
                    child_id = child[0]
                    org_ids.append(child_id)
                    collect_child_org_ids(child_id)
            
            collect_child_org_ids(int(org_id))
            return org_ids
            
        except Exception as e:
            logger.error(f"传统递归查询失败: {e}")
            return [int(org_id)]
    
    def get_org_managers(self, org_id: int, customer_id: int = None, 
                        role_type: str = None) -> List[Dict]:
        """
        获取组织管理员 - 统一接口
        
        Args:
            org_id: 组织ID
            customer_id: 租户ID
            role_type: 角色类型 ('manager', 'supervisor')
            
        Returns:
            管理员列表
        """
        if customer_id is None:
            try:
                customer_id = request.args.get('customerId', None, type=int)
            except RuntimeError:
                # 在没有Flask上下文时，不设置默认customer_id，让查询逻辑根据org_id自动处理
                customer_id = None
                logger.info("无Flask上下文，不设置默认customer_id，将根据org_id查询")
        
        try:
            # 优先使用闭包表查询
            managers = self.org_optimized.find_org_managers(org_id, customer_id, role_type)
            return managers
            
        except Exception as e:
            logger.warning(f"闭包表查询管理员失败，使用传统查询: {str(e)}")
            return self._get_org_managers_legacy(org_id, customer_id, role_type)
    
    def _get_org_managers_legacy(self, org_id: int, customer_id: int, 
                                role_type: str = None) -> List[Dict]:
        """传统查询管理员"""
        try:
            query = db.session.query(UserInfo, UserOrg)\
                .join(UserOrg, UserInfo.id == UserOrg.user_id)\
                .filter(UserOrg.org_id == org_id)\
                .filter(UserOrg.principal == '1')\
                .filter(UserInfo.is_deleted.is_(False))\
                .filter(UserInfo.status == '1')
            
            if customer_id is not None:
                query = query.filter(UserOrg.customer_id == customer_id)
            
            results = query.all()
            
            managers = []
            for user_info, user_org in results:
                managers.append({
                    'user_id': user_info.id,
                    'user_name': user_info.user_name,
                    'org_id': user_org.org_id,
                    'role_type': 'manager',  # 从principal字段推断
                    'org_level': 0  # 传统查询无法确定层级
                })
            
            return managers
            
        except Exception as e:
            logger.error(f"传统查询管理员失败: {str(e)}")
            return []
    
    def get_escalation_chain(self, org_id: int, customer_id: int = None) -> List[Dict]:
        """
        获取告警升级链 - 统一接口
        
        Args:
            org_id: 组织ID
            customer_id: 租户ID
            
        Returns:
            按层级排序的管理员列表
        """
        if customer_id is None:
            try:
                customer_id = request.args.get('customerId', None, type=int)
            except RuntimeError:
                # 在没有Flask上下文时，不设置默认customer_id，让查询逻辑根据org_id自动处理
                customer_id = None
                logger.info("无Flask上下文，不设置默认customer_id，将根据org_id查询")
        
        try:
            # 优先使用闭包表查询
            escalation_managers = self.org_optimized.find_escalation_managers(
                org_id, customer_id, "manager"
            )
            return escalation_managers
            
        except Exception as e:
            logger.warning(f"闭包表查询升级链失败，使用传统查询: {str(e)}")
            return self._get_escalation_chain_legacy(org_id, customer_id)
    
    def _get_escalation_chain_legacy(self, org_id: int, customer_id: int) -> List[Dict]:
        """传统递归查询升级链"""
        try:
            escalation_chain = []
            current_org_id = org_id
            
            while current_org_id:
                # 查找当前组织的管理员
                managers = self._get_org_managers_legacy(current_org_id, customer_id)
                escalation_chain.extend(managers)
                
                # 查找父组织
                parent_org = db.session.query(OrgInfo)\
                    .filter(OrgInfo.id == current_org_id)\
                    .filter(OrgInfo.is_deleted == 0)\
                    .first()
                
                current_org_id = parent_org.parent_id if parent_org and parent_org.parent_id != 0 else None
            
            return escalation_chain
            
        except Exception as e:
            logger.error(f"传统查询升级链失败: {str(e)}")
            return []
    
    def get_root_departments(self, customer_id: int = None) -> List[Dict]:
        """
        获取根部门列表 - 移除ancestors字段依赖
        
        Args:
            customer_id: 租户ID
            
        Returns:
            根部门列表（不再包含ancestors字段）
        """
        try:
            query = db.session.query(OrgInfo)\
                .filter(OrgInfo.parent_id == 0)\
                .filter(OrgInfo.is_deleted == 0)\
                .order_by(OrgInfo.sort)
            
            if customer_id is not None:
                query = query.filter(OrgInfo.customer_id == customer_id)
            
            departments = query.all()
            
            formatted_departments = []
            for dept in departments:
                formatted_departments.append({
                    'id': dept.id,
                    'name': dept.name,
                    'code': dept.code,
                    'parent_id': dept.parent_id,
                    'level': dept.level,
                    'sort': dept.sort,
                    'status': dept.status
                })
            
            return formatted_departments
            
        except Exception as e:
            logger.error(f"获取根部门失败: {str(e)}")
            return []
    
    def batch_get_org_managers(self, org_ids: List[int], customer_id: int = None,
                              role_type: str = None) -> Dict[int, List[Dict]]:
        """
        批量获取多个组织的管理员
        
        Args:
            org_ids: 组织ID列表
            customer_id: 租户ID
            role_type: 角色类型
            
        Returns:
            以组织ID为键的管理员字典
        """
        if customer_id is None:
            try:
                customer_id = request.args.get('customerId', None, type=int)
            except RuntimeError:
                # 在没有Flask上下文时，不设置默认customer_id，让查询逻辑根据org_id自动处理
                customer_id = None
                logger.info("无Flask上下文，不设置默认customer_id，将根据org_id查询")
        
        try:
            # 优先使用闭包表批量查询
            return self.org_optimized.batch_find_org_managers(
                org_ids, customer_id, role_type
            )
            
        except Exception as e:
            logger.warning(f"批量查询失败，逐个查询: {str(e)}")
            result_dict = {}
            for org_id in org_ids:
                result_dict[org_id] = self.get_org_managers(org_id, customer_id, role_type)
            return result_dict

# 全局实例
_org_service_instance = None

def get_unified_org_service() -> OrgService:
    """获取统一组织服务实例"""
    global _org_service_instance
    if _org_service_instance is None:
        _org_service_instance = OrgService()
    return _org_service_instance

# 向后兼容的函数，供现有代码使用
def get_org_tree_unified(org_id: int, customer_id: int = None) -> Dict:
    """统一的组织树查询接口"""
    service = get_unified_org_service()
    return service.get_org_tree(org_id, customer_id)

def get_org_descendants_unified(org_id: int, customer_id: int = None) -> List[int]:
    """统一的子组织ID查询接口"""
    service = get_unified_org_service()
    return service.get_org_descendants_ids(org_id, customer_id)

def get_escalation_chain_unified(org_id: int, customer_id: int = None) -> List[Dict]:
    """统一的告警升级链查询接口"""
    service = get_unified_org_service()
    return service.get_escalation_chain(org_id, customer_id)
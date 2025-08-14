# -*- coding: utf-8 -*-
"""管理员用户判断工具类 - 实时查询管理员权限，无缓存延迟"""

from sqlalchemy import text
from .models import db
import logging

logger = logging.getLogger(__name__)

class AdminHelper:
    """管理员用户判断工具类 - 实时权限查询"""
    
    def __init__(self):
        pass  # 移除Redis缓存相关初始化
    
    def get_admin_user_ids(self):
        """获取所有管理员用户ID列表 - 实时查询数据库"""
        try:
            # 直接从数据库查询，移除缓存机制确保实时性
            admin_ids = self._query_admin_users_from_db()
            logger.debug(f"实时查询到{len(admin_ids)}个管理员用户")
            return admin_ids
            
        except Exception as e:
            logger.error(f"获取admin用户ID失败: {e}")
            # 出错时返回空集合，避免影响业务
            return set()
    
    def _query_admin_users_from_db(self):
        """从数据库查询管理员用户 - 增强查询条件，确保用户状态有效"""
        try:
            # 查询isAdmin=1的用户，增加用户状态检查
            query = text("""
                SELECT DISTINCT u.id 
                FROM sys_user u
                JOIN sys_user_role ur ON u.id = ur.user_id
                JOIN sys_role r ON ur.role_id = r.id
                WHERE r.is_admin = 1 
                AND u.is_deleted = 0 
                AND u.status = '1'
                AND ur.is_deleted = 0
                AND r.is_deleted = 0
                AND r.status = '1'
            """)
            
            result = db.session.execute(query)
            admin_ids = {str(row[0]) for row in result}  # 转换为字符串集合
            
            logger.debug(f"从数据库查询到{len(admin_ids)}个有效管理员用户")
            return admin_ids
            
        except Exception as e:
            logger.error(f"数据库查询admin用户失败: {e}")
            return set()
    
    def is_admin_user(self, user_id):
        """判断用户是否为管理员 - 实时查询版本"""
        if not user_id:
            return False
        
        try:
            admin_ids = self.get_admin_user_ids()
            result = str(user_id) in admin_ids
            logger.debug(f"用户{user_id}管理员权限检查结果: {result}")
            return result
        except Exception as e:
            logger.error(f"判断admin用户失败: {e}")
            return False
    
    def filter_non_admin_users(self, user_list, user_id_field='id'):
        """过滤掉管理员用户，只返回普通员工 - 实时查询版本"""
        try:
            admin_ids = self.get_admin_user_ids()
            filtered_users = []
            
            for user in user_list:
                # 支持字典和对象两种格式
                if isinstance(user, dict):
                    user_id = str(user.get(user_id_field, ''))
                else:
                    user_id = str(getattr(user, user_id_field, ''))
                
                if user_id and user_id not in admin_ids:
                    filtered_users.append(user)
            
            logger.debug(f"过滤前: {len(user_list)}个用户，过滤后: {len(filtered_users)}个员工用户")
            return filtered_users
            
        except Exception as e:
            logger.error(f"过滤admin用户失败: {e}")
            # 出错时返回原列表，避免影响业务
            return user_list
    
    def get_admin_statistics(self):
        """获取管理员用户统计信息 - 实时查询版本"""
        try:
            admin_ids = self.get_admin_user_ids()
            
            return {
                'total_admin_users': len(admin_ids),
                'admin_user_ids': list(admin_ids),
                'cache_status': 'disabled',  # 缓存已禁用
                'query_mode': 'realtime'     # 实时查询模式
            }
            
        except Exception as e:
            logger.error(f"获取admin统计信息失败: {e}")
            return {
                'total_admin_users': 0,
                'admin_user_ids': [],
                'cache_status': 'error',
                'error': str(e)
            }

# 创建全局实例
admin_helper = AdminHelper()

# 提供全局辅助函数 - 实时查询版本
def is_admin_user(user_id):
    """全局函数：判断用户是否为管理员 - 实时查询"""
    return admin_helper.is_admin_user(user_id)

def filter_non_admin_users(user_list, user_id_field='id'):
    """全局函数：过滤掉管理员用户 - 实时查询"""
    return admin_helper.filter_non_admin_users(user_list, user_id_field)

def get_admin_user_ids():
    """全局函数：获取所有管理员用户ID - 实时查询"""
    return admin_helper.get_admin_user_ids()

def get_admin_statistics():
    """全局函数：获取管理员统计信息 - 实时查询"""
    return admin_helper.get_admin_statistics() 
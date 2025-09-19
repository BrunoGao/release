"""
用户服务
提供用户管理的业务逻辑
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

from app.base.mysql import MySQLClient
from app.base.redis import RedisClient
from .auth import PasswordManager

logger = logging.getLogger(__name__)


class UserService:
    """用户服务"""
    
    def __init__(self, mysql_client: MySQLClient, redis_client: RedisClient):
        self.mysql = mysql_client
        self.redis = redis_client
        self.password_manager = PasswordManager()
        self.cache_prefix = "user:"
        self.cache_ttl = 1800  # 30分钟
    
    # 用户基础操作
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取用户信息"""
        cache_key = f"{self.cache_prefix}profile:{user_id}"
        
        # 尝试从缓存获取
        cached_user = await self.redis.get_json(cache_key)
        if cached_user:
            return cached_user
        
        try:
            query = """
                SELECT 
                    u.id, u.username, u.realname, u.email, u.phone,
                    u.avatar, u.status, u.user_type, u.gender,
                    u.birthday, u.work_no, u.telephone, u.customer_id,
                    u.created_time, u.updated_time,
                    -- 主组织信息
                    o.id as org_id, o.org_name, o.org_code,
                    -- 角色信息
                    GROUP_CONCAT(r.role_name) as roles
                FROM sys_user u
                LEFT JOIN sys_user_org uo ON u.id = uo.user_id AND uo.is_main = 1 AND uo.del_flag = 0
                LEFT JOIN sys_org o ON uo.org_id = o.id AND o.del_flag = 0
                LEFT JOIN sys_user_role ur ON u.id = ur.user_id AND ur.del_flag = 0
                LEFT JOIN sys_role r ON ur.role_id = r.id AND r.del_flag = 0
                WHERE u.id = :user_id AND u.del_flag = 0
                GROUP BY u.id
            """
            
            user = await self.mysql.execute_first(query, {'user_id': user_id})
            
            if user:
                # 处理角色列表
                if user['roles']:
                    user['roles'] = user['roles'].split(',')
                else:
                    user['roles'] = []
                
                # 缓存结果
                await self.redis.set_json(cache_key, user, self.cache_ttl)
            
            return user
            
        except Exception as e:
            logger.error(f"获取用户信息失败 {user_id}: {e}")
            raise
    
    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名获取用户信息"""
        try:
            query = """
                SELECT 
                    id, username, realname, email, phone, password,
                    salt, status, user_type, customer_id, created_time
                FROM sys_user
                WHERE username = :username AND del_flag = 0
            """
            
            return await self.mysql.execute_first(query, {'username': username})
            
        except Exception as e:
            logger.error(f"根据用户名获取用户失败 {username}: {e}")
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """根据邮箱获取用户信息"""
        try:
            query = """
                SELECT 
                    id, username, realname, email, phone,
                    status, user_type, customer_id, created_time
                FROM sys_user
                WHERE email = :email AND del_flag = 0
            """
            
            return await self.mysql.execute_first(query, {'email': email})
            
        except Exception as e:
            logger.error(f"根据邮箱获取用户失败 {email}: {e}")
            raise
    
    async def create_user(self, user_data: Dict[str, Any]) -> str:
        """创建用户"""
        try:
            # 检查用户名是否存在
            existing_user = await self.get_user_by_username(user_data['username'])
            if existing_user:
                raise ValueError(f"用户名 {user_data['username']} 已存在")
            
            # 检查邮箱是否存在
            if user_data.get('email'):
                existing_email = await self.get_user_by_email(user_data['email'])
                if existing_email:
                    raise ValueError(f"邮箱 {user_data['email']} 已存在")
            
            # 加密密码
            if 'password' in user_data:
                salt = self.password_manager.generate_salt()
                hashed_password = self.password_manager.hash_password(
                    user_data['password'], salt
                )
                user_data['password'] = hashed_password
                user_data['salt'] = salt
            
            # 设置默认值
            user_data.setdefault('status', 1)
            user_data.setdefault('user_type', 'user')
            user_data['created_time'] = datetime.now()
            user_data['updated_time'] = datetime.now()
            
            # 插入用户
            query = """
                INSERT INTO sys_user (
                    username, password, salt, realname, email, phone,
                    avatar, status, user_type, gender, birthday, work_no,
                    telephone, customer_id, created_time, updated_time
                ) VALUES (
                    :username, :password, :salt, :realname, :email, :phone,
                    :avatar, :status, :user_type, :gender, :birthday, :work_no,
                    :telephone, :customer_id, :created_time, :updated_time
                )
            """
            
            user_id = await self.mysql.execute_insert(query, user_data)
            
            logger.info(f"用户创建成功: {user_data['username']} (ID: {user_id})")
            return str(user_id)
            
        except Exception as e:
            logger.error(f"创建用户失败: {e}")
            raise
    
    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        """更新用户信息"""
        try:
            # 移除不允许更新的字段
            forbidden_fields = ['id', 'username', 'password', 'salt', 'created_time']
            for field in forbidden_fields:
                update_data.pop(field, None)
            
            if not update_data:
                return True
            
            update_data['updated_time'] = datetime.now()
            
            # 构建更新语句
            set_clause = ', '.join([f"{key} = :{key}" for key in update_data.keys()])
            query = f"""
                UPDATE sys_user 
                SET {set_clause}
                WHERE id = :user_id AND del_flag = 0
            """
            
            update_data['user_id'] = user_id
            affected_rows = await self.mysql.execute_update(query, update_data)
            
            if affected_rows > 0:
                # 清除缓存
                await self.clear_user_cache(user_id)
                logger.info(f"用户更新成功: {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"更新用户失败 {user_id}: {e}")
            raise
    
    async def change_password(
        self, 
        user_id: str, 
        old_password: str, 
        new_password: str
    ) -> bool:
        """修改密码"""
        try:
            # 获取用户当前密码信息
            query = """
                SELECT password, salt 
                FROM sys_user 
                WHERE id = :user_id AND del_flag = 0
            """
            
            user = await self.mysql.execute_first(query, {'user_id': user_id})
            if not user:
                raise ValueError("用户不存在")
            
            # 验证旧密码
            if not self.password_manager.verify_password(
                old_password, user['password'], user['salt']
            ):
                raise ValueError("原密码错误")
            
            # 生成新密码哈希
            new_salt = self.password_manager.generate_salt()
            new_hashed = self.password_manager.hash_password(new_password, new_salt)
            
            # 更新密码
            update_query = """
                UPDATE sys_user 
                SET password = :password, salt = :salt, updated_time = :updated_time
                WHERE id = :user_id
            """
            
            affected_rows = await self.mysql.execute_update(update_query, {
                'password': new_hashed,
                'salt': new_salt,
                'updated_time': datetime.now(),
                'user_id': user_id
            })
            
            if affected_rows > 0:
                logger.info(f"密码修改成功: {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"修改密码失败 {user_id}: {e}")
            raise
    
    async def reset_password(self, user_id: str, new_password: str) -> bool:
        """重置密码（管理员操作）"""
        try:
            # 生成新密码哈希
            new_salt = self.password_manager.generate_salt()
            new_hashed = self.password_manager.hash_password(new_password, new_salt)
            
            # 更新密码
            query = """
                UPDATE sys_user 
                SET password = :password, salt = :salt, updated_time = :updated_time
                WHERE id = :user_id AND del_flag = 0
            """
            
            affected_rows = await self.mysql.execute_update(query, {
                'password': new_hashed,
                'salt': new_salt,
                'updated_time': datetime.now(),
                'user_id': user_id
            })
            
            if affected_rows > 0:
                logger.info(f"密码重置成功: {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"重置密码失败 {user_id}: {e}")
            raise
    
    # 用户状态管理
    async def activate_user(self, user_id: str) -> bool:
        """激活用户"""
        return await self.update_user_status(user_id, 1)
    
    async def deactivate_user(self, user_id: str) -> bool:
        """停用用户"""
        return await self.update_user_status(user_id, 0)
    
    async def update_user_status(self, user_id: str, status: int) -> bool:
        """更新用户状态"""
        try:
            query = """
                UPDATE sys_user 
                SET status = :status, updated_time = :updated_time
                WHERE id = :user_id AND del_flag = 0
            """
            
            affected_rows = await self.mysql.execute_update(query, {
                'status': status,
                'updated_time': datetime.now(),
                'user_id': user_id
            })
            
            if affected_rows > 0:
                # 清除缓存
                await self.clear_user_cache(user_id)
                logger.info(f"用户状态更新成功: {user_id} -> {status}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"更新用户状态失败 {user_id}: {e}")
            raise
    
    # 用户查询
    async def search_users(
        self,
        keyword: Optional[str] = None,
        org_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        status: Optional[int] = None,
        user_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """搜索用户"""
        try:
            conditions = ["u.del_flag = 0"]
            params = {}
            
            if keyword:
                conditions.append("""
                    (u.username LIKE :keyword 
                     OR u.realname LIKE :keyword 
                     OR u.email LIKE :keyword 
                     OR u.phone LIKE :keyword)
                """)
                params['keyword'] = f"%{keyword}%"
            
            if org_id:
                conditions.append("""
                    u.id IN (
                        SELECT user_id FROM sys_user_org 
                        WHERE org_id = :org_id AND del_flag = 0
                    )
                """)
                params['org_id'] = org_id
            
            if customer_id:
                conditions.append("u.customer_id = :customer_id")
                params['customer_id'] = customer_id
            
            if status is not None:
                conditions.append("u.status = :status")
                params['status'] = status
            
            if user_type:
                conditions.append("u.user_type = :user_type")
                params['user_type'] = user_type
            
            where_clause = " AND ".join(conditions)
            
            # 统计总数
            count_query = f"""
                SELECT COUNT(*) as total
                FROM sys_user u
                WHERE {where_clause}
            """
            
            total_result = await self.mysql.execute_first(count_query, params)
            total = total_result['total'] if total_result else 0
            
            # 查询数据
            offset = (page - 1) * page_size
            params.update({
                'limit': page_size,
                'offset': offset
            })
            
            query = f"""
                SELECT 
                    u.id, u.username, u.realname, u.email, u.phone,
                    u.avatar, u.status, u.user_type, u.gender,
                    u.work_no, u.customer_id, u.created_time,
                    -- 主组织
                    o.org_name as main_org_name
                FROM sys_user u
                LEFT JOIN sys_user_org uo ON u.id = uo.user_id AND uo.is_main = 1 AND uo.del_flag = 0
                LEFT JOIN sys_org o ON uo.org_id = o.id AND o.del_flag = 0
                WHERE {where_clause}
                ORDER BY u.created_time DESC
                LIMIT :limit OFFSET :offset
            """
            
            users = await self.mysql.execute_query(query, params)
            
            return {
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size,
                'users': users
            }
            
        except Exception as e:
            logger.error(f"搜索用户失败: {e}")
            raise
    
    async def get_users_by_org(self, org_id: str) -> List[Dict[str, Any]]:
        """获取组织下的所有用户"""
        try:
            query = """
                SELECT 
                    u.id, u.username, u.realname, u.email, u.phone,
                    u.status, u.user_type, uo.is_main
                FROM sys_user u
                INNER JOIN sys_user_org uo ON u.id = uo.user_id
                WHERE uo.org_id = :org_id 
                AND u.del_flag = 0 AND uo.del_flag = 0
                ORDER BY uo.is_main DESC, u.realname ASC
            """
            
            return await self.mysql.execute_query(query, {'org_id': org_id})
            
        except Exception as e:
            logger.error(f"获取组织用户失败 {org_id}: {e}")
            raise
    
    # 用户统计
    async def get_user_statistics(
        self, 
        customer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取用户统计信息"""
        cache_key = f"{self.cache_prefix}stats:{customer_id or 'all'}"
        
        # 尝试从缓存获取
        cached_stats = await self.redis.get_json(cache_key)
        if cached_stats:
            return cached_stats
        
        try:
            params = {}
            where_clause = "WHERE u.del_flag = 0"
            
            if customer_id:
                where_clause += " AND u.customer_id = :customer_id"
                params['customer_id'] = customer_id
            
            # 基础统计
            basic_stats_query = f"""
                SELECT 
                    COUNT(*) as total_users,
                    COUNT(CASE WHEN u.status = 1 THEN 1 END) as active_users,
                    COUNT(CASE WHEN u.status = 0 THEN 1 END) as inactive_users,
                    COUNT(CASE WHEN u.user_type = 'admin' THEN 1 END) as admin_users,
                    COUNT(CASE WHEN u.user_type = 'user' THEN 1 END) as normal_users
                FROM sys_user u
                {where_clause}
            """
            
            basic_stats = await self.mysql.execute_first(basic_stats_query, params)
            
            # 性别统计
            gender_stats_query = f"""
                SELECT 
                    u.gender,
                    COUNT(*) as count
                FROM sys_user u
                {where_clause} AND u.gender IS NOT NULL
                GROUP BY u.gender
            """
            
            gender_stats = await self.mysql.execute_query(gender_stats_query, params)
            
            # 注册趋势（最近30天）
            trend_query = f"""
                SELECT 
                    DATE(u.created_time) as date,
                    COUNT(*) as count
                FROM sys_user u
                {where_clause} AND u.created_time >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                GROUP BY DATE(u.created_time)
                ORDER BY date DESC
            """
            
            trend_data = await self.mysql.execute_query(trend_query, params)
            
            stats = {
                'basic': basic_stats,
                'gender_distribution': gender_stats,
                'registration_trend': trend_data,
                'generated_at': datetime.now().isoformat()
            }
            
            # 缓存结果
            await self.redis.set_json(cache_key, stats, 300)  # 5分钟
            
            return stats
            
        except Exception as e:
            logger.error(f"获取用户统计失败: {e}")
            raise
    
    # 缓存管理
    async def clear_user_cache(self, user_id: str):
        """清除用户缓存"""
        try:
            cache_keys = [
                f"{self.cache_prefix}profile:{user_id}",
                f"{self.cache_prefix}permissions:{user_id}",
                f"{self.cache_prefix}roles:{user_id}"
            ]
            
            await self.redis.delete(*cache_keys)
            logger.debug(f"用户缓存已清除: {user_id}")
            
        except Exception as e:
            logger.error(f"清除用户缓存失败 {user_id}: {e}")
    
    async def refresh_user_cache(self, user_id: str):
        """刷新用户缓存"""
        try:
            # 清除旧缓存
            await self.clear_user_cache(user_id)
            
            # 预热缓存
            await self.get_user_by_id(user_id)
            
            logger.debug(f"用户缓存已刷新: {user_id}")
            
        except Exception as e:
            logger.error(f"刷新用户缓存失败 {user_id}: {e}")
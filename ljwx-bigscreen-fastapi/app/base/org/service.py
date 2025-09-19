"""
组织架构服务
提供组织结构的业务逻辑
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from app.base.mysql import MySQLClient
from app.base.redis import RedisClient
from .tree import OrgTreeBuilder

logger = logging.getLogger(__name__)


class OrganizationService:
    """组织架构服务"""
    
    def __init__(self, mysql_client: MySQLClient, redis_client: RedisClient):
        self.mysql = mysql_client
        self.redis = redis_client
        self.tree_builder = OrgTreeBuilder()
        self.cache_prefix = "org:"
        self.cache_ttl = 3600  # 1小时
    
    # 组织管理
    async def get_organization_tree(
        self, 
        customer_id: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """获取组织架构树"""
        cache_key = f"{self.cache_prefix}tree:{customer_id or 'all'}"
        
        if use_cache:
            cached_tree = await self.redis.get_json(cache_key)
            if cached_tree:
                return cached_tree
        
        try:
            # 查询组织数据
            query = """
                SELECT 
                    id, parent_id, org_name as name, org_code as code,
                    org_type as type, level, sort_order, status,
                    customer_id, created_time, updated_time
                FROM sys_org
                WHERE del_flag = 0
            """
            params = {}
            
            if customer_id:
                query += " AND customer_id = :customer_id"
                params['customer_id'] = customer_id
            
            query += " ORDER BY sort_order ASC, created_time ASC"
            
            org_data = await self.mysql.execute_query(query, params)
            
            # 构建树结构
            tree = self.tree_builder.build_tree(org_data)
            
            # 缓存结果
            if use_cache:
                await self.redis.set_json(cache_key, tree, self.cache_ttl)
            
            return tree
            
        except Exception as e:
            logger.error(f"获取组织架构树失败: {e}")
            raise
    
    async def get_organization_by_id(self, org_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取组织信息"""
        cache_key = f"{self.cache_prefix}org:{org_id}"
        
        # 尝试从缓存获取
        cached_org = await self.redis.get_json(cache_key)
        if cached_org:
            return cached_org
        
        try:
            query = """
                SELECT 
                    id, parent_id, org_name as name, org_code as code,
                    org_type as type, level, sort_order, status,
                    customer_id, description, created_time, updated_time
                FROM sys_org
                WHERE id = :org_id AND del_flag = 0
            """
            
            org = await self.mysql.execute_first(query, {'org_id': org_id})
            
            if org:
                # 缓存结果
                await self.redis.set_json(cache_key, org, self.cache_ttl)
            
            return org
            
        except Exception as e:
            logger.error(f"获取组织信息失败 {org_id}: {e}")
            raise
    
    async def get_child_organizations(
        self, 
        parent_id: Optional[str] = None,
        customer_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取子组织列表"""
        try:
            query = """
                SELECT 
                    id, parent_id, org_name as name, org_code as code,
                    org_type as type, level, sort_order, status,
                    customer_id, created_time, updated_time
                FROM sys_org
                WHERE del_flag = 0
            """
            params = {}
            
            if parent_id:
                query += " AND parent_id = :parent_id"
                params['parent_id'] = parent_id
            else:
                query += " AND (parent_id IS NULL OR parent_id = '')"
            
            if customer_id:
                query += " AND customer_id = :customer_id"
                params['customer_id'] = customer_id
            
            query += " ORDER BY sort_order ASC, created_time ASC"
            
            return await self.mysql.execute_query(query, params)
            
        except Exception as e:
            logger.error(f"获取子组织失败: {e}")
            raise
    
    async def get_organization_path(self, org_id: str) -> List[Dict[str, Any]]:
        """获取组织路径（从根到当前组织）"""
        try:
            query = """
                WITH RECURSIVE org_path AS (
                    -- 起始组织
                    SELECT id, parent_id, org_name as name, level, 0 as depth
                    FROM sys_org
                    WHERE id = :org_id AND del_flag = 0
                    
                    UNION ALL
                    
                    -- 递归查找父组织
                    SELECT o.id, o.parent_id, o.org_name as name, o.level, p.depth + 1
                    FROM sys_org o
                    INNER JOIN org_path p ON o.id = p.parent_id
                    WHERE o.del_flag = 0
                )
                SELECT id, parent_id, name, level
                FROM org_path
                ORDER BY depth DESC
            """
            
            return await self.mysql.execute_query(query, {'org_id': org_id})
            
        except Exception as e:
            logger.error(f"获取组织路径失败 {org_id}: {e}")
            raise
    
    async def get_organization_descendants(self, org_id: str) -> List[Dict[str, Any]]:
        """获取组织的所有后代"""
        try:
            query = """
                WITH RECURSIVE org_descendants AS (
                    -- 起始组织
                    SELECT id, parent_id, org_name as name, level, 0 as depth
                    FROM sys_org
                    WHERE id = :org_id AND del_flag = 0
                    
                    UNION ALL
                    
                    -- 递归查找子组织
                    SELECT o.id, o.parent_id, o.org_name as name, o.level, d.depth + 1
                    FROM sys_org o
                    INNER JOIN org_descendants d ON o.parent_id = d.id
                    WHERE o.del_flag = 0
                )
                SELECT id, parent_id, name, level, depth
                FROM org_descendants
                WHERE depth > 0
                ORDER BY depth ASC, name ASC
            """
            
            return await self.mysql.execute_query(query, {'org_id': org_id})
            
        except Exception as e:
            logger.error(f"获取组织后代失败 {org_id}: {e}")
            raise
    
    # 用户组织关系
    async def get_users_in_organization(
        self, 
        org_id: str,
        include_descendants: bool = False
    ) -> List[Dict[str, Any]]:
        """获取组织下的用户"""
        try:
            if include_descendants:
                # 获取包含子组织的所有用户
                query = """
                    WITH RECURSIVE org_tree AS (
                        SELECT id FROM sys_org WHERE id = :org_id AND del_flag = 0
                        UNION ALL
                        SELECT o.id FROM sys_org o
                        INNER JOIN org_tree t ON o.parent_id = t.id
                        WHERE o.del_flag = 0
                    )
                    SELECT DISTINCT
                        u.id, u.username, u.realname, u.email, u.phone,
                        u.status, uo.org_id, o.org_name
                    FROM sys_user u
                    INNER JOIN sys_user_org uo ON u.id = uo.user_id
                    INNER JOIN org_tree ot ON uo.org_id = ot.id
                    INNER JOIN sys_org o ON uo.org_id = o.id
                    WHERE u.del_flag = 0 AND uo.del_flag = 0
                    ORDER BY u.realname
                """
            else:
                # 只获取直接属于该组织的用户
                query = """
                    SELECT 
                        u.id, u.username, u.realname, u.email, u.phone,
                        u.status, uo.org_id, o.org_name
                    FROM sys_user u
                    INNER JOIN sys_user_org uo ON u.id = uo.user_id
                    INNER JOIN sys_org o ON uo.org_id = o.id
                    WHERE uo.org_id = :org_id 
                    AND u.del_flag = 0 AND uo.del_flag = 0
                    ORDER BY u.realname
                """
            
            return await self.mysql.execute_query(query, {'org_id': org_id})
            
        except Exception as e:
            logger.error(f"获取组织用户失败 {org_id}: {e}")
            raise
    
    async def get_user_organizations(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户所属的组织"""
        cache_key = f"{self.cache_prefix}user_orgs:{user_id}"
        
        # 尝试从缓存获取
        cached_orgs = await self.redis.get_json(cache_key)
        if cached_orgs:
            return cached_orgs
        
        try:
            query = """
                SELECT 
                    o.id, o.org_name as name, o.org_code as code,
                    o.org_type as type, o.level, uo.is_main
                FROM sys_org o
                INNER JOIN sys_user_org uo ON o.id = uo.org_id
                WHERE uo.user_id = :user_id 
                AND o.del_flag = 0 AND uo.del_flag = 0
                ORDER BY uo.is_main DESC, o.sort_order ASC
            """
            
            orgs = await self.mysql.execute_query(query, {'user_id': user_id})
            
            # 缓存结果
            await self.redis.set_json(cache_key, orgs, self.cache_ttl)
            
            return orgs
            
        except Exception as e:
            logger.error(f"获取用户组织失败 {user_id}: {e}")
            raise
    
    async def get_user_main_organization(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户主组织"""
        try:
            query = """
                SELECT 
                    o.id, o.org_name as name, o.org_code as code,
                    o.org_type as type, o.level
                FROM sys_org o
                INNER JOIN sys_user_org uo ON o.id = uo.org_id
                WHERE uo.user_id = :user_id AND uo.is_main = 1
                AND o.del_flag = 0 AND uo.del_flag = 0
                LIMIT 1
            """
            
            return await self.mysql.execute_first(query, {'user_id': user_id})
            
        except Exception as e:
            logger.error(f"获取用户主组织失败 {user_id}: {e}")
            raise
    
    # 统计分析
    async def get_organization_statistics(
        self, 
        org_id: Optional[str] = None,
        customer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取组织统计信息"""
        cache_key = f"{self.cache_prefix}stats:{org_id or 'all'}:{customer_id or 'all'}"
        
        # 尝试从缓存获取
        cached_stats = await self.redis.get_json(cache_key)
        if cached_stats:
            return cached_stats
        
        try:
            base_conditions = "WHERE o.del_flag = 0"
            params = {}
            
            if org_id:
                # 如果指定组织，统计该组织及其子组织
                base_conditions += """
                    AND o.id IN (
                        WITH RECURSIVE org_tree AS (
                            SELECT id FROM sys_org WHERE id = :org_id AND del_flag = 0
                            UNION ALL
                            SELECT child.id FROM sys_org child
                            INNER JOIN org_tree parent ON child.parent_id = parent.id
                            WHERE child.del_flag = 0
                        )
                        SELECT id FROM org_tree
                    )
                """
                params['org_id'] = org_id
            
            if customer_id:
                base_conditions += " AND o.customer_id = :customer_id"
                params['customer_id'] = customer_id
            
            # 组织统计
            org_stats_query = f"""
                SELECT 
                    COUNT(*) as total_orgs,
                    COUNT(CASE WHEN o.org_type = 'company' THEN 1 END) as companies,
                    COUNT(CASE WHEN o.org_type = 'department' THEN 1 END) as departments,
                    COUNT(CASE WHEN o.org_type = 'team' THEN 1 END) as teams,
                    COUNT(CASE WHEN o.status = 1 THEN 1 END) as active_orgs
                FROM sys_org o
                {base_conditions}
            """
            
            org_stats = await self.mysql.execute_first(org_stats_query, params)
            
            # 用户统计
            user_stats_query = f"""
                SELECT 
                    COUNT(DISTINCT u.id) as total_users,
                    COUNT(DISTINCT CASE WHEN u.status = 1 THEN u.id END) as active_users
                FROM sys_user u
                INNER JOIN sys_user_org uo ON u.id = uo.user_id
                INNER JOIN sys_org o ON uo.org_id = o.id
                {base_conditions} AND u.del_flag = 0 AND uo.del_flag = 0
            """
            
            user_stats = await self.mysql.execute_first(user_stats_query, params)
            
            # 层级统计
            level_stats_query = f"""
                SELECT 
                    o.level,
                    COUNT(*) as count
                FROM sys_org o
                {base_conditions}
                GROUP BY o.level
                ORDER BY o.level
            """
            
            level_stats = await self.mysql.execute_query(level_stats_query, params)
            
            stats = {
                'organization': org_stats,
                'user': user_stats,
                'level_distribution': level_stats,
                'generated_at': datetime.now().isoformat()
            }
            
            # 缓存结果（较短的TTL）
            await self.redis.set_json(cache_key, stats, 300)  # 5分钟
            
            return stats
            
        except Exception as e:
            logger.error(f"获取组织统计失败: {e}")
            raise
    
    # 缓存管理
    async def clear_organization_cache(
        self, 
        org_id: Optional[str] = None,
        customer_id: Optional[str] = None
    ):
        """清除组织缓存"""
        try:
            if org_id:
                # 清除特定组织的缓存
                await self.redis.delete(f"{self.cache_prefix}org:{org_id}")
            
            if customer_id:
                # 清除特定租户的缓存
                pattern = f"{self.cache_prefix}*:{customer_id}"
                keys = await self.redis.scan_keys(pattern)
                if keys:
                    await self.redis.delete(*keys)
            else:
                # 清除所有组织缓存
                pattern = f"{self.cache_prefix}*"
                keys = await self.redis.scan_keys(pattern)
                if keys:
                    await self.redis.delete(*keys)
            
            logger.info(f"组织缓存已清除: org_id={org_id}, customer_id={customer_id}")
            
        except Exception as e:
            logger.error(f"清除组织缓存失败: {e}")
    
    async def refresh_organization_cache(self, customer_id: Optional[str] = None):
        """刷新组织缓存"""
        try:
            # 清除旧缓存
            await self.clear_organization_cache(customer_id=customer_id)
            
            # 预热缓存
            await self.get_organization_tree(customer_id=customer_id, use_cache=True)
            
            logger.info(f"组织缓存已刷新: customer_id={customer_id}")
            
        except Exception as e:
            logger.error(f"刷新组织缓存失败: {e}")
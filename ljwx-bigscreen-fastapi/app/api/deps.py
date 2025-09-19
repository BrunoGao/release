"""
API 依赖注入
提供通用的依赖项
"""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_write_db, get_read_db
from app.core.cache import get_cache
from app.base.redis import RedisClient
from app.base.mysql import MySQLClient
from app.base.user import UserService
from app.base.org import OrganizationService
from app.config.settings import get_settings

settings = get_settings()
security = HTTPBearer()


# 数据库依赖
async def get_mysql_client(
    db: AsyncSession = Depends(get_write_db)
) -> MySQLClient:
    """获取 MySQL 客户端"""
    return MySQLClient(db)


async def get_redis_client() -> RedisClient:
    """获取 Redis 客户端"""
    return RedisClient()


# 服务依赖
async def get_user_service(
    mysql_client: MySQLClient = Depends(get_mysql_client),
    redis_client: RedisClient = Depends(get_redis_client)
) -> UserService:
    """获取用户服务"""
    return UserService(mysql_client, redis_client)


async def get_org_service(
    mysql_client: MySQLClient = Depends(get_mysql_client),
    redis_client: RedisClient = Depends(get_redis_client)
) -> OrganizationService:
    """获取组织服务"""
    return OrganizationService(mysql_client, redis_client)


# 认证依赖
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """验证 JWT Token"""
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    token_payload: dict = Depends(verify_token),
    user_service: UserService = Depends(get_user_service)
) -> dict:
    """获取当前用户"""
    user_id = token_payload.get("sub")
    
    user = await user_service.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if user['status'] != 1:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )
    
    return user


async def get_current_active_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """获取当前活跃用户"""
    return current_user


# 权限依赖
def require_permissions(*permissions: str):
    """要求特定权限"""
    async def permission_checker(
        current_user: dict = Depends(get_current_active_user)
    ) -> dict:
        # 这里实现权限检查逻辑
        # 简化版本：检查用户角色
        user_roles = current_user.get('roles', [])
        
        # 管理员拥有所有权限
        if 'admin' in user_roles:
            return current_user
        
        # 检查特定权限
        # 实际项目中需要实现更复杂的权限验证逻辑
        
        return current_user
    
    return permission_checker


def require_customer_access(customer_id: str):
    """要求客户访问权限"""
    async def customer_checker(
        current_user: dict = Depends(get_current_active_user)
    ) -> dict:
        user_customer_id = current_user.get('customer_id')
        
        # 检查用户是否属于该客户
        if user_customer_id != customer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: insufficient customer permissions"
            )
        
        return current_user
    
    return customer_checker


# 分页依赖
class PaginationParams:
    """分页参数"""
    def __init__(
        self,
        page: int = 1,
        page_size: int = 20,
        max_page_size: int = 100
    ):
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 20
        if page_size > max_page_size:
            page_size = max_page_size
            
        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size


def get_pagination_params(
    page: int = 1,
    page_size: int = 20
) -> PaginationParams:
    """获取分页参数"""
    return PaginationParams(page, page_size)


# 请求上下文
async def get_request_context(request: Request) -> dict:
    """获取请求上下文信息"""
    return {
        'ip_address': request.client.host,
        'user_agent': request.headers.get('user-agent'),
        'request_id': request.headers.get('x-request-id'),
        'timestamp': request.state.__dict__.get('start_time')
    }


# 业务服务依赖
async def get_alert_service(
    mysql_client: MySQLClient = Depends(get_mysql_client),
    redis_client: RedisClient = Depends(get_redis_client)
):
    """获取告警服务"""
    from app.business.alert import AlertService
    return AlertService(mysql_client, redis_client)


async def get_health_service(
    mysql_client: MySQLClient = Depends(get_mysql_client),
    redis_client: RedisClient = Depends(get_redis_client)
):
    """获取健康数据服务"""
    from app.business.health_data import HealthDataService
    return HealthDataService(mysql_client, redis_client)


# 缓存依赖
async def get_cache_client():
    """获取缓存客户端"""
    return get_cache()


# 可选认证（某些接口可以匿名访问）
async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    user_service: UserService = Depends(get_user_service)
) -> Optional[dict]:
    """获取可选的当前用户（支持匿名访问）"""
    if not credentials:
        return None
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        
        user_id = payload.get("sub")
        if user_id:
            user = await user_service.get_user_by_id(user_id)
            if user and user['status'] == 1:
                return user
    except JWTError:
        pass
    
    return None
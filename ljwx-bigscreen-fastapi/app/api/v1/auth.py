"""
认证相关 API
"""

from datetime import datetime, timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from jose import jwt

from app.api.deps import get_user_service, get_current_user
from app.base.user import UserService
from app.config.settings import get_settings

router = APIRouter()
settings = get_settings()


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user_info: dict


class UserLogin(BaseModel):
    username: str
    password: str


class UserInfo(BaseModel):
    id: str
    username: str
    realname: str
    email: str
    phone: str
    avatar: str
    status: int
    user_type: str
    org_id: str
    org_name: str
    roles: list


class ChangePassword(BaseModel):
    old_password: str
    new_password: str


def create_access_token(data: dict, expires_delta: timedelta = None):
    """创建访问令牌"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    
    return encoded_jwt


@router.post("/login", response_model=Token, summary="用户登录")
async def login(
    user_credentials: UserLogin,
    user_service: UserService = Depends(get_user_service)
):
    """
    用户登录接口
    
    - **username**: 用户名
    - **password**: 密码
    """
    # 验证用户凭据
    user = await user_service.get_user_by_username(user_credentials.username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 验证密码
    if not user_service.password_manager.verify_password(
        user_credentials.password, user['password'], user['salt']
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查用户状态
    if user['status'] != 1:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账户已被禁用"
        )
    
    # 获取完整用户信息
    user_info = await user_service.get_user_by_id(user['id'])
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user['id'], "username": user['username']},
        expires_delta=access_token_expires
    )
    
    # 返回令牌和用户信息
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_info={
            "id": user_info['id'],
            "username": user_info['username'],
            "realname": user_info['realname'],
            "email": user_info['email'],
            "phone": user_info['phone'],
            "avatar": user_info['avatar'],
            "status": user_info['status'],
            "user_type": user_info['user_type'],
            "org_id": user_info.get('org_id'),
            "org_name": user_info.get('org_name'),
            "roles": user_info.get('roles', [])
        }
    )


@router.post("/token", response_model=Token, summary="获取访问令牌")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_service: UserService = Depends(get_user_service)
):
    """
    OAuth2 兼容的令牌获取接口
    """
    user_credentials = UserLogin(
        username=form_data.username,
        password=form_data.password
    )
    
    return await login(user_credentials, user_service)


@router.get("/me", response_model=UserInfo, summary="获取当前用户信息")
async def get_current_user_info(
    current_user: dict = Depends(get_current_user)
):
    """
    获取当前登录用户的详细信息
    """
    return UserInfo(
        id=current_user['id'],
        username=current_user['username'],
        realname=current_user['realname'],
        email=current_user['email'] or "",
        phone=current_user['phone'] or "",
        avatar=current_user['avatar'] or "",
        status=current_user['status'],
        user_type=current_user['user_type'],
        org_id=current_user.get('org_id', ""),
        org_name=current_user.get('org_name', ""),
        roles=current_user.get('roles', [])
    )


@router.post("/change-password", summary="修改密码")
async def change_password(
    password_data: ChangePassword,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    修改当前用户密码
    
    - **old_password**: 原密码
    - **new_password**: 新密码
    """
    success = await user_service.change_password(
        current_user['id'],
        password_data.old_password,
        password_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码修改失败"
        )
    
    return {"message": "密码修改成功"}


@router.post("/logout", summary="用户登出")
async def logout(
    current_user: dict = Depends(get_current_user)
):
    """
    用户登出接口
    
    注意：JWT 是无状态的，实际的登出需要客户端删除令牌
    这里主要用于记录登出日志
    """
    # 可以在这里添加登出日志记录
    # 或者将令牌加入黑名单（需要 Redis 支持）
    
    return {"message": "登出成功"}


@router.post("/refresh", response_model=Token, summary="刷新访问令牌")
async def refresh_access_token(
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    刷新访问令牌
    """
    # 检查用户状态
    user = await user_service.get_user_by_id(current_user['id'])
    if not user or user['status'] != 1:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户状态异常"
        )
    
    # 创建新的访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user['id'], "username": user['username']},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_info={
            "id": user['id'],
            "username": user['username'],
            "realname": user['realname'],
            "email": user['email'],
            "phone": user['phone'],
            "avatar": user['avatar'],
            "status": user['status'],
            "user_type": user['user_type'],
            "org_id": user.get('org_id'),
            "org_name": user.get('org_name'),
            "roles": user.get('roles', [])
        }
    )
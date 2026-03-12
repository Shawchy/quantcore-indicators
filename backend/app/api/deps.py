from typing import Optional
try:
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger

from app.core.security import (
    verify_access_token,
    TokenData,
    User
)


# HTTP Bearer Token 认证
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)]
) -> User:
    """
    获取当前登录用户
    
    使用方式:
    @router.get("/protected")
    async def protected_route(current_user: User = Depends(get_current_user)):
        return {"user": current_user.username}
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    token_data = verify_access_token(token)
    
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌无效或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 这里应该从数据库获取用户信息
    # 为了简化，直接创建 User 对象
    user = User(
        user_id=token_data.user_id,
        username=token_data.username,
        role=token_data.role,
        is_active=True
    )
    
    logger.debug(f"用户认证成功：{user.username}")
    
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    return current_user


async def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """获取当前管理员用户"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


async def get_optional_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)]
) -> Optional[User]:
    """
    获取当前登录用户（可选）
    
    使用方式:
    @router.get("/public")
    async def public_route(current_user: OptionalCurrentUser = None):
        return {"user": current_user.username if current_user else "anonymous"}
    """
    if credentials is None:
        return None
    
    token = credentials.credentials
    token_data = verify_access_token(token)
    
    if token_data is None:
        return None
    
    user = User(
        user_id=token_data.user_id,
        username=token_data.username,
        role=token_data.role,
        is_active=True
    )
    
    logger.debug(f"用户认证成功：{user.username}")
    
    return user


# 便捷的类型注解
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentActiveUser = Annotated[User, Depends(get_current_active_user)]
CurrentAdminUser = Annotated[User, Depends(get_current_admin_user)]
OptionalCurrentUser = Annotated[Optional[User], Depends(get_optional_current_user)]

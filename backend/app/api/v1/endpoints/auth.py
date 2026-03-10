from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from loguru import logger

from app.core.security import (
    login_for_access_token,
    refresh_access_token,
    Token,
    User
)
from app.api.deps import CurrentUser


router = APIRouter(prefix="/auth", tags=["认证"])


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/login", response_model=Token)
async def login(request: LoginRequest):
    """
    用户登录
    
    - **username**: 用户名
    - **password**: 密码
    
    默认用户:
    - admin / admin123 (管理员)
    - user / user123 (普通用户)
    """
    try:
        token = await login_for_access_token(request.username, request.password)
        logger.info(f"用户 {request.username} 登录成功")
        return token
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(request: RefreshTokenRequest):
    """刷新访问令牌"""
    try:
        token = await refresh_access_token(request.refresh_token)
        return token
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: CurrentUser):
    """获取当前用户信息"""
    return current_user


@router.post("/logout")
async def logout(current_user: CurrentUser):
    """用户登出"""
    # 实际应用中应该将令牌加入黑名单
    logger.info(f"用户 {current_user.username} 登出")
    return {"message": "登出成功"}

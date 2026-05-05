import hashlib
import asyncio
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from loguru import logger

from app.core.security import (
    login_for_access_token,
    refresh_access_token,
    Token,
    User,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
from app.api.deps import CurrentUser
from app.config import settings
from app.core.token_blacklist import token_blacklist


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
    """
    try:
        token = await login_for_access_token(request.username, request.password)
        logger.info(f"用户 {request.username} 登录成功")
        return token
    except ValueError as e:
        logger.warning(f"登录失败 [{request.username}]: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e) if settings.DEBUG else "用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(request: RefreshTokenRequest):
    """刷新访问令牌"""
    # 1. 先检查令牌是否已被撤销
    if await token_blacklist.is_revoked(request.refresh_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="刷新令牌已被撤销",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # 2. 刷新令牌（生成新的访问令牌和刷新令牌）
        token = await refresh_access_token(request.refresh_token)
        
        # 3. 刷新成功后撤销旧刷新令牌（防止重复使用）
        try:
            await token_blacklist.revoke(request.refresh_token, token_type="refresh")
        except Exception as revoke_error:
            # 撤销失败不影响令牌返回，但需要记录日志以便后续处理
            logger.error(f"旧刷新令牌撤销失败: {revoke_error}，令牌仍可使用但存在重复使用风险")
        
        return token
    except ValueError as e:
        logger.warning(f"令牌刷新失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e) if settings.DEBUG else "刷新令牌无效或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: CurrentUser):
    """获取当前用户信息"""
    return current_user


@router.post("/logout")
async def logout(current_user: CurrentUser, request: Request):
    """用户登出"""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        access_token = auth_header[7:]
        await token_blacklist.revoke(access_token, token_type="access")
    logger.info(f"用户 {current_user.username} 登出")
    return {"message": "登出成功"}

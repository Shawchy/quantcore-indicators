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


router = APIRouter(prefix="/auth", tags=["认证"])


class TokenBlacklist:
    def __init__(self):
        self._cache: set[str] = set()
        self._initialized = asyncio.Event()

    async def initialize(self):
        if self._initialized.is_set():
            return
        try:
            from app.storage.sqlite import get_session, RevokedToken
            from sqlalchemy import select, delete
            now = datetime.now(timezone.utc)
            async with get_session() as session:
                await session.execute(
                    delete(RevokedToken).where(RevokedToken.expires_at <= now)
                )
                await session.commit()
                result = await session.execute(
                    select(RevokedToken.token_hash).where(RevokedToken.expires_at > now)
                )
                self._cache = {row[0] for row in result.all()}
            logger.info(f"令牌黑名单已初始化，加载 {len(self._cache)} 条记录")
        except Exception as e:
            logger.warning(f"令牌黑名单初始化失败，使用空缓存：{e}")
        finally:
            self._initialized.set()

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    async def is_revoked(self, token: str) -> bool:
        if not self._initialized.is_set():
            await self.initialize()
        return self._hash_token(token) in self._cache

    async def revoke(self, token: str, token_type: str = "access"):
        if not self._initialized.is_set():
            await self.initialize()
        token_hash = self._hash_token(token)
        if token_hash in self._cache:
            return
        if token_type == "refresh":
            expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        else:
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        try:
            from app.storage.sqlite import get_session, RevokedToken
            async with get_session() as session:
                existing = await session.execute(
                    RevokedToken.__table__.select().where(RevokedToken.token_hash == token_hash)
                )
                if existing.first() is None:
                    session.add(RevokedToken(
                        token_hash=token_hash,
                        token_type=token_type,
                        expires_at=expires_at,
                    ))
                    await session.commit()
                self._cache.add(token_hash)
        except IntegrityError:
            self._cache.add(token_hash)
            logger.debug(f"令牌撤销记录已存在，跳过：{token_hash[:8]}...")
        except Exception as e:
            self._cache.discard(token_hash)
            logger.error(f"令牌撤销失败：{e}")


token_blacklist = TokenBlacklist()


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
    if await token_blacklist.is_revoked(request.refresh_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="刷新令牌已被撤销",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        token = await refresh_access_token(request.refresh_token)
        await token_blacklist.revoke(request.refresh_token, token_type="refresh")
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

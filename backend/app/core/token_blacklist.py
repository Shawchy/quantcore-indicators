"""令牌黑名单服务

独立的令牌黑名单管理模块，避免 deps.py 和 auth.py 之间的循环依赖。
使用数据库持久化 + 内存缓存的双重存储策略。
"""

import hashlib
import asyncio
from datetime import datetime, timedelta, timezone
from loguru import logger

from app.core.security import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS


class TokenBlacklist:
    """令牌黑名单（数据库持久化 + 内存缓存）"""

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
        except Exception as e:
            logger.error(f"令牌撤销持久化失败：{e}")
            self._cache.add(token_hash)


token_blacklist = TokenBlacklist()

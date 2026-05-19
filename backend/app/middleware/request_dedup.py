"""
请求去重中间件

防止短时间内重复请求压垮系统，对相同请求进行合并/去重
"""
import asyncio
import hashlib
import time
from collections import defaultdict
from typing import Dict, Optional, Tuple

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger


class RequestDeduplicator:
    """请求去重器 - 基于 IP + 路径 + 参数的指纹去重"""

    def __init__(
        self,
        window_seconds: float = 2.0,
        max_pending_per_key: int = 10,
        cleanup_interval: int = 60,
    ):
        self._window = window_seconds
        self._max_pending = max_pending_per_key
        self._cleanup_interval = cleanup_interval

        self._pending: Dict[str, list] = defaultdict(list)
        self._fingerprints: Dict[str, float] = {}
        self._lock = asyncio.Lock()

        self._stats = {
            "total_requests": 0,
            "deduplicated": 0,
            "passed": 0,
        }

    def _make_fingerprint(self, request: Request) -> str:
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        query = str(request.query_params) if request.query_params else ""
        method = request.method
        raw = f"{method}:{client_ip}:{path}:{query}"
        return hashlib.md5(raw.encode()).hexdigest()

    def _is_duplicate(self, fingerprint: str) -> bool:
        now = time.time()
        last_time = self._fingerprints.get(fingerprint)
        if last_time is not None and (now - last_time) < self._window:
            return True
        return False

    async def check(self, request: Request) -> Tuple[bool, str]:
        self._stats["total_requests"] += 1
        fingerprint = self._make_fingerprint(request)

        async with self._lock:
            pending_list = self._pending[fingerprint]
            if len(pending_list) >= self._max_pending:
                self._stats["deduplicated"] += 1
                return True, fingerprint

            if self._is_duplicate(fingerprint):
                pending_list.append(time.time())
                self._stats["deduplicated"] += 1
                return True, fingerprint

            self._fingerprints[fingerprint] = time.time()
            self._stats["passed"] += 1
            return False, fingerprint

    async def record_completion(self, fingerprint: str):
        async with self._lock:
            if fingerprint in self._pending:
                self._pending[fingerprint] = self._pending[fingerprint][1:]
                if not self._pending[fingerprint]:
                    del self._pending[fingerprint]

    async def cleanup(self):
        now = time.time()
        async with self._lock:
            expired_fps = [
                fp for fp, t in self._fingerprints.items()
                if (now - t) > self._window * 3
            ]
            for fp in expired_fps:
                del self._fingerprints[fp]

            for fp in list(self._pending.keys()):
                self._pending[fp] = [
                    t for t in self._pending[fp]
                    if (now - t) < self._window * 3
                ]
                if not self._pending[fp]:
                    del self._pending[fp]

    def get_stats(self) -> dict:
        total = self._stats["total_requests"]
        dedup_rate = (
            self._stats["deduplicated"] / total * 100
            if total > 0 else 0.0
        )
        return {
            **self._stats,
            "dedup_rate": f"{dedup_rate:.2f}%",
            "active_fingerprints": len(self._fingerprints),
            "pending_keys": len(self._pending),
            "window_seconds": self._window,
        }


request_deduplicator = RequestDeduplicator()


class RequestDedupMiddleware(BaseHTTPMiddleware):
    """请求去重 HTTP 中间件"""

    SKIP_PATHS = {
        "/docs", "/redoc", "/openapi.json",
        "/health", "/metrics", "/ready",
    }

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        if path in self.SKIP_PATHS or path.startswith("/docs"):
            return await call_next(request)

        if request.method != "GET":
            return await call_next(request)

        is_dup, fingerprint = await request_deduplicator.check(request)

        if is_dup:
            return Response(
                content='{"success":false,"code":"DUPLICATE_REQUEST","message":"请求过于频繁，请稍后再试","data":null}',
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": str(int(request_deduplicator._window))},
            )

        try:
            response = await call_next(request)
            return response
        finally:
            await request_deduplicator.record_completion(fingerprint)


async def dedup_cleanup_task():
    """定期清理过期指纹"""
    while True:
        await asyncio.sleep(request_deduplicator._cleanup_interval)
        try:
            await request_deduplicator.cleanup()
        except Exception as e:
            logger.error(f"去重清理任务异常: {e}")


def dedup_middleware_stats() -> dict:
    return request_deduplicator.get_stats()

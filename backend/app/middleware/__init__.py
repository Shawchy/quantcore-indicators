"""
中间件模块

提供限流、熔断、监控、去重等中间件功能
"""
from .rate_limiter import (
    TokenBucketRateLimiter,
    rate_limiters,
    init_rate_limiters,
    get_rate_limiter,
    RATE_LIMIT_CONFIG
)
from .circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    circuit_breakers,
    init_circuit_breakers,
    get_circuit_breaker,
    CIRCUIT_BREAKER_CONFIG
)
from .request_dedup import (
    RequestDeduplicator,
    RequestDedupMiddleware,
    request_deduplicator,
    dedup_middleware_stats,
)


def init_middleware():
    """初始化所有中间件"""
    init_rate_limiters()
    init_circuit_breakers()

    from loguru import logger
    logger.info("中间件初始化完成")


__all__ = [
    "TokenBucketRateLimiter",
    "rate_limiters",
    "init_rate_limiters",
    "get_rate_limiter",
    "RATE_LIMIT_CONFIG",

    "CircuitBreaker",
    "CircuitState",
    "circuit_breakers",
    "init_circuit_breakers",
    "get_circuit_breaker",
    "CIRCUIT_BREAKER_CONFIG",

    "RequestDeduplicator",
    "RequestDedupMiddleware",
    "request_deduplicator",
    "dedup_middleware_stats",

    "init_middleware",
]

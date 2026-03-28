"""
监控指标收集器

收集和记录系统性能指标
"""
from prometheus_client import Counter, Histogram, Gauge
from datetime import datetime
import time
from typing import Dict, Any
from loguru import logger


# Prometheus 指标定义
REQUEST_COUNT = Counter(
    'data_source_requests_total',
    'Total requests to data sources',
    ['source', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'data_source_request_duration_seconds',
    'Request duration in seconds',
    ['source', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

DATA_QUALITY_SCORE = Gauge(
    'data_quality_score',
    'Data quality score (0-1)',
    ['source', 'data_type']
)

CACHE_HIT_RATE = Gauge(
    'cache_hit_rate',
    'Cache hit rate (0-1)',
    ['cache_type']
)

CIRCUIT_BREAKER_STATE = Gauge(
    'circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=open, 2=half_open)',
    ['source']
)

RATE_LIMITER_REJECTION = Counter(
    'rate_limiter_rejection_total',
    'Total rate limiter rejections',
    ['source']
)


class MetricsCollector:
    """指标收集器"""
    
    @staticmethod
    def record_request(
        source: str,
        endpoint: str,
        duration: float,
        success: bool
    ):
        """
        记录请求指标
        
        Args:
            source: 数据源名称
            endpoint: 端点名称
            duration: 请求持续时间（秒）
            success: 是否成功
        """
        status = "success" if success else "failure"
        
        REQUEST_COUNT.labels(
            source=source,
            endpoint=endpoint,
            status=status
        ).inc()
        
        REQUEST_DURATION.labels(
            source=source,
            endpoint=endpoint
        ).observe(duration)
        
        logger.debug(
            f"记录请求指标: {source}/{endpoint}, "
            f"耗时: {duration:.3f}s, "
            f"状态: {status}"
        )
    
    @staticmethod
    def record_data_quality(
        source: str,
        data_type: str,
        score: float
    ):
        """
        记录数据质量
        
        Args:
            source: 数据源名称
            data_type: 数据类型
            score: 质量评分 (0-1)
        """
        DATA_QUALITY_SCORE.labels(
            source=source,
            data_type=data_type
        ).set(score)
        
        logger.debug(
            f"记录数据质量: {source}/{data_type}, "
            f"评分: {score:.2f}"
        )
    
    @staticmethod
    def record_cache_hit_rate(
        cache_type: str,
        hit_rate: float
    ):
        """
        记录缓存命中率
        
        Args:
            cache_type: 缓存类型
            hit_rate: 命中率 (0-1)
        """
        CACHE_HIT_RATE.labels(
            cache_type=cache_type
        ).set(hit_rate)
        
        logger.debug(
            f"记录缓存命中率: {cache_type}, "
            f"命中率: {hit_rate:.2%}"
        )
    
    @staticmethod
    def record_circuit_breaker_state(
        source: str,
        state: str
    ):
        """
        记录断路器状态
        
        Args:
            source: 数据源名称
            state: 断路器状态 (closed/open/half_open)
        """
        state_map = {
            "closed": 0,
            "open": 1,
            "half_open": 2
        }
        
        CIRCUIT_BREAKER_STATE.labels(
            source=source
        ).set(state_map.get(state, 0))
        
        logger.debug(
            f"记录断路器状态: {source}, "
            f"状态: {state}"
        )
    
    @staticmethod
    def record_rate_limiter_rejection(source: str):
        """
        记录限流器拒绝
        
        Args:
            source: 数据源名称
        """
        RATE_LIMITER_REJECTION.labels(
            source=source
        ).inc()
        
        logger.debug(f"记录限流器拒绝: {source}")
    
    @staticmethod
    def get_all_metrics() -> Dict[str, Any]:
        """获取所有指标"""
        return {
            "requests": {
                "count": REQUEST_COUNT._metrics,
                "duration": REQUEST_DURATION._metrics,
            },
            "quality": DATA_QUALITY_SCORE._metrics,
            "cache": CACHE_HIT_RATE._metrics,
            "circuit_breaker": CIRCUIT_BREAKER_STATE._metrics,
            "rate_limiter": RATE_LIMITER_REJECTION._metrics,
        }


# 性能监控装饰器
def monitor_performance(source: str, endpoint: str):
    """
    性能监控装饰器
    
    用法:
        @monitor_performance("efinance", "get_kline")
        async def get_kline(code: str):
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise e
            finally:
                duration = time.time() - start_time
                MetricsCollector.record_request(
                    source,
                    endpoint,
                    duration,
                    success
                )
        
        return wrapper
    return decorator

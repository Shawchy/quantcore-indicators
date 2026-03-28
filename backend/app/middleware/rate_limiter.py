"""
令牌桶限流器

实现基于令牌桶算法的限流机制，防止数据源被过度请求
"""
import time
from collections import defaultdict
from datetime import datetime
from typing import Dict, Optional
from loguru import logger


class TokenBucketRateLimiter:
    """令牌桶限流器"""
    
    def __init__(self, rate: float, capacity: int):
        """
        初始化令牌桶限流器
        
        Args:
            rate: 令牌生成速率 (个/秒)
            capacity: 桶容量 (最大令牌数)
        """
        self.rate = rate
        self.capacity = capacity
        self._buckets: Dict[str, dict] = defaultdict(lambda: {
            "tokens": capacity,
            "last_update": time.time()
        })
        self._stats = defaultdict(lambda: {"allowed": 0, "rejected": 0})
    
    async def acquire(self, key: str, tokens: int = 1) -> bool:
        """
        获取令牌
        
        Args:
            key: 限流键 (如数据源名称)
            tokens: 需要的令牌数
        
        Returns:
            是否成功获取令牌
        """
        bucket = self._buckets[key]
        now = time.time()
        
        # 添加令牌
        elapsed = now - bucket["last_update"]
        bucket["tokens"] = min(
            self.capacity,
            bucket["tokens"] + elapsed * self.rate
        )
        bucket["last_update"] = now
        
        # 检查是否有足够令牌
        if bucket["tokens"] >= tokens:
            bucket["tokens"] -= tokens
            self._stats[key]["allowed"] += 1
            return True
        else:
            self._stats[key]["rejected"] += 1
            logger.warning(
                f"限流触发: {key}, "
                f"当前令牌: {bucket['tokens']:.2f}, "
                f"需要: {tokens}"
            )
            return False
    
    def get_stats(self, key: str) -> dict:
        """
        获取统计信息
        
        Args:
            key: 限流键
        
        Returns:
            统计信息字典
        """
        bucket = self._buckets[key]
        stats = self._stats[key]
        
        total = stats["allowed"] + stats["rejected"]
        rejection_rate = (
            stats["rejected"] / total * 100 
            if total > 0 else 0.0
        )
        
        return {
            "key": key,
            "current_tokens": round(bucket["tokens"], 2),
            "capacity": self.capacity,
            "rate": self.rate,
            "allowed": stats["allowed"],
            "rejected": stats["rejected"],
            "rejection_rate": f"{rejection_rate:.2f}%",
            "last_update": datetime.fromtimestamp(
                bucket["last_update"]
            ).isoformat()
        }
    
    def get_all_stats(self) -> Dict[str, dict]:
        """获取所有键的统计信息"""
        return {
            key: self.get_stats(key)
            for key in self._buckets.keys()
        }
    
    def reset(self, key: str):
        """重置指定键的限流器"""
        if key in self._buckets:
            self._buckets[key] = {
                "tokens": self.capacity,
                "last_update": time.time()
            }
            self._stats[key] = {"allowed": 0, "rejected": 0}
            logger.info(f"限流器已重置: {key}")


# 数据源限流配置
RATE_LIMIT_CONFIG = {
    "efinance": {"rate": 10, "capacity": 60},      # 10 个/秒，峰值 60
    "akshare": {"rate": 5, "capacity": 30},        # 5 个/秒，峰值 30
    "baostock": {"rate": 3, "capacity": 20},       # 3 个/秒，峰值 20
    "tickflow": {"rate": 20, "capacity": 100},     # 20 个/秒，峰值 100
}

# 全局限流器实例
rate_limiters: Dict[str, TokenBucketRateLimiter] = {}


def init_rate_limiters():
    """初始化限流器"""
    global rate_limiters
    
    for source, config in RATE_LIMIT_CONFIG.items():
        rate_limiters[source] = TokenBucketRateLimiter(
            rate=config["rate"],
            capacity=config["capacity"]
        )
        logger.info(
            f"初始化限流器: {source}, "
            f"速率: {config['rate']}/s, "
            f"容量: {config['capacity']}"
        )


def get_rate_limiter(source: str) -> Optional[TokenBucketRateLimiter]:
    """获取指定数据源的限流器"""
    return rate_limiters.get(source)

"""
缓存优化器

提供多级缓存、缓存预热和缓存策略管理
"""
import time
import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from loguru import logger
from functools import wraps
from collections import OrderedDict


class LRUCache:
    """LRU 缓存实现"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 300):
        self.max_size = max_size
        self.ttl = ttl
        self.cache: OrderedDict = OrderedDict()
        self.access_times: Dict[str, float] = {}
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_size": 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key in self.cache:
            if time.time() - self.access_times[key] < self.ttl:
                self.cache.move_to_end(key)
                self.stats["hits"] += 1
                return self.cache[key]
            else:
                del self.cache[key]
                del self.access_times[key]
        
        self.stats["misses"] += 1
        return None
    
    def set(self, key: str, value: Any):
        """设置缓存"""
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.max_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                del self.access_times[oldest_key]
                self.stats["evictions"] += 1
            
            self.stats["total_size"] += 1
        
        self.cache[key] = value
        self.access_times[key] = time.time()
    
    def delete(self, key: str):
        """删除缓存"""
        if key in self.cache:
            del self.cache[key]
            del self.access_times[key]
            self.stats["total_size"] -= 1
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.access_times.clear()
        self.stats["total_size"] = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0
        
        return {
            **self.stats,
            "hit_rate": f"{hit_rate:.2%}",
            "size": len(self.cache),
            "max_size": self.max_size
        }


class MultiLevelCache:
    """多级缓存"""
    
    def __init__(self):
        self.l1_cache = LRUCache(max_size=100, ttl=60)
        self.l2_cache = LRUCache(max_size=1000, ttl=300)
        self.l3_cache = LRUCache(max_size=10000, ttl=3600)
        
        self.stats = {
            "l1_hits": 0,
            "l2_hits": 0,
            "l3_hits": 0,
            "total_misses": 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """从多级缓存获取"""
        value = self.l1_cache.get(key)
        if value is not None:
            self.stats["l1_hits"] += 1
            return value
        
        value = self.l2_cache.get(key)
        if value is not None:
            self.stats["l2_hits"] += 1
            self.l1_cache.set(key, value)
            return value
        
        value = self.l3_cache.get(key)
        if value is not None:
            self.stats["l3_hits"] += 1
            self.l2_cache.set(key, value)
            self.l1_cache.set(key, value)
            return value
        
        self.stats["total_misses"] += 1
        return None
    
    def set(self, key: str, value: Any, level: str = "all"):
        """设置多级缓存"""
        if level in ["all", "l1"]:
            self.l1_cache.set(key, value)
        if level in ["all", "l2"]:
            self.l2_cache.set(key, value)
        if level in ["all", "l3"]:
            self.l3_cache.set(key, value)
    
    def delete(self, key: str):
        """从所有级别删除"""
        self.l1_cache.delete(key)
        self.l2_cache.delete(key)
        self.l3_cache.delete(key)
    
    def clear_all(self):
        """清空所有缓存"""
        self.l1_cache.clear()
        self.l2_cache.clear()
        self.l3_cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_requests = (
            self.stats["l1_hits"] + 
            self.stats["l2_hits"] + 
            self.stats["l3_hits"] + 
            self.stats["total_misses"]
        )
        
        return {
            "l1_cache": self.l1_cache.get_stats(),
            "l2_cache": self.l2_cache.get_stats(),
            "l3_cache": self.l3_cache.get_stats(),
            "stats": {
                **self.stats,
                "total_requests": total_requests,
                "overall_hit_rate": f"{(self.stats['l1_hits'] + self.stats['l2_hits'] + self.stats['l3_hits']) / total_requests:.2%}" if total_requests > 0 else "0%"
            }
        }


class CacheOptimizer:
    """缓存优化器"""
    
    def __init__(self):
        self.multi_level_cache = MultiLevelCache()
        self.warmup_tasks: List[str] = []
        self.cache_policies: Dict[str, Dict[str, Any]] = {
            "kline": {
                "ttl": 300,
                "level": "l2",
                "preload": True
            },
            "realtime": {
                "ttl": 60,
                "level": "l1",
                "preload": False
            },
            "indicators": {
                "ttl": 3600,
                "level": "l3",
                "preload": True
            }
        }
    
    def cached(self, cache_type: str = "default"):
        """
        缓存装饰器
        
        用法:
            @cache_optimizer.cached("kline")
            async def get_kline(code: str):
                ...
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                cache_key = f"{func.__name__}:{args}:{kwargs}"
                
                cached_result = self.multi_level_cache.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"缓存命中: {cache_key}")
                    return cached_result
                
                result = await func(*args, **kwargs)
                
                policy = self.cache_policies.get(cache_type, {})
                level = policy.get("level", "l2")
                
                self.multi_level_cache.set(cache_key, result, level)
                logger.debug(f"缓存设置: {cache_key}")
                
                return result
            
            return wrapper
        return decorator
    
    async def warmup_cache(self, data_type: str, items: List[str]):
        """
        缓存预热
        
        预加载常用数据到缓存
        """
        logger.info(f"开始缓存预热: {data_type}, 数量: {len(items)}")
        
        warmed = 0
        
        if data_type == "kline":
            from app.services.stock_service import stock_service
            
            for code in items:
                try:
                    await stock_service.get_kline(code)
                    warmed += 1
                    
                    if warmed % 10 == 0:
                        logger.info(f"预热进度: {warmed}/{len(items)}")
                
                except Exception as e:
                    logger.warning(f"预热失败: {code}, {e}")
        
        logger.info(f"缓存预热完成: {data_type}, 成功: {warmed}")
        
        return {
            "data_type": data_type,
            "total": len(items),
            "warmed": warmed
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        return self.multi_level_cache.get_stats()
    
    def clear_cache(self, level: Optional[str] = None):
        """清空缓存"""
        if level == "l1":
            self.multi_level_cache.l1_cache.clear()
        elif level == "l2":
            self.multi_level_cache.l2_cache.clear()
        elif level == "l3":
            self.multi_level_cache.l3_cache.clear()
        else:
            self.multi_level_cache.clear_all()
        
        logger.info(f"缓存已清空: {level or 'all'}")
    
    def get_cache_policies(self) -> Dict[str, Dict[str, Any]]:
        """获取缓存策略"""
        return self.cache_policies
    
    def set_cache_policy(self, cache_type: str, policy: Dict[str, Any]):
        """设置缓存策略"""
        self.cache_policies[cache_type] = policy
        logger.info(f"缓存策略已更新: {cache_type}")


cache_optimizer = CacheOptimizer()

from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Any, Optional
import asyncio
import threading
from loguru import logger

from app.config import settings
from app.storage.classification import UNIFIED_DATA_CONFIGS


class AsyncLRUCache:
    
    def __init__(self, max_size: int = 1000, ttl: int = 300):
        self.max_size = max_size
        self.ttl = ttl
        self._cache: OrderedDict = OrderedDict()
        self._timestamps: dict = {}
        self._lock = asyncio.Lock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0
    
    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            if self._is_expired(key):
                del self._cache[key]
                del self._timestamps[key]
                self._misses += 1
                return None
            
            self._cache.move_to_end(key)
            self._hits += 1
            return self._cache[key]
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        async with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                if len(self._cache) >= self.max_size:
                    oldest_key = next(iter(self._cache))
                    del self._cache[oldest_key]
                    del self._timestamps[oldest_key]
                    self._evictions += 1
            
            self._cache[key] = value
            self._timestamps[key] = {
                "created": datetime.now(),
                "ttl": ttl or self.ttl
            }
    
    async def delete(self, key: str) -> bool:
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                del self._timestamps[key]
                return True
            return False
    
    async def clear(self) -> None:
        async with self._lock:
            self._cache.clear()
            self._timestamps.clear()
            self._hits = 0
            self._misses = 0
            self._evictions = 0
    
    def _is_expired(self, key: str) -> bool:
        if key not in self._timestamps:
            return True
        
        info = self._timestamps[key]
        elapsed = (datetime.now() - info["created"]).total_seconds()
        return elapsed > info["ttl"]
    
    def get_stats(self) -> dict:
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0.0
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "ttl": self.ttl,
            "hits": self._hits,
            "misses": self._misses,
            "evictions": self._evictions,
            "hit_rate": f"{hit_rate:.2f}%"
        }


class CacheManager:
    _instance = None
    _init_lock = threading.Lock()
    
    def __new__(cls):
        with cls._init_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True

        self._caches = {}
        for data_type, config in UNIFIED_DATA_CONFIGS.items():
            self._caches[data_type] = AsyncLRUCache(
                max_size=config.max_cache_size,
                ttl=config.ttl
            )

        logger.info(f"缓存管理器初始化完成（从 UNIFIED_DATA_CONFIGS 加载 {len(self._caches)} 个缓存）")
    
    def get_cache(self, cache_type: str) -> AsyncLRUCache:
        return self._caches.get(cache_type)
    
    async def get(self, cache_type: str, key: str) -> Optional[Any]:
        cache = self.get_cache(cache_type)
        if cache:
            return await cache.get(key)
        return None
    
    async def set(self, cache_type: str, key: str, value: Any, ttl: Optional[int] = None) -> None:
        cache = self.get_cache(cache_type)
        if cache:
            await cache.set(key, value, ttl)
    
    async def delete(self, cache_type: str, key: str) -> bool:
        cache = self.get_cache(cache_type)
        if cache:
            return await cache.delete(key)
        return False
    
    async def clear_cache(self, cache_type: str) -> None:
        cache = self.get_cache(cache_type)
        if cache:
            await cache.clear()
    
    async def clear_all(self) -> None:
        for cache in self._caches.values():
            await cache.clear()
    
    def get_all_stats(self) -> dict:
        return {
            name: cache.get_stats()
            for name, cache in self._caches.items()
        }


cache_manager = CacheManager()

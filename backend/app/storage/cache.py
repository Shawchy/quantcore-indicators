from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Any, Optional
import threading
from loguru import logger

from app.config import settings


class LRUCache:
    def __init__(self, max_size: int = 1000, ttl: int = 300):
        self.max_size = max_size
        self.ttl = ttl
        self._cache: OrderedDict = OrderedDict()
        self._timestamps: dict = {}
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                return None
            
            if self._is_expired(key):
                self._remove(key)
                return None
            
            self._cache.move_to_end(key)
            return self._cache[key]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                if len(self._cache) >= self.max_size:
                    self._pop_oldest()
            
            self._cache[key] = value
            self._timestamps[key] = {
                "created": datetime.now(),
                "ttl": ttl or self.ttl
            }
    
    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                self._remove(key)
                return True
            return False
    
    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()
    
    def _is_expired(self, key: str) -> bool:
        if key not in self._timestamps:
            return True
        
        info = self._timestamps[key]
        elapsed = (datetime.now() - info["created"]).total_seconds()
        return elapsed > info["ttl"]
    
    def _remove(self, key: str) -> None:
        del self._cache[key]
        del self._timestamps[key]
    
    def _pop_oldest(self) -> None:
        if self._cache:
            key = next(iter(self._cache))
            self._remove(key)
    
    def get_stats(self) -> dict:
        with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "ttl": self.ttl
            }


class CacheManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._caches = {
            "realtime": LRUCache(max_size=500, ttl=60),
            "kline": LRUCache(max_size=200, ttl=300),
            "indicators": LRUCache(max_size=200, ttl=300),
            "sector": LRUCache(max_size=100, ttl=300),
            "chip": LRUCache(max_size=200, ttl=600),
            "screener": LRUCache(max_size=50, ttl=120),
            "backtest": LRUCache(max_size=20, ttl=3600),
        }
        logger.info("缓存管理器初始化完成")
    
    def get_cache(self, cache_type: str) -> LRUCache:
        return self._caches.get(cache_type)
    
    def get(self, cache_type: str, key: str) -> Optional[Any]:
        cache = self.get_cache(cache_type)
        if cache:
            return cache.get(key)
        return None
    
    def set(self, cache_type: str, key: str, value: Any, ttl: Optional[int] = None) -> None:
        cache = self.get_cache(cache_type)
        if cache:
            cache.set(key, value, ttl)
    
    def delete(self, cache_type: str, key: str) -> bool:
        cache = self.get_cache(cache_type)
        if cache:
            return cache.delete(key)
        return False
    
    def clear_cache(self, cache_type: str) -> None:
        cache = self.get_cache(cache_type)
        if cache:
            cache.clear()
    
    def clear_all(self) -> None:
        for cache in self._caches.values():
            cache.clear()
    
    def get_all_stats(self) -> dict:
        return {
            name: cache.get_stats()
            for name, cache in self._caches.items()
        }


cache_manager = CacheManager()

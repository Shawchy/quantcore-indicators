"""
API 调用统计和缓存管理器

功能：
1. 统计 API 调用次数、成功率、响应时间
2. 实现数据缓存，减少重复调用
3. 智能缓存过期策略
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from loguru import logger
import hashlib
import json


@dataclass
class APICallStats:
    """API 调用统计信息"""
    api_name: str
    total_calls: int = 0
    success_calls: int = 0
    failed_calls: int = 0
    total_time: float = 0.0  # 总耗时（秒）
    last_call_time: Optional[datetime] = None
    last_error: Optional[str] = None
    
    @property
    def success_rate(self) -> float:
        """计算成功率"""
        if self.total_calls == 0:
            return 0.0
        return self.success_calls / self.total_calls * 100
    
    @property
    def avg_response_time(self) -> float:
        """计算平均响应时间（毫秒）"""
        if self.success_calls == 0:
            return 0.0
        return (self.total_time / self.success_calls) * 1000


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    data: Any
    created_at: datetime
    expires_at: Optional[datetime]
    hit_count: int = 0
    
    def is_expired(self) -> bool:
        """检查缓存是否过期"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def hit(self):
        """增加命中次数"""
        self.hit_count += 1


class APICache:
    """
    API 缓存管理器
    
    功能：
    1. 基于 TTL 的缓存过期
    2. 自动清理过期缓存
    3. 缓存命中率统计
    """
    
    def __init__(self, default_ttl: int = 300, max_size: int = 1000):
        """
        初始化缓存管理器
        
        Args:
            default_ttl: 默认缓存时间（秒），默认 5 分钟
            max_size: 最大缓存条目数
        """
        self._cache: Dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._lock = asyncio.Lock()
        
        # 缓存统计
        self.total_hits = 0
        self.total_misses = 0
        
        logger.info(f"API 缓存管理器初始化完成 (TTL={default_ttl}s, max_size={max_size})")
    
    def _generate_key(self, api_name: str, params: Dict[str, Any]) -> str:
        """生成缓存键"""
        key_str = f"{api_name}:{json.dumps(params, sort_keys=True, default=str)}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    async def get(self, api_name: str, params: Dict[str, Any]) -> Optional[Any]:
        """
        从缓存获取数据
        
        Args:
            api_name: API 名称
            params: API 参数
            
        Returns:
            缓存的数据，如果不存在或已过期则返回 None
        """
        key = self._generate_key(api_name, params)
        
        async with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self.total_misses += 1
                return None
            
            if entry.is_expired():
                # 删除过期缓存
                del self._cache[key]
                self.total_misses += 1
                logger.debug(f"缓存过期：{api_name}")
                return None
            
            # 缓存命中
            entry.hit()
            self.total_hits += 1
            logger.debug(f"缓存命中：{api_name} (命中次数={entry.hit_count})")
            return entry.data
    
    async def set(
        self,
        api_name: str,
        params: Dict[str, Any],
        data: Any,
        ttl: Optional[int] = None
    ) -> None:
        """
        设置缓存
        
        Args:
            api_name: API 名称
            params: API 参数
            data: 要缓存的数据
            ttl: 缓存时间（秒），None 则使用默认值
        """
        key = self._generate_key(api_name, params)
        
        async with self._lock:
            # 检查缓存大小
            if len(self._cache) >= self.max_size:
                # 清理最早过期的缓存
                await self._cleanup_oldest()
            
            expires_at = datetime.now() + timedelta(seconds=ttl or self.default_ttl)
            
            entry = CacheEntry(
                key=key,
                data=data,
                created_at=datetime.now(),
                expires_at=expires_at
            )
            
            self._cache[key] = entry
            logger.debug(f"缓存设置：{api_name} (TTL={ttl or self.default_ttl}s)")
    
    async def _cleanup_oldest(self) -> None:
        """清理最早的缓存（按过期时间）"""
        # 按过期时间排序
        sorted_entries = sorted(
            self._cache.items(),
            key=lambda x: x[1].expires_at or datetime.max
        )
        
        # 删除最老的 10% 缓存
        count_to_delete = max(1, int(len(self._cache) * 0.1))
        for key, _ in sorted_entries[:count_to_delete]:
            del self._cache[key]
        
        logger.debug(f"清理缓存：删除{count_to_delete}条")
    
    async def clear(self, api_name: Optional[str] = None) -> None:
        """
        清除缓存
        
        Args:
            api_name: API 名称，None 则清除所有缓存
        """
        async with self._lock:
            if api_name is None:
                self._cache.clear()
                logger.info("清除所有缓存")
            else:
                # 清除指定 API 的缓存（需要遍历匹配）
                keys_to_delete = []
                for key, entry in self._cache.items():
                    if key.startswith(api_name):
                        keys_to_delete.append(key)
                
                for key in keys_to_delete:
                    del self._cache[key]
                
                logger.info(f"清除 {api_name} 的缓存 ({len(keys_to_delete)}条)")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        hit_rate = 0.0
        if self.total_hits + self.total_misses > 0:
            hit_rate = self.total_hits / (self.total_hits + self.total_misses) * 100
        
        return {
            "total_entries": len(self._cache),
            "max_size": self.max_size,
            "total_hits": self.total_hits,
            "total_misses": self.total_misses,
            "hit_rate": hit_rate,
            "default_ttl": self.default_ttl
        }


class APIStats:
    """
    API 调用统计管理器
    
    功能：
    1. 记录每次 API 调用
    2. 统计成功率、响应时间
    3. 生成统计报告
    """
    
    _instance: Optional['APIStats'] = None
    
    def __new__(cls) -> 'APIStats':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._stats: Dict[str, APICallStats] = {}
        self._lock = asyncio.Lock()
        self._initialized = True
        
        logger.info("API 统计管理器初始化完成")
    
    async def record_call(
        self,
        api_name: str,
        success: bool,
        duration: float,
        error: Optional[str] = None
    ) -> None:
        """
        记录 API 调用
        
        Args:
            api_name: API 名称
            success: 是否成功
            duration: 调用耗时（秒）
            error: 错误信息（失败时）
        """
        async with self._lock:
            if api_name not in self._stats:
                self._stats[api_name] = APICallStats(api_name=api_name)
            
            stats = self._stats[api_name]
            stats.total_calls += 1
            stats.last_call_time = datetime.now()
            
            if success:
                stats.success_calls += 1
                stats.total_time += duration
            else:
                stats.failed_calls += 1
                stats.last_error = error
            
            # 记录日志
            if success:
                logger.debug(f"API 调用成功：{api_name} ({duration*1000:.2f}ms)")
            else:
                logger.warning(f"API 调用失败：{api_name} - {error}")
    
    async def get_stats(self, api_name: Optional[str] = None) -> Dict[str, Any]:
        """
        获取统计信息
        
        Args:
            api_name: API 名称，None 则获取所有 API 的统计
            
        Returns:
            统计信息字典
        """
        async with self._lock:
            if api_name:
                if api_name not in self._stats:
                    return {}
                return self._stats[api_name].__dict__
            else:
                return {
                    name: stats.__dict__
                    for name, stats in self._stats.items()
                }
    
    async def get_report(self) -> str:
        """生成统计报告"""
        async with self._lock:
            if not self._stats:
                return "暂无 API 调用记录"
            
            lines = [
                "=" * 80,
                "API 调用统计报告",
                "=" * 80,
                f"统计时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"API 总数：{len(self._stats)}",
                "-" * 80
            ]
            
            # 按调用次数排序
            sorted_stats = sorted(
                self._stats.values(),
                key=lambda x: x.total_calls,
                reverse=True
            )
            
            for stats in sorted_stats:
                lines.append(
                    f"\n{stats.api_name}:"
                    f"\n  总调用：{stats.total_calls}"
                    f"\n  成功：{stats.success_calls} ({stats.success_rate:.1f}%)"
                    f"\n  失败：{stats.failed_calls}"
                    f"\n  平均响应：{stats.avg_response_time:.2f}ms"
                )
                
                if stats.last_error:
                    lines.append(f"  最后错误：{stats.last_error}")
            
            lines.append("\n" + "=" * 80)
            return "\n".join(lines)


# 创建全局单例
api_cache = APICache(default_ttl=300, max_size=1000)
api_stats = APIStats()


def get_api_cache() -> APICache:
    """获取缓存管理器实例"""
    return api_cache


def get_api_stats() -> APIStats:
    """获取统计管理器实例"""
    return api_stats


# 装饰器：自动缓存和统计
def api_call_cache(ttl: Optional[int] = None):
    """
    装饰器：自动缓存 API 调用结果
    
    Usage:
        @api_call_cache(ttl=600)
        async def get_stock_info(...):
            pass
    """
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            cache = get_api_cache()
            stats = get_api_stats()
            
            # 生成参数
            api_name = func.__name__
            params = {
                "args": args[1:] if args else [],  # 跳过 self
                "kwargs": kwargs
            }
            
            # 尝试从缓存获取
            cached_data = await cache.get(api_name, params)
            if cached_data is not None:
                return cached_data
            
            # 执行 API 调用并计时
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                # 记录成功调用
                await stats.record_call(api_name, True, duration)
                
                # 缓存结果
                if result is not None and result != []:
                    await cache.set(api_name, params, result, ttl)
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                await stats.record_call(api_name, False, duration, str(e))
                raise
        
        return wrapper
    return decorator

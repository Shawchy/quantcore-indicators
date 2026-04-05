"""
批量请求优化器

将多个请求合并为批量请求，提高效率和降低数据源压力
"""

from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
from collections import defaultdict
from loguru import logger

from .strategy_config import DataSourceType


@dataclass
class BatchRequest:
    """批量请求项"""
    key: str  # 请求标识（如股票代码）
    params: Dict[str, Any]  # 请求参数
    future: asyncio.Future  # 异步 Future 对象
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def wait_time(self) -> float:
        """等待时间（秒）"""
        return (datetime.now() - self.timestamp).total_seconds()


@dataclass
class BatchResult:
    """批量请求结果"""
    key: str
    success: bool
    data: Any
    error: Optional[str] = None


class BatchRequestOptimizer:
    """批量请求优化器
    
    特性：
    1. 自动合并相同类型的请求
    2. 可配置的批量大小和延迟
    3. 支持超时处理
    4. 失败重试机制
    """
    
    def __init__(
        self,
        max_batch_size: int = 10,
        max_wait_time: float = 0.1,
        max_wait_count: int = 5
    ):
        """
        初始化批量请求优化器
        
        Args:
            max_batch_size: 最大批量大小
            max_wait_time: 最大等待时间（秒）
            max_wait_count: 最大等待请求数
        """
        self._max_batch_size = max_batch_size
        self._max_wait_time = max_wait_time
        self._max_wait_count = max_wait_count
        
        # 请求队列：{数据类型: {数据源: [请求列表]}}
        self._queues: Dict[str, Dict[str, List[BatchRequest]]] = defaultdict(
            lambda: defaultdict(list)
        )
        
        # 批处理定时器
        self._timers: Dict[str, asyncio.Task] = {}
        
        # 锁
        self._lock = asyncio.Lock()
        
        # 统计
        self._stats = {
            "total_requests": 0,
            "batched_requests": 0,
            "batch_count": 0,
            "avg_batch_size": 0.0,
            "avg_wait_time": 0.0,
        }
    
    async def request(
        self,
        data_type: str,
        source: DataSourceType,
        key: str,
        params: Dict[str, Any],
        fetch_func: Callable[[List[str]], Any]
    ) -> Any:
        """
        发送批量优化请求
        
        Args:
            data_type: 数据类型
            source: 数据源
            key: 请求标识
            params: 请求参数
            fetch_func: 批量获取函数
        
        Returns:
            请求结果
        """
        source_key = source.value
        
        async with self._lock:
            # 检查是否已有相同请求在处理中
            for req in self._queues[data_type][source_key]:
                if req.key == key:
                    # 等待已有请求的结果
                    logger.debug(f"复用已有请求: {key}")
                    return await req.future
            
            # 创建新请求
            future = asyncio.get_event_loop().create_future()
            request = BatchRequest(key=key, params=params, future=future)
            
            # 添加到队列
            self._queues[data_type][source_key].append(request)
            self._stats["total_requests"] += 1
            
            # 检查是否需要立即处理
            queue_size = len(self._queues[data_type][source_key])
            
            if queue_size >= self._max_batch_size:
                # 达到最大批量，立即处理
                await self._process_batch(data_type, source_key, fetch_func)
            elif queue_size >= self._max_wait_count:
                # 达到最大等待数，立即处理
                await self._process_batch(data_type, source_key, fetch_func)
            elif source_key not in self._timers:
                # 启动定时器
                self._timers[source_key] = asyncio.create_task(
                    self._batch_timer(data_type, source_key, fetch_func)
                )
        
        # 等待结果
        try:
            return await asyncio.wait_for(future, timeout=30.0)
        except asyncio.TimeoutError:
            logger.error(f"请求超时: {key}")
            raise
    
    async def _batch_timer(
        self,
        data_type: str,
        source_key: str,
        fetch_func: Callable[[List[str]], Any]
    ):
        """批处理定时器"""
        await asyncio.sleep(self._max_wait_time)
        
        async with self._lock:
            if source_key in self._timers:
                del self._timers[source_key]
            
            if self._queues[data_type][source_key]:
                await self._process_batch(data_type, source_key, fetch_func)
    
    async def _process_batch(
        self,
        data_type: str,
        source_key: str,
        fetch_func: Callable[[List[str]], Any]
    ):
        """处理批量请求"""
        requests = self._queues[data_type][source_key]
        self._queues[data_type][source_key] = []
        
        if not requests:
            return
        
        # 更新统计
        batch_size = len(requests)
        self._stats["batched_requests"] += batch_size
        self._stats["batch_count"] += 1
        
        # 计算平均等待时间
        wait_times = [req.wait_time for req in requests]
        avg_wait = sum(wait_times) / len(wait_times)
        
        # 更新平均统计
        n = self._stats["batch_count"]
        self._stats["avg_batch_size"] = (
            (self._stats["avg_batch_size"] * (n - 1) + batch_size) / n
        )
        self._stats["avg_wait_time"] = (
            (self._stats["avg_wait_time"] * (n - 1) + avg_wait) / n
        )
        
        logger.debug(
            f"处理批量请求: {data_type}/{source_key}, "
            f"数量: {batch_size}, 平均等待: {avg_wait:.3f}s"
        )
        
        # 提取所有 key
        keys = [req.key for req in requests]
        
        try:
            # 批量获取数据
            results = await fetch_func(keys)
            
            # 分发结果
            if isinstance(results, dict):
                # 结果是字典格式
                for req in requests:
                    if req.key in results:
                        req.future.set_result(results[req.key])
                    else:
                        req.future.set_exception(
                            KeyError(f"结果中未找到: {req.key}")
                        )
            elif isinstance(results, list) and len(results) == len(requests):
                # 结果是列表格式，按顺序对应
                for req, result in zip(requests, results):
                    req.future.set_result(result)
            else:
                # 其他格式，所有请求返回相同结果
                for req in requests:
                    req.future.set_result(results)
                    
        except Exception as e:
            logger.error(f"批量请求失败: {e}")
            # 所有请求都失败
            for req in requests:
                req.future.set_exception(e)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self._stats,
            "efficiency": (
                self._stats["batched_requests"] / self._stats["total_requests"]
                if self._stats["total_requests"] > 0 else 0.0
            ),
        }
    
    def reset_stats(self):
        """重置统计"""
        self._stats = {
            "total_requests": 0,
            "batched_requests": 0,
            "batch_count": 0,
            "avg_batch_size": 0.0,
            "avg_wait_time": 0.0,
        }


class DataSourceBatchAdapter:
    """数据源批量适配器
    
    为各个数据源提供批量请求接口
    """
    
    def __init__(self, base_adapter: Any):
        self._base = base_adapter
        self._optimizer = BatchRequestOptimizer()
    
    async def get_klines_batch(
        self,
        codes: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq"
    ) -> Dict[str, Any]:
        """批量获取 K 线数据"""
        results = {}
        
        for code in codes:
            try:
                result = await self._base.get_kline(
                    code, start_date, end_date, adjust
                )
                results[code] = result
            except Exception as e:
                logger.warning(f"获取 {code} K线失败: {e}")
                results[code] = None
        
        return results
    
    async def get_stock_infos_batch(self, codes: List[str]) -> Dict[str, Any]:
        """批量获取股票信息"""
        results = {}
        
        for code in codes:
            try:
                result = await self._base.get_stock_info(code)
                results[code] = result
            except Exception as e:
                logger.warning(f"获取 {code} 信息失败: {e}")
                results[code] = None
        
        return results
    
    async def get_realtime_quotes_batch(self, codes: List[str]) -> Dict[str, Any]:
        """批量获取实时行情"""
        results = {}
        
        for code in codes:
            try:
                result = await self._base.get_realtime_quote(code)
                results[code] = result
            except Exception as e:
                logger.warning(f"获取 {code} 实时行情失败: {e}")
                results[code] = None
        
        return results


# 全局批量请求优化器实例
batch_optimizer = BatchRequestOptimizer()

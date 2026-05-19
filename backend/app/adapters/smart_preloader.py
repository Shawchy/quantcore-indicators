"""
智能预加载器

根据用户行为模式和时间段预加载数据，提升响应速度
"""

from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, time
from collections import defaultdict, deque
import asyncio
from loguru import logger

from .strategy_config import DataSourceType, get_priority_sources


@dataclass
class UserPattern:
    """用户行为模式"""
    user_id: str
    
    # 关注的股票
    watched_stocks: Set[str] = field(default_factory=set)
    
    # 频繁请求的数据类型
    frequent_data_types: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    # 活跃时间段（小时）
    active_hours: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    
    # 最近请求记录
    recent_requests: deque = field(default_factory=lambda: deque(maxlen=100))
    
    # 最后活跃时间
    last_active: Optional[datetime] = None
    
    def record_request(self, data_type: str, code: Optional[str] = None):
        """记录用户请求"""
        now = datetime.now()
        hour = now.hour
        
        self.active_hours[hour] += 1
        self.frequent_data_types[data_type] += 1
        self.recent_requests.append({
            "data_type": data_type,
            "code": code,
            "timestamp": now
        })
        self.last_active = now
        
        if code:
            self.watched_stocks.add(code)
    
    def get_top_stocks(self, n: int = 10) -> List[str]:
        """获取最常关注的股票"""
        # 统计最近请求中的股票频率
        stock_count = defaultdict(int)
        for req in self.recent_requests:
            if req.get("code"):
                stock_count[req["code"]] += 1
        
        # 按频率排序
        sorted_stocks = sorted(stock_count.items(), key=lambda x: x[1], reverse=True)
        return [s[0] for s in sorted_stocks[:n]]
    
    def get_top_data_types(self, n: int = 5) -> List[str]:
        """获取最常请求的数据类型"""
        sorted_types = sorted(
            self.frequent_data_types.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return [t[0] for t in sorted_types[:n]]
    
    def is_active_now(self) -> bool:
        """检查用户当前是否活跃"""
        if not self.last_active:
            return False
        
        # 5分钟内活跃认为是活跃用户
        return (datetime.now() - self.last_active).total_seconds() < 300
    
    def get_preload_candidates(self) -> List[Dict[str, Any]]:
        """获取预加载候选列表"""
        candidates = []
        
        # 获取当前时间
        now = datetime.now()
        current_hour = now.hour
        
        # 检查是否在交易时间
        is_trading_time = self._is_trading_time(current_hour)
        
        # 预加载关注的股票
        top_stocks = self.get_top_stocks(5)
        top_data_types = self.get_top_data_types(3)
        
        for stock in top_stocks:
            for data_type in top_data_types:
                # 交易时间优先加载实时数据
                if is_trading_time and data_type in ["realtime_quote", "tick"]:
                    priority = 1
                else:
                    priority = 2
                
                candidates.append({
                    "code": stock,
                    "data_type": data_type,
                    "priority": priority,
                    "user_id": self.user_id
                })
        
        # 按优先级排序
        candidates.sort(key=lambda x: x["priority"])
        return candidates
    
    def _is_trading_time(self, hour: int) -> bool:
        """检查是否在交易时间"""
        # 简单判断：9:30 - 15:00
        return 9 <= hour <= 15


class SmartPreloader:
    
    CACHE_TTL_SECONDS = 300
    MAX_CACHE_SIZE = 200
    
    def __init__(
        self,
        max_concurrent_preloads: int = 5,
        preload_interval: int = 60
    ):
        self._max_concurrent = max_concurrent_preloads
        self._preload_interval = preload_interval
        
        self._user_patterns: Dict[str, UserPattern] = {}
        self._preload_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._preloaded_cache: Dict[str, Any] = {}
        self._preload_task: Optional[asyncio.Task] = None
        self._semaphore = asyncio.Semaphore(max_concurrent_preloads)
        self._cache_ttl = self.CACHE_TTL_SECONDS
        
        self._stats = {
            "total_preloads": 0,
            "successful_preloads": 0,
            "failed_preloads": 0,
            "cache_hits": 0,
            "cache_evictions": 0,
        }
    
    async def start(self):
        """启动预加载任务"""
        if self._preload_task is None:
            self._preload_task = asyncio.create_task(self._preload_loop())
            logger.info("智能预加载器已启动")
    
    async def stop(self):
        """停止预加载任务"""
        if self._preload_task:
            self._preload_task.cancel()
            try:
                await self._preload_task
            except asyncio.CancelledError:
                pass
            self._preload_task = None
            logger.info("智能预加载器已停止")
    
    async def _preload_loop(self):
        """预加载循环"""
        while True:
            try:
                # 分析所有活跃用户
                await self._analyze_active_users()
                
                # 处理预加载队列
                await self._process_preload_queue()
                
                await asyncio.sleep(self._preload_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"预加载循环错误: {e}")
    
    async def _analyze_active_users(self):
        """分析活跃用户并生成预加载任务"""
        for user_id, pattern in self._user_patterns.items():
            if not pattern.is_active_now():
                continue
            
            # 获取预加载候选
            candidates = pattern.get_preload_candidates()
            
            for candidate in candidates:
                cache_key = f"{candidate['data_type']}:{candidate['code']}"
                
                # 检查是否已缓存
                if cache_key in self._preloaded_cache:
                    continue
                
                # 添加到预加载队列（使用优先级队列，priority 越小优先级越高）
                # 使用元组 (priority, timestamp, candidate) 确保可比较
                await self._preload_queue.put((
                    candidate["priority"],
                    candidate["code"],  # 使用 code 作为第二排序键
                    candidate
                ))
    
    async def _process_preload_queue(self):
        """处理预加载队列"""
        tasks = []
        
        while not self._preload_queue.empty() and len(tasks) < self._max_concurrent:
            try:
                priority, code, candidate = self._preload_queue.get_nowait()
                
                task = asyncio.create_task(
                    self._preload_data(candidate)
                )
                tasks.append(task)
            except asyncio.QueueEmpty:
                break
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _preload_data(self, candidate: Dict[str, Any]):
        """预加载数据"""
        async with self._semaphore:
            data_type = candidate["data_type"]
            code = candidate["code"]
            cache_key = f"{data_type}:{code}"
            
            self._stats["total_preloads"] += 1
            
            try:
                # 这里应该调用实际的数据获取方法
                # 暂时使用模拟数据
                data = await self._fetch_data(data_type, code)
                
                if data:
                    if len(self._preloaded_cache) >= self.MAX_CACHE_SIZE:
                        oldest_key = min(
                            self._preloaded_cache,
                            key=lambda k: self._preloaded_cache[k]["timestamp"]
                        )
                        del self._preloaded_cache[oldest_key]
                        self._stats["cache_evictions"] += 1
                    
                    self._preloaded_cache[cache_key] = {
                        "data": data,
                        "timestamp": datetime.now(),
                        "candidate": candidate
                    }
                    self._stats["successful_preloads"] += 1
                    logger.debug(f"预加载成功: {cache_key}")
                else:
                    self._stats["failed_preloads"] += 1
                    
            except Exception as e:
                self._stats["failed_preloads"] += 1
                logger.warning(f"预加载失败 {cache_key}: {e}")
    
    async def _fetch_data(self, data_type: str, code: str) -> Any:
        try:
            from app.adapters import data_source_manager
            
            method_map = {
                "kline": "get_kline",
                "realtime_quote": "get_realtime_quote",
                "stock_info": "get_stock_info",
                "indicators": "get_indicators",
                "chip": "get_chip_data",
            }
            
            method_name = method_map.get(data_type)
            if not method_name:
                return None
            
            if data_type == "kline":
                return await data_source_manager.get_kline(code)
            elif data_type == "realtime_quote":
                return await data_source_manager.get_realtime_quote(code)
            elif data_type == "stock_info":
                return await data_source_manager.get_stock_info(code)
            elif data_type == "indicators":
                return await data_source_manager.get_indicators(code)
            elif data_type == "chip":
                return await data_source_manager.get_chip_data(code)
            
            return None
        except Exception as e:
            logger.debug(f"预加载获取数据失败 {data_type}:{code}: {e}")
            return None
    
    def record_user_request(
        self,
        user_id: str,
        data_type: str,
        code: Optional[str] = None
    ):
        """
        记录用户请求
        
        Args:
            user_id: 用户ID
            data_type: 数据类型
            code: 股票代码（可选）
        """
        if user_id not in self._user_patterns:
            self._user_patterns[user_id] = UserPattern(user_id)
        
        self._user_patterns[user_id].record_request(data_type, code)
    
    def get_preloaded_data(self, data_type: str, code: str) -> Optional[Any]:
        cache_key = f"{data_type}:{code}"
        
        if cache_key in self._preloaded_cache:
            entry = self._preloaded_cache[cache_key]
            age = (datetime.now() - entry["timestamp"]).total_seconds()
            
            if age > self._cache_ttl:
                del self._preloaded_cache[cache_key]
                self._stats["cache_evictions"] += 1
                return None
            
            self._stats["cache_hits"] += 1
            return entry["data"]
        
        return None
    
    def clear_cache(self, older_than: Optional[int] = None):
        """
        清理缓存
        
        Args:
            older_than: 清理超过多少秒的缓存（None 表示清理所有）
        """
        if older_than is None:
            self._preloaded_cache.clear()
        else:
            now = datetime.now()
            keys_to_remove = []
            
            for key, entry in self._preloaded_cache.items():
                age = (now - entry["timestamp"]).total_seconds()
                if age > older_than:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self._preloaded_cache[key]
            
            logger.info(f"清理了 {len(keys_to_remove)} 个过期缓存项")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self._stats,
            "cache_size": len(self._preloaded_cache),
            "active_users": len([u for u in self._user_patterns.values() if u.is_active_now()]),
            "total_users": len(self._user_patterns),
        }
    
    def get_user_pattern(self, user_id: str) -> Optional[UserPattern]:
        """获取用户行为模式"""
        return self._user_patterns.get(user_id)


# 全局智能预加载器实例
smart_preloader = SmartPreloader()

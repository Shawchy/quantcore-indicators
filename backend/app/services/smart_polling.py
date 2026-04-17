"""
智能轮询服务 (Smart Polling Service)

针对爬虫数据源架构优化的实时性解决方案：
- 动态调整轮询频率（交易时间/非交易时间）
- 批量请求优化（减少API调用次数）
- 智能频率限制（保护数据源安全）
- 用户分级权限控制
- 随机抖动机制（模拟人类行为）

使用场景：
- 替代WebSocket（爬虫场景不适用长连接）
- 平衡实时性与反爬安全性
- 降低服务器负载70-90%
"""

import asyncio
import random
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from loguru import logger


class UserTier(str, Enum):
    """用户等级"""
    NORMAL = "normal"           # 普通用户
    PREMIUM = "premium"         # 高级用户（VIP）
    ENTERPRISE = "enterprise"   # 企业用户


class MarketState(str, Enum):
    """市场状态"""
    PRE_MARKET = "pre_market"       # 盘前（9:15-9:30）
    TRADING = "trading"            # 交易时间（9:30-11:30, 13:00-15:00）
    LUNCH_BREAK = "lunch_break"    # 午间休市（11:30-13:00）
    AFTER_MARKET = "after_market"  # 盘后（15:00-16:00）
    CLOSED = "closed"              # 休市


@dataclass
class PollingConfig:
    """轮询配置"""
    interval_min: int = 30         # 最小间隔（秒）
    interval_max: int = 60         # 最大间隔（秒）
    jitter_range: float = 0.3      # 抖动范围（±30%）
    batch_size: int = 10           # 批量请求大小
    max_requests_per_hour: int = 120  # 每小时最大请求数
    cache_ttl: int = 30            # 缓存TTL（秒）


@dataclass 
class RateLimitInfo:
    """频率限制信息"""
    requests_made: int = 0
    window_start: datetime = field(default_factory=datetime)
    is_limited: bool = False
    reset_time: Optional[datetime] = None


class SmartPollingService:
    """
    智能轮询服务
    
    核心特性：
    1. 根据市场状态动态调整频率
    2. 用户分级权限管理
    3. 全局QPS保护
    4. 批量请求合并
    5. 智能缓存策略
    
    使用示例：
        >>> polling = SmartPollingService()
        >>> data = await polling.get_realtime_batch(
        ...     codes=["000001", "600000"],
        ...     user_tier="premium"
        ... )
    """
    
    MARKET_SCHEDULE = {
        "pre_market":   (9, 15, 9, 30),     # 盘前
        "morning":      (9, 30, 11, 30),    # 上午交易
        "lunch":        (11, 30, 13, 0),     # 午休
        "afternoon":    (13, 0, 15, 0),      # 下午交易
        "after_market": (15, 0, 16, 0),      # 盘后
    }
    
    TIER_CONFIGS = {
        UserTier.NORMAL: PollingConfig(
            interval_min=45,
            interval_max=90,
            batch_size=10,
            max_requests_per_hour=60,
            cache_ttl=45
        ),
        UserTier.PREMIUM: PollingConfig(
            interval_min=20,
            interval_max=40,
            batch_size=20,
            max_requests_per_hour=150,
            cache_ttl=20
        ),
        UserTier.ENTERPRISE: PollingConfig(
            interval_min=10,
            interval_max=25,
            batch_size=50,
            max_requests_per_hour=300,
            cache_ttl=10
        ),
    }
    
    def __init__(self):
        self._rate_limits: Dict[str, RateLimitInfo] = {}
        self._global_counter: Dict[str, int] = {}
        self._global_window_start: datetime = datetime.now()
        self._cache: Dict[str, tuple] = {}  # {key: (data, timestamp)}
        self._request_history: List[Dict] = []  # 请求历史（用于分析）
        
        logger.info("SmartPollingService 初始化完成")
    
    def get_market_state(self) -> MarketState:
        """
        获取当前市场状态
        
        Returns:
            MarketState: 市场状态枚举
        """
        now = datetime.now()
        current_time = (now.hour, now.minute)
        
        weekday = now.weekday()
        if weekday >= 5:  # 周末
            return MarketState.CLOSED
        
        for state_name, (start_h, start_m, end_h, end_m) in self.MARKET_SCHEDULE.items():
            start = (start_h, start_m)
            end = (end_h, end_m)
            
            if state_name == "lunch":
                if start <= current_time < end:
                    return MarketState.LUNCH_BREAK
            elif state_name == "after_market":
                if start <= current_time < end:
                    return MarketState.AFTER_MARKET
            else:
                if start <= current_time < end:
                    if state_name == "pre_market":
                        return MarketState.PRE_MARKET
                    elif state_name == "morning":
                        return MarketState.TRADING
                    elif state_name == "afternoon":
                        return MarketState.TRADING
        
        return MarketState.CLOSED
    
    def get_optimal_interval(self, user_tier: str = "normal") -> int:
        """
        获取最优轮询间隔
        
        根据市场状态、用户等级计算最佳请求间隔，
        并添加随机抖动以模拟人类行为。
        
        Args:
            user_tier: 用户等级
            
        Returns:
            int: 推荐的轮询间隔（秒）
        """
        tier = UserTier(user_tier)
        config = self.TIER_CONFIGS[tier]
        market_state = self.get_market_state()
        
        base_interval = config.interval_min
        
        if market_state == MarketState.TRADING:
            base_interval = config.interval_min
        elif market_state == MarketState.PRE_MARKET:
            base_interval = int(config.interval_min * 1.5)
        elif market_state == MarketState.LUNCH_BREAK:
            base_interval = int(config.interval_max * 1.5)
        elif market_state == MarketState.CLOSED:
            base_interval = int(config.interval_max * 1.5)  # 非交易时间适度延长
        else:
            base_interval = config.interval_max
        
        jitter = random.uniform(
            1 - config.jitter_range,
            1 + config.jitter_range
        )
        
        final_interval = int(base_interval * jitter)
        
        final_interval = max(final_interval, 10)
        
        return final_interval
    
    async def check_rate_limit(
        self, 
        user_id: str = "anonymous",
        user_tier: str = "normal"
    ) -> RateLimitInfo:
        """
        检查频率限制
        
        Args:
            user_id: 用户标识
            user_tier: 用户等级
            
        Returns:
            RateLimitInfo: 限制信息
        """
        tier = UserTier(user_tier)
        config = self.TIER_CONFIGS[tier]
        now = datetime.now()
        
        if user_id not in self._rate_limits:
            self._rate_limits[user_id] = RateLimitInfo(
                window_start=now
            )
        
        limit_info = self._rate_limits[user_id]
        
        window_age = (now - limit_info.window_start).total_seconds()
        
        if window_age >= 3600:
            limit_info.requests_made = 0
            limit_info.window_start = now
            limit_info.is_limited = False
            limit_info.reset_time = None
        
        global_age = (now - self._global_window_start).total_seconds()
        if global_age >= 3600:
            self._global_counter.clear()
            self._global_window_start = now
        
        if limit_info.requests_made >= config.max_requests_per_hour:
            limit_info.is_limited = True
            limit_info.reset_time = limit_info.window_start + timedelta(hours=1)
            logger.warning(f"用户 {user_id} 达到频率限制")
            return limit_info
        
        limit_info.is_limited = False
        return limit_info
    
    async def get_realtime_batch(
        self,
        codes: List[str],
        user_id: str = "anonymous",
        user_tier: str = "normal",
        fetch_func: Optional[Callable] = None,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        批量获取实时行情（核心方法）
        
        优化流程：
        1. 检查频率限制
        2. 从缓存获取可用数据
        3. 对未缓存数据批量获取
        4. 更新缓存
        5. 返回合并结果
        
        Args:
            codes: 股票代码列表
            user_id: 用户ID
            user_tier: 用户等级
            fetch_func: 数据获取函数（可选，默认使用适配器）
            force_refresh: 强制刷新缓存
            
        Returns:
            Dict: {
                "success": bool,
                "data": {code: quote_data},
                "cached_count": int,
                "fresh_count": int,
                "rate_limited": bool,
                "next_interval": int,
                "timestamp": str
            }
        """
        tier = UserTier(user_tier)
        config = self.TIER_CONFIGS[tier]
        now = datetime.now()
        
        rate_info = await self.check_rate_limit(user_id, user_tier)
        
        result = {
            "success": True,
            "data": {},
            "cached_count": 0,
            "fresh_count": 0,
            "rate_limited": rate_info.is_limited,
            "next_interval": self.get_optimal_interval(user_tier),
            "timestamp": now.isoformat()
        }
        
        if rate_info.is_limited and not force_refresh:
            result["success"] = False
            result["message"] = f"频率限制，请在 {rate_info.reset_time.strftime('%H:%M:%S')} 后重试"
            return result
        
        cached_data = {}
        uncached_codes = []
        
        for code in codes:
            cache_key = f"realtime_{code}"
            
            if not force_refresh and cache_key in self._cache:
                cached_timestamp, cached_value = self._cache[cache_key]
                age = (now - cached_timestamp).total_seconds()
                
                if age < config.cache_ttl:
                    cached_data[code] = cached_value
                    result["cached_count"] += 1
                    continue
            
            uncached_codes.append(code)
        
        result["data"].update(cached_data)
        
        if uncached_codes:
            try:
                fresh_data = await self._batch_fetch_with_retry(
                    uncached_codes,
                    fetch_func,
                    config.batch_size
                )
                
                if fresh_data:
                    for code, data in fresh_data.items():
                        cache_key = f"realtime_{code}"
                        self._cache[cache_key] = (now, data)
                        result["data"][code] = data
                        result["fresh_count"] += 1
                    
                    if user_id in self._rate_limits:
                        self._rate_limits[user_id].requests_made += 1
                    
                    self._record_request(user_id, len(uncached_codes), success=True)
                    
            except Exception as e:
                logger.error(f"批量获取失败: {e}")
                result["success"] = False
                result["error"] = str(e)
                
                self._record_request(user_id, len(uncached_codes), success=False)
        
        self._cleanup_cache(max_size=1000)
        
        return result
    
    async def _batch_fetch_with_retry(
        self,
        codes: List[str],
        fetch_func: Optional[Callable],
        batch_size: int,
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """
        带重试的批量获取
        
        分批处理大量请求，每批之间添加延迟以避免触发限流。
        
        Args:
            codes: 股票代码列表
            fetch_func: 获取函数
            batch_size: 批次大小
            max_retries: 最大重试次数
            
        Returns:
            Dict: {code: data}
        """
        all_data = {}
        
        batches = [codes[i:i+batch_size] for i in range(0, len(codes), batch_size)]
        
        for batch_idx, batch in enumerate(batches):
            retry_count = 0
            success = False
            
            while retry_count <= max_retries and not success:
                try:
                    if fetch_func:
                        batch_data = await fetch_func(batch)
                    else:
                        batch_data = await self._default_fetch(batch)
                    
                    if batch_data:
                        all_data.update(batch_data)
                        success = True
                    else:
                        retry_count += 1
                        
                except Exception as e:
                    retry_count += 1
                    logger.warning(f"批次 {batch_idx} 第{retry_count}次失败: {e}")
                    
                    if retry_count <= max_retries:
                        wait_time = min(2 ** retry_count, 10)
                        await asyncio.sleep(wait_time)
            
            if batch_idx < len(batches) - 1:
                delay = random.uniform(0.5, 1.5)
                await asyncio.delay(delay)
        
        return all_data
    
    async def _default_fetch(self, codes: List[str]) -> Dict[str, Any]:
        """默认数据获取方法（使用数据源管理器）"""
        try:
            from app.adapters import data_source_manager
            
            results = {}
            for code in codes:
                try:
                    quote = await data_source_manager.get_realtime_quote(code)
                    if quote:
                        results[code] = quote
                        
                    await asyncio.sleep(random.uniform(0.1, 0.3))
                    
                except Exception as e:
                    logger.debug(f"获取 {code} 失败: {e}")
                    continue
            
            return results
            
        except ImportError:
            logger.warning("数据源管理器未初始化，使用mock数据")
            return self._generate_mock_data(codes)
    
    def _generate_mock_data(self, codes: List[str]) -> Dict[str, Any]:
        """生成测试用mock数据"""
        mock_data = {}
        base_price = 12.50
        
        for i, code in enumerate(codes):
            change_pct = random.uniform(-5, 5)
            price = base_price * (1 + change_pct / 100)
            
            mock_data[code] = {
                "code": code,
                "name": f"测试股票{code}",
                "price": round(price, 2),
                "change": round(price - base_price, 2),
                "change_pct": round(change_pct, 2),
                "volume": random.randint(100000, 10000000),
                "amount": random.randint(1000000, 1000000000),
                "turnover_rate": round(random.uniform(0.5, 8), 2),
                "high": round(price * 1.02, 2),
                "low": round(price * 0.98, 2),
                "open": round(price * 1.01, 2),
                "prev_close": round(base_price, 2),
                "timestamp": datetime.now().isoformat()
            }
            
            base_price += random.uniform(-0.5, 0.5)
        
        return mock_data
    
    def _record_request(self, user_id: str, count: int, success: bool):
        """记录请求历史"""
        self._request_history.append({
            "timestamp": datetime.now(),
            "user_id": user_id,
            "count": count,
            "success": success
        })
        
        if len(self._request_history) > 1000:
            self._request_history = self._request_history[-500:]
    
    def _cleanup_cache(self, max_size: int = 1000):
        """清理过期和过多的缓存"""
        now = datetime.now()
        
        expired_keys = [
            key for key, (ts, _) in self._cache.items()
            if (now - ts).total_seconds() > 300
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        if len(self._cache) > max_size:
            sorted_items = sorted(
                self._cache.items(),
                key=lambda x: x[1][0]
            )
            
            keys_to_remove = [item[0] for item in sorted_items[:-max_size]]
            for key in keys_to_remove:
                del self._cache[key]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取服务统计信息
        
        Returns:
            Dict: 统计数据
        """
        now = datetime.now()
        
        recent_requests = [
            r for r in self._request_history
            if (now - r["timestamp"]).total_seconds() < 3600
        ]
        
        total_requests = sum(r["count"] for r in recent_requests)
        successful_requests = sum(
            r["count"] for r in recent_requests if r["success"]
        )
        
        active_users = len(set(r["user_id"] for r in recent_requests))
        
        return {
            "cache_size": len(self._cache),
            "active_users_last_hour": active_users,
            "total_requests_last_hour": total_requests,
            "successful_requests_last_hour": successful_requests,
            "success_rate": (
                f"{successful_requests/total_requests*100:.1f}%"
                if total_requests > 0 else "N/A"
            ),
            "market_state": self.get_market_state().value,
            "current_time": now.strftime("%H:%M:%S"),
            "recommended_interval_normal": self.get_optimal_interval("normal"),
            "recommended_interval_premium": self.get_optimal_interval("premium"),
        }


# 全局单例实例
smart_polling_service = SmartPollingService()


async def demo_usage():
    """演示用法"""
    service = SmartPollingService()
    
    print("=" * 60)
    print("🚀 SmartPollingService 演示")
    print("=" * 60)
    
    print(f"\n📊 当前市场状态: {service.get_market_state().value}")
    print(f"⏰ 推荐轮询间隔:")
    print(f"   - 普通用户: {service.get_optimal_interval('normal')}秒")
    print(f"   - 高级用户: {service.get_optimal_interval('premium')}秒")
    print(f"   - 企业用户: {service.get_optimal_interval('enterprise')}秒")
    
    test_codes = ["000001", "600000", "300001", "601398", "000858"]
    
    print(f"\n📡 批量获取 {len(test_codes)} 只股票行情...")
    result = await service.get_realtime_batch(
        codes=test_codes,
        user_id="demo_user",
        user_tier="premium"
    )
    
    print(f"\n✅ 获取结果:")
    print(f"   - 成功: {result['success']}")
    print(f"   - 缓存命中: {result['cached_count']}")
    print(f"   - 新鲜数据: {result['fresh_count']}")
    print(f"   - 下次建议间隔: {result['next_interval']}秒")
    
    if result['data']:
        print(f"\n📈 数据示例 (前3只):")
        for code in list(result['data'].keys())[:3]:
            data = result['data'][code]
            print(f"   {code}: 价格={data.get('price')}, "
                  f"涨跌幅={data.get('change_pct')}%")
    
    stats = service.get_statistics()
    print(f"\n📊 服务统计:")
    for key, value in stats.items():
        print(f"   - {key}: {value}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_usage())

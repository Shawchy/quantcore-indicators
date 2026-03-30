"""
智能数据加载器

基于统一存储层，提供智能的数据加载策略：
1. 优先从 L1 缓存获取
2. 缓存未命中则从 L2 数据库获取
3. 数据库未命中则从 API 获取并回填
4. 自动预热常用数据
5. 智能预测和定时预热
"""
import asyncio
from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict
from loguru import logger

from app.storage.unified_storage import storage_manager, DataCategory
from app.adapters.factory import data_source_manager
from app.services.local_database import local_db_service


class SmartDataLoader:
    """智能数据加载器"""
    
    # 缓存命中率告警阈值
    HIT_RATE_WARNING_THRESHOLD = 0.3  # 30%
    HIT_RATE_CRITICAL_THRESHOLD = 0.1  # 10%
    
    def __init__(self):
        self._storage = storage_manager
        self._warmup_done = False
        
        # 访问频率统计（用于智能预热）
        self._access_frequency: Dict[str, int] = defaultdict(int)
        self._last_access_time: Dict[str, datetime] = {}
        self._access_lock = asyncio.Lock()
        
        # 告警统计
        self._last_warning_time: Optional[datetime] = None
        self._warning_cooldown = timedelta(minutes=5)  # 告警冷却时间
    
    async def get_kline(
        self,
        code: str,
        period: str = "daily",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        use_cache: bool = True
    ) -> Optional[List[Any]]:
        """
        智能获取 K 线数据
        
        Args:
            code: 股票代码
            period: K 线周期（daily/weekly/monthly）
            start_date: 开始日期
            end_date: 结束日期
            use_cache: 是否使用缓存
            
        Returns:
            K 线数据列表
        """
        storage = self._storage.get_kline_storage(period)
        
        # 尝试从存储层获取
        if use_cache:
            data = await storage.get(
                code,
                start_date=start_date,
                end_date=end_date
            )
            if data:
                # 记录访问频率
                await self._record_access(code)
                return data
        
        # 未命中则从 API 获取
        logger.debug(f"从 API 获取 K 线数据：{code} {period}")
        kline_data = await data_source_manager.get_kline(
            code=code,
            start_date=start_date,
            end_date=end_date
        )
        
        if kline_data:
            # 保存到存储层
            await storage.set(code, kline_data)
            logger.info(f"K 线数据已缓存：{code} {len(kline_data)}条")
            # 记录访问频率
            await self._record_access(code)
        
        return kline_data
    
    async def get_quote(
        self,
        code: str,
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        智能获取实时行情
        
        Args:
            code: 股票代码
            use_cache: 是否使用缓存
            
        Returns:
            行情数据
        """
        storage = self._storage.get_quote_storage()
        
        # 尝试从存储层获取（缓存 30 秒）
        if use_cache:
            data = await storage.get(code)
            if data:
                # 记录访问频率
                await self._record_access(code)
                # 数据库返回的是 StockQuote 对象，需要转换为字典
                if hasattr(data, '__table__'):  # SQLAlchemy 模型
                    return {
                        "code": data.code,
                        "name": data.name,
                        "price": data.price,
                        "change": data.change,
                        "change_pct": data.change_pct,
                        "volume": data.volume,
                        "amount": data.amount,
                        "high": data.high,
                        "low": data.low,
                        "open": data.open,
                        "prev_close": data.prev_close,
                    }
                # 缓存中可能是列表格式（见 set 方法）
                elif isinstance(data, list) and len(data) > 0:
                    return data[0] if isinstance(data[0], dict) else data
                # 直接是字典
                elif isinstance(data, dict):
                    return data
                return data
        
        # 未命中则从 API 获取
        logger.debug(f"从 API 获取实时行情：{code}")
        quote_data = await data_source_manager.get_realtime_quote(code)
        
        if quote_data:
            # 保存到存储层（自动同步到数据库）
            await storage.set(code, [quote_data])
            # 记录访问频率
            await self._record_access(code)
        
        return quote_data
    
    async def _record_access(self, code: str):
        """记录数据访问（用于智能预热）"""
        async with self._access_lock:
            self._access_frequency[code] += 1
            self._last_access_time[code] = datetime.now()
    
    async def _get_hot_codes(self, limit: int = 50) -> List[str]:
        """获取热门股票代码（基于访问频率）"""
        async with self._access_lock:
            # 按访问频率排序
            sorted_codes = sorted(
                self._access_frequency.items(),
                key=lambda x: x[1],
                reverse=True
            )
            return [code for code, _ in sorted_codes[:limit]]
    
    async def _check_hit_rate_and_warn(self):
        """检查缓存命中率并告警"""
        stats = self.get_storage_stats()
        
        # 计算总体命中率
        total_hits = 0
        total_misses = 0
        for category_stats in stats.values():
            if isinstance(category_stats, dict):
                total_hits += category_stats.get('l1_hits', 0)
                total_hits += category_stats.get('l2_hits', 0)
                total_hits += category_stats.get('l3_hits', 0)
                total_misses += category_stats.get('misses', 0)
        
        total_requests = total_hits + total_misses
        if total_requests == 0:
            return
        
        hit_rate = total_hits / total_requests
        
        # 检查是否需要告警
        now = datetime.now()
        if self._last_warning_time and (now - self._last_warning_time) < self._warning_cooldown:
            return  # 冷却期内不重复告警
        
        # 根据命中率级别告警
        if hit_rate < self.HIT_RATE_CRITICAL_THRESHOLD:
            logger.error(f"⚠️ 缓存命中率严重偏低：{hit_rate:.2%} (阈值：{self.HIT_RATE_CRITICAL_THRESHOLD:.2%})")
            self._last_warning_time = now
        elif hit_rate < self.HIT_RATE_WARNING_THRESHOLD:
            logger.warning(f"⚠️ 缓存命中率偏低：{hit_rate:.2%} (阈值：{self.HIT_RATE_WARNING_THRESHOLD:.2%})")
            self._last_warning_time = now
    
    async def get_fund_nav(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        use_cache: bool = True
    ) -> Optional[List[Any]]:
        """
        智能获取基金净值
        
        Args:
            code: 基金代码
            start_date: 开始日期
            end_date: 结束日期
            use_cache: 是否使用缓存
            
        Returns:
            基金净值数据列表
        """
        storage = self._storage.get_fund_storage()
        
        # 尝试从存储层获取
        if use_cache:
            data = await storage.get(
                code,
                start_date=start_date,
                end_date=end_date
            )
            if data:
                return data
        
        # 未命中则从 API 获取
        logger.debug(f"从 API 获取基金净值：{code}")
        # TODO: 实现基金净值获取
        # fund_nav = await data_source_manager.get_fund_nav(code, start_date, end_date)
        
        return None
    
    async def warmup_cache(self, stock_codes: List[str] = None, use_smart_warmup: bool = True):
        """
        预热缓存
        
        Args:
            stock_codes: 要预热的股票代码列表
            use_smart_warmup: 是否使用智能预热（基于访问频率）
        """
        if self._warmup_done:
            logger.debug("缓存已预热过")
            # 即使已预热，也检查命中率
            await self._check_hit_rate_and_warn()
            return
        
        logger.info("开始预热缓存...")
        
        # 智能预热：优先预热热门股票
        if use_smart_warmup:
            hot_codes = await self._get_hot_codes(limit=50)
            if hot_codes:
                stock_codes = hot_codes
                logger.info(f"使用智能预热：{len(hot_codes)}只热门股票")
        
        # 默认预热热门股票
        if not stock_codes:
            stock_codes = [
                "000001", "000002", "000063", "000100", "000333",
                "000538", "000568", "000651", "000725", "000858",
                "300059", "300750", "600000", "600016", "600028",
                "600030", "600031", "600036", "600048", "600050",
                "600104", "600276", "600309", "600519", "600585",
                "600690", "600745", "600809", "600887", "601012",
                "601088", "601166", "601211", "601288", "601318",
                "601398", "601601", "601628", "601633", "601668",
                "601688", "601766", "601816", "601857", "601888",
                "601899", "601919", "601988", "601995", "603259"
            ]
        
        # 预热行情数据
        quote_storage = self._storage.get_quote_storage()
        success_count = 0
        for code in stock_codes[:50]:  # 限制数量
            try:
                quote = await data_source_manager.get_realtime_quote(code)
                if quote:
                    await quote_storage.set(code, [quote], sync_to_lower=False)
                    success_count += 1
            except Exception as e:
                logger.debug(f"预热行情失败 {code}: {e}")
        
        logger.info(f"行情数据预热完成：{success_count}/{len(stock_codes[:50])}")
        
        # 预热最近 30 天的 K 线
        kline_storage = self._storage.get_kline_storage("daily")
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
        
        kline_success = 0
        for code in stock_codes[:20]:  # 限制数量
            try:
                kline = await data_source_manager.get_kline(
                    code=code,
                    start_date=start_date,
                    end_date=end_date
                )
                if kline:
                    await kline_storage.set(code, kline, sync_to_lower=False)
                    kline_success += 1
            except Exception as e:
                logger.debug(f"预热 K 线失败 {code}: {e}")
        
        logger.info(f"K 线数据预热完成：{kline_success}/{len(stock_codes[:20])}")
        
        self._warmup_done = True
        logger.info(f"缓存预热完成：{len(stock_codes)}只股票")
        
        # 预热后检查命中率
        await self._check_hit_rate_and_warn()
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储器统计信息"""
        return self._storage.get_all_stats()
    
    async def get_health_report(self) -> Dict[str, Any]:
        """
        获取健康报告
        
        Returns:
            包含命中率、告警状态等信息的报告
        """
        stats = self.get_storage_stats()
        
        # 计算总体命中率
        total_hits = 0
        total_misses = 0
        for category_stats in stats.values():
            if isinstance(category_stats, dict):
                total_hits += category_stats.get('l1_hits', 0)
                total_hits += category_stats.get('l2_hits', 0)
                total_hits += category_stats.get('l3_hits', 0)
                total_misses += category_stats.get('misses', 0)
        
        total_requests = total_hits + total_misses
        hit_rate = total_hits / total_requests if total_requests > 0 else 0
        
        # 确定健康状态
        if hit_rate >= 0.7:
            health_status = "healthy"
        elif hit_rate >= 0.3:
            health_status = "warning"
        else:
            health_status = "critical"
        
        return {
            "health_status": health_status,
            "hit_rate": hit_rate,
            "total_requests": total_requests,
            "total_hits": total_hits,
            "total_misses": total_misses,
            "l1_hits": total_hits,  # 简化
            "cache_warmed": self._warmup_done,
            "timestamp": datetime.now().isoformat()
        }
    
    async def check_and_report(self) -> Dict[str, Any]:
        """检查缓存状态并生成报告（包含告警）"""
        report = await self.get_health_report()
        
        # 根据健康状态生成告警
        if report["health_status"] == "critical":
            logger.error(
                f"🚨 缓存健康状态严重：命中率 {report['hit_rate']:.2%}, "
                f"总请求 {report['total_requests']}, 命中 {report['total_hits']}, "
                f"未命中 {report['total_misses']}"
            )
        elif report["health_status"] == "warning":
            logger.warning(
                f"⚠️ 缓存健康状态偏低：命中率 {report['hit_rate']:.2%}"
            )
        else:
            logger.info(
                f"✅ 缓存健康状态良好：命中率 {report['hit_rate']:.2%}"
            )
        
        return report
    
    async def cleanup_old_data(self, days: int = 90):
        """
        清理过期数据
        
        Args:
            days: 保留最近 N 天的数据
        """
        await local_db_service.cleanup_old_data(days)


# 全局实例
smart_loader = SmartDataLoader()

from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio
import pandas as pd
from loguru import logger
from sqlalchemy import select

from app.adapters import data_source_manager, KLineData
from app.services.data_processor import DataProcessor
from app.services.indicators_manager import IndicatorsManager, get_indicators_manager
from app.storage import (
    StockInfo, KLine, TechnicalIndicatorDB, RealtimeQuote,
    get_session, cache_manager, parquet_store
)
from app.core.exceptions import DataNotFoundException, DataSourceException
from app.services.data_persistence import data_persistence
from app.services.data_loader import data_loader, LoadPriority, LoadProgress


class StockService:
    def __init__(self, prefer_talib: bool = False):
        """
        初始化股票服务
        
        Args:
            prefer_talib: 是否优先使用 TA-Lib（如果可用）
        """
        self.processor = DataProcessor()
        # 使用现代化的指标管理器，支持 pandas-ta 和 TA-Lib 双库
        self.indicator_manager = get_indicators_manager(prefer_talib=prefer_talib)
        logger.info(f"StockService 初始化完成，指标库：{'TA-Lib' if self.indicator_manager.prefer_talib else 'pandas-ta'}")
    
    async def get_stock_basic(self, code: str) -> Dict[str, Any]:
        """
        获取股票基本信息（优先从数据库/缓存获取）
        
        优先级：
        1. 内存缓存（最快）
        2. 数据库（本地存储）
        3. 数据源（最后选择，受频率限制）
        """
        # L1: 内存缓存
        cache_key = f"stock_basic_{code}"
        cached = await cache_manager.get("kline", cache_key)
        if cached:
            logger.debug(f"从缓存获取股票信息：{code}")
            return cached
        
        # L2: 数据库
        try:
            async with get_session() as session:
                result = await session.execute(
                    select(StockInfo).where(StockInfo.code == code)
                )
                stock = result.scalar_one_or_none()
                
                if stock:
                    data = {
                        "code": stock.code,
                        "name": stock.name,
                        "market": stock.market,
                        "industry": stock.industry,
                        "sector": stock.sector,
                        "area": stock.area,
                        "list_date": stock.list_date,
                        "total_shares": stock.total_shares,
                        "float_shares": stock.float_shares
                    }
                    # 更新缓存
                    await cache_manager.set("kline", cache_key, data, ttl=3600)  # 1 小时
                    logger.debug(f"从数据库获取股票信息：{code}")
                    return data
        except Exception as e:
            logger.warning(f"从数据库读取股票信息失败 {code}: {e}")
        
        # L3: 数据源（最后选择）
        try:
            stock_info = await data_source_manager.get_stock_info(code)
            if stock_info:
                data = {
                    "code": stock_info.code,
                    "name": stock_info.name,
                    "market": stock_info.market,
                    "industry": stock_info.industry,
                    "sector": stock_info.sector,
                    "area": stock_info.area,
                    "list_date": stock_info.list_date,
                    "total_shares": stock_info.total_shares,
                    "float_shares": stock_info.float_shares
                }
                # 异步保存到数据库和缓存
                asyncio.create_task(self._save_stock_info_to_db(code, data))
                logger.debug(f"从数据源获取股票信息：{code}")
                return data
        except Exception as e:
            logger.error(f"从数据源获取股票信息失败 {code}: {e}")
            # 如果数据源失败，检查是否有缓存的旧数据
            old_cached = await cache_manager.get("kline", cache_key)
            if old_cached:
                logger.warning(f"使用缓存的旧数据：{code}")
                return old_cached
        
        raise DataNotFoundException(f"股票 {code} 不存在")
    
    async def _save_stock_info_to_db(self, code: str, data: Dict[str, Any]):
        """异步保存股票信息到数据库"""
        try:
            async with get_session() as session:
                # 检查是否已存在
                result = await session.execute(
                    select(StockInfo).where(StockInfo.code == code)
                )
                if result.scalar_one_or_none():
                    logger.debug(f"股票信息已存在，跳过保存：{code}")
                    return
                
                # 保存新记录
                stock = StockInfo(
                    code=code,
                    name=data["name"],
                    market=data.get("market", ""),
                    industry=data.get("industry"),
                    sector=data.get("sector"),
                    area=data.get("area"),
                    list_date=data.get("list_date"),
                    total_shares=data.get("total_shares"),
                    float_shares=data.get("float_shares")
                )
                session.add(stock)
                await session.commit()
                logger.info(f"保存股票信息到数据库：{code}")
        except Exception as e:
            logger.warning(f"保存股票信息到数据库失败 {code}: {e}")
    
    async def get_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq",
        use_cache: bool = True,
        persist: bool = True,
        priority_load: bool = True
    ) -> Dict[str, Any]:
        """
        获取 K 线数据（按需加载）
        
        策略：
        1. 优先从数据库缓存读取
        2. 如果数据库没有，才从数据源拉取
        3. 拉取后保存到数据库供后续使用
        
        Returns:
            {
                "status": "complete",
                "data": [...],
                "coverage": None,
                "background_loading": False
            }
        """
        # 按需加载：先查数据库，没有才拉取
        klines = await self._load_kline_on_demand(
            code, start_date, end_date, adjust, use_cache, persist
        )
        return {
            "status": "complete",
            "data": klines,
            "coverage": None,
            "background_loading": False
        }
    
    async def _load_kline_on_demand(
        self,
        code: str,
        start_date: Optional[str],
        end_date: Optional[str],
        adjust: str,
        use_cache: bool,
        persist: bool
    ) -> List[Dict[str, Any]]:
        """
        按需加载 K 线数据（Lazy Loading）
        
        加载策略：
        1. 优先从数据库读取（已缓存的数据）
        2. 如果数据库没有或数据不足，才从数据源拉取
        3. 拉取的数据保存到数据库，下次直接使用
        """
        cache_key = f"kline_{code}_{start_date}_{end_date}_{adjust}"
        
        # 1. 尝试从缓存读取
        if use_cache:
            cached = await cache_manager.get("kline", cache_key)
            if cached:
                logger.info(f"缓存命中：{code}, {len(cached)} 条")
                return cached
        
        # 2. 从数据库读取
        db_klines = await data_persistence.get_klines_from_db(
            code, start_date, end_date, adjust
        )
        
        if db_klines and len(db_klines) >= 100:
            # 数据库有足够数据，直接使用
            logger.info(f"数据库命中：{code}, {len(db_klines)} 条")
            klines = db_klines
        else:
            # 3. 数据库不足，从数据源拉取
            logger.info(f"数据库不足，从数据源拉取：{code}")
            klines = await data_source_manager.get_kline(code, start_date, end_date, adjust)
            
            if not klines:
                logger.warning(f"数据源返回空数据：{code}")
                raise DataNotFoundException(f"股票 {code} K 线数据不存在")
            
            logger.info(f"从数据源拉取 {len(klines)} 条：{code}")
            
            # 4. 保存到数据库（如果启用持久化）
            if persist:
                try:
                    await data_persistence.save_klines(code, klines, adjust)
                    logger.info(f"已保存到数据库：{code}, {len(klines)} 条")
                except Exception as e:
                    logger.warning(f"保存失败：{e}")
        
        # 5. 处理数据并返回
        df = pd.DataFrame([{
            "date": k.date,
            "open": k.open,
            "high": k.high,
            "low": k.low,
            "close": k.close,
            "volume": k.volume,
            "amount": k.amount,
            "turnover_rate": k.turnover_rate
        } for k in klines])
        
        df = self.processor.process_kline(df)
        result = df.to_dict("records")
        
        # 6. 更新缓存
        if use_cache:
            await cache_manager.set("kline", cache_key, result)
        
        return result
    
    async def _load_kline_priority(self, code: str, adjust: str, persist: bool) -> Dict[str, Any]:
        """优先加载本月和本年数据（已废弃，保留兼容）"""
        logger.warning("_load_kline_priority 已废弃，使用 _load_kline_on_demand")
        return await self._load_kline_on_demand(code, None, None, adjust, True, persist)
    
    async def _load_kline_traditional(
        self,
        code: str,
        start_date: Optional[str],
        end_date: Optional[str],
        adjust: str,
        use_cache: bool,
        persist: bool
    ) -> List[Dict[str, Any]]:
        """传统方式加载全部数据（已废弃，保留兼容）"""
        logger.warning("_load_kline_traditional 已废弃，使用 _load_kline_on_demand")
        return await self._load_kline_on_demand(code, start_date, end_date, adjust, use_cache, persist)
    
    async def get_technical_indicators(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        cache_key = f"indicators_{code}_{start_date}_{end_date}"
        cached = await cache_manager.get("indicators", cache_key)
        if cached:
            return cached
        
        # 注意：这里调用 get_kline 会返回 Dict，需要提取 data 字段
        kline_result = await self.get_kline(code, start_date, end_date, priority_load=False)
        klines = kline_result["data"] if isinstance(kline_result, dict) else kline_result
        
        df = pd.DataFrame(klines)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
        
        # 使用现代化的指标管理器计算所有指标
        df = self.indicator_manager.calculate_all_indicators(df, price_column="close")
        
        indicator_cols = ["date", "ma5", "ma10", "ma20", "ma60", 
                         "rsi6", "rsi12", "rsi24", 
                         "macd", "macd_signal", "macd_hist",
                         "boll_upper", "boll_mid", "boll_lower",
                         "k", "d", "j", "atr"]
        
        available_cols = [col for col in indicator_cols if col in df.columns]
        result_df = df[available_cols].copy()
        
        if "date" in result_df.columns:
            result_df["date"] = result_df["date"].dt.strftime("%Y-%m-%d")
        
        result = result_df.to_dict("records")
        
        await cache_manager.set("indicators", cache_key, result)
        
        return result
    
    async def get_realtime_quote(self, code: str) -> Dict[str, Any]:
        """
        获取实时行情（三级缓存优化）
        
        L1: 内存缓存 (60 秒) - 最快
        L2: 数据库缓存 (永久，直到更新) - 次快
        L3: 数据源实时拉取 - 最慢，受频率限制
        
        优先级策略：
        1. 优先使用缓存，避免触发数据源频率限制
        2. 数据源失败时，降级使用旧缓存
        3. 异步更新缓存，不阻塞返回
        """
        cache_key = f"realtime_{code}"
        
        # L1: 检查内存缓存（最快）
        cached = await cache_manager.get("realtime", cache_key)
        if cached:
            logger.debug(f"从内存缓存获取实时行情：{code}")
            return cached
        
        # L2: 检查数据库缓存（次快）
        try:
            async with get_session() as session:
                result = await session.execute(
                    select(RealtimeQuote).where(RealtimeQuote.code == code)
                )
                db_quote = result.scalar_one_or_none()
                
                if db_quote:
                    # 转换为字典格式
                    quote = {
                        "code": db_quote.code,
                        "name": db_quote.name,
                        "price": db_quote.price,
                        "change": db_quote.change,
                        "change_pct": db_quote.change_pct,
                        "volume": db_quote.volume,
                        "amount": db_quote.amount,
                        "high": db_quote.high,
                        "low": db_quote.low,
                        "open": db_quote.open,
                        "prev_close": db_quote.prev_close,
                        "turnover_rate": db_quote.turnover_rate,
                        "quote_time": db_quote.quote_time,
                    }
                    
                    # 更新内存缓存（60 秒）
                    await cache_manager.set("realtime", cache_key, quote, ttl=60)
                    
                    logger.debug(f"从数据库获取实时行情：{code}")
                    return quote
        except Exception as e:
            logger.warning(f"从数据库读取实时行情失败 {code}: {e}")
        
        # L3: 从数据源获取（最后选择）
        try:
            quote = await data_source_manager.get_realtime_quote(code)
            
            if not quote:
                raise DataNotFoundException(f"股票 {code} 实时行情不存在")
            
            # 保存到内存缓存
            await cache_manager.set("realtime", cache_key, quote, ttl=60)
            
            # 异步保存到数据库（不阻塞返回）
            asyncio.create_task(self._save_realtime_quote_to_db(code, quote))
            
            logger.debug(f"从数据源获取实时行情：{code}")
            return quote
            
        except Exception as e:
            logger.error(f"获取实时行情失败 {code}: {e}")
            # 降级策略：如果数据源失败，检查是否有旧缓存
            old_cached = await cache_manager.get("realtime", cache_key)
            if old_cached:
                logger.warning(f"使用缓存的旧实时行情：{code}")
                return old_cached
            
            raise DataNotFoundException(f"股票 {code} 实时行情获取失败：{e}")
    
    async def _save_realtime_quote_to_db(self, code: str, quote: Dict[str, Any]):
        """保存实时行情到数据库（异步后台任务）"""
        try:
            async with get_session() as session:
                # 检查是否已存在
                result = await session.execute(
                    select(RealtimeQuote).where(RealtimeQuote.code == code)
                )
                db_quote = result.scalar_one_or_none()
                
                if db_quote:
                    # 更新现有记录
                    db_quote.name = quote.get("name", db_quote.name)
                    db_quote.price = quote.get("price", 0)
                    db_quote.change = quote.get("change", 0)
                    db_quote.change_pct = quote.get("change_pct", 0)
                    db_quote.volume = quote.get("volume", 0)
                    db_quote.amount = quote.get("amount", 0)
                    db_quote.high = quote.get("high", 0)
                    db_quote.low = quote.get("low", 0)
                    db_quote.open = quote.get("open", 0)
                    db_quote.prev_close = quote.get("prev_close", 0)
                    db_quote.turnover_rate = quote.get("turnover_rate", 0)
                    db_quote.quote_time = quote.get("quote_time", "")
                    db_quote.updated_at = datetime.now()
                else:
                    # 创建新记录
                    new_quote = RealtimeQuote(
                        code=code,
                        name=quote.get("name", ""),
                        price=quote.get("price", 0),
                        change=quote.get("change", 0),
                        change_pct=quote.get("change_pct", 0),
                        volume=quote.get("volume", 0),
                        amount=quote.get("amount", 0),
                        high=quote.get("high", 0),
                        low=quote.get("low", 0),
                        open=quote.get("open", 0),
                        prev_close=quote.get("prev_close", 0),
                        turnover_rate=quote.get("turnover_rate", 0),
                        quote_time=quote.get("quote_time", ""),
                    )
                    session.add(new_quote)
                
                await session.commit()
                logger.debug(f"实时行情已保存到数据库：{code}")
                
        except Exception as e:
            logger.error(f"保存实时行情到数据库失败 {code}: {e}")
            try:
                await session.rollback()
            except:
                pass
    
    async def search_stocks(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        stocks = await data_source_manager.get_stock_list()
        
        keyword = keyword.lower()
        filtered = [
            {
                "code": s.code,
                "name": s.name,
                "market": s.market,
                "industry": s.industry
            }
            for s in stocks
            if keyword in s.code.lower() or keyword in s.name.lower()
        ]
        
        return filtered[:limit]
    
    async def get_klines_batch(
        self,
        codes: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq"
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        批量获取 K 线数据（解决 N+1 查询问题）
        
        Args:
            codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权类型
            
        Returns:
            {
                "000001": [...],
                "000002": [...],
                ...
            }
        """
        from sqlalchemy import select
        from app.storage import KLine
        
        results = {}
        
        # 批量查询数据库
        async with get_session() as session:
            query = select(KLine).where(KLine.code.in_(codes))
            
            if start_date:
                query = query.where(KLine.date >= start_date)
            if end_date:
                query = query.where(KLine.date <= end_date)
            
            result = await session.execute(query)
            db_klines = result.scalars().all()
        
        # 按股票代码分组
        grouped = {}
        for kline in db_klines:
            if kline.code not in grouped:
                grouped[kline.code] = []
            grouped[kline.code].append({
                "date": kline.date,
                "open": kline.open,
                "high": kline.high,
                "low": kline.low,
                "close": kline.close,
                "volume": kline.volume,
                "amount": kline.amount,
                "turnover_rate": kline.turnover_rate
            })
        
        # 对于数据库中没有的股票，从数据源获取
        missing_codes = [code for code in codes if code not in grouped or len(grouped[code]) < 100]
        
        if missing_codes:
            from asyncio import gather
            tasks = [
                self._load_kline_traditional(code, start_date, end_date, adjust, True, True)
                for code in missing_codes
            ]
            fetched_data = await gather(*tasks, return_exceptions=True)
            
            for code, data in zip(missing_codes, fetched_data):
                if isinstance(data, list):
                    grouped[code] = data
                else:
                    logger.warning(f"批量获取 {code} K 线数据失败：{data}")
                    grouped[code] = []
        
        return grouped
    
    async def get_realtime_quotes_batch(
        self,
        codes: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        批量获取实时行情（并发优化）
        
        Args:
            codes: 股票代码列表
            
        Returns:
            {
                "000001": {...},
                "000002": {...},
                ...
            }
        """
        from asyncio import gather, Semaphore
        
        # 限制并发数，避免过多请求
        semaphore = Semaphore(10)
        
        async def fetch_with_semaphore(code: str) -> tuple:
            async with semaphore:
                try:
                    quote = await self.get_realtime_quote(code)
                    return (code, quote)
                except Exception as e:
                    logger.warning(f"获取 {code} 实时行情失败：{e}")
                    return (code, None)
        
        tasks = [fetch_with_semaphore(code) for code in codes]
        results = await gather(*tasks)
        
        return {code: quote for code, quote in results if quote is not None}
    
    async def get_weekly_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq",
        use_cache: bool = True,
        persist: bool = True
    ) -> List[KLineData]:
        """
        获取周线 K 线数据（支持缓存和持久化）
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权类型
            use_cache: 是否使用缓存
            persist: 是否持久化到数据库
            
        Returns:
            周线 K 线数据列表
        """
        cache_key = f"kline_weekly_{code}_{start_date}_{end_date}_{adjust}"
        
        # 1. 尝试从缓存读取
        if use_cache:
            cached = await cache_manager.get("kline", cache_key)
            if cached:
                logger.info(f"周线缓存命中：{code}, {len(cached)} 条")
                return cached
        
        # 2. 从数据库读取
        db_klines = await data_persistence.get_klines_from_db(
            code, start_date, end_date, adjust
        )
        
        if db_klines and len(db_klines) >= 50:
            # 数据库有足够数据，直接使用
            logger.info(f"周线数据库命中：{code}, {len(db_klines)} 条")
            klines = db_klines
        else:
            # 3. 数据库不足，从数据源拉取
            logger.info(f"周线数据库不足，从数据源拉取：{code}")
            try:
                klines = await data_source_manager.get_weekly_kline(code, start_date, end_date, adjust)
            except PermissionError as pe:
                logger.warning(f"周线数据权限不足 {code}，已自动切换备选数据源：{pe}")
                klines = []
            except Exception as e:
                logger.error(f"获取周线数据失败 {code}: {e}")
                klines = []
            
            # 4. 保存到数据库（如果启用持久化）
            if persist and klines:
                await data_persistence.save_klines(code, klines, adjust)
        
        # 5. 更新缓存
        if use_cache and klines:
            await cache_manager.set("kline", cache_key, klines)
        
        return klines
    
    async def get_monthly_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq",
        use_cache: bool = True,
        persist: bool = True
    ) -> List[KLineData]:
        """
        获取月线 K 线数据（支持缓存和持久化）
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权类型
            use_cache: 是否使用缓存
            persist: 是否持久化到数据库
            
        Returns:
            月线 K 线数据列表
        """
        cache_key = f"kline_monthly_{code}_{start_date}_{end_date}_{adjust}"
        
        # 1. 尝试从缓存读取
        if use_cache:
            cached = await cache_manager.get("kline", cache_key)
            if cached:
                logger.info(f"月线缓存命中：{code}, {len(cached)} 条")
                return cached
        
        # 2. 从数据库读取
        db_klines = await data_persistence.get_klines_from_db(
            code, start_date, end_date, adjust
        )
        
        if db_klines and len(db_klines) >= 20:
            # 数据库有足够数据，直接使用
            logger.info(f"月线数据库命中：{code}, {len(db_klines)} 条")
            klines = db_klines
        else:
            # 3. 数据库不足，从数据源拉取
            logger.info(f"月线数据库不足，从数据源拉取：{code}")
            try:
                klines = await data_source_manager.get_monthly_kline(code, start_date, end_date, adjust)
            except PermissionError as pe:
                logger.warning(f"月线数据权限不足 {code}，已自动切换备选数据源：{pe}")
                klines = []
            except Exception as e:
                logger.error(f"获取月线数据失败 {code}: {e}")
                klines = []
            
            # 4. 保存到数据库（如果启用持久化）
            if persist and klines:
                await data_persistence.save_klines(code, klines, adjust)
        
        # 5. 更新缓存
        if use_cache and klines:
            await cache_manager.set("kline", cache_key, klines)
        
        return klines


# 单例
stock_service = StockService()

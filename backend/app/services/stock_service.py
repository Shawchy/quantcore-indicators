from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio
import pandas as pd
from loguru import logger
from sqlalchemy import select

from app.adapters import data_source_manager, KLineData
from app.services.data_processor import DataProcessor
from app.services.indicators import IndicatorCalculator
from app.storage import (
    StockInfo, KLine, TechnicalIndicatorDB, RealtimeQuote,
    get_session, cache_manager, parquet_store
)
from app.core.exceptions import DataNotFoundException, DataSourceException
from app.services.data_persistence import data_persistence
from app.services.data_loader import data_loader, LoadPriority, LoadProgress


class StockService:
    def __init__(self):
        self.processor = DataProcessor()
        self.indicator_calc = IndicatorCalculator()
    
    async def get_stock_basic(self, code: str) -> Dict[str, Any]:
        cache_key = f"stock_basic_{code}"
        cached = await cache_manager.get("kline", cache_key)
        if cached:
            return cached
        
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
                await cache_manager.set("kline", cache_key, data)
                return data
        
        stock_info = await data_source_manager.get_stock_info(code)
        if stock_info:
            return {
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
        
        raise DataNotFoundException(f"股票 {code} 不存在")
    
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
        获取 K 线数据（支持分层加载）
        
        Returns:
            {
                "status": "partial" | "complete",
                "data": [...],
                "coverage": {...},
                "background_loading": True | False
            }
        """
        # 如果指定了日期范围或禁用优先加载，使用传统方式
        if start_date or end_date or not priority_load:
            klines = await self._load_kline_traditional(
                code, start_date, end_date, adjust, use_cache, persist
            )
            return {
                "status": "complete",
                "data": klines,
                "coverage": None,
                "background_loading": False
            }
        
        # 启用优先加载模式
        return await self._load_kline_priority(code, adjust, persist)
    
    async def _load_kline_priority(self, code: str, adjust: str, persist: bool) -> Dict[str, Any]:
        """优先加载本月和本年数据"""
        try:
            # 第一优先：加载本月数据
            progress = await data_loader.load_kline_priority(
                code=code,
                data_source_manager=data_source_manager,
                data_persistence=data_persistence,
                priority=LoadPriority.CURRENT_MONTH
            )
            
            # 处理数据
            df = pd.DataFrame(progress.data)
            if not df.empty:
                df = self.processor.process_kline(df)
                result = df.to_dict("records")
            else:
                result = []
            
            return {
                "status": progress.status,
                "data": result,
                "coverage": progress.coverage,
                "background_loading": progress.background_loading,
                "total_expected": progress.total_expected,
                "loaded": progress.loaded
            }
            
        except Exception as e:
            logger.error(f"优先加载失败 {code}: {e}")
            # 降级到传统方式
            klines = await self._load_kline_traditional(code, None, None, adjust, True, persist)
            return {
                "status": "complete",
                "data": klines,
                "coverage": None,
                "background_loading": False
            }
    
    async def _load_kline_traditional(
        self,
        code: str,
        start_date: Optional[str],
        end_date: Optional[str],
        adjust: str,
        use_cache: bool,
        persist: bool
    ) -> List[Dict[str, Any]]:
        """传统方式加载全部数据"""
        cache_key = f"kline_{code}_{start_date}_{end_date}_{adjust}"
        
        if use_cache:
            cached = await cache_manager.get("kline", cache_key)
            if cached:
                logger.info(f"从缓存读取 {len(cached)} 条 K 线：{code}, 日期范围：{start_date} - {end_date}")
                return cached
        
        db_klines = await data_persistence.get_klines_from_db(
            code, start_date, end_date, adjust
        )
        
        logger.info(f"数据库查询结果：{len(db_klines) if db_klines else 0} 条，日期范围：{start_date} - {end_date}")
        
        if db_klines and len(db_klines) >= 100:
            klines = db_klines
            logger.info(f"从本地数据库读取 {len(klines)} 条 K 线：{code}")
        else:
            logger.info(f"数据库数据不足，从数据源获取：{code}, 日期范围：{start_date} - {end_date}")
            klines = await data_source_manager.get_kline(code, start_date, end_date, adjust)
            logger.info(f"数据源返回 {len(klines) if klines else 0} 条 K 线：{code}")
            
            if persist and klines:
                try:
                    await data_persistence.save_klines(code, klines, adjust)
                    logger.info(f"保存 {len(klines)} 条 K 线数据到数据库：{code}")
                except Exception as e:
                    logger.warning(f"保存 K 线数据失败：{e}")
        
        if not klines:
            raise DataNotFoundException(f"股票 {code} K 线数据不存在")
        
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
        
        if use_cache:
            await cache_manager.set("kline", cache_key, result)
        
        logger.info(f"返回 {len(result)} 条 K 线数据：{code}")
        
        return result
    
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
        
        df = self.indicator_calc.calculate_all(df)
        
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
        
        L1: 内存缓存 (60 秒)
        L2: 数据库缓存 (永久，直到更新)
        L3: 数据源实时拉取
        """
        cache_key = f"realtime_{code}"
        
        # L1: 检查内存缓存
        cached = await cache_manager.get("realtime", cache_key)
        if cached:
            return cached
        
        # L2: 检查数据库缓存
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
                    
                    # 更新内存缓存
                    await cache_manager.set("realtime", cache_key, quote, ttl=60)
                    
                    logger.debug(f"从数据库获取实时行情：{code}")
                    return quote
        except Exception as e:
            logger.warning(f"从数据库读取实时行情失败 {code}: {e}")
        
        # L3: 从数据源获取
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
        adjust: str = "qfq"
    ) -> List[KLineData]:
        """
        获取周线 K 线数据
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权类型
            
        Returns:
            周线 K 线数据列表
        """
        from app.adapters.factory import get_data_source
        
        data_source = await get_data_source()
        return await data_source.get_weekly_kline(code, start_date, end_date, adjust)
    
    async def get_monthly_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq"
    ) -> List[KLineData]:
        """
        获取月线 K 线数据
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权类型
            
        Returns:
            月线 K 线数据列表
        """
        from app.adapters.factory import get_data_source
        
        data_source = await get_data_source()
        return await data_source.get_monthly_kline(code, start_date, end_date, adjust)
    
    async def get_top_list(self, trade_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取龙虎榜数据
        
        Args:
            trade_date: 交易日期
            
        Returns:
            龙虎榜数据列表
        """
        from app.adapters.factory import get_data_source
        
        data_source = await get_data_source()
        return await data_source.get_top_list(trade_date)
    
    async def get_forecast(self, code: str, ann_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取业绩预告数据
        
        Args:
            code: 股票代码
            ann_date: 公告日期
            
        Returns:
            业绩预告数据列表
        """
        from app.adapters.factory import get_data_source
        
        data_source = await get_data_source()
        return await data_source.get_forecast(code, ann_date)
    
    async def get_moneyflow(self, code: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取资金流向数据
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            资金流向数据列表
        """
        from app.adapters.factory import get_data_source
        
        data_source = await get_data_source()
        return await data_source.get_moneyflow(code, start_date, end_date)


# 单例
stock_service = StockService()

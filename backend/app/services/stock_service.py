from typing import Optional, List, Dict, Any
from datetime import datetime
import pandas as pd
from loguru import logger
from sqlalchemy import select

from app.adapters import data_source_manager, KLineData
from app.services import DataProcessor, IndicatorCalculator
from app.storage import (
    StockInfo, KLine, TechnicalIndicatorDB, WatchlistDB,
    get_session, cache_manager, parquet_store
)
from app.core.exceptions import DataNotFoundException, DataSourceException


class StockService:
    def __init__(self):
        self.processor = DataProcessor()
        self.indicator_calc = IndicatorCalculator()
    
    async def get_stock_basic(self, code: str) -> Dict[str, Any]:
        cache_key = f"stock_basic_{code}"
        cached = cache_manager.get("kline", cache_key)
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
                cache_manager.set("kline", cache_key, data)
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
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        cache_key = f"kline_{code}_{start_date}_{end_date}_{adjust}"
        
        if use_cache:
            cached = cache_manager.get("kline", cache_key)
            if cached:
                return cached
        
        klines = await data_source_manager.get_kline(code, start_date, end_date, adjust)
        
        if not klines:
            raise DataNotFoundException(f"股票 {code} K线数据不存在")
        
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
            cache_manager.set("kline", cache_key, result)
        
        return result
    
    async def get_technical_indicators(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        cache_key = f"indicators_{code}_{start_date}_{end_date}"
        cached = cache_manager.get("indicators", cache_key)
        if cached:
            return cached
        
        klines = await self.get_kline(code, start_date, end_date)
        
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
        
        cache_manager.set("indicators", cache_key, result)
        
        return result
    
    async def get_realtime_quote(self, code: str) -> Dict[str, Any]:
        cache_key = f"realtime_{code}"
        cached = cache_manager.get("realtime", cache_key)
        if cached:
            return cached
        
        quote = await data_source_manager.get_realtime_quote(code)
        
        if not quote:
            raise DataNotFoundException(f"股票 {code} 实时行情不存在")
        
        cache_manager.set("realtime", cache_key, quote, ttl=60)
        
        return quote
    
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


class WatchlistService:
    async def get_watchlist(self) -> List[Dict[str, Any]]:
        async with get_session() as session:
            result = await session.execute(select(WatchlistDB))
            watchlist = result.scalars().all()
            
            return [{
                "code": item.code,
                "note": item.note,
                "created_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": item.updated_at.strftime("%Y-%m-%d %H:%M:%S")
            } for item in watchlist]
    
    async def add_to_watchlist(self, code: str, note: Optional[str] = None) -> Dict[str, Any]:
        async with get_session() as session:
            existing = await session.execute(
                select(WatchlistDB).where(WatchlistDB.code == code)
            )
            if existing.scalar_one_or_none():
                return {"code": code, "message": "已在自选股中"}
            
            watchlist_item = WatchlistDB(code=code, note=note)
            session.add(watchlist_item)
            await session.commit()
            
            return {
                "code": code,
                "note": note,
                "message": "添加成功"
            }
    
    async def remove_from_watchlist(self, code: str) -> Dict[str, Any]:
        async with get_session() as session:
            result = await session.execute(
                select(WatchlistDB).where(WatchlistDB.code == code)
            )
            item = result.scalar_one_or_none()
            
            if not item:
                return {"code": code, "message": "不在自选股中"}
            
            await session.delete(item)
            await session.commit()
            
            return {"code": code, "message": "删除成功"}
    
    async def update_watchlist_note(self, code: str, note: str) -> Dict[str, Any]:
        async with get_session() as session:
            result = await session.execute(
                select(WatchlistDB).where(WatchlistDB.code == code)
            )
            item = result.scalar_one_or_none()
            
            if not item:
                return {"code": code, "message": "不在自选股中"}
            
            item.note = note
            await session.commit()
            
            return {
                "code": code,
                "note": note,
                "message": "更新成功"
            }
    
    async def get_watchlist_quotes(self) -> List[Dict[str, Any]]:
        watchlist = await self.get_watchlist()
        quotes = []
        
        stock_service = StockService()
        for item in watchlist:
            try:
                quote = await stock_service.get_realtime_quote(item["code"])
                quote["note"] = item["note"]
                quotes.append(quote)
            except Exception as e:
                logger.warning(f"获取自选股 {item['code']} 行情失败: {e}")
        
        return quotes


stock_service = StockService()
watchlist_service = WatchlistService()

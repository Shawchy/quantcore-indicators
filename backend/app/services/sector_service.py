from typing import Optional, List, Dict, Any
import pandas as pd
from loguru import logger
from sqlalchemy import select

from app.adapters import data_source_manager
from app.storage import cache_manager, SectorInfo, get_session
from app.core.exceptions import DataNotFoundException
from app.api.v1.endpoints.data_source_control import should_use_mock_data


class SectorService:
    async def get_sector_list(self, sector_type: str = "industry") -> List[Dict[str, Any]]:
        cache_key = f"sector_list_{sector_type}"
        cached = await cache_manager.get("sector", cache_key)
        if cached:
            return cached
        
        # 在模拟数据模式下，从数据库读取
        if should_use_mock_data():
            async with get_session() as session:
                result = await session.execute(
                    select(SectorInfo).where(SectorInfo.sector_type == sector_type)
                )
                sectors = result.scalars().all()
                
                result = [{
                    "code": s.code,
                    "name": s.name,
                    "sector_type": s.sector_type,
                    "change_pct": s.change_pct,
                    "volume": s.volume,
                    "amount": s.amount
                } for s in sectors]
                
                await cache_manager.set("sector", cache_key, result)
                return result
        
        sectors = await data_source_manager.get_sector_list(sector_type)
        
        result = [{
            "code": s.code,
            "name": s.name,
            "sector_type": s.sector_type,
            "change_pct": s.change_pct,
            "volume": s.volume,
            "amount": s.amount
        } for s in sectors]
        
        await cache_manager.set("sector", cache_key, result)
        
        return result
    
    async def get_sector_ranking(
        self,
        sector_type: str = "industry",
        sort_by: str = "change_pct",
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        cache_key = f"sector_ranking_{sector_type}_{sort_by}_{limit}"
        cached = await cache_manager.get("sector", cache_key)
        if cached:
            return cached
        
        sectors = await self.get_sector_list(sector_type)
        
        if sort_by == "change_pct":
            sectors = sorted(sectors, key=lambda x: x.get("change_pct", 0) or 0, reverse=True)
        elif sort_by == "volume":
            sectors = sorted(sectors, key=lambda x: x.get("volume", 0) or 0, reverse=True)
        elif sort_by == "amount":
            sectors = sorted(sectors, key=lambda x: x.get("amount", 0) or 0, reverse=True)
        
        result = sectors[:limit]
        
        await cache_manager.set("sector", cache_key, result)
        
        return result
    
    async def get_sector_components(self, sector_code: str) -> List[Dict[str, Any]]:
        cache_key = f"sector_components_{sector_code}"
        cached = await cache_manager.get("sector", cache_key)
        if cached:
            return cached
        
        codes = await data_source_manager.get_sector_components(sector_code)
        
        if not codes:
            raise DataNotFoundException(f"板块 {sector_code} 不存在或无成分股")
        
        result = [{"code": code} for code in codes]
        
        await cache_manager.set("sector", cache_key, result)
        
        return result
    
    async def get_sector_leaders(
        self,
        sector_code: str,
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        from asyncio import gather, Semaphore
        
        components = await self.get_sector_components(sector_code)
        
        leaders = []
        from app.services.stock_service import stock_service
        
        # 使用信号量限制并发数，避免过多请求
        semaphore = Semaphore(10)
        
        async def fetch_with_semaphore(item):
            async with semaphore:
                try:
                    quote = await stock_service.get_realtime_quote(item["code"])
                    if quote:
                        return {
                            "code": item["code"],
                            "name": quote.get("name", ""),
                            "change_pct": quote.get("change_pct", 0),
                            "price": quote.get("price", 0),
                            "volume": quote.get("volume", 0)
                        }
                    return None
                except Exception as e:
                    logger.warning(f"获取股票 {item['code']} 行情失败：{e}")
                    return None
        
        # 并发获取最多 50 只股票的行情
        tasks = [fetch_with_semaphore(item) for item in components[:50]]
        results = await gather(*tasks)
        
        # 过滤掉 None 值
        leaders = [result for result in results if result is not None]
        
        # 按涨跌幅排序
        leaders.sort(key=lambda x: x.get("change_pct", 0) or 0, reverse=True)
        
        return leaders[:top_n]


sector_service = SectorService()

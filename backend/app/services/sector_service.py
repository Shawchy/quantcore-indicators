from typing import Optional, List, Dict, Any
import pandas as pd
from loguru import logger
from sqlalchemy import select

from app.adapters import data_source_manager
from app.storage import cache_manager, SectorInfo, get_session
from app.core.exceptions import DataNotFoundException


class SectorService:
    async def get_sector_list(self, sector_type: str = "industry") -> List[Dict[str, Any]]:
        cache_key = f"sector_list_{sector_type}"
        cached = await cache_manager.get("sector", cache_key)
        if cached:
            return cached
        
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
        components = await self.get_sector_components(sector_code)
        
        leaders = []
        from app.services.stock_service import stock_service
        
        for item in components[:50]:
            try:
                quote = await stock_service.get_realtime_quote(item["code"])
                if quote:
                    leaders.append({
                        "code": item["code"],
                        "name": quote.get("name", ""),
                        "change_pct": quote.get("change_pct", 0),
                        "price": quote.get("price", 0),
                        "volume": quote.get("volume", 0)
                    })
            except Exception as e:
                logger.warning(f"获取股票 {item['code']} 行情失败: {e}")
        
        leaders.sort(key=lambda x: x.get("change_pct", 0) or 0, reverse=True)
        
        return leaders[:top_n]


sector_service = SectorService()

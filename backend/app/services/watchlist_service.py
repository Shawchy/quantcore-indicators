from typing import List, Dict, Any, Optional
import asyncio
from sqlalchemy import select
from loguru import logger

from app.storage import WatchlistDB, get_session
from app.services.stock_service import StockService

_stock_service_instance: Optional[StockService] = None


def _get_stock_service() -> StockService:
    global _stock_service_instance
    if _stock_service_instance is None:
        _stock_service_instance = StockService()
    return _stock_service_instance


class WatchlistService:
    
    async def get_watchlist(self) -> List[Dict[str, Any]]:
        async with get_session() as session:
            result = await session.execute(select(WatchlistDB))
            watchlist = result.scalars().all()
            
            return [{
                "code": item.code,
                "note": item.note,
                "created_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S") if item.created_at else None,
                "updated_at": item.updated_at.strftime("%Y-%m-%d %H:%M:%S") if item.updated_at else None
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
        if not watchlist:
            return []
        
        stock_service = _get_stock_service()
        
        async def _fetch_quote(item: Dict) -> Optional[Dict]:
            try:
                quote = await stock_service.get_realtime_quote(item["code"])
                quote["note"] = item["note"]
                return quote
            except Exception as e:
                logger.warning(f"获取自选股 {item['code']} 行情失败：{e}")
                return None
        
        tasks = [_fetch_quote(item) for item in watchlist]
        results = await asyncio.gather(*tasks)
        
        return [r for r in results if r is not None]


watchlist_service = WatchlistService()

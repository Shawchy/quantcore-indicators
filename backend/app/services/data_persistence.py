from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np
from loguru import logger
import asyncio
from sqlalchemy import select, and_

from app.storage.sqlite import get_session, KLine as KLineDB, StockInfo as StockInfoDB
from app.adapters import KLineData
from app.config import settings


class DataPersistence:
    def __init__(self):
        self.parquet_dir = Path(settings.PARQUET_DIR)
        self.parquet_dir.mkdir(parents=True, exist_ok=True)
    
    async def save_klines(
        self,
        code: str,
        klines: List[KLineData],
        adjust: str = "qfq"
    ) -> int:
        if not klines:
            return 0
        
        saved_count = 0
        
        async with get_session() as session:
            for kline in klines:
                try:
                    existing = await session.execute(
                        select(KLineDB).where(
                            and_(
                                KLineDB.code == code,
                                KLineDB.date == kline.date,
                                KLineDB.adjust_type == adjust
                            )
                        )
                    )
                    
                    if existing.scalar_one_or_none():
                        continue
                    
                    db_kline = KLineDB(
                        code=code,
                        date=kline.date,
                        open=kline.open,
                        high=kline.high,
                        low=kline.low,
                        close=kline.close,
                        volume=kline.volume,
                        amount=kline.amount,
                        turnover_rate=kline.turnover_rate,
                        adjust_type=adjust
                    )
                    session.add(db_kline)
                    saved_count += 1
                    
                except Exception as e:
                    logger.warning(f"保存K线失败 {code} {kline.date}: {e}")
            
            await session.commit()
        
        if saved_count > 0:
            logger.info(f"已保存 {saved_count} 条K线数据: {code}")
            await self._save_to_parquet(code, klines, adjust)
        
        return saved_count
    
    async def _save_to_parquet(
        self,
        code: str,
        klines: List[KLineData],
        adjust: str
    ):
        try:
            df = pd.DataFrame([{
                "date": k.date,
                "open": k.open,
                "high": k.high,
                "low": k.low,
                "close": k.close,
                "volume": k.volume,
                "amount": k.amount,
                "turnover_rate": k.turnover_rate,
                "adjust_type": adjust
            } for k in klines])
            
            parquet_file = self.parquet_dir / f"{code}_{adjust}.parquet"
            
            if parquet_file.exists():
                existing_df = pd.read_parquet(parquet_file)
                combined_df = pd.concat([existing_df, df], ignore_index=True)
                combined_df = combined_df.drop_duplicates(subset=["date"], keep="last")
                combined_df = combined_df.sort_values("date")
                combined_df.to_parquet(parquet_file, index=False)
            else:
                df.to_parquet(parquet_file, index=False)
            
            logger.info(f"已归档到Parquet: {code}_{adjust}")
            
        except Exception as e:
            logger.warning(f"保存Parquet失败 {code}: {e}")
    
    async def get_klines_from_db(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq",
        limit: int = 5000
    ) -> List[KLineData]:
        async with get_session() as session:
            query = select(KLineDB).where(
                and_(
                    KLineDB.code == code,
                    KLineDB.adjust_type == adjust
                )
            )
            
            if start_date:
                query = query.where(KLineDB.date >= start_date)
            if end_date:
                query = query.where(KLineDB.date <= end_date)
            
            query = query.order_by(KLineDB.date).limit(limit)
            
            result = await session.execute(query)
            klines = result.scalars().all()
            
            return [
                KLineData(
                    code=k.code,
                    date=k.date,
                    open=k.open,
                    high=k.high,
                    low=k.low,
                    close=k.close,
                    volume=k.volume,
                    amount=k.amount,
                    turnover_rate=k.turnover_rate
                )
                for k in klines
            ]
    
    async def get_klines_from_parquet(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq"
    ) -> List[KLineData]:
        parquet_file = self.parquet_dir / f"{code}_{adjust}.parquet"
        
        if not parquet_file.exists():
            return []
        
        try:
            df = pd.read_parquet(parquet_file)
            
            if start_date:
                df = df[df["date"] >= start_date]
            if end_date:
                df = df[df["date"] <= end_date]
            
            df = df.sort_values("date")
            
            return [
                KLineData(
                    code=code,
                    date=row["date"],
                    open=row["open"],
                    high=row["high"],
                    low=row["low"],
                    close=row["close"],
                    volume=row["volume"],
                    amount=row.get("amount"),
                    turnover_rate=row.get("turnover_rate")
                )
                for _, row in df.iterrows()
            ]
            
        except Exception as e:
            logger.warning(f"读取Parquet失败 {code}: {e}")
            return []
    
    async def get_latest_date(
        self,
        code: str,
        adjust: str = "qfq"
    ) -> Optional[str]:
        klines = await self.get_klines_from_db(code, adjust=adjust, limit=1)
        if klines:
            return klines[0].date
        
        klines = await self.get_klines_from_parquet(code, adjust=adjust)
        if klines:
            return klines[-1].date
        
        return None
    
    async def save_stock_info(self, stock_data: Dict[str, Any]) -> bool:
        async with get_session() as session:
            try:
                existing = await session.execute(
                    select(StockInfoDB).where(StockInfoDB.code == stock_data["code"])
                )
                
                if existing.scalar_one_or_none():
                    return False
                
                stock = StockInfoDB(
                    code=stock_data["code"],
                    name=stock_data["name"],
                    market=stock_data.get("market", ""),
                    industry=stock_data.get("industry"),
                    sector=stock_data.get("sector"),
                    area=stock_data.get("area"),
                    list_date=stock_data.get("list_date"),
                    total_shares=stock_data.get("total_shares"),
                    float_shares=stock_data.get("float_shares")
                )
                session.add(stock)
                await session.commit()
                return True
                
            except Exception as e:
                logger.warning(f"保存股票信息失败 {stock_data.get('code')}: {e}")
                return False
    
    async def get_stock_info_list(
        self,
        limit: int = 5000,
        industry: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        async with get_session() as session:
            query = select(StockInfoDB)
            
            if industry:
                query = query.where(StockInfoDB.industry == industry)
            
            query = query.limit(limit)
            
            result = await session.execute(query)
            stocks = result.scalars().all()
            
            return [{
                "code": s.code,
                "name": s.name,
                "market": s.market,
                "industry": s.industry,
                "sector": s.sector,
                "area": s.area,
                "list_date": s.list_date,
                "total_shares": s.total_shares,
                "float_shares": s.float_shares
            } for s in stocks]


data_persistence = DataPersistence()

from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np
from loguru import logger
from sqlalchemy import select

from app.adapters import data_source_manager, ChipData
from app.storage import cache_manager, ChipData as ChipDataDB, get_session
from app.core.exceptions import DataNotFoundException


class ChipService:
    async def get_chip_data(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        cache_key = f"chip_data_{code}_{start_date}_{end_date}"
        cached = await cache_manager.get("chip", cache_key)
        if cached:
            return cached
        
        chip_data = await data_source_manager.get_chip_data(code, start_date, end_date)
        
        if not chip_data:
            raise DataNotFoundException(f"股票 {code} 筹码数据不存在")
        
        result = [{
            "code": c.code,
            "date": c.date,
            "shareholder_count": c.shareholder_count,
            "avg_shares_per_holder": c.avg_shares_per_holder,
            "top10_holders_ratio": c.top10_holders_ratio
        } for c in chip_data]
        
        await cache_manager.set("chip", cache_key, result)
        
        return result
    
    async def calculate_control_degree(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        chip_data = await self.get_chip_data(code, start_date, end_date)
        
        if not chip_data:
            raise DataNotFoundException(f"股票 {code} 筹码数据不足")
        
        df = pd.DataFrame(chip_data)
        df = df.sort_values("date")
        
        df["shareholder_change"] = df["shareholder_count"].pct_change()
        
        df["control_degree"] = self._compute_control_degree(df)
        
        latest = df.iloc[-1]
        
        return {
            "code": code,
            "date": latest["date"],
            "shareholder_count": latest["shareholder_count"],
            "avg_shares_per_holder": latest["avg_shares_per_holder"],
            "shareholder_change": latest.get("shareholder_change", 0),
            "control_degree": latest.get("control_degree", 0),
            "history": df[["date", "shareholder_count", "control_degree"]].to_dict("records")
        }
    
    def _compute_control_degree(self, df: pd.DataFrame) -> pd.Series:
        if "shareholder_count" not in df.columns:
            return pd.Series(0, index=df.index)
        
        shareholder_count = df["shareholder_count"]
        
        max_count = shareholder_count.max()
        min_count = shareholder_count.min()
        
        if max_count == min_count:
            return pd.Series(0.5, index=df.index)
        
        normalized = (max_count - shareholder_count) / (max_count - min_count)
        
        if "avg_shares_per_holder" in df.columns:
            avg_shares = df["avg_shares_per_holder"]
            max_avg = avg_shares.max()
            min_avg = avg_shares.min()
            
            if max_avg != min_avg:
                avg_normalized = (avg_shares - min_avg) / (max_avg - min_avg)
                control_degree = 0.6 * normalized + 0.4 * avg_normalized
                return control_degree
        
        return normalized
    
    async def screen_high_control(
        self,
        min_control_degree: float = 0.5,
        max_control_degree: float = 1.0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        stocks = await data_source_manager.get_stock_list()
        
        results = []
        for stock in stocks[:100]:
            try:
                control_info = await self.calculate_control_degree(stock.code)
                control_degree = control_info.get("control_degree", 0)
                
                if min_control_degree <= control_degree <= max_control_degree:
                    results.append({
                        "code": stock.code,
                        "name": stock.name,
                        "control_degree": control_degree,
                        "shareholder_count": control_info.get("shareholder_count"),
                        "date": control_info.get("date")
                    })
            except Exception as e:
                logger.debug(f"计算 {stock.code} 控盘度失败: {e}")
                continue
        
        results.sort(key=lambda x: x["control_degree"], reverse=True)
        
        return results[:limit]
    
    async def get_control_ranking(
        self,
        sort_order: str = "desc",
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        cache_key = f"control_ranking_{sort_order}_{limit}"
        cached = await cache_manager.get("chip", cache_key)
        if cached:
            return cached
        
        results = await self.screen_high_control(0, 1, limit * 2)
        
        if sort_order == "asc":
            results.sort(key=lambda x: x["control_degree"])
        else:
            results.sort(key=lambda x: x["control_degree"], reverse=True)
        
        result = results[:limit]
        await cache_manager.set("chip", cache_key, result, ttl=600)
        
        return result


chip_service = ChipService()

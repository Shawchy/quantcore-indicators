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
        
        # 1. 检查内存缓存
        cached = await cache_manager.get("chip", cache_key)
        if cached:
            logger.debug(f"从内存缓存获取筹码数据：{code}")
            return cached
        
        # 2. 优先从数据库读取（避免每次都从数据源拉取）
        try:
            async with get_session() as session:
                query = select(ChipDataDB).where(ChipDataDB.code == code)
                if start_date:
                    query = query.where(ChipDataDB.date >= start_date)
                if end_date:
                    query = query.where(ChipDataDB.date <= end_date)
                
                result = await session.execute(query)
                chip_data = result.scalars().all()
                
                if chip_data:
                    logger.debug(f"从数据库获取筹码数据：{code} ({len(chip_data)}条)")
                    result = [{
                        "code": c.code,
                        "date": c.date,
                        "shareholder_count": c.shareholder_count,
                        "avg_shares_per_holder": c.avg_shares_per_holder,
                        "top10_holders_ratio": getattr(c, 'top10_holders_ratio', None),
                        "control_degree": getattr(c, 'control_degree', None),
                        "concentration": getattr(c, 'concentration', None)
                    } for c in chip_data]
                    
                    await cache_manager.set("chip", cache_key, result)
                    return result
        except Exception as e:
            logger.warning(f"从数据库读取筹码数据失败：{code}, {e}")
        
        # 3. 数据库没有数据时，从数据源获取
        logger.info(f"数据库无筹码数据，从数据源获取：{code}")
        
        # 从数据源获取数据
        chip_data = await data_source_manager.get_chip_data(code, start_date, end_date)
        
        if not chip_data:
            raise DataNotFoundException(f"股票 {code} 筹码数据不存在")
        
        # 保存到数据库
        try:
            await self._save_chip_data(code, chip_data)
            logger.info(f"保存 {len(chip_data)} 条筹码数据到数据库：{code}")
        except Exception as e:
            logger.warning(f"保存筹码数据失败：{e}")
        
        result = [{
            "code": c.code,
            "date": c.date,
            "shareholder_count": c.shareholder_count,
            "avg_shares_per_holder": c.avg_shares_per_holder,
            "top10_holders_ratio": getattr(c, 'top10_holders_ratio', None),
            "control_degree": getattr(c, 'control_degree', None),
            "concentration": getattr(c, 'concentration', None)
        } for c in chip_data]
        
        await cache_manager.set("chip", cache_key, result)
        
        return result
    
    async def _save_chip_data(self, code: str, chip_data: List[ChipData]):
        """批量保存筹码数据到数据库"""
        logger.debug(f"开始保存筹码数据：{code}, 共{len(chip_data)}条")
        
        if not chip_data:
            logger.warning(f"没有数据需要保存：{code}")
            return
        
        try:
            async with get_session() as session:
                # 1. 查询已存在的记录
                dates = [c.date for c in chip_data]
                logger.debug(f"查询已存在记录：{code}, 日期范围：{min(dates)}-{max(dates)}")
                
                query = select(ChipDataDB.date).where(
                    ChipDataDB.code == code,
                    ChipDataDB.date.in_(dates)
                )
                result = await session.execute(query)
                existing_dates = set(result.scalars().all())
                
                logger.debug(f"已存在 {len(existing_dates)} 条记录，需要插入 {len(chip_data) - len(existing_dates)} 条")
                
                # 2. 过滤出需要插入的记录
                to_insert = []
                for c in chip_data:
                    if c.date not in existing_dates:
                        db_chip = ChipDataDB(
                            code=code,
                            date=c.date,
                            shareholder_count=c.shareholder_count,
                            avg_shares_per_holder=c.avg_shares_per_holder,
                            top10_holders_ratio=getattr(c, 'top10_holders_ratio', None),
                            control_degree=getattr(c, 'control_degree', None),
                            concentration=getattr(c, 'concentration', None)
                        )
                        to_insert.append(db_chip)
                
                # 3. 批量插入
                if to_insert:
                    logger.debug(f"批量插入 {len(to_insert)} 条记录：{code}")
                    session.add_all(to_insert)
                    await session.commit()
                    logger.info(f"批量保存 {len(to_insert)} 条筹码数据：{code}")
                else:
                    logger.debug(f"所有数据已存在，无需插入：{code}")
                    
        except Exception as e:
            logger.error(f"保存筹码数据到数据库失败：{code}, 错误：{str(e)}", exc_info=True)
            raise
    
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

"""
市场成交额数据持久化服务

提供历史成交额的存储和查询功能
"""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
from datetime import datetime
import asyncio
import random
import akshare as ak
from loguru import logger

from app.storage.sqlite import MarketTurnover, get_session


class MarketTurnoverService:
    """市场成交额服务"""
    
    @staticmethod
    async def save_turnover_data(
        session: AsyncSession,
        trade_date: str,
        sh_turnover: float,
        sz_turnover: float,
        total_turnover: float,
        stock_count: int = 0
    ) -> bool:
        try:
            result = await session.execute(
                select(MarketTurnover).where(MarketTurnover.trade_date == trade_date)
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                existing.sh_turnover = sh_turnover
                existing.sz_turnover = sz_turnover
                existing.total_turnover = total_turnover
                existing.stock_count = stock_count
                existing.updated_at = datetime.now()
                logger.info(f"更新成交额数据：{trade_date}")
            else:
                new_record = MarketTurnover(
                    trade_date=trade_date,
                    sh_turnover=sh_turnover,
                    sz_turnover=sz_turnover,
                    total_turnover=total_turnover,
                    stock_count=stock_count
                )
                session.add(new_record)
                logger.info(f"保存成交额数据：{trade_date}")
            
            await session.commit()
            return True
            
        except Exception as e:
            logger.error(f"保存成交额数据失败：{e}")
            await session.rollback()
            return False
    
    @staticmethod
    async def get_turnover_data(
        session: AsyncSession,
        trade_date: str
    ) -> Optional[Dict[str, Any]]:
        try:
            result = await session.execute(
                select(MarketTurnover).where(MarketTurnover.trade_date == trade_date)
            )
            record = result.scalar_one_or_none()
            
            if record:
                return {
                    'trade_date': record.trade_date,
                    'sh_turnover': record.sh_turnover,
                    'sz_turnover': record.sz_turnover,
                    'total_turnover': record.total_turnover,
                    'stock_count': record.stock_count
                }
            return None
            
        except Exception as e:
            logger.error(f"获取成交额数据失败：{e}")
            return None
    
    @staticmethod
    async def get_latest_turnover(session: AsyncSession) -> Optional[Dict[str, Any]]:
        try:
            result = await session.execute(
                select(MarketTurnover).order_by(MarketTurnover.trade_date.desc()).limit(1)
            )
            record = result.scalar_one_or_none()
            
            if record:
                return {
                    'trade_date': record.trade_date,
                    'sh_turnover': record.sh_turnover,
                    'sz_turnover': record.sz_turnover,
                    'total_turnover': record.total_turnover,
                    'stock_count': record.stock_count
                }
            return None
            
        except Exception as e:
            logger.error(f"获取最新成交额数据失败：{e}")
            return None
    
    @staticmethod
    async def fetch_and_save_latest(session: AsyncSession) -> Optional[Dict[str, Any]]:
        try:
            from app.services.trading_calendar import trading_calendar
            trade_date = await trading_calendar.get_latest_trading_day()
            
            existing = await MarketTurnoverService.get_turnover_data(session, trade_date)
            if existing:
                logger.info(f"数据库已有 {trade_date} 成交额数据")
                return existing
            
            logger.info(f"从 akshare 获取 {trade_date} 成交额数据...")
            
            max_retries = 3
            df_sh = None
            df_sz = None
            
            for retry_attempt in range(max_retries):
                try:
                    df_sh = ak.stock_sh_a_spot_em()
                    df_sz = ak.stock_sz_a_spot_em()
                    break
                except Exception as e:
                    if retry_attempt < max_retries - 1:
                        delay = (2 ** retry_attempt) * 1.0 + random.uniform(0, 0.5)
                        logger.warning(f"获取成交额数据失败，{delay:.1f}秒后重试（{retry_attempt+1}/{max_retries}）: {e}")
                        await asyncio.sleep(delay)
                    else:
                        raise e
            
            sh_turnover = df_sh['成交额'].sum()
            sz_turnover = df_sz['成交额'].sum()
            total_turnover = sh_turnover + sz_turnover
            stock_count = len(df_sh) + len(df_sz)
            
            logger.info(f"沪市：{sh_turnover/100000000:.2f}亿，深市：{sz_turnover/100000000:.2f}亿")
            
            success = await MarketTurnoverService.save_turnover_data(
                session, trade_date, sh_turnover, sz_turnover, total_turnover, stock_count
            )
            
            if success:
                logger.info(f"✅ 保存 {trade_date} 成交额数据成功")
                return {
                    'trade_date': trade_date,
                    'sh_turnover': sh_turnover,
                    'sz_turnover': sz_turnover,
                    'total_turnover': total_turnover,
                    'stock_count': stock_count
                }
            else:
                logger.error(f"保存 {trade_date} 成交额数据失败")
                return None
                
        except Exception as e:
            logger.error(f"获取并保存成交额数据失败：{e}")
            return None


market_turnover_service = MarketTurnoverService()

"""
市场成交额数据持久化服务

提供历史成交额的存储和查询功能
"""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
from datetime import datetime
import akshare as ak
from loguru import logger


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
        """
        保存成交额数据到数据库
        
        Args:
            session: 数据库会话
            trade_date: 交易日期 YYYYMMDD
            sh_turnover: 沪市成交额（元）
            sz_turnover: 深市成交额（元）
            total_turnover: 总成交额（元）
            stock_count: 股票总数
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 检查是否已存在
            result = await session.execute(
                select(MarketTurnover).where(MarketTurnover.trade_date == trade_date)
            )
            existing = result.fetchone()
            
            if existing:
                # 更新现有记录
                existing[0].sh_turnover = sh_turnover
                existing[0].sz_turnover = sz_turnover
                existing[0].total_turnover = total_turnover
                existing[0].stock_count = stock_count
                existing[0].updated_at = datetime.now().isoformat()
                logger.info(f"更新成交额数据：{trade_date}")
            else:
                # 插入新记录
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
        """
        获取指定日期的成交额数据
        
        Args:
            session: 数据库会话
            trade_date: 交易日期 YYYYMMDD
            
        Returns:
            dict: 成交额数据，包含 sh_turnover, sz_turnover, total_turnover
            None: 如果数据不存在
        """
        try:
            result = await session.execute(
                select(MarketTurnover).where(MarketTurnover.trade_date == trade_date)
            )
            record = result.fetchone()
            
            if record:
                r = record[0]
                return {
                    'trade_date': r.trade_date,
                    'sh_turnover': r.sh_turnover,
                    'sz_turnover': r.sz_turnover,
                    'total_turnover': r.total_turnover,
                    'stock_count': r.stock_count
                }
            return None
            
        except Exception as e:
            logger.error(f"获取成交额数据失败：{e}")
            return None
    
    @staticmethod
    async def get_latest_turnover(session: AsyncSession) -> Optional[Dict[str, Any]]:
        """
        获取最新交易日的成交额数据
        
        Args:
            session: 数据库会话
            
        Returns:
            dict: 成交额数据
            None: 如果没有数据
        """
        try:
            result = await session.execute(
                select(MarketTurnover).order_by(MarketTurnover.trade_date.desc()).limit(1)
            )
            record = result.fetchone()
            
            if record:
                r = record[0]
                return {
                    'trade_date': r.trade_date,
                    'sh_turnover': r.sh_turnover,
                    'sz_turnover': r.sz_turnover,
                    'total_turnover': r.total_turnover,
                    'stock_count': r.stock_count
                }
            return None
            
        except Exception as e:
            logger.error(f"获取最新成交额数据失败：{e}")
            return None
    
    @staticmethod
    async def fetch_and_save_latest(session: AsyncSession) -> Optional[Dict[str, Any]]:
        """
        获取最新成交额数据并保存到数据库
        
        Args:
            session: 数据库会话
            
        Returns:
            dict: 成交额数据
            None: 如果获取失败
        """
        try:
            # 获取最新交易日期
            from app.services.trading_calendar import trading_calendar
            trade_date = await trading_calendar.get_latest_trading_day()
            
            # 检查数据库是否已有该日期数据
            existing = await MarketTurnoverService.get_turnover_data(session, trade_date)
            if existing:
                logger.info(f"数据库已有 {trade_date} 成交额数据")
                return existing
            
            # 从 akshare 获取数据
            logger.info(f"从 akshare 获取 {trade_date} 成交额数据...")
            df_sh = ak.stock_sh_a_spot_em()
            df_sz = ak.stock_sz_a_spot_em()
            
            sh_turnover = df_sh['成交额'].sum()
            sz_turnover = df_sz['成交额'].sum()
            total_turnover = sh_turnover + sz_turnover
            stock_count = len(df_sh) + len(df_sz)
            
            logger.info(f"沪市：{sh_turnover/100000000:.2f}亿，深市：{sz_turnover/100000000:.2f}亿")
            
            # 保存到数据库
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


# SQLAlchemy 模型
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class MarketTurnover(Base):
    """市场成交额历史表"""
    __tablename__ = 'market_turnover'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_date = Column(String(8), unique=True, nullable=False, index=True)
    sh_turnover = Column(Float, nullable=False)
    sz_turnover = Column(Float, nullable=False)
    total_turnover = Column(Float, nullable=False)
    stock_count = Column(Integer, default=0)
    created_at = Column(String, default=datetime.now().isoformat)
    updated_at = Column(String, default=datetime.now().isoformat, onupdate=datetime.now().isoformat)


# 创建全局实例
market_turnover_service = MarketTurnoverService()

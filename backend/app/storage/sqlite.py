from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Float, Integer, DateTime, Text, Boolean, UniqueConstraint, Index
from datetime import datetime
from typing import Optional, AsyncGenerator
from pathlib import Path
from contextlib import asynccontextmanager

from app.config import settings


class Base(DeclarativeBase):
    pass


class StockInfo(Base):
    __tablename__ = "stock_info"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    market: Mapped[str] = mapped_column(String(10))
    industry: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    sector: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    area: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    list_date: Mapped[Optional[str]] = mapped_column(String(20))
    total_shares: Mapped[Optional[float]] = mapped_column(Float)
    float_shares: Mapped[Optional[float]] = mapped_column(Float)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        # 复合索引优化查询性能
        Index("idx_stock_industry_market", "industry", "market"),
        Index("idx_stock_sector_market", "sector", "market"),
    )


class KLine(Base):
    __tablename__ = "kline"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    date: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    volume: Mapped[float] = mapped_column(Float)
    amount: Mapped[Optional[float]] = mapped_column(Float)
    turnover_rate: Mapped[Optional[float]] = mapped_column(Float)
    adjust_type: Mapped[str] = mapped_column(String(10), default="qfq")
    
    __table_args__ = (
        UniqueConstraint("code", "date", "adjust_type", name="u_kline_code_date"),
        # 复合索引优化查询性能
        Index("idx_kline_code_date", "code", "date"),
        Index("idx_kline_code_adjust", "code", "adjust_type"),
    )


class TechnicalIndicatorDB(Base):
    __tablename__ = "technical_indicators"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    date: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    ma5: Mapped[Optional[float]] = mapped_column(Float)
    ma10: Mapped[Optional[float]] = mapped_column(Float)
    ma20: Mapped[Optional[float]] = mapped_column(Float)
    ma60: Mapped[Optional[float]] = mapped_column(Float)
    rsi6: Mapped[Optional[float]] = mapped_column(Float)
    rsi12: Mapped[Optional[float]] = mapped_column(Float)
    rsi24: Mapped[Optional[float]] = mapped_column(Float)
    macd: Mapped[Optional[float]] = mapped_column(Float)
    macd_signal: Mapped[Optional[float]] = mapped_column(Float)
    macd_hist: Mapped[Optional[float]] = mapped_column(Float)
    
    __table_args__ = (
        UniqueConstraint("code", "date", name="u_indicator_code_date"),
        # 复合索引优化查询性能
        Index("idx_indicator_code_date", "code", "date"),
        Index("idx_indicator_ma", "code", "ma5", "ma10", "ma20"),
    )


class WatchlistDB(Base):
    __tablename__ = "watchlist"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    note: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class ChipData(Base):
    __tablename__ = "chip_data"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    date: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    shareholder_count: Mapped[Optional[float]] = mapped_column(Float)
    avg_shares_per_holder: Mapped[Optional[float]] = mapped_column(Float)
    control_degree: Mapped[Optional[float]] = mapped_column(Float)
    concentration: Mapped[Optional[float]] = mapped_column(Float)
    
    __table_args__ = (
        UniqueConstraint("code", "date", name="u_chip_code_date"),
    )


class SectorInfo(Base):
    __tablename__ = "sector_info"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    sector_type: Mapped[str] = mapped_column(String(20))
    change_pct: Mapped[Optional[float]] = mapped_column(Float)
    volume: Mapped[Optional[float]] = mapped_column(Float)
    amount: Mapped[Optional[float]] = mapped_column(Float)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class Strategy(Base):
    __tablename__ = "strategy"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    strategy_type: Mapped[str] = mapped_column(String(50))
    config: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class BacktestRecord(Base):
    __tablename__ = "backtest_record"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    backtest_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    strategy_id: Mapped[str] = mapped_column(String(50))
    start_date: Mapped[str] = mapped_column(String(20))
    end_date: Mapped[str] = mapped_column(String(20))
    initial_capital: Mapped[float] = mapped_column(Float)
    final_capital: Mapped[Optional[float]] = mapped_column(Float)
    total_return: Mapped[Optional[float]] = mapped_column(Float)
    annual_return: Mapped[Optional[float]] = mapped_column(Float)
    max_drawdown: Mapped[Optional[float]] = mapped_column(Float)
    sharpe_ratio: Mapped[Optional[float]] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    result_path: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class TradeRecord(Base):
    __tablename__ = "trade_record"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    backtest_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    trade_type: Mapped[str] = mapped_column(String(10))
    code: Mapped[str] = mapped_column(String(10))
    price: Mapped[float] = mapped_column(Float)
    quantity: Mapped[float] = mapped_column(Float)
    amount: Mapped[float] = mapped_column(Float)
    commission: Mapped[float] = mapped_column(Float, default=0)
    trade_date: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        Index("idx_user_username_email", "username", "email"),
    )


engine = None
async_session_maker = None


async def init_database():
    global engine, async_session_maker
    
    db_path = Path(settings.SQLITE_DIR)
    db_path.mkdir(parents=True, exist_ok=True)
    
    db_file = db_path / "quant.db"
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_file}",
        echo=settings.DEBUG
    )

    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    # 只创建表结构，不删除现有数据
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
    global async_session_maker
    if async_session_maker is None:
        await init_database()
    
    async with async_session_maker() as session:
        yield session

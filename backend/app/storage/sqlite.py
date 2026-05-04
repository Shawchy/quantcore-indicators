from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Float, Integer, DateTime, Text, Boolean, UniqueConstraint, Index, select
from datetime import datetime
from typing import Optional, AsyncGenerator
from pathlib import Path
from contextlib import asynccontextmanager
from loguru import logger

from app.config import settings


class Base(DeclarativeBase):
    pass


class StockInfo(Base):
    __tablename__ = "stock_info"
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 基本信息
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    market: Mapped[str] = mapped_column(String(10))
    
    # 证券类型（1：股票，2：指数，3：其它，4：可转债，5：ETF）
    type: Mapped[Optional[int]] = mapped_column(Integer, default=1, index=True)
    
    # 上市状态（1：上市，0：退市）
    status: Mapped[Optional[int]] = mapped_column(Integer, default=1, index=True)
    
    # 上市/退市日期
    list_date: Mapped[Optional[str]] = mapped_column(String(20))
    delist_date: Mapped[Optional[str]] = mapped_column(String(20))
    
    # 行业/板块/地区
    industry: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    sector: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    area: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    
    # 股本信息（单位：股）
    total_shares: Mapped[Optional[float]] = mapped_column(Float)
    float_shares: Mapped[Optional[float]] = mapped_column(Float)
    
    # 更新时间
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
    volume: Mapped[float] = mapped_column(Float, index=True)  # 新增索引
    amount: Mapped[Optional[float]] = mapped_column(Float)
    turnover_rate: Mapped[Optional[float]] = mapped_column(Float, index=True)  # 新增索引
    pre_close: Mapped[Optional[float]] = mapped_column(Float)  # 昨日收盘价
    adjust_type: Mapped[str] = mapped_column(String(10), default="qfq")
    
    __table_args__ = (
        UniqueConstraint("code", "date", "adjust_type", name="u_kline_code_date"),
        # 复合索引优化查询性能
        Index("idx_kline_code_date", "code", "date"),
        Index("idx_kline_code_adjust", "code", "adjust_type"),
        # 新增复合索引
        Index("idx_kline_volume_date", "volume", "date"),  # 成交量排序
        Index("idx_kline_turnover_date", "turnover_rate", "date"),  # 换手率排序
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
    rsi6: Mapped[Optional[float]] = mapped_column(Float, index=True)  # 新增索引
    rsi12: Mapped[Optional[float]] = mapped_column(Float)
    rsi24: Mapped[Optional[float]] = mapped_column(Float)
    macd: Mapped[Optional[float]] = mapped_column(Float, index=True)  # 新增索引
    macd_signal: Mapped[Optional[float]] = mapped_column(Float)
    macd_hist: Mapped[Optional[float]] = mapped_column(Float)
    
    __table_args__ = (
        UniqueConstraint("code", "date", name="u_indicator_code_date"),
        # 复合索引优化查询性能
        Index("idx_indicator_code_date", "code", "date"),
        Index("idx_indicator_ma", "code", "ma5", "ma10", "ma20"),
        # 新增复合索引
        Index("idx_indicator_macd", "code", "macd", "macd_signal"),  # MACD 选股
        Index("idx_indicator_rsi", "code", "rsi6"),  # RSI 选股
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
    shareholder_count: Mapped[Optional[float]] = mapped_column(Float, index=True)  # 新增索引
    avg_shares_per_holder: Mapped[Optional[float]] = mapped_column(Float)
    control_degree: Mapped[Optional[float]] = mapped_column(Float)
    concentration: Mapped[Optional[float]] = mapped_column(Float, index=True)  # 新增索引
    
    __table_args__ = (
        UniqueConstraint("code", "date", name="u_chip_code_date"),
        # 新增复合索引
        Index("idx_chip_concentration_date", "concentration", "date"),  # 集中度排序
    )


class SectorInfo(Base):
    __tablename__ = "sector_info"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    sector_type: Mapped[str] = mapped_column(String(20), index=True)  # 添加索引
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
    code: Mapped[str] = mapped_column(String(10), index=True)  # 新增索引
    price: Mapped[float] = mapped_column(Float)
    quantity: Mapped[float] = mapped_column(Float)
    amount: Mapped[float] = mapped_column(Float)
    commission: Mapped[float] = mapped_column(Float, default=0)
    trade_date: Mapped[str] = mapped_column(String(20), index=True)  # 新增索引
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    __table_args__ = (
        # 新增复合索引
        Index("idx_trade_backtest_date", "backtest_id", "trade_date"),  # 回测时间分布
        Index("idx_trade_code_date", "code", "trade_date"),  # 个股交易历史
    )


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


class RealtimeQuote(Base):
    __tablename__ = "realtime_quote"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    price: Mapped[float] = mapped_column(Float)  # 最新价
    change: Mapped[float] = mapped_column(Float)  # 涨跌额
    change_pct: Mapped[float] = mapped_column(Float)  # 涨跌幅
    volume: Mapped[float] = mapped_column(Float)  # 成交量
    amount: Mapped[float] = mapped_column(Float)  # 成交额
    high: Mapped[float] = mapped_column(Float)  # 最高价
    low: Mapped[float] = mapped_column(Float)  # 最低价
    open: Mapped[float] = mapped_column(Float)  # 今开
    prev_close: Mapped[float] = mapped_column(Float)  # 昨收
    turnover_rate: Mapped[Optional[float]] = mapped_column(Float)  # 换手率
    quote_time: Mapped[str] = mapped_column(String(20), index=True)  # 行情时间
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        # 唯一约束：每只股票只有一个最新行情
        UniqueConstraint("code", name="u_quote_code"),
        # 复合索引优化查询性能
        Index("idx_quote_code_time", "code", "quote_time"),
        Index("idx_quote_change_pct", "change_pct"),  # 涨跌幅排行
        Index("idx_quote_volume", "volume"),  # 成交量排行
    )


class MarketRanking(Base):
    __tablename__ = "market_ranking"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ranking_date: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    ranking_time: Mapped[str] = mapped_column(String(20), nullable=False)
    ts_code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    price: Mapped[float] = mapped_column(Float)
    change: Mapped[float] = mapped_column(Float)
    change_pct: Mapped[float] = mapped_column(Float, index=True)
    volume: Mapped[float] = mapped_column(Float)
    amount: Mapped[float] = mapped_column(Float)
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    prev_close: Mapped[float] = mapped_column(Float)
    turnover_rate: Mapped[Optional[float]] = mapped_column(Float)
    ranking_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    rank_position: Mapped[int] = mapped_column(Integer, index=True)
    data_source: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    __table_args__ = (
        UniqueConstraint("ranking_date", "ranking_type", "ts_code", name="u_ranking_date_type_code"),
        Index("idx_ranking_date_type", "ranking_date", "ranking_type"),
        Index("idx_ranking_date_position", "ranking_date", "rank_position"),
        Index("idx_ranking_code_date", "ts_code", "ranking_date"),
    )


class MarketTurnover(Base):
    __tablename__ = "market_turnover"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trade_date: Mapped[str] = mapped_column(String(8), unique=True, nullable=False, index=True)
    sh_turnover: Mapped[float] = mapped_column(Float, nullable=False)
    sz_turnover: Mapped[float] = mapped_column(Float, nullable=False)
    total_turnover: Mapped[float] = mapped_column(Float, nullable=False)
    stock_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


# ========== 从 local_database.py 迁移的独有ORM模型 ==========

class FundBasic(Base):
    """基金基本信息表"""
    __tablename__ = 'fund_basic'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100))
    fund_type: Mapped[str] = mapped_column(String(50))
    manager: Mapped[str] = mapped_column(String(50))
    company: Mapped[str] = mapped_column(String(100))
    establish_date: Mapped[str] = mapped_column(String(20))
    fund_size: Mapped[float] = mapped_column(Float)
    management_fee: Mapped[float] = mapped_column(Float)
    custody_fee: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class FundNAV(Base):
    """基金净值数据表"""
    __tablename__ = 'fund_nav'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    date: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    nav: Mapped[float] = mapped_column(Float)
    accumulated_nav: Mapped[float] = mapped_column(Float)
    nav_change: Mapped[float] = mapped_column(Float)
    nav_growth: Mapped[float] = mapped_column(Float)
    discount_rate: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class FundHolding(Base):
    """基金持仓数据表"""
    __tablename__ = 'fund_holding'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    report_date: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    stock_code: Mapped[str] = mapped_column(String(10), nullable=False)
    stock_name: Mapped[str] = mapped_column(String(50))
    holding_volume: Mapped[float] = mapped_column(Float)
    holding_amount: Mapped[float] = mapped_column(Float)
    holding_ratio: Mapped[float] = mapped_column(Float)
    stock_rank: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class FundAssetAllocation(Base):
    """基金资产配置表"""
    __tablename__ = 'fund_asset_allocation'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    report_date: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    stock_ratio: Mapped[float] = mapped_column(Float)
    bond_ratio: Mapped[float] = mapped_column(Float)
    cash_ratio: Mapped[float] = mapped_column(Float)
    other_ratio: Mapped[float] = mapped_column(Float)
    total_asset: Mapped[float] = mapped_column(Float)
    net_asset: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class StockKlineWeekly(Base):
    """周线 K 线数据表"""
    __tablename__ = 'stock_kline_weekly'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    date: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    volume: Mapped[float] = mapped_column(Float)
    amount: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class StockKlineMonthly(Base):
    """月线 K 线数据表"""
    __tablename__ = 'stock_kline_monthly'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    date: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    volume: Mapped[float] = mapped_column(Float)
    amount: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class StockBillboard(Base):
    """龙虎榜数据表"""
    __tablename__ = 'stock_billboard'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50))
    trade_date: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    close_price: Mapped[float] = mapped_column(Float)
    change_pct: Mapped[float] = mapped_column(Float)
    turnover_ratio: Mapped[float] = mapped_column(Float)
    buy_amount: Mapped[float] = mapped_column(Float)
    sell_amount: Mapped[float] = mapped_column(Float)
    net_amount: Mapped[float] = mapped_column(Float)
    reason: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class StockMoneyflow(Base):
    """资金流向数据表"""
    __tablename__ = 'stock_moneyflow'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50))
    trade_date: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    main_force_in: Mapped[float] = mapped_column(Float)
    main_force_out: Mapped[float] = mapped_column(Float)
    main_force_net: Mapped[float] = mapped_column(Float)
    super_large_in: Mapped[float] = mapped_column(Float)
    large_in: Mapped[float] = mapped_column(Float)
    medium_in: Mapped[float] = mapped_column(Float)
    small_in: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class StockShareholder(Base):
    """股东信息表"""
    __tablename__ = 'stock_shareholder'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    report_date: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    holder_name: Mapped[str] = mapped_column(String(100))
    holder_type: Mapped[str] = mapped_column(String(50))
    holding_shares: Mapped[float] = mapped_column(Float)
    holding_ratio: Mapped[float] = mapped_column(Float)
    holder_rank: Mapped[int] = mapped_column(Integer)
    change_type: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class StockFinancial(Base):
    """财务数据表"""
    __tablename__ = 'stock_financial'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    report_date: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    report_type: Mapped[str] = mapped_column(String(20))
    eps: Mapped[float] = mapped_column(Float)
    bvps: Mapped[float] = mapped_column(Float)
    roe: Mapped[float] = mapped_column(Float)
    gross_margin: Mapped[float] = mapped_column(Float)
    net_margin: Mapped[float] = mapped_column(Float)
    debt_ratio: Mapped[float] = mapped_column(Float)
    total_revenue: Mapped[float] = mapped_column(Float)
    net_profit: Mapped[float] = mapped_column(Float)
    operating_cash_flow: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class SectorComponent(Base):
    """板块成分股表"""
    __tablename__ = 'sector_components'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sector_code: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    sector_name: Mapped[str] = mapped_column(String(100))
    stock_code: Mapped[str] = mapped_column(String(10), nullable=False)
    stock_name: Mapped[str] = mapped_column(String(50))
    weight: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class RevokedToken(Base):
    """已撤销令牌表"""
    __tablename__ = 'revoked_tokens'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    token_type: Mapped[str] = mapped_column(String(10), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


engine = None
async_session_maker = None


async def init_database():
    global engine, async_session_maker
    
    db_path = Path(settings.SQLITE_DIR)
    db_path.mkdir(parents=True, exist_ok=True)
    
    db_file = db_path / "quant.db"
    
    # 新增：确保数据库文件存在（用于 WAL 模式初始化）
    if not db_file.exists():
        import aiosqlite
        async with aiosqlite.connect(str(db_file)) as db:
            pass
    
    # 创建异步引擎
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_file}",
        echo=settings.DEBUG,
        pool_size=20,  # 增加连接池大小
        max_overflow=20,  # 增加最大溢出连接数
        pool_pre_ping=True,  # 连接前 ping 测试
        pool_recycle=3600,  # 1 小时回收连接
    )
    
    # ✅ 关键优化：添加事件监听器设置 PRAGMA
    from sqlalchemy import event
    
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragmas(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        
        try:
            # 核心性能优化
            cursor.execute("PRAGMA journal_mode = WAL")      # 启用 WAL 模式（最关键！）
            cursor.execute("PRAGMA synchronous = NORMAL")     # 放宽同步策略
            cursor.execute("PRAGMA cache_size = -64000")       # 64MB 缓存（默认仅 2MB）
            cursor.execute("PRAGMA temp_store = MEMORY")       # 临时表放内存
            cursor.execute("PRAGMA mmap_size = 268435456")     # 256MB 内存映射
            
            # 可靠性优化
            cursor.execute("PRAGMA busy_timeout = 5000")       # 5秒忙等待
            cursor.execute("PRAGMA foreign_keys = ON")          # 外键约束
            cursor.execute("PRAGMA wal_autocheckpoint = 1000") # 自动 checkpoint
            
            logger.debug("SQLite PRAGMA 设置完成：WAL模式 + 性能优化")
            
        except Exception as e:
            logger.error(f"设置 SQLite PRAGMA 失败: {e}")
        finally:
            cursor.close()
    
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    # 只创建表结构，不删除现有数据
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # ✅ 验证 WAL 模式是否生效
    from sqlalchemy import text
    async with engine.begin() as conn:
        result = await conn.run_sync(
            lambda conn: conn.execute(text("PRAGMA journal_mode")).fetchone()
        )
        journal_mode = result[0] if result else "unknown"
        
        if journal_mode == "wal":
            logger.success(f"✓ SQLite WAL 模式已启用！journal_mode={journal_mode}")
        else:
            logger.warning(f"⚠ SQLite journal_mode={journal_mode}（非WAL，性能可能受限）")
    
    # 创建默认用户
    await create_default_users()
    
    # 自动检查和同步股票列表
    await auto_sync_stock_list_on_startup()


async def create_default_users():
    """创建默认管理员和用户"""
    from app.core.security import get_password_hash
    
    async with get_session() as session:
        # 检查是否已有 admin 用户
        result = await session.execute(select(User).where(User.username == "admin"))
        if result.scalar_one_or_none():
            return  # 已存在，不重复创建
        
        # 创建 admin 用户
        admin_user = User(
            user_id=1,
            username="admin",
            email="admin@example.com",
            password=get_password_hash(settings.DEFAULT_ADMIN_PASSWORD),
            role="admin",
            is_active=True
        )
        
        # 检查是否已有 user 用户
        result = await session.execute(select(User).where(User.username == "user"))
        if not result.scalar_one_or_none():
            # 创建普通用户
            user_user = User(
                user_id=2,
                username="user",
                email="user@example.com",
                password=get_password_hash(settings.DEFAULT_USER_PASSWORD),
                role="user",
                is_active=True
            )
            session.add(user_user)
        
        session.add(admin_user)
        await session.commit()
        
        if settings.DEBUG:
            logger.info(f"已创建默认用户：admin/{settings.DEFAULT_ADMIN_PASSWORD}, user/{settings.DEFAULT_USER_PASSWORD}")


async def auto_sync_stock_list_on_startup():
    """
    应用启动时自动同步股票列表
    
    检查数据库状态，如果为空或数据过期则自动同步
    """
    try:
        from app.services.stock_list_sync import stock_list_sync
        
        # 检查数据库状态
        status = await stock_list_sync.check_database_status()
        
        logger.info(
            f"启动时检查股票列表：{status['total_count']}只股票，"
            f"最后更新：{status['last_update'] or '从未'}，"
            f"距今：{status['days_since_update'] or 'N/A'}天"
        )
        
        # 如果数据库为空或数据过期，触发同步
        if status['needs_update']:
            logger.warning("股票列表数据过期或为空，触发自动同步...")
            success = await stock_list_sync.auto_sync()
            
            if success:
                logger.info("股票列表自动同步成功")
            else:
                logger.error("股票列表自动同步失败，但应用将继续启动")
        else:
            logger.info("股票列表数据有效，无需同步")
            
    except Exception as e:
        logger.error(f"启动时自动同步股票列表失败：{e}")
        # 不阻塞应用启动


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
    global async_session_maker
    if async_session_maker is None:
        await init_database()
    
    async with async_session_maker() as session:
        yield session


# ✅ 新增：定期 Checkpoint 任务（控制 WAL 文件大小）
async def sqlite_checkpoint_task():
    """
    定期执行 SQLite checkpoint
    
    作用：
    - 将 WAL 日志写入主数据库文件
    - 控制 WAL 文件大小，防止无限增长
    - 建议每 30 分钟执行一次
    """
    global engine
    
    if engine is None:
        logger.warning("数据库未初始化，跳过 checkpoint")
        return
    
    try:
        async with engine.begin() as conn:
            # 执行 TRUNCATE checkpoint（清理 WAL 文件）
            result = await conn.run_sync(
                lambda conn: conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
            )
            
            if result:
                wal_size = result[0] if len(result) > 0 else 0
                logger.debug(f"SQLite checkpoint 完成，WAL 文件大小: {wal_size} 页")
            
    except Exception as e:
        logger.error(f"SQLite checkpoint 失败: {e}")


# ✅ 新增：启动定期 Checkpoint 调度任务
def start_checkpoint_scheduler():
    """启动定期 Checkpoint 后台任务"""
    import asyncio
    
    async def _checkpoint_loop():
        while True:
            try:
                await asyncio.sleep(1800)  # 每 30 分钟执行一次
                await sqlite_checkpoint_task()
            except Exception as e:
                logger.error(f"Checkpoint 调度异常: {e}")
                await asyncio.sleep(60)  # 出错后等待 1 分钟再试
    
    task = asyncio.create_task(_checkpoint_loop())
    logger.info("✓ SQLite 定期 Checkpoint 调度器已启动（每30分钟）")
    return task


# ========== 向后兼容别名 ==========
# 为 local_database.py 等旧代码提供兼容性支持

StockBasic = StockInfo           # 旧名称 StockBasic → 新名称 StockInfo
StockKlineDaily = KLine          # 旧名称 StockKlineDaily → 新名称 KLine
StockQuote = RealtimeQuote       # 旧名称 StockQuote → 新名称 RealtimeQuote

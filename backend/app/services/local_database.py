"""
本地数据库服务

提供本地数据存储和同步功能，减少对实时 API 的依赖
"""
from sqlalchemy import create_engine, Column, String, Float, Integer, Date, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import pandas as pd
from loguru import logger
import asyncio

from app.config import settings

Base = declarative_base()


# ========== 数据库模型 ==========

class StockBasic(Base):
    """股票基本信息表"""
    __tablename__ = 'stock_basic'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), unique=True, index=True, nullable=False)
    name = Column(String(50))
    market = Column(String(10))
    industry = Column(String(100))
    sector = Column(String(100))
    list_date = Column(String(20))
    total_shares = Column(Float)
    float_shares = Column(Float)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class StockKlineDaily(Base):
    """日线 K 线数据表"""
    __tablename__ = 'stock_kline_daily'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), index=True, nullable=False)
    date = Column(String(20), index=True, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    amount = Column(Float)
    turnover_rate = Column(Float)
    pre_close = Column(Float)
    created_at = Column(DateTime, default=datetime.now)
    
    __table_args__ = (
        # 唯一约束：同一只股票同一天只能有一条记录
        {'sqlite_autoincrement': True}
    )


class StockQuote(Base):
    """实时行情快照表"""
    __tablename__ = 'stock_quote'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), index=True, nullable=False)
    name = Column(String(50))
    price = Column(Float)
    change = Column(Float)
    change_pct = Column(Float)
    volume = Column(Float)
    amount = Column(Float)
    high = Column(Float)
    low = Column(Float)
    open = Column(Float)
    prev_close = Column(Float)
    turnover_rate = Column(Float)
    total_market_cap = Column(Float)
    float_market_cap = Column(Float)
    quote_time = Column(DateTime, default=datetime.now)
    created_at = Column(DateTime, default=datetime.now)


class SectorInfo(Base):
    """板块信息表"""
    __tablename__ = 'sector_info'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100))
    sector_type = Column(String(20))  # industry/concept
    change_pct = Column(Float)
    volume = Column(Float)
    amount = Column(Float)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class FundBasic(Base):
    """基金基本信息表"""
    __tablename__ = 'fund_basic'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), unique=True, index=True, nullable=False)
    name = Column(String(100))
    fund_type = Column(String(50))  # 基金类型：股票型/债券型/混合型/ETF 等
    manager = Column(String(50))  # 基金经理
    company = Column(String(100))  # 基金公司
    establish_date = Column(String(20))  # 成立日期
    fund_size = Column(Float)  # 基金规模（亿元）
    management_fee = Column(Float)  # 管理费率
    custody_fee = Column(Float)  # 托管费率
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class FundNAV(Base):
    """基金净值数据表"""
    __tablename__ = 'fund_nav'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), index=True, nullable=False)
    date = Column(String(20), index=True, nullable=False)
    nav = Column(Float)  # 单位净值
    accumulated_nav = Column(Float)  # 累计净值
    nav_change = Column(Float)  # 净值增长额
    nav_growth = Column(Float)  # 净值增长率
    discount_rate = Column(Float)  # 折溢价率（ETF/LOF）
    created_at = Column(DateTime, default=datetime.now)
    
    __table_args__ = (
        # 唯一约束：同一只基金同一天只能有一条记录
        {'sqlite_autoincrement': True}
    )


class FundHolding(Base):
    """基金持仓数据表"""
    __tablename__ = 'fund_holding'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), index=True, nullable=False)
    report_date = Column(String(20), index=True, nullable=False)  # 报告期
    stock_code = Column(String(10), nullable=False)  # 持仓股票代码
    stock_name = Column(String(50))  # 持仓股票名称
    holding_volume = Column(Float)  # 持仓数量（股）
    holding_amount = Column(Float)  # 持仓金额（元）
    holding_ratio = Column(Float)  # 占净值比例（%）
    stock_rank = Column(Integer)  # 持仓排名（1-10）
    created_at = Column(DateTime, default=datetime.now)
    
    __table_args__ = (
        # 唯一约束
        {'sqlite_autoincrement': True}
    )


class FundAssetAllocation(Base):
    """基金资产配置表"""
    __tablename__ = 'fund_asset_allocation'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), index=True, nullable=False)
    report_date = Column(String(20), index=True, nullable=False)  # 报告期
    stock_ratio = Column(Float)  # 股票投资比例（%）
    bond_ratio = Column(Float)  # 债券投资比例（%）
    cash_ratio = Column(Float)  # 货币资金比例（%）
    other_ratio = Column(Float)  # 其他资产比例（%）
    total_asset = Column(Float)  # 总资产（亿元）
    net_asset = Column(Float)  # 净资产（亿元）
    created_at = Column(DateTime, default=datetime.now)


class StockKlineWeekly(Base):
    """周线 K 线数据表"""
    __tablename__ = 'stock_kline_weekly'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), index=True, nullable=False)
    date = Column(String(20), index=True, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    amount = Column(Float)
    created_at = Column(DateTime, default=datetime.now)


class StockKlineMonthly(Base):
    """月线 K 线数据表"""
    __tablename__ = 'stock_kline_monthly'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), index=True, nullable=False)
    date = Column(String(20), index=True, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    amount = Column(Float)
    created_at = Column(DateTime, default=datetime.now)


class StockBillboard(Base):
    """龙虎榜数据表"""
    __tablename__ = 'stock_billboard'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), index=True, nullable=False)
    name = Column(String(50))
    trade_date = Column(String(20), index=True, nullable=False)
    close_price = Column(Float)
    change_pct = Column(Float)
    turnover_ratio = Column(Float)
    buy_amount = Column(Float)  # 买入总额
    sell_amount = Column(Float)  # 卖出总额
    net_amount = Column(Float)  # 净额
    reason = Column(String(200))  # 上榜原因
    created_at = Column(DateTime, default=datetime.now)


class StockMoneyflow(Base):
    """资金流向数据表"""
    __tablename__ = 'stock_moneyflow'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), index=True, nullable=False)
    name = Column(String(50))
    trade_date = Column(String(20), index=True, nullable=False)
    main_force_in = Column(Float)  # 主力流入
    main_force_out = Column(Float)  # 主力流出
    main_force_net = Column(Float)  # 主力净额
    super_large_in = Column(Float)  # 超大单流入
    large_in = Column(Float)  # 大单流入
    medium_in = Column(Float)  # 中单流入
    small_in = Column(Float)  # 小单流入
    created_at = Column(DateTime, default=datetime.now)


class StockShareholder(Base):
    """股东信息表"""
    __tablename__ = 'stock_shareholder'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), index=True, nullable=False)
    report_date = Column(String(20), index=True, nullable=False)  # 报告期
    holder_name = Column(String(100))  # 股东名称
    holder_type = Column(String(50))  # 股东类型（流通股东/十大股东）
    holding_shares = Column(Float)  # 持股数量
    holding_ratio = Column(Float)  # 持股比例（%）
    holder_rank = Column(Integer)  # 股东排名
    change_type = Column(String(20))  # 增减类型（增持/减持/新进）
    created_at = Column(DateTime, default=datetime.now)


class StockFinancial(Base):
    """财务数据表"""
    __tablename__ = 'stock_financial'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), index=True, nullable=False)
    report_date = Column(String(20), index=True, nullable=False)  # 报告期
    report_type = Column(String(20))  # 报告类型（年报/季报）
    eps = Column(Float)  # 每股收益
    bvps = Column(Float)  # 每股净资产
    roe = Column(Float)  # 净资产收益率
    gross_margin = Column(Float)  # 销售毛利率
    net_margin = Column(Float)  # 销售净利率
    debt_ratio = Column(Float)  # 资产负债率
    total_revenue = Column(Float)  # 营业总收入
    net_profit = Column(Float)  # 净利润
    operating_cash_flow = Column(Float)  # 经营现金流
    created_at = Column(DateTime, default=datetime.now)


class SectorComponent(Base):
    """板块成分股表"""
    __tablename__ = 'sector_components'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sector_code = Column(String(20), index=True, nullable=False)
    sector_name = Column(String(100))
    stock_code = Column(String(10), nullable=False)
    stock_name = Column(String(50))
    weight = Column(Float)  # 权重（%）
    created_at = Column(DateTime, default=datetime.now)


# ========== 本地数据库服务 ==========

class LocalDatabaseService:
    """本地数据库服务类"""
    
    def __init__(self):
        self.db_path = settings.SQLITE_DIR
        self.engine = None
        self.SessionLocal = None
        self._initialized = False
    
    async def initialize(self) -> bool:
        """初始化数据库连接和表"""
        try:
            import os
            os.makedirs(self.db_path, exist_ok=True)
            
            db_file = f"{self.db_path}/quant.db"
            logger.info(f"初始化本地数据库：{db_file}")
            
            # 创建数据库引擎
            self.engine = create_engine(
                f"sqlite:///{db_file}",
                echo=False,
                poolclass=StaticPool,
                connect_args={"timeout": 30}
            )
            
            # 创建所有表
            Base.metadata.create_all(self.engine)
            
            # 创建会话工厂
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            self._initialized = True
            logger.info("本地数据库初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"本地数据库初始化失败：{e}")
            return False
    
    def get_session(self):
        """获取数据库会话"""
        if not self._initialized:
            raise RuntimeError("数据库未初始化，请先调用 initialize()")
        return self.SessionLocal()
    
    async def sync_stock_list(self, stock_list: List[Any]) -> int:
        """
        同步股票列表到本地数据库
        
        Args:
            stock_list: 股票列表，每个元素包含 code, name, market 等字段
            
        Returns:
            同步的股票数量
        """
        if not self._initialized:
            logger.error("数据库未初始化")
            return 0
        
        try:
            session = self.get_session()
            count = 0
            
            for stock in stock_list:
                # 检查是否已存在
                existing = session.query(StockBasic).filter(
                    StockBasic.code == stock.code
                ).first()
                
                if existing:
                    # 更新
                    existing.name = stock.name
                    existing.market = stock.market
                    existing.industry = getattr(stock, 'industry', None)
                    existing.sector = getattr(stock, 'sector', None)
                    existing.list_date = getattr(stock, 'list_date', None)
                    existing.total_shares = getattr(stock, 'total_shares', None)
                    existing.float_shares = getattr(stock, 'float_shares', None)
                else:
                    # 插入
                    new_stock = StockBasic(
                        code=stock.code,
                        name=stock.name,
                        market=stock.market,
                        industry=getattr(stock, 'industry', None),
                        sector=getattr(stock, 'sector', None),
                        list_date=getattr(stock, 'list_date', None),
                        total_shares=getattr(stock, 'total_shares', None),
                        float_shares=getattr(stock, 'float_shares', None)
                    )
                    session.add(new_stock)
                
                count += 1
            
            session.commit()
            logger.info(f"同步股票列表成功：{count}只股票")
            return count
            
        except Exception as e:
            logger.error(f"同步股票列表失败：{e}")
            session.rollback()
            return 0
        finally:
            session.close()
    
    async def sync_kline_data(
        self,
        code: str,
        kline_data: List[Any],
        period: str = 'daily'
    ) -> int:
        """
        同步 K 线数据到本地数据库
        
        Args:
            code: 股票代码
            kline_data: K 线数据列表
            period: K 线周期（daily/weekly/monthly）
            
        Returns:
            同步的数据条数
        """
        if not self._initialized:
            logger.error("数据库未初始化")
            return 0
        
        try:
            session = self.get_session()
            count = 0
            
            for kline in kline_data:
                # 检查是否已存在
                existing = session.query(StockKlineDaily).filter(
                    StockKlineDaily.code == code,
                    StockKlineDaily.date == kline.date
                ).first()
                
                if existing:
                    # 更新
                    existing.open = kline.open
                    existing.high = kline.high
                    existing.low = kline.low
                    existing.close = kline.close
                    existing.volume = kline.volume
                    existing.amount = kline.amount
                    existing.turnover_rate = kline.turnover_rate
                    existing.pre_close = kline.pre_close
                else:
                    # 插入
                    new_kline = StockKlineDaily(
                        code=code,
                        date=kline.date,
                        open=kline.open,
                        high=kline.high,
                        low=kline.low,
                        close=kline.close,
                        volume=kline.volume,
                        amount=kline.amount,
                        turnover_rate=kline.turnover_rate,
                        pre_close=kline.pre_close
                    )
                    session.add(new_kline)
                
                count += 1
            
            session.commit()
            logger.info(f"同步 K 线数据成功 {code}: {count}条")
            return count
            
        except Exception as e:
            logger.error(f"同步 K 线数据失败 {code}: {e}")
            session.rollback()
            return 0
        finally:
            session.close()
    
    async def sync_quote_data(self, quotes: List[Dict[str, Any]]) -> int:
        """
        同步实时行情数据到本地数据库
        
        Args:
            quotes: 行情数据列表，每个元素是字典
            
        Returns:
            同步的数据条数
        """
        if not self._initialized:
            logger.error("数据库未初始化")
            return 0
        
        try:
            session = self.get_session()
            count = 0
            
            for quote_data in quotes:
                code = quote_data.get('code')
                if not code:
                    continue
                
                # 删除旧数据（保留最新）
                session.query(StockQuote).filter(
                    StockQuote.code == code
                ).delete()
                
                # 插入新数据
                new_quote = StockQuote(
                    code=code,
                    name=quote_data.get('name', ''),
                    price=quote_data.get('price', 0),
                    change=quote_data.get('change', 0),
                    change_pct=quote_data.get('change_pct', 0),
                    volume=quote_data.get('volume', 0),
                    amount=quote_data.get('amount', 0),
                    high=quote_data.get('high', 0),
                    low=quote_data.get('low', 0),
                    open=quote_data.get('open', 0),
                    prev_close=quote_data.get('prev_close', 0),
                    turnover_rate=quote_data.get('turnover_rate', 0),
                    total_market_cap=quote_data.get('total_market_cap', 0),
                    float_market_cap=quote_data.get('float_market_cap', 0),
                    quote_time=datetime.now()
                )
                session.add(new_quote)
                count += 1
            
            session.commit()
            logger.info(f"同步实时行情成功：{count}条")
            return count
            
        except Exception as e:
            logger.error(f"同步实时行情失败：{e}")
            session.rollback()
            return 0
        finally:
            session.close()
    
    async def get_stock_list_from_db(self) -> List[StockBasic]:
        """从本地数据库获取股票列表"""
        if not self._initialized:
            return []
        
        try:
            session = self.get_session()
            stocks = session.query(StockBasic).all()
            return stocks
        except Exception as e:
            logger.error(f"从数据库获取股票列表失败：{e}")
            return []
        finally:
            session.close()
    
    async def get_kline_from_db(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[StockKlineDaily]:
        """从本地数据库获取 K 线数据"""
        if not self._initialized:
            return []
        
        try:
            session = self.get_session()
            query = session.query(StockKlineDaily).filter(
                StockKlineDaily.code == code
            )
            
            if start_date:
                query = query.filter(StockKlineDaily.date >= start_date)
            if end_date:
                query = query.filter(StockKlineDaily.date <= end_date)
            
            klines = query.order_by(StockKlineDaily.date).all()
            return klines
        except Exception as e:
            logger.error(f"从数据库获取 K 线数据失败 {code}: {e}")
            return []
        finally:
            session.close()
    
    async def get_quote_from_db(self, code: str) -> Optional[StockQuote]:
        """从本地数据库获取实时行情"""
        if not self._initialized:
            return None
        
        try:
            session = self.get_session()
            quote = session.query(StockQuote).filter(
                StockQuote.code == code
            ).order_by(StockQuote.quote_time.desc()).first()
            return quote
        except Exception as e:
            logger.error(f"从数据库获取行情失败 {code}: {e}")
            return None
        finally:
            session.close()
    
    # ========== 基金相关方法 ==========
    
    async def sync_fund_list(self, fund_list: List[Any]) -> int:
        """
        同步基金列表到本地数据库
        
        Args:
            fund_list: 基金列表，每个元素包含 code, name, fund_type 等字段
            
        Returns:
            同步的基金数量
        """
        if not self._initialized:
            logger.error("数据库未初始化")
            return 0
        
        try:
            session = self.get_session()
            count = 0
            
            for fund in fund_list:
                # 检查是否已存在
                existing = session.query(FundBasic).filter(
                    FundBasic.code == fund.code
                ).first()
                
                if existing:
                    # 更新
                    existing.name = fund.name
                    existing.fund_type = getattr(fund, 'fund_type', None)
                    existing.manager = getattr(fund, 'manager', None)
                    existing.company = getattr(fund, 'company', None)
                    existing.establish_date = getattr(fund, 'establish_date', None)
                    existing.fund_size = getattr(fund, 'fund_size', None)
                    existing.management_fee = getattr(fund, 'management_fee', None)
                    existing.custody_fee = getattr(fund, 'custody_fee', None)
                else:
                    # 插入
                    new_fund = FundBasic(
                        code=fund.code,
                        name=fund.name,
                        fund_type=getattr(fund, 'fund_type', None),
                        manager=getattr(fund, 'manager', None),
                        company=getattr(fund, 'company', None),
                        establish_date=getattr(fund, 'establish_date', None),
                        fund_size=getattr(fund, 'fund_size', None),
                        management_fee=getattr(fund, 'management_fee', None),
                        custody_fee=getattr(fund, 'custody_fee', None)
                    )
                    session.add(new_fund)
                
                count += 1
            
            session.commit()
            logger.info(f"同步基金列表成功：{count}只基金")
            return count
            
        except Exception as e:
            logger.error(f"同步基金列表失败：{e}")
            session.rollback()
            return 0
        finally:
            session.close()
    
    async def sync_fund_nav(self, code: str, nav_data: List[Any]) -> int:
        """
        同步基金净值数据到本地数据库
        
        Args:
            code: 基金代码
            nav_data: 净值数据列表
            
        Returns:
            同步的数据条数
        """
        if not self._initialized:
            logger.error("数据库未初始化")
            return 0
        
        try:
            session = self.get_session()
            count = 0
            
            for nav in nav_data:
                # 检查是否已存在
                existing = session.query(FundNAV).filter(
                    FundNAV.code == code,
                    FundNAV.date == nav.date
                ).first()
                
                if existing:
                    # 更新
                    existing.nav = nav.nav
                    existing.accumulated_nav = nav.accumulated_nav
                    existing.nav_change = nav.nav_change
                    existing.nav_growth = nav.nav_growth
                    existing.discount_rate = nav.discount_rate
                else:
                    # 插入
                    new_nav = FundNAV(
                        code=code,
                        date=nav.date,
                        nav=nav.nav,
                        accumulated_nav=nav.accumulated_nav,
                        nav_change=nav.nav_change,
                        nav_growth=nav.nav_growth,
                        discount_rate=nav.discount_rate
                    )
                    session.add(new_nav)
                
                count += 1
            
            session.commit()
            logger.info(f"同步基金净值成功 {code}: {count}条")
            return count
            
        except Exception as e:
            logger.error(f"同步基金净值失败 {code}: {e}")
            session.rollback()
            return 0
        finally:
            session.close()
    
    async def sync_fund_holding(self, code: str, report_date: str, holdings: List[Any]) -> int:
        """
        同步基金持仓数据到本地数据库
        
        Args:
            code: 基金代码
            report_date: 报告期
            holdings: 持仓数据列表
            
        Returns:
            同步的数据条数
        """
        if not self._initialized:
            logger.error("数据库未初始化")
            return 0
        
        try:
            session = self.get_session()
            count = 0
            
            # 删除该报告期的旧数据
            session.query(FundHolding).filter(
                FundHolding.code == code,
                FundHolding.report_date == report_date
            ).delete()
            
            for holding in holdings:
                new_holding = FundHolding(
                    code=code,
                    report_date=report_date,
                    stock_code=holding.stock_code,
                    stock_name=holding.stock_name,
                    holding_volume=holding.holding_volume,
                    holding_amount=holding.holding_amount,
                    holding_ratio=holding.holding_ratio,
                    stock_rank=holding.stock_rank
                )
                session.add(new_holding)
                count += 1
            
            session.commit()
            logger.info(f"同步基金持仓成功 {code} ({report_date}): {count}条")
            return count
            
        except Exception as e:
            logger.error(f"同步基金持仓失败 {code}: {e}")
            session.rollback()
            return 0
        finally:
            session.close()
    
    async def get_fund_list_from_db(self) -> List[FundBasic]:
        """从本地数据库获取基金列表"""
        if not self._initialized:
            return []
        
        try:
            session = self.get_session()
            funds = session.query(FundBasic).all()
            return funds
        except Exception as e:
            logger.error(f"从数据库获取基金列表失败：{e}")
            return []
        finally:
            session.close()
    
    async def get_fund_nav_from_db(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[FundNAV]:
        """从本地数据库获取基金净值数据"""
        if not self._initialized:
            return []
        
        try:
            session = self.get_session()
            query = session.query(FundNAV).filter(
                FundNAV.code == code
            )
            
            if start_date:
                query = query.filter(FundNAV.date >= start_date)
            if end_date:
                query = query.filter(FundNAV.date <= end_date)
            
            nav_list = query.order_by(FundNAV.date).all()
            return nav_list
        except Exception as e:
            logger.error(f"从数据库获取基金净值失败 {code}: {e}")
            return []
        finally:
            session.close()
    
    async def get_fund_holding_from_db(
        self,
        code: str,
        report_date: Optional[str] = None
    ) -> List[FundHolding]:
        """从本地数据库获取基金持仓数据"""
        if not self._initialized:
            return []
        
        try:
            session = self.get_session()
            query = session.query(FundHolding).filter(
                FundHolding.code == code
            )
            
            if report_date:
                query = query.filter(FundHolding.report_date == report_date)
            
            holdings = query.order_by(FundHolding.stock_rank).all()
            return holdings
        except Exception as e:
            logger.error(f"从数据库获取基金持仓失败 {code}: {e}")
            return []
        finally:
            session.close()
    
    # ========== 周月线 K 线相关方法 ==========
    
    async def sync_kline_weekly(self, code: str, kline_data: List[Any]) -> int:
        """同步周线 K 线数据"""
        if not self._initialized:
            return 0
        
        try:
            session = self.get_session()
            count = 0
            
            for kline in kline_data:
                existing = session.query(StockKlineWeekly).filter(
                    StockKlineWeekly.code == code,
                    StockKlineWeekly.date == kline.date
                ).first()
                
                if existing:
                    existing.open = kline.open
                    existing.high = kline.high
                    existing.low = kline.low
                    existing.close = kline.close
                    existing.volume = kline.volume
                    existing.amount = kline.amount
                else:
                    new_kline = StockKlineWeekly(
                        code=code,
                        date=kline.date,
                        open=kline.open,
                        high=kline.high,
                        low=kline.low,
                        close=kline.close,
                        volume=kline.volume,
                        amount=kline.amount
                    )
                    session.add(new_kline)
                count += 1
            
            session.commit()
            logger.info(f"同步周线 K 线成功 {code}: {count}条")
            return count
        except Exception as e:
            logger.error(f"同步周线 K 线失败 {code}: {e}")
            session.rollback()
            return 0
        finally:
            session.close()
    
    async def sync_kline_monthly(self, code: str, kline_data: List[Any]) -> int:
        """同步月线 K 线数据"""
        if not self._initialized:
            return 0
        
        try:
            session = self.get_session()
            count = 0
            
            for kline in kline_data:
                existing = session.query(StockKlineMonthly).filter(
                    StockKlineMonthly.code == code,
                    StockKlineMonthly.date == kline.date
                ).first()
                
                if existing:
                    existing.open = kline.open
                    existing.high = kline.high
                    existing.low = kline.low
                    existing.close = kline.close
                    existing.volume = kline.volume
                    existing.amount = kline.amount
                else:
                    new_kline = StockKlineMonthly(
                        code=code,
                        date=kline.date,
                        open=kline.open,
                        high=kline.high,
                        low=kline.low,
                        close=kline.close,
                        volume=kline.volume,
                        amount=kline.amount
                    )
                    session.add(new_kline)
                count += 1
            
            session.commit()
            logger.info(f"同步月线 K 线成功 {code}: {count}条")
            return count
        except Exception as e:
            logger.error(f"同步月线 K 线失败 {code}: {e}")
            session.rollback()
            return 0
        finally:
            session.close()
    
    async def get_kline_weekly_from_db(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[StockKlineWeekly]:
        """从本地数据库获取周线 K 线数据"""
        if not self._initialized:
            return []
        
        try:
            session = self.get_session()
            query = session.query(StockKlineWeekly).filter(
                StockKlineWeekly.code == code
            )
            
            if start_date:
                query = query.filter(StockKlineWeekly.date >= start_date)
            if end_date:
                query = query.filter(StockKlineWeekly.date <= end_date)
            
            klines = query.order_by(StockKlineWeekly.date).all()
            return klines
        except Exception as e:
            logger.error(f"从数据库获取周线 K 线失败 {code}: {e}")
            return []
        finally:
            session.close()
    
    async def get_kline_monthly_from_db(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[StockKlineMonthly]:
        """从本地数据库获取月线 K 线数据"""
        if not self._initialized:
            return []
        
        try:
            session = self.get_session()
            query = session.query(StockKlineMonthly).filter(
                StockKlineMonthly.code == code
            )
            
            if start_date:
                query = query.filter(StockKlineMonthly.date >= start_date)
            if end_date:
                query = query.filter(StockKlineMonthly.date <= end_date)
            
            klines = query.order_by(StockKlineMonthly.date).all()
            return klines
        except Exception as e:
            logger.error(f"从数据库获取月线 K 线失败 {code}: {e}")
            return []
        finally:
            session.close()
    
    # ========== 龙虎榜/资金流向相关方法 ==========
    
    async def sync_billboard(self, billboard_data: List[Any]) -> int:
        """同步龙虎榜数据"""
        if not self._initialized:
            return 0
        
        try:
            session = self.get_session()
            count = 0
            
            for item in billboard_data:
                new_item = StockBillboard(
                    code=item.code,
                    name=item.name,
                    trade_date=item.trade_date,
                    close_price=item.close_price,
                    change_pct=item.change_pct,
                    turnover_ratio=item.turnover_ratio,
                    buy_amount=item.buy_amount,
                    sell_amount=item.sell_amount,
                    net_amount=item.net_amount,
                    reason=item.reason
                )
                session.add(new_item)
                count += 1
            
            session.commit()
            logger.info(f"同步龙虎榜成功：{count}条")
            return count
        except Exception as e:
            logger.error(f"同步龙虎榜失败：{e}")
            session.rollback()
            return 0
        finally:
            session.close()
    
    async def get_billboard_from_db(
        self,
        trade_date: str,
        code: Optional[str] = None
    ) -> List[StockBillboard]:
        """从本地数据库获取龙虎榜数据"""
        if not self._initialized:
            return []
        
        try:
            session = self.get_session()
            query = session.query(StockBillboard).filter(
                StockBillboard.trade_date == trade_date
            )
            
            if code:
                query = query.filter(StockBillboard.code == code)
            
            items = query.all()
            return items
        except Exception as e:
            logger.error(f"从数据库获取龙虎榜失败：{e}")
            return []
        finally:
            session.close()
    
    async def sync_moneyflow(self, moneyflow_data: List[Any]) -> int:
        """同步资金流向数据"""
        if not self._initialized:
            return 0
        
        try:
            session = self.get_session()
            count = 0
            
            for item in moneyflow_data:
                # 删除旧数据
                session.query(StockMoneyflow).filter(
                    StockMoneyflow.code == item.code,
                    StockMoneyflow.trade_date == item.trade_date
                ).delete()
                
                new_item = StockMoneyflow(
                    code=item.code,
                    name=item.name,
                    trade_date=item.trade_date,
                    main_force_in=item.main_force_in,
                    main_force_out=item.main_force_out,
                    main_force_net=item.main_force_net,
                    super_large_in=item.super_large_in,
                    large_in=item.large_in,
                    medium_in=item.medium_in,
                    small_in=item.small_in
                )
                session.add(new_item)
                count += 1
            
            session.commit()
            logger.info(f"同步资金流向成功：{count}条")
            return count
        except Exception as e:
            logger.error(f"同步资金流向失败：{e}")
            session.rollback()
            return 0
        finally:
            session.close()
    
    async def get_moneyflow_from_db(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[StockMoneyflow]:
        """从本地数据库获取资金流向数据"""
        if not self._initialized:
            return []
        
        try:
            session = self.get_session()
            query = session.query(StockMoneyflow).filter(
                StockMoneyflow.code == code
            )
            
            if start_date:
                query = query.filter(StockMoneyflow.trade_date >= start_date)
            if end_date:
                query = query.filter(StockMoneyflow.trade_date <= end_date)
            
            items = query.order_by(StockMoneyflow.trade_date.desc()).all()
            return items
        except Exception as e:
            logger.error(f"从数据库获取资金流向失败 {code}: {e}")
            return []
        finally:
            session.close()
    
    # ========== 股东/财务数据相关方法 ==========
    
    async def sync_shareholder(self, code: str, report_date: str, shareholders: List[Any]) -> int:
        """同步股东信息数据"""
        if not self._initialized:
            return 0
        
        try:
            session = self.get_session()
            count = 0
            
            # 删除该报告期的旧数据
            session.query(StockShareholder).filter(
                StockShareholder.code == code,
                StockShareholder.report_date == report_date
            ).delete()
            
            for holder in shareholders:
                new_holder = StockShareholder(
                    code=code,
                    report_date=report_date,
                    holder_name=holder.holder_name,
                    holder_type=holder.holder_type,
                    holding_shares=holder.holding_shares,
                    holding_ratio=holder.holding_ratio,
                    holder_rank=holder.holder_rank,
                    change_type=holder.change_type
                )
                session.add(new_holder)
                count += 1
            
            session.commit()
            logger.info(f"同步股东信息成功 {code} ({report_date}): {count}条")
            return count
        except Exception as e:
            logger.error(f"同步股东信息失败 {code}: {e}")
            session.rollback()
            return 0
        finally:
            session.close()
    
    async def get_shareholder_from_db(
        self,
        code: str,
        report_date: Optional[str] = None
    ) -> List[StockShareholder]:
        """从本地数据库获取股东信息"""
        if not self._initialized:
            return []
        
        try:
            session = self.get_session()
            query = session.query(StockShareholder).filter(
                StockShareholder.code == code
            )
            
            if report_date:
                query = query.filter(StockShareholder.report_date == report_date)
            
            items = query.order_by(StockShareholder.holder_rank).all()
            return items
        except Exception as e:
            logger.error(f"从数据库获取股东信息失败 {code}: {e}")
            return []
        finally:
            session.close()
    
    async def sync_financial(self, code: str, financial_data: List[Any]) -> int:
        """同步财务数据"""
        if not self._initialized:
            return 0
        
        try:
            session = self.get_session()
            count = 0
            
            for item in financial_data:
                # 删除旧数据
                session.query(StockFinancial).filter(
                    StockFinancial.code == code,
                    StockFinancial.report_date == item.report_date
                ).delete()
                
                new_item = StockFinancial(
                    code=code,
                    report_date=item.report_date,
                    report_type=item.report_type,
                    eps=item.eps,
                    bvps=item.bvps,
                    roe=item.roe,
                    gross_margin=item.gross_margin,
                    net_margin=item.net_margin,
                    debt_ratio=item.debt_ratio,
                    total_revenue=item.total_revenue,
                    net_profit=item.net_profit,
                    operating_cash_flow=item.operating_cash_flow
                )
                session.add(new_item)
                count += 1
            
            session.commit()
            logger.info(f"同步财务数据成功 {code}: {count}条")
            return count
        except Exception as e:
            logger.error(f"同步财务数据失败 {code}: {e}")
            session.rollback()
            return 0
        finally:
            session.close()
    
    async def get_financial_from_db(
        self,
        code: str,
        report_date: Optional[str] = None
    ) -> List[StockFinancial]:
        """从本地数据库获取财务数据"""
        if not self._initialized:
            return []
        
        try:
            session = self.get_session()
            query = session.query(StockFinancial).filter(
                StockFinancial.code == code
            )
            
            if report_date:
                query = query.filter(StockFinancial.report_date == report_date)
            
            items = query.order_by(StockFinancial.report_date.desc()).all()
            return items
        except Exception as e:
            logger.error(f"从数据库获取财务数据失败 {code}: {e}")
            return []
        finally:
            session.close()
    
    # ========== 板块成分股相关方法 ==========
    
    async def sync_sector_components(self, sector_code: str, sector_name: str, components: List[Any]) -> int:
        """同步板块成分股数据"""
        if not self._initialized:
            return 0
        
        try:
            session = self.get_session()
            count = 0
            
            # 删除旧数据
            session.query(SectorComponent).filter(
                SectorComponent.sector_code == sector_code
            ).delete()
            
            for component in components:
                new_component = SectorComponent(
                    sector_code=sector_code,
                    sector_name=sector_name,
                    stock_code=component.stock_code,
                    stock_name=component.stock_name,
                    weight=component.weight
                )
                session.add(new_component)
                count += 1
            
            session.commit()
            logger.info(f"同步板块成分股成功 {sector_name}: {count}条")
            return count
        except Exception as e:
            logger.error(f"同步板块成分股失败 {sector_name}: {e}")
            session.rollback()
            return 0
        finally:
            session.close()
    
    async def get_sector_components_from_db(self, sector_code: str) -> List[SectorComponent]:
        """从本地数据库获取板块成分股"""
        if not self._initialized:
            return []
        
        try:
            session = self.get_session()
            components = session.query(SectorComponent).filter(
                SectorComponent.sector_code == sector_code
            ).order_by(SectorComponent.weight.desc()).all()
            return components
        except Exception as e:
            logger.error(f"从数据库获取板块成分股失败 {sector_code}: {e}")
            return []
        finally:
            session.close()
    
    # ========== 数据清理相关方法 ==========
    
    async def cleanup_old_data(self, days: int = 90):
        """
        清理过期数据
        
        Args:
            days: 保留最近 N 天的数据，默认 90 天
        """
        if not self._initialized:
            return 0
        
        from datetime import timedelta
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        try:
            session = self.get_session()
            total_deleted = 0
            
            # 清理资金流向数据
            deleted = session.query(StockMoneyflow).filter(
                StockMoneyflow.trade_date < cutoff_date
            ).delete(synchronize_session=False)
            total_deleted += deleted
            
            # 清理龙虎榜数据
            deleted = session.query(StockBillboard).filter(
                StockBillboard.trade_date < cutoff_date
            ).delete(synchronize_session=False)
            total_deleted += deleted
            
            session.commit()
            logger.info(f"清理过期数据完成：删除 {total_deleted}条 {days}天前的数据")
            return total_deleted
            
        except Exception as e:
            logger.error(f"清理过期数据失败：{e}")
            session.rollback()
            return 0
        finally:
            session.close()
    
    async def cleanup_kline_data(self, code: str, period: str = "daily", keep_years: int = 5):
        """
        清理 K 线数据
        
        Args:
            code: 股票代码
            period: K 线类型（daily/weekly/monthly）
            keep_years: 保留最近 N 年的数据，默认 5 年
        """
        if not self._initialized:
            return 0
        
        from datetime import timedelta
        
        table_map = {
            "daily": StockKlineDaily,
            "weekly": StockKlineWeekly,
            "monthly": StockKlineMonthly
        }
        
        if period not in table_map:
            logger.error(f"不支持的 K 线类型：{period}")
            return 0
        
        table = table_map[period]
        cutoff_date = (datetime.now() - timedelta(days=365 * keep_years)).strftime("%Y-%m-%d")
        
        try:
            session = self.get_session()
            deleted = session.query(table).filter(
                table.code == code,
                table.date < cutoff_date
            ).delete(synchronize_session=False)
            
            session.commit()
            logger.info(f"清理 K 线数据完成 {code} {period}: 删除 {deleted}条 {keep_years}年前的数据")
            return deleted
            
        except Exception as e:
            logger.error(f"清理 K 线数据失败 {code} {period}: {e}")
            session.rollback()
            return 0
        finally:
            session.close()
    
    # ========== 数据删除方法 ==========
    
    async def delete_kline_data(self, code: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> int:
        """删除 K 线数据"""
        if not self._initialized:
            return 0
        
        try:
            session = self.get_session()
            query = session.query(StockKlineDaily).filter(StockKlineDaily.code == code)
            
            if start_date:
                query = query.filter(StockKlineDaily.date >= start_date)
            if end_date:
                query = query.filter(StockKlineDaily.date <= end_date)
            
            deleted = query.delete(synchronize_session=False)
            session.commit()
            logger.debug(f"删除 K 线数据成功：{code}, 删除 {deleted} 条")
            return deleted
        except Exception as e:
            logger.error(f"删除 K 线数据失败：{e}")
            return 0
        finally:
            session.close()
    
    async def delete_kline_weekly(self, code: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> int:
        """删除周线 K 线数据"""
        if not self._initialized:
            return 0
        
        try:
            session = self.get_session()
            query = session.query(StockKlineWeekly).filter(StockKlineWeekly.code == code)
            
            if start_date:
                query = query.filter(StockKlineWeekly.date >= start_date)
            if end_date:
                query = query.filter(StockKlineWeekly.date <= end_date)
            
            deleted = query.delete(synchronize_session=False)
            session.commit()
            logger.debug(f"删除周线 K 线数据成功：{code}, 删除 {deleted} 条")
            return deleted
        except Exception as e:
            logger.error(f"删除周线 K 线数据失败：{e}")
            return 0
        finally:
            session.close()
    
    async def delete_kline_monthly(self, code: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> int:
        """删除月线 K 线数据"""
        if not self._initialized:
            return 0
        
        try:
            session = self.get_session()
            query = session.query(StockKlineMonthly).filter(StockKlineMonthly.code == code)
            
            if start_date:
                query = query.filter(StockKlineMonthly.date >= start_date)
            if end_date:
                query = query.filter(StockKlineMonthly.date <= end_date)
            
            deleted = query.delete(synchronize_session=False)
            session.commit()
            logger.debug(f"删除月线 K 线数据成功：{code}, 删除 {deleted} 条")
            return deleted
        except Exception as e:
            logger.error(f"删除月线 K 线数据失败：{e}")
            return 0
        finally:
            session.close()
    
    async def delete_quote_data(self, code: str) -> int:
        """删除实时行情数据"""
        if not self._initialized:
            return 0
        
        try:
            session = self.get_session()
            deleted = session.query(StockQuote).filter(StockQuote.code == code).delete(synchronize_session=False)
            session.commit()
            logger.debug(f"删除实时行情数据成功：{code}, 删除 {deleted} 条")
            return deleted
        except Exception as e:
            logger.error(f"删除实时行情数据失败：{e}")
            return 0
        finally:
            session.close()
    
    async def delete_fund_nav(self, code: str) -> int:
        """删除基金净值数据"""
        if not self._initialized:
            return 0
        
        try:
            session = self.get_session()
            deleted = session.query(FundNAV).filter(FundNAV.code == code).delete(synchronize_session=False)
            session.commit()
            logger.debug(f"删除基金净值数据成功：{code}, 删除 {deleted} 条")
            return deleted
        except Exception as e:
            logger.error(f"删除基金净值数据失败：{e}")
            return 0
        finally:
            session.close()
    
    async def delete_billboard(self, trade_date: Optional[str] = None, code: Optional[str] = None) -> int:
        """删除龙虎榜数据"""
        if not self._initialized:
            return 0
        
        try:
            session = self.get_session()
            query = session.query(StockBillboard)
            
            if trade_date:
                query = query.filter(StockBillboard.trade_date == trade_date)
            if code:
                query = query.filter(StockBillboard.code == code)
            
            deleted = query.delete(synchronize_session=False)
            session.commit()
            logger.debug(f"删除龙虎榜数据成功，删除 {deleted} 条")
            return deleted
        except Exception as e:
            logger.error(f"删除龙虎榜数据失败：{e}")
            return 0
        finally:
            session.close()
    
    async def delete_moneyflow(self, code: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> int:
        """删除资金流向数据"""
        if not self._initialized:
            return 0
        
        try:
            session = self.get_session()
            query = session.query(StockMoneyflow).filter(StockMoneyflow.code == code)
            
            if start_date:
                query = query.filter(StockMoneyflow.trade_date >= start_date)
            if end_date:
                query = query.filter(StockMoneyflow.trade_date <= end_date)
            
            deleted = query.delete(synchronize_session=False)
            session.commit()
            logger.debug(f"删除资金流向数据成功：{code}, 删除 {deleted} 条")
            return deleted
        except Exception as e:
            logger.error(f"删除资金流向数据失败：{e}")
            return 0
        finally:
            session.close()
    
    async def get_database_stats(self) -> Dict[str, int]:
        """获取数据库统计信息"""
        if not self._initialized:
            return {}
        
        try:
            session = self.get_session()
            stats = {
                "stocks": session.query(StockBasic).count(),
                "funds": session.query(FundBasic).count(),
                "daily_klines": session.query(StockKlineDaily).count(),
                "weekly_klines": session.query(StockKlineWeekly).count(),
                "monthly_klines": session.query(StockKlineMonthly).count(),
                "quotes": session.query(StockQuote).count(),
                "billboards": session.query(StockBillboard).count(),
                "moneyflows": session.query(StockMoneyflow).count(),
                "shareholders": session.query(StockShareholder).count(),
                "financials": session.query(StockFinancial).count(),
                "sectors": session.query(SectorInfo).count(),
                "sector_components": session.query(SectorComponent).count(),
                "fund_nav": session.query(FundNAV).count(),
                "fund_holdings": session.query(FundHolding).count(),
            }
            return stats
        except Exception as e:
            logger.error(f"获取数据库统计失败：{e}")
            return {}
        finally:
            session.close()
    
    async def close(self):
        """关闭数据库连接"""
        if self.engine:
            self.engine.dispose()
            self._initialized = False
            logger.info("本地数据库已关闭")


# 全局实例
local_db_service = LocalDatabaseService()

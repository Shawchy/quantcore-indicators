from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd


class DataSourceType(str, Enum):
    AKSHARE = "akshare"
    BAOSTOCK = "baostock"
    YFINANCE = "yfinance"
    TUSHARE = "tushare"
    EFINANCE = "efinance"


@dataclass
class StockBasicInfo:
    code: str
    name: str
    market: str
    industry: Optional[str] = None
    sector: Optional[str] = None
    area: Optional[str] = None
    list_date: Optional[str] = None
    total_shares: Optional[float] = None
    float_shares: Optional[float] = None


@dataclass
class KLineData:
    code: str
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: Optional[float] = None
    turnover_rate: Optional[float] = None


@dataclass
class SectorInfo:
    code: str
    name: str
    sector_type: str
    change_pct: Optional[float] = None
    volume: Optional[float] = None
    amount: Optional[float] = None


@dataclass
class ChipData:
    """股东人数（筹码）数据"""
    code: str
    date: str
    shareholder_count: Optional[int] = None
    avg_shares_per_holder: Optional[float] = None
    top10_holders_ratio: Optional[float] = None


@dataclass
class BillboardEntry:
    code: str
    name: str
    close_price: Optional[float] = None
    change_pct: Optional[float] = None
    turnover_amount: Optional[float] = None
    net_amount: Optional[float] = None
    buy_amount: Optional[float] = None
    sell_amount: Optional[float] = None
    reason: Optional[str] = None
    trade_date: str = ""


@dataclass
class BoardInfo:
    code: str
    name: str
    board_type: str
    close_price: Optional[float] = None
    change_pct: Optional[float] = None


@dataclass
class ShareholderInfo:
    """股东信息"""
    code: str
    report_date: str  # 报告期/更新日期
    holder_code: str  # 股东代码
    holder_name: str  # 股东名称
    hold_amount: Optional[float] = None  # 持股数（股）
    hold_ratio: Optional[float] = None  # 持股比例（%）
    change: Optional[str] = None  # 增减描述（不变/新进/数值）
    change_rate: Optional[float] = None  # 变动率（%）


@dataclass
class IndexComponent:
    """指数成分股"""
    index_code: str
    index_name: str
    code: str
    name: str
    weight: Optional[float] = None
    industry: Optional[str] = None


@dataclass
class CapitalFlowItem:
    code: str
    name: str
    close_price: Optional[float] = None
    change_pct: Optional[float] = None
    main_net_amount: Optional[float] = None
    main_net_amount_rate: Optional[float] = None
    buy_elg_amount: Optional[float] = None
    buy_lg_amount: Optional[float] = None
    buy_md_amount: Optional[float] = None
    buy_sm_amount: Optional[float] = None
    trade_date: str = ""


@dataclass
class MarketQuote:
    """市场实时行情"""
    code: str
    name: str
    change_pct: Optional[float] = None
    price: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    open: Optional[float] = None
    change: Optional[float] = None
    turnover_rate: Optional[float] = None
    volume_ratio: Optional[float] = None
    pe_ratio: Optional[float] = None
    volume: Optional[float] = None
    amount: Optional[float] = None
    prev_close: Optional[float] = None
    total_market_cap: Optional[float] = None
    float_market_cap: Optional[float] = None
    market_type: Optional[str] = None


@dataclass
class FinancialPerformance:
    """财务业绩数据（季度）"""
    code: str
    name: str
    report_date: str  # 公告日期
    revenue: Optional[float] = None  # 营业收入
    revenue_growth: Optional[float] = None  # 营业收入同比增长
    revenue_qoq: Optional[float] = None  # 营业收入季度环比
    net_profit: Optional[float] = None  # 净利润
    net_profit_growth: Optional[float] = None  # 净利润同比增长
    net_profit_qoq: Optional[float] = None  # 净利润季度环比
    eps: Optional[float] = None  # 每股收益
    bvps: Optional[float] = None  # 每股净资产
    roe: Optional[float] = None  # 净资产收益率
    gross_margin: Optional[float] = None  # 销售毛利率
    cfps: Optional[float] = None  # 每股经营现金流量


@dataclass
class FundInfo:
    """基金基本信息"""
    code: str                    # 基金代码
    name: str                    # 基金简称
    establish_date: Optional[str] = None  # 成立日期
    change_pct: Optional[float] = None    # 涨跌幅（%）
    net_asset_value: Optional[float] = None  # 最新净值
    fund_company: Optional[str] = None       # 基金公司
    nav_update_date: Optional[str] = None    # 净值更新日期
    description: Optional[str] = None         # 简介


class BaseDataAdapter(ABC):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._is_initialized = False
    
    @property
    @abstractmethod
    def source_type(self) -> DataSourceType:
        pass
    
    @abstractmethod
    async def initialize(self) -> bool:
        pass
    
    @abstractmethod
    async def close(self) -> None:
        pass
    
    @abstractmethod
    async def get_stock_list(self, market: Optional[str] = None) -> List[StockBasicInfo]:
        pass
    
    @abstractmethod
    async def get_stock_info(self, code: str) -> Optional[StockBasicInfo]:
        pass
    
    @abstractmethod
    async def get_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq",
        period: str = "daily"
    ) -> List[KLineData]:
        """获取 K 线数据（支持多种周期）
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权方式（qfq/hfq/no）
            period: K 线周期，可选：
                - '1m': 1 分钟
                - '5m': 5 分钟
                - '15m': 15 分钟
                - '30m': 30 分钟
                - '60m': 60 分钟
                - 'daily': 日线
                - 'weekly': 周线
                - 'monthly': 月线
        """
        pass
    
    @abstractmethod
    async def get_weekly_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq"
    ) -> List[KLineData]:
        pass
    
    @abstractmethod
    async def get_monthly_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq"
    ) -> List[KLineData]:
        pass
    
    @abstractmethod
    async def get_realtime_quote(self, code: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def get_sector_list(self, sector_type: str = "industry") -> List[SectorInfo]:
        pass
    
    @abstractmethod
    async def get_sector_components(self, sector_code: str) -> List[str]:
        pass
    
    @abstractmethod
    async def get_chip_data(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[ChipData]:
        pass
    
    @abstractmethod
    async def get_daily_billboard(self, trade_date: Optional[str] = None) -> List[BillboardEntry]:
        pass
    
    @abstractmethod
    async def get_belong_board(self, code: str) -> List[BoardInfo]:
        pass
    
    @abstractmethod
    async def get_members(self, index_code: str) -> List[IndexComponent]:
        """获取指数成分股
        
        Args:
            index_code: 指数代码或指数名称
        
        Returns:
            指数成分股列表
        """
        pass
    
    @abstractmethod
    async def get_members(self, index_code: str) -> List[IndexComponent]:
        pass
    
    @abstractmethod
    async def get_today_bill(self, trade_date: Optional[str] = None) -> List[CapitalFlowItem]:
        pass
    
    @abstractmethod
    async def get_history_bill(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[CapitalFlowItem]:
        pass
    
    @abstractmethod
    async def get_top10_stock_holder_info(self, code: str) -> List[ShareholderInfo]:
        pass
    
    @abstractmethod
    async def get_market_realtime_quotes(self, market_types: Optional[List[str]] = None) -> List[MarketQuote]:
        pass
    
    @abstractmethod
    async def get_financial_performance(
        self,
        code: str,
        report_date: Optional[str] = None,
        report_type: str = "quarterly"
    ) -> List[FinancialPerformance]:
        """获取财务业绩数据
        
        Args:
            code: 股票代码
            report_date: 报告日期，格式 'YYYY-MM-DD'
                - None: 获取最新季报
                - '2024-03-31': 获取 2024 年一季报
                - '2023-12-31': 获取 2023 年年报
            report_type: 报告类型
        
        Returns:
            财务业绩数据列表
        """
        pass
    
    def normalize_code(self, code: str) -> str:
        return code.strip().upper()
    
    def format_date(self, date: str) -> str:
        if len(date) == 8:
            return f"{date[:4]}-{date[4:6]}-{date[6:8]}"
        return date
    
    def kline_to_dataframe(self, klines: List[KLineData]) -> pd.DataFrame:
        if not klines:
            return pd.DataFrame()
        
        data = [
            {
                "code": k.code,
                "date": k.date,
                "open": k.open,
                "high": k.high,
                "low": k.low,
                "close": k.close,
                "volume": k.volume,
                "amount": k.amount,
                "turnover_rate": k.turnover_rate
            }
            for k in klines
        ]
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        return df

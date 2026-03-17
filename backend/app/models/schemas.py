from pydantic import BaseModel
from typing import Generic, TypeVar, Optional, List

T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    success: bool = True
    code: str = "SUCCESS"
    message: str = "操作成功"
    data: Optional[T] = None


class PageInfo(BaseModel):
    page: int = 1
    page_size: int = 20
    total: int = 0
    total_pages: int = 0


class PagedResponseModel(BaseModel, Generic[T]):
    success: bool = True
    code: str = "SUCCESS"
    message: str = "操作成功"
    data: Optional[List[T]] = None
    page_info: Optional[PageInfo] = None


class StockBasic(BaseModel):
    code: str
    name: str
    market: str
    industry: Optional[str] = None
    list_date: Optional[str] = None


class KLineData(BaseModel):
    code: str
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: Optional[float] = None
    turnover_rate: Optional[float] = None
    pre_close: Optional[float] = None  # 昨日收盘价


class TechnicalIndicator(BaseModel):
    code: str
    date: str
    ma5: Optional[float] = None
    ma10: Optional[float] = None
    ma20: Optional[float] = None
    ma60: Optional[float] = None
    rsi6: Optional[float] = None
    rsi12: Optional[float] = None
    rsi24: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None


class MarketMoneyflowData(BaseModel):
    """大盘资金流向数据模型"""
    trade_date: str
    close_sh: Optional[float] = None
    pct_change_sh: Optional[float] = None
    close_sz: Optional[float] = None
    pct_change_sz: Optional[float] = None
    net_amount: Optional[float] = None
    net_amount_rate: Optional[float] = None
    buy_elg_amount: Optional[float] = None
    buy_elg_amount_rate: Optional[float] = None
    buy_lg_amount: Optional[float] = None
    buy_lg_amount_rate: Optional[float] = None
    buy_md_amount: Optional[float] = None
    buy_md_amount_rate: Optional[float] = None
    buy_sm_amount: Optional[float] = None
    buy_sm_amount_rate: Optional[float] = None


class BillboardEntry(BaseModel):
    """龙虎榜单条目"""
    code: str
    name: str
    close_price: Optional[float] = None
    change_pct: Optional[float] = None
    turnover_amount: Optional[float] = None
    net_amount: Optional[float] = None
    buy_amount: Optional[float] = None
    sell_amount: Optional[float] = None
    reason: Optional[str] = None
    trade_date: str


class BoardInfo(BaseModel):
    """股票所属板块信息"""
    code: str
    name: str
    board_type: str
    close_price: Optional[float] = None
    change_pct: Optional[float] = None


class ShareholderInfo(BaseModel):
    """股东信息"""
    code: str
    shareholder_name: str
    shareholder_type: Optional[str] = None
    hold_amount: Optional[float] = None
    hold_ratio: Optional[float] = None
    change_amount: Optional[float] = None
    change_ratio: Optional[float] = None
    report_date: str


class IndexComponent(BaseModel):
    """指数成分股"""
    code: str
    name: str
    weight: Optional[float] = None
    industry: Optional[str] = None


class CapitalFlowItem(BaseModel):
    """资金流向条目"""
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
    trade_date: str


class MarketQuote(BaseModel):
    """市场实时行情数据"""
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

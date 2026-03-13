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

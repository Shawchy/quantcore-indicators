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

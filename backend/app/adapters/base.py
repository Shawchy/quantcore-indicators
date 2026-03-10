from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import pandas as pd


class DataSourceType(str, Enum):
    AKSHARE = "akshare"
    BAOSTOCK = "baostock"
    YFINANCE = "yfinance"
    TUSHARE = "tushare"


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
    code: str
    date: str
    shareholder_count: Optional[float] = None
    avg_shares_per_holder: Optional[float] = None
    top10_holders_ratio: Optional[float] = None


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

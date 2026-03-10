from .base import (
    BaseDataAdapter,
    DataSourceType,
    StockBasicInfo,
    KLineData,
    SectorInfo,
    ChipData
)

from .akshare_adapter import AkShareAdapter
from .baostock_adapter import BaostockAdapter
from .yfinance_adapter import YFinanceAdapter

try:
    from .tushare_adapter import TushareAdapter
except ImportError:
    TushareAdapter = None

from .factory import DataSourceFactory, DataSourceManager, data_source_manager

__all__ = [
    "BaseDataAdapter",
    "DataSourceType",
    "StockBasicInfo",
    "KLineData",
    "SectorInfo",
    "ChipData",
    "AkShareAdapter",
    "BaostockAdapter",
    "YFinanceAdapter",
    "TushareAdapter",
    "DataSourceFactory",
    "DataSourceManager",
    "data_source_manager"
]

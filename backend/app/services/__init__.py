"""
业务处理层 (L3: Business Services Layer)

职责:
- 核心领域服务（股票/板块/筹码/选股）
- 缓存与编排服务
- 定时任务服务

依赖规则:
- 可调用 L2 (processing/) 的数据处理函数
- 可调用 L1 (infrastructure/) 的存储/缓存/适配器
- 不被 L1/L2 依赖

注意: 数据处理模块已迁移至 processing/
      - DataCleaner, PriceAdjuster, DataProcessor → processing.data_processor
      - DataValidator → processing.data_validator
      - IndicatorsManager, get_indicators_manager → processing.indicators_manager
"""

# 核心业务服务
from .stock_service import StockService, stock_service
from .watchlist_service import WatchlistService, watchlist_service
from .sector_service import SectorService, sector_service
from .chip_service import ChipService, chip_service
from .screener_service import Screener, StockScreener, screener

# 其他业务服务
from .cache_service import CacheService, cache_service
from .chart_data_service import ChartDataService, chart_data_service
from .market_turnover_service import market_turnover_service
from .moneyflow_service import MoneyflowService, moneyflow_service
from .stock_info_service import StockInfoService, get_stock_info_service
from .data_sync_scheduler import DataSyncScheduler, data_sync_scheduler
from .trading_calendar import TradingCalendarService, trading_calendar
from .stock_list_sync import StockListSync, stock_list_sync

# 从 processing/ 重新导出数据处理模块（兼容性，延迟导入）
try:
    from app.processing.data_processor import DataCleaner, PriceAdjuster, DataProcessor
    from app.processing.data_validator import DataValidator, data_validator
    from app.processing.indicators_manager import IndicatorsManager, get_indicators_manager
    PROCESSING_AVAILABLE = True
except ImportError as e:
    print(f"[WARN] processing 模块导入失败: {e}")
    DataCleaner = None
    PriceAdjuster = None
    DataProcessor = None
    DataValidator = None
    data_validator = None
    IndicatorsManager = None
    get_indicators_manager = None
    PROCESSING_AVAILABLE = False

__all__ = [
    # Core Domain Services
    "StockService", "stock_service",
    "SectorService", "sector_service",
    "ChipService", "chip_service",
    "Screener", "StockScreener", "screener",
    "WatchlistService", "watchlist_service",
    "MoneyflowService", "moneyflow_service",
    "StockInfoService", "stock_info_service",
    
    # Orchestration Services
    "CacheService", "cache_service",
    "ChartDataService", "chart_data_service",
    "market_turnover_service",
    
    # Scheduling Services
    "DataSyncScheduler", "data_sync_scheduler",
    "TradingCalendarService", "trading_calendar",
    "StockListSync", "stock_list_sync",
    
    # Processing (re-exported from processing/)
    "DataCleaner", "PriceAdjuster", "DataProcessor",
    "DataValidator", "data_validator",
    "IndicatorsManager", "get_indicators_manager",
]

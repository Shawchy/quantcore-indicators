"""
基础设施层 (L1: Infrastructure Layer)

职责:
- 存储引擎 (L1缓存/L2 SQLite/L3 Parquet)
- 数据源适配器 (efinance/akshare/baostock/tickflow)
- 数据治理 (热点追踪/分区管理/生命周期)
- 工具函数 (日期/标准化/统计)

依赖规则:
- 仅依赖外部库 (SQLAlchemy, aiofiles, pandas)
- 不调用任何上层业务逻辑
- 可被 L2 (processing/) 和 L3 (services/) 调用
"""

# 存储引擎
from app.storage import (
    Base, StockInfo, KLine, TechnicalIndicatorDB,
    WatchlistDB, ChipData, SectorInfo, Strategy,
    BacktestRecord, TradeRecord, User, RealtimeQuote,
    init_database, get_session,
    cache_manager, CacheManager, AsyncLRUCache,
    parquet_manager, ParquetManager,
)

# 分类系统
from app.storage.classification import (
    DataTier, UnifiedDataConfig, UNIFIED_DATA_CONFIGS,
    get_config, get_tier
)

# 数据源适配器
from app.adapters.factory import DataSourceFactory, DataSourceManager, data_source_manager

__all__ = [
    # Storage ORM Models
    "Base", "StockInfo", "KLine", "TechnicalIndicatorDB",
    "WatchlistDB", "ChipData", "SectorInfo", "Strategy",
    "BacktestRecord", "TradeRecord", "User", "RealtimeQuote",
    "init_database", "get_session",
    
    # Storage Engines
    "cache_manager", "CacheManager", "AsyncLRUCache",
    "parquet_manager", "ParquetManager",
    
    # Classification System
    "DataTier", "UnifiedDataConfig", "UNIFIED_DATA_CONFIGS",
    "get_config", "get_tier",
    
    # Adapters
    "DataSourceFactory", "DataSourceManager", "data_source_manager",
]

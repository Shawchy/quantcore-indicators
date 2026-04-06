"""
QuantCore - 高性能量化交易框架

QuantCore 是一个使用 Rust 引擎 + Python 接口的高性能量化交易框架，
旨在提供媲美 Backtrader、Vn.py 等专业框架的功能和性能。
"""

__version__ = "0.1.1"
__author__ = "QuantCore Team"

# 核心数据模型
from quantcore.core import (
    Bar, 
    Order, 
    Trade, 
    Position, 
    Portfolio,
    OrderSide,
    OrderType,
    OrderStatus,
)

# 回测引擎
from quantcore.engine import (
    BacktestEngine, 
    BacktestConfig,
    BacktestResult,
)

# 策略
from quantcore.strategy import Strategy, StrategyRunner

# 数据
from quantcore.data import (
    DataLoader,
    BaostockAdapter,
    CSVLoader,
    DataCache,
    CachedDataLoader,
    create_data_loader,
    load_baostock_data,
    load_csv_data,
)

# 风控
from quantcore.risk import (
    RiskManager,
    PositionLimit,
    StopLoss,
)

# 绩效
from quantcore.performance import (
    PerformanceAnalyzer,
    PerformanceReport,
)

# 技术指标
from quantcore.indicators import (
    ma,
    ema,
    macd,
    rsi,
    bollinger_bands,
    kdj,
    atr,
    cci,
    williams_r,
    obv,
)

# 日志系统
from quantcore.logger import (
    get_logger,
    get_backtest_logger,
    get_strategy_logger,
    get_data_logger,
    get_trade_logger,
    set_log_level,
    set_log_file,
    log_context,
    log_call,
    LogLevel,
)

# 参数优化
from quantcore.optimizer import (
    GridSearch,
    RandomSearch,
    optimize_strategy,
    OptimizationResult,
)

__all__ = [
    # 核心数据
    "Bar",
    "Order",
    "Trade",
    "Position",
    "Portfolio",
    "OrderSide",
    "OrderType",
    "OrderStatus",
    
    # 回测引擎
    "BacktestEngine",
    "BacktestConfig",
    "BacktestResult",
    
    # 策略
    "Strategy",
    "StrategyRunner",
    
    # 数据
    "DataLoader",
    "BaostockAdapter",
    "CSVLoader",
    "DataCache",
    "CachedDataLoader",
    "create_data_loader",
    "load_baostock_data",
    "load_csv_data",
    
    # 风控
    "RiskManager",
    "PositionLimit",
    "StopLoss",
    
    # 绩效
    "PerformanceAnalyzer",
    "PerformanceReport",
    
    # 技术指标
    "ma",
    "ema",
    "macd",
    "rsi",
    "bollinger_bands",
    "kdj",
    "atr",
    "cci",
    "williams_r",
    "obv",
    
    # 日志系统
    "get_logger",
    "get_backtest_logger",
    "get_strategy_logger",
    "get_data_logger",
    "get_trade_logger",
    "set_log_level",
    "set_log_file",
    "log_context",
    "log_call",
    "LogLevel",
    
    # 参数优化
    "GridSearch",
    "RandomSearch",
    "optimize_strategy",
    "OptimizationResult",
]

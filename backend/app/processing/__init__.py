"""
数据处理层 (L2: Data Processing Layer)

职责:
- 数据清洗、校验、标准化
- 技术指标计算引擎
- 性能加速（向量化筛选、回测加速）
- 指标预计算

依赖规则:
- 仅依赖 pandas, numpy 等纯计算库
- 可被 L3 (services/) 调用
- 不调用任何上层业务逻辑

模块列表:
- data_processor: 数据清洗 + 价格复权
- data_validator: 数据格式校验
- indicators_manager: 技术指标计算引擎
- indicator_precomputer: 指标预计算缓存
- batch_screener: 向量化批量筛选器
- backtest_accelerator: 回测数据预加载
"""

# 延迟导入，避免循环依赖
__all__ = [
    "DataCleaner",
    "PriceAdjuster", 
    "DataProcessor",
    "DataValidator",
    "data_validator",
    "IndicatorsManager",
    "get_indicators_manager",
    "IndicatorPrecomputer",
    "BatchScreener",
    "CompareOp",
    "ScreenCondition",
    "BacktestAccelerator",
]

def __getattr__(name):
    """延迟导入支持"""
    if name in ["DataCleaner", "PriceAdjuster", "DataProcessor"]:
        from .data_processor import DataCleaner, PriceAdjuster, DataProcessor
        return locals()[name]
    elif name in ["DataValidator", "data_validator"]:
        from .data_validator import DataValidator, data_validator
        return locals()[name]
    elif name in ["IndicatorsManager", "get_indicators_manager"]:
        from .indicators_manager import IndicatorsManager, get_indicators_manager
        return locals()[name]
    elif name == "IndicatorPrecomputer":
        from .indicator_precomputer import IndicatorPrecomputer
        return IndicatorPrecomputer
    elif name in ["BatchScreener", "CompareOp", "ScreenCondition"]:
        from .batch_screener import BatchScreener, CompareOp, ScreenCondition
        return locals().get(name)
    elif name == "BacktestAccelerator":
        from .backtest_accelerator import BacktestAccelerator
        return BacktestAccelerator
    raise AttributeError(f"module 'app.processing' has no attribute {name}")

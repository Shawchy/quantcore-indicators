"""
因子计算引擎模块

核心组件：
- FactorCalculator: 因子计算器基类
- FactorEngine: 因子引擎（工厂模式）
- FactorRegistry: 因子注册中心
- FactorPipeline: 因子流水线
"""

from .calculator import (
    BaseFactorCalculator,
    MomentumCalculator,
    ReversalCalculator,
    VolatilityCalculator,
    LiquidityCalculator,
    ValueCalculator,
    QualityCalculator,
    GrowthCalculator,
    SentimentCalculator,
)
from .registry import FactorRegistry, FactorSpec, FactorCategory
from .engine import FactorEngine
from .pipeline import FactorPipeline

__all__ = [
    "BaseFactorCalculator",
    "MomentumCalculator",
    "ReversalCalculator",
    "VolatilityCalculator",
    "LiquidityCalculator",
    "ValueCalculator",
    "QualityCalculator",
    "GrowthCalculator",
    "SentimentCalculator",
    "FactorRegistry",
    "FactorSpec",
    "FactorCategory",
    "FactorEngine",
    "FactorPipeline",
]

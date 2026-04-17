"""
组合优化器模块

提供多种投资组合优化方法：
- Mean-Variance (均值-方差优化)
- Risk Parity (风险平价)
- Maximum Diversification (最大分散度)
- Black-Litterman (贝叶斯观点融合)
- Factor Constraints (因子暴露约束)
"""

from .base import BaseOptimizer, OptimizationConstraints, OptimizationResult
from .mean_variance import MeanVarianceOptimizer
from .risk_parity import RiskParityOptimizer
from .black_litterman import BlackLittermanOptimizer
from .max_diversification import MaxDiversificationOptimizer
from .factor_constraints import FactorConstrainedOptimizer
from .transaction_cost import TransactionCostModel, Rebalancer

__all__ = [
    "BaseOptimizer",
    "OptimizationConstraints",
    "OptimizationResult",
    "MeanVarianceOptimizer",
    "RiskParityOptimizer", 
    "BlackLittermanOptimizer",
    "MaxDiversificationOptimizer",
    "FactorConstrainedOptimizer",
    "TransactionCostModel",
    "Rebalancer",
]

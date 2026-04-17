"""
Barra 风险模型模块

实现 CNE5/CNE6 风格风险模型：
- 10 个风格因子
- 行业因子
- 协方差矩阵估计
- 风险归因分析
"""

from .barra_model import BarraRiskModel, BarraFactorExposure, StyleFactorCalculator
from .covariance import CovarianceEstimator, SpecificRiskEstimator
from .risk_attribution import RiskAttribution

__all__ = [
    "BarraRiskModel",
    "BarraFactorExposure", 
    "StyleFactorCalculator",
    "CovarianceEstimator",
    "SpecificRiskEstimator",
    "RiskAttribution",
]

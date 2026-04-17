"""
因子研究模块

提供因子测试和验证功能：
- ICAnalysis: IC 分析
- LayeredBacktestResult: 分层回测结果
- FactorTester: 因子测试器
"""

from .ic_analysis import ICAnalysis
from .layered_backtest import LayeredBacktestResult, LayeredBacktester
from .factor_tester import FactorTester

__all__ = [
    "ICAnalysis",
    "LayeredBacktestResult",
    "LayeredBacktester",
    "FactorTester",
]

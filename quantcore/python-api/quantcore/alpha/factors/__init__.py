"""
Data Factor 因子库

完整的 Data Factor 四大类：
1. MarketFactorLibrary - 市场量价因子
2. FundamentalFactorLibrary - 基本面因子
3. AlternativeFactorLibrary - 另类数据因子 ⭐
4. StructuredFactorLibrary - 结构化另类因子 ⭐
"""

from .market import MarketFactorLibrary
from .fundamental import FundamentalFactorLibrary
from .alternative import AlternativeFactorLibrary
from .structured import StructuredFactorLibrary

__all__ = [
    "MarketFactorLibrary",
    "FundamentalFactorLibrary",
    "AlternativeFactorLibrary",
    "StructuredFactorLibrary",
]

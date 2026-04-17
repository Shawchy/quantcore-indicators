"""
Data Factor Alpha 工厂

完整的 Data Factor 体系：
1. Market Data Factor (量价因子)
2. Fundamental Data Factor (基本面因子)
3. Alternative Data Factor (另类数据因子) ⭐
4. Alternative Structure Factor (结构化另类因子)

核心组件：
- AlphaFactory: 工厂主类，统一管理所有组件
- FactorEngine: 因子计算引擎
- RiskModel: Barra风险模型
- Optimizer: 组合优化器套件
- AlternativeCrawlers: 另类数据采集

使用示例：
    from quantcore.alpha import AlphaFactory
    
    factory = AlphaFactory()
    result = await factory.run_full_pipeline(symbols, returns)
"""

from .engine import FactorEngine, FactorCalculator
from .storage import FactorDatabase
from .factors import (
    MarketFactorLibrary,
    FundamentalFactorLibrary,
    AlternativeFactorLibrary,
    StructuredFactorLibrary,
)
from .research import FactorTester, ICAnalysis, LayeredBacktestResult

# Alpha工厂核心
from .factory import (
    AlphaFactory,
    AlphaFactoryConfig,
    FactorProductionResult,
    PortfolioOptimizationResult,
)

# 风险模型
from .risk.barra_model import BarraRiskModel

# 组合优化器
from .optimizer.mean_variance import MeanVarianceOptimizer
from .optimizer.risk_parity import RiskParityOptimizer
from .optimizer.black_litterman import BlackLittermanOptimizer
from .optimizer.max_diversification import MaxDiversificationOptimizer
from .optimizer.factor_constraints import FactorConstrainedOptimizer
from .optimizer.transaction_cost import TransactionCostModel

# 另类数据采集
from .alternative.raw import (
    BackendAdapter,
    BackendConfig,
    FundFlowCrawler,
    SentimentCrawler,
    ESGCrawler,
)

__all__ = [
    # 核心工厂
    "AlphaFactory",
    "AlphaFactoryConfig",
    "FactorProductionResult",
    "PortfolioOptimizationResult",
    
    # 因子引擎
    "FactorEngine",
    "FactorCalculator",
    
    # 存储
    "FactorDatabase",
    
    # 因子库
    "MarketFactorLibrary",
    "FundamentalFactorLibrary",
    "AlternativeFactorLibrary",
    "StructuredFactorLibrary",
    
    # 研究
    "FactorTester",
    "ICAnalysis",
    "LayeredBacktestResult",
    
    # 风险模型
    "BarraRiskModel",
    
    # 优化器
    "MeanVarianceOptimizer",
    "RiskParityOptimizer",
    "BlackLittermanOptimizer",
    "MaxDiversificationOptimizer",
    "FactorConstrainedOptimizer",
    "TransactionCostModel",
    
    # 另类数据
    "BackendAdapter",
    "BackendConfig",
    "FundFlowCrawler",
    "SentimentCrawler",
    "ESGCrawler",
]

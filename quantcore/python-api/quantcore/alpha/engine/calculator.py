"""
因子计算器核心模块

实现所有基础因子计算器的基类和具体实现。
"""

from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable

import numpy as np
import pandas as pd
from loguru import logger


class FactorCategory(Enum):
    """因子类别枚举"""
    MARKET = "market"
    FUNDAMENTAL = "fundamental"
    ALTERNATIVE = "alternative"
    STRUCTURED = "structured"


@dataclass
class FactorSpec:
    """因子规格定义"""
    name: str
    category: FactorCategory
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    frequency: str = "daily"
    lookback_window: int = 252
    is_neutralized: bool = True
    normalization_method: str = "zscore"

    def __hash__(self):
        return hash(self.name)


@dataclass
class FactorResult:
    """因子计算结果"""
    factor_name: str
    values: pd.Series
    metadata: Dict[str, Any] = field(default_factory=dict)
    calculation_time: float = 0.0


class BaseFactorCalculator(ABC):
    """
    因子计算器基类
    
    所有因子计算器必须继承此类并实现 calculate 方法。
    
    使用示例：
        class MyFactor(BaseFactorCalculator):
            def __init__(self):
                spec = FactorSpec(
                    name="MY_FACTOR",
                    category=FactorCategory.MARKET,
                    description="我的自定义因子"
                )
                super().__init__(spec)
            
            def calculate(self, data: pd.DataFrame, **kwargs) -> pd.Series:
                # 实现因子计算逻辑
                return data['close'].pct_change()
    """
    
    def __init__(self, spec: FactorSpec):
        self.spec = spec
    
    @abstractmethod
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.Series:
        """
        计算因子值
        
        Args:
            data: 输入数据 DataFrame（必须包含 open/high/low/close/volume 列）
            **kwargs: 其他参数
            
        Returns:
            pd.Series: 因子值序列
        """
        pass
    
    def validate_input(self, data: pd.DataFrame) -> bool:
        """验证输入数据"""
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        return all(col in data.columns for col in required_cols)
    
    def normalize(self, factor_values: pd.Series, method: str = "zscore") -> pd.Series:
        """
        标准化因子值
        
        Args:
            factor_values: 原始因子值
            method: 标准化方法 (zscore/rank/minmax)
            
        Returns:
            标准化后的因子值
        """
        if method == "zscore":
            std = factor_values.std()
            if std > 0:
                return (factor_values - factor_values.mean()) / std
            return pd.Series(0.0, index=factor_values.index)
        
        elif method == "rank":
            return factor_values.rank(pct=True) * 2 - 1
        
        elif method == "minmax":
            min_val = factor_values.min()
            max_val = factor_values.max()
            if max_val > min_val:
                return (factor_values - min_val) / (max_val - min_val)
            return pd.Series(0.5, index=factor_values.index)
        
        else:
            raise ValueError(f"未知标准化方法: {method}")
    
    def winsorize(self, factor_values: pd.Series, limits: tuple = (0.01, 0.99)) -> pd.Series:
        """
        去极值处理
        
        Args:
            factor_values: 因子值
            limits: 分位数边界
            
        Returns:
            去极值后的因子值
        """
        lower = factor_values.quantile(limits[0])
        upper = factor_values.quantile(limits[1])
        return factor_values.clip(lower, upper)
    
    def process(self, data: pd.DataFrame, **kwargs) -> FactorResult:
        """
        完整处理流程：计算 → 去极值 → 标准化
        
        Returns:
            FactorResult: 处理后的因子结果
        """
        import time
        start_time = time.time()
        
        raw_values = self.calculate(data, **kwargs)
        
        if raw_values is None or len(raw_values) == 0:
            return FactorResult(
                factor_name=self.spec.name,
                values=pd.Series(),
                metadata={"status": "empty"}
            )
        
        winsorized = self.winsorize(raw_values)
        normalized = self.normalize(winsorized, self.spec.normalization_method)
        
        calc_time = time.time() - start_time
        
        return FactorResult(
            factor_name=self.spec.name,
            values=normalized,
            metadata={
                "category": self.spec.category.value,
                "frequency": self.spec.frequency,
                "lookback": self.spec.lookback_window,
                "raw_mean": float(raw_values.mean()),
                "raw_std": float(raw_values.std()),
                "valid_count": int(raw_values.notna().sum()),
                "total_count": len(raw_values),
            },
            calculation_time=calc_time
        )


class MomentumCalculator(BaseFactorCalculator):
    """
    动量因子计算器
    
    支持多种动量定义：
    - 收益率动量：N期累计收益率
    - 偏离均线动量：价格偏离均线的程度
    - 调整后动量：考虑换手率的动量
    """
    
    def __init__(self, period: int = 20):
        spec = FactorSpec(
            name=f"MOMENTUM_{period}",
            category=FactorCategory.MARKET,
            description=f"{period}日动量因子",
            parameters={"period": period},
            frequency="daily",
            lookback_window=period
        )
        super().__init__(spec)
        self.period = period
    
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.Series:
        close = data['close']
        returns = close.pct_change()
        momentum = (1 + returns).rolling(self.period).prod() - 1
        return momentum.dropna()


class ReversalCalculator(BaseFactorCalculator):
    """
    反转因子计算器
    
    捕捉短期价格反转效应。
    """
    
    def __init__(self, period: int = 5):
        spec = FactorSpec(
            name=f"REVERSAL_{period}",
            category=FactorCategory.MARKET,
            description=f"{period}日反转因子",
            parameters={"period": period},
            frequency="daily",
            lookback_window=period
        )
        super().__init__(spec)
        self.period = period
    
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.Series:
        close = data['close']
        returns = close.pct_change()
        reversal = -returns.rolling(self.period).sum()
        return reversal.dropna()


class VolatilityCalculator(BaseFactorCalculator):
    """
    波动率因子计算器
    
    计算历史波动率，用于低波动策略。
    """
    
    def __init__(self, period: int = 20):
        spec = FactorSpec(
            name=f"VOLATILITY_{period}",
            category=FactorCategory.MARKET,
            description=f"{period}日波动率因子",
            parameters={"period": period},
            frequency="daily",
            lookback_window=period
        )
        super().__init__(spec)
        self.period = period
    
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.Series:
        returns = data['close'].pct_change()
        volatility = returns.rolling(self.period).std() * np.sqrt(252)
        return -volatility.dropna()


class LiquidityCalculator(BaseFactorCalculator):
    """
    流动性因子计算器
    
    包含：
    - Amihud 非流动性指标
    - 换手率
    - 成交额占比
    """
    
    def __init__(self, metric: str = "amihud"):
        spec = FactorSpec(
            name=f"LIQUIDITY_{metric.upper()}",
            category=FactorCategory.MARKET,
            description=f"流动性因子 ({metric})",
            parameters={"metric": metric},
            frequency="daily",
            lookback_window=20
        )
        super().__init__(spec)
        self.metric = metric
    
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.Series:
        if self.metric == "amihud":
            returns = abs(data['close'].pct_change())
            volume = data['volume'].replace(0, np.nan)
            amihud = returns / volume
            return -(amihud.rolling(20).mean()).dropna()
        
        elif self.metric == "turnover":
            if 'turnover_rate' in data.columns:
                return data['turnover_rate']
            return pd.Series()
        
        elif self.metric == "amount_ratio":
            if 'amount' in data.columns and 'total_market_cap' in data.columns:
                return data['amount'] / data['total_market_cap']
            return pd.Series()
        
        else:
            raise ValueError(f"未知的流动性指标: {self.metric}")


class ValueCalculator(BaseFactorCalculator):
    """
    价值因子计算器（基本面）
    
    基于 PE/PB/PS/PCF/EV-EBITDA 的综合价值得分。
    """
    
    def __init__(self, metrics: List[str] = None):
        if metrics is None:
            metrics = ["pe", "pb"]
        spec = FactorSpec(
            name="VALUE",
            category=FactorCategory.FUNDAMENTAL,
            description="综合价值因子",
            parameters={"metrics": metrics},
            frequency="quarterly",
            lookback_window=252
        )
        super().__init__(spec)
        self.metrics = metrics
    
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.Series:
        value_scores = []
        
        col_map = {
            'pe': 'pe_ratio',
            'pb': 'pb_ratio',
            'ps': 'ps_ttm',
            'pcf': 'pcf1_ttm',
            'ev_ebitda': 'ev_ebitda_24a'
        }
        
        for metric in self.metrics:
            col_name = col_map.get(metric)
            if col_name and col_name in data.columns:
                inv_metric = 1 / data[col_name].replace(0, np.nan)
                z_score = (inv_metric - inv_metric.mean()) / inv_metric.std()
                value_scores.append(z_score)
        
        if value_scores:
            combined_value = pd.concat(value_scores, axis=1).mean(axis=1)
            return combined_value
        
        return pd.Series()


class QualityCalculator(BaseFactorCalculator):
    """
    质量因子计算器（基本面）
    
    基于 ROE/ROIC/毛利率/净利率的综合质量得分。
    """
    
    def __init__(self, metrics: List[str] = None):
        if metrics is None:
            metrics = ["roe", "gross_margin"]
        spec = FactorSpec(
            name="QUALITY",
            category=FactorCategory.FUNDAMENTAL,
            description="综合质量因子",
            parameters={"metrics": metrics},
            frequency="quarterly",
            lookback_window=252
        )
        super().__init__(spec)
        self.metrics = metrics
    
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.Series:
        quality_scores = []
        
        col_map = {
            'roe': 'roe',
            'roic': 'roic',
            'gross_margin': 'gross_margin',
            'net_margin': 'net_profit_margin',
            'asset_turnover': 'asset_turnover'
        }
        
        for metric in self.metrics:
            col_name = col_map.get(metric)
            if col_name and col_name in data.columns:
                z_score = (data[col_name] - data[col_name].mean()) / data[col_name].std()
                quality_scores.append(z_score)
        
        if quality_scores:
            combined_quality = pd.concat(quality_scores, axis=1).mean(axis=1)
            return combined_quality
        
        return pd.Series()


class GrowthCalculator(BaseFactorCalculator):
    """
    成长因子计算器（基本面）
    
    基于营收增速/净利增速/EPS增速的成长性得分。
    """
    
    def __init__(self, metrics: List[str] = None):
        if metrics is None:
            metrics = ["revenue_growth", "net_profit_growth"]
        spec = FactorSpec(
            name="GROWTH",
            category=FactorCategory.FUNDAMENTAL,
            description="综合成长因子",
            parameters={"metrics": metrics},
            frequency="quarterly",
            lookback_window=252
        )
        super().__init__(spec)
        self.metrics = metrics
    
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.Series:
        growth_scores = []
        
        col_map = {
            'revenue_growth': 'revenue_yoy',
            'net_profit_growth': 'net_profit_yoy',
            'eps_growth': 'eps_growth_ttm',
            'revenue_qoq': 'revenue_qoq'
        }
        
        for metric in self.metrics:
            col_name = col_map.get(metric)
            if col_name and col_name in data.columns:
                z_score = (data[col_name] - data[col_name].mean()) / data[col_name].std()
                growth_scores.append(z_score)
        
        if growth_scores:
            combined_growth = pd.concat(growth_scores, axis=1).mean(axis=1)
            return combined_growth
        
        return pd.Series()


class SentimentCalculator(BaseFactorCalculator):
    """
    情感因子计算器（另类数据）
    
    使用 NLP 分析新闻、公告的情感倾向。
    """
    
    def __init__(self, source: str = "news"):
        spec = FactorSpec(
            name=f"SENTIMENT_{source.upper()}",
            category=FactorCategory.ALTERNATIVE,
            description=f"情感因子 ({source})",
            parameters={"source": source},
            frequency="daily",
            lookback_window=5
        )
        super().__init__(spec)
        self.source = source
    
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.Series:
        if 'sentiment_score' in data.columns:
            return data['sentiment_score']
        
        elif 'text' in data.columns:
            try:
                from quantcore.alpha.alternative.nlp.sentiment_analyzer import SentimentAnalyzer
                analyzer = SentimentAnalyzer()
                scores = analyzer.batch_analyze(data['text'].tolist())
                return pd.Series(scores, index=data.index)
            except ImportError:
                logger.warning("NLP 模块不可用，使用规则方法")
                return self._rule_based_sentiment(data.get('text', pd.Series()))
        
        return pd.Series()
    
    def _rule_based_sentiment(self, texts: pd.Series) -> pd.Series:
        positive_words = ['增长', '盈利', '利好', '上涨', '突破', '增持', '推荐', '买入', '超预期']
        negative_words = ['下降', '亏损', '利空', '下跌', '跌破', '减持', '卖出', '低于预期', '风险']
        
        scores = []
        for text in texts:
            text_str = str(text).lower()
            pos_count = sum(1 for w in positive_words if w in text_str)
            neg_count = sum(1 for w in negative_words if w in text_str)
            total = pos_count + neg_count
            if total > 0:
                score = (pos_count - neg_count) / total
            else:
                score = 0.0
            scores.append(score)
        
        return pd.Series(scores, index=texts.index)


class FundFlowCalculator(BaseFactorCalculator):
    """
    资金流向因子计算器（另类数据）
    
    基于主力资金净流入的因子。
    """
    
    def __init__(self, metric: str = "main_net"):
        spec = FactorSpec(
            name=f"FUND_FLOW_{metric.upper()}",
            category=FactorCategory.ALTERNATIVE,
            description=f"资金流向因子 ({metric})",
            parameters={"metric": metric},
            frequency="daily",
            lookback_window=20
        )
        super().__init__(spec)
        self.metric = metric
    
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.Series:
        if self.metric == "main_net" and 'main_net_inflow' in data.columns:
            main_net = data['main_net_inflow']
            normalized = (main_net - main_net.mean()) / main_net.std()
            return normalized
        
        elif self.metric == "northbound" and 'northbound_net' in data.columns:
            northbound = data['northbound_net']
            normalized = (northbound - northbound.mean()) / northbound.std()
            return normalized
        
        elif self.metric == "lhb" and 'lhb_net_buy' in data.columns:
            lhb = data['lhb_net_buy']
            normalized = (lhb - lhb.mean()) / lhb.std()
            return normalized
        
        return pd.Series()


class EventDriverCalculator(BaseFactorCalculator):
    """
    事件驱动因子计算器（另类数据）
    
    基于涨停/跌停/龙虎榜等事件的因子。
    """
    
    def __init__(self, event_type: str = "limit_up"):
        spec = FactorSpec(
            name=f"EVENT_{event_type.upper()}",
            category=FactorCategory.ALTERNATIVE,
            description=f"事件驱动因子 ({event_type})",
            parameters={"event_type": event_type},
            frequency="daily",
            lookback_window=5
        )
        super().__init__(spec)
        self.event_type = event_type
    
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.Series:
        if self.event_type == "limit_up" and 'is_limit_up' in data.columns:
            limit_up_days = data['is_limit_up'].rolling(5).sum()
            return limit_up_days
        
        elif self.event_type == "lhb_appear" and 'in_lhb' in data.columns:
            lhb_count = data['in_lhb'].rolling(20).sum()
            return lhb_count
        
        elif self.event_type == "institution_recommend" and 'recommend_count' in data.columns:
            rec_score = data['recommend_count'] * data['avg_rating']
            return rec_score
        
        return pd.Series()


SIZE_CALCULATOR_MAP = {}
REVERSAL_CALCULATOR_MAP = {}
VOLATILITY_CALCULATOR_MAP = {}
LIQUIDITY_CALCULATOR_MAP = {}


def register_default_calculators():
    """注册默认因子计算器到全局映射表"""
    global SIZE_CALCULATOR_MAP, REVERSAL_CALCULATOR_MAP
    global VOLATILITY_CALCULATOR_MAP, LIQUIDITY_CALCULATOR_MAP
    
    for period in [5, 10, 20, 60, 120, 250]:
        SIZE_CALCULATOR_MAP[f"MOMENTUM_{period}"] = MomentumCalculator(period)
        REVERSAL_CALCULATOR_MAP[f"REVERSAL_{period}"] = ReversalCalculator(period)
        VOLATILITY_CALCULATOR_MAP[f"VOLATILITY_{period}"] = VolatilityCalculator(period)
    
    LIQUIDITY_CALCULATOR_MAP["LIQUIDITY_AMIHUD"] = LiquidityCalculator("amihud")
    LIQUIDITY_CALCULATOR_MAP["LIQUIDITY_TURNOVER"] = LiquidityCalculator("turnover")


register_default_calculators()

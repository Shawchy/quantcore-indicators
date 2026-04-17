"""
Barra CNE5/CNE6 风险模型

实现完整的 Barra 风格风险模型，包含：
- 10 个风格因子（Beta, Momentum, Size, EarningsYield, Volatility, Growth, Value, Leverage, Liquidity, NonLinearSize）
- 行业因子
- 协方差矩阵估计 (EWMA)
- 特质风险估计
- 组合风险计算与归因

使用示例：
    from quantcore.alpha.risk import BarraRiskModel
    
    barra = BarraRiskModel()
    
    # 计算因子暴露
    exposures = barra.calculate_all_exposures(stock_data, market_returns)
    
    # 估算协方差矩阵
    cov_matrix = barra.estimate_covariance(factor_returns)
    
    # 计算组合风险
    risk = barra.calculate_portfolio_risk(weights, exposures, cov_matrix)
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, date
import numpy as np
import pandas as pd
from loguru import logger


# 申万一级行业分类
SW_INDUSTRY_CLASSIFICATION = {
    "银行": ["银行"],
    "非银金融": ["证券", "保险", "多元金融"],
    "房地产": ["房地产开发", "房地产服务"],
    "建筑装饰": ["建筑装修", "基础建设"],
    "建筑材料": ["水泥", "玻璃", "其他建材"],
    "钢铁": ["钢铁"],
    "有色金属": ["工业金属", "贵金属", "能源金属"],
    "化工": ["化学原料", "化学制品", "塑料", "橡胶"],
    "石油石化": ["油气开采", "油服工程", "炼化贸易"],
    "煤炭": ["煤炭"],
    "公用事业": ["电力", "水务", "燃气"],
    "交通运输": ["铁路公路", "物流", "港口航运", "航空机场"],
    "汽车": ["乘用车", "商用车", "汽车零部件"],
    "机械设备": ["通用设备", "专用设备", "仪器仪表", "轨交设备"],
    "电气设备": ["电源设备", "电网设备", "电机"],
    "国防军工": ["航天装备", "航海装备", "地面兵装"],
    "电子": ["半导体", "消费电子", "光学光电子", "元件", "其他电子"],
    "计算机": ["计算机设备", "软件开发", "IT服务"],
    "通信": "通信",
    "传媒": ["媒体", "游戏", "广告营销"],
    "家用电器": ["白色家电", "黑色家电", "家电零部件", "小家电"],
    "轻工制造": ["造纸", "包装印刷", "家居用品", "文娱用品"],
    "纺织服装": ["纺织制造", "服装家饰", "饰品"],
    "商贸零售": ["一般零售", "专业连锁", "商业物业经营"],
    "社会服务": ["酒店餐饮", "旅游及景区", "教育", "体育", "美容护理"],
    "食品饮料": ["白酒", "啤酒", "软饮料", "休闲食品", "食品加工", "调味发酵品", "乳品", "保健品"],
    "农林牧渔": ["种植业", "渔业", "养殖", "动物保健", "饲料"],
    "医药生物": ["化学制药", "中药", "生物制品", "医药商业", "医疗器械", "医疗服务"],
    "综合": ["综合"],
}


@dataclass
class BarraFactorExposure:
    """Barra 因子暴露"""
    symbol: str
    trade_date: date
    
    # 10 个风格因子暴露
    beta: float = 0.0
    momentum: float = 0.0
    size: float = 0.0
    earnings_yield: float = 0.0
    volatility: float = 0.0
    growth: float = 0.0
    value: float = 0.0
    leverage: float = 0.0
    liquidity: float = 0.0
    non_linear_size: float = 0.0
    
    # 特质风险
    specific_risk: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "beta": self.beta,
            "momentum": self.momentum,
            "size": self.size,
            "earnings_yield": self.earnings_yield,
            "volatility": self.volatility,
            "growth": self.growth,
            "value": self.value,
            "leverage": self.leverage,
            "liquidity": self.liquidity,
            "non_linear_size": self.non_linear_size,
        }
    
    @property
    def style_factors(self) -> np.ndarray:
        """返回风格因子向量"""
        return np.array([
            self.beta, self.momentum, self.size, self.earnings_yield,
            self.volatility, self.growth, self.value, self.leverage,
            self.liquidity, self.non_linear_size
        ])


@dataclass
class PortfolioRiskResult:
    """组合风险分析结果"""
    total_risk: float = 0.0  # 总风险（波动率）
    factor_risk: float = 0.0  # 因子风险
    specific_risk: float = 0.0  # 特质风险
    
    # 风险分解
    factor_contributions: Dict[str, float] = field(default_factory=dict)
    industry_contributions: Dict[str, float] = field(default_factory=dict)
    
    # 边际风险贡献
    marginal_contributions: Dict[str, float] = field(default_factory=dict)
    
    # 统计信息
    tracking_error: Optional[float] = None  # 跟踪误差（相对于基准）
    beta_to_market: Optional[float] = None  # 市场Beta
    information_ratio: Optional[float] = None  # 信息比率


class StyleFactorCalculator:
    """
    Barra 风格因子计算器
    
    计算 CNE5/CNE6 的 10 个风格因子的原始值。
    """
    
    STYLE_FACTORS = [
        'BETA', 'MOMENTUM', 'SIZE', 'EARNINGS_YIELD',
        'VOLATILITY', 'GROWTH', 'VALUE', 'LEVERAGE',
        'LIQUIDITY', 'NON_LINEAR_SIZE'
    ]
    
    @staticmethod
    def calculate_beta(
        stock_returns: pd.Series,
        market_returns: pd.Series,
        window: int = 252
    ) -> float:
        """
        计算 Beta 因子
        
        Beta = Cov(r_stock, r_market) / Var(r_market)
        
        Args:
            stock_returns: 股票日收益率序列
            market_returns: 市场指数日收益率序列
            window: 回看窗口
            
        Returns:
            float: Beta 值
        """
        common_idx = stock_returns.dropna().index.intersection(market_returns.dropna().index)
        
        if len(common_idx) < window * 0.8:
            return 1.0  # 默认值
        
        r_stock = stock_returns.loc[common_idx].iloc[-window:]
        r_market = market_returns.loc[common_idx].iloc[-window:]
        
        covariance = np.cov(r_stock, r_market)[0, 1]
        market_variance = np.var(r_market, ddof=1)
        
        if market_variance > 0:
            beta = covariance / market_variance
            # 限制范围 [-3, 3]
            return max(-3.0, min(3.0, beta))
        
        return 1.0
    
    @staticmethod
    def calculate_momentum(
        stock_returns: pd.Series,
        lookback: int = 504,  # 约 2 年
        lag: int = 21  # 跳过最近 1 个月
    ) -> float:
        """
        计算 Momentum 因子
        
        过去 N 天（跳过最近 M 天）的累计收益率。
        
        Args:
            stock_returns: 日收益率
            lookback: 回看期
            lag: 滞后期
            
        Returns:
            float: 动量因子值
        """
        returns = stock_returns.dropna()
        
        if len(returns) < lookback + lag:
            return 0.0
        
        momentum_period = returns.iloc[-(lookback + lag):-lag]
        
        if len(momentum_period) == 0:
            return 0.0
        
        log_returns = np.log(1 + momentum_period.replace([np.inf, -np.inf], 0))
        momentum = np.exp(log_returns.sum()) - 1
        
        return momentum
    
    @staticmethod
    def calculate_size(market_cap: float) -> float:
        """
        计算 Size 因子（对数市值）
        
        Args:
            market_cap: 总市值（元）
            
        Returns:
            float: 对数市值
        """
        if market_cap <= 0:
            return 0.0
        
        return np.log(market_cap)
    
    @staticmethod
    def calculate_non_linear_size(size_factor: float) -> float:
        """
        计算 NonLinearSize 因子（Size 的三次方）
        
        用于捕捉市值非线性效应。
        """
        return size_factor ** 3
    
    @staticmethod
    def calculate_earnings_yield(
        earnings: float,
        price: float,
        market_cap: float
    ) -> float:
        """
        计算 Earnings Yield 因子
        
        EY = Earnings / MarketCap
        
        Args:
            earnings: 净利润（或 TTM 净利润）
            price: 当前股价
            market_cap: 总市值
            
        Returns:
            float: 盈利收益率
        """
        if market_cap <= 0 or earnings <= 0:
            return 0.0
        
        ey = earnings / market_cap
        return ey
    
    @staticmethod
    def calculate_volatility(
        stock_returns: pd.Series,
        window: int = 252
    ) -> float:
        """
        计算 Volatility 因子（年化波动率）
        
        Args:
            stock_returns: 日收益率
            window: 回看窗口
            
        Returns:
            float: 年化波动率
        """
        returns = stock_returns.dropna()
        
        if len(returns) < window * 0.5:
            return 0.5  # 默认中等波动
        
        vol = returns.iloc[-window:].std() * np.sqrt(252)
        return min(vol, 5.0)  # 限制最大值
    
    @staticmethod
    def calculate_growth(
        revenue_growth: Optional[float] = None,
        profit_growth: Optional[float] = None,
        eps_growth: Optional[float] = None
    ) -> float:
        """
        计算 Growth 因子（综合成长性）
        
        综合营收增速、净利增速、EPS 增速。
        """
        growth_values = []
        
        for g in [revenue_growth, profit_growth, eps_growth]:
            if g is not None and not np.isnan(g):
                growth_values.append(g)
        
        if growth_values:
            return np.mean(growth_values)
        
        return 0.0
    
    @staticmethod
    def calculate_value(
        pe: Optional[float] = None,
        pb: Optional[float] = None,
        ps: Optional[float] = None,
        pcf: Optional[float] = None
    ) -> float:
        """
        计算 Value 因子（综合估值水平）
        
        对多个估值指标取倒数后标准化。
        """
        inv_metrics = []
        
        for val, metric in [(pe, "PE"), (pb, "PB"), (ps, "PS"), (pcf, "PCF")]:
            if val is not None and val > 0:
                inv_metrics.append(1.0 / val)
        
        if inv_metrics:
            return np.mean(inv_metrics)
        
        return 0.0
    
    @staticmethod
    def calculate_leverage(
        debt_ratio: Optional[float] = None,
        debt_to_equity: Optional[float] = None,
        interest_coverage: Optional[float] = None
    ) -> float:
        """
        计算 Leverage 因子（杠杆水平）
        
        综合资产负债率、负债权益比等。
        """
        leverage_values = []
        
        if debt_ratio is not None and not np.isnan(debt_ratio):
            leverage_values.append(debt_ratio)
        
        if debt_to_equity is not None and not np.isnan(debt_to_equity):
            leverage_values.append(min(debt_to_equity, 10))
        
        if leverage_values:
            return np.mean(leverage_values)
        
        return 0.0
    
    @staticmethod
    def calculate_liquidity(
        turnover_rate: Optional[float] = None,
        amount_ratio: Optional[float] = None,
        amihud: Optional[float] = None
    ) -> float:
        """
        计算 Liquidity 因子（流动性）
        
        综合换手率、成交额占比、Amihud 指标。
        """
        liquidity_score = 0.0
        count = 0
        
        if turnover_rate is not None and turnover_rate > 0:
            liquidity_score += min(turnover_rate / 100, 1.0)  # 归一化
            count += 1
        
        if amount_ratio is not None and amount_ratio >= 0:
            liquidity_score += min(amount_ratio * 10, 1.0)
            count += 1
        
        if amihud is not None and amihud > 0:
            # Amihud 越小，流动性越好
            liquidity_score += min(1.0 / (amihud * 100 + 0.01), 1.0)
            count += 1
        
        if count > 0:
            return liquidity_score / count
        
        return 0.5


class BarraRiskModel:
    """
    Barra CNE5/CNE6 风险模型
    
    完整的风险建模系统，包括：
    
    **风格因子（10个）：**
    1. BETA - 市场贝塔
    2. MOMENTUM - 动量
    3. SIZE - 市值
    4. EARNINGS_YIELD - 盈利收益率
    5. VOLATILITY - 波动率
    6. GROWTH - 成长性
    7. VALUE - 价值
    8. LEVERAGE - 杠杆
    9. LIQUIDITY - 流动性
    10. NON_LINEAR_SIZE - 非线性市值
    
    **行业因子：**
    基于申万/中信一级行业分类
    
    **功能：**
    - 计算因子暴露矩阵
    - 估计因子协方差矩阵
    - 计算组合风险
    - 风险归因分析
    
    使用示例：
        barra = BarraRiskModel()
        
        # 计算所有股票的因子暴露
        exposure_df = barra.calculate_exposures_for_portfolio(stock_data_dict)
        
        # 估算协方差矩阵
        cov = barra.estimate_factor_covariance(factor_returns_history)
        
        # 分析组合风险
        risk_result = barra.analyze_portfolio(weights, exposure_df, cov)
    """
    
    STYLE_FACTORS = StyleFactorCalculator.STYLE_FACTORS
    
    def __init__(self, version: str = "CNE6"):
        """
        初始化 Barra 模型
        
        Args:
            version: 版本 ("CNE5" 或 "CNE6")
        """
        self.version = version
        self._factor_covariance: Optional[pd.DataFrame] = None
        self._specific_risk: Optional[pd.Series] = None
        self._industry_list: List[str] = list(SW_INDUSTRY_CLASSIFICATION.keys())
        
        logger.info(f"Barra {version} 风险模型初始化完成")
    
    def calculate_single_exposure(
        self,
        symbol: str,
        trade_date: date,
        stock_data: Dict[str, Any],
        market_returns: pd.Series
    ) -> BarraFactorExposure:
        """
        计算单只股票的 Barra 因子暴露
        
        Args:
            symbol: 股票代码
            trade_date: 交易日期
            stock_data: 股票数据字典，需包含：
                - returns: 收益率序列
                - market_cap: 总市值
                - pe/pb/ps: 估值指标
                - roe/gross_margin: 盈利指标
                - revenue_growth/net_profit_growth: 成长指标
                - asset_liability_ratio/debt_to_equity: 杠杆指标
                - turnover_rate: 换手率
            market_returns: 市场收益率序列
            
        Returns:
            BarraFactorExposure: 因子暴露对象
        """
        calc = StyleFactorCalculator
        
        returns = stock_data.get("returns", pd.Series())
        market_cap = stock_data.get("market_cap", 0)
        
        exposure = BarraFactorExposure(
            symbol=symbol,
            trade_date=trade_date,
            
            # 风格因子
            beta=calc.calculate_beta(returns, market_returns),
            momentum=calc.calculate_momentum(returns),
            size=calc.calculate_size(market_cap),
            earnings_yield=calc.calculate_earnings_yield(
                stock_data.get("net_profit", 0),
                stock_data.get("price", 0),
                market_cap
            ),
            volatility=calc.calculate_volatility(returns),
            growth=calc.calculate_growth(
                stock_data.get("revenue_yoy"),
                stock_data.get("net_profit_yoy"),
                stock_data.get("eps_growth_ttm")
            ),
            value=calc.calculate_value(
                stock_data.get("pe_ratio"),
                stock_data.get("pb_ratio"),
                stock_data.get("ps_ttm"),
                stock_data.get("pcf1_ttm")
            ),
            leverage=calc.calculate_leverage(
                stock_data.get("asset_liability_ratio"),
                stock_data.get("debt_to_equity"),
                stock_data.get("interest_coverage")
            ),
            liquidity=calc.calculate_liquidity(
                stock_data.get("turnover_rate"),
                stock_data.get("amount") / market_cap if market_cap > 0 else None,
                stock_data.get("amihud_illiquidity")
            ),
            non_linear_size=calc.calculate_non_linear_size(
                calc.calculate_size(market_cap)
            )
        )
        
        return exposure
    
    def calculate_all_exposures(
        self,
        stocks_data: Dict[str, Dict[str, Any]],
        trade_date: date,
        market_returns: pd.Series
    ) -> pd.DataFrame:
        """
        批量计算多只股票的因子暴露
        
        Args:
            stocks_data: {symbol: stock_data}
            trade_date: 交易日期
            market_returns: 市场收益率
            
        Returns:
            DataFrame: 因子暴露矩阵 (index=symbol, columns=factors)
        """
        exposures = {}
        
        for symbol, data in stocks_data.items():
            try:
                exp = self.calculate_single_exposure(symbol, trade_date, data, market_returns)
                row = {
                    "BETA": exp.beta,
                    "MOMENTUM": exp.momentum,
                    "SIZE": exp.size,
                    "EARNINGS_YIELD": exp.earnings_yield,
                    "VOLATILITY": exp.volatility,
                    "GROWTH": exp.growth,
                    "VALUE": exp.value,
                    "LEVERAGE": exp.leverage,
                    "LIQUIDITY": exp.liquidity,
                    "NON_LINEAR_SIZE": exp.non_linear_size,
                }
                exposures[symbol] = row
                
            except Exception as e:
                logger.debug(f"计算 {symbol} 因子暴露失败: {e}")
                continue
        
        df = pd.DataFrame.from_dict(exposures, orient="index")
        return df
    
    def normalize_exposures(self, exposure_df: pd.DataFrame) -> pd.DataFrame:
        """
        标准化因子暴露（横截面标准化）
        
        对每个因子进行：
        1. 去极值（Winsorize）
        2. 标准化（Z-score）
        
        Args:
            exposure_df: 原始因子暴露矩阵
            
        Returns:
            DataFrame: 标准化后的因子暴露
        """
        normalized = exposure_df.copy()
        
        for col in normalized.columns:
            values = normalized[col].dropna()
            
            if len(values) == 0 or values.std() == 0:
                continue
            
            # 去极值
            lower = values.quantile(0.01)
            upper = values.quantile(0.99)
            clipped = values.clip(lower, upper)
            
            # 标准化
            z_score = (clipped - clipped.mean()) / clipped.std()
            normalized[col] = z_score
        
        return normalized
    
    def estimate_factor_covariance(
        self,
        factor_returns: pd.DataFrame,
        method: str = "ewma",
        lambda_decay: float = 0.94,
        window: int = 252
    ) -> pd.DataFrame:
        """
        估计因子协方差矩阵
        
        支持：
        - EWMA: 指数加权移动平均
        - Simple: 简单滚动窗口
        - Newey-West: 异方差稳健估计
        
        Args:
            factor_returns: 因子收益率时间序列 (date × factor)
            method: 估计方法
            lambda_decay: EWMA 衰减因子
            window: 回看窗口
            
        Returns:
            DataFrame: 协方差矩阵 (factor × factor)
        """
        factors = list(self.STYLE_FACTORS)
        available_factors = [f for f in factors if f in factor_returns.columns]
        
        if len(available_factors) == 0:
            logger.warning("没有可用的因子数据用于协方差估计")
            return pd.DataFrame()
        
        ret = factor_returns[available_factors].dropna()
        
        if method == "ewma":
            # EWMA 协方差
            n = min(len(ret), window)
            weights = np.array([lambda_decay ** i for i in range(n)])
            weights = weights / weights.sum()
            
            centered = ret.iloc[-n:] - ret.iloc[-n:].mean()
            
            cov_matrix = np.zeros((len(available_factors), len(available_factors)))
            
            for i in range(n):
                w = weights[n - 1 - i]
                r = centered.iloc[-(i+1)].values.reshape(-1, 1)
                cov_matrix += w * (r @ r.T)
            
            result = pd.DataFrame(
                cov_matrix,
                index=available_factors,
                columns=available_factors
            )
            
        elif method == "simple":
            # 简单协方差
            result = ret.tail(window).cov() * 252  # 年化
            
        else:
            raise ValueError(f"未知协方差估计方法: {method}")
        
        self._factor_covariance = result
        return result
    
    def estimate_specific_risk(
        self,
        residual_returns: pd.DataFrame,
        window: int = 60
    ) -> pd.Series:
        """
        估计特质风险（残差风险）
        
        Args:
            residual_returns: 残差收益率 (date × symbol)
            window: 回看窗口
            
        Returns:
            Series: 各股票特质风险
        """
        specific_vol = residual_returns.tail(window).std() * np.sqrt(252)
        
        # 限制范围
        specific_vol = specific_vol.clip(lower=0.05, upper=2.0)
        
        self._specific_risk = specific_vol
        return specific_vol
    
    def calculate_portfolio_risk(
        self,
        weights: pd.Series,
        factor_exposures: pd.DataFrame,
        factor_covariance: pd.DataFrame,
        specific_risk: Optional[pd.Series] = None
    ) -> PortfolioRiskResult:
        """
        计算组合风险
        
        总风险² = 因子风险² + 特质风险²
        
        因子风险 = w' × B × F × B' × w
        特质风险 = Σ(w_i² × σ_i²)
        
        Args:
            weights: 组合权重 (symbol → weight)
            factor_exposures: 因子暴露矩阵 (symbol × factor)
            factor_covariance: 因子协方差矩阵
            specific_risk: 特质风险序列
            
        Returns:
            PortfolioRiskResult: 风险分析结果
        """
        # 对齐数据
        common_symbols = weights.index.intersection(factor_exposures.index)
        common_factors = factor_exposures.columns.intersection(factor_covariance.columns)
        
        if len(common_symbols) == 0:
            return PortfolioRiskResult(total_risk=0.0)
        
        w = weights.loc[common_symbols].values
        B = factor_exposures.loc[common_symbols, common_factors].values
        F = factor_covariance.loc[common_factors, common_factors].values
        
        # 因子风险
        portfolio_factor_exposure = (w * B.T).sum(axis=1)  # 1 × n_factors
        factor_variance = portfolio_factor_exposure @ F @ portfolio_factor_exposure
        factor_risk = np.sqrt(max(0, factor_variance))
        
        # 特质风险
        if specific_risk is not None:
            spec_common = specific_risk.loc[common_symbols]
            specific_variance = (w**2 * spec_common.values**2).sum()
            specific_risk_val = np.sqrt(max(0, specific_variance))
        else:
            specific_risk_val = 0.0
            specific_variance = 0.0
        
        # 总风险
        total_risk = np.sqrt(max(0, factor_variance + specific_variance))
        
        # 因子贡献分解
        factor_contrib = {}
        marginal_contrib = {}
        
        for i, factor in enumerate(common_factors):
            contrib = portfolio_factor_exposure[i]**2 * F[i, i]
            factor_contrib[factor] = np.sqrt(abs(contrib)) * np.sign(contrib)
            
            # 边际风险贡献
            marginal = portfolio_factor_exposure[i] * (F @ portfolio_factor_exposure)[i] / total_risk if total_risk > 0 else 0
            marginal_contrib[factor] = marginal
        
        return PortfolioRiskResult(
            total_risk=float(total_risk),
            factor_risk=float(factor_risk),
            specific_risk=float(specific_risk_val),
            factor_contributions={k: float(v) for k, v in factor_contrib.items()},
            marginal_contributions={k: float(v) for k, v in marginal_contrib.items()}
        )
    
    def analyze_portfolio(
        self,
        weights: pd.Series,
        stocks_data: Dict[str, Dict[str, Any]],
        trade_date: date,
        market_returns: pd.Series,
        benchmark_weights: Optional[pd.Series] = None
    ) -> PortfolioRiskResult:
        """
        完整的组合风险分析
        
        Args:
            weights: 组合权重
            stocks_data: 股票数据
            trade_date: 交易日期
            market_returns: 市场收益
            benchmark_weights: 基准权重（可选，用于计算跟踪误差）
            
        Returns:
            PortfolioRiskResult: 完整风险分析
        """
        # 计算因子暴露
        exposures = self.calculate_all_exposures(stocks_data, trade_date, market_returns)
        norm_exposures = self.normalize_exposures(exposures)
        
        # 使用默认协方差（如果未提供）
        if self._factor_covariance is None:
            # 使用单位矩阵作为默认
            factors = list(self.STYLE_FACTORS)
            self._factor_covariance = pd.DataFrame(
                np.eye(len(factors)) * 0.04,  # 默认年化波动 20%
                index=factors,
                columns=factors
            )
        
        # 计算组合风险
        result = self.calculate_portfolio_risk(
            weights, norm_exposures, self._factor_covariance
        )
        
        # 如果有基准，计算跟踪误差
        if benchmark_weights is not None:
            active_weights = weights.sub(benchmark_weights, fill_value=0)
            active_risk = self.calculate_portfolio_risk(
                active_weights, norm_exposures, self._factor_covariance
            )
            result.tracking_error = active_risk.total_risk
        
        return result
    
    def get_factor_summary(self) -> Dict[str, str]:
        """获取因子说明"""
        descriptions = {
            "BETA": "市场贝塔 - 衡量股票对市场波动的敏感度",
            "MOMENTUM": "动量 - 过去收益率（排除近期）",
            "SIZE": "市值 - 对数总市值",
            "EARNINGS_YIELD": "盈利收益率 - 净利润/市值",
            "VOLATILITY": "波动率 - 历史价格波动程度",
            "GROWTH": "成长性 - 营收/利润增长速度",
            "VALUE": "价值 - 估值水平（PE/PB/PS综合）",
            "LEVERAGE": "杠杆 - 财务杠杆水平",
            "LIQUIDITY": "流动性 - 交易活跃程度",
            "NON_LINEAR_SIZE": "非线性市值 - 市值的立方"
        }
        return descriptions


class CovarianceEstimator:
    """协方差矩阵估计器"""
    
    @staticmethod
    def ewma_covariance(returns: pd.DataFrame, lambda_decay: float = 0.94) -> pd.DataFrame:
        """EWMA 协方差估计"""
        n = len(returns)
        weights = np.array([lambda_decay ** (n - 1 - i) for i in range(n)])
        weights = weights / weights.sum()
        
        mean = returns.mean()
        centered = returns - mean
        
        cov = np.zeros((len(returns.columns), len(returns.columns)))
        
        for i in range(n):
            r = centered.iloc[i].values.reshape(-1, 1)
            cov += weights[i] * (r @ r.T)
        
        return pd.DataFrame(cov, index=returns.columns, columns=returns.columns)
    
    @staticmethod
    def newey_west_covariance(returns: pd.DataFrame, lag: int = 20) -> pd.DataFrame:
        """Newey-West 异方差稳健协方差"""
        try:
            import statsmodels.api as sm
            cov = sm.regression.linear_model.OLS(
                returns.values[:, 0],
                sm.add_constant(returns.values[:, 1:])
            ).fit(cov_type='HAC', cov_kwds={'maxlags': lag}).cov_HC0
            return pd.DataFrame(cov)
        except ImportError:
            # fallback to simple covariance
            return returns.cov()


class SpecificRiskEstimator:
    """特质风险估计器"""
    
    @staticmethod
    def estimate_from_residuals(residuals: pd.DataFrame, window: int = 60) -> pd.Series:
        """从残差估计特质风险"""
        return residuals.tail(window).std() * np.sqrt(252)
    
    @staticmethod
    def structural_model(
        factor_exposures: pd.DataFrame,
        market_cap: pd.Series,
        volume: Optional[pd.Series] = None
    ) -> pd.Series:
        """
        结构化特质风险模型
        
        特质风险 = f(市值, 流动性, 因子暴露偏离度)
        """
        # 基于市值的基准风险
        log_cap = np.log(market_cap.clip(lower=1e6))
        base_risk = 0.3 - 0.02 * (log_cap - log_cap.mean()) / log_cap.std()
        base_risk = base_risk.clip(lower=0.05, upper=1.0)
        
        # 流动性调整
        if volume is not None:
            turnover = volume / market_cap
            adj = 1.0 - 0.3 * turnover.rank(pct=True).clip(0, 1)
            base_risk = base_risk * adj
        
        return base_risk


class RiskAttribution:
    """风险归因分析"""
    
    @staticmethod
    def decompose_risk(
        portfolio_risk: PortfolioRiskResult
    ) -> Dict[str, Any]:
        """
        分解风险来源
        
        Returns:
            Dict: {
                "total_risk": 总风险,
                "factor_risk_pct": 因子风险占比,
                "specific_risk_pct": 特质风险占比,
                "top_factor_risks": 主要因子风险贡献排序,
                "risk_concentration": 风险集中度 (HHI)
            }
        """
        total = portfolio_risk.total_risk
        
        if total == 0:
            return {"total_risk": 0, "error": "无风险数据"}
        
        factor_pct = portfolio_risk.factor_risk / total * 100
        specific_pct = portfolio_risk.specific_risk / total * 100
        
        # 排序因子贡献
        sorted_contrib = sorted(
            portfolio_risk.factor_contributions.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        
        # 风险集中度 (Herfindahl-Hirschman Index)
        contributions = list(portfolio_risk.factor_contributions.values())
        if contributions:
            total_contrib = sum(abs(c) for c in contributions)
            if total_contrib > 0:
                hhi = sum((c / total_contrib)**2 for c in map(abs, contributions))
            else:
                hhi = 0
        else:
            hhi = 0
        
        return {
            "total_risk": total,
            "factor_risk": portfolio_risk.factor_risk,
            "specific_risk": portfolio_risk.specific_risk,
            "factor_risk_pct": round(factor_pct, 2),
            "specific_risk_pct": round(specific_pct, 2),
            "top_factor_risks": sorted_contrib[:5],
            "risk_concentration": round(hhi, 4),
            "marginal_contributions": dict(sorted(
                portfolio_risk.marginal_contributions.items(),
                key=lambda x: abs(x[1]),
                reverse=True
            ))
        }

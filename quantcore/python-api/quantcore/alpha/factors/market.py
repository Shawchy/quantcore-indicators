"""
Market Data Factor (市场量价因子库)

完整的量价因子集合：
- 动量因子 (Momentum)
- 反转因子 (Reversal)
- 波动率因子 (Volatility) - 低波动
- 流动性因子 (Liquidity)
- 价量关系因子
- 技术指标因子
- 资金流向因子
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from loguru import logger


@dataclass
class MarketFactorConfig:
    """市场因子配置"""
    momentum_periods: List[int] = None  # [5, 10, 20, 60, 120, 250]
    reversal_periods: List[int] = None  # [1, 5, 10]
    volatility_periods: List[int] = None  # [5, 20, 60]
    liquidity_metrics: List[str] = None  # ["amihud", "turnover", "amount_ratio"]


class MarketFactorLibrary:
    """
    市场量价因子库
    
    提供完整的市场数据因子计算方法，包括：
    
    **动量类：**
    - MOMENTUM_N: N日累计收益率
    
    **反转类：**
    - REVERSAL_N: N日收益率取反（短期反转）
    
    **波动率类（低波动）：**
    - VOLATILITY_N: 历史波动率的负值
    
    **流动性类：**
    - LIQUIDITY_AMIHUD: Amihud非流动性指标取负
    - LIQUIDITY_TURNOVER: 换手率
    - LIQUIDITY_AMOUNT_RATIO: 成交额/市值比
    
    **价量关系：**
    - PRICE_VOLUME_CORR: 价量相关系数
    - VOLUME_TREND: 成交量趋势
    - VWAP_DEVIATION: VWAP偏离度
    
    **技术指标：**
    - RSI_N: 相对强弱指标标准化
    - MACD: MACD柱状图值
    - BOLL_POSITION: 布林带位置
    
    **资金流向：**
    - MAIN_NET_INFLOW: 主力净流入标准化
    - NORTHBOUND_NET: 北向资金净流入
    - LARGE_ORDER_RATIO: 大单占比
    
    使用示例：
        library = MarketFactorLibrary()
        
        # 计算所有市场因子
        factors = library.calculate_all(data)
        
        # 计算特定类别
        momentum = library.calculate_momentum(data, periods=[20, 60])
    """
    
    def __init__(self, config: Optional[MarketFactorConfig] = None):
        self.config = config or MarketFactorConfig()
        
        if self.config.momentum_periods is None:
            self.config.momentum_periods = [5, 10, 20, 60, 120, 250]
        if self.config.reversal_periods is None:
            self.config.reversal_periods = [1, 5, 10]
        if self.config.volatility_periods is None:
            self.config.volatility_periods = [5, 20, 60]
        if self.config.liquidity_metrics is None:
            self.config.liquidity_metrics = ["amihud", "turnover", "amount_ratio"]
    
    def calculate_all(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有市场因子
        
        Args:
            data: 包含 open/high/low/close/volume 的 DataFrame
            
        Returns:
            DataFrame: 所有市场因子
        """
        results = {}
        
        # 动量因子
        momentum = self.calculate_momentum(data)
        results.update(momentum)
        
        # 反转因子
        reversal = self.calculate_reversal(data)
        results.update(reversal)
        
        # 波动率因子
        volatility = self.calculate_volatility(data)
        results.update(volatility)
        
        # 流动性因子
        liquidity = self.calculate_liquidity(data)
        results.update(liquidity)
        
        # 价量关系
        price_volume = self.calculate_price_volume(data)
        results.update(price_volume)
        
        # 技术指标
        technical = self.calculate_technical(data)
        results.update(technical)
        
        return pd.DataFrame(results)
    
    def calculate_momentum(self, data: pd.DataFrame, periods: List[int] = None) -> Dict[str, pd.Series]:
        """
        计算动量因子
        
        Args:
            data: 价格数据
            periods: 回看期数列表
            
        Returns:
            {factor_name: Series}
        """
        periods = periods or self.config.momentum_periods
        close = data['close']
        returns = close.pct_change()
        
        factors = {}
        for period in periods:
            name = f"MOMENTUM_{period}"
            
            # 累计收益
            momentum = (1 + returns).rolling(period).prod() - 1
            
            # 标准化
            std = momentum.std()
            if std > 0:
                normalized = (momentum - momentum.mean()) / std
            else:
                normalized = momentum * 0
            
            factors[name] = normalized.dropna()
        
        return factors
    
    def calculate_reversal(self, data: pd.DataFrame, periods: List[int] = None) -> Dict[str, pd.Series]:
        """
        计算反转因子（短期）
        
        Args:
            data: 价格数据
            periods: 回看期数列表
            
        Returns:
            {factor_name: Series}
        """
        periods = periods or self.config.reversal_periods
        close = data['close']
        returns = close.pct_change()
        
        factors = {}
        for period in periods:
            name = f"REVERSAL_{period}"
            
            # 反转效应（短期收益为负，预期未来上涨）
            reversal = -returns.rolling(period).sum()
            
            # 标准化
            std = reversal.std()
            if std > 0:
                normalized = (reversal - reversal.mean()) / std
            else:
                normalized = reversal * 0
            
            factors[name] = normalized.dropna()
        
        return factors
    
    def calculate_volatility(self, data: pd.DataFrame, periods: List[int] = None) -> Dict[str, pd.Series]:
        """
        计算波动率因子（低波动策略）
        
        Args:
            data: 价格数据
            periods: 回看期数列表
            
        Returns:
            {factor_name: Series} (负值表示低波动=好)
        """
        periods = periods or self.config.volatility_periods
        returns = data['close'].pct_change()
        
        factors = {}
        for period in periods:
            name = f"VOLATILITY_{period}"
            
            # 年化波动率
            volatility = returns.rolling(period).std() * np.sqrt(252)
            
            # 取负值（低波动=好）
            neg_volatility = -volatility
            
            # 标准化
            std = neg_volatility.std()
            if std > 0:
                normalized = (neg_volatility - neg_volatility.mean()) / std
            else:
                normalized = neg_volatility * 0
            
            factors[name] = normalized.dropna()
        
        return factors
    
    def calculate_liquidity(self, data: pd.DataFrame, metrics: List[str] = None) -> Dict[str, pd.Series]:
        """
        计算流动性因子
        
        Args:
            data: 包含 volume/amount/turnover 的 DataFrame
            metrics: 要计算的指标列表
            
        Returns:
            {factor_name: Series}
        """
        metrics = metrics or self.config.liquidity_metrics
        factors = {}
        
        for metric in metrics:
            if metric == "amihud":
                # Amihud 非流动性指标
                returns = abs(data['close'].pct_change())
                volume = data['volume'].replace(0, np.nan)
                amihud = returns / volume
                
                # 取负值（高流动性=好）
                neg_amihud = -(amihud.rolling(20).mean())
                
                std = neg_amihud.std()
                if std > 0:
                    factors["LIQUIDITY_AMIHUD"] = ((neg_amihud - neg_amihud.mean()) / std).dropna()
            
            elif metric == "turnover" and 'turnover_rate' in data.columns:
                turnover = data['turnover_rate']
                std = turnover.std()
                if std > 0:
                    factors["LIQUIDITY_TURNOVER"] = ((turnover - turnover.mean()) / std).dropna()
            
            elif metric == "amount_ratio" and 'amount' in data.columns and 'total_market_cap' in data.columns:
                ratio = data['amount'] / data['total_market_cap'].replace(0, np.nan)
                std = ratio.std()
                if std > 0:
                    factors["LIQUIDITY_AMOUNT_RATIO"] = ((ratio - ratio.mean()) / std).dropna()
        
        return factors
    
    def calculate_price_volume(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        计算价量关系因子
        
        包括：
        - 价量相关系数
        - 成交量趋势
        - VWAP偏离度
        """
        factors = {}
        close = data['close']
        volume = data['volume']
        amount = data.get('amount', close * volume)
        
        # 1. 价量相关系数（20日滚动）
        price_returns = close.pct_change()
        volume_changes = volume.pct_change()
        
        corr = price_returns.rolling(20).corr(volume_changes)
        std = corr.std() if corr.std() > 0 else 1
        factors["PRICE_VOLUME_CORR"] = ((corr - corr.mean()) / std).dropna()
        
        # 2. 成交量趋势（20日线性回归斜率）
        vol_trend = volume.rolling(20).apply(
            lambda x: np.polyfit(range(len(x)), x.values, 1)[0]
        ) if len(volume) >= 20 else pd.Series(dtype=float)
        
        std = vol_trend.std() if len(vol_trend) > 0 and vol_trend.std() > 0 else 1
        factors["VOLUME_TREND"] = ((vol_trend - vol_trend.mean()) / std).dropna()
        
        # 3. VWAP偏离度
        vwap = (amount).rolling(20).sum() / (volume.rolling(20).sum()).replace(0, np.nan)
        deviation = (close - vwap) / vwap.replace([np.inf, -np.inf], np.nan)
        
        std = deviation.std() if deviation.std() > 0 else 1
        factors["VWAP_DEVIATION"] = ((deviation - deviation.mean()) / std).dropna()
        
        return factors
    
    def calculate_technical(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        计算技术指标因子
        
        包括：
        - RSI (相对强弱指标)
        - MACD (指数平滑异同移动平均线)
        - BOLL_POSITION (布林带位置)
        """
        factors = {}
        close = data['close']
        
        # 1. RSI (14日)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        
        # 标准化为 [-1, 1]
        rsi_normalized = (rsi - 50) / 50
        factors["RSI_14"] = rsi_normalized.dropna()
        
        # 2. MACD 柱状图
        ema12 = close.ewm(span=12).mean()
        ema26 = close.ewm(span=26).mean()
        dif = ema12 - ema26
        dea = dif.ewm(span=9).mean()
        macd_hist = (dif - dea) * 2  # 柱状图
        
        std = macd_hist.std() if macd_hist.std() > 0 else 1
        factors["MACD_HIST"] = ((macd_hist - macd_hist.mean()) / std).dropna()
        
        # 3. 布林带位置
        ma20 = close.rolling(20).mean()
        std20 = close.rolling(20).std()
        upper = ma20 + 2 * std20
        lower = ma20 - 2 * std20
        
        boll_position = (close - lower) / (upper - lower).replace(0, np.nan)
        boll_position = boll_position.clip(-1, 1)
        
        factors["BOLL_POSITION"] = boll_position.dropna()
        
        return factors
    
    def calculate_fund_flow(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        计算资金流向因子
        
        需要数据包含：
        - main_net_inflow: 主力净流入
        - northbound_net: 北向资金
        - super_large_order: 超大单净流入
        - large_order: 大单净流入
        """
        factors = {}
        
        # 主力净流入
        if 'main_net_inflow' in data.columns:
            main = data['main_net_inflow']
            std = main.std() if main.std() > 0 else 1
            factors["MAIN_NET_INFLOW"] = ((main - main.mean()) / std).dropna()
        
        # 北向资金
        if 'northbound_net' in data.columns:
            nb = data['northbound_net']
            std = nb.std() if nb.std() > 0 else 1
            factors["NORTHBOUND_NET"] = ((nb - nb.mean()) / std).dropna()
        
        # 大单占比
        if 'super_large_order' in data.columns and 'large_order' in data.columns:
            large_total = data['super_large_order'] + data['large_order']
            total_flow = data.get('main_net_inflow', large_total)
            ratio = large_total / total_flow.abs().replace(0, np.nan)
            
            std = ratio.std() if ratio.std() > 0 else 1
            factors["LARGE_ORDER_RATIO"] = ((ratio - ratio.mean()) / std).dropna()
        
        return factors
    
    def list_available_factors(self) -> List[Dict[str, str]]:
        """列出所有可用的市场因子"""
        factors = []
        
        for period in self.config.momentum_periods:
            factors.append({
                "name": f"MOMENTUM_{period}",
                "category": "momentum",
                "description": f"{period}日动量因子"
            })
        
        for period in self.config.reversal_periods:
            factors.append({
                "name": f"REVERSAL_{period}",
                "category": "reversal",
                "description": f"{period}日反转因子"
            })
        
        for period in self.config.volatility_periods:
            factors.append({
                "name": f"VOLATILITY_{period}",
                "category": "volatility",
                "description": f"{period}日波动率因子（低波动）"
            })
        
        factors.extend([
            {"name": "LIQUIDITY_AMIHUD", "category": "liquidity", "description": "Amihud非流动性"},
            {"name": "LIQUIDITY_TURNOVER", "category": "liquidity", "description": "换手率"},
            {"name": "PRICE_VOLUME_CORR", "category": "price_volume", "description": "价量相关系数"},
            {"name": "VOLUME_TREND", "category": "price_volume", "description": "成交量趋势"},
            {"name": "RSI_14", "category": "technical", "description": "相对强弱指标"},
            {"name": "MACD_HIST", "category": "technical", "description": "MACD柱状图"},
            {"name": "BOLL_POSITION", "category": "technical", "description": "布林带位置"},
            {"name": "MAIN_NET_INFLOW", "category": "fund_flow", "description": "主力净流入"},
            {"name": "NORTHBOUND_NET", "category": "fund_flow", "description": "北向资金净流入"},
        ])
        
        return factors

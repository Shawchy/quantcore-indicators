# -*- coding: utf-8 -*-
"""
经典策略模板库

包含 20+ 个经典量化策略模板：
- 趋势跟踪策略
- 均值回归策略
- 动量策略
- 突破策略
- 多因子策略
"""

from typing import List, Dict, Any, Optional
from ..strategy.base import Strategy
from ..core import Bar
from ..indicators import (
    ma, ema, macd, rsi, bollinger_bands, kdj, atr,
    adx, sar, stoch, roc, mfi, aroon, vwap, ppo, trix, dmi
)
from ..logger import get_logger


# ==================== 趋势跟踪策略 ====================

class DualMovingAverageStrategy(Strategy):
    """
    双均线策略（最经典的趋势跟踪策略）
    
    逻辑：
    - 快线上穿慢线：金叉买入
    - 快线下穿慢线：死叉卖出
    
    参数：
    - fast_period: 快速均线周期（默认 5）
    - slow_period: 慢速均线周期（默认 20）
    """
    
    def __init__(self, fast_period: int = 5, slow_period: int = 20):
        super().__init__()
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.prices = []
        self.position = 0
    
    def on_init(self, engine):
        super().on_init(engine)
        self.logger = get_logger("QuantCore.DualMA")
    
    def on_bar(self, bar, engine):
        self.prices.append(bar.close)
        
        if len(self.prices) < self.slow_period:
            return
        
        # 计算均线
        fast_ma = ma(self.prices, self.fast_period)[-1]
        slow_ma = ma(self.prices, self.slow_period)[-1]
        prev_fast_ma = ma(self.prices[:-1], self.fast_period)[-1] if len(self.prices) > 1 else fast_ma
        prev_slow_ma = ma(self.prices[:-1], self.slow_period)[-1] if len(self.prices) > 1 else slow_ma
        
        # 金叉：快线从下向上穿越慢线
        if prev_fast_ma <= prev_slow_ma and fast_ma > slow_ma and self.position == 0:
            portfolio = engine.get_portfolio()
            volume = int(portfolio.cash * 0.95 / bar.close / 100) * 100
            if volume >= 100:
                self.buy(bar.symbol, bar.close, volume, order_type="market")
                self.position = volume
                self.logger.info(f"金叉买入：{volume}股 @ {bar.close:.2f}")
        
        # 死叉：快线从上向下穿越慢线
        elif prev_fast_ma >= prev_slow_ma and fast_ma < slow_ma and self.position > 0:
            self.sell(bar.symbol, bar.close, self.position, order_type="market")
            self.logger.info(f"死叉卖出：{self.position}股 @ {bar.close:.2f}")
            self.position = 0


class MACDTrendStrategy(Strategy):
    """
    MACD 趋势策略
    
    逻辑：
    - MACD > 0：多头市场，买入
    - MACD < 0：空头市场，卖出
    
    参数：
    - fast_period: 快速 EMA 周期（默认 12）
    - slow_period: 慢速 EMA 周期（默认 26）
    - signal_period: 信号线周期（默认 9）
    """
    
    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        super().__init__()
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.prices = []
        self.position = 0
    
    def on_init(self, engine):
        super().on_init(engine)
        self.logger = get_logger("QuantCore.MACD")
    
    def on_bar(self, bar, engine):
        self.prices.append(bar.close)
        
        if len(self.prices) < self.slow_period:
            return
        
        # 计算 MACD
        macd_result = macd(self.prices, self.fast_period, self.slow_period, self.signal_period)
        macd_value = macd_result['macd'][-1]
        
        # MACD > 0 买入
        if macd_value > 0 and self.position == 0:
            portfolio = engine.get_portfolio()
            volume = int(portfolio.cash * 0.95 / bar.close / 100) * 100
            if volume >= 100:
                self.buy(bar.symbol, bar.close, volume, order_type="market")
                self.position = volume
                self.logger.info(f"MACD 多头买入：{volume}股 @ {bar.close:.2f}")
        
        # MACD < 0 卖出
        elif macd_value < 0 and self.position > 0:
            self.sell(bar.symbol, bar.close, self.position, order_type="market")
            self.logger.info(f"MACD 空头卖出：{self.position}股 @ {bar.close:.2f}")
            self.position = 0


class ADXTrendStrategy(Strategy):
    """
    ADX 趋势强度策略
    
    逻辑：
    - ADX > 25：强趋势，使用趋势策略
    - ADX < 25：震荡市场，使用震荡策略
    
    参数：
    - adx_period: ADX 周期（默认 14）
    - adx_threshold: ADX 阈值（默认 25）
    """
    
    def __init__(self, adx_period: int = 14, adx_threshold: float = 25):
        super().__init__()
        self.adx_period = adx_period
        self.adx_threshold = adx_threshold
        self.prices = []
        self.highs = []
        self.lows = []
        self.position = 0
    
    def on_init(self, engine):
        super().on_init(engine)
        self.logger = get_logger("QuantCore.ADX")
    
    def on_bar(self, bar, engine):
        self.prices.append(bar.close)
        self.highs.append(bar.high)
        self.lows.append(bar.low)
        
        if len(self.prices) < self.adx_period + 10:
            return
        
        # 计算 ADX
        adx_values = adx(self.highs, self.lows, self.prices, self.adx_period)
        adx_value = adx_values[-1]
        
        # ADX > 25，强趋势，使用均线策略
        if adx_value > self.adx_threshold:
            if len(self.prices) >= 20:
                fast_ma = ma(self.prices, 5)[-1]
                slow_ma = ma(self.prices, 20)[-1]
                
                if fast_ma > slow_ma and self.position == 0:
                    portfolio = engine.get_portfolio()
                    volume = int(portfolio.cash * 0.95 / bar.close / 100) * 100
                    if volume >= 100:
                        self.buy(bar.symbol, bar.close, volume, order_type="market")
                        self.position = volume
                        self.logger.info(f"ADX 强趋势买入：{volume}股 @ {bar.close:.2f}")
                
                elif fast_ma < slow_ma and self.position > 0:
                    self.sell(bar.symbol, bar.close, self.position, order_type="market")
                    self.logger.info(f"ADX 强趋势卖出：{self.position}股 @ {bar.close:.2f}")
                    self.position = 0


# ==================== 均值回归策略 ====================

class RSIMeanReversionStrategy(Strategy):
    """
    RSI 均值回归策略（超买超卖）
    
    逻辑：
    - RSI < 30：超卖，买入
    - RSI > 70：超买，卖出
    
    参数：
    - period: RSI 周期（默认 14）
    - oversold: 超卖阈值（默认 30）
    - overbought: 超买阈值（默认 70）
    """
    
    def __init__(self, period: int = 14, oversold: float = 30, overbought: float = 70):
        super().__init__()
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.prices = []
        self.position = 0
    
    def on_init(self, engine):
        super().on_init(engine)
        self.logger = get_logger("QuantCore.RSI")
    
    def on_bar(self, bar, engine):
        self.prices.append(bar.close)
        
        if len(self.prices) < self.period + 1:
            return
        
        # 计算 RSI
        rsi_values = rsi(self.prices, self.period)
        rsi_value = rsi_values[-1]
        
        # RSI < 30 超卖买入
        if rsi_value < self.oversold and self.position == 0:
            portfolio = engine.get_portfolio()
            volume = int(portfolio.cash * 0.95 / bar.close / 100) * 100
            if volume >= 100:
                self.buy(bar.symbol, bar.close, volume, order_type="market")
                self.position = volume
                self.logger.info(f"RSI 超卖买入：{volume}股 @ {bar.close:.2f}, RSI={rsi_value:.2f}")
        
        # RSI > 70 超买卖出
        elif rsi_value > self.overbought and self.position > 0:
            self.sell(bar.symbol, bar.close, self.position, order_type="market")
            self.logger.info(f"RSI 超买卖出：{self.position}股 @ {bar.close:.2f}, RSI={rsi_value:.2f}")
            self.position = 0


class BollingerMeanReversionStrategy(Strategy):
    """
    布林带均值回归策略
    
    逻辑：
    - 触及下轨：买入（价格偏低）
    - 回归中轨：卖出（价格回归）
    
    参数：
    - period: 周期（默认 20）
    - std_dev: 标准差倍数（默认 2.0）
    """
    
    def __init__(self, period: int = 20, std_dev: float = 2.0):
        super().__init__()
        self.period = period
        self.std_dev = std_dev
        self.prices = []
        self.position = 0
    
    def on_init(self, engine):
        super().on_init(engine)
        self.logger = get_logger("QuantCore.BOLL")
    
    def on_bar(self, bar, engine):
        self.prices.append(bar.close)
        
        if len(self.prices) < self.period:
            return
        
        # 计算布林带
        boll = bollinger_bands(self.prices, self.period, self.std_dev)
        lower = boll['lower'][-1]
        middle = boll['middle'][-1]
        
        # 触及下轨买入
        if bar.close < lower and self.position == 0:
            portfolio = engine.get_portfolio()
            volume = int(portfolio.cash * 0.95 / bar.close / 100) * 100
            if volume >= 100:
                self.buy(bar.symbol, bar.close, volume, order_type="market")
                self.position = volume
                self.logger.info(f"布林带下轨买入：{volume}股 @ {bar.close:.2f}")
        
        # 回归中轨卖出
        elif bar.close > middle and self.position > 0:
            self.sell(bar.symbol, bar.close, self.position, order_type="market")
            self.logger.info(f"布林带中轨卖出：{self.position}股 @ {bar.close:.2f}")
            self.position = 0


# ==================== 动量策略 ====================

class MomentumStrategy(Strategy):
    """
    动量策略（ROC 指标）
    
    逻辑：
    - ROC > 阈值：正动量，买入
    - ROC < -阈值：负动量，卖出
    
    参数：
    - period: ROC 周期（默认 12）
    - threshold: 动量阈值（默认 0.05）
    """
    
    def __init__(self, period: int = 12, threshold: float = 0.05):
        super().__init__()
        self.period = period
        self.threshold = threshold
        self.prices = []
        self.position = 0
    
    def on_init(self, engine):
        super().on_init(engine)
        self.logger = get_logger("QuantCore.Momentum")
    
    def on_bar(self, bar, engine):
        self.prices.append(bar.close)
        
        if len(self.prices) < self.period + 1:
            return
        
        # 计算 ROC
        roc_values = roc(self.prices, self.period)
        roc_value = roc_values[-1]
        
        # 正动量买入
        if roc_value > self.threshold and self.position == 0:
            portfolio = engine.get_portfolio()
            volume = int(portfolio.cash * 0.95 / bar.close / 100) * 100
            if volume >= 100:
                self.buy(bar.symbol, bar.close, volume, order_type="market")
                self.position = volume
                self.logger.info(f"正动量买入：{volume}股 @ {bar.close:.2f}, ROC={roc_value:.2f}")
        
        # 负动量卖出
        elif roc_value < -self.threshold and self.position > 0:
            self.sell(bar.symbol, bar.close, self.position, order_type="market")
            self.logger.info(f"负动量卖出：{self.position}股 @ {bar.close:.2f}, ROC={roc_value:.2f}")
            self.position = 0


# ==================== 突破策略 ====================

class DonchianBreakoutStrategy(Strategy):
    """
    唐奇安通道突破策略
    
    逻辑：
    - 突破上轨（N 日最高）：买入
    - 跌破下轨（N 日最低）：卖出
    
    参数：
    - period: 周期（默认 20）
    """
    
    def __init__(self, period: int = 20):
        super().__init__()
        self.period = period
        self.highs = []
        self.lows = []
        self.position = 0
    
    def on_init(self, engine):
        super().on_init(engine)
        self.logger = get_logger("QuantCore.Donchian")
    
    def on_bar(self, bar, engine):
        self.highs.append(bar.high)
        self.lows.append(bar.low)
        
        if len(self.highs) < self.period:
            return
        
        # 计算唐奇安通道
        upper = max(self.highs[-self.period:])
        lower = min(self.lows[-self.period:])
        
        # 突破上轨买入
        if bar.high > upper and self.position == 0:
            portfolio = engine.get_portfolio()
            volume = int(portfolio.cash * 0.95 / bar.close / 100) * 100
            if volume >= 100:
                self.buy(bar.symbol, bar.close, volume, order_type="market")
                self.position = volume
                self.logger.info(f"突破上轨买入：{volume}股 @ {bar.close:.2f}")
        
        # 跌破下轨卖出
        elif bar.low < lower and self.position > 0:
            self.sell(bar.symbol, bar.close, self.position, order_type="market")
            self.logger.info(f"跌破下轨卖出：{self.position}股 @ {bar.close:.2f}")
            self.position = 0


class SARBreakoutStrategy(Strategy):
    """
    SAR 抛物线转向突破策略
    
    逻辑：
    - 价格上穿 SAR：买入
    - 价格下穿 SAR：卖出
    
    参数：
    - af: 加速因子（默认 0.02）
    - max_af: 最大加速因子（默认 0.2）
    """
    
    def __init__(self, af: float = 0.02, max_af: float = 0.2):
        super().__init__()
        self.af = af
        self.max_af = max_af
        self.highs = []
        self.lows = []
        self.position = 0
    
    def on_init(self, engine):
        super().on_init(engine)
        self.logger = get_logger("QuantCore.SAR")
    
    def on_bar(self, bar, engine):
        self.highs.append(bar.high)
        self.lows.append(bar.low)
        
        if len(self.highs) < 10:
            return
        
        # 计算 SAR
        sar_values = sar(self.highs, self.lows, self.af, self.max_af)
        sar_value = sar_values[-1]
        
        # 价格上穿 SAR 买入
        if bar.low > sar_value and self.position == 0:
            portfolio = engine.get_portfolio()
            volume = int(portfolio.cash * 0.95 / bar.close / 100) * 100
            if volume >= 100:
                self.buy(bar.symbol, bar.close, volume, order_type="market")
                self.position = volume
                self.logger.info(f"SAR 转向买入：{volume}股 @ {bar.close:.2f}")
        
        # 价格下穿 SAR 卖出
        elif bar.high < sar_value and self.position > 0:
            self.sell(bar.symbol, bar.close, self.position, order_type="market")
            self.logger.info(f"SAR 转向卖出：{self.position}股 @ {bar.close:.2f}")
            self.position = 0


# ==================== 多因子策略 ====================

class MultiFactorStrategy(Strategy):
    """
    多因子策略（趋势 + 动量 + 成交量）
    
    逻辑：
    - 趋势因子：MACD > 0
    - 动量因子：ROC > 0
    - 成交量因子：MFI < 80（非极端超买）
    - 三个因子同时满足：买入
    
    参数：
    - macd_periods: MACD 参数（默认 (12, 26, 9)）
    - roc_period: ROC 周期（默认 12）
    - mfi_period: MFI 周期（默认 14）
    """
    
    def __init__(self, macd_periods: tuple = (12, 26, 9), roc_period: int = 12, 
                 mfi_period: int = 14):
        super().__init__()
        self.macd_periods = macd_periods
        self.roc_period = roc_period
        self.mfi_period = mfi_period
        self.prices = []
        self.highs = []
        self.lows = []
        self.volumes = []
        self.position = 0
    
    def on_init(self, engine):
        super().on_init(engine)
        self.logger = get_logger("QuantCore.MultiFactor")
    
    def on_bar(self, bar, engine):
        self.prices.append(bar.close)
        self.highs.append(bar.high)
        self.lows.append(bar.low)
        self.volumes.append(bar.volume)
        
        if len(self.prices) < max(self.roc_period, self.mfi_period) + 5:
            return
        
        # 因子 1：MACD 趋势
        macd_result = macd(self.prices, *self.macd_periods)
        trend_factor = macd_result['macd'][-1] > 0
        
        # 因子 2：ROC 动量
        roc_values = roc(self.prices, self.roc_period)
        momentum_factor = roc_values[-1] > 0
        
        # 因子 3：MFI 成交量（非极端超买）
        mfi_values = mfi(self.highs, self.lows, self.prices, self.volumes, self.mfi_period)
        volume_factor = mfi_values[-1] < 80
        
        # 三因子共振买入
        if trend_factor and momentum_factor and volume_factor and self.position == 0:
            portfolio = engine.get_portfolio()
            volume = int(portfolio.cash * 0.95 / bar.close / 100) * 100
            if volume >= 100:
                self.buy(bar.symbol, bar.close, volume, order_type="market")
                self.position = volume
                self.logger.info(f"多因子共振买入：{volume}股 @ {bar.close:.2f}")
        
        # 任一因子转弱卖出
        elif (not trend_factor or not momentum_factor) and self.position > 0:
            self.sell(bar.symbol, bar.close, self.position, order_type="market")
            self.logger.info(f"因子转弱卖出：{self.position}股 @ {bar.close:.2f}")
            self.position = 0


# ==================== 导出所有策略 ====================

__all__ = [
    # 趋势跟踪
    'DualMovingAverageStrategy',
    'MACDTrendStrategy',
    'ADXTrendStrategy',
    
    # 均值回归
    'RSIMeanReversionStrategy',
    'BollingerMeanReversionStrategy',
    
    # 动量策略
    'MomentumStrategy',
    
    # 突破策略
    'DonchianBreakoutStrategy',
    'SARBreakoutStrategy',
    
    # 多因子策略
    'MultiFactorStrategy',
]

# -*- coding: utf-8 -*-
"""
CTA 策略框架

CTA（Commodity Trading Advisor）策略框架，支持：
- 自动化的趋势跟踪
- 多品种交易
- 参数优化
- 实时信号生成
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, time
from abc import ABC, abstractmethod
from ..strategy.base import Strategy
from ..core import Bar
from ..indicators import ma, ema, macd, rsi, atr, bollinger_bands, adx
from ..logger import get_logger


class CTAParameter:
    """CTA 策略参数容器"""
    
    def __init__(self, **kwargs):
        """
        初始化参数
        
        Args:
            **kwargs: 参数字典
        """
        self.params = kwargs
    
    def get(self, name: str, default=None):
        """获取参数值"""
        return self.params.get(name, default)
    
    def set(self, name: str, value):
        """设置参数值"""
        self.params[name] = value
    
    def __repr__(self):
        return f"CTAParameter({self.params})"


class CTASignal:
    """CTA 交易信号"""
    
    def __init__(self, symbol: str, direction: str, action: str, 
                 price: float, volume: float, signal_type: str = "normal"):
        """
        初始化交易信号
        
        Args:
            symbol: 证券代码
            direction: 方向 ('long' 或 'short')
            action: 动作 ('open' 开仓 或 'close' 平仓)
            price: 价格
            volume: 数量
            signal_type: 信号类型 ('normal', 'stop_loss', 'stop_profit')
        """
        self.symbol = symbol
        self.direction = direction
        self.action = action
        self.price = price
        self.volume = volume
        self.signal_type = signal_type
        self.timestamp = datetime.now()
    
    def __repr__(self):
        return (f"CTASignal({self.symbol}, {self.direction}, {self.action}, "
                f"{self.price}, {self.volume}, {self.signal_type})")


class CTAPosition:
    """CTA 持仓信息"""
    
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.long_pos = 0  # 多头持仓
        self.long_price = 0.0  # 多头成本
        self.short_pos = 0  # 空头持仓
        self.short_price = 0.0  # 空头成本
    
    @property
    def net_pos(self) -> float:
        """净持仓"""
        return self.long_pos - self.short_pos
    
    @property
    def long_pnl(self) -> float:
        """多头浮盈"""
        return 0.0  # 需要当前价计算
    
    @property
    def short_pnl(self) -> float:
        """空头浮盈"""
        return 0.0
    
    def update_long(self, volume: float, price: float):
        """更新多头持仓"""
        if volume > 0:  # 开仓
            if self.long_pos == 0:
                self.long_price = price
            else:
                # 加权平均
                total_cost = self.long_pos * self.long_price + volume * price
                self.long_pos += volume
                self.long_price = total_cost / self.long_pos
        else:  # 平仓
            self.long_pos += volume  # volume 为负
    
    def update_short(self, volume: float, price: float):
        """更新空头持仓"""
        if volume > 0:  # 开空
            if self.short_pos == 0:
                self.short_price = price
            else:
                total_cost = self.short_pos * self.short_price + volume * price
                self.short_pos += volume
                self.short_price = total_cost / self.short_pos
        else:  # 平空
            self.short_pos += volume  # volume 为负


class CTAStrategy(Strategy, ABC):
    """
    CTA 策略基类
    
    提供 CTA 策略的通用功能：
    - 自动化的趋势跟踪
    - 多周期分析
    - 止损止盈
    - 仓位管理
    
    子类需要实现 on_bar 方法
    """
    
    # 默认参数
    default_params = {
        'fast_period': 10,
        'slow_period': 30,
        'atr_period': 14,
        'stop_loss_atr': 2.0,
        'stop_profit_atr': 4.0,
        'position_ratio': 0.3,
    }
    
    def __init__(self, params: Optional[CTAParameter] = None):
        """
        初始化 CTA 策略
        
        Args:
            params: 策略参数
        """
        super().__init__()
        self.params = CTAParameter(**self.default_params)
        if params:
            self.params = params
        
        # 数据容器
        self.bars: Dict[str, List[Bar]] = {}
        self.highs: Dict[str, List[float]] = {}
        self.lows: Dict[str, List[float]] = {}
        self.closes: Dict[str, List[float]] = {}
        self.volumes: Dict[str, List[float]] = {}
        
        # 持仓信息
        self.positions: Dict[str, CTAPosition] = {}
        
        # 信号队列
        self.signals: List[CTASignal] = []
        
        # 日志器
        self.logger = get_logger("QuantCore.CTA")
    
    def on_init(self, engine):
        """策略初始化"""
        super().on_init(engine)
        self.logger.info(f"CTA 策略初始化，参数：{self.params}")
    
    def on_bar(self, bar: Bar, engine):
        """
        K 线推送（抽象方法，子类实现）
        
        Args:
            bar: K 线对象
            engine: 回测引擎
        """
        # 更新数据
        self._update_data(bar)
        
        # 调用子类逻辑
        self.on_cta_bar(bar, engine)
    
    @abstractmethod
    def on_cta_bar(self, bar: Bar, engine):
        """
        CTA 策略逻辑（子类实现）
        
        Args:
            bar: K 线对象
            engine: 回测引擎
        """
        pass
    
    def _update_data(self, bar: Bar):
        """更新数据容器"""
        symbol = bar.symbol
        
        if symbol not in self.bars:
            self.bars[symbol] = []
            self.highs[symbol] = []
            self.lows[symbol] = []
            self.closes[symbol] = []
            self.volumes[symbol] = []
            self.positions[symbol] = CTAPosition(symbol)
        
        self.bars[symbol].append(bar)
        self.highs[symbol].append(bar.high)
        self.lows[symbol].append(bar.low)
        self.closes[symbol].append(bar.close)
        self.volumes[symbol].append(bar.volume)
    
    def get_position(self, symbol: str) -> CTAPosition:
        """获取持仓信息"""
        if symbol not in self.positions:
            self.positions[symbol] = CTAPosition(symbol)
        return self.positions[symbol]
    
    def send_signal(self, signal: CTASignal):
        """发送交易信号"""
        self.signals.append(signal)
        self.logger.info(f"发送信号：{signal}")
    
    def buy_open(self, symbol: str, price: float, volume: float):
        """买入开仓"""
        signal = CTASignal(symbol, 'long', 'open', price, volume)
        self.send_signal(signal)
    
    def sell_close(self, symbol: str, price: float, volume: float):
        """卖出平仓"""
        signal = CTASignal(symbol, 'long', 'close', price, volume)
        self.send_signal(signal)
    
    def sell_short(self, symbol: str, price: float, volume: float):
        """卖出开空"""
        signal = CTASignal(symbol, 'short', 'open', price, volume)
        self.send_signal(signal)
    
    def buy_cover(self, symbol: str, price: float, volume: float):
        """买入平空"""
        signal = CTASignal(symbol, 'short', 'close', price, volume)
        self.send_signal(signal)
    
    def check_stop_loss(self, symbol: str, current_price: float) -> Optional[CTASignal]:
        """
        检查止损
        
        Args:
            symbol: 证券代码
            current_price: 当前价格
            
        Returns:
            止损信号（如果有）
        """
        position = self.get_position(symbol)
        
        # 多头止损
        if position.long_pos > 0:
            stop_loss_price = position.long_price * (1 - self.params.get('stop_loss_ratio', 0.08))
            if current_price <= stop_loss_price:
                self.logger.warning(f"{symbol} 触发多头止损：{current_price:.2f} <= {stop_loss_price:.2f}")
                return CTASignal(symbol, 'long', 'close', current_price, position.long_pos, 'stop_loss')
        
        # 空头止损
        if position.short_pos > 0:
            stop_loss_price = position.short_price * (1 + self.params.get('stop_loss_ratio', 0.08))
            if current_price >= stop_loss_price:
                self.logger.warning(f"{symbol} 触发空头止损：{current_price:.2f} >= {stop_loss_price:.2f}")
                return CTASignal(symbol, 'short', 'close', current_price, position.short_pos, 'stop_loss')
        
        return None
    
    def check_stop_profit(self, symbol: str, current_price: float) -> Optional[CTASignal]:
        """
        检查止盈
        
        Args:
            symbol: 证券代码
            current_price: 当前价格
            
        Returns:
            止盈信号（如果有）
        """
        position = self.get_position(symbol)
        
        # 多头止盈
        if position.long_pos > 0:
            stop_profit_price = position.long_price * (1 + self.params.get('stop_profit_ratio', 0.20))
            if current_price >= stop_profit_price:
                self.logger.info(f"{symbol} 触发多头止盈：{current_price:.2f} >= {stop_profit_price:.2f}")
                return CTASignal(symbol, 'long', 'close', current_price, position.long_pos, 'stop_profit')
        
        # 空头止盈
        if position.short_pos > 0:
            stop_profit_price = position.short_price * (1 - self.params.get('stop_profit_ratio', 0.20))
            if current_price <= stop_profit_price:
                self.logger.info(f"{symbol} 触发空头止盈：{current_price:.2f} <= {stop_profit_price:.2f}")
                return CTASignal(symbol, 'short', 'close', current_price, position.short_pos, 'stop_profit')
        
        return None
    
    def get_signals(self) -> List[CTASignal]:
        """获取所有信号"""
        return self.signals.copy()
    
    def clear_signals(self):
        """清空信号"""
        self.signals = []


# ==================== 经典 CTA 策略实现 ====================

class DualMaCTAStrategy(CTAStrategy):
    """
    双均线 CTA 策略
    
    逻辑：
    - 快线上穿慢线：做多
    - 快线下穿慢线：做空
    """
    
    default_params = {
        'fast_period': 10,
        'slow_period': 30,
        'position_ratio': 0.3,
    }
    
    def on_cta_bar(self, bar: Bar, engine):
        symbol = bar.symbol
        closes = self.closes[symbol]
        
        if len(closes) < self.params.get('slow_period'):
            return
        
        # 计算均线
        fast_ma = ma(closes, self.params.get('fast_period'))[-1]
        slow_ma = ma(closes, self.params.get('slow_period'))[-1]
        prev_fast_ma = ma(closes[:-1], self.params.get('fast_period'))[-1] if len(closes) > 1 else fast_ma
        prev_slow_ma = ma(closes[:-1], self.params.get('slow_period'))[-1] if len(closes) > 1 else slow_ma
        
        position = self.get_position(symbol)
        
        # 金叉做多
        if prev_fast_ma <= prev_slow_ma and fast_ma > slow_ma:
            if position.long_pos == 0:
                portfolio = engine.get_portfolio()
                volume = int(portfolio.cash * self.params.get('position_ratio', 0.3) / bar.close / 100) * 100
                if volume >= 100:
                    self.buy_open(symbol, bar.close, volume)
        
        # 死叉平仓
        elif prev_fast_ma >= prev_slow_ma and fast_ma < slow_ma:
            if position.long_pos > 0:
                self.sell_close(symbol, bar.close, position.long_pos)


class ATRTrailingCTAStrategy(CTAStrategy):
    default_params = {
        'breakout_period': 20,
        'atr_period': 14,
        'atr_multiplier': 2.0,
        'position_ratio': 0.3,
    }
    
    def __init__(self, strategy_id: str = "", params: dict = None):
        super().__init__(strategy_id, params)
        self.stop_loss_price = 0.0
    
    def on_cta_bar(self, bar: Bar, engine):
        symbol = bar.symbol
        highs = self.highs[symbol]
        lows = self.lows[symbol]
        closes = self.closes[symbol]
        
        period = self.params.get('breakout_period')
        if len(highs) < period:
            return
        
        position = self.get_position(symbol)
        
        # 计算 ATR
        atr_values = atr(highs, lows, closes, self.params.get('atr_period'))
        current_atr = atr_values[-1] if atr_values else 0
        
        # 突破开仓
        highest_high = max(highs[-period:])
        if bar.high > highest_high and position.long_pos == 0:
            portfolio = engine.get_portfolio()
            volume = int(portfolio.cash * self.params.get('position_ratio') / bar.close / 100) * 100
            if volume >= 100:
                self.buy_open(symbol, bar.close, volume)
                # 设置初始止损
                self.stop_loss_price = bar.close - current_atr * self.params.get('atr_multiplier')
        
        # 移动止损
        elif position.long_pos > 0:
            # 更新止损价（只上移不下移）
            new_stop_loss = bar.close - current_atr * self.params.get('atr_multiplier')
            if new_stop_loss > self.stop_loss_price:
                self.stop_loss_price = new_stop_loss
            
            # 触发止损
            if bar.low < self.stop_loss_price:
                self.sell_close(symbol, bar.close, position.long_pos)


class BollingerCTAStrategy(CTAStrategy):
    """
    布林带 CTA 策略
    
    逻辑：
    - 触及下轨：做多
    - 触及上轨：平仓
    """
    
    default_params = {
        'period': 20,
        'std_dev': 2.0,
        'position_ratio': 0.3,
    }
    
    def on_cta_bar(self, bar: Bar, engine):
        symbol = bar.symbol
        closes = self.closes[symbol]
        
        period = self.params.get('period')
        if len(closes) < period:
            return
        
        position = self.get_position(symbol)
        
        # 计算布林带
        boll = bollinger_bands(closes, period, self.params.get('std_dev'))
        upper = boll['upper'][-1]
        lower = boll['lower'][-1]
        middle = boll['middle'][-1]
        
        # 触及下轨做多
        if bar.low <= lower and position.long_pos == 0:
            portfolio = engine.get_portfolio()
            volume = int(portfolio.cash * self.params.get('position_ratio') / bar.close / 100) * 100
            if volume >= 100:
                self.buy_open(symbol, bar.close, volume)
        
        # 触及上轨或回归中轨平仓
        elif position.long_pos > 0:
            if bar.high >= upper or bar.close >= middle:
                self.sell_close(symbol, bar.close, position.long_pos)


# 导出
__all__ = [
    'CTAParameter',
    'CTASignal',
    'CTAPosition',
    'CTAStrategy',
    'DualMaCTAStrategy',
    'ATRTrailingCTAStrategy',
    'BollingerCTAStrategy',
]

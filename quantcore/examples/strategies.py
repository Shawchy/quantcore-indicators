# -*- coding: utf-8 -*-
"""
示例策略：双均线策略

策略逻辑：
- 当快线上穿慢线（金叉）时买入
- 当快线下穿慢线（死叉）时卖出
"""

from quantcore.strategy import Strategy
from typing import List


class DualMAStrategy(Strategy):
    """双均线策略"""
    
    # 策略参数
    parameters = {
        'fast_period': 5,    # 快线周期
        'slow_period': 20,   # 慢线周期
    }
    
    def __init__(self, fast_period: int = 5, slow_period: int = 20):
        """
        初始化策略
        
        Args:
            fast_period: 快线周期
            slow_period: 慢线周期
        """
        super().__init__()
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.prices: List[float] = []
        self.position = 0  # 当前持仓
    
    def on_init(self, engine):
        """策略初始化"""
        super().on_init(engine)
        self.prices = []
        self.position = 0
        print(f"策略初始化：快线={self.fast_period}, 慢线={self.slow_period}")
    
    def on_bar(self, bar, engine):
        """
        K 线事件
        
        Args:
            bar: K 线数据
            engine: 回测引擎
        """
        # 记录收盘价
        self.prices.append(bar.close)
        
        # 等待足够的数据
        if len(self.prices) < self.slow_period:
            return
        
        # 计算均线
        fast_ma = sum(self.prices[-self.fast_period:]) / self.fast_period
        slow_ma = sum(self.prices[-self.slow_period:]) / self.slow_period
        
        # 前一周期的均线
        if len(self.prices) > self.slow_period:
            prev_fast_ma = sum(self.prices[-self.slow_period:-self.slow_period+self.fast_period]) / self.fast_period
            prev_slow_ma = sum(self.prices[-self.slow_period-1:-1]) / self.slow_period
        else:
            prev_fast_ma = fast_ma
            prev_slow_ma = slow_ma
        
        # 金叉：快线上穿慢线
        if prev_fast_ma <= prev_slow_ma and fast_ma > slow_ma:
            if self.position == 0:
                # 买入
                order = self.buy(bar.symbol, bar.close, 1000)
                self.position = 1
                print(f"{bar.timestamp} 金叉买入 {bar.symbol} @ {bar.close:.2f}")
        
        # 死叉：快线下穿慢线
        elif prev_fast_ma >= prev_slow_ma and fast_ma < slow_ma:
            if self.position == 1:
                # 卖出
                order = self.sell(bar.symbol, bar.close, 1000)
                self.position = 0
                print(f"{bar.timestamp} 死叉卖出 {bar.symbol} @ {bar.close:.2f}")
    
    def on_finish(self, engine):
        """回测结束"""
        print(f"策略结束，最终持仓：{self.position}")


# 简单示例：买入持有策略
class BuyAndHoldStrategy(Strategy):
    """买入持有策略"""
    
    def __init__(self, symbol: str = "SH.600000", volume: int = 1000):
        """
        初始化策略
        
        Args:
            symbol: 证券代码
            volume: 买入数量
        """
        super().__init__()
        self.symbol = symbol
        self.volume = volume
        self.bought = False
    
    def on_bar(self, bar, engine):
        """
        K 线事件
        
        Args:
            bar: K 线数据
            engine: 回测引擎
        """
        # 第一天买入并持有
        if not self.bought and bar.symbol == self.symbol:
            order = self.buy(self.symbol, bar.close, self.volume)
            self.bought = True
            print(f"{bar.timestamp} 买入 {self.symbol} {self.volume}股 @ {bar.close:.2f}")

# -*- coding: utf-8 -*-
"""
策略框架模块

提供策略开发接口：
- Strategy: 策略基类
- StrategyRunner: 策略运行器
"""

from typing import TYPE_CHECKING, List, Dict, Any
from datetime import datetime

if TYPE_CHECKING:
    from ..engine import BacktestEngine
    from ..core import Bar


class Strategy:
    """策略基类"""
    
    # 策略参数（子类可覆盖）
    parameters = {}
    
    def __init__(self):
        """初始化策略"""
        self.engine = None
        self.context = {}
    
    def on_init(self, engine: 'BacktestEngine'):
        """
        策略初始化
        
        Args:
            engine: 回测引擎
        """
        self.engine = engine
    
    def on_bar(self, bar: 'Bar', engine: 'BacktestEngine'):
        """
        K 线事件
        
        Args:
            bar: K 线数据
            engine: 回测引擎
        """
        raise NotImplementedError("子类必须实现 on_bar 方法")
    
    def on_order(self, order):
        """
        订单事件
        
        Args:
            order: 订单对象
        """
        pass
    
    def on_trade(self, trade):
        """
        成交事件
        
        Args:
            trade: 成交对象
        """
        pass
    
    def on_finish(self, engine: 'BacktestEngine'):
        """
        回测结束
        
        Args:
            engine: 回测引擎
        """
        pass
    
    def buy(self, symbol: str, price: float, volume: int, order_type: str = "market"):
        """
        买入
        
        Args:
            symbol: 证券代码
            price: 价格
            volume: 数量
            order_type: 订单类型 ("market" 或 "limit")
        """
        return self.engine.buy(symbol, price, volume, order_type)
    
    def sell(self, symbol: str, price: float, volume: int, order_type: str = "market"):
        """
        卖出
        
        Args:
            symbol: 证券代码
            price: 价格
            volume: 数量
            order_type: 订单类型 ("market" 或 "limit")
        """
        return self.engine.sell(symbol, price, volume, order_type)
    
    def get_position(self, symbol: str):
        """获取持仓"""
        return self.engine.get_portfolio().get_position(symbol)
    
    def has_position(self, symbol: str) -> bool:
        """是否有持仓"""
        return self.engine.get_portfolio().has_position(symbol)
    
    def get_cash(self) -> float:
        """获取可用资金"""
        return self.engine.get_portfolio().cash


class StrategyRunner:
    """策略运行器"""
    
    def __init__(self, strategy: Strategy):
        """
        初始化策略运行器
        
        Args:
            strategy: 策略对象
        """
        self.strategy = strategy
    
    def run(self, engine: 'BacktestEngine', bars: List['Bar']) -> Any:
        """
        运行策略回测
        
        Args:
            engine: 回测引擎
            bars: K 线数据列表
            
        Returns:
            回测结果
        """
        # 初始化策略
        self.strategy.on_init(engine)
        
        # 处理每个 K 线
        for bar in bars:
            # 触发策略
            self.strategy.on_bar(bar, engine)
        
        # 回测结束
        self.strategy.on_finish(engine)
        
        # 运行回测并返回结果
        return engine.run(self.strategy, bars)

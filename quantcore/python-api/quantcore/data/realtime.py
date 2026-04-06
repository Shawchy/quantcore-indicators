# -*- coding: utf-8 -*-
"""
实时数据接入模块

支持多种实时数据源：
- WebSocket 实时行情
- 轮询 API 数据
- 数据推送回调
"""

from typing import Dict, List, Any, Optional, Callable, AsyncGenerator
from datetime import datetime
from abc import ABC, abstractmethod
import asyncio
import time
from ..core import Bar
from ..logger import get_logger


class TickData:
    """Tick 数据"""
    
    def __init__(self, symbol: str, price: float, volume: float, 
                 open_interest: float = 0, **kwargs):
        self.symbol = symbol
        self.price = price
        self.volume = volume
        self.open_interest = open_interest
        self.timestamp = datetime.now()
        
        # 买卖盘口
        self.bid_price_1 = kwargs.get('bid_price_1', 0)
        self.bid_volume_1 = kwargs.get('bid_volume_1', 0)
        self.ask_price_1 = kwargs.get('ask_price_1', 0)
        self.ask_volume_1 = kwargs.get('ask_volume_1', 0)
        
        # 其他字段
        self.open = kwargs.get('open', 0)
        self.high = kwargs.get('high', 0)
        self.low = kwargs.get('low', 0)
        self.prev_close = kwargs.get('prev_close', 0)
    
    def to_bar(self) -> Bar:
        """转换为 Bar 对象"""
        return Bar(
            timestamp=self.timestamp,
            symbol=self.symbol,
            open=self.open or self.price,
            high=self.high or self.price,
            low=self.low or self.price,
            close=self.price,
            volume=self.volume,
            turnover=self.price * self.volume
        )
    
    def __repr__(self):
        return f"TickData({self.symbol}, {self.price}, {self.volume})"


class DataSubscriber(ABC):
    """数据订阅器基类"""
    
    def __init__(self):
        self.logger = get_logger("QuantCore.DataSubscriber")
        self.callbacks: Dict[str, List[Callable]] = {}
        self.running = False
    
    def subscribe(self, symbol: str, callback: Callable[[TickData], None]):
        """
        订阅数据
        
        Args:
            symbol: 证券代码
            callback: 回调函数
        """
        if symbol not in self.callbacks:
            self.callbacks[symbol] = []
        self.callbacks[symbol].append(callback)
        self.logger.info(f"订阅：{symbol}")
    
    def unsubscribe(self, symbol: str):
        """取消订阅"""
        if symbol in self.callbacks:
            del self.callbacks[symbol]
            self.logger.info(f"取消订阅：{symbol}")
    
    def _notify(self, tick: TickData):
        """通知所有回调"""
        symbol = tick.symbol
        if symbol in self.callbacks:
            for callback in self.callbacks[symbol]:
                try:
                    callback(tick)
                except Exception as e:
                    self.logger.error(f"回调错误：{e}")
    
    @abstractmethod
    async def connect(self):
        """连接数据源"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """断开连接"""
        pass
    
    @abstractmethod
    async def start(self):
        """开始接收数据"""
        pass
    
    @abstractmethod
    async def stop(self):
        """停止接收数据"""
        pass


class MockDataSubscriber(DataSubscriber):
    """
    模拟数据订阅器（用于测试）
    
    生成模拟的实时行情数据
    """
    
    def __init__(self, symbols: List[str], base_prices: Dict[str, float],
                 volatility: float = 0.02):
        """
        初始化
        
        Args:
            symbols: 证券代码列表
            base_prices: 基准价格字典
            volatility: 波动率
        """
        super().__init__()
        self.symbols = symbols
        self.base_prices = base_prices
        self.volatility = volatility
        self.current_prices = {s: base_prices.get(s, 10.0) for s in symbols}
    
    async def connect(self):
        """连接"""
        self.running = True
        self.logger.info("模拟数据源已连接")
    
    async def disconnect(self):
        """断开"""
        self.running = False
        self.logger.info("模拟数据源已断开")
    
    async def start(self):
        """开始发送数据"""
        self.running = True
        self.logger.info(f"开始发送模拟数据：{self.symbols}")
        
        while self.running:
            for symbol in self.symbols:
                # 生成随机价格
                import random
                change = random.gauss(0, self.volatility)
                self.current_prices[symbol] *= (1 + change)
                
                # 生成 Tick
                tick = TickData(
                    symbol=symbol,
                    price=self.current_prices[symbol],
                    volume=random.randint(100, 1000),
                    bid_price_1=self.current_prices[symbol] * 0.999,
                    bid_volume_1=random.randint(100, 500),
                    ask_price_1=self.current_prices[symbol] * 1.001,
                    ask_volume_1=random.randint(100, 500),
                )
                
                self._notify(tick)
            
            # 每秒发送一次
            await asyncio.sleep(1)
    
    async def stop(self):
        """停止"""
        self.running = False
        self.logger.info("停止发送模拟数据")


class BaostockRealtimeSubscriber(DataSubscriber):
    """
    Baostock 实时数据订阅器（轮询模式）
    
    通过轮询 Baostock API 获取实时行情
    """
    
    def __init__(self, symbols: List[str], interval: float = 3.0):
        """
        初始化
        
        Args:
            symbols: 证券代码列表
            interval: 轮询间隔（秒）
        """
        super().__init__()
        self.symbols = symbols
        self.interval = interval
        self.last_ticks: Dict[str, TickData] = {}
    
    async def connect(self):
        """连接"""
        import baostock as bs
        bs.login()
        self.running = True
        self.logger.info("Baostock 已连接")
    
    async def disconnect(self):
        """断开"""
        import baostock as bs
        bs.logout()
        self.running = False
        self.logger.info("Baostock 已断开")
    
    async def start(self):
        """开始接收数据"""
        self.running = True
        self.logger.info(f"开始轮询 Baostock：{self.symbols}")
        
        while self.running:
            for symbol in self.symbols:
                try:
                    tick = await self._fetch_tick(symbol)
                    if tick:
                        self.last_ticks[symbol] = tick
                        self._notify(tick)
                except Exception as e:
                    self.logger.error(f"获取 {symbol} 数据失败：{e}")
            
            await asyncio.sleep(self.interval)
    
    async def _fetch_tick(self, symbol: str) -> Optional[TickData]:
        """获取单个证券的 Tick 数据"""
        try:
            import baostock as bs
            
            # 查询实时行情
            rs = bs.query_realtime_price(symbol)
            if rs.error_code != '0':
                return None
            
            data = rs.get_row_data()
            if not data:
                return None
            
            # 解析数据
            fields = rs.fields
            data_dict = dict(zip(fields, data))
            
            price = float(data_dict.get('lastPrice', 0))
            volume = float(data_dict.get('volume', 0))
            
            tick = TickData(
                symbol=symbol,
                price=price,
                volume=volume,
                open=float(data_dict.get('open', 0)),
                high=float(data_dict.get('high', 0)),
                low=float(data_dict.get('low', 0)),
                prev_close=float(data_dict.get('preClose', 0)),
            )
            
            return tick
        
        except Exception as e:
            self.logger.error(f"解析数据失败：{e}")
            return None
    
    async def stop(self):
        """停止"""
        self.running = False
        self.logger.info("停止轮询 Baostock")


class RealtimeDataManager:
    """
    实时数据管理器
    
    统一管理多个数据订阅器
    """
    
    def __init__(self):
        self.subscribers: Dict[str, DataSubscriber] = {}
        self.logger = get_logger("QuantCore.RealtimeDataManager")
    
    def add_subscriber(self, name: str, subscriber: DataSubscriber):
        """添加数据订阅器"""
        self.subscribers[name] = subscriber
        self.logger.info(f"添加数据订阅器：{name}")
    
    def remove_subscriber(self, name: str):
        """移除数据订阅器"""
        if name in self.subscribers:
            del self.subscribers[name]
            self.logger.info(f"移除数据订阅器：{name}")
    
    async def start_all(self):
        """启动所有订阅器"""
        self.logger.info("启动所有数据订阅器")
        
        # 连接所有订阅器
        for name, subscriber in self.subscribers.items():
            await subscriber.connect()
        
        # 启动所有订阅器
        tasks = [sub.start() for sub in self.subscribers.values()]
        await asyncio.gather(*tasks)
    
    async def stop_all(self):
        """停止所有订阅器"""
        self.logger.info("停止所有数据订阅器")
        
        for name, subscriber in self.subscribers.items():
            await subscriber.stop()
            await subscriber.disconnect()
    
    def subscribe(self, symbol: str, callback: Callable[[TickData], None], 
                  subscriber_name: str = 'default'):
        """订阅数据"""
        if subscriber_name in self.subscribers:
            self.subscribers[subscriber_name].subscribe(symbol, callback)
    
    def unsubscribe(self, symbol: str, subscriber_name: str = 'default'):
        """取消订阅"""
        if subscriber_name in self.subscribers:
            self.subscribers[subscriber_name].unsubscribe(symbol)


# 便捷函数
def create_mock_subscriber(symbols: List[str], base_prices: Dict[str, float],
                           volatility: float = 0.02) -> MockDataSubscriber:
    """创建模拟数据订阅器"""
    return MockDataSubscriber(symbols, base_prices, volatility)


def create_baostock_subscriber(symbols: List[str], 
                               interval: float = 3.0) -> BaostockRealtimeSubscriber:
    """创建 Baostock 实时订阅器"""
    return BaostockRealtimeSubscriber(symbols, interval)


# 导出
__all__ = [
    'TickData',
    'DataSubscriber',
    'MockDataSubscriber',
    'BaostockRealtimeSubscriber',
    'RealtimeDataManager',
    'create_mock_subscriber',
    'create_baostock_subscriber',
]

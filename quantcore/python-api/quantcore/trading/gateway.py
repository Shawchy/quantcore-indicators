# -*- coding: utf-8 -*-
"""
实盘交易接口原型

提供实盘交易的基础框架：
- 订单管理
- 持仓管理
- 账户查询
- 交易接口抽象

注意：这是原型实现，实际使用需要对接真实的交易 API
"""

from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import uuid
from ..logger import get_logger


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "pending"  # 待提交
    SUBMITTED = "submitted"  # 已提交
    FILLED = "filled"  # 已成交
    PARTIALLY_FILLED = "partially_filled"  # 部分成交
    CANCELLED = "cancelled"  # 已取消
    REJECTED = "rejected"  # 已拒绝


class OrderSide(Enum):
    """订单方向"""
    BUY = "buy"  # 买入
    SELL = "sell"  # 卖出


class OrderType(Enum):
    """订单类型"""
    MARKET = "market"  # 市价单
    LIMIT = "limit"  # 限价单
    STOP = "stop"  # 止损单


@dataclass
class Order:
    """订单对象"""
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    price: float
    quantity: float
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    filled_price: float = 0.0
    commission: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def unfilled_quantity(self) -> float:
        """未成交数量"""
        return self.quantity - self.filled_quantity
    
    @property
    def is_active(self) -> bool:
        """是否活跃订单"""
        return self.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED, 
                               OrderStatus.PARTIALLY_FILLED]


@dataclass
class Trade:
    """成交对象"""
    trade_id: str
    order_id: str
    symbol: str
    side: OrderSide
    price: float
    quantity: float
    commission: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Position:
    """持仓对象"""
    symbol: str
    quantity: float
    available_quantity: float
    cost_price: float
    current_price: float
    market_value: float = 0.0
    unrealized_pnl: float = 0.0
    
    def update_price(self, price: float):
        """更新当前价"""
        self.current_price = price
        self.market_value = self.quantity * price
        self.unrealized_pnl = (price - self.cost_price) * self.quantity


@dataclass
class Account:
    """账户对象"""
    account_id: str
    total_asset: float
    available_cash: float
    frozen_cash: float
    market_value: float
    total_pnl: float
    today_pnl: float


class TradingGateway(ABC):
    """交易接口抽象基类"""
    
    def __init__(self):
        self.logger = get_logger("QuantCore.TradingGateway")
        self.connected = False
        
        # 本地缓存
        self.orders: Dict[str, Order] = {}
        self.trades: Dict[str, Trade] = {}
        self.positions: Dict[str, Position] = {}
        
        # 回调函数
        self.on_order_callback: Optional[Callable[[Order], None]] = None
        self.on_trade_callback: Optional[Callable[[Trade], None]] = None
        self.on_position_callback: Optional[Callable[[Position], None]] = None
    
    @abstractmethod
    async def connect(self, **kwargs) -> bool:
        """连接交易接口"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """断开连接"""
        pass
    
    @abstractmethod
    async def send_order(self, order: Order) -> bool:
        """发送订单"""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """撤销订单"""
        pass
    
    @abstractmethod
    async def query_orders(self) -> List[Order]:
        """查询订单"""
        pass
    
    @abstractmethod
    async def query_positions(self) -> Dict[str, Position]:
        """查询持仓"""
        pass
    
    @abstractmethod
    async def query_account(self) -> Account:
        """查询账户"""
        pass
    
    def set_order_callback(self, callback: Callable[[Order], None]):
        """设置订单回调"""
        self.on_order_callback = callback
    
    def set_trade_callback(self, callback: Callable[[Trade], None]):
        """设置成交回调"""
        self.on_trade_callback = callback
    
    def set_position_callback(self, callback: Callable[[Position], None]):
        """设置持仓回调"""
        self.on_position_callback = callback
    
    def _notify_order(self, order: Order):
        """通知订单更新"""
        if self.on_order_callback:
            self.on_order_callback(order)
    
    def _notify_trade(self, trade: Trade):
        """通知成交"""
        if self.on_trade_callback:
            self.on_trade_callback(trade)
    
    def _notify_position(self, position: Position):
        """通知持仓更新"""
        if self.on_position_callback:
            self.on_position_callback(position)


class MockTradingGateway(TradingGateway):
    """
    模拟交易接口（用于测试）
    
    模拟订单提交、成交等流程
    """
    
    def __init__(self, initial_cash: float = 1000000.0):
        super().__init__()
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.account_id = "MOCK_ACCOUNT"
    
    async def connect(self, **kwargs) -> bool:
        """连接"""
        self.connected = True
        self.logger.info(f"模拟交易接口已连接，初始资金：{self.initial_cash:,.2f}")
        return True
    
    async def disconnect(self):
        """断开"""
        self.connected = False
        self.logger.info("模拟交易接口已断开")
    
    async def send_order(self, order: Order) -> bool:
        """发送订单（模拟成交）"""
        if not self.connected:
            self.logger.error("未连接")
            return False
        
        # 保存订单
        self.orders[order.order_id] = order
        
        # 模拟订单状态变化
        order.status = OrderStatus.SUBMITTED
        self._notify_order(order)
        
        # 模拟立即成交（简化）
        if order.side == OrderSide.BUY:
            cost = order.price * order.quantity
            if cost > self.cash:
                order.status = OrderStatus.REJECTED
                self.logger.warning(f"资金不足，订单拒绝")
                self._notify_order(order)
                return False
            
            self.cash -= cost
            order.filled_quantity = order.quantity
            order.filled_price = order.price
        
        elif order.side == OrderSide.SELL:
            # 检查持仓
            if order.symbol not in self.positions:
                order.status = OrderStatus.REJECTED
                self.logger.warning(f"无持仓，订单拒绝")
                self._notify_order(order)
                return False
            
            pos = self.positions[order.symbol]
            if order.quantity > pos.available_quantity:
                order.status = OrderStatus.REJECTED
                self.logger.warning(f"持仓不足，订单拒绝")
                self._notify_order(order)
                return False
            
            self.cash += order.price * order.quantity
            order.filled_quantity = order.quantity
            order.filled_price = order.price
        
        # 更新订单状态
        order.status = OrderStatus.FILLED
        order.commission = order.price * order.quantity * 0.0003  # 模拟佣金
        self._notify_order(order)
        
        # 生成成交
        trade = Trade(
            trade_id=str(uuid.uuid4()),
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side,
            price=order.filled_price,
            quantity=order.filled_quantity,
            commission=order.commission
        )
        self.trades[trade.trade_id] = trade
        self._notify_trade(trade)
        
        # 更新持仓
        self._update_position(order.symbol, order.side, order.filled_quantity, 
                             order.filled_price)
        
        self.logger.info(f"订单成交：{order}")
        return True
    
    async def cancel_order(self, order_id: str) -> bool:
        """撤销订单"""
        if order_id not in self.orders:
            return False
        
        order = self.orders[order_id]
        if not order.is_active:
            return False
        
        order.status = OrderStatus.CANCELLED
        self._notify_order(order)
        self.logger.info(f"订单已撤销：{order_id}")
        return True
    
    async def query_orders(self) -> List[Order]:
        """查询订单"""
        return list(self.orders.values())
    
    async def query_positions(self) -> Dict[str, Position]:
        """查询持仓"""
        return self.positions.copy()
    
    async def query_account(self) -> Account:
        """查询账户"""
        market_value = sum(pos.market_value for pos in self.positions.values())
        total_asset = self.cash + market_value
        
        return Account(
            account_id=self.account_id,
            total_asset=total_asset,
            available_cash=self.cash,
            frozen_cash=0.0,
            market_value=market_value,
            total_pnl=total_asset - self.initial_cash,
            today_pnl=0.0
        )
    
    def _update_position(self, symbol: str, side: OrderSide, 
                        quantity: float, price: float):
        """更新持仓"""
        if symbol not in self.positions:
            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=0,
                available_quantity=0,
                cost_price=0,
                current_price=price
            )
        
        pos = self.positions[symbol]
        
        if side == OrderSide.BUY:
            # 买入开仓
            total_cost = pos.quantity * pos.cost_price + quantity * price
            pos.quantity += quantity
            pos.available_quantity += quantity
            pos.cost_price = total_cost / pos.quantity if pos.quantity > 0 else 0
        
        elif side == OrderSide.SELL:
            # 卖出平仓
            pos.quantity -= quantity
            pos.available_quantity -= quantity
        
        pos.current_price = price
        pos.market_value = pos.quantity * pos.current_price
        
        self._notify_position(pos)


class LiveTradingEngine:
    """
    实盘交易引擎
    
    整合交易接口、风控、策略
    """
    
    def __init__(self, gateway: TradingGateway):
        """
        初始化
        
        Args:
            gateway: 交易接口
        """
        self.gateway = gateway
        self.logger = get_logger("QuantCore.LiveTradingEngine")
        
        # 策略实例
        self.strategies = {}
        
        # 运行状态
        self.running = False
    
    def add_strategy(self, name: str, strategy):
        """添加策略"""
        self.strategies[name] = strategy
        self.logger.info(f"添加策略：{name}")
    
    async def start(self):
        """启动引擎"""
        self.logger.info("启动实盘交易引擎")
        
        # 连接交易接口
        connected = await self.gateway.connect()
        if not connected:
            self.logger.error("连接交易接口失败")
            return
        
        self.running = True
        
        # 启动策略
        for name, strategy in self.strategies.items():
            self.logger.info(f"启动策略：{name}")
            strategy.on_init(self)
        
        self.logger.info("实盘交易引擎已启动")
    
    async def stop(self):
        """停止引擎"""
        self.logger.info("停止实盘交易引擎")
        self.running = False
        
        # 停止策略
        for name, strategy in self.strategies.items():
            self.logger.info(f"停止策略：{name}")
        
        # 断开连接
        await self.gateway.disconnect()
        
        self.logger.info("实盘交易引擎已停止")
    
    def buy(self, symbol: str, price: float, quantity: float, 
            order_type: str = "market") -> Optional[str]:
        """
        买入
        
        Args:
            symbol: 证券代码
            price: 价格
            quantity: 数量
            order_type: 订单类型
            
        Returns:
            订单 ID（如果成功）
        """
        if not self.running:
            self.logger.error("引擎未运行")
            return None
        
        order = Order(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET if order_type == "market" else OrderType.LIMIT,
            price=price,
            quantity=quantity
        )
        
        # 异步发送订单（简化为同步）
        import asyncio
        success = asyncio.get_event_loop().run_until_complete(
            self.gateway.send_order(order)
        )
        
        return order.order_id if success else None
    
    def sell(self, symbol: str, price: float, quantity: float,
             order_type: str = "market") -> Optional[str]:
        """
        卖出
        
        Args:
            symbol: 证券代码
            price: 价格
            quantity: 数量
            order_type: 订单类型
            
        Returns:
            订单 ID（如果成功）
        """
        if not self.running:
            self.logger.error("引擎未运行")
            return None
        
        order = Order(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side=OrderSide.SELL,
            order_type=OrderType.MARKET if order_type == "market" else OrderType.LIMIT,
            price=price,
            quantity=quantity
        )
        
        import asyncio
        success = asyncio.get_event_loop().run_until_complete(
            self.gateway.send_order(order)
        )
        
        return order.order_id if success else None
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """获取持仓"""
        import asyncio
        positions = asyncio.get_event_loop().run_until_complete(
            self.gateway.query_positions()
        )
        return positions.get(symbol)
    
    def get_account(self) -> Optional[Account]:
        """获取账户信息"""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(
            self.gateway.query_account()
        )


# 便捷函数
def create_mock_gateway(initial_cash: float = 1000000.0) -> MockTradingGateway:
    """创建模拟交易接口"""
    return MockTradingGateway(initial_cash)


# 导出
__all__ = [
    'OrderStatus',
    'OrderSide',
    'OrderType',
    'Order',
    'Trade',
    'Position',
    'Account',
    'TradingGateway',
    'MockTradingGateway',
    'LiveTradingEngine',
    'create_mock_gateway',
]

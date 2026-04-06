"""
核心数据模块

提供量化交易的基础数据类型：
- Bar: K 线数据
- Order: 订单
- Trade: 成交
- Position: 持仓
- Portfolio: 投资组合
"""

from typing import Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class OrderSide(Enum):
    """订单方向"""
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """订单类型"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class Bar:
    """K 线数据"""
    timestamp: datetime
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    turnover: Optional[float] = None
    open_interest: Optional[int] = None
    
    def __post_init__(self):
        """验证数据"""
        assert self.high >= self.low, "最高价不能低于最低价"
        assert self.high >= self.open and self.high >= self.close, "最高价必须大于等于开盘价和收盘价"
        assert self.low <= self.open and self.low <= self.close, "最低价必须小于等于开盘价和收盘价"
    
    @property
    def average_price(self) -> float:
        """平均价格"""
        return (self.high + self.low + self.close) / 3
    
    @property
    def price_range(self) -> float:
        """价格范围"""
        return self.high - self.low
    
    @property
    def price_change_percent(self) -> float:
        """涨跌幅"""
        if self.open == 0:
            return 0.0
        return (self.close - self.open) / self.open


@dataclass
class Order:
    """订单"""
    order_id: str
    strategy_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    price: float
    quantity: int
    filled_quantity: int = 0
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    @property
    def remaining_quantity(self) -> int:
        """未成交数量"""
        return self.quantity - self.filled_quantity
    
    def is_filled(self) -> bool:
        """是否已完全成交"""
        return self.status == OrderStatus.FILLED
    
    def is_active(self) -> bool:
        """是否活跃（待成交）"""
        return self.status in [
            OrderStatus.PENDING,
            OrderStatus.SUBMITTED,
            OrderStatus.PARTIALLY_FILLED
        ]


@dataclass
class Trade:
    """成交记录"""
    trade_id: str
    order_id: str
    strategy_id: str
    symbol: str
    side: str
    price: float
    quantity: int
    commission: float = 0.0
    tax: float = 0.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    @property
    def turnover(self) -> float:
        """成交金额"""
        return self.price * self.quantity
    
    @property
    def net_amount(self) -> float:
        """净成交金额（扣除费用）"""
        return self.turnover - self.commission - self.tax


@dataclass
class Position:
    """持仓"""
    symbol: str
    side: str
    quantity: int
    cost_price: float
    current_price: float
    available_quantity: int = None  # 可用数量（T+1：昨日持仓）
    yesterday_quantity: int = 0  # 昨日持仓
    today_long: int = 0  # 今日买入
    today_short: int = 0  # 今日卖出
    
    def __post_init__(self):
        if self.available_quantity is None:
            self.available_quantity = self.quantity
    
    @property
    def cost_value(self) -> float:
        """持仓成本"""
        return self.cost_price * self.quantity
    
    def update_for_tplus1(self):
        """更新 T+1 状态（每日结束时调用）"""
        # 今仓变昨仓
        self.yesterday_quantity = self.quantity
        self.available_quantity = self.quantity
        self.today_long = 0
        self.today_short = 0
    
    @property
    def market_value(self) -> float:
        """持仓市值"""
        return self.current_price * self.quantity
    
    @property
    def unrealized_pnl(self) -> float:
        """浮动盈亏"""
        return self.market_value - self.cost_value
    
    @property
    def unrealized_pnl_percent(self) -> float:
        """浮动盈亏比例"""
        if self.cost_value == 0:
            return 0.0
        return self.unrealized_pnl / self.cost_value
    
    def update_price(self, price: float):
        """更新当前价格"""
        self.current_price = price
    
    def can_sell(self, quantity: int) -> bool:
        """是否可卖出指定数量"""
        return self.available_quantity >= quantity


@dataclass
class Portfolio:
    """投资组合"""
    initial_capital: float
    cash: float = None
    positions: dict = None
    frozen_cash: float = 0.0
    
    def __post_init__(self):
        if self.cash is None:
            self.cash = self.initial_capital
        if self.positions is None:
            self.positions = {}
    
    @property
    def market_value(self) -> float:
        """总市值"""
        return sum(pos.market_value for pos in self.positions.values())
    
    @property
    def total_asset(self) -> float:
        """总资产"""
        return self.cash + self.market_value
    
    @property
    def total_pnl(self) -> float:
        """总盈亏"""
        return self.total_asset - self.initial_capital
    
    @property
    def total_pnl_percent(self) -> float:
        """总盈亏比例"""
        if self.initial_capital == 0:
            return 0.0
        return self.total_pnl / self.initial_capital
    
    @property
    def available_cash(self) -> float:
        """可用资金"""
        return self.cash - self.frozen_cash
    
    @property
    def position_ratio(self) -> float:
        """仓位比例"""
        if self.total_asset == 0:
            return 0.0
        return self.market_value / self.total_asset
    
    def has_position(self, symbol: str) -> bool:
        """是否有某个持仓"""
        return symbol in self.positions
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """获取持仓"""
        return self.positions.get(symbol)
    
    def add_position(self, position: Position):
        """添加持仓"""
        self.positions[position.symbol] = position
    
    def remove_position(self, symbol: str):
        """移除持仓"""
        if symbol in self.positions:
            del self.positions[symbol]
    
    def update(self):
        """更新组合市值和盈亏"""
        # 重新计算总市值和盈亏
        pass

"""
回测引擎模块

提供回测功能：
- BacktestEngine: 回测引擎
- BacktestConfig: 回测配置
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

from ..core import Bar, Order, Trade, Portfolio, OrderSide, OrderType


@dataclass
class BacktestConfig:
    """回测配置"""
    initial_capital: float = 1000000.0  # 初始资金
    commission_rate: float = 0.0003  # 佣金率
    slippage: float = 0.001  # 滑点
    stamp_tax: float = 0.001  # 印花税（卖出）
    min_commission: float = 5.0  # 最小手续费
    benchmark: Optional[str] = None  # 基准代码
    
    def __post_init__(self):
        """验证配置"""
        assert self.initial_capital > 0, "初始资金必须大于 0"
        assert 0 <= self.commission_rate <= 1, "佣金率必须在 0-1 之间"
        assert 0 <= self.slippage <= 1, "滑点必须在 0-1 之间"
        assert 0 <= self.stamp_tax <= 1, "印花税必须在 0-1 之间"


@dataclass
class BacktestResult:
    """回测结果"""
    initial_capital: float = 1000000.0  # 初始资金
    final_capital: float = 1000000.0  # 最终资金
    total_return: float = 0.0  # 总收益
    annual_return: float = 0.0  # 年化收益
    benchmark_return: float = 0.0  # 基准收益
    excess_return: float = 0.0  # 超额收益
    volatility: float = 0.0  # 波动率
    sharpe_ratio: float = 0.0  # 夏普比率
    max_drawdown: float = 0.0  # 最大回撤
    sortino_ratio: float = 0.0  # 索提诺比率
    calmar_ratio: float = 0.0  # 卡尔玛比率
    win_rate: float = 0.0  # 胜率
    profit_loss_ratio: float = 0.0  # 盈亏比
    total_trades: int = 0  # 交易次数
    winning_trades: int = 0  # 盈利交易次数
    losing_trades: int = 0  # 亏损交易次数
    positions: dict = None  # 当前持仓
    trades: list = None  # 所有成交
    daily_values: list = None  # 每日账户值
    start_date: datetime = None  # 开始日期
    end_date: datetime = None  # 结束日期
    
    def __post_init__(self):
        """初始化默认值"""
        if self.positions is None:
            self.positions = {}
        if self.trades is None:
            self.trades = []
        if self.daily_values is None:
            self.daily_values = []
    
    def __repr__(self) -> str:
        return (
            f"BacktestResult(total_return={self.total_return:.2%}, "
            f"sharpe={self.sharpe_ratio:.2f}, max_dd={self.max_drawdown:.2%})"
        )


class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, config: BacktestConfig):
        """
        初始化回测引擎
        
        Args:
            config: 回测配置
        """
        from ..logger import get_logger
        
        self.config = config
        self.portfolio = Portfolio(initial_capital=config.initial_capital)
        self.orders: List[Order] = []
        self.trades: List[Trade] = []
        self.daily_values: List[float] = []
        self._trade_counter = 0
        self.logger = get_logger("QuantCore.BacktestEngine")
    
    def get_portfolio(self) -> Portfolio:
        """获取投资组合"""
        return self.portfolio
    
    def run(self, strategy, bars: List[Bar]) -> BacktestResult:
        strategy.on_init(self)
        
        prev_date = None
        pending_orders = []
        
        for i, bar in enumerate(bars):
            current_date = bar.timestamp.date() if hasattr(bar.timestamp, 'date') else str(bar.timestamp)[:10]
            
            if prev_date is not None and current_date != prev_date:
                self._update_tplus1_positions()
            
            prev_date = current_date
            
            self._update_positions(bar)
            
            if pending_orders:
                next_bar = bars[i] if i < len(bars) else bar
                open_price = next_bar.open if hasattr(next_bar, 'open') else next_bar.close
                self._match_pending_orders(pending_orders, open_price, bar)
                pending_orders = []
            
            strategy.on_bar(bar, self)
            
            new_pending = [o for o in self.orders if o.status.value == "pending" or o.status == OrderStatus.PENDING]
            if new_pending:
                pending_orders.extend(new_pending)
            
            self.daily_values.append(self.portfolio.total_asset)
        
        strategy.on_finish(self)
        
        result = self._calculate_performance()
        return result
    
    def _update_tplus1_positions(self):
        """更新所有持仓的 T+1 状态（每日结束时调用）"""
        for position in self.portfolio.positions.values():
            position.update_for_tplus1()
    
    def _update_positions(self, bar: Bar):
        """更新持仓价格"""
        for position in self.portfolio.positions.values():
            position.update_price(bar.close)
        self.portfolio.update()
    
    def _create_order(
        self,
        symbol: str,
        side: OrderSide,
        price: float,
        volume: int,
        order_type: str = "market",
        order_id_prefix: str = ""
    ) -> Order:
        """
        创建订单（内部方法）
        
        Args:
            symbol: 证券代码
            side: 订单方向（买入/卖出）
            price: 价格
            volume: 数量
            order_type: 订单类型 ("market" 或 "limit")
            order_id_prefix: 订单 ID 前缀
            
        Returns:
            订单对象
        """
        # 转换订单类型
        ot = OrderType.LIMIT if order_type == "limit" else OrderType.MARKET
        
        order = Order(
            order_id=f"{order_id_prefix}-{len(self.orders) + 1}",
            strategy_id="default",
            symbol=symbol,
            side=side,
            order_type=ot,
            price=price,
            quantity=volume,
        )
        self.orders.append(order)
        return order
    
    def buy(self, symbol: str, price: float, volume: int, order_type: str = "market") -> Order:
        """
        买入
        
        Args:
            symbol: 证券代码
            price: 价格
            volume: 数量
            order_type: 订单类型 ("market" 或 "limit")
            
        Returns:
            订单对象
        """
        return self._create_order(symbol, OrderSide.BUY, price, volume, order_type, "BUY")
    
    def sell(self, symbol: str, price: float, volume: int, order_type: str = "market") -> Order:
        """
        卖出
        
        Args:
            symbol: 证券代码
            price: 价格
            volume: 数量
            order_type: 订单类型 ("market" 或 "limit")
            
        Returns:
            订单对象
        """
        return self._create_order(symbol, OrderSide.SELL, price, volume, order_type, "SELL")
    
    def _match_orders(self, bar: Bar):
        from ..core import OrderStatus, OrderType
        
        pending_orders = [o for o in self.orders if o.status == OrderStatus.PENDING]
        
        if pending_orders:
            self.logger.debug(f"  发现 {len(pending_orders)} 个待成交订单")
        
        filled_orders = []
        
        for order in pending_orders:
            filled = False
            
            if order.order_type == OrderType.MARKET:
                if order.side.value == "buy":
                    fill_price = bar.close * (1 + self.config.slippage)
                else:
                    fill_price = bar.close * (1 - self.config.slippage)
                
                fill_quantity = order.quantity
                filled = True
                
                self.logger.debug(f"  市价单 {order.order_id} 准备成交：{order.side.value} {fill_quantity} @ {fill_price:.2f}")
            
            elif order.order_type == OrderType.LIMIT:
                if order.side.value == "buy":
                    if bar.low <= order.price:
                        fill_price = order.price
                        fill_quantity = order.quantity
                        filled = True
                        self.logger.debug(f"  限价买单 {order.order_id} 成交：{order.quantity} @ {order.price:.2f} (Bar Low: {bar.low:.2f})")
                else:
                    if bar.high >= order.price:
                        fill_price = order.price
                        fill_quantity = order.quantity
                        filled = True
                        self.logger.debug(f"  限价卖单 {order.order_id} 成交：{order.quantity} @ {order.price:.2f} (Bar High: {bar.high:.2f})")
            
            if filled:
                trade = self._generate_trade(order, fill_price, fill_quantity)
                self.trades.append(trade)
                
                order.status = OrderStatus.FILLED
                order.filled_quantity = fill_quantity
                order.updated_at = bar.timestamp
                
                self._update_portfolio_from_trade(trade)
                
                filled_orders.append(order)
        
        if filled_orders:
            for order in filled_orders:
                self.logger.info(f"订单 {order.order_id} 成交：{order.side.value} {order.filled_quantity} @ {order.price:.2f}")
    
    def _match_pending_orders(self, pending_orders: list, open_price: float, bar: Bar):
        from ..core import OrderStatus, OrderType
        
        for order in pending_orders:
            filled = False
            
            if order.order_type == OrderType.MARKET:
                if order.side.value == "buy":
                    fill_price = open_price * (1 + self.config.slippage)
                else:
                    fill_price = open_price * (1 - self.config.slippage)
                
                fill_quantity = order.quantity
                filled = True
            elif order.order_type == OrderType.LIMIT:
                if order.side.value == "buy":
                    if open_price <= order.price:
                        fill_price = order.price
                        fill_quantity = order.quantity
                        filled = True
                else:
                    if open_price >= order.price:
                        fill_price = order.price
                        fill_quantity = order.quantity
                        filled = True
            
            if filled:
                trade = self._generate_trade(order, fill_price, fill_quantity)
                self.trades.append(trade)
                
                order.status = OrderStatus.FILLED
                order.filled_quantity = fill_quantity
                order.updated_at = bar.timestamp
                
                self._update_portfolio_from_trade(trade)
    
    def _update_portfolio_from_trade(self, trade: Trade):
        """根据成交更新持仓（支持 T+1）"""
        from ..core import Position
        
        if trade.side.value == "buy":
            # 买入：增加持仓，减少现金
            cost = trade.price * trade.quantity + trade.commission + trade.tax
            self.portfolio.cash -= cost
            
            # 更新或创建持仓
            if trade.symbol in self.portfolio.positions:
                pos = self.portfolio.positions[trade.symbol]
                pos.quantity += trade.quantity
                pos.today_long += trade.quantity  # 今日买入
                # 更新成本价（加权平均）
                total_cost = pos.cost_price * (pos.quantity - trade.quantity) + trade.price * trade.quantity
                pos.cost_price = total_cost / pos.quantity if pos.quantity > 0 else trade.price
            else:
                self.portfolio.positions[trade.symbol] = Position(
                    symbol=trade.symbol,
                    side="long",
                    quantity=trade.quantity,
                    cost_price=trade.price,
                    current_price=trade.price,
                    available_quantity=0,  # T+1：今日买入不可用
                    yesterday_quantity=0,
                    today_long=trade.quantity,
                )
        else:
            # 卖出：减少持仓，增加现金
            if trade.symbol not in self.portfolio.positions:
                self.logger.warning(f"卖出无持仓：{trade.symbol}")
                return
            
            pos = self.portfolio.positions[trade.symbol]
            
            # T+1 检查：只能卖出可用数量（昨日持仓）
            if trade.quantity > pos.available_quantity:
                self.logger.warning(f"卖出数量超过可用持仓：{trade.quantity} > {pos.available_quantity}")
                trade.quantity = pos.available_quantity
            
            proceeds = trade.price * trade.quantity - trade.commission - trade.tax
            self.portfolio.cash += proceeds
            
            # 更新持仓
            pos.quantity -= trade.quantity
            pos.today_short += trade.quantity  # 今日卖出
            
            # 如果持仓为 0，删除持仓
            if pos.quantity <= 0:
                del self.portfolio.positions[trade.symbol]
    
    def _generate_trade(self, order: Order, price: float, quantity: int) -> Trade:
        """生成成交记录"""
        self._trade_counter += 1
        
        # 计算手续费
        turnover = price * quantity
        commission = max(turnover * self.config.commission_rate, self.config.min_commission)
        
        # 计算印花税（仅卖出收取）
        tax = 0.0
        if order.side == "sell":
            tax = turnover * self.config.stamp_tax
        
        trade = Trade(
            trade_id=f"TRD-{self._trade_counter}",
            order_id=order.order_id,
            strategy_id=order.strategy_id,
            symbol=order.symbol,
            side=order.side,
            price=price,
            quantity=quantity,
            commission=commission,
            tax=tax,
        )
        
        self.trades.append(trade)
        return trade
    
    def _calculate_performance(self) -> BacktestResult:
        """计算绩效指标"""
        import statistics
        
        result = BacktestResult()
        
        if len(self.daily_values) == 0:
            result.total_trades = len(self.trades)
            result.positions = dict(self.portfolio.positions)
            result.trades = self.trades.copy()
            return result
        
        # 基础指标
        result.initial_capital = self.config.initial_capital
        result.final_capital = self.daily_values[-1]
        result.total_return = (self.daily_values[-1] - self.config.initial_capital) / self.config.initial_capital
        result.daily_values = self.daily_values.copy()
        
        # 计算日收益率
        daily_returns = []
        for i in range(1, len(self.daily_values)):
            prev_value = self.daily_values[i-1]
            curr_value = self.daily_values[i]
            if prev_value > 0:
                daily_return = (curr_value - prev_value) / prev_value
                daily_returns.append(daily_return)
        
        # 年化收益（假设 252 个交易日）
        if len(daily_returns) > 0:
            total_days = len(self.daily_values)
            result.annual_return = (1 + result.total_return) ** (252 / total_days) - 1
        
        # 波动率（年化）
        if len(daily_returns) > 1:
            daily_volatility = statistics.stdev(daily_returns)
            result.volatility = daily_volatility * (252 ** 0.5)
        
        # 夏普比率（假设无风险利率为 3%）
        if result.volatility > 0:
            risk_free_rate = 0.03
            result.sharpe_ratio = (result.annual_return - risk_free_rate) / result.volatility
        
        # 最大回撤
        peak = self.daily_values[0]
        max_drawdown = 0.0
        for value in self.daily_values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak if peak > 0 else 0
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        result.max_drawdown = max_drawdown
        
        # 卡尔玛比率
        if result.max_drawdown > 0:
            result.calmar_ratio = result.annual_return / result.max_drawdown
        
        # 索提诺比率（只考虑下行波动）
        if len(daily_returns) > 1:
            downside_returns = [r for r in daily_returns if r < 0]
            if downside_returns:
                downside_std = statistics.stdev(downside_returns) if len(downside_returns) > 1 else downside_returns[0]
                if downside_std > 0:
                    result.sortino_ratio = (result.annual_return - 0.03) / (downside_std * (252 ** 0.5))
        
        # 交易统计
        result.total_trades = len(self.trades)
        result.positions = dict(self.portfolio.positions)
        result.trades = self.trades.copy()
        
        # 胜率和盈亏比
        if self.trades:
            avg_buy_prices = {}
            winning = 0
            losing = 0
            total_win = 0.0
            total_loss = 0.0
            
            for trade in self.trades:
                symbol = trade.symbol
                if trade.side.value == "buy":
                    if symbol not in avg_buy_prices:
                        avg_buy_prices[symbol] = {"total_cost": 0.0, "total_qty": 0}
                    avg_buy_prices[symbol]["total_cost"] += trade.price * trade.quantity
                    avg_buy_prices[symbol]["total_qty"] += trade.quantity
                elif trade.side.value == "sell":
                    if symbol in avg_buy_prices and avg_buy_prices[symbol]["total_qty"] > 0:
                        avg_cost = avg_buy_prices[symbol]["total_cost"] / avg_buy_prices[symbol]["total_qty"]
                        pnl = (trade.price - avg_cost) * trade.quantity - trade.commission - trade.tax
                        if pnl > 0:
                            winning += 1
                            total_win += pnl
                        else:
                            losing += 1
                            total_loss += abs(pnl)
                        avg_buy_prices[symbol]["total_cost"] -= avg_cost * trade.quantity
                        avg_buy_prices[symbol]["total_qty"] -= trade.quantity
            
            result.winning_trades = winning
            result.losing_trades = losing
            
            if winning + losing > 0:
                result.win_rate = winning / (winning + losing)
            
            if losing > 0 and total_loss > 0:
                avg_win = total_win / winning if winning > 0 else 0
                avg_loss = total_loss / losing
                result.profit_loss_ratio = avg_win / avg_loss
        
        return result

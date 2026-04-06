# -*- coding: utf-8 -*-
"""
风险管理系统

提供全面的风险控制功能：
- 仓位控制
- 止损止盈
- 单日亏损限制
- 最大回撤控制
- 交易限制
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskConfig:
    """风险配置参数"""
    # 仓位控制
    max_position_ratio: float = 0.95  # 最大仓位比例
    max_single_position_ratio: float = 0.30  # 单只股票最大仓位比例
    
    # 止损控制
    stop_loss_ratio: float = 0.08  # 止损线（8%）
    stop_profit_ratio: float = 0.20  # 止盈线（20%）
    
    # 亏损限制
    max_daily_loss: float = 50000.0  # 单日最大亏损
    max_drawdown_ratio: float = 0.15  # 最大回撤（15%）
    
    # 交易限制
    max_trades_per_day: int = 10  # 单日最大交易次数
    min_cash_ratio: float = 0.05  # 最小现金比例


@dataclass
class RiskMetrics:
    """风险指标"""
    # 仓位指标
    total_asset: float = 0.0
    position_value: float = 0.0
    position_ratio: float = 0.0
    cash: float = 0.0
    cash_ratio: float = 0.0
    
    # 盈亏指标
    daily_pnl: float = 0.0
    total_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    
    # 回撤指标
    peak_value: float = 0.0
    current_drawdown: float = 0.0
    max_drawdown: float = 0.0
    
    # 交易统计
    trades_today: int = 0
    total_trades: int = 0


class RiskManager:
    """
    风险管理器
    
    功能：
    1. 实时监控风险指标
    2. 交易前风控检查
    3. 止损止盈判断
    4. 风险预警
    5. 强制平仓（极端情况）
    
    使用示例：
    ```python
    from quantcore.risk import RiskManager, RiskConfig
    
    config = RiskConfig(
        max_position_ratio=0.90,
        stop_loss_ratio=0.08,
        max_daily_loss=50000
    )
    
    risk_manager = RiskManager(config, initial_capital=1000000)
    
    # 交易前检查
    if risk_manager.can_buy(symbol, amount):
        engine.buy(symbol, price, amount)
    
    # 更新持仓
    risk_manager.update_position(symbol, quantity, cost_price, current_price)
    
    # 检查止损
    if risk_manager.check_stop_loss(symbol, current_price):
        engine.sell(symbol, price, quantity)
    ```
    """
    
    def __init__(self, config: RiskConfig, initial_capital: float, is_backtest: bool = False):
        """
        初始化风控管理器
        
        Args:
            config: 风控配置
            initial_capital: 初始资金
            is_backtest: 是否为回测模式（回测模式使用传入的日期而非系统日期）
        """
        self.config = config
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        
        # 持仓信息 {symbol: {quantity, cost_price, current_price}}
        self.positions: Dict[str, Dict[str, float]] = {}
        
        # 交易记录
        self.today_trades: List[Dict[str, Any]] = []
        self.today_pnl: float = 0.0
        self.today_date: Optional[date] = None
        self.is_backtest = is_backtest  # 回测模式标志
        
        # 风险指标
        self.peak_value: float = initial_capital
        self.max_drawdown: float = 0.0
        
        # 风险日志
        self.risk_logs: List[Dict[str, Any]] = []
        
        # 风控开关
        self.enabled: bool = True
        self.trading_halted: bool = False  # 是否暂停交易
    
    def update_portfolio(self, total_asset: float, cash: float, current_date: Optional[date] = None):
        """
        更新组合资产
        
        Args:
            total_asset: 总资产
            cash: 现金
            current_date: 当前日期（回测模式必须传入）
        """
        self.current_capital = total_asset
        self.cash = cash
        
        # 更新峰值
        if total_asset > self.peak_value:
            self.peak_value = total_asset
        
        # 计算回撤
        if self.peak_value > 0:
            self.current_drawdown = (self.peak_value - total_asset) / self.peak_value
            self.max_drawdown = max(self.max_drawdown, self.current_drawdown)
        
        # 检查日期（新的一天重置交易计数）
        if self.is_backtest:
            # 回测模式：使用传入的日期
            today = current_date
        else:
            # 实盘模式：使用系统日期
            today = date.today()
        
        if today is not None and self.today_date != today:
            self.today_date = today
            self.today_trades = []
            self.today_pnl = 0.0
    
    def update_position(self, symbol: str, quantity: float, cost_price: float, 
                       current_price: float):
        """
        更新持仓信息
        
        Args:
            symbol: 证券代码
            quantity: 数量
            cost_price: 成本价
            current_price: 当前价
        """
        self.positions[symbol] = {
            'quantity': quantity,
            'cost_price': cost_price,
            'current_price': current_price,
            'market_value': quantity * current_price
        }
    
    def remove_position(self, symbol: str):
        """移除持仓"""
        if symbol in self.positions:
            del self.positions[symbol]
    
    def get_risk_metrics(self) -> RiskMetrics:
        """获取风险指标"""
        # 计算持仓市值
        position_value = sum(pos['market_value'] for pos in self.positions.values())
        total_asset = position_value + self.cash
        
        # 计算仓位
        position_ratio = position_value / total_asset if total_asset > 0 else 0
        cash_ratio = self.cash / total_asset if total_asset > 0 else 0
        
        # 计算盈亏
        total_cost = sum(pos['quantity'] * pos['cost_price'] for pos in self.positions.values())
        unrealized_pnl = position_value - total_cost
        total_pnl = total_asset - self.initial_capital
        
        return RiskMetrics(
            total_asset=total_asset,
            position_value=position_value,
            position_ratio=position_ratio,
            cash=self.cash,
            cash_ratio=cash_ratio,
            daily_pnl=self.today_pnl,
            total_pnl=total_pnl,
            unrealized_pnl=unrealized_pnl,
            peak_value=self.peak_value,
            current_drawdown=self.current_drawdown,
            max_drawdown=self.max_drawdown,
            trades_today=len(self.today_trades),
            total_trades=len(self.today_trades)
        )
    
    def can_buy(self, symbol: str, amount: float, price: float) -> bool:
        """
        检查是否可以买入
        
        Args:
            symbol: 证券代码
            amount: 买入数量
            price: 买入价格
            
        Returns:
            bool: 是否允许买入
        """
        if not self.enabled or self.trading_halted:
            return False
        
        # 1. 检查单日交易次数
        if len(self.today_trades) >= self.config.max_trades_per_day:
            self.log_risk("超过单日最大交易次数", RiskLevel.HIGH)
            return False
        
        # 2. 检查现金是否足够
        total_cost = amount * price
        if total_cost > self.cash * 0.95:  # 留 5% 缓冲
            self.log_risk("现金不足", RiskLevel.MEDIUM)
            return False
        
        # 3. 检查单只股票仓位限制
        current_position_value = self.positions.get(symbol, {}).get('market_value', 0)
        new_position_value = current_position_value + total_cost
        total_asset = sum(pos['market_value'] for pos in self.positions.values()) + self.cash
        
        if total_asset > 0:
            single_ratio = new_position_value / total_asset
            if single_ratio > self.config.max_single_position_ratio:
                self.log_risk(f"单只股票仓位超限：{single_ratio:.2%}", RiskLevel.HIGH)
                return False
        
        # 4. 检查总仓位限制
        position_value = sum(pos['market_value'] for pos in self.positions.values())
        if total_asset > 0:
            new_position_ratio = (position_value + total_cost) / total_asset
            if new_position_ratio > self.config.max_position_ratio:
                self.log_risk(f"总仓位超限：{new_position_ratio:.2%}", RiskLevel.HIGH)
                return False
        
        return True
    
    def can_sell(self, symbol: str, amount: float) -> bool:
        """
        检查是否可以卖出
        
        Args:
            symbol: 证券代码
            amount: 卖出数量
            
        Returns:
            bool: 是否允许卖出
        """
        if not self.enabled:
            return False
        
        # 检查持仓是否足够
        if symbol not in self.positions:
            return False
        
        position = self.positions[symbol]
        if amount > position['quantity']:
            return False
        
        return True
    
    def check_stop_loss(self, symbol: str, current_price: float) -> bool:
        """
        检查是否触发止损
        
        Args:
            symbol: 证券代码
            current_price: 当前价格
            
        Returns:
            bool: 是否触发止损
        """
        if symbol not in self.positions:
            return False
        
        position = self.positions[symbol]
        cost_price = position['cost_price']
        
        # 计算盈亏比例
        pnl_ratio = (current_price - cost_price) / cost_price
        
        # 止损检查
        if pnl_ratio <= -self.config.stop_loss_ratio:
            self.log_risk(f"{symbol} 触发止损：{pnl_ratio:.2%}", RiskLevel.CRITICAL)
            return True
        
        return False
    
    def check_stop_profit(self, symbol: str, current_price: float) -> bool:
        """
        检查是否触发止盈
        
        Args:
            symbol: 证券代码
            current_price: 当前价格
            
        Returns:
            bool: 是否触发止盈
        """
        if symbol not in self.positions:
            return False
        
        position = self.positions[symbol]
        cost_price = position['cost_price']
        
        # 计算盈亏比例
        pnl_ratio = (current_price - cost_price) / cost_price
        
        # 止盈检查
        if pnl_ratio >= self.config.stop_profit_ratio:
            self.log_risk(f"{symbol} 触发止盈：{pnl_ratio:.2%}", RiskLevel.MEDIUM)
            return True
        
        return False
    
    def check_daily_loss_limit(self) -> bool:
        """
        检查是否触及单日亏损限制
        
        Returns:
            bool: 是否触及限制
        """
        if self.today_pnl <= -self.config.max_daily_loss:
            self.log_risk(f"触及单日亏损限制：{self.today_pnl:.2f}", RiskLevel.CRITICAL)
            self.trading_halted = True
            return True
        return False
    
    def check_max_drawdown(self) -> bool:
        """
        检查是否触及最大回撤限制
        
        Returns:
            bool: 是否触及限制
        """
        if self.current_drawdown >= self.config.max_drawdown_ratio:
            self.log_risk(f"触及最大回撤限制：{self.current_drawdown:.2%}", RiskLevel.CRITICAL)
            self.trading_halted = True
            return True
        return False
    
    def add_trade(self, symbol: str, side: str, amount: float, price: float, 
                  pnl: float = 0.0):
        """
        添加交易记录
        
        Args:
            symbol: 证券代码
            side: 买卖方向 ('buy' 或 'sell')
            amount: 数量
            price: 价格
            pnl: 盈亏
        """
        trade = {
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'price': price,
            'pnl': pnl,
            'timestamp': datetime.now()
        }
        self.today_trades.append(trade)
        self.today_pnl += pnl
    
    def get_position_info(self, symbol: str) -> Optional[Dict[str, float]]:
        """获取持仓信息"""
        return self.positions.get(symbol)
    
    def get_all_positions(self) -> Dict[str, Dict[str, float]]:
        """获取所有持仓"""
        return self.positions.copy()
    
    def log_risk(self, message: str, level: RiskLevel):
        """记录风险日志"""
        log_entry = {
            'timestamp': datetime.now(),
            'message': message,
            'level': level.value
        }
        self.risk_logs.append(log_entry)
        
        # 打印警告
        if level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            print(f"[RISK {level.value.upper()}] {message}")
    
    def get_risk_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取风险日志"""
        return self.risk_logs[-limit:]
    
    def enable(self):
        """启用风控"""
        self.enabled = True
        self.trading_halted = False
    
    def disable(self):
        """禁用风控"""
        self.enabled = False
    
    def reset_daily(self):
        """重置每日统计"""
        self.today_trades = []
        self.today_pnl = 0.0
        self.trading_halted = False
    
    def get_risk_report(self) -> Dict[str, Any]:
        """获取风险报告"""
        metrics = self.get_risk_metrics()
        
        return {
            'date': str(date.today()),
            'total_asset': metrics.total_asset,
            'position_ratio': f"{metrics.position_ratio:.2%}",
            'cash_ratio': f"{metrics.cash_ratio:.2%}",
            'daily_pnl': f"{metrics.daily_pnl:.2f}",
            'total_pnl': f"{metrics.total_pnl:.2f}",
            'current_drawdown': f"{metrics.current_drawdown:.2%}",
            'max_drawdown': f"{metrics.max_drawdown:.2%}",
            'trades_today': metrics.trades_today,
            'trading_halted': self.trading_halted,
            'risk_level': self._calculate_risk_level().value
        }
    
    def _calculate_risk_level(self) -> RiskLevel:
        """计算当前风险等级"""
        metrics = self.get_risk_metrics()
        
        # 检查各项指标
        if self.trading_halted:
            return RiskLevel.CRITICAL
        
        if metrics.current_drawdown > self.config.max_drawdown_ratio * 0.8:
            return RiskLevel.CRITICAL
        
        if metrics.position_ratio > self.config.max_position_ratio * 0.9:
            return RiskLevel.HIGH
        
        if abs(metrics.daily_pnl) > self.config.max_daily_loss * 0.8:
            return RiskLevel.HIGH
        
        if metrics.position_ratio > self.config.max_position_ratio * 0.7:
            return RiskLevel.MEDIUM
        
        return RiskLevel.LOW


# 导出
__all__ = [
    'RiskConfig',
    'RiskMetrics',
    'RiskLevel',
    'RiskManager',
]

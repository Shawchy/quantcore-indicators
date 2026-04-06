# -*- coding: utf-8 -*-
"""
风险管理模块

提供风险管理功能：
- RiskManager: 风险管理器
- PositionLimit: 仓位限制
- StopLoss: 止损策略
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class PositionLimit:
    """仓位限制"""
    symbol: str  # 证券代码
    max_percent: float  # 最大仓位比例
    max_volume: int  # 最大数量


@dataclass
class StopLoss:
    """止损策略"""
    type: str  # 'fixed', 'trailing', 'time'
    percent: float  # 止损比例
    trigger_price: Optional[float] = None  # 触发价格


class RiskManager:
    """风险管理器"""
    
    def __init__(self):
        """初始化风险管理器"""
        self.position_limits: List[PositionLimit] = []
        self.stop_losses: Dict[str, StopLoss] = {}
        self.daily_loss_limit: float = 50000.0  # 单日最大亏损
        self.max_drawdown_limit: float = 0.15  # 最大回撤限制
        self.total_position_limit: float = 0.95  # 总仓位限制
    
    def add_position_limit(self, limit: PositionLimit):
        """添加仓位限制"""
        self.position_limits.append(limit)
    
    def add_stop_loss(self, symbol: str, stop_loss: StopLoss):
        """添加止损策略"""
        self.stop_losses[symbol] = stop_loss
    
    def set_daily_loss_limit(self, amount: float):
        """设置单日最大亏损"""
        self.daily_loss_limit = amount
    
    def set_max_drawdown(self, percent: float):
        """设置最大回撤"""
        self.max_drawdown_limit = percent
    
    def check_buy(self, symbol: str, price: float, volume: int, 
                  portfolio_value: float, current_position: int) -> bool:
        """
        检查买入是否合规
        
        Args:
            symbol: 证券代码
            price: 价格
            volume: 数量
            portfolio_value: 组合总值
            current_position: 当前持仓
            
        Returns:
            是否允许买入
        """
        # 检查总仓位限制
        new_position_value = (current_position + volume) * price
        if new_position_value / portfolio_value > self.total_position_limit:
            print(f"超过总仓位限制：{self.total_position_limit*100:.0f}%")
            return False
        
        # 检查单个证券仓位限制
        for limit in self.position_limits:
            if limit.symbol == symbol:
                if (current_position + volume) > limit.max_volume:
                    print(f"超过最大数量限制：{limit.max_volume}")
                    return False
                if new_position_value / portfolio_value > limit.max_percent:
                    print(f"超过最大仓位比例：{limit.max_percent*100:.0f}%")
                    return False
        
        return True
    
    def check_sell(self, symbol: str, price: float, volume: int,
                   current_position: int) -> bool:
        """
        检查卖出是否合规
        
        Returns:
            是否允许卖出
        """
        # T+1 检查（简化版）
        if volume > current_position:
            print(f"超过可卖数量：{current_position}")
            return False
        
        return True
    
    def check_stop_loss(self, symbol: str, current_price: float, 
                        cost_price: float) -> bool:
        """
        检查是否触发止损
        
        Returns:
            是否触发止损
        """
        if symbol not in self.stop_losses:
            return False
        
        stop_loss = self.stop_losses[symbol]
        
        if stop_loss.type == 'fixed':
            # 固定止损
            loss_percent = (current_price - cost_price) / cost_price
            if loss_percent <= -stop_loss.percent:
                print(f"{symbol} 触发固定止损：{loss_percent*100:.2f}%")
                return True
        
        elif stop_loss.type == 'trailing':
            # 移动止损（简化版）
            peak_price = max(cost_price, current_price)
            loss_percent = (peak_price - current_price) / peak_price
            if loss_percent >= stop_loss.percent:
                print(f"{symbol} 触发移动止损：{loss_percent*100:.2f}%")
                return True
        
        return False
    
    def check_daily_loss(self, daily_pnl: float) -> bool:
        """
        检查单日亏损
        
        Returns:
            是否超过限制
        """
        if daily_pnl < -self.daily_loss_limit:
            print(f"超过单日亏损限制：{daily_pnl:.2f}")
            return True
        return False

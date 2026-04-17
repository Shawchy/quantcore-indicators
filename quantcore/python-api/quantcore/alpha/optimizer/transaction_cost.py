"""
交易成本模型与再平衡策略

计算交易成本，优化再平衡时机和方式。
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from loguru import logger


@dataclass
class TransactionCostConfig:
    """交易成本配置"""
    commission_rate: float = 0.0003  # 佣金率 (万三)
    stamp_tax_rate: float = 0.001  # 印花税（仅卖出）
    slippage_rate: float = 0.001  # 滑点 (0.1%)
    impact_coefficient: float = 0.1  # 市场冲击系数
    min_commission: float = 5.0  # 最小佣金 (元)
    
    # A 股特殊规则
    t_plus_one: bool = True  # T+1 规则
    price_tick: float = 0.01  # 价格最小变动单位
    lot_size: int = 100  # 最小交易手数


@dataclass
class TradeCost:
    """单笔交易成本"""
    symbol: str
    direction: str  # "buy" / "sell"
    quantity: int
    price: float
    
    commission: float = 0.0  # 佣金
    stamp_tax: float = 0.0  # 印花税
    slippage: float = 0.0  # 滑点成本
    market_impact: float = 0.0  # 市场冲击
    total_cost: float = 0.0  # 总成本
    cost_ratio: float = 0.0  # 成本占比


class TransactionCostModel:
    """
    交易成本模型
    
    计算 A 股交易的完整成本：
    - 佣金（双向）
    - 印花税（卖出）
    - 滑点
    - 市场冲击（大额交易）
    
    使用示例：
        model = TransactionCostModel()
        
        cost = model.calculate_trade_cost(
            symbol="000001",
            direction="buy",
            quantity=1000,
            price=12.50,
            market_cap=1e12
        )
        print(f"总成本: {cost.total_cost:.2f} 元")
    """
    
    def __init__(self, config: Optional[TransactionCostConfig] = None):
        self.config = config or TransactionCostConfig()
    
    def calculate_trade_cost(
        self,
        symbol: str,
        direction: str,
        quantity: int,
        price: float,
        market_cap: Optional[float] = None,
        avg_daily_volume: Optional[float] = None
    ) -> TradeCost:
        """
        计算单笔交易成本
        
        Args:
            symbol: 股票代码
            direction: "buy" 或 "sell"
            quantity: 交易数量（股）
            price: 交易价格
            market_cap: 总市值（用于市场冲击估算）
            avg_daily_volume: 日均成交量
            
        Returns:
            TradeCost: 详细成本明细
        """
        trade_value = abs(quantity * price)
        
        # 1. 佣金
        commission = max(
            trade_value * self.config.commission_rate,
            self.config.min_commission
        )
        
        # 2. 印花税（仅卖出）
        if direction == "sell":
            stamp_tax = trade_value * self.config.stamp_tax_rate
        else:
            stamp_tax = 0.0
        
        # 3. 滑点
        slippage = trade_value * self.config.slippage_rate
        
        # 4. 市场冲击（基于交易金额占市值比例）
        if market_cap is not None and market_cap > 0:
            trade_ratio = trade_value / market_cap
            impact = self._calculate_market_impact(trade_ratio, trade_value)
        elif avg_daily_volume is not None:
            volume_ratio = trade_value / avg_daily_volume
            impact = self._calculate_market_impact(volume_ratio, trade_value)
        else:
            impact = 0.0
        
        total_cost = commission + stamp_tax + slippage + impact
        cost_ratio = total_cost / trade_value if trade_value > 0 else 0
        
        return TradeCost(
            symbol=symbol,
            direction=direction,
            quantity=quantity,
            price=price,
            commission=commission,
            stamp_tax=stamp_tax,
            slippage=slippage,
            market_impact=impact,
            total_cost=total_cost,
            cost_ratio=cost_ratio
        )
    
    def _calculate_market_impact(self, ratio: float, trade_value: float) -> float:
        """计算市场冲击成本"""
        # 简化的平方根模型：Impact ∝ ratio^{2/3}
        if ratio <= 0:
            return 0.0
        
        impact = self.config.impact_coefficient * (trade_value ** 0.5) * (ratio ** 0.67)
        
        return impact
    
    def calculate_rebalance_cost(
        self,
        current_weights: pd.Series,
        target_weights: pd.Series,
        prices: pd.Series,
        portfolio_value: float,
        market_caps: Optional[pd.Series] = None
    ) -> Dict[str, Any]:
        """
        计算再平衡的总成本
        
        Args:
            current_weights: 当前权重
            target_weights: 目标权重
            prices: 各资产价格
            portfolio_value: 组合总值
            market_caps: 各资产市值（可选）
            
        Returns:
            Dict: 成本分析结果
        """
        common_idx = current_weights.index.intersection(target_weights.index)
        
        trades = []
        total_cost = 0.0
        
        for symbol in common_idx:
            w_old = current_weights[symbol]
            w_new = target_weights.get(symbol, 0)
            
            delta_w = w_new - w_old
            
            if abs(delta_w) < 0.005:  # 忽略小于0.5%的变动
                continue
            
            old_value = w_old * portfolio_value
            new_value = w_new * portfolio_value
            delta_value = new_value - old_value
            
            price = prices.get(symbol, 1.0)
            quantity = int(abs(delta_value) / price / 100) * 100  # 取整到百股
            direction = "buy" if delta_value > 0 else "sell"
            
            if quantity == 0:
                continue
            
            mcap = market_caps[symbol] if market_caps is not None else None
            
            cost = self.calculate_trade_cost(
                symbol=symbol,
                direction=direction,
                quantity=quantity,
                price=price,
                market_cap=mcap
            )
            
            trades.append({
                "symbol": symbol,
                "direction": direction,
                "quantity": quantity,
                "delta_weight": delta_w,
                "delta_value": delta_value,
                "cost": cost.total_cost,
                "cost_ratio": cost.cost_ratio
            })
            
            total_cost += cost.total_cost
        
        turnover = sum(t["delta_value"] for t in trades) / (2 * portfolio_value)
        
        return {
            "trades": trades,
            "total_trades": len(trades),
            "total_cost": total_cost,
            "cost_ratio": total_cost / portfolio_value if portfolio_value > 0 else 0,
            "turnover": turnover,
            "n_buys": sum(1 for t in trades if t["direction"] == "buy"),
            "n_sells": sum(1 for t in trades if t["direction"] == "sell"),
            "is_acceptable": total_cost / portfolio_value < 0.01 if portfolio_value > 0 else False
        }
    
    def optimize_rebalance_threshold(
        self,
        current_weights: pd.Series,
        target_weights: pd.Series,
        prices: pd.Series,
        portfolio_value: float,
        max_cost_ratio: float = 0.02
    ) -> Tuple[pd.Series, Dict]:
        """
        优化再平衡阈值
        
        只对偏离超过阈值的资产进行交易，
        以控制交易成本。
        
        Returns:
            Tuple: (实际执行的目标权重, 成本信息)
        """
        deviation = (target_weights - current_weights).abs()
        
        # 找出需要调整的资产
        threshold = self._estimate_optimal_threshold(deviation, portfolio_value)
        
        adjusted_target = current_weights.copy()
        for symbol in deviation.index:
            if deviation[symbol] >= threshold:
                adjusted_target[symbol] = target_weights[symbol]
        
        # 归一化
        adjusted_target = adjusted_target / adjusted_target.sum()
        
        cost_info = self.calculate_rebalance_cost(
            current_weights, adjusted_target, prices, portfolio_value
        )
        
        # 如果成本过高，提高阈值重新计算
        if cost_info["cost_ratio"] > max_cost_ratio:
            threshold *= 1.5
            adjusted_target = current_weights.copy()
            for symbol in deviation.index:
                if deviation[symbol] >= threshold:
                    adjusted_target[symbol] = target_weights[symbol]
            adjusted_target = adjusted_target / adjusted_target.sum()
            
            cost_info = self.calculate_rebalance_cost(
                current_weights, adjusted_target, prices, portfolio_value
            )
        
        return adjusted_target, cost_info
    
    def _estimate_optimal_threshold(
        self,
        deviation: pd.Series,
        portfolio_value: float
    ) -> float:
        """估计最优再平衡阈值"""
        # 基于偏差分布确定阈值
        median_dev = deviation.median()
        mean_dev = deviation.mean()
        
        # 使用分位数作为阈值
        threshold = max(median_dev * 0.5, 0.02)  # 至少 2%
        threshold = min(threshold, 0.10)  # 至多 10%
        
        return threshold


class Rebalancer:
    """
    再平衡策略管理器
    
    提供多种再平衡策略：
    - 定期再平衡（按时间）
    - 阈值触发再平衡（偏离度）
    - 波动率目标再平衡
    - 日历效应再平衡
    """
    
    def __init__(self, cost_model: Optional[TransactionCostModel] = None):
        self.cost_model = cost_model or TransactionCostModel()
    
    def should_rebalance(
        self,
        current_weights: pd.Series,
        target_weights: pd.Series,
        strategy: str = "threshold",
        **kwargs
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        判断是否需要再平衡
        
        Args:
            current_weights: 当前权重
            target_weights: 目标权重
            strategy: 策略类型 ("threshold"/"calendar"/"volatility"/"drift")
            **kwargs: 策略参数
            
        Returns:
            Tuple: (是否需要再平衡, 详情)
        """
        drift = (target_weights - current_weights).abs().sum() / 2
        
        info = {
            "current_date": kwargs.get("date"),
            "max_drift": float(drift),
            "mean_drift": float((target_weights - current_weights).abs().mean()),
            "top_drifts": dict(target_weights.nlargest(3))
        }
        
        if strategy == "threshold":
            threshold = kwargs.get("threshold", 0.05)
            should = drift >= threshold
            info["threshold"] = threshold
            info["exceeded"] = should
            
        elif strategy == "calendar":
            days_since_last = kwargs.get("days_since_last", 30)
            frequency = kwargs.get("frequency", "monthly")  # monthly/quarterly
            
            freq_days = {"monthly": 21, "quarterly": 63}.get(frequency, 21)
            should = days_since_last >= freq_days
            info["days_since_last"] = days_since_last
            info["frequency"] = frequency
            
        elif strategy == "volatility":
            current_vol = kwargs.get("portfolio_volatility", 0.15)
            target_vol = kwargs.get("target_volatility", 0.15)
            vol_diff = abs(current_vol - target_vol)
            
            should = vol_diff > 0.02  # 波动率偏离超过 2%
            info["current_vol"] = current_vol
            info["target_vol"] = target_vol
            info["vol_difference"] = vol_diff
            
        else:
            should = drift >= 0.03  # 默认 3% 偏离
        
        return should, info
    
    def generate_rebalance_orders(
        self,
        current_weights: pd.Series,
        target_weights: pd.Series,
        prices: pd.Series,
        portfolio_value: float,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        生成再平衡订单列表
        
        Returns:
            List[Dict]: 订单列表 [{symbol, side, quantity, ...}]
        """
        optimized_target, cost_info = self.cost_model.optimize_rebalance_threshold(
            current_weights, target_weights, prices, portfolio_value
        )
        
        orders = []
        
        for symbol in optimized_target.index:
            w_old = current_weights.get(symbol, 0)
            w_new = optimized_target[symbol]
            
            if abs(w_new - w_old) < 0.005:
                continue
            
            price = prices.get(symbol, 1.0)
            delta_value = (w_new - w_old) * portfolio_value
            quantity = int(abs(delta_value) / price / 100) * 100
            
            if quantity == 0:
                continue
            
            direction = "BUY" if delta_value > 0 else "SELL"
            
            orders.append({
                "symbol": symbol,
                "side": direction,
                "quantity": quantity,
                "price": price,
                "target_weight": w_new,
                "current_weight": w_old,
                "notional": abs(delta_value)
            })
        
        return orders

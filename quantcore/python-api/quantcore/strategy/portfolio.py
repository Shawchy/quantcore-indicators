"""
多策略组合模块

支持多个策略的组合管理、资金分配和绩效分析
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import copy

from .base import Strategy
from ..core import Bar, Order, Trade, Position, Portfolio
from ..engine import BacktestEngine, BacktestResult
from ..logger import get_logger, QuantLogger


@dataclass
class StrategyConfig:
    """策略配置"""
    name: str
    strategy: Strategy
    weight: float  # 权重 (0-1)
    capital_allocation: float = 0.0  # 分配资金（计算得出）
    enabled: bool = True  # 是否启用


@dataclass
class StrategyResult:
    """策略执行结果"""
    name: str
    weight: float
    initial_capital: float
    final_capital: float
    return_rate: float
    sharpe_ratio: float
    max_drawdown: float
    total_trades: int
    daily_values: List[float] = field(default_factory=list)


class StrategyPortfolio:
    """
    多策略组合管理器
    
    功能：
    1. 管理多个策略实例
    2. 按权重分配资金
    3. 独立运行各策略
    4. 汇总组合绩效
    5. 支持策略间隔离（独立持仓、订单）
    
    使用示例：
    ```python
    portfolio = StrategyPortfolio(initial_capital=1000000)
    portfolio.add_strategy("MACD", MACDStrategy(), weight=0.4)
    portfolio.add_strategy("RSI", RSIStrategy(), weight=0.3)
    portfolio.add_strategy("BOLL", BOLLStrategy(), weight=0.3)
    
    result = portfolio.run(bars)
    print(f"组合收益：{result['total_return']:.2%}")
    ```
    """
    
    def __init__(self, initial_capital: float = 1000000.0):
        """
        初始化策略组合
        
        Args:
            initial_capital: 初始总资金
        """
        self.initial_capital = initial_capital
        self.strategies: Dict[str, StrategyConfig] = {}
        self.results: Dict[str, StrategyResult] = {}
        self.logger = get_logger("QuantCore.Portfolio")
        
        # 组合级别的统计
        self.combined_daily_values: List[float] = []
        self.combined_trades: List[Trade] = []
        
    def add_strategy(self, name: str, strategy: Strategy, weight: float) -> None:
        """
        添加策略到组合
        
        Args:
            name: 策略名称
            strategy: 策略实例
            weight: 权重 (0-1)，所有策略权重之和应为 1
            
        Example:
        ```python
        portfolio.add_strategy("Trend", TrendFollowingStrategy(), weight=0.5)
        portfolio.add_strategy("MeanReversion", MeanReversionStrategy(), weight=0.5)
        ```
        """
        if weight <= 0 or weight > 1:
            raise ValueError(f"权重必须在 (0, 1] 范围内：{weight}")
        
        if name in self.strategies:
            raise ValueError(f"策略已存在：{name}")
        
        config = StrategyConfig(
            name=name,
            strategy=strategy,
            weight=weight,
            capital_allocation=self.initial_capital * weight
        )
        
        self.strategies[name] = config
        self.logger.info(f"添加策略：{name}, 权重={weight:.2%}, 分配资金={config.capital_allocation:.2f}")
    
    def remove_strategy(self, name: str) -> None:
        """移除策略"""
        if name in self.strategies:
            del self.strategies[name]
            self.logger.info(f"移除策略：{name}")
        else:
            self.logger.warning(f"策略不存在：{name}")
    
    def enable_strategy(self, name: str) -> None:
        """启用策略"""
        if name in self.strategies:
            self.strategies[name].enabled = True
            self.logger.info(f"启用策略：{name}")
        else:
            self.logger.warning(f"策略不存在：{name}")
    
    def disable_strategy(self, name: str) -> None:
        """禁用策略"""
        if name in self.strategies:
            self.strategies[name].enabled = False
            self.logger.info(f"禁用策略：{name}")
        else:
            self.logger.warning(f"策略不存在：{name}")
    
    def validate_weights(self) -> bool:
        """
        验证权重之和是否为 1
        
        Returns:
            bool: 权重是否有效
        """
        total_weight = sum(
            cfg.weight for cfg in self.strategies.values() 
            if cfg.enabled
        )
        
        if abs(total_weight - 1.0) > 0.001:
            self.logger.warning(f"权重之和不等于 1: {total_weight:.4f}")
            return False
        
        return True
    
    def run(
        self,
        bars: List[Bar],
        symbol: str = "SH.600000",
        commission_rate: float = 0.0003,
        tax_rate: float = 0.001,
        slippage: float = 0.002,
        tplus1: bool = True
    ) -> Dict[str, Any]:
        """
        运行策略组合回测
        
        Args:
            bars: K 线数据列表
            symbol: 交易标的
            commission_rate: 手续费率
            tax_rate: 税率
            slippage: 滑点
            tplus1: 是否启用 T+1 交易规则
            
        Returns:
            dict: 组合回测结果
        """
        if not self.strategies:
            raise ValueError("没有策略可运行")
        
        # 验证权重（仅提示警告，不阻止运行）
        self.validate_weights()
        
        self.logger.info(f"开始运行策略组合，共 {len(self.strategies)} 个策略")
        self.logger.info(f"初始资金：{self.initial_capital:.2f}")
        
        # 重置结果
        self.results = {}
        self.combined_daily_values = []
        self.combined_trades = []
        
        # 为每个策略创建独立的引擎并运行
        strategy_results = {}
        
        for name, config in self.strategies.items():
            if not config.enabled:
                self.logger.info(f"跳过禁用的策略：{name}")
                continue
            
            self.logger.info(f"\n运行策略：{name} (权重={config.weight:.2%})")
            
            # 创建独立的回测引擎
            from ..engine import BacktestConfig
            engine_config = BacktestConfig(
                initial_capital=config.capital_allocation,
                commission_rate=commission_rate,
                slippage=slippage,
                stamp_tax=tax_rate
            )
            engine = BacktestEngine(config=engine_config)
            
            # 运行策略
            result = engine.run(config.strategy, bars)
            
            # 记录结果
            strategy_result = StrategyResult(
                name=name,
                weight=config.weight,
                initial_capital=config.capital_allocation,
                final_capital=result.final_capital,
                return_rate=result.total_return,
                sharpe_ratio=result.sharpe_ratio,
                max_drawdown=result.max_drawdown,
                total_trades=result.total_trades,
                daily_values=engine.daily_values
            )
            
            strategy_results[name] = strategy_result
            self.results[name] = strategy_result
            
            # 累积每日资产值（用于计算组合净值曲线）
            if not self.combined_daily_values:
                self.combined_daily_values = [0.0] * len(engine.daily_values)
            
            for i, value in enumerate(engine.daily_values):
                self.combined_daily_values[i] += value
            
            # 累积交易记录
            self.combined_trades.extend(engine.trades)
            
            self.logger.info(
                f"策略 {name} 完成："
                f"收益={result.total_return:.2%}, "
                f"夏普={result.sharpe_ratio:.2f}, "
                f"最大回撤={result.max_drawdown:.2%}"
            )
        
        # 计算组合绩效
        portfolio_result = self._calculate_portfolio_performance(strategy_results)
        
        self.logger.info(f"\n组合回测完成")
        self.logger.info(f"组合总收益：{portfolio_result['total_return']:.2%}")
        self.logger.info(f"组合夏普比率：{portfolio_result['sharpe_ratio']:.2f}")
        self.logger.info(f"组合最大回撤：{portfolio_result['max_drawdown']:.2%}")
        
        return portfolio_result
    
    def _calculate_portfolio_performance(
        self,
        strategy_results: Dict[str, StrategyResult]
    ) -> Dict[str, Any]:
        """
        计算组合绩效
        
        Args:
            strategy_results: 各策略结果
            
        Returns:
            dict: 组合绩效指标
        """
        # 初始和最终资金
        total_initial = sum(r.initial_capital for r in strategy_results.values())
        total_final = sum(r.final_capital for r in strategy_results.values())
        
        # 组合收益率
        total_return = (total_final - total_initial) / total_initial
        
        # 组合夏普比率（加权平均）
        weighted_sharpe = sum(
            r.weight * r.sharpe_ratio 
            for r in strategy_results.values()
        )
        
        # 组合最大回撤（简化：取各策略最大回撤的加权平均）
        # 更精确的方法需要基于组合净值曲线计算
        weighted_max_dd = sum(
            r.weight * r.max_drawdown 
            for r in strategy_results.values()
        )
        
        # 总交易次数
        total_trades = sum(r.total_trades for r in strategy_results.values())
        
        # 计算组合日收益率序列（用于更精确的统计）
        if self.combined_daily_values:
            daily_returns = []
            for i in range(1, len(self.combined_daily_values)):
                prev_value = self.combined_daily_values[i-1]
                curr_value = self.combined_daily_values[i]
                if prev_value > 0:
                    daily_return = (curr_value - prev_value) / prev_value
                    daily_returns.append(daily_return)
            
            # 基于日收益率计算夏普比率
            if daily_returns:
                import statistics
                avg_daily_return = statistics.mean(daily_returns)
                std_daily_return = statistics.stdev(daily_returns) if len(daily_returns) > 1 else 1.0
                
                # 年化夏普比率（假设 252 个交易日）
                if std_daily_return > 0:
                    precise_sharpe = (avg_daily_return / std_daily_return) * (252 ** 0.5)
                else:
                    precise_sharpe = 0.0
                
                # 使用精确计算的夏普比率
                sharpe_ratio = precise_sharpe
            else:
                sharpe_ratio = weighted_sharpe
        else:
            sharpe_ratio = weighted_sharpe
        
        # 计算精确的最大回撤
        max_drawdown = self._calculate_combined_max_drawdown()
        
        return {
            'total_return': total_return,
            'total_initial_capital': total_initial,
            'total_final_capital': total_final,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'total_trades': total_trades,
            'num_strategies': len(strategy_results),
            'strategy_results': strategy_results,
            'daily_values': self.combined_daily_values,
        }
    
    def _calculate_combined_max_drawdown(self) -> float:
        """
        基于组合净值曲线计算最大回撤
        
        Returns:
            float: 最大回撤
        """
        if not self.combined_daily_values:
            return 0.0
        
        peak = self.combined_daily_values[0]
        max_dd = 0.0
        
        for value in self.combined_daily_values:
            if value > peak:
                peak = value
            
            drawdown = (peak - value) / peak if peak > 0 else 0
            max_dd = max(max_dd, drawdown)
        
        return max_dd
    
    def get_strategy_result(self, name: str) -> Optional[StrategyResult]:
        """获取单个策略的结果"""
        return self.results.get(name)
    
    def get_all_results(self) -> Dict[str, StrategyResult]:
        """获取所有策略的结果"""
        return self.results
    
    def print_summary(self) -> None:
        """打印组合摘要"""
        print("\n" + "="*60)
        print("策略组合回测摘要")
        print("="*60)
        
        print(f"\n初始资金：{self.initial_capital:,.2f}")
        print(f"策略数量：{len(self.strategies)}")
        
        print("\n各策略表现:")
        print("-"*60)
        print(f"{'策略名称':<20} {'权重':>8} {'收益':>10} {'夏普':>8} {'回撤':>10}")
        print("-"*60)
        
        for name, result in self.results.items():
            print(
                f"{name:<20} "
                f"{result.weight:>7.2%} "
                f"{result.return_rate:>9.2%} "
                f"{result.sharpe_ratio:>8.2f} "
                f"{result.max_drawdown:>9.2%}"
            )
        
        print("-"*60)
        
        # 组合汇总
        if self.combined_daily_values:
            initial = self.combined_daily_values[0]
            final = self.combined_daily_values[-1]
            total_return = (final - initial) / initial
            
            max_dd = self._calculate_combined_max_drawdown()
            
            print(f"\n组合汇总:")
            print(f"  最终资金：{final:,.2f}")
            print(f"  组合收益：{total_return:.2%}")
            print(f"  组合夏普：{self._calculate_portfolio_performance(self.results)['sharpe_ratio']:.2f}")
            print(f"  组合回撤：{max_dd:.2%}")
        
        print("="*60)

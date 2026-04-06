# -*- coding: utf-8 -*-
"""
多策略组合示例

展示如何使用 StrategyPortfolio 实现多策略组合投资：
1. 等权重组合
2. 自定义权重组合
3. 动态调整策略权重
"""

from datetime import datetime
import random
from quantcore.strategy.base import Strategy
from quantcore.strategy.portfolio import StrategyPortfolio
from quantcore.core import Bar
from quantcore.indicators import macd, rsi, bollinger_bands
from quantcore.logger import get_logger


class TrendFollowingStrategy(Strategy):
    """趋势跟踪策略"""
    
    def __init__(self, fast_period: int = 10, slow_period: int = 30):
        super().__init__()
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.position = 0
        self.prices = []
    
    def on_init(self, engine):
        super().on_init(engine)
        self.logger = get_logger("QuantCore.TrendStrategy")
    
    def on_bar(self, bar, engine):
        self.prices.append(bar.close)
        
        if len(self.prices) < self.slow_period:
            return
        
        # 计算快慢均线
        from quantcore.indicators import ma
        fast_ma_values = ma(self.prices, self.fast_period)
        slow_ma_values = ma(self.prices, self.slow_period)
        
        if not fast_ma_values or not slow_ma_values:
            return
        
        fast_ma = fast_ma_values[-1]
        slow_ma = slow_ma_values[-1]
        
        # 金叉买入，死叉卖出
        if fast_ma > slow_ma and self.position == 0:
            portfolio = engine.get_portfolio()
            volume = int(portfolio.cash * 0.95 / bar.close / 100) * 100
            if volume >= 100:
                self.buy(bar.symbol, bar.close, volume, order_type="market")
                self.position = volume
                self.logger.info(f"金叉买入：{volume}股 @ {bar.close:.2f}")
        
        elif fast_ma < slow_ma and self.position > 0:
            self.sell(bar.symbol, bar.close, self.position, order_type="market")
            self.logger.info(f"死叉卖出：{self.position}股 @ {bar.close:.2f}")
            self.position = 0


class MeanReversionStrategy(Strategy):
    """均值回归策略"""
    
    def __init__(self, period: int = 20, threshold: float = 2.0):
        super().__init__()
        self.period = period
        self.threshold = threshold
        self.position = 0
        self.prices = []
    
    def on_init(self, engine):
        super().on_init(engine)
        self.logger = get_logger("QuantCore.MeanReversionStrategy")
    
    def on_bar(self, bar, engine):
        self.prices.append(bar.close)
        
        if len(self.prices) < self.period:
            return
        
        # 计算布林带
        boll = bollinger_bands(self.prices, self.period, self.threshold)
        lower = boll['lower'][-1]
        upper = boll['upper'][-1]
        middle = boll['middle'][-1]
        
        # 触及下轨买入，回归中轨卖出
        if bar.close < lower and self.position == 0:
            portfolio = engine.get_portfolio()
            volume = int(portfolio.cash * 0.95 / bar.close / 100) * 100
            if volume >= 100:
                self.buy(bar.symbol, bar.close, volume, order_type="market")
                self.position = volume
                self.logger.info(f"触及下轨买入：{volume}股 @ {bar.close:.2f}")
        
        elif bar.close > middle and self.position > 0:
            self.sell(bar.symbol, bar.close, self.position, order_type="market")
            self.logger.info(f"回归中轨卖出：{self.position}股 @ {bar.close:.2f}")
            self.position = 0


class MomentumStrategy(Strategy):
    """动量策略"""
    
    def __init__(self, lookback: int = 10, threshold: float = 0.05):
        super().__init__()
        self.lookback = lookback
        self.threshold = threshold
        self.position = 0
        self.prices = []
    
    def on_init(self, engine):
        super().on_init(engine)
        self.logger = get_logger("QuantCore.MomentumStrategy")
    
    def on_bar(self, bar, engine):
        self.prices.append(bar.close)
        
        if len(self.prices) < self.lookback + 1:
            return
        
        # 计算动量
        momentum = (self.prices[-1] - self.prices[-self.lookback - 1]) / self.prices[-self.lookback - 1]
        
        # 正动量买入，负动量卖出
        if momentum > self.threshold and self.position == 0:
            portfolio = engine.get_portfolio()
            volume = int(portfolio.cash * 0.95 / bar.close / 100) * 100
            if volume >= 100:
                self.buy(bar.symbol, bar.close, volume, order_type="market")
                self.position = volume
                self.logger.info(f"正动量买入：{volume}股 @ {bar.close:.2f}, 动量={momentum:.2%}")
        
        elif momentum < -self.threshold and self.position > 0:
            self.sell(bar.symbol, bar.close, self.position, order_type="market")
            self.logger.info(f"负动量卖出：{self.position}股 @ {bar.close:.2f}, 动量={momentum:.2%}")
            self.position = 0


def generate_market_data(days: int = 252) -> list:
    """
    生成模拟市场数据
    
    Args:
        days: 交易日天数
        
    Returns:
        Bar 对象列表
    """
    from datetime import timedelta
    bars = []
    base_price = 100.0
    
    # 生成有趋势和波动的价格
    trend = 0.0002  # 每日平均涨幅
    volatility = 0.02  # 日波动率
    
    price = base_price
    start_date = datetime(2024, 1, 1)
    
    for i in range(days):
        # 随机游走 + 趋势
        daily_return = random.gauss(trend, volatility)
        price = price * (1 + daily_return)
        
        # 生成 OHLC
        open_price = price
        close_price = price * (1 + random.gauss(0, 0.01))
        high_price = max(open_price, close_price) * (1 + abs(random.gauss(0, 0.01)))
        low_price = min(open_price, close_price) * (1 - abs(random.gauss(0, 0.01)))
        
        # 生成日期（跳过周末）
        current_date = start_date + timedelta(days=i)
        
        bar = Bar(
            timestamp=current_date,
            symbol="SH.000001",
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            volume=int(1000000 * (1 + random.gauss(0, 0.2))),
            turnover=close_price * 1000000
        )
        bars.append(bar)
    
    return bars


def example_equal_weight_portfolio():
    """等权重组合示例"""
    print("\n" + "="*70)
    print("示例 1: 等权重三策略组合")
    print("="*70)
    
    # 创建组合
    portfolio = StrategyPortfolio(initial_capital=1000000)
    
    # 添加三个策略，每个权重 1/3
    portfolio.add_strategy("Trend", TrendFollowingStrategy(), weight=0.34)
    portfolio.add_strategy("MeanReversion", MeanReversionStrategy(), weight=0.33)
    portfolio.add_strategy("Momentum", MomentumStrategy(), weight=0.33)
    
    # 生成数据
    bars = generate_market_data(252)
    
    # 运行回测
    result = portfolio.run(
        bars,
        commission_rate=0.0003,
        tax_rate=0.001,
        slippage=0.002,
        tplus1=True
    )
    
    # 打印结果
    portfolio.print_summary()
    
    return result


def example_custom_weight_portfolio():
    """自定义权重组合示例"""
    print("\n" + "="*70)
    print("示例 2: 自定义权重组合（趋势为主）")
    print("="*70)
    
    # 创建组合
    portfolio = StrategyPortfolio(initial_capital=500000)
    
    # 趋势策略占 50%，均值回归 30%，动量 20%
    portfolio.add_strategy("Trend", TrendFollowingStrategy(fast_period=10, slow_period=30), weight=0.50)
    portfolio.add_strategy("MeanReversion", MeanReversionStrategy(period=20, threshold=2.0), weight=0.30)
    portfolio.add_strategy("Momentum", MomentumStrategy(lookback=10, threshold=0.05), weight=0.20)
    
    # 生成数据
    bars = generate_market_data(252)
    
    # 运行回测
    result = portfolio.run(bars, tplus1=True)
    
    # 打印结果
    portfolio.print_summary()
    
    return result


def example_strategy_rotation():
    """策略轮动示例"""
    print("\n" + "="*70)
    print("示例 3: 策略轮动（动态调整权重）")
    print("="*70)
    
    # 创建组合
    portfolio = StrategyPortfolio(initial_capital=1000000)
    
    # 初始配置：趋势策略 60%，均值回归 40%
    portfolio.add_strategy("Trend", TrendFollowingStrategy(), weight=0.6)
    portfolio.add_strategy("MeanReversion", MeanReversionStrategy(), weight=0.4)
    
    # 生成数据
    bars = generate_market_data(252)
    
    # 第一阶段：运行原始配置
    print("\n阶段 1: 趋势 60% + 均值回归 40%")
    bars_phase1 = bars[:126]  # 前半年
    result1 = portfolio.run(bars_phase1, tplus1=True)
    portfolio.print_summary()
    
    # 根据表现调整权重
    trend_result = portfolio.get_strategy_result("Trend")
    mean_rev_result = portfolio.get_strategy_result("MeanReversion")
    
    print(f"\n阶段 1 策略表现:")
    print(f"  Trend: 收益={trend_result.return_rate:.2%}")
    print(f"  MeanReversion: 收益={mean_rev_result.return_rate:.2%}")
    
    # 简单规则：表现好的策略增加权重
    if trend_result.return_rate > mean_rev_result.return_rate:
        print("\n调整权重：趋势 70% + 均值回归 30%")
        # 注意：实际使用中需要重新创建组合或修改权重配置
    else:
        print("\n调整权重：趋势 50% + 均值回归 50%")
    
    # 第二阶段：使用新权重（这里简化处理，实际应重新配置）
    print("\n阶段 2: 继续使用原有权重运行后半年数据")
    bars_phase2 = bars[126:]
    result2 = portfolio.run(bars_phase2, tplus1=True)
    portfolio.print_summary()


def main():
    """运行所有示例"""
    print("\n" + "="*70)
    print("QuantCore 多策略组合示例")
    print("="*70)
    
    # 示例 1: 等权重组合
    result1 = example_equal_weight_portfolio()
    
    # 示例 2: 自定义权重组合
    result2 = example_custom_weight_portfolio()
    
    # 示例 3: 策略轮动
    example_strategy_rotation()
    
    print("\n" + "="*70)
    print("所有示例运行完成！")
    print("="*70)


if __name__ == "__main__":
    main()

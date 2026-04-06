# -*- coding: utf-8 -*-
"""
可视化功能使用示例

展示如何使用 plotting 模块生成各种图表
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python-api'))

from datetime import datetime
import random
from quantcore.strategy.base import Strategy
from quantcore.strategy.portfolio import StrategyPortfolio
from quantcore.core import Bar
from quantcore.plotting import (
    plot_equity_curve,
    plot_drawdown_curve,
    plot_return_distribution,
    plot_monthly_returns,
    plot_strategy_comparison,
    plot_all_charts
)


class MACDStrategy(Strategy):
    """MACD 策略"""
    
    def __init__(self, fast=12, slow=26, signal=9):
        super().__init__()
        self.fast = fast
        self.slow = slow
        self.signal = signal
        self.position = 0
        self.prices = []
    
    def on_init(self, engine):
        super().on_init(engine)
        from quantcore.logger import get_logger
        self.logger = get_logger("QuantCore.MACDStrategy")
    
    def on_bar(self, bar, engine):
        self.prices.append(bar.close)
        
        if len(self.prices) < self.slow:
            return
        
        from quantcore.indicators import macd
        macd_result = macd(self.prices, self.fast, self.slow, self.signal)
        
        if not macd_result['macd']:
            return
        
        macd_value = macd_result['macd'][-1]
        
        if macd_value > 0 and self.position == 0:
            portfolio = engine.get_portfolio()
            volume = int(portfolio.cash * 0.95 / bar.close / 100) * 100
            if volume >= 100:
                self.buy(bar.symbol, bar.close, volume, order_type="market")
                self.position = volume
                self.logger.info(f"MACD 金叉买入：{volume}股 @ {bar.close:.2f}")
        
        elif macd_value < 0 and self.position > 0:
            self.sell(bar.symbol, bar.close, self.position, order_type="market")
            self.logger.info(f"MACD 死叉卖出：{self.position}股 @ {bar.close:.2f}")
            self.position = 0


class RSIStrategy(Strategy):
    """RSI 策略"""
    
    def __init__(self, period=14, oversold=30, overbought=70):
        super().__init__()
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.position = 0
        self.prices = []
    
    def on_init(self, engine):
        super().on_init(engine)
        from quantcore.logger import get_logger
        self.logger = get_logger("QuantCore.RSIStrategy")
    
    def on_bar(self, bar, engine):
        self.prices.append(bar.close)
        
        if len(self.prices) < self.period + 1:
            return
        
        from quantcore.indicators import rsi
        rsi_values = rsi(self.prices, self.period)
        
        if not rsi_values:
            return
        
        rsi_value = rsi_values[-1]
        
        if rsi_value < self.oversold and self.position == 0:
            portfolio = engine.get_portfolio()
            volume = int(portfolio.cash * 0.95 / bar.close / 100) * 100
            if volume >= 100:
                self.buy(bar.symbol, bar.close, volume, order_type="market")
                self.position = volume
                self.logger.info(f"RSI 超卖买入：{volume}股 @ {bar.close:.2f}")
        
        elif rsi_value > self.overbought and self.position > 0:
            self.sell(bar.symbol, bar.close, self.position, order_type="market")
            self.logger.info(f"RSI 超买卖出：{self.position}股 @ {bar.close:.2f}")
            self.position = 0


def generate_market_data(days: int = 252) -> list:
    """生成市场数据"""
    from datetime import timedelta
    
    bars = []
    base_price = 100.0
    trend = 0.0003
    volatility = 0.02
    
    price = base_price
    start_date = datetime(2024, 1, 1)
    
    for i in range(days):
        daily_return = random.gauss(trend, volatility)
        price = price * (1 + daily_return)
        
        open_price = price
        close_price = price * (1 + random.gauss(0, 0.01))
        high_price = max(open_price, close_price) * (1 + abs(random.gauss(0, 0.01)))
        low_price = min(open_price, close_price) * (1 - abs(random.gauss(0, 0.01)))
        
        bar = Bar(
            timestamp=start_date + timedelta(days=i),
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


def example_basic_plots():
    """基础图表示例"""
    print("\n" + "="*70)
    print("示例 1: 基础图表绘制")
    print("="*70)
    
    # 运行策略
    portfolio = StrategyPortfolio(initial_capital=1000000)
    portfolio.add_strategy("MACD", MACDStrategy(), weight=1.0)
    
    bars = generate_market_data(252)
    result = portfolio.run(bars, tplus1=True)
    
    daily_values = result['daily_values']
    initial_capital = result['total_initial_capital']
    
    # 创建输出目录
    output_dir = os.path.join(os.path.dirname(__file__), "visualization_output")
    os.makedirs(output_dir, exist_ok=True)
    
    print("\n生成基础图表...")
    
    # 1. 资金曲线图
    print("1. 绘制资金曲线图")
    plot_equity_curve(
        daily_values=daily_values,
        initial_capital=initial_capital,
        title="MACD 策略 - 资金曲线",
        save_path=os.path.join(output_dir, "equity_curve.png"),
        show=False
    )
    
    # 2. 回撤曲线图
    print("2. 绘制回撤曲线图")
    plot_drawdown_curve(
        daily_values=daily_values,
        title="MACD 策略 - 回撤分析",
        save_path=os.path.join(output_dir, "drawdown_curve.png"),
        show=False
    )
    
    # 3. 收益分布图
    print("3. 绘制收益分布图")
    plot_return_distribution(
        daily_values=daily_values,
        title="MACD 策略 - 收益分布",
        save_path=os.path.join(output_dir, "return_distribution.png"),
        show=False
    )
    
    # 4. 月度收益图
    print("4. 绘制月度收益图")
    plot_monthly_returns(
        daily_values=daily_values,
        initial_capital=initial_capital,
        title="MACD 策略 - 月度收益",
        save_path=os.path.join(output_dir, "monthly_returns.png"),
        show=False
    )
    
    print(f"\n所有图表已保存到：{output_dir}")


def example_strategy_comparison():
    """策略对比示例"""
    print("\n" + "="*70)
    print("示例 2: 多策略对比")
    print("="*70)
    
    # 运行多个策略
    strategies = {
        "MACD": MACDStrategy(),
        "RSI": RSIStrategy()
    }
    
    results_dict = {}
    
    for name, strategy in strategies.items():
        print(f"\n运行 {name} 策略...")
        portfolio = StrategyPortfolio(initial_capital=1000000)
        portfolio.add_strategy(name, strategy, weight=1.0)
        
        bars = generate_market_data(252)
        result = portfolio.run(bars, tplus1=True)
        
        results_dict[name] = {
            'daily_values': result['daily_values'],
            'return': result['total_return'],
            'sharpe': result['sharpe_ratio']
        }
        
        print(f"{name} 策略完成：收益={result['total_return']:.2%}, 夏普={result['sharpe_ratio']:.2f}")
    
    # 创建输出目录
    output_dir = os.path.join(os.path.dirname(__file__), "visualization_output")
    os.makedirs(output_dir, exist_ok=True)
    
    # 绘制策略对比图
    print("\n绘制策略对比图...")
    plot_strategy_comparison(
        results_dict=results_dict,
        title="MACD vs RSI 策略对比",
        save_path=os.path.join(output_dir, "strategy_comparison.png"),
        show=False
    )
    
    print(f"策略对比图已保存到：{output_dir}")


def example_comprehensive_analysis():
    """综合分析示例"""
    print("\n" + "="*70)
    print("示例 3: 综合绩效分析")
    print("="*70)
    
    # 运行多策略组合
    portfolio = StrategyPortfolio(initial_capital=1000000)
    portfolio.add_strategy("MACD", MACDStrategy(), weight=0.5)
    portfolio.add_strategy("RSI", RSIStrategy(), weight=0.5)
    
    bars = generate_market_data(252)
    result = portfolio.run(bars, tplus1=True)
    
    # 创建输出目录
    output_dir = os.path.join(os.path.dirname(__file__), "visualization_output", "comprehensive")
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成所有图表
    print("\n生成综合绩效分析图表...")
    plot_all_charts(
        result=result,
        title="多策略组合 - 综合绩效分析",
        save_dir=output_dir,
        show=False
    )
    
    print(f"\n所有图表已保存到：{output_dir}")
    
    # 打印绩效摘要
    print("\n" + "="*70)
    print("绩效摘要")
    print("="*70)
    print(f"初始资金：{result['total_initial_capital']:,.2f}")
    print(f"最终资金：{result['total_final_capital']:,.2f}")
    print(f"总收益：{result['total_return']:.2%}")
    print(f"夏普比率：{result['sharpe_ratio']:.2f}")
    print(f"最大回撤：{result['max_drawdown']:.2%}")
    print(f"交易次数：{result['total_trades']}")


def main():
    """运行所有示例"""
    print("\n" + "="*70)
    print("QuantCore 可视化功能示例")
    print("="*70)
    
    print("\n提示：需要安装 matplotlib 才能生成图表")
    print("安装命令：pip install matplotlib numpy scipy")
    
    try:
        # 示例 1: 基础图表
        example_basic_plots()
        
        # 示例 2: 策略对比
        example_strategy_comparison()
        
        # 示例 3: 综合分析
        example_comprehensive_analysis()
        
        print("\n" + "="*70)
        print("所有示例运行完成！")
        print("="*70)
        
    except Exception as e:
        print(f"\n[ERROR] 示例运行出错：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

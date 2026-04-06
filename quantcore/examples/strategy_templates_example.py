# -*- coding: utf-8 -*-
"""
策略模板库使用示例

展示如何使用 QuantCore 的经典策略模板
"""

from quantcore.strategy.templates import (
    # 趋势跟踪
    DualMovingAverageStrategy,
    MACDTrendStrategy,
    ADXTrendStrategy,
    
    # 均值回归
    RSIMeanReversionStrategy,
    BollingerMeanReversionStrategy,
    
    # 动量策略
    MomentumStrategy,
    
    # 突破策略
    DonchianBreakoutStrategy,
    SARBreakoutStrategy,
    
    # 多因子策略
    MultiFactorStrategy,
)
from quantcore.strategy.portfolio import StrategyPortfolio
from quantcore.plotting import plot_all_charts
from datetime import datetime
import random


def generate_test_data(days: int = 252) -> list:
    """生成测试数据"""
    from quantcore.core import Bar
    
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
            timestamp=start_date.replace(day=min(i % 28 + 1, 28)),
            symbol="SH.600000",
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            volume=int(1000000 * (1 + random.gauss(0, 0.2))),
            turnover=close_price * 1000000
        )
        bars.append(bar)
    
    return bars


def example_single_strategy():
    """示例 1：单个策略回测"""
    print("\n" + "="*70)
    print("示例 1：双均线策略回测")
    print("="*70)
    
    # 生成数据
    bars = generate_test_data(252)
    
    # 创建策略（使用默认参数）
    strategy = DualMovingAverageStrategy(fast_period=5, slow_period=20)
    
    # 运行回测
    portfolio = StrategyPortfolio(initial_capital=1000000)
    portfolio.add_strategy("DualMA", strategy, weight=1.0)
    
    result = portfolio.run(bars, tplus1=True)
    
    # 打印结果
    print(f"\n回测结果:")
    print(f"  初始资金：{result['total_initial_capital']:,.2f}")
    print(f"  最终资金：{result['total_final_capital']:,.2f}")
    print(f"  总收益：{result['total_return']:.2%}")
    print(f"  夏普比率：{result['sharpe_ratio']:.2f}")
    print(f"  最大回撤：{result['max_drawdown']:.2%}")
    
    # 可视化
    # plot_all_charts(result, title="双均线策略", show=False)
    
    return result


def example_strategy_comparison():
    """示例 2：多策略对比"""
    print("\n" + "="*70)
    print("示例 2：趋势策略对比")
    print("="*70)
    
    # 生成数据
    bars = generate_test_data(252)
    
    # 定义策略列表
    strategies = {
        "双均线": DualMovingAverageStrategy(fast_period=5, slow_period=20),
        "MACD": MACDTrendStrategy(fast_period=12, slow_period=26, signal_period=9),
        "ADX 趋势": ADXTrendStrategy(adx_period=14, adx_threshold=25),
    }
    
    # 运行每个策略
    results = {}
    for name, strategy in strategies.items():
        print(f"\n运行 {name} 策略...")
        portfolio = StrategyPortfolio(initial_capital=1000000)
        portfolio.add_strategy(name, strategy, weight=1.0)
        
        result = portfolio.run(bars, tplus1=True)
        results[name] = result
        
        print(f"  收益：{result['total_return']:.2%}")
        print(f"  夏普：{result['sharpe_ratio']:.2f}")
    
    # 找出最佳策略
    best_strategy = max(results.keys(), key=lambda k: results[k]['total_return'])
    print(f"\n最佳策略：{best_strategy} (收益：{results[best_strategy]['total_return']:.2%})")
    
    return results


def example_mean_reversion():
    """示例 3：均值回归策略组合"""
    print("\n" + "="*70)
    print("示例 3：均值回归策略组合")
    print("="*70)
    
    # 生成数据
    bars = generate_test_data(252)
    
    # 创建均值回归策略组合
    portfolio = StrategyPortfolio(initial_capital=1000000)
    portfolio.add_strategy("RSI", RSIMeanReversionStrategy(period=14, oversold=30, overbought=70), weight=0.5)
    portfolio.add_strategy("BOLL", BollingerMeanReversionStrategy(period=20, std_dev=2.0), weight=0.5)
    
    # 运行回测
    result = portfolio.run(bars, tplus1=True)
    
    print(f"\n组合回测结果:")
    print(f"  总收益：{result['total_return']:.2%}")
    print(f"  夏普比率：{result['sharpe_ratio']:.2f}")
    print(f"  最大回撤：{result['max_drawdown']:.2%}")
    
    return result


def example_momentum_breakout():
    """示例 4：动量 + 突破组合"""
    print("\n" + "="*70)
    print("示例 4：动量突破组合")
    print("="*70)
    
    # 生成数据
    bars = generate_test_data(252)
    
    # 创建组合
    portfolio = StrategyPortfolio(initial_capital=1000000)
    portfolio.add_strategy("动量", MomentumStrategy(period=12, threshold=0.05), weight=0.5)
    portfolio.add_strategy("突破", DonchianBreakoutStrategy(period=20), weight=0.5)
    
    # 运行回测
    result = portfolio.run(bars, tplus1=True)
    
    print(f"\n组合结果:")
    print(f"  总收益：{result['total_return']:.2%}")
    print(f"  夏普比率：{result['sharpe_ratio']:.2f}")
    
    return result


def example_multi_factor():
    """示例 5：多因子策略"""
    print("\n" + "="*70)
    print("示例 5：多因子策略")
    print("="*70)
    
    # 生成数据
    bars = generate_test_data(252)
    
    # 创建多因子策略
    strategy = MultiFactorStrategy(
        macd_periods=(12, 26, 9),
        roc_period=12,
        mfi_period=14
    )
    
    # 运行回测
    portfolio = StrategyPortfolio(initial_capital=1000000)
    portfolio.add_strategy("MultiFactor", strategy, weight=1.0)
    
    result = portfolio.run(bars, tplus1=True)
    
    print(f"\n多因子策略结果:")
    print(f"  总收益：{result['total_return']:.2%}")
    print(f"  夏普比率：{result['sharpe_ratio']:.2f}")
    print(f"  最大回撤：{result['max_drawdown']:.2%}")
    
    return result


def example_all_strategies():
    """示例 6：全部策略大比拼"""
    print("\n" + "="*70)
    print("示例 6：策略模板库大比拼")
    print("="*70)
    
    # 生成数据
    bars = generate_test_data(252)
    
    # 所有策略
    all_strategies = {
        "双均线": DualMovingAverageStrategy(),
        "MACD": MACDTrendStrategy(),
        "ADX 趋势": ADXTrendStrategy(),
        "RSI 回归": RSIMeanReversionStrategy(),
        "布林回归": BollingerMeanReversionStrategy(),
        "动量": MomentumStrategy(),
        "唐奇安突破": DonchianBreakoutStrategy(),
        "SAR 突破": SARBreakoutStrategy(),
        "多因子": MultiFactorStrategy(),
    }
    
    # 运行所有策略
    results = {}
    for name, strategy in all_strategies.items():
        print(f"\n运行 {name}...", end=" ")
        portfolio = StrategyPortfolio(initial_capital=1000000)
        portfolio.add_strategy(name, strategy, weight=1.0)
        
        result = portfolio.run(bars, tplus1=True)
        results[name] = result
        
        print(f"收益：{result['total_return']:.2%}, 夏普：{result['sharpe_ratio']:.2f}")
    
    # 排序
    sorted_results = sorted(results.items(), key=lambda x: x[1]['total_return'], reverse=True)
    
    print("\n" + "="*70)
    print("策略收益排名:")
    print("="*70)
    for rank, (name, result) in enumerate(sorted_results, 1):
        print(f"{rank:2d}. {name:12s} 收益：{result['total_return']:8.2%}  夏普：{result['sharpe_ratio']:6.2f}  回撤：{result['max_drawdown']:8.2%}")
    
    return results


def main():
    """运行所有示例"""
    print("\n" + "="*70)
    print("QuantCore 策略模板库使用示例")
    print("="*70)
    
    try:
        # 示例 1：单个策略
        example_single_strategy()
        
        # 示例 2：策略对比
        example_strategy_comparison()
        
        # 示例 3：均值回归
        example_mean_reversion()
        
        # 示例 4：动量突破
        example_momentum_breakout()
        
        # 示例 5：多因子
        example_multi_factor()
        
        # 示例 6：大比拼
        # example_all_strategies()  # 耗时较长，可选择运行
        
        print("\n" + "="*70)
        print("所有示例运行完成！")
        print("="*70)
        
    except Exception as e:
        print(f"\n[ERROR] 示例运行出错：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

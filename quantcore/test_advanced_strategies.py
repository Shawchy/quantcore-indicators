"""
高级策略测试

测试所有高级策略的表现
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python-api'))

from quantcore import BacktestEngine, BacktestConfig, StrategyRunner, PerformanceReport
from examples.advanced_strategies import (
    MACDStrategy,
    RSIStrategy,
    BOLLStrategy,
    MultiFactorStrategy,
    TrendFollowingStrategy,
    create_strategy,
)
from datetime import datetime, timedelta


def generate_test_data(days: int = 200):
    """生成测试数据"""
    from quantcore import Bar
    
    bars = []
    base_price = 10.0
    
    for i in range(days):
        # 生成带有趋势和波动的数据
        trend = 0.02 * (i // 30)  # 每月一个趋势
        noise = ((i % 7) - 3) * 0.05  # 周期性噪音
        wave = 0.5 * ((i % 20) - 10) / 10  # 更大周期的波动
        
        price = base_price + trend + noise + wave
        
        # 生成高低开收
        open_price = price
        close_price = price * (1 + ((i % 3) - 1) * 0.02)
        high_price = max(open_price, close_price) * 1.02
        low_price = min(open_price, close_price) * 0.98
        
        bar = Bar(
            timestamp=datetime(2024, 1, 1) + timedelta(days=i),
            symbol="SH.600000",
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            volume=1000000 + (i % 10) * 100000,
            turnover=price * (1000000 + (i % 10) * 100000)
        )
        bars.append(bar)
    
    return bars


def test_single_strategy(strategy_class, name: str, bars):
    """测试单个策略"""
    print(f"\n{'='*60}")
    print(f"测试策略：{name}")
    print(f"{'='*60}")
    
    try:
        # 创建策略
        strategy = strategy_class()
        
        # 配置回测
        config = BacktestConfig(
            initial_capital=1000000.0,
            commission_rate=0.0003,
            slippage=0.001,
        )
        
        # 创建引擎
        engine = BacktestEngine(config)
        
        # 运行回测
        runner = StrategyRunner(strategy)
        result = runner.run(engine, bars)
        
        # 输出结果
        print(f"\n回测结果:")
        print(f"  初始资金：{result.initial_capital:,.2f}")
        print(f"  最终资金：{result.final_capital:,.2f}")
        print(f"  总收益：{result.total_return*100:.2f}%")
        print(f"  交易次数：{result.total_trades}")
        
        # 绩效分析 - 暂时跳过，因为 Rust/Python Trade 对象转换问题
        # if result.daily_values and len(result.daily_values) > 0:
        #     from quantcore import PerformanceAnalyzer
        #     analyzer = PerformanceAnalyzer(
        #         result.trades,
        #         result.daily_values,
        #         result.initial_capital
        #     )
        #     print(f"\n绩效指标:")
        #     print(f"  年化收益：{analyzer.annual_return(250)*100:.2f}%")
        #     print(f"  波动率：{analyzer.volatility()*100:.2f}%")
        #     print(f"  夏普比率：{analyzer.sharpe_ratio(0.03):.2f}")
        #     print(f"  最大回撤：{analyzer.max_drawdown()*100:.2f}%")
        #     print(f"  胜率：{analyzer.win_rate()*100:.2f}%")
        
        return result
    except Exception as e:
        print(f"策略测试失败：{e}")
        import traceback
        traceback.print_exc()
        return None


def test_strategy_factory():
    """测试策略工厂"""
    print(f"\n{'='*60}")
    print("测试策略工厂")
    print(f"{'='*60}")
    
    # 测试创建不同策略
    strategies = ['macd', 'rsi', 'boll', 'multi_factor', 'trend_following']
    
    for name in strategies:
        strategy = create_strategy(name)
        print(f"[OK] 创建策略：{strategy.name}")
    
    # 测试带参数创建
    strategy = create_strategy('macd', fast_period=10, slow_period=20)
    print(f"[OK] 创建带参数的 MACD 策略：fast={strategy.fast_period}, slow={strategy.slow_period}")


def compare_strategies():
    """对比所有策略"""
    print(f"\n{'='*60}")
    print("策略对比")
    print(f"{'='*60}")
    
    # 生成数据
    bars = generate_test_data(200)
    
    # 策略列表
    strategy_classes = [
        ("MACD", MACDStrategy),
        ("RSI", RSIStrategy),
        ("BOLL", BOLLStrategy),
        ("Multi-Factor", MultiFactorStrategy),
        ("Trend Following", TrendFollowingStrategy),
    ]
    
    results = []
    
    for name, cls in strategy_classes:
        try:
            result = test_single_strategy(cls, name, bars)
            results.append((name, result))
        except Exception as e:
            print(f"✗ {name} 策略测试失败：{e}")
            results.append((name, None))
    
    # 汇总对比
    print(f"\n{'='*60}")
    print("策略表现汇总")
    print(f"{'='*60}")
    print(f"{'策略':<20} {'收益率':>12} {'交易次数':>10}")
    print(f"{'-'*60}")
    
    for name, result in results:
        if result:
            return_str = f"{result.total_return*100:.2f}%"
            trades = result.total_trades
            print(f"{name:<20} {return_str:>12} {trades:>10}")
        else:
            print(f"{name:<20} {'N/A':>12} {'N/A':>10}")
    
    print(f"{'-'*60}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("QuantCore 高级策略测试")
    print("="*60)
    
    # 测试策略工厂
    test_strategy_factory()
    
    # 对比所有策略
    compare_strategies()
    
    print("\n" + "="*60)
    print("所有测试完成！")
    print("="*60)

# -*- coding: utf-8 -*-
"""
测试策略框架
"""

from quantcore import quantcore_engine as qe
from quantcore.strategy import Strategy, StrategyRunner
from examples.strategies import BuyAndHoldStrategy, DualMAStrategy

print("=" * 70)
print("QuantCore 策略框架测试")
print("=" * 70)

# 1. 测试 Strategy 基类
print("\n1. 测试 Strategy 基类")
strategy = BuyAndHoldStrategy(symbol="SH.600000", volume=1000)
print(f"   策略已创建：{strategy.__class__.__name__}")

# 2. 创建测试数据
print("\n2. 创建测试 K 线数据")
bars = [
    qe.Bar("2024-01-01 10:00:00", "SH.600000", 10.0, 10.2, 9.8, 10.1, 1000000, 10100000.0),
    qe.Bar("2024-01-02 10:00:00", "SH.600000", 10.1, 10.5, 10.0, 10.4, 1200000, 12360000.0),
    qe.Bar("2024-01-03 10:00:00", "SH.600000", 10.4, 10.6, 10.2, 10.3, 1100000, 11440000.0),
    qe.Bar("2024-01-04 10:00:00", "SH.600000", 10.3, 10.7, 10.3, 10.6, 1300000, 13650000.0),
    qe.Bar("2024-01-05 10:00:00", "SH.600000", 10.6, 10.8, 10.5, 10.7, 1000000, 10650000.0),
]
print(f"   创建了 {len(bars)} 条 K 线数据")

# 3. 测试买入持有策略
print("\n3. 测试买入持有策略")
config = qe.BacktestConfig(initial_capital=1000000.0)
engine = qe.BacktestEngine(config)

# 创建策略运行器
runner = StrategyRunner(strategy)

# 运行回测
result = runner.run(engine, bars)

print(f"   回测结果：{result}")
print(f"   总收益：{result.total_return*100:.2f}%")
print(f"   交易次数：{result.total_trades}")
print(f"   最终资金：{result.final_capital:.2f}")

# 4. 测试双均线策略
print("\n4. 测试双均线策略（需要更多数据）")

# 生成更多测试数据（30 天）
import random
bars_30 = []
price = 10.0
for i in range(30):
    open_price = price
    close_price = price + random.uniform(-0.3, 0.3)
    high_price = max(open_price, close_price) + random.uniform(0, 0.2)
    low_price = min(open_price, close_price) - random.uniform(0, 0.2)
    volume = random.randint(800000, 1500000)
    
    bar = qe.Bar(
        f"2024-01-{i+1:02d} 10:00:00",
        "SH.600000",
        open_price,
        high_price,
        low_price,
        close_price,
        volume,
        close_price * volume
    )
    bars_30.append(bar)
    price = close_price

print(f"   创建了 {len(bars_30)} 条 K 线数据")

# 运行双均线策略
config2 = qe.BacktestConfig(initial_capital=1000000.0)
engine2 = qe.BacktestEngine(config2)

dual_ma_strategy = DualMAStrategy(fast_period=5, slow_period=10)
runner2 = StrategyRunner(dual_ma_strategy)

result2 = runner2.run(engine2, bars_30)

print(f"   回测结果：{result2}")
print(f"   总收益：{result2.total_return*100:.2f}%")
print(f"   交易次数：{result2.total_trades}")
print(f"   最终资金：{result2.final_capital:.2f}")

print("\n" + "=" * 70)
print("策略框架测试完成！")
print("=" * 70)
print("\n下一步：")
print("1. 实现数据加载器")
print("2. 实现绩效分析模块")
print("3. 实现技术指标库")
print("\n继续加油！")

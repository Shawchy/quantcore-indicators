# -*- coding: utf-8 -*-
"""
测试回测引擎
"""

from quantcore import quantcore_engine as qe

print("=" * 70)
print("QuantCore 回测引擎测试")
print("=" * 70)

# 1. 测试 BacktestConfig
print("\n1. 测试 BacktestConfig (回测配置)")
config = qe.BacktestConfig(
    initial_capital=1000000.0,
    commission_rate=0.0003,
    slippage=0.001,
    stamp_tax=0.001,
    min_commission=5.0
)
print(f"   配置：初始资金={config.initial_capital}, 佣金率={config.commission_rate}")

# 2. 测试 BacktestEngine
print("\n2. 测试 BacktestEngine (回测引擎)")
engine = qe.BacktestEngine(config)
print(f"   引擎已创建")

# 3. 创建测试数据
print("\n3. 创建测试 K 线数据")
bars = [
    qe.Bar("2024-01-01 10:00:00", "SH.600000", 10.0, 10.2, 9.8, 10.1, 1000000, 10100000.0),
    qe.Bar("2024-01-02 10:00:00", "SH.600000", 10.1, 10.5, 10.0, 10.4, 1200000, 12360000.0),
    qe.Bar("2024-01-03 10:00:00", "SH.600000", 10.4, 10.6, 10.2, 10.3, 1100000, 11440000.0),
    qe.Bar("2024-01-04 10:00:00", "SH.600000", 10.3, 10.7, 10.3, 10.6, 1300000, 13650000.0),
    qe.Bar("2024-01-05 10:00:00", "SH.600000", 10.6, 10.8, 10.5, 10.7, 1000000, 10650000.0),
]
print(f"   创建了 {len(bars)} 条 K 线数据")

# 4. 手动测试买卖
print("\n4. 测试买入操作")
order = engine.buy("SH.600000", 10.1, 1000)
print(f"   买入订单：{order}")

print("\n5. 处理订单")
engine.process_orders(bars[0])
print(f"   订单处理完成")

# 5. 查看结果
print("\n6. 查看投资组合")
portfolio = engine.get_portfolio()
print(f"   投资组合：{portfolio}")

print("\n7. 查看成交列表")
trades = engine.get_trades()
print(f"   成交数量：{len(trades)}")
for trade in trades:
    print(f"   {trade}")

# 6. 运行完整回测
print("\n8. 运行完整回测")
engine2 = qe.BacktestEngine(config)

# 简单策略：第一天买入，最后一天卖出
engine2.buy("SH.600000", bars[0].close, 1000)
result = engine2.run(bars)

print(f"   回测结果：{result}")
print(f"   总收益：{result.total_return*100:.2f}%")
print(f"   交易次数：{result.total_trades}")
print(f"   最终资金：{result.final_capital:.2f}")

print("\n" + "=" * 70)
print("回测引擎测试完成！")
print("=" * 70)
print("\n下一步：")
print("1. 实现 Strategy 基类")
print("2. 创建示例策略")
print("3. 运行真实策略回测")
print("\n继续加油！")

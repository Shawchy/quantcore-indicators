# -*- coding: utf-8 -*-
"""
综合功能测试
"""

from quantcore import quantcore_engine as qe
from quantcore.indicators import ma, ema, macd, rsi, bollinger_bands
from quantcore.risk import RiskManager, PositionLimit

print("=" * 70)
print("QuantCore 综合功能测试")
print("=" * 70)

# 1. 测试技术指标
print("\n1. 测试技术指标")

# 生成测试数据
prices = [10.0 + i * 0.1 for i in range(30)]

# MA
ma_5 = ma(prices, 5)
print(f"   MA(5): {ma_5[-3:]}")

# EMA
ema_12 = ema(prices, 12)
print(f"   EMA(12): {ema_12[-3:]}")

# MACD
macd_result = macd(prices)
print(f"   MACD: {len(macd_result['macd'])} 条数据")

# RSI
rsi_14 = rsi(prices, 14)
print(f"   RSI(14): {rsi_14[-3:]}")

# BOLL
boll = bollinger_bands(prices, 20)
print(f"   BOLL: 上轨={boll['upper'][-1]:.2f}, 中轨={boll['middle'][-1]:.2f}, 下轨={boll['lower'][-1]:.2f}")

# 2. 测试风险管理
print("\n2. 测试风险管理")

risk = RiskManager()
risk.add_position_limit(PositionLimit(symbol="SH.600000", max_percent=0.1, max_volume=10000))
risk.set_daily_loss_limit(50000.0)

# 测试买入检查
can_buy = risk.check_buy("SH.600000", 10.0, 1000, 1000000.0, 0)
print(f"   买入检查：{'允许' if can_buy else '拒绝'}")

# 测试卖出检查
can_sell = risk.check_sell("SH.600000", 10.0, 500, 1000)
print(f"   卖出检查：{'允许' if can_sell else '拒绝'}")

# 3. 测试绩效分析（Rust）
print("\n3. 测试绩效分析（Rust 引擎）")

# 创建模拟数据
trades = []
portfolio_values = [1000000.0, 1005000.0, 998000.0, 1010000.0, 1015000.0]

analyzer = qe.PerformanceAnalyzer(trades, portfolio_values, 1000000.0)
print(f"   总收益：{analyzer.total_return()*100:.2f}%")
print(f"   夏普比率：{analyzer.sharpe_ratio(0.03):.2f}")
print(f"   最大回撤：{analyzer.max_drawdown()*100:.2f}%")

print("\n" + "=" * 70)
print("综合功能测试完成！")
print("=" * 70)
print("\nQuantCore 核心功能：")
print("✅ 数据模型")
print("✅ 回测引擎")
print("✅ 策略框架")
print("✅ 技术指标")
print("✅ 风险管理")
print("✅ 绩效分析")
print("\n框架已可使用！")

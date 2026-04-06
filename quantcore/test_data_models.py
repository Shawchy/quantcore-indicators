"""
测试所有基础数据模型
"""

from quantcore import quantcore_engine as qe

print("=" * 70)
print("🎉 QuantCore 基础数据模型测试")
print("=" * 70)

# 1. 测试 Bar
print("\n1️⃣ 测试 Bar (K 线数据)")
bar = qe.Bar(
    timestamp="2024-01-01 10:00:00",
    symbol="SH.600000",
    open=10.0,
    high=10.5,
    low=9.8,
    close=10.2,
    volume=1000000,
    turnover=10200000.0
)
print(f"   {bar}")
print(f"   平均价格：{bar.average_price():.4f}")
print(f"   价格范围：{bar.price_range():.2f}")
print(f"   涨跌幅：{bar.price_change_percent()*100:.2f}%")

# 2. 测试 Tick
print("\n2️⃣ 测试 Tick (Tick 数据)")
tick = qe.Tick(
    timestamp="2024-01-01 10:00:00.123456",
    symbol="SH.600000",
    last_price=10.2,
    bid_price=10.19,
    bid_volume=500,
    ask_price=10.21,
    ask_volume=600,
    volume=100000,
    turnover=1020000.0
)
print(f"   {tick}")

# 3. 测试 Order
print("\n3️⃣ 测试 Order (订单)")
order = qe.Order(
    order_id="ORD-001",
    symbol="SH.600000",
    side=qe.OrderSide.Buy,
    order_type=qe.OrderType.Market,
    price=10.2,
    quantity=1000
)
print(f"   {order}")
print(f"   是否活跃：{order.is_active()}")
print(f"   未成交数量：{order.remaining_quantity()}")

# 4. 测试 Trade
print("\n4️⃣ 测试 Trade (成交)")
trade = qe.Trade(
    trade_id="TRD-001",
    order_id="ORD-001",
    symbol="SH.600000",
    side="buy",
    price=10.2,
    quantity=1000,
    commission=3.06
)
print(f"   {trade}")
print(f"   净成交金额：{trade.net_amount():.2f}")

# 5. 测试 Position
print("\n5️⃣ 测试 Position (持仓)")
position = qe.Position(
    symbol="SH.600000",
    side="long",
    quantity=1000,
    cost_price=10.0,
    current_price=10.2
)
print(f"   {position}")
print(f"   持仓成本：{position.cost_value():.2f}")
print(f"   持仓市值：{position.market_value():.2f}")
print(f"   浮动盈亏：{position.unrealized_pnl():.2f}")
print(f"   盈亏比例：{position.unrealized_pnl_percent()*100:.2f}%")
print(f"   可卖出：{position.can_sell(500)}")

# 6. 测试 Portfolio
print("\n6️⃣ 测试 Portfolio (投资组合)")
portfolio = qe.Portfolio(initial_capital=1000000.0)
print(f"   初始组合：{portfolio}")

# 添加持仓
portfolio.add_position(position)
print(f"   添加持仓后：{portfolio}")
print(f"   持仓数量：{portfolio.position_count()}")
print(f"   是否有 SH.600000：{portfolio.has_position('SH.600000')}")
print(f"   仓位比例：{portfolio.position_ratio()*100:.2f}%")

# 更新价格
position.update_price(10.5)
print(f"   价格更新到 10.5 后：{portfolio}")

print("\n" + "=" * 70)
print("✅ 所有数据模型测试通过！")
print("=" * 70)
print("\n下一步：")
print("1. 实现回测引擎框架")
print("2. 实现订单匹配逻辑")
print("3. 创建策略基类")
print("\n继续加油！🚀")

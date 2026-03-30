"""
检查 akshare 成交量数据的真实含义
对比多个数据源
"""
import akshare as ak
import efinance as ef

print("=" * 60)
print("对比多个数据源的上证指数成交量数据")
print("=" * 60)

# 方法 1: akshare
print("\n1. AkShare 数据:")
df = ak.stock_zh_index_daily(symbol="sh000001")
latest = df.iloc[-1]
print(f"   日期：{latest['date']}")
print(f"   收盘：{latest['close']:.2f}")
print(f"   成交量：{latest['volume']:,}")
print(f"   成交量 (亿): {latest['volume']/100000000:.2f}亿")

# 检查数据列的含义
print(f"\n   数据列说明:")
print(f"   - volume: {latest['volume']:,}")
print(f"   - 可能是成交金额 (元)? {latest['volume']/100000000:.2f}亿")
print(f"   - 可能是成交股数 (股)? {latest['volume']/100000000:.2f}亿股")

# 方法 2: 尝试从其他渠道获取
print("\n2. 尝试使用 efinance 获取:")
try:
    # efinance 获取指数数据
    df_ef = ef.index.get_daily_data('000001')
    if df_ef is not None and len(df_ef) > 0:
        latest_ef = df_ef.iloc[-1]
        print(f"   日期：{latest_ef.name}")
        print(f"   收盘：{latest_ef.get('收盘', 'N/A')}")
        print(f"   成交量：{latest_ef.get('成交量', 'N/A')}")
        print(f"   成交额：{latest_ef.get('成交额', 'N/A')}")
    else:
        print("   无数据")
except Exception as e:
    print(f"   失败：{e}")

# 方法 3: 检查历史数据趋势
print("\n3. 历史数据趋势分析 (最近 5 天):")
print("-" * 60)
for i in range(1, 6):
    row = df.iloc[-i]
    vol = row['volume']
    close = row['close']
    # 假设 volume 是成交金额 (元)
    vol_as_amount = vol / 100000000  # 亿
    # 假设 volume 是成交股数 (股)
    vol_as_shares = vol / 100000000  # 亿股
    estimated_amount_if_shares = vol * close / 100000000  # 亿
    
    print(f"{row['date']}:")
    print(f"   收盘={close:.2f}, volume={vol:,}")
    print(f"   如果 volume 是金额：{vol_as_amount:.2f}亿")
    print(f"   如果 volume 是股数：{vol_as_shares:.2f}亿股 → 成交额≈{estimated_amount_if_shares:.2f}亿")

print("\n" + "=" * 60)
print("分析结论:")
print("  - 上证指数日均成交额通常在 3000-5000 亿元")
print("  - 如果 volume 是成交金额，数值约为 5600-8000 亿，偏大但合理")
print("  - 如果 volume 是成交股数，计算出的成交额过大，不合理")
print("  - 推测：akshare 的 volume 字段可能是成交金额 (元) 而非成交量 (股)")
print("=" * 60)

"""
尝试使用 efinance 获取指数成交额数据
"""
import efinance as ef
import pandas as pd

print("=" * 70)
print("尝试使用 efinance 获取指数数据")
print("=" * 70)

# 尝试获取上证指数数据
try:
    print("\n1. 使用 efinance 获取指数 K 线数据:")
    # efinance 的指数代码格式
    # 上证指数：000001 或 sh000001
    df = ef.index.get_k_data('000001')
    
    if df is not None and len(df) > 0:
        print(f"  成功获取 {len(df)} 条数据")
        print(f"  列名：{df.columns.tolist()}")
        print(f"\n  最新数据:")
        latest = df.iloc[-1]
        print(f"    日期：{latest.name}")
        for col in df.columns:
            print(f"    {col}: {latest.get(col, 'N/A')}")
    else:
        print("  无数据")
        
except Exception as e:
    print(f"  失败：{e}")
    import traceback
    traceback.print_exc()

# 尝试获取市场总成交额
try:
    print("\n2. 尝试获取市场总成交额:")
    # 获取沪深两市总成交额
    df_market = ef.stock.get_market_activity()
    if df_market is not None:
        print(f"  获取到市场活跃度数据")
        print(df_market)
    else:
        print("  无数据")
except Exception as e:
    print(f"  失败：{e}")

# 尝试获取指数实时行情
try:
    print("\n3. 尝试获取指数实时行情:")
    quote = ef.index.get_realtime_quote('000001')
    if quote is not None:
        print(f"  上证指数实时行情:")
        for key, value in quote.items():
            print(f"    {key}: {value}")
    else:
        print("  无数据")
except Exception as e:
    print(f"  失败：{e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)

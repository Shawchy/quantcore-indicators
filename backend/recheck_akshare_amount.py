"""
重新检查 akshare 指数数据，寻找准确的成交额数据
"""
import akshare as ak
import pandas as pd

print("=" * 70)
print("重新检查 akshare 指数数据")
print("=" * 70)

# 获取上证指数数据
df = ak.stock_zh_index_daily(symbol="sh000001")

print(f"\n数据列：{df.columns.tolist()}")
print(f"\n数据示例 (最近 3 天):")
print(df.tail(3))

# 检查所有可能的成交额相关列
possible_amount_cols = ['amount', 'turnover', 'volume', '成交额', '成交量', '金额', '成交']
print(f"\n检查可能的成交额列:")
for col in df.columns:
    # 检查列名是否包含相关关键词
    for keyword in possible_amount_cols:
        if keyword.lower() in col.lower():
            print(f"  找到相关列：{col}")
            print(f"    最新值：{df[col].iloc[-1]:,}")
            print(f"    数据类型：{df[col].dtype}")

# 分析 volume 字段
print(f"\nVolume 字段分析:")
latest_volume = df['volume'].iloc[-1]
print(f"  volume 值：{latest_volume:,}")
print(f"  如果作为金额 (元): {latest_volume/100000000:.2f}亿")
print(f"  如果作为股数 (股): {latest_volume/100000000:.2f}亿股")

# 对比真实数据
print(f"\n真实数据对比 (2026 年 3 月 27 日):")
print(f"  沪市实际成交额：7,996.96 亿元")
print(f"  akshare volume: {latest_volume/100000000:.2f}亿")
print(f"  差距倍数：{7996.96 / (latest_volume/100000000):.2f}倍")

# 尝试其他 akshare 接口
print("\n" + "=" * 70)
print("尝试其他 akshare 接口")
print("=" * 70)

# 尝试获取 stock_zh_index_spot 实时行情
try:
    print("\n尝试 stock_zh_index_spot:")
    # 获取所有指数实时行情
    df_spot = ak.stock_zh_index_spot()
    if df_spot is not None and len(df_spot) > 0:
        print(f"  获取到 {len(df_spot)} 条数据")
        print(f"  列名：{df_spot.columns.tolist()}")
        
        # 查找上证指数
        sh_index = df_spot[df_spot['code'] == 'sh000001']
        if len(sh_index) > 0:
            print(f"\n  上证指数数据:")
            for col in sh_index.columns:
                print(f"    {col}: {sh_index.iloc[0].get(col, 'N/A')}")
        else:
            print("  未找到上证指数")
    else:
        print("  无数据")
except Exception as e:
    print(f"  失败：{e}")

print("\n" + "=" * 70)

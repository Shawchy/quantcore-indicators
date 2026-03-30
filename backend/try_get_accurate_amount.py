"""
使用 akshare 获取更准确的指数成交额数据
尝试不同的接口
"""
import akshare as ak
import pandas as pd

print("=" * 70)
print("尝试 akshare 的不同接口获取成交额")
print("=" * 70)

# 方法 1: stock_zh_index_daily 的 volume 字段乘以某个系数
print("\n方法 1: 分析 volume 字段与实际成交额的关系")
df = ak.stock_zh_index_daily(symbol="sh000001")
latest = df.iloc[-1]

# 实际沪市成交额：7996.96 亿元
actual_amount = 7996.96 * 100000000  # 转换为元
ak_volume = latest['volume']

print(f"  akshare volume: {ak_volume:,}")
print(f"  实际成交额：{actual_amount:,.2f} 元")
print(f"  比例系数：{actual_amount / ak_volume:.4f}")

# 测试其他日期
print(f"\n  历史数据验证:")
for i in range(1, 6):
    row = df.iloc[-i]
    vol = row['volume']
    # 假设比例系数约为 14.25
    estimated = vol * 14.25 / 100000000  # 亿
    print(f"  {row['date']}: volume={vol:,}, 估算={estimated:.2f}亿")

# 方法 2: 尝试获取指数成分股数据来计算总成交额
print("\n" + "=" * 70)
print("方法 2: 尝试获取指数成分股数据")
print("=" * 70)

try:
    # 获取上证 50 成分股
    print("\n获取上证 50 成分股:")
    df_constituents = ak.index_stock_cons(symbol="000016")
    if df_constituents is not None and len(df_constituents) > 0:
        print(f"  成分股数量：{len(df_constituents)}")
        print(f"  列名：{df_constituents.columns.tolist()}")
    else:
        print("  无数据")
except Exception as e:
    print(f"  失败：{e}")

# 方法 3: 使用 stock_board_industry_name_em 获取行业板块成交额
print("\n" + "=" * 70)
print("方法 3: 尝试东方财富行业板块数据")
print("=" * 70)

try:
    # 获取沪市 A 股列表
    print("\n获取沪市 A 股列表:")
    df_sh_stocks = ak.stock_sh_a_spot_em()
    if df_sh_stocks is not None and len(df_sh_stocks) > 0:
        print(f"  沪市股票数量：{len(df_sh_stocks)}")
        print(f"  列名：{df_sh_stocks.columns.tolist()}")
        
        # 计算总成交额
        if '成交额' in df_sh_stocks.columns:
            total_amount = df_sh_stocks['成交额'].sum()
            print(f"  沪市总成交额：{total_amount/100000000:.2f}亿")
        else:
            print("  未找到'成交额'列")
            # 尝试其他列名
            for col in df_sh_stocks.columns:
                if 'amount' in col.lower() or '成交' in col:
                    print(f"  找到相关列：{col}")
    else:
        print("  无数据")
except Exception as e:
    print(f"  失败：{e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)

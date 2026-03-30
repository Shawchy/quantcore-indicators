"""
测试 akshare 获取指数实时行情的正确方法
"""
import akshare as ak

# 方法 1: 使用 stock_zh_index_spot
try:
    print("方法 1: stock_zh_index_spot")
    df = ak.stock_zh_index_spot()
    print(f"成功获取到 {len(df)} 条数据")
    if len(df) > 0:
        sh_index = df[df['symbol'] == 'sh000001']
        if len(sh_index) > 0:
            print("\n上证指数:")
            print(sh_index)
        else:
            print("\n未找到上证指数数据")
            print(df.head())
except Exception as e:
    print(f"方法 1 失败：{e}")

print("\n" + "="*80 + "\n")

# 方法 2: 使用 stock_zh_index_daily
try:
    print("方法 2: stock_zh_index_daily")
    df = ak.stock_zh_index_daily(symbol="sh000001")
    print(f"成功获取到 {len(df)} 条数据")
    if len(df) > 0:
        print(df.tail())
except Exception as e:
    print(f"方法 2 失败：{e}")

"""
测试 akshare 获取指数实时行情
"""
import akshare as ak

# 测试上证指数
try:
    print("测试获取上证指数实时行情...")
    df = ak.index_zh_a_hist(symbol="000001", period="realtime")
    print(f"成功获取到 {len(df)} 条数据")
    if len(df) > 0:
        print(df.tail())
except Exception as e:
    print(f"失败：{e}")
    print("\n尝试使用其他方法...")
    
    # 尝试获取历史数据
    try:
        df = ak.index_zh_a_hist(symbol="000001")
        print(f"\n获取历史数据成功：{len(df)} 条")
        print(df.tail())
    except Exception as e2:
        print(f"历史数据也失败：{e2}")

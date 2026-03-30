"""
检查 akshare 指数数据中的涨跌信息
"""
import akshare as ak
import pandas as pd

try:
    print("获取上证指数历史数据...")
    df = ak.stock_zh_index_daily(symbol="sh000001")
    print(f"成功获取到 {len(df)} 条数据\n")
    
    if len(df) >= 2:
        # 获取最新两条数据
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        print("最新数据:")
        print(f"  日期：{latest['date']}")
        print(f"  收盘：{latest['close']}")
        print(f"  开盘：{latest['open']}")
        print(f"  最高：{latest['high']}")
        print(f"  最低：{latest['low']}")
        print(f"  成交量：{latest['volume']}")
        
        print("\n前一交易日数据:")
        print(f"  日期：{prev['date']}")
        print(f"  收盘：{prev['close']}")
        
        # 计算涨跌额和涨跌幅
        change = latest['close'] - prev['close']
        change_pct = (change / prev['close']) * 100
        
        print(f"\n计算结果:")
        print(f"  涨跌额：{change:.2f}")
        print(f"  涨跌幅：{change_pct:.2f}%")
        
except Exception as e:
    print(f"失败：{e}")
    import traceback
    traceback.print_exc()

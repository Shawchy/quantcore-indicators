"""
检查 akshare 指数数据中的成交额信息
"""
import akshare as ak
import pandas as pd

try:
    print("获取上证指数历史数据...")
    df = ak.stock_zh_index_daily(symbol="sh000001")
    
    if df is not None and len(df) > 0:
        print(f"成功获取到 {len(df)} 条数据")
        print("\n数据列：")
        print(df.columns.tolist())
        print("\n最新数据:")
        latest = df.iloc[-1]
        for col in df.columns:
            print(f"  {col}: {latest.get(col, 'N/A')}")
        
        # 检查是否有成交额相关的列
        amount_cols = [col for col in df.columns if 'amount' in str(col).lower() or '成交' in str(col)]
        if amount_cols:
            print(f"\n成交额相关列：{amount_cols}")
        else:
            print("\n未找到成交额相关列")
            
        # 检查所有列的数据类型和示例值
        print("\n所有列的示例值:")
        for col in df.columns:
            print(f"  {col}: {type(latest.get(col)).__name__} = {latest.get(col)}")
        
except Exception as e:
    print(f"失败：{e}")
    import traceback
    traceback.print_exc()

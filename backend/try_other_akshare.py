"""
尝试使用 akshare 其他接口获取指数成交额
"""
import akshare as ak

try:
    # 尝试 1: stock_zh_index_spot 实时行情
    print("尝试 1: stock_zh_index_spot 实时行情")
    print("=" * 60)
    try:
        df_spot = ak.stock_zh_index_spot()
        if df_spot is not None and len(df_spot) > 0:
            print(f"获取到 {len(df_spot)} 条实时行情")
            print("列名:", df_spot.columns.tolist())
            
            # 查找上证指数
            sh_index = df_spot[df_spot['code'] == 'sh000001']
            if len(sh_index) > 0:
                print("\n上证指数数据:")
                for col in sh_index.columns:
                    print(f"  {col}: {sh_index.iloc[0].get(col, 'N/A')}")
        else:
            print("  无数据")
    except Exception as e:
        print(f"  失败：{e}")
    
    print("\n")
    
    # 尝试 2: stock_zh_index_minute 分时数据
    print("尝试 2: stock_zh_index_minute 分时数据")
    print("=" * 60)
    try:
        df_minute = ak.stock_zh_index_minute(symbol="sh000001", period='1', adjust='')
        if df_minute is not None and len(df_minute) > 0:
            print(f"获取到 {len(df_minute)} 条分时数据")
            print("列名:", df_minute.columns.tolist())
            print("\n最新数据:")
            latest = df_minute.iloc[-1]
            for col in df_minute.columns:
                print(f"  {col}: {latest.get(col, 'N/A')}")
        else:
            print("  无数据")
    except Exception as e:
        print(f"  失败：{e}")
    
    print("\n")
    
    # 尝试 3: 使用 efinance 获取指数数据
    print("尝试 3: efinance 获取指数数据")
    print("=" * 60)
    try:
        import efinance as ef
        # 获取指数实时行情
        quote = ef.stock.get_realtime_info('000001')
        if quote is not None:
            print("上证指数数据:")
            print(f"  代码：{quote.get('code', 'N/A')}")
            print(f"  名称：{quote.get('name', 'N/A')}")
            print(f"  价格：{quote.get('price', 'N/A')}")
            print(f"  成交量：{quote.get('volume', 'N/A')}")
            print(f"  成交额：{quote.get('amount', 'N/A')}")
            print(f"  换手率：{quote.get('turnoverRate', 'N/A')}")
        else:
            print("  无数据")
    except Exception as e:
        print(f"  失败：{e}")
        
except Exception as e:
    print(f"程序错误：{e}")
    import traceback
    traceback.print_exc()

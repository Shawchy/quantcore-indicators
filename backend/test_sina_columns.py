"""
检查新浪接口返回的字段名
"""
import akshare as ak

if __name__ == '__main__':
    print("获取新浪 A 股实时行情...")
    df = ak.stock_zh_a_spot()
    
    print(f"\n数据形状：{df.shape}")
    print(f"\n列名:")
    for i, col in enumerate(df.columns):
        print(f"  {i+1}. {col}")
    
    print(f"\n前 3 行数据:")
    print(df.head(3))
    
    print(f"\n测试过滤股票 000001:")
    df_000001 = df[df['code'] == '000001']
    if len(df_000001) > 0:
        print(df_000001.iloc[0])
    else:
        print("未找到 000001")

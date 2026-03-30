"""
检查上证指数成交量的单位和合理性
"""
import asyncio
import sys
sys.path.insert(0, 'app')

from adapters.efinance_adapter import EFinanceAdapter

async def check_volume_unit():
    adapter = EFinanceAdapter()
    
    print("=" * 60)
    print("检查上证指数成交量单位和成交额计算")
    print("=" * 60)
    
    quote = await adapter.get_realtime_quote('000001')
    
    if quote:
        volume = quote['volume']
        price = quote['price']
        amount = quote['amount']
        
        print(f"\n上证指数数据:")
        print(f"  收盘价：{price:.2f} 点")
        print(f"  成交量：{volume:,} (当前单位)")
        print(f"  成交额：{amount:,.2f} 元")
        
        print(f"\n成交量单位分析:")
        print(f"  如果单位是手：{volume/100:.2f} 手")
        print(f"  如果单位是股：{volume/100000000:.2f} 亿股")
        
        print(f"\n成交额计算:")
        print(f"  当前计算：{volume:,} × {price:.2f} × 100 = {amount:,.2f} 元")
        print(f"  假设单位是股：{volume:,} × {price:.2f} = {volume * price:,.2f} 元")
        print(f"  假设单位是手：{volume:,} × {price:.2f} × 100 = {amount:,.2f} 元")
        
        # 合理性检查
        print(f"\n合理性检查:")
        print(f"  上证指数日均成交额通常在 3000-5000 亿左右")
        print(f"  当前计算值：{amount/100000000:.2f} 亿")
        print(f"  如果除以 100：{amount/100/100000000:.2f} 亿")
        
        # 检查 akshare 原始数据
        import akshare as ak
        df = ak.stock_zh_index_daily(symbol="sh000001")
        latest = df.iloc[-1]
        print(f"\nakshare 原始数据:")
        print(f"  volume: {latest['volume']:,}")
        print(f"  close: {latest['close']:.2f}")
        
        # 对比历史数据
        print(f"\n历史数据对比:")
        for i in range(1, 6):
            row = df.iloc[-i]
            vol = row['volume']
            close = row['close']
            estimated_amount = vol * close  # 假设单位是股
            print(f"  {row['date']}: 成交量={vol:,}, 收盘={close:.2f}, 估算成交额={estimated_amount/100000000:.2f}亿")
        
    print("\n" + "=" * 60)

if __name__ == '__main__':
    import asyncio
    asyncio.run(check_volume_unit())

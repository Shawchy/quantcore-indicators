"""
检查市场成交额数据
"""
import asyncio
import sys
sys.path.insert(0, 'app')

from adapters.efinance_adapter import EFinanceAdapter

async def check_market_amount():
    adapter = EFinanceAdapter()
    
    print("=" * 60)
    print("检查市场成交额数据")
    print("=" * 60)
    
    # 检查上证指数
    print("\n获取上证指数数据...")
    quote = await adapter.get_realtime_quote('000001')
    
    if quote:
        print(f"  代码：{quote['code']}")
        print(f"  名称：{quote['name']}")
        print(f"  当前点位：{quote['price']:.2f}")
        print(f"  成交量：{quote.get('volume', 'N/A')}")
        print(f"  成交额：{quote.get('amount', 'N/A')}")
        print(f"  成交量 (手): {quote.get('volume', 0):,}")
        print(f"  成交额 (元): {quote.get('amount', 0):,.2f}")
        
        # 检查数据合理性
        volume = quote.get('volume', 0)
        amount = quote.get('amount', 0)
        
        print(f"\n  数据检查:")
        print(f"    成交量是否合理：{'✅' if volume > 0 else '❌'} (值：{volume})")
        print(f"    成交额是否合理：{'✅' if amount > 0 else '❌'} (值：{amount})")
    else:
        print("  ❌ 获取数据失败")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    asyncio.run(check_market_amount())

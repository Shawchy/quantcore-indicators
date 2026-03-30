"""
测试所有指数的成交额数据
"""
import asyncio
import sys
sys.path.insert(0, 'app')

from adapters.efinance_adapter import EFinanceAdapter

async def test_indices_amount():
    adapter = EFinanceAdapter()
    
    indices = {
        '000001': '上证指数',
        '399001': '深证成指',
        '399006': '创业板指',
        '000016': '上证 50',
        '000300': '沪深 300',
    }
    
    print("=" * 70)
    print("测试所有指数的成交额数据")
    print("=" * 70)
    
    for code, name in indices.items():
        print(f"\n{name} ({code}):")
        quote = await adapter.get_realtime_quote(code)
        
        if quote:
            price = quote['price']
            volume = quote.get('volume', 0)
            amount = quote.get('amount', 0)
            
            print(f"  当前点位：{price:.2f}")
            print(f"  成交量：{volume:,} {'手' if volume > 0 else '(无数据)'}")
            print(f"  成交额：{amount:,.2f} 元 ({amount/100000000:.2f}亿)")
            
            # 检查数据合理性
            if amount > 0:
                print(f"  ✅ 成交额数据正常")
            else:
                print(f"  ❌ 成交额数据为 0")
        else:
            print(f"  ❌ 获取数据失败")
    
    print("\n" + "=" * 70)
    print("说明：")
    print("  - 指数数据通常只提供成交额，不提供成交量")
    print("  - 数据来源：AkShare (stock_zh_index_daily)")
    print("  - 成交额单位：元")
    print("=" * 70)

if __name__ == '__main__':
    asyncio.run(test_indices_amount())

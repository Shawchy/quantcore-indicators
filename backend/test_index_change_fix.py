"""
测试上证指数涨跌额和涨跌幅修复
"""
import asyncio
import sys
sys.path.insert(0, 'app')

from adapters.efinance_adapter import EFinanceAdapter

async def test_index_change():
    adapter = EFinanceAdapter()
    
    # 测试上证指数
    print("测试上证指数 (000001)...")
    quote = await adapter.get_realtime_quote('000001')
    
    if quote:
        print(f"  代码：{quote['code']}")
        print(f"  名称：{quote['name']}")
        print(f"  当前点位：{quote['price']:.2f}")
        print(f"  涨跌额：{quote['change']:+.2f}")
        print(f"  涨跌幅：{quote['change_pct']:+.2f}%")
        print(f"  开盘：{quote['open']:.2f}")
        print(f"  最高：{quote['high']:.2f}")
        print(f"  最低：{quote['low']:.2f}")
        print(f"  昨收：{quote.get('prev_close', 'N/A')}")
        
        # 验证数据是否合理
        if quote['change'] != 0.0 or quote['change_pct'] != 0.0:
            print("\n✅ 成功！涨跌额和涨跌幅已正确计算")
        else:
            print("\n❌ 失败！涨跌额和涨跌幅仍为 0")
    else:
        print("❌ 获取数据失败")
    
    print("\n" + "="*50)
    
    # 测试深证成指
    print("测试深证成指 (399001)...")
    quote = await adapter.get_realtime_quote('399001')
    
    if quote:
        print(f"  代码：{quote['code']}")
        print(f"  名称：{quote['name']}")
        print(f"  当前点位：{quote['price']:.2f}")
        print(f"  涨跌额：{quote['change']:+.2f}")
        print(f"  涨跌幅：{quote['change_pct']:+.2f}%")
        
        if quote['change'] != 0.0 or quote['change_pct'] != 0.0:
            print("\n✅ 成功！涨跌额和涨跌幅已正确计算")
        else:
            print("\n⚠️  注意：涨跌数据为 0，可能是数据源问题")
    else:
        print("❌ 获取数据失败")

if __name__ == '__main__':
    asyncio.run(test_index_change())

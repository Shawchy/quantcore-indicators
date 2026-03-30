"""
测试所有指数名称是否正确显示
"""
import asyncio
import sys
sys.path.insert(0, 'app')

from adapters.efinance_adapter import EFinanceAdapter

async def test_all_indices():
    adapter = EFinanceAdapter()
    
    # 所有指数代码和期望的中文名称
    indices = {
        '000001': '上证指数',
        '399001': '深证成指',
        '399006': '创业板指',
        '000016': '上证 50',
        '000300': '沪深 300',
    }
    
    print("=" * 60)
    print("测试所有指数名称显示")
    print("=" * 60)
    
    all_passed = True
    
    for code, expected_name in indices.items():
        print(f"\n测试 {code}...")
        quote = await adapter.get_realtime_quote(code)
        
        if quote:
            actual_name = quote['name']
            status = "✅" if actual_name == expected_name else "❌"
            
            print(f"  代码：{code}")
            print(f"  期望名称：{expected_name}")
            print(f"  实际名称：{actual_name} {status}")
            print(f"  当前点位：{quote['price']:.2f}")
            print(f"  涨跌额：{quote['change']:+.2f}")
            print(f"  涨跌幅：{quote['change_pct']:+.2f}%")
            
            if actual_name != expected_name:
                all_passed = False
        else:
            print(f"  ❌ 获取数据失败")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有指数名称显示正确！")
    else:
        print("❌ 部分指数名称显示不正确")
    print("=" * 60)

if __name__ == '__main__':
    asyncio.run(test_all_indices())

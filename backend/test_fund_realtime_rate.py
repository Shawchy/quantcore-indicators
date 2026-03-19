"""
基金实时估算涨跌幅 API 测试脚本

测试 efinance.fund.get_realtime_increase_rate 接口
"""
import asyncio
import sys
sys.path.insert(0, 'd:/PROJ/Quant/backend')

from app.adapters.efinance_adapter import EFinanceAdapter


async def test_single_fund():
    """测试单只基金查询"""
    print("=" * 60)
    print("测试 1: 单只基金实时估算涨跌幅")
    print("=" * 60)
    
    adapter = EFinanceAdapter()
    await adapter.initialize()
    
    try:
        # 测试单只基金
        result = await adapter.get_fund_realtime_increase_rate('161725')
        
        if result:
            print(f"✅ 获取成功")
            print(f"   基金代码：{result['code']}")
            print(f"   基金名称：{result['name']}")
            print(f"   最新净值：{result.get('net_value', 'N/A')}")
            print(f"   净值日期：{result.get('nav_date', 'N/A')}")
            print(f"   估算时间：{result.get('estimate_time', 'N/A')}")
            print(f"   估算涨跌幅：{result.get('estimate_change_pct', 'N/A')}%")
        else:
            print("❌ 获取失败：返回空值")
    
    except Exception as e:
        print(f"❌ 测试失败：{e}")
    
    await adapter.close()


async def test_multi_funds():
    """测试多只基金批量查询"""
    print("\n" + "=" * 60)
    print("测试 2: 多只基金实时估算涨跌幅（批量查询）")
    print("=" * 60)
    
    adapter = EFinanceAdapter()
    await adapter.initialize()
    
    try:
        # 测试多只基金
        result = await adapter.get_fund_realtime_increase_rate(['161725', '005827', '005918'])
        
        if result and isinstance(result, list):
            print(f"✅ 获取成功，共{len(result)}只基金")
            print()
            for fund in result:
                print(f"   基金代码：{fund['code']}")
                print(f"   基金名称：{fund['name']}")
                print(f"   最新净值：{fund.get('net_value', 'N/A')}")
                print(f"   净值日期：{fund.get('nav_date', 'N/A')}")
                print(f"   估算时间：{fund.get('estimate_time', 'N/A')}")
                print(f"   估算涨跌幅：{fund.get('estimate_change_pct', 'N/A')}%")
                print("-" * 60)
        else:
            print("❌ 获取失败：返回空值或非列表")
    
    except Exception as e:
        print(f"❌ 测试失败：{e}")
    
    await adapter.close()


async def test_cache():
    """测试缓存机制"""
    print("\n" + "=" * 60)
    print("测试 3: 缓存机制测试")
    print("=" * 60)
    
    adapter = EFinanceAdapter()
    await adapter.initialize()
    
    try:
        # 第一次查询（应该从 API 获取）
        print("第一次查询（从 API 获取）...")
        result1 = await adapter.get_fund_realtime_increase_rate('161725')
        
        # 第二次查询（应该从缓存获取）
        print("第二次查询（从缓存获取）...")
        result2 = await adapter.get_fund_realtime_increase_rate('161725')
        
        if result1 and result2:
            print(f"✅ 缓存测试成功")
            print(f"   两次查询结果一致：{result1 == result2}")
            print(f"   估算涨跌幅：{result1.get('estimate_change_pct', 'N/A')}%")
        else:
            print("❌ 缓存测试失败")
    
    except Exception as e:
        print(f"❌ 测试失败：{e}")
    
    await adapter.close()


async def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("基金实时估算涨跌幅 API 测试")
    print("=" * 60)
    print()
    
    # 测试 1: 单只基金
    await test_single_fund()
    
    # 测试 2: 多只基金
    await test_multi_funds()
    
    # 测试 3: 缓存机制
    await test_cache()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

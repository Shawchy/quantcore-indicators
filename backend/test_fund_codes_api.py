"""
测试基金代码列表 API 功能
"""
import asyncio
import sys
sys.path.insert(0, 'd:/PROJ/Quant/backend')

from app.adapters.efinance_adapter import EFinanceAdapter


async def test_fund_codes_api():
    """测试基金代码列表 API"""
    print("=" * 60)
    print("测试基金代码列表 API 功能")
    print("=" * 60)
    
    # 初始化适配器
    adapter = EFinanceAdapter()
    await adapter.initialize()
    
    # 测试 1: 获取全部类型基金
    print("\n[测试 1] 获取全部类型的基金代码")
    try:
        funds = await adapter.get_fund_codes()
        if funds:
            print(f"✅ 成功获取 {len(funds)} 只基金")
            print(f"   前 10 只基金：")
            for i, fund in enumerate(funds[:10]):
                print(f"   {i+1}. {fund['code']} - {fund['name']}")
        else:
            print("❌ 获取失败")
    except Exception as e:
        print(f"❌ 异常：{e}")
    
    # 测试 2: 获取股票型基金
    print("\n[测试 2] 获取股票型基金代码（gp）")
    try:
        funds = await adapter.get_fund_codes('gp')
        if funds:
            print(f"✅ 成功获取 {len(funds)} 只股票型基金")
            print(f"   前 10 只：")
            for i, fund in enumerate(funds[:10]):
                print(f"   {i+1}. {fund['code']} - {fund['name']}")
        else:
            print("❌ 获取失败")
    except Exception as e:
        print(f"❌ 异常：{e}")
    
    # 测试 3: 获取 ETF 基金
    print("\n[测试 3] 获取 ETF 基金代码（etf）")
    try:
        funds = await adapter.get_fund_codes('etf')
        if funds:
            print(f"✅ 成功获取 {len(funds)} 只 ETF 基金")
            print(f"   前 10 只：")
            for i, fund in enumerate(funds[:10]):
                print(f"   {i+1}. {fund['code']} - {fund['name']}")
        else:
            print("❌ 获取失败")
    except Exception as e:
        print(f"❌ 异常：{e}")
    
    # 测试 4: 获取债券型基金
    print("\n[测试 4] 获取债券型基金代码（zq）")
    try:
        funds = await adapter.get_fund_codes('zq')
        if funds:
            print(f"✅ 成功获取 {len(funds)} 只债券型基金")
            print(f"   前 5 只：")
            for i, fund in enumerate(funds[:5]):
                print(f"   {i+1}. {fund['code']} - {fund['name']}")
        else:
            print("❌ 获取失败")
    except Exception as e:
        print(f"❌ 异常：{e}")
    
    # 测试 5: 获取混合型基金
    print("\n[测试 5] 获取混合型基金代码（hh）")
    try:
        funds = await adapter.get_fund_codes('hh')
        if funds:
            print(f"✅ 成功获取 {len(funds)} 只混合型基金")
            print(f"   前 5 只：")
            for i, fund in enumerate(funds[:5]):
                print(f"   {i+1}. {fund['code']} - {fund['name']}")
        else:
            print("❌ 获取失败")
    except Exception as e:
        print(f"❌ 异常：{e}")
    
    # 测试 6: 获取指数型基金
    print("\n[测试 6] 获取指数型基金代码（zs）")
    try:
        funds = await adapter.get_fund_codes('zs')
        if funds:
            print(f"✅ 成功获取 {len(funds)} 只指数型基金")
            print(f"   前 5 只：")
            for i, fund in enumerate(funds[:5]):
                print(f"   {i+1}. {fund['code']} - {fund['name']}")
        else:
            print("❌ 获取失败")
    except Exception as e:
        print(f"❌ 异常：{e}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_fund_codes_api())

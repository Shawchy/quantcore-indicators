"""
测试基金 API 功能
"""
import asyncio
import sys
sys.path.insert(0, 'd:/PROJ/Quant/backend')

from app.adapters.efinance_adapter import EFinanceAdapter


async def test_fund_api():
    """测试基金 API"""
    print("=" * 60)
    print("测试基金 API 功能")
    print("=" * 60)
    
    # 初始化适配器
    adapter = EFinanceAdapter()
    await adapter.initialize()
    
    # 测试 1: 获取单只基金信息
    print("\n[测试 1] 获取单只基金基本信息（161725 - 招商中证白酒指数）")
    try:
        fund_info = await adapter.get_fund_base_info('161725')
        if fund_info:
            print(f"✅ 成功获取基金信息：")
            print(f"   基金代码：{fund_info.get('code')}")
            print(f"   基金简称：{fund_info.get('name')}")
            print(f"   成立日期：{fund_info.get('establish_date')}")
            print(f"   涨跌幅：{fund_info.get('change_pct')}%")
            print(f"   最新净值：{fund_info.get('net_asset_value')}")
            print(f"   基金公司：{fund_info.get('fund_company')}")
            print(f"   净值更新日期：{fund_info.get('nav_update_date')}")
            desc = fund_info.get('description', '')
            if desc and len(str(desc)) > 50:
                desc = str(desc)[:50] + '...'
            print(f"   简介：{desc}")
        else:
            print("❌ 获取失败")
    except Exception as e:
        print(f"❌ 异常：{e}")
    
    # 测试 2: 获取多只基金信息
    print("\n[测试 2] 获取多只基金基本信息（161725, 005827）")
    try:
        fund_list = await adapter.get_fund_base_info(['161725', '005827'])
        if fund_list and len(fund_list) > 0:
            print(f"✅ 成功获取 {len(fund_list)} 只基金信息：")
            for i, fund in enumerate(fund_list):
                print(f"   {i+1}. {fund.get('name')} ({fund.get('code')})")
                print(f"      涨跌幅：{fund.get('change_pct')}%，净值：{fund.get('net_asset_value')}")
                print(f"      基金公司：{fund.get('fund_company')}")
        else:
            print("❌ 获取失败")
    except Exception as e:
        print(f"❌ 异常：{e}")
    
    # 测试 3: 获取不存在的基金
    print("\n[测试 3] 获取不存在的基金（999999）")
    try:
        fund_info = await adapter.get_fund_base_info('999999')
        if fund_info:
            print(f"✅ 获取到基金：{fund_info.get('name')}")
        else:
            print("✅ 正确返回 None（预期行为）")
    except Exception as e:
        print(f"❌ 异常：{e}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_fund_api())

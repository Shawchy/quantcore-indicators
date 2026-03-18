"""
测试基金持仓 API 功能
"""
import asyncio
import sys
sys.path.insert(0, 'd:/PROJ/Quant/backend')

from app.adapters.efinance_adapter import EFinanceAdapter


async def test_fund_position_api():
    """测试基金持仓 API"""
    print("=" * 60)
    print("测试基金持仓 API 功能")
    print("=" * 60)
    
    # 初始化适配器
    adapter = EFinanceAdapter()
    await adapter.initialize()
    
    # 测试 1: 获取最新公开的持仓数据
    print("\n[测试 1] 获取最新公开的持仓数据（161725 - 招商中证白酒指数）")
    try:
        positions = await adapter.get_fund_invest_position('161725')
        if positions:
            print(f"✅ 成功获取 {len(positions)} 条持仓数据")
            print(f"   前 5 大重仓股：")
            for i, pos in enumerate(positions[:5]):
                print(f"   {i+1}. {pos['stock_code']} - {pos['stock_name']}")
                print(f"      持仓占比：{pos['position_ratio']}%")
                print(f"      较上期变化：{pos['change']:+.2f}%")
                print(f"      公开日期：{pos['report_date']}")
        else:
            print("❌ 获取失败")
    except Exception as e:
        print(f"❌ 异常：{e}")
    
    # 测试 2: 获取单个日期的持仓数据
    print("\n[测试 2] 获取单个日期的持仓数据（2021-12-31）")
    try:
        positions = await adapter.get_fund_invest_position('161725', '2021-12-31')
        if positions:
            print(f"✅ 成功获取 {len(positions)} 条持仓数据")
            print(f"   前 3 大重仓股：")
            for i, pos in enumerate(positions[:3]):
                print(f"   {i+1}. {pos['stock_name']} - {pos['position_ratio']}%")
        else:
            print("❌ 获取失败")
    except Exception as e:
        print(f"❌ 异常：{e}")
    
    # 测试 3: 获取多个日期的持仓数据
    print("\n[测试 3] 获取多个日期的持仓数据（2021-12-31 和 2021-09-30）")
    try:
        positions = await adapter.get_fund_invest_position(
            '161725',
            ['2021-12-31', '2021-09-30']
        )
        if positions:
            print(f"✅ 成功获取 {len(positions)} 条持仓数据（包含两个日期）")
            # 按日期分组统计
            dates = set(pos['report_date'] for pos in positions)
            print(f"   包含日期：{len(dates)} 个")
            for date in sorted(dates, reverse=True):
                count = sum(1 for pos in positions if pos['report_date'] == date)
                print(f"   - {date}: {count} 条")
        else:
            print("❌ 获取失败")
    except Exception as e:
        print(f"❌ 异常：{e}")
    
    # 测试 4: 获取另一只基金的持仓
    print("\n[测试 4] 获取另一只基金的持仓（005827 - 易方达蓝筹精选混合）")
    try:
        positions = await adapter.get_fund_invest_position('005827')
        if positions:
            print(f"✅ 成功获取 {len(positions)} 条持仓数据")
            print(f"   前 5 大重仓股：")
            for i, pos in enumerate(positions[:5]):
                print(f"   {i+1}. {pos['stock_code']} - {pos['stock_name']}")
                print(f"      持仓占比：{pos['position_ratio']}%")
                print(f"      较上期变化：{pos['change']:+.2f}%")
        else:
            print("❌ 获取失败")
    except Exception as e:
        print(f"❌ 异常：{e}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_fund_position_api())

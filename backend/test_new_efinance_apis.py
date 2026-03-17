"""测试 efinance 新增 API"""
import asyncio
from app.adapters.efinance_adapter import EFinanceAdapter

async def test_billboard():
    """测试龙虎榜 API"""
    print("\n=== 测试龙虎榜 API ===")
    adapter = EFinanceAdapter()
    await adapter.initialize()
    
    try:
        data = await adapter.get_daily_billboard()
        print(f"获取龙虎榜数据：{len(data)} 条")
        if data:
            print(f"示例数据：{data[0]}")
    except Exception as e:
        print(f"龙虎榜 API 测试失败：{e}")
    
    await adapter.close()

async def test_belong_board():
    """测试股票所属板块 API"""
    print("\n=== 测试股票所属板块 API ===")
    adapter = EFinanceAdapter()
    await adapter.initialize()
    
    try:
        boards = await adapter.get_belong_board('600000')
        print(f"获取浦发银行所属板块：{len(boards)} 个")
        for board in boards:
            print(f"  - {board.name} ({board.board_type})")
    except Exception as e:
        print(f"所属板块 API 测试失败：{e}")
    
    await adapter.close()

async def test_capital_flow():
    """测试资金流向 API"""
    print("\n=== 测试资金流向 API ===")
    adapter = EFinanceAdapter()
    await adapter.initialize()
    
    try:
        flows = await adapter.get_history_bill('600000')
        print(f"获取浦发银行历史资金流向：{len(flows)} 条")
        if flows:
            print(f"示例数据：日期={flows[0].trade_date}, 主力净流入={flows[0].main_net_amount}")
    except Exception as e:
        print(f"资金流向 API 测试失败：{e}")
    
    await adapter.close()

async def test_shareholders():
    """测试股东信息 API"""
    print("\n=== 测试股东信息 API ===")
    adapter = EFinanceAdapter()
    await adapter.initialize()
    
    try:
        shareholders = await adapter.get_top10_stock_holder_info('600000')
        print(f"获取浦发银行前十大股东：{len(shareholders)} 条")
        for sh in shareholders[:3]:
            print(f"  - {sh.shareholder_name}: 持股 {sh.hold_amount}股 ({sh.hold_ratio}%)")
    except Exception as e:
        print(f"股东信息 API 测试失败：{e}")
    
    await adapter.close()

async def main():
    print("开始测试 efinance 新增 API...")
    await test_billboard()
    await test_belong_board()
    await test_capital_flow()
    await test_shareholders()
    print("\n测试完成！")

if __name__ == '__main__':
    asyncio.run(main())

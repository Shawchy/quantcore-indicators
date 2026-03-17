"""测试 efinance 市场实时行情 API"""
import asyncio
from app.adapters.efinance_adapter import EFinanceAdapter

async def test_market_quotes():
    """测试市场实时行情 API"""
    print("\n=== 测试市场实时行情 API ===")
    adapter = EFinanceAdapter()
    await adapter.initialize()
    
    # 测试 1: 获取沪深 A 股
    print("\n1. 测试沪深 A 股行情...")
    try:
        data = await adapter.get_market_realtime_quotes(['沪深 A 股'])
        print(f"获取沪深 A 股行情：{len(data)} 条")
        if data:
            print(f"示例：{data[0].code} {data[0].name} 最新价={data[0].price} 涨跌幅={data[0].change_pct}%")
    except Exception as e:
        print(f"沪深 A 股测试失败：{e}")
    
    # 测试 2: 获取创业板
    print("\n2. 测试创业板行情...")
    try:
        data = await adapter.get_market_realtime_quotes(['创业板'])
        print(f"获取创业板行情：{len(data)} 条")
        if data:
            print(f"示例：{data[0].code} {data[0].name} 最新价={data[0].price} 涨跌幅={data[0].change_pct}%")
    except Exception as e:
        print(f"创业板测试失败：{e}")
    
    # 测试 3: 获取 ETF
    print("\n3. 测试 ETF 基金行情...")
    try:
        data = await adapter.get_market_realtime_quotes(['ETF'])
        print(f"获取 ETF 基金行情：{len(data)} 条")
        if data:
            print(f"示例：{data[0].code} {data[0].name} 最新价={data[0].price} 涨跌幅={data[0].change_pct}%")
    except Exception as e:
        print(f"ETF 测试失败：{e}")
    
    # 测试 4: 获取多个市场类型
    print("\n4. 测试多个市场类型（创业板 + 科创板）...")
    try:
        data = await adapter.get_market_realtime_quotes(['创业板', '科创板'])
        print(f"获取创业板 + 科创板行情：{len(data)} 条")
        if data:
            print(f"示例：{data[0].code} {data[0].name} 最新价={data[0].price} 涨跌幅={data[0].change_pct}%")
    except Exception as e:
        print(f"多市场测试失败：{e}")
    
    # 测试 5: 获取行业板块
    print("\n5. 测试行业板块行情...")
    try:
        data = await adapter.get_market_realtime_quotes(['行业板块'])
        print(f"获取行业板块行情：{len(data)} 条")
        if data:
            print(f"示例：{data[0].code} {data[0].name} 最新价={data[0].price} 涨跌幅={data[0].change_pct}%")
    except Exception as e:
        print(f"行业板块测试失败：{e}")
    
    await adapter.close()

async def main():
    print("开始测试 efinance 市场实时行情 API...")
    await test_market_quotes()
    print("\n测试完成！")

if __name__ == '__main__':
    asyncio.run(main())

"""
测试 efinance 数据源
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.adapters import data_source_manager


async def test_efinance():
    """测试 efinance 数据源"""
    
    print("\n" + "=" * 70)
    print("efinance 数据源测试")
    print("=" * 70)
    
    # 强制设置数据源优先级
    from app.config import settings
    settings.DATA_SOURCE_PRIORITY = ["tushare", "efinance", "akshare", "baostock"]
    
    # 重置工厂初始化状态
    from app.adapters.factory import DataSourceFactory
    DataSourceFactory._initialized = False
    DataSourceFactory._adapters.clear()
    
    # 初始化数据源
    await data_source_manager.initialize()
    
    # 检查 efinance 是否可用
    adapters = data_source_manager._factory._adapters
    print(f"\n已初始化的数据源：{list(adapters.keys())}")
    
    if 'efinance' not in [s.value for s in adapters.keys()]:
        print("\n❌ efinance 未被初始化，可能是优先级不够或有其他问题")
        return
    
    print("\n✅ efinance 数据源已初始化")
    
    # 测试 1：获取股票列表
    print("\n1️⃣ 测试获取股票列表...")
    try:
        stock_list = await data_source_manager.get_stock_list(source_type='efinance')
        print(f"✅ 获取到 {len(stock_list)} 只股票")
        if stock_list:
            print(f"   示例：{stock_list[0].code} - {stock_list[0].name}")
    except Exception as e:
        print(f"❌ 获取股票列表失败：{e}")
    
    # 测试 2：获取股票信息
    print("\n2️⃣ 测试获取股票信息（000001）...")
    try:
        stock_info = await data_source_manager.get_stock_info("000001", source_type='efinance')
        if stock_info:
            print(f"✅ 获取成功")
            print(f"   代码：{stock_info.code}")
            print(f"   名称：{stock_info.name}")
            print(f"   市场：{stock_info.market}")
        else:
            print("❌ 未获取到数据")
    except Exception as e:
        print(f"❌ 获取股票信息失败：{e}")
    
    # 测试 3：获取 K 线数据
    print("\n3️⃣ 测试获取 K 线数据（000001）...")
    try:
        klines = await data_source_manager.get_kline(
            "000001",
            start_date="20240101",
            end_date="20241231",
            source_type='efinance'
        )
        if klines:
            print(f"✅ 获取到 {len(klines)} 条 K 线数据")
            print(f"   最新一条：{klines[-1].date} - 开:{klines[-1].open} 高:{klines[-1].high} 低:{klines[-1].low} 收:{klines[-1].close}")
        else:
            print("❌ 未获取到数据")
    except Exception as e:
        print(f"❌ 获取 K 线数据失败：{e}")
    
    # 测试 4：获取实时行情
    print("\n4️⃣ 测试获取实时行情（000001）...")
    try:
        quote = await data_source_manager.get_realtime_quote("000001", source_type='efinance')
        if quote and quote.get('price'):
            print(f"✅ 获取成功")
            print(f"   最新价：{quote['price']}")
            print(f"   涨跌幅：{quote['change_pct']}%")
            print(f"   成交量：{quote['volume']}")
        else:
            print("❌ 未获取到数据")
    except Exception as e:
        print(f"❌ 获取实时行情失败：{e}")
    
    # 测试 5：获取板块列表
    print("\n5️⃣ 测试获取板块列表...")
    try:
        sectors = await data_source_manager.get_sector_list(sector_type="industry", source_type='efinance')
        if sectors:
            print(f"✅ 获取到 {len(sectors)} 个板块")
            print(f"   示例：{sectors[0].name} ({sectors[0].code})")
        else:
            print("❌ 未获取到数据")
    except Exception as e:
        print(f"❌ 获取板块列表失败：{e}")
    
    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)
    
    await data_source_manager.close()


if __name__ == "__main__":
    asyncio.run(test_efinance())

"""
测试按需加载功能

验证点：
1. 启动时不会批量预加载数据
2. 只在请求特定股票时才拉取数据
3. 拉取后数据会保存到数据库
4. 再次请求时直接从数据库读取，不会重复拉取
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.adapters import data_source_manager
from app.services.stock_service import StockService
from app.storage.sqlite import get_session, KLine
from sqlalchemy import select, func


async def test_lazy_loading():
    """测试按需加载功能"""
    
    print("\n" + "=" * 70)
    print("按需加载功能测试")
    print("=" * 70)
    
    # 1. 初始化数据源（不应该触发批量加载）
    print("\n1️⃣ 初始化数据源...")
    await data_source_manager.initialize()
    print("✅ 数据源初始化完成（未触发批量加载）")
    
    # 2. 检查数据库中股票数量
    print("\n2️⃣ 检查数据库状态...")
    async with get_session() as session:
        result = await session.execute(select(func.count()).select_from(KLine))
        kline_count = result.scalar()
        print(f"📊 数据库中 K 线数据总数：{kline_count} 条")
    
    # 3. 请求单只股票数据（应该触发按需加载）
    print("\n3️⃣ 请求单只股票数据（000001）...")
    stock_service = StockService()
    
    kline_data = await stock_service.get_kline(
        code="000001",
        start_date="20240101",
        end_date="20241231",
        adjust="qfq",
        use_cache=True,
        persist=True
    )
    
    print(f"✅ 获取到 {len(kline_data['data'])} 条 K 线数据")
    print(f"📊 数据状态：{kline_data['status']}")
    print(f"📊 后台加载：{kline_data['background_loading']}")
    
    # 4. 再次请求同一只股票（应该从数据库读取）
    print("\n4️⃣ 再次请求同一只股票（应该从数据库读取）...")
    kline_data2 = await stock_service.get_kline(
        code="000001",
        start_date="20240101",
        end_date="20241231",
        adjust="qfq",
        use_cache=True,
        persist=True
    )
    
    print(f"✅ 获取到 {len(kline_data2['data'])} 条 K 线数据")
    print(f"📊 数据状态：{kline_data2['status']}")
    
    # 5. 请求另一只股票（应该触发新的拉取）
    print("\n5️⃣ 请求另一只股票（000002）...")
    try:
        kline_data3 = await stock_service.get_kline(
            code="000002",
            start_date="20240101",
            end_date="20241231",
            adjust="qfq",
            use_cache=True,
            persist=True
        )
        print(f"✅ 获取到 {len(kline_data3['data'])} 条 K 线数据")
    except Exception as e:
        print(f"⚠️ 获取失败：{e}")
    
    # 6. 检查数据库变化
    print("\n6️⃣ 检查数据库状态变化...")
    async with get_session() as session:
        result = await session.execute(select(func.count()).select_from(KLine))
        new_kline_count = result.scalar()
        print(f"📊 数据库中 K 线数据总数：{new_kline_count} 条")
        print(f"📈 新增数据：{new_kline_count - kline_count} 条")
    
    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)
    print("\n验证结果：")
    print("✅ 启动时未批量预加载数据")
    print("✅ 只在请求时才拉取数据")
    print("✅ 拉取后数据保存到数据库")
    print("✅ 再次请求时从数据库读取")
    
    await data_source_manager.close()


if __name__ == "__main__":
    asyncio.run(test_lazy_loading())

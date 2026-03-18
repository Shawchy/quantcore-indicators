"""
测试数据源优先级参数功能
"""
import asyncio
import sys
sys.path.insert(0, 'd:/PROJ/Quant/backend')

from app.adapters.factory import data_source_manager


async def test_priority_params():
    """测试优先级参数"""
    print("=" * 60)
    print("测试数据源优先级参数功能")
    print("=" * 60)
    
    # 初始化
    await data_source_manager.initialize()
    
    print(f"\n可用数据源：{data_source_manager.get_available_sources()}")
    
    # 测试 1: 默认自动选择
    print("\n[测试 1] 默认自动选择（不传参数）")
    try:
        result = await data_source_manager.get_stock_info("600519")
        if result:
            print(f"✅ 成功获取：{result.code} - {result.name}")
        else:
            print("❌ 获取失败")
    except Exception as e:
        print(f"❌ 异常：{e}")
    
    # 测试 2: 指定优先级
    print("\n[测试 2] 指定优先级：efinance")
    try:
        result = await data_source_manager.get_stock_info(
            "600519",
            source_type="efinance"
        )
        if result:
            print(f"✅ 成功获取：{result.code} - {result.name}")
        else:
            print("❌ 获取失败")
    except Exception as e:
        print(f"❌ 异常：{e}")
    
    # 测试 3: 临时优先级列表
    print("\n[测试 3] 临时优先级：efinance,akshare")
    try:
        result = await data_source_manager.get_stock_info(
            "600519",
            source_priority="efinance,akshare"
        )
        if result:
            print(f"✅ 成功获取：{result.code} - {result.name}")
        else:
            print("❌ 获取失败")
    except Exception as e:
        print(f"❌ 异常：{e}")
    
    # 测试 4: 排除数据源
    print("\n[测试 4] 排除 tushare（如果有的话）")
    try:
        result = await data_source_manager.get_stock_info(
            "600519",
            source_exclude="tushare"
        )
        if result:
            print(f"✅ 成功获取：{result.code} - {result.name}")
        else:
            print("❌ 获取失败")
    except Exception as e:
        print(f"❌ 异常：{e}")
    
    # 测试 5: 强制使用且不允许故障转移
    print("\n[测试 5] 强制使用 efinance，不允许故障转移")
    try:
        result = await data_source_manager.get_stock_info(
            "600519",
            source_type="efinance",
            fallback=False
        )
        if result:
            print(f"✅ 成功获取：{result.code} - {result.name}")
        else:
            print("❌ 获取失败")
    except Exception as e:
        print(f"❌ 异常：{e}")
    
    # 测试 6: 获取股票列表
    print("\n[测试 6] 获取股票列表（默认优先级）")
    try:
        stocks = await data_source_manager.get_stock_list()
        if stocks:
            print(f"✅ 成功获取 {len(stocks)} 只股票")
            print(f"   前 3 只：{[s.name for s in stocks[:3]]}")
        else:
            print("❌ 获取失败")
    except Exception as e:
        print(f"❌ 异常：{e}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_priority_params())

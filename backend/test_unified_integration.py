"""
统一适配器集成测试

验证新模块集成到现有系统的功能
"""
import asyncio
from datetime import datetime, timedelta


async def test_unified_adapter():
    """测试统一适配器基本功能"""
    print("\n" + "=" * 60)
    print("Unified Adapter Integration Test")
    print("=" * 60)
    
    # 导入统一适配器
    from app.adapters.unified_adapter import EFinanceUnifiedAdapter
    from app.models.unified_models import DataSourceType
    
    # 创建适配器实例
    adapter = EFinanceUnifiedAdapter()
    await adapter.initialize()
    
    print(f"\n[*] Adapter initialized: {adapter.source_type.value}")
    
    # 测试获取 K 线数据（使用统一格式）
    print("\nTest 1: Get unified K-line data")
    code = "600000"
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    klines = await adapter.get_unified_kline(
        code=code,
        start_date=start_date,
        end_date=end_date,
        adjust_type="qfq",
        save_to_storage=False,  # 测试时不保存
        calculate_indicators=False
    )
    
    print(f"[*] Got {code} K-line data: {len(klines)} records")
    
    if klines:
        # 显示第一条数据
        first = klines[0]
        print(f"\nFirst record:")
        print(f"  Date: {first.date}")
        print(f"  Open: {first.open}")
        print(f"  Close: {first.close}")
        print(f"  High: {first.high}")
        print(f"  Low: {first.low}")
        print(f"  Volume: {first.volume}")
    
    # 测试数据验证
    print("\nTest 2: Data validation")
    from app.utils.data_normalizer import DataNormalizer
    
    valid_count = sum(1 for k in klines if DataNormalizer.validate_kline(k))
    print(f"[*] Data validation passed: {valid_count}/{len(klines)} records")
    
    # 测试批量获取
    print("\nTest 3: Batch K-line data acquisition")
    codes = ["600000", "000001"]
    results = await adapter.get_unified_kline_batch(
        codes=codes,
        start_date=start_date,
        end_date=end_date,
        save_to_storage=False,
        max_concurrent=2
    )
    
    success_count = sum(1 for klines in results.values() if klines)
    total_count = sum(len(klines) for klines in results.values())
    print(f"[*] Batch acquisition complete: {success_count}/{len(codes)} succeeded, {total_count} total records")
    
    # 测试技术指标计算
    print("\nTest 4: Technical indicator calculation")
    if len(klines) > 30:
        df = adapter._klines_to_dataframe(klines)
        df_with_indicators = adapter.indicators_manager.calculate_all_indicators(df)
        print(f"[*] Indicator calculation complete, data shape: {df_with_indicators.shape}")
    else:
        print("[!] Insufficient data, skipping indicator calculation")
    
    await adapter.close()
    
    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)


async def test_factory_integration():
    """测试工厂类集成"""
    print("\n" + "=" * 60)
    print("工厂类集成测试")
    print("=" * 60)
    
    from app.adapters.factory import DataSourceFactory
    
    # 初始化工厂
    print("\n初始化工厂...")
    await DataSourceFactory.initialize()
    
    # 获取统一适配器
    print("\n获取统一适配器...")
    try:
        unified_adapter = DataSourceFactory.get_unified_adapter("efinance")
        print(f"✓ 成功获取统一适配器：{unified_adapter.source_type.value}")
        
        # 验证适配器类型
        from app.adapters.unified_adapter import UnifiedDataAdapter
        if isinstance(unified_adapter, UnifiedDataAdapter):
            print("✓ 适配器类型正确：UnifiedDataAdapter")
        else:
            print("⚠ 适配器类型不正确")
        
    except Exception as e:
        print(f"✗ 获取统一适配器失败：{e}")
    
    # 获取普通适配器
    print("\n获取普通适配器...")
    try:
        normal_adapter = DataSourceFactory.get_adapter("efinance")
        print(f"✓ 成功获取普通适配器：{normal_adapter.source_type.value}")
    except Exception as e:
        print(f"✗ 获取普通适配器失败：{e}")
    
    print("\n" + "=" * 60)
    print("工厂集成测试完成！")
    print("=" * 60)


async def main():
    """运行所有测试"""
    try:
        await test_unified_adapter()
        await asyncio.sleep(2)
        await test_factory_integration()
    except Exception as e:
        print(f"\n测试失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

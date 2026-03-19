"""
生产环境验证脚本

验证统一适配器在生产环境的性能和稳定性
"""
import asyncio
import time
from datetime import datetime, timedelta
from typing import List


async def test_large_scale_data():
    """测试大规模数据处理"""
    print("\n" + "=" * 70)
    print("Production Environment Validation - Large Scale Data Test")
    print("=" * 70)
    
    from app.adapters.unified_adapter import EFinanceUnifiedAdapter
    
    adapter = EFinanceUnifiedAdapter()
    await adapter.initialize()
    
    # 测试 1: 长时间序列数据（1 年）
    print("\n[Test 1] Long time series data (1 year)")
    code = "600000"
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    
    start_time = time.time()
    klines = await adapter.get_unified_kline(
        code=code,
        start_date=start_date,
        end_date=end_date,
        save_to_storage=False
    )
    elapsed = time.time() - start_time
    
    print(f"  ✓ Got {len(klines)} records in {elapsed:.2f}s")
    print(f"  ✓ Average speed: {len(klines)/elapsed:.1f} records/s")
    
    # 测试 2: 大批量股票获取（10 只股票）
    print("\n[Test 2] Large batch acquisition (10 stocks)")
    codes = [
        "600000", "600036", "601318", "601398", "600519",
        "000001", "000002", "000858", "300750", "300059"
    ]
    
    start_time = time.time()
    results = await adapter.get_unified_kline_batch(
        codes=codes,
        start_date=start_date,
        end_date=end_date,
        max_concurrent=3,
        save_to_storage=False
    )
    elapsed = time.time() - start_time
    
    success_count = sum(1 for klines in results.values() if klines)
    total_count = sum(len(klines) for klines in results.values())
    
    print(f"  ✓ Success: {success_count}/{len(codes)} stocks")
    print(f"  ✓ Total records: {total_count}")
    print(f"  ✓ Time: {elapsed:.2f}s")
    print(f"  ✓ Average speed: {total_count/elapsed:.1f} records/s")
    
    # 测试 3: 技术指标计算性能
    print("\n[Test 3] Technical indicator calculation performance")
    if len(klines) > 30:
        df = adapter._klines_to_dataframe(klines)
        
        start_time = time.time()
        df_with_indicators = adapter.indicators_manager.calculate_all_indicators(df)
        elapsed = time.time() - start_time
        
        print(f"  ✓ Calculated {len(df_with_indicators.columns)} columns")
        print(f"  ✓ Time: {elapsed:.2f}s")
        print(f"  ✓ Data shape: {df_with_indicators.shape}")
    
    # 测试 4: 数据验证性能
    print("\n[Test 4] Data validation performance")
    start_time = time.time()
    
    from app.utils.data_normalizer import DataNormalizer
    valid_count = sum(1 for k in klines if DataNormalizer.validate_kline(k))
    elapsed = time.time() - start_time
    
    print(f"  ✓ Validated {valid_count}/{len(klines)} records")
    print(f"  ✓ Time: {elapsed:.2f}s")
    print(f"  ✓ Speed: {len(klines)/elapsed:.1f} records/s")
    
    # 测试 5: 存储性能（实际写入）
    print("\n[Test 5] Storage performance (actual write)")
    # 只测试少量数据
    test_klines = klines[:10]
    
    start_time = time.time()
    for kline in test_klines:
        await adapter.storage_router.save_kline(
            code=code,
            kline_data=kline.model_dump(),
            adjust_type="qfq"
        )
    elapsed = time.time() - start_time
    
    print(f"  ✓ Stored {len(test_klines)} records")
    print(f"  ✓ Time: {elapsed:.2f}s")
    print(f"  ✓ Speed: {len(test_klines)/elapsed:.1f} records/s")
    
    await adapter.close()
    
    print("\n" + "=" * 70)
    print("Production validation complete!")
    print("=" * 70)
    
    # 返回性能指标
    return {
        "single_fetch_speed": len(klines) / elapsed,
        "batch_fetch_speed": total_count / elapsed,
        "validation_speed": len(klines) / elapsed,
        "total_records": total_count,
        "success_rate": success_count / len(codes)
    }


async def test_concurrent_load():
    """测试并发负载"""
    print("\n" + "=" * 70)
    print("Concurrent Load Test")
    print("=" * 70)
    
    from app.adapters.unified_adapter import EFinanceUnifiedAdapter
    
    adapter = EFinanceUnifiedAdapter()
    await adapter.initialize()
    
    # 测试不同并发级别
    concurrency_levels = [1, 2, 3, 5]
    
    for concurrency in concurrency_levels:
        print(f"\n[Concurrency: {concurrency}]")
        
        codes = ["600000", "000001", "300750"][:concurrency]
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        start_time = time.time()
        results = await adapter.get_unified_kline_batch(
            codes=codes,
            start_date=start_date,
            end_date=end_date,
            max_concurrent=concurrency,
            save_to_storage=False
        )
        elapsed = time.time() - start_time
        
        total_records = sum(len(klines) for klines in results.values())
        print(f"  ✓ Records: {total_records}")
        print(f"  ✓ Time: {elapsed:.2f}s")
        print(f"  ✓ Speed: {total_records/elapsed:.1f} records/s")
    
    await adapter.close()
    
    print("\n" + "=" * 70)
    print("Concurrent load test complete!")
    print("=" * 70)


async def main():
    """运行所有生产环境验证"""
    try:
        # 测试 1: 大规模数据
        metrics = await test_large_scale_data()
        
        # 输出性能指标
        print("\n" + "=" * 70)
        print("Performance Metrics Summary")
        print("=" * 70)
        print(f"Single fetch speed: {metrics['single_fetch_speed']:.1f} records/s")
        print(f"Batch fetch speed: {metrics['batch_fetch_speed']:.1f} records/s")
        print(f"Validation speed: {metrics['validation_speed']:.1f} records/s")
        print(f"Total records processed: {metrics['total_records']}")
        print(f"Success rate: {metrics['success_rate']:.1%}")
        print("=" * 70)
        
        # 测试 2: 并发负载
        await test_concurrent_load()
        
    except Exception as e:
        print(f"\nValidation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

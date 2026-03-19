"""
efinance K 线周期测试脚本

测试不同周期的 K 线数据获取
"""

import asyncio
from app.adapters.efinance_adapter import EFinanceAdapter


async def test_kline_periods():
    """测试不同周期的 K 线数据"""
    print("\n" + "="*60)
    print("efinance K 线周期测试")
    print("="*60)
    
    adapter = EFinanceAdapter()
    await adapter.initialize()
    
    # 测试的周期列表
    periods = [
        ("1m", "1 分钟"),
        ("5m", "5 分钟"),
        ("30m", "30 分钟"),
        ("60m", "60 分钟"),
        ("daily", "日线"),
        ("weekly", "周线"),
        ("monthly", "月线")
    ]
    
    code = "600519"  # 贵州茅台
    results = []
    
    print(f"\n测试股票：{code}（贵州茅台）\n")
    
    for period_code, period_name in periods:
        try:
            print(f"获取 {period_name} ({period_code})...", end=" ")
            
            # 获取 K 线数据
            klines = await adapter.get_kline(
                code,
                period=period_code,
                start_date="2024-01-01",
                end_date="2024-12-31"
            )
            
            if klines:
                # 显示最新一条数据
                latest = klines[-1]
                print(f"✓ {len(klines)}条，最新：{latest.date} 收盘={latest.close:.2f}")
                results.append((period_name, True, len(klines)))
            else:
                print(f"✗ 无数据")
                results.append((period_name, False, 0))
            
            # 查看统计
            stats = adapter.get_stats()
            print(f"  统计：请求{stats['total_requests']}次，成功率{stats['success_rate']}")
            
        except Exception as e:
            print(f"✗ 错误：{e}")
            results.append((period_name, False, 0))
    
    # 汇总
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for period_name, success, count in results:
        status = "✓ 通过" if success else "✗ 失败"
        count_str = f" ({count}条)" if success else ""
        print(f"{status} - {period_name}{count_str}")
    
    print(f"\n总计：{passed}/{total} 周期通过")
    
    # 最终统计
    final_stats = adapter.get_stats()
    print(f"\n最终统计：")
    print(f"  总请求：{final_stats['total_requests']}")
    print(f"  成功率：{final_stats['success_rate']}")
    print(f"  连续失败：{final_stats['consecutive_failures']}")
    
    if passed == total:
        print("\n✓ 所有周期测试通过！")
    else:
        print(f"\n⚠ {total - passed} 个周期未通过，请检查日志")


async def test_adjust_types():
    """测试不同复权方式"""
    print("\n" + "="*60)
    print("K 线复权方式测试")
    print("="*60)
    
    adapter = EFinanceAdapter()
    await adapter.initialize()
    
    code = "600519"
    adjusts = [
        ("qfq", "前复权"),
        ("hfq", "后复权"),
        ("no", "不复权")
    ]
    
    print(f"\n测试股票：{code}（贵州茅台）\n")
    
    for adjust_code, adjust_name in adjusts:
        try:
            print(f"获取 {adjust_name} ({adjust_code})...", end=" ")
            
            klines = await adapter.get_kline(
                code,
                adjust=adjust_code,
                period="daily",
                start_date="2024-01-01",
                end_date="2024-12-31"
            )
            
            if klines:
                latest = klines[-1]
                print(f"✓ {len(klines)}条，最新：{latest.date} 收盘={latest.close:.2f}")
            else:
                print(f"✗ 无数据")
            
        except Exception as e:
            print(f"✗ 错误：{e}")
    
    print("\n✓ 复权方式测试完成！")


async def test_cache():
    """测试缓存机制"""
    print("\n" + "="*60)
    print("K 线缓存机制测试")
    print("="*60)
    
    adapter = EFinanceAdapter()
    await adapter.initialize()
    
    code = "600519"
    
    # 第一次请求
    print(f"\n第一次请求 {code}（日线）...")
    import time
    start = time.time()
    klines1 = await adapter.get_kline(code, period="daily")
    time1 = time.time() - start
    print(f"  耗时：{time1:.3f}秒，数据：{len(klines1)}条")
    
    # 第二次请求（缓存）
    print(f"第二次请求 {code}（日线，应从缓存返回）...")
    start = time.time()
    klines2 = await adapter.get_kline(code, period="daily")
    time2 = time.time() - start
    print(f"  耗时：{time2:.3f}秒，数据：{len(klines2)}条")
    
    # 不同周期（新请求）
    print(f"第三次请求 {code}（60 分钟，新请求）...")
    start = time.time()
    klines3 = await adapter.get_kline(code, period="60m")
    time3 = time.time() - start
    print(f"  耗时：{time3:.3f}秒，数据：{len(klines3)}条")
    
    # 缓存加速比
    if time2 > 0:
        speedup = time1 / time2
        print(f"\n✓ 缓存加速：{speedup:.1f}x")
    else:
        print(f"\n✓ 缓存命中（瞬间返回）")
    
    print("\n✓ 缓存机制测试完成！")


async def main():
    """运行所有测试"""
    try:
        # 测试 1：不同周期
        await test_kline_periods()
        
        # 等待 2 秒
        await asyncio.sleep(2)
        
        # 测试 2：不同复权
        await test_adjust_types()
        
        # 等待 2 秒
        await asyncio.sleep(2)
        
        # 测试 3：缓存机制
        await test_cache()
        
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n✗ 测试程序异常：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

"""
智能数据源优化测试脚本
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.adapters import (
    data_source_manager,
    dynamic_priority_manager,
    batch_optimizer,
    smart_preloader,
    DataSourceType,
)


async def test_data_source_manager():
    """测试数据源管理器"""
    print("=" * 70)
    print("数据源管理器集成测试")
    print("=" * 70)
    
    # 1. 初始化
    print("\n1. 初始化数据源管理器...")
    try:
        await data_source_manager.initialize()
        print("   ✓ 初始化成功")
    except Exception as e:
        print(f"   ✗ 初始化失败: {e}")
        return
    
    # 2. 获取策略信息
    print("\n2. 获取策略信息 (kline):")
    try:
        info = data_source_manager.get_strategy_info("kline")
        if info:
            print(f"   ✓ 获取成功")
            print(f"   - 优先级: {info['priority']}")
            print(f"   - 敏感度: {info['sensitivity']}")
            print(f"   - 缓存TTL: {info['cache_ttl']}秒")
    except Exception as e:
        print(f"   ✗ 获取失败: {e}")
    
    # 3. 测试数据获取（记录性能）
    print("\n3. 测试数据获取（记录性能统计）:")
    try:
        # 获取股票信息
        stock_info = await data_source_manager.get_stock_info("600000")
        if stock_info:
            print(f"   ✓ 获取股票信息成功: {stock_info.name}")
        else:
            print("   ✗ 未获取到股票信息")
        
        # 获取K线数据
        kline = await data_source_manager.get_kline("600000", "2025-03-01", "2025-03-05")
        if kline:
            print(f"   ✓ 获取K线数据成功: {len(kline)} 条")
        else:
            print("   ✗ 未获取到K线数据")
            
    except Exception as e:
        print(f"   ✗ 数据获取失败: {e}")
    
    # 4. 获取优化统计
    print("\n4. 获取优化统计信息:")
    try:
        stats = data_source_manager.get_optimization_stats()
        print(f"   ✓ 优化已启用: {stats.get('optimization_enabled', False)}")
        
        if stats.get('optimization_enabled'):
            # 动态优先级统计
            if 'dynamic_priority' in stats:
                print(f"   - 动态优先级数据类型数: {len(stats['dynamic_priority'].get('data_types', {}))}")
            
            # 智能预加载统计
            if 'smart_preloader' in stats:
                preloader_stats = stats['smart_preloader']
                print(f"   - 预加载用户数: {preloader_stats.get('total_users', 0)}")
                print(f"   - 活跃用户数: {preloader_stats.get('active_users', 0)}")
            
            # 批量优化统计
            if 'batch_optimizer' in stats:
                batch_stats = stats['batch_optimizer']
                print(f"   - 批量请求总数: {batch_stats.get('total_requests', 0)}")
                print(f"   - 平均批量大小: {batch_stats.get('avg_batch_size', 0):.2f}")
    except Exception as e:
        print(f"   ✗ 获取统计失败: {e}")
    
    # 5. 获取性能报告
    print("\n5. 获取性能报告:")
    try:
        report = data_source_manager.get_performance_report()
        if report.get('optimization_enabled'):
            print(f"   ✓ 性能报告已生成")
            print(f"   - 最后更新: {report.get('last_update', 'N/A')}")
            print(f"   - 数据类型数: {len(report.get('data_types', {}))}")
        else:
            print("   ⚠ 优化未启用")
    except Exception as e:
        print(f"   ✗ 获取性能报告失败: {e}")
    
    # 6. 关闭
    print("\n6. 关闭数据源管理器...")
    try:
        await data_source_manager.close()
        print("   ✓ 关闭成功")
    except Exception as e:
        print(f"   ✗ 关闭失败: {e}")
    
    print("\n" + "=" * 70)


async def test_individual_modules():
    """测试独立模块"""
    print("\n" + "=" * 70)
    print("独立模块测试")
    print("=" * 70)
    
    # 1. 测试动态优先级
    print("\n1. 动态优先级管理器:")
    try:
        await dynamic_priority_manager.start()
        print("   ✓ 启动成功")
        
        # 记录一些请求
        dynamic_priority_manager.record_request(
            DataSourceType.AKSHARE, "kline", True, 0.5
        )
        dynamic_priority_manager.record_request(
            DataSourceType.EFINANCE, "kline", True, 0.3
        )
        
        # 获取优先级
        priority = dynamic_priority_manager.get_priority("kline")
        print(f"   ✓ 动态优先级: {[s.value for s in priority]}")
        
        # 获取报告
        report = dynamic_priority_manager.get_priority_report()
        print(f"   ✓ 报告数据类型数: {len(report.get('data_types', {}))}")
        
        await dynamic_priority_manager.stop()
        print("   ✓ 停止成功")
    except Exception as e:
        print(f"   ✗ 测试失败: {e}")
    
    # 2. 测试批量优化器
    print("\n2. 批量请求优化器:")
    try:
        stats = batch_optimizer.get_stats()
        print(f"   ✓ 批量优化器统计:")
        print(f"     - 总请求数: {stats.get('total_requests', 0)}")
        print(f"     - 批量请求数: {stats.get('batched_requests', 0)}")
        print(f"     - 平均批量大小: {stats.get('avg_batch_size', 0):.2f}")
    except Exception as e:
        print(f"   ✗ 测试失败: {e}")
    
    # 3. 测试智能预加载
    print("\n3. 智能预加载器:")
    try:
        await smart_preloader.start()
        print("   ✓ 启动成功")
        
        # 记录用户请求
        smart_preloader.record_user_request("user_123", "realtime_quote", "600000")
        smart_preloader.record_user_request("user_123", "kline", "600000")
        smart_preloader.record_user_request("user_123", "realtime_quote", "000001")
        
        # 获取统计
        stats = smart_preloader.get_stats()
        print(f"   ✓ 预加载统计:")
        print(f"     - 总用户数: {stats.get('total_users', 0)}")
        print(f"     - 活跃用户数: {stats.get('active_users', 0)}")
        print(f"     - 缓存大小: {stats.get('cache_size', 0)}")
        
        # 获取用户模式
        pattern = smart_preloader.get_user_pattern("user_123")
        if pattern:
            print(f"   ✓ 用户关注股票: {list(pattern.watched_stocks)[:3]}")
        
        await smart_preloader.stop()
        print("   ✓ 停止成功")
    except Exception as e:
        print(f"   ✗ 测试失败: {e}")
    
    print("\n" + "=" * 70)


async def main():
    """主测试函数"""
    print("\n" + "=" * 70)
    print("智能数据源优化集成测试")
    print("=" * 70)
    
    # 测试独立模块
    await test_individual_modules()
    
    # 测试数据源管理器集成
    await test_data_source_manager()
    
    print("\n✓ 所有测试完成")


if __name__ == "__main__":
    asyncio.run(main())

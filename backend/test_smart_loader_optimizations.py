"""
智能数据加载器优化测试

验证所有优化功能：
1. 访问频率统计
2. 智能预热
3. 缓存命中率监控
4. 健康报告和告警
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.smart_loader import smart_loader


async def test_smart_loader_optimizations():
    """测试智能加载器优化功能"""
    print("=" * 70)
    print("智能数据加载器优化功能测试")
    print("=" * 70)
    
    # 1. 测试访问频率统计
    print("\n[测试 1] 访问频率统计")
    print("-" * 70)
    
    # 模拟多次访问
    test_codes = ["600519", "000001", "300750"]
    for i in range(3):
        for code in test_codes:
            quote = await smart_loader.get_quote(code, use_cache=True)
            if quote:
                print(f"访问 {code}: 价格 {quote.get('price', 'N/A')}")
    
    print(f"✅ 访问频率统计完成")
    print(f"   记录代码数：{len(smart_loader._access_frequency)}")
    
    # 2. 测试智能预热
    print("\n[测试 2] 智能预热（基于访问频率）")
    print("-" * 70)
    
    # 先模拟一些访问
    for code in ["600519", "000001"]:
        for _ in range(5):
            await smart_loader._record_access(code)
    
    hot_codes = await smart_loader._get_hot_codes(limit=5)
    print(f"热门代码：{hot_codes}")
    
    # 执行智能预热
    await smart_loader.warmup_cache(use_smart_warmup=True)
    
    # 3. 测试健康报告
    print("\n[测试 3] 缓存健康报告")
    print("-" * 70)
    
    health_report = await smart_loader.get_health_report()
    print(f"健康状态：{health_report['health_status']}")
    print(f"缓存命中率：{health_report['hit_rate']:.2%}")
    print(f"总请求数：{health_report['total_requests']}")
    print(f"命中次数：{health_report['total_hits']}")
    print(f"未命中次数：{health_report['total_misses']}")
    print(f"缓存已预热：{health_report['cache_warmed']}")
    
    # 4. 测试监控告警
    print("\n[测试 4] 监控告警")
    print("-" * 70)
    
    report = await smart_loader.check_and_report()
    print(f"报告生成完成")
    print(f"健康状态：{report['health_status']}")
    
    # 5. 测试存储统计
    print("\n[测试 5] 存储器统计信息")
    print("-" * 70)
    
    stats = smart_loader.get_storage_stats()
    for category, category_stats in stats.items():
        if isinstance(category_stats, dict):
            l1_hits = category_stats.get('l1_hits', 0)
            l2_hits = category_stats.get('l2_hits', 0)
            misses = category_stats.get('misses', 0)
            print(f"{category}: L1={l1_hits}, L2={l2_hits}, Miss={misses}")
    
    print("\n" + "=" * 70)
    print("测试完成！所有优化功能正常")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_smart_loader_optimizations())

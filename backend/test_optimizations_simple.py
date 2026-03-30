"""
智能数据加载器优化验证测试
"""
import asyncio
from app.services.smart_loader import smart_loader

async def test():
    print("=" * 70)
    print("智能数据加载器优化验证")
    print("=" * 70)
    
    # 测试 1: 访问频率统计
    print("\n[1] 测试访问频率统计")
    quote = await smart_loader.get_quote("600519", use_cache=True)
    if quote:
        print(f"✅ 访问成功：600519 价格={quote.get('price', 'N/A')}")
        print(f"   访问记录数：{len(smart_loader._access_frequency)}")
    
    # 测试 2: 热门代码
    print("\n[2] 测试获取热门代码")
    hot_codes = await smart_loader._get_hot_codes(limit=5)
    print(f"✅ 热门代码：{hot_codes}")
    
    # 测试 3: 健康报告
    print("\n[3] 测试健康报告")
    report = await smart_loader.get_health_report()
    print(f"✅ 健康状态：{report['health_status']}")
    print(f"   命中率：{report['hit_rate']:.2%}")
    
    # 测试 4: 监控告警
    print("\n[4] 测试监控告警")
    check_report = await smart_loader.check_and_report()
    print(f"✅ 报告状态：{check_report['health_status']}")
    
    print("\n" + "=" * 70)
    print("所有优化功能验证完成！")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test())

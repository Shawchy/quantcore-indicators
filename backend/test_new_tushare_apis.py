"""
测试新增的 Tushare API

测试装饰器注册和新 API 功能
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.adapters.tushare_adapter import TushareAdapter
from app.utils.tushare_api_registry import get_api_registry


async def test_new_apis():
    """测试新增的 API"""
    print("=" * 80)
    print("测试新增的 Tushare API")
    print("=" * 80)
    
    # 创建适配器
    adapter = TushareAdapter()
    
    # 初始化
    print("\n📌 初始化 Tushare 适配器...")
    success = await adapter.initialize()
    
    if not success:
        print("⚠️  Tushare 初始化失败，跳过测试")
        return
    
    print("✅ 初始化成功\n")
    
    # 获取注册表
    registry = get_api_registry()
    
    # 测试 1: 周线 K 线（需要 2000 分）
    print("📌 测试 1: 周线 K 线（需要 2000 分）")
    api_info = registry.get_api_info("get_weekly")
    if api_info:
        print(f"   API 信息：{api_info.description}")
        print(f"   所需积分：{api_info.min_points}分")
        print(f"   当前积分：{registry._instance._points_manager.get_points() if hasattr(registry, '_instance') else 'N/A'}分")
        
        has_perm = registry.check_permission("get_weekly")
        print(f"   权限状态：{'✅ 可用' if has_perm else '❌ 不足'}")
    else:
        print("   ❌ API 未注册")
    
    # 测试 2: 月线 K 线（需要 2000 分）
    print("\n📌 测试 2: 月线 K 线（需要 2000 分）")
    api_info = registry.get_api_info("get_monthly")
    if api_info:
        print(f"   API 信息：{api_info.description}")
        print(f"   所需积分：{api_info.min_points}分")
        has_perm = registry.check_permission("get_monthly")
        print(f"   权限状态：{'✅ 可用' if has_perm else '❌ 不足'}")
    else:
        print("   ❌ API 未注册")
    
    # 测试 3: 龙虎榜（需要 200 分）
    print("\n📌 测试 3: 龙虎榜（需要 200 分）")
    api_info = registry.get_api_info("get_top_list")
    if api_info:
        print(f"   API 信息：{api_info.description}")
        print(f"   所需积分：{api_info.min_points}分")
        has_perm = registry.check_permission("get_top_list")
        print(f"   权限状态：{'✅ 可用' if has_perm else '❌ 不足'}")
    else:
        print("   ❌ API 未注册")
    
    # 测试 4: 业绩预告（需要 800 分）
    print("\n📌 测试 4: 业绩预告（需要 800 分）")
    api_info = registry.get_api_info("get_forecast")
    if api_info:
        print(f"   API 信息：{api_info.description}")
        print(f"   所需积分：{api_info.min_points}分")
        has_perm = registry.check_permission("get_forecast")
        print(f"   权限状态：{'✅ 可用' if has_perm else '❌ 不足'}")
    else:
        print("   ❌ API 未注册")
    
    # 测试 5: 资金流向（需要 5000 分）
    print("\n📌 测试 5: 资金流向（需要 5000 分）")
    api_info = registry.get_api_info("get_moneyflow")
    if api_info:
        print(f"   API 信息：{api_info.description}")
        print(f"   所需积分：{api_info.min_points}分")
        has_perm = registry.check_permission("get_moneyflow")
        print(f"   权限状态：{'✅ 可用' if has_perm else '❌ 不足'}")
    else:
        print("   ❌ API 未注册")
    
    # 统计
    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)
    
    new_apis = ["get_weekly", "get_monthly", "get_top_list", "get_forecast", "get_moneyflow"]
    registered = 0
    available = 0
    
    for api_name in new_apis:
        api_info = registry.get_api_info(api_name)
        if api_info:
            registered += 1
            if registry.check_permission(api_name):
                available += 1
    
    print(f"\n新增 API 数量：{len(new_apis)}")
    print(f"已注册：{registered}/{len(new_apis)}")
    print(f"可用（积分足够）：{available}/{registered}")
    
    # 显示所有可用 API
    print(f"\n📊 当前可用 API 总数：{len(registry.get_available_apis())}")
    print(f"📊 当前不可用 API 总数：{len(registry.get_unavailable_apis())}")
    
    print("\n" + "=" * 80)


async def main():
    await test_new_apis()


if __name__ == "__main__":
    asyncio.run(main())

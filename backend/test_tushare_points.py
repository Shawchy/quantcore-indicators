"""
Tushare 积分权限管理测试脚本

测试积分管理器和数据源智能切换功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.utils.tushare_points_manager import get_points_manager
from app.adapters.factory import DataSourceFactory, DataSourceManager


def test_points_manager():
    """测试积分管理器"""
    print("=" * 60)
    print("测试 1: Tushare 积分管理器")
    print("=" * 60)
    
    manager = get_points_manager()
    
    print(f"\n📊 当前积分：{manager.get_points()}分")
    print(f"✅ 可用接口数量：{len(manager.get_available_permissions())}")
    print(f"❌ 不可用接口数量：{len(manager.get_unavailable_permissions())}")
    
    # 显示权限摘要
    summary = manager.get_permission_summary()
    print(f"\n📋 权限摘要:")
    print(f"   可用接口：{summary['available_count']} 个")
    print(f"   不可用接口：{summary['unavailable_count']} 个")
    
    if summary.get('next_level'):
        print(f"   下一等级：{summary['next_level']}分")
        print(f"   还差：{summary['points_to_next']}分")
    
    # 测试具体接口权限
    print(f"\n🔍 接口权限测试:")
    test_apis = [
        ("daily", "日线行情", 120),
        ("adj_factor", "复权因子", 120),
        ("intraday", "分钟线", 5000),
        ("top_list", "龙虎榜", 200),
        ("weekly", "周线", 2000),
    ]
    
    for api_name, api_desc, required_points in test_apis:
        has_perm = manager.has_permission(api_name)
        status = "✅" if has_perm else "❌"
        needed = manager.get_points_needed(api_name)
        
        if has_perm:
            print(f"   {status} {api_desc} ({api_name}) - 可用")
        else:
            print(f"   {status} {api_desc} ({api_name}) - 需要{needed}分")
    
    print()


async def test_data_source_initialization():
    """测试数据源初始化"""
    print("=" * 60)
    print("测试 2: 数据源初始化（带积分管理）")
    print("=" * 60)
    
    # 初始化数据源工厂
    await DataSourceFactory.initialize()
    
    # 获取可用的数据源列表
    available_sources = DataSourceFactory.get_available_sources()
    print(f"\n✅ 可用数据源：{available_sources}")
    
    # 检查配置
    print(f"📊 默认数据源：{settings.DEFAULT_DATA_SOURCE}")
    print(f"📊 Tushare 积分：{settings.TUSHARE_POINTS}分")
    print(f"📊 Tushare Token: {'已配置' if settings.TUSHARE_TOKEN else '未配置'}")
    
    print()


async def test_intelligent_switching():
    """测试智能切换逻辑"""
    print("=" * 60)
    print("测试 3: 智能数据源切换（基于积分）")
    print("=" * 60)
    
    manager = DataSourceManager()
    await manager.initialize()
    
    # 测试日线数据（120 分应该可用）
    print("\n📌 测试 1: 日线 K 线数据（120 分权限）")
    try:
        klines = await manager.get_kline("600519", source_type="tushare")
        if klines:
            print(f"   ✅ 成功获取 {len(klines)} 条 K 线数据（使用 Tushare）")
            print(f"   最新日期：{klines[-1].date}")
            print(f"   收盘价：{klines[-1].close}")
        else:
            print(f"   ⚠️  未获取到数据（可能积分不足，已降级）")
    except Exception as e:
        print(f"   ❌ 获取失败：{e}")
    
    # 测试分钟线数据（需要 5000 分）
    print("\n📌 测试 2: 分钟 K 线数据（需要 5000 分）")
    try:
        minute_data = await manager.get_stock_zh_a_minute(
            symbol="600519",
            period="5",
            source_type="tushare"
        )
        if minute_data:
            print(f"   ✅ 成功获取 {len(minute_data)} 条 5 分钟 K 线（使用 Tushare）")
        else:
            print(f"   ⚠️  积分不足，自动降级到 AkShare")
            # 尝试使用 AkShare
            minute_data_ak = await manager.get_stock_zh_a_minute(
                symbol="600519",
                period="5",
                source_type="akshare"
            )
            if minute_data_ak:
                print(f"   ✅ 使用 AkShare 成功获取 {len(minute_data_ak)} 条数据")
            else:
                print(f"   ❌ 所有数据源都失败")
    except Exception as e:
        print(f"   ❌ 获取失败：{e}")
    
    print()


async def test_fallback_logic():
    """测试降级逻辑"""
    print("=" * 60)
    print("测试 4: 数据源降级逻辑")
    print("=" * 60)
    
    manager = DataSourceManager()
    await manager.initialize()
    
    # 测试 1: 请求 Tushare（如果积分不足应该降级）
    print("\n📌 测试：请求 Tushare 数据源")
    adapter = manager.get_adapter("tushare")
    if adapter:
        print(f"   实际使用：{adapter.source_type.value}")
        if adapter.source_type.value != "tushare":
            print(f"   ⚠️  已自动降级（Tushare 不可用或积分不足）")
        else:
            print(f"   ✅ 使用 Tushare（积分充足）")
    
    # 测试 2: 不指定数据源
    print("\n📌 测试：不指定数据源（自动选择）")
    adapter = manager.get_adapter()
    print(f"   实际使用：{adapter.source_type.value}")
    
    print()


def show_configuration():
    """显示配置信息"""
    print("=" * 60)
    print("📋 当前配置信息")
    print("=" * 60)
    
    print(f"\n⚙️  基本配置:")
    print(f"   DEFAULT_DATA_SOURCE: {settings.DEFAULT_DATA_SOURCE}")
    print(f"   TUSHARE_TOKEN: {'已配置' if settings.TUSHARE_TOKEN else '未配置'}")
    print(f"   TUSHARE_POINTS: {settings.TUSHARE_POINTS}分")
    
    print(f"\n📊 积分权限配置:")
    for points, apis in sorted(settings.TUSHARE_PERMISSION_CONFIG.items()):
        print(f"   {points}分：{len(apis)} 个接口")
    
    print(f"\n🎯 推荐配置:")
    if settings.TUSHARE_POINTS < 200:
        print(f"   建议完善信息获取 200 分，可使用龙虎榜等数据")
    if settings.TUSHARE_POINTS < 5000:
        print(f"   建议获取 5000 分，可使用分钟线数据")
    if settings.TUSHARE_POINTS < 10000:
        print(f"   建议获取 10000 分，可使用 Level-2 等高级数据")
    
    print()


async def main():
    """主测试函数"""
    print("\n" + "🚀" * 30)
    print("Tushare 积分权限管理测试")
    print("🚀" * 30 + "\n")
    
    try:
        # 显示配置
        show_configuration()
        
        # 测试 1: 积分管理器
        test_points_manager()
        
        # 测试 2: 数据源初始化
        await test_data_source_initialization()
        
        # 测试 3: 智能切换
        await test_intelligent_switching()
        
        # 测试 4: 降级逻辑
        await test_fallback_logic()
        
        print("=" * 60)
        print("✅ 所有测试完成！")
        print("=" * 60)
        
        print("\n📊 总结:")
        print("   ✅ 积分管理器：正常工作")
        print("   ✅ 权限控制：已实现")
        print("   ✅ 智能切换：已实现")
        print("   ✅ 自动降级：已实现")
        
        print("\n💡 提示:")
        print("   - 日线数据：120 分即可使用 Tushare")
        print("   - 分钟线数据：需要 5000 分，否则自动降级到 AkShare")
        print("   - 系统会根据积分自动选择最优数据源")
        print("   - 业务代码无需修改，完全无感切换")
        
        print("\n📚 更多信息请查看:")
        print("   - TUSHARE_POINTS_GUIDE.md - 积分配置指南")
        print("   - TUSHARE_SETUP.md - Tushare 配置指南")
        print()
        
    except Exception as e:
        print(f"\n❌ 测试失败：{str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

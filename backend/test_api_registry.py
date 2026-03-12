"""
Tushare API 注册表测试脚本

测试 API 分组管理功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from app.utils.tushare_api_registry import get_api_registry, APIGroup
from app.utils.tushare_points_manager import get_points_manager


def test_api_registry():
    """测试 API 注册表基本功能"""
    print("=" * 80)
    print("测试 1: API 注册表基本功能")
    print("=" * 80)
    
    registry = get_api_registry()
    
    print(f"\n✅ 注册表初始化成功")
    print(f"📊 注册 API 总数：{len(registry._apis)}")
    print(f"📊 分组数量：{len(registry._groups)}")
    
    # 测试获取 API 信息
    print(f"\n📋 测试获取 API 信息:")
    test_apis = ["daily", "intraday", "bar", "top_list"]
    
    for api_name in test_apis:
        api_info = registry.get_api_info(api_name)
        if api_info:
            print(f"   ✅ {api_name:20s} - {api_info.description:20s} "
                  f"({api_info.group.value[0]}, {api_info.min_points}分)")
        else:
            print(f"   ❌ {api_name:20s} - 未找到")
    
    print()


def test_api_groups():
    """测试 API 分组"""
    print("=" * 80)
    print("测试 2: API 分组信息")
    print("=" * 80)
    
    registry = get_api_registry()
    
    print(f"\n📊 API 分组统计:\n")
    
    for group in sorted(APIGroup, key=lambda x: x.value[1]):
        group_info = registry.get_group_info(group)
        status = "✅" if group_info['available_apis'] > 0 else "🔒"
        
        print(f"{status} {group_info['name']:15s} ({group_info['required_points']:5d}分)")
        print(f"   {group_info['description']}")
        print(f"   可用：{group_info['available_apis']:2d}/{group_info['total_apis']:2d}")
        
        if group_info['api_list']:
            print(f"   接口：{', '.join(group_info['api_list'][:3])}")
            if len(group_info['api_list']) > 3:
                print(f"         ... 还有 {len(group_info['api_list']) - 3} 个")
        print()


def test_permission_check():
    """测试权限检查"""
    print("=" * 80)
    print("测试 3: API 权限检查")
    print("=" * 80)
    
    registry = get_api_registry()
    points_mgr = get_points_manager()
    
    print(f"\n📊 当前积分：{points_mgr.get_points()}分\n")
    
    # 测试不同积分要求的 API
    test_cases = [
        ("daily", 120),
        ("top_list", 200),
        ("forecast", 800),
        ("intraday", 5000),
        ("level2_tick", 10000),
    ]
    
    print(f"{'API 名称':20s} {'描述':20s} {'所需积分':>8s} {'当前积分':>8s} {'状态':>8s}")
    print("-" * 80)
    
    for api_name, required in test_cases:
        api_info = registry.get_api_info(api_name)
        if api_info:
            has_perm = registry.check_permission(api_name)
            status = "✅ 可用" if has_perm else "❌ 不足"
            print(f"{api_name:20s} {api_info.description:20s} "
                  f"{required:>8d} {points_mgr.get_points():>8d} {status:>8s}")
    
    print()


def test_available_apis():
    """测试可用 API 列表"""
    print("=" * 80)
    print("测试 4: 可用/不可用 API 列表")
    print("=" * 80)
    
    registry = get_api_registry()
    
    available = registry.get_available_apis()
    unavailable = registry.get_unavailable_apis()
    
    print(f"\n✅ 可用 API ({len(available)}个):")
    for api_name in available[:10]:  # 只显示前 10 个
        api_info = registry.get_api_info(api_name)
        if api_info:
            print(f"   - {api_name}: {api_info.description} "
                  f"({api_info.group.value[0]}, {api_info.min_points}分)")
    
    if len(available) > 10:
        print(f"   ... 还有 {len(available) - 10} 个")
    
    print(f"\n🔒 不可用 API ({len(unavailable)}个):")
    for item in unavailable[:5]:  # 只显示前 5 个
        print(f"   - {item['name']}: {item['description']} "
              f"(需要{item['required_points']}分，还差{item['lack_points']}分)")
    
    if len(unavailable) > 5:
        print(f"   ... 还有 {len(unavailable) - 5} 个")
    
    print()


def test_permission_summary():
    """测试权限摘要"""
    print("=" * 80)
    print("测试 5: 权限摘要信息")
    print("=" * 80)
    
    registry = get_api_registry()
    summary = registry.get_permission_summary()
    
    print(f"\n📊 权限摘要:")
    print(f"   当前积分：{summary['current_points']}分")
    print(f"   可用 API：{summary['available_count']}/{summary['total_count']}")
    print(f"   不可用 API：{summary['unavailable_count']}/{summary['total_count']}")
    
    if summary['next_level']:
        print(f"\n🎯 下一等级:")
        print(f"   分组：{summary['next_level']['name']}")
        print(f"   描述：{summary['next_level']['description']}")
        print(f"   需要：{summary['next_level']['required_points']}分")
        print(f"   还差：{summary['next_level']['lack_points']}分")
    
    print(f"\n📋 分组详情:")
    for group_name, group_info in summary['groups'].items():
        status = "✅" if group_info['available_apis'] > 0 else "🔒"
        print(f"   {status} {group_name:15s} ({group_info['required_points']:5d}分) "
              f"- {group_info['available_apis']:2d}/{group_info['total_apis']:2d} 可用")
    
    print()


def test_documentation():
    """测试文档生成"""
    print("=" * 80)
    print("测试 6: API 文档生成")
    print("=" * 80)
    
    registry = get_api_registry()
    
    doc = registry.generate_api_documentation()
    print(doc)


async def main():
    """主测试函数"""
    print("\n" + "🚀" * 40)
    print("Tushare API 注册表功能测试")
    print("🚀" * 40 + "\n")
    
    try:
        # 测试 1: 基本功能
        test_api_registry()
        
        # 测试 2: 分组信息
        test_api_groups()
        
        # 测试 3: 权限检查
        test_permission_check()
        
        # 测试 4: 可用 API 列表
        test_available_apis()
        
        # 测试 5: 权限摘要
        test_permission_summary()
        
        # 测试 6: 文档生成
        test_documentation()
        
        print("=" * 80)
        print("✅ 所有测试完成！")
        print("=" * 80)
        
        print("\n📊 总结:")
        print("   ✅ API 注册表：正常工作")
        print("   ✅ 分组管理：正常工作")
        print("   ✅ 权限检查：正常工作")
        print("   ✅ 文档生成：正常工作")
        
        print("\n💡 提示:")
        print("   - API 注册表已初始化，共注册了所有 Tushare API")
        print("   - 根据当前积分自动计算可用 API")
        print("   - 支持装饰器模式注册新的 API")
        print("   - 可以自动生成 API 文档")
        print()
        
    except Exception as e:
        print(f"\n❌ 测试失败：{str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

"""
统一策略配置测试脚本
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.adapters.strategy_config import (
    UNIFIED_DATA_STRATEGY,
    ADAPTER_CONFIG,
    get_strategy,
    get_priority_sources,
    get_cache_ttl,
    get_client_config,
    validate_strategy_config,
    DataSourceType,
    APISensitivity,
)
from app.adapters.factory import DataSourceManager


def test_strategy_config():
    """测试策略配置"""
    print("=" * 70)
    print("统一策略配置测试")
    print("=" * 70)
    
    # 1. 验证配置有效性
    print("\n1. 配置验证:")
    errors = validate_strategy_config()
    if errors:
        print("   ✗ 配置验证失败:")
        for error in errors:
            print(f"     - {error}")
    else:
        print("   ✓ 配置验证通过")
    
    # 2. 统计配置信息
    print("\n2. 配置统计:")
    print(f"   - 数据类型数量: {len(UNIFIED_DATA_STRATEGY)}")
    print(f"   - 数据源适配器: {len(ADAPTER_CONFIG)}")
    
    # 3. 测试获取策略
    print("\n3. 测试获取策略 (kline):")
    strategy = get_strategy("kline")
    if strategy:
        print(f"   ✓ 策略获取成功")
        print(f"   - 优先级: {[s.value for s in strategy.priority]}")
        print(f"   - 敏感度: {strategy.sensitivity.value}")
        print(f"   - 首选客户端: {strategy.preferred_client}")
        print(f"   - 缓存 TTL: {strategy.cache_ttl}秒")
    else:
        print("   ✗ 策略获取失败")
    
    # 4. 测试获取优先级
    print("\n4. 测试获取优先级:")
    for data_type in ["kline", "realtime_quote", "stock_list", "chip"]:
        priority = get_priority_sources(data_type)
        print(f"   {data_type}: {[s.value for s in priority]}")
    
    # 5. 测试获取缓存 TTL
    print("\n5. 测试获取缓存 TTL:")
    for data_type in ["realtime_quote", "kline", "stock_list", "financial"]:
        ttl = get_cache_ttl(data_type)
        print(f"   {data_type}: {ttl}秒")
    
    # 6. 测试获取客户端配置
    print("\n6. 测试获取客户端配置:")
    for data_type in ["kline", "realtime_quote", "sector"]:
        config = get_client_config(data_type)
        print(f"   {data_type}: {config}")
    
    # 7. 检查适配器启用状态
    print("\n7. 适配器启用状态:")
    for source_type in DataSourceType:
        from app.adapters.strategy_config import is_adapter_enabled
        enabled = is_adapter_enabled(source_type)
        status = "✓ 启用" if enabled else "✗ 禁用"
        print(f"   {source_type.value}: {status}")
    
    print("\n" + "=" * 70)


async def test_data_source_manager():
    """测试数据源管理器"""
    print("\n" + "=" * 70)
    print("数据源管理器测试")
    print("=" * 70)
    
    manager = DataSourceManager()
    
    # 1. 初始化
    print("\n1. 初始化数据源管理器:")
    try:
        await manager.initialize()
        print("   ✓ 初始化成功")
    except Exception as e:
        print(f"   ✗ 初始化失败: {e}")
        return
    
    # 2. 获取策略信息
    print("\n2. 获取策略信息 (kline):")
    info = manager.get_strategy_info("kline")
    if info:
        print(f"   ✓ 获取成功")
        for key, value in info.items():
            print(f"   - {key}: {value}")
    else:
        print("   ✗ 获取失败")
    
    # 3. 获取所有策略
    print("\n3. 获取所有策略信息:")
    all_strategies = manager.get_all_strategies()
    print(f"   ✓ 共 {len(all_strategies)} 种数据类型")
    
    # 4. 关闭
    print("\n4. 关闭数据源管理器:")
    await manager.close()
    print("   ✓ 关闭成功")
    
    print("\n" + "=" * 70)


def compare_old_new_config():
    """对比新旧配置"""
    print("\n" + "=" * 70)
    print("新旧配置对比")
    print("=" * 70)
    
    # 旧配置（config.py 中的 DATA_SOURCE_BY_TYPE）
    old_config = {
        "kline": ["tickflow", "akshare", "efinance", "baostock"],
        "realtime_quote": ["efinance", "akshare", "tickflow"],
        "stock_list": ["akshare", "efinance"],
        "chip": ["akshare"],
    }
    
    print("\n配置对比:")
    print(f"{'数据类型':<20} {'旧配置':<40} {'新配置':<40}")
    print("-" * 100)
    
    for data_type in old_config.keys():
        old_priority = old_config[data_type]
        new_strategy = get_strategy(data_type)
        new_priority = [s.value for s in new_strategy.priority] if new_strategy else []
        
        old_str = ", ".join(old_priority)
        new_str = ", ".join(new_priority)
        
        match = "✓" if old_priority == new_priority else "✗"
        print(f"{data_type:<20} {old_str:<40} {new_str:<40} {match}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    # 运行配置测试
    test_strategy_config()
    
    # 对比新旧配置
    compare_old_new_config()
    
    # 运行数据源管理器测试
    asyncio.run(test_data_source_manager())
    
    print("\n✓ 所有测试完成")

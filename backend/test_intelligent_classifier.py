"""
智能数据分类器测试

测试智能分类器是否能正确判断：
1. 是否应该缓存
2. 应该使用哪个缓存层级
3. 应该设置什么 TTL
4. 是否需要持久化
"""
import asyncio
from app.storage.intelligent_classifier import (
    IntelligentDataClassifier,
    DataFreshness,
    AccessPattern,
    DataImportance,
    classify_data
)


def test_data_classifier():
    """测试数据分类器"""
    print("\n" + "="*70)
    print("智能数据分类器测试")
    print("="*70)
    
    # 测试各种数据类型
    test_cases = [
        # (数据类型，预期缓存层级，预期 TTL 范围)
        ("realtime_quote", "l1", 60),
        ("kline_daily", "l2", 1800),
        ("kline_minute", "l1", 300),
        ("indicators", "l2", 1800),
        ("sector", "l2", 1800),
        ("moneyflow", "l3", 3600),
        ("billboard", "l3", 3600),
        ("financial", "l3", 7200),
        ("stock_list", "l3", 3600),
    ]
    
    all_passed = True
    
    for data_type, expected_level, expected_ttl in test_cases:
        decision = IntelligentDataClassifier.classify(data_type)
        
        # 检查缓存层级
        level_match = decision.cache_level == expected_level
        
        # 检查 TTL（允许一定误差）
        ttl_match = abs(decision.ttl_seconds - expected_ttl) <= 600
        
        # 检查是否应该缓存
        should_cache = decision.should_cache
        
        # 检查是否应该持久化
        should_persist = decision.should_persist
        
        # 打印结果
        status = "✅" if (level_match and ttl_match) else "❌"
        print(f"\n{status} {data_type}:")
        print(f"   缓存层级：{decision.cache_level.upper()} (预期：{expected_level.upper()}) {'✅' if level_match else '❌'}")
        print(f"   TTL: {decision.ttl_seconds}s (预期：~{expected_ttl}s) {'✅' if ttl_match else '❌'}")
        print(f"   缓存：{'是' if should_cache else '否'}")
        print(f"   持久化：{'是' if should_persist else '否'}")
        print(f"   原因：{decision.reason}")
        
        if not (level_match and ttl_match):
            all_passed = False
    
    return all_passed


def test_custom_params():
    """测试自定义参数"""
    print("\n" + "="*70)
    print("自定义参数测试")
    print("="*70)
    
    # 测试 1: 强制 kline_daily 使用 L1 缓存
    print("\n📋 测试 1: 强制 kline_daily 使用 L1 缓存")
    decision = classify_data(
        'kline_daily',
        freshness='hot',
        access_pattern='frequent',
        importance='critical'
    )
    print(f"   缓存层级：{decision.cache_level.upper()}")
    print(f"   TTL: {decision.ttl_seconds}s")
    print(f"   原因：{decision.reason}")
    
    # 测试 2: 设置 billboard 为不缓存
    print("\n📋 测试 2: 设置 billboard 为可选数据（低频访问）")
    decision = classify_data(
        'billboard',
        access_pattern='rare',
        importance='optional'
    )
    print(f"   缓存：{'是' if decision.should_cache else '否'}")
    print(f"   缓存层级：{decision.cache_level.upper()}")
    print(f"   原因：{decision.reason}")
    
    # 测试 3: 实时行情设置为重要数据
    print("\n📋 测试 3: 实时行情设置为核心数据")
    decision = classify_data(
        'realtime_quote',
        importance='critical'
    )
    print(f"   缓存：{'是' if decision.should_cache else '否'}")
    print(f"   缓存层级：{decision.cache_level.upper()}")
    print(f"   TTL: {decision.ttl_seconds}s")
    print(f"   原因：{decision.reason}")


def test_all_data_types():
    """测试所有预定义的数据类型"""
    print("\n" + "="*70)
    print("所有数据类型遍历测试")
    print("="*70)
    
    profiles = IntelligentDataClassifier.DATA_PROFILES
    
    print(f"\n共 {len(profiles)} 种数据类型:\n")
    
    for data_type, profile in sorted(profiles.items()):
        decision = IntelligentDataClassifier.classify(data_type)
        
        print(f"📦 {data_type}:")
        print(f"   画像：新鲜度={profile.freshness.value}, 访问={profile.access_pattern.value}, 重要性={profile.importance.value}")
        print(f"   决策：缓存={decision.cache_level.upper()}, TTL={decision.ttl_seconds}s, 持久化={decision.persist_target}")
        print(f"   原因：{decision.reason}")
        print()


def main():
    """运行所有测试"""
    print("\n" + "="*70)
    print("智能数据分类器完整测试")
    print("="*70)
    
    # 测试 1: 基本分类
    test1_passed = test_data_classifier()
    
    # 测试 2: 自定义参数
    test_custom_params()
    
    # 测试 3: 遍历所有类型
    test_all_data_types()
    
    # 总结
    print("\n" + "="*70)
    print("测试总结")
    print("="*70)
    
    if test1_passed:
        print("\n✅ 所有测试通过！智能分类器工作正常")
        return True
    else:
        print("\n⚠️ 部分测试未通过，请检查")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

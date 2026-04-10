"""
验证分类系统重构 - 确保无回归
"""
import sys
import asyncio

def test_classification_module():
    """测试1: 验证 classification.py 模块导入和基本功能"""
    print("\n[TEST 1] 测试 classification 模块...")
    try:
        from app.storage.classification import (
            DataTier, UnifiedDataConfig, UNIFIED_DATA_CONFIGS,
            get_config, get_tier
        )
        print(f"  [OK] 成功导入 classification 模块")

        # 测试 DataTier 枚举
        assert DataTier.REALTIME.key == "realtime"
        assert DataTier.HOT.key == "hot"
        assert DataTier.WARM.key == "warm"
        assert DataTier.COLD.key == "cold"
        assert DataTier.ARCHIVED.key == "archived"
        print(f"  [OK] DataTier 枚举值正确 (5个层级)")

        # 测试 DataTier 属性
        assert DataTier.REALTIME.priority == 0
        assert DataTier.REALTIME.default_ttl == 60
        assert DataTier.HOT.default_ttl == 300
        print(f"  [OK] DataTier 属性正确")

        # 测试 UNIFIED_DATA_CONFIGS
        assert len(UNIFIED_DATA_CONFIGS) >= 10  # 至少有10种数据类型配置
        assert "kline" in UNIFIED_DATA_CONFIGS
        assert "realtime" in UNIFIED_DATA_CONFIGS
        print(f"  [OK] UNIFIED_DATA_CONFIGS 包含 {len(UNIFIED_DATA_CONFIGS)} 种数据类型")

        # 测试 get_config
        config = get_config("kline")
        assert config.tier == DataTier.HOT
        assert config.ttl == 300
        assert config.max_cache_size == 1000
        print(f"  [OK] get_config('kline') 返回正确: tier=HOT, ttl=300, size=1000")

        # 测试 get_tier
        tier = get_tier("realtime")
        assert tier == DataTier.REALTIME
        print(f"  [OK] get_tier('realtime') = REALTIME")

        # 测试 DataTier.from_access_rate
        assert DataTier.from_access_rate(600) == DataTier.HOT
        assert DataTier.from_access_rate(200) == DataTier.WARM
        assert DataTier.from_access_rate(50) == DataTier.COLD
        print(f"  [OK] DataTier.from_access_rate() 正确")

        # 测试 DataTier.from_age_days
        assert DataTier.from_age_days(0) == DataTier.REALTIME
        assert DataTier.from_age_days(50) == DataTier.HOT
        assert DataTier.from_age_days(400) == DataTier.WARM
        assert DataTier.from_age_days(1000) == DataTier.COLD
        assert DataTier.from_age_days(2000) == DataTier.ARCHIVED
        print(f"  [OK] DataTier.from_age_days() 正确")

        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_storage_service():
    """测试2: 验证 storage_service.py 重构后功能正常"""
    print("\n[TEST 2] 测试 storage_service...")
    try:
        from app.storage.storage_service import UnifiedStorageService, StorageDecision

        service = UnifiedStorageService()

        # 测试 classify_data（使用新的统一分类）
        decision = service.classify_data("kline")
        assert isinstance(decision, StorageDecision)
        assert decision.should_cache == True
        assert decision.ttl_seconds == 300
        print(f"  [OK] classify_data('kline'): cache={decision.should_cache}, ttl={decision.ttl_seconds}")

        decision = service.classify_data("realtime")
        assert decision.cache_level == "l1"
        assert decision.ttl_seconds == 60
        print(f"  [OK] classify_data('realtime'): level=l1, ttl={decision.ttl_seconds}")

        decision = service.classify_data("backtest")
        assert decision.cache_level == "l3"
        print(f"  [OK] classify_data('backtest'): level=l3")

        # 测试未知类型默认值
        decision = service.classify_data("unknown_type")
        assert decision.should_cache == True
        print(f"  [OK] classify_data('unknown_type') 使用默认值")

        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_hot_spot_tracker():
    """测试3: 验证 hot_spot_tracker.py 使用 DataTier"""
    print("\n[TEST 3] 测试 hot_spot_tracker...")
    try:
        from app.storage.hot_spot_tracker import HotSpotTracker, HotStockInfo
        from app.storage.classification import DataTier

        tracker = HotSpotTracker()

        # 记录访问
        for _ in range(600):  # >500 次，应该被分类为 HOT
            tracker.record_access("000001", "read")

        # 获取层级
        tier = tracker.get_tier("000001")
        assert tier == DataTier.HOT, f"Expected HOT, got {tier}"
        print(f"  [OK] get_tier('000001') = HOT (600次访问)")

        # 测试动态 TTL
        ttl = tracker.get_dynamic_ttl("000001", base_ttl=60)
        assert ttl == int(60 * 0.3), f"Expected 18, got {ttl}"
        print(f"  [OK] get_dynamic_ttl() = {ttl}s (HOT x0.3)")

        # 测试优先级
        priority = tracker.get_priority("000001")
        assert priority == 0, f"Expected 0, got {priority}"
        print(f"  [OK] get_priority() = {priority} (HOT最高)")

        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_partition_manager():
    """测试4: 验证 data_partition_manager.py 使用 DataTier"""
    print("\n[TEST 4] 测试 data_partition_manager...")
    try:
        from app.storage.data_partition_manager import (
            DataPartitionManager, PartitionRule, PartitionStats,
            DEFAULT_PARTITION_RULES
        )
        from app.storage.classification import DataTier

        # 验证 DEFAULT_PARTITION_RULES 使用 DataTier
        assert len(DEFAULT_PARTITION_RULES) == 5
        assert DEFAULT_PARTITION_RULES[0].tier == DataTier.REALTIME
        assert DEFAULT_PARTITION_RULES[1].tier == DataTier.HOT
        assert DEFAULT_PARTITION_RULES[2].tier == DataTier.WARM
        assert DEFAULT_PARTITION_RULES[3].tier == DataTier.COLD
        assert DEFAULT_PARTITION_RULES[4].tier == DataTier.ARCHIVED
        print(f"  [OK] DEFAULT_PARTITION_RULES 使用 DataTier (5条规则)")

        # 测试 get_partition_for_data
        manager = DataPartitionManager()

        tier = manager.get_partition_for_data("2026-04-10")  # 今天
        assert tier == DataTier.REALTIME, f"Expected REALTIME, got {tier}"
        print(f"  [OK] get_partition_for_data('2026-04-10') = REALTIME")

        tier = manager.get_partition_for_data("2025-12-01")  # ~130天前 -> WARM
        assert tier == DataTier.WARM, f"Expected WARM, got {tier}"
        print(f"  [OK] get_partition_for_data('2025-12-01') = WARM")

        tier = manager.get_partition_for_data("2020-01-01")  # 多年前
        assert tier == DataTier.ARCHIVED, f"Expected ARCHIVED, got {tier}"
        print(f"  [OK] get_partition_for_data('2020-01-01') = ARCHIVED")

        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cache_integration():
    """测试5: 验证 cache.py 和 cache_service.py 从 UNIFIED_DATA_CONFIGS 初始化"""
    print("\n[TEST 5] 测试缓存集成...")
    try:
        from app.storage.cache import CacheManager
        from app.services.cache_service import CacheService
        from app.storage.classification import UNIFIED_DATA_CONFIGS

        # 测试 CacheManager 初始化
        cm = CacheManager()
        cache_types = list(cm._caches.keys())

        # 应该包含 UNIFIED_DATA_CONFIGS 中的所有类型
        config_types = set(UNIFIED_DATA_CONFIGS.keys())
        cache_set = set(cache_types)

        missing = config_types - cache_set
        extra = cache_set - config_types

        assert len(missing) == 0, f"CacheManager 缺少类型: {missing}"
        print(f"  [OK] CacheManager._caches 包含所有 {len(cache_types)} 种类型")

        # 验证配置一致性
        for data_type in ["kline", "realtime", "sector"]:
            expected_ttl = UNIFIED_DATA_CONFIGS[data_type].ttl
            actual_cache = cm.get_cache(data_type)
            assert actual_cache.ttl == expected_ttl, \
                f"{data_type}: expected TTL={expected_ttl}, got {actual_cache.ttl}"
        print(f"  [OK] CacheManager TTL 与 UNIFIED_DATA_CONFIGS 一致")

        # 测试 CacheService 初始化
        cs = CacheService()
        assert len(cs.cache_config) == len(UNIFIED_DATA_CONFIGS)
        print(f"  [OK] CacheService.cache_config 包含 {len(cs.cache_config)} 个配置")

        # 验证 sector TTL 已修复为 3600
        assert cs.cache_config["sector"]["ttl"] == 3600
        print(f"  [OK] sector TTL = 3600 (bug已修复)")

        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_compareop_cleanup():
    """测试6: 验证 CompareOperator 已删除"""
    print("\n[TEST 6] 测试 CompareOp 清理...")
    try:
        # 尝试导入旧的 CompareOperator（应该失败）
        try:
            from app.services.screener_service import CompareOperator
            print(f"  [FAIL] CompareOperator 仍然存在（应已删除）")
            return False
        except (ImportError, AttributeError):
            print(f"  [OK] CompareOperator 已成功删除")

        # 验证 CompareOp 仍然存在
        from app.storage.batch_screener import CompareOp
        assert CompareOp.GT.value == ">"
        assert CompareOp.LT.value == "<"
        print(f"  [OK] CompareOp 仍然可用 ({len(CompareOp)} 个操作符)")

        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """运行所有测试"""
    print("=" * 60)
    print("  分类系统重构验证测试")
    print("=" * 60)

    results = []

    results.append(("classification模块", test_classification_module()))
    results.append(("storage_service", test_storage_service()))
    results.append(("hot_spot_tracker", test_hot_spot_tracker()))
    results.append(("data_partition_manager", test_data_partition_manager()))
    results.append(("cache集成", test_cache_integration()))
    results.append(("CompareOp清理", test_compareop_cleanup()))

    print("\n" + "=" * 60)
    print("  测试结果汇总")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {name}")

    print(f"\n  总计: {passed}/{total} 通过")

    if passed == total:
        print("\n  所有测试通过! 重构成功完成。")
        return 0
    else:
        print(f"\n  {total - passed} 个测试失败，需要修复。")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

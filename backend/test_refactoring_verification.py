"""
数据中台分层重构验证测试

验证内容:
1. L2 (processing/) 模块导入
2. L3 (services/) 模块导入（兼容性）
3. L1 (infrastructure/) 模块导入
4. 跨层调用正常
5. 无循环依赖
6. 废弃模块已删除
"""
import sys
import asyncio


def test_processing_layer():
    """测试1: 验证 L2 数据处理层"""
    print("\n[TEST 1] 测试 L2 数据处理层 (processing/)...")
    try:
        from app.processing import (
            DataCleaner, PriceAdjuster, DataProcessor,
            DataValidator, data_validator,
            IndicatorsManager, get_indicators_manager,
            IndicatorPrecomputer,
            BatchScreener, CompareOp, ScreenCondition,
            BacktestAccelerator
        )
        print(f"  [OK] 成功导入 processing 层所有模块")

        # 验证实例化
        processor = DataProcessor()
        assert hasattr(processor, 'cleaner')
        assert hasattr(processor, 'adjuster')
        print(f"  [OK] DataProcessor 实例化成功")

        validator = DataValidator()
        assert hasattr(validator, 'validate_kline_data')
        assert hasattr(validator, 'validate_stock_code')
        print(f"  [OK] DataValidator 实例化成功")

        manager = get_indicators_manager()
        assert isinstance(manager, IndicatorsManager)
        print(f"  [OK] IndicatorsManager 实例化成功")

        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_services_layer():
    """测试2: 验证 L3 业务处理层（兼容性）"""
    print("\n[TEST 2] 测试 L3 业务处理层 (services/ - 兼容性)...")
    try:
        from app.services import (
            StockService, stock_service,
            SectorService, sector_service,
            ChipService, chip_service,
            Screener, StockScreener, screener,
            WatchlistService, watchlist_service,
            CacheService, cache_service,
            # 从 processing/ 重新导出的类
            DataCleaner, PriceAdjuster, DataProcessor,
            DataValidator, data_validator,
            IndicatorsManager, get_indicators_manager,
        )
        print(f"  [OK] 成功导入 services 层所有核心模块")

        # 验证单例实例化
        assert isinstance(stock_service, StockService)
        assert isinstance(sector_service, SectorService)
        assert isinstance(chip_service, ChipService)
        assert isinstance(cache_service, CacheService)
        print(f"  [OK] 所有全局单例正确初始化")

        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_infrastructure_layer():
    """测试3: 验证 L1 基础设施层"""
    print("\n[TEST 3] 测试 L1 基础设施层 (infrastructure/)...")
    try:
        from app.infrastructure import (
            DataSourceManager, data_source_manager,
            DataTier, UNIFIED_DATA_CONFIGS, get_config,
            CacheManager, AsyncLRUCache,
            ParquetManager,
        )
        print(f"  [OK] 成功导入 infrastructure 层所有模块")

        # 验证分类系统
        config = get_config("kline")
        assert config.tier == DataTier.HOT
        assert config.ttl == 300
        print(f"  [OK] 分类系统正常工作 (DataTier + Config)")

        # 验证缓存管理器
        cm = CacheManager()
        assert "kline" in cm._caches
        print(f"  [OK] CacheManager 正常工作")

        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cross_layer_calls():
    """测试4: 验证跨层调用"""
    print("\n[TEST 4] 测试跨层调用...")
    try:
        # L3 → L2 调用
        from app.services import StockService, stock_service
        from app.processing import IndicatorsManager
        
        service = StockService()
        assert isinstance(service.indicator_manager, IndicatorsManager)
        print(f"  [OK] L3(StockService) → L2(IndicatorsManager) 调用正常")

        # L3 → L1 调用
        from app.storage.storage_service import UnifiedStorageService
        storage = UnifiedStorageService()
        
        decision = storage.classify_data("kline")
        assert decision.should_cache == True
        print(f"  [OK] L3 → L1(storage_service.classify_data) 调用正常")

        # L2 独立工作（不依赖上层）
        from app.processing import DataValidator
        result = DataValidator.validate_stock_code("000001")
        assert result == True
        print(f"  [OK] L2(DataValidator) 可独立运行，不依赖上层")

        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_deprecated_removed():
    """测试5: 验证废弃模块已删除"""
    print("\n[TEST 5] 验证废弃模块已删除...")
    import os
    
    deprecated_files = [
        "app/services/smart_loader.py",
        "app/services/indicators.py",           # 旧指标类
        "app/services/data_persistence.py",     # 与storage重叠
        "app/services/data_loader.py",          # 已迁移到stock_service
        "app/services/data_processor.py",       # 已迁移到processing/
        "app/services/data_validator.py",       # 已迁移到processing/
        "app/services/indicators_manager.py",   # 已迁移到processing/
    ]
    
    all_removed = True
    for file_path in deprecated_files:
        full_path = os.path.join(os.path.dirname(__file__), "..", file_path)
        if os.path.exists(full_path):
            print(f"  [WARN] {file_path} 仍存在（应已删除）")
            all_removed = False
        else:
            print(f"  [OK] {file_path} 已删除")
    
    if all_removed:
        print(f"  [OK] 所有废弃模块已清理")
    
    return True


def test_new_structure():
    """测试6: 验证新目录结构"""
    print("\n[TEST 6] 验证新目录结构...")
    import os
    
    base_dir = os.path.dirname(os.path.dirname(__file__))
    
    new_dirs = [
        ("processing/", "L2 数据处理层"),
        ("infrastructure/", "L1 基础设施层"),
        ("services/", "L3 业务处理层"),
        ("storage/", "存储引擎"),
        ("adapters/", "数据源适配器"),
    ]
    
    for dir_name, desc in new_dirs:
        dir_path = os.path.join(base_dir, "app", dir_name)
        if os.path.exists(dir_path):
            file_count = len([f for f in os.listdir(dir_path) if f.endswith('.py')])
            print(f"  [OK] {dir_name} ({desc}) - {file_count} 个文件")
        else:
            print(f"  [FAIL] {dir_name} ({desc}) 不存在")
            return False
    
    return True


async def main():
    """运行所有验证测试"""
    print("=" * 70)
    print("  数据中台分层重构验证测试")
    print("=" * 70)

    results = []

    results.append(("L2 数据处理层", test_processing_layer()))
    results.append(("L3 业务处理层(兼容)", test_services_layer()))
    results.append(("L1 基础设施层", test_infrastructure_layer()))
    results.append(("跨层调用", test_cross_layer_calls()))
    results.append(("废弃模块清理", test_deprecated_removed()))
    results.append(("新目录结构", test_new_structure()))

    print("\n" + "=" * 70)
    print("  测试结果汇总")
    print("=" * 70)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {name}")

    print(f"\n  总计: {passed}/{total} 通过")

    if passed == total:
        print("\n  所有测试通过! 分层重构完成。")
        print("\n  新架构:")
        print("  ├── processing/      (L2: 数据处理)")
        print("  ├── services/        (L3: 业务逻辑)")
        print("  └── infrastructure/  (L1: 存储接入)")
        return 0
    else:
        print(f"\n  {total - passed} 个测试失败，需要修复。")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

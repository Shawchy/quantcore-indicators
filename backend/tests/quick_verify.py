"""
快速验证脚本 - 验证所有新模块是否正常工作
"""

import asyncio
import sys
import os

# 设置UTF-8编码（解决Windows控制台问题）
os.environ["PYTHONIOENCODING"] = "utf-8"

async def quick_test():
    print("=" * 60)
    print("SMART POLLING SYSTEM - QUICK VERIFICATION")
    print("=" * 60)
    
    all_passed = True
    
    # Test 1: SmartPollingService
    print("\n[1/4] Testing SmartPollingService...")
    try:
        from app.services.smart_polling import SmartPollingService
        
        service = SmartPollingService()
        
        # 市场状态
        state = service.get_market_state()
        assert state is not None, "Market state should not be None"
        print(f"  ✓ Market state: {state.value}")
        
        # 轮询间隔
        interval = service.get_optimal_interval("normal")
        assert 10 <= interval <= 200, f"Interval {interval} out of range"
        print(f"  ✓ Optimal interval (normal): {interval}s")
        
        # 批量获取
        result = await service.get_realtime_batch(
            codes=["000001", "600000"],
            user_tier="premium"
        )
        assert result["success"], "Batch fetch should succeed"
        assert len(result["data"]) == 2, "Should get 2 stocks"
        print(f"  ✓ Batch fetch: {len(result['data'])} stocks")
        
        print("[PASS] SmartPollingService\n")
        
    except Exception as e:
        print(f"[FAIL] SmartPollingService: {e}\n")
        all_passed = False
    
    # Test 2: IncrementalUpdateService
    print("[2/4] Testing IncrementalUpdateService...")
    try:
        from app.services.incremental_update import IncrementalUpdateService
        
        updater = IncrementalUpdateService()
        
        old_data = {"000001": {"price": 12.50, "volume": 1000}}
        new_data = {"000001": {"price": 12.55, "volume": 1100}}
        
        delta = updater.compute_delta(old_data, new_data)
        assert delta["total_changes"] > 0, "Should detect changes"
        print(f"  ✓ Delta detected: {delta['total_changes']} changes")
        
        compact = updater.export_delta_for_frontend(delta)
        assert len(compact) > 0, "Compact JSON should not be empty"
        print(f"  ✓ Compact export: {len(compact)} bytes")
        
        print("[PASS] IncrementalUpdateService\n")
        
    except Exception as e:
        print(f"[FAIL] IncrementalUpdateService: {e}\n")
        all_passed = False
    
    # Test 3: HierarchicalCache
    print("[3/4] Testing HierarchicalCache...")
    try:
        from app.services.hierarchical_cache import (
            HierarchicalCache,
            CacheLevel,
            DataType
        )
        
        cache = HierarchicalCache()
        
        # 写入和读取
        test_key = "test_key_123"
        test_val = {"code": "000001", "price": 12.50}
        
        await cache.set(test_key, test_val, DataType.REALTIME_HOTSPOT)
        retrieved = await cache.get(test_key, CacheLevel.L1)
        
        assert retrieved is not None, "L1 cache should return data"
        assert retrieved["code"] == "000001", "Data mismatch"
        print(f"  ✓ L1 cache write/read OK")
        
        # get_or_set with caching
        call_count = 0
        async def fetch_func():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)
            return {"test": "data"}
        
        key2 = cache.generate_cache_key("test", id="abc")
        data1, src1 = await cache.get_or_set(key2, DataType.REALTIME_NORMAL, fetch_func)
        data2, src2 = await cache.get_or_set(key2, DataType.REALTIME_NORMAL, fetch_func)
        
        assert src1 == "fresh", "First call should be fresh"
        assert src2 == "l1_hit", "Second call should hit L1"
        assert call_count == 1, f"Fetch should be called once, got {call_count}"
        print(f"  ✓ get_or_set caching works (fetch called: {call_count}x)")
        
        # 统计信息
        stats = cache.get_statistics()
        assert "hit_rate" in stats, "Stats missing hit_rate"
        print(f"  ✓ Statistics available: {len(stats)} metrics")
        
        print("[PASS] HierarchicalCache\n")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[FAIL] HierarchicalCache: {e}\n")
        all_passed = False
    
    # Test 4: AntiScrapingRules
    print("[4/4] Testing AntiScrapingRules...")
    try:
        from app.utils.anti_scraping_rules import AntiScrapingRules, RiskLevel
        
        safety = AntiScrapingRules()
        
        # 规则检查
        status = safety.check_before_request("efinance")
        assert status.is_safe, "EFinance should be safe initially"
        assert isinstance(status.risk_level, RiskLevel), "Risk level should be RiskLevel enum"
        print(f"  ✓ Safety check passed (risk: {status.risk_level.value})")
        
        # User-Agent轮换
        uas = [safety.get_user_agent("efinance") for _ in range(20)]
        unique_uas = len(set(uas))
        assert unique_uas > 1, "Should have multiple UAs"
        print(f"  ✓ UA rotation works ({unique_uas} unique)")
        
        # Interval calculation
        intervals = [safety.get_optimal_interval("akshare") for _ in range(10)]
        has_variance = max(intervals) != min(intervals)
        assert has_variance, "Intervals should vary"
        print(f"  ✓ Interval randomization OK (range: {min(intervals):.1f}-{max(intervals):.1f}s)")
        
        # Cooling mechanism
        for _ in range(5):
            safety.record_request("yfinance", "/fail", False)
        cooldown_status = safety.check_before_request("yfinance")
        assert not cooldown_status.is_safe or cooldown_status.cooldown_until is not None
        print(f"  ✓ Cooldown mechanism active")
        
        print("[PASS] AntiScrapingRules\n")
        
    except Exception as e:
        print(f"[FAIL] AntiScrapingRules: {e}\n")
        all_passed = False
    
    # Summary
    print("=" * 60)
    if all_passed:
        print("✓ ALL MODULES VERIFIED SUCCESSFULLY!")
        print("=" * 60)
        return 0
    else:
        print("✗ SOME TESTS FAILED - CHECK OUTPUT ABOVE")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(quick_test())
    sys.exit(exit_code)

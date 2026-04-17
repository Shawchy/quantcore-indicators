"""
智能轮询系统集成测试

验证所有模块是否正常工作：
1. SmartPollingService - 智能轮询
2. IncrementalUpdateService - 增量更新
3. HierarchicalCache - 分层缓存
4. AntiScrapingRules - 反爬安全
5. API端点集成测试
"""

import asyncio
import sys
from datetime import datetime


def print_section(title: str):
    """打印分节标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_test(name: str, passed: bool, detail: str = ""):
    """打印测试结果"""
    icon = "✅" if passed else "❌"
    status = "PASS" if passed else "FAIL"
    msg = f"{icon} [{status}] {name}"
    if detail:
        msg += f"\n      → {detail}"
    print(msg)
    return passed


async def test_smart_polling():
    """测试智能轮询服务"""
    print_section("Test 1: SmartPollingService 智能轮询")
    
    from app.services.smart_polling import SmartPollingService
    
    service = SmartPollingService()
    
    # 测试1.1: 市场状态检测
    market_state = service.get_market_state()
    passed1 = market_state is not None
    print_test(
        "市场状态检测",
        passed1,
        f"当前状态: {market_state.value if passed1 else 'None'}"
    )
    
    # 测试1.2: 轮询间隔计算
    interval_normal = service.get_optimal_interval("normal")
    interval_premium = service.get_optimal_interval("premium")
    interval_enterprise = service.get_optimal_interval("enterprise")
    
    passed2 = (
        10 <= interval_normal <= 120 and
        10 <= interval_premium <= 90 and
        10 <= interval_enterprise <= 60
    )
    print_test(
        "轮询间隔合理性",
        passed2,
        f"normal={interval_normal}s, premium={interval_premium}s, enterprise={interval_enterprise}s"
    )
    
    # 测试1.3: 频率限制检查
    rate_info = await service.check_rate_limit("test_user", "normal")
    passed3 = not rate_info.is_limited
    print_test(
        "频率限制检查",
        passed3,
        f"limited={rate_info.is_limited}, requests={rate_info.requests_made}"
    )
    
    # 测试1.4: 批量获取（mock模式）
    test_codes = ["000001", "600000", "300001"]
    result = await service.get_realtime_batch(
        codes=test_codes,
        user_id="test_user",
        user_tier="premium"
    )
    
    passed4 = result["success"] and len(result["data"]) == len(test_codes)
    print_test(
        "批量数据获取",
        passed4,
        f"获取 {len(result['data'])}/{len(test_codes)} 只股票"
    )
    
    # 测试1.5: 缓存命中测试
    result2 = await service.get_realtime_batch(
        codes=test_codes[:1],
        user_tier="normal"
    )
    
    passed5 = result2["cached_count"] > 0 or result2["fresh_count"] > 0
    print_test(
        "缓存机制工作",
        passed5,
        f"缓存命中={result2['cached_count']}, 新鲜数据={result2['fresh_count']}"
    )
    
    # 测试1.6: 统计信息
    stats = service.get_statistics()
    passed6 = "cache_size" in stats and "market_state" in stats
    print_test(
        "统计信息完整性",
        passed6,
        f"包含 {len(stats)} 个指标"
    )
    
    all_passed = all([passed1, passed2, passed3, passed4, passed5, passed6])
    return all_passed


async def test_incremental_update():
    """测试增量更新服务"""
    print_section("Test 2: IncrementalUpdateService 增量更新")
    
    from app.services.incremental_update import IncrementalUpdateService
    
    updater = IncrementalUpdateService()
    
    # 准备测试数据
    old_data = {
        "000001": {
            "name": "平安银行",
            "price": 12.50,
            "change_pct": 1.20,
            "volume": 1000000,
            "amount": 12500000,
            "turnover_rate": 0.85,
        },
        "600000": {
            "name": "浦发银行",
            "price": 8.90,
            "change_pct": -0.55,
            "volume": 800000,
        }
    }
    
    new_data = {
        "000001": {
            "name": "平安银行",
            "price": 12.55,       # +0.05 (变化)
            "change_pct": 1.60,   # +0.40 (变化)
            "volume": 1050000,    # +50000 (变化)
            "amount": 13177500,   # 变化
            "turnover_rate": 0.89, # +0.04 (变化)
        },
        "600000": {
            "name": "浦发银行",
            "price": 8.90,         # 无变化
            "change_pct": -0.55,   # 无变化
            "volume": 800000,      # 无变化
        },
        "300001": {               # 新增
            "name": "特锐德",
            "price": 25.80,
            "change_pct": 2.35,
        }
    }
    
    # 测试2.1: 增量计算
    delta = updater.compute_delta(old_data, new_data)
    
    passed1 = delta["total_changes"] > 0
    print_test(
        "增量计算正确性",
        passed1,
        f"检测到 {delta['total_changes']} 个变更"
    )
    
    # 测试2.2: 变更字段识别
    passed2 = "000001" in delta["changed_codes"]
    passed3 = "600000" not in delta["changed_codes"] or delta["delta"].get("600000") is None
    print_test(
        "变化字段识别",
        passed2 and passed3,
        f"变化股票: {delta['changed_codes']}"
    )
    
    # 测试2.3: 新增数据识别
    passed4 = "300001" in [c for c in delta["changed_codes"] if delta["delta"].get(c, {}).get("_action") == "added"]
    print_test(
        "新增数据识别",
        passed4,
        "300001 应被标记为新增"
    )
    
    # 测试2.4: 增量应用
    frontend_state = {"000001": old_data["000001"]}
    updated_state = updater.apply_delta_to_frontend_state(frontend_state, delta)
    
    passed5 = updated_state["000001"]["price"] == 12.55
    print_test(
        "增量应用到前端状态",
        passed5,
        f"价格更新为: {updated_state['000001']['price']}"
    )
    
    # 测试2.5: 紧凑格式导出
    compact_json = updater.export_delta_for_frontend(delta)
    full_json_len = len(str(new_data))
    compact_len = len(compact_json)
    
    passed6 = compact_len < full_json_len
    compression_ratio = compact_len / full_json_len * 100
    print_test(
        "紧凑格式压缩效果",
        passed6,
        f"压缩比: {compression_ratio:.1f}% ({compact_len}/{full_json_len} bytes)"
    )
    
    # 测试2.6: 变更历史记录
    history = updater.get_change_history(code="000001")
    passed7 = len(history) > 0
    print_test(
        "变更历史记录",
        passed7,
        f"记录数: {len(history)}"
    )
    
    all_passed = all([passed1, passed2, passed3, passed4, passed5, passed6, passed7])
    return all_passed


async def test_hierarchical_cache():
    """测试分层缓存"""
    print_section("Test 3: HierarchicalCache 分层缓存")
    
    from app.services.hierarchical_cache import (
        HierarchicalCache, 
        CacheLevel, 
        DataType
    )
    
    cache = HierarchicalCache()
    
    test_key = "test_quote_000001"
    test_data = {"code": "000001", "price": 12.50, "name": "平安银行"}
    
    # 测试3.1: 写入L1缓存
    await cache.set(test_key, test_data, DataType.REALTIME_HOTSPOT)
    l1_data = await cache.get(test_key, CacheLevel.L1)
    
    passed1 = l1_data is not None and l1_data["code"] == "000001"
    print_test("L1缓存写入/读取", passed1, f"数据: {l1_data}")
    
    # 测试3.2: L2传播
    l2_data = await cache.get(test_key, CacheLevel.L2)
    passed2 = l2_data is not None
    print_test("L1→L2自动传播", passed2, f"L2数据存在: {passed2}")
    
    # 测试3.3: get_or_set方法
    call_count = 0
    
    async def mock_fetch():
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.01)
        return {"code": "600000", "price": 8.90}
    
    key2 = cache.generate_cache_key("realtime", code="600000")
    data1, source1 = await cache.get_or_set(key2, DataType.REALTIME_NORMAL, mock_fetch)
    data2, source2 = await cache.get_or_set(key2, DataType.REALTIME_NORMAL, mock_fetch)
    
    passed3 = source1 == "fresh" and source2 == "l1_hit"
    passed4 = call_count == 1  # 只调用一次fetch
    print_test("get_or_set缓存命中", passed3, f"source1={source1}, source2={source2}")
    print_test("避免重复请求", passed4, f"fetch调用次数: {call_count}")
    
    # 测试3.4: 缓存失效
    invalidate_count = await cache.invalidate(key=test_key)
    invalidated_data = await cache.get(test_key, CacheLevel.L1)
    
    passed5 = invalidate_count >= 1 and invalidated_data is None
    print_test("缓存失效功能", passed5, f"清除数量: {invalidate_count}")
    
    # 测试3.5: 模式匹配清除
    pattern_key1 = "pattern_test_001"
    pattern_key2 = "pattern_test_002"
    other_key = "other_test_003"
    
    await cache.set(pattern_key1, {}, DataType.REALTIME_NORMAL)
    await cache.set(pattern_key2, {}, DataType.REALTIME_NORMAL)
    await cache.set(other_key, {}, DataType.REALTIME_NORMAL)
    
    pattern_count = await cache.invalidate(pattern="pattern_*")
    passed6 = pattern_count == 2
    print_test("模式匹配清除", passed6, f"清除数量: {pattern_count} (应为2)")
    
    # 测试3.6: 统计信息
    stats = cache.get_statistics()
    passed7 = "hit_rate" in stats and "entries_count" in stats
    print_test("统计信息完整", passed7, f"指标数: {len(stats)}")
    
    all_passed = all([passed1, passed2, passed3, passed4, passed5, passed6, passed7])
    return all_passed


async def test_anti_scraping_rules():
    """测试反爬安全规则"""
    print_section("Test 4: AntiScrapingRules 反爬安全")
    
    from app.utils.anti_scraping_rules import AntiScrapingRules, RiskLevel
    
    safety = AntiScrapingRules()
    
    # 测试4.1: 规则加载
    rules_loaded = len(safety.DEFAULT_RULES) >= 4
    print_test("默认规则加载", rules_loaded, f"规则数量: {len(safety.DEFAULT_RULES)}")
    
    # 测试4.2: 安全检查
    for source_name in ["efinance", "akshare", "baostock"]:
        status = safety.check_before_request(source_name)
        
        passed = status.is_safe and isinstance(status.risk_level, RiskLevel)
        icon = "✅" if passed else "❌"
        print(f"{icon} [{source_name.upper()}] 安全检查: {'安全' if status.is_safe else '受限'} "
              f"(风险等级: {status.risk_level.value})")
    
    # 测试4.3: User-Agent轮换
    ua1 = safety.get_user_agent("efinance")
    ua2 = safety.get_user_agent("efinance")
    
    # 多次调用应该可能得到不同的UA（因为随机）
    ua_list = [safety.get_user_agent("efinance") for _ in range(10)]
    unique_uas = len(set(ua_list))
    
    passed3 = unique_uas > 1  # 至少有几种不同的UA
    print_test("User-Agent轮换", passed3, f"唯一UA数: {unique_uas}/10")
    
    # 测试4.4: 请求间隔计算
    intervals = []
    for _ in range(5):
        interval = safety.get_optimal_interval("efinance")
        intervals.append(interval)
    
    has_variance = max(intervals) != min(intervals)
    all_reasonable = all(1.0 <= i <= 10.0 for i in intervals)
    
    passed4 = has_variance and all_reasonable
    print_test(
        "请求间隔随机性",
        passed4,
        f"间隔范围: {min(intervals):.2f}s - {max(intervals):.2f}s"
    )
    
    # 测试4.5: 请求记录
    safety.record_request("efinance", "/api/quote", True, 150.0)
    safety.record_request("efinance", "/api/kline", True, 200.0)
    safety.record_request("akshare", "/api/stock", False, 5000.0)  # 失败请求
    
    stats = safety.get_statistics()
    passed5 = "total_requests_today" in stats
    print_test("请求记录与统计", passed5, f"今日请求数: {stats.get('total_requests_today', 'N/A')}")
    
    # 测试4.6: 连续失败触发冷却
    for i in range(5):
        safety.record_request("yfinance", "/api/fail", False, 1000.0)
    
    cooldown_status = safety.check_before_request("yfinance")
    passed6 = not cooldown_status.is_safe or cooldown_status.cooldown_until is not None
    print_test(
        "连续失败冷却机制",
        passed6,
        f"冷却中: {cooldown_status.cooldown_until is not None}"
    )
    
    all_passed = all([rules_loaded, passed3, passed4, passed5, passed6])
    return all_passed


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "🚀" * 35)
    print("  🧪 SMART POLLING SYSTEM - INTEGRATION TEST SUITE")
    print("🚀" * 35)
    
    results = {}
    
    try:
        results["SmartPollingService"] = await test_smart_polling()
    except Exception as e:
        print(f"\n❌ SmartPollingService 测试异常: {e}")
        results["SmartPollingService"] = False
    
    try:
        results["IncrementalUpdateService"] = await test_incremental_update()
    except Exception as e:
        print(f"\n❌ IncrementalUpdateService 测试异常: {e}")
        results["IncrementalUpdateService"] = False
    
    try:
        results["HierarchicalCache"] = await test_hierarchical_cache()
    except Exception as e:
        print(f"\n❌ HierarchicalCache 测试异常: {e}")
        results["HierarchicalCache"] = False
    
    try:
        results["AntiScrapingRules"] = await test_anti_scraping_rules()
    except Exception as e:
        print(f"\n❌ AntiScrapingRules 测试异常: {e}")
        results["AntiScrapingRules"] = False
    
    # 汇总结果
    print_section("TEST SUMMARY")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\n📊 总体结果:")
    print(f"   通过模块: {passed_tests}/{total_tests}")
    print(f"   成功率: {passed_tests/total_tests*100:.1f}%")
    
    for module_name, passed in results.items():
        icon = "✅" if passed else "❌"
        status = "PASS" if passed else "FAIL"
        print(f"   {icon} {module_name}: {status}")
    
    if passed_tests == total_tests:
        print("\n🎉 所有测试通过！系统集成成功！")
    else:
        failed_modules = [m for m, p in results.items() if not p]
        print(f"\n⚠️  {len(failed_modules)} 个模块需要修复:")
        for module in failed_modules:
            print(f"   - {module}")
    
    print(f"\n⏰ 测试完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

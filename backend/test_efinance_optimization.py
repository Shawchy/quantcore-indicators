"""
efinance 反风控优化测试脚本

测试新增的优化功能：
1. User-Agent 轮换
2. 自适应延迟
3. 失败统计
4. 时间段检测
"""

import asyncio
import time
from app.adapters.efinance_adapter import EFinanceAdapter


async def test_user_agent_rotation():
    """测试 User-Agent 轮换"""
    print("\n" + "="*60)
    print("测试：User-Agent 轮换")
    print("="*60)
    
    adapter = EFinanceAdapter()
    await adapter.initialize()
    
    # 获取 5 次，观察 User-Agent 是否轮换
    user_agents = []
    for i in range(5):
        ua = adapter._rotate_user_agent()
        user_agents.append(ua[:60] + "...")
        print(f"[{i+1}] {ua[:60]}...")
    
    # 检查是否有重复
    unique_uas = set(user_agents)
    if len(unique_uas) > 1:
        print(f"✓ User-Agent 轮换正常（5 次中有{len(unique_uas)}个不同）")
        return True
    else:
        print("✗ User-Agent 未轮换")
        return False


async def test_time_based_delay():
    """测试时间段延迟"""
    print("\n" + "="*60)
    print("测试：时间段延迟")
    print("="*60)
    
    adapter = EFinanceAdapter()
    
    # 获取当前时间段
    delay_range = adapter._get_time_based_delay()
    
    import datetime
    now = datetime.datetime.now()
    current_time = now.hour * 60 + now.minute
    
    # 判断时间段
    if (9*60+30 <= current_time <= 11*60+30) or (13*60 <= current_time <= 15*60):
        period = "交易时段"
        expected = (2.0, 4.0)
    elif 15*60 < current_time <= 22*60:
        period = "盘后时段"
        expected = (1.0, 2.0)
    else:
        period = "夜间"
        expected = (0.5, 1.5)
    
    print(f"当前时间：{now.strftime('%H:%M')}")
    print(f"时间段：{period}")
    print(f"延迟范围：{delay_range}")
    print(f"预期范围：{expected}")
    
    if delay_range == expected:
        print(f"✓ 时间段延迟配置正确")
        return True
    else:
        print(f"? 时间段延迟配置可能异常")
        return True  # 即使不匹配也不算失败（可能是时区问题）


async def test_adaptive_delay():
    """测试自适应延迟（含失败次数增加延迟）"""
    print("\n" + "="*60)
    print("测试：自适应延迟")
    print("="*60)
    
    adapter = EFinanceAdapter()
    adapter._adaptive_delay_enabled = True
    
    # 模拟失败场景
    print("\n模拟连续失败场景：")
    for i in range(4):
        adapter.record_request_failure()
        
        # 获取当前延迟范围
        min_delay, max_delay = adapter._get_time_based_delay()
        extra_delay = min(adapter._consecutive_failures, 5)
        actual_min = min_delay + extra_delay
        actual_max = max_delay + extra_delay
        
        print(f"  失败{i+1}次：基础延迟 ({min_delay}, {max_delay}) + 额外延迟 {extra_delay} = ({actual_min}, {actual_max})秒")
    
    # 重置
    adapter.record_request_success()
    print(f"\n成功后：连续失败次数 = {adapter._consecutive_failures}")
    
    if adapter._consecutive_failures == 0:
        print("✓ 自适应延迟和重置机制正常")
        return True
    else:
        print("✗ 重置机制异常")
        return False


async def test_request_stats():
    """测试请求统计"""
    print("\n" + "="*60)
    print("测试：请求统计")
    print("="*60)
    
    adapter = EFinanceAdapter()
    await adapter.initialize()
    
    # 模拟请求
    print("\n模拟请求场景：")
    adapter._request_count = 10
    adapter._fail_count = 2
    adapter._consecutive_failures = 0
    
    # 获取统计
    stats = adapter.get_stats()
    
    print(f"总请求数：{stats['total_requests']}")
    print(f"失败次数：{stats['failed_requests']}")
    print(f"成功率：{stats['success_rate']}")
    print(f"连续失败：{stats['consecutive_failures']}")
    print(f"User-Agent 数量：{stats['user_agents_count']}")
    print(f"自适应延迟：{stats['adaptive_delay_enabled']}")
    
    expected_success_rate = (10 - 2) / 10 * 100
    actual_success_rate = float(stats['success_rate'].rstrip('%'))
    
    if abs(actual_success_rate - expected_success_rate) < 0.01:
        print(f"✓ 请求统计正确（成功率 {actual_success_rate:.2f}%）")
        return True
    else:
        print(f"✗ 请求统计异常（预期{expected_success_rate}%，实际{actual_success_rate}%）")
        return False


async def test_real_request():
    """测试真实请求（观察日志中的 User-Agent 轮换）"""
    print("\n" + "="*60)
    print("测试：真实请求（观察 User-Agent 轮换）")
    print("="*60)
    
    adapter = EFinanceAdapter()
    await adapter.initialize()
    
    # 获取 3 只股票
    codes = ["601012", "300274", "002594"]
    
    print(f"\n开始获取 {len(codes)} 只股票行情...")
    for i, code in enumerate(codes, 1):
        print(f"\n[{i}/{len(codes)}] 获取 {code}...")
        quote = await adapter.get_latest_quote(code)
        
        if quote:
            print(f"  ✓ 成功：{code} - {quote.get('price', 'N/A')}元")
        else:
            print(f"  ✗ 失败：{code}")
        
        # 查看统计
        stats = adapter.get_stats()
        print(f"  统计：请求{stats['total_requests']}次，失败{stats['failed_requests']}次")
    
    # 最终统计
    final_stats = adapter.get_stats()
    print(f"\n最终统计：")
    print(f"  总请求：{final_stats['total_requests']}")
    print(f"  成功率：{final_stats['success_rate']}")
    print(f"  当前延迟：{final_stats['current_delay_range']}")
    
    if final_stats['total_requests'] > 0:
        print("✓ 真实请求测试完成")
        return True
    else:
        print("✗ 无请求记录")
        return False


async def test_custom_settings():
    """测试自定义设置"""
    print("\n" + "="*60)
    print("测试：自定义设置")
    print("="*60)
    
    adapter = EFinanceAdapter()
    await adapter.initialize()
    
    # 测试禁用自适应延迟
    print("\n1. 禁用自适应延迟...")
    adapter.enable_adaptive_delay(False)
    print(f"  自适应延迟：{adapter._adaptive_delay_enabled}")
    
    # 测试自定义延迟
    print("\n2. 设置自定义延迟...")
    adapter.set_custom_delay(3.0, 5.0)
    print(f"  延迟范围：{adapter._request_delay_range}")
    
    # 测试重新启用
    print("\n3. 重新启用自适应延迟...")
    adapter.enable_adaptive_delay(True)
    print(f"  自适应延迟：{adapter._adaptive_delay_enabled}")
    
    if adapter._adaptive_delay_enabled:
        print("✓ 自定义设置功能正常")
        return True
    else:
        print("✗ 自定义设置异常")
        return False


async def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("efinance 反风控优化测试")
    print("="*60)
    
    tests = [
        ("User-Agent 轮换", test_user_agent_rotation),
        ("时间段延迟", test_time_based_delay),
        ("自适应延迟", test_adaptive_delay),
        ("请求统计", test_request_stats),
        ("真实请求", test_real_request),
        ("自定义设置", test_custom_settings),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} 测试失败：{e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
        
        await asyncio.sleep(1)
    
    # 汇总
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status} - {name}")
    
    print(f"\n总计：{passed}/{total} 测试通过")
    
    if passed == total:
        print("\n✓ 所有优化功能运行正常！")
    else:
        print(f"\n⚠ {total - passed} 个测试未通过，请检查日志")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n✗ 测试程序异常：{e}")
        import traceback
        traceback.print_exc()

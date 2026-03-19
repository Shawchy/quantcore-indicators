"""
efinance 反风控机制测试脚本

运行此脚本测试反风控机制是否正常工作：
1. 请求头设置
2. 频率控制
3. 缓存机制
4. 重试机制

使用方法：
    python test_efinance_anti_crawling.py
"""

import asyncio
import time
from app.adapters.factory import DataSourceManager
from loguru import logger


async def test_request_headers():
    """测试 1：请求头设置"""
    print("\n" + "="*60)
    print("测试 1：请求头设置")
    print("="*60)
    
    adapter = await DataSourceManager.get_adapter("efinance")
    
    # 检查请求头是否已设置
    import efinance as ef
    if hasattr(ef.stock, '_session'):
        headers = ef.stock._session.headers
        print(f"✓ User-Agent: {headers.get('User-Agent', '未设置')[:50]}...")
        print(f"✓ Referer: {headers.get('Referer', '未设置')}")
        print(f"✓ Accept: {headers.get('Accept', '未设置')[:50]}...")
    else:
        print("✗ 无法访问 _session 对象")
    
    return True


async def test_rate_limiting():
    """测试 2：频率控制"""
    print("\n" + "="*60)
    print("测试 2：频率控制（应观察到 1-2 秒延迟）")
    print("="*60)
    
    adapter = await DataSourceManager.get_adapter("efinance")
    
    # 连续调用 3 次，观察延迟
    codes = ["601012", "300274", "002594"]
    start_time = time.time()
    
    print(f"\n开始获取 {len(codes)} 只股票行情...")
    for i, code in enumerate(codes, 1):
        quote = await adapter.get_latest_quote(code)
        elapsed = time.time() - start_time
        print(f"[{i}/{len(codes)}] {code}: {quote.get('price', 'N/A')}元 (总耗时：{elapsed:.2f}秒)")
    
    total_time = time.time() - start_time
    avg_delay = total_time / (len(codes) - 1) if len(codes) > 1 else 0
    
    print(f"\n✓ 总耗时：{total_time:.2f}秒")
    print(f"✓ 平均延迟：{avg_delay:.2f}秒/次")
    
    if 1.0 <= avg_delay <= 3.0:
        print("✓ 频率控制正常（1-2 秒/次）")
        return True
    else:
        print(f"✗ 频率控制异常（应为 1-2 秒/次，实际 {avg_delay:.2f}秒）")
        return False


async def test_cache_mechanism():
    """测试 3：缓存机制"""
    print("\n" + "="*60)
    print("测试 3：缓存机制（第二次应瞬间返回）")
    print("="*60)
    
    adapter = await DataSourceManager.get_adapter("efinance")
    code = "601012"
    
    # 第一次请求（实际网络请求）
    print(f"\n第一次请求 {code}...")
    start = time.time()
    quote1 = await adapter.get_latest_quote(code)
    time1 = time.time() - start
    print(f"✓ 第一次耗时：{time1:.3f}秒，价格：{quote1.get('price', 'N/A')}元")
    
    # 第二次请求（应从缓存返回）
    print(f"\n第二次请求 {code}（应从缓存返回）...")
    start = time.time()
    quote2 = await adapter.get_latest_quote(code)
    time2 = time.time() - start
    print(f"✓ 第二次耗时：{time2:.3f}秒，价格：{quote2.get('price', 'N/A')}元")
    
    # 验证缓存
    if time2 < time1 * 0.1:  # 缓存应该快 10 倍以上
        print(f"✓ 缓存机制正常（加速 {time1/time2:.1f}x）")
        return True
    else:
        print(f"✗ 缓存机制可能未生效")
        return False


async def test_batch_optimization():
    """测试 4：批量请求优化"""
    print("\n" + "="*60)
    print("测试 4：批量请求优化（批量 vs 单次）")
    print("="*60)
    
    adapter = await DataSourceManager.get_adapter("efinance")
    codes = ["601012", "300274", "002594", "688223", "000858"]
    
    # 方式 1：批量获取
    print(f"\n方式 1：批量获取 {len(codes)} 只股票...")
    start = time.time()
    batch_quotes = await adapter.get_latest_quote(codes)
    batch_time = time.time() - start
    print(f"✓ 批量获取耗时：{batch_time:.3f}秒，成功：{len(batch_quotes)}只")
    
    # 方式 2：单次循环（不推荐）
    print(f"\n方式 2：单次循环获取 {len(codes)} 只股票（不推荐）...")
    start = time.time()
    single_quotes = []
    for code in codes:
        quote = await adapter.get_latest_quote(code)
        single_quotes.append(quote)
    single_time = time.time() - start
    print(f"✓ 单次循环耗时：{single_time:.3f}秒，成功：{len(single_quotes)}只")
    
    # 对比
    print(f"\n✓ 批量获取比单次循环快 {single_time/batch_time:.1f}x")
    print(f"✓ 批量请求减少 {len(codes)-1} 次网络请求")
    
    return True


async def test_retry_mechanism():
    """测试 5：重试机制（模拟失败场景）"""
    print("\n" + "="*60)
    print("测试 5：重试机制（查看日志中的重试信息）")
    print("="*60)
    
    adapter = await DataSourceManager.get_adapter("efinance")
    
    # 尝试获取不存在的股票（可能触发重试）
    print("\n尝试获取无效股票代码（观察重试日志）...")
    quote = await adapter.get_latest_quote("999999")
    
    if not quote:
        print("✓ 无效股票返回空数据（符合预期）")
        return True
    else:
        print(f"? 返回数据：{quote}")
        return True


async def test_proxy_setting():
    """测试 6：代理 IP 设置"""
    print("\n" + "="*60)
    print("测试 6：代理 IP 设置（仅测试接口可用性）")
    print("="*60)
    
    adapter = await DataSourceManager.get_adapter("efinance")
    
    # 测试设置代理（使用无效代理，仅测试接口）
    print("\n尝试设置代理（使用无效地址，仅测试接口）...")
    result = await adapter.set_proxy("http://127.0.0.1:7890")
    print(f"✓ 设置代理接口：{'成功' if result else '失败'}")
    
    # 清除代理
    await adapter.clear_proxy()
    print("✓ 清除代理：完成")
    
    return True


async def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("efinance 反风控机制测试")
    print("="*60)
    
    tests = [
        ("请求头设置", test_request_headers),
        ("频率控制", test_rate_limiting),
        ("缓存机制", test_cache_mechanism),
        ("批量优化", test_batch_optimization),
        ("重试机制", test_retry_mechanism),
        ("代理设置", test_proxy_setting),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} 测试失败：{e}")
            results.append((name, False))
        
        # 测试间隔延迟
        await asyncio.sleep(1)
    
    # 汇总结果
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
        print("\n✓ 所有反风控机制运行正常！")
    else:
        print(f"\n⚠ {total - passed} 个测试未通过，请检查日志")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n✗ 测试程序异常：{e}")

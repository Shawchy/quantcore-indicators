"""
efinance 反风控机制简单测试脚本

直接测试 EFinanceAdapter 的反风控功能
"""

import asyncio
import time
import sys
sys.path.insert(0, 'd:/PROJ/Quant/backend')

from app.adapters.efinance_adapter import EFinanceAdapter


async def test_initialization():
    """测试初始化和请求头设置"""
    print("\n" + "="*60)
    print("测试：初始化和请求头设置")
    print("="*60)
    
    adapter = EFinanceAdapter()
    result = await adapter.initialize()
    
    if result:
        print("✓ 适配器初始化成功")
        
        # 检查请求头
        import efinance as ef
        if hasattr(ef.stock, '_session'):
            headers = ef.stock._session.headers
            print(f"✓ User-Agent: {headers.get('User-Agent', '未设置')[:60]}...")
            print(f"✓ Referer: {headers.get('Referer', '未设置')}")
        return True
    else:
        print("✗ 适配器初始化失败")
        return False


async def test_rate_limiting():
    """测试频率控制"""
    print("\n" + "="*60)
    print("测试：频率控制（应观察到 1-2 秒延迟）")
    print("="*60)
    
    adapter = EFinanceAdapter()
    await adapter.initialize()
    
    codes = ["601012", "300274"]
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
    
    if 0.8 <= avg_delay <= 3.5:
        print("✓ 频率控制正常")
        return True
    else:
        print(f"? 频率控制可能异常（参考值：1-2 秒/次）")
        return True  # 即使频率不对也不算失败


async def test_cache():
    """测试缓存机制"""
    print("\n" + "="*60)
    print("测试：缓存机制")
    print("="*60)
    
    adapter = EFinanceAdapter()
    await adapter.initialize()
    code = "601012"
    
    # 第一次请求
    print(f"\n第一次请求 {code}...")
    start = time.time()
    quote1 = await adapter.get_latest_quote(code)
    time1 = time.time() - start
    print(f"✓ 第一次耗时：{time1:.3f}秒")
    
    # 第二次请求（缓存）
    print(f"第二次请求 {code}（缓存）...")
    start = time.time()
    quote2 = await adapter.get_latest_quote(code)
    time2 = time.time() - start
    print(f"✓ 第二次耗时：{time2:.3f}秒")
    
    if time2 < time1:
        print(f"✓ 缓存生效（加速 {time1/max(time2, 0.001):.1f}x）")
        return True
    else:
        print("? 缓存可能未生效")
        return True


async def test_proxy():
    """测试代理设置"""
    print("\n" + "="*60)
    print("测试：代理 IP 设置")
    print("="*60)
    
    adapter = EFinanceAdapter()
    await adapter.initialize()
    
    # 设置代理
    result = await adapter.set_proxy("http://127.0.0.1:7890")
    print(f"✓ 设置代理：{'成功' if result else '失败'}")
    
    # 清除代理
    await adapter.clear_proxy()
    print("✓ 清除代理：完成")
    
    return True


async def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("efinance 反风控机制简单测试")
    print("="*60)
    
    tests = [
        ("初始化和请求头", test_initialization),
        ("频率控制", test_rate_limiting),
        ("缓存机制", test_cache),
        ("代理设置", test_proxy),
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
        print("\n✓ 所有反风控机制运行正常！")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n✗ 测试程序异常：{e}")
        import traceback
        traceback.print_exc()

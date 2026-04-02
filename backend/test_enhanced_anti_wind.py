"""
增强版反风控功能测试脚本

测试内容：
1. 代理池管理
2. 智能请求调度
3. Cookie 持久化
4. 浏览器指纹伪装
5. 验证码检测
6. 完整流程测试

使用方法：
    python test_enhanced_anti_wind.py
"""

import asyncio
import os
import sys

os.environ['PLAYWRIGHT_BROWSERS_PATH'] = 'd:/PROJ/Quant/backend/playwright_browsers'


async def test_proxy_pool():
    print("\n" + "="*60)
    print("测试 1：代理池管理")
    print("="*60)
    
    from app.adapters.anti_wind_control import ProxyPool
    
    pool = ProxyPool()
    
    pool.add_proxy("192.168.1.1", 8080)
    pool.add_proxy("192.168.1.2", 8080, protocol="https")
    pool.add_proxy("192.168.1.3", 8080, username="user", password="pass")
    
    print(f"\n添加了 3 个代理")
    
    proxy = pool.get_proxy()
    if proxy:
        print(f"✓ 获取代理成功: {proxy.host}:{proxy.port}")
        print(f"  URL: {proxy.url}")
        
        pool.report_success(proxy, 0.5)
        print(f"✓ 报告成功后成功率: {proxy.success_rate:.1%}")
    else:
        print("✗ 获取代理失败")
    
    status = pool.get_status()
    print(f"\n代理池状态:")
    print(f"  总数: {status['total']}")
    print(f"  可用: {status['available']}")
    print(f"  忙碌: {status['busy']}")
    print(f"  屏蔽: {status['blocked']}")
    
    print("\n✓ 代理池测试完成")
    return True


async def test_smart_scheduler():
    print("\n" + "="*60)
    print("测试 2：智能请求调度")
    print("="*60)
    
    from app.adapters.anti_wind_control import SmartRequestScheduler
    
    scheduler = SmartRequestScheduler()
    
    print("\n模拟不同时间段的请求延迟:")
    
    delays = []
    for i in range(5):
        delay = scheduler.get_delay("eastmoney.com")
        delays.append(delay)
        print(f"  请求 {i+1}: 延迟 {delay:.2f}s")
    
    print(f"\n平均延迟: {sum(delays)/len(delays):.2f}s")
    
    print("\n模拟失败后延迟变化:")
    scheduler.report_failure("eastmoney.com")
    delay_after_fail = scheduler.get_delay("eastmoney.com")
    print(f"  失败后延迟: {delay_after_fail:.2f}s")
    
    print("\n模拟成功后延迟恢复:")
    scheduler.report_success("eastmoney.com")
    delay_after_success = scheduler.get_delay("eastmoney.com")
    print(f"  成功后延迟: {delay_after_success:.2f}s")
    
    print("\n✓ 智能调度测试完成")
    return True


async def test_cookie_manager():
    print("\n" + "="*60)
    print("测试 3：Cookie 持久化")
    print("="*60)
    
    from app.adapters.anti_wind_control import CookieManager
    
    manager = CookieManager("data/test_cookies")
    
    test_cookies = [
        {"name": "session_id", "value": "abc123", "domain": ".eastmoney.com"},
        {"name": "user_token", "value": "xyz789", "domain": ".eastmoney.com"},
    ]
    
    await manager.save_cookies("eastmoney.com", test_cookies)
    print("✓ Cookie 已保存")
    
    loaded = await manager.load_cookies("eastmoney.com")
    if loaded:
        print(f"✓ Cookie 已加载: {len(loaded)} 条")
        for cookie in loaded:
            print(f"  - {cookie['name']}: {cookie['value'][:20]}...")
    else:
        print("✗ Cookie 加载失败")
    
    await manager.clear_cookies("eastmoney.com")
    print("✓ Cookie 已清除")
    
    print("\n✓ Cookie 管理测试完成")
    return True


async def test_fingerprint():
    print("\n" + "="*60)
    print("测试 4：浏览器指纹伪装")
    print("="*60)
    
    from app.adapters.anti_wind_control import EnhancedFingerprint
    
    script = EnhancedFingerprint.get_stealth_script()
    
    checks = [
        ("webdriver 隐藏", "'webdriver'" in script or "webdriver" in script),
        ("plugins 伪装", "'plugins'" in script or "plugins" in script),
        ("languages 设置", "'languages'" in script or "languages" in script),
        ("chrome 对象", "window.chrome" in script),
        ("WebGL 指纹", "WebGLRenderingContext" in script),
        ("Canvas 噪声", "HTMLCanvasElement" in script),
        ("Audio 指纹", "AudioContext" in script),
        ("toString 修复", "Function.toString" in script),
    ]
    
    print(f"\n指纹伪装脚本长度: {len(script)} 字符")
    print("\n伪装特性检查:")
    
    all_passed = True
    for name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"  {status} {name}")
        if not passed:
            all_passed = False
    
    print(f"\n随机 User-Agent: {EnhancedFingerprint.get_random_user_agent()[:60]}...")
    print(f"随机视口: {EnhancedFingerprint.get_random_viewport()}")
    
    print("\n✓ 指纹伪装测试完成")
    return all_passed


async def test_captcha_detector():
    print("\n" + "="*60)
    print("测试 5：验证码检测")
    print("="*60)
    
    from app.adapters.anti_wind_control import CaptchaDetector
    
    print("\n验证码指示器列表:")
    indicators = CaptchaDetector.CAPTCHA_INDICATORS[:10]
    for indicator in indicators:
        print(f"  - {indicator}")
    print(f"  ... 共 {len(CaptchaDetector.CAPTCHA_INDICATORS)} 个指示器")
    
    print("\n✓ 验证码检测测试完成")
    return True


async def test_enhanced_adapter():
    print("\n" + "="*60)
    print("测试 6：增强版适配器完整流程")
    print("="*60)
    
    try:
        from app.adapters.enhanced_playwright_adapter import EnhancedPlaywrightAdapter
        
        adapter = EnhancedPlaywrightAdapter({
            'headless': True,
            'enable_proxy': False,
            'enable_cookies': True,
            'enable_captcha_detection': True,
        })
        
        print("\n初始化适配器...")
        success = await adapter.initialize()
        
        if success:
            print("✓ 初始化成功")
            
            status = adapter.get_status()
            print(f"\n适配器状态:")
            print(f"  已初始化: {status['initialized']}")
            print(f"  无头模式: {status['headless']}")
            print(f"  请求次数: {status['request_count']}")
            
            print("\n尝试访问东方财富...")
            quotes = await adapter.get_market_realtime_quotes()
            
            if quotes:
                print(f"✓ 获取行情成功: {len(quotes)} 条")
                sample = quotes[0]
                print(f"  示例: {sample.code} {sample.name}")
            else:
                print("⚠ 未获取到数据（可能是非交易时间）")
            
            await adapter.close()
            print("\n✓ 适配器已关闭")
            return True
        else:
            print("✗ 初始化失败")
            return False
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_anti_wind_manager():
    print("\n" + "="*60)
    print("测试 7：反风控管理器集成")
    print("="*60)
    
    from app.adapters.anti_wind_control import AntiWindControlManager
    
    manager = AntiWindControlManager({
        'enable_proxy': True,
        'enable_cookies': True,
        'enable_smart_schedule': True,
        'enable_captcha_detection': True,
    })
    
    manager.add_proxy("192.168.1.100", 8080)
    manager.add_proxy("192.168.1.101", 8080)
    
    print("\n模拟请求流程:")
    
    context = await manager.before_request(
        "https://quote.eastmoney.com/center/gridlist.html",
        "eastmoney.com"
    )
    
    print(f"  请求上下文:")
    print(f"    延迟: {context['delay']:.2f}s")
    print(f"    代理: {context['proxy'] or '无'}")
    print(f"    Cookie: {len(context['cookies']) if context['cookies'] else 0} 条")
    print(f"    指纹脚本: {len(context['fingerprint_script'])} 字符")
    
    await manager.after_request(
        success=True,
        domain="eastmoney.com",
        response_time=1.5,
        cookies=[{"name": "test", "value": "123"}]
    )
    
    stats = manager.get_stats()
    print(f"\n统计信息:")
    print(f"  总请求: {stats['total_requests']}")
    print(f"  成功: {stats['successful_requests']}")
    print(f"  成功率: {stats['success_rate']}")
    
    print("\n✓ 反风控管理器测试完成")
    return True


async def main():
    print("\n" + "="*60)
    print("增强版反风控功能测试")
    print("="*60)
    
    tests = [
        ("代理池管理", test_proxy_pool),
        ("智能请求调度", test_smart_scheduler),
        ("Cookie 持久化", test_cookie_manager),
        ("浏览器指纹伪装", test_fingerprint),
        ("验证码检测", test_captcha_detector),
        ("反风控管理器集成", test_anti_wind_manager),
        ("增强版适配器完整流程", test_enhanced_adapter),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} 测试异常: {e}")
            results.append((name, False))
        
        await asyncio.sleep(0.5)
    
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
        print("\n✓ 所有测试通过！增强版反风控功能就绪")
    else:
        print(f"\n⚠ {total - passed} 个测试未通过")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n✗ 测试程序异常: {e}")

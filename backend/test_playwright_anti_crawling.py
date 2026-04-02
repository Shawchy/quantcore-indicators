"""
Playwright 无头浏览器反风控测试脚本

测试内容：
1. 浏览器适配器初始化
2. 反检测机制验证
3. 数据获取测试
4. 智能切换器测试

使用方法：
    python test_playwright_anti_crawling.py
"""

import asyncio
import time
import os
from loguru import logger

os.environ['PLAYWRIGHT_BROWSERS_PATH'] = 'd:/PROJ/Quant/backend/playwright_browsers'

async def test_playwright_api_directly():
    """直接测试 Playwright API"""
    print("\n" + "="*60)
    print("测试 0：Playwright API 直接测试")
    print("="*60)
    
    from playwright.async_api import async_playwright
    
    print("1. 测试 async_playwright().start()...")
    pw = await async_playwright().start()
    print(f"2. playwright 对象: {pw}")
    print(f"3. 类型: {type(pw)}")
    
    if pw is None:
        print("错误: async_playwright().start() 返回 None!")
        return False
    
    chromium_exe = os.path.join(
        os.environ['PLAYWRIGHT_BROWSERS_PATH'],
        'chromium-1148', 'chrome-win', 'chrome.exe'
    )
    
    browser = await pw.chromium.launch(
        headless=True,
        executable_path=chromium_exe
    )
    print(f"4. browser: {browser}")
    
    context = await browser.new_context()
    page = await context.new_page()
    await page.goto("https://www.baidu.com")
    print(f"5. title: {await page.title()}")
    
    await browser.close()
    print("✓ Playwright API 直接测试成功!")
    return True


async def test_browser_adapter():
    """测试浏览器适配器"""
    print("\n" + "="*60)
    print("测试 1：Playwright 浏览器适配器初始化")
    print("="*60)
    
    try:
        from app.adapters.playwright_adapter import PlaywrightAdapter
        
        adapter = PlaywrightAdapter({
            'headless': True,
            'browser_type': 'chromium'
        })
        
        print("\n初始化浏览器适配器...")
        start = time.time()
        success = await adapter.initialize()
        init_time = time.time() - start
        
        if success:
            print(f"✓ 初始化成功，耗时 {init_time:.2f}秒")
            
            status = adapter.get_status()
            print(f"✓ 浏览器类型: {status['browser_type']}")
            print(f"✓ 无头模式: {status['headless']}")
            
            await adapter.close()
            print("✓ 浏览器已关闭")
            return True
        else:
            print("✗ 初始化失败")
            return False
            
    except ImportError as e:
        print(f"✗ Playwright 未安装: {e}")
        print("  请运行: pip install playwright && playwright install chromium")
        return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False


async def test_anti_detection():
    """测试反检测机制"""
    print("\n" + "="*60)
    print("测试 2：反检测机制验证")
    print("="*60)
    
    try:
        from app.adapters.playwright_adapter import PlaywrightAdapter
        
        adapter = PlaywrightAdapter({'headless': True})
        
        if not await adapter.initialize():
            print("✗ 初始化失败")
            return False
        
        print("\n检查浏览器指纹...")
        
        webdriver_check = await adapter._page.evaluate("navigator.webdriver")
        print(f"✓ navigator.webdriver: {webdriver_check} (应为 undefined)")
        
        plugins = await adapter._page.evaluate("navigator.plugins.length")
        print(f"✓ plugins 数量: {plugins} (应大于 0)")
        
        languages = await adapter._page.evaluate("navigator.languages")
        print(f"✓ languages: {languages}")
        
        chrome_obj = await adapter._page.evaluate("typeof window.chrome")
        print(f"✓ window.chrome: {chrome_obj} (应为 object)")
        
        await adapter.close()
        
        if webdriver_check is None and plugins > 0:
            print("\n✓ 反检测机制正常")
            return True
        else:
            print("\n✗ 反检测机制可能存在问题")
            return False
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False


async def test_data_fetch():
    """测试数据获取"""
    print("\n" + "="*60)
    print("测试 3：数据获取测试")
    print("="*60)
    
    try:
        from app.adapters.playwright_adapter import PlaywrightAdapter
        
        adapter = PlaywrightAdapter({'headless': True})
        
        if not await adapter.initialize():
            print("✗ 初始化失败")
            return False
        
        print("\n获取市场行情数据...")
        start = time.time()
        quotes = await adapter.get_market_realtime_quotes()
        fetch_time = time.time() - start
        
        if quotes:
            print(f"✓ 获取成功: {len(quotes)} 条数据，耗时 {fetch_time:.2f}秒")
            if len(quotes) > 0:
                sample = quotes[0]
                print(f"  示例: {sample.code} {sample.name} 价格:{sample.price}")
        else:
            print("⚠ 未获取到数据（可能是非交易时间）")
        
        await adapter.close()
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False


async def test_smart_switcher():
    """测试智能切换器"""
    print("\n" + "="*60)
    print("测试 4：智能数据源切换器")
    print("="*60)
    
    try:
        from app.adapters.smart_switcher import SmartDataSourceSwitcher, FallbackConfig
        from app.adapters.akshare_adapter import AkShareAdapter
        
        config = FallbackConfig(
            enable_browser_fallback=True,
            max_retries_before_fallback=2,
            browser_headless=True
        )
        
        switcher = SmartDataSourceSwitcher(config)
        
        api_adapter = AkShareAdapter()
        await api_adapter.initialize()
        
        print("\n初始化智能切换器...")
        success = await switcher.initialize(api_adapter)
        
        if success:
            print("✓ 切换器初始化成功")
            
            status = switcher.get_status_report()
            print(f"✓ 浏览器降级可用: {status['browser_available']}")
            print(f"✓ 当前数据源: {status['current_source']}")
            
            print("\n尝试获取股票列表...")
            stocks = await switcher.get_stock_list()
            if stocks:
                print(f"✓ 获取成功: {len(stocks)} 只股票")
            
            final_status = switcher.get_status_report()
            api_status = final_status['sources'].get('api', {})
            print(f"\nAPI 状态:")
            print(f"  - 健康度: {api_status.get('health')}")
            print(f"  - 成功率: {api_status.get('success_rate')}")
            print(f"  - 请求次数: {api_status.get('total_requests')}")
            
            await switcher.close()
            print("\n✓ 切换器测试完成")
            return True
        else:
            print("✗ 切换器初始化失败")
            return False
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_proxy_setting():
    """测试代理设置"""
    print("\n" + "="*60)
    print("测试 5：代理设置（仅测试接口）")
    print("="*60)
    
    try:
        from app.adapters.playwright_adapter import PlaywrightAdapter
        
        adapter = PlaywrightAdapter({'headless': True})
        
        if not await adapter.initialize():
            print("✗ 初始化失败")
            return False
        
        print("\n测试代理设置接口...")
        await adapter.set_proxy("http://127.0.0.1:7890")
        print("✓ 代理设置接口正常")
        
        await adapter.clear_proxy()
        print("✓ 代理清除接口正常")
        
        await adapter.close()
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False


async def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("Playwright 无头浏览器反风控测试")
    print("="*60)
    
    tests = [
        ("浏览器适配器初始化", test_browser_adapter),
        ("反检测机制验证", test_anti_detection),
        ("数据获取测试", test_data_fetch),
        ("智能切换器测试", test_smart_switcher),
        ("代理设置测试", test_proxy_setting),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} 测试异常: {e}")
            results.append((name, False))
        
        await asyncio.sleep(1)
    
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
        print("\n✓ 所有测试通过！反风控机制就绪")
    else:
        print(f"\n⚠ {total - passed} 个测试未通过")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n✗ 测试程序异常: {e}")

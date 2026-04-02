"""
诊断适配器初始化缓慢问题
"""

import asyncio
import time
from pathlib import Path


async def diagnose_initialization():
    print("\n=== 适配器初始化诊断 ===\n")
    
    # 测试 1: Playwright 初始化
    print("1. 测试 Playwright 初始化...")
    start = time.time()
    try:
        from playwright.async_api import async_playwright
        playwright = await async_playwright().start()
        playwright_init_time = time.time() - start
        print(f"   Playwright start: {playwright_init_time:.2f}s")
        
        # 测试浏览器启动
        start = time.time()
        browsers_path = Path("d:/PROJ/Quant/backend/playwright_browsers/chromium-1148/chrome-win/chrome.exe")
        
        launch_options = {
            'headless': True,
            'args': [
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        }
        
        if browsers_path.exists():
            launch_options['executable_path'] = str(browsers_path)
            print(f"   使用 Chromium: {browsers_path}")
        
        browser = await playwright.chromium.launch(**launch_options)
        browser_launch_time = time.time() - start
        print(f"   Browser launch: {browser_launch_time:.2f}s")
        
        # 测试创建上下文
        start = time.time()
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
        )
        context_time = time.time() - start
        print(f"   Context create: {context_time:.2f}s")
        
        # 测试创建页面
        start = time.time()
        page = await context.new_page()
        page_time = time.time() - start
        print(f"   Page create: {page_time:.2f}s")
        
        # 测试访问首页
        start = time.time()
        await page.goto("https://www.eastmoney.com/", timeout=30000)
        await asyncio.sleep(1)
        navigate_time = time.time() - start
        print(f"   Navigate + sleep(1): {navigate_time:.2f}s")
        
        await browser.close()
        await playwright.stop()
        
        total_pw_time = playwright_init_time + browser_launch_time + context_time + page_time + navigate_time
        print(f"\n   Playwright 总初始化时间：{total_pw_time:.2f}s")
        
    except Exception as e:
        print(f"   失败: {e}")
        return
    
    # 测试 2: curl_cffi 初始化
    print("\n2. 测试 curl_cffi 初始化...")
    start = time.time()
    try:
        from curl_cffi.requests import Session
        curl_sessions = {}
        for fp in ['chrome120', 'chrome119', 'chrome118', 'firefox120', 'chrome110']:
            curl_sessions[fp] = Session(impersonate=fp)
        
        curl_time = time.time() - start
        print(f"   curl_cffi ({len(curl_sessions)} sessions): {curl_time:.2f}s")
        
        for session in curl_sessions.values():
            session.close()
    except ImportError:
        print("   curl_cffi 未安装")
    except Exception as e:
        print(f"   失败: {e}")
    
    # 测试 3: tls-client 初始化
    print("\n3. 测试 tls-client 初始化...")
    start = time.time()
    try:
        import tls_client
        tls_session = tls_client.Session(client_identifier='chrome120')
        tls_time = time.time() - start
        print(f"   tls-client: {tls_time:.2f}s")
    except ImportError:
        print("   tls-client 未安装")
    except Exception as e:
        print(f"   失败: {e}")
    
    # 测试 4: httpx 初始化
    print("\n4. 测试 httpx 初始化...")
    start = time.time()
    try:
        import httpx
        httpx_client = httpx.Client(
            http2=True,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'},
            timeout=30.0,
        )
        httpx_time = time.time() - start
        print(f"   httpx: {httpx_time:.2f}s")
        httpx_client.close()
    except ImportError:
        print("   httpx 未安装")
    except Exception as e:
        print(f"   失败: {e}")
    
    print("\n" + "=" * 60)
    print("诊断结论:")
    print("=" * 60)
    print(f"Playwright 初始化: {total_pw_time:.2f}s (主要耗时)")
    print(f"  - playwright start: {playwright_init_time:.2f}s")
    print(f"  - browser launch: {browser_launch_time:.2f}s")
    print(f"  - context + page: {context_time + page_time:.2f}s")
    print(f"  - navigate + sleep: {navigate_time:.2f}s")
    print("\n建议:")
    if total_pw_time > 10:
        print("  1. Playwright 初始化较慢，建议使用 PlaywrightPool 预创建实例")
        print("  2. 考虑懒加载：仅在需要时才初始化 Playwright")
        print("  3. 减少不必要的 sleep 时间")
    if browser_launch_time > 5:
        print("  4. 浏览器启动慢，检查 Chromium 路径是否正确")


if __name__ == "__main__":
    asyncio.run(diagnose_initialization())

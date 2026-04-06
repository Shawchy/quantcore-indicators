"""
测试 DrissionPage 和 Playwright 是否能正常工作（修复版）
"""
import asyncio
import time
from loguru import logger


async def test_drission():
    """测试 DrissionPage（使用 Edge）"""
    print("\n" + "="*60)
    print("测试 DrissionPage (Edge)")
    print("="*60)
    
    try:
        from DrissionPage import ChromiumPage, ChromiumOptions
        
        print("✅ DrissionPage 导入成功")
        
        # 配置 Edge 浏览器路径
        edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        
        options = ChromiumOptions()
        options.headless(True)
        options.set_argument('--disable-blink-features=AutomationControlled')
        options.set_argument('--disable-dev-shm-usage')
        options.set_argument('--no-sandbox')
        options.set_paths(browser_path=edge_path)
        
        print(f"启动浏览器：{edge_path}")
        page = ChromiumPage(options)
        
        try:
            print("访问东方财富网站...")
            start_time = time.time()
            page.get('https://fund.eastmoney.com/')
            elapsed = time.time() - start_time
            print(f"✅ 页面加载成功，耗时：{elapsed:.2f}秒")
            
            # 获取 Cookie
            print("获取 Cookie...")
            cookies = page.cookies()
            print(f"✅ 获取到 {len(cookies)} 个 Cookie")
            
            # 显示前 3 个 Cookie
            for i, cookie in enumerate(cookies[:3]):
                print(f"   Cookie {i+1}: {cookie.get('name')} = {cookie.get('value')[:50]}...")
            
            return True
            
        finally:
            print("关闭浏览器...")
            page.quit()
            print("✅ 浏览器已关闭")
            
    except Exception as e:
        print(f"❌ DrissionPage 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


async def test_playwright_async():
    """测试 Playwright（使用异步 API）"""
    print("\n" + "="*60)
    print("测试 Playwright (异步 API)")
    print("="*60)
    
    try:
        from playwright.async_api import async_playwright
        
        print("✅ Playwright 异步 API 导入成功")
        
        # 启动 Playwright
        print("启动 Playwright...")
        playwright = await async_playwright().start()
        
        try:
            # 启动浏览器
            print("启动浏览器...")
            browser = await playwright.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            try:
                # 创建上下文
                print("创建浏览器上下文...")
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    locale='zh-CN',
                    timezone_id='Asia/Shanghai',
                )
                
                page = await context.new_page()
                
                try:
                    # 访问网站
                    print("访问东方财富网站...")
                    start_time = time.time()
                    await page.goto('https://fund.eastmoney.com/')
                    await page.wait_for_load_state('networkidle')
                    elapsed = time.time() - start_time
                    print(f"✅ 页面加载成功，耗时：{elapsed:.2f}秒")
                    
                    # 获取 Cookie
                    print("获取 Cookie...")
                    cookies = await context.cookies()
                    print(f"✅ 获取到 {len(cookies)} 个 Cookie")
                    
                    # 显示前 3 个 Cookie
                    for i, cookie in enumerate(cookies[:3]):
                        print(f"   Cookie {i+1}: {cookie.get('name')} = {cookie.get('value')[:50]}...")
                    
                    return True
                    
                finally:
                    print("关闭页面...")
                    await page.close()
            finally:
                print("关闭上下文...")
                await context.close()
                print("关闭浏览器...")
                await browser.close()
        finally:
            print("停止 Playwright...")
            await playwright.stop()
            
    except Exception as e:
        print(f"❌ Playwright 异步测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


async def test_credential_injector_with_edge():
    """测试凭证注入器（配置 Edge 路径）"""
    print("\n" + "="*60)
    print("测试凭证注入器 (配置 Edge)")
    print("="*60)
    
    try:
        from app.adapters.credential_injector import CredentialInjector
        
        edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        
        print(f"创建凭证注入器 (Edge: {edge_path})...")
        injector = CredentialInjector({
            'browser_path': edge_path,
            'headless': True,
        })
        
        print("初始化凭证注入器...")
        await injector.initialize()
        
        status = injector.get_status()
        print(f"\n✅ 凭证注入器状态:")
        print(f"   初始化：{status.get('initialized')}")
        print(f"   浏览器模式：{status.get('browser_mode', 'N/A')}")
        print(f"   已注入：{status.get('patched')}")
        
        # 获取凭证
        print("\n获取凭证...")
        success = await injector.fetch_credentials('eastmoney.com')
        print(f"凭证获取结果：{success}")
        
        # 显示状态
        status = injector.get_status()
        credentials = status.get('credentials', {})
        if 'eastmoney.com' in credentials:
            cred_status = credentials['eastmoney.com']
            print(f"✅ 凭证状态:")
            print(f"   有效：{cred_status.get('valid')}")
            print(f"   更新时间：{cred_status.get('updated_at')}")
        
        return success
        
    except Exception as e:
        print(f"❌ 凭证注入器测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


async def test_curl_cffi():
    """测试 curl_cffi（无需浏览器）"""
    print("\n" + "="*60)
    print("测试 curl_cffi (无需浏览器)")
    print("="*60)
    
    try:
        from curl_cffi import requests
        
        print("✅ curl_cffi 导入成功")
        
        # 模拟浏览器请求
        print("发送请求到东方财富...")
        start_time = time.time()
        
        response = requests.get(
            'https://fund.eastmoney.com/',
            impersonate='chrome120',
            timeout=30
        )
        
        elapsed = time.time() - start_time
        print(f"✅ 请求成功，耗时：{elapsed:.2f}秒")
        print(f"   状态码：{response.status_code}")
        print(f"   响应长度：{len(response.content)} 字节")
        
        # 显示 Cookie
        cookies = response.cookies
        print(f"   获取到 {len(cookies)} 个 Cookie")
        
        return True
        
    except Exception as e:
        print(f"❌ curl_cffi 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("浏览器和凭证注入测试（修复版）")
    print("="*60)
    
    # 测试 DrissionPage（使用 Edge）
    drission_ok = await test_drission()
    
    # 测试 Playwright（异步 API）
    playwright_ok = await test_playwright_async()
    
    # 测试凭证注入器（配置 Edge）
    injector_ok = await test_credential_injector_with_edge()
    
    # 测试 curl_cffi（无需浏览器）
    curl_cffi_ok = await test_curl_cffi()
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"DrissionPage (Edge): {'✅ 通过' if drission_ok else '❌ 失败'}")
    print(f"Playwright (异步): {'✅ 通过' if playwright_ok else '❌ 失败'}")
    print(f"凭证注入器：{'✅ 通过' if injector_ok else '❌ 失败'}")
    print(f"curl_cffi: {'✅ 通过' if curl_cffi_ok else '❌ 失败'}")
    
    total = sum([drission_ok, playwright_ok, injector_ok, curl_cffi_ok])
    if total == 4:
        print(f"\n🎉 所有测试通过！(4/4)")
    else:
        print(f"\n⚠️  {total}/4 测试通过，部分测试失败")


if __name__ == '__main__':
    asyncio.run(main())

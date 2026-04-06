"""
测试 DrissionPage 和 Playwright 是否能正常工作
"""
import asyncio
import time
from loguru import logger

async def test_drission():
    """测试 DrissionPage"""
    print("\n" + "="*60)
    print("测试 DrissionPage")
    print("="*60)
    
    try:
        from DrissionPage import ChromiumPage, ChromiumOptions
        
        print("✅ DrissionPage 导入成功")
        
        # 配置无头模式
        options = ChromiumOptions()
        options.headless(True)
        options.set_argument('--disable-blink-features=AutomationControlled')
        options.set_argument('--disable-dev-shm-usage')
        options.set_argument('--no-sandbox')
        
        print("启动浏览器...")
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


async def test_playwright():
    """测试 Playwright"""
    print("\n" + "="*60)
    print("测试 Playwright")
    print("="*60)
    
    try:
        from playwright.sync_api import sync_playwright
        
        print("✅ Playwright 导入成功")
        
        # 启动 Playwright
        print("启动 Playwright...")
        playwright = sync_playwright().start()
        
        try:
            # 启动浏览器
            print("启动浏览器...")
            browser = playwright.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            try:
                # 创建上下文
                print("创建浏览器上下文...")
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    locale='zh-CN',
                    timezone_id='Asia/Shanghai',
                )
                
                page = context.new_page()
                
                try:
                    # 访问网站
                    print("访问东方财富网站...")
                    start_time = time.time()
                    page.goto('https://fund.eastmoney.com/')
                    page.wait_for_load_state('networkidle')
                    elapsed = time.time() - start_time
                    print(f"✅ 页面加载成功，耗时：{elapsed:.2f}秒")
                    
                    # 获取 Cookie
                    print("获取 Cookie...")
                    cookies = context.cookies()
                    print(f"✅ 获取到 {len(cookies)} 个 Cookie")
                    
                    # 显示前 3 个 Cookie
                    for i, cookie in enumerate(cookies[:3]):
                        print(f"   Cookie {i+1}: {cookie.get('name')} = {cookie.get('value')[:50]}...")
                    
                    return True
                    
                finally:
                    print("关闭页面...")
                    page.close()
            finally:
                print("关闭上下文...")
                context.close()
                print("关闭浏览器...")
                browser.close()
        finally:
            print("停止 Playwright...")
            playwright.stop()
            
    except Exception as e:
        print(f"❌ Playwright 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


async def test_credential_injector():
    """测试凭证注入器"""
    print("\n" + "="*60)
    print("测试凭证注入器")
    print("="*60)
    
    try:
        from app.adapters.credential_injector import CredentialInjector
        
        print("创建凭证注入器...")
        injector = CredentialInjector()
        
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


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("浏览器和凭证注入测试")
    print("="*60)
    
    # 测试 DrissionPage
    drission_ok = await test_drission()
    
    # 测试 Playwright
    playwright_ok = await test_playwright()
    
    # 测试凭证注入器
    injector_ok = await test_credential_injector()
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"DrissionPage: {'✅ 通过' if drission_ok else '❌ 失败'}")
    print(f"Playwright: {'✅ 通过' if playwright_ok else '❌ 失败'}")
    print(f"凭证注入器：{'✅ 通过' if injector_ok else '❌ 失败'}")
    
    if drission_ok and playwright_ok and injector_ok:
        print("\n🎉 所有测试通过！")
    else:
        print("\n⚠️  部分测试失败，请检查错误信息")


if __name__ == '__main__':
    asyncio.run(main())

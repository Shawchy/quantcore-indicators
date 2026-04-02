import asyncio
import os
import sys

os.environ['PLAYWRIGHT_BROWSERS_PATH'] = 'd:/PROJ/Quant/backend/playwright_browsers'

async def test_simple():
    print("=" * 60)
    print("简单 Playwright 测试")
    print("=" * 60)
    
    from playwright.async_api import async_playwright
    
    print("\n1. 调用 async_playwright().start()...")
    
    try:
        playwright = await async_playwright().start()
        print(f"2. playwright 类型: {type(playwright)}")
        
        if playwright is None:
            print("错误: playwright 是 None!")
            return
        
        chromium_exe = os.path.join(
            os.environ['PLAYWRIGHT_BROWSERS_PATH'],
            'chromium-1148', 'chrome-win', 'chrome.exe'
        )
        print(f"3. Chromium 路径: {chromium_exe}")
        print(f"4. 文件存在: {os.path.exists(chromium_exe)}")
        
        browser = await playwright.chromium.launch(
            headless=True,
            executable_path=chromium_exe
        )
        print(f"5. browser: {browser}")
        
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.goto("https://www.baidu.com")
        print(f"6. title: {await page.title()}")
        
        await browser.close()
        print("\n✓ 测试成功!")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple())

import asyncio
import os
import sys

os.environ['PLAYWRIGHT_BROWSERS_PATH'] = 'd:/PROJ/Quant/backend/playwright_browsers'

async def debug_playwright():
    print("=" * 60)
    print("Playwright 调试测试")
    print("=" * 60)
    
    from playwright.async_api import async_playwright
    
    print("\n测试使用 executable_path 参数...")
    
    playwright = await async_playwright().start()
    print(f"1. playwright 类型: {type(playwright)}")
    
    chromium_exe = os.path.join(
        os.environ['PLAYWRIGHT_BROWSERS_PATH'],
        'chromium-1148', 'chrome-win', 'chrome.exe'
    )
    print(f"2. Chromium 路径: {chromium_exe}")
    print(f"3. 文件存在: {os.path.exists(chromium_exe)}")
    
    browser = await playwright.chromium.launch(
        headless=True,
        executable_path=chromium_exe
    )
    print(f"4. browser: {browser}")
    
    context = await browser.new_context()
    print(f"5. context: {context}")
    
    page = await context.new_page()
    print(f"6. page: {page}")
    
    await page.goto("https://www.baidu.com")
    print(f"7. title: {await page.title()}")
    
    await browser.close()
    print("\n✓ 测试成功!")

if __name__ == "__main__":
    asyncio.run(debug_playwright())

if __name__ == "__main__":
    asyncio.run(debug_playwright())

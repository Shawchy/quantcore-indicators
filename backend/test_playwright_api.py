import asyncio
from playwright.async_api import async_playwright

async def main():
    print("Testing Playwright API...")
    
    # 方法 1: 使用上下文管理器
    print("\n方法 1: 上下文管理器")
    async with async_playwright() as p:
        print(f"  p type: {type(p)}")
        print(f"  p.chromium: {p.chromium}")
        browser = await p.chromium.launch(headless=True)
        print(f"  browser: {browser}")
        await browser.close()
        print("  ✓ 方法 1 成功")
    
    # 方法 2: 手动 start
    print("\n方法 2: 手动 start")
    playwright = async_playwright()
    print(f"  playwright type: {type(playwright)}")
    
    result = await playwright.start()
    print(f"  start() result: {result}")
    print(f"  start() result type: {type(result)}")
    
    if result is None:
        print("  start() 返回 None，使用 playwright 对象本身")
        p = playwright
    else:
        p = result
    
    print(f"  p.chromium: {p.chromium}")
    browser = await p.chromium.launch(headless=True)
    print(f"  browser: {browser}")
    await browser.close()
    await playwright.stop()
    print("  ✓ 方法 2 成功")

if __name__ == "__main__":
    asyncio.run(main())

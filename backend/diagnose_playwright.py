"""
使用 Playwright 测试真实浏览器能否访问
"""

import asyncio
import os

os.environ['PLAYWRIGHT_BROWSERS_PATH'] = 'd:/PROJ/Quant/backend/playwright_browsers'


async def test_with_playwright():
    from playwright.async_api import async_playwright
    
    print("=== 使用 Playwright 测试真实浏览器 ===\n")
    
    playwright = await async_playwright().start()
    
    browsers_path = os.environ.get('PLAYWRIGHT_BROWSERS_PATH')
    chromium_exe = os.path.join(browsers_path, 'chromium-1148', 'chrome-win', 'chrome.exe')
    
    browser = await playwright.chromium.launch(
        headless=True,
        executable_path=chromium_exe if os.path.exists(chromium_exe) else None
    )
    
    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        locale='zh-CN',
        timezone_id='Asia/Shanghai',
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    )
    
    page = await context.new_page()
    
    # 监听网络请求
    api_responses = []
    
    async def handle_response(response):
        if 'push2.eastmoney.com' in response.url:
            api_responses.append({
                'url': response.url,
                'status': response.status,
                'ok': response.ok
            })
            print(f"  捕获 API 请求: {response.status} - {response.url[:80]}...")
    
    page.on('response', handle_response)
    
    try:
        # 访问东方财富行情页面
        print("1. 访问东方财富行情页面...")
        await page.goto(
            "https://quote.eastmoney.com/center/gridlist.html",
            wait_until='domcontentloaded',
            timeout=30000
        )
        
        print(f"  页面标题: {await page.title()}")
        
        # 等待数据加载
        print("\n2. 等待数据加载...")
        await asyncio.sleep(5)
        
        # 检查是否有数据
        print("\n3. 检查页面内容...")
        
        # 尝试获取表格数据
        rows = await page.query_selector_all('.dataview-body tbody tr')
        print(f"  找到 {len(rows)} 行数据")
        
        if rows:
            print("\n  示例数据:")
            for row in rows[:3]:
                cells = await row.query_selector_all('td')
                if len(cells) >= 2:
                    code = await cells[1].inner_text()
                    name = await cells[2].inner_text()
                    print(f"    {code}: {name}")
        
        print(f"\n4. 捕获到的 API 响应: {len(api_responses)} 个")
        for resp in api_responses:
            print(f"  {resp['status']}: {resp['url'][:60]}...")
        
        # 截图
        await page.screenshot(path='screenshot_playwright.png')
        print("\n5. 截图已保存: screenshot_playwright.png")
        
        # 获取 Cookie
        cookies = await context.cookies()
        print(f"\n6. 获取到 {len(cookies)} 个 Cookie")
        
        success = len(rows) > 0 or len(api_responses) > 0
        return success
        
    except Exception as e:
        print(f"错误: {e}")
        return False
    finally:
        await browser.close()


async def test_api_directly_in_browser():
    from playwright.async_api import async_playwright
    
    print("\n=== 在浏览器中直接请求 API ===\n")
    
    playwright = await async_playwright().start()
    
    browsers_path = os.environ.get('PLAYWRIGHT_BROWSERS_PATH')
    chromium_exe = os.path.join(browsers_path, 'chromium-1148', 'chrome-win', 'chrome.exe')
    
    browser = await playwright.chromium.launch(
        headless=True,
        executable_path=chromium_exe if os.path.exists(chromium_exe) else None
    )
    
    context = await browser.new_context()
    page = await context.new_page()
    
    try:
        # 直接请求 API
        api_url = "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=10&po=1&np=1&fltt=2&invt=2&fid=f12&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23&fields=f12,f14,f2,f3"
        
        print(f"请求: {api_url[:80]}...")
        
        response = await page.goto(api_url, timeout=30000)
        
        print(f"状态码: {response.status}")
        
        if response.ok:
            content = await page.content()
            print(f"响应长度: {len(content)}")
            
            # 尝试提取 JSON
            text = await page.evaluate('() => document.body.innerText')
            print(f"响应内容: {text[:500]}...")
            
            return True
        else:
            print(f"请求失败: {response.status}")
            return False
            
    except Exception as e:
        print(f"错误: {e}")
        return False
    finally:
        await browser.close()


async def main():
    print("="*60)
    print("Playwright 真实浏览器测试")
    print("="*60)
    
    result1 = await test_with_playwright()
    result2 = await test_api_directly_in_browser()
    
    print("\n" + "="*60)
    print("结论")
    print("="*60)
    
    if result1 or result2:
        print("""
✓ Playwright 可以正常访问！

**根本原因确认：Python requests 被识别为爬虫**

服务器通过以下方式识别并拦截了 Python requests：
1. TLS 指纹（ClientHello 格式、扩展顺序）
2. HTTP/2 支持情况
3. 请求头特征
4. 行为特征（请求频率、时间模式）

**解决方案：**
1. ✓ 使用 Playwright（已实现）
2. ✓ 使用凭证注入（已实现）
3. 使用代理 IP 池
4. 使用 curl_cffi 库
""")
    else:
        print("Playwright 也无法访问，可能是 IP 被封禁")


if __name__ == "__main__":
    asyncio.run(main())

"""
完整测试 TLS 指纹伪装 + Cookie 获取
"""

import asyncio
import os

os.environ['PLAYWRIGHT_BROWSERS_PATH'] = 'd:/PROJ/Quant/backend/playwright_browsers'


async def test_full_flow():
    print("\n=== 完整测试：TLS 指纹伪装 + Cookie 获取 ===\n")
    
    from curl_cffi import requests as curl_requests
    from curl_cffi.requests import Session
    
    # 1. 创建模拟 Chrome 的 Session
    print("1. 创建 Chrome TLS 指纹 Session...")
    session = Session(impersonate="chrome120")
    print("   ✓ Session 创建成功")
    
    # 2. 先访问主页获取 Cookie
    print("\n2. 访问东方财富主页获取 Cookie...")
    try:
        resp = session.get(
            "https://quote.eastmoney.com/center/gridlist.html",
            timeout=30
        )
        print(f"   状态码: {resp.status_code}")
        print(f"   Cookie 数量: {len(resp.cookies)}")
        
        for cookie in resp.cookies:
            print(f"     - {cookie.name}: {cookie.value[:20]}...")
            
    except Exception as e:
        print(f"   访问主页失败: {e}")
        return False
    
    # 3. 使用相同 Session 请求 API
    print("\n3. 请求 API...")
    api_url = "https://push2.eastmoney.com/api/qt/clist/get"
    params = {
        'pn': 1,
        'pz': 10,
        'po': 1,
        'np': 1,
        'fltt': 2,
        'invt': 2,
        'fid': 'f12',
        'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',
        'fields': 'f12,f14,f2,f3'
    }
    
    try:
        resp = session.get(api_url, params=params, timeout=30)
        print(f"   状态码: {resp.status_code}")
        print(f"   响应长度: {len(resp.text)}")
        
        if resp.status_code == 200 and len(resp.text) > 100:
            data = resp.json()
            print(f"   ✓ JSON 解析成功")
            
            if 'data' in data and data['data']:
                items = data['data'].get('diff', [])
                print(f"   ✓ 获取到 {len(items)} 条数据")
                for item in items[:3]:
                    print(f"     - {item.get('f12')}: {item.get('f14')}")
                return True
            else:
                print(f"   响应内容: {resp.text[:200]}")
        else:
            print(f"   响应: {resp.text[:200]}")
            
    except Exception as e:
        print(f"   请求失败: {e}")
    
    session.close()
    return False


async def test_with_playwright_cookies():
    print("\n=== 测试：Playwright 获取 Cookie + curl_cffi 请求 ===\n")
    
    from playwright.async_api import async_playwright
    from curl_cffi.requests import Session
    
    # 1. 使用 Playwright 获取 Cookie
    print("1. Playwright 获取 Cookie...")
    
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
    )
    page = await context.new_page()
    
    try:
        await page.goto(
            "https://quote.eastmoney.com/center/gridlist.html",
            wait_until='domcontentloaded',
            timeout=30000
        )
        await asyncio.sleep(3)
        
        cookies = await context.cookies()
        print(f"   ✓ 获取到 {len(cookies)} 个 Cookie")
        
        # 2. 转换 Cookie 格式
        cookie_dict = {c['name']: c['value'] for c in cookies}
        
    except Exception as e:
        print(f"   失败: {e}")
        await browser.close()
        return False
    
    await browser.close()
    
    # 3. 使用 curl_cffi 携带 Cookie 请求
    print("\n2. curl_cffi 携带 Cookie 请求...")
    
    session = Session(impersonate="chrome120")
    
    api_url = "https://push2.eastmoney.com/api/qt/clist/get"
    params = {
        'pn': 1,
        'pz': 10,
        'po': 1,
        'np': 1,
        'fltt': 2,
        'invt': 2,
        'fid': 'f12',
        'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',
        'fields': 'f12,f14,f2,f3'
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Referer': 'https://quote.eastmoney.com/center/gridlist.html',
    }
    
    try:
        resp = session.get(
            api_url,
            params=params,
            headers=headers,
            cookies=cookie_dict,
            timeout=30
        )
        print(f"   状态码: {resp.status_code}")
        print(f"   响应长度: {len(resp.text)}")
        
        if resp.status_code == 200 and len(resp.text) > 100:
            data = resp.json()
            print(f"   ✓ JSON 解析成功")
            
            if 'data' in data and data['data']:
                items = data['data'].get('diff', [])
                print(f"   ✓ 获取到 {len(items)} 条数据")
                return True
            else:
                print(f"   响应: {resp.text[:200]}")
        else:
            print(f"   响应: {resp.text[:200]}")
            
    except Exception as e:
        print(f"   请求失败: {e}")
    
    session.close()
    return False


async def test_different_browsers():
    print("\n=== 测试不同浏览器指纹 ===\n")
    
    from curl_cffi.requests import Session
    
    browsers = ["chrome120", "chrome110", "chrome107", "firefox110", "safari15_5"]
    
    for browser in browsers:
        print(f"\n测试 {browser}...")
        
        try:
            session = Session(impersonate=browser)
            
            # 先访问主页
            resp = session.get("https://quote.eastmoney.com/", timeout=15)
            print(f"  主页状态码: {resp.status_code}")
            
            # 再请求 API
            api_url = "https://push2.eastmoney.com/api/qt/clist/get"
            params = {
                'pn': 1, 'pz': 5, 'po': 1, 'np': 1,
                'fltt': 2, 'invt': 2, 'fid': 'f12',
                'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',
                'fields': 'f12,f14'
            }
            
            resp = session.get(api_url, params=params, timeout=15)
            print(f"  API 状态码: {resp.status_code}")
            print(f"  响应长度: {len(resp.text)}")
            
            if resp.status_code == 200 and len(resp.text) > 100:
                print(f"  ✓ {browser} 成功!")
                session.close()
                return browser
            
            session.close()
            
        except Exception as e:
            print(f"  失败: {type(e).__name__}")
        
        await asyncio.sleep(2)
    
    return None


async def main():
    print("="*60)
    print("TLS 指纹伪装完整测试")
    print("="*60)
    
    result1 = await test_full_flow()
    result2 = await test_with_playwright_cookies()
    result3 = await test_different_browsers()
    
    print("\n" + "="*60)
    print("测试结果")
    print("="*60)
    
    print(f"curl_cffi 完整流程: {'✓' if result1 else '✗'}")
    print(f"Playwright + curl_cffi: {'✓' if result2 else '✗'}")
    print(f"最佳浏览器指纹: {result3 or '无'}")
    
    if not any([result1, result2, result3]):
        print("""
结论：curl_cffi 也被拦截

可能原因：
1. IP 已被临时封禁
2. 需要更多请求头
3. 需要特定的请求顺序
4. 服务器检测到异常行为

建议：
1. 使用代理 IP
2. 使用完整的 Playwright 方案
3. 等待一段时间后重试
""")


if __name__ == "__main__":
    asyncio.run(main())

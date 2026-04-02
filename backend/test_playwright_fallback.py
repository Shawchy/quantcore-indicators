"""
测试 Playwright 获取高敏感 API 数据

验证 Playwright 能否成功获取：
1. A股列表
2. 板块列表
3. 实时行情
"""

import asyncio
import json
import time
from pathlib import Path


async def test_playwright_fallback():
    print("\n=== Playwright 兜底测试 ===\n")
    
    test_apis = [
        ("A股列表", "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=50&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23&fields=f12,f14,f2,f3,f4,f5,f6"),
        ("板块列表", "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=50&fs=m:90+t:2&fields=f12,f14,f2,f3,f4,f5,f6"),
        ("资金流向", "https://push2.eastmoney.com/api/qt/stock/fflow/kline/get?secid=0.000001&klt=101&lmt=10&fields1=f1,f2,f3,f7&fields2=f51,f52,f53,f54,f55,f56,f58,f60"),
    ]
    
    from playwright.async_api import async_playwright
    
    print("初始化 Playwright...")
    playwright = await async_playwright().start()
    
    executable_path = Path(__file__).parent / "playwright_browsers" / "chromium-1148" / "chrome-win" / "chrome.exe"
    
    if executable_path.exists():
        browser = await playwright.chromium.launch(
            headless=True,
            executable_path=str(executable_path),
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        )
    else:
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        )
    
    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    )
    
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']});
        window.chrome = {runtime: {}};
    """)
    
    page = await context.new_page()
    
    print("先访问首页建立会话...")
    try:
        await page.goto("https://www.eastmoney.com/", timeout=30000)
        await asyncio.sleep(1)
        print("首页访问成功")
    except Exception as e:
        print(f"首页访问失败: {e}")
    
    results = {}
    
    for name, url in test_apis:
        print(f"\n测试: {name}")
        print("-" * 50)
        
        start = time.time()
        try:
            response = await page.goto(url, timeout=30000)
            elapsed = time.time() - start
            
            if response and response.status == 200:
                content = await page.content()
                
                try:
                    text_content = await page.evaluate("() => document.body.innerText")
                    data = json.loads(text_content)
                    
                    success = data.get('data') is not None
                    data_count = 0
                    
                    if data.get('data'):
                        if 'diff' in data['data']:
                            data_count = len(data['data']['diff'])
                        elif 'klines' in data['data']:
                            data_count = len(data['data']['klines'])
                    
                    results[name] = {
                        'success': success,
                        'status': response.status,
                        'data_count': data_count,
                        'time': elapsed,
                        'has_data': data.get('data') is not None,
                    }
                    
                    print(f"  Status: {response.status}")
                    print(f"  Time: {elapsed:.2f}s")
                    print(f"  Has Data: {success}")
                    print(f"  Data Count: {data_count}")
                    
                    if data_count > 0:
                        sample_data = data['data'].get('diff', data['data'].get('klines', []))
                        if sample_data:
                            print(f"  Sample: {json.dumps(sample_data[:2] if isinstance(sample_data, list) else str(sample_data)[:200], ensure_ascii=False)}")
                    
                except json.JSONDecodeError as e:
                    results[name] = {'success': False, 'error': f'JSON parse error: {e}'}
                    print(f"  FAIL: JSON parse error")
            else:
                results[name] = {'success': False, 'status': response.status if response else None}
                print(f"  FAIL: Status {response.status if response else 'None'}")
                
        except Exception as e:
            results[name] = {'success': False, 'error': str(e)}
            print(f"  FAIL: {type(e).__name__}: {e}")
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    print("\n| API        | Status | Has Data | Data Count | Time   |")
    print("|------------|--------|----------|------------|--------|")
    
    for name, result in results.items():
        status = 'OK' if result.get('success') else 'FAIL'
        has_data = 'Yes' if result.get('has_data') else 'No'
        count = result.get('data_count', 0)
        elapsed = result.get('time', 0)
        print(f"| {name:10} | {status:6} | {has_data:8} | {count:10} | {elapsed:.2f}s |")
    
    success_count = sum(1 for r in results.values() if r.get('success'))
    print(f"\nTotal: {success_count}/{len(results)} success")
    
    await browser.close()
    await playwright.stop()
    
    return results


if __name__ == "__main__":
    asyncio.run(test_playwright_fallback())

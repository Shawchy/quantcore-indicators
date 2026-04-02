"""
凭证注入功能测试脚本

测试 Playwright 获取凭证 → AKShare 使用的方案

使用方法：
    python test_credential_injector.py
"""

import asyncio
import os

os.environ['PLAYWRIGHT_BROWSERS_PATH'] = 'd:/PROJ/Quant/backend/playwright_browsers'


async def test_credential_injector():
    print("\n" + "="*60)
    print("测试：Playwright 获取凭证 → AKShare 使用")
    print("="*60)
    
    from app.adapters.credential_injector import CredentialInjector
    
    injector = CredentialInjector({
        'headless': True,
        'cookie_max_age_hours': 24,
    })
    
    print("\n1. 初始化凭证注入器...")
    success = await injector.initialize()
    
    if not success:
        print("✗ 初始化失败")
        return False
    
    print("✓ 初始化成功")
    
    print("\n2. 获取东方财富凭证...")
    success = await injector.fetch_credentials('eastmoney.com')
    
    if not success:
        print("✗ 获取凭证失败")
        await injector.close()
        return False
    
    print("✓ 获取凭证成功")
    
    cookies = injector.get_cookies('eastmoney.com')
    print(f"\n3. 获取到的 Cookie 数量: {len(cookies)}")
    
    if cookies:
        print("\nCookie 示例:")
        for cookie in cookies[:5]:
            print(f"  - {cookie.get('name')}: {cookie.get('value', '')[:30]}...")
    
    cookie_dict = injector.get_cookie_dict('eastmoney.com')
    print(f"\nCookie 字典: {len(cookie_dict)} 个键")
    
    headers = injector.get_headers('eastmoney.com')
    print(f"\nHeaders:")
    for key, value in headers.items():
        print(f"  {key}: {value[:50]}..." if len(str(value)) > 50 else f"  {key}: {value}")
    
    print("\n4. 注入凭证到 requests...")
    success = injector.patch_requests('eastmoney.com')
    
    if success:
        print("✓ 凭证注入成功")
    else:
        print("✗ 凭证注入失败")
        await injector.close()
        return False
    
    print("\n5. 使用 AKShare 获取数据（凭证已注入）...")
    
    try:
        import akshare as ak
        
        print("\n获取 A 股实时行情...")
        df = ak.stock_zh_a_spot_em()
        print(f"✓ 获取成功: {len(df)} 条数据")
        if len(df) > 0:
            print(f"  示例: {df.iloc[0]['代码']} {df.iloc[0]['名称']}")
        
    except Exception as e:
        print(f"✗ AKShare 调用失败: {e}")
    
    print("\n6. 恢复原始 requests...")
    injector.unpatch_requests()
    print("✓ 已恢复")
    
    print("\n7. 关闭凭证注入器...")
    await injector.close()
    print("✓ 已关闭")
    
    return True


async def test_akshare_with_credential():
    print("\n" + "="*60)
    print("测试：AkShareWithCredential 上下文管理器")
    print("="*60)
    
    from app.adapters.credential_injector import AkShareWithCredential
    
    print("\n使用上下文管理器...")
    
    async with AkShareWithCredential() as akshare:
        print("✓ 初始化完成，凭证已注入")
        
        status = akshare.get_status()
        print(f"\n状态: {status}")
        
        print("\n获取 A 股实时行情...")
        try:
            df = akshare.get_stock_zh_a_spot()
            print(f"✓ 获取成功: {len(df)} 条数据")
        except Exception as e:
            print(f"获取失败: {e}")
        
        print("\n获取个股信息...")
        try:
            df = akshare.get_stock_individual_info("000001")
            print(f"✓ 获取成功")
            print(df)
        except Exception as e:
            print(f"获取失败: {e}")
    
    print("\n✓ 上下文管理器已退出，资源已清理")
    return True


async def test_manual_injection():
    print("\n" + "="*60)
    print("测试：手动注入凭证到 requests.Session")
    print("="*60)
    
    from app.adapters.credential_injector import CredentialInjector
    import requests
    
    injector = CredentialInjector({'headless': True})
    
    print("\n1. 初始化并获取凭证...")
    await injector.initialize()
    await injector.fetch_credentials('eastmoney.com')
    
    cookies = injector.get_cookie_dict('eastmoney.com')
    headers = injector.get_headers('eastmoney.com')
    
    print(f"✓ Cookie: {len(cookies)} 个")
    print(f"✓ Headers: {len(headers)} 个")
    
    print("\n2. 创建带凭证的 Session...")
    session = requests.Session()
    session.cookies.update(cookies)
    session.headers.update(headers)
    
    print("✓ Session 已配置")
    
    print("\n3. 使用 Session 访问东方财富...")
    try:
        response = session.get(
            "https://push2.eastmoney.com/api/qt/clist/get",
            params={
                'pn': 1,
                'pz': 10,
                'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',
                'fields': 'f12,f14,f2,f3,f4,f5,f6'
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ 请求成功: {response.status_code}")
            
            if data.get('data') and data['data'].get('diff'):
                print(f"  获取到 {len(data['data']['diff'])} 条数据")
                for item in data['data']['diff'][:3]:
                    print(f"    - {item.get('f12')}: {item.get('f14')}")
        else:
            print(f"✗ 请求失败: {response.status_code}")
            
    except Exception as e:
        print(f"✗ 请求异常: {e}")
    
    await injector.close()
    return True


async def main():
    print("\n" + "="*60)
    print("凭证注入功能测试")
    print("="*60)
    
    tests = [
        ("凭证注入器基础功能", test_credential_injector),
        ("AkShareWithCredential 上下文管理器", test_akshare_with_credential),
        ("手动注入到 Session", test_manual_injection),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} 测试异常: {e}")
            import traceback
            traceback.print_exc()
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


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n✗ 测试程序异常: {e}")

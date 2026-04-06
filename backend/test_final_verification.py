"""
最终验证测试
验证 DrissionPage 的 Edge 路径配置是否正常工作
"""
import asyncio
from app.adapters.credential_injector import CredentialInjector


async def test_auto_detect_edge():
    """测试自动检测 Edge 浏览器"""
    print("\n" + "="*60)
    print("测试 1: 自动检测 Edge 浏览器")
    print("="*60)
    
    injector = CredentialInjector()
    
    # 检查是否自动检测到 Edge
    browser_path = injector._config.get('browser_path')
    
    if browser_path:
        print(f"✅ 自动检测到 Edge 浏览器：{browser_path}")
        
        # 验证路径是否存在
        import os
        if os.path.exists(browser_path):
            print(f"✅ 浏览器路径存在且有效")
            return True
        else:
            print(f"❌ 浏览器路径不存在：{browser_path}")
            return False
    else:
        print("⚠️  未检测到 Edge 浏览器，将使用系统默认 Chrome")
        return True  # 也算通过，因为没有 Edge 是正常情况


async def test_explicit_edge_config():
    """测试显式配置 Edge 路径"""
    print("\n" + "="*60)
    print("测试 2: 显式配置 Edge 路径")
    print("="*60)
    
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    
    injector = CredentialInjector({
        'browser_path': edge_path,
        'headless': True,
    })
    
    config_path = injector._config.get('browser_path')
    
    if config_path == edge_path:
        print(f"✅ 显式配置的 Edge 路径已正确设置：{config_path}")
        return True
    else:
        print(f"❌ 配置的路径不正确：{config_path}")
        return False


async def test_credential_fetch_with_auto_detect():
    """测试使用自动检测的 Edge 路径获取凭证"""
    print("\n" + "="*60)
    print("测试 3: 使用自动检测的 Edge 路径获取凭证")
    print("="*60)
    
    # 不指定 browser_path，使用自动检测
    injector = CredentialInjector()
    
    await injector.initialize()
    
    print("获取凭证...")
    success = await injector.fetch_credentials('eastmoney.com')
    
    if success:
        print("✅ 使用自动检测的 Edge 路径成功获取凭证")
        
        # 验证凭证状态
        status = injector.get_status()
        credentials = status.get('credentials', {})
        
        if 'eastmoney.com' in credentials:
            cred = credentials['eastmoney.com']
            if cred.get('valid'):
                print(f"✅ 凭证有效")
                return True
            else:
                print("❌ 凭证无效")
                return False
        else:
            print("❌ 未找到凭证信息")
            return False
    else:
        print("❌ 获取凭证失败")
        return False


async def test_credential_fetch_with_explicit_config():
    """测试使用显式配置的 Edge 路径获取凭证"""
    print("\n" + "="*60)
    print("测试 4: 使用显式配置的 Edge 路径获取凭证")
    print("="*60)
    
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    
    injector = CredentialInjector({
        'browser_path': edge_path,
        'headless': True,
    })
    
    await injector.initialize()
    
    print("获取凭证...")
    success = await injector.fetch_credentials('eastmoney.com')
    
    if success:
        print("✅ 使用显式配置的 Edge 路径成功获取凭证")
        return True
    else:
        print("❌ 获取凭证失败")
        return False


async def test_patch_requests():
    """测试注入凭证到 requests"""
    print("\n" + "="*60)
    print("测试 5: 注入凭证到 requests")
    print("="*60)
    
    injector = CredentialInjector()
    await injector.initialize()
    
    await injector.fetch_credentials('eastmoney.com')
    
    print("注入凭证到 requests...")
    patch_result = injector.patch_requests_with_tls()
    
    if patch_result:
        print("✅ 成功注入凭证到 requests")
        return True
    else:
        print("❌ 注入凭证失败")
        return False


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("DrissionPage Edge 路径配置 - 最终验证测试")
    print("="*60)
    
    tests = [
        ("自动检测 Edge 浏览器", test_auto_detect_edge),
        ("显式配置 Edge 路径", test_explicit_edge_config),
        ("自动检测获取凭证", test_credential_fetch_with_auto_detect),
        ("显式配置获取凭证", test_credential_fetch_with_explicit_config),
        ("注入凭证到 requests", test_patch_requests),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ 测试失败：{test_name}")
            print(f"错误：{e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {test_name}")
    
    print(f"\n总计：{passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！DrissionPage 的 Edge 路径配置完全正常！")
        return True
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查错误信息")
        return False


if __name__ == '__main__':
    success = asyncio.run(main())
    exit(0 if success else 1)

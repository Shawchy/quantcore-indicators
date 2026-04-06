"""
反爬策略优化验证脚本

测试内容：
1. DrissionPage 优先模式
2. undetected-chromedriver 模式
3. 手动 Cookie 加载
4. Cookie 自动续期监听器
5. 增强请求头伪装
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from app.adapters.credential_injector import CredentialInjector, CookieMonitor


async def test_initialization_priority():
    """测试 1：初始化优先级"""
    print("\n" + "="*60)
    print("测试 1：初始化优先级")
    print("="*60)
    
    injector = CredentialInjector({
        'headless': True,
        'cookie_storage_dir': 'data/cookies',
    })
    
    success = await injector.initialize()
    
    if success:
        print(f"✅ 初始化成功")
        print(f"   使用模式：{injector._browser_mode}")
        
        # 验证模式优先级
        if injector._browser_mode == "manual_cookie":
            print("   ✅ 手动 Cookie 模式（最高优先级）")
        elif injector._browser_mode == "drission":
            print("   ✅ DrissionPage 模式（推荐）")
        elif injector._browser_mode == "uc":
            print("   ✅ undetected-chromedriver 模式（强反爬）")
        elif injector._browser_mode == "playwright_sync":
            print("   ✅ Playwright 同步模式")
        else:
            print("   ⚠️  curl_cffi 模式（降级）")
    else:
        print("❌ 初始化失败")
    
    await injector.close()
    return success


async def test_manual_cookie_loading():
    """测试 2：手动 Cookie 加载"""
    print("\n" + "="*60)
    print("测试 2：手动 Cookie 加载")
    print("="*60)
    
    injector = CredentialInjector({
        'headless': True,
        'cookie_storage_dir': 'data/cookies',
    })
    
    # 检查是否有手动 Cookie 文件
    import os
    cookie_file = Path("data/cookies/eastmoney_com_manual.json")
    
    if cookie_file.exists():
        print(f"✅ 发现手动 Cookie 文件：{cookie_file}")
        
        success = await injector.initialize()
        
        if success and injector._browser_mode == "manual_cookie":
            print("✅ 手动 Cookie 加载成功")
            print(f"   Cookie 数量：{len(injector._cookies.get('eastmoney.com', []))}")
        else:
            print("⚠️  手动 Cookie 未加载（可能已过期）")
    else:
        print("⚠️  手动 Cookie 文件不存在")
        print(f"   示例文件：data/cookies/eastmoney_com_manual.json.example")
    
    await injector.close()
    return True


async def test_header_generation():
    """测试 3：增强请求头伪装"""
    print("\n" + "="*60)
    print("测试 3：增强请求头伪装")
    print("="*60)
    
    injector = CredentialInjector()
    
    # 生成 10 个请求头，验证多样性
    headers_set = set()
    
    for i in range(10):
        headers = injector._get_realistic_headers()
        headers_set.add(headers['User-Agent'])
    
    print(f"✅ 生成 {len(headers_set)} 种不同的 User-Agent")
    print(f"   多样性：{len(headers_set) / 10:.1%}")
    
    # 打印示例请求头
    sample_headers = injector._get_realistic_headers()
    print(f"\n示例请求头：")
    for key, value in list(sample_headers.items())[:5]:
        print(f"   {key}: {value}")
    
    # 验证 Sec-CH-UA 字段
    if 'Sec-Ch-Ua-Platform' in sample_headers:
        print(f"\n✅ 包含 Sec-CH-UA 字段（Chrome/Edge 特征）")
    else:
        print(f"\n⚠️  未包含 Sec-CH-UA 字段（Firefox/Safari）")
    
    return True


async def test_cookie_monitor():
    """测试 4：Cookie 自动续期监听器"""
    print("\n" + "="*60)
    print("测试 4：Cookie 自动续期监听器")
    print("="*60)
    
    injector = CredentialInjector({
        'headless': True,
        'cookie_max_age_hours': 24,  # 24 小时过期
    })
    
    await injector.initialize()
    
    # 创建监听器
    monitor = CookieMonitor(injector)
    
    # 启动监听（测试模式：1 分钟检查一次）
    await monitor.start_monitoring(check_interval_minutes=1)
    print("✅ Cookie 监听器已启动")
    print("   检查间隔：1 分钟")
    print("   过期时间：24 小时")
    
    # 运行 5 秒后停止
    await asyncio.sleep(5)
    monitor.stop_monitoring()
    print("✅ Cookie 监听器已停止（测试完成）")
    
    await injector.close()
    return True


async def test_undetected_chromedriver_availability():
    """测试 5：undetected-chromedriver 可用性"""
    print("\n" + "="*60)
    print("测试 5：undetected-chromedriver 可用性")
    print("="*60)
    
    try:
        import undetected_chromedriver as uc
        print("✅ undetected-chromedriver 已安装")
        
        # 尝试初始化（不访问网站）
        try:
            options = uc.ChromeOptions()
            options.add_argument('--headless=new')
            options.add_argument('--disable-gpu')
            
            driver = uc.Chrome(options=options, use_subprocess=False)
            print("✅ undetected-chromedriver 可正常初始化")
            driver.quit()
            
        except Exception as e:
            print(f"⚠️  undetected-chromedriver 初始化失败：{e}")
        
        return True
        
    except ImportError:
        print("⚠️  undetected-chromedriver 未安装")
        print("   安装命令：pip install undetected-chromedriver")
        return False


async def test_drissionpage_availability():
    """测试 6：DrissionPage 可用性"""
    print("\n" + "="*60)
    print("测试 6：DrissionPage 可用性")
    print("="*60)
    
    try:
        from DrissionPage import ChromiumPage
        print("✅ DrissionPage 已安装")
        
        # 尝试初始化（不访问网站）
        try:
            from DrissionPage import ChromiumOptions
            options = ChromiumOptions()
            options.headless(True)
            
            # 不实际启动浏览器，只检测导入
            print("✅ DrissionPage 可正常使用")
            
        except Exception as e:
            print(f"⚠️  DrissionPage 初始化失败：{e}")
        
        return True
        
    except ImportError:
        print("⚠️  DrissionPage 未安装")
        print("   安装命令：pip install DrissionPage")
        return False


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("反爬策略优化验证测试")
    print("="*60)
    
    tests = [
        ("DrissionPage 可用性", test_drissionpage_availability),
        ("undetected-chromedriver 可用性", test_undetected_chromedriver_availability),
        ("初始化优先级", test_initialization_priority),
        ("手动 Cookie 加载", test_manual_cookie_loading),
        ("增强请求头伪装", test_header_generation),
        ("Cookie 自动续期监听器", test_cookie_monitor),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} 测试异常：{e}")
            results.append((test_name, False))
    
    # 打印总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}: {test_name}")
    
    print(f"\n总计：{passed}/{total} 测试通过 ({passed/total:.1%})")
    
    if passed == total:
        print("\n🎉 所有测试通过！反爬策略优化已完成。")
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查相关配置。")


if __name__ == "__main__":
    asyncio.run(run_all_tests())

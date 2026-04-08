"""
测试 AntiWindFacade 重构

验证新的反爬策略门面是否正常工作。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.adapters.anti_wind.facade import AntiWindFacade
from app.adapters.anti_wind.strategies.base import BaseStrategy


async def test_facade_initialization():
    """测试 1：Facade 初始化"""
    print("\n" + "="*60)
    print("测试 1: AntiWindFacade 初始化")
    print("="*60)
    
    facade = AntiWindFacade({
        'enable_cookie_inject': True,
        'enable_tls_fingerprint': True,
        'enable_rate_limit': True,
        'enable_ua_rotation': True,
        'enable_smart_retry': True,
        'max_retries': 3,
        'min_delay': 0.5,
        'max_delay': 1.0,
    })
    
    print(f"\n✅ Facade 初始化成功")
    print(f"策略数量：{len(facade.strategies)}")
    
    facade.print_status()
    
    return True


async def test_single_strategy():
    """测试 2: 单个策略执行"""
    print("\n" + "="*60)
    print("测试 2: 单个策略执行")
    print("="*60)
    
    facade = AntiWindFacade({
        'enable_cookie_inject': True,
        'enable_tls_fingerprint': False,
        'enable_rate_limit': False,
        'enable_ua_rotation': True,
        'enable_smart_retry': False,
    })
    
    print(f"\n启用的策略：{facade.get_enabled_strategies()}")
    
    # 测试 UA 轮换
    ua_strategy = facade.get_strategy('UARotatorStrategy')
    if ua_strategy:
        print(f"UA 池大小：{ua_strategy.get_ua_pool_size()}")
        print(f"当前 UA: {ua_strategy.get_current_ua()[:50]}...")
    
    return True


async def test_mock_request():
    """测试 3: 模拟请求"""
    print("\n" + "="*60)
    print("测试 3: 模拟请求（使用 AntiWindFacade）")
    print("="*60)
    
    facade = AntiWindFacade({
        'enable_cookie_inject': True,
        'enable_tls_fingerprint': False,  # 避免需要 curl_cffi
        'enable_rate_limit': True,
        'enable_ua_rotation': True,
        'enable_smart_retry': True,
        'max_retries': 2,
        'min_delay': 0.1,
        'max_delay': 0.3,
    })
    
    # 模拟请求函数
    async def mock_request(url: str, method: str, headers: Dict, **kwargs):
        print(f"\n📞 模拟请求：{method} {url}")
        print(f"Headers: {len(headers)} 个")
        print(f"UA: {headers.get('User-Agent', 'N/A')[:50]}...")
        print(f"Cookie: {'Cookie' in headers}")
        
        # 返回模拟响应
        return {'status': 'success', 'url': url}
    
    try:
        result = await facade.execute_with_strategies(
            request_func=mock_request,
            url='https://example.com/api/test',
            method='GET'
        )
        
        print(f"\n✅ 请求成功：{result}")
        return True
        
    except Exception as e:
        print(f"\n❌ 请求失败：{e}")
        return False


async def test_strategy_enable_disable():
    """测试 4: 策略启用/禁用"""
    print("\n" + "="*60)
    print("测试 4: 策略启用/禁用")
    print("="*60)
    
    facade = AntiWindFacade({
        'enable_cookie_inject': True,
        'enable_tls_fingerprint': True,
        'enable_rate_limit': True,
        'enable_ua_rotation': True,
        'enable_smart_retry': False,
    })
    
    print(f"\n初始状态：{facade.get_strategy_status()}")
    
    # 禁用 UA 轮换
    facade.disable_strategy('UARotatorStrategy')
    print(f"\n禁用 UA 轮换后：{facade.get_strategy_status()}")
    
    # 重新启用
    facade.enable_strategy('UARotatorStrategy')
    print(f"\n重新启用后：{facade.get_strategy_status()}")
    
    return True


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("AntiWindFacade 重构测试")
    print("="*60)
    
    tests = [
        ("Facade 初始化", test_facade_initialization),
        ("单个策略执行", test_single_strategy),
        ("模拟请求", test_mock_request),
        ("策略启用/禁用", test_strategy_enable_disable),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} 测试异常：{e}")
            import traceback
            traceback.print_exc()
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
        print("\n🎉 所有测试通过！AntiWindFacade 重构成功。")
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查。")


if __name__ == "__main__":
    # 需要 Dict 类型提示
    from typing import Dict
    
    asyncio.run(run_all_tests())

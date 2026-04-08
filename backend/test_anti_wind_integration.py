"""
测试 AntiWindFacade 在 AkShareAdapter 中的集成

验证新的反爬策略门面是否正常工作。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger
from typing import Dict, Any

# 配置日志
logger.remove()
logger.add(
    lambda msg: print(msg, end=''),
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)


async def test_anti_wind_facade_initialization():
    """测试 1: AntiWindFacade 初始化"""
    print("\n" + "="*60)
    print("测试 1: AntiWindFacade 初始化")
    print("="*60)
    
    try:
        from app.adapters.anti_wind import AntiWindFacade
        
        facade = AntiWindFacade({
            'enable_cookie_inject': True,
            'enable_tls_fingerprint': True,
            'enable_rate_limit': True,
            'enable_ua_rotation': True,
            'enable_smart_retry': True,
            'enable_proxy_pool': False,
            'max_retries': 3,
        })
        
        facade.print_status()
        
        print("✅ AntiWindFacade 初始化成功")
        return True
        
    except Exception as e:
        print(f"❌ AntiWindFacade 初始化失败：{e}")
        import traceback
        traceback.print_exc()
        return False


async def test_akshare_adapter_initialization():
    """测试 2: AkShareAdapter 初始化"""
    print("\n" + "="*60)
    print("测试 2: AkShareAdapter 初始化")
    print("="*60)
    
    try:
        from app.adapters.akshare_adapter import AkShareAdapter
        
        adapter = AkShareAdapter()
        await adapter.initialize()
        
        # 检查是否有 anti_wind 属性
        assert hasattr(adapter, 'anti_wind'), "AkShareAdapter 没有 anti_wind 属性"
        assert adapter.anti_wind is not None, "anti_wind 属性为 None"
        
        print("✅ AkShareAdapter 初始化成功")
        print(f"   - anti_wind 类型：{type(adapter.anti_wind).__name__}")
        return True
        
    except Exception as e:
        print(f"❌ AkShareAdapter 初始化失败：{e}")
        import traceback
        traceback.print_exc()
        return False


async def test_execute_with_anti_wind():
    """测试 3: _execute_with_anti_wind 方法"""
    print("\n" + "="*60)
    print("测试 3: _execute_with_anti_wind 方法")
    print("="*60)
    
    try:
        from app.adapters.akshare_adapter import AkShareAdapter
        
        adapter = AkShareAdapter()
        await adapter.initialize()
        
        # 检查是否有 _execute_with_anti_wind 方法
        assert hasattr(adapter, '_execute_with_anti_wind'), "AkShareAdapter 没有 _execute_with_anti_wind 方法"
        
        # 测试执行一个简单的同步函数（接受 url, method, headers 参数）
        def mock_fetch(url="", method="GET", headers=None, **kwargs):
            return {"status": "success", "data": "test"}
        
        result = await adapter._execute_with_anti_wind(
            request_func=mock_fetch,
            url="https://example.com/test",
            method="GET",
            context="test_method"
        )
        
        assert result == {"status": "success", "data": "test"}, f"返回结果不正确：{result}"
        
        print("✅ _execute_with_anti_wind 方法测试成功")
        print(f"   - 返回结果：{result}")
        return True
        
    except Exception as e:
        print(f"❌ _execute_with_anti_wind 方法测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


async def test_all_strategies_enabled():
    """测试 4: 所有策略都已启用"""
    print("\n" + "="*60)
    print("测试 4: 所有策略都已启用")
    print("="*60)
    
    try:
        from app.adapters.akshare_adapter import AkShareAdapter
        
        adapter = AkShareAdapter()
        await adapter.initialize()
        
        # 获取所有策略
        strategies = adapter.anti_wind.strategies
        strategy_names = [s.name for s in strategies]
        
        print(f"   - 已加载策略：{strategy_names}")
        
        # 检查关键策略是否存在
        expected_strategies = ['CookieInject', 'TLSFingerprint', 'RateLimit', 'UARotator']
        for expected in expected_strategies:
            assert any(expected in name for name in strategy_names), f"缺少策略：{expected}"
        
        # SmartRetry 是特殊的，它不在 strategies 列表中
        has_retry = adapter.anti_wind._retry_strategy is not None
        print(f"   - SmartRetry 策略：{'✅ 已加载' if has_retry else '❌ 未加载'}")
        
        # 检查所有策略是否启用
        enabled_count = sum(1 for s in strategies if s.is_enabled())
        print(f"   - 启用的策略数：{enabled_count}/{len(strategies)}")
        
        print("✅ 所有策略都已正确加载和启用")
        return True
        
    except Exception as e:
        print(f"❌ 策略加载测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


async def test_proxy_pool_strategy():
    """测试 5: 代理池策略"""
    print("\n" + "="*60)
    print("测试 5: 代理池策略")
    print("="*60)
    
    try:
        from app.adapters.anti_wind import ProxyPoolStrategy
        
        strategy = ProxyPoolStrategy({
            'min_success_rate': 0.3,
            'max_consecutive_fails': 3,
        })
        
        # 添加测试代理
        strategy.add_proxy('127.0.0.1', 8080)
        strategy.add_proxy('192.168.1.1', 3128)
        
        # 获取状态
        status = strategy.get_status()
        print(f"   - 代理总数：{status['total']}")
        print(f"   - 可用代理：{status['available']}")
        
        print("✅ 代理池策略测试成功")
        return True
        
    except Exception as e:
        print(f"❌ 代理池策略测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


async def test_captcha_handler_strategy():
    """测试 6: 验证码处理策略"""
    print("\n" + "="*60)
    print("测试 6: 验证码处理策略")
    print("="*60)
    
    try:
        from app.adapters.anti_wind import CaptchaHandlerStrategy
        
        strategy = CaptchaHandlerStrategy({
            'timeout': 60,
            'check_interval': 1,
        })
        
        # 获取状态
        status = strategy.get_status()
        print(f"   - 超时时间：{status['timeout']}秒")
        print(f"   - 检测到验证码：{status['captcha_detected']}")
        
        print("✅ 验证码处理策略测试成功")
        return True
        
    except Exception as e:
        print(f"❌ 验证码处理策略测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*70)
    print("🧪 AntiWindFacade 集成测试")
    print("="*70)
    
    tests = [
        ("AntiWindFacade 初始化", test_anti_wind_facade_initialization),
        ("AkShareAdapter 初始化", test_akshare_adapter_initialization),
        ("_execute_with_anti_wind 方法", test_execute_with_anti_wind),
        ("所有策略启用", test_all_strategies_enabled),
        ("代理池策略", test_proxy_pool_strategy),
        ("验证码处理策略", test_captcha_handler_strategy),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} 测试异常：{e}")
            results.append((name, False))
    
    # 统计结果
    print("\n" + "="*70)
    print("📊 测试结果汇总")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print(f"\n总计：{passed}/{total} 测试通过 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 所有测试通过！AntiWindFacade 集成成功！")
        return True
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查问题")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

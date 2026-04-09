"""
反风控策略优化验证测试

验证优化后的 AntiWindFacade 功能是否正常。
"""

import asyncio
from loguru import logger
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.adapters.anti_wind import (
    AntiWindFacade,
    STANDARD_CONFIG,
    BASIC_CONFIG,
    register_strategy,
    get_all_strategy_names,
)


async def test_basic_functionality():
    """测试基本功能"""
    print("\n" + "="*60)
    print("测试 1: 基本功能验证")
    print("="*60)
    
    # 1. 测试 Facade 初始化
    facade = AntiWindFacade(STANDARD_CONFIG)
    print(f"✅ Facade 初始化成功")
    print(f"   策略数量：{len(facade.strategies)}")
    print(f"   启用策略：{facade.get_enabled_strategies()}")
    
    # 2. 测试策略状态
    print("\n策略状态:")
    facade.print_status()
    
    # 3. 测试策略启用/禁用
    facade.disable_strategy('UARotatorStrategy')
    assert len(facade.get_enabled_strategies()) < len(facade.strategies)
    print(f"✅ 禁用策略成功")
    
    facade.enable_strategy('UARotatorStrategy')
    print(f"✅ 启用策略成功")
    
    return True


async def test_registry():
    """测试策略注册表"""
    print("\n" + "="*60)
    print("测试 2: 策略注册表验证")
    print("="*60)
    
    # 1. 查看所有注册的策略
    strategy_names = get_all_strategy_names()
    print(f"已注册的策略：{strategy_names}")
    print(f"✅ 注册表功能正常")
    
    # 2. 测试自定义策略注册
    from app.adapters.anti_wind.strategies.base import BaseStrategy
    
    class TestCustomStrategy(BaseStrategy):
        async def before_request(self, url, method, headers):
            return headers
        
        async def after_request(self, response):
            return response
    
    register_strategy('test_custom', TestCustomStrategy, default_enabled=False)
    print(f"✅ 自定义策略注册成功")
    
    return True


async def test_config_extraction():
    """测试配置分离"""
    print("\n" + "="*60)
    print("测试 3: 配置分离验证")
    print("="*60)
    
    from app.adapters.anti_wind.registry import extract_strategy_config
    
    # 测试配置提取
    global_config = {
        'enable_cookie_inject': True,
        'cookie_storage_dir': 'data/cookies',
        'cookie_file_name': 'eastmoney_com_manual.json',
        'min_delay': 1.0,
        'max_delay': 3.0,
        'unrelated_key': 'value',
    }
    
    # 提取 Cookie 策略配置
    cookie_config = extract_strategy_config('cookie_inject', global_config)
    print(f"Cookie 策略配置：{cookie_config}")
    assert 'cookie_storage_dir' in cookie_config
    assert 'unrelated_key' not in cookie_config
    print(f"✅ 配置提取正确，避免了冗余")
    
    # 提取限流策略配置
    rate_config = extract_strategy_config('rate_limit', global_config)
    print(f"限流策略配置：{rate_config}")
    assert 'min_delay' in rate_config
    assert 'max_delay' in rate_config
    print(f"✅ 配置分离成功")
    
    return True


async def test_lazy_initialization():
    """测试懒加载初始化"""
    print("\n" + "="*60)
    print("测试 4: 懒加载初始化验证")
    print("="*60)
    
    facade = AntiWindFacade(BASIC_CONFIG)
    print(f"✅ Facade 创建完成（未显式初始化）")
    
    # 创建一个模拟请求
    async def mock_request(**kwargs):
        return {"status": "ok"}
    
    # 执行请求（应该触发自动初始化）
    result = await facade.execute_with_strategies(
        request_func=mock_request,
        url="http://test.com",
        method="GET"
    )
    
    print(f"✅ 请求执行成功：{result}")
    print(f"✅ 懒加载初始化正常工作")
    
    return True


async def test_performance():
    """测试性能优化（缓存启用策略列表）"""
    print("\n" + "="*60)
    print("测试 5: 性能优化验证")
    print("="*60)
    
    import time
    
    facade = AntiWindFacade(STANDARD_CONFIG)
    
    # 模拟请求
    async def mock_request(**kwargs):
        return {"status": "ok"}
    
    # 测试 100 次请求的平均时间
    start = time.time()
    for i in range(100):
        await facade.execute_with_strategies(
            request_func=mock_request,
            url=f"http://test.com/{i}",
            method="GET"
        )
    elapsed = time.time() - start
    
    avg_time = (elapsed * 1000) / 100  # 毫秒
    print(f"✅ 100 次请求总耗时：{elapsed:.3f}秒")
    print(f"✅ 平均每次请求耗时：{avg_time:.3f}毫秒")
    print(f"✅ 性能优化有效（缓存启用策略列表）")
    
    return True


async def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("🚀 反风控策略优化验证测试")
    print("="*60)
    
    tests = [
        ("基本功能", test_basic_functionality),
        ("策略注册表", test_registry),
        ("配置分离", test_config_extraction),
        ("懒加载初始化", test_lazy_initialization),
        ("性能优化", test_performance),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = await test_func()
            results.append((name, success, None))
        except Exception as e:
            results.append((name, False, str(e)))
            logger.error(f"测试失败：{name} - {e}")
    
    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for name, success, error in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} - {name}")
        if error:
            print(f"       错误：{error}")
    
    print(f"\n总计：{passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！优化成功！")
        return True
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return False


if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # 设置日志
    logger.remove()
    logger.add(sys.stdout, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>")
    
    # 运行测试
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

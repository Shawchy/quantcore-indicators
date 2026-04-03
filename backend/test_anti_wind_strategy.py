"""
反风控策略验证测试

测试项目：
1. 启动时间测试（懒加载验证）
2. 凭证注入器核心方法验证
3. 高敏感 API 测试
4. 智能重试测试
"""

import asyncio
import time
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from app.adapters.akshare_adapter import AkShareAdapter
from app.adapters.efinance_adapter import EFinanceAdapter
from app.adapters.credential_injector import CredentialInjector
from loguru import logger


async def test_startup_time():
    """测试 1: 启动时间测试（懒加载验证）"""
    print("\n" + "="*60)
    print("测试 1: 启动时间测试（懒加载验证）")
    print("="*60)
    
    start_time = time.time()
    
    # 初始化 AkShare 适配器
    ak_adapter = AkShareAdapter()
    ak_success = await ak_adapter.initialize()
    ak_elapsed = time.time() - start_time
    
    # 初始化 EFinance 适配器
    ef_start = time.time()
    ef_adapter = EFinanceAdapter()
    ef_success = await ef_adapter.initialize()
    ef_elapsed = time.time() - ef_start
    
    print(f"\n✅ AkShare 适配器初始化:")
    print(f"   - 状态：{'成功' if ak_success else '失败'}")
    print(f"   - 耗时：{ak_elapsed:.3f}秒")
    print(f"   - 预期：< 1.0 秒")
    print(f"   - 结果：{'✅ 通过' if ak_elapsed < 1.0 else '❌ 失败'}")
    
    print(f"\n✅ EFinance 适配器初始化:")
    print(f"   - 状态：{'成功' if ef_success else '失败'}")
    print(f"   - 耗时：{ef_elapsed:.3f}秒")
    print(f"   - 预期：< 1.0 秒")
    print(f"   - 结果：{'✅ 通过' if ef_elapsed < 1.0 else '❌ 失败'}")
    
    # 验证懒加载
    print(f"\n📋 懒加载验证:")
    print(f"   - AkShare 适配器 _injector 已创建：{hasattr(ak_adapter, '_injector')}")
    print(f"   - AkShare 适配器 _injector._is_patched: {ak_adapter._injector._is_patched if hasattr(ak_adapter, '_injector') else 'N/A'}")
    print(f"   - EFinance 适配器 _injector 已创建：{hasattr(ef_adapter, '_injector')}")
    print(f"   - EFinance 适配器 _injector._is_patched: {ef_adapter._injector._is_patched if hasattr(ef_adapter, '_injector') else 'N/A'}")
    
    return ak_elapsed < 1.0 and ef_elapsed < 1.0


async def test_credential_injector_methods():
    """测试 2: 凭证注入器核心方法验证"""
    print("\n" + "="*60)
    print("测试 2: 凭证注入器核心方法验证")
    print("="*60)
    
    injector = CredentialInjector({
        'tls_patch_mode': 'curl_cffi',
        'impersonate': 'chrome120',
        'headless': True,
    })
    
    # 验证方法存在
    print(f"\n📋 方法存在性验证:")
    print(f"   - initialize() 方法：{'✅ 存在' if hasattr(injector, 'initialize') else '❌ 不存在'}")
    print(f"   - fetch_credentials() 方法：{'✅ 存在' if hasattr(injector, 'fetch_credentials') else '❌ 不存在'}")
    print(f"   - patch_requests_with_tls() 方法：{'✅ 存在' if hasattr(injector, 'patch_requests_with_tls') else '❌ 不存在'}")
    
    # 验证配置
    print(f"\n📋 配置验证:")
    print(f"   - tls_patch_mode: {injector._config.get('tls_patch_mode')}")
    print(f"   - impersonate: {injector._config.get('impersonate')}")
    print(f"   - headless: {injector._config.get('headless')}")
    print(f"   - target_domains: {injector._config.get('target_domains')}")
    
    all_methods_exist = (
        hasattr(injector, 'initialize') and
        hasattr(injector, 'fetch_credentials') and
        hasattr(injector, 'patch_requests_with_tls')
    )
    
    print(f"\n✅ 核心方法验证：{'通过' if all_methods_exist else '失败'}")
    
    return all_methods_exist


async def test_high_sensitivity_api():
    """测试 3: 高敏感 API 测试（触发凭证获取）"""
    print("\n" + "="*60)
    print("测试 3: 高敏感 API 测试（触发凭证获取）")
    print("="*60)
    
    # 测试 AkShare get_sector_list
    print(f"\n📋 测试 AkShare get_sector_list():")
    ak_adapter = AkShareAdapter()
    await ak_adapter.initialize()
    
    start_time = time.time()
    try:
        sectors = await ak_adapter.get_sector_list('industry')
        elapsed = time.time() - start_time
        
        print(f"   - 获取板块数量：{len(sectors)}")
        print(f"   - 耗时：{elapsed:.3f}秒")
        print(f"   - 凭证已注入：{ak_adapter._injector._is_patched}")
        print(f"   - 结果：{'✅ 通过' if len(sectors) > 0 else '⚠️ 无数据'}")
        
        ak_success = len(sectors) > 0
    except Exception as e:
        print(f"   - 错误：{e}")
        print(f"   - 结果：❌ 失败")
        ak_success = False
    
    # 测试 EFinance get_stock_list
    print(f"\n📋 测试 EFinance get_stock_list():")
    ef_adapter = EFinanceAdapter()
    await ef_adapter.initialize()
    
    start_time = time.time()
    try:
        stocks = await ef_adapter.get_stock_list()
        elapsed = time.time() - start_time
        
        print(f"   - 获取股票数量：{len(stocks)}")
        print(f"   - 耗时：{elapsed:.3f}秒")
        print(f"   - 凭证已注入：{ef_adapter._injector._is_patched if hasattr(ef_adapter, '_injector') else 'N/A'}")
        print(f"   - 结果：{'✅ 通过' if len(stocks) > 0 else '⚠️ 无数据'}")
        
        ef_success = len(stocks) > 0
    except Exception as e:
        print(f"   - 错误：{e}")
        print(f"   - 结果：❌ 失败")
        ef_success = False
    
    return ak_success or ef_success


async def test_smart_retry():
    """测试 4: 智能重试测试"""
    print("\n" + "="*60)
    print("测试 4: 智能重试测试")
    print("="*60)
    
    from app.adapters.smart_retry import SmartRetryExecutor, ErrorClassifier, ErrorType
    
    # 验证错误分类器
    print(f"\n📋 错误分类器验证:")
    
    test_cases = [
        (Exception("RemoteDisconnected"), ErrorType.CONNECTION_CLOSED),
        (Exception("429 Too Many Requests"), ErrorType.RATE_LIMITED),
        (Exception("403 Forbidden"), ErrorType.IP_BLOCKED),
        (Exception("Connection aborted"), ErrorType.CONNECTION_CLOSED),
        (Exception("Timeout"), ErrorType.TIMEOUT),
    ]
    
    all_passed = True
    for error, expected_type in test_cases:
        classified = ErrorClassifier.classify(error)
        passed = classified == expected_type
        all_passed = all_passed and passed
        print(f"   - {str(error)[:30]:30s} → {classified.name:20s} {'✅' if passed else '❌'}")
    
    # 验证 SmartRetryExecutor
    print(f"\n📋 SmartRetryExecutor 验证:")
    executor = SmartRetryExecutor({
        'max_retries': 3,
        'base_wait_seconds': 2.0,
    })
    
    print(f"   - max_retries: {executor._strategy._max_retries}")
    print(f"   - base_wait_seconds: {executor._strategy._base_wait_seconds}")
    print(f"   - 模式切换回调已设置：{executor._on_switch_mode_callback is not None}")
    
    return all_passed


async def main():
    """运行所有测试"""
    print("\n" + "="*70)
    print("反风控策略验证测试")
    print("="*70)
    
    results = {}
    
    # 测试 1: 启动时间
    results['启动时间测试'] = await test_startup_time()
    
    # 测试 2: 凭证注入器方法
    results['凭证注入器方法验证'] = await test_credential_injector_methods()
    
    # 测试 3: 高敏感 API
    results['高敏感 API 测试'] = await test_high_sensitivity_api()
    
    # 测试 4: 智能重试
    results['智能重试测试'] = await test_smart_retry()
    
    # 总结
    print("\n" + "="*70)
    print("测试总结")
    print("="*70)
    
    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name:20s} {status}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    
    print(f"\n总计：{total_passed}/{total_tests} 测试通过")
    
    if total_passed == total_tests:
        print("\n🎉 所有测试通过！反风控策略实施成功！")
        return True
    else:
        print(f"\n⚠️ 有 {total_tests - total_passed} 个测试未通过，请检查")
        return False


if __name__ == "__main__":
    # 设置日志
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # 运行测试
    success = asyncio.run(main())
    
    # 退出码
    sys.exit(0 if success else 1)

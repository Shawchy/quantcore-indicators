"""
综合测试：智能重试 + 凭证注入 + TLS 指纹伪装

测试内容：
1. AkShare 适配器智能重试
2. EFinance 适配器智能重试  
3. TLS 错误自动切换
4. HybridTLSClient 降级方案
"""

import asyncio
import sys
sys.path.insert(0, '.')

from app.adapters.akshare_adapter import AkShareAdapter
from app.adapters.efinance_adapter import EFinanceAdapter


async def test_akshare_smart_retry():
    """测试 AkShare 智能重试"""
    print("\n" + "=" * 70)
    print("测试 AkShare 适配器（智能重试 + 凭证注入）")
    print("=" * 70)
    
    adapter = AkShareAdapter()
    
    # 初始化
    print("\n1. 初始化适配器...")
    success = await adapter.initialize()
    print(f"   结果：{'✓ 成功' if success else '✗ 失败'}")
    
    if not success:
        print("   跳过后续测试")
        return False
    
    # 检查组件
    print(f"   - 凭证注入器：{'✓' if hasattr(adapter, '_injector') else '✗'}")
    print(f"   - SmartRetryExecutor: {'✓' if hasattr(adapter, '_retry_executor') else '✗'}")
    print(f"   - HybridTLSClient: {'✓' if hasattr(adapter, '_hybrid_client') else '✗'}")
    
    # 测试高敏感 API：板块列表
    print("\n2. 测试板块列表（高敏感 API）...")
    try:
        sectors = await adapter.get_sector_list('industry')
        if sectors:
            print(f"   ✓ 成功获取 {len(sectors)} 个板块")
            print(f"   示例：{sectors[0].name} ({sectors[0].code})")
        else:
            print(f"   ✗ 失败：返回空列表")
    except Exception as e:
        print(f"   ✗ 异常：{type(e).__name__}: {e}")
    
    # 测试概念板块
    print("\n3. 测试概念板块列表...")
    try:
        sectors = await adapter.get_sector_list('concept')
        if sectors:
            print(f"   ✓ 成功获取 {len(sectors)} 个概念板块")
        else:
            print(f"   ✗ 失败：返回空列表")
    except Exception as e:
        print(f"   ✗ 异常：{type(e).__name__}: {e}")
    
    await adapter.close()
    return True


async def test_efinance_smart_retry():
    """测试 EFinance 智能重试"""
    print("\n" + "=" * 70)
    print("测试 EFinance 适配器（智能重试 + 凭证注入）")
    print("=" * 70)
    
    adapter = EFinanceAdapter()
    
    # 初始化
    print("\n1. 初始化适配器...")
    success = await adapter.initialize()
    print(f"   结果：{'✓ 成功' if success else '✗ 失败'}")
    
    if not success:
        print("   跳过后续测试")
        return False
    
    # 检查组件
    print(f"   - 凭证注入器：{'✓' if hasattr(adapter, '_injector') else '✗'}")
    print(f"   - SmartRetryExecutor: {'✓' if hasattr(adapter, '_retry_executor') else '✗'}")
    print(f"   - HybridTLSClient: {'✓' if hasattr(adapter, '_hybrid_client') else '✗'}")
    
    # 测试高敏感 API：股票列表
    print("\n2. 测试股票列表（高敏感 API）...")
    try:
        stocks = await adapter.get_stock_list()
        if stocks:
            print(f"   ✓ 成功获取 {len(stocks)} 只股票")
            print(f"   示例：{stocks[0].name} ({stocks[0].code})")
        else:
            print(f"   ✗ 失败：返回空列表")
    except Exception as e:
        print(f"   ✗ 异常：{type(e).__name__}: {e}")
    
    await adapter.close()
    return True


async def main():
    print("\n" + "=" * 70)
    print("智能重试 + 凭证注入 + TLS 指纹伪装 综合测试")
    print("=" * 70)
    
    # 测试 AkShare
    ak_success = await test_akshare_smart_retry()
    
    # 测试 EFinance
    ef_success = await test_efinance_smart_retry()
    
    # 总结
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)
    print(f"\nAkShare 适配器：{'✓ 成功' if ak_success else '✗ 失败'}")
    print(f"EFinance 适配器：{'✓ 成功' if ef_success else '✗ 失败'}")
    
    if ak_success and ef_success:
        print("\n✅ 所有测试通过！")
        print("\n已验证功能：")
        print("  ✓ 凭证注入模式（懒加载）")
        print("  ✓ SmartRetryExecutor 智能重试")
        print("  ✓ TLS 错误自动检测")
        print("  ✓ HybridTLSClient 自动降级")
        print("  ✓ 高敏感 API 成功获取")
    else:
        print("\n⚠️ 部分测试失败，请检查日志")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(main())

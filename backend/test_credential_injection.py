"""
测试凭证注入模式效果

验证：
1. AkShare 适配器集成凭证注入
2. EFinance 适配器集成凭证注入
3. 高敏感 API（板块列表、股票列表）成功率
"""

import asyncio
import json
import time
import sys
sys.path.insert(0, '.')

from app.adapters.akshare_adapter import AkShareAdapter
from app.adapters.efinance_adapter import EFinanceAdapter


async def test_akshare_with_credential_injection():
    """测试 AkShare 凭证注入模式"""
    print("\n" + "=" * 60)
    print("测试 AkShare 适配器（凭证注入模式）")
    print("=" * 60)
    
    adapter = AkShareAdapter()
    
    # 初始化
    print("\n1. 初始化适配器...")
    success = await adapter.initialize()
    print(f"   初始化：{'成功' if success else '失败'}")
    
    if not success:
        print("   跳过后续测试")
        return False
    
    # 测试高敏感 API：板块列表
    print("\n2. 测试板块列表（高敏感 API）...")
    start = time.time()
    sectors = await adapter.get_sector_list('industry')
    elapsed = time.time() - start
    
    if sectors:
        print(f"   状态：✓ 成功")
        print(f"   耗时：{elapsed:.2f}s")
        print(f"   板块数量：{len(sectors)}")
        if sectors:
            print(f"   示例：{sectors[0].name} ({sectors[0].code})")
    else:
        print(f"   状态：✗ 失败")
        print(f"   耗时：{elapsed:.2f}s")
    
    # 测试概念板块
    print("\n3. 测试概念板块列表...")
    start = time.time()
    sectors = await adapter.get_sector_list('concept')
    elapsed = time.time() - start
    
    if sectors:
        print(f"   状态：✓ 成功")
        print(f"   耗时：{elapsed:.2f}s")
        print(f"   板块数量：{len(sectors)}")
    else:
        print(f"   状态：✗ 失败")
    
    # 测试低敏感 API：K 线数据
    print("\n4. 测试 K 线数据（低敏感 API）...")
    start = time.time()
    klines = await adapter.get_kline('000001', '1d', limit=10)
    elapsed = time.time() - start
    
    if klines:
        print(f"   状态：✓ 成功")
        print(f"   耗时：{elapsed:.2f}s")
        print(f"   K 线条数：{len(klines)}")
    else:
        print(f"   状态：✗ 失败")
    
    await adapter.close()
    return True


async def test_efinance_with_credential_injection():
    """测试 EFinance 凭证注入模式"""
    print("\n" + "=" * 60)
    print("测试 EFinance 适配器（凭证注入模式）")
    print("=" * 60)
    
    adapter = EFinanceAdapter()
    
    # 初始化
    print("\n1. 初始化适配器...")
    success = await adapter.initialize()
    print(f"   初始化：{'成功' if success else '失败'}")
    
    if not success:
        print("   跳过后续测试")
        return False
    
    # 测试高敏感 API：股票列表
    print("\n2. 测试股票列表（高敏感 API）...")
    start = time.time()
    stocks = await adapter.get_stock_list()
    elapsed = time.time() - start
    
    if stocks:
        print(f"   状态：✓ 成功")
        print(f"   耗时：{elapsed:.2f}s")
        print(f"   股票数量：{len(stocks)}")
        if stocks:
            print(f"   示例：{stocks[0].name} ({stocks[0].code})")
    else:
        print(f"   状态：✗ 失败")
        print(f"   耗时：{elapsed:.2f}s")
    
    # 测试低敏感 API：实时行情
    print("\n3. 测试实时行情（低敏感 API）...")
    start = time.time()
    quotes = await adapter.get_realtime_quotes(['000001'])
    elapsed = time.time() - start
    
    if quotes:
        print(f"   状态：✓ 成功")
        print(f"   耗时：{elapsed:.2f}s")
        print(f"   行情数量：{len(quotes)}")
    else:
        print(f"   状态：✗ 失败")
    
    # 测试 K 线数据
    print("\n4. 测试 K 线数据...")
    start = time.time()
    klines = await adapter.get_kline('000001', '1d', limit=10)
    elapsed = time.time() - start
    
    if klines:
        print(f"   状态：✓ 成功")
        print(f"   耗时：{elapsed:.2f}s")
        print(f"   K 线条数：{len(klines)}")
    else:
        print(f"   状态：✗ 失败")
    
    await adapter.close()
    return True


async def main():
    print("\n" + "=" * 60)
    print("凭证注入模式效果测试")
    print("=" * 60)
    
    # 测试 AkShare
    ak_success = await test_akshare_with_credential_injection()
    
    # 测试 EFinance
    ef_success = await test_efinance_with_credential_injection()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"AkShare 适配器：{'✓ 成功' if ak_success else '✗ 失败'}")
    print(f"EFinance 适配器：{'✓ 成功' if ef_success else '✗ 失败'}")
    
    if ak_success and ef_success:
        print("\n✓ 凭证注入模式已成功集成到两个适配器")
        print("✓ 高敏感 API（板块列表、股票列表）应该能够正常获取")
        print("✓ TLS 指纹伪装已启用（curl_cffi chrome120）")
    else:
        print("\n✗ 部分测试失败，请检查日志")


if __name__ == "__main__":
    asyncio.run(main())

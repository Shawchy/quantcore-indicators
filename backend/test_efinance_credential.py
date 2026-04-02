"""
Efinance 凭证注入测试脚本

测试 Playwright 获取凭证 → Efinance 使用

使用方法：
    python test_efinance_credential.py
"""

import asyncio
import os

os.environ['PLAYWRIGHT_BROWSERS_PATH'] = 'd:/PROJ/Quant/backend/playwright_browsers'


async def test_efinance_with_credential():
    print("\n" + "="*60)
    print("测试：Playwright 获取凭证 → Efinance 使用")
    print("="*60)
    
    from app.adapters.credential_injector import EfinanceWithCredential
    
    print("\n1. 使用上下文管理器初始化...")
    
    async with EfinanceWithCredential() as ef:
        print("✓ 初始化完成，凭证已注入")
        
        status = ef.get_status()
        print(f"\n状态:")
        print(f"  - 已初始化: {status['initialized']}")
        print(f"  - 已注入: {status['patched']}")
        print(f"  - Cookie 数量: {status['cookies_count']}")
        
        print("\n2. 测试 Efinance 获取实时行情...")
        try:
            df = ef.get_realtime_quotes()
            print(f"✓ 获取成功: {len(df)} 条数据")
            if len(df) > 0:
                sample = df.iloc[0]
                print(f"  示例: {sample['股票代码']} {sample['股票名称']} 价格:{sample['最新价']}")
        except Exception as e:
            print(f"获取失败: {e}")
        
        print("\n3. 测试获取股票基本信息...")
        try:
            info = ef.get_base_info('000001')
            print(f"✓ 获取成功:")
            for key, value in list(info.items())[:5]:
                print(f"  - {key}: {value}")
        except Exception as e:
            print(f"获取失败: {e}")
        
        print("\n4. 测试获取 K 线数据...")
        try:
            df = ef.get_quote_history('000001')
            print(f"✓ 获取成功: {len(df)} 条数据")
            if len(df) > 0:
                print(f"  最新: {df.iloc[-1]['日期']} 收盘:{df.iloc[-1]['收盘']}")
        except Exception as e:
            print(f"获取失败: {e}")
        
        print("\n5. 测试获取行业板块...")
        try:
            df = ef.get_industry_board()
            print(f"✓ 获取成功: {len(df)} 条数据")
            if len(df) > 0:
                print(f"  示例: {df.iloc[0]['板块名称']} 涨幅:{df.iloc[0]['涨跌幅']}")
        except Exception as e:
            print(f"获取失败: {e}")
        
        print("\n6. 测试获取概念板块...")
        try:
            df = ef.get_concept_board()
            print(f"✓ 获取成功: {len(df)} 条数据")
        except Exception as e:
            print(f"获取失败: {e}")
    
    print("\n✓ 上下文管理器已退出，资源已清理")
    return True


async def test_unified_manager():
    print("\n" + "="*60)
    print("测试：统一凭证管理器")
    print("="*60)
    
    from app.adapters.credential_injector import UnifiedCredentialManager
    
    manager = UnifiedCredentialManager({
        'headless': True,
        'auto_refresh': True,
        'refresh_interval_minutes': 30,
    })
    
    print("\n1. 初始化统一凭证管理器...")
    success = await manager.initialize()
    
    if not success:
        print("✗ 初始化失败")
        return False
    
    print("✓ 初始化成功")
    
    status = manager.get_status()
    print(f"\n状态:")
    print(f"  - 已初始化: {status['initialized']}")
    print(f"  - Cookie 数量: {status['cookies_count']}")
    print(f"  - 自动刷新: {status['auto_refresh']}")
    
    print("\n2. 使用 AKShare...")
    try:
        import akshare as ak
        df = ak.stock_individual_info_em(symbol='000001')
        print(f"✓ AKShare 调用成功")
    except Exception as e:
        print(f"AKShare 调用失败: {e}")
    
    print("\n3. 使用 Efinance...")
    try:
        import efinance as ef
        df = ef.stock.get_realtime_quotes()
        print(f"✓ Efinance 调用成功: {len(df)} 条")
    except Exception as e:
        print(f"Efinance 调用失败: {e}")
    
    await manager.close()
    print("\n✓ 统一凭证管理器已关闭")
    return True


async def test_comparison():
    print("\n" + "="*60)
    print("测试：对比有无凭证的效果")
    print("="*60)
    
    print("\n1. 不使用凭证直接调用 Efinance...")
    try:
        import efinance as ef
        import time
        
        start = time.time()
        df = ef.stock.get_realtime_quotes()
        elapsed = time.time() - start
        
        print(f"  耗时: {elapsed:.2f}s")
        print(f"  数据量: {len(df)} 条")
    except Exception as e:
        print(f"  失败: {e}")
    
    print("\n2. 使用凭证注入后调用 Efinance...")
    from app.adapters.credential_injector import EfinanceWithCredential
    
    async with EfinanceWithCredential() as ef:
        try:
            import time
            start = time.time()
            df = ef.get_realtime_quotes()
            elapsed = time.time() - start
            
            print(f"  耗时: {elapsed:.2f}s")
            print(f"  数据量: {len(df)} 条")
        except Exception as e:
            print(f"  失败: {e}")
    
    return True


async def main():
    print("\n" + "="*60)
    print("Efinance 凭证注入功能测试")
    print("="*60)
    
    tests = [
        ("EfinanceWithCredential 上下文管理器", test_efinance_with_credential),
        ("统一凭证管理器", test_unified_manager),
        ("有无凭证对比测试", test_comparison),
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

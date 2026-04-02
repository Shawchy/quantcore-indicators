"""
测试 TLS 指纹伪装 + Cookie 注入

验证 Playwright Cookie + curl_cffi TLS 指纹方案
"""

import asyncio
import os

os.environ['PLAYWRIGHT_BROWSERS_PATH'] = 'd:/PROJ/Quant/backend/playwright_browsers'


async def test_tls_fingerprint_with_cookies():
    print("\n" + "="*60)
    print("测试：TLS 指纹伪装 + Cookie 注入")
    print("="*60)
    
    from app.adapters.credential_injector import AkShareWithCredential
    
    print("\n1. 使用 TLS 指纹伪装模式初始化...")
    
    async with AkShareWithCredential(use_tls=True) as ak:
        status = ak.get_status()
        print(f"\n状态:")
        print(f"  - TLS 模式: {status.get('tls_mode')}")
        print(f"  - curl_session_active: {status.get('curl_session_active')}")
        print(f"  - impersonate: {status.get('impersonate')}")
        print(f"  - Cookie 数量: {status.get('cookies_count')}")
        
        print("\n2. 测试 AKShare API 调用...")
        
        print("\n测试 stock_individual_info_em...")
        try:
            df = ak.get_stock_individual_info('000001')
            print(f"✓ 成功: {len(df)} 条")
        except Exception as e:
            print(f"✗ 失败: {e}")
        
        print("\n测试 stock_zh_a_spot_em...")
        try:
            df = ak.get_stock_zh_a_spot()
            print(f"✓ 成功: {len(df)} 条")
            if len(df) > 0:
                print(f"  示例: {df.iloc[0]['代码']} {df.iloc[0]['名称']}")
        except Exception as e:
            print(f"✗ 失败: {e}")
        
        print("\n测试 stock_board_industry_name_em...")
        try:
            df = ak.get_board_industry_name_em()
            print(f"✓ 成功: {len(df)} 条")
        except Exception as e:
            print(f"✗ 失败: {e}")


async def test_compare_modes():
    print("\n" + "="*60)
    print("对比测试：普通模式 vs TLS 指纹伪装模式")
    print("="*60)
    
    from app.adapters.credential_injector import AkShareWithCredential
    
    print("\n1. 普通模式（Python requests TLS 指纹）...")
    async with AkShareWithCredential(use_tls=False) as ak:
        try:
            df = ak.get_stock_individual_info('000001')
            print(f"✓ 普通模式成功: {len(df)} 条")
        except Exception as e:
            print(f"✗ 普通模式失败: {type(e).__name__}")
    
    print("\n2. TLS 指纹伪装模式（Chrome 120 指纹）...")
    async with AkShareWithCredential(use_tls=True) as ak:
        status = ak.get_status()
        print(f"   TLS 模式: {status.get('tls_mode')}")
        
        try:
            df = ak.get_stock_individual_info('000001')
            print(f"✓ TLS 模式成功: {len(df)} 条")
        except Exception as e:
            print(f"✗ TLS 模式失败: {type(e).__name__}")


async def test_efinance_with_tls():
    print("\n" + "="*60)
    print("测试：Efinance + TLS 指纹伪装")
    print("="*60)
    
    from app.adapters.credential_injector import EfinanceWithCredential
    
    async with EfinanceWithCredential(use_tls=True) as ef:
        status = ef.get_status()
        print(f"\n状态:")
        print(f"  - TLS 模式: {status.get('tls_mode')}")
        print(f"  - impersonate: {status.get('impersonate')}")
        
        print("\n测试 get_realtime_quotes...")
        try:
            df = ef.get_realtime_quotes()
            print(f"✓ 成功: {len(df)} 条")
            if len(df) > 0:
                print(f"  示例: {df.iloc[0]['股票代码']} {df.iloc[0]['股票名称']}")
        except Exception as e:
            print(f"✗ 失败: {e}")
        
        print("\n测试 get_quote_history...")
        try:
            df = ef.get_quote_history('000001')
            print(f"✓ 成功: {len(df)} 条")
        except Exception as e:
            print(f"✗ 失败: {e}")


async def main():
    print("\n" + "="*60)
    print("TLS 指纹伪装完整测试")
    print("="*60)
    
    await test_tls_fingerprint_with_cookies()
    await test_compare_modes()
    await test_efinance_with_tls()
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())

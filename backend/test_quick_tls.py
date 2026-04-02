"""
快速测试 TLS 指纹解决方案
"""

import asyncio
import json
import sys
sys.path.insert(0, '.')

from app.adapters.hybrid_tls_client import HybridTLSClient


async def quick_test():
    print("\n=== TLS 指纹解决方案快速测试 ===\n")
    
    client = HybridTLSClient({
        'playwright_pool_size': 2,
        'enable_http2': True,
        'fallback_to_playwright': True,
    })
    
    print("初始化...")
    success = await client.initialize()
    
    if not success:
        print("初始化失败")
        return
    
    stats = client.get_stats()
    print(f"tls_client: {stats.get('tls_client_available')}")
    print(f"curl_cffi: {stats.get('curl_cffi_clients', [])}")
    print(f"httpx: {stats.get('httpx_available')}")
    
    test_apis = [
        ("K线", "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=0.000001&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt=101&fqt=1&end=20500101&lmt=10", "kline"),
        ("A股列表", "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=10&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23&fields=f12,f14,f2,f3", "stock_list"),
    ]
    
    for name, url, api_type in test_apis:
        print(f"\n测试: {name}")
        try:
            result = await client.get(url, timeout=20, api_type=api_type)
            print(f"  状态码: {result['status_code']}")
            print(f"  响应长度: {len(result['text'])}")
            
            try:
                data = json.loads(result['text'])
                has_data = data.get('data') is not None
                print(f"  有数据: {has_data}")
                if has_data:
                    if 'diff' in data['data']:
                        print(f"  数据条数: {len(data['data']['diff'])}")
                    elif 'klines' in data['data']:
                        print(f"  K线条数: {len(data['data']['klines'])}")
            except:
                print(f"  JSON解析失败")
                
        except Exception as e:
            print(f"  失败: {e}")
    
    await client.close()
    print("\n测试完成")


if __name__ == "__main__":
    asyncio.run(quick_test())

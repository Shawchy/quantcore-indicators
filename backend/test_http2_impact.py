"""
测试 HTTP/2 对成功率的影响

对比测试：
1. curl_cffi (HTTP/1.1 + TLS 指纹)
2. httpx (HTTP/2 + TLS 指纹)
3. tls-client (HTTP/2 + TLS 指纹)
"""

import asyncio
import time
from typing import Dict, Any, List, Tuple


async def test_http2_impact():
    print("\n=== HTTP/2 对成功率影响测试 ===\n")
    
    test_apis = [
        ("K线数据", "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=0.000001&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt=101&fqt=1&end=20500101&lmt=10"),
        ("资金流向", "https://push2.eastmoney.com/api/qt/stock/fflow/kline/get?secid=0.000001&klt=101&lmt=10&fields1=f1,f2,f3,f7&fields2=f51,f52,f53,f54,f55,f56,f58,f60"),
        ("A股列表", "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=10&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23&fields=f12,f14,f2,f3"),
    ]
    
    results = {
        'curl_cffi': {},
        'httpx': {},
        'tls_client': {},
    }
    
    print("1. 测试 curl_cffi (HTTP/1.1 + TLS 指纹)")
    print("-" * 50)
    try:
        from curl_cffi.requests import Session
        curl_session = Session(impersonate='chrome120')
        
        for name, url in test_apis:
            start = time.time()
            try:
                resp = curl_session.get(url, timeout=15)
                elapsed = time.time() - start
                success = resp.status_code == 200 and len(resp.text) > 100
                results['curl_cffi'][name] = {
                    'success': success,
                    'status': resp.status_code,
                    'length': len(resp.text),
                    'time': elapsed,
                }
                status = 'OK' if success else 'FAIL'
                print(f"  {name}: {status} (status={resp.status_code}, len={len(resp.text)}, time={elapsed:.2f}s)")
            except Exception as e:
                results['curl_cffi'][name] = {'success': False, 'error': str(e)}
                print(f"  {name}: FAIL ({type(e).__name__})")
        
        curl_session.close()
    except ImportError:
        print("  curl_cffi not installed")
    
    print("\n2. 测试 httpx (HTTP/2)")
    print("-" * 50)
    try:
        import httpx
        httpx_client = httpx.Client(
            http2=True,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'},
            timeout=15.0,
        )
        
        for name, url in test_apis:
            start = time.time()
            try:
                resp = httpx_client.get(url)
                elapsed = time.time() - start
                success = resp.status_code == 200 and len(resp.text) > 100
                results['httpx'][name] = {
                    'success': success,
                    'status': resp.status_code,
                    'length': len(resp.text),
                    'time': elapsed,
                }
                status = 'OK' if success else 'FAIL'
                print(f"  {name}: {status} (status={resp.status_code}, len={len(resp.text)}, time={elapsed:.2f}s)")
            except Exception as e:
                results['httpx'][name] = {'success': False, 'error': str(e)}
                print(f"  {name}: FAIL ({type(e).__name__})")
        
        httpx_client.close()
    except ImportError:
        print("  httpx not installed")
    
    print("\n3. 测试 tls-client (HTTP/2 + TLS 指纹)")
    print("-" * 50)
    try:
        import tls_client
        tls_session = tls_client.Session(client_identifier='chrome120')
        
        for name, url in test_apis:
            start = time.time()
            try:
                resp = tls_session.get(url, timeout_seconds=15)
                elapsed = time.time() - start
                success = resp.status_code == 200 and len(resp.text) > 100
                results['tls_client'][name] = {
                    'success': success,
                    'status': resp.status_code,
                    'length': len(resp.text),
                    'time': elapsed,
                }
                status = 'OK' if success else 'FAIL'
                print(f"  {name}: {status} (status={resp.status_code}, len={len(resp.text)}, time={elapsed:.2f}s)")
            except Exception as e:
                results['tls_client'][name] = {'success': False, 'error': str(e)}
                print(f"  {name}: FAIL ({type(e).__name__})")
    except ImportError:
        print("  tls-client not installed")
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    print("\n| Client     | K-line | Fund Flow | Stock List | Rate   |")
    print("|------------|--------|-----------|------------|--------|")
    
    for client_name, client_results in results.items():
        if not client_results:
            continue
        success_count = sum(1 for r in client_results.values() if r.get('success', False))
        total = len(client_results)
        rate = f"{success_count}/{total}"
        
        kline = 'OK' if client_results.get('K线数据', {}).get('success', False) else 'FAIL'
        fund = 'OK' if client_results.get('资金流向', {}).get('success', False) else 'FAIL'
        stock = 'OK' if client_results.get('A股列表', {}).get('success', False) else 'FAIL'
        
        print(f"| {client_name:10} | {kline:6} | {fund:9} | {stock:10} | {rate:6} |")
    
    print("\nConclusion:")
    curl_success = sum(1 for r in results['curl_cffi'].values() if r.get('success', False)) if results['curl_cffi'] else 0
    httpx_success = sum(1 for r in results['httpx'].values() if r.get('success', False)) if results['httpx'] else 0
    tls_success = sum(1 for r in results['tls_client'].values() if r.get('success', False)) if results['tls_client'] else 0
    
    print(f"  - curl_cffi (HTTP/1.1): {curl_success}/3 success")
    print(f"  - httpx (HTTP/2): {httpx_success}/3 success")
    print(f"  - tls-client (HTTP/2): {tls_success}/3 success")
    
    if httpx_success > curl_success:
        print("  -> HTTP/2 improves success rate")
    elif httpx_success == curl_success:
        print("  -> HTTP/2 has no significant impact on success rate")
    else:
        print("  -> HTTP/2 does not improve success rate")


if __name__ == "__main__":
    asyncio.run(test_http2_impact())

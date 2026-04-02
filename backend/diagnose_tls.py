"""
测试 TLS 指纹问题

Python requests 的 TLS 握手特征可能被识别
"""

import subprocess
import json

def test_with_curl():
    print("=== 使用 curl 测试（不同 TLS 指纹）===\n")
    
    url = "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=5&po=1&np=1&fltt=2&invt=2&fid=f12&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23&fields=f12,f14,f2,f3"
    
    cmd = [
        'curl', '-s', '-w', '\\n%{http_code}',
        '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        '-H', 'Referer: https://quote.eastmoney.com/',
        url
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        output = result.stdout.strip()
        lines = output.rsplit('\n', 1)
        
        if len(lines) == 2:
            body, status = lines
            print(f"状态码: {status}")
            print(f"响应长度: {len(body)}")
            print(f"响应内容: {body[:300]}...")
            
            if status == '200' and len(body) > 100:
                print("\n✓ curl 请求成功！")
                print("结论: 问题在于 Python requests 的 TLS 指纹被识别")
                return True
        else:
            print(f"响应: {output[:300]}")
            
    except Exception as e:
        print(f"curl 失败: {e}")
    
    return False


def test_tls_fingerprint():
    print("\n=== 检查 TLS 指纹差异 ===\n")
    
    print("Python requests 使用的 TLS 库:")
    try:
        import ssl
        print(f"  SSL 版本: {ssl.OPENSSL_VERSION}")
    except:
        print("  无法获取")
    
    print("\n浏览器 TLS 特征:")
    print("  - 支持 TLS 1.3")
    print("  - 支持特定密码套件")
    print("  - 扩展顺序不同")
    print("  - ClientHello 格式不同")
    
    print("\nPython requests TLS 特征:")
    print("  - 使用 urllib3")
    print("  - TLS 扩展顺序固定")
    print("  - 可能缺少某些扩展")
    print("  - 容易被识别为自动化工具")


def test_http2():
    print("\n=== 测试 HTTP/2 支持 ===\n")
    
    try:
        import httpx
        
        url = "https://push2.eastmoney.com/api/qt/clist/get"
        params = {
            'pn': 1, 'pz': 5, 'po': 1, 'np': 1,
            'fltt': 2, 'invt': 2, 'fid': 'f12',
            'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',
            'fields': 'f12,f14,f2,f3'
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://quote.eastmoney.com/',
        }
        
        with httpx.Client(http2=True, timeout=10) as client:
            resp = client.get(url, params=params, headers=headers)
            print(f"HTTP/2 请求状态码: {resp.status_code}")
            print(f"响应长度: {len(resp.text)}")
            print(f"HTTP 版本: {resp.http_version}")
            
            if resp.status_code == 200:
                print(f"响应: {resp.text[:200]}...")
                return True
                
    except ImportError:
        print("httpx 未安装，跳过 HTTP/2 测试")
    except Exception as e:
        print(f"HTTP/2 请求失败: {e}")
    
    return False


def main():
    print("="*60)
    print("TLS 指纹诊断")
    print("="*60)
    
    test_tls_fingerprint()
    curl_ok = test_with_curl()
    http2_ok = test_http2()
    
    print("\n" + "="*60)
    print("结论")
    print("="*60)
    
    if curl_ok:
        print("""
✓ curl 可以正常访问，但 Python requests 不行

**根本原因：TLS 指纹识别**

服务器通过 TLS 握手特征识别并拦截了 Python requests：
1. TLS 扩展顺序与浏览器不同
2. 密码套件列表不同
3. ClientHello 格式差异
4. 缺少某些浏览器特有的扩展

**解决方案：**
1. 使用 Playwright（真实浏览器 TLS 指纹）
2. 使用 curl_cffi（模拟浏览器 TLS）
3. 使用代理服务
4. 使用 HTTP/2 客户端（httpx）
""")
    else:
        print("""
curl 也无法访问，可能是：
1. IP 被封禁
2. 需要特定的 Cookie
3. 需要验证码
""")


if __name__ == "__main__":
    main()

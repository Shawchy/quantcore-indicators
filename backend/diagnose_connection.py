"""
诊断连接断开原因

测试内容：
1. 检查是否是验证码
2. 检查请求头特征
3. 检查 IP 状态
4. 检查 TLS 指纹
"""

import requests
import time

def test_basic_request():
    print("\n=== 测试 1：基础请求 ===")
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    params = {
        'pn': 1,
        'pz': 10,
        'po': 1,
        'np': 1,
        'fltt': 2,
        'invt': 2,
        'fid': 'f12',
        'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',
        'fields': 'f12,f14,f2,f3,f4,f5,f6'
    }
    
    try:
        resp = requests.get(url, params=params, timeout=10)
        print(f"状态码: {resp.status_code}")
        print(f"响应长度: {len(resp.text)}")
        print(f"响应内容前 200 字符: {resp.text[:200]}")
        return resp.status_code == 200
    except Exception as e:
        print(f"请求失败: {type(e).__name__}: {e}")
        return False


def test_with_headers():
    print("\n=== 测试 2：带完整请求头 ===")
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    params = {
        'pn': 1,
        'pz': 10,
        'po': 1,
        'np': 1,
        'fltt': 2,
        'invt': 2,
        'fid': 'f12',
        'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',
        'fields': 'f12,f14,f2,f3,f4,f5,f6'
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://quote.eastmoney.com/',
        'Origin': 'https://quote.eastmoney.com',
        'Connection': 'keep-alive',
        'Sec-Ch-Ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
    }
    
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"状态码: {resp.status_code}")
        print(f"响应长度: {len(resp.text)}")
        print(f"响应内容前 200 字符: {resp.text[:200]}")
        return resp.status_code == 200
    except Exception as e:
        print(f"请求失败: {type(e).__name__}: {e}")
        return False


def test_with_session():
    print("\n=== 测试 3：使用 Session（模拟浏览器行为）===")
    
    session = requests.Session()
    
    # 先访问主页获取 Cookie
    print("步骤 1: 访问主页...")
    try:
        resp = session.get(
            "https://quote.eastmoney.com/",
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9',
            },
            timeout=15
        )
        print(f"主页状态码: {resp.status_code}")
        print(f"获取 Cookie: {len(session.cookies)} 个")
        for cookie in session.cookies:
            print(f"  - {cookie.name}: {cookie.value[:30]}...")
    except Exception as e:
        print(f"访问主页失败: {e}")
        return False
    
    # 等待一下模拟人类行为
    time.sleep(2)
    
    # 再请求 API
    print("\n步骤 2: 请求 API...")
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    params = {
        'pn': 1,
        'pz': 10,
        'po': 1,
        'np': 1,
        'fltt': 2,
        'invt': 2,
        'fid': 'f12',
        'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',
        'fields': 'f12,f14,f2,f3,f4,f5,f6'
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Referer': 'https://quote.eastmoney.com/',
        'Origin': 'https://quote.eastmoney.com',
    }
    
    try:
        resp = session.get(url, params=params, headers=headers, timeout=10)
        print(f"API 状态码: {resp.status_code}")
        print(f"响应长度: {len(resp.text)}")
        print(f"响应内容前 500 字符: {resp.text[:500]}")
        return resp.status_code == 200
    except Exception as e:
        print(f"请求失败: {type(e).__name__}: {e}")
        return False


def test_response_headers():
    print("\n=== 测试 4：检查响应头 ===")
    url = "https://quote.eastmoney.com/"
    
    try:
        resp = requests.get(url, timeout=15)
        print(f"状态码: {resp.status_code}")
        print("\n响应头:")
        for key, value in resp.headers.items():
            print(f"  {key}: {value}")
        
        # 检查是否有验证码相关内容
        content = resp.text
        captcha_keywords = ['captcha', '验证', 'geetest', '极验', 'slider', '滑动']
        found = []
        for kw in captcha_keywords:
            if kw.lower() in content.lower():
                found.append(kw)
        
        if found:
            print(f"\n⚠ 发现验证码关键词: {found}")
        else:
            print("\n✓ 未发现验证码关键词")
            
    except Exception as e:
        print(f"请求失败: {type(e).__name__}: {e}")


def test_api_directly():
    print("\n=== 测试 5：直接测试 API 响应 ===")
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    params = {
        'pn': 1,
        'pz': 5,
        'po': 1,
        'np': 1,
        'fltt': 2,
        'invt': 2,
        'fid': 'f12',
        'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',
        'fields': 'f12,f14,f2,f3'
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Referer': 'https://quote.eastmoney.com/',
    }
    
    for i in range(3):
        print(f"\n尝试 {i+1}/3:")
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            print(f"  状态码: {resp.status_code}")
            print(f"  响应长度: {len(resp.text)}")
            
            # 尝试解析 JSON
            try:
                data = resp.json()
                print(f"  JSON 解析成功")
                if 'data' in data:
                    print(f"  数据: {str(data['data'])[:200]}")
                else:
                    print(f"  响应: {str(data)[:200]}")
            except:
                print(f"  非 JSON 响应: {resp.text[:200]}")
            
            return True
            
        except requests.exceptions.ConnectionError as e:
            print(f"  连接错误: {e}")
            if 'RemoteDisconnected' in str(e):
                print("  ⚠ 服务器主动断开连接 - 可能原因:")
                print("    1. IP 被临时封禁")
                print("    2. 请求特征被识别为爬虫")
                print("    3. 缺少必要的请求头")
                print("    4. 触发了风控规则")
        except requests.exceptions.Timeout as e:
            print(f"  超时: {e}")
        except Exception as e:
            print(f"  其他错误: {type(e).__name__}: {e}")
        
        time.sleep(2)
    
    return False


def main():
    print("="*60)
    print("连接断开原因诊断")
    print("="*60)
    
    tests = [
        ("基础请求", test_basic_request),
        ("带完整请求头", test_with_headers),
        ("使用 Session", test_with_session),
        ("检查响应头", test_response_headers),
        ("直接测试 API", test_api_directly),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            result = test_func()
            results[name] = result
        except Exception as e:
            print(f"\n测试异常: {e}")
            results[name] = False
        
        time.sleep(1)
    
    print("\n" + "="*60)
    print("诊断结果")
    print("="*60)
    
    for name, result in results.items():
        status = "✓ 成功" if result else "✗ 失败"
        print(f"{status} - {name}")
    
    print("\n" + "="*60)
    print("结论")
    print("="*60)
    
    if not any(results.values()):
        print("""
连接被服务器主动断开的可能原因：

1. **IP 被临时封禁**
   - 短时间内请求次数过多
   - 解决方案：使用代理 IP 池

2. **请求特征被识别**
   - User-Agent、请求头等特征明显
   - 解决方案：使用 Playwright 模拟真实浏览器

3. **缺少 Cookie/Session**
   - 未建立有效会话
   - 解决方案：先访问主页获取 Cookie

4. **TLS 指纹识别**
   - Python requests 的 TLS 握手特征被识别
   - 解决方案：使用浏览器或 curl_cffi

5. **触发风控规则**
   - 请求频率、时间模式异常
   - 解决方案：智能请求调度
""")
    else:
        print("部分测试成功，问题可能是间歇性的")


if __name__ == "__main__":
    main()

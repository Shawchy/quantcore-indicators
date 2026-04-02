"""
反爬虫机制深度测试

测试内容：
1. 请求顺序依赖性
2. 请求频率检测
3. 特定 API 的反爬策略
"""

import asyncio
import os
import time
import random
from datetime import datetime
from collections import defaultdict

os.environ['PLAYWRIGHT_BROWSERS_PATH'] = 'd:/PROJ/Quant/backend/playwright_browsers'


class AntiCrawlAnalyzer:
    """反爬虫机制分析器"""
    
    def __init__(self):
        self.results = {
            'request_order': {},
            'frequency': {},
            'api_specific': {},
        }
        self._request_history = defaultdict(list)
    
    async def test_request_order(self):
        """测试请求顺序依赖性"""
        print("\n" + "="*60)
        print("测试 1：请求顺序依赖性")
        print("="*60)
        
        from curl_cffi.requests import Session
        
        test_sequences = [
            {
                'name': '直接请求 API',
                'steps': [
                    ('api', 'https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=5&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23&fields=f12,f14'),
                ]
            },
            {
                'name': '先主页后 API',
                'steps': [
                    ('page', 'https://quote.eastmoney.com/'),
                    ('api', 'https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=5&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23&fields=f12,f14'),
                ]
            },
            {
                'name': '先行情页后 API',
                'steps': [
                    ('page', 'https://quote.eastmoney.com/center/gridlist.html'),
                    ('api', 'https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=5&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23&fields=f12,f14'),
                ]
            },
            {
                'name': '完整流程：主页→行情页→API',
                'steps': [
                    ('page', 'https://www.eastmoney.com/'),
                    ('page', 'https://quote.eastmoney.com/'),
                    ('page', 'https://quote.eastmoney.com/center/gridlist.html'),
                    ('api', 'https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=5&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23&fields=f12,f14'),
                ]
            },
        ]
        
        for sequence in test_sequences:
            print(f"\n测试: {sequence['name']}")
            print("-" * 40)
            
            session = Session(impersonate="chrome120")
            cookies_collected = []
            
            for step_type, url in sequence['steps']:
                try:
                    resp = session.get(url, timeout=15)
                    cookies_count = len(resp.cookies)
                    cookies_collected.append(cookies_count)
                    
                    if step_type == 'api':
                        success = resp.status_code == 200 and len(resp.text) > 100
                        data_preview = resp.text[:100] if success else f"状态码: {resp.status_code}"
                        
                        print(f"  API 结果: {'✓ 成功' if success else '✗ 失败'}")
                        print(f"  状态码: {resp.status_code}")
                        print(f"  响应长度: {len(resp.text)}")
                        print(f"  累计 Cookie: {sum(cookies_collected)} 个")
                        
                        self.results['request_order'][sequence['name']] = {
                            'success': success,
                            'status_code': resp.status_code,
                            'cookies_count': sum(cookies_collected),
                        }
                    else:
                        print(f"  访问页面: {url[:50]}...")
                        print(f"  状态码: {resp.status_code}, Cookie: {cookies_count} 个")
                        
                    await asyncio.sleep(random.uniform(1, 2))
                    
                except Exception as e:
                    print(f"  ✗ 错误: {type(e).__name__}")
                    self.results['request_order'][sequence['name']] = {
                        'success': False,
                        'error': str(e),
                    }
            
            session.close()
            await asyncio.sleep(2)
    
    async def test_frequency_detection(self):
        """测试频率检测机制"""
        print("\n" + "="*60)
        print("测试 2：请求频率检测")
        print("="*60)
        
        from curl_cffi.requests import Session
        
        frequencies = [
            ('无延迟', 0),
            ('0.5秒', 0.5),
            ('1秒', 1.0),
            ('2秒', 2.0),
            ('3秒', 3.0),
            ('5秒', 5.0),
        ]
        
        for name, delay in frequencies:
            print(f"\n测试频率: {name}")
            print("-" * 40)
            
            session = Session(impersonate="chrome120")
            
            # 先访问主页获取 Cookie
            try:
                resp = session.get("https://quote.eastmoney.com/center/gridlist.html", timeout=15)
                print(f"  预热: 状态码 {resp.status_code}, Cookie {len(resp.cookies)} 个")
            except Exception as e:
                print(f"  预热失败: {e}")
                session.close()
                continue
            
            await asyncio.sleep(2)
            
            # 连续请求测试
            success_count = 0
            fail_count = 0
            
            for i in range(5):
                try:
                    api_url = "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=5&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23&fields=f12,f14"
                    resp = session.get(api_url, timeout=15)
                    
                    if resp.status_code == 200 and len(resp.text) > 100:
                        success_count += 1
                        print(f"  请求 {i+1}: ✓ 成功 (长度: {len(resp.text)})")
                    else:
                        fail_count += 1
                        print(f"  请求 {i+1}: ✗ 失败 (状态码: {resp.status_code})")
                        
                except Exception as e:
                    fail_count += 1
                    print(f"  请求 {i+1}: ✗ 错误 ({type(e).__name__})")
                
                if delay > 0:
                    await asyncio.sleep(delay)
            
            session.close()
            
            self.results['frequency'][name] = {
                'success_count': success_count,
                'fail_count': fail_count,
                'success_rate': success_count / 5 if success_count + fail_count > 0 else 0,
            }
            
            print(f"  结果: {success_count}/5 成功")
            
            await asyncio.sleep(3)
    
    async def test_api_specific(self):
        """测试不同 API 的反爬策略"""
        print("\n" + "="*60)
        print("测试 3：不同 API 的反爬策略")
        print("="*60)
        
        from curl_cffi.requests import Session
        
        apis = [
            {
                'name': 'A股列表',
                'url': 'https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=10&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23&fields=f12,f14,f2,f3',
                'sensitive': 'high',
            },
            {
                'name': '个股信息',
                'url': 'https://push2.eastmoney.com/api/qt/stock/get?secid=0.000001&fields=f57,f58,f43,f169,f170,f46,f44,f51,f168,f47,f48',
                'sensitive': 'low',
            },
            {
                'name': 'K线数据',
                'url': 'https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=0.000001&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt=101&fqt=1&end=20500101&lmt=10',
                'sensitive': 'low',
            },
            {
                'name': '板块列表',
                'url': 'https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=10&fs=m:90+t:2&fields=f12,f14,f2,f3,f62,f184,f66,f69,f72,f75,f78,f81,f84,f87',
                'sensitive': 'high',
            },
            {
                'name': '资金流向',
                'url': 'https://push2.eastmoney.com/api/qt/stock/fflow/kline/get?secid=0.000001&klt=101&lmt=10&fields1=f1,f2,f3,f7&fields2=f51,f52,f53,f54,f55,f56,f58,f60',
                'sensitive': 'medium',
            },
        ]
        
        session = Session(impersonate="chrome120")
        
        # 预热
        print("\n预热: 访问主页...")
        try:
            resp = session.get("https://quote.eastmoney.com/", timeout=15)
            print(f"  状态码: {resp.status_code}, Cookie: {len(resp.cookies)} 个")
        except Exception as e:
            print(f"  预热失败: {e}")
        
        await asyncio.sleep(3)
        
        for api in apis:
            print(f"\n测试: {api['name']} (敏感度: {api['sensitive']})")
            print("-" * 40)
            
            for attempt in range(3):
                try:
                    resp = session.get(api['url'], timeout=15)
                    
                    success = resp.status_code == 200 and len(resp.text) > 100
                    
                    if success:
                        try:
                            data = resp.json()
                            has_data = 'data' in data and data['data'] is not None
                            print(f"  尝试 {attempt+1}: ✓ 成功 (有数据: {has_data})")
                        except:
                            print(f"  尝试 {attempt+1}: ✓ 成功 (长度: {len(resp.text)})")
                    else:
                        print(f"  尝试 {attempt+1}: ✗ 失败 (状态码: {resp.status_code}, 长度: {len(resp.text)})")
                    
                    self.results['api_specific'][api['name']] = {
                        'sensitive': api['sensitive'],
                        'success': success,
                        'status_code': resp.status_code,
                    }
                    
                except Exception as e:
                    print(f"  尝试 {attempt+1}: ✗ 错误 ({type(e).__name__})")
                    self.results['api_specific'][api['name']] = {
                        'sensitive': api['sensitive'],
                        'success': False,
                        'error': str(e),
                    }
                
                await asyncio.sleep(2)
            
            await asyncio.sleep(3)
        
        session.close()
    
    def print_summary(self):
        """打印测试总结"""
        print("\n" + "="*60)
        print("测试总结")
        print("="*60)
        
        print("\n1. 请求顺序依赖性:")
        for name, result in self.results['request_order'].items():
            status = "✓" if result.get('success') else "✗"
            print(f"  {status} {name}: {result}")
        
        print("\n2. 请求频率检测:")
        for name, result in self.results['frequency'].items():
            rate = result.get('success_rate', 0) * 100
            print(f"  {name}: {result.get('success_count', 0)}/5 成功 ({rate:.0f}%)")
        
        print("\n3. API 敏感度:")
        for name, result in self.results['api_specific'].items():
            status = "✓" if result.get('success') else "✗"
            print(f"  {status} [{result.get('sensitive', '?')}] {name}")


async def main():
    print("="*60)
    print("反爬虫机制深度测试")
    print("="*60)
    
    analyzer = AntiCrawlAnalyzer()
    
    await analyzer.test_request_order()
    await analyzer.test_frequency_detection()
    await analyzer.test_api_specific()
    
    analyzer.print_summary()


if __name__ == "__main__":
    asyncio.run(main())

"""
TLS 指纹解决方案 - 增强版

目标：提供多层 TLS 指纹伪装，最大化成功率，最小化资源消耗

方案层级：
1. tls-client - 最新 TLS 指纹库
2. curl_cffi - 多指纹轮换
3. Playwright 池 - 浏览器实例池 (3个实例)
4. HTTP/2 支持 - 协议级别伪装

特性：
- 持久化指纹成功率数据
- 动态更新最优指纹
- 自动故障切换
"""

from typing import Optional, Dict, Any, List
from loguru import logger
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import asyncio
import random
import json
import time
import os


class TLSClientType(Enum):
    TLS_CLIENT = "tls_client"
    CURL_CFFI = "curl_cffi"
    HTTPX = "httpx"
    PLAYWRIGHT = "playwright"


@dataclass
class TLSClientConfig:
    client_type: TLSClientType
    impersonate: str
    priority: int
    success_rate: float = 0.0


@dataclass
class FingerprintStats:
    success_count: int = 0
    fail_count: int = 0
    last_used: float = 0.0
    last_success: float = 0.0
    
    @property
    def success_rate(self) -> float:
        total = self.success_count + self.fail_count
        return self.success_count / max(1, total)


class FingerprintPersistence:
    """指纹数据持久化管理"""
    
    DEFAULT_PATH = Path(__file__).parent.parent / "data" / "tls_fingerprint_stats.json"
    
    def __init__(self, storage_path: Optional[Path] = None):
        self._storage_path = storage_path or self.DEFAULT_PATH
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._data: Dict[str, Dict[str, Any]] = {}
        self._load()
    
    def _load(self):
        if self._storage_path.exists():
            try:
                with open(self._storage_path, 'r', encoding='utf-8') as f:
                    self._data = json.load(f)
                logger.info(f"加载指纹统计数据: {len(self._data)} 条记录")
            except Exception as e:
                logger.warning(f"加载指纹数据失败: {e}")
                self._data = {}
    
    def save(self):
        try:
            with open(self._storage_path, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            logger.debug(f"保存指纹统计数据: {len(self._data)} 条记录")
        except Exception as e:
            logger.warning(f"保存指纹数据失败: {e}")
    
    def get_stats(self, fingerprint: str) -> FingerprintStats:
        fp_data = self._data.get(fingerprint, {})
        return FingerprintStats(
            success_count=fp_data.get('success_count', 0),
            fail_count=fp_data.get('fail_count', 0),
            last_used=fp_data.get('last_used', 0),
            last_success=fp_data.get('last_success', 0),
        )
    
    def record_success(self, fingerprint: str, api_type: str = "default"):
        if fingerprint not in self._data:
            self._data[fingerprint] = {
                'success_count': 0,
                'fail_count': 0,
                'last_used': 0,
                'last_success': 0,
                'api_stats': {},
            }
        
        self._data[fingerprint]['success_count'] += 1
        self._data[fingerprint]['last_used'] = time.time()
        self._data[fingerprint]['last_success'] = time.time()
        
        if api_type not in self._data[fingerprint]['api_stats']:
            self._data[fingerprint]['api_stats'][api_type] = {'success': 0, 'fail': 0}
        self._data[fingerprint]['api_stats'][api_type]['success'] += 1
        
        self.save()
    
    def record_failure(self, fingerprint: str, api_type: str = "default"):
        if fingerprint not in self._data:
            self._data[fingerprint] = {
                'success_count': 0,
                'fail_count': 0,
                'last_used': 0,
                'last_success': 0,
                'api_stats': {},
            }
        
        self._data[fingerprint]['fail_count'] += 1
        self._data[fingerprint]['last_used'] = time.time()
        
        if api_type not in self._data[fingerprint]['api_stats']:
            self._data[fingerprint]['api_stats'][api_type] = {'success': 0, 'fail': 0}
        self._data[fingerprint]['api_stats'][api_type]['fail'] += 1
        
        self.save()
    
    def get_best_fingerprints(self, api_type: str = None, limit: int = 5) -> List[str]:
        fps_with_rates = []
        
        for fp, data in self._data.items():
            if api_type and api_type in data.get('api_stats', {}):
                api_data = data['api_stats'][api_type]
                total = api_data['success'] + api_data['fail']
                rate = api_data['success'] / max(1, total)
            else:
                total = data['success_count'] + data['fail_count']
                rate = data['success_count'] / max(1, total)
            
            fps_with_rates.append((fp, rate, total))
        
        fps_with_rates.sort(key=lambda x: (x[1], x[2]), reverse=True)
        
        return [fp for fp, _, _ in fps_with_rates[:limit]]


class TLSFingerprintPool:
    """TLS 指纹池 - 带持久化支持"""
    
    BROWSER_FINGERPRINTS = {
        'chrome': [
            'chrome120', 'chrome119', 'chrome118', 'chrome117', 'chrome116',
            'chrome110', 'chrome107', 'chrome104', 'chrome101', 'chrome99',
        ],
        'firefox': [
            'firefox120', 'firefox117', 'firefox110', 'firefox102',
        ],
        'safari': [
            'safari15_5', 'safari15_3', 'safari15_2',
        ],
        'edge': [
            'edge101', 'edge99',
        ],
    }
    
    def __init__(self, persistence: Optional[FingerprintPersistence] = None):
        self._persistence = persistence or FingerprintPersistence()
        self._current_fingerprint: Optional[str] = None
    
    def get_available_fingerprints(self) -> List[str]:
        all_fps = []
        for fps in self.BROWSER_FINGERPRINTS.values():
            all_fps.extend(fps)
        return all_fps
    
    def get_best_fingerprint(self, api_type: str = None) -> str:
        best_fps = self._persistence.get_best_fingerprints(api_type, limit=5)
        
        if best_fps:
            return random.choice(best_fps[:3])
        
        return random.choice(['chrome120', 'chrome119', 'chrome118'])
    
    def get_browser_type(self, fingerprint: str) -> str:
        for browser, fps in self.BROWSER_FINGERPRINTS.items():
            if fingerprint in fps:
                return browser
        return 'unknown'
    
    def report_success(self, fingerprint: str, api_type: str = "default"):
        self._persistence.record_success(fingerprint, api_type)
    
    def report_failure(self, fingerprint: str, api_type: str = "default"):
        self._persistence.record_failure(fingerprint, api_type)
    
    def get_stats(self) -> Dict[str, Any]:
        return self._persistence._data


class DrissionPagePool:
    """DrissionPage 浏览器实例池（替代 Playwright，避免 Windows 异步问题）"""
    
    def __init__(self, pool_size: int = 3):
        self._pool_size = pool_size
        self._pages: List[Any] = []
        self._available = asyncio.Queue()
        self._is_initialized = False
        self._lock = asyncio.Lock()
        self._session_established = False
    
    async def initialize(self) -> bool:
        if self._is_initialized:
            return True
        
        try:
            from playwright.async_api import async_playwright
            
            self._playwright = await async_playwright().start()
            
            launch_options = {
                'headless': True,
                'args': [
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-site-isolation-trials',
                ]
            }
            
            if self.DEFAULT_CHROMIUM_PATH.exists():
                launch_options['executable_path'] = str(self.DEFAULT_CHROMIUM_PATH)
                logger.info(f"使用 Chromium: {self.DEFAULT_CHROMIUM_PATH}")
            
            self._browser = await self._playwright.chromium.launch(**launch_options)
            
            for i in range(self._pool_size):
                context = await self._browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                    locale='zh-CN',
                    timezone_id='Asia/Shanghai',
                )
                
                await context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                    Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']});
                    window.chrome = {runtime: {}};
                """)
                
                page = await context.new_page()
                page.set_default_timeout(30000)
                
                self._contexts.append(context)
                self._pages.append(page)
                await self._available.put(page)
            
            self._is_initialized = True
            logger.info(f"Playwright 池初始化成功，{self._pool_size} 个实例")
            return True
            
        except Exception as e:
            logger.error(f"Playwright 池初始化失败: {e}")
            return False
    
    async def _ensure_session(self, page: Any) -> bool:
        """懒加载会话建立：仅在首次请求时访问首页"""
        if self._session_established:
            return True
        
        try:
            await page.goto("https://www.eastmoney.com/", timeout=30000)
            self._session_established = True
            logger.debug("Playwright 会话建立成功")
            return True
        except Exception as e:
            logger.warning(f"建立会话失败：{e}")
            return False
    
    async def acquire(self, timeout: float = 30.0) -> Optional[Any]:
        if not self._is_initialized:
            if not await self.initialize():
                return None
        
        try:
            page = await asyncio.wait_for(self._available.get(), timeout=timeout)
            await self._ensure_session(page)
            return page
        except asyncio.TimeoutError:
            logger.warning("获取 Playwright 实例超时")
            return None
    
    async def release(self, page: Any):
        if page:
            await self._available.put(page)
    
    async def execute(self, url: str, headers: Dict = None, cookies: Dict = None, 
                      timeout: int = 30) -> Optional[Dict]:
        page = await self.acquire()
        if not page:
            return None
        
        try:
            if cookies:
                context = self._contexts[self._pages.index(page)]
                await context.add_cookies([
                    {'name': k, 'value': v, 'domain': '.eastmoney.com'}
                    for k, v in cookies.items()
                ])
            
            response = await page.goto(url, timeout=timeout * 1000)
            
            if response and response.status == 200:
                try:
                    text_content = await page.evaluate("() => document.body.innerText")
                    import json
                    data = json.loads(text_content)
                    
                    if data.get('data') is not None:
                        return {
                            'status_code': response.status,
                            'content': text_content.encode(),
                            'text': text_content,
                            'headers': {},
                            'cookies': {},
                            'ok': True,
                            'data': data.get('data'),
                        }
                except json.JSONDecodeError:
                    pass
                except Exception:
                    pass
                
                content = await page.content()
                return {
                    'status_code': response.status,
                    'content': content.encode(),
                    'text': content,
                    'headers': {},
                    'cookies': {},
                    'ok': True,
                }
            
            return None
            
        except Exception as e:
            logger.debug(f"Playwright 执行失败: {type(e).__name__}")
            return None
        finally:
            await self.release(page)
    
    async def close(self):
        for page in self._pages:
            try:
                await page.close()
            except:
                pass
        
        for context in self._contexts:
            try:
                await context.close()
            except:
                pass
        
        if self._browser:
            try:
                await self._browser.close()
            except:
                pass
        
        if self._playwright:
            try:
                await self._playwright.stop()
            except:
                pass
        
        self._is_initialized = False
        logger.info("Playwright 池已关闭")


class TLSClientPool:
    """TLS 客户端池 - 支持 tls-client, curl_cffi, httpx"""
    
    def __init__(self, fingerprint_pool: Optional[TLSFingerprintPool] = None):
        self._tls_client = None
        self._curl_clients: Dict[str, Any] = {}
        self._httpx_client = None
        self._fingerprint_pool = fingerprint_pool or TLSFingerprintPool()
    
    async def initialize(self) -> bool:
        success = False
        
        try:
            import tls_client
            self._tls_client = tls_client.Session(client_identifier='chrome120')
            logger.info("tls-client 初始化成功")
            success = True
        except ImportError:
            logger.warning("tls-client 未安装，跳过")
        except Exception as e:
            logger.warning(f"tls-client 初始化失败: {e}")
        
        try:
            from curl_cffi.requests import Session
            
            for fp in ['chrome120', 'chrome119', 'chrome118', 'firefox120', 'chrome110']:
                self._curl_clients[fp] = Session(impersonate=fp)
            
            logger.info(f"curl_cffi 初始化成功，{len(self._curl_clients)} 个指纹")
            success = True
        except ImportError:
            logger.warning("curl_cffi 未安装，跳过")
        except Exception as e:
            logger.warning(f"curl_cffi 初始化失败: {e}")
        
        try:
            import httpx
            self._httpx_client = httpx.Client(
                http2=True,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                },
                timeout=30.0,
            )
            logger.info("httpx (HTTP/2) 初始化成功")
            success = True
        except ImportError:
            logger.warning("httpx 未安装，跳过")
        except Exception as e:
            logger.warning(f"httpx 初始化失败: {e}")
        
        return success
    
    def get_client(self, client_type: TLSClientType = None, fingerprint: str = None):
        if client_type == TLSClientType.TLS_CLIENT and self._tls_client:
            return ('tls_client', self._tls_client, fingerprint or 'chrome120')
        
        if client_type == TLSClientType.HTTPX and self._httpx_client:
            return ('httpx', self._httpx_client, 'http2')
        
        if client_type == TLSClientType.CURL_CFFI or client_type is None:
            fp = fingerprint or self._fingerprint_pool.get_best_fingerprint()
            if fp in self._curl_clients:
                return ('curl_cffi', self._curl_clients[fp], fp)
        
        return None
    
    def get_available_fingerprints(self) -> List[str]:
        return self._fingerprint_pool.get_available_fingerprints()
    
    def get_best_fingerprint(self, api_type: str = None) -> str:
        return self._fingerprint_pool.get_best_fingerprint(api_type)
    
    def report_success(self, client_type: str, fingerprint: str, api_type: str = "default"):
        self._fingerprint_pool.report_success(fingerprint, api_type)
    
    def report_failure(self, client_type: str, fingerprint: str, api_type: str = "default"):
        self._fingerprint_pool.report_failure(fingerprint, api_type)
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            'tls_client_available': self._tls_client is not None,
            'curl_cffi_clients': list(self._curl_clients.keys()),
            'httpx_available': self._httpx_client is not None,
            'fingerprint_stats': self._fingerprint_pool.get_stats(),
        }
    
    def close(self):
        for client in self._curl_clients.values():
            try:
                client.close()
            except:
                pass
        
        if self._httpx_client:
            try:
                self._httpx_client.close()
            except:
                pass


class HybridTLSClient:
    """混合 TLS 客户端 - 多层自动切换
    
    层级策略：
    1. tls-client (最新 TLS 指纹)
    2. curl_cffi (多指纹轮换)
    3. httpx (HTTP/2 协议)
    4. Playwright 池 (浏览器实例)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._config = {
            'max_retries_per_client': 2,
            'rotate_fingerprint_on_fail': True,
            'fallback_to_playwright': True,
            'playwright_pool_size': 3,
            'enable_http2': True,
            **(config or {})
        }
        
        self._persistence = FingerprintPersistence()
        self._fingerprint_pool = TLSFingerprintPool(self._persistence)
        self._client_pool = TLSClientPool(self._fingerprint_pool)
        self._playwright_pool: Optional[PlaywrightPool] = None
        
        self._is_initialized = False
    
    async def initialize(self) -> bool:
        """懒加载初始化：不预先创建 Playwright 实例，仅在首次请求时创建"""
        success = await self._client_pool.initialize()
        
        if self._config['fallback_to_playwright']:
            self._playwright_pool = PlaywrightPool(self._config['playwright_pool_size'])
            # Playwright 池将在首次请求时初始化，不阻塞启动
        else:
            self._playwright_pool = None
        
        self._is_initialized = success
        return success
    
    async def get(
        self,
        url: str,
        headers: Optional[Dict] = None,
        cookies: Optional[Dict] = None,
        timeout: int = 30,
        api_type: str = "default"
    ) -> Any:
        if not self._is_initialized:
            raise RuntimeError("客户端未初始化")
        
        result = await self._try_tls_client(url, headers, cookies, timeout, api_type)
        if result:
            return result
        
        result = await self._try_curl_cffi_rotate(url, headers, cookies, timeout, api_type)
        if result:
            return result
        
        if self._config['enable_http2']:
            result = await self._try_httpx(url, headers, cookies, timeout, api_type)
            if result:
                return result
        
        if self._config['fallback_to_playwright']:
            result = await self._try_playwright(url, headers, cookies, timeout)
            if result:
                return result
        
        raise Exception("所有 TLS 客户端均失败")
    
    async def _try_tls_client(self, url, headers, cookies, timeout, api_type):
        client_info = self._client_pool.get_client(TLSClientType.TLS_CLIENT)
        if not client_info:
            return None
        
        client_type, client, fingerprint = client_info
        
        try:
            response = client.get(
                url,
                headers=headers,
                cookies=cookies,
                timeout_seconds=timeout
            )
            
            if response.status_code == 200:
                self._client_pool.report_success(client_type, fingerprint, api_type)
                return self._wrap_response(response)
            
        except Exception as e:
            logger.debug(f"tls-client 失败: {type(e).__name__}")
            self._client_pool.report_failure(client_type, fingerprint, api_type)
        
        return None
    
    async def _try_curl_cffi_rotate(self, url, headers, cookies, timeout, api_type):
        fingerprints = self._client_pool.get_available_fingerprints()[:5]
        
        for fp in fingerprints:
            client_info = self._client_pool.get_client(TLSClientType.CURL_CFFI, fp)
            if not client_info:
                continue
            
            client_type, client, fingerprint = client_info
            
            try:
                response = client.get(
                    url,
                    headers=headers,
                    cookies=cookies,
                    timeout=timeout
                )
                
                if response.status_code == 200:
                    self._client_pool.report_success(client_type, fingerprint, api_type)
                    return self._wrap_response(response)
                    
            except Exception as e:
                logger.debug(f"curl_cffi ({fingerprint}) 失败: {type(e).__name__}")
                self._client_pool.report_failure(client_type, fingerprint, api_type)
        
        return None
    
    async def _try_httpx(self, url, headers, cookies, timeout, api_type):
        client_info = self._client_pool.get_client(TLSClientType.HTTPX)
        if not client_info:
            return None
        
        client_type, client, fingerprint = client_info
        
        try:
            response = client.get(
                url,
                headers=headers,
                cookies=cookies,
                timeout=timeout
            )
            
            if response.status_code == 200:
                self._client_pool.report_success(client_type, fingerprint, api_type)
                return self._wrap_httpx_response(response)
            
        except Exception as e:
            logger.debug(f"httpx 失败: {type(e).__name__}")
            self._client_pool.report_failure(client_type, fingerprint, api_type)
        
        return None
    
    async def _try_playwright(self, url, headers, cookies, timeout):
        if not self._playwright_pool:
            return None
        
        if not self._playwright_pool._is_initialized:
            if not await self._playwright_pool.initialize():
                return None
        
        return await self._playwright_pool.execute(url, headers, cookies, timeout)
    
    def _wrap_response(self, response) -> Dict:
        return {
            'status_code': response.status_code,
            'content': response.content,
            'text': response.text,
            'headers': dict(response.headers),
            'cookies': response.cookies if hasattr(response, 'cookies') else {},
            'ok': response.status_code == 200,
        }
    
    def _wrap_httpx_response(self, response) -> Dict:
        return {
            'status_code': response.status_code,
            'content': response.content,
            'text': response.text,
            'headers': dict(response.headers),
            'cookies': dict(response.cookies) if response.cookies else {},
            'ok': response.status_code == 200,
        }
    
    def get_stats(self) -> Dict[str, Any]:
        stats = self._client_pool.get_stats()
        if self._playwright_pool:
            stats['playwright_pool_size'] = self._playwright_pool._pool_size
            stats['playwright_initialized'] = self._playwright_pool._is_initialized
        return stats
    
    async def close(self):
        self._client_pool.close()
        if self._playwright_pool:
            await self._playwright_pool.close()


async def test_hybrid_tls_client():
    """测试混合 TLS 客户端"""
    print("\n=== 测试增强版混合 TLS 客户端 ===\n")
    
    client = HybridTLSClient({
        'playwright_pool_size': 3,
        'enable_http2': True,
        'fallback_to_playwright': True,
    })
    
    print("初始化...")
    success = await client.initialize()
    
    if not success:
        print("初始化失败")
        return
    
    print(f"状态: {client.get_stats()}")
    
    test_apis = [
        ("K线数据", "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=0.000001&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt=101&fqt=1&end=20500101&lmt=10", "kline"),
        ("资金流向", "https://push2.eastmoney.com/api/qt/stock/fflow/kline/get?secid=0.000001&klt=101&lmt=10&fields1=f1,f2,f3,f7&fields2=f51,f52,f53,f54,f55,f56,f58,f60", "fund_flow"),
        ("A股列表", "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=10&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23&fields=f12,f14,f2,f3", "stock_list"),
    ]
    
    for name, url, api_type in test_apis:
        print(f"\n测试: {name}")
        try:
            result = await client.get(url, timeout=15, api_type=api_type)
            print(f"  状态码: {result['status_code']}")
            print(f"  响应长度: {len(result['text'])}")
            print(f"  成功: {result['ok']}")
        except Exception as e:
            print(f"  失败: {e}")
    
    print(f"\n最终统计: {json.dumps(client.get_stats(), indent=2, ensure_ascii=False, default=str)}")
    
    await client.close()


if __name__ == "__main__":
    asyncio.run(test_hybrid_tls_client())

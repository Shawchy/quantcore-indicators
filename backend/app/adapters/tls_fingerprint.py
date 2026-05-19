"""
TLS 指纹伪装模块

解决 Python requests TLS 指纹被识别的问题：
1. curl_cffi - 模拟浏览器 TLS 指纹
2. tls-client - 专门的 TLS 指纹模拟库
3. httpx with HTTP/2 - 使用 HTTP/2 协议

安装：
    pip install curl_cffi
    pip install tls-client
    pip install httpx
"""

from typing import Optional, Dict, Any, List
from loguru import logger
import os


class TLSFingerprintClient:
    """TLS 指纹伪装客户端
    
    支持多种后端：
    - curl_cffi: 模拟 Chrome/Firefox/Safari 的 TLS 指纹
    - tls-client: 专门的 TLS 指纹模拟库
    - httpx: HTTP/2 支持
    """
    
    def __init__(self, backend: str = "curl_cffi", impersonate: str = "chrome120"):
        self._backend = backend
        self._impersonate = impersonate
        self._client = None
        self._session = None
        
        self._available_backends = self._check_available_backends()
    
    def _check_available_backends(self) -> Dict[str, bool]:
        backends = {}
        
        try:
            from curl_cffi import requests as curl_requests
            backends['curl_cffi'] = True
        except ImportError:
            backends['curl_cffi'] = False
        
        try:
            import tls_client
            backends['tls_client'] = True
        except ImportError:
            backends['tls_client'] = False
        
        try:
            import httpx
            backends['httpx'] = True
        except ImportError:
            backends['httpx'] = False
        
        return backends
    
    def initialize(self) -> bool:
        if self._backend == "curl_cffi" and self._available_backends.get('curl_cffi'):
            return self._init_curl_cffi()
        elif self._backend == "tls_client" and self._available_backends.get('tls_client'):
            return self._init_tls_client()
        elif self._backend == "httpx" and self._available_backends.get('httpx'):
            return self._init_httpx()
        else:
            for backend, available in self._available_backends.items():
                if available:
                    logger.info(f"使用可用的后端: {backend}")
                    self._backend = backend
                    return self.initialize()
            
            logger.error("没有可用的 TLS 指纹伪装后端")
            logger.info("请安装其中一个: pip install curl_cffi / pip install tls-client / pip install httpx")
            return False
    
    def _init_curl_cffi(self) -> bool:
        try:
            from curl_cffi import requests as curl_requests
            from curl_cffi.requests import Session
            
            self._session = Session(impersonate=self._impersonate)
            self._client = curl_requests
            
            logger.info(f"curl_cffi 初始化成功，模拟浏览器: {self._impersonate}")
            return True
            
        except Exception as e:
            logger.error(f"curl_cffi 初始化失败: {e}")
            return False
    
    def _init_tls_client(self) -> bool:
        try:
            import tls_client
            
            self._session = tls_client.Session(
                client_identifier=self._impersonate
            )
            self._client = tls_client
            
            logger.info(f"tls_client 初始化成功，模拟浏览器: {self._impersonate}")
            return True
            
        except Exception as e:
            logger.error(f"tls_client 初始化失败: {e}")
            return False
    
    def _init_httpx(self) -> bool:
        try:
            import httpx
            
            self._session = httpx.Client(
                http2=True,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                }
            )
            self._client = httpx
            
            logger.info("httpx 初始化成功，启用 HTTP/2")
            return True
            
        except Exception as e:
            logger.error(f"httpx 初始化失败: {e}")
            return False
    
    def get(
        self,
        url: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        cookies: Optional[Dict] = None,
        timeout: int = 30
    ) -> Any:
        if self._backend == "curl_cffi":
            return self._get_curl_cffi(url, params, headers, cookies, timeout)
        elif self._backend == "tls_client":
            return self._get_tls_client(url, params, headers, cookies, timeout)
        elif self._backend == "httpx":
            return self._get_httpx(url, params, headers, cookies, timeout)
        else:
            raise RuntimeError("未初始化客户端")
    
    def _get_curl_cffi(self, url, params, headers, cookies, timeout):
        response = self._session.get(
            url,
            params=params,
            headers=headers,
            cookies=cookies,
            timeout=timeout
        )
        return TLSResponse(
            status_code=response.status_code,
            content=response.content,
            text=response.text,
            headers=dict(response.headers),
            cookies=dict(response.cookies),
            ok=response.status_code == 200
        )
    
    def _get_tls_client(self, url, params, headers, cookies, timeout):
        response = self._session.get(
            url,
            params=params,
            headers=headers,
            cookies=cookies,
            timeout_seconds=timeout
        )
        return TLSResponse(
            status_code=response.status_code,
            content=response.content,
            text=response.text,
            headers=dict(response.headers),
            cookies=response.cookies,
            ok=response.status_code == 200
        )
    
    def _get_httpx(self, url, params, headers, cookies, timeout):
        response = self._session.get(
            url,
            params=params,
            headers=headers,
            cookies=cookies,
            timeout=timeout
        )
        return TLSResponse(
            status_code=response.status_code,
            content=response.content,
            text=response.text,
            headers=dict(response.headers),
            cookies=dict(response.cookies),
            ok=response.status_code == 200
        )
    
    def close(self):
        if self._session:
            try:
                self._session.close()
            except Exception:
                pass
    
    @property
    def backend_info(self) -> Dict[str, Any]:
        return {
            'current_backend': self._backend,
            'impersonate': self._impersonate,
            'available_backends': self._available_backends,
        }


class TLSResponse:
    """统一的响应对象"""
    
    def __init__(
        self,
        status_code: int,
        content: bytes,
        text: str,
        headers: Dict,
        cookies: Dict,
        ok: bool
    ):
        self.status_code = status_code
        self.content = content
        self.text = text
        self.headers = headers
        self.cookies = cookies
        self.ok = ok
    
    def json(self):
        import json
        return json.loads(self.text)
    
    def __repr__(self):
        return f"<TLSResponse [{self.status_code}]>"


class TLSFingerprintInjector:
    """TLS 指纹注入器
    
    替换 requests 库，使用 TLS 指纹伪装
    """
    
    def __init__(self, backend: str = "curl_cffi", impersonate: str = "chrome120"):
        self._client = TLSFingerprintClient(backend, impersonate)
        self._original_request = None
        self._original_session_request = None
        self._is_patched = False
    
    def initialize(self) -> bool:
        return self._client.initialize()
    
    def patch_requests(self) -> bool:
        if self._is_patched:
            return True
        
        try:
            import requests
            
            self._original_request = requests.request
            self._original_session_request = requests.Session.request
            
            client = self._client
            
            def patched_request(method, url, **kwargs):
                if method.upper() == 'GET':
                    response = client.get(
                        url,
                        params=kwargs.get('params'),
                        headers=kwargs.get('headers'),
                        cookies=kwargs.get('cookies'),
                        timeout=kwargs.get('timeout', 30)
                    )
                    
                    return TLSResponseAdapter(response)
                else:
                    return self._original_request(method, url, **kwargs)
            
            def patched_session_request(self_session, method, url, **kwargs):
                if method.upper() == 'GET':
                    merged_cookies = dict(self_session.cookies)
                    if kwargs.get('cookies'):
                        merged_cookies.update(kwargs['cookies'])
                    
                    merged_headers = dict(self_session.headers)
                    if kwargs.get('headers'):
                        merged_headers.update(kwargs['headers'])
                    
                    response = client.get(
                        url,
                        params=kwargs.get('params'),
                        headers=merged_headers,
                        cookies=merged_cookies,
                        timeout=kwargs.get('timeout', 30)
                    )
                    
                    return TLSResponseAdapter(response)
                else:
                    return self._original_session_request(self_session, method, url, **kwargs)
            
            requests.request = patched_request
            requests.Session.request = patched_session_request
            
            self._is_patched = True
            logger.info("已替换 requests 为 TLS 指纹伪装客户端")
            return True
            
        except Exception as e:
            logger.error(f"Patch requests 失败: {e}")
            return False
    
    def unpatch_requests(self):
        if not self._is_patched:
            return
        
        try:
            import requests
            
            if self._original_request:
                requests.request = self._original_request
            if self._original_session_request:
                requests.Session.request = self._original_session_request
            
            self._is_patched = False
            logger.info("已恢复原始 requests")
        except Exception as e:
            logger.error(f"恢复 requests 失败: {e}")
    
    def close(self):
        self.unpatch_requests()
        self._client.close()


class TLSResponseAdapter:
    """适配器，使 TLSResponse 兼容 requests.Response"""
    
    def __init__(self, tls_response: TLSResponse):
        self._response = tls_response
        self.status_code = tls_response.status_code
        self.content = tls_response.content
        self.text = tls_response.text
        self.headers = tls_response.headers
        self.cookies = tls_response.cookies
        self.ok = tls_response.ok
    
    def json(self):
        return self._response.json()
    
    def raise_for_status(self):
        if not self.ok:
            raise Exception(f"HTTP {self.status_code}")
    
    def __getattr__(self, name):
        return getattr(self._response, name)
    
    def __repr__(self):
        return f"<Response [{self.status_code}]>"


async def test_tls_fingerprint():
    """测试 TLS 指纹伪装"""
    print("\n=== 测试 TLS 指纹伪装 ===\n")
    
    injector = TLSFingerprintInjector(backend="curl_cffi", impersonate="chrome120")
    
    print("1. 初始化 TLS 指纹客户端...")
    if not injector.initialize():
        print("初始化失败")
        return False
    
    print(f"后端信息: {injector._client.backend_info}")
    
    print("\n2. 测试请求东方财富 API...")
    
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
        'fields': 'f12,f14,f2,f3'
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Referer': 'https://quote.eastmoney.com/',
    }
    
    try:
        response = injector._client.get(url, params=params, headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应长度: {len(response.text)}")
        
        if response.ok:
            data = response.json()
            print(f"JSON 解析成功")
            if 'data' in data and data['data']:
                print(f"获取到 {len(data['data'].get('diff', []))} 条数据")
                for item in data['data'].get('diff', [])[:3]:
                    print(f"  - {item.get('f12')}: {item.get('f14')}")
            return True
        else:
            print(f"请求失败: {response.status_code}")
            
    except Exception as e:
        print(f"请求异常: {e}")
    
    injector.close()
    return False


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_tls_fingerprint())

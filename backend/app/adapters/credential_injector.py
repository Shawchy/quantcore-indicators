"""
凭证注入器

使用 Playwright 获取凭证，然后注入到 AKShare 中：
1. Playwright 访问目标网站获取 Cookie
2. 将 Cookie 注入到 requests Session
3. AKShare 使用带有凭证的 Session 发送请求

原理：
- AKShare 底层使用 requests 库
- 通过 monkey-patch requests，注入 Cookie 和 Headers
- 实现无缝集成

增强版：
- 支持 curl_cffi（TLS 指纹伪装）
- 解决 Python requests TLS 指纹被识别的问题
"""

from typing import Optional, List, Dict, Any
from loguru import logger
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import random
import json
import os
import time
import hashlib


class TLSPatchMode(Enum):
    NONE = "none"
    CURL_CFFI = "curl_cffi"
    TLS_CLIENT = "tls_client"


class CurlResponseAdapter:
    """适配 curl_cffi 响应对象，使其兼容 requests.Response"""
    
    def __init__(self, curl_response):
        self._response = curl_response
        self.status_code = curl_response.status_code
        self.content = curl_response.content
        self.text = curl_response.text
        self.headers = dict(curl_response.headers)
        self.cookies = curl_response.cookies
        self.ok = curl_response.status_code == 200
        self.url = getattr(curl_response, 'url', '')
    
    def json(self):
        import json
        return json.loads(self.text)
    
    def raise_for_status(self):
        if not self.ok:
            raise Exception(f"HTTP {self.status_code}")
    
    def __repr__(self):
        return f"<Response [{self.status_code}]>"


class CredentialInjector:
    """凭证注入器
    
    使用 Playwright 获取网站凭证，注入到 AKShare 请求中
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._config = {
            'headless': True,
            'cookie_max_age_hours': 24,
            'refresh_before_minutes': 30,
            'target_domains': [
                'eastmoney.com',
                'quote.eastmoney.com',
                'data.eastmoney.com',
                'fund.eastmoney.com',
            ],
            'tls_patch_mode': TLSPatchMode.CURL_CFFI,
            'impersonate': 'chrome120',
            **(config or {})
        }
        
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        
        self._cookies: Dict[str, List[Dict]] = {}
        self._cookies_updated_at: Dict[str, datetime] = {}
        
        self._user_agents: Dict[str, str] = {}
        self._headers: Dict[str, Dict[str, str]] = {}
        
        self._original_request = None
        self._original_session_request = None
        self._is_patched = False
        self._is_initialized = False
        
        self._curl_session = None
        self._tls_mode: TLSPatchMode = TLSPatchMode.NONE
    
    async def initialize(self) -> bool:
        try:
            from playwright.async_api import async_playwright
            
            playwright_manager = async_playwright()
            self._playwright = await playwright_manager.start()
            
            if self._playwright is None:
                raise RuntimeError("Playwright start() returned None")
            
            browsers_path = os.environ.get(
                'PLAYWRIGHT_BROWSERS_PATH',
                'd:/PROJ/Quant/backend/playwright_browsers'
            )
            chromium_exe = os.path.join(browsers_path, 'chromium-1148', 'chrome-win', 'chrome.exe')
            
            launch_options = {'headless': self._config['headless']}
            if os.path.exists(chromium_exe):
                launch_options['executable_path'] = chromium_exe
                logger.info(f"使用 Chromium: {chromium_exe}")
            
            self._browser = await self._playwright.chromium.launch(**launch_options)
            
            self._is_initialized = True
            logger.info("凭证注入器初始化成功")
            return True
            
        except ImportError:
            logger.warning("Playwright 未安装，凭证注入功能不可用")
            return False
        except Exception as e:
            logger.error(f"凭证注入器初始化失败: {e}")
            return False
    
    async def close(self) -> None:
        try:
            if self._page:
                await self._page.close()
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
        except Exception as e:
            logger.error(f"关闭凭证注入器失败: {e}")
        finally:
            self._is_initialized = False
            self._is_patched = False
            self._playwright = None
            self._browser = None
            self._context = None
            self._page = None
            logger.info("凭证注入器已关闭")
    
    async def fetch_credentials(self, domain: str) -> bool:
        if not self._is_initialized:
            logger.warning("凭证注入器未初始化")
            return False
        
        try:
            if self._context:
                await self._context.close()
            
            self._context = await self._browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                locale='zh-CN',
                timezone_id='Asia/Shanghai',
                user_agent=self._get_random_user_agent(),
            )
            
            self._page = await self._context.new_page()
            
            if 'eastmoney' in domain:
                success = await self._fetch_eastmoney_credentials(domain)
            else:
                success = await self._fetch_generic_credentials(domain)
            
            if success:
                self._cookies[domain] = await self._context.cookies()
                self._cookies_updated_at[domain] = datetime.now()
                
                await self._extract_headers(domain)
                
                logger.info(f"成功获取 {domain} 的凭证")
            
            return success
            
        except Exception as e:
            logger.error(f"获取凭证失败 {domain}: {e}")
            return False
    
    async def _fetch_eastmoney_credentials(self, domain: str) -> bool:
        try:
            if 'quote' in domain:
                url = "https://quote.eastmoney.com/center/gridlist.html"
            elif 'data' in domain:
                url = "https://data.eastmoney.com/"
            else:
                url = "https://www.eastmoney.com/"
            
            logger.info(f"访问 {url} 获取凭证...")
            
            await self._page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            await asyncio.sleep(3)
            
            try:
                await self._page.wait_for_load_state('networkidle', timeout=10000)
            except Exception:
                pass
            
            await self._simulate_human_behavior()
            
            return True
            
        except Exception as e:
            logger.error(f"获取东方财富凭证失败: {e}")
            return False
    
    async def _fetch_generic_credentials(self, domain: str) -> bool:
        try:
            url = f"https://{domain}"
            
            await self._page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(2)
            
            return True
            
        except Exception as e:
            logger.error(f"获取通用凭证失败: {e}")
            return False
    
    async def _simulate_human_behavior(self) -> None:
        try:
            import random
            
            for _ in range(random.randint(2, 5)):
                x = random.randint(100, 1800)
                y = random.randint(100, 900)
                await self._page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.1, 0.3))
            
            if random.random() < 0.5:
                await self._page.evaluate('window.scrollBy(0, 300)')
                await asyncio.sleep(0.5)
                await self._page.evaluate('window.scrollBy(0, -300)')
                
        except Exception:
            pass
    
    async def _extract_headers(self, domain: str) -> None:
        try:
            user_agent = await self._page.evaluate('navigator.userAgent')
            self._user_agents[domain] = user_agent
            
            self._headers[domain] = {
                'User-Agent': user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
        except Exception as e:
            logger.warning(f"提取 Headers 失败: {e}")
    
    def _get_random_user_agent(self) -> str:
        import random
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        ]
        return random.choice(user_agents)
    
    def get_cookies(self, domain: str) -> List[Dict]:
        cookies = self._cookies.get(domain, [])
        
        if cookies:
            updated_at = self._cookies_updated_at.get(domain)
            if updated_at:
                age = datetime.now() - updated_at
                max_age = timedelta(hours=self._config['cookie_max_age_hours'])
                
                if age > max_age:
                    logger.warning(f"{domain} 的 Cookie 已过期")
                    return []
        
        return cookies
    
    def get_cookie_dict(self, domain: str) -> Dict[str, str]:
        cookies = self.get_cookies(domain)
        return {c['name']: c['value'] for c in cookies if 'name' in c and 'value' in c}
    
    def get_headers(self, domain: str) -> Dict[str, str]:
        return self._headers.get(domain, {
            'User-Agent': self._get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        })
    
    def patch_requests(self, domain: str = 'eastmoney.com') -> bool:
        if self._is_patched:
            logger.debug("requests 已被 patch")
            return True
        
        try:
            import requests
            
            self._original_request = requests.request
            self._original_session_request = requests.Session.request
            
            cookies = self.get_cookie_dict(domain)
            headers = self.get_headers(domain)
            
            injector = self
            
            def patched_request(method, url, **kwargs):
                if any(d in url for d in injector._config['target_domains']):
                    if 'cookies' not in kwargs:
                        kwargs['cookies'] = cookies
                    elif isinstance(kwargs['cookies'], dict):
                        kwargs['cookies'].update(cookies)
                    
                    if 'headers' not in kwargs:
                        kwargs['headers'] = headers.copy()
                    elif isinstance(kwargs['headers'], dict):
                        merged_headers = headers.copy()
                        merged_headers.update(kwargs['headers'])
                        kwargs['headers'] = merged_headers
                
                return injector._original_request(method, url, **kwargs)
            
            def patched_session_request(self_session, method, url, **kwargs):
                if any(d in url for d in injector._config['target_domains']):
                    if 'cookies' not in kwargs:
                        kwargs['cookies'] = cookies
                    elif isinstance(kwargs['cookies'], dict):
                        kwargs['cookies'].update(cookies)
                    
                    if 'headers' not in kwargs:
                        kwargs['headers'] = headers.copy()
                    elif isinstance(kwargs['headers'], dict):
                        merged_headers = headers.copy()
                        merged_headers.update(kwargs['headers'])
                        kwargs['headers'] = merged_headers
                
                return injector._original_session_request(self_session, method, url, **kwargs)
            
            requests.request = patched_request
            requests.Session.request = patched_session_request
            
            self._is_patched = True
            logger.info(f"已注入 {domain} 的凭证到 requests")
            return True
            
        except Exception as e:
            logger.error(f"Patch requests 失败: {e}")
            return False
    
    def unpatch_requests(self) -> None:
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
    
    def _init_curl_cffi(self) -> bool:
        """初始化 curl_cffi TLS 指纹伪装"""
        try:
            from curl_cffi.requests import Session
            
            impersonate = self._config.get('impersonate', 'chrome120')
            self._curl_session = Session(impersonate=impersonate)
            self._tls_mode = TLSPatchMode.CURL_CFFI
            
            logger.info(f"curl_cffi 初始化成功，模拟浏览器: {impersonate}")
            return True
            
        except ImportError:
            logger.warning("curl_cffi 未安装，TLS 指纹伪装不可用")
            logger.info("安装命令: pip install curl_cffi")
            return False
        except Exception as e:
            logger.error(f"curl_cffi 初始化失败: {e}")
            return False
    
    def patch_requests_with_tls(self, domain: str = 'eastmoney.com') -> bool:
        """使用 TLS 指纹伪装 patch requests
        
        这是推荐的方案：
        1. 使用 Playwright 获取 Cookie
        2. 使用 curl_cffi 发送请求（TLS 指纹伪装）
        """
        if self._is_patched:
            return True
        
        if not self._init_curl_cffi():
            logger.warning("TLS 指纹伪装初始化失败，回退到普通模式")
            return self.patch_requests(domain)
        
        try:
            import requests
            
            self._original_request = requests.request
            self._original_session_request = requests.Session.request
            
            cookies = self.get_cookie_dict(domain)
            headers = self.get_headers(domain)
            
            curl_session = self._curl_session
            config = self._config
            
            def patched_request(method, url, **kwargs):
                if any(d in url for d in config['target_domains']):
                    merged_cookies = cookies.copy()
                    if kwargs.get('cookies'):
                        merged_cookies.update(kwargs['cookies'])
                    
                    merged_headers = headers.copy()
                    if kwargs.get('headers'):
                        merged_headers.update(kwargs['headers'])
                    
                    try:
                        if method.upper() == 'GET':
                            response = curl_session.get(
                                url,
                                params=kwargs.get('params'),
                                headers=merged_headers,
                                cookies=merged_cookies,
                                timeout=kwargs.get('timeout', 30)
                            )
                        elif method.upper() == 'POST':
                            response = curl_session.post(
                                url,
                                data=kwargs.get('data'),
                                json=kwargs.get('json'),
                                headers=merged_headers,
                                cookies=merged_cookies,
                                timeout=kwargs.get('timeout', 30)
                            )
                        else:
                            return self._original_request(method, url, **kwargs)
                        
                        return CurlResponseAdapter(response)
                        
                    except Exception as e:
                        logger.warning(f"curl_cffi 请求失败: {e}，回退到 requests")
                        return self._original_request(method, url, **kwargs)
                else:
                    return self._original_request(method, url, **kwargs)
            
            def patched_session_request(self_session, method, url, **kwargs):
                if any(d in url for d in config['target_domains']):
                    merged_cookies = dict(self_session.cookies)
                    merged_cookies.update(cookies)
                    if kwargs.get('cookies'):
                        merged_cookies.update(kwargs['cookies'])
                    
                    merged_headers = dict(self_session.headers)
                    merged_headers.update(headers)
                    if kwargs.get('headers'):
                        merged_headers.update(kwargs['headers'])
                    
                    try:
                        if method.upper() == 'GET':
                            response = curl_session.get(
                                url,
                                params=kwargs.get('params'),
                                headers=merged_headers,
                                cookies=merged_cookies,
                                timeout=kwargs.get('timeout', 30)
                            )
                        elif method.upper() == 'POST':
                            response = curl_session.post(
                                url,
                                data=kwargs.get('data'),
                                json=kwargs.get('json'),
                                headers=merged_headers,
                                cookies=merged_cookies,
                                timeout=kwargs.get('timeout', 30)
                            )
                        else:
                            return self._original_session_request(self_session, method, url, **kwargs)
                        
                        return CurlResponseAdapter(response)
                        
                    except Exception as e:
                        logger.warning(f"curl_cffi 请求失败: {e}，回退到 requests")
                        return self._original_session_request(self_session, method, url, **kwargs)
                else:
                    return self._original_session_request(self_session, method, url, **kwargs)
            
            requests.request = patched_request
            requests.Session.request = patched_session_request
            
            self._is_patched = True
            logger.info(f"已注入 {domain} 的凭证到 requests (TLS 指纹伪装模式)")
            return True
            
        except Exception as e:
            logger.error(f"TLS Patch requests 失败: {e}")
            return False
    
    def get_tls_status(self) -> Dict[str, Any]:
        """获取 TLS 指纹伪装状态"""
        return {
            'tls_mode': self._tls_mode.value,
            'curl_session_active': self._curl_session is not None,
            'impersonate': self._config.get('impersonate'),
        }
    
    async def refresh_credentials_if_needed(self, domain: str) -> bool:
        updated_at = self._cookies_updated_at.get(domain)
        
        if not updated_at:
            return await self.fetch_credentials(domain)
        
        refresh_threshold = timedelta(
            minutes=self._config['refresh_before_minutes']
        )
        max_age = timedelta(hours=self._config['cookie_max_age_hours'])
        
        age = datetime.now() - updated_at
        
        if age > max_age - refresh_threshold:
            logger.info(f"刷新 {domain} 的凭证...")
            return await self.fetch_credentials(domain)
        
        return True
    
    def get_status(self) -> Dict[str, Any]:
        return {
            'initialized': self._is_initialized,
            'patched': self._is_patched,
            'domains': list(self._cookies.keys()),
            'cookies_count': {
                domain: len(cookies) 
                for domain, cookies in self._cookies.items()
            },
            'last_updated': {
                domain: dt.isoformat() if dt else None
                for domain, dt in self._cookies_updated_at.items()
            },
        }


class AkShareWithCredential:
    """带凭证注入的 AKShare 包装器
    
    使用方法：
        async with AkShareWithCredential() as akshare:
            df = akshare.stock_zh_a_spot_em()
        
        # 使用 TLS 指纹伪装（推荐）
        async with AkShareWithCredential(use_tls=True) as akshare:
            df = akshare.stock_zh_a_spot_em()
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, use_tls: bool = True):
        self._injector = CredentialInjector(config)
        self._domain = 'eastmoney.com'
        self._use_tls = use_tls
    
    async def __aenter__(self):
        await self._injector.initialize()
        await self._injector.fetch_credentials(self._domain)
        
        if self._use_tls:
            self._injector.patch_requests_with_tls(self._domain)
        else:
            self._injector.patch_requests(self._domain)
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._injector.unpatch_requests()
        await self._injector.close()
    
    async def initialize(self) -> bool:
        success = await self._injector.initialize()
        if success:
            await self._injector.fetch_credentials(self._domain)
            
            if self._use_tls:
                self._injector.patch_requests_with_tls(self._domain)
            else:
                self._injector.patch_requests(self._domain)
        
        return success
    
    async def close(self) -> None:
        self._injector.unpatch_requests()
        await self._injector.close()
    
    async def refresh_credentials(self) -> bool:
        return await self._injector.refresh_credentials_if_needed(self._domain)
    
    def get_status(self) -> Dict[str, Any]:
        return self._injector.get_status()
    
    def get_stock_zh_a_spot(self):
        import akshare as ak
        return ak.stock_zh_a_spot_em()
    
    def get_stock_individual_info(self, symbol: str):
        import akshare as ak
        return ak.stock_individual_info_em(symbol=symbol)
    
    def get_stock_zh_a_hist(
        self,
        symbol: str,
        period: str = "daily",
        start_date: str = "",
        end_date: str = "",
        adjust: str = "qfq"
    ):
        import akshare as ak
        return ak.stock_zh_a_hist(
            symbol=symbol,
            period=period,
            start_date=start_date,
            end_date=end_date,
            adjust=adjust
        )
    
    def get_board_industry_name_em(self):
        import akshare as ak
        return ak.stock_board_industry_name_em()
    
    def get_board_concept_name_em(self):
        import akshare as ak
        return ak.stock_board_concept_name_em()
    
    def get_individual_fund_flow(self, stock: str, market: str = "sz"):
        import akshare as ak
        return ak.stock_individual_fund_flow(stock=stock, market=market)
    
    def get_stock_fund_flow(self, stock: str, market: str = "sz"):
        import akshare as ak
        return ak.stock_individual_fund_flow(stock=stock, market=market)
    
    def get_industry_fund_flow(self):
        import akshare as ak
        return ak.stock_fund_flow_industry()
    
    def get_concept_fund_flow(self):
        import akshare as ak
        return ak.stock_fund_flow_concept()
    
    def __getattr__(self, name):
        import akshare as ak
        return getattr(ak, name)


class EfinanceWithCredential:
    """带凭证注入的 Efinance 包装器
    
    使用方法：
        async with EfinanceWithCredential() as ef:
            df = ef.get_realtime_quotes()
        
        # 使用 TLS 指纹伪装（推荐）
        async with EfinanceWithCredential(use_tls=True) as ef:
            df = ef.get_realtime_quotes()
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, use_tls: bool = True):
        self._injector = CredentialInjector(config)
        self._domain = 'eastmoney.com'
        self._use_tls = use_tls
    
    async def __aenter__(self):
        await self._injector.initialize()
        await self._injector.fetch_credentials(self._domain)
        
        if self._use_tls:
            self._injector.patch_requests_with_tls(self._domain)
        else:
            self._injector.patch_requests(self._domain)
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._injector.unpatch_requests()
        await self._injector.close()
    
    async def initialize(self) -> bool:
        success = await self._injector.initialize()
        if success:
            await self._injector.fetch_credentials(self._domain)
            
            if self._use_tls:
                self._injector.patch_requests_with_tls(self._domain)
            else:
                self._injector.patch_requests(self._domain)
        
        return success
    
    async def close(self) -> None:
        self._injector.unpatch_requests()
        await self._injector.close()
    
    async def refresh_credentials(self) -> bool:
        return await self._injector.refresh_credentials_if_needed(self._domain)
    
    def get_status(self) -> Dict[str, Any]:
        status = self._injector.get_status()
        status.update(self._injector.get_tls_status())
        return status
    
    def get_realtime_quotes(self):
        import efinance as ef
        return ef.stock.get_realtime_quotes()
    
    def get_quote_history(
        self,
        stock_codes: str,
        beg: str = "19000101",
        end: str = "20500101",
        klt: int = 101,
        fqt: int = 1
    ):
        import efinance as ef
        return ef.stock.get_quote_history(
            stock_codes=stock_codes,
            beg=beg,
            end=end,
            klt=klt,
            fqt=fqt
        )
    
    def get_base_info(self, stock_code: str):
        import efinance as ef
        return ef.stock.get_base_info(stock_code)
    
    def get_deal_detail(self, stock_code: str):
        import efinance as ef
        return ef.stock.get_deal_detail(stock_code)
    
    def get_all_base_info(self):
        import efinance as ef
        return ef.stock.get_all_base_info()
    
    def get_industry_board(self):
        import akshare as ak
        return ak.stock_board_industry_name_em()
    
    def get_concept_board(self):
        import akshare as ak
        return ak.stock_board_concept_name_em()
    
    def get_fund_flow(self, stock: str, market: str = "sz"):
        import akshare as ak
        return ak.stock_individual_fund_flow(stock=stock, market=market)
    
    def get_fund_flow_history(self, stock: str, market: str = "sz"):
        import akshare as ak
        return ak.stock_individual_fund_flow(stock=stock, market=market)
    
    def get_main_fund_flow(self):
        import akshare as ak
        return ak.stock_main_fund_flow()
    
    def get_shareholders(self, stock_code: str):
        import efinance as ef
        return ef.stock.get_top10_stock_holder_info(stock_code)
    
    def __getattr__(self, name):
        import efinance as ef
        return getattr(ef, name)


class UnifiedCredentialManager:
    """统一凭证管理器
    
    同时支持 AKShare 和 Efinance 的凭证注入
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._config = {
            'headless': True,
            'domains': ['eastmoney.com'],
            'auto_refresh': True,
            'refresh_interval_minutes': 30,
            **(config or {})
        }
        
        self._injector = CredentialInjector(self._config)
        self._is_initialized = False
        self._last_refresh: Optional[datetime] = None
    
    async def initialize(self) -> bool:
        success = await self._injector.initialize()
        if success:
            for domain in self._config['domains']:
                await self._injector.fetch_credentials(domain)
            self._injector.patch_requests(self._config['domains'][0])
            self._is_initialized = True
            self._last_refresh = datetime.now()
        return success
    
    async def close(self) -> None:
        self._injector.unpatch_requests()
        await self._injector.close()
        self._is_initialized = False
    
    async def refresh_if_needed(self) -> bool:
        if not self._config['auto_refresh']:
            return True
        
        if not self._last_refresh:
            return await self.initialize()
        
        elapsed = datetime.now() - self._last_refresh
        if elapsed.total_seconds() >= self._config['refresh_interval_minutes'] * 60:
            logger.info("自动刷新凭证...")
            for domain in self._config['domains']:
                success = await self._injector.refresh_credentials_if_needed(domain)
                if not success:
                    return False
            self._last_refresh = datetime.now()
        
        return True
    
    def get_akshare(self) -> 'AkShareWithCredential':
        return AkShareWithCredential._from_injector(self._injector)
    
    def get_efinance(self) -> 'EfinanceWithCredential':
        return EfinanceWithCredential._from_injector(self._injector)
    
    def get_status(self) -> Dict[str, Any]:
        return {
            **self._injector.get_status(),
            'last_refresh': self._last_refresh.isoformat() if self._last_refresh else None,
            'auto_refresh': self._config['auto_refresh'],
        }
    
    @property
    def is_initialized(self) -> bool:
        return self._is_initialized

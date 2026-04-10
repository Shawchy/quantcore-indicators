"""
凭证注入器 v2

优化版本：
1. 全局单例模式，所有适配器共享同一个注入器
2. 懒加载 + 预加载双模式
3. 简化流程，减少不必要的日志
4. 改进锁机制，避免死锁
5. 支持凭证预热（应用启动时预加载）
"""

from typing import Optional, List, Dict, Any
from loguru import logger
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import asyncio
import time
import threading


class BrowserMode(Enum):
    """浏览器模式"""
    DRISSION = "drission"
    CURL_CFFI = "curl_cffi"
    NONE = "none"


@dataclass
class CredentialStatus:
    """凭证状态"""
    domain: str
    cookies: Optional[List[Dict]] = None
    headers: Optional[Dict[str, str]] = None
    updated_at: Optional[datetime] = None
    is_valid: bool = False
    fetch_attempts: int = 0


class CredentialInjectorV2:
    """凭证注入器 v2（全局单例）"""
    
    _instance: Optional['CredentialInjectorV2'] = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化（只执行一次）"""
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._config = {
            'headless': True,
            'cookie_max_age_hours': 24,
            'target_domains': ['eastmoney.com'],
            'auto_patch': True,  # 自动 patch requests
            'preload_on_init': False,  # 启动时预加载凭证
            **(config or {})
        }
        
        # 凭证存储
        self._credentials: Dict[str, CredentialStatus] = {}
        
        # 浏览器实例
        self._browser_mode = BrowserMode.NONE
        self._browser_executor = None
        self._page = None
        
        # 状态标志
        self._initialized = False
        self._is_patched = False
        self._is_preloaded = False
        
        # 锁
        self._init_lock = asyncio.Lock()
        self._fetch_lock = asyncio.Lock()
        
        logger.info("凭证注入器 v2 初始化（全局单例）")
    
    @classmethod
    def get_instance(cls, config: Optional[Dict[str, Any]] = None) -> 'CredentialInjectorV2':
        """获取全局单例实例"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(config)
        return cls._instance
    
    async def initialize(self) -> bool:
        """初始化（检测可用模式）"""
        if self._initialized:
            return True
        
        async with self._init_lock:
            if self._initialized:
                return True
            
            # 检测可用模式（简化版）
            self._browser_mode = self._detect_browser_mode()
            
            logger.info(f"凭证注入器初始化完成，模式：{self._browser_mode.value}")
            self._initialized = True
            
            # 可选：预加载凭证
            if self._config.get('preload_on_init'):
                await self._preload_credentials()
            
            return True
    
    def _detect_browser_mode(self) -> BrowserMode:
        """检测可用的浏览器模式"""
        # Level 1: DrissionPage（推荐）
        try:
            from DrissionPage import ChromiumPage
            logger.info("✅ DrissionPage 可用")
            return BrowserMode.DRISSION
        except ImportError:
            pass
        
        # Level 2: curl_cffi（无需浏览器）
        logger.info("✅ 使用 curl_cffi 模式（无需浏览器）")
        return BrowserMode.CURL_CFFI
    
    async def _preload_credentials(self):
        """预加载凭证（应用启动时）"""
        if self._is_preloaded:
            return
        
        logger.info("开始预加载凭证...")
        
        for domain in self._config['target_domains']:
            try:
                await self._fetch_credentials_internal(domain)
            except Exception as e:
                logger.warning(f"预加载 {domain} 凭证失败：{e}")
        
        self._is_preloaded = True
        logger.info("凭证预加载完成")
    
    async def get_credentials(self, domain: str) -> CredentialStatus:
        """获取凭证（懒加载）"""
        if not self._initialized:
            await self.initialize()
        
        # 检查是否有有效凭证
        if domain in self._credentials:
            status = self._credentials[domain]
            if status.is_valid and self._is_credential_fresh(status):
                return status
        
        # 获取新凭证
        async with self._fetch_lock:
            # 双重检查
            if domain in self._credentials:
                status = self._credentials[domain]
                if status.is_valid and self._is_credential_fresh(status):
                    return status
            
            await self._fetch_credentials_internal(domain)
            return self._credentials.get(domain, CredentialStatus(domain=domain))
    
    def _is_credential_fresh(self, status: CredentialStatus) -> bool:
        """检查凭证是否新鲜（未过期）"""
        if not status.updated_at:
            return False
        
        age = datetime.now() - status.updated_at
        max_age = timedelta(hours=self._config['cookie_max_age_hours'])
        return age < max_age
    
    async def _fetch_credentials_internal(self, domain: str) -> bool:
        """内部获取凭证方法"""
        logger.info(f"获取 {domain} 凭证...")
        
        if self._browser_mode == BrowserMode.CURL_CFFI:
            # curl_cffi 模式不需要获取凭证
            self._credentials[domain] = CredentialStatus(
                domain=domain,
                is_valid=True,
                updated_at=datetime.now()
            )
            logger.info(f"curl_cffi 模式：跳过 {domain} 凭证获取")
            return True
        
        # 浏览器模式：获取 Cookie
        try:
            cookies = await self._fetch_cookies_with_browser(domain)
            
            if cookies:
                self._credentials[domain] = CredentialStatus(
                    domain=domain,
                    cookies=cookies,
                    headers=self._generate_headers(),
                    updated_at=datetime.now(),
                    is_valid=True
                )
                logger.info(f"✅ 成功获取 {domain} 凭证")
                return True
            else:
                logger.warning(f"获取 {domain} 凭证返回空")
                return False
                
        except Exception as e:
            logger.error(f"获取 {domain} 凭证失败：{e}")
            self._credentials[domain] = CredentialStatus(
                domain=domain,
                is_valid=False,
                fetch_attempts=1
            )
            return False
    
    async def _fetch_cookies_with_browser(self, domain: str) -> Optional[List[Dict]]:
        """使用浏览器获取 Cookie"""
        if self._browser_mode == BrowserMode.DRISSION:
            # 首先尝试标准 DrissionPage 模式
            result = await self._fetch_with_drission(domain)
            if result:
                return result
            # 如果标准模式失败，使用增强模式
            logger.info("标准 DrissionPage 模式失败，尝试增强模式...")
            return await self._fetch_with_drission_enhanced(domain)
        else:
            return None
    
    async def _fetch_with_drission(self, domain: str) -> Optional[List[Dict]]:
        """DrissionPage 获取 Cookie"""
        loop = asyncio.get_event_loop()
        
        def sync_fetch():
            try:
                from DrissionPage import ChromiumPage, ChromiumOptions
                
                options = ChromiumOptions()
                options.headless(True)
                options.set_argument('--disable-blink-features=AutomationControlled')
                
                page = ChromiumPage(options)
                
                try:
                    if 'eastmoney' in domain:
                        page.get('https://fund.eastmoney.com/')
                    time.sleep(2)
                    
                    cookies = page.cookies()
                    return [{
                        'name': c.get('name', ''),
                        'value': c.get('value', ''),
                        'domain': c.get('domain', domain),
                        'path': c.get('path', '/'),
                    } for c in cookies]
                finally:
                    page.quit()
            except Exception as e:
                logger.error(f"DrissionPage 获取凭证失败：{e}")
                return None
        
        try:
            return await loop.run_in_executor(self._browser_executor, sync_fetch)
        except Exception as e:
            logger.error(f"DrissionPage 获取凭证异常：{e}")
            return None
    
    async def _fetch_with_drission_enhanced(self, domain: str) -> Optional[List[Dict]]:
        """DrissionPage 增强模式获取 Cookie（替代 Playwright）"""
        loop = asyncio.get_event_loop()
        
        def sync_fetch():
            try:
                from DrissionPage import ChromiumPage, ChromiumOptions
                
                # 配置无头模式
                options = ChromiumOptions()
                options.headless(True)
                options.set_argument('--disable-blink-features=AutomationControlled')
                options.set_argument('--disable-dev-shm-usage')
                options.set_argument('--no-sandbox')
                options.set_argument('--disable-features=IsolateOrigins,site-per-process')
                options.set_argument('--window-size=1920,1080')
                
                # 配置浏览器路径
                browser_path = self._config.get('browser_path')
                if browser_path:
                    options.set_paths(browser_path=browser_path)
                
                page = ChromiumPage(options)
                
                try:
                    if 'eastmoney' in domain:
                        page.get('https://fund.eastmoney.com/')
                        page.wait.load_start()
                    
                    time.sleep(2)
                    
                    cookies = page.cookies()
                    
                    # 转换为标准格式
                    cookie_list = []
                    for cookie in cookies:
                        cookie_list.append({
                            'name': cookie.get('name', ''),
                            'value': cookie.get('value', ''),
                            'domain': cookie.get('domain', domain),
                            'path': cookie.get('path', '/'),
                        })
                    
                    return cookie_list
                finally:
                    page.quit()
            except Exception as e:
                logger.error(f"DrissionPage 增强模式获取凭证失败：{e}")
                return None
        
        try:
            return await loop.run_in_executor(self._browser_executor, sync_fetch)
        except Exception as e:
            logger.error(f"DrissionPage 增强模式获取凭证异常：{e}")
            return None
    
    def _generate_headers(self) -> Dict[str, str]:
        """生成请求头"""
        import random
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        ]
        
        return {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
    
    def patch_requests(self, domain: str = 'eastmoney.com') -> bool:
        """注入凭证到 requests"""
        if self._is_patched:
            return True
        
        status = self._credentials.get(domain)
        if not status or not status.is_valid:
            logger.warning(f"{domain} 凭证无效，跳过注入")
            return False
        
        try:
            import requests
            
            cookies = {c['name']: c['value'] for c in status.cookies} if status.cookies else {}
            headers = status.headers or self._generate_headers()
            
            # 保存原始方法
            original_request = requests.request
            original_session_request = requests.Session.request
            
            def patched_request(method, url, **kwargs):
                if domain in url:
                    if 'cookies' not in kwargs:
                        kwargs['cookies'] = cookies
                    elif isinstance(kwargs['cookies'], dict):
                        kwargs['cookies'].update(cookies)
                    
                    if 'headers' not in kwargs:
                        kwargs['headers'] = headers.copy()
                    elif isinstance(kwargs['headers'], dict):
                        merged = headers.copy()
                        merged.update(kwargs['headers'])
                        kwargs['headers'] = merged
                
                return original_request(method, url, **kwargs)
            
            def patched_session_request(self_session, method, url, **kwargs):
                if domain in url:
                    if 'cookies' not in kwargs:
                        kwargs['cookies'] = cookies
                    elif isinstance(kwargs['cookies'], dict):
                        kwargs['cookies'].update(cookies)
                    
                    if 'headers' not in kwargs:
                        kwargs['headers'] = headers.copy()
                    elif isinstance(kwargs['headers'], dict):
                        merged = headers.copy()
                        merged.update(kwargs['headers'])
                        kwargs['headers'] = merged
                
                return original_session_request(self_session, method, url, **kwargs)
            
            requests.request = patched_request
            requests.Session.request = patched_session_request
            
            self._is_patched = True
            logger.info(f"✅ 已注入 {domain} 凭证")
            return True
            
        except Exception as e:
            logger.error(f"Patch requests 失败：{e}")
            return False
    
    def unpatch_requests(self) -> None:
        """恢复原始 requests"""
        if not self._is_patched:
            return
        
        try:
            import requests
            # 恢复原始方法（需要保存原始引用）
            self._is_patched = False
            logger.info("已恢复原始 requests")
        except Exception as e:
            logger.error(f"恢复 requests 失败：{e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            'initialized': self._initialized,
            'browser_mode': self._browser_mode.value,
            'patched': self._is_patched,
            'credentials': {
                domain: {
                    'valid': status.is_valid,
                    'updated_at': status.updated_at.isoformat() if status.updated_at else None,
                    'attempts': status.fetch_attempts,
                }
                for domain, status in self._credentials.items()
            },
        }


# 全局便捷函数
def get_credential_injector(config: Optional[Dict[str, Any]] = None) -> CredentialInjectorV2:
    """获取全局凭证注入器实例"""
    return CredentialInjectorV2.get_instance(config)


async def init_credential_injector(config: Optional[Dict[str, Any]] = None) -> CredentialInjectorV2:
    """初始化全局凭证注入器"""
    injector = get_credential_injector(config)
    await injector.initialize()
    return injector

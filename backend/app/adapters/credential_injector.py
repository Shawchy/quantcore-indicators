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

注意：
- Windows 上使用同步 API + 线程池运行 Playwright
- 避免 asyncio 事件循环与 subprocess 的兼容性问题
"""

from typing import Optional, List, Dict, Any, Union
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
from concurrent.futures import ThreadPoolExecutor
import threading


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
        # 自动检测 Edge 浏览器路径
        default_browser_path = self._detect_edge_path()
        
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
            'browser_path': default_browser_path,  # 自动检测 Edge 路径
            **(config or {})
        }
        
        # 线程池用于运行同步 Playwright
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='playwright')
        self._lock = threading.Lock()
        
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
        self._init_lock = asyncio.Lock()
        self._fetch_lock = asyncio.Lock()
        
        # Windows 禁用 Playwright（asyncio 事件循环不支持 subprocess）
        # 改为使用同步 API + 线程池
        self._playwright_disabled = False  # 启用 Playwright
        self._drission_available = False   # DrissionPage 可用性
        self._playwright_sync_available = False  # Playwright 同步可用性
        
        # 线程池用于运行同步浏览器操作
        self._browser_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix='browser')
        
        logger.info("凭证注入器初始化：支持 DrissionPage + Playwright 同步 + curl_cffi 三级降级")
        
        # 日志频率限制
        self._last_warning_time: Dict[str, float] = {}
        self._warning_cooldown = 10.0  # 同 URL 10 秒内只打印一次
    
    def _detect_edge_path(self) -> Optional[str]:
        """自动检测 Microsoft Edge 浏览器路径"""
        import os
        
        # 常见的 Edge 安装路径
        edge_paths = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%PROGRAMFILES%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%PROGRAMFILES(X86)%\Microsoft\Edge\Application\msedge.exe"),
        ]
        
        for path in edge_paths:
            if os.path.exists(path):
                logger.debug(f"检测到 Edge 浏览器：{path}")
                return path
        
        logger.warning("未检测到 Microsoft Edge 浏览器，将使用系统默认 Chrome")
        return None
    
    async def initialize(self) -> bool:
        """初始化凭证注入器（四级降级检测，2026 优化版）
        
        优先级：
        0. 手动 Cookie（最高优先级，零开销）
        1. DrissionPage（最优，自动绕过反爬）
        2. undetected-chromedriver（强反爬场景）
        3. Playwright 同步 + 线程池（稳定可靠）
        4. curl_cffi（无需浏览器，TLS 指纹伪装）
        """
        if self._is_initialized:
            return True
        
        async with self._init_lock:
            if self._is_initialized:
                return True
            
            # Level 0: 检测手动 Cookie（新增，2026 优化）
            manual_cookie_loaded = False
            for domain in self._config['target_domains']:
                if await self._load_manual_cookies(domain):
                    manual_cookie_loaded = True
                    logger.info(f"✅ Level 0: 加载手动 Cookie 成功：{domain}")
            
            if manual_cookie_loaded:
                self._browser_mode = "manual_cookie"
                logger.info("🚀 使用手动 Cookie 模式（零开销，推荐）")
                self._is_initialized = True
                return True
            
            # Level 1: 检测 DrissionPage
            try:
                from DrissionPage import ChromiumPage
                self._drission_available = True
                logger.info("✅ Level 1: DrissionPage 可用（最优模式）")
            except ImportError:
                logger.info("⚠️  Level 1: DrissionPage 不可用，尝试 Level 2")
                self._drission_available = False
            
            # Level 2: 检测 undetected-chromedriver（新增，2026 优化）
            uc_available = False
            if not self._drission_available:
                try:
                    import undetected_chromedriver as uc
                    uc_available = True
                    logger.info("✅ Level 2: undetected-chromedriver 可用（强反爬模式）")
                except ImportError:
                    logger.info("⚠️  Level 2: undetected-chromedriver 不可用，尝试 Level 3")
            
            # Level 3: curl_cffi（总是可用）
            logger.info("✅ Level 3: curl_cffi 可用（降级模式）")
            
            # 确定使用哪个模式
            if self._drission_available:
                self._browser_mode = "drission"
                logger.info("🚀 使用 DrissionPage 模式（推荐）")
            elif uc_available:
                self._browser_mode = "uc"
                logger.info("🚀 使用 undetected-chromedriver 模式（强反爬）")
            else:
                self._browser_mode = "curl_cffi"
                logger.info("🚀 使用 curl_cffi TLS 指纹伪装模式")
            
            self._is_initialized = True
            return True
    
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
        """获取凭证（四级降级，2026 优化版）
        
        1. DrissionPage（最优）
        2. undetected-chromedriver（强反爬）
        3. Playwright 同步 + 线程池
        4. curl_cffi（无需浏览器）
        """
        if not self._is_initialized:
            await self.initialize()
        
        async with self._fetch_lock:
            # 检查是否有有效凭证
            if self._cookies.get(domain) and self._cookies_updated_at.get(domain):
                age = datetime.now() - self._cookies_updated_at[domain]
                if age < timedelta(hours=self._config['cookie_max_age_hours']):
                    logger.debug(f"{domain} 凭证有效，跳过获取")
                    return True
            
            # 根据模式选择获取方式
            if self._browser_mode == "drission":
                return await self._fetch_with_drission(domain)
            elif self._browser_mode == "uc":
                return await self._fetch_with_undetected_chromedriver(domain)
            elif self._browser_mode == "playwright_sync":
                # 使用 DrissionPage 增强模式替代 Playwright（避免 Windows 异步问题）
                return await self._fetch_with_drission_enhanced(domain)
            else:
                # curl_cffi 模式，不需要获取凭证
                logger.info(f"curl_cffi 模式：跳过凭证获取，使用 TLS 指纹伪装")
                return True
    
    async def _load_manual_cookies(self, domain: str) -> bool:
        """加载手动获取的 Cookie（优先级最高，零开销）"""
        try:
            # 检查手动配置文件
            safe_domain = domain.replace('.', '_').replace(':', '_')
            manual_cookie_file = os.path.join(
                self._config['cookie_storage_dir'],
                f"{safe_domain}_manual.json"
            )
            
            if os.path.exists(manual_cookie_file):
                with open(manual_cookie_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 检查是否过期
                captured_at = datetime.fromisoformat(data['captured_at'])
                expires_in_days = data.get('expires_in_days', 7)
                
                if (datetime.now() - captured_at).days < expires_in_days:
                    self._cookies[domain] = data['cookies']
                    self._cookies_updated_at[domain] = captured_at
                    logger.info(f"✅ 加载手动 Cookie 成功：{domain} (过期时间：{expires_in_days}天)")
                    return True
                else:
                    logger.warning(f"⚠️  手动 Cookie 已过期：{domain}，请重新获取")
                    # 删除过期文件
                    try:
                        os.remove(manual_cookie_file)
                        logger.info(f"已删除过期的手动 Cookie 文件：{manual_cookie_file}")
                    except OSError:
                        pass
                    
        except FileNotFoundError:
            # 文件不存在是正常情况
            pass
        except Exception as e:
            logger.error(f"加载手动 Cookie 失败：{e}")
        
        return False
    
    async def save_manual_cookies(self, domain: str, cookies: List[Dict], expires_in_days: int = 7) -> bool:
        """保存手动获取的 Cookie 到配置文件
        
        Args:
            domain: 域名
            cookies: Cookie 列表
            expires_in_days: 有效期（天）
        """
        try:
            safe_domain = domain.replace('.', '_').replace(':', '_')
            manual_cookie_file = os.path.join(
                self._config['cookie_storage_dir'],
                f"{safe_domain}_manual.json"
            )
            
            data = {
                'domain': domain,
                'cookies': cookies,
                'captured_at': datetime.now().isoformat(),
                'expires_in_days': expires_in_days,
            }
            
            with open(manual_cookie_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 同时加载到内存
            self._cookies[domain] = cookies
            self._cookies_updated_at[domain] = datetime.now()
            
            logger.info(f"✅ 手动 Cookie 已保存：{domain} (有效期：{expires_in_days}天)")
            logger.info(f"   文件路径：{manual_cookie_file}")
            return True
            
        except Exception as e:
            logger.error(f"保存手动 Cookie 失败：{e}")
            return False
    
    async def _fetch_with_drission(self, domain: str) -> bool:
        """使用 DrissionPage 获取凭证（最优模式）"""
        logger.info(f"使用 DrissionPage 获取 {domain} 凭证...")
        
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
                
                # 配置浏览器路径
                browser_path = self._config.get('browser_path')
                if browser_path:
                    logger.debug(f"使用浏览器路径：{browser_path}")
                    options.set_paths(browser_path=browser_path)
                
                # 启动浏览器
                page = ChromiumPage(options)
                
                try:
                    # 访问东方财富网
                    if 'eastmoney' in domain:
                        page.get('https://www.eastmoney.com/')
                    
                    # 等待页面加载
                    import time
                    time.sleep(2)
                    
                    # 获取 Cookie
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
                logger.error(f"DrissionPage 获取凭证失败：{e}")
                return None
        
        try:
            # 在线程池中运行
            cookie_list = await loop.run_in_executor(
                self._browser_executor,
                sync_fetch
            )
            
            if cookie_list:
                self._cookies[domain] = cookie_list
                self._cookies_updated_at[domain] = datetime.now()
                logger.info(f"✅ DrissionPage 成功获取 {domain} 凭证")
                return True
            else:
                logger.warning("DrissionPage 获取凭证返回空列表")
                return False
                
        except Exception as e:
            logger.error(f"DrissionPage 获取凭证异常：{e}")
            return False
    
    async def _fetch_with_undetected_chromedriver(self, domain: str) -> bool:
        """使用 undetected-chromedriver 获取凭证（强反爬模式）"""
        logger.info(f"使用 undetected-chromedriver 获取 {domain} 凭证...")
        
        loop = asyncio.get_event_loop()
        
        def sync_fetch():
            try:
                import undetected_chromedriver as uc
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                
                # 配置浏览器选项
                options = uc.ChromeOptions()
                
                if self._config['headless']:
                    options.add_argument('--headless=new')
                
                # 关键反爬配置
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-gpu')
                
                # 随机化指纹
                options.add_argument(f'--user-agent={self._get_random_user_agent()}')
                options.add_argument('--window-size=1920,1080')
                
                # 禁用自动化特征
                options.add_experimental_option('excludeSwitches', ['enable-automation'])
                options.add_experimental_option('useAutomationExtension', False)
                
                # 启动浏览器
                driver = uc.Chrome(
                    options=options,
                    use_subprocess=False,  # 禁用子进程，提高稳定性
                    auto_load_extensions=False
                )
                
                try:
                    # 访问东方财富网
                    if 'eastmoney' in domain:
                        driver.get('https://www.eastmoney.com/')
                        
                        # 等待页面加载
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.TAG_NAME, "body"))
                        )
                    
                    # 获取 Cookie
                    cookies = driver.get_cookies()
                    
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
                    driver.quit()
                    
            except Exception as e:
                logger.error(f"undetected-chromedriver 获取凭证失败：{e}")
                return None
        
        try:
            # 在线程池中运行
            cookie_list = await loop.run_in_executor(
                self._browser_executor,
                sync_fetch
            )
            
            if cookie_list:
                self._cookies[domain] = cookie_list
                self._cookies_updated_at[domain] = datetime.now()
                logger.info(f"✅ undetected-chromedriver 成功获取 {domain} 凭证")
                return True
            else:
                logger.warning("undetected-chromedriver 获取凭证返回空列表")
                return False
                
        except Exception as e:
            logger.error(f"undetected-chromedriver 获取凭证异常：{e}")
            return False
    
    async def _fetch_with_drission_enhanced(self, domain: str) -> bool:
        """使用 DrissionPage 获取凭证（增强模式，替代 Playwright）"""
        logger.info(f"使用 DrissionPage 增强模式获取 {domain} 凭证...")
        
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
                
                # 配置浏览器路径
                browser_path = self._config.get('browser_path')
                if browser_path:
                    logger.debug(f"使用浏览器路径：{browser_path}")
                    options.set_paths(browser_path=browser_path)
                
                # 配置视口和区域
                options.set_argument('--window-size=1920,1080')
                
                # 启动浏览器
                page = ChromiumPage(options)
                
                try:
                    # 访问东方财富网
                    if 'eastmoney' in domain:
                        page.get('https://www.eastmoney.com/')
                        page.wait.load_start()
                    
                    # 等待页面加载
                    import time
                    time.sleep(2)
                    
                    # 获取 Cookie
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
            # 在线程池中运行
            cookie_list = await loop.run_in_executor(
                self._browser_executor,
                sync_fetch
            )
            
            if cookie_list:
                self._cookies[domain] = cookie_list
                self._cookies_updated_at[domain] = datetime.now()
                logger.info(f"✅ DrissionPage 增强模式成功获取 {domain} 凭证")
                return True
            else:
                logger.warning("DrissionPage 增强模式获取凭证返回空列表")
                return False
                
        except Exception as e:
            logger.error(f"DrissionPage 增强模式获取凭证异常：{e}")
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
        """获取随机 User-Agent（2026 增强版，基于真实设备信息）"""
        import random
        user_agents = [
            # Windows + Chrome（主力，50% 概率）
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            
            # macOS + Chrome（20% 概率）
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            
            # Windows + Edge（15% 概率）
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
            
            # Windows + Firefox（10% 概率）
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
            
            # macOS + Safari（5% 概率）
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
        ]
        return random.choice(user_agents)
    
    def _get_realistic_headers(self, rotate: bool = True) -> Dict[str, str]:
        """生成真实的请求头（基于真实设备信息，2026 增强版）
        
        Args:
            rotate: 是否轮换设备信息（默认 True）
        """
        import random
        
        # 真实设备信息池
        devices = [
            {
                # Windows + Chrome
                'ua': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                'platform': "Win32",
                'languages': "zh-CN,zh;q=0.9,en;q=0.8",
                'sec_ch_ua_platform': '"Windows"',
                'sec_ch_ua_mobile': '?0',
                'sec_ch_ua': '"Not A(Brand";v="8", "Chromium";v="122", "Google Chrome";v="122"',
            },
            {
                # macOS + Chrome
                'ua': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                'platform': "MacIntel",
                'languages': "zh-CN,zh;q=0.9,en;q=0.8",
                'sec_ch_ua_platform': '"macOS"',
                'sec_ch_ua_mobile': '?0',
                'sec_ch_ua': '"Not A(Brand";v="8", "Chromium";v="122", "Google Chrome";v="122"',
            },
            {
                # Windows + Edge
                'ua': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
                'platform': "Win32",
                'languages': "zh-CN,zh;q=0.9,en;q=0.8",
                'sec_ch_ua_platform': '"Windows"',
                'sec_ch_ua_mobile': '?0',
                'sec_ch_ua': '"Not A(Brand";v="8", "Chromium";v="122", "Microsoft Edge";v="122"',
            },
            {
                # Windows + Firefox
                'ua': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
                'platform': "Win32",
                'languages': "zh-CN,zh;q=0.9,en;q=0.8",
                # Firefox 不使用 Sec-CH-UA
            },
            {
                # macOS + Safari
                'ua': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
                'platform': "MacIntel",
                'languages': "zh-CN,zh;q=0.9,en;q=0.8",
                # Safari 不使用 Sec-CH-UA
            },
        ]
        
        device = random.choice(devices)
        
        # 基础请求头
        headers = {
            'User-Agent': device['ua'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': device['languages'],
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        }
        
        # Chrome/Edge 特有请求头
        if 'Chrome' in device['ua'] or 'Edg' in device['ua']:
            headers.update({
                'Sec-Ch-Ua-Platform': device.get('sec_ch_ua_platform', ''),
                'Sec-Ch-Ua-Mobile': device.get('sec_ch_ua_mobile', '?0'),
                'Sec-Ch-Ua': device.get('sec_ch_ua', ''),
            })
        
        return headers
    
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
            logger.info(f"✅ 已注入 {domain} 的凭证到 requests (模式：{self._browser_mode})")
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
    
    async def _refresh_credentials_on_failure(self):
        """请求失败时自动刷新凭证（后台任务）"""
        try:
            logger.info("后台刷新凭证...")
            for domain in self._config['target_domains'][:1]:  # 只刷新第一个域名
                await self.fetch_credentials(domain)
                logger.info(f"后台刷新 {domain} 凭证完成")
                break
        except Exception as e:
            logger.error(f"后台刷新凭证失败：{e}")
    
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
                        # curl_cffi 失败，尝试降级
                        logger.warning(f"curl_cffi 请求失败：{e}")
                        
                        # 检查是否需要重新获取凭证
                        if '56' in str(e) or 'Connection closed' in str(e):
                            logger.info("检测到连接被关闭，尝试重新获取凭证...")
                            # 异步获取凭证（不阻塞）
                            asyncio.create_task(self._refresh_credentials_on_failure())
                        
                        # 降级到普通 requests
                        logger.info("降级到普通 requests")
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
                        # 日志频率限制：同 URL 10 秒内只打印一次
                        import time
                        current_time = time.time()
                        url_key = url.split('?')[0]  # 忽略查询参数
                        last_warning = self._last_warning_time.get(url_key, 0)
                        
                        if current_time - last_warning > self._warning_cooldown:
                            logger.warning(f"curl_cffi 请求失败：{e}，回退到 requests")
                            self._last_warning_time[url_key] = current_time
                        
                        # 添加延迟，避免重试过快
                        time.sleep(2.0)  # 延迟 2 秒
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
        """
        获取东方财富行业板块名称
        
        注意：返回值需要检查类型，akshare 可能返回错误码（整数）而不是 DataFrame
        """
        import akshare as ak
        return ak.stock_board_industry_name_em()
    
    def get_board_concept_name_em(self):
        """
        获取东方财富概念板块名称
        
        注意：返回值需要检查类型，akshare 可能返回错误码（整数）而不是 DataFrame
        """
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


_global_injector: Optional[CredentialInjector] = None
_injector_lock = asyncio.Lock()


class CookieMonitor:
    """Cookie 监听器，自动续期"""
    
    def __init__(self, injector: CredentialInjector):
        self._injector = injector
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
    
    async def start_monitoring(self, check_interval_minutes: int = 60):
        """启动监听
        
        Args:
            check_interval_minutes: 检查间隔（分钟），默认 60 分钟
        """
        if self._monitoring:
            logger.warning("Cookie 监听器已在运行")
            return
        
        self._monitoring = True
        self._monitor_task = asyncio.create_task(
            self._monitor_loop(check_interval_minutes)
        )
        logger.info(f"✅ Cookie 监听器已启动（检查间隔：{check_interval_minutes}分钟）")
    
    async def _monitor_loop(self, check_interval_minutes: int):
        """监听循环"""
        while self._monitoring:
            await asyncio.sleep(check_interval_minutes * 60)
            
            for domain in list(self._injector._cookies.keys()):
                updated_at = self._injector._cookies_updated_at.get(domain)
                
                if updated_at:
                    age = datetime.now() - updated_at
                    max_age_hours = self._injector._config['cookie_max_age_hours']
                    
                    # 提前 1 小时续期
                    if age.total_seconds() > (max_age_hours - 1) * 3600:
                        logger.info(f"⚠️  Cookie 即将过期，自动续期：{domain}")
                        
                        try:
                            # 后台刷新凭证
                            success = await self._injector.fetch_credentials(domain)
                            
                            if success:
                                logger.info(f"✅ Cookie 已续期：{domain}")
                            else:
                                logger.error(f"❌ Cookie 续期失败：{domain}")
                        except Exception as e:
                            logger.error(f"Cookie 续期异常：{domain}, 错误：{e}")
    
    def stop_monitoring(self):
        """停止监听"""
        self._monitoring = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
            logger.info("Cookie 监听器已停止")


async def get_global_injector(config: Optional[Dict[str, Any]] = None) -> CredentialInjector:
    """获取全局凭证注入器单例"""
    global _global_injector
    
    async with _injector_lock:
        if _global_injector is None:
            _global_injector = CredentialInjector(config)
        return _global_injector

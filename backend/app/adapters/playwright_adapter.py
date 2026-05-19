"""
Playwright 无头浏览器适配器

特性：
1. 反检测机制 - 模拟真实浏览器行为
2. 请求指纹随机化
3. 自动处理 JavaScript 渲染
4. 智能重试和错误恢复
5. 代理 IP 支持
"""

from typing import Optional, List, Dict, Any
from loguru import logger
from datetime import datetime
import asyncio
import random
import json
import re

from .base import (
    BaseDataAdapter,
    DataSourceType,
    StockBasicInfo,
    KLineData,
    SectorInfo,
    MarketQuote
)


class PlaywrightAdapter(BaseDataAdapter):
    """Playwright 无头浏览器适配器
    
    反风控策略：
    1. 浏览器指纹随机化
    2. 随机化请求间隔
    3. 模拟人类行为（鼠标移动、滚动）
    4. 处理 JavaScript 挑战
    5. Cookie 和 Session 管理
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._browser = None
        self._context = None
        self._page = None
        self._playwright = None
        self._playwright_manager = None
        
        self._is_initialized = False
        self._last_request_time = 0
        self._request_count = 0
        
        self._config = {
            'headless': True,
            'browser_type': 'chromium',
            'proxy': None,
            'user_agent': None,
            'viewport': {'width': 1920, 'height': 1080},
            'locale': 'zh-CN',
            'timezone': 'Asia/Shanghai',
            'request_timeout': 30000,
            'navigation_timeout': 60000,
            'slow_mo': 0,
            **(config or {})
        }
        
        self._request_delay_range = (2.0, 5.0)
        self._max_retries = 3
        self._consecutive_failures = 0
        
        self._user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
        ]
        
        self._eastmoney_urls = {
            'stock_list': 'https://quote.eastmoney.com/center/gridlist.html',
            'stock_quote': 'https://quote.eastmoney.com/{market}{code}.html',
            'kline': 'https://quote.eastmoney.com/kline.html',
            'sector_list': 'https://quote.eastmoney.com/center/boardlist.html',
            'fund_flow': 'https://data.eastmoney.com/zjlx/',
            'zt_pool': 'https://quote.eastmoney.com/ztb/',
        }
    
    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.EFINANCE
    
    async def initialize(self) -> bool:
        try:
            from playwright.async_api import async_playwright
            
            self._playwright = await async_playwright().start()
            
            if self._playwright is None:
                raise RuntimeError("Playwright start() returned None")
            
            browser_type = self._config['browser_type']
            launch_options = {
                'headless': self._config['headless'],
                'args': [
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-site-isolation-trials',
                    '--disable-web-security',
                    '--disable-features=BlockInsecurePrivateNetworkRequests',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-infobars',
                    '--disable-background-networking',
                    '--disable-breakpad',
                    '--disable-component-update',
                    '--disable-default-apps',
                    '--disable-extensions',
                    '--disable-sync',
                    '--metrics-recording-only',
                    '--no-first-run',
                    '--disable-automation',
                    '--disable-password-generation',
                    '--disable-single-click-autofill',
                    '--disable-translate-new-ux',
                    '--disable-autofill-keyboard-accessory-view',
                    '--enable-async-dns',
                    '--enable-smooth-scrolling',
                    '--enable-tcp-fast-open',
                    '--enable-features=NetworkService,NetworkServiceInProcess',
                    '--force-color-profile=srgb',
                ]
            }
            
            if self._config.get('proxy'):
                launch_options['proxy'] = {'server': self._config['proxy']}
            
            import os
            from app.config import settings
            browsers_path = os.environ.get('PLAYWRIGHT_BROWSERS_PATH', os.path.join(str(settings.BASE_DIR), 'playwright_browsers'))
            chromium_exe = os.path.join(browsers_path, 'chromium-1148', 'chrome-win', 'chrome.exe')
            
            if os.path.exists(chromium_exe):
                launch_options['executable_path'] = chromium_exe
                logger.info(f"使用 Chromium 可执行文件: {chromium_exe}")
            
            try:
                if browser_type == 'firefox':
                    self._browser = await self._playwright.firefox.launch(**launch_options)
                elif browser_type == 'webkit':
                    self._browser = await self._playwright.webkit.launch(**launch_options)
                else:
                    self._browser = await self._playwright.chromium.launch(**launch_options)
            except Exception as e:
                if 'headless_shell' in str(e) or 'Executable' in str(e):
                    logger.warning(f"Chromium headless shell 不可用，尝试使用 channel='chrome': {e}")
                    launch_options['channel'] = 'chrome'
                    if 'executable_path' in launch_options:
                        del launch_options['executable_path']
                    self._browser = await self._playwright.chromium.launch(**launch_options)
                else:
                    raise
            
            await self._create_context()
            
            self._is_initialized = True
            logger.info(f"Playwright 浏览器适配器初始化成功 ({browser_type})")
            return True
            
        except ImportError:
            logger.error("Playwright 未安装，请运行: pip install playwright && playwright install chromium")
            return False
        except Exception as e:
            logger.error(f"Playwright 初始化失败: {e}")
            return False
    
    async def _create_context(self):
        if self._context:
            await self._context.close()
        
        context_options = {
            'viewport': self._config['viewport'],
            'locale': self._config['locale'],
            'timezone_id': self._config['timezone'],
            'user_agent': self._config.get('user_agent') or random.choice(self._user_agents),
            'java_script_enabled': True,
            'bypass_csp': True,
            'ignore_https_errors': True,
        }
        
        self._context = await self._browser.new_context(**context_options)
        
        await self._context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                    { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                    { name: 'Native Client', filename: 'internal-nacl-plugin' }
                ]
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en-US', 'en']
            });
            
            Object.defineProperty(navigator, 'platform', {
                get: () => 'Win32'
            });
            
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 8
            });
            
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => 8
            });
            
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
            
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            const originalToString = Function.toString;
            Function.toString = function() {
                if (this === window.navigator.permissions.query) {
                    return 'function query() { [native code] }';
                }
                return originalToString.call(this);
            };
        """)
        
        self._page = await self._context.new_page()
        
        await self._page.set_default_timeout(self._config['request_timeout'])
        await self._page.set_default_navigation_timeout(self._config['navigation_timeout'])
        
        await self._setup_request_interception()
    
    async def _setup_request_interception(self):
        async def handle_route(route):
            headers = route.request.headers.copy()
            headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8'
            headers['Accept-Language'] = 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7'
            headers['Accept-Encoding'] = 'gzip, deflate, br'
            headers['Cache-Control'] = 'max-age=0'
            headers['Sec-Ch-Ua'] = '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"'
            headers['Sec-Ch-Ua-Mobile'] = '?0'
            headers['Sec-Ch-Ua-Platform'] = '"Windows"'
            headers['Sec-Fetch-Dest'] = 'document'
            headers['Sec-Fetch-Mode'] = 'navigate'
            headers['Sec-Fetch-Site'] = 'none'
            headers['Sec-Fetch-User'] = '?1'
            headers['Upgrade-Insecure-Requests'] = '1'
            
            await route.continue_(headers=headers)
        
        await self._page.route('**/*', handle_route)
    
    async def close(self) -> None:
        try:
            if self._page:
                await self._page.close()
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright_manager:
                await self._playwright_manager.__aexit__(None, None, None)
        except Exception as e:
            logger.error(f"关闭 Playwright 失败: {e}")
        finally:
            self._is_initialized = False
            self._playwright = None
            self._playwright_manager = None
            self._browser = None
            self._context = None
            self._page = None
            logger.info("Playwright 浏览器适配器已关闭")
    
    async def _rate_limit(self):
        delay = random.uniform(*self._request_delay_range)
        
        if self._consecutive_failures > 0:
            delay *= (1 + self._consecutive_failures * 0.5)
        
        await asyncio.sleep(delay)
    
    async def _simulate_human_behavior(self):
        try:
            viewport = self._page.viewport_size
            if viewport:
                x = random.randint(100, viewport['width'] - 100)
                y = random.randint(100, viewport['height'] - 100)
                await self._page.mouse.move(x, y)
                
                if random.random() < 0.3:
                    scroll_y = random.randint(100, 500)
                    await self._page.evaluate(f'window.scrollBy(0, {scroll_y})')
                    await asyncio.sleep(random.uniform(0.1, 0.3))
                    await self._page.evaluate(f'window.scrollBy(0, -{scroll_y})')
        except Exception:
            pass
    
    async def _navigate_with_retry(self, url: str, wait_until: str = 'networkidle') -> bool:
        for attempt in range(self._max_retries):
            try:
                await self._rate_limit()
                
                response = await self._page.goto(url, wait_until=wait_until, timeout=self._config['navigation_timeout'])
                
                if response and response.status == 200:
                    await self._simulate_human_behavior()
                    self._consecutive_failures = 0
                    self._request_count += 1
                    return True
                elif response and response.status == 403:
                    logger.warning(f"访问被拒绝 (403)，尝试重新创建上下文")
                    await self._create_context()
                    continue
                else:
                    logger.warning(f"请求返回非 200 状态: {response.status if response else 'No response'}")
                    
            except Exception as e:
                self._consecutive_failures += 1
                logger.warning(f"导航失败 (尝试 {attempt + 1}/{self._max_retries}): {e}")
                
                if attempt < self._max_retries - 1:
                    await asyncio.sleep((attempt + 1) * 2)
                    await self._create_context()
        
        return False
    
    async def get_stock_list(self, market: Optional[str] = None) -> List[StockBasicInfo]:
        try:
            url = self._eastmoney_urls['stock_list']
            
            if not await self._navigate_with_retry(url):
                return []
            
            await self._page.wait_for_selector('.dataview-body', timeout=10000)
            
            stocks = []
            rows = await self._page.query_selector_all('.dataview-body tbody tr')
            
            for row in rows[:100]:
                try:
                    cells = await row.query_selector_all('td')
                    if len(cells) >= 2:
                        code = await cells[1].inner_text()
                        name = await cells[2].inner_text()
                        
                        code = code.strip()
                        name = name.strip()
                        
                        if code and name and re.match(r'^\d{6}$', code):
                            market_tag = "SH" if code.startswith('6') else "SZ"
                            stocks.append(StockBasicInfo(
                                code=code,
                                name=name,
                                market=market_tag
                            ))
                except Exception:
                    continue
            
            logger.info(f"Playwright 获取股票列表成功: {len(stocks)} 条")
            return stocks
            
        except Exception as e:
            logger.error(f"Playwright 获取股票列表失败: {e}")
            return []
    
    async def get_stock_info(self, code: str) -> Optional[StockBasicInfo]:
        try:
            market = '1' if code.startswith('6') else '0'
            url = f"https://quote.eastmoney.com/{market}.{code}.html"
            
            if not await self._navigate_with_retry(url):
                return None
            
            await self._page.wait_for_selector('.quote-header', timeout=10000)
            
            name_elem = await self._page.query_selector('.quote-header .name')
            name = await name_elem.inner_text() if name_elem else ""
            
            return StockBasicInfo(
                code=code,
                name=name.strip(),
                market="SH" if code.startswith('6') else "SZ"
            )
            
        except Exception as e:
            logger.error(f"Playwright 获取股票信息失败 {code}: {e}")
            return None
    
    async def get_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq"
    ) -> List[KLineData]:
        try:
            market = '1' if code.startswith('6') else '0'
            url = f"https://quote.eastmoney.com/kline.html?code={market}.{code}"
            
            if not await self._navigate_with_retry(url):
                return []
            
            await self._page.wait_for_selector('.kline', timeout=10000)
            
            klines = []
            
            return klines
            
        except Exception as e:
            logger.error(f"Playwright 获取 K 线失败 {code}: {e}")
            return []
    
    async def get_market_realtime_quotes(self, market_types: Optional[List[str]] = None) -> List[MarketQuote]:
        try:
            url = "https://quote.eastmoney.com/center/gridlist.html#hs_a_board"
            
            if not await self._navigate_with_retry(url):
                return []
            
            await self._page.wait_for_selector('.dataview-body', timeout=15000)
            
            await asyncio.sleep(2)
            
            quotes = []
            rows = await self._page.query_selector_all('.dataview-body tbody tr')
            
            for row in rows:
                try:
                    cells = await row.query_selector_all('td')
                    if len(cells) >= 10:
                        code = await cells[1].inner_text()
                        name = await cells[2].inner_text()
                        
                        def parse_float(text):
                            try:
                                return float(text.strip().replace(',', '').replace('%', ''))
                            except:
                                return None
                        
                        quote = MarketQuote(
                            code=code.strip(),
                            name=name.strip(),
                            price=parse_float(await cells[3].inner_text()),
                            change_pct=parse_float(await cells[4].inner_text()),
                            change=parse_float(await cells[5].inner_text()),
                            volume=parse_float(await cells[6].inner_text()),
                            amount=parse_float(await cells[7].inner_text()),
                            high=parse_float(await cells[8].inner_text()),
                            low=parse_float(await cells[9].inner_text()),
                            market_type="A 股"
                        )
                        quotes.append(quote)
                        
                except Exception:
                    continue
            
            logger.info(f"Playwright 获取市场行情成功: {len(quotes)} 条")
            return quotes
            
        except Exception as e:
            logger.error(f"Playwright 获取市场行情失败: {e}")
            return []
    
    async def get_sector_list(self, sector_type: str = "industry") -> List[SectorInfo]:
        try:
            if sector_type == "industry":
                url = "https://quote.eastmoney.com/center/boardlist.html#industry_board"
            else:
                url = "https://quote.eastmoney.com/center/boardlist.html#concept_board"
            
            if not await self._navigate_with_retry(url):
                return []
            
            await self._page.wait_for_selector('.dataview-body', timeout=15000)
            
            await asyncio.sleep(2)
            
            sectors = []
            rows = await self._page.query_selector_all('.dataview-body tbody tr')
            
            for row in rows:
                try:
                    cells = await row.query_selector_all('td')
                    if len(cells) >= 4:
                        name = await cells[1].inner_text()
                        change_pct_text = await cells[2].inner_text()
                        
                        def parse_float(text):
                            try:
                                return float(text.strip().replace('%', ''))
                            except:
                                return None
                        
                        sector = SectorInfo(
                            code="",
                            name=name.strip(),
                            sector_type=sector_type,
                            change_pct=parse_float(change_pct_text)
                        )
                        sectors.append(sector)
                        
                except Exception:
                    continue
            
            logger.info(f"Playwright 获取板块列表成功: {len(sectors)} 条")
            return sectors
            
        except Exception as e:
            logger.error(f"Playwright 获取板块列表失败: {e}")
            return []
    
    async def get_sector_components(self, sector_code: str) -> List[str]:
        return []
    
    async def get_realtime_quote(self, code: str) -> Dict[str, Any]:
        try:
            market = '1' if code.startswith('6') else '0'
            url = f"https://quote.eastmoney.com/{market}.{code}.html"
            
            if not await self._navigate_with_retry(url):
                return {}
            
            await self._page.wait_for_selector('.quote-header', timeout=10000)
            
            quote = {'code': code}
            
            name_elem = await self._page.query_selector('.quote-header .name')
            if name_elem:
                quote['name'] = await name_elem.inner_text()
            
            price_elem = await self._page.query_selector('.quote-header .price')
            if price_elem:
                try:
                    quote['price'] = float(await price_elem.inner_text())
                except:
                    pass
            
            return quote
            
        except Exception as e:
            logger.error(f"Playwright 获取实时行情失败 {code}: {e}")
            return {}
    
    async def set_proxy(self, proxy: str):
        self._config['proxy'] = proxy
        if self._is_initialized:
            await self._create_context()
        logger.info(f"Playwright 代理已设置: {proxy}")
    
    async def clear_proxy(self):
        self._config['proxy'] = None
        if self._is_initialized:
            await self._create_context()
        logger.info("Playwright 代理已清除")
    
    async def take_screenshot(self, path: str) -> bool:
        try:
            await self._page.screenshot(path=path)
            return True
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return False
    
    async def get_cookies(self) -> List[Dict]:
        return await self._context.cookies()
    
    async def set_cookies(self, cookies: List[Dict]):
        await self._context.add_cookies(cookies)
    
    def get_status(self) -> Dict[str, Any]:
        return {
            'initialized': self._is_initialized,
            'browser_type': self._config['browser_type'],
            'headless': self._config['headless'],
            'request_count': self._request_count,
            'consecutive_failures': self._consecutive_failures,
            'proxy': self._config.get('proxy'),
        }

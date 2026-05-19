"""
增强版 Playwright 适配器

整合所有反风控组件：
1. 代理 IP 池管理
2. 智能请求调度
3. Cookie 持久化
4. 增强浏览器指纹
5. 验证码检测与处理
"""

from typing import Optional, List, Dict, Any
from loguru import logger
from datetime import datetime
import asyncio
import random
import os
import time
from app.config import settings

from .base import (
    BaseDataAdapter,
    DataSourceType,
    StockBasicInfo,
    KLineData,
    SectorInfo,
    MarketQuote
)
from .anti_wind import (
    AntiWindFacade,
    CookieInjectStrategy,
    CaptchaHandlerStrategy,
    ProxyPoolStrategy,
)


class EnhancedPlaywrightAdapter(BaseDataAdapter):
    """增强版 Playwright 无头浏览器适配器
    
    反风控策略：
    1. 代理 IP 池自动轮换
    2. 智能请求调度（自适应延迟）
    3. Cookie 持久化（保持会话）
    4. 增强浏览器指纹伪装
    5. 验证码检测与处理
    6. 请求失败自动恢复
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        self._browser = None
        self._context = None
        self._page = None
        self._playwright = None
        self._playwright_manager = None
        
        self._is_initialized = False
        self._request_count = 0
        
        self._config = {
            'headless': True,
            'browser_type': 'chromium',
            'proxy': None,
            'request_timeout': 30000,
            'navigation_timeout': 60000,
            'captcha_timeout': 60,
            'max_retries': 3,
            'enable_proxy': True,
            'enable_cookies': True,
            'enable_captcha_detection': True,
            **(config or {})
        }
        
        # 使用新的 AntiWindFacade 统一管理反爬策略
        self._anti_wind = AntiWindFacade({
            'enable_cookie_inject': self._config['enable_cookies'],
            'enable_captcha_handler': self._config['enable_captcha_detection'],
            'enable_proxy_pool': self._config['enable_proxy'],
            'enable_rate_limit': True,
            'enable_ua_rotation': False,  # 浏览器适配器不需要 UA 轮换
            'enable_smart_retry': True,
            'max_retries': self._config.get('max_retries', 3),
            'captcha_config': {
                'timeout': self._config.get('captcha_timeout', 60),
            },
        })
        
        self._eastmoney_urls = {
            'stock_list': 'https://quote.eastmoney.com/center/gridlist.html',
            'stock_quote': 'https://quote.eastmoney.com/{market}{code}.html',
            'kline': 'https://quote.eastmoney.com/kline.html',
            'sector_list': 'https://quote.eastmoney.com/center/boardlist.html',
            'fund_flow': 'https://data.eastmoney.com/zjlx/',
            'zt_pool': 'https://quote.eastmoney.com/ztb/',
        }
        
        self._current_domain: Optional[str] = None
    
    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.EFINANCE
    
    def add_proxy(self, host: str, port: int, **kwargs) -> None:
        self._anti_wind.add_proxy(host, port, **kwargs)
    
    def add_proxies_from_file(self, filepath: str) -> int:
        return self._anti_wind.add_proxies_from_file(filepath)
    
    async def initialize(self) -> bool:
        try:
            from playwright.async_api import async_playwright
            
            self._playwright_manager = async_playwright()
            self._playwright = await self._playwright_manager.start()
            
            if self._playwright is None:
                raise RuntimeError("Playwright start() returned None")
            
            await self._create_browser()
            await self._create_context()
            
            self._is_initialized = True
            logger.info("增强版 Playwright 适配器初始化成功（使用 AntiWindFacade 统一管理）")
            return True
            
        except ImportError:
            logger.error("Playwright 未安装，请运行: pip install playwright && playwright install chromium")
            return False
        except Exception as e:
            logger.error(f"Playwright 初始化失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def _create_browser(self) -> None:
        launch_options = {
            'headless': self._config['headless'],
            'args': [
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-site-isolation-trials',
                '--disable-web-security',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-infobars',
                '--disable-background-networking',
                '--disable-breakpad',
                '--disable-component-update',
                '--disable-default-apps',
                '--disable-extensions',
                '--disable-sync',
                '--no-first-run',
                '--disable-automation',
                '--enable-async-dns',
                '--enable-smooth-scrolling',
                '--force-color-profile=srgb',
            ]
        }
        
        browsers_path = os.environ.get(
            'PLAYWRIGHT_BROWSERS_PATH',
            os.path.join(str(settings.BASE_DIR), 'playwright_browsers')
        )
        chromium_exe = os.path.join(browsers_path, 'chromium-1148', 'chrome-win', 'chrome.exe')
        
        if os.path.exists(chromium_exe):
            launch_options['executable_path'] = chromium_exe
            logger.info(f"使用 Chromium: {chromium_exe}")
        
        self._browser = await self._playwright.chromium.launch(**launch_options)
    
    async def _create_context(self) -> None:
        if self._context:
            await self._context.close()
        
        context_options = {
            'viewport': {'width': 1920, 'height': 1080},
            'locale': 'zh-CN',
            'timezone_id': 'Asia/Shanghai',
            'user_agent': self._anti_wind.fingerprint.get_random_user_agent(),
            'java_script_enabled': True,
            'bypass_csp': True,
            'ignore_https_errors': True,
        }
        
        if self._config.get('proxy'):
            context_options['proxy'] = {'server': self._config['proxy']}
        
        self._context = await self._browser.new_context(**context_options)
        
        await self._context.add_init_script(
            self._anti_wind.fingerprint.get_stealth_script()
        )
        
        self._page = await self._context.new_page()
        
        self._page.set_default_timeout(self._config['request_timeout'])
        self._page.set_default_navigation_timeout(self._config['navigation_timeout'])
        
        await self._setup_request_interception()
    
    async def _setup_request_interception(self) -> None:
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
            logger.info("增强版 Playwright 适配器已关闭")
    
    async def _navigate_with_anti_wind(self, url: str) -> bool:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        
        context = await self._anti_wind.before_request(url, domain)
        
        if context['delay'] > 0:
            logger.debug(f"请求延迟: {context['delay']:.2f}s")
            await asyncio.sleep(context['delay'])
        
        start_time = time.time()
        
        for attempt in range(self._config['max_retries']):
            try:
                response = await self._page.goto(
                    url,
                    wait_until='networkidle',
                    timeout=self._config['navigation_timeout']
                )
                
                if response and response.status == 200:
                    captcha_result = await self._anti_wind.check_captcha(self._page)
                    
                    if captcha_result['detected']:
                        logger.warning(f"检测到验证码: {captcha_result['message']}")
                        
                        if self._config['enable_captcha_detection']:
                            solved = await CaptchaDetector.wait_for_manual_solve(
                                self._page,
                                self._config['captcha_timeout']
                            )
                            if not solved:
                                await self._anti_wind.after_request(
                                    success=False,
                                    domain=domain,
                                    error="验证码未解决"
                                )
                                return False
                    
                    await self._simulate_human_behavior()
                    
                    response_time = time.time() - start_time
                    cookies = await self._context.cookies()
                    
                    await self._anti_wind.after_request(
                        success=True,
                        domain=domain,
                        response_time=response_time,
                        cookies=cookies
                    )
                    
                    self._request_count += 1
                    return True
                    
                elif response and response.status == 403:
                    logger.warning(f"访问被拒绝 (403)，尝试重建上下文")
                    await self._create_context()
                    continue
                    
                elif response and response.status == 429:
                    logger.warning(f"请求过于频繁 (429)")
                    await self._anti_wind.after_request(
                        success=False,
                        domain=domain,
                        error="Rate limited (429)"
                    )
                    await asyncio.sleep(30)
                    await self._create_context()
                    continue
                    
                else:
                    status = response.status if response else 'No response'
                    logger.warning(f"请求返回非 200 状态: {status}")
                    
            except Exception as e:
                self._anti_wind.scheduler.report_failure(domain)
                logger.warning(f"导航失败 (尝试 {attempt + 1}/{self._config['max_retries']}): {e}")
                
                if attempt < self._config['max_retries'] - 1:
                    await asyncio.sleep((attempt + 1) * 3)
                    await self._create_context()
        
        await self._anti_wind.after_request(
            success=False,
            domain=domain,
            error="Max retries exceeded"
        )
        return False
    
    async def _simulate_human_behavior(self) -> None:
        try:
            viewport = self._page.viewport_size
            if viewport:
                for _ in range(random.randint(1, 3)):
                    x = random.randint(100, viewport['width'] - 100)
                    y = random.randint(100, viewport['height'] - 100)
                    await self._page.mouse.move(x, y, steps=random.randint(5, 10))
                    await asyncio.sleep(random.uniform(0.05, 0.2))
                
                if random.random() < 0.4:
                    scroll_y = random.randint(100, 500)
                    await self._page.evaluate(f'window.scrollBy(0, {scroll_y})')
                    await asyncio.sleep(random.uniform(0.1, 0.3))
                    await self._page.evaluate(f'window.scrollBy(0, -{scroll_y})')
                
                if random.random() < 0.2:
                    await self._page.mouse.wheel(0, random.randint(-100, 100))
                    
        except Exception:
            pass
    
    async def get_stock_list(self, market: Optional[str] = None) -> List[StockBasicInfo]:
        try:
            url = self._eastmoney_urls['stock_list']
            
            if not await self._navigate_with_anti_wind(url):
                return []
            
            await self._page.wait_for_selector('.dataview-body', timeout=10000)
            await asyncio.sleep(2)
            
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
                        
                        if code and name:
                            market_tag = "SH" if code.startswith('6') else "SZ"
                            stocks.append(StockBasicInfo(
                                code=code,
                                name=name,
                                market=market_tag
                            ))
                except Exception:
                    continue
            
            logger.info(f"获取股票列表成功: {len(stocks)} 条")
            return stocks
            
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return []
    
    async def get_market_realtime_quotes(
        self,
        market_types: Optional[List[str]] = None
    ) -> List[MarketQuote]:
        try:
            url = "https://quote.eastmoney.com/center/gridlist.html#hs_a_board"
            
            if not await self._navigate_with_anti_wind(url):
                return []
            
            await self._page.wait_for_selector('.dataview-body', timeout=15000)
            await asyncio.sleep(2)
            
            quotes = []
            rows = await self._page.query_selector_all('.dataview-body tbody tr')
            
            for row in rows:
                try:
                    cells = await row.query_selector_all('td')
                    if len(cells) >= 10:
                        def parse_float(text):
                            try:
                                return float(text.strip().replace(',', '').replace('%', ''))
                            except (ValueError, TypeError, AttributeError):
                                return None
                        
                        quote = MarketQuote(
                            code=(await cells[1].inner_text()).strip(),
                            name=(await cells[2].inner_text()).strip(),
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
            
            logger.info(f"获取市场行情成功: {len(quotes)} 条")
            return quotes
            
        except Exception as e:
            logger.error(f"获取市场行情失败: {e}")
            return []
    
    async def get_sector_list(self, sector_type: str = "industry") -> List[SectorInfo]:
        try:
            if sector_type == "industry":
                url = "https://quote.eastmoney.com/center/boardlist.html#industry_board"
            else:
                url = "https://quote.eastmoney.com/center/boardlist.html#concept_board"
            
            if not await self._navigate_with_anti_wind(url):
                return []
            
            await self._page.wait_for_selector('.dataview-body', timeout=15000)
            await asyncio.sleep(2)
            
            sectors = []
            rows = await self._page.query_selector_all('.dataview-body tbody tr')
            
            for row in rows:
                try:
                    cells = await row.query_selector_all('td')
                    if len(cells) >= 4:
                        def parse_float(text):
                            try:
                                return float(text.strip().replace('%', ''))
                            except (ValueError, TypeError, AttributeError):
                                return None
                        
                        sector = SectorInfo(
                            code="",
                            name=(await cells[1].inner_text()).strip(),
                            sector_type=sector_type,
                            change_pct=parse_float(await cells[2].inner_text())
                        )
                        sectors.append(sector)
                        
                except Exception:
                    continue
            
            logger.info(f"获取板块列表成功: {len(sectors)} 条")
            return sectors
            
        except Exception as e:
            logger.error(f"获取板块列表失败: {e}")
            return []
    
    async def get_stock_info(self, code: str) -> Optional[StockBasicInfo]:
        try:
            market = '1' if code.startswith('6') else '0'
            url = f"https://quote.eastmoney.com/{market}.{code}.html"
            
            if not await self._navigate_with_anti_wind(url):
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
            logger.error(f"获取股票信息失败 {code}: {e}")
            return None
    
    async def get_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq"
    ) -> List[KLineData]:
        return []
    
    async def get_sector_components(self, sector_code: str) -> List[str]:
        return []
    
    async def get_realtime_quote(self, code: str) -> Dict[str, Any]:
        try:
            market = '1' if code.startswith('6') else '0'
            url = f"https://quote.eastmoney.com/{market}.{code}.html"
            
            if not await self._navigate_with_anti_wind(url):
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
                except (ValueError, TypeError):
                    pass
            
            return quote
            
        except Exception as e:
            logger.error(f"获取实时行情失败 {code}: {e}")
            return {}
    
    def get_status(self) -> Dict[str, Any]:
        return {
            'initialized': self._is_initialized,
            'headless': self._config['headless'],
            'request_count': self._request_count,
            'anti_wind_stats': self._anti_wind.get_stats(),
        }
    
    async def take_screenshot(self, path: str) -> bool:
        try:
            await self._page.screenshot(path=path)
            return True
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return False

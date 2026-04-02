"""
增强版反风控模块

特性：
1. 代理 IP 池管理
2. 智能请求调度
3. Cookie 持久化
4. 浏览器指纹增强
5. 验证码检测与处理
6. 请求去重与缓存
"""

from typing import Optional, List, Dict, Any, Callable
from loguru import logger
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import random
import json
import os
import hashlib
import time


class ProxyStatus(Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


@dataclass
class ProxyInfo:
    host: str
    port: int
    protocol: str = "http"
    username: Optional[str] = None
    password: Optional[str] = None
    status: ProxyStatus = ProxyStatus.UNKNOWN
    last_used: Optional[datetime] = None
    success_count: int = 0
    fail_count: int = 0
    avg_response_time: float = 0.0
    blocked_until: Optional[datetime] = None
    
    @property
    def url(self) -> str:
        if self.username and self.password:
            return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol}://{self.host}:{self.port}"
    
    @property
    def success_rate(self) -> float:
        total = self.success_count + self.fail_count
        if total == 0:
            return 0.5
        return self.success_count / total


@dataclass
class RequestFingerprint:
    url: str
    method: str = "GET"
    params: Dict = field(default_factory=dict)
    headers: Dict = field(default_factory=dict)
    
    @property
    def hash(self) -> str:
        content = f"{self.url}:{self.method}:{json.dumps(self.params, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()


class ProxyPool:
    """代理 IP 池管理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._proxies: List[ProxyInfo] = []
        self._current_index = 0
        self._config = {
            'min_success_rate': 0.3,
            'block_duration_minutes': 30,
            'cooldown_seconds': 5,
            'max_consecutive_fails': 3,
            **(config or {})
        }
        self._consecutive_fails: Dict[str, int] = {}
    
    def add_proxy(
        self,
        host: str,
        port: int,
        protocol: str = "http",
        username: Optional[str] = None,
        password: Optional[str] = None
    ) -> None:
        proxy = ProxyInfo(
            host=host,
            port=port,
            protocol=protocol,
            username=username,
            password=password,
            status=ProxyStatus.AVAILABLE
        )
        self._proxies.append(proxy)
        logger.info(f"代理已添加: {host}:{port}")
    
    def add_proxies_from_file(self, filepath: str) -> int:
        if not os.path.exists(filepath):
            logger.error(f"代理文件不存在: {filepath}")
            return 0
        
        count = 0
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                try:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        host = parts[0]
                        port = int(parts[1])
                        protocol = parts[2] if len(parts) > 2 else "http"
                        username = parts[3] if len(parts) > 3 else None
                        password = parts[4] if len(parts) > 4 else None
                        
                        self.add_proxy(host, port, protocol, username, password)
                        count += 1
                except Exception as e:
                    logger.warning(f"解析代理失败: {line}, 错误: {e}")
        
        logger.info(f"从文件加载 {count} 个代理")
        return count
    
    def get_proxy(self) -> Optional[ProxyInfo]:
        if not self._proxies:
            return None
        
        now = datetime.now()
        available_proxies = []
        
        for proxy in self._proxies:
            if proxy.status == ProxyStatus.BLOCKED:
                if proxy.blocked_until and now < proxy.blocked_until:
                    continue
                else:
                    proxy.status = ProxyStatus.AVAILABLE
                    proxy.blocked_until = None
            
            if proxy.status == ProxyStatus.AVAILABLE:
                if proxy.last_used:
                    elapsed = (now - proxy.last_used).total_seconds()
                    if elapsed < self._config['cooldown_seconds']:
                        continue
                
                if proxy.success_rate >= self._config['min_success_rate']:
                    available_proxies.append(proxy)
        
        if not available_proxies:
            logger.warning("没有可用的代理 IP")
            return None
        
        available_proxies.sort(key=lambda p: (
            -p.success_rate,
            p.avg_response_time,
            -(p.success_count + p.fail_count)
        ))
        
        selected = available_proxies[0]
        selected.status = ProxyStatus.BUSY
        selected.last_used = now
        
        return selected
    
    def report_success(self, proxy: ProxyInfo, response_time: float) -> None:
        proxy.success_count += 1
        proxy.status = ProxyStatus.AVAILABLE
        
        if proxy.avg_response_time == 0:
            proxy.avg_response_time = response_time
        else:
            proxy.avg_response_time = proxy.avg_response_time * 0.8 + response_time * 0.2
        
        proxy_key = f"{proxy.host}:{proxy.port}"
        self._consecutive_fails[proxy_key] = 0
        
        logger.debug(f"代理成功: {proxy.host}:{proxy.port}, 成功率: {proxy.success_rate:.1%}")
    
    def report_failure(self, proxy: ProxyInfo, error: str) -> None:
        proxy.fail_count += 1
        proxy_key = f"{proxy.host}:{proxy.port}"
        self._consecutive_fails[proxy_key] = self._consecutive_fails.get(proxy_key, 0) + 1
        
        if self._consecutive_fails[proxy_key] >= self._config['max_consecutive_fails']:
            proxy.status = ProxyStatus.BLOCKED
            proxy.blocked_until = datetime.now() + timedelta(
                minutes=self._config['block_duration_minutes']
            )
            logger.warning(f"代理已屏蔽: {proxy.host}:{proxy.port}, 原因: {error}")
        else:
            proxy.status = ProxyStatus.AVAILABLE
    
    def get_status(self) -> Dict[str, Any]:
        available = sum(1 for p in self._proxies if p.status == ProxyStatus.AVAILABLE)
        busy = sum(1 for p in self._proxies if p.status == ProxyStatus.BUSY)
        blocked = sum(1 for p in self._proxies if p.status == ProxyStatus.BLOCKED)
        
        return {
            'total': len(self._proxies),
            'available': available,
            'busy': busy,
            'blocked': blocked,
            'proxies': [
                {
                    'host': p.host,
                    'port': p.port,
                    'status': p.status.value,
                    'success_rate': f"{p.success_rate:.1%}",
                    'success_count': p.success_count,
                    'fail_count': p.fail_count,
                }
                for p in self._proxies[:10]
            ]
        }


class SmartRequestScheduler:
    """智能请求调度器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._config = {
            'base_delay': 2.0,
            'max_delay': 30.0,
            'adaptive_factor': 1.5,
            'burst_threshold': 5,
            'burst_cooldown': 60,
            'time_windows': {
                'peak': (9, 11, 15),      # 9-11点，高延迟
                'normal': (11, 14, 3),     # 11-14点，中等延迟
                'low': (14, 24, 2),        # 14-24点，低延迟
                'night': (0, 9, 1),        # 0-9点，最低延迟
            },
            **(config or {})
        }
        
        self._request_history: List[datetime] = []
        self._last_burst_time: Optional[datetime] = None
        self._consecutive_failures = 0
        self._domain_delays: Dict[str, float] = {}
    
    def get_delay(self, domain: str = None) -> float:
        now = datetime.now()
        current_hour = now.hour
        
        base_multiplier = 1.0
        for window_name, (start, end, multiplier) in self._config['time_windows'].items():
            if start <= current_hour < end:
                base_multiplier = multiplier
                break
        
        self._request_history = [
            t for t in self._request_history
            if (now - t).total_seconds() < 60
        ]
        
        burst_multiplier = 1.0
        if len(self._request_history) >= self._config['burst_threshold']:
            burst_multiplier = 2.0
            self._last_burst_time = now
        
        if self._last_burst_time:
            elapsed = (now - self._last_burst_time).total_seconds()
            if elapsed < self._config['burst_cooldown']:
                burst_multiplier = 1.5
        
        failure_multiplier = 1 + self._consecutive_failures * 0.5
        
        domain_multiplier = 1.0
        if domain and domain in self._domain_delays:
            domain_multiplier = self._domain_delays[domain]
        
        delay = (
            self._config['base_delay'] *
            base_multiplier *
            burst_multiplier *
            failure_multiplier *
            domain_multiplier
        )
        
        delay = min(delay, self._config['max_delay'])
        jitter = random.uniform(0.8, 1.2)
        final_delay = delay * jitter
        
        self._request_history.append(now)
        
        logger.debug(
            f"请求延迟: {final_delay:.2f}s "
            f"(时间:{base_multiplier}x, 突发:{burst_multiplier}x, "
            f"失败:{failure_multiplier}x, 域名:{domain_multiplier}x)"
        )
        
        return final_delay
    
    def report_success(self, domain: str = None) -> None:
        self._consecutive_failures = 0
        
        if domain:
            if domain in self._domain_delays:
                self._domain_delays[domain] = max(1.0, self._domain_delays[domain] * 0.9)
            else:
                self._domain_delays[domain] = 1.0
    
    def report_failure(self, domain: str = None, is_rate_limit: bool = False) -> None:
        self._consecutive_failures += 1
        
        if domain:
            current = self._domain_delays.get(domain, 1.0)
            increase = 2.0 if is_rate_limit else 1.5
            self._domain_delays[domain] = min(current * increase, 10.0)
    
    async def wait(self, domain: str = None) -> None:
        delay = self.get_delay(domain)
        await asyncio.sleep(delay)


class CookieManager:
    """Cookie 持久化管理器"""
    
    def __init__(self, storage_dir: str = "data/cookies"):
        self._storage_dir = storage_dir
        self._cookies: Dict[str, List[Dict]] = {}
        
        os.makedirs(storage_dir, exist_ok=True)
    
    def _get_filepath(self, domain: str) -> str:
        safe_domain = domain.replace(':', '_').replace('/', '_')
        return os.path.join(self._storage_dir, f"{safe_domain}.json")
    
    async def save_cookies(self, domain: str, cookies: List[Dict]) -> None:
        self._cookies[domain] = cookies
        
        filepath = self._get_filepath(domain)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    'domain': domain,
                    'cookies': cookies,
                    'saved_at': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
            logger.debug(f"Cookie 已保存: {domain}")
        except Exception as e:
            logger.error(f"保存 Cookie 失败: {e}")
    
    async def load_cookies(self, domain: str) -> Optional[List[Dict]]:
        if domain in self._cookies:
            return self._cookies[domain]
        
        filepath = self._get_filepath(domain)
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            saved_at = datetime.fromisoformat(data['saved_at'])
            if (datetime.now() - saved_at).days > 7:
                logger.debug(f"Cookie 已过期: {domain}")
                return None
            
            cookies = data['cookies']
            self._cookies[domain] = cookies
            logger.debug(f"Cookie 已加载: {domain}, {len(cookies)} 条")
            return cookies
            
        except Exception as e:
            logger.error(f"加载 Cookie 失败: {e}")
            return None
    
    async def clear_cookies(self, domain: str = None) -> None:
        if domain:
            self._cookies.pop(domain, None)
            filepath = self._get_filepath(domain)
            if os.path.exists(filepath):
                os.remove(filepath)
            logger.debug(f"Cookie 已清除: {domain}")
        else:
            self._cookies.clear()
            for f in os.listdir(self._storage_dir):
                if f.endswith('.json'):
                    os.remove(os.path.join(self._storage_dir, f))
            logger.debug("所有 Cookie 已清除")


class EnhancedFingerprint:
    """增强版浏览器指纹伪装"""
    
    @staticmethod
    def get_stealth_script() -> str:
        script = """
            // 隐藏 webdriver 属性
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
                configurable: true
            });
            
            // 删除 __webdriver_script_fn
            delete window.__webdriver_script_fn;
            delete window.__driver_evaluate;
            delete window.__webdriver_evaluate;
            delete window.__selenium_evaluate;
            delete window.__fxdriver_evaluate;
            delete window.__driver_unwrapped;
            delete window.__webdriver_unwrapped;
            delete window.__selenium_unwrapped;
            delete window.__fxdriver_unwrapped;
            
            // 模拟真实插件
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    const plugins = [
                        { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                        { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
                        { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' },
                        { name: 'Widevine Content Decryption Module', filename: 'widevinecdmadapter.dll', description: 'Enables Widevine licenses for HTML5 media' }
                    ];
                    plugins.item = (index) => plugins[index] || null;
                    plugins.namedItem = (name) => plugins.find(p => p.name === name) || null;
                    plugins.refresh = () => {};
                    return plugins;
                },
                configurable: true
            });
            
            // 模拟语言
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en-US', 'en'],
                configurable: true
            });
            
            // 模拟平台
            Object.defineProperty(navigator, 'platform', {
                get: () => 'Win32',
                configurable: true
            });
            
            // 模拟硬件信息
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 8,
                configurable: true
            });
            
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => 8,
                configurable: true
            });
            
            // 模拟 maxTouchPoints
            Object.defineProperty(navigator, 'maxTouchPoints', {
                get: () => 0,
                configurable: true
            });
            
            // 模拟 vendor
            Object.defineProperty(navigator, 'vendor', {
                get: () => 'Google Inc.',
                configurable: true
            });
            
            // 模拟 connection
            Object.defineProperty(navigator, 'connection', {
                get: () => ({
                    effectiveType: '4g',
                    rtt: 50,
                    downlink: 10,
                    saveData: false
                }),
                configurable: true
            });
            
            // 模拟 permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // 模拟 chrome 对象
            window.chrome = {
                runtime: {
                    connect: () => {},
                    sendMessage: () => {},
                    onMessage: { addListener: () => {} },
                    onConnect: { addListener: () => {} }
                },
                loadTimes: function() {},
                csi: function() {},
                app: {
                    isInstalled: false,
                    InstallState: { DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed' },
                    RunningState: { CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running' }
                },
                webstore: {
                    onInstallStageChanged: { addListener: () => {} },
                    onDownloadProgress: { addListener: () => {} }
                }
            };
            
            // 修复 toString
            const originalToString = Function.toString;
            Function.toString = function() {
                if (this === window.navigator.permissions.query) {
                    return 'function query() { [native code] }';
                }
                if (this === window.chrome.runtime.connect) {
                    return 'function connect() { [native code] }';
                }
                if (this === window.chrome.runtime.sendMessage) {
                    return 'function sendMessage() { [native code] }';
                }
                return originalToString.call(this);
            };
            
            // 模拟 WebGL 指纹
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) return 'Intel Inc.';
                if (parameter === 37446) return 'Intel(R) UHD Graphics 630';
                return getParameter.apply(this, arguments);
            };
            
            // 模拟 Canvas 指纹噪声
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function(type) {
                if (this.width === 220 && this.height === 30) {
                    // 可能是指纹检测
                    const noise = Math.random() * 0.0001;
                    const context = this.getContext('2d');
                    if (context) {
                        const imageData = context.getImageData(0, 0, this.width, this.height);
                        for (let i = 0; i < imageData.data.length; i += 4) {
                            imageData.data[i] += Math.floor(noise * 255);
                        }
                        context.putImageData(imageData, 0, 0);
                    }
                }
                return originalToDataURL.apply(this, arguments);
            };
            
            // 模拟 Audio 指纹
            const originalAudioContext = window.AudioContext || window.webkitAudioContext;
            if (originalAudioContext) {
                const originalCreateAnalyser = originalAudioContext.prototype.createAnalyser;
                originalAudioContext.prototype.createAnalyser = function() {
                    const analyser = originalCreateAnalyser.apply(this, arguments);
                    const originalGetFloatFrequencyData = analyser.getFloatFrequencyData;
                    analyser.getFloatFrequencyData = function(array) {
                        originalGetFloatFrequencyData.apply(this, arguments);
                        for (let i = 0; i < array.length; i++) {
                            array[i] += Math.random() * 0.0001;
                        }
                    };
                    return analyser;
                };
            }
            
            // 隐藏自动化标志
            if (window.document.$cdc_asdjflasutopfhvcZLmcfl_) {
                delete window.document.$cdc_asdjflasutopfhvcZLmcfl_;
            }
            if (window.document.$chrome_asyncScriptInfo) {
                delete window.document.$chrome_asyncScriptInfo;
            }
            
            console.log('[Stealth] 指纹伪装已加载');
        """
        return script
    
    @staticmethod
    def validate_stealth_script(script: str) -> bool:
        checks = [
            ("webdriver 隐藏", "'webdriver'" in script),
            ("plugins 伪装", "'plugins'" in script),
            ("languages 设置", "'languages'" in script),
            ("chrome 对象", "window.chrome" in script),
            ("WebGL 指纹", "WebGLRenderingContext" in script),
            ("Canvas 噪声", "HTMLCanvasElement" in script),
            ("Audio 指纹", "AudioContext" in script),
            ("toString 修复", "Function.toString" in script),
        ]
        all_passed = all(passed for _, passed in checks)
        if not all_passed:
            for name, passed in checks:
                if not passed:
                    logger.warning(f"指纹伪装检查未通过: {name}")
        return all_passed
    
    @staticmethod
    def get_random_viewport() -> Dict[str, int]:
        viewports = [
            {'width': 1920, 'height': 1080},
            {'width': 1680, 'height': 1050},
            {'width': 1440, 'height': 900},
            {'width': 1536, 'height': 864},
            {'width': 1366, 'height': 768},
            {'width': 2560, 'height': 1440},
        ]
        return random.choice(viewports)
    
    @staticmethod
    def get_random_user_agent() -> str:
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
        ]
        return random.choice(user_agents)


class CaptchaDetector:
    """验证码检测器"""
    
    CAPTCHA_INDICATORS = [
        'captcha', '验证码', '滑动验证', '图形验证',
        'geetest', '极验', 'vaptcha', '网易易盾',
        'aliyun', '阿里云验证', '腾讯验证码',
        '请完成安全验证', '安全检查', '人机验证',
        'slider', 'slide-verify', 'nc_1_wrapper'
    ]
    
    @classmethod
    async def detect(cls, page) -> Dict[str, Any]:
        result = {
            'detected': False,
            'type': None,
            'selector': None,
            'message': None
        }
        
        try:
            content = await page.content()
            page_text = await page.evaluate('() => document.body.innerText')
            
            for indicator in cls.CAPTCHA_INDICATORS:
                if indicator.lower() in content.lower() or indicator in page_text:
                    result['detected'] = True
                    result['message'] = f"检测到验证码指示器: {indicator}"
                    
                    if 'geetest' in content.lower() or '极验' in page_text:
                        result['type'] = 'geetest'
                    elif 'slider' in content.lower() or '滑动' in page_text:
                        result['type'] = 'slider'
                    elif '图形验证' in page_text:
                        result['type'] = 'image'
                    else:
                        result['type'] = 'unknown'
                    
                    break
            
            if not result['detected']:
                captcha_selectors = [
                    '.geetest_slider', '.geetest_panel',
                    '#nc_1_wrapper', '.nc_wrapper',
                    '.captcha', '#captcha',
                    '.verify-wrap', '.slide-verify'
                ]
                
                for selector in captcha_selectors:
                    element = await page.query_selector(selector)
                    if element:
                        result['detected'] = True
                        result['type'] = 'slider'
                        result['selector'] = selector
                        result['message'] = f"检测到验证码元素: {selector}"
                        break
            
        except Exception as e:
            logger.error(f"验证码检测失败: {e}")
        
        return result
    
    @classmethod
    async def wait_for_manual_solve(cls, page, timeout: int = 60) -> bool:
        logger.info("检测到验证码，等待人工处理...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            result = await cls.detect(page)
            if not result['detected']:
                logger.info("验证码已通过")
                return True
            await asyncio.sleep(1)
        
        logger.warning(f"验证码处理超时 ({timeout}秒)")
        return False


class AntiWindControlManager:
    """反风控管理器 - 整合所有反风控组件"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._config = {
            'enable_proxy': True,
            'enable_cookies': True,
            'enable_smart_schedule': True,
            'enable_captcha_detection': True,
            'cookie_storage_dir': 'data/cookies',
            **(config or {})
        }
        
        self.proxy_pool = ProxyPool()
        self.scheduler = SmartRequestScheduler()
        self.cookie_manager = CookieManager(self._config['cookie_storage_dir'])
        self.fingerprint = EnhancedFingerprint()
        self.captcha_detector = CaptchaDetector()
        
        self._current_proxy: Optional[ProxyInfo] = None
        self._stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'captcha_encountered': 0,
            'proxy_rotations': 0,
        }
    
    async def before_request(self, url: str, domain: str = None) -> Dict[str, Any]:
        self._stats['total_requests'] += 1
        
        context = {
            'proxy': None,
            'cookies': None,
            'delay': 0,
            'fingerprint_script': self.fingerprint.get_stealth_script(),
        }
        
        if self._config['enable_smart_schedule']:
            context['delay'] = self.scheduler.get_delay(domain)
        
        if self._config['enable_proxy']:
            proxy = self.proxy_pool.get_proxy()
            if proxy:
                context['proxy'] = proxy.url
                self._current_proxy = proxy
        
        if self._config['enable_cookies'] and domain:
            cookies = await self.cookie_manager.load_cookies(domain)
            if cookies:
                context['cookies'] = cookies
        
        return context
    
    async def after_request(
        self,
        success: bool,
        domain: str = None,
        response_time: float = 0,
        error: str = None,
        cookies: List[Dict] = None
    ) -> None:
        if success:
            self._stats['successful_requests'] += 1
            self.scheduler.report_success(domain)
            
            if self._current_proxy:
                self.proxy_pool.report_success(self._current_proxy, response_time)
            
            if cookies and domain and self._config['enable_cookies']:
                await self.cookie_manager.save_cookies(domain, cookies)
        else:
            self._stats['failed_requests'] += 1
            self.scheduler.report_failure(domain)
            
            if self._current_proxy:
                self.proxy_pool.report_failure(self._current_proxy, error or "Unknown error")
    
    async def check_captcha(self, page) -> Dict[str, Any]:
        if not self._config['enable_captcha_detection']:
            return {'detected': False}
        
        result = await self.captcha_detector.detect(page)
        
        if result['detected']:
            self._stats['captcha_encountered'] += 1
            logger.warning(f"验证码检测: {result['message']}")
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        success_rate = 0
        if self._stats['total_requests'] > 0:
            success_rate = self._stats['successful_requests'] / self._stats['total_requests']
        
        return {
            **self._stats,
            'success_rate': f"{success_rate:.1%}",
            'proxy_pool': self.proxy_pool.get_status(),
        }
    
    def add_proxy(self, host: str, port: int, **kwargs) -> None:
        self.proxy_pool.add_proxy(host, port, **kwargs)
    
    def add_proxies_from_file(self, filepath: str) -> int:
        return self.proxy_pool.add_proxies_from_file(filepath)

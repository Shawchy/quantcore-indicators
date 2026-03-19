import asyncio
<<<<<<< HEAD
from typing import Optional, List, Dict, Any, Union
from enum import Enum
=======
import time
import random
from typing import Optional, List, Dict, Any, Callable, TypeVar, Union
from functools import wraps
>>>>>>> 7aaa7cbe85a09d6bf88368f14e12d60640ec9467
from loguru import logger
from pydantic import BaseModel

try:
    import efinance as ef
    from efinance.utils import MarketType
    EF_AVAILABLE = True
except ImportError:
    EF_AVAILABLE = False
    logger.warning("efinance 未安装，请运行：pip install efinance")

from .base import (
    BaseDataAdapter,
    DataSourceType,
    StockBasicInfo,
    KLineData,
    SectorInfo,
    ChipData,
<<<<<<< HEAD
    IndexMember
=======
    FinancialPerformance
>>>>>>> 7aaa7cbe85a09d6bf88368f14e12d60640ec9467
)
from app.models.schemas import (
    BillboardEntry,
    BoardInfo,
    ShareholderInfo,
    IndexComponent,
    CapitalFlowItem
)


class CompanyPerformance(BaseModel):
    """公司业绩表现数据"""
    code: str
    name: str
    report_date: str
    revenue: float  # 营业收入
    revenue_growth: float  # 营业收入同比增长
    revenue_qoq: float  # 营业收入季度环比
    net_profit: float  # 净利润
    net_profit_growth: float  # 净利润同比增长
    net_profit_qoq: float  # 净利润季度环比
    eps: float  # 每股收益
    bps: float  # 每股净资产
    roe: float  # 净资产收益率
    gross_margin: float  # 销售毛利率
    cash_flow_per_share: float  # 每股经营现金流量


class DealDetail(BaseModel):
    """股票成交明细数据"""
    stock_name: str  # 股票名称
    stock_code: str  # 股票代码
    prev_close: float  # 昨收价
    trade_time: str  # 成交时间（HH:MM:SS）
    price: float  # 成交价
    volume: int  # 成交量（手）
    order_count: int  # 成交单数


class HistoryBill(BaseModel):
    """股票历史单子流入流出数据"""
    stock_name: str  # 股票名称
    stock_code: str  # 股票代码
    date: str  # 日期
    main_net_amount: float  # 主力净流入
    small_net_amount: float  # 小单净流入
    medium_net_amount: float  # 中单净流入
    big_net_amount: float  # 大单净流入
    super_net_amount: float  # 超大单净流入
    main_net_ratio: float  # 主力净流入占比
    small_net_ratio: float  # 小单流入净占比
    medium_net_ratio: float  # 中单流入净占比
    big_net_ratio: float  # 大单流入净占比
    super_net_ratio: float  # 超大单流入净占比
    close_price: float  # 收盘价
    change_pct: float  # 涨跌幅
from app.utils.data_validator import validator
from app.utils.tushare_cache_stats import api_call_cache


class MarketQuote(BaseModel):
    """市场实时行情数据"""
    code: str
    name: str
    change_pct: Optional[float] = None
    price: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    open: Optional[float] = None
    change: Optional[float] = None
    turnover_rate: Optional[float] = None
    volume_ratio: Optional[float] = None
    pe_ratio: Optional[float] = None
    volume: Optional[float] = None
    amount: Optional[float] = None
    prev_close: Optional[float] = None
    total_market_cap: Optional[float] = None
    float_market_cap: Optional[float] = None
    market_type: Optional[str] = None


class EFinanceAdapter(BaseDataAdapter):
    """efinance 数据源适配器
    
    efinance 是一个免费的金融数据接口库，提供 A 股、基金、期货等数据
    GitHub: https://github.com/Micro-sun/efinance
    
    特点：
    - 完全免费，无需注册
    - 数据来源于东方财富
    - 支持 A 股、基金、期货、债券等
    - 实时行情、历史 K 线、财务数据等
    
    反风控机制：
    - 请求头伪装（模拟浏览器）
    - 请求频率控制（1-2 秒间隔 + 随机延时）
    - 批量请求优化（减少请求次数）
    - 本地缓存策略（减少重复请求）
    - 失败重试机制（指数退避）
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._is_initialized = False
        
        # 内存缓存
        self._cache: Dict[str, Any] = {}
        self._cache_timestamp: Dict[str, float] = {}
        # 不同数据的缓存时间（秒）
        self._cache_ttl = {
            'kline': 300,        # K 线：5 分钟
            'stock_list': 1800,  # 股票列表：30 分钟
            'stock_info': 600,   # 股票信息：10 分钟
            'quote': 60,         # 实时行情：1 分钟
            'sector': 300,       # 板块：5 分钟
            'default': 300       # 默认：5 分钟
        }
        
        # 反风控设置
        self._request_delay_range = (1.0, 2.0)  # 请求间隔（秒）
        self._max_retries = 3  # 最大重试次数
        self._retry_base_delay = 2.0  # 重试基础延迟（秒）
        
        # 请求头轮换池（多个浏览器配置）
        self._user_agents = [
            # Chrome - Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            # Chrome - macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            # Edge - Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
            # Firefox - Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
            # Firefox - macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.3; rv:123.0) Gecko/20100101 Firefox/123.0",
            # Safari - macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        ]
        
        # 当前使用的 User-Agent 索引
        self._current_ua_index = 0
        
        # 请求统计
        self._request_count = 0
        self._fail_count = 0
        self._last_request_time = 0
        
        # 动态调整参数
        self._adaptive_delay_enabled = True  # 启用自适应延迟
        self._consecutive_failures = 0  # 连续失败次数
    
    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.EFINANCE
    
    def _get_local_user_agent(self) -> str:
        """获取本地设备的 User-Agent
        
        Returns:
            str: 当前系统的真实 User-Agent
        """
        try:
            import platform
            import sys
            
            # 获取系统信息
            system = platform.system()
            release = platform.release()
            machine = platform.machine()
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            
            if system == "Windows":
                return f"Mozilla/5.0 (Windows NT 10.0; {machine}; Python/{python_version})"
            elif system == "Darwin":
                return f"Mozilla/5.0 (Macintosh; Intel Mac OS X {release}; {machine}; Python/{python_version})"
            elif system == "Linux":
                return f"Mozilla/5.0 (X11; Linux {machine}; Python/{python_version})"
            else:
                return f"Mozilla/5.0 ({system} {release}; {machine}; Python/{python_version})"
        except Exception as e:
            logger.warning(f"获取本地 User-Agent 失败：{e}")
            return "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    
    def _rotate_user_agent(self) -> str:
        """轮换 User-Agent
        
        Returns:
            str: 轮换后的 User-Agent
        """
        # 随机选择一个 User-Agent
        ua = random.choice(self._user_agents)
        self._current_ua_index = (self._current_ua_index + 1) % len(self._user_agents)
        return ua
    
    def _get_time_based_delay(self) -> tuple:
        """根据时间段获取延迟范围
        
        Returns:
            tuple: (min_delay, max_delay)
        
        Note:
            - 交易时段（9:30-15:00）：延迟更长，降低被封风险
            - 非交易时段：延迟较短，提高效率
            - 夜间（22:00-7:00）：延迟最短
        """
        import datetime
        
        now = datetime.datetime.now()
        hour = now.hour
        minute = now.minute
        current_time = hour * 60 + minute
        
        # 交易时段：9:30-11:30, 13:00-15:00
        if (9*60+30 <= current_time <= 11*60+30) or (13*60 <= current_time <= 15*60):
            # 交易时段：2-4 秒
            return (2.0, 4.0)
        # 盘后时段：15:00-22:00
        elif 15*60 < current_time <= 22*60:
            # 盘后：1-2 秒
            return (1.0, 2.0)
        # 夜间：22:00-9:30
        else:
            # 夜间：0.5-1.5 秒
            return (0.5, 1.5)
    
    def _setup_request_headers(self, rotate: bool = True):
        """设置请求头（模拟浏览器，降低被识别为爬虫的概率）
        
        Args:
            rotate: 是否轮换 User-Agent，默认 True
        """
        try:
            # 轮换或选择 User-Agent
            if rotate:
                user_agent = self._rotate_user_agent()
            else:
                user_agent = self._user_agents[0]
            
            # 配置全局请求头（模拟浏览器）
            headers = {
                "User-Agent": user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7",
                "Accept-Encoding": "gzip, deflate",
                "Referer": "https://eastmoney.com/",  # 来源页（东方财富网）
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-site",
                "Cache-Control": "max-age=0"
            }
            
            # 覆盖 efinance 底层的 requests 请求头
            if hasattr(ef.stock, '_session'):
                ef.stock._session.headers.update(headers)
                logger.debug(f"efinance 请求头已设置（反风控伪装）: {user_agent[:50]}...")
        except Exception as e:
            logger.warning(f"设置请求头失败：{e}")
    
    async def _rate_limit(self):
        """请求频率控制（异步版本，支持自适应延迟）"""
        # 如果启用自适应延迟，根据时间段调整
        if self._adaptive_delay_enabled:
            min_delay, max_delay = self._get_time_based_delay()
            
            # 根据连续失败次数增加延迟
            if self._consecutive_failures > 0:
                # 每失败一次，延迟增加 1 秒，最多增加 5 秒
                extra_delay = min(self._consecutive_failures, 5)
                min_delay += extra_delay
                max_delay += extra_delay
            
            delay = random.uniform(min_delay, max_delay)
        else:
            delay = random.uniform(*self._request_delay_range)
        
        await asyncio.sleep(delay)
        
        # 记录最后一次请求时间
        self._last_request_time = time.time()
        self._request_count += 1
    
    def _rate_limit_sync(self):
        """请求频率控制（同步版本，用于同步函数）"""
        delay = random.uniform(*self._request_delay_range)
        time.sleep(delay)
    
    async def set_proxy(self, proxy_url: str) -> bool:
        """设置代理 IP（当 IP 被封禁时使用）
        
        Args:
            proxy_url: 代理地址，例如：
                - 'http://127.0.0.1:7890'
                - 'http://user:pass@proxy.server:port'
        
        Returns:
            bool: 设置是否成功
        
        Note:
            - 仅当 IP 被封禁时才需要使用代理
            - 需要自备有效的代理服务器
            - 设置后对所有后续请求生效
        """
        try:
            if not EF_AVAILABLE:
                return False
            
            proxies = {
                "http": proxy_url,
                "https": proxy_url
            }
            
            if hasattr(ef.stock, '_session'):
                ef.stock._session.proxies.update(proxies)
                logger.info(f"代理 IP 已设置：{proxy_url}")
                return True
            else:
                logger.warning("无法设置代理：ef.stock._session 不存在")
                return False
        except Exception as e:
            logger.error(f"设置代理 IP 失败：{e}")
            return False
    
    async def clear_proxy(self):
        """清除代理设置"""
        try:
            if hasattr(ef.stock, '_session'):
                ef.stock._session.proxies.clear()
                logger.info("代理 IP 已清除")
        except Exception as e:
            logger.warning(f"清除代理失败：{e}")
    
    def record_request_success(self):
        """记录请求成功（重置连续失败计数）"""
        self._consecutive_failures = 0
        self._fail_count = max(0, self._fail_count - 1)  # 成功时减少失败计数
    
    def record_request_failure(self):
        """记录请求失败（增加连续失败计数）"""
        self._consecutive_failures += 1
        self._fail_count += 1
        
        # 如果连续失败超过阈值，记录警告
        if self._consecutive_failures >= 3:
            logger.warning(f"连续失败 {self._consecutive_failures}次，建议暂停请求或切换 IP")
        
        # 自动轮换 User-Agent
        if self._consecutive_failures >= 2:
            self._setup_request_headers(rotate=True)
            logger.info(f"自动轮换 User-Agent（连续失败{self._consecutive_failures}次）")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取请求统计信息
        
        Returns:
            Dict: 包含请求统计信息的字典
        """
        success_rate = 0.0
        if self._request_count > 0:
            success_rate = (self._request_count - self._fail_count) / self._request_count * 100
        
        return {
            "total_requests": self._request_count,
            "failed_requests": self._fail_count,
            "success_rate": f"{success_rate:.2f}%",
            "consecutive_failures": self._consecutive_failures,
            "current_delay_range": self._get_time_based_delay() if self._adaptive_delay_enabled else self._request_delay_range,
            "adaptive_delay_enabled": self._adaptive_delay_enabled,
            "user_agents_count": len(self._user_agents),
            "current_ua_index": self._current_ua_index
        }
    
    def enable_adaptive_delay(self, enabled: bool = True):
        """启用/禁用自适应延迟
        
        Args:
            enabled: 是否启用自适应延迟
        """
        self._adaptive_delay_enabled = enabled
        logger.info(f"自适应延迟已{'启用' if enabled else '禁用'}")
    
    def set_custom_delay(self, min_delay: float, max_delay: float):
        """设置自定义延迟范围
        
        Args:
            min_delay: 最小延迟（秒）
            max_delay: 最大延迟（秒）
        """
        self._request_delay_range = (min_delay, max_delay)
        self._adaptive_delay_enabled = False  # 禁用自适应延迟
        logger.info(f"自定义延迟范围：{min_delay}-{max_delay}秒（已禁用自适应延迟）")
    
    async def initialize(self) -> bool:
        """初始化适配器，包含反风控设置"""
        if not EF_AVAILABLE:
            logger.warning("efinance 模块不可用，跳过初始化")
            return False
        
        try:
            # 1. 设置请求头（伪装浏览器，使用本地设备信息）
            self._setup_request_headers(rotate=True)
            
            # 2. efinance 无需其他初始化，直接可用
            self._is_initialized = True
            
            # 获取当前时间段
            import datetime
            now = datetime.datetime.now()
            hour = now.hour
            minute = now.minute
            current_time = hour * 60 + minute
            
            time_period = "交易时段" if ((9*60+30 <= current_time <= 11*60+30) or (13*60 <= current_time <= 15*60)) else "非交易时段"
            
            logger.info("efinance 适配器初始化成功（含反风控设置）")
            logger.info(f"  - 请求头：已配置（{len(self._user_agents)}个浏览器配置，自动轮换）")
            logger.info(f"  - 当前时间段：{time_period}")
            logger.info(f"  - 请求频率：自适应延迟（根据时间段和失败次数调整）")
            logger.info(f"  - 最大重试：{self._max_retries}次（指数退避）")
            logger.info(f"  - 缓存策略：实时行情 60 秒，股票信息 10 分钟")
            logger.info(f"  - 失败统计：已启用（自动调整策略）")
            return True
        except Exception as e:
            logger.error(f"efinance 适配器初始化失败：{e}")
            return False
    
    async def close(self):
        """关闭连接"""
        self._is_initialized = False
        self._cache.clear()
        self._cache_timestamp.clear()
        logger.info("efinance 适配器已关闭")
    
    def _get_cache_key(self, prefix: str, **kwargs) -> str:
        """生成缓存 key"""
        key_parts = [prefix]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")
        return "_".join(key_parts)
    
    def _get_from_cache(self, key: str, ttl_type: str = 'default') -> Optional[Any]:
        """从缓存获取数据"""
        import time
        if key not in self._cache:
            return None
        
        timestamp = self._cache_timestamp.get(key, 0)
        ttl = self._cache_ttl.get(ttl_type, self._cache_ttl['default'])
        
        if time.time() - timestamp > ttl:
            del self._cache[key]
            del self._cache_timestamp[key]
            return None
        
        return self._cache[key]
    
    def _set_to_cache(self, key: str, value: Any, ttl_type: str = 'default'):
        """设置缓存"""
        import time
        self._cache[key] = value
        self._cache_timestamp[key] = time.time()
    
    def rate_limit_decorator(min_delay: float = 1.0, max_delay: float = 2.0, retries: int = 3):
        """请求频率控制装饰器（带重试机制）
        
        Args:
            min_delay: 最小延迟（秒）
            max_delay: 最大延迟（秒）
            retries: 重试次数
            
        Usage:
            @rate_limit_decorator(min_delay=1.5, max_delay=2.5, retries=3)
            async def get_data(...):
                ...
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                self = args[0] if args else None
                
                # 1. 频率控制
                if isinstance(self, EFinanceAdapter):
                    await self._rate_limit()
                else:
                    await asyncio.sleep(random.uniform(min_delay, max_delay))
                
                # 2. 执行请求，带重试机制
                last_error = None
                for attempt in range(retries):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        last_error = e
                        if attempt < retries - 1:
                            # 指数退避：2s -> 4s -> 8s
                            delay = (2 ** attempt) * min_delay + random.uniform(0, 1)
                            logger.debug(f"{func.__name__} 请求失败，{delay:.1f}秒后重试（{attempt+1}/{retries}）: {e}")
                            await asyncio.sleep(delay)
                        else:
                            logger.error(f"{func.__name__} 请求失败，已重试{retries}次：{e}")
                
                # 所有重试都失败
                raise last_error if last_error else Exception("请求失败")
            
            return wrapper
        return decorator
    
    async def get_stock_list(self) -> List[StockBasicInfo]:
        """获取股票列表"""
        try:
            if not EF_AVAILABLE:
                return []
            
            cache_key = self._get_cache_key('stock_list')
            cached = self._get_from_cache(cache_key, 'stock_list')
            if cached:
                return cached
            
            # 频率控制
            await self._rate_limit()
            
            # 获取沪深 A 股实时行情，从中提取股票基本信息
            df = ef.stock.get_realtime_quotes()
            
            stocks = []
            for row in df.itertuples(index=False):
                code = str(getattr(row, '股票代码', '')).zfill(6)
                # 过滤掉非 A 股数据
                if not code or not code.isdigit():
                    continue
                
                # 安全转换浮点数，处理 '-' 等无效值
                def safe_float(value, default=0.0):
                    try:
                        v = float(value) if value not in ('-', '', None) else default
                        return v
                    except (ValueError, TypeError):
                        return default
                
                price = safe_float(getattr(row, '最新价', 1), 1.0)
                if price == 0:
                    price = 1.0
                
                stocks.append(StockBasicInfo(
                    code=code,
                    name=getattr(row, '股票名称', ''),
                    market='SH' if code.startswith('6') else 'SZ',
                    industry='',
                    area='',
                    list_date='',
                    total_shares=safe_float(getattr(row, '总市值', 0)) / price,
                    float_shares=safe_float(getattr(row, '流通市值', 0)) / price
                ))
            
            self._set_to_cache(cache_key, stocks, 'stock_list')
            logger.info(f"获取股票列表成功：{len(stocks)}只")
            return stocks
            
        except Exception as e:
            logger.error(f"获取股票列表失败：{e}")
            return []
    
    async def get_stock_info(self, code: str) -> Optional[StockBasicInfo]:
        """获取股票信息（单只）
        
        Args:
            code: 股票代码
            
        Returns:
            股票基本信息，失败返回 None
            
        Note:
            使用 efinance.stock.get_base_info 接口，获取更详细的股票信息
        """
        try:
            if not EF_AVAILABLE:
                return None
            
            cache_key = self._get_cache_key('stock_info', code=code)
            cached = self._get_from_cache(cache_key, 'stock_info')
            if cached:
                return cached
            
            # 频率控制
            await self._rate_limit()
            
            # 获取单只股票信息
            result = ef.stock.get_base_info(code.zfill(6))
            
            if result is None or (hasattr(result, 'empty') and result.empty):
                return None
            
            # 单只股票返回 Series
            if hasattr(result, 'dtype'):
                # 安全获取数值，处理 NaN
                def safe_get(key, default=0.0):
                    val = result.get(key, default)
                    if val is None or (isinstance(val, float) and str(val) == 'nan'):
                        return default
                    try:
                        return float(val)
                    except (ValueError, TypeError):
                        return default
                
                latest_price = safe_get('最新价', 1.0)
                if latest_price == 0:
                    latest_price = 1.0
                
                total_market_cap = safe_get('总市值', 0.0)
                float_market_cap = safe_get('流通市值', 0.0)
                
                stock = StockBasicInfo(
                    code=code.zfill(6),
                    name=str(result.get('股票名称', '') or ''),
                    market='SH' if code.startswith('6') else 'SZ',
                    industry=str(result.get('所处行业', '') or ''),
                    area='',
                    list_date='',
                    total_shares=total_market_cap / latest_price if total_market_cap > 0 else 0.0,
                    float_shares=float_market_cap / latest_price if float_market_cap > 0 else 0.0
                )
            else:
                return None
            
            self._set_to_cache(cache_key, stock, 'stock_info')
            return stock
            
        except Exception as e:
            logger.error(f"获取股票信息失败 {code}: {e}")
            return None
    
<<<<<<< HEAD
    async def get_stocks_base_info(self, stock_codes: List[str]) -> List[StockBasicInfo]:
        """
        批量获取多只股票的基本信息
        
        Args:
            stock_codes: 股票代码列表，如 ['600519', '000858']
        
        Returns:
            股票基本信息列表
=======
    async def get_stock_info_batch(self, codes: List[str]) -> List[StockBasicInfo]:
        """批量获取股票信息
        
        Args:
            codes: 股票代码列表
            
        Returns:
            股票基本信息列表
            
        Note:
            使用 efinance.stock.get_base_info 批量接口，效率更高
>>>>>>> 7aaa7cbe85a09d6bf88368f14e12d60640ec9467
        """
        try:
            if not EF_AVAILABLE:
                return []
            
<<<<<<< HEAD
            if not stock_codes:
                return []
            
            # 生成缓存 key
            codes_key = '_'.join(sorted(stock_codes))
            cache_key = self._get_cache_key('stocks_base_info', codes=codes_key)
            cached = self._get_from_cache(cache_key, 'stock_list')
            if cached:
                return cached
            
            # 批量获取股票信息
            df = ef.stock.get_base_info(stock_codes)
=======
            # 过滤空代码
            valid_codes = [c.zfill(6) for c in codes if c]
            
            if not valid_codes:
                return []
            
            cache_key = self._get_cache_key('stock_info_batch', codes=','.join(sorted(valid_codes)))
            cached = self._get_from_cache(cache_key, 'stock_info')
            if cached:
                return cached
            
            # 频率控制
            await self._rate_limit()
            
            # 批量获取股票信息
            df = ef.stock.get_base_info(valid_codes)
>>>>>>> 7aaa7cbe85a09d6bf88368f14e12d60640ec9467
            
            if df is None or (hasattr(df, 'empty') and df.empty):
                return []
            
            stocks = []
            for row in df.itertuples(index=False):
<<<<<<< HEAD
                code = str(getattr(row, '股票代码', '')).zfill(6)
                if not code:
                    continue
                
                # 安全转换浮点数
                def safe_float(value, default=0.0):
                    try:
                        if value is None or value == '' or value == '-' or (isinstance(value, float) and str(value) == 'nan'):
                            return default
                        return float(value)
                    except (ValueError, TypeError):
                        return default
                
                # 获取最新价用于计算股本
                latest_price = safe_float(getattr(row, '最新价', 1.0), 1.0)
                if latest_price == 0:
                    latest_price = 1.0
                
                total_shares_raw = safe_float(getattr(row, '总市值', 0.0), 0.0)
                float_shares_raw = safe_float(getattr(row, '流通市值', 0.0), 0.0)
                
                stocks.append(StockBasicInfo(
                    code=code,
                    name=getattr(row, '股票名称', '') or '',
                    market='SH' if code.startswith('6') else 'SZ',
                    industry=getattr(row, '所处行业', '') or '',
                    area='',
                    list_date='',
                    total_shares=total_shares_raw / latest_price if total_shares_raw > 0 else 0.0,
                    float_shares=float_shares_raw / latest_price if float_shares_raw > 0 else 0.0
                ))
            
            self._set_to_cache(cache_key, stocks, 'stock_list')
=======
                code = str(getattr(row, '股票代码', ''))
                if not code:
                    continue
                
                # 安全获取数值
                def safe_get(key, default=0.0):
                    val = getattr(row, key, default)
                    if val is None or (isinstance(val, float) and str(val) == 'nan'):
                        return default
                    try:
                        return float(val)
                    except (ValueError, TypeError):
                        return default
                
                latest_price = safe_get('最新价', 1.0)
                if latest_price == 0:
                    latest_price = 1.0
                
                total_market_cap = safe_get('总市值', 0.0)
                float_market_cap = safe_get('流通市值', 0.0)
                
                stocks.append(StockBasicInfo(
                    code=code,
                    name=str(getattr(row, '股票名称', '') or ''),
                    market='SH' if code.startswith('6') else 'SZ',
                    industry=str(getattr(row, '所处行业', '') or ''),
                    area='',
                    list_date='',
                    total_shares=total_market_cap / latest_price if total_market_cap > 0 else 0.0,
                    float_shares=float_market_cap / latest_price if float_market_cap > 0 else 0.0
                ))
            
            self._set_to_cache(cache_key, stocks, 'stock_info')
>>>>>>> 7aaa7cbe85a09d6bf88368f14e12d60640ec9467
            logger.info(f"批量获取股票信息成功：{len(stocks)}只")
            return stocks
            
        except Exception as e:
            logger.error(f"批量获取股票信息失败：{e}")
            return []
    
<<<<<<< HEAD
    async def get_deal_detail(self, stock_code: str, max_count: int = 1000000) -> List[DealDetail]:
        """
        获取股票最新交易日成交明细
        
        Args:
            stock_code: 股票代码或股票名称，如 '600519' 或 '贵州茅台'
            max_count: 最近的最大数据条数，默认 1000000
            
        Returns:
            成交明细数据列表
        
        Examples:
            >>> adapter = EFinanceAdapter()
            >>> deals = await adapter.get_deal_detail('600519')
            >>> for deal in deals[:5]:
            ...     print(f"{deal.trade_time} - {deal.price:.2f}元 - {deal.volume}手")
        """
        try:
            if not EF_AVAILABLE:
                return []
            
            cache_key = self._get_cache_key('deal_detail', code=stock_code, max_count=max_count)
            cached = self._get_from_cache(cache_key, 'kline')
            if cached:
                return cached
            
            # 获取成交明细数据
            df = ef.stock.get_deal_detail(stock_code, max_count=max_count)
            
            if df.empty:
                return []
            
            deals = []
            for row in df.itertuples(index=False):
                # 安全转换数值
                def safe_int(value, default=0):
                    try:
                        if value is None or value == '' or value == '-' or (isinstance(value, float) and str(value) == 'nan'):
                            return default
                        return int(value)
                    except (ValueError, TypeError):
                        return default
                
                def safe_float(value, default=0.0):
                    try:
                        if value is None or value == '' or value == '-' or (isinstance(value, float) and str(value) == 'nan'):
                            return default
                        return float(value)
                    except (ValueError, TypeError):
                        return default
                
                stock_code_raw = str(getattr(row, '股票代码', '')).zfill(6)
                if not stock_code_raw:
                    continue
                
                deals.append(DealDetail(
                    stock_name=getattr(row, '股票名称', '') or '',
                    stock_code=stock_code_raw,
                    prev_close=safe_float(getattr(row, '昨收', 0), 0.0),
                    trade_time=str(getattr(row, '时间', '') or ''),
                    price=safe_float(getattr(row, '成交价', 0), 0.0),
                    volume=safe_int(getattr(row, '成交量', 0), 0),
                    order_count=safe_int(getattr(row, '单数', 0), 0)
                ))
            
            self._set_to_cache(cache_key, deals, 'kline')
            logger.info(f"获取 {stock_code} 成交明细成功：{len(deals)}条")
            return deals
            
        except Exception as e:
            logger.error(f"获取成交明细失败 {stock_code}: {e}")
            return []
    
    async def get_history_bill(self, stock_code: str) -> List[HistoryBill]:
        """
        获取单只股票历史单子流入流出数据
        
        Args:
            stock_code: 股票代码
            
        Returns:
            历史单子流入流出数据列表
        
        Examples:
            >>> adapter = EFinanceAdapter()
            >>> bills = await adapter.get_history_bill('600519')
            >>> for bill in bills[:5]:
            ...     print(f"{bill.date} - 主力净流入：{bill.main_net_amount/1e8:.2f}亿")
        """
        try:
            if not EF_AVAILABLE:
                return []
            
            cache_key = self._get_cache_key('history_bill', code=stock_code)
            cached = self._get_from_cache(cache_key, 'kline')
            if cached:
                return cached
            
            # 获取历史单子流入流出数据
            df = ef.stock.get_history_bill(stock_code)
            
            if df.empty:
                return []
            
            bills = []
            for row in df.itertuples(index=False):
                # 安全转换数值
                def safe_float(value, default=0.0):
                    try:
                        if value is None or value == '' or value == '-' or (isinstance(value, float) and str(value) == 'nan'):
                            return default
                        return float(value)
                    except (ValueError, TypeError):
                        return default
                
                stock_code_raw = str(getattr(row, '股票代码', '')).zfill(6)
                if not stock_code_raw:
                    continue
                
                date_raw = getattr(row, '日期', '')
                if date_raw:
                    if isinstance(date_raw, str):
                        date = date_raw.split(' ')[0].replace('-', '')
                    else:
                        date = str(date_raw)[:10].replace('-', '')
                    if len(date) == 10:  # YYYY-MM-DD 格式
                        date = date.replace('-', '')
                else:
                    date = ''
                
                bills.append(HistoryBill(
                    stock_name=getattr(row, '股票名称', '') or '',
                    stock_code=stock_code_raw,
                    date=date,
                    main_net_amount=safe_float(getattr(row, '主力净流入', 0), 0.0),
                    small_net_amount=safe_float(getattr(row, '小单净流入', 0), 0.0),
                    medium_net_amount=safe_float(getattr(row, '中单净流入', 0), 0.0),
                    big_net_amount=safe_float(getattr(row, '大单净流入', 0), 0.0),
                    super_net_amount=safe_float(getattr(row, '超大单净流入', 0), 0.0),
                    main_net_ratio=safe_float(getattr(row, '主力净流入占比', 0), 0.0),
                    small_net_ratio=safe_float(getattr(row, '小单流入净占比', 0), 0.0),
                    medium_net_ratio=safe_float(getattr(row, '中单流入净占比', 0), 0.0),
                    big_net_ratio=safe_float(getattr(row, '大单流入净占比', 0), 0.0),
                    super_net_ratio=safe_float(getattr(row, '超大单流入净占比', 0), 0.0),
                    close_price=safe_float(getattr(row, '收盘价', 0), 0.0),
                    change_pct=safe_float(getattr(row, '涨跌幅', 0), 0.0)
                ))
            
            self._set_to_cache(cache_key, bills, 'kline')
            logger.info(f"获取 {stock_code} 历史资金流向成功：{len(bills)}条")
            return bills
            
        except Exception as e:
            logger.error(f"获取历史资金流向失败 {stock_code}: {e}")
            return []
    
=======
>>>>>>> 7aaa7cbe85a09d6bf88368f14e12d60640ec9467
    async def get_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
<<<<<<< HEAD
        klt: int = 101,
        fqt: int = 1,
        market_type: Optional[str] = None,
        adjust: Optional[str] = None
    ) -> List[KLineData]:
        """
        获取股票 K 线数据（支持多种周期和复权方式）
        
        Args:
            code: 股票代码或名称，如 '600519' 或 '贵州茅台'
            start_date: 开始日期，格式：YYYY-MM-DD 或 YYYYMMDD，默认 '1900-01-01'
            end_date: 结束日期，格式：YYYY-MM-DD 或 YYYYMMDD，默认 '2050-01-01'
            klt: 时间间隔（秒），默认 101（日线）
                - 1: 分钟
                - 5: 5 分钟
                - 15: 15 分钟
                - 30: 30 分钟
                - 60: 60 分钟
                - 101: 日
                - 102: 周
                - 103: 月
            fqt: 复权方式，默认 1（前复权）
                - 0: 不复权
                - 1: 前复权
                - 2: 后复权
            market_type: 市场类型，可选值：
                - 'A_stock': A 股（默认）
                - 'Hongkong': 港股
                - 'London_stock_exchange': 英股
                - 'US_stock': 美股
            adjust: 兼容旧参数，如果提供则转换为 fqt
                - 'qfq': 前复权 (fqt=1)
                - 'hfq': 后复权 (fqt=2)
                - None: 不复权 (fqt=0)
        
        Returns:
            K 线数据列表
        
        Examples:
            >>> adapter = EFinanceAdapter()
            >>> # 获取日线数据（前复权）
            >>> klines = await adapter.get_kline('600519')
            >>> # 获取周线数据（不复权）
            >>> weekly = await adapter.get_kline('600519', klt=102, fqt=0)
            >>> # 获取 60 分钟 K 线
            >>> hourly = await adapter.get_kline('600519', klt=60)
=======
        adjust: str = "qfq",
        period: str = "daily"
    ) -> List[KLineData]:
        """获取 K 线数据（支持多种周期）
        
        Args:
            code: 股票代码
            start_date: 开始日期，格式：YYYY-MM-DD 或 YYYYMMDD，默认 '1900-01-01'
            end_date: 结束日期，格式：YYYY-MM-DD 或 YYYYMMDD，默认 '2050-01-01'
            adjust: 复权方式，可选：
                - 'qfq': 前复权（默认）
                - 'hfq': 后复权
                - 'no': 不复权
            period: K 线周期，可选：
                - '1m': 1 分钟
                - '5m': 5 分钟
                - '15m': 15 分钟
                - '30m': 30 分钟
                - '60m': 60 分钟
                - 'daily': 日线（默认）
                - 'weekly': 周线
                - 'monthly': 月线
        
        Returns:
            List[KLineData]: K 线数据列表
        
        Examples:
            # 日线
            klines = await adapter.get_kline("600519", period="daily")
            
            # 60 分钟线
            klines = await adapter.get_kline("600519", period="60m")
            
            # 周线
            klines = await adapter.get_kline("600519", period="weekly")
>>>>>>> 7aaa7cbe85a09d6bf88368f14e12d60640ec9467
        """
        try:
            if not EF_AVAILABLE:
                return []
            
<<<<<<< HEAD
            # 兼容旧的 adjust 参数
            if adjust is not None and fqt == 1:
                if adjust == 'qfq':
                    fqt = 1
                elif adjust == 'hfq':
                    fqt = 2
                else:
                    fqt = 0
            
            # 格式化日期
            beg = start_date.replace('-', '') if start_date else '19000101'
            if len(beg) == 8 and '-' not in beg:
                pass  # 已经是 YYYYMMDD 格式
            elif len(beg) == 10:
                beg = beg.replace('-', '')
            
            end = end_date.replace('-', '') if end_date else '20500101'
            if len(end) == 8 and '-' not in end:
                pass
            elif len(end) == 10:
                end = end.replace('-', '')
            
            cache_key = self._get_cache_key('kline', code=code, start=beg, end=end, klt=klt, fqt=fqt)
=======
            # 周期映射（efinance 的 klt 参数）
            period_map = {
                '1m': 1,      # 1 分钟
                '5m': 5,      # 5 分钟
                '15m': 15,    # 15 分钟
                '30m': 30,    # 30 分钟
                '60m': 60,    # 60 分钟
                'daily': 101, # 日线
                'weekly': 102, # 周线
                'monthly': 103 # 月线
            }
            
            if period not in period_map:
                logger.warning(f"未知的周期：{period}，使用默认周期 daily")
                period = 'daily'
            
            klt = period_map[period]
            
            # 复权映射（efinance 的 fqt 参数）
            adjust_map = {
                'qfq': 1,   # 前复权
                'hfq': 2,   # 后复权
                'no': 0,    # 不复权
                '': 0       # 不复权
            }
            
            fqt = adjust_map.get(adjust, 1)  # 默认前复权
            
            cache_key = self._get_cache_key('kline', code=code, start=start_date, end=end_date, adjust=adjust, period=period)
>>>>>>> 7aaa7cbe85a09d6bf88368f14e12d60640ec9467
            cached = self._get_from_cache(cache_key, 'kline')
            if cached:
                self.record_request_success()  # 缓存命中也算成功
                return cached
            
<<<<<<< HEAD
            # 构建参数
            kwargs = {
                'beg': beg,
                'end': end,
                'klt': klt,
                'fqt': fqt,
                'use_id_cache': True
            }
            
            # 处理市场类型
            if market_type:
                try:
                    market_enum = getattr(MarketType, market_type, None)
                    if market_enum:
                        kwargs['market_type'] = market_enum
                except Exception:
                    logger.warning(f"无效的市场类型：{market_type}")
            
            # 获取 K 线数据
            df = ef.stock.get_quote_history(code.zfill(6), **kwargs)
=======
            # 频率控制
            await self._rate_limit()
            
            # 处理日期格式
            if start_date:
                beg = start_date.replace('-', '') if '-' in start_date else start_date
            else:
                beg = '19000101'
            
            if end_date:
                end = end_date.replace('-', '') if '-' in end_date else end_date
            else:
                end = '20500101'
            
            # efinance 直接传股票代码即可，会自动识别市场
            df = ef.stock.get_quote_history(
                code.zfill(6),
                period=klt,
                fqt=fqt,
                beg=beg,
                end=end
            )
>>>>>>> 7aaa7cbe85a09d6bf88368f14e12d60640ec9467
            
            if df.empty:
                logger.warning(f"K 线数据为空：{code} (period={period})")
                self.record_request_success()  # 空数据也算成功（非错误）
                return []
            
            klines = []
            prev_close = None
            for row in df.itertuples(index=False):
                # 获取日期字段
                date_raw = str(getattr(row, '时间', getattr(row, '日期', '')))
                
                if not date_raw or date_raw == '':
                    logger.warning(f"K 线数据日期为空：{code}")
                    continue
                
                # 统一格式为 YYYYMMDD
                if len(date_raw) == 10 and '-' in date_raw:
                    date = date_raw.replace('-', '')
                elif len(date_raw) == 8:
                    date = date_raw
                else:
                    logger.warning(f"K 线数据日期格式异常：{date_raw}")
                    continue
                
                # 安全转换浮点数
                def safe_float(value, default=0.0):
                    try:
                        if value is None or value == '' or value == '-' or (isinstance(value, float) and str(value) == 'nan'):
                            return default
                        return float(value)
                    except (ValueError, TypeError):
                        return default
                
                current_close = safe_float(getattr(row, '收盘', 0), 0.0)
                klines.append(KLineData(
                    code=code,
                    date=date,
                    open=safe_float(getattr(row, '开盘', 0), 0.0),
                    high=safe_float(getattr(row, '最高', 0), 0.0),
                    low=safe_float(getattr(row, '最低', 0), 0.0),
                    close=current_close,
                    volume=safe_float(getattr(row, '成交量', 0), 0.0),
                    amount=safe_float(getattr(row, '成交额', 0), 0.0),
                    turnover_rate=safe_float(getattr(row, '换手率', 0), 0.0),
                    pre_close=prev_close
                ))
                prev_close = current_close
            
            # 按日期排序
            klines.sort(key=lambda x: x.date)
            
            self._set_to_cache(cache_key, klines, 'kline')
<<<<<<< HEAD
            logger.info(f"获取 K 线数据成功 {code}: {len(klines)}条 (klt={klt}, fqt={fqt})")
=======
            self.record_request_success()  # 记录成功
            logger.info(f"获取 K 线数据成功 {code} ({period}): {len(klines)}条")
>>>>>>> 7aaa7cbe85a09d6bf88368f14e12d60640ec9467
            return klines
            
        except Exception as e:
            self.record_request_failure()  # 记录失败
            logger.error(f"获取 K 线数据失败 {code} (period={period}): {e}")
            return []
    
    async def get_multi_kline(
        self,
        stock_codes: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        klt: int = 101,
        fqt: int = 1,
        market_type: Optional[str] = None
    ) -> Dict[str, List[KLineData]]:
        """
        批量获取多只股票的 K 线数据
        
        Args:
            stock_codes: 股票代码列表，如 ['600519', '300750']
            start_date: 开始日期，格式：YYYY-MM-DD 或 YYYYMMDD
            end_date: 结束日期，格式：YYYY-MM-DD 或 YYYYMMDD
            klt: 时间间隔，默认 101（日线）
            fqt: 复权方式，默认 1（前复权）
            market_type: 市场类型
        
        Returns:
            字典，key 为股票代码，value 为 K 线数据列表
        
        Examples:
            >>> adapter = EFinanceAdapter()
            >>> klines = await adapter.get_multi_kline(['600519', '300750'])
            >>> for code, data in klines.items():
            ...     print(f"{code}: {len(data)}条 K 线数据")
        """
        try:
            if not EF_AVAILABLE:
                return {}
            
            if not stock_codes:
                return {}
            
            # 生成缓存 key
            codes_key = '_'.join(sorted(stock_codes))
            cache_key = self._get_cache_key('multi_kline', codes=codes_key, start=start_date, end=end_date, klt=klt, fqt=fqt)
            cached = self._get_from_cache(cache_key, 'kline')
            if cached:
                return cached
            
            # 格式化日期
            beg = start_date.replace('-', '') if start_date else '19000101'
            if len(beg) == 10:
                beg = beg.replace('-', '')
            
            end = end_date.replace('-', '') if end_date else '20500101'
            if len(end) == 10:
                end = end.replace('-', '')
            
            # 构建参数
            kwargs = {
                'beg': beg,
                'end': end,
                'klt': klt,
                'fqt': fqt,
                'use_id_cache': True
            }
            
            # 处理市场类型
            if market_type:
                try:
                    market_enum = getattr(MarketType, market_type, None)
                    if market_enum:
                        kwargs['market_type'] = market_enum
                except Exception:
                    logger.warning(f"无效的市场类型：{market_type}")
            
            # 批量获取 K 线数据
            result_dict = ef.stock.get_quote_history(stock_codes, **kwargs)
            
            if not result_dict:
                return {}
            
            all_klines = {}
            for code, df in result_dict.items():
                if df.empty:
                    all_klines[code] = []
                    continue
                
                klines = []
                prev_close = None
                for row in df.itertuples(index=False):
                    date_raw = str(getattr(row, '时间', getattr(row, '日期', '')))
                    
                    if not date_raw or date_raw == '':
                        continue
                    
                    if len(date_raw) == 10 and '-' in date_raw:
                        date = date_raw.replace('-', '')
                    elif len(date_raw) == 8:
                        date = date_raw
                    else:
                        continue
                    
                    def safe_float(value, default=0.0):
                        try:
                            if value is None or value == '' or value == '-' or (isinstance(value, float) and str(value) == 'nan'):
                                return default
                            return float(value)
                        except (ValueError, TypeError):
                            return default
                    
                    current_close = safe_float(getattr(row, '收盘', 0), 0.0)
                    klines.append(KLineData(
                        code=code,
                        date=date,
                        open=safe_float(getattr(row, '开盘', 0), 0.0),
                        high=safe_float(getattr(row, '最高', 0), 0.0),
                        low=safe_float(getattr(row, '最低', 0), 0.0),
                        close=current_close,
                        volume=safe_float(getattr(row, '成交量', 0), 0.0),
                        amount=safe_float(getattr(row, '成交额', 0), 0.0),
                        turnover_rate=safe_float(getattr(row, '换手率', 0), 0.0),
                        pre_close=prev_close
                    ))
                    prev_close = current_close
                
                klines.sort(key=lambda x: x.date)
                all_klines[code] = klines
            
            self._set_to_cache(cache_key, all_klines, 'kline')
            logger.info(f"批量获取 K 线数据成功：{len(all_klines)}只股票")
            return all_klines
            
        except Exception as e:
            logger.error(f"批量获取 K 线数据失败：{e}")
            return {}
    
    @api_call_cache(ttl=1800)  # 缓存 30 分钟
    async def get_weekly_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fqt: int = 1,
        market_type: Optional[str] = None,
        adjust: Optional[str] = None
    ) -> List[KLineData]:
        """
        获取周 K 线数据（带重试机制）
        
        Args:
            code: 股票代码或名称
            start_date: 开始日期，格式：YYYY-MM-DD 或 YYYYMMDD
            end_date: 结束日期，格式：YYYY-MM-DD 或 YYYYMMDD
            fqt: 复权方式，默认 1（前复权）
                - 0: 不复权
                - 1: 前复权
                - 2: 后复权
            market_type: 市场类型
            adjust: 兼容旧参数
        
        Returns:
            周 K 线数据列表
        """
        # 直接调用优化后的 get_kline 方法
        return await self.get_kline(
            code=code,
            start_date=start_date,
            end_date=end_date,
            klt=102,  # 周线
            fqt=fqt,
            market_type=market_type,
            adjust=adjust
        )
    
    @api_call_cache(ttl=1800)  # 缓存 30 分钟
    async def get_monthly_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fqt: int = 1,
        market_type: Optional[str] = None,
        adjust: Optional[str] = None
    ) -> List[KLineData]:
        """
        获取月 K 线数据（带重试机制）
        
        Args:
            code: 股票代码或名称
            start_date: 开始日期，格式：YYYY-MM-DD 或 YYYYMMDD
            end_date: 结束日期，格式：YYYY-MM-DD 或 YYYYMMDD
            fqt: 复权方式，默认 1（前复权）
                - 0: 不复权
                - 1: 前复权
                - 2: 后复权
            market_type: 市场类型
            adjust: 兼容旧参数
        
        Returns:
            月 K 线数据列表
        """
        # 直接调用优化后的 get_kline 方法
        return await self.get_kline(
            code=code,
            start_date=start_date,
            end_date=end_date,
            klt=103,  # 月线
            fqt=fqt,
            market_type=market_type,
            adjust=adjust
        )
    
    async def get_realtime_quote(self, code: str) -> Dict[str, Any]:
<<<<<<< HEAD
        """
        获取沪深市场股票最新行情快照
        
        Args:
            code: 股票代码，如 '600519'
            
        Returns:
            实时行情数据字典，包含以下字段：
=======
        """获取单只股票实时行情（精准查询，使用 get_quote_snapshot）
        
        Args:
            code: 股票代码
            
        Returns:
            实时行情字典，包含以下字段：
>>>>>>> 7aaa7cbe85a09d6bf88368f14e12d60640ec9467
            - code: 股票代码
            - name: 股票名称
            - price: 最新价
            - change: 涨跌额
            - change_pct: 涨跌幅
<<<<<<< HEAD
            - prev_close: 昨收价
            - open: 今开价
            - high: 最高价
            - low: 最低价
            - volume: 成交量（手）
            - amount: 成交额（元）
            - turnover_rate: 换手率（%）
            - avg_price: 均价
            - limit_up: 涨停价
            - limit_down: 跌停价
            - quote_time: 时间戳
            - bid_prices: 买盘价格列表 [买 1，买 2，买 3，买 4，买 5]
            - ask_prices: 卖盘价格列表 [卖 1，卖 2，卖 3，卖 4，卖 5]
            - bid_volumes: 买盘数量列表 [买 1 量，买 2 量，买 3 量，买 4 量，买 5 量]
            - ask_volumes: 卖盘数量列表 [卖 1 量，卖 2 量，卖 3 量，卖 4 量，卖 5 量]
        
        Examples:
            >>> adapter = EFinanceAdapter()
            >>> quote = await adapter.get_realtime_quote('600519')
            >>> print(f"贵州茅台最新价：{quote['price']}元，涨跌幅：{quote['change_pct']}%")
=======
            - high: 最高价
            - low: 最低价
            - open: 今开
            - prev_close: 昨收
            - volume: 成交量
            - amount: 成交额
            - turnover_rate: 换手率
            - quote_time: 报价时间
            - avg_price: 均价
            - total_market_cap: 总市值
            - float_market_cap: 流通市值
            - pe_ratio: 市盈率
            - pb_ratio: 市净率
            - limit_up: 涨停价
            - limit_down: 跌停价
            - bid_prices: 买盘价格 [买 1, 买 2, 买 3, 买 4, 买 5]
            - ask_prices: 卖盘价格 [卖 1, 卖 2, 卖 3, 卖 4, 卖 5]
            - bid_volumes: 买盘数量 [买 1, 买 2, 买 3, 买 4, 买 5]
            - ask_volumes: 卖盘数量 [卖 1, 卖 2, 卖 3, 卖 4, 卖 5]
            
        Note:
            使用 efinance.stock.get_quote_snapshot 接口
            获取完整的股票行情快照，包含五档买卖盘
            适合精准查询单只股票的最新行情
            缓存时间：60 秒
            
        Examples:
            quote = await adapter.get_realtime_quote("600519")
            print(f"贵州茅台最新价：{quote['price']}")
            print(f"买一价：{quote['bid_prices'][0]}")
            print(f"卖一价：{quote['ask_prices'][0]}")
>>>>>>> 7aaa7cbe85a09d6bf88368f14e12d60640ec9467
        """
        try:
            if not EF_AVAILABLE:
                return {}
            
            cache_key = self._get_cache_key('quote', code=code)
            cached = self._get_from_cache(cache_key, 'quote')
            if cached:
                self.record_request_success()  # 缓存命中也算成功
                return cached
            
            # 频率控制
            await self._rate_limit()
            
            # 获取实时行情快照
            series = ef.stock.get_quote_snapshot(code.zfill(6))
            
            if series is None or len(series) == 0:
                logger.warning(f"实时行情快照为空：{code}")
                self.record_request_success()  # 空数据也算成功（非错误）
                return {}
            
<<<<<<< HEAD
            # 安全转换浮点数
            def safe_float(value, default=0.0):
                try:
                    if value is None or value == '' or value == '-' or (isinstance(value, float) and str(value) == 'nan'):
                        return default
                    return float(value)
                except (ValueError, TypeError):
                    return default
            
            # 安全转换整数
            def safe_int(value, default=0):
                try:
                    if value is None or value == '' or value == '-' or (isinstance(value, float) and str(value) == 'nan'):
                        return default
                    return int(float(value))
                except (ValueError, TypeError):
                    return default
            
            # 获取五档买卖盘数据
            bid_prices = []
            ask_prices = []
            bid_volumes = []
            ask_volumes = []
            
            for i in range(1, 6):
                # 买盘数据
                bid_price = series.get(f'买{i}价', None)
                bid_vol = series.get(f'买{i}数量', None)
                if bid_price is not None:
                    bid_prices.append(safe_float(bid_price, 0.0))
                    bid_volumes.append(safe_int(bid_vol, 0))
                else:
                    bid_prices.append(0.0)
                    bid_volumes.append(0)
                
                # 卖盘数据
                ask_price = series.get(f'卖{i}价', None)
                ask_vol = series.get(f'卖{i}数量', None)
                if ask_price is not None:
                    ask_prices.append(safe_float(ask_price, 0.0))
                    ask_volumes.append(safe_int(ask_vol, 0))
                else:
                    ask_prices.append(0.0)
                    ask_volumes.append(0)
            
=======
            # 安全获取数值
            def safe_float(key, default=0.0):
                val = series.get(key, default)
                if val is None or (isinstance(val, float) and str(val) == 'nan'):
                    return default
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return default
            
            # 构建完整的行情数据
>>>>>>> 7aaa7cbe85a09d6bf88368f14e12d60640ec9467
            quote = {
                # 基本信息
                'code': code,
<<<<<<< HEAD
                'name': series.get('名称', '') or '',
                'price': safe_float(series.get('最新价', 0), 0.0),
                'change': safe_float(series.get('涨跌额', 0), 0.0),
                'change_pct': safe_float(series.get('涨跌幅', 0), 0.0),
                'high': safe_float(series.get('最高', 0), 0.0),
                'low': safe_float(series.get('最低', 0), 0.0),
                'open': safe_float(series.get('今开', 0), 0.0),
                'prev_close': safe_float(series.get('昨收', 0), 0.0),
                'volume': safe_int(series.get('成交量', 0), 0),
                'amount': safe_float(series.get('成交额', 0), 0.0),
                'turnover_rate': safe_float(series.get('换手率', 0), 0.0),
                'avg_price': safe_float(series.get('均价', 0), 0.0),
                'limit_up': safe_float(series.get('涨停价', 0), 0.0),
                'limit_down': safe_float(series.get('跌停价', 0), 0.0),
                'quote_time': series.get('时间', '') or '',
                'bid_prices': bid_prices,  # [买 1, 买 2, 买 3, 买 4, 买 5]
                'ask_prices': ask_prices,  # [卖 1, 卖 2, 卖 3, 卖 4, 卖 5]
                'bid_volumes': bid_volumes,  # [买 1 量，买 2 量，买 3 量，买 4 量，买 5 量]
                'ask_volumes': ask_volumes,  # [卖 1 量，卖 2 量，卖 3 量，卖 4 量，卖 5 量]
                'bid1_price': bid_prices[0] if bid_prices[0] > 0 else None,
                'bid1_volume': bid_volumes[0] if bid_volumes[0] > 0 else None,
                'ask1_price': ask_prices[0] if ask_prices[0] > 0 else None,
                'ask1_volume': ask_volumes[0] if ask_volumes[0] > 0 else None
            }
            
            self._set_to_cache(cache_key, quote, 'quote')
            logger.info(f"获取实时行情成功 {code}: {quote['price']}元 ({quote['change_pct']}%)")
=======
                'name': str(series.get('名称', '') or ''),
                
                # 价格信息
                'price': safe_float('最新价'),
                'change': safe_float('涨跌额'),
                'change_pct': safe_float('涨跌幅'),
                'high': safe_float('最高'),
                'low': safe_float('最低'),
                'open': safe_float('今开'),
                'prev_close': safe_float('昨收'),
                'avg_price': safe_float('均价'),
                
                # 成交信息
                'volume': safe_float('成交量'),
                'amount': safe_float('成交额'),
                'turnover_rate': safe_float('换手率'),
                
                # 估值指标
                'pe_ratio': safe_float('市盈率'),
                'pb_ratio': safe_float('市净率'),
                
                # 市值信息
                'total_market_cap': safe_float('总市值'),
                'float_market_cap': safe_float('流通市值'),
                
                # 涨跌停价格
                'limit_up': safe_float('涨停价'),
                'limit_down': safe_float('跌停价'),
                
                # 时间信息
                'quote_time': str(series.get('时间', '') or ''),
                
                # 五档买卖盘
                'bid_prices': [
                    safe_float('买 1 价', 0),
                    safe_float('买 2 价', 0),
                    safe_float('买 3 价', 0),
                    safe_float('买 4 价', 0),
                    safe_float('买 5 价', 0)
                ],
                'ask_prices': [
                    safe_float('卖 1 价', 0),
                    safe_float('卖 2 价', 0),
                    safe_float('卖 3 价', 0),
                    safe_float('卖 4 价', 0),
                    safe_float('卖 5 价', 0)
                ],
                'bid_volumes': [
                    safe_float('买 1 数量', 0),
                    safe_float('买 2 数量', 0),
                    safe_float('买 3 数量', 0),
                    safe_float('买 4 数量', 0),
                    safe_float('买 5 数量', 0)
                ],
                'ask_volumes': [
                    safe_float('卖 1 数量', 0),
                    safe_float('卖 2 数量', 0),
                    safe_float('卖 3 数量', 0),
                    safe_float('卖 4 数量', 0),
                    safe_float('卖 5 数量', 0)
                ]
            }
            
            self._set_to_cache(cache_key, quote, 'quote')
            self.record_request_success()  # 记录成功
            logger.info(f"获取实时行情快照成功 {code}: {quote['price']}")
>>>>>>> 7aaa7cbe85a09d6bf88368f14e12d60640ec9467
            return quote
            
        except Exception as e:
            self.record_request_failure()  # 记录失败
            logger.error(f"获取实时行情快照失败 {code}: {e}")
            return {}
    
<<<<<<< HEAD
    async def get_latest_quote(self, stock_codes: List[str]) -> List[Dict[str, Any]]:
        """
        获取沪深市场多只股票的实时涨幅情况
        
        Args:
            stock_codes: 股票代码列表，如 ['600519', '300750']
            
        Returns:
            多只股票的实时行情数据列表
        
        Examples:
            >>> adapter = EFinanceAdapter()
            >>> quotes = await adapter.get_latest_quote(['600519', '300750'])
            >>> for quote in quotes:
            ...     print(f"{quote['name']}: {quote['price']}元 ({quote['change_pct']}%)")
=======
    async def get_latest_quote(self, codes: Union[str, List[str]]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """获取股票最新行情（支持批量精准查询）
        
        Args:
            codes: 股票代码或股票代码列表
                - 单只股票：'601012'
                - 多只股票：['601012', '300274', '002594']
            
        Returns:
            Dict 或 List[Dict]：
                - 单只股票：返回单个字典
                - 多只股票：返回字典列表
                
        Note:
            使用 efinance.stock.get_latest_quote 接口（或 get_quote 别名）
            适合精准查询指定股票的最新行情
            与 get_realtime_quote 的区别：
                - get_realtime_quote: 单只股票，使用 get_quote_snapshot
                - get_latest_quote: 支持批量，使用 get_latest_quote/get_quote
            
            缓存时间：60 秒
            
        Examples:
            # 单只股票
            quote = await adapter.get_latest_quote("601012")
            
            # 多只股票
            quotes = await adapter.get_latest_quote(["601012", "300274", "002594"])
        """
        try:
            if not EF_AVAILABLE:
                return {} if isinstance(codes, str) else []
            
            # 统一转换为列表处理
            if isinstance(codes, str):
                code_list = [codes]
                is_single = True
            else:
                code_list = codes
                is_single = False
            
            # 构建缓存 key
            cache_key = self._get_cache_key('latest_quote', codes=','.join(sorted(code_list)))
            cached = self._get_from_cache(cache_key, 'quote')
            if cached:
                self.record_request_success()  # 缓存命中也算成功
                return cached[0] if is_single else cached
            
            # 频率控制
            await self._rate_limit()
            
            # 调用 efinance API
            # 注意：get_latest_quote 和 get_quote 是别名，功能完全一致
            try:
                df = ef.stock.get_latest_quote([c.zfill(6) for c in code_list])
            except AttributeError:
                # 某些版本可能是 get_quote
                df = ef.stock.get_quote([c.zfill(6) for c in code_list])
            
            if df is None or df.empty:
                logger.warning(f"efinance 返回空数据：{code_list}")
                self.record_request_failure()  # 空数据视为失败
                return {} if is_single else []
            
            quotes = []
            for row in df.itertuples(index=False):
                # 安全转换浮点数
                def safe_float(key, default=0.0):
                    val = getattr(row, key, default)
                    if val is None or (isinstance(val, float) and str(val) == 'nan'):
                        return default
                    try:
                        return float(val)
                    except (ValueError, TypeError):
                        return default
                
                quote = {
                    'code': str(getattr(row, '股票代码', '')),
                    'name': str(getattr(row, '股票名称', '')),
                    'price': safe_float('最新价'),
                    'change': safe_float('涨跌额'),
                    'change_pct': safe_float('涨跌幅'),
                    'high': safe_float('最高价'),
                    'low': safe_float('最低价'),
                    'open': safe_float('今开'),
                    'prev_close': safe_float('昨收'),
                    'volume': safe_float('成交量'),
                    'amount': safe_float('成交额'),
                    'turnover_rate': safe_float('换手率'),
                    'pe_ratio': safe_float('市盈率 (动)'),
                    'pb_ratio': safe_float('市净率'),
                    'total_market_cap': safe_float('总市值'),
                    'float_market_cap': safe_float('流通市值')
                }
                quotes.append(quote)
            
            self._set_to_cache(cache_key, quotes, 'quote')
            self.record_request_success()  # 记录成功
            
            if is_single:
                logger.debug(f"获取最新行情成功 {code_list[0]}: {quotes[0]['price']}")
                return quotes[0]
            else:
                logger.info(f"获取最新行情成功：{len(quotes)}只股票")
                return quotes
                
        except Exception as e:
            self.record_request_failure()  # 记录失败
            logger.error(f"获取最新行情失败 {codes}: {e}")
            return {} if isinstance(codes, str) else []
    
    async def get_deal_detail(self, code: str, max_count: int = 1000000) -> List[Dict[str, Any]]:
        """获取股票最新交易日成交明细
        
        Args:
            code: 股票代码
            max_count: 最近的最大数据条数，默认 1000000
            
        Returns:
            成交明细列表，每个包含：
            - time: 时间
            - price: 成交价
            - volume: 成交量
            - amount: 成交额
            - order_type: 单数
            
        Note:
            使用 efinance.stock.get_deal_detail 接口
            获取最新交易日的逐笔成交明细
>>>>>>> 7aaa7cbe85a09d6bf88368f14e12d60640ec9467
        """
        try:
            if not EF_AVAILABLE:
                return []
            
<<<<<<< HEAD
            if not stock_codes:
                return []
            
            # 生成缓存 key
            codes_key = '_'.join(sorted(stock_codes))
            cache_key = self._get_cache_key('latest_quote', codes=codes_key)
=======
            cache_key = self._get_cache_key('deal_detail', code=code)
>>>>>>> 7aaa7cbe85a09d6bf88368f14e12d60640ec9467
            cached = self._get_from_cache(cache_key, 'quote')
            if cached:
                return cached
            
<<<<<<< HEAD
            # 批量获取实时行情
            df = ef.stock.get_latest_quote(stock_codes)
=======
            # 频率控制
            await self._rate_limit()
            
            # 获取成交明细
            df = ef.stock.get_deal_detail(code.zfill(6), max_count=max_count)
>>>>>>> 7aaa7cbe85a09d6bf88368f14e12d60640ec9467
            
            if df.empty:
                return []
            
<<<<<<< HEAD
            quotes = []
            for row in df.itertuples(index=False):
                # 安全转换数值
                def safe_float(value, default=0.0):
                    try:
                        if value is None or value == '' or value == '-' or (isinstance(value, float) and str(value) == 'nan'):
                            return default
                        return float(value)
                    except (ValueError, TypeError):
                        return default
                
                code = str(getattr(row, '代码', '')).zfill(6)
                if not code:
                    continue
                
                quotes.append({
                    'code': code,
                    'name': getattr(row, '名称', '') or '',
                    'change_pct': safe_float(getattr(row, '涨跌幅', 0), 0.0),
                    'price': safe_float(getattr(row, '最新价', 0), 0.0),
                    'high': safe_float(getattr(row, '最高', 0), 0.0),
                    'low': safe_float(getattr(row, '最低', 0), 0.0),
                    'open': safe_float(getattr(row, '今开', 0), 0.0),
                    'change': safe_float(getattr(row, '涨跌额', 0), 0.0),
                    'turnover_rate': safe_float(getattr(row, '换手率', 0), 0.0),
                    'volume_ratio': safe_float(getattr(row, '量比', 0), 0.0),
                    'pe_ratio_dynamic': safe_float(getattr(row, '动态市盈率', 0), 0.0),
                    'volume': safe_float(getattr(row, '成交量', 0), 0.0),
                    'amount': safe_float(getattr(row, '成交额', 0), 0.0),
                    'prev_close': safe_float(getattr(row, '昨日收盘', 0), 0.0),
                    'total_market_cap': safe_float(getattr(row, '总市值', 0), 0.0),
                    'float_market_cap': safe_float(getattr(row, '流通市值', 0), 0.0),
                    'market_type': getattr(row, '市场类型', '') or '',
                    'quote_id': getattr(row, '行情 ID', '') or ''
                })
            
            self._set_to_cache(cache_key, quotes, 'quote')
            logger.info(f"批量获取实时行情成功：{len(quotes)}只")
            return quotes
            
        except Exception as e:
            logger.error(f"批量获取实时行情失败：{e}")
=======
            deals = []
            for row in df.itertuples(index=False):
                time_str = str(getattr(row, '时间', ''))
                
                deals.append({
                    'code': code.zfill(6),
                    'name': str(getattr(row, '股票名称', '')),
                    'prev_close': float(getattr(row, '昨收', 0) or 0),
                    'time': time_str,
                    'price': float(getattr(row, '成交价', 0) or 0),
                    'volume': int(getattr(row, '成交量', 0) or 0),
                    'order_type': int(getattr(row, '单数', 0) or 0)
                })
            
            self._set_to_cache(cache_key, deals, 'quote')
            logger.info(f"获取成交明细成功 {code}: {len(deals)}条")
            return deals
            
        except Exception as e:
            logger.error(f"获取成交明细失败 {code}: {e}")
            return []
    
    async def get_history_bill(self, code: str) -> List[Dict[str, Any]]:
        """获取股票历史资金流向数据
        
        Args:
            code: 股票代码
            
        Returns:
            历史资金流向列表，每个包含：
            - date: 日期
            - main_net_amount: 主力净流入
            - sm_net_amount: 小单净流入
            - md_net_amount: 中单净流入
            - lg_net_amount: 大单净流入
            - elg_net_amount: 超大单净流入
            - main_net_ratio: 主力净流入占比
            - close_price: 收盘价
            - change_pct: 涨跌幅
            
        Note:
            使用 efinance.stock.get_history_bill 接口
            获取股票历史的每日资金流向数据
        """
        try:
            if not EF_AVAILABLE:
                return []
            
            cache_key = self._get_cache_key('history_bill', code=code)
            cached = self._get_from_cache(cache_key, 'bill')
            if cached:
                return cached
            
            # 频率控制
            await self._rate_limit()
            
            # 获取历史资金流向
            df = ef.stock.get_history_bill(code.zfill(6))
            
            if df.empty:
                return []
            
            bills = []
            for row in df.itertuples(index=False):
                date_raw = str(getattr(row, '日期', ''))
                if len(date_raw) >= 10:
                    date = date_raw[:10].replace('-', '')
                else:
                    date = date_raw
                
                # 安全获取数值
                def safe_get(key, default=0.0):
                    val = getattr(row, key, default)
                    if val is None or (isinstance(val, float) and str(val) == 'nan'):
                        return default
                    try:
                        return float(val)
                    except (ValueError, TypeError):
                        return default
                
                bills.append({
                    'code': code.zfill(6),
                    'name': str(getattr(row, '股票名称', '')),
                    'date': date,
                    'main_net_amount': safe_get('主力净流入'),
                    'sm_net_amount': safe_get('小单净流入'),
                    'md_net_amount': safe_get('中单净流入'),
                    'lg_net_amount': safe_get('大单净流入'),
                    'elg_net_amount': safe_get('超大单净流入'),
                    'main_net_ratio': safe_get('主力净流入占比'),
                    'sm_net_ratio': safe_get('小单流入净占比'),
                    'md_net_ratio': safe_get('中单流入净占比'),
                    'lg_net_ratio': safe_get('大单流入净占比'),
                    'elg_net_ratio': safe_get('超大单流入净占比'),
                    'close_price': safe_get('收盘价'),
                    'change_pct': safe_get('涨跌幅')
                })
            
            # 按日期倒序排列（最新的在前）
            bills.sort(key=lambda x: x['date'], reverse=True)
            
            self._set_to_cache(cache_key, bills, 'bill')
            logger.info(f"获取历史资金流向成功 {code}: {len(bills)}条")
            return bills
            
        except Exception as e:
            logger.error(f"获取历史资金流向失败 {code}: {e}")
>>>>>>> 7aaa7cbe85a09d6bf88368f14e12d60640ec9467
            return []
    
    async def get_sector_list(self, sector_type: str = "industry") -> List[SectorInfo]:
        """获取板块列表"""
        try:
            if not EF_AVAILABLE:
                return []
            
            # 获取行业板块或概念板块
            if sector_type == "industry":
                fs = '行业板块'
            else:
                fs = '概念板块'
            
            df = ef.stock.get_realtime_quotes(fs)
            
            sectors = []
            for row in df.itertuples(index=False):
                code = str(getattr(row, '股票代码', ''))
                name = getattr(row, '股票名称', '')
                if code and name:
                    sectors.append(SectorInfo(
                        code=code,
                        name=name,
                        sector_type=sector_type
                    ))
            
            logger.info(f"获取板块列表成功：{len(sectors)}个")
            return sectors
            
        except Exception as e:
            logger.error(f"获取板块列表失败：{e}")
            return []
    
    async def get_sector_components(self, sector_code: str) -> List[str]:
        """获取板块成分股"""
        try:
            if not EF_AVAILABLE:
                return []
            
            # 使用 get_belong_board 反向查询成分股
            # efinance 没有直接的板块成分股接口，这里返回空列表
            logger.warning(f"efinance 暂不支持获取板块成分股 {sector_code}")
            return []
            
        except Exception as e:
            logger.error(f"获取板块成分股失败 {sector_code}: {e}")
            return []
    
    async def get_chip_data(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[ChipData]:
        """获取筹码数据"""
        try:
            if not EF_AVAILABLE:
                return []
            
            # 获取全市场股东人数数据，然后筛选指定股票
            df = ef.stock.get_latest_holder_number()
            
            if df.empty:
                return []
            
            # 筛选指定股票
            stock_df = df[df['股票代码'] == code.zfill(6)]
            
            chip_data = []
            for row in stock_df.itertuples(index=False):
                date = str(getattr(row, '公告日期', ''))
                if len(date) >= 10:
                    date = date[:10].replace('-', '')
                
                if start_date and date < start_date.replace('-', ''):
                    continue
                if end_date and date > end_date.replace('-', ''):
                    continue
                
                chip_data.append(ChipData(
                    code=code,
                    date=date,
                    shareholder_count=float(getattr(row, '股东人数', 0) or 0)
                ))
            
            # 按日期排序
            chip_data.sort(key=lambda x: x.date)
            
            logger.info(f"获取筹码数据成功 {code}: {len(chip_data)}条")
            return chip_data
            
        except Exception as e:
            logger.error(f"获取筹码数据失败 {code}: {e}")
            return []
    
    async def get_daily_billboard(
<<<<<<< HEAD
        self, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> List[BillboardEntry]:
        """
        获取指定日期区间的龙虎榜详情数据
        
        Args:
            start_date: 开始日期，格式：YYYY-MM-DD
                - None: 最新一个榜单公开日（默认）
                - "2021-08-27": 2021 年 8 月 27 日
            
            end_date: 结束日期，格式：YYYY-MM-DD
                - None: 最新一个榜单公开日（默认）
                - "2021-08-31": 2021 年 8 月 31 日
            
        Returns:
            龙虎榜详情数据列表
        
        Examples:
            >>> adapter = EFinanceAdapter()
            >>> # 获取最新龙虎榜
            >>> latest = await adapter.get_daily_billboard()
            >>> # 获取指定日期区间
            >>> bills = await adapter.get_daily_billboard('2021-08-20', '2021-08-27')
=======
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[BillboardEntry]:
        """获取龙虎榜单数据
        
        Args:
            start_date: 开始日期，格式：YYYY-MM-DD，默认最新一个榜单日
            end_date: 结束日期，格式：YYYY-MM-DD，默认最新一个榜单日
            
        Returns:
            龙虎榜单数据列表
            
        Note:
            使用 efinance.stock.get_daily_billboard 接口
            支持获取单个日期或日期区间的龙虎榜数据
>>>>>>> 7aaa7cbe85a09d6bf88368f14e12d60640ec9467
        """
        try:
            if not EF_AVAILABLE:
                return []
            
<<<<<<< HEAD
            # 生成缓存 key
            date_key = f"{start_date or 'latest'}_{end_date or 'latest'}"
            cache_key = self._get_cache_key('billboard', date=date_key)
=======
            cache_key = self._get_cache_key('billboard', start=start_date, end=end_date)
>>>>>>> 7aaa7cbe85a09d6bf88368f14e12d60640ec9467
            cached = self._get_from_cache(cache_key, 'default')
            if cached:
                return cached
            
<<<<<<< HEAD
            # 获取龙虎榜数据（支持日期范围）
            df = ef.stock.get_daily_billboard(start_date, end_date)
=======
            # 频率控制
            await self._rate_limit()
            
            # 获取龙虎榜数据（支持日期区间）
            df = ef.stock.get_daily_billboard(start_date=start_date, end_date=end_date)
>>>>>>> 7aaa7cbe85a09d6bf88368f14e12d60640ec9467
            
            if df.empty:
                return []
            
            entries = []
            for row in df.itertuples(index=False):
                code = str(getattr(row, '股票代码', ''))
                if not code:
                    continue
                
<<<<<<< HEAD
                # 安全转换浮点数
                def safe_float(value, default=0.0):
                    try:
                        if value is None or value == '' or value == '-' or (isinstance(value, float) and str(value) == 'nan'):
                            return default
                        return float(value)
                    except (ValueError, TypeError):
                        return default
                
                code_padded = code.zfill(6)
                trade_date = str(getattr(row, '上榜日期', '') or '')
                
                entries.append(BillboardEntry(
                    code=code_padded,
                    name=getattr(row, '股票名称', '') or '',
                    close_price=safe_float(getattr(row, '收盘价', 0), 0.0),
                    change_pct=safe_float(getattr(row, '涨跌幅', 0), 0.0),
                    turnover_rate=safe_float(getattr(row, '换手率', 0), 0.0),
                    turnover_amount=safe_float(getattr(row, '市场总成交额', 0), 0.0),
                    net_amount=safe_float(getattr(row, '龙虎榜净买额', 0), 0.0),
                    buy_amount=safe_float(getattr(row, '龙虎榜买入额', 0), 0.0),
                    sell_amount=safe_float(getattr(row, '龙虎榜卖出额', 0), 0.0),
                    total_amount=safe_float(getattr(row, '龙虎榜成交额', 0), 0.0),
                    net_ratio=safe_float(getattr(row, '净买额占总成交比', 0), 0.0),
                    amount_ratio=safe_float(getattr(row, '成交额占总成交比', 0), 0.0),
                    float_market_cap=safe_float(getattr(row, '流通市值', 0), 0.0),
                    reason=getattr(row, '上榜原因', '') or '',
                    trade_date=trade_date,
                    interpretation=getattr(row, '解读', '') or ''  # 如：卖一主卖，成功率 48.36%
                ))
            
            self._set_to_cache(cache_key, entries, 'default')
            date_range = f"{start_date} 至 {end_date}" if start_date and end_date else "最新"
            logger.info(f"获取龙虎榜数据成功（{date_range}）：{len(entries)}条")
=======
                # 安全获取数值
                def safe_get(key, default=0.0):
                    val = getattr(row, key, default)
                    if val is None or (isinstance(val, float) and str(val) == 'nan'):
                        return default
                    try:
                        return float(val)
                    except (ValueError, TypeError):
                        return default
                
                trade_date_raw = str(getattr(row, '上榜日期', ''))
                if len(trade_date_raw) >= 10:
                    trade_date_raw = trade_date_raw[:10].replace('-', '')
                
                entries.append(BillboardEntry(
                    code=code.zfill(6),
                    name=getattr(row, '股票名称', ''),
                    close_price=safe_get('收盘价'),
                    change_pct=safe_get('涨跌幅'),
                    turnover_amount=safe_get('成交额'),
                    net_amount=safe_get('龙虎榜净买额'),
                    buy_amount=safe_get('龙虎榜买入额'),
                    sell_amount=safe_get('龙虎榜卖出额'),
                    reason=getattr(row, '上榜原因', ''),
                    trade_date=trade_date_raw
                ))
            
            self._set_to_cache(cache_key, entries, 'default')
            logger.info(f"获取龙虎榜数据成功（{start_date or '最新'} 至 {end_date or '最新'}）：{len(entries)}条")
>>>>>>> 7aaa7cbe85a09d6bf88368f14e12d60640ec9467
            return entries
            
        except Exception as e:
            logger.error(f"获取龙虎榜数据失败：{e}")
            return []
    
    async def get_belong_board(self, code: str) -> List[BoardInfo]:
        """
        获取股票所属板块
        
        Args:
            code: 股票代码
            
        Returns:
<<<<<<< HEAD
            所属板块列表，包含行业板块、概念板块、地域板块、指数板块等
        
        Examples:
            >>> adapter = EFinanceAdapter()
            >>> boards = await adapter.get_belong_board('600519')
            >>> for board in boards:
            ...     print(f"{board.name} - {board.board_type} - {board.change_pct}%")
=======
            所属板块列表
            
        Note:
            使用 efinance.stock.get_belong_board 接口
            返回行业板块、概念板块、地域板块、指数板块等
>>>>>>> 7aaa7cbe85a09d6bf88368f14e12d60640ec9467
        """
        try:
            if not EF_AVAILABLE:
                return []
            
            cache_key = self._get_cache_key('board', code=code)
            cached = self._get_from_cache(cache_key, 'stock_info')
            if cached:
                return cached
            
            # 频率控制
            await self._rate_limit()
            
            # 获取股票所属板块
            df = ef.stock.get_belong_board(code.zfill(6))
            
            if df.empty:
                return []
            
            boards = []
            for row in df.itertuples(index=False):
<<<<<<< HEAD
                # 获取板块类型
                board_type_raw = getattr(row, '板块类型', '')
                if board_type_raw == '1':
                    board_type_name = '行业板块'
                elif board_type_raw == '2':
                    board_type_name = '概念板块'
                elif board_type_raw == '3':
                    board_type_name = '地域板块'
                else:
                    board_type_name = '其他'
=======
                board_code = str(getattr(row, '板块代码', ''))
                board_name = str(getattr(row, '板块名称', ''))
                board_change = float(getattr(row, '板块涨幅', 0) or 0)
                
                # 根据板块代码判断板块类型
                board_type_name = self._classify_board_type(board_code, board_name)
>>>>>>> 7aaa7cbe85a09d6bf88368f14e12d60640ec9467
                
                board_code = str(getattr(row, '板块代码', '')).zfill(6)
                
                boards.append(BoardInfo(
<<<<<<< HEAD
                    code=board_code,
                    name=getattr(row, '板块名称', ''),
                    board_type=board_type_name,
                    board_code=board_code,
                    close_price=float(getattr(row, '板块价格', 0) or 0),
                    change_pct=float(getattr(row, '板块涨幅', 0) or 0),
                    stock_name=getattr(row, '股票名称', ''),
                    stock_code=str(getattr(row, '股票代码', '')).zfill(6)
=======
                    code=board_code.zfill(6) if len(board_code) < 6 else board_code,
                    name=board_name,
                    board_type=board_type_name,
                    close_price=0.0,  # get_belong_board 不返回板块价格
                    change_pct=board_change
>>>>>>> 7aaa7cbe85a09d6bf88368f14e12d60640ec9467
                ))
            
            self._set_to_cache(cache_key, boards, 'stock_info')
            logger.info(f"获取股票 {code} 所属板块成功：{len(boards)}个")
            return boards
            
        except Exception as e:
            logger.error(f"获取股票所属板块失败 {code}: {e}")
            return []
    
<<<<<<< HEAD
    async def get_members(self, index_code: str) -> List[IndexMember]:
        """
        获取指数成分股信息
        
        Args:
            index_code: 指数名称或指数代码，如 '000300' 或 '沪深 300'
            
        Returns:
            指数成分股列表
=======
    def _classify_board_type(self, board_code: str, board_name: str) -> str:
        """根据板块代码和名称判断板块类型
        
        Args:
            board_code: 板块代码
            board_name: 板块名称
            
        Returns:
            板块类型名称
        """
        # 行业板块：BK04xx
        if board_code.startswith('BK04'):
            return '行业板块'
        # 概念板块：BK05xx, BK09xx, BK10xx
        elif board_code.startswith('BK05') or board_code.startswith('BK09') or board_code.startswith('BK10'):
            return '概念板块'
        # 地域板块：BK01xx
        elif board_code.startswith('BK01'):
            return '地域板块'
        # 指数板块：BK06xx, BK07xx, BK08xx
        elif board_code.startswith('BK06') or board_code.startswith('BK07') or board_code.startswith('BK08'):
            return '指数板块'
        # 其他
        else:
            return '其他'
    
    async def get_members(self, index_code: str) -> List[IndexComponent]:
        """获取指数成分股
        
        Args:
            index_code: 指数代码或指数名称
                - 指数代码：'000300'（沪深 300）、'000016'（上证 50）
                - 指数名称：'沪深 300'、'中证白酒'
            
        Returns:
            指数成分股列表，包含：
            - index_code: 指数代码
            - index_name: 指数名称
            - code: 股票代码
            - name: 股票名称
            - weight: 股票权重（%）
            
        Note:
            使用 efinance.stock.get_members 接口
            支持通过指数代码或指数名称查询
            
        Examples:
            # 获取沪深 300 成分股
            components = await adapter.get_members("000300")
            
            # 获取中证白酒成分股
            components = await adapter.get_members("中证白酒")
>>>>>>> 7aaa7cbe85a09d6bf88368f14e12d60640ec9467
        """
        try:
            if not EF_AVAILABLE:
                return []
            
            cache_key = self._get_cache_key('members', code=index_code)
            cached = self._get_from_cache(cache_key, 'stock_list')
            if cached:
                return cached
            
            # 频率控制
            await self._rate_limit()
            
            # 获取指数成分股
            df = ef.stock.get_members(index_code)
            
            if df.empty:
                return []
            
            members = []
            for row in df.itertuples(index=False):
<<<<<<< HEAD
                # 安全转换浮点数
                def safe_float(value, default=0.0):
                    try:
                        if value is None or value == '' or value == '-' or (isinstance(value, float) and str(value) == 'nan'):
                            return default
                        return float(value)
                    except (ValueError, TypeError):
                        return default
                
                stock_code = str(getattr(row, '股票代码', '')).zfill(6)
                if not stock_code:
=======
                weight_val = getattr(row, '股票权重', None)
                try:
                    weight = float(weight_val) if weight_val is not None and weight_val != '' else None
                except (ValueError, TypeError):
                    weight = None
                
                components.append(IndexComponent(
                    index_code=str(getattr(row, '指数代码', '')),
                    index_name=str(getattr(row, '指数名称', '')),
                    code=str(getattr(row, '股票代码', '')).zfill(6),
                    name=str(getattr(row, '股票名称', '')),
                    weight=weight
                ))
            
            self._set_to_cache(cache_key, components, 'sector')
            logger.info(f"获取 {index_code} 成分股成功：{len(components)}只")
            return components
            
        except Exception as e:
            logger.error(f"获取指数成分股失败 {index_code}: {e}")
            return []
            
            if df.empty:
                return []
            
            components = []
            for row in df.itertuples(index=False):
                code = str(getattr(row, '股票代码', ''))
                if not code:
>>>>>>> 7aaa7cbe85a09d6bf88368f14e12d60640ec9467
                    continue
                
                members.append(IndexMember(
                    index_code=str(getattr(row, '指数代码', '')).zfill(6),
                    index_name=getattr(row, '指数名称', '') or '',
                    stock_code=stock_code,
                    stock_name=getattr(row, '股票名称', '') or '',
                    weight=safe_float(getattr(row, '股票权重', None), None)
                ))
            
            self._set_to_cache(cache_key, members, 'stock_list')
            logger.info(f"获取指数 {index_code} 成分股成功：{len(members)}只")
            return members
            
        except Exception as e:
            logger.error(f"获取指数成分股失败 {index_code}: {e}")
            return []
    
    async def get_today_bill(self, trade_date: Optional[str] = None) -> List[CapitalFlowItem]:
        """获取当日资金流向
        
        Args:
            trade_date: 交易日期，格式：YYYY-MM-DD，默认今日
            
        Returns:
            资金流向数据列表
        """
        try:
            if not EF_AVAILABLE:
                return []
            
            cache_key = self._get_cache_key('today_bill', date=trade_date)
            cached = self._get_from_cache(cache_key, 'quote')
            if cached:
                return cached
            
            # 频率控制
            await self._rate_limit()
            
            # 获取当日资金流向
            df = ef.stock.get_today_bill(trade_date)
            
            if df.empty:
                return []
            
            flows = []
            for row in df.itertuples(index=False):
                code = str(getattr(row, '股票代码', ''))
                if not code:
                    continue
                
                flows.append(CapitalFlowItem(
                    code=code.zfill(6),
                    name=getattr(row, '股票名称', ''),
                    close_price=float(getattr(row, '最新价', 0) or 0),
                    change_pct=float(getattr(row, '涨跌幅', 0) or 0),
                    main_net_amount=float(getattr(row, '主力净流入', 0) or 0),
                    main_net_amount_rate=float(getattr(row, '主力净流入率', 0) or 0),
                    buy_elg_amount=float(getattr(row, '超大单净流入', 0) or 0),
                    buy_lg_amount=float(getattr(row, '大单净流入', 0) or 0),
                    buy_md_amount=float(getattr(row, '中单净流入', 0) or 0),
                    buy_sm_amount=float(getattr(row, '小单净流入', 0) or 0),
                    trade_date=trade_date or ''
                ))
            
            self._set_to_cache(cache_key, flows, 'quote')
            logger.info(f"获取当日资金流向成功：{len(flows)}条")
            return flows
            
        except Exception as e:
            self.record_request_failure()  # 记录失败
            logger.error(f"获取当日资金流向失败：{e}")
            return []
    
    async def get_stock_bill_detail(self, code: str) -> List[Dict[str, Any]]:
        """获取单只股票最新交易日的日内分钟级单子流入流出数据
        
        Args:
            code: 股票代码
            
        Returns:
            资金流向明细列表，每个元素包含：
            - code: 股票代码
            - time: 时间（格式：YYYY-MM-DD HH:MM）
            - main_net_amount: 主力净流入（元）
            - sm_net_amount: 小单净流入（元）
            - md_net_amount: 中单净流入（元）
            - lg_net_amount: 大单净流入（元）
            - elg_net_amount: 超大单净流入（元）
            
        Note:
            使用 efinance.stock.get_today_bill 接口
            获取单只股票最新交易日的分钟级资金流向数据
            缓存时间：60 秒
            
        Examples:
            # 获取贵州茅台资金流向明细
            bill_detail = await adapter.get_stock_bill_detail("600519")
            
            # 查看最新一分钟数据
            if bill_detail:
                latest = bill_detail[-1]
                print(f"时间：{latest['time']}")
                print(f"主力净流入：{latest['main_net_amount']}元")
                print(f"超大单净流入：{latest['elg_net_amount']}元")
        """
        try:
            if not EF_AVAILABLE:
                return []
            
            cache_key = self._get_cache_key('bill_detail', code=code)
            cached = self._get_from_cache(cache_key, 'quote')
            if cached:
                self.record_request_success()  # 缓存命中也算成功
                return cached
            
            # 频率控制
            await self._rate_limit()
            
            # 获取单只股票资金流向明细
            df = ef.stock.get_today_bill(code.zfill(6))
            
            if df.empty:
                logger.warning(f"股票资金流向明细为空：{code}")
                self.record_request_success()  # 空数据也算成功（非错误）
                return []
            
            bill_details = []
            for row in df.itertuples(index=False):
                # 获取时间字段
                time_raw = str(getattr(row, '时间', ''))
                
                # 构建数据
                detail = {
                    'code': code,
                    'time': time_raw,
                    'main_net_amount': float(getattr(row, '主力净流入', 0) or 0),
                    'sm_net_amount': float(getattr(row, '小单净流入', 0) or 0),
                    'md_net_amount': float(getattr(row, '中单净流入', 0) or 0),
                    'lg_net_amount': float(getattr(row, '大单净流入', 0) or 0),
                    'elg_net_amount': float(getattr(row, '超大单净流入', 0) or 0)
                }
                bill_details.append(detail)
            
            self._set_to_cache(cache_key, bill_details, 'quote')
            self.record_request_success()  # 记录成功
            logger.info(f"获取股票资金流向明细成功 {code}: {len(bill_details)}条")
            return bill_details
            
        except Exception as e:
            self.record_request_failure()  # 记录失败
            logger.error(f"获取股票资金流向明细失败 {code}: {e}")
            return []
    
    async def get_history_bill(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[CapitalFlowItem]:
        """获取历史资金流向
        
        Args:
            code: 股票代码
            start_date: 开始日期，格式：YYYY-MM-DD
            end_date: 结束日期，格式：YYYY-MM-DD
            
        Returns:
            历史资金流向数据列表
        """
        try:
            if not EF_AVAILABLE:
                return []
            
            cache_key = self._get_cache_key('history_bill', code=code, start=start_date, end=end_date)
            cached = self._get_from_cache(cache_key, 'kline')
            if cached:
                return cached
            
            # 获取历史资金流向 - efinance 只接受股票代码
            df = ef.stock.get_history_bill(code.zfill(6))
            
            if df.empty:
                return []
            
            flows = []
            for row in df.itertuples(index=False):
                date = str(getattr(row, '时间', ''))
                if len(date) == 10:
                    date = date.replace('-', '')
                
                # 根据日期范围筛选
                if start_date and date < start_date.replace('-', ''):
                    continue
                if end_date and date > end_date.replace('-', ''):
                    continue
                
                flows.append(CapitalFlowItem(
                    code=code,
                    name='',
                    close_price=float(getattr(row, '最新价', 0) or 0),
                    change_pct=float(getattr(row, '涨跌幅', 0) or 0),
                    main_net_amount=float(getattr(row, '主力净流入', 0) or 0),
                    main_net_amount_rate=float(getattr(row, '主力净流入率', 0) or 0),
                    buy_elg_amount=float(getattr(row, '超大单净流入', 0) or 0),
                    buy_lg_amount=float(getattr(row, '大单净流入', 0) or 0),
                    buy_md_amount=float(getattr(row, '中单净流入', 0) or 0),
                    buy_sm_amount=float(getattr(row, '小单净流入', 0) or 0),
                    trade_date=date
                ))
            
            # 按日期排序
            flows.sort(key=lambda x: x.trade_date)
            
            self._set_to_cache(cache_key, flows, 'kline')
            logger.info(f"获取 {code} 历史资金流向成功：{len(flows)}条")
            return flows
            
        except Exception as e:
            logger.error(f"获取历史资金流向失败 {code}: {e}")
            return []
    
    async def get_top10_stock_holder_info(
        self, 
        code: str, 
        top: int = 4
    ) -> List[ShareholderInfo]:
        """获取前十大股东信息（支持指定获取前 top 个股东）
        
        Args:
            code: 股票代码
            top: 获取前 top 个股东，默认 4，可选 1-10
                - 4: 获取前 4 大流通股东（默认）
                - 10: 获取前 10 大流通股东
                - 1-10: 获取指定数量的股东
            
        Returns:
            前十大股东信息列表，包含：
            - code: 股票代码
            - report_date: 报告期（更新日期）
            - holder_code: 股东代码
            - holder_name: 股东名称
            - hold_amount: 持股数（股）
            - hold_ratio: 持股比例（%）
            - change: 增减描述（不变/新进/数值）
            - change_rate: 变动率（%）
            
        Note:
            使用 efinance.stock.get_top10_stock_holder_info 接口
            获取沪深市场指定股票前十大流通股东信息
            支持获取前 1-10 大股东，默认前 4 大
            缓存时间：10 分钟
            
        Examples:
            # 获取前 4 大流通股东（默认）
            shareholders = await adapter.get_top10_stock_holder_info("600519")
            
            # 获取前 10 大流通股东
            shareholders = await adapter.get_top10_stock_holder_info("600519", top=10)
            
            # 获取前 1 大股东
            shareholders = await adapter.get_top10_stock_holder_info("600519", top=1)
        """
        try:
            if not EF_AVAILABLE:
                return []
            
            # 参数验证
            if not isinstance(top, int) or top < 1 or top > 10:
                logger.warning(f"top 参数无效：{top}，使用默认值 4")
                top = 4
            
            cache_key = self._get_cache_key('shareholder', code=code, top=top)
            cached = self._get_from_cache(cache_key, 'stock_info')
            if cached:
                self.record_request_success()  # 缓存命中也算成功
                return cached
            
            # 频率控制
            await self._rate_limit()
            
            # 获取前十大股东信息（efinance 的 top 参数支持 1-10）
            df = ef.stock.get_top10_stock_holder_info(code.zfill(6), top=top)
            
            if df.empty:
                logger.warning(f"前十大股东信息为空：{code} (top={top})")
                self.record_request_success()  # 空数据也算成功（非错误）
                return []
            
            def safe_parse_amount(value):
                """安全解析持股数量，支持'亿'、'万'等单位"""
                try:
                    if value is None or value == '' or value == '-':
                        return None
                    value_str = str(value)
                    # 处理'亿'单位
                    if '亿' in value_str:
                        num_str = value_str.replace('亿', '').strip()
                        return float(num_str) * 100000000
                    # 处理'万'单位
                    elif '万' in value_str:
                        num_str = value_str.replace('万', '').strip()
                        return float(num_str) * 10000
                    # 处理纯数字（股）
                    else:
                        return float(value_str.replace(',', '').strip())
                except (ValueError, TypeError):
                    return None
            
            def safe_parse_ratio(value):
                """安全解析百分比，支持'%'符号"""
                try:
                    if value is None or value == '' or value == '-':
                        return 0.0
                    value_str = str(value)
                    if '%' in value_str:
                        return float(value_str.replace('%', '').strip())
                    else:
                        return float(value_str.replace('%', '').strip())
                except (ValueError, TypeError):
                    return 0.0
            
            def safe_parse_change(value):
                """安全解析增减字段，支持'不变'、'新进'、数值等"""
                try:
                    if value is None or value == '' or value == '--':
                        return '不变'
                    value_str = str(value).strip()
                    # 特殊标记
                    if value_str in ['不变', '新进', '减持', '增持']:
                        return value_str
                    # 数值型增减（带单位）
                    if '万' in value_str or '亿' in value_str:
                        return value_str
                    # 纯数值（股）
                    try:
                        num = float(value_str.replace(',', '').strip())
                        if num > 0:
                            return f"+{int(num)}"
                        elif num < 0:
                            return f"{int(num)}"
                        else:
                            return '不变'
                    except:
                        return value_str
                except Exception:
                    return '未知'
            
            shareholders = []
            for row in df.itertuples(index=False):
                # 获取字段值
                holder_code = str(getattr(row, '股东代码', ''))
                holder_name = str(getattr(row, '股东名称', ''))
                report_date = str(getattr(row, '更新日期', getattr(row, '报告期', '')))
                
                # 解析持股数
                hold_amount_raw = getattr(row, '持股数', None)
                hold_amount = safe_parse_amount(hold_amount_raw)
                
                # 解析持股比例
                hold_ratio_raw = getattr(row, '持股比例', None)
                hold_ratio = safe_parse_ratio(hold_ratio_raw)
                
                # 解析增减
                change_raw = getattr(row, '增减', getattr(row, '持股变化', None))
                change = safe_parse_change(change_raw)
                
                # 解析变动率
                change_rate_raw = getattr(row, '变动率', getattr(row, '持股变化比例', None))
                change_rate = safe_parse_ratio(change_rate_raw) if change_rate_raw is not None else None
                
                shareholders.append(ShareholderInfo(
                    code=code,
                    report_date=report_date[:10] if len(report_date) >= 10 else report_date,
                    holder_code=holder_code,
                    holder_name=holder_name,
                    hold_amount=hold_amount,
                    hold_ratio=hold_ratio,
                    change=change,
                    change_rate=change_rate
                ))
            
            self._set_to_cache(cache_key, shareholders, 'stock_info')
            self.record_request_success()  # 记录成功
            logger.info(f"获取 {code} 前{top}大股东信息成功：{len(shareholders)}条")
            return shareholders
            
        except Exception as e:
            self.record_request_failure()  # 记录失败
            logger.error(f"获取前十大股东信息失败 {code} (top={top}): {e}")
            return []
    
<<<<<<< HEAD
    async def get_all_company_performance(self, date: Optional[str] = None) -> List[CompanyPerformance]:
        """
        获取沪深市场股票某一季度的表现情况
        
        Args:
            date: 报告发布日期，可选
                - None: 最新季报
                - '2021-06-30': 2021 年 Q2 季度报
                - '2021-03-31': 2021 年 Q1 季度报
        
        Returns:
            公司业绩表现数据列表
        """
        try:
            if not EF_AVAILABLE:
                return []
            
            cache_key = self._get_cache_key('performance', date=date or 'latest')
            cached = self._get_from_cache(cache_key, 'kline')
            if cached:
                return cached
            
            # 获取业绩表现数据
            df = ef.stock.get_all_company_performance(date)
            
            if df.empty:
                return []
            
            performances = []
            for row in df.itertuples(index=False):
                # 安全转换数值
                def safe_float(value, default=0.0):
                    try:
                        if value is None or value == '' or value == '-' or (isinstance(value, float) and str(value) == 'nan'):
                            return default
                        return float(value)
                    except (ValueError, TypeError):
                        return default
                
                code = str(getattr(row, '股票代码', '')).zfill(6)
                if not code:
                    continue
                
                # 处理公告日期
                report_date_raw = getattr(row, '公告日期', '')
                if report_date_raw:
                    if isinstance(report_date_raw, str):
                        report_date = report_date_raw.split(' ')[0].replace('-', '')
                    else:
                        report_date = str(report_date_raw)[:10].replace('-', '')
                else:
                    report_date = ''
                
                performances.append(CompanyPerformance(
                    code=code,
                    name=getattr(row, '股票简称', ''),
                    report_date=report_date,
                    revenue=safe_float(getattr(row, '营业收入', 0)),
                    revenue_growth=safe_float(getattr(row, '营业收入同比增长', 0)),
                    revenue_qoq=safe_float(getattr(row, '营业收入季度环比', 0)),
                    net_profit=safe_float(getattr(row, '净利润', 0)),
                    net_profit_growth=safe_float(getattr(row, '净利润同比增长', 0)),
                    net_profit_qoq=safe_float(getattr(row, '净利润季度环比', 0)),
                    eps=safe_float(getattr(row, '每股收益', 0)),
                    bps=safe_float(getattr(row, '每股净资产', 0)),
                    roe=safe_float(getattr(row, '净资产收益率', 0)),
                    gross_margin=safe_float(getattr(row, '销售毛利率', 0)),
                    cash_flow_per_share=safe_float(getattr(row, '每股经营现金流量', 0))
                ))
            
            self._set_to_cache(cache_key, performances, 'kline')
            logger.info(f"获取公司业绩表现成功：{len(performances)}条，报告期：{date or '最新'}")
            return performances
            
        except Exception as e:
            logger.error(f"获取公司业绩表现失败：{e}")
            return []
    
    async def get_all_report_dates(self) -> List[str]:
        """
        获取所有可选的报告发布日期
        
        Returns:
            报告日期列表，格式：YYYY-MM-DD
        """
        try:
            if not EF_AVAILABLE:
                return []
            
            cache_key = self._get_cache_key('report_dates')
            cached = self._get_from_cache(cache_key, 'stock_list')
            if cached:
                return cached
            
            # 获取所有报告日期
            dates = ef.stock.get_all_report_dates()
            
            if not dates:
                return []
            
            # 转换为字符串列表
            date_list = [str(d) for d in dates]
            
            self._set_to_cache(cache_key, date_list, 'stock_list')
            logger.info(f"获取报告日期列表成功：{len(date_list)}个")
            return date_list
            
        except Exception as e:
            logger.error(f"获取报告日期列表失败：{e}")
            return []
    
    async def get_market_realtime_quotes(self, market_types: Optional[List[str]] = None) -> List[MarketQuote]:
        """
        获取市场实时行情数据
=======
    async def get_market_realtime_quotes(
        self,
        market_types: Optional[List[str]] = None,
        fs: Optional[str] = None,
        fields: Optional[List[str]] = None,
        retry: int = 3,
        timeout: int = 15
    ) -> List[MarketQuote]:
        """获取市场/板块实时行情（支持多维度筛选）
        
        支持的市场类型：
        - A 股市场：'沪深 A 股'（默认）、'沪 A'、'深 A'、'北 A'
        - 板块指数：'创业板'、'科创板'
        - 基金市场：'ETF'、'LOF'
        - 行业概念：'行业板块'、'概念板块'
        - 国际市场：'港股'、'美股'、'中概股'
        - 其他：'可转债'、'期货'
        - 指数系列：'沪深系列指数'、'上证系列指数'、'深证系列指数'
        - 特色板块：'沪股通'、'深股通'、'新股'
>>>>>>> 7aaa7cbe85a09d6bf88368f14e12d60640ec9467
        
        Args:
            market_types: 市场类型列表（可选）
                示例：['创业板']、['ETF']、['行业板块']
                默认：None（表示沪深 A 股）
            
            fs: 高级筛选条件（优先级高于 market_types），支持：
                - 板块代码：'884723'（光伏概念）、'000300'（沪深 300）
                - 市场类型：'mkt:1'（沪市）、'mkt:0'（深市）、'mkt:2'（北交所）
                - 自定义条件：'pctChg:>0'（上涨）、'totMv:>50000000000'（市值>500 亿）
                - 多条件组合：'884723,pctChg:>0,totMv:>20000000000'
            
            fields: 自定义返回字段列表（可选）
                可选字段：'股票代码'、'股票名称'、'涨跌幅'、'最新价'、'最高'、'最低'、'今开'、
                         '涨跌额'、'换手率'、'量比'、'动态市盈率'、'成交量'、'成交额'、'昨日收盘'、
                         '总市值'、'流通市值'、'行情 ID'、'市场类型'
                默认：None（返回全部字段）
            
            retry: 重试次数，默认 3 次
            timeout: 超时时间（秒），默认 15 秒
            
        Returns:
            List[MarketQuote]: 市场实时行情列表
            
        Note:
            使用 efinance.stock.get_realtime_quotes 接口
            支持多维度筛选，适合批量获取特定范围股票数据
            缓存时间：60 秒
            
        Examples:
            # 获取沪深 A 股全部股票（默认）
            quotes = await adapter.get_market_realtime_quotes()
            
            # 获取创业板股票
            quotes = await adapter.get_market_realtime_quotes(market_types=['创业板'])
            
            # 获取 ETF 基金
            quotes = await adapter.get_market_realtime_quotes(market_types=['ETF'])
            
            # 获取光伏板块股票（使用板块代码）
            quotes = await adapter.get_market_realtime_quotes(fs="884723")
            
            # 获取北交所股票
            quotes = await adapter.get_market_realtime_quotes(fs="mkt:2")
            
            # 获取光伏板块中上涨的股票
            quotes = await adapter.get_market_realtime_quotes(fs="884723,pctChg:>0")
            
            # 获取行业板块
            quotes = await adapter.get_market_realtime_quotes(market_types=['行业板块'])
            
            # 获取港股
            quotes = await adapter.get_market_realtime_quotes(market_types=['港股'])
            
            # 获取沪深 300 指数成分股
            quotes = await adapter.get_market_realtime_quotes(fs="000300")
        """
        try:
            if not EF_AVAILABLE:
                return []
            
            # 确定筛选条件
            if fs:
                # 使用自定义筛选条件（优先级更高）
                filter_condition = fs
                cache_prefix = f'fs_{fs}'
            elif market_types:
                # efinance 支持的市场类型
                supported_types = [
                    '沪深 A 股', '沪 A', '深 A', '北 A',
                    '创业板', '科创板',
                    'ETF', 'LOF',
                    '行业板块', '概念板块',
                    '港股', '美股', '中概股',
                    '可转债', '期货',
                    '沪深系列指数', '上证系列指数', '深证系列指数',
                    '沪股通', '深股通', '新股'
                ]
                
                # 过滤不支持的类型
                valid_types = [t for t in market_types if t in supported_types]
                if not valid_types:
                    logger.warning(f"efinance 不支持的市场类型：{market_types}，使用默认沪深 A 股")
                    filter_condition = None
                    cache_prefix = 'all'
                elif len(valid_types) == 1:
                    filter_condition = valid_types[0]
                    cache_prefix = valid_types[0]
                else:
                    filter_condition = valid_types
                    cache_prefix = '_'.join(valid_types)
            else:
                # 不传参数，默认获取沪深 A 股（最稳定）
                filter_condition = None
                cache_prefix = 'all'
            
            # 构建缓存 key
            cache_key = self._get_cache_key('market_quotes', fs=cache_prefix)
            cached = self._get_from_cache(cache_key, 'quote')
            if cached:
                logger.debug(f"从缓存获取市场实时行情：{cache_key}")
                return cached
            
            # 调用 efinance API，添加重试机制和超时控制
            df = None
            for attempt in range(retry):
                try:
                    df = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(
                            None,
                            lambda: ef.stock.get_realtime_quotes(filter_condition)
                        ),
                        timeout=timeout
                    )
                    break
                except asyncio.TimeoutError:
                    logger.warning(f"获取市场实时行情超时（{timeout}秒），重试 {attempt + 1}/{retry}")
                    if attempt < retry - 1:
                        await asyncio.sleep(2)
                    else:
                        raise
                except Exception as e:
                    if attempt < retry - 1:
                        logger.warning(f"获取市场实时行情失败，重试 {attempt + 1}/{retry}: {e}")
                        await asyncio.sleep(1)
                    else:
                        raise
            
            if df is None or df.empty:
                logger.warning(f"efinance 返回空数据：{filter_condition}")
                return []
            
            quotes = []
            for row in df.itertuples(index=False):
                # 安全转换浮点数
                def safe_float(value, default=None):
                    try:
                        if value is None or value == '' or value == '-' or (isinstance(value, float) and str(value) == 'nan'):
                            return default
                        return float(value)
                    except (ValueError, TypeError):
                        return default
                
                code = str(getattr(row, '股票代码', '')).zfill(6)
                if not code:
                    continue
                
                quotes.append(MarketQuote(
                    code=code,
                    name=getattr(row, '股票名称', ''),
                    change_pct=safe_float(getattr(row, '涨跌幅', None)),
                    price=safe_float(getattr(row, '最新价', None)),
                    high=safe_float(getattr(row, '最高', None)),
                    low=safe_float(getattr(row, '最低', None)),
                    open=safe_float(getattr(row, '今开', None)),
                    change=safe_float(getattr(row, '涨跌额', None)),
                    turnover_rate=safe_float(getattr(row, '换手率', None)),
                    volume_ratio=safe_float(getattr(row, '量比', None)),
                    pe_ratio=safe_float(getattr(row, '动态市盈率', None)),
                    volume=safe_float(getattr(row, '成交量', None)),
                    amount=safe_float(getattr(row, '成交额', None)),
                    prev_close=safe_float(getattr(row, '昨日收盘', None)),
                    total_market_cap=safe_float(getattr(row, '总市值', None)),
                    float_market_cap=safe_float(getattr(row, '流通市值', None)),
                    market_type=getattr(row, '市场类型', None)
                ))
            
            # 保存到缓存（5 分钟）
            self._set_to_cache(cache_key, quotes, 'quote')
            logger.info(f"获取市场实时行情成功：{len(quotes)}条，市场类型：{market_types or '沪深 A 股（默认）'}")
            return quotes
            
        except asyncio.TimeoutError:
            logger.error(f"获取市场实时行情超时（15 秒）：{market_types}")
            return []
        except Exception as e:
            logger.error(f"获取市场实时行情失败：{e}")
            # 降级策略：尝试使用默认市场类型（沪深 A 股）
            if market_types is not None:
                logger.warning(f"尝试使用默认市场类型（沪深 A 股）重试...")
                try:
                    return await self.get_market_realtime_quotes(None)
                except Exception as fallback_error:
                    logger.error(f"使用默认市场类型重试失败：{fallback_error}")
            return []
    
    async def get_financial_performance(
        self,
        code: str,
        report_date: Optional[str] = None,
        report_type: str = "quarterly"
    ) -> List[FinancialPerformance]:
        """获取财务业绩数据（季度报）
        
        Args:
            code: 股票代码
            report_date: 报告日期，格式 'YYYY-MM-DD'，例如 '2024-03-31'
                      - None: 获取最新季报（默认）
                      - '2024-03-31': 获取 2024 年一季报
                      - '2023-12-31': 获取 2023 年年报
            report_type: 报告类型，目前只支持 'quarterly'（季度报）
        
        Returns:
            财务业绩数据列表
            
        Note:
            efinance 提供的是季度业绩数据，包括营业收入、净利润等关键指标
            支持获取历史多个季度的数据
        """
        try:
            if not EF_AVAILABLE:
                return []
            
            cache_key = self._get_cache_key('financial', code=code, date=report_date, type=report_type)
            cached = self._get_from_cache(cache_key, 'stock_info')
            if cached:
                return cached
            
            # 频率控制
            await self._rate_limit()
            
            # 获取指定报告期的数据
            # efinance 的 get_all_company_performance 可以指定 date 参数
            # 如果不指定，默认获取最新季报
            df = ef.stock.get_all_company_performance(report_date)
            
            if df.empty:
                return []
            
            # 筛选指定股票
            stock_df = df[df['股票代码'] == code.zfill(6)]
            
            if stock_df.empty:
                logger.warning(f"未找到股票 {code} 的财务业绩数据（报告期：{report_date or '最新'}）")
                return []
            
            performances = []
            for row in stock_df.itertuples(index=False):
                # 安全转换数值
                def safe_float(value, default=None):
                    try:
                        if value is None or value == '' or value == '-' or (isinstance(value, float) and str(value) == 'nan'):
                            return default
                        return float(value)
                    except (ValueError, TypeError):
                        return default
                
                report_date_str = str(getattr(row, '公告日期', ''))
                if len(report_date_str) >= 10:
                    report_date_str = report_date_str[:10].replace('-', '')
                
                performances.append(FinancialPerformance(
                    code=code,
                    name=getattr(row, '股票简称', ''),
                    report_date=report_date_str,
                    revenue=safe_float(getattr(row, '营业收入', None)),
                    revenue_growth=safe_float(getattr(row, '营业收入同比增长', None)),
                    revenue_qoq=safe_float(getattr(row, '营业收入季度环比', None)),
                    net_profit=safe_float(getattr(row, '净利润', None)),
                    net_profit_growth=safe_float(getattr(row, '净利润同比增长', None)),
                    net_profit_qoq=safe_float(getattr(row, '净利润季度环比', None)),
                    eps=safe_float(getattr(row, '每股收益', None)),
                    bvps=safe_float(getattr(row, '每股净资产', None)),
                    roe=safe_float(getattr(row, '净资产收益率', None)),
                    gross_margin=safe_float(getattr(row, '销售毛利率', None)),
                    cfps=safe_float(getattr(row, '每股经营现金流量', None))
                ))
            
            # 按公告日期排序（最新的在前）
            performances.sort(key=lambda x: x.report_date, reverse=True)
            
            self._set_to_cache(cache_key, performances, 'stock_info')
            logger.info(f"获取 {code} 财务业绩数据成功（报告期：{report_date or '最新'}）：{len(performances)}条")
            return performances
            
        except Exception as e:
            logger.error(f"获取财务业绩数据失败 {code}（报告期：{report_date or '最新'}）: {e}")
            return []
    
    async def get_all_report_dates(self) -> List[Dict[str, str]]:
        """获取所有可用的报告期日期
        
        Returns:
            报告期日期列表，每个元素包含 'date' 和 'name' 字段
            
        Example:
            [
                {'date': '2024-03-31', 'name': '2024年 一季报'},
                {'date': '2023-12-31', 'name': '2023年 年报'},
                ...
            ]
        """
        try:
            if not EF_AVAILABLE:
                return []
            
            cache_key = self._get_cache_key('report_dates')
            cached = self._get_from_cache(cache_key, 'stock_info')
            if cached:
                return cached
            
            # 获取所有报告期
            df = ef.stock.get_all_report_dates()
            
            if df.empty:
                return []
            
            report_dates = []
            for row in df.itertuples(index=False):
                report_dates.append({
                    'date': str(getattr(row, '报告日期', '')),
                    'name': str(getattr(row, '季报名称', ''))
                })
            
            self._set_to_cache(cache_key, report_dates, 'stock_info')
            logger.info(f"获取所有报告期日期成功：{len(report_dates)}个")
            return report_dates
            
        except Exception as e:
            logger.error(f"获取所有报告期日期失败：{e}")
            return []
    
    async def get_historical_financial_performance(
        self,
        code: str,
        limit: int = 10
    ) -> List[FinancialPerformance]:
        """获取历史多个季度的财务业绩数据
        
        Args:
            code: 股票代码
            limit: 获取最近几个季度的数据（默认 10 个）
        
        Returns:
            历史财务业绩数据列表，按时间倒序排列
            
        Note:
            会自动获取所有可用的报告期，然后依次获取每个报告期的数据
        """
        try:
            if not EF_AVAILABLE:
                return []
            
            # 获取所有可用的报告期
            report_dates_df = ef.stock.get_all_report_dates()
            
            if report_dates_df.empty:
                return []
            
            # 获取最近的 N 个报告期
            recent_dates = report_dates_df.head(limit)['报告日期'].tolist()
            
            all_performances = []
            for report_date in recent_dates:
                # 获取指定报告期的数据
                performances = await self.get_financial_performance(
                    code=code,
                    report_date=report_date
                )
                all_performances.extend(performances)
            
            # 按报告日期排序（最新的在前）
            all_performances.sort(key=lambda x: x.report_date, reverse=True)
            
            logger.info(f"获取 {code} 历史财务业绩数据成功：{len(all_performances)}条")
            return all_performances
            
        except Exception as e:
            logger.error(f"获取历史财务业绩数据失败 {code}: {e}")
            return []
    
    # ========== 基金 API ==========
    
    async def get_fund_base_info(
        self,
        fund_codes: Union[str, List[str]]
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """获取基金基本信息
        
        Args:
            fund_codes: 6 位基金代码或多个 6 位基金代码构成的列表
                示例：'161725' 或 ['161725', '005827']
        
        Returns:
            单只基金返回 Dict[str, Any]（对应 Series）
            多只基金返回 List[Dict[str, Any]]（对应 DataFrame）
            
        Note:
            使用 efinance.fund.get_base_info 接口
            获取基金的基本信息，包括基金代码、简称、成立日期、涨跌幅、最新净值等
            缓存时间：10 分钟
            
        Examples:
            # 获取单只基金信息
            fund_info = await adapter.get_fund_base_info('161725')
            
            # 获取多只基金信息
            fund_list = await adapter.get_fund_base_info(['161725', '005827'])
        """
        try:
            if not EF_AVAILABLE:
                return None if isinstance(fund_codes, str) else []
            
            # 处理单只基金
            if isinstance(fund_codes, str):
                code = fund_codes.strip()
                cache_key = self._get_cache_key('fund_info', code=code)
                cached = self._get_from_cache(cache_key, 'fund_info')
                if cached:
                    return cached
                
                # 频率控制
                await self._rate_limit()
                
                # 获取单只基金信息
                result = ef.fund.get_base_info(code)
                
                if result is None or (hasattr(result, 'empty') and result.empty):
                    return None
                
                # 解析 Series 数据
                fund_info = {
                    'code': str(result.get('基金代码', code)),
                    'name': str(result.get('基金简称', '')),
                    'establish_date': str(result.get('成立日期', '')),
                    'change_pct': float(result.get('涨跌幅', 0)) if result.get('涨跌幅') is not None else None,
                    'net_asset_value': float(result.get('最新净值', 0)) if result.get('最新净值') is not None else None,
                    'fund_company': str(result.get('基金公司', '')),
                    'nav_update_date': str(result.get('净值更新日期', '')),
                    'description': str(result.get('简介', ''))
                }
                
                self._set_to_cache(cache_key, fund_info, 'fund_info')
                logger.info(f"获取基金 {code} 基本信息成功")
                return fund_info
            
            # 处理多只基金（列表）
            else:
                valid_codes = [c.strip() for c in fund_codes if c and len(c.strip()) >= 6]
                
                if not valid_codes:
                    return []
                
                cache_key = self._get_cache_key('fund_info_batch', codes=','.join(sorted(valid_codes)))
                cached = self._get_from_cache(cache_key, 'fund_info')
                if cached:
                    return cached
                
                # 频率控制
                await self._rate_limit()
                
                # 批量获取基金信息
                df = ef.fund.get_base_info(valid_codes)
                
                if df is None or (hasattr(df, 'empty') and df.empty):
                    return []
                
                fund_list = []
                for row in df.itertuples(index=False):
                    fund_info = {
                        'code': str(getattr(row, '基金代码', '')).zfill(6),
                        'name': str(getattr(row, '基金简称', '')),
                        'establish_date': str(getattr(row, '成立日期', '')),
                        'change_pct': float(getattr(row, '涨跌幅', 0)) if getattr(row, '涨跌幅', None) is not None else None,
                        'net_asset_value': float(getattr(row, '最新净值', 0)) if getattr(row, '最新净值', None) is not None else None,
                        'fund_company': str(getattr(row, '基金公司', '')),
                        'nav_update_date': str(getattr(row, '净值更新日期', '')),
                        'description': str(getattr(row, '简介', ''))
                    }
                    fund_list.append(fund_info)
                
                self._set_to_cache(cache_key, fund_list, 'fund_info')
                logger.info(f"获取基金基本信息成功：{len(fund_list)}条")
                return fund_list
            
        except Exception as e:
            logger.error(f"获取基金基本信息失败 {fund_codes}: {e}")
            return None if isinstance(fund_codes, str) else []
    
    async def get_fund_codes(
        self,
        fund_type: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """获取天天基金网公开的全部公募基金名单
        
        Args:
            fund_type: 基金类型（可选）
                - 'zq': 债券类型基金
                - 'gp': 股票类型基金
                - 'etf': ETF 基金
                - 'hh': 混合型基金
                - 'zs': 指数型基金
                - 'fof': FOF 基金
                - 'qdii': QDII 型基金
                - None: 全部类型
            
        Returns:
            基金代码列表，每项包含：
            - code: 基金代码
            - name: 基金简称
            
        Note:
            使用 efinance.fund.get_fund_codes 接口
            获取天天基金网公开的公募基金份额
            缓存时间：30 分钟
            
        Examples:
            # 获取全部类型基金
            funds = await adapter.get_fund_codes()
            
            # 获取股票型基金
            funds = await adapter.get_fund_codes('gp')
            
            # 获取 ETF 基金
            funds = await adapter.get_fund_codes('etf')
        """
        try:
            if not EF_AVAILABLE:
                return []
            
            # 构建缓存 key
            cache_key = self._get_cache_key('fund_codes', fund_type=fund_type or 'all')
            cached = self._get_from_cache(cache_key, 'fund_info')
            if cached:
                return cached
            
            # 频率控制
            await self._rate_limit()
            
            # 获取基金代码列表
            df = ef.fund.get_fund_codes(ft=fund_type)
            
            if df is None or (hasattr(df, 'empty') and df.empty):
                return []
            
            # 转换为列表
            fund_list = []
            for row in df.itertuples(index=False):
                fund_info = {
                    'code': str(getattr(row, '基金代码', '')).strip(),
                    'name': str(getattr(row, '基金简称', '')).strip()
                }
                # 过滤空代码
                if fund_info['code']:
                    fund_list.append(fund_info)
            
            # 保存到缓存（30 分钟）
            self._set_to_cache(cache_key, fund_list, 'fund_info')
            logger.info(f"获取基金代码列表成功：{len(fund_list)}条，类型：{fund_type or '全部'}")
            return fund_list
            
        except Exception as e:
            logger.error(f"获取基金代码列表失败（类型：{fund_type}）: {e}")
            return []
    
    async def get_fund_invest_position(
        self,
        fund_code: str,
        dates: Optional[Union[str, List[str]]] = None
    ) -> List[Dict[str, Any]]:
        """获取基金持仓占比数据
        
        Args:
            fund_code: 基金代码（6 位）
            dates: 日期或日期列表（可选）
                - None: 最新公开日期
                - '2020-01-01': 单个公开持仓日期
                - ['2020-12-31', '2019-12-31']: 多个公开持仓日期
            
        Returns:
            基金持仓占比数据列表，每项包含：
            - fund_code: 基金代码
            - stock_code: 股票代码
            - stock_name: 股票简称
            - position_ratio: 持仓占比（%）
            - change: 较上期变化（%）
            - report_date: 公开日期
            
        Note:
            使用 efinance.fund.get_invest_position 接口
            获取基金的前十大重仓股持仓占比数据
            缓存时间：10 分钟
            
        Examples:
            # 获取最新公开的持仓数据
            positions = await adapter.get_fund_invest_position('161725')
            
            # 获取单个日期的持仓数据
            positions = await adapter.get_fund_invest_position('161725', '2021-12-31')
            
            # 获取多个日期的持仓数据
            positions = await adapter.get_fund_invest_position('161725', ['2021-12-31', '2021-09-30'])
        """
        try:
            if not EF_AVAILABLE:
                return []
            
            # 构建缓存 key
            if dates is None:
                cache_key = self._get_cache_key('fund_position', code=fund_code, dates='latest')
            elif isinstance(dates, str):
                cache_key = self._get_cache_key('fund_position', code=fund_code, dates=dates)
            else:
                cache_key = self._get_cache_key('fund_position', code=fund_code, dates=','.join(sorted(dates)))
            
            cached = self._get_from_cache(cache_key, 'fund_info')
            if cached:
                return cached
            
            # 频率控制
            await self._rate_limit()
            
            # 获取基金持仓数据
            df = ef.fund.get_invest_position(fund_code, dates=dates)
            
            if df is None or (hasattr(df, 'empty') and df.empty):
                return []
            
            # 转换为列表
            position_list = []
            for row in df.itertuples(index=False):
                position_info = {
                    'fund_code': str(getattr(row, '基金代码', fund_code)).strip(),
                    'stock_code': str(getattr(row, '股票代码', '')).strip().zfill(6),
                    'stock_name': str(getattr(row, '股票简称', '')).strip(),
                    'position_ratio': float(getattr(row, '持仓占比', 0)) if getattr(row, '持仓占比', None) is not None else None,
                    'change': float(getattr(row, '较上期变化', 0)) if getattr(row, '较上期变化', None) is not None else None,
                    'report_date': str(getattr(row, '公开日期', '')).strip()[:10] if getattr(row, '公开日期', None) is not None else None
                }
                # 过滤空股票代码
                if position_info['stock_code']:
                    position_list.append(position_info)
            
            # 保存到缓存（10 分钟）
            self._set_to_cache(cache_key, position_list, 'fund_info')
            logger.info(f"获取基金 {fund_code} 持仓占比数据成功：{len(position_list)}条")
            return position_list
            
        except Exception as e:
            logger.error(f"获取基金持仓占比数据失败 {fund_code} (dates={dates}): {e}")
            return []
    
    async def get_fund_quote_history(
        self,
        fund_code: str,
        pz: int = 40000
    ) -> List[Dict[str, Any]]:
        """
        获取单只基金历史净值数据
        
        Args:
            fund_code: 6 位基金代码
            pz: 页码，默认为 40000 以获取全部历史数据
        
        Returns:
            基金历史净值数据列表，每项包含：
            - date: 日期
            - unit_nav: 单位净值
            - accumulated_nav: 累计净值
            - change_pct: 涨跌幅（%）
            
        Note:
            使用 efinance.fund.get_quote_history 接口
            单只基金历史净值查询（精准模式）
            缓存时间：10 分钟
            
        Examples:
            # 获取全部历史净值
            history = await adapter.get_fund_quote_history('161725')
            
            # 获取部分历史净值
            history = await adapter.get_fund_quote_history('161725', pz=100)
        """
        try:
            if not EF_AVAILABLE:
                return []
            
            # 构建缓存 key
            cache_key = self._get_cache_key('fund_history', code=fund_code, pz=pz)
            cached = self._get_from_cache(cache_key, 'fund_info')
            if cached:
                return cached
            
            # 频率控制
            await self._rate_limit()
            
            # 获取基金历史净值
            df = ef.fund.get_quote_history(fund_code, pz=pz)
            
            if df is None or (hasattr(df, 'empty') and df.empty):
                return []
            
            # 转换为列表
            history_list = []
            for row in df.itertuples(index=False):
                history_info = {
                    'fund_code': fund_code,
                    'date': str(getattr(row, '日期', '')).strip()[:10] if getattr(row, '日期', None) is not None else None,
                    'unit_nav': float(getattr(row, '单位净值', 0)) if getattr(row, '单位净值', None) is not None else None,
                    'accumulated_nav': float(getattr(row, '累计净值', 0)) if getattr(row, '累计净值', None) is not None else None,
                    'change_pct': float(getattr(row, '涨跌幅', 0)) if getattr(row, '涨跌幅', None) is not None else None,
                }
                history_list.append(history_info)
            
            # 保存到缓存（10 分钟）
            self._set_to_cache(cache_key, history_list, 'fund_info')
            logger.info(f"获取基金 {fund_code} 历史净值数据成功：{len(history_list)}条")
            return history_list
            
        except Exception as e:
            logger.error(f"获取基金历史净值数据失败 {fund_code}: {e}")
            return []
    
    async def get_fund_quote_history_multi(
        self,
        fund_codes: List[str],
        pz: int = 40000
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        批量获取多只基金历史净值数据
        
        Args:
            fund_codes: 多只基金代码列表
            pz: 页码，默认为 40000 以获取全部历史数据
        
        Returns:
            字典，key = 基金代码，value = 对应净值数据列表
            每个净值数据包含：
            - date: 日期
            - unit_nav: 单位净值
            - accumulated_nav: 累计净值
            - change_pct: 涨跌幅（%）
            
        Note:
            使用 efinance.fund.get_quote_history_multi 接口
            多只基金历史净值批量查询（高效模式）
            缓存时间：10 分钟
            风控概率低，推荐批量查询使用
            
        Examples:
            # 批量获取多只基金历史净值
            history_dict = await adapter.get_fund_quote_history_multi(['161725', '005918'])
            
            # 访问单只基金数据
            history_161725 = history_dict['161725']
            history_005918 = history_dict['005918']
        """
        try:
            if not EF_AVAILABLE:
                return {}
            
            if not fund_codes or not isinstance(fund_codes, list):
                return {}
            
            # 构建缓存 key
            cache_key = self._get_cache_key('fund_history_multi', codes=','.join(sorted(fund_codes)), pz=pz)
            cached = self._get_from_cache(cache_key, 'fund_info')
            if cached:
                return cached
            
            # 频率控制
            await self._rate_limit()
            
            # 批量获取基金历史净值
            result_dict = ef.fund.get_quote_history_multi(fund_codes, pz=pz)
            
            if not result_dict or not isinstance(result_dict, dict):
                return {}
            
            # 转换为统一格式
            history_dict = {}
            total_count = 0
            for code, df in result_dict.items():
                if df is None or (hasattr(df, 'empty') and df.empty):
                    history_dict[code] = []
                    continue
                
                history_list = []
                for row in df.itertuples(index=False):
                    history_info = {
                        'fund_code': code,
                        'date': str(getattr(row, '日期', '')).strip()[:10] if getattr(row, '日期', None) is not None else None,
                        'unit_nav': float(getattr(row, '单位净值', 0)) if getattr(row, '单位净值', None) is not None else None,
                        'accumulated_nav': float(getattr(row, '累计净值', 0)) if getattr(row, '累计净值', None) is not None else None,
                        'change_pct': float(getattr(row, '涨跌幅', 0)) if getattr(row, '涨跌幅', None) is not None else None,
                    }
                    history_list.append(history_info)
                
                history_dict[code] = history_list
                total_count += len(history_list)
            
            # 保存到缓存（10 分钟）
            self._set_to_cache(cache_key, history_dict, 'fund_info')
            logger.info(f"批量获取 {len(fund_codes)} 只基金历史净值数据成功：共{total_count}条")
            return history_dict
            
        except Exception as e:
            logger.error(f"批量获取基金历史净值数据失败：{e}")
            return {}
    
    async def get_fund_realtime_increase_rate(
        self,
        fund_codes: Union[str, List[str]]
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """获取基金实时估算涨跌幅度
        
        Args:
            fund_codes: 6 位基金代码或者 6 位基金代码构成的字符串列表
                示例：'161725' 或 ['161725', '005827']
        
        Returns:
            单只基金返回 Dict[str, Any]
            多只基金返回 List[Dict[str, Any]]
            每个包含：
            - code: 基金代码
            - name: 基金名称
            - net_value: 最新净值
            - nav_date: 最新净值公开日期
            - estimate_time: 估算时间
            - estimate_change_pct: 估算涨跌幅
            
        Note:
            使用 efinance.fund.get_realtime_increase_rate 接口
            获取基金的实时估算涨跌情况
            缓存时间：60 秒（实时数据）
            
        Examples:
            # 单只基金
            rate_info = await adapter.get_fund_realtime_increase_rate('161725')
            
            # 多只基金
            rate_list = await adapter.get_fund_realtime_increase_rate(['161725', '005827'])
        """
        try:
            if not EF_AVAILABLE:
                return None if isinstance(fund_codes, str) else []
            
            # 处理单只基金
            if isinstance(fund_codes, str):
                code = fund_codes.strip()
                cache_key = self._get_cache_key('fund_rate', code=code)
                cached = self._get_from_cache(cache_key, 'quote')
                if cached:
                    return cached
                
                # 频率控制
                await self._rate_limit()
                
                # 获取单只基金实时估算涨跌幅
                df = ef.fund.get_realtime_increase_rate(code)
                
                if df is None or (hasattr(df, 'empty') and df.empty):
                    return None
                
                # 解析 DataFrame（单只基金也返回 DataFrame）
                row = df.iloc[0] if len(df) > 0 else None
                if row is None:
                    return None
                
                # 安全获取数值
                def safe_float(key, default=None):
                    val = row.get(key, default)
                    if val is None or (isinstance(val, float) and str(val) == 'nan'):
                        return default
                    try:
                        return float(val)
                    except (ValueError, TypeError):
                        return default
                
                rate_info = {
                    'code': str(row.get('基金代码', code)).strip().zfill(6),
                    'name': str(row.get('基金名称', '')).strip(),
                    'net_value': safe_float('最新净值'),
                    'nav_date': str(row.get('最新净值公开日期', '')).strip()[:10] if row.get('最新净值公开日期') else None,
                    'estimate_time': str(row.get('估算时间', '')).strip(),
                    'estimate_change_pct': safe_float('估算涨跌幅')
                }
                
                self._set_to_cache(cache_key, rate_info, 'quote')
                logger.info(f"获取基金 {code} 实时估算涨跌幅成功：{rate_info['estimate_change_pct']}%")
                return rate_info
            
            # 处理多只基金（列表）
            else:
                valid_codes = [c.strip() for c in fund_codes if c and len(c.strip()) >= 6]
                
                if not valid_codes:
                    return []
                
                cache_key = self._get_cache_key('fund_rate_batch', codes=','.join(sorted(valid_codes)))
                cached = self._get_from_cache(cache_key, 'quote')
                if cached:
                    return cached
                
                # 频率控制
                await self._rate_limit()
                
                # 批量获取基金实时估算涨跌幅
                df = ef.fund.get_realtime_increase_rate(valid_codes)
                
                if df is None or (hasattr(df, 'empty') and df.empty):
                    return []
                
                # 转换为列表
                rate_list = []
                for row in df.itertuples(index=False):
                    # 安全获取数值
                    def safe_get(key, default=None):
                        val = getattr(row, key, default)
                        if val is None or (isinstance(val, float) and str(val) == 'nan'):
                            return default
                        try:
                            return float(val)
                        except (ValueError, TypeError):
                            return default
                    
                    rate_info = {
                        'code': str(getattr(row, '基金代码', '')).strip().zfill(6),
                        'name': str(getattr(row, '基金名称', '')).strip(),
                        'net_value': safe_get('最新净值'),
                        'nav_date': str(getattr(row, '最新净值公开日期', '')).strip()[:10] if getattr(row, '最新净值公开日期', None) else None,
                        'estimate_time': str(getattr(row, '估算时间', '')).strip(),
                        'estimate_change_pct': safe_get('估算涨跌幅')
                    }
                    # 过滤空基金代码
                    if rate_info['code']:
                        rate_list.append(rate_info)
                
                self._set_to_cache(cache_key, rate_list, 'quote')
                logger.info(f"获取基金实时估算涨跌幅成功：{len(rate_list)}条")
                return rate_list
            
        except Exception as e:
            logger.error(f"获取基金实时估算涨跌幅失败 {fund_codes}: {e}")
            return None if isinstance(fund_codes, str) else []
    
    async def get_fund_period_change(
        self,
        fund_code: str
    ) -> List[Dict[str, Any]]:
        """获取基金阶段涨跌幅度
        
        Args:
            fund_code: 6 位基金代码
        
        Returns:
            基金阶段涨跌数据列表，每项包含：
            - fund_code: 基金代码
            - period: 时间段（如：近一周、近一月、近三月等）
            - return_rate: 收益率（%）
            - avg_return: 同类平均（%）
            - rank: 同类排行
            - total_count: 同类总数
            - rank_rate: 排名百分比（rank/total_count，越低越好）
            
        Note:
            使用 efinance.fund.get_period_change 接口
            获取基金在不同时间段的收益率、同类平均、同类排行等数据
            缓存时间：10 分钟
            
        Examples:
            # 获取基金阶段涨跌幅
            period_data = await adapter.get_fund_period_change('161725')
            
            # 查看近一年表现
            one_year = next(p for p in period_data if p['period'] == '近一年')
            print(f"近一年收益率：{one_year['return_rate']}%")
            print(f"同类排名：{one_year['rank']}/{one_year['total_count']}")
        """
        try:
            if not EF_AVAILABLE:
                return []
            
            # 构建缓存 key
            cache_key = self._get_cache_key('fund_period', code=fund_code)
            cached = self._get_from_cache(cache_key, 'fund_info')
            if cached:
                return cached
            
            # 频率控制
            await self._rate_limit()
            
            # 获取基金阶段涨跌幅
            df = ef.fund.get_period_change(fund_code)
            
            if df is None or (hasattr(df, 'empty') and df.empty):
                return []
            
            # 转换为列表
            period_list = []
            for row in df.itertuples(index=False):
                # 安全获取数值
                def safe_get(key, default=None):
                    val = getattr(row, key, default)
                    if val is None or (isinstance(val, float) and str(val) == 'nan'):
                        return default
                    try:
                        return float(val) if val != '' else default
                    except (ValueError, TypeError):
                        return default
                
                # 获取字段值
                period = str(getattr(row, '时间段', '')).strip()
                return_rate = safe_get('收益率')
                avg_return = safe_get('同类平均')
                rank = safe_get('同类排行')
                total_count = safe_get('同类总数')
                
                # 计算排名百分比（越低越好）
                rank_rate = None
                if rank is not None and total_count is not None and total_count > 0:
                    rank_rate = rank / total_count
                
                period_info = {
                    'fund_code': str(getattr(row, '基金代码', fund_code)).strip().zfill(6),
                    'period': period,
                    'return_rate': return_rate,
                    'avg_return': avg_return,
                    'rank': int(rank) if rank is not None else None,
                    'total_count': int(total_count) if total_count is not None else None,
                    'rank_rate': rank_rate
                }
                
                # 过滤空时间段
                if period_info['period']:
                    period_list.append(period_info)
            
            # 保存到缓存（10 分钟）
            self._set_to_cache(cache_key, period_list, 'fund_info')
            logger.info(f"获取基金 {fund_code} 阶段涨跌幅成功：{len(period_list)}个时间段")
            return period_list
            
        except Exception as e:
            logger.error(f"获取基金阶段涨跌幅失败 {fund_code}: {e}")
            return []
    
    async def get_fund_types_percentage(
        self,
        fund_code: str,
        dates: Optional[Union[str, List[str]]] = None
    ) -> List[Dict[str, Any]]:
        """获取基金不同类型占比信息（资产配置比例）
        
        Args:
            fund_code: 6 位基金代码
            dates: 日期或日期列表（可选）
                - None: 最新公开日期
                - '2020-01-01': 单个公开持仓日期
                - ['2020-12-31', '2019-12-31']: 多个公开持仓日期
            
        Returns:
            基金资产配置比例数据列表，每项包含：
            - fund_code: 基金代码
            - report_date: 公开日期
            - stock_ratio: 股票比重（%）
            - bond_ratio: 债券比重（%）
            - cash_ratio: 现金比重（%）
            - other_ratio: 其他比重（%）
            - total_scale: 总规模（亿元）
            
        Note:
            使用 efinance.fund.get_types_percentage 接口
            获取基金在不同日期的股票、债券、现金等各类资产占比
            缓存时间：10 分钟
            
        Examples:
            # 获取最新资产配置
            assets = await adapter.get_fund_types_percentage('005827')
            
            # 获取指定日期的资产配置
            assets = await adapter.get_fund_types_percentage('005827', '2021-12-31')
            
            # 获取多个日期的资产配置
            assets = await adapter.get_fund_types_percentage('005827', ['2021-12-31', '2021-06-30'])
        """
        try:
            if not EF_AVAILABLE:
                return []
            
            # 构建缓存 key
            if dates is None:
                cache_key = self._get_cache_key('fund_assets', code=fund_code, dates='latest')
            elif isinstance(dates, str):
                cache_key = self._get_cache_key('fund_assets', code=fund_code, dates=dates)
            else:
                cache_key = self._get_cache_key('fund_assets', code=fund_code, dates=','.join(sorted(dates)))
            
            cached = self._get_from_cache(cache_key, 'fund_info')
            if cached:
                return cached
            
            # 频率控制
            await self._rate_limit()
            
            # 获取基金资产配置数据
            df = ef.fund.get_types_percentage(fund_code, dates=dates)
            
            if df is None or (hasattr(df, 'empty') and df.empty):
                logger.debug(f"基金 {fund_code} 资产配置数据为空 (dates={dates})")
                return []
            
            # 调试：打印 DataFrame 信息
            logger.debug(f"基金 {fund_code} 资产配置数据：{len(df)}行，列：{list(df.columns)}")
            
            # 转换为列表
            assets_list = []
            for row in df.itertuples(index=False):
                # 安全获取数值
                def safe_get(key, default=None):
                    val = getattr(row, key, default)
                    if val is None or val == '--' or val == '' or (isinstance(val, float) and str(val) == 'nan'):
                        return default
                    try:
                        return float(val)
                    except (ValueError, TypeError):
                        return default
                
                # 获取字段值 - 兼容不同的列名
                report_date = None
                for date_col in ['公开日期', '日期', '报告期']:
                    if hasattr(row, date_col):
                        report_date = str(getattr(row, date_col, '')).strip()[:10] if getattr(row, date_col, None) else None
                        if report_date:
                            break
                
                assets_info = {
                    'fund_code': str(getattr(row, '基金代码', fund_code)).strip().zfill(6),
                    'report_date': report_date if report_date else (dates if isinstance(dates, str) else None),  # 如果没找到日期，使用传入的 dates 参数
                    'stock_ratio': safe_get('股票比重'),
                    'bond_ratio': safe_get('债券比重'),
                    'cash_ratio': safe_get('现金比重'),
                    'other_ratio': safe_get('其他 比重', 0.0),  # 注意：efinance 返回的列名有空格
                    'total_scale': safe_get('总规模 (亿元)')  # 注意：efinance 返回的列名有括号
                }
                
                # 如果还是没有日期，且是查询最新数据，则使用当前日期
                if not assets_info['report_date'] and dates is None:
                    from datetime import datetime
                    assets_info['report_date'] = datetime.now().strftime('%Y-%m-%d')
                
                # 过滤空数据
                if assets_info['report_date']:
                    assets_list.append(assets_info)
            
            # 保存到缓存（10 分钟）
            self._set_to_cache(cache_key, assets_list, 'fund_info')
            logger.info(f"获取基金 {fund_code} 资产配置比例成功：{len(assets_list)}个日期")
            return assets_list
            
        except Exception as e:
            logger.error(f"获取基金资产配置比例失败 {fund_code} (dates={dates}): {e}")
            return []

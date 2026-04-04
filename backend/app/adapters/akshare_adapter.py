from typing import Optional, List, Dict, Any, Tuple, Callable
import akshare as ak
import pandas as pd
from loguru import logger
from datetime import datetime
import asyncio
import random
import time

from .base import (
    BaseDataAdapter,
    DataSourceType,
    StockBasicInfo,
    KLineData,
    SectorInfo,
    ChipData,
    MarketQuote
)
from .smart_retry import SmartRetryExecutor, ErrorClassifier, ErrorType
from .hybrid_tls_client import HybridTLSClient


class CacheEntry:
    """缓存条目类"""
    
    def __init__(self, data: Any, expires_at: float):
        self.data = data
        self.expires_at = expires_at
    
    def is_expired(self) -> bool:
        """检查缓存是否过期"""
        return time.time() > self.expires_at


class AkShareAdapter(BaseDataAdapter):
    """AkShare 数据源适配器
    
    特性：
    - 支持所有 akshare 接口
    - 包含反风控机制（请求延迟、重试、伪装）
    - 异步支持
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._last_request_time = 0
        self._min_request_interval = 1.5  # akshare 需要更保守
        
        # 缓存机制
        self._cache: Dict[str, CacheEntry] = {}
        
        # 反风控设置
        self._request_delay_range = (2.0, 4.0)  # 请求间隔（秒），默认更保守
        self._retry_base_delay = 3.0  # 重试基础延迟（秒）
        self._max_retries = 5  # 最大重试次数
        self._consecutive_failures = 0  # 连续失败次数
        self._adaptive_delay_enabled = True  # 启用自适应延迟
        self._is_initialized = False
        
        # 限流检测
        self._rate_limit_detected = False
        self._rate_limit_count = 0
        self._last_rate_limit_time = 0
        
        # User-Agent 轮换池（简化版：4 个主流浏览器）
        self._user_agents = [
            # Chrome 最新版（主力）
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            
            # Chrome 上一版（备用）
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            
            # Edge（备用）
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
            
            # Firefox（备用）
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
        ]
        self._current_user_agent = self._user_agents[0]  # 默认使用第一个
        
        # 智能重试执行器
        self._retry_executor = SmartRetryExecutor({
            'max_retries': 3,
            'base_wait_seconds': 2.0,
        })
        
        # 混合 TLS 客户端（用于降级）
        self._hybrid_client: Optional[HybridTLSClient] = None
        
        # 设置模式切换回调
        self._retry_executor.set_switch_mode_callback(self._fallback_to_hybrid_client)
    
    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.AKSHARE
    
    async def _ensure_credentials(self) -> bool:
        """确保凭证有效（懒加载获取）"""
        if not hasattr(self, '_injector') or self._injector is None:
            return False
        
        # 如果已有有效凭证，跳过
        if self._injector._is_patched:
            return True
        
        # 首次获取凭证
        try:
            logger.info("正在获取凭证（首次请求）...")
            
            # 初始化 Playwright（懒加载）
            if not await self._injector.initialize():
                logger.warning("Playwright 初始化失败，使用普通模式")
                return False
            
            # 获取凭证
            await self._injector.fetch_credentials('eastmoney.com')
            
            # 注入 TLS 指纹
            self._injector.patch_requests_with_tls()
            
            logger.info("凭证获取并注入成功")
            return True
            
        except Exception as e:
            logger.warning(f"获取凭证失败：{e}，使用普通模式")
            return False
    
    async def close(self) -> None:
        self._is_initialized = False
        logger.info("AkShare 适配器已关闭")
    
    # ========== 缓存机制 ===========
    
    def _get_cache_key(self, api_name: str, **kwargs) -> str:
        """生成缓存键
        
        Args:
            api_name: API 名称
            **kwargs: 参数键值对
            
        Returns:
            缓存键字符串
        """
        params = '_'.join(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return f"ak_{api_name}_{params}" if params else f"ak_{api_name}"
    
    def _get_from_cache(self, key: str, category: str = "default") -> Optional[Any]:
        """从缓存获取数据
        
        Args:
            key: 缓存键
            category: 缓存分类
            
        Returns:
            缓存的数据，如果不存在或已过期则返回 None
        """
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        if entry.is_expired():
            del self._cache[key]
            logger.debug(f"缓存已过期：{key}")
            return None
        
        logger.debug(f"缓存命中：{key}")
        return entry.data
    
    def _save_to_cache(self, key: str, data: Any, category: str = "default", ttl: int = 300) -> None:
        """保存数据到缓存
        
        Args:
            key: 缓存键
            data: 要保存的数据
            category: 缓存分类
            ttl: 生存时间（秒），默认 5 分钟
        """
        if data is None:
            return
        
        expires_at = time.time() + ttl
        self._cache[key] = CacheEntry(data, expires_at)
        logger.debug(f"保存到缓存：{key}, TTL={ttl}s")
    
    # ========== 反风控方法 ===========
    
    def _get_time_based_delay(self) -> Tuple[float, float]:
        """根据当前时间段获取合适的延迟范围
        
        Returns:
            tuple: (min_delay, max_delay)
        """
        current_hour = datetime.now().hour
        
        # 交易时段（9:30-11:30, 13:00-15:00）使用较长延迟
        if (9 <= current_hour <= 11) or (13 <= current_hour <= 14):
            return (1.5, 3.0)
        # 非交易时段使用较短延迟
        else:
            return (0.5, 1.5)
    
    async def _rate_limit(self) -> None:
        """异步请求限流"""
        if self._adaptive_delay_enabled:
            min_delay, max_delay = self._get_time_based_delay()
            
            # 如果检测到限流，大幅增加延迟
            if self._rate_limit_detected:
                min_delay *= 3
                max_delay *= 3
                logger.warning(f"检测到限流，使用 3 倍延迟：{min_delay:.1f}-{max_delay:.1f}秒")
            
            # 根据连续失败次数增加额外延迟
            if self._consecutive_failures > 0:
                extra_delay = min(self._consecutive_failures * 2, 10)
                min_delay += extra_delay
                max_delay += extra_delay
            
            delay = random.uniform(min_delay, max_delay)
        else:
            delay = random.uniform(*self._request_delay_range)
        
        logger.debug(f"AkShare 请求限流：延迟 {delay:.2f}秒")
        await asyncio.sleep(delay)
    
    def _detect_rate_limit(self, error: Exception) -> bool:
        """检测是否被限流
        
        Args:
            error: 捕获的异常
            
        Returns:
            bool: 是否检测到限流
        """
        error_msg = str(error).lower()
        rate_limit_keywords = [
            'connection aborted',
            'remote end closed',
            'too many requests',
            'rate limit',
            'frequency limit',
            'access denied',
            'ip blocked',
            'request rejected'
        ]
        
        is_rate_limit = any(keyword in error_msg for keyword in rate_limit_keywords)
        
        if is_rate_limit:
            current_time = time.time()
            # 5 分钟内多次限流才确认
            if current_time - self._last_rate_limit_time < 300:
                self._rate_limit_count += 1
                if self._rate_limit_count >= 3:
                    self._rate_limit_detected = True
                    logger.warning(f"确认被限流！5 分钟内{self._rate_limit_count}次触发")
            else:
                self._rate_limit_count = 1
                self._last_rate_limit_time = current_time
        
        return is_rate_limit
    
    def _rate_limit_sync(self) -> None:
        """同步请求限流"""
        delay = random.uniform(*self._request_delay_range)
        time.sleep(delay)
    
    def get_anti_wind_config(self) -> Dict[str, Any]:
        """获取反风控配置信息"""
        return {
            "request_delay_range": self._request_delay_range,
            "current_delay_range": self._get_time_based_delay() if self._adaptive_delay_enabled else self._request_delay_range,
            "adaptive_delay_enabled": self._adaptive_delay_enabled,
            "max_retries": self._max_retries,
            "consecutive_failures": self._consecutive_failures,
            "user_agent_pool_size": len(self._user_agents),
            "current_user_agent": self._current_user_agent[:50] + "...",
            "user_agent_rotation": "已启用"
        }
    
    def enable_adaptive_delay(self, enabled: bool = True) -> None:
        """启用/禁用自适应延迟
        
        Args:
            enabled: 是否启用自适应延迟
        """
        self._adaptive_delay_enabled = enabled
        status = "已启用" if enabled else "已禁用"
        logger.info(f"AkShare 自适应延迟：{status}")
    
    def reset_rate_limit_status(self) -> None:
        """重置限流状态（在成功请求后调用）"""
        if self._rate_limit_detected:
            self._rate_limit_detected = False
            self._rate_limit_count = 0
            self._last_rate_limit_time = 0
            logger.info("限流状态已重置")
    
    def set_custom_delay(self, min_delay: float, max_delay: float) -> None:
        """设置自定义延迟范围
        
        Args:
            min_delay: 最小延迟（秒）
            max_delay: 最大延迟（秒）
        """
        self._request_delay_range = (min_delay, max_delay)
        self._adaptive_delay_enabled = False  # 禁用自适应延迟
        logger.info(f"AkShare 自定义延迟范围：{min_delay}-{max_delay}秒（已禁用自适应延迟）")
    
    def _rotate_user_agent(self) -> None:
        """轮换 User-Agent"""
        old_ua = self._current_user_agent
        self._current_user_agent = random.choice(self._user_agents)
        logger.debug(f"User-Agent 已轮换：{old_ua[:50]}... -> {self._current_user_agent[:50]}...")
    
    def get_current_user_agent(self) -> str:
        """获取当前 User-Agent"""
        return self._current_user_agent
    
    @staticmethod
    def rate_limit_decorator(min_delay: float = 1.0, max_delay: float = 2.0, retries: int = 3) -> Callable:
        """限流装饰器（用于同步方法）
        
        Args:
            min_delay: 最小延迟（秒）
            max_delay: 最大延迟（秒）
            retries: 重试次数
        
        Example:
            @rate_limit_decorator(min_delay=1.5, max_delay=2.5, retries=3)
            def fetch_data():
                pass
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                self = args[0] if args else None
                for attempt in range(retries):
                    try:
                        # 请求前延迟
                        if hasattr(self, '_rate_limit_sync'):
                            self._rate_limit_sync()
                        
                        result = func(*args, **kwargs)
                        
                        # 成功后重置失败计数
                        if hasattr(self, '_consecutive_failures'):
                            self._consecutive_failures = 0
                        
                        return result
                    except Exception as e:
                        if hasattr(self, '_consecutive_failures'):
                            self._consecutive_failures += 1
                        
                        if attempt < retries - 1:
                            # 指数退避
                            delay = (2 ** attempt) * min_delay + random.uniform(0, 1)
                            logger.debug(f"{func.__name__} 请求失败，{delay:.1f}秒后重试（{attempt+1}/{retries}）: {e}")
                            time.sleep(delay)
                        else:
                            logger.error(f"{func.__name__} 失败，已达最大重试次数：{e}")
                            raise
                return None
            return wrapper
        return decorator
    
    @staticmethod
    def async_rate_limit_decorator(min_delay: float = 1.0, max_delay: float = 2.0, retries: int = 3) -> Callable:
        """异步限流装饰器
        
        Args:
            min_delay: 最小延迟（秒）
            max_delay: 最大延迟（秒）
            retries: 重试次数
        
        Example:
            @async_rate_limit_decorator(min_delay=1.5, max_delay=2.5, retries=3)
            async def fetch_data():
                pass
        """
        def decorator(func):
            async def wrapper(*args, **kwargs):
                self = args[0] if args else None
                for attempt in range(retries):
                    try:
                        # 请求前延迟
                        if hasattr(self, '_rate_limit'):
                            await self._rate_limit()
                        
                        result = await func(*args, **kwargs)
                        
                        # 成功后重置失败计数
                        if hasattr(self, '_consecutive_failures'):
                            self._consecutive_failures = 0
                        
                        return result
                    except Exception as e:
                        if hasattr(self, '_consecutive_failures'):
                            self._consecutive_failures += 1
                        
                        # 检测是否被限流
                        if hasattr(self, '_detect_rate_limit'):
                            if self._detect_rate_limit(e):
                                # 轮换 User-Agent
                                if hasattr(self, '_rotate_user_agent'):
                                    self._rotate_user_agent()
                        
                        if attempt < retries - 1:
                            # 指数退避 + 限流惩罚
                            base_delay = (2 ** attempt) * min_delay
                            if hasattr(self, '_rate_limit_detected') and self._rate_limit_detected:
                                base_delay *= 2  # 限流时延迟翻倍
                            
                            delay = base_delay + random.uniform(0, 1)
                            logger.debug(f"{func.__name__} 请求失败，{delay:.1f}秒后重试（{attempt+1}/{retries}）: {e}")
                            await asyncio.sleep(delay)
                        else:
                            logger.error(f"{func.__name__} 失败，已达最大重试次数：{e}")
                            raise
                return None
            return wrapper
        return decorator
    
    async def initialize(self) -> bool:
        """初始化 AkShare 适配器，集成凭证注入和 TLS 指纹伪装"""
        try:
            # 集成凭证注入器（带 TLS 指纹伪装）
            from .credential_injector import CredentialInjector
            
            self._injector = CredentialInjector({
                'tls_patch_mode': 'curl_cffi',
                'impersonate': 'chrome120',
                'headless': True,
            })
            
            # 懒加载：不立即初始化 Playwright，仅在需要时获取凭证
            # 懒加载 HybridTLSClient（仅在需要时初始化）
            self._hybrid_client: Optional[HybridTLSClient] = None
            
            logger.info("AkShare 适配器初始化成功（凭证注入模式待命 + 智能重试）")
            logger.info(f"  - TLS 指纹：curl_cffi (chrome120)")
            logger.info(f"  - 智能重试：已启用（自动切换模式）")
            logger.info(f"  - 降级方案：HybridTLSClient（懒加载，tls-client → curl_cffi → Playwright）")
            logger.info(f"  - 请求频率：自适应延迟（根据时间段和失败次数调整）")
            logger.info(f"  - 最大重试：{self._max_retries}次（指数退避）")
            
            self._is_initialized = True
            return True
            
        except Exception as e:
            logger.error(f"AkShare 适配器初始化失败：{e}")
            return False
    
    async def _fallback_to_hybrid_client(self, url: str, **kwargs) -> Optional[Dict]:
        """降级到混合 TLS 客户端（懒加载初始化）"""
        # 懒加载初始化 HybridTLSClient
        if self._hybrid_client is None:
            logger.info("首次使用 HybridTLSClient，正在初始化...")
            self._hybrid_client = HybridTLSClient({
                'playwright_pool_size': 2,
                'enable_http2': True,
                'fallback_to_playwright': True,
            })
            await self._hybrid_client.initialize()
            logger.info("HybridTLSClient 初始化完成")
        
        logger.info("检测到 TLS 指纹错误，降级到 HybridTLSClient...")
        
        try:
            result = await self._hybrid_client.get(
                url=url,
                headers=kwargs.get('headers'),
                cookies=kwargs.get('cookies'),
                timeout=kwargs.get('timeout', 30),
                api_type=kwargs.get('api_type', 'fallback')
            )
            
            logger.info(f"HybridTLSClient 请求成功：状态码 {result.get('status_code')}")
            return result
            
        except Exception as e:
            logger.error(f"HybridTLSClient 也失败：{e}")
            return None
    
    async def close(self) -> None:
        self._is_initialized = False
        logger.info("AkShare 适配器已关闭")
    
    async def get_stock_list(self, market: Optional[str] = None) -> List[StockBasicInfo]:
        """获取 A 股股票列表（带 TLS 指纹伪装 + 凭证注入）"""
        # 确保凭证有效（TLS 指纹伪装）
        await self._ensure_credentials()
        
        # 限流
        await self._rate_limit()
        
        def fetch_sync():
            df = ak.stock_zh_a_spot_em()
            stocks = []
            for _, row in df.iterrows():
                code = str(row["代码"])
                name = str(row["名称"])
                market_tag = "SH" if code.startswith("6") else "SZ"
                stocks.append(StockBasicInfo(code=code, name=name, market=market_tag))
            return stocks
        
        try:
            result = await self._retry_executor.execute(
                func=fetch_sync,
                context="get_stock_list"
            )
            return result or []
        except Exception as e:
            logger.error(f"获取股票列表失败：{e}")
            return []
    
    async def get_stock_info(self, code: str) -> Optional[StockBasicInfo]:
        """获取个股详细信息（带 TLS 指纹伪装 + 凭证注入 + 缓存）"""
        # 生成缓存键
        cache_key = self._get_cache_key('stock_info', code=code)
        cached = self._get_from_cache(cache_key, 'stock_basic')
        if cached:
            logger.debug(f"缓存命中：{cache_key}")
            return cached
        
        # 确保凭证有效（TLS 指纹伪装）
        await self._ensure_credentials()
        
        # 限流
        await self._rate_limit()
        
        def fetch_sync():
            df = ak.stock_individual_info_em(symbol=code)
            info_dict = dict(zip(df["item"], df["value"]))
            market_tag = "SH" if code.startswith("6") else "SZ"
            return StockBasicInfo(
                code=code,
                name=info_dict.get("股票简称", ""),
                market=market_tag,
                industry=info_dict.get("行业"),
                list_date=info_dict.get("上市时间"),
                total_shares=float(info_dict.get("总市值", 0)) / 100000000 if info_dict.get("总市值") else None
            )
        
        try:
            result = await self._retry_executor.execute(
                func=fetch_sync,
                context="get_stock_info"
            )
            # 保存到缓存（股票信息变化慢，缓存 10 分钟）
            if result:
                self._save_to_cache(cache_key, result, 'stock_basic', ttl=600)
            return result
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
        """获取个股 K 线数据（带 TLS 指纹伪装 + 凭证注入 + 缓存）"""
        # 生成缓存键
        cache_key = self._get_cache_key('kline', code=code, start=start_date, end=end_date, adjust=adjust)
        cached = self._get_from_cache(cache_key, 'kline')
        if cached:
            logger.debug(f"缓存命中：{cache_key}")
            return cached
        
        # 确保凭证有效（TLS 指纹伪装）
        await self._ensure_credentials()
        
        # 限流
        await self._rate_limit()
        
        adjust_map = {
            "qfq": "qfq",
            "hfq": "hfq",
            "": ""
        }
        adjust_type = adjust_map.get(adjust, "qfq")
        
        from app.utils.date_utils import to_int_date
        
        start_date_int = to_int_date(start_date) if start_date else 19900101
        end_date_int = to_int_date(end_date) if end_date else 20991231
        
        def fetch_sync():
            df = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_date_int,
                end_date=end_date_int,
                adjust=adjust_type
            )
            
            if df is None or df.empty:
                logger.warning(f"K 线数据为空：{code}")
                return []
            
            klines = []
            for _, row in df.iterrows():
                klines.append(KLineData(
                    code=code,
                    date=self.format_date(str(row["日期"])),
                    open=float(row["开盘"]),
                    high=float(row["最高"]),
                    low=float(row["最低"]),
                    close=float(row["收盘"]),
                    volume=float(row["成交量"]),
                    amount=float(row["成交额"]) if "成交额" in row else None,
                    turnover_rate=float(row["换手率"]) if "换手率" in row else None
                ))
            return klines
        
        try:
            result = await self._retry_executor.execute(
                func=fetch_sync,
                context="get_kline"
            )
            # 保存到缓存（K 线数据盘后更新，缓存到次日）
            if result:
                logger.info(f"获取 K 线数据成功 {code}: {len(result)}条")
                self._save_to_cache(cache_key, result, 'kline', ttl=3600)
            return result or []
        except Exception as e:
            logger.error(f"获取 K 线数据失败 {code}: {e}")
            return []
    
    async def get_market_index_kline(
        self,
        index_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[KLineData]:
        """获取大盘指数 K 线数据（带 TLS 指纹伪装 + 凭证注入）"""
        # 确保凭证有效（TLS 指纹伪装）
        await self._ensure_credentials()
        
        try:
            await self._rate_limit()
            
            # 使用 akshare 获取指数历史行情（正确的 API 是 index_zh_a_hist）
            df = ak.index_zh_a_hist(
                symbol=index_code,
                period="daily",
                start_date=start_date.replace("-", "") if start_date else "19900101",
                end_date=end_date.replace("-", "") if end_date else "20991231"
            )
            
            klines = []
            for _, row in df.iterrows():
                klines.append(KLineData(
                    code=index_code,
                    date=self.format_date(str(row["date"])),
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row["volume"]) if "volume" in row else 0,
                    amount=0  # 指数通常没有成交额数据
                ))
            
            return klines
            
        except Exception as e:
            logger.error(f"获取指数 K 线失败 {index_code}: {e}")
            return []
    
    async def get_realtime_quote(self, code: str) -> Dict[str, Any]:
        """获取个股实时行情（带 TLS 指纹伪装 + 凭证注入 + 缓存）"""
        # 生成缓存键
        cache_key = self._get_cache_key('realtime_quote', code=code)
        cached = self._get_from_cache(cache_key, 'quote')
        if cached:
            logger.debug(f"缓存命中：{cache_key}")
            return cached
        
        # 确保凭证有效（TLS 指纹伪装）
        await self._ensure_credentials()
        
        # 限流
        await self._rate_limit()
        
        def fetch_sync():
            df = ak.stock_zh_a_spot_em()
            row = df[df["代码"] == code]
            if row.empty:
                return None
            row = row.iloc[0]
            return {
                "code": code,
                "name": row["名称"],
                "price": float(row["最新价"]),
                "change": float(row["涨跌额"]),
                "change_pct": float(row["涨跌幅"]),
                "volume": float(row["成交量"]),
                "amount": float(row["成交额"]),
                "high": float(row["最高"]),
                "low": float(row["最低"]),
                "open": float(row["今开"]),
                "prev_close": float(row["昨收"]),
                "turnover_rate": float(row["换手率"]) if "换手率" in row else None
            }
        
        try:
            result = await self._retry_executor.execute(
                func=fetch_sync,
                context="get_realtime_quote"
            )
            # 保存到缓存（实时行情变化快，缓存 60 秒）
            if result:
                self._save_to_cache(cache_key, result, 'quote', ttl=60)
            return result or {}
        except Exception as e:
            logger.error(f"获取实时行情失败 {code}: {e}")
            return {}
    
    async def get_market_realtime_quotes(
        self,
        market_types: Optional[List[str]] = None
    ) -> List[MarketQuote]:
        """获取市场实时行情（带 TLS 指纹伪装 + 凭证注入）"""
        # 确保凭证有效（TLS 指纹伪装）
        await self._ensure_credentials()
        
        # 限流
        await self._rate_limit()
        
        def fetch_sync():
            df = ak.stock_zh_a_spot_em()
            
            if df is None or df.empty:
                return []
            
            quotes = []
            for _, row in df.iterrows():
                def safe_float(value, default=None):
                    try:
                        if value is None or value == '' or value == '-':
                            return default
                        return float(value)
                    except (ValueError, TypeError):
                        return default
                
                code = str(row.get("代码", "")).zfill(6)
                if not code:
                    continue
                
                quotes.append(MarketQuote(
                    code=code,
                    name=str(row.get("名称", "")),
                    change_pct=safe_float(row.get("涨跌幅")),
                    price=safe_float(row.get("最新价")),
                    high=safe_float(row.get("最高")),
                    low=safe_float(row.get("最低")),
                    open=safe_float(row.get("今开")),
                    change=safe_float(row.get("涨跌额")),
                    turnover_rate=safe_float(row.get("换手率")),
                    volume_ratio=safe_float(row.get("量比")),
                    pe_ratio=safe_float(row.get("市盈率 - 动态")),
                    volume=safe_float(row.get("成交量")),
                    amount=safe_float(row.get("成交额")),
                    prev_close=safe_float(row.get("昨收")),
                    total_market_cap=safe_float(row.get("总市值")),
                    float_market_cap=safe_float(row.get("流通市值")),
                    market_type="A 股"
                ))
            return quotes
        
        try:
            result = await self._retry_executor.execute(
                func=fetch_sync,
                context="get_market_realtime_quotes"
            )
            quotes = result or []
            
            if quotes:
                logger.info(f"akshare 获取市场实时行情成功：{len(quotes)}条")
            return quotes
            
        except Exception as e:
            logger.error(f"akshare 获取市场实时行情失败：{e}")
            return []
    
    async def get_sector_list(self, sector_type: str = "industry") -> List[SectorInfo]:
        """获取板块列表（高敏感 API，需要凭证注入 + 智能重试）"""
        # 确保凭证有效（懒加载）
        if not await self._ensure_credentials():
            logger.warning("凭证注入失败，尝试直接请求")
        
        async def fetch():
            if sector_type == "industry":
                df = ak.stock_board_industry_name_em()
            elif sector_type == "concept":
                df = ak.stock_board_concept_name_em()
            else:
                df = ak.stock_board_industry_name_em()
            
            # 检查返回值类型，akshare 可能返回错误码（整数）而不是 DataFrame
            if df is None:
                logger.warning(f"akshare 返回 None，无法获取板块列表")
                return []
            
            if isinstance(df, int):
                logger.warning(f"akshare 返回错误码：{df}，可能是 API 限流或网络问题")
                raise ValueError(f"akshare 返回错误码：{df}")
            
            if not hasattr(df, 'iterrows'):
                logger.warning(f"akshare 返回非 DataFrame 类型：{type(df)}")
                raise TypeError(f"akshare 返回类型错误：{type(df)}，期望 DataFrame")
            
            sectors = []
            for _, row in df.iterrows():
                sectors.append(SectorInfo(
                    code=str(row["板块代码"]),
                    name=str(row["板块名称"]),
                    sector_type=sector_type,
                    change_pct=float(row["涨跌幅"]) if "涨跌幅" in row else None,
                    volume=float(row["成交量"]) if "成交量" in row else None
                ))
            return sectors
        
        try:
            # 使用智能重试执行器
            result = await self._retry_executor.execute(
                func=fetch,
                context="get_sector_list",
                on_switch_mode=lambda: self._handle_sector_list_fallback(sector_type)
            )
            return result or []
        except Exception as e:
            logger.error(f"get_sector_list 智能重试失败：{e}")
            # 最后尝试降级方案
            return await self._handle_sector_list_fallback(sector_type)
    
    async def _handle_sector_list_fallback(self, sector_type: str) -> List[SectorInfo]:
        """降级处理：使用 HybridTLSClient 获取板块列表"""
        logger.info(f"使用 HybridTLSClient 获取 {sector_type} 板块列表...")
        
        try:
            if sector_type == "industry":
                url = "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=500&fs=m:90+t:1&fields=f12,f13,f14"
            else:
                url = "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=500&fs=m:90+t:2&fields=f12,f13,f14"
            
            result = await self._fallback_to_hybrid_client(url, api_type="sector_list")
            
            if result and result.get('ok'):
                import json
                data = json.loads(result['text'])
                if data.get('data') and data['data'].get('diff'):
                    sectors = []
                    for item in data['data']['diff']:
                        sectors.append(SectorInfo(
                            code=str(item.get('f12', '')),
                            name=str(item.get('f14', '')),
                            sector_type=sector_type,
                            change_pct=float(item.get('f3', 0)) if item.get('f3') else None,
                            volume=float(item.get('f5', 0)) if item.get('f5') else None
                        ))
                    logger.info(f"HybridTLSClient 获取板块列表成功：{len(sectors)}个")
                    return sectors
            
            logger.warning(f"HybridTLSClient 获取板块列表失败")
            return []
            
        except Exception as e:
            logger.error(f"降级方案也失败：{e}")
            return []
    
    async def get_sector_components(self, sector_code: str) -> List[str]:
        """获取板块成分股（带 TLS 指纹伪装 + 凭证注入）"""
        # 确保凭证有效（TLS 指纹伪装）
        await self._ensure_credentials()
        
        # 限流
        await self._rate_limit()
        
        def fetch_sync():
            df = ak.stock_board_industry_cons_em(symbol=sector_code)
            
            if df is None or isinstance(df, int) or not hasattr(df, 'columns'):
                logger.warning(f"akshare 返回无效数据：{type(df)}")
                return []
            
            return df["代码"].tolist()
        
        try:
            result = await self._retry_executor.execute(
                func=fetch_sync,
                context="get_sector_components"
            )
            return result or []
        except Exception as e:
            logger.error(f"获取板块成分股失败 {sector_code}: {e}")
            return []
    
    async def get_sector_ranking(
        self,
        sector_type: str = "industry",
        sort_by: str = "change_pct",
        limit: int = 20
    ) -> List[SectorInfo]:
        """获取板块排名（带 TLS 指纹伪装 + 凭证注入）"""
        # 确保凭证有效（TLS 指纹伪装）
        await self._ensure_credentials()
        
        # 限流
        await self._rate_limit()
        
        def fetch_sync():
            if sector_type == "industry":
                df = ak.stock_board_industry_name_em()
            else:
                df = ak.stock_board_concept_name_em()
            
            if df is None or isinstance(df, int) or not hasattr(df, 'iterrows'):
                logger.warning(f"akshare 返回无效数据：{type(df)}")
                return []
            
            sort_col = "涨跌幅" if sort_by == "change_pct" else "成交量"
            df = df.sort_values(by=sort_col, ascending=False)
            df = df.head(limit)
            
            sectors = []
            for _, row in df.iterrows():
                sectors.append(SectorInfo(
                    code=str(row["板块代码"]),
                    name=str(row["板块名称"]),
                    sector_type=sector_type,
                    change_pct=float(row["涨跌幅"]) if "涨跌幅" in row else None
                ))
            return sectors
        
        try:
            result = await self._retry_executor.execute(
                func=fetch_sync,
                context="get_sector_ranking"
            )
            return result or []
        except Exception as e:
            logger.error(f"获取板块排名失败：{e}")
            return []
    
    async def get_chip_data(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[ChipData]:
        """获取筹码数据（带 TLS 指纹伪装 + 凭证注入）"""
        # 确保凭证有效（TLS 指纹伪装）
        await self._ensure_credentials()
        
        # 限流
        await self._rate_limit()
        
        def fetch_sync():
            df = ak.stock_zh_a_gdhs(symbol=code)
            if df.empty:
                return []
            
            # 查找日期列
            date_column = None
            for col in ['报告日期', '股东人数', '股东人数', '日期']:
                if col in df.columns:
                    date_column = col
                    break
            
            if not date_column:
                logger.warning(f"未找到日期列，可用列：{df.columns.tolist()}")
                return []
            
            chip_data = []
            for _, row in df.iterrows():
                date = str(row[date_column])
                if start_date and date < start_date:
                    continue
                if end_date and date > end_date:
                    continue
                
                # 查找股东人数列
                count_column = None
                for col in ['股东人数', '股东总人数']:
                    if col in df.columns:
                        count_column = col
                        break
                
                if not count_column:
                    continue
                
                chip_data.append(ChipData(
                    code=code,
                    date=date,
                    shareholder_count=float(row[count_column]),
                    avg_shares_per_holder=float(row["户均持股数量"]) if "户均持股数量" in row else None
                ))
            return chip_data
        
        try:
            result = await self._retry_executor.execute(
                func=fetch_sync,
                context="get_chip_data"
            )
            return result or []
        except Exception as e:
            logger.error(f"获取筹码数据失败 {code}: {e}")
            return []
    
    async def get_market_moneyflow_dc(
        self,
        market_type: str = 'all',
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取大盘资金流向（带 TLS 指纹伪装 + 凭证注入）"""
        # 确保凭证有效（TLS 指纹伪装）
        await self._ensure_credentials()
        
        # 限流
        await self._rate_limit()
        
        def fetch_sync():
            # 使用 akshare 获取全市场资金流向
            df = ak.stock_individual_fund_flow()
            
            if df is None or df.empty:
                return {}
            
            # 计算主力资金流向
            main_net = float(df['主力净流入'].sum()) if '主力净流入' in df.columns else 0
            buy_elg = float(df['超大单净流入'].sum()) if '超大单净流入' in df.columns else 0
            buy_big = float(df['大单净流入'].sum()) if '大单净流入' in df.columns else 0
            sell_medium = float(df['中单净流入'].sum()) if '中单净流入' in df.columns else 0
            sell_small = float(df['小单净流入'].sum()) if '小单净流入' in df.columns else 0
            
            # 统计涨跌家数
            rise_count = len(df[df['涨跌幅'] > 0]) if '涨跌幅' in df.columns else 0
            fall_count = len(df[df['涨跌幅'] < 0]) if '涨跌幅' in df.columns else 0
            
            return {
                'market_type': market_type,
                'main_net_amount': main_net,
                'buy_elg_amount': buy_elg,
                'buy_big_amount': buy_big,
                'sell_medium_amount': sell_medium,
                'sell_small_amount': sell_small,
                'rise_count': int(rise_count),
                'fall_count': int(fall_count),
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        
        try:
            result = await self._retry_executor.execute(
                func=fetch_sync,
                context="get_market_moneyflow_dc"
            )
            result_dict = result or {}
            
            if result_dict:
                logger.info(f"获取大盘资金流向成功：{market_type}")
            return result_dict
            
        except Exception as e:
            logger.error(f"获取大盘资金流向失败 {market_type}: {e}")
            return {}
    
    async def get_stock_financial(self, code: str) -> Dict[str, Any]:
        """获取财务数据（带 TLS 指纹伪装 + 凭证注入）"""
        # 确保凭证有效（TLS 指纹伪装）
        await self._ensure_credentials()
        
        # 限流
        await self._rate_limit()
        
        def fetch_sync():
            df = ak.stock_financial_abstract_ths(symbol=code, indicator="全部") 
            return df.to_dict("records")
        
        try:
            result = await self._retry_executor.execute(
                func=fetch_sync,
                context="get_stock_financial"
            )
            return result or {}
        except Exception as e:
            logger.error(f"获取财务数据失败 {code}: {e}")
            return {}
    
    # ========== 东方财富特色数据接口（从 EastMoneyAdapter 合并）==========
    
    async def get_stock_changes(self, change_type: str = "big_buy") -> List[Any]:
        """获取盘口异动数据（带 TLS 指纹伪装 + 凭证注入）
        
        Args:
            change_type: 异动类型，可选：
                - rocket: 火箭发射
                - rebound: 快速反弹
                - big_buy: 大笔买入
                - limit_up: 封涨停板
                - limit_down: 封跌停板
                等
        
        Returns:
            盘口异动数据列表
        """
        # 确保凭证有效（TLS 指纹伪装）
        await self._ensure_credentials()
        
        # 限流
        await self._rate_limit()
        
        def fetch_sync():
            df = ak.stock_change_em(symbol=change_type)
            
            if df is None or df.empty:
                return []
            
            changes = []
            for _, row in df.iterrows():
                changes.append({
                    'code': str(row.get('代码', '')),
                    'name': str(row.get('名称', '')),
                    'change_pct': float(row.get('涨跌幅', 0)) if pd.notna(row.get('涨跌幅')) else None,
                    'change': float(row.get('涨跌额', 0)) if pd.notna(row.get('涨跌额')) else None,
                    'volume': float(row.get('成交量', 0)) if pd.notna(row.get('成交量')) else None,
                    'amount': float(row.get('成交额', 0)) if pd.notna(row.get('成交额')) else None,
                    'change_reason': str(row.get('异动类型', ''))
                })
            return changes
        
        try:
            result = await self._retry_executor.execute(
                func=fetch_sync,
                context="get_stock_changes"
            )
            if result:
                logger.info(f"获取盘口异动数据成功，共{len(result)}条")
            return result or []
        except Exception as e:
            logger.error(f"获取盘口异动数据失败：{e}")
            return []
    
    async def get_zt_pool(self, date: Optional[str] = None) -> List[Any]:
        """获取涨停股池数据（带 TLS 指纹伪装 + 凭证注入）
        
        Args:
            date: 日期，格式 YYYYMMDD，默认为今日
        
        Returns:
            涨停股池数据列表
        """
        # 确保凭证有效（TLS 指纹伪装）
        await self._ensure_credentials()
        
        # 限流
        await self._rate_limit()
        
        if not date:
            date = datetime.now().strftime('%Y%m%d')
        
        def fetch_sync():
            df = ak.stock_zt_pool_em(date=date)
            
            if df is None or df.empty:
                return []
            
            zt_stocks = []
            for _, row in df.iterrows():
                zt_stocks.append({
                    'code': str(row.get('代码', '')),
                    'name': str(row.get('名称', '')),
                    'change_pct': float(row.get('涨跌幅', 0)) if pd.notna(row.get('涨跌幅')) else None,
                    'latest_price': float(row.get('最新价', 0)) if pd.notna(row.get('最新价')) else None,
                    'turnover': float(row.get('成交额', 0)) if pd.notna(row.get('成交额')) else None,
                    'float_mv': float(row.get('流通市值', 0)) if pd.notna(row.get('流通市值')) else None,
                    'total_mv': float(row.get('总市值', 0)) if pd.notna(row.get('总市值')) else None,
                    'turnover_rate': float(row.get('换手率', 0)) if pd.notna(row.get('换手率')) else None,
                    'seal_fund': float(row.get('封板资金', 0)) if pd.notna(row.get('封板资金')) else None,
                    'first_seal_time': str(row.get('首次封板时间', '')),
                    'last_seal_time': str(row.get('最后封板时间', '')),
                    'open_count': int(row.get('炸板次数', 0)) if pd.notna(row.get('炸板次数')) else None,
                    'zt_stats': str(row.get('涨停统计', '')),
                    'continuous_count': int(row.get('连板数', 1)) if pd.notna(row.get('连板数')) else None,
                    'industry': str(row.get('所属行业', ''))
                })
            return zt_stocks
        
        try:
            result = await self._retry_executor.execute(
                func=fetch_sync,
                context="get_zt_pool"
            )
            if result:
                logger.info(f"获取涨停股池数据成功：{date}, 共{len(result)}条")
            return result or []
        except Exception as e:
            logger.error(f"获取涨停股池数据失败：{e}")
            return []
    
    async def get_zt_pool_previous(self, date: Optional[str] = None) -> List[Any]:
        """获取昨日涨停股池数据（带 TLS 指纹伪装 + 凭证注入）
        
        Args:
            date: 日期，格式 YYYYMMDD，默认为昨日
        
        Returns:
            昨日涨停股池数据列表
        """
        # 确保凭证有效（TLS 指纹伪装）
        await self._ensure_credentials()
        
        # 限流
        await self._rate_limit()
        
        if not date:
            date = datetime.now().strftime('%Y%m%d')
        
        def fetch_sync():
            df = ak.stock_zt_pool_previous_em(date=date)
            
            if df is None or df.empty:
                return []
            
            zt_stocks = []
            for _, row in df.iterrows():
                zt_stocks.append({
                    'code': str(row.get('代码', '')),
                    'name': str(row.get('名称', '')),
                    'change_pct': float(row.get('涨跌幅', 0)) if pd.notna(row.get('涨跌幅')) else None,
                    'latest_price': float(row.get('最新价', 0)) if pd.notna(row.get('最新价')) else None,
                    'limit_up_price': float(row.get('涨停价', 0)) if pd.notna(row.get('涨停价')) else None,
                    'turnover': float(row.get('成交额', 0)) if pd.notna(row.get('成交额')) else None,
                    'float_mv': float(row.get('流通市值', 0)) if pd.notna(row.get('流通市值')) else None,
                    'total_mv': float(row.get('总市值', 0)) if pd.notna(row.get('总市值')) else None,
                    'turnover_rate': float(row.get('换手率', 0)) if pd.notna(row.get('换手率')) else None,
                    'speed_pct': float(row.get('涨速', 0)) if pd.notna(row.get('涨速')) else None,
                    'amplitude': float(row.get('振幅', 0)) if pd.notna(row.get('振幅')) else None
                })
            return zt_stocks
        
        try:
            result = await self._retry_executor.execute(
                func=fetch_sync,
                context="get_zt_pool_previous"
            )
            if result:
                logger.info(f"获取昨日涨停股池数据成功：{date}, 共{len(result)}条")
            return result or []
        except Exception as e:
            logger.error(f"获取昨日涨停股池数据失败：{e}")
            return []
    
    async def get_zt_strong(self, date: Optional[str] = None) -> List[Any]:
        """获取强势股池数据（连续涨停股）（带 TLS 指纹伪装 + 凭证注入）
        
        Args:
            date: 日期，格式 YYYYMMDD，默认为今日
        
        Returns:
            强势股池数据列表
        """
        # 确保凭证有效（TLS 指纹伪装）
        await self._ensure_credentials()
        
        # 限流
        await self._rate_limit()
        
        if not date:
            date = datetime.now().strftime('%Y%m%d')
        
        def fetch_sync():
            df = ak.stock_zt_strong_em(date=date)
            
            if df is None or df.empty:
                return []
            
            zt_stocks = []
            for _, row in df.iterrows():
                zt_stocks.append({
                    'code': str(row.get('代码', '')),
                    'name': str(row.get('名称', '')),
                    'change_pct': float(row.get('涨跌幅', 0)) if pd.notna(row.get('涨跌幅')) else None,
                    'latest_price': float(row.get('最新价', 0)) if pd.notna(row.get('最新价')) else None,
                    'continuous_count': int(row.get('连板数', 1)) if pd.notna(row.get('连板数')) else None,
                    'industry': str(row.get('所属行业', '')),
                    'reason': str(row.get('涨停理由', ''))
                })
            return zt_stocks
        
        try:
            result = await self._retry_executor.execute(
                func=fetch_sync,
                context="get_zt_strong"
            )
            if result:
                logger.info(f"获取强势股池数据成功：{date}, 共{len(result)}条")
            return result or []
        except Exception as e:
            logger.error(f"获取强势股池数据失败：{e}")
            return []
    
    async def get_zt_sub_new(self, date: Optional[str] = None) -> List[Any]:
        """获取次新股涨停池数据（带 TLS 指纹伪装 + 凭证注入）
        
        Args:
            date: 日期，格式 YYYYMMDD，默认为今日
        
        Returns:
            次新股涨停池数据列表
        """
        # 确保凭证有效（TLS 指纹伪装）
        await self._ensure_credentials()
        
        # 限流
        await self._rate_limit()
        
        if not date:
            date = datetime.now().strftime('%Y%m%d')
        
        def fetch_sync():
            df = ak.stock_zt_sub_new_em(date=date)
            
            if df is None or df.empty:
                return []
            
            zt_stocks = []
            for _, row in df.iterrows():
                zt_stocks.append({
                    'code': str(row.get('代码', '')),
                    'name': str(row.get('名称', '')),
                    'change_pct': float(row.get('涨跌幅', 0)) if pd.notna(row.get('涨跌幅')) else None,
                    'latest_price': float(row.get('最新价', 0)) if pd.notna(row.get('最新价')) else None,
                    'turnover': float(row.get('成交额', 0)) if pd.notna(row.get('成交额')) else None,
                    'float_mv': float(row.get('流通市值', 0)) if pd.notna(row.get('流通市值')) else None,
                    'total_mv': float(row.get('总市值', 0)) if pd.notna(row.get('总市值')) else None,
                    'turnover_rate': float(row.get('换手率', 0)) if pd.notna(row.get('换手率')) else None,
                    'open_count': int(row.get('炸板次数', 0)) if pd.notna(row.get('炸板次数')) else None,
                    'industry': str(row.get('所属行业', '')),
                    'list_date': str(row.get('上市日期', ''))
                })
            return zt_stocks
        
        try:
            result = await self._retry_executor.execute(
                func=fetch_sync,
                context="get_zt_sub_new"
            )
            if result:
                logger.info(f"获取次新股涨停池数据成功：{date}, 共{len(result)}条")
            return result or []
        except Exception as e:
            logger.error(f"获取次新股涨停池数据失败：{e}")
            return []
    
    async def get_board_changes(self) -> List[Any]:
        """获取板块异动数据（带 TLS 指纹伪装 + 凭证注入）
        
        Returns:
            板块异动数据列表
        """
        # 确保凭证有效（TLS 指纹伪装）
        await self._ensure_credentials()
        
        # 限流
        await self._rate_limit()
        
        def fetch_sync():
            df = ak.stock_board_change_em()
            
            if df is None or df.empty:
                return []
            
            changes = []
            for _, row in df.iterrows():
                changes.append({
                    'board_name': str(row.get('板块名称', '')),
                    'change_pct': float(row.get('涨跌幅', 0)) if pd.notna(row.get('涨跌幅')) else None,
                    'net_inflow': float(row.get('主力净流入', 0)) if pd.notna(row.get('主力净流入')) else None,
                    'change_count': int(row.get('板块异动总次数', 0)) if pd.notna(row.get('板块异动总次数')) else None,
                    'top_stock_code': str(row.get('板块异动最频繁个股及所属类型 - 股票代码', '')),
                    'top_stock_name': str(row.get('板块异动最频繁个股及所属类型 - 股票名称', '')),
                    'top_stock_type': str(row.get('板块异动最频繁个股及所属类型 - 买卖方向', '')),
                    'change_types': row.get('板块具体异动类型列表及出现次数', [])
                })
            return changes
        
        try:
            result = await self._retry_executor.execute(
                func=fetch_sync,
                context="get_board_changes"
            )
            if result:
                logger.info(f"获取板块异动数据成功，共{len(result)}条")
            return result or []
        except Exception as e:
            logger.error(f"获取板块异动数据失败：{e}")
            return []
    
    async def get_stock_info_sh_name_code(self, symbol: str = "主板 A 股") -> List[Any]:
        """获取上海证券交易所股票列表（带 TLS 指纹伪装 + 凭证注入）"""
        # 确保凭证有效（TLS 指纹伪装）
        await self._ensure_credentials()
        
        # 限流
        await self._rate_limit()
        
        def fetch_sync():
            df = ak.stock_info_sh_name_code(symbol=symbol)
            
            if df is None or df.empty:
                return []
            
            stocks = []
            for _, row in df.iterrows():
                stocks.append({
                    'code': str(row.get('证券代码', '')),
                    'name': str(row.get('证券简称', ''))
                })
            return stocks
        
        try:
            result = await self._retry_executor.execute(
                func=fetch_sync,
                context="get_stock_info_sh_name_code"
            )
            if result:
                logger.info(f"获取上交所股票列表成功 ({symbol}), 共{len(result)}条")
            return result or []
        except Exception as e:
            logger.error(f"获取上交所股票列表失败：{e}")
            return []
    
    async def get_stock_info_sz_name_code(self, symbol: str = "主板 A 股") -> List[Any]:
        """获取深圳证券交易所股票列表（带 TLS 指纹伪装 + 凭证注入）"""
        # 确保凭证有效（TLS 指纹伪装）
        await self._ensure_credentials()
        
        # 限流
        await self._rate_limit()
        
        def fetch_sync():
            df = ak.stock_info_sz_name_code(symbol=symbol)
            
            if df is None or df.empty:
                return []
            
            stocks = []
            for _, row in df.iterrows():
                stocks.append({
                    'code': str(row.get('证券代码', '')),
                    'name': str(row.get('证券简称', ''))
                })
            return stocks
        
        try:
            result = await self._retry_executor.execute(
                func=fetch_sync,
                context="get_stock_info_sz_name_code"
            )
            if result:
                logger.info(f"获取深交所股票列表成功 ({symbol}), 共{len(result)}条")
            return result or []
        except Exception as e:
            logger.error(f"获取深交所股票列表失败：{e}")
            return []
    
    async def get_stock_info_bj_name_code(self) -> List[Any]:
        """获取北京证券交易所股票列表（带 TLS 指纹伪装 + 凭证注入）"""
        # 确保凭证有效（TLS 指纹伪装）
        await self._ensure_credentials()
        
        # 限流
        await self._rate_limit()
        
        def fetch_sync():
            df = ak.stock_info_bj_name_code()
            
            if df is None or df.empty:
                return []
            
            stocks = []
            for _, row in df.iterrows():
                stocks.append({
                    'code': str(row.get('证券代码', '')),
                    'name': str(row.get('证券简称', ''))
                })
            return stocks
        
        try:
            result = await self._retry_executor.execute(
                func=fetch_sync,
                context="get_stock_info_bj_name_code"
            )
            if result:
                logger.info(f"获取北交所股票列表成功，共{len(result)}条")
            return result or []
        except Exception as e:
            logger.error(f"获取北交所股票列表失败：{e}")
            return []
    
    async def get_board_industry_name_em(self) -> List[Any]:
        """获取东方财富行业板块列表（带 TLS 指纹伪装 + 凭证注入）"""
        # 确保凭证有效（TLS 指纹伪装）
        await self._ensure_credentials()
        
        # 限流
        await self._rate_limit()
        
        def fetch_sync():
            df = ak.stock_board_industry_name_em()
            
            if df is None or not hasattr(df, 'iterrows') or df.empty:
                return []
            
            boards = []
            for _, row in df.iterrows():
                boards.append({
                    'code': str(row.get('板块代码', '')),
                    'name': str(row.get('板块名称', '')),
                    'change_pct': float(row.get('涨跌幅', 0)) if pd.notna(row.get('涨跌幅')) else None,
                    'change': float(row.get('涨跌额', 0)) if pd.notna(row.get('涨跌额')) else None,
                    'total_mv': float(row.get('总市值', 0)) if pd.notna(row.get('总市值')) else None,
                    'turnover': float(row.get('成交额', 0)) if pd.notna(row.get('成交额')) else None
                })
            return boards
        
        try:
            result = await self._retry_executor.execute(
                func=fetch_sync,
                context="get_board_industry_name_em"
            )
            if result:
                logger.info(f"获取东方财富行业板块列表成功，共{len(result)}条")
            return result or []
        except Exception as e:
            logger.error(f"获取东方财富行业板块列表失败：{e}")
            return []
    
    async def get_board_industry_cons_em(self, symbol: str) -> List[Any]:
        """获取东方财富行业板块成份股（带 TLS 指纹伪装 + 凭证注入）"""
        # 确保凭证有效（TLS 指纹伪装）
        await self._ensure_credentials()
        
        # 限流
        await self._rate_limit()
        
        def fetch_sync():
            df = ak.stock_board_industry_cons_em(symbol=symbol)
            
            if df is None or df.empty:
                return []
            
            cons_data = []
            for _, row in df.iterrows():
                cons_data.append({
                    'code': str(row.get('代码', '')),
                    'name': str(row.get('名称', '')),
                    'change_pct': float(row.get('涨跌幅', 0)) if pd.notna(row.get('涨跌幅')) else None,
                    'latest_price': float(row.get('最新价', 0)) if pd.notna(row.get('最新价')) else None,
                    'change': float(row.get('涨跌额', 0)) if pd.notna(row.get('涨跌额')) else None,
                    'volume': float(row.get('成交量', 0)) if pd.notna(row.get('成交量')) else None,
                    'amount': float(row.get('成交额', 0)) if pd.notna(row.get('成交额')) else None,
                    'turnover_rate': float(row.get('换手率', 0)) if pd.notna(row.get('换手率')) else None,
                    'pe_ratio': float(row.get('市盈率 - 动态', 0)) if pd.notna(row.get('市盈率 - 动态')) else None,
                    'pb_ratio': float(row.get('市净率', 0)) if pd.notna(row.get('市净率')) else None
                })
            return cons_data
        
        try:
            result = await self._retry_executor.execute(
                func=fetch_sync,
                context="get_board_industry_cons_em"
            )
            if result:
                logger.info(f"获取东方财富行业板块成份股成功 ({symbol}), 共{len(result)}条")
            return result or []
        except Exception as e:
            logger.error(f"获取东方财富行业板块成份股失败：{e}")
            return []

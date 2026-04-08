from typing import Optional, List, Dict, Any, Tuple, Callable, Union
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
from .anti_wind import (
    AntiWindFacade,
    CookieInjectStrategy,
    TLSFingerprintStrategy,
    RateLimitStrategy,
    UARotatorStrategy,
    SmartRetryStrategy,
    ProxyPoolStrategy,
)
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
        
        # 缓存机制
        self._cache: Dict[str, CacheEntry] = {}
        
        # 反风控门面（统一管理所有策略）
        self.anti_wind = AntiWindFacade({
            'enable_cookie_inject': True,
            'enable_tls_fingerprint': True,
            'enable_rate_limit': True,
            'enable_ua_rotation': True,
            'enable_smart_retry': True,
            'enable_proxy_pool': False,  # 默认禁用，需要时启用
            'max_retries': 3,
            'rate_limit_config': {
                'base_delay_range': (2.0, 4.0),  # akshare 需要更保守
                'adaptive_delay_enabled': True,
            },
            'retry_config': {
                'max_retries': 3,
                'base_wait_seconds': 2.0,
            },
            'ua_config': {
                'rotation_interval': 10,
            },
        })
        
        # 混合 TLS 客户端（用于降级）
        self._hybrid_client: Optional[HybridTLSClient] = None
        
        self._is_initialized = False
        
        logger.info("AkShare 适配器已初始化（使用 AntiWindFacade 统一管理反爬策略）")
    
    async def _execute_with_anti_wind(
        self,
        request_func: Callable,
        url: str = "",
        method: str = "GET",
        **kwargs
    ) -> Any:
        """使用 AntiWindFacade 执行请求
        
        Args:
            request_func: 请求函数（同步或异步）
            url: 请求 URL（可选）
            method: 请求方法（可选）
            **kwargs: 其他参数
        
        Returns:
            请求结果
        """
        return await self.anti_wind.execute_with_strategies(
            request_func=request_func,
            url=url,
            method=method,
            **kwargs
        )
    
    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.AKSHARE
    
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
        """异步请求限流 - 由 AntiWindFacade 的 RateLimitStrategy 处理"""
        # 此方法已废弃，由 AntiWindFacade 自动处理
        logger.debug("_rate_limit 已废弃，由 RateLimitStrategy 处理")
        return
    
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
        """同步请求限流 - 由 AntiWindFacade 的 RateLimitStrategy 处理"""
        # 此方法已废弃，由 AntiWindFacade 自动处理
        logger.debug("_rate_limit_sync 已废弃，由 RateLimitStrategy 处理")
        return
    
    def get_anti_wind_config(self) -> Dict[str, Any]:
        """获取反风控配置信息"""
        return {
            "max_retries": self.anti_wind.config.get('max_retries', 3) if hasattr(self, 'anti_wind') else 3,
            "consecutive_failures": self._consecutive_failures,
            "anti_wind_strategies": len(self.anti_wind.strategies) if hasattr(self, 'anti_wind') else 0,
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
    
    def set_custom_delay_range(self, min_delay: float, max_delay: float) -> None:
        """【已废弃】设置自定义延迟范围 - 由 AntiWindFacade 的 RateLimitStrategy 处理
        
        Args:
            min_delay: 最小延迟（秒）
            max_delay: 最大延迟（秒）
        """
        # 此方法已废弃，由 AntiWindFacade 的 RateLimitStrategy 处理
        logger.debug("set_custom_delay_range 已废弃，由 RateLimitStrategy 处理")
        return
    
    def _rotate_user_agent(self) -> None:
        """【已废弃】轮换 User-Agent - 由 AntiWindFacade 的 UARotatorStrategy 处理"""
        # 此方法已废弃，保留仅用于向后兼容
        logger.debug("_rotate_user_agent 已废弃，由 UARotatorStrategy 处理")
    
    def get_current_user_agent(self) -> str:
        """获取当前 User-Agent（从 AntiWindFacade 的 UARotatorStrategy 获取）"""
        if hasattr(self, 'anti_wind'):
            ua_strategy = self.anti_wind.get_strategy('UARotator')
            if ua_strategy and hasattr(ua_strategy, '_user_agents') and ua_strategy._user_agents:
                return ua_strategy._user_agents[0]
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
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
                            # 指数退避
                            base_delay = (2 ** attempt) * min_delay
                            
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
        """初始化 AkShare 适配器，使用 AntiWindFacade 统一管理反爬策略"""
        try:
            # AntiWindFacade 在 __init__ 中已自动初始化，这里只需要打印状态
            logger.info("AkShare 适配器初始化成功（使用 AntiWindFacade 统一管理）")
            self.anti_wind.print_status()
            
            # 懒加载初始化 HybridTLSClient（用于降级）
            self._hybrid_client: Optional[HybridTLSClient] = None
            
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
        
        # 添加延迟，避免重试过快
        import asyncio
        await asyncio.sleep(3.0)  # 延迟 3 秒
        
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
        """
        获取 A 股股票列表
        
        ⚠️ 注意：此方法已废弃，建议使用 Baostock 适配器获取股票列表
        Akshare 只提供 code 和 name 两个字段，缺少 type, status, list_date, delist_date 等关键字段
        
        Returns:
            List[StockBasicInfo]: 股票列表（仅包含 code, name, market）
        """
        logger.warning("⚠️ akshare 适配器 get_stock_list 方法已废弃，建议使用 Baostock 适配器")
        logger.warning("⚠️ akshare 只提供 code 和 name 字段，缺少 type, status, list_date, delist_date 等关键字段")
        
        def fetch_sync():
            # 使用新浪接口替代东方财富接口（stock_zh_a_spot_em 已失效）
            df = ak.stock_zh_a_spot()
            stocks = []
            for _, row in df.iterrows():
                code = str(row.get("code", ""))
                if not code:
                    continue
                # 补齐 6 位代码
                code = code.zfill(6)
                name = str(row.get("name", ""))
                market_tag = "SH" if code.startswith("6") or code.startswith("9") else "SZ"
                stocks.append(StockBasicInfo(code=code, name=name, market=market_tag))
            return stocks
        
        try:
            result = await self._execute_with_anti_wind(
                request_func=fetch_sync,
                context="get_stock_list"
            )
            return result or []
        except Exception as e:
            logger.error(f"获取股票列表失败：{e}")
            return []
    
    async def get_stock_info(self, code: str) -> Optional[StockBasicInfo]:
        """获取个股详细信息（使用 AntiWindFacade 统一管理反爬策略 + 缓存）"""
        # 生成缓存键
        cache_key = self._get_cache_key('stock_info', code=code)
        cached = self._get_from_cache(cache_key, 'stock_basic')
        if cached:
            logger.debug(f"缓存命中：{cache_key}")
            return cached
        
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
            # 使用 AntiWindFacade 执行（自动处理 Cookie 注入、TLS 指纹、限流、重试）
            result = await self._execute_with_anti_wind(
                request_func=fetch_sync,
                context="get_stock_info"
            )
            # 保存到缓存（股票信息变化慢，缓存 10 分钟）
            if result:
                self._save_to_cache(cache_key, result, 'stock_basic', ttl=600)
            return result
        except Exception as e:
            logger.error(f"获取股票信息失败 {code}: {e}")
            return None
    
    async def get_stock_individual_info_em(self, code: str) -> Optional[Dict[str, Any]]:
        """获取个股详细资料（高危反爬 API，使用全部反爬策略）
        
        策略说明：
        1. 凭证注入（Cookie + Headers）
        2. TLS 指纹伪装（curl_cffi）
        3. 智能重试（自动降级）
        4. 请求限流（自适应延迟）
        5. User-Agent 轮换
        6. 缓存保护（5 分钟）
        
        Args:
            code: 股票代码（6 位）
        
        Returns:
            个股详细资料字典，包含：
            - 最新价、涨跌幅、涨跌额
            - 总市值、流通市值
            - 市盈率、市净率
            - 每股收益、净资产收益率
            - 所属行业、地区
            - 上市日期等
        """
        logger.info(f"🔍 开始获取个股详细资料：{code}（高危 API，使用 AntiWindFacade 全部策略）")
        
        # 生成缓存键（缓存 5 分钟，避免频繁请求）
        cache_key = self._get_cache_key('stock_individual_info_em', code=code)
        cached = self._get_from_cache(cache_key, 'stock_info_em')
        if cached:
            logger.info(f"✅ 缓存命中：{code}")
            return cached
        
        def fetch_sync():
            """同步获取数据"""
            logger.info(f"📞 调用 ak.stock_individual_info_em('{code}')...")
            df = ak.stock_individual_info_em(symbol=code)
            
            if df is None or df.empty:
                logger.warning(f"⚠️  API 返回空数据：{code}")
                return None
            
            # 解析数据
            info_dict = dict(zip(df["item"], df["value"]))
            
            # 转换为标准格式
            result = {
                'code': code,
                'latest_price': float(info_dict.get('最新价', 0)) if info_dict.get('最新价') else None,
                'change_pct': float(info_dict.get('涨跌幅', 0)) if info_dict.get('涨跌幅') else None,
                'change_amount': float(info_dict.get('涨跌额', 0)) if info_dict.get('涨跌额') else None,
                'total_market_cap': float(info_dict.get('总市值', 0)) if info_dict.get('总市值') else None,
                'float_market_cap': float(info_dict.get('流通市值', 0)) if info_dict.get('流通市值') else None,
                'pe_ratio': float(info_dict.get('市盈率 - 动态', 0)) if info_dict.get('市盈率 - 动态') else None,
                'pb_ratio': float(info_dict.get('市净率', 0)) if info_dict.get('市净率') else None,
                'eps': float(info_dict.get('每股收益', 0)) if info_dict.get('每股收益') else None,
                'roe': float(info_dict.get('净资产收益率', 0)) if info_dict.get('净资产收益率') else None,
                'bps': float(info_dict.get('每股净资产', 0)) if info_dict.get('每股净资产') else None,
                'industry': info_dict.get('所属行业', ''),
                'area': info_dict.get('地区', ''),
                'list_date': info_dict.get('上市时间', ''),
                'total_shares': float(info_dict.get('总股本', 0)) if info_dict.get('总股本') else None,
                'float_shares': float(info_dict.get('流通股本', 0)) if info_dict.get('流通股本') else None,
                'revenue': float(info_dict.get('营业收入', 0)) if info_dict.get('营业收入') else None,
                'net_profit': float(info_dict.get('净利润', 0)) if info_dict.get('净利润') else None,
                'gross_margin': float(info_dict.get('毛利率', 0)) if info_dict.get('毛利率') else None,
            }
            
            logger.info(f"✅ 获取成功：{code} - {info_dict.get('股票简称', 'Unknown')}")
            return result
        
        # 使用 AntiWindFacade 执行（自动处理所有反爬策略）
        result = await self._execute_with_anti_wind(
            request_func=fetch_sync,
            context="get_stock_individual_info_em"
        )
        
        # 保存到缓存（缓存 5 分钟）
        if result:
            self._save_to_cache(cache_key, result, 'stock_info_em', ttl=300)
            logger.info(f"💾 已保存到缓存：{code}")
        
        return result or {
            'code': code,
            'error': 'Request failed',
            'latest_price': None,
            'change_pct': None,
            'total_market_cap': None,
            'float_market_cap': None,
            'pe_ratio': None,
            'pb_ratio': None,
            'industry': None,
        }
    
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
            result = await self._execute_with_anti_wind(
                request_func=fetch_sync,
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
        
        def fetch_sync():
            # 使用新浪接口替代东方财富接口（stock_zh_a_spot_em 已失效）
            df = ak.stock_zh_a_spot()
            row = df[df["code"] == code]
            if row.empty:
                return None
            row = row.iloc[0]
            return {
                "code": code,
                "name": row.get("name", ""),
                "price": float(row.get("最新价", 0)),
                "change": float(row.get("涨跌额", 0)),
                "change_pct": float(row.get("涨跌幅", 0)),
                "volume": float(row.get("成交量", 0)),
                "amount": float(row.get("成交额", 0)),
                "high": float(row.get("最高", 0)),
                "low": float(row.get("最低", 0)),
                "open": float(row["今开"]),
                "prev_close": float(row["昨收"]),
                "turnover_rate": float(row["换手率"]) if "换手率" in row else None
            }
        
        try:
            result = await self._execute_with_anti_wind(
                request_func=fetch_sync,
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
        
        def fetch_sync():
            # 使用新浪接口替代东方财富接口（stock_zh_a_spot_em 已失效）
            df = ak.stock_zh_a_spot()
            
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
                
                code = str(row.get("code", "")).zfill(6)
                if not code:
                    continue
                
                quotes.append(MarketQuote(
                    code=code,
                    name=str(row.get("name", "")),
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
            result = await self._execute_with_anti_wind(
                request_func=fetch_sync,
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
        """获取板块列表（高敏感 API，使用 AntiWindFacade 统一管理）"""
        
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
            result = await self._execute_with_anti_wind(
                request_func=fetch,
                context="get_sector_list"
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
        
        def fetch_sync():
            df = ak.stock_board_industry_cons_em(symbol=sector_code)
            
            if df is None or isinstance(df, int) or not hasattr(df, 'columns'):
                logger.warning(f"akshare 返回无效数据：{type(df)}")
                return []
            
            return df["代码"].tolist()
        
        try:
            result = await self._execute_with_anti_wind(
                request_func=fetch_sync,
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
            result = await self._execute_with_anti_wind(
                request_func=fetch_sync,
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
            result = await self._execute_with_anti_wind(
                request_func=fetch_sync,
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
            result = await self._execute_with_anti_wind(
                request_func=fetch_sync,
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
        
        def fetch_sync():
            df = ak.stock_financial_abstract_ths(symbol=code, indicator="全部") 
            return df.to_dict("records")
        
        try:
            result = await self._execute_with_anti_wind(
                request_func=fetch_sync,
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
            result = await self._execute_with_anti_wind(
                request_func=fetch_sync,
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
            result = await self._execute_with_anti_wind(
                request_func=fetch_sync,
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
            result = await self._execute_with_anti_wind(
                request_func=fetch_sync,
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
            result = await self._execute_with_anti_wind(
                request_func=fetch_sync,
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
            result = await self._execute_with_anti_wind(
                request_func=fetch_sync,
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
            result = await self._execute_with_anti_wind(
                request_func=fetch_sync,
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
            result = await self._execute_with_anti_wind(
                request_func=fetch_sync,
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
            result = await self._execute_with_anti_wind(
                request_func=fetch_sync,
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
            result = await self._execute_with_anti_wind(
                request_func=fetch_sync,
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
            result = await self._execute_with_anti_wind(
                request_func=fetch_sync,
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
            result = await self._execute_with_anti_wind(
                request_func=fetch_sync,
                context="get_board_industry_cons_em"
            )
            if result:
                logger.info(f"获取东方财富行业板块成份股成功 ({symbol}), 共{len(result)}条")
            return result or []
        except Exception as e:
            logger.error(f"获取东方财富行业板块成份股失败：{e}")
            return []
    
    # ========== 基金 API ==========
    
    async def get_fund_base_info(
        self,
        fund_codes: Union[str, List[str]]
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """获取基金基本信息（使用 akshare）
        
        Args:
            fund_codes: 6 位基金代码或多个 6 位基金代码构成的列表
                示例：'161725' 或 ['161725', '005827']
        
        Returns:
            单只基金返回字典，多只基金返回字典列表
        """
        try:
            # 处理单只基金
            if isinstance(fund_codes, str):
                code = fund_codes.strip()
                cache_key = self._get_cache_key('fund_info', code=code)
                cached = self._get_from_cache(cache_key, 'fund_info')
                if cached:
                    return cached
                
                # 频率控制
                await self._rate_limit()
                
                # 使用 akshare 获取基金信息
                import akshare as ak
                df = ak.fund_open_fund_info_em(fund=code)
                
                if df is None or (hasattr(df, 'empty') and df.empty):
                    return None
                
                # 解析数据
                row = df.iloc[0] if len(df) > 0 else None
                if row is None:
                    return None
                
                fund_info = {
                    'code': code,
                    'name': str(row.get('基金简称', '')),
                    'establish_date': str(row.get('成立日期', '')),
                    'change_pct': float(row.get('涨跌幅', 0)) if pd.notna(row.get('涨跌幅')) else None,
                    'net_asset_value': float(row.get('单位净值', 0)) if pd.notna(row.get('单位净值')) else None,
                    'fund_company': str(row.get('基金公司', '')),
                    'nav_update_date': str(row.get('净值日期', '')),
                    'description': ''
                }
                
                self._save_to_cache(cache_key, fund_info, 'fund_info')
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
                import akshare as ak
                fund_list = []
                for code in valid_codes:
                    try:
                        df = ak.fund_open_fund_info_em(fund=code)
                        if df is not None and len(df) > 0:
                            row = df.iloc[0]
                            fund_info = {
                                'code': code,
                                'name': str(row.get('基金简称', '')),
                                'establish_date': str(row.get('成立日期', '')),
                                'change_pct': float(row.get('涨跌幅', 0)) if pd.notna(row.get('涨跌幅')) else None,
                                'net_asset_value': float(row.get('单位净值', 0)) if pd.notna(row.get('单位净值')) else None,
                                'fund_company': str(row.get('基金公司', '')),
                                'nav_update_date': str(row.get('净值日期', '')),
                                'description': ''
                            }
                            fund_list.append(fund_info)
                    except Exception as e:
                        logger.error(f"获取基金 {code} 信息失败：{e}")
                        continue
                
                self._save_to_cache(cache_key, fund_list, 'fund_info')
                logger.info(f"获取基金基本信息成功：{len(fund_list)}条")
                return fund_list
        
        except Exception as e:
            logger.error(f"获取基金基本信息失败 {fund_codes}: {e}")
            # 返回空列表而不是 None，避免前端解析错误
            if isinstance(fund_codes, str):
                # 单只基金返回空字典
                return {'code': fund_codes, 'name': '', 'establish_date': '', 'change_pct': None, 'net_asset_value': None, 'fund_company': '', 'nav_update_date': '', 'description': ''}
            else:
                # 多只基金返回空列表
                return []

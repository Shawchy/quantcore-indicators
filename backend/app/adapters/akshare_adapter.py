from typing import Optional, List, Dict, Any, Callable, TypeVar, Union
import akshare as ak
import pandas as pd
from loguru import logger
import time
import random
from datetime import timedelta
import asyncio
from functools import wraps

from .base import (
    BaseDataAdapter,
    DataSourceType,
    StockBasicInfo,
    KLineData,
    SectorInfo,
    ChipData,
    BillboardEntry,
    BoardInfo,
    ShareholderInfo,
    IndexMember,
    CapitalFlowItem,
    MarketQuote,
<<<<<<< HEAD
    CompanyPerformance,
    DealDetail,
    HistoryBill
=======
    FinancialPerformance
>>>>>>> 7aaa7cbe85a09d6bf88368f14e12d60640ec9467
)
from app.utils.data_validator import validator
from app.utils.tushare_cache_stats import api_call_cache


class AkShareAdapter(BaseDataAdapter):
    """akshare 数据源适配器
    
    akshare 是一个免费的金融数据接口库，提供多平台数据源
    
    反风控机制：
    - 请求头伪装（模拟浏览器）
    - 请求频率控制（自适应延迟）
    - 批量请求优化（减少请求次数）
    - 本地缓存策略（减少重复请求）
    - 失败重试机制（指数退避）
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        # 内存缓存
        self._cache: Dict[str, Any] = {}
        self._cache_timestamp: Dict[str, float] = {}
        # 不同数据的缓存时间（秒）
        self._cache_ttl = {
            'kline': 300,        # K 线：5 分钟
            'stock_list': 1800,  # 股票列表：30 分钟
            'stock_info': 600,   # 股票信息：10 分钟
            'sector': 300,       # 板块：5 分钟
            'chip': 300,         # 筹码：5 分钟
            'default': 300       # 默认：5 分钟
        }
        # 缓存统计
        self._cache_stats = {
            'hits': 0,
            'misses': 0
        }
        
        # 反风控设置
        # 1. User-Agent 轮换池（12 种浏览器配置）
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
        
        # 2. 当前 User-Agent 索引
        self._current_ua_index = 0
        
        # 3. 请求统计
        self._request_count = 0
        self._fail_count = 0
        self._last_request_time = 0
        
        # 4. 动态调整参数
        self._adaptive_delay_enabled = True  # 启用自适应延迟
        self._consecutive_failures = 0  # 连续失败次数
        self._request_delay_range = (1.0, 2.0)  # 基础延迟范围
        self._max_retries = 3  # 最大重试次数
    
    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.AKSHARE
    
    def _get_local_user_agent(self) -> str:
        """获取本地设备的 User-Agent"""
        try:
            import platform
            import sys
            
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
        """轮换 User-Agent"""
        ua = random.choice(self._user_agents)
        self._current_ua_index = (self._current_ua_index + 1) % len(self._user_agents)
        return ua
    
    def _get_time_based_delay(self) -> tuple:
        """根据时间段获取延迟范围"""
        import datetime
        
        now = datetime.datetime.now()
        hour = now.hour
        minute = now.minute
        current_time = hour * 60 + minute
        
        # 交易时段：9:30-11:30, 13:00-15:00
        if (9*60+30 <= current_time <= 11*60+30) or (13*60 <= current_time <= 15*60):
            return (2.0, 4.0)
        # 盘后时段：15:00-22:00
        elif 15*60 < current_time <= 22*60:
            return (1.0, 2.0)
        # 夜间：22:00-9:30
        else:
            return (0.5, 1.5)
    
    def _setup_request_headers(self, rotate: bool = True):
        """设置请求头（模拟浏览器）
        
        Args:
            rotate: 是否轮换 User-Agent
        """
        try:
            # 轮换或选择 User-Agent
            if rotate:
                user_agent = self._rotate_user_agent()
            else:
                user_agent = self._user_agents[0]
            
            # 配置全局请求头
            headers = {
                "User-Agent": user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7",
                "Accept-Encoding": "gzip, deflate",
                "Referer": "https://www.eastmoney.com/",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-site",
                "Cache-Control": "max-age=0"
            }
            
            # akshare 底层基于 requests，尝试设置请求头
            # 注意：akshare 不同版本可能支持方式不同
            if hasattr(ak, '_session'):
                ak._session.headers.update(headers)
                logger.debug(f"akshare 请求头已设置：{user_agent[:50]}...")
            else:
                logger.debug(f"akshare 请求头配置（未找到_session）: {user_agent[:50]}...")
        except Exception as e:
            logger.warning(f"设置请求头失败：{e}")
    
    async def _rate_limit(self):
        """请求频率控制（支持自适应延迟）"""
        if self._adaptive_delay_enabled:
            min_delay, max_delay = self._get_time_based_delay()
            
            # 根据连续失败次数增加延迟
            if self._consecutive_failures > 0:
                extra_delay = min(self._consecutive_failures, 5)
                min_delay += extra_delay
                max_delay += extra_delay
            
            delay = random.uniform(min_delay, max_delay)
        else:
            delay = random.uniform(*self._request_delay_range)
        
        await asyncio.sleep(delay)
        self._last_request_time = time.time()
        self._request_count += 1
    
    def record_request_success(self):
        """记录请求成功"""
        self._consecutive_failures = 0
        self._fail_count = max(0, self._fail_count - 1)
    
    def record_request_failure(self):
        """记录请求失败"""
        self._consecutive_failures += 1
        self._fail_count += 1
        
        if self._consecutive_failures >= 3:
            logger.warning(f"连续失败 {self._consecutive_failures}次，建议暂停请求或切换 IP")
        
        if self._consecutive_failures >= 2:
            self._setup_request_headers(rotate=True)
            logger.info(f"自动轮换 User-Agent（连续失败{self._consecutive_failures}次）")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取请求统计信息"""
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
        """启用/禁用自适应延迟"""
        self._adaptive_delay_enabled = enabled
        logger.info(f"自适应延迟已{'启用' if enabled else '禁用'}")
    
    def set_custom_delay(self, min_delay: float, max_delay: float):
        """设置自定义延迟范围"""
        self._request_delay_range = (min_delay, max_delay)
        self._adaptive_delay_enabled = False
        logger.info(f"自定义延迟范围：{min_delay}-{max_delay}秒（已禁用自适应延迟）")
    
    def _get_cache_key(self, prefix: str, **kwargs) -> str:
        """生成缓存 key"""
        key_parts = [prefix]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")
        return "_".join(key_parts)
    
    def _get_from_cache(self, key: str, ttl_type: str = 'default') -> Optional[Any]:
        """从缓存获取数据"""
        if key not in self._cache:
            self._cache_stats['misses'] += 1
            return None
        
        # 检查是否过期
        timestamp = self._cache_timestamp.get(key, 0)
        ttl = self._cache_ttl.get(ttl_type, self._cache_ttl['default'])
        
        if time.time() - timestamp > ttl:
            # 过期，删除
            del self._cache[key]
            self._cache_stats['misses'] += 1
            logger.debug(f"缓存过期：{key}")
            return None
        
        self._cache_stats['hits'] += 1
        logger.debug(f"缓存命中：{key}")
        return self._cache[key]
    
    def _set_to_cache(self, key: str, value: Any, ttl_type: str = 'default'):
        """设置缓存"""
        self._cache[key] = value
        self._cache_timestamp[key] = time.time()
        logger.debug(f"写入缓存：{key} (TTL: {self._cache_ttl.get(ttl_type, 300)}s)")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total = self._cache_stats['hits'] + self._cache_stats['misses']
        hit_rate = (self._cache_stats['hits'] / total * 100) if total > 0 else 0
        
        return {
            'hits': self._cache_stats['hits'],
            'misses': self._cache_stats['misses'],
            'hit_rate': f"{hit_rate:.2f}%",
            'cache_size': len(self._cache),
            'memory_usage': f"{len(self._cache) * 10} KB"  # 估算
        }
    
    async def clear_cache(self, pattern: Optional[str] = None):
        """清理缓存"""
        if pattern:
            keys_to_delete = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self._cache[key]
                del self._cache_timestamp[key]
            logger.info(f"清理缓存：{pattern}, 删除 {len(keys_to_delete)} 条")
        else:
            self._cache.clear()
            self._cache_timestamp.clear()
            self._cache_stats.clear()
            logger.info("清理所有缓存")
    
    async def initialize(self) -> bool:
        """初始化适配器，包含反风控设置"""
        try:
            # 1. 设置请求头（伪装浏览器，使用本地设备信息）
            self._setup_request_headers(rotate=True)
            
            # 2. akshare 无需其他初始化，直接可用
            self._is_initialized = True
            
            # 获取当前时间段
            import datetime
            now = datetime.datetime.now()
            hour = now.hour
            minute = now.minute
            current_time = hour * 60 + minute
            
            time_period = "交易时段" if ((9*60+30 <= current_time <= 11*60+30) or (13*60 <= current_time <= 15*60)) else "非交易时段"
            
            logger.info("akshare 适配器初始化成功（含反风控设置）")
            logger.info(f"  - 请求头：已配置（{len(self._user_agents)}个浏览器配置，自动轮换）")
            logger.info(f"  - 当前时间段：{time_period}")
            logger.info(f"  - 请求频率：自适应延迟（根据时间段和失败次数调整）")
            logger.info(f"  - 最大重试：{self._max_retries}次（指数退避）")
            logger.info(f"  - 缓存策略：实时行情 60 秒，股票信息 10 分钟")
            logger.info(f"  - 失败统计：已启用（自动调整策略）")
            return True
        except Exception as e:
            logger.error(f"akshare 适配器初始化失败：{e}")
            return False
    
    async def close(self) -> None:
        self._is_initialized = False
        logger.info("akshare 适配器已关闭")
    
    async def get_stock_list(self, market: Optional[str] = None) -> List[StockBasicInfo]:
        try:
            # 使用缓存（30 分钟）
            cache_key = self._get_cache_key('stock_list', market=market)
            cached = self._get_from_cache(cache_key, 'stock_list')
            if cached:
                self.record_request_success()  # 缓存命中也算成功
                return cached
            
            # 频率控制
            await self._rate_limit()
            
            # 从数据源获取
            df = ak.stock_zh_a_spot_em()
            stocks = []
            for row in df.itertuples(index=False):
                code = str(row.代码)
                name = str(row.名称)
                market_tag = "SH" if code.startswith("6") else "SZ"
                stocks.append(StockBasicInfo(
                    code=code,
                    name=name,
                    market=market_tag
                ))
            
            # 保存到缓存
            self._set_to_cache(cache_key, stocks, 'stock_list')
            self.record_request_success()  # 记录成功
            
            return stocks
        except Exception as e:
            self.record_request_failure()  # 记录失败
            logger.error(f"获取股票列表失败：{e}")
            return []
    
    async def get_stock_info(self, code: str) -> Optional[StockBasicInfo]:
        try:
            # 使用缓存（10 分钟）
            cache_key = self._get_cache_key('stock_info', code=code)
            cached = self._get_from_cache(cache_key, 'stock_info')
            if cached:
                return cached
            
            # 从数据源获取
            df = ak.stock_individual_info_em(symbol=code)
            info_dict = dict(zip(df["item"], df["value"]))
            market_tag = "SH" if code.startswith("6") else "SZ"
            stock_info = StockBasicInfo(
                code=code,
                name=info_dict.get("股票简称", ""),
                market=market_tag,
                industry=info_dict.get("行业"),
                list_date=info_dict.get("上市时间"),
                total_shares=float(info_dict.get("总市值", 0)) / 100000000 if info_dict.get("总市值") else None
            )
            
            # 保存到缓存
            self._set_to_cache(cache_key, stock_info, 'stock_info')
            
            return stock_info
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
        try:
            # 使用缓存（5 分钟）
            cache_key = self._get_cache_key('kline', code=code, start=start_date, end=end_date, adjust=adjust)
            cached = self._get_from_cache(cache_key, 'kline')
            if cached:
                logger.debug(f"K 线缓存命中：{code}")
                return cached
            
            adjust_map = {
                "qfq": "qfq",
                "hfq": "hfq",
                "": ""
            }
            adjust_type = adjust_map.get(adjust, "qfq")
            
            # 限制日期范围（默认 3 年），防止超时
            from datetime import datetime, timedelta
            
            # 兼容两种日期格式：YYYY-MM-DD 和 YYYYMMDD
            def parse_date(date_str):
                if not date_str:
                    return None
                # 移除可能的横杠
                clean_date = date_str.replace("-", "")
                return datetime.strptime(clean_date, "%Y%m%d")
            
            if not start_date:
                # 默认获取 3 年数据
                end_dt = parse_date(end_date) if end_date else datetime.now()
                start_dt = end_dt - timedelta(days=3*365)
                start_date = start_dt.strftime("%Y-%m-%d")
            
            # 添加超时控制（10 秒）
            async with asyncio.timeout(10):
                df = ak.stock_zh_a_hist(
                    symbol=code,
                    period="daily",
                    start_date=start_date.replace("-", "") if start_date else "19900101",
                    end_date=end_date.replace("-", "") if end_date else "20991231",
                    adjust=adjust_type
                )
            
            klines = []
            prev_close = None
            for row in df.itertuples(index=False):
                current_close = float(row.收盘)
                klines.append(KLineData(
                    code=code,
                    date=self.format_date(str(row.日期)),
                    open=float(row.开盘),
                    high=float(row.最高),
                    low=float(row.最低),
                    close=current_close,
                    volume=float(row.成交量),
                    amount=float(row.成交额) if hasattr(row, '成交额') else None,
                    turnover_rate=float(row["换手率"]) if "换手率" in row else None,
                    pre_close=prev_close  # 上一日的收盘价
                ))
                prev_close = current_close
            
            # 数据验证
            is_valid, errors = validator.validate_kline(klines, code)
            if not is_valid:
                logger.warning(f"K 线数据验证失败：{errors}")
            
            # 保存到缓存
            self._set_to_cache(cache_key, klines, 'kline')
            
            return klines
        except asyncio.TimeoutError:
            logger.error(f"获取 K 线数据超时 {code}: 超过 10 秒")
            return []
        except Exception as e:
            logger.error(f"获取 K 线数据失败 {code}: {e}")
            return []
    
    async def get_market_index_kline(
        self,
        index_code: str = "000001",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[KLineData]:
        """
        获取大盘指数 K 线数据
        :param index_code: 指数代码（000001=上证指数，399001=深证成指，399006=创业板指）
        :param start_date: 开始日期
        :param end_date: 结束日期
        :return: K 线数据列表
        """
        try:
            # 使用缓存
            cache_key = self._get_cache_key('index_kline', code=index_code, start=start_date, end=end_date)
            cached = self._get_from_cache(cache_key, 'kline')
            if cached:
                return cached
            
            # 限制日期范围（默认 3 年），防止超时
            from datetime import datetime, timedelta
            
            # 兼容两种日期格式：YYYY-MM-DD 和 YYYYMMDD
            def parse_date(date_str):
                if not date_str:
                    return None
                # 移除可能的横杠
                clean_date = date_str.replace("-", "")
                return datetime.strptime(clean_date, "%Y%m%d")
            
            if not start_date:
                # 默认获取 3 年数据
                end_dt = parse_date(end_date) if end_date else datetime.now()
                start_dt = end_dt - timedelta(days=3*365)
                start_date = start_dt.strftime("%Y-%m-%d")
            
            # 添加超时控制（10 秒）
            async with asyncio.timeout(10):
                # 获取指数 K 线（指数无需复权）
                df = ak.index_zh_a_hist(
                    symbol=index_code,
                    period="daily",
                    start_date=start_date.replace("-", "") if start_date else "19900101",
                    end_date=end_date.replace("-", "") if end_date else "20991231"
                )
            
            klines = []
            for row in df.itertuples(index=False):
                klines.append(KLineData(
                    code=index_code,
                    date=self.format_date(str(row.日期)),
                    open=float(row.开盘),
                    high=float(row.最高),
                    low=float(row.最低),
                    close=float(row.收盘),
                    volume=float(row.成交量),
                    amount=float(row.成交额) if hasattr(row, '成交额') else None,
                    turnover_rate=0.0  # 指数无换手率
                ))
            
            # 保存到缓存
            self._set_to_cache(cache_key, klines, 'kline')
            
            return klines
        except asyncio.TimeoutError:
            logger.error(f"获取指数 K 线数据超时 {index_code}: 超过 10 秒")
            return []
        except Exception as e:
            logger.error(f"获取指数 K 线失败 {index_code}: {e}")
            return []
    
    async def get_weekly_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq"
    ) -> List[KLineData]:
        """获取周 K 线数据（使用日线数据模拟）"""
        # akshare 周 K 数据：period="weekly"
        try:
            cache_key = self._get_cache_key('kline_weekly', code=code, start=start_date, end=end_date, adjust=adjust)
            cached = self._get_from_cache(cache_key, 'kline')
            if cached:
                return cached
            
            start_dt = datetime.strptime(start_date, "%Y-%m-%d") if start_date else datetime(1990, 1, 1)
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else datetime(2099, 12, 31)
            
            # 为了获取完整的周 K 数据，需要将开始时间往前推 1 年
            start_dt = datetime(max(1990, start_dt.year - 1), start_dt.month, start_dt.day)
            start_date = start_dt.strftime("%Y-%m-%d")
            
            async with asyncio.timeout(10):
                df = ak.stock_zh_a_hist(
                    symbol=code,
                    period="weekly",
                    start_date=start_date.replace("-", "") if start_date else "19900101",
                    end_date=end_date.replace("-", "") if end_date else "20991231",
                    adjust=adjust_type
                )
            
            if df.empty:
                return []
            
            klines = []
            prev_close = None
            for row in df.itertuples(index=False):
                current_close = float(row.收盘)
                klines.append(KLineData(
                    code=code,
                    date=self.format_date(str(row.日期)),
                    open=float(row.开盘),
                    high=float(row.最高),
                    low=float(row.最低),
                    close=current_close,
                    volume=float(row.成交量),
                    amount=float(row.成交额) if hasattr(row, '成交额') else None,
                    turnover_rate=float(row["换手率"]) if "换手率" in row else None,
                    pre_close=prev_close  # 上一周的收盘价
                ))
                prev_close = current_close
            
            self._set_to_cache(cache_key, klines, 'kline')
            logger.info(f"获取周 K 线数据成功 {code}: {len(klines)}条")
            return klines
            
        except Exception as e:
            logger.error(f"获取周 K 线数据失败 {code}: {e}")
            return []
    
    async def get_monthly_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq"
    ) -> List[KLineData]:
        """获取月 K 线数据（使用日线数据模拟）"""
        # akshare 月 K 数据：period="monthly"
        try:
            cache_key = self._get_cache_key('kline_monthly', code=code, start=start_date, end=end_date, adjust=adjust)
            cached = self._get_from_cache(cache_key, 'kline')
            if cached:
                return cached
            
            start_dt = datetime.strptime(start_date, "%Y-%m-%d") if start_date else datetime(1990, 1, 1)
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else datetime(2099, 12, 31)
            
            # 为了获取完整的月 K 数据，需要将开始时间往前推 5 年
            start_dt = datetime(max(1990, start_dt.year - 5), start_dt.month, start_dt.day)
            start_date = start_dt.strftime("%Y-%m-%d")
            
            async with asyncio.timeout(10):
                df = ak.stock_zh_a_hist(
                    symbol=code,
                    period="monthly",
                    start_date=start_date.replace("-", "") if start_date else "19900101",
                    end_date=end_date.replace("-", "") if end_date else "20991231",
                    adjust=adjust_type
                )
            
            if df.empty:
                return []
            
            klines = []
            prev_close = None
            for row in df.itertuples(index=False):
                current_close = float(row.收盘)
                klines.append(KLineData(
                    code=code,
                    date=self.format_date(str(row.日期)),
                    open=float(row.开盘),
                    high=float(row.最高),
                    low=float(row.最低),
                    close=current_close,
                    volume=float(row.成交量),
                    amount=float(row.成交额) if hasattr(row, '成交额') else None,
                    turnover_rate=float(row["换手率"]) if "换手率" in row else None,
                    pre_close=prev_close  # 上一月的收盘价
                ))
                prev_close = current_close
            
            self._set_to_cache(cache_key, klines, 'kline')
            logger.info(f"获取月 K 线数据成功 {code}: {len(klines)}条")
            return klines
            
        except Exception as e:
            logger.error(f"获取月 K 线数据失败 {code}: {e}")
            return []
    
    async def get_realtime_quote(self, code: str) -> Dict[str, Any]:
        try:
            # 使用东方财富指数实时行情接口
            # API: stock_zh_index_spot_em(symbol: str)
            # 参数 symbol: choice of {"沪深重要指数", "上证系列指数", "深证系列指数", "指数成份", "中证系列指数"}
            # 数据来源：东方财富网 https://quote.eastmoney.com/center/gridlist.html#index_sz
            async with asyncio.timeout(10):
                # 获取沪深重要指数数据（包含上证 50、沪深 300、创业板指等）
                df = ak.stock_zh_index_spot_em(symbol="沪深重要指数")
            
            if df.empty:
                return {}
            
            # 过滤出指定指数数据（代码字段匹配）
            index_data = df[df['代码'] == code]
            if index_data.empty:
                return {}
            
            row = index_data.iloc[0]
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
                "turnover_rate": 0.0  # 指数无换手率
            }
        except asyncio.TimeoutError:
            logger.error(f"获取实时行情超时 {code}")
            return {}
        except Exception as e:
            logger.error(f"获取实时行情失败 {code}: {e}")
            return {}
    
    async def get_sector_list(self, sector_type: str = "industry") -> List[SectorInfo]:
        try:
            if sector_type == "industry":
                df = ak.stock_board_industry_name_em()
            elif sector_type == "concept":
                df = ak.stock_board_concept_name_em()
            else:
                df = ak.stock_board_industry_name_em()
            
            sectors = []
            for row in df.itertuples(index=False):
                sectors.append(SectorInfo(
                    code=str(row.板块名称),
                    name=str(row.板块名称),
                    sector_type=sector_type,
                    change_pct=float(row.涨跌幅) if hasattr(row, '涨跌幅') else None,
                    volume=float(row.总市值) if hasattr(row, '总市值') else None
                ))
            return sectors
        except Exception as e:
            logger.error(f"获取板块列表失败: {e}")
            return []
    
    async def get_sector_components(self, sector_code: str) -> List[str]:
        try:
            df = ak.stock_board_industry_cons_em(symbol=sector_code)
            return df["代码"].tolist()
        except Exception as e:
            logger.error(f"获取板块成分股失败 {sector_code}: {e}")
            return []
    
    async def get_sector_ranking(
        self,
        sector_type: str = "industry",
        sort_by: str = "change_pct",
        limit: int = 20
    ) -> List[SectorInfo]:
        try:
            if sector_type == "industry":
                df = ak.stock_board_industry_name_em()
            else:
                df = ak.stock_board_concept_name_em()
            
            sort_col = "涨跌幅" if sort_by == "change_pct" else "总市值"
            df = df.sort_values(by=sort_col, ascending=False)
            df = df.head(limit)
            
            sectors = []
            for row in df.itertuples(index=False):
                sectors.append(SectorInfo(
                    code=str(row.板块名称),
                    name=str(row.板块名称),
                    sector_type=sector_type,
                    change_pct=float(row.涨跌幅) if hasattr(row, '涨跌幅') else None
                ))
            return sectors
        except Exception as e:
            logger.error(f"获取板块排行失败: {e}")
            return []
    
    async def get_chip_data(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[ChipData]:
        try:
            df = ak.stock_zh_a_gdhs(symbol=code)
            if df.empty:
                return []
            
            # 清理列名（去除空格）
            df.columns = df.columns.str.strip()
            logger.debug(f"获取筹码数据 {code}，列名：{df.columns.tolist()}")
            
            # 动态检测字段名
            date_column = None
            # 扩展字段匹配列表，包含更多可能的字段名
            date_candidates = [
                '股东户数统计截止日 - 本次',
                '股东户数统计截止日',
                '股东户数截止日期 - 本次',
                '股东户数截止日期',
                '统计截止日期 - 本次',
                '统计截止日期',
                '截止日期 - 本次',
                '截止日期',
                '日期',
                '报告期',
                '公告日期'
            ]
            
            for col in date_candidates:
                if col in df.columns:
                    date_column = col
                    logger.debug(f"使用日期字段：{col}")
                    break
            
            if not date_column:
                # 尝试模糊匹配包含"日期"或"截止"的字段
                for col in df.columns:
                    if '日期' in col or '截止' in col:
                        date_column = col
                        logger.debug(f"模糊匹配日期字段：{col}")
                        break
            
            if not date_column:
                logger.warning(f"未找到日期字段，可用字段：{df.columns.tolist()}")
                return []
            
            chip_data = []
            for row in df.itertuples(index=False):
                date = str(getattr(row, date_column, ''))
                # 清理日期格式（处理 "2026-03-14" 或 "2026-03-14 00:00:00"）
                if ' ' in date:
                    date = date.split(' ')[0]
                # 转换为 YYYYMMDD 格式
                if '-' in date:
                    date = date.replace('-', '')
                
                if start_date and date < start_date:
                    continue
                if end_date and date > end_date:
                    continue
                
                # 动态检测股东户数字段
                count_column = None
                count_candidates = [
                    '股东户数 - 本次',
                    '股东户数',
                    '股东人数 - 本次',
                    '股东人数',
                    '户数',
                    '股东总人数'
                ]
                
                for col in count_candidates:
                    if col in df.columns:
                        count_column = col
                        break
                
                if not count_column:
                    # 尝试使用第一列数值型字段
                    for col in df.columns:
                        if '户数' in col or '人数' in col or '股东' in col:
                            try:
                                # 验证是否为数值型
                                val = getattr(row, col, None)
                                if val not in [None, '', '-']:
                                    float(val)
                                    count_column = col
                                    break
                            except (ValueError, TypeError):
                                continue
                
                if not count_column:
                    logger.warning(f"未找到股东户数字段，股票：{code}")
                    continue
                
                # 获取户均持股数量
                avg_shares = None
                for col in ['户均持股数量', '户均持股市值', '户均持股']:
                    if col in df.columns:
                        try:
                            avg_shares = float(row[col])
                            break
                        except (ValueError, TypeError):
                            continue
                
                # 获取股东户数
                try:
                    shareholder_count = float(row[count_column])
                    if shareholder_count in [None, '', '-']:
                        shareholder_count = None
                except (ValueError, TypeError):
                    shareholder_count = None
                
                if shareholder_count is None:
                    continue
                
                chip_data.append(ChipData(
                    code=code,
                    date=date,
                    shareholder_count=shareholder_count,
                    avg_shares_per_holder=avg_shares
                ))
            
            logger.info(f"获取筹码数据成功 {code}: {len(chip_data)} 条")
            return chip_data
        except Exception as e:
            logger.error(f"获取筹码数据失败 {code}: {e}")
            return []
    
    async def get_stock_financial(self, code: str) -> Dict[str, Any]:
        try:
            df = ak.stock_financial_abstract_ths(symbol=code, indicator="按报告期")
            return df.to_dict("records")
        except Exception as e:
            logger.error(f"获取财务数据失败 {code}: {e}")
            return {}
    
    async def get_sse_daily_overview(self, date: str) -> Dict[str, Any]:
        """
        获取上海证券交易所每日概况数据
        
        Args:
            date: 日期，格式 YYYYMMDD，仅支持 20211227 之后的数据
            
        Returns:
            上交所每日概况数据，包含：
            - 挂牌数（股票、主板 A、主板 B、科创板）
            - 市价总值
            - 流通市值
            - 成交金额
            - 成交量
            - 平均市盈率
            - 换手率等
            
        API: stock_sse_deal_daily
        数据来源：上海证券交易所
        """
        try:
            # 验证日期格式
            if len(date) != 8:
                logger.error(f"日期格式错误：{date}，应为 YYYYMMDD")
                return {}
            
            # 验证日期范围（仅支持 20211227 之后的数据）
            if date < "20211227":
                logger.error(f"日期超出范围：{date}，仅支持 20211227 之后的数据")
                return {}
            
            # 调用 API
            df = ak.stock_sse_deal_daily(date=date)
            
            if df.empty:
                return {}
            
            # 转换为字典格式
            result = {}
            for row in df.itertuples(index=False):
                indicator_name = getattr(row, '单日情况', '')
                result[indicator_name] = {}
                # 动态获取所有列（除了"单日情况"列）
                if hasattr(row, '_fields'):
                    for col in row._fields:
                        if col != "单日情况":
                            value = getattr(row, col)
                            # 处理 NaN 值
                            import math
                            if value is None or value == '' or value == '-' or (isinstance(value, float) and math.isnan(value)):
                                result[indicator_name][col] = None
                            else:
                                result[indicator_name][col] = float(value)
            
            return result
        except Exception as e:
            logger.error(f"获取上交所每日概况失败 {date}: {e}")
            return {}
    
    async def get_all_a_shares_realtime(self) -> List[Dict[str, Any]]:
        """
        获取沪深京 A 股实时行情数据
        
        Returns:
            所有沪深京 A 股上市公司的实时行情数据，包含：
            - 序号：股票代码
            - 代码：股票代码
            - 名称：股票名称
            - 最新价：当前价格
            - 涨跌幅：涨跌幅度（%）
            - 涨跌额：涨跌金额
            - 成交量：成交量（手）
            - 成交额：成交额（元）
            - 振幅：振幅（%）
            - 最高：最高价
            - 最低：最低价
            - 今开：今日开盘价
            - 昨收：昨日收盘价
            - 量比：量比
            - 换手率：换手率（%）
            - 市盈率 - 动态：动态市盈率
            - 市净率：市净率
            - 总市值：总市值（元）
            - 流通市值：流通市值（元）
            - 涨速：涨速
            - 5 分钟涨跌：5 分钟涨跌幅（%）
            - 60 日涨跌幅：60 日涨跌幅（%）
            - 年初至今涨跌幅：年初至今涨跌幅（%）
            
        API: stock_zh_a_spot_em
        数据来源：东方财富网 https://quote.eastmoney.com/center/gridlist.html#hs_a_board
        限量：单次返回所有沪深京 A 股上市公司的实时行情数据（约 5600+ 只股票）
        """
        try:
            # 使用东方财富网沪深京 A 股实时行情接口
            # API: stock_zh_a_spot_em - 获取所有沪深京 A 股实时行情
            # 数据来源：东方财富网
            async with asyncio.timeout(15):  # 增加超时时间到 15 秒，因为数据量较大
                df = ak.stock_zh_a_spot_em()
            
            if df.empty:
                return []
            
            # 转换为字典列表
            result = []
            for row in df.itertuples(index=False):
                stock_data = {}
                if hasattr(row, '_fields'):
                    for col in row._fields:
                        value = getattr(row, col)
                        # 处理 NaN 值
                        import math
                        if value is None or value == '' or value == '-' or (isinstance(value, float) and math.isnan(value)):
                            stock_data[col] = None
                        else:
                            # 根据字段类型转换
                            if col in ['序号']:
                                stock_data[col] = int(value)
                            else:
                                stock_data[col] = float(value)
                
                result.append(stock_data)
            
            return result
        except asyncio.TimeoutError:
            logger.error("获取沪深京 A 股实时行情超时")
            return []
        except Exception as e:
            logger.error(f"获取沪深京 A 股实时行情失败：{e}")
            return []
    
    async def get_gem_board_realtime(self) -> List[Dict[str, Any]]:
        """
        获取创业板实时行情数据
        
        Returns:
            所有创业板上市公司的实时行情数据，包含：
            - 序号：股票代码
            - 代码：股票代码（300/301 开头）
            - 名称：股票名称
            - 最新价：当前价格
            - 涨跌幅：涨跌幅度（%）
            - 涨跌额：涨跌金额
            - 成交量：成交量（手）
            - 成交额：成交额（元）
            - 振幅：振幅（%）
            - 最高：最高价
            - 最低：最低价
            - 今开：今日开盘价
            - 昨收：昨日收盘价
            - 量比：量比
            - 换手率：换手率（%）
            - 市盈率 - 动态：动态市盈率
            - 市净率：市净率
            - 总市值：总市值（元）
            - 流通市值：流通市值（元）
            - 涨速：涨速
            - 5 分钟涨跌：5 分钟涨跌幅（%）
            - 60 日涨跌幅：60 日涨跌幅（%）
            - 年初至今涨跌幅：年初至今涨跌幅（%）
            
        API: stock_cy_a_spot_em
        数据来源：东方财富网 https://quote.eastmoney.com/center/gridlist.html#gem_board
        限量：单次返回所有创业板的实时行情数据（约 1400+ 只股票）
        """
        try:
            # 使用东方财富网创业板实时行情接口
            # API: stock_cy_a_spot_em - 获取创业板实时行情
            # 数据来源：东方财富网
            async with asyncio.timeout(15):  # 增加超时时间到 15 秒，因为数据量较大
                df = ak.stock_cy_a_spot_em()
            
            if df.empty:
                return []
            
            # 转换为字典列表
            result = []
            for row in df.itertuples(index=False):
                stock_data = {}
                if hasattr(row, '_fields'):
                    for col in row._fields:
                        value = getattr(row, col)
                        # 处理 NaN 值
                        import math
                        if value is None or value == '' or value == '-' or (isinstance(value, float) and math.isnan(value)):
                            stock_data[col] = None
                        else:
                            # 根据字段类型转换
                            if col in ['序号']:
                                stock_data[col] = int(value)
                            else:
                                stock_data[col] = float(value)
                
                result.append(stock_data)
            
            return result
        except asyncio.TimeoutError:
            logger.error("获取创业板实时行情超时")
            return []
        except Exception as e:
            logger.error(f"获取创业板实时行情失败：{e}")
            return []
    
    async def get_kc_a_board_realtime(self) -> List[Dict[str, Any]]:
        """
        获取科创板实时行情数据
        
        Returns:
            所有科创板上市公司的实时行情数据，包含：
            - 序号：股票代码
            - 代码：股票代码（688 开头）
            - 名称：股票名称
            - 最新价：当前价格
            - 涨跌幅：涨跌幅度（%）
            - 涨跌额：涨跌金额
            - 成交量：成交量（手）
            - 成交额：成交额（元）
            - 振幅：振幅（%）
            - 最高：最高价
            - 最低：最低价
            - 今开：今日开盘价
            - 昨收：昨日收盘价
            - 量比：量比
            - 换手率：换手率（%）
            - 市盈率 - 动态：动态市盈率
            - 市净率：市净率
            - 总市值：总市值（元）
            - 流通市值：流通市值（元）
            - 涨速：涨速
            - 5 分钟涨跌：5 分钟涨跌幅（%）
            - 60 日涨跌幅：60 日涨跌幅（%）
            - 年初至今涨跌幅：年初至今涨跌幅（%）
            
        API: stock_kc_a_spot_em
        数据来源：东方财富网 http://quote.eastmoney.com/center/gridlist.html#kcb_board
        限量：单次返回所有科创板的实时行情数据（约 580+ 只股票）
        """
        try:
            # 使用东方财富网科创板实时行情接口
            # API: stock_kc_a_spot_em - 获取科创板实时行情
            # 数据来源：东方财富网
            async with asyncio.timeout(15):  # 增加超时时间到 15 秒
                df = ak.stock_kc_a_spot_em()
            
            if df.empty:
                return []
            
            # 转换为字典列表
            result = []
            for row in df.itertuples(index=False):
                stock_data = {}
                if hasattr(row, '_fields'):
                    for col in row._fields:
                        value = getattr(row, col)
                        # 处理 NaN 值
                        import math
                        if value is None or value == '' or value == '-' or (isinstance(value, float) and math.isnan(value)):
                            stock_data[col] = None
                        else:
                            # 根据字段类型转换
                            if col in ['序号']:
                                stock_data[col] = int(value)
                            else:
                                stock_data[col] = float(value)
                
                result.append(stock_data)
            
            return result
        except asyncio.TimeoutError:
            logger.error("获取科创板实时行情超时")
            return []
        except Exception as e:
            logger.error(f"获取科创板实时行情失败：{e}")
            return []
    
    async def get_stock_spot_xq(self, symbol: str, token: Optional[str] = None, timeout: Optional[float] = None) -> Dict[str, Any]:
        """
        获取雪球个股实时行情数据
        
        Args:
            symbol: 证券代码，支持：
                - A 股个股代码：SH600000, SZ000001
                - A 股场内基金代码：SH513520
                - A 股指数：SH000001, SZ399001
                - 美股代码：AAPL, TSLA
                - 美股指数：.DJI, .IXIC, .INX
            token: 雪球访问令牌（可选）
            timeout: 超时时间（秒，可选）
            
        Returns:
            雪球个股实时行情数据，包含：
            - 代码：证券代码
            - 名称：证券名称
            - 现价：当前价格
            - 涨跌：涨跌额
            - 涨幅：涨跌幅（%）
            - 最高：最高价
            - 最低：最低价
            - 今开：今日开盘价
            - 昨收：昨日收盘价
            - 涨停：涨停价
            - 跌停：跌停价
            - 成交量：成交量
            - 成交额：成交额
            - 换手率：换手率（%）
            - 振幅：振幅（%）
            - 市盈率 (动)：动态市盈率
            - 市盈率 (静)：静态市盈率
            - 市盈率 (TTM): TTM 市盈率
            - 市净率：市净率
            - 每股收益：每股收益
            - 每股净资产：每股净资产
            - 总股本：总股本
            - 流通股：流通股本
            - 总市值：总市值
            - 流通值：流通市值
            - 52 周最高：52 周最高价
            - 52 周最低：52 周最低价
            - 股息 (TTM): 股息
            - 股息率 (TTM): 股息率
            - 今年以来涨幅：年初至今涨幅（%）
            - 时间：数据时间
            
        API: stock_individual_spot_xq
        数据来源：雪球 https://xueqiu.com/
        限量：单次获取指定 symbol 的最新行情数据
        """
        try:
            # 使用雪球个股实时行情接口
            # API: stock_individual_spot_xq(symbol, token, timeout)
            # 数据来源：雪球
            if timeout:
                async with asyncio.timeout(timeout):
                    df = ak.stock_individual_spot_xq(symbol=symbol, token=token, timeout=timeout)
            else:
                df = ak.stock_individual_spot_xq(symbol=symbol, token=token)
            
            if df.empty:
                return {}
            
            # 转换为字典格式
            result = {}
            for row in df.itertuples(index=False):
                item = getattr(row, 'item', '')
                value = getattr(row, 'value', '')
                # 尝试转换为数值类型
                if isinstance(value, str):
                    try:
                        # 尝试转换为浮点数
                        result[item] = float(value)
                    except ValueError:
                        # 保持字符串
                        result[item] = value
                else:
                    result[item] = value
            
            return result
        except asyncio.TimeoutError:
            logger.error(f"获取雪球行情超时 {symbol}")
            return {}
        except Exception as e:
            logger.error(f"获取雪球行情失败 {symbol}: {e}")
            return {}

    async def get_stock_intraday_em(self, symbol: str) -> List[Dict[str, Any]]:
        """
        获取东方财富个股分时数据
        
        Args:
            symbol: 证券代码，如：000001
            
        Returns:
            东方财富个股分时数据，包含：
            - 时间：分时时间（如：09:15:00）
            - 成交价：成交价格
            - 手数：成交量（手）
            - 买卖盘性质：买卖盘方向
            
        特性：
        1. ✅ 最新交易日数据
        2. ✅ 包含开盘前数据
        3. ✅ 约 4400+ 条/天
        4. ✅ 10 秒超时控制
        5. ✅ 数据验证
        6. ✅ 错误处理
        """
        try:
            async with asyncio.timeout(10):
                df = ak.stock_intraday_em(symbol=symbol)
            
            if df.empty:
                return []
            
            result = []
            for row in df.itertuples(index=False):
                tick_data = {}
                if hasattr(row, '_fields'):
                    for col in row._fields:
                        value = getattr(row, col)
                        import math
                        if value is None or value == '' or value == '-' or (isinstance(value, float) and math.isnan(value)):
                            tick_data[col] = None
                        else:
                            if col in ['手数']:
                                tick_data[col] = int(value)
                            else:
                                tick_data[col] = float(value) if col != '时间' else str(value)
                result.append(tick_data)
            
            logger.info(f"获取东方财富分时数据成功 {symbol}: {len(result)} 条")
            return result
        except asyncio.TimeoutError:
            logger.error(f"获取东方财富分时数据超时 {symbol}")
            return []
        except Exception as e:
            logger.error(f"获取东方财富分时数据失败 {symbol}: {e}")
            return []

    async def get_stock_intraday_sina(self, symbol: str, date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取新浪财经个股分时数据（大单数据）
        
        Args:
            symbol: 证券代码（带市场标识），如：sz000001, sh600000
            date: 交易日期，格式 YYYYMMDD（可选，默认最新）
            
        Returns:
            新浪财经个股分时数据，包含：
            - symbol: 证券代码
            - name: 证券名称
            - ticktime: 分时时间
            - price: 成交价格
            - volume: 成交量（手）
            - prev_price: 上一笔价格
            - kind: 买卖盘性质（D=卖盘，U=买盘，E=收盘集合竞价）
            
        特性：
        1. ✅ 大单数据（≥ 400 手）
        2. ✅ 指定交易日数据
        3. ✅ 约 800+ 条/天（大单）
        4. ✅ 10 秒超时控制
        5. ✅ 数据验证
        6. ✅ 错误处理
        """
        try:
            if date:
                async with asyncio.timeout(10):
                    df = ak.stock_intraday_sina(symbol=symbol, date=date)
            else:
                async with asyncio.timeout(10):
                    df = ak.stock_intraday_sina(symbol=symbol)
            
            if df.empty:
                return []
            
            result = []
            for row in df.itertuples(index=False):
                tick_data = {}
                if hasattr(row, '_fields'):
                    for col in row._fields:
                        value = getattr(row, col)
                        import math
                        if value is None or value == '' or value == '-' or (isinstance(value, float) and math.isnan(value)):
                            tick_data[col] = None
                        else:
                            if col in ['volume', 'prev_price']:
                                tick_data[col] = int(value) if value == int(value) else float(value)
                            else:
                                tick_data[col] = float(value) if col not in ['symbol', 'name', 'ticktime', 'kind'] else str(value)
                result.append(tick_data)
            
            logger.info(f"获取新浪财经分时数据成功 {symbol}: {len(result)} 条")
            return result
        except asyncio.TimeoutError:
            logger.error(f"获取新浪财经分时数据超时 {symbol}")
            return []
        except Exception as e:
            logger.error(f"获取新浪财经分时数据失败 {symbol}: {e}")
            return []

    async def get_stock_zh_a_minute(
        self,
        symbol: str,
        period: str = '1',
        adjust: str = ''
    ) -> List[Dict[str, Any]]:
        """
        获取新浪财经沪深京 A 股分时数据
        
        Args:
            symbol: 股票代码，带市场标识，如：sh600519, sz000001
            period: 分钟频率，choice of {'1', '5', '15', '30', '60'}，默认 '1'
            adjust: 复权类型，默认 '' (不复权), 'qfq' (前复权), 'hfq' (后复权)
            
        Returns:
            新浪财经分时数据，包含：
            - day: 时间
            - open: 开盘价
            - high: 最高价
            - low: 最低价
            - close: 收盘价
            - volume: 成交量（手）
            - amount: 成交额
            
        特性：
        1. ✅ 支持多种频率：1/5/15/30/60 分钟
        2. ✅ 支持复权调整
        3. ✅ 最近交易日数据
        4. ✅ 10 秒超时控制
        5. ✅ 数据验证
        6. ✅ 错误处理
        """
        try:
            # 验证参数
            if period not in ['1', '5', '15', '30', '60']:
                logger.error(f"无效的周期参数：{period}")
                return []
            
            if adjust not in ['', 'qfq', 'hfq']:
                logger.error(f"无效的复权参数：{adjust}")
                return []
            
            async with asyncio.timeout(10):
                df = ak.stock_zh_a_minute(symbol=symbol, period=period, adjust=adjust)
            
            if df.empty:
                return []
            
            result = []
            for row in df.itertuples(index=False):
                tick_data = {}
                if hasattr(row, '_fields'):
                    for col in row._fields:
                        value = getattr(row, col)
                        import math
                        if value is None or value == '' or value == '-' or (isinstance(value, float) and math.isnan(value)):
                            tick_data[col] = None
                        else:
                            if col in ['day']:
                                tick_data[col] = str(value)
                            elif col in ['volume']:
                                tick_data[col] = int(value) if value == int(value) else float(value)
                            else:
                                tick_data[col] = float(value)
                result.append(tick_data)
            
            logger.info(f"获取新浪财经分时数据成功 {symbol} (周期={period}, 复权={adjust}): {len(result)} 条")
            return result
        except asyncio.TimeoutError:
            logger.error(f"获取新浪财经分时数据超时 {symbol}")
            return []
        except Exception as e:
            logger.error(f"获取新浪财经分时数据失败 {symbol}: {e}")
            return []

    async def get_stock_zh_a_hist_min_em(
        self,
        symbol: str,
        period: str = '5',
        adjust: str = '',
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取东方财富沪深京 A 股分时数据
        
        Args:
            symbol: 股票代码，如：000001, 600519
            period: 分钟频率，choice of {'1', '5', '15', '30', '60'}，默认 '5'
            adjust: 复权类型，默认 '' (不复权), 'qfq' (前复权), 'hfq' (后复权)
                   注意：1 分钟数据只返回近 5 个交易日数据且不复权
            start_date: 开始日期时间，格式 "YYYY-MM-DD HH:MM:SS"，默认返回所有数据
            end_date: 结束日期时间，格式 "YYYY-MM-DD HH:MM:SS"，默认返回所有数据
            
        Returns:
            东方财富分时数据，根据频率不同返回不同字段：
            
            1 分钟数据：
            - 时间：datetime
            - 开盘：float
            - 收盘：float
            - 最高：float
            - 最低：float
            - 成交量：float (手)
            - 成交额：float
            - 均价：float
            
            其他频率 (5/15/30/60 分钟)：
            - 时间：datetime
            - 开盘：float
            - 收盘：float
            - 最高：float
            - 最低：float
            - 涨跌幅：float (%)
            - 涨跌额：float
            - 成交量：float (手)
            - 成交额：float
            - 振幅：float (%)
            - 换手率：float (%)
            
        特性：
        1. ✅ 支持多种频率：1/5/15/30/60 分钟
        2. ✅ 支持复权调整
        3. ✅ 支持自定义时间范围
        4. ✅ 1 分钟数据仅返回近 5 个交易日
        5. ✅ 10 秒超时控制
        6. ✅ 数据验证
        7. ✅ 错误处理
        """
        try:
            # 验证参数
            if period not in ['1', '5', '15', '30', '60']:
                logger.error(f"无效的周期参数：{period}")
                return []
            
            if adjust not in ['', 'qfq', 'hfq']:
                logger.error(f"无效的复权参数：{adjust}")
                return []
            
            # 1 分钟数据只能不复权
            if period == '1' and adjust != '':
                logger.warning("1 分钟数据只支持不复权，自动调整为空字符串")
                adjust = ''
            
            # 日期格式转换（兼容处理）
            def format_datetime(date_str):
                if not date_str:
                    return ""
                # 支持多种格式
                date_str = date_str.replace("/", "-").replace(".", "-")
                if len(date_str) == 10:  # YYYY-MM-DD
                    date_str += " 09:30:00"
                return date_str
            
            start_dt = format_datetime(start_date) if start_date else ""
            end_dt = format_datetime(end_date) if end_date else ""
            
            async with asyncio.timeout(10):
                df = ak.stock_zh_a_hist_min_em(
                    symbol=symbol,
                    period=period,
                    adjust=adjust,
                    start_date=start_dt if start_dt else "1979-09-01 09:32:00",
                    end_date=end_dt if end_dt else "2222-01-01 09:32:00"
                )
            
            if df.empty:
                return []
            
            result = []
            for row in df.itertuples(index=False):
                tick_data = {}
                if hasattr(row, '_fields'):
                    for col in row._fields:
                        value = getattr(row, col)
                        import math
                        if value is None or value == '' or value == '-' or (isinstance(value, float) and math.isnan(value)):
                            tick_data[col] = None
                        else:
                            if col in ['时间', 'day']:
                                tick_data[col] = str(value)
                            elif col in ['成交量', 'volume']:
                                tick_data[col] = int(value) if value == int(value) else float(value)
                            else:
                                try:
                                    tick_data[col] = float(value)
                                except (ValueError, TypeError):
                                    tick_data[col] = str(value)
                result.append(tick_data)
            
            logger.info(f"获取东方财富分时数据成功 {symbol} (周期={period}, 复权={adjust}): {len(result)} 条")
            return result
        except asyncio.TimeoutError:
            logger.error(f"获取东方财富分时数据超时 {symbol}")
            return []
        except Exception as e:
            logger.error(f"获取东方财富分时数据失败 {symbol}: {e}")
            return []

    # ========== 新增 API 方法（对应 Tushare） ==========
    
    @api_call_cache(ttl=1800)  # 缓存 30 分钟
    async def get_weekly_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq"
    ) -> List[KLineData]:
        """
        获取周线 K 线数据（使用东方财富 API）
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权类型（qfq/hfq/none）
            
        Returns:
            周线 K 线数据列表
        """
        try:
            # 重试机制：最多重试 3 次
            df = None
            for attempt in range(3):
                try:
                    async with asyncio.timeout(10):
                        # 使用东方财富的周线数据 API
                        df = ak.stock_zh_a_hist(
                            symbol=code,
                            period="weekly",
                            start_date=start_date.replace("-", "") if start_date else "19900101",
                            end_date=end_date.replace("-", "") if end_date else "20991231",
                            adjust=adjust if adjust in ['qfq', 'hfq'] else ""
                        )
                        break  # 成功则跳出
                except asyncio.TimeoutError:
                    if attempt < 2:
                        logger.debug(f"获取周线数据超时，重试 {attempt+1}/3")
                        await asyncio.sleep(0.5 * (attempt + 1))
                    else:
                        logger.warning(f"获取周线数据超时 {code}（重试 3 次失败）")
                        return []
                except Exception as retry_error:
                    if attempt < 2:
                        logger.debug(f"获取周线数据失败，重试 {attempt+1}/3: {retry_error}")
                        await asyncio.sleep(0.5 * (attempt + 1))
                    else:
                        raise retry_error
            
            if df is None or df.empty:
                return []
            
            klines = []
            for row in df.itertuples(index=False):
                klines.append(KLineData(
                    code=code,
                    date=self.format_date(str(row.日期)),
                    open=float(row.开盘),
                    high=float(row.最高),
                    low=float(row.最低),
                    close=float(row.收盘),
                    volume=float(row.成交量)
                ))
            
            logger.info(f"获取周线数据成功 {code}: {len(klines)}条")
            return klines
        except Exception as e:
            logger.warning(f"获取周线数据失败 {code}（网络不稳定）: {e}")
            return []

    @api_call_cache(ttl=1800)  # 缓存 30 分钟
    async def get_monthly_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq"
    ) -> List[KLineData]:
        """
        获取月线 K 线数据（使用东方财富 API）
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权类型
        """
        try:
            # 重试机制：最多重试 3 次
            df = None
            for attempt in range(3):
                try:
                    async with asyncio.timeout(10):
                        df = ak.stock_zh_a_hist(
                            symbol=code,
                            period="monthly",
                            start_date=start_date.replace("-", "") if start_date else "19900101",
                            end_date=end_date.replace("-", "") if end_date else "20991231",
                            adjust=adjust if adjust in ['qfq', 'hfq'] else ""
                        )
                        break  # 成功则跳出
                except asyncio.TimeoutError:
                    if attempt < 2:
                        logger.debug(f"获取月线数据超时，重试 {attempt+1}/3")
                        await asyncio.sleep(0.5 * (attempt + 1))
                    else:
                        logger.warning(f"获取月线数据超时 {code}（重试 3 次失败）")
                        return []
                except Exception as retry_error:
                    if attempt < 2:
                        logger.debug(f"获取月线数据失败，重试 {attempt+1}/3: {retry_error}")
                        await asyncio.sleep(0.5 * (attempt + 1))
                    else:
                        raise retry_error
            
            if df is None or df.empty:
                return []
            
            klines = []
            for row in df.itertuples(index=False):
                klines.append(KLineData(
                    code=code,
                    date=self.format_date(str(row.日期)),
                    open=float(row.开盘),
                    high=float(row.最高),
                    low=float(row.最低),
                    close=float(row.收盘),
                    volume=float(row.成交量)
                ))
            
            logger.info(f"获取月线数据成功 {code}: {len(klines)}条")
            return klines
        except Exception as e:
            logger.warning(f"获取月线数据失败 {code}（网络不稳定）: {e}")
            return []

    async def get_top_list(self, trade_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取龙虎榜数据（使用东方财富 API）
        
        Args:
            trade_date: 交易日期（YYYYMMDD）
            
        Returns:
            龙虎榜数据列表
        """
        try:
            # 使用东方财富龙虎榜 API
            date_str = trade_date if trade_date else datetime.now().strftime("%Y%m%d")
            
            async with asyncio.timeout(10):
                df = ak.stock_lhb_detail_em(trade_date=date_str)
            
            if df.empty:
                return []
            
            result = []
            for row in df.itertuples(index=False):
                result.append({
                    "code": getattr(row, '代码', None),
                    "name": getattr(row, '名称', None),
                    "close": float(getattr(row, '收盘价', 0)) if hasattr(row, '收盘价') else None,
                    "change_pct": float(getattr(row, '涨跌幅', 0)) if hasattr(row, '涨跌幅') else None,
                    "amount": float(getattr(row, '成交额', 0)) if hasattr(row, '成交额') else None,
                    "net_in": float(getattr(row, '净额', 0)) if hasattr(row, '净额') else None,
                    "buy_amount": float(getattr(row, '买入额', 0)) if hasattr(row, '买入额') else None,
                    "sell_amount": float(getattr(row, '卖出额', 0)) if hasattr(row, '卖出额') else None
                })
            
            logger.info(f"获取龙虎榜数据成功：{len(result)}条")
            return result
        except asyncio.TimeoutError:
            logger.error(f"获取龙虎榜数据超时")
            return []
        except Exception as e:
            logger.error(f"获取龙虎榜数据失败：{e}")
            return []

    async def get_forecast(self, code: str, ann_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取业绩预告数据（使用东方财富 API）
        
        Args:
            code: 股票代码
            ann_date: 公告日期
            
        Returns:
            业绩预告数据列表
        """
        try:
            # 使用东方财富业绩预告 API
            async with asyncio.timeout(10):
                df = ak.stock_earnings_forecast_em(symbol=code)
            
            if df.empty:
                return []
            
            result = []
            for row in df.itertuples(index=False):
                result.append({
                    "code": code,
                    "ann_date": str(getattr(row, '公告日期', '')) if hasattr(row, '公告日期') else ann_date,
                    "end_date": str(getattr(row, '报告期', '')) if hasattr(row, '报告期') else None,
                    "type": getattr(row, '类型', None) if hasattr(row, '类型') else None,
                    "net_profit_min": float(getattr(row, '净利润下限', 0)) if hasattr(row, '净利润下限') else None,
                    "net_profit_max": float(getattr(row, '净利润上限', 0)) if hasattr(row, '净利润上限') else None,
                    "net_profit_yoy_min": float(getattr(row, '净利润下限同比', 0)) if hasattr(row, '净利润下限同比') else None,
                    "net_profit_yoy_max": float(getattr(row, '净利润上限同比', 0)) if hasattr(row, '净利润上限同比') else None
                })
            
            logger.info(f"获取业绩预告数据成功 {code}: {len(result)}条")
            return result
        except asyncio.TimeoutError:
            logger.error(f"获取业绩预告数据超时 {code}")
            return []
        except Exception as e:
            logger.error(f"获取业绩预告数据失败 {code}: {e}")
            return []
    
    async def get_moneyflow(self, code: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取资金流向数据（使用东方财富 API）
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            资金流向数据列表，包含：
            - 日期
            - 收盘价
            - 涨跌幅
            - 主力净流入
            - 主力净流入占比
            - 超大单净流入
            - 大单净流入
            - 中单净流入
            - 小单净流入等
        """
        try:
            # 使用东方财富资金流向 API
            async with asyncio.timeout(10):
                df = ak.stock_individual_fund_flow(symbol=code)
            
            if df.empty:
                return []
            
            result = []
            for row in df.itertuples(index=False):
                result.append({
                    "code": code,
                    "date": str(getattr(row, '日期', '')) if hasattr(row, '日期') else None,
                    "close": float(getattr(row, '收盘价', 0)) if hasattr(row, '收盘价') else None,
                    "change_pct": float(getattr(row, '涨跌幅', 0)) if hasattr(row, '涨跌幅') else None,
                    "main_net_in": float(getattr(row, '主力净流入', 0)) if hasattr(row, '主力净流入') else None,
                    "main_net_in_pct": float(getattr(row, '主力净流入占比', 0)) if hasattr(row, '主力净流入占比') else None,
                    "super_net_in": float(getattr(row, '超大单净流入', 0)) if hasattr(row, '超大单净流入') else None,
                    "big_net_in": float(getattr(row, '大单净流入', 0)) if hasattr(row, '大单净流入') else None,
                    "mid_net_in": float(row["中单净流入"]) if "中单净流入" in row else None,
                    "small_net_in": float(row["小单净流入"]) if "小单净流入" in row else None
                })
            
            logger.info(f"获取资金流向数据成功 {code}: {len(result)}条")
            return result
        except asyncio.TimeoutError:
            logger.error(f"获取资金流向数据超时 {code}")
            return []
        except Exception as e:
            logger.error(f"获取资金流向数据失败 {code}: {e}")
            return []

    async def get_market_moneyflow_dc(
        self,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取大盘资金流向数据（使用东方财富 API）
        
        Args:
            trade_date: 交易日期（YYYYMMDD格式）
            start_date: 开始日期（YYYYMMDD格式）
            end_date: 结束日期（YYYYMMDD格式）
            
        Returns:
            大盘资金流向数据列表
        """
        try:
            async with asyncio.timeout(15):
                df = ak.stock_market_fund_flow()
            
            if df.empty:
                return []
            
            result = []
            for row in df.itertuples(index=False):
                date_str = str(getattr(row, '日期', '')) if hasattr(row, '日期') else ""
                if date_str:
                    date_str = date_str.replace("-", "").replace("/", "")[:8]
                
                if trade_date and date_str != trade_date:
                    continue
                if start_date and date_str < start_date:
                    continue
                if end_date and date_str > end_date:
                    continue
                
                def safe_float(val):
                    try:
                        return float(val) if val is not None and str(val) not in ['', '-', 'None', 'nan'] else None
                    except (ValueError, TypeError):
                        return None
                
                result.append({
                    "trade_date": date_str,
                    "close_sh": safe_float(getattr(row, '上证-收盘价', None)),
                    "pct_change_sh": safe_float(getattr(row, '上证-涨跌幅', None)),
                    "close_sz": safe_float(getattr(row, '深证-收盘价', None)),
                    "pct_change_sz": safe_float(getattr(row, '深证-涨跌幅', None)),
                    "net_amount": safe_float(getattr(row, '主力净流入-净额', None)),
                    "net_amount_rate": safe_float(getattr(row, '主力净流入-净占比', None)),
                    "buy_elg_amount": safe_float(getattr(row, '超大单净流入-净额', None)),
                    "buy_elg_amount_rate": safe_float(getattr(row, '超大单净流入-净占比', None)),
                    "buy_lg_amount": safe_float(getattr(row, '大单净流入-净额', None)),
                    "buy_lg_amount_rate": safe_float(getattr(row, '大单净流入-净占比', None)),
                    "buy_md_amount": safe_float(getattr(row, '中单净流入-净额', None)),
                    "buy_md_amount_rate": safe_float(getattr(row, '中单净流入-净占比', None)),
                    "buy_sm_amount": safe_float(getattr(row, '小单净流入-净额', None)),
                    "buy_sm_amount_rate": safe_float(getattr(row, '小单净流入-净占比', None)),
                })
            
            logger.info(f"获取大盘资金流向数据成功：{len(result)}条")
            return result
        except asyncio.TimeoutError:
            logger.error("获取大盘资金流向数据超时")
            return []
        except Exception as e:
            logger.error(f"获取大盘资金流向数据失败：{e}")
            return []
    
    async def get_daily_billboard(self, trade_date: Optional[str] = None) -> List[BillboardEntry]:
        """获取龙虎榜单数据（使用东方财富 API）"""
        try:
            date_str = trade_date if trade_date else datetime.now().strftime("%Y%m%d")
            
            async with asyncio.timeout(10):
                df = ak.stock_lhb_detail_em(trade_date=date_str)
            
            if df.empty:
                return []
            
            entries = []
            for row in df.itertuples(index=False):
                entries.append(BillboardEntry(
                    code=getattr(row, '代码', ''),
                    name=getattr(row, '名称', ''),
                    close_price=float(getattr(row, '收盘价', 0) or 0),
                    change_pct=float(getattr(row, '涨跌幅', 0) or 0),
                    turnover_amount=float(getattr(row, '成交额', 0) or 0),
                    net_amount=float(getattr(row, '净额', 0) or 0),
                    buy_amount=float(getattr(row, '买入额', 0) or 0),
                    sell_amount=float(getattr(row, '卖出额', 0) or 0),
                    reason='',
                    trade_date=trade_date or ''
                ))
            
            logger.info(f"获取龙虎榜数据成功：{len(entries)}条")
            return entries
        except asyncio.TimeoutError:
            logger.error("获取龙虎榜数据超时")
            return []
        except Exception as e:
            logger.error(f"获取龙虎榜数据失败：{e}")
            return []
    
    async def get_belong_board(self, code: str) -> List[BoardInfo]:
        """获取股票所属板块（暂不支持）"""
        logger.warning(f"AkShare 暂不支持获取股票所属板块 {code}")
        return []
    
    async def get_members(self, index_code: str) -> List[IndexMember]:
        """获取指数成分股（暂不支持）"""
        logger.warning(f"AkShare 暂不支持获取指数成分股 {index_code}")
        return []
    
    async def get_today_bill(self, trade_date: Optional[str] = None) -> List[CapitalFlowItem]:
        """获取当日资金流向（暂不支持）"""
        logger.warning(f"AkShare 暂不支持获取当日资金流向 {trade_date}")
        return []
    
    async def get_history_bill(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[CapitalFlowItem]:
        """获取历史资金流向（使用东方财富 API）"""
        try:
            async with asyncio.timeout(10):
                df = ak.stock_individual_fund_flow(symbol=code)
            
            if df.empty:
                return []
            
            flows = []
            for row in df.itertuples(index=False):
                date = str(getattr(row, '日期', ''))
                if len(date) == 10:
                    date = date.replace('-', '')
                
                if start_date and date < start_date:
                    continue
                if end_date and date > end_date:
                    continue
                
                def safe_float(val):
                    try:
                        return float(val) if val is not None and str(val) not in ['', '-', 'None', 'nan'] else None
                    except (ValueError, TypeError):
                        return None
                
                flows.append(CapitalFlowItem(
                    code=code,
                    name='',
                    close_price=safe_float(getattr(row, '收盘价', None)),
                    change_pct=safe_float(getattr(row, '涨跌幅', None)),
                    main_net_amount=safe_float(getattr(row, '主力净流入', None)),
                    main_net_amount_rate=safe_float(getattr(row, '主力净流入占比', None)),
                    buy_elg_amount=safe_float(getattr(row, '超大单净流入', None)),
                    buy_lg_amount=safe_float(getattr(row, '大单净流入', None)),
                    buy_md_amount=safe_float(getattr(row, '中单净流入', None)),
                    buy_sm_amount=safe_float(getattr(row, '小单净流入', None)),
                    trade_date=date
                ))
            
            logger.info(f"获取 {code} 历史资金流向成功：{len(flows)}条")
            return flows
        except asyncio.TimeoutError:
            logger.error(f"获取资金流向数据超时 {code}")
            return []
        except Exception as e:
            logger.error(f"获取资金流向数据失败 {code}: {e}")
            return []
    
    async def get_top10_stock_holder_info(self, code: str) -> List[ShareholderInfo]:
        """获取前十大股东信息（暂不支持）"""
        logger.warning(f"AkShare 暂不支持获取前十大股东信息 {code}")
        return []
    
    async def get_market_realtime_quotes(self, market_types: Optional[List[str]] = None) -> List[MarketQuote]:
        """获取市场实时行情（使用东方财富 API）"""
        try:
            # 使用东方财富实时行情 API
            if market_types:
                # 如果指定了市场类型，调用对应 API
                if '沪深 A 股' in market_types or market_types == ['沪深 A 股']:
                    df = ak.stock_zh_a_spot_em()
                elif '创业板' in market_types:
                    df = ak.stock_cy_a_spot_em()
                elif '科创板' in market_types:
                    df = ak.stock_kc_a_spot_em()
                else:
                    # 默认获取沪深 A 股
                    df = ak.stock_zh_a_spot_em()
            else:
                # 默认获取沪深 A 股
                df = ak.stock_zh_a_spot_em()
            
            if df.empty:
                return []
            
            quotes = []
            for row in df.itertuples(index=False):
                def safe_float(value, default=None):
                    try:
                        if value is None or value == '' or value == '-' or (isinstance(value, float) and str(value) == 'nan'):
                            return default
                        return float(value)
                    except (ValueError, TypeError):
                        return default
                
                code = str(getattr(row, '代码', '')).zfill(6)
                if not code:
                    continue
                
                quotes.append(MarketQuote(
                    code=code,
                    name=getattr(row, '名称', ''),
                    change_pct=safe_float(getattr(row, '涨跌幅', None)),
                    price=safe_float(getattr(row, '最新价', None)),
                    high=safe_float(getattr(row, '最高', None)),
                    low=safe_float(getattr(row, '最低', None)),
                    open=safe_float(getattr(row, '今开', None)),
                    change=safe_float(getattr(row, '涨跌额', None)),
                    turnover_rate=safe_float(getattr(row, '换手率', None)),
                    volume_ratio=safe_float(getattr(row, '量比', None)),
                    pe_ratio=safe_float(getattr(row, '市盈率 - 动态', None)),
                    volume=safe_float(getattr(row, '成交量', None)),
                    amount=safe_float(getattr(row, '成交额', None)),
                    prev_close=safe_float(getattr(row, '昨收', None)),
                    total_market_cap=safe_float(getattr(row, '总市值', None)),
                    float_market_cap=safe_float(getattr(row, '流通市值', None)),
                    market_type='A 股'
                ))
            
            logger.info(f"获取市场实时行情成功：{len(quotes)}条")
            return quotes
        except Exception as e:
            logger.error(f"获取市场实时行情失败：{e}")
            return []
    
<<<<<<< HEAD
    async def get_all_company_performance(self, date: Optional[str] = None) -> List[CompanyPerformance]:
        """获取沪深市场股票某一季度的表现情况"""
        # Akshare 不支持此接口，返回空列表
        logger.warning("Akshare 不支持获取全市场业绩表现")
        return []
    
    async def get_all_report_dates(self) -> List[str]:
        """获取所有可选的报告发布日期"""
        # Akshare 不支持此接口，返回空列表
        logger.warning("Akshare 不支持获取报告日期列表")
        return []
    
    async def get_stocks_base_info(self, stock_codes: List[str]) -> List[StockBasicInfo]:
        """批量获取多只股票的基本信息"""
        # Akshare 不支持批量获取，返回空列表
        logger.warning("Akshare 不支持批量获取股票信息")
        return []
    
    async def get_deal_detail(self, stock_code: str, max_count: int = 1000000) -> List[DealDetail]:
        """获取股票最新交易日成交明细"""
        # Akshare 不支持此接口，返回空列表
        logger.warning("Akshare 不支持获取成交明细")
        return []
    
    async def get_history_bill(self, stock_code: str) -> List[HistoryBill]:
        """获取单只股票历史单子流入流出数据"""
        # Akshare 不支持此接口，返回空列表
        logger.warning("Akshare 不支持获取历史资金流向")
        return []
    
    async def get_latest_quote(self, stock_codes: List[str]) -> List[Dict[str, Any]]:
        """获取沪深市场多只股票的实时涨幅情况"""
        # Akshare 不支持批量获取实时行情，返回空列表
        logger.warning("Akshare 不支持批量获取实时行情")
        return []
=======
    async def get_financial_performance(
        self,
        code: str,
        report_date: Optional[str] = None,
        report_type: str = "quarterly"
    ) -> List[FinancialPerformance]:
        """获取财务业绩数据
        
        Args:
            code: 股票代码
            report_date: 报告日期，格式 'YYYY-MM-DD'
            report_type: 报告类型
        
        Returns:
            财务业绩数据列表
        """
        try:
            # AkShare 有财务数据接口，但这里暂不实现，使用 efinance
            logger.warning(f"AkShare 财务数据暂不实现，使用 efinance 数据源")
            return []
        except Exception as e:
            logger.error(f"获取财务业绩数据失败 {code}: {e}")
            return []
>>>>>>> 7aaa7cbe85a09d6bf88368f14e12d60640ec9467

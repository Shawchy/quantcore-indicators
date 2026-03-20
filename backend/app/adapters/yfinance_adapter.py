from typing import Optional, List, Dict, Any
import yfinance as yf
import pandas as pd
from loguru import logger
import asyncio
import time

from .base import (
    BaseDataAdapter,
    DataSourceType,
    StockBasicInfo,
    KLineData,
    SectorInfo,
    ChipData
)


class YFinanceAdapter(BaseDataAdapter):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # 缓存机制
        self._cache: Dict[str, Any] = {}
        self._cache_timestamp: Dict[str, float] = {}
        self._cache_ttl = {
            'kline': 300,        # K 线：5 分钟
            'stock_info': 600,   # 股票信息：10 分钟
            'quote': 60,         # 实时行情：1 分钟
            'default': 300       # 默认：5 分钟
        }
        
        # 重试机制
        self._max_retries = 3
        self._retry_base_delay = 1.0
        
        # 超时控制
        self._timeout = 10  # 秒
    
    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.YFINANCE
    
    async def initialize(self) -> bool:
        try:
            self._is_initialized = True
            logger.info("YFinance 适配器初始化成功（已启用缓存、重试、超时控制）")
            logger.info(f"  - 缓存策略：K 线 5 分钟，股票信息 10 分钟，实时行情 1 分钟")
            logger.info(f"  - 重试机制：最多{self._max_retries}次，指数退避")
            logger.info(f"  - 超时控制：{self._timeout}秒")
            return True
        except Exception as e:
            logger.error(f"YFinance 适配器初始化失败：{e}")
            return False
    
    async def close(self) -> None:
        self._is_initialized = False
        self._cache.clear()
        self._cache_timestamp.clear()
        logger.info("YFinance 适配器已关闭")
    
    def _get_yf_symbol(self, code: str) -> str:
        if code.startswith("6"):
            return f"{code}.SS"
        else:
            return f"{code}.SZ"
    
    def _get_cache_key(self, prefix: str, **kwargs) -> str:
        """生成缓存 key"""
        key_parts = [prefix]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")
        return "_".join(key_parts)
    
    def _get_from_cache(self, key: str, ttl_type: str = 'default') -> Optional[Any]:
        """从缓存获取数据"""
        if key not in self._cache:
            return None
        
        timestamp = self._cache_timestamp.get(key, 0)
        ttl = self._cache_ttl.get(ttl_type, self._cache_ttl['default'])
        
        if time.time() - timestamp > ttl:
            # 过期，删除
            del self._cache[key]
            del self._cache_timestamp[key]
            logger.debug(f"缓存过期：{key}")
            return None
        
        logger.debug(f"缓存命中：{key}")
        return self._cache[key]
    
    def _set_to_cache(self, key: str, value: Any, ttl_type: str = 'default'):
        """设置缓存"""
        self._cache[key] = value
        self._cache_timestamp[key] = time.time()
        logger.debug(f"写入缓存：{key} (TTL: {self._cache_ttl.get(ttl_type, 300)}s)")
    
    async def _fetch_with_retry(self, func, *args, **kwargs):
        """带重试的获取（支持异步函数）"""
        for attempt in range(self._max_retries):
            try:
                async with asyncio.timeout(self._timeout):
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
            except asyncio.TimeoutError:
                if attempt < self._max_retries - 1:
                    delay = self._retry_base_delay * (2 ** attempt)
                    logger.warning(f"请求超时，{delay}秒后重试 {attempt+1}/{self._max_retries}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"请求超时（重试{self._max_retries}次失败）")
                    raise
            except Exception as e:
                if attempt < self._max_retries - 1:
                    delay = self._retry_base_delay * (2 ** attempt)
                    logger.warning(f"请求失败：{e}，{delay}秒后重试 {attempt+1}/{self._max_retries}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"请求失败（重试{self._max_retries}次失败）: {e}")
                    raise
        
        return None
    
    async def get_stock_list(self, market: Optional[str] = None) -> List[StockBasicInfo]:
        logger.warning("YFinance不支持获取A股列表")
        return []
    
    async def get_stock_info(self, code: str) -> Optional[StockBasicInfo]:
        try:
            # 缓存检查
            cache_key = self._get_cache_key('stock_info', code=code)
            cached = self._get_from_cache(cache_key, 'stock_info')
            if cached:
                return cached
            
            symbol = self._get_yf_symbol(code)
            
            async def fetch():
                ticker = yf.Ticker(symbol)
                return ticker.info
            
            info = await self._fetch_with_retry(fetch)
            
            stock_info = StockBasicInfo(
                code=code,
                name=info.get("longName", info.get("shortName", "")),
                market="SH" if code.startswith("6") else "SZ",
                industry=info.get("industry"),
                sector=info.get("sector"),
                total_shares=info.get("sharesOutstanding")
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
            # 缓存检查
            cache_key = self._get_cache_key('kline', code=code, start=start_date, end=end_date, adjust=adjust)
            cached = self._get_from_cache(cache_key, 'kline')
            if cached:
                logger.debug(f"K 线缓存命中：{code}")
                return cached
            
            symbol = self._get_yf_symbol(code)
            auto_adjust = adjust in ["qfq", "hfq"]
            
            async def fetch():
                ticker = yf.Ticker(symbol)
                return ticker.history(
                    start=start_date,
                    end=end_date,
                    auto_adjust=auto_adjust
                )
            
            df = await self._fetch_with_retry(fetch)
            
            klines = []
            for idx, row in enumerate(df.itertuples(index=False)):
                klines.append(KLineData(
                    code=code,
                    date=df.index[idx].strftime("%Y-%m-%d"),
                    open=float(row.Open),
                    high=float(row.High),
                    low=float(row.Low),
                    close=float(row.Close),
                    volume=float(row.Volume),
                    amount=None
                ))
            
            # 保存到缓存
            self._set_to_cache(cache_key, klines, 'kline')
            
            return klines
        except asyncio.TimeoutError:
            logger.error(f"获取 K 线数据超时 {code}: 超过{self._timeout}秒")
            return []
        except Exception as e:
            logger.error(f"获取 K 线数据失败 {code}: {e}")
            return []
    
    async def get_realtime_quote(self, code: str) -> Dict[str, Any]:
        try:
            # 缓存检查（实时行情缓存时间短）
            cache_key = self._get_cache_key('quote', code=code)
            cached = self._get_from_cache(cache_key, 'quote')
            if cached:
                return cached
            
            symbol = self._get_yf_symbol(code)
            
            async def fetch():
                ticker = yf.Ticker(symbol)
                return ticker.info
            
            info = await self._fetch_with_retry(fetch)
            
            quote = {
                "code": code,
                "name": info.get("longName", ""),
                "price": info.get("currentPrice", info.get("regularMarketPrice", 0)),
                "change": info.get("regularMarketChange", 0),
                "change_pct": info.get("regularMarketChangePercent", 0),
                "volume": info.get("regularMarketVolume", 0),
                "high": info.get("dayHigh", 0),
                "low": info.get("dayLow", 0),
                "open": info.get("regularMarketOpen", 0),
                "prev_close": info.get("previousClose", 0)
            }
            
            # 保存到缓存
            self._set_to_cache(cache_key, quote, 'quote')
            
            return quote
        except asyncio.TimeoutError:
            logger.error(f"获取实时行情超时 {code}: 超过{self._timeout}秒")
            return {}
        except Exception as e:
            logger.error(f"获取实时行情失败 {code}: {e}")
            return {}
    
    async def get_sector_list(self, sector_type: str = "industry") -> List[SectorInfo]:
        logger.warning("YFinance不支持获取A股板块列表")
        return []
    
    async def get_sector_components(self, sector_code: str) -> List[str]:
        logger.warning("YFinance不支持获取板块成分股")
        return []
    
    async def get_chip_data(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[ChipData]:
        try:
            # 缓存检查
            cache_key = self._get_cache_key('chip', code=code)
            cached = self._get_from_cache(cache_key, 'stock_info')
            if cached:
                return cached
            
            symbol = self._get_yf_symbol(code)
            
            async def fetch():
                ticker = yf.Ticker(symbol)
                return ticker.major_holders, ticker.institutional_holders
            
            major_holders, institutional_holders = await self._fetch_with_retry(fetch)
            
            chip_data = [ChipData(
                code=code,
                date=pd.Timestamp.now().strftime("%Y-%m-%d"),
                top10_holders_ratio=major_holders.iloc[0, 0] if not major_holders.empty else None
            )]
            
            # 保存到缓存
            self._set_to_cache(cache_key, chip_data, 'stock_info')
            
            return chip_data
        except Exception as e:
            logger.error(f"获取筹码数据失败 {code}: {e}")
            return []
    
    # ========== 批量接口（覆盖基类默认实现） ==========
    
    async def get_kline_batch(
        self,
        codes: List[str],
        start_date: str,
        end_date: str,
        adjust: str = "qfq",
        batch_size: int = 5,
        max_concurrent: int = 2
    ) -> Dict[str, List[KLineData]]:
        """批量获取 K 线数据（针对 YFinance 优化）
        
        YFinance 对并发有限制，使用更保守的参数
        """
        return await super().get_kline_batch(
            codes, start_date, end_date, adjust,
            batch_size=batch_size,
            max_concurrent=max_concurrent
        )
    
    async def get_stock_info_batch(
        self,
        codes: List[str],
        batch_size: int = 10,
        max_concurrent: int = 3
    ) -> Dict[str, StockBasicInfo]:
        """批量获取股票信息（针对 YFinance 优化）"""
        return await super().get_stock_info_batch(
            codes,
            batch_size=batch_size,
            max_concurrent=max_concurrent
        )

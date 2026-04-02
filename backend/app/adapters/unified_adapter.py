"""
统一数据源适配器

整合 AKShare API 和 Playwright 浏览器两种方式：
1. 优先使用 AKShare（快速、低资源）
2. AKShare 失败时自动降级到 Playwright
3. 共享 Cookie 和代理配置
"""

from typing import Optional, List, Dict, Any
from loguru import logger
from datetime import datetime
import asyncio

from .base import (
    BaseDataAdapter,
    DataSourceType,
    StockBasicInfo,
    KLineData,
    SectorInfo,
    MarketQuote
)
from .akshare_adapter import AkShareAdapter
from .enhanced_playwright_adapter import EnhancedPlaywrightAdapter
from .anti_wind_control import AntiWindControlManager


class UnifiedDataAdapter(BaseDataAdapter):
    """统一数据源适配器
    
    自动在 AKShare API 和 Playwright 浏览器之间切换：
    - 正常情况使用 AKShare（快速、低资源消耗）
    - API 失败/被封时自动降级到 Playwright（反风控兜底）
    - 可以共享 Cookie 和代理配置
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        self._config = {
            'enable_browser_fallback': True,
            'max_api_retries': 2,
            'browser_headless': True,
            'share_cookies': True,
            'share_proxy': True,
            **(config or {})
        }
        
        self._api_adapter: Optional[AkShareAdapter] = None
        self._browser_adapter: Optional[EnhancedPlaywrightAdapter] = None
        self._anti_wind = AntiWindControlManager()
        
        self._is_initialized = False
        self._current_source = "api"
        self._api_fail_count = 0
        self._api_fail_threshold = 3
    
    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.AKSHARE
    
    async def initialize(self) -> bool:
        try:
            self._api_adapter = AkShareAdapter()
            await self._api_adapter.initialize()
            logger.info("AKShare 适配器初始化成功")
            
            if self._config['enable_browser_fallback']:
                self._browser_adapter = EnhancedPlaywrightAdapter({
                    'headless': self._config['browser_headless'],
                    'enable_proxy': self._config['share_proxy'],
                    'enable_cookies': self._config['share_cookies'],
                })
            
            self._is_initialized = True
            return True
            
        except Exception as e:
            logger.error(f"统一适配器初始化失败: {e}")
            return False
    
    async def _ensure_browser_ready(self) -> bool:
        if not self._browser_adapter:
            return False
        
        if not self._browser_adapter._is_initialized:
            logger.info("初始化浏览器适配器...")
            success = await self._browser_adapter.initialize()
            if success:
                if self._config['share_proxy']:
                    for proxy in self._anti_wind.proxy_pool._proxies:
                        self._browser_adapter.add_proxy(proxy.host, proxy.port)
            return success
        
        return True
    
    async def _execute_with_fallback(self, method_name: str, *args, **kwargs) -> Any:
        if not self._is_initialized:
            raise RuntimeError("适配器未初始化")
        
        result = None
        use_browser = self._api_fail_count >= self._api_fail_threshold
        
        if not use_browser:
            try:
                method = getattr(self._api_adapter, method_name)
                result = await method(*args, **kwargs)
                
                if result is not None and (not isinstance(result, (list, dict)) or len(result) > 0):
                    self._api_fail_count = 0
                    self._current_source = "api"
                    return result
                    
            except Exception as e:
                logger.warning(f"AKShare {method_name} 失败: {e}")
                self._api_fail_count += 1
        
        if self._config['enable_browser_fallback']:
            if await self._ensure_browser_ready():
                try:
                    logger.info(f"使用浏览器适配器执行 {method_name}")
                    method = getattr(self._browser_adapter, method_name)
                    result = await method(*args, **kwargs)
                    self._current_source = "browser"
                    return result
                    
                except Exception as e:
                    logger.error(f"浏览器适配器 {method_name} 也失败: {e}")
        
        return result
    
    async def get_stock_list(self, market: Optional[str] = None) -> List[StockBasicInfo]:
        return await self._execute_with_fallback('get_stock_list', market)
    
    async def get_stock_info(self, code: str) -> Optional[StockBasicInfo]:
        return await self._execute_with_fallback('get_stock_info', code)
    
    async def get_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq"
    ) -> List[KLineData]:
        return await self._execute_with_fallback('get_kline', code, start_date, end_date, adjust)
    
    async def get_market_realtime_quotes(
        self,
        market_types: Optional[List[str]] = None
    ) -> List[MarketQuote]:
        return await self._execute_with_fallback('get_market_realtime_quotes', market_types)
    
    async def get_sector_list(self, sector_type: str = "industry") -> List[SectorInfo]:
        return await self._execute_with_fallback('get_sector_list', sector_type)
    
    async def get_sector_components(self, sector_code: str) -> List[str]:
        return await self._execute_with_fallback('get_sector_components', sector_code)
    
    async def get_realtime_quote(self, code: str) -> Dict[str, Any]:
        return await self._execute_with_fallback('get_realtime_quote', code)
    
    def add_proxy(self, host: str, port: int, **kwargs) -> None:
        self._anti_wind.add_proxy(host, port, **kwargs)
        
        if self._browser_adapter and self._config['share_proxy']:
            self._browser_adapter.add_proxy(host, port, **kwargs)
    
    def add_proxies_from_file(self, filepath: str) -> int:
        count = self._anti_wind.add_proxies_from_file(filepath)
        
        if self._browser_adapter and self._config['share_proxy']:
            self._browser_adapter.add_proxies_from_file(filepath)
        
        return count
    
    async def force_use_browser(self) -> None:
        self._api_fail_count = self._api_fail_threshold
        logger.info("已切换到浏览器模式")
    
    async def force_use_api(self) -> None:
        self._api_fail_count = 0
        self._current_source = "api"
        logger.info("已切换到 API 模式")
    
    def get_status(self) -> Dict[str, Any]:
        return {
            'initialized': self._is_initialized,
            'current_source': self._current_source,
            'api_fail_count': self._api_fail_count,
            'browser_available': self._browser_adapter is not None,
            'browser_initialized': (
                self._browser_adapter._is_initialized 
                if self._browser_adapter else False
            ),
            'anti_wind_stats': self._anti_wind.get_stats(),
        }
    
    async def close(self) -> None:
        if self._browser_adapter:
            await self._browser_adapter.close()
        
        self._is_initialized = False
        logger.info("统一数据源适配器已关闭")

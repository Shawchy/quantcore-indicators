"""
智能数据源切换器

特性：
1. 自动检测数据源故障
2. API 失败时自动降级到浏览器数据源
3. 健康状态监控
4. 自动恢复机制
"""

from typing import Optional, Dict, Any, List, Callable
from loguru import logger
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass, field
from enum import Enum
import random


class DataSourceHealth(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class DataSourceStatus:
    name: str
    health: DataSourceHealth = DataSourceHealth.HEALTHY
    consecutive_failures: int = 0
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    total_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    last_error: Optional[str] = None
    cooldown_until: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 1.0
        return 1.0 - (self.failed_requests / self.total_requests)
    
    @property
    def is_available(self) -> bool:
        if self.health == DataSourceHealth.UNHEALTHY:
            if self.cooldown_until and datetime.now() < self.cooldown_until:
                return False
        return True


@dataclass
class FallbackConfig:
    enable_browser_fallback: bool = True
    max_retries_before_fallback: int = 2
    health_check_interval: int = 60
    unhealthy_threshold: int = 5
    recovery_threshold: int = 3
    cooldown_duration: int = 300
    browser_headless: bool = True
    browser_proxy: Optional[str] = None


class SmartDataSourceSwitcher:
    """智能数据源切换器
    
    自动在 API 数据源和浏览器数据源之间切换：
    - 正常情况使用 API（快速、低资源）
    - API 失败时自动降级到浏览器（反风控兜底）
    - 定期健康检查，自动恢复
    """
    
    def __init__(self, config: Optional[FallbackConfig] = None):
        self._config = config or FallbackConfig()
        self._api_adapter = None
        self._browser_adapter = None
        self._status: Dict[str, DataSourceStatus] = {}
        self._current_source: str = "api"
        self._is_initialized = False
        self._health_check_task = None
        
    async def initialize(
        self,
        api_adapter,
        browser_adapter=None
    ) -> bool:
        self._api_adapter = api_adapter
        
        if self._config.enable_browser_fallback:
            if browser_adapter:
                self._browser_adapter = browser_adapter
            else:
                try:
                    from .playwright_adapter import PlaywrightAdapter
                    self._browser_adapter = PlaywrightAdapter({
                        'headless': self._config.browser_headless,
                        'proxy': self._config.browser_proxy
                    })
                except ImportError:
                    logger.warning("Playwright 未安装，浏览器降级功能不可用")
                    self._browser_adapter = None
        
        self._status['api'] = DataSourceStatus(name='api')
        self._status['browser'] = DataSourceStatus(name='browser')
        
        if self._browser_adapter:
            browser_init = await self._browser_adapter.initialize()
            if not browser_init:
                logger.warning("浏览器适配器初始化失败")
                self._browser_adapter = None
        
        self._is_initialized = True
        logger.info(f"智能数据源切换器初始化完成，浏览器降级: {'启用' if self._browser_adapter else '禁用'}")
        return True
    
    async def close(self) -> None:
        if self._health_check_task:
            self._health_check_task.cancel()
        
        if self._browser_adapter:
            await self._browser_adapter.close()
        
        self._is_initialized = False
        logger.info("智能数据源切换器已关闭")
    
    def _update_status(self, source: str, success: bool, response_time: float = 0, error: str = None):
        status = self._status.get(source)
        if not status:
            return
        
        status.total_requests += 1
        
        if success:
            status.consecutive_failures = 0
            status.last_success = datetime.now()
            
            if status.avg_response_time == 0:
                status.avg_response_time = response_time
            else:
                status.avg_response_time = status.avg_response_time * 0.8 + response_time * 0.2
            
            if status.health == DataSourceHealth.UNHEALTHY:
                if status.consecutive_failures == 0:
                    pass
            elif status.health == DataSourceHealth.DEGRADED:
                if status.consecutive_failures == 0:
                    status.health = DataSourceHealth.HEALTHY
                    logger.info(f"数据源 {source} 已恢复健康")
        else:
            status.consecutive_failures += 1
            status.failed_requests += 1
            status.last_failure = datetime.now()
            status.last_error = error
            
            if status.consecutive_failures >= self._config.unhealthy_threshold:
                status.health = DataSourceHealth.UNHEALTHY
                status.cooldown_until = datetime.now() + timedelta(seconds=self._config.cooldown_duration)
                logger.warning(f"数据源 {source} 标记为不健康，冷却至 {status.cooldown_until}")
            elif status.consecutive_failures >= self._config.max_retries_before_fallback:
                status.health = DataSourceHealth.DEGRADED
                logger.warning(f"数据源 {source} 标记为降级")
    
    def _should_fallback_to_browser(self) -> bool:
        if not self._browser_adapter:
            return False
        
        api_status = self._status.get('api')
        if not api_status:
            return False
        
        if api_status.health == DataSourceHealth.UNHEALTHY:
            return True
        
        if api_status.consecutive_failures >= self._config.max_retries_before_fallback:
            return True
        
        return False
    
    async def execute_with_fallback(
        self,
        method_name: str,
        *args,
        prefer_browser: bool = False,
        **kwargs
    ) -> Any:
        if not self._is_initialized:
            raise RuntimeError("切换器未初始化")
        
        start_time = datetime.now()
        
        if prefer_browser and self._browser_adapter:
            return await self._execute_browser(method_name, *args, **kwargs)
        
        if self._should_fallback_to_browser():
            logger.info(f"API 数据源不健康，自动切换到浏览器")
            return await self._execute_browser(method_name, *args, **kwargs)
        
        result = await self._execute_api(method_name, *args, **kwargs)
        
        if result is None or (isinstance(result, (list, dict)) and len(result) == 0):
            if self._browser_adapter:
                logger.info(f"API 返回空数据，尝试浏览器降级")
                result = await self._execute_browser(method_name, *args, **kwargs)
        
        return result
    
    async def _execute_api(self, method_name: str, *args, **kwargs) -> Any:
        start_time = datetime.now()
        
        try:
            method = getattr(self._api_adapter, method_name)
            result = await method(*args, **kwargs)
            
            response_time = (datetime.now() - start_time).total_seconds()
            self._update_status('api', success=True, response_time=response_time)
            
            return result
            
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            self._update_status('api', success=False, response_time=response_time, error=str(e))
            logger.warning(f"API {method_name} 失败: {e}")
            return None
    
    async def _execute_browser(self, method_name: str, *args, **kwargs) -> Any:
        if not self._browser_adapter:
            return None
        
        start_time = datetime.now()
        
        try:
            method = getattr(self._browser_adapter, method_name, None)
            if not method:
                logger.warning(f"浏览器适配器不支持方法: {method_name}")
                return None
            
            result = await method(*args, **kwargs)
            
            response_time = (datetime.now() - start_time).total_seconds()
            self._update_status('browser', success=True, response_time=response_time)
            
            return result
            
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            self._update_status('browser', success=False, response_time=response_time, error=str(e))
            logger.error(f"浏览器 {method_name} 失败: {e}")
            return None
    
    async def get_stock_list(self, market: Optional[str] = None) -> List:
        return await self.execute_with_fallback('get_stock_list', market)
    
    async def get_stock_info(self, code: str) -> Any:
        return await self.execute_with_fallback('get_stock_info', code)
    
    async def get_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq"
    ) -> List:
        return await self.execute_with_fallback('get_kline', code, start_date, end_date, adjust)
    
    async def get_market_realtime_quotes(self, market_types: Optional[List[str]] = None) -> List:
        return await self.execute_with_fallback('get_market_realtime_quotes', market_types)
    
    async def get_sector_list(self, sector_type: str = "industry") -> List:
        return await self.execute_with_fallback('get_sector_list', sector_type)
    
    async def get_realtime_quote(self, code: str) -> Dict:
        return await self.execute_with_fallback('get_realtime_quote', code)
    
    def get_status_report(self) -> Dict[str, Any]:
        return {
            'current_source': self._current_source,
            'browser_available': self._browser_adapter is not None,
            'sources': {
                name: {
                    'health': status.health.value,
                    'consecutive_failures': status.consecutive_failures,
                    'success_rate': f"{status.success_rate * 100:.1f}%",
                    'avg_response_time': f"{status.avg_response_time:.2f}s",
                    'total_requests': status.total_requests,
                    'last_success': status.last_success.isoformat() if status.last_success else None,
                    'last_failure': status.last_failure.isoformat() if status.last_failure else None,
                    'last_error': status.last_error,
                    'is_available': status.is_available,
                }
                for name, status in self._status.items()
            },
            'config': {
                'enable_browser_fallback': self._config.enable_browser_fallback,
                'max_retries_before_fallback': self._config.max_retries_before_fallback,
                'unhealthy_threshold': self._config.unhealthy_threshold,
                'cooldown_duration': self._config.cooldown_duration,
            }
        }
    
    async def force_switch_to_browser(self) -> bool:
        if not self._browser_adapter:
            return False
        
        self._current_source = "browser"
        logger.info("强制切换到浏览器数据源")
        return True
    
    async def force_switch_to_api(self) -> bool:
        self._current_source = "api"
        logger.info("强制切换到 API 数据源")
        return True
    
    async def reset_status(self, source: str = "api"):
        if source in self._status:
            self._status[source] = DataSourceStatus(name=source)
            logger.info(f"已重置 {source} 数据源状态")
    
    async def set_proxy(self, proxy: str):
        if self._browser_adapter:
            await self._browser_adapter.set_proxy(proxy)
            logger.info(f"浏览器代理已设置: {proxy}")
    
    async def clear_proxy(self):
        if self._browser_adapter:
            await self._browser_adapter.clear_proxy()
            logger.info("浏览器代理已清除")

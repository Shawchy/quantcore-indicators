"""
智能数据源路由器

根据 API 敏感度自动选择最优方案：
1. 低敏感 API → curl_cffi（快速、低资源）
2. 高敏感 API → Playwright（反风控兜底）

使用统一策略配置 (strategy_config.py)
"""

from typing import Optional, Dict, Any, List, Callable
from loguru import logger
from dataclasses import dataclass
from enum import Enum
import asyncio

# 导入统一策略配置
from .strategy_config import (
    APISensitivity,
    get_strategy,
    get_client_config,
    UNIFIED_DATA_STRATEGY,
)


@dataclass
class APIConfig:
    """API 配置（兼容旧版本，实际使用统一策略配置）"""
    name: str
    sensitivity: APISensitivity
    preferred_client: str  # "curl_cffi" or "playwright"
    fallback_client: Optional[str] = None


class SmartDataRouter:
    """智能数据源路由器
    
    根据 API 敏感度自动选择最优方案：
    - 低敏感 API：优先使用 curl_cffi（快速）
    - 高敏感 API：直接使用 Playwright（可靠）
    
    使用统一策略配置替代分散的 API_CONFIGS
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._config = {
            'auto_fallback': True,
            'cache_client': True,
            'log_routing': True,
            **(config or {})
        }
        
        self._curl_client = None
        self._playwright_client = None
        
        self._stats = {
            'curl_cffi_requests': 0,
            'playwright_requests': 0,
            'fallback_count': 0,
            'success_by_client': {'curl_cffi': 0, 'playwright': 0},
            'failure_by_client': {'curl_cffi': 0, 'playwright': 0},
        }
    
    async def initialize(self) -> bool:
        """初始化客户端"""
        try:
            # 初始化 curl_cffi
            from curl_cffi.requests import Session
            self._curl_client = Session(impersonate="chrome120")
            logger.info("curl_cffi 客户端初始化成功")
            
            return True
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            return False
    
    async def _ensure_playwright(self) -> bool:
        """确保 Playwright 客户端可用"""
        if self._playwright_client and self._playwright_client._is_initialized:
            return True
        
        try:
            from .enhanced_playwright_adapter import EnhancedPlaywrightAdapter
            self._playwright_client = EnhancedPlaywrightAdapter()
            return await self._playwright_client.initialize()
        except Exception as e:
            logger.error(f"Playwright 初始化失败: {e}")
            return False
    
    def get_api_config(self, api_name: str) -> APIConfig:
        """
        获取 API 配置 - 使用统一策略配置
        
        Args:
            api_name: API 名称（数据类型）
        
        Returns:
            API 配置
        """
        # 优先使用统一策略配置
        strategy = get_strategy(api_name)
        if strategy:
            return APIConfig(
                name=api_name,
                sensitivity=strategy.sensitivity,
                preferred_client=strategy.preferred_client,
                fallback_client=strategy.fallback_client,
            )
        
        # 默认配置
        return APIConfig(
            name=api_name,
            sensitivity=APISensitivity.LOW,
            preferred_client='curl_cffi',
            fallback_client=None,
        )
    
    async def route_request(
        self,
        api_name: str,
        request_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        路由请求到合适的客户端
        
        Args:
            api_name: API 名称（数据类型）
            request_func: 请求函数
            *args, **kwargs: 请求参数
        
        Returns:
            请求结果
        """
        config = self.get_api_config(api_name)
        
        if self._config['log_routing']:
            logger.debug(f"路由请求 {api_name}: 敏感度={config.sensitivity.value}, 客户端={config.preferred_client}")
        
        # 根据敏感度选择客户端
        if config.sensitivity == APISensitivity.HIGH:
            # 高敏感：直接使用 Playwright
            return await self._execute_with_playwright(request_func, *args, **kwargs)
        
        elif config.sensitivity == APISensitivity.MEDIUM:
            # 中敏感：先尝试 curl_cffi，失败时降级到 Playwright
            try:
                return await self._execute_with_curl(request_func, *args, **kwargs)
            except Exception as e:
                if self._config['auto_fallback'] and config.fallback_client:
                    logger.warning(f"curl_cffi 失败，降级到 Playwright: {e}")
                    self._stats['fallback_count'] += 1
                    return await self._execute_with_playwright(request_func, *args, **kwargs)
                raise
        
        else:
            # 低敏感：使用 curl_cffi
            return await self._execute_with_curl(request_func, *args, **kwargs)
    
    async def _execute_with_curl(self, func: Callable, *args, **kwargs) -> Any:
        """使用 curl_cffi 执行请求"""
        if not self._curl_client:
            raise RuntimeError("curl_cffi 客户端未初始化")
        
        self._stats['curl_cffi_requests'] += 1
        
        try:
            # 将 curl_cffi session 注入 kwargs
            if 'session' not in kwargs:
                kwargs['session'] = self._curl_client
            
            result = await func(*args, **kwargs)
            self._stats['success_by_client']['curl_cffi'] += 1
            return result
        except Exception as e:
            self._stats['failure_by_client']['curl_cffi'] += 1
            raise
    
    async def _execute_with_playwright(self, func: Callable, *args, **kwargs) -> Any:
        """使用 Playwright 执行请求"""
        if not await self._ensure_playwright():
            raise RuntimeError("Playwright 客户端不可用")
        
        self._stats['playwright_requests'] += 1
        
        try:
            # 将 Playwright 客户端注入 kwargs
            if 'playwright' not in kwargs:
                kwargs['playwright'] = self._playwright_client
            
            result = await func(*args, **kwargs)
            self._stats['success_by_client']['playwright'] += 1
            return result
        except Exception as e:
            self._stats['failure_by_client']['playwright'] += 1
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """获取路由统计信息"""
        total_requests = self._stats['curl_cffi_requests'] + self._stats['playwright_requests']
        
        return {
            **self._stats,
            'total_requests': total_requests,
            'curl_cffi_ratio': self._stats['curl_cffi_requests'] / total_requests if total_requests > 0 else 0,
            'playwright_ratio': self._stats['playwright_requests'] / total_requests if total_requests > 0 else 0,
            'fallback_rate': self._stats['fallback_count'] / total_requests if total_requests > 0 else 0,
        }
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self._stats = {
            'curl_cffi_requests': 0,
            'playwright_requests': 0,
            'fallback_count': 0,
            'success_by_client': {'curl_cffi': 0, 'playwright': 0},
            'failure_by_client': {'curl_cffi': 0, 'playwright': 0},
        }
    
    async def close(self) -> None:
        """关闭路由器"""
        if self._curl_client:
            try:
                self._curl_client.close()
                logger.info("curl_cffi 客户端已关闭")
            except Exception as e:
                logger.error(f"关闭 curl_cffi 客户端失败: {e}")
        
        if self._playwright_client:
            try:
                await self._playwright_client.close()
                logger.info("Playwright 客户端已关闭")
            except Exception as e:
                logger.error(f"关闭 Playwright 客户端失败: {e}")
    
    def get_all_api_configs(self) -> Dict[str, APIConfig]:
        """获取所有 API 配置 - 使用统一策略配置"""
        from .strategy_config import get_all_data_types
        
        return {
            data_type: self.get_api_config(data_type)
            for data_type in get_all_data_types()
        }


# 全局路由器实例
smart_router = SmartDataRouter()

"""
智能数据源路由器

根据 API 敏感度自动选择最优方案：
1. 低敏感 API → curl_cffi（快速、低资源）
2. 高敏感 API → Playwright（反风控兜底）
"""

from typing import Optional, Dict, Any, List, Callable
from loguru import logger
from dataclasses import dataclass
from enum import Enum
import asyncio


class APISensitivity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class APIConfig:
    name: str
    sensitivity: APISensitivity
    preferred_client: str  # "curl_cffi" or "playwright"
    fallback_client: Optional[str] = None


class SmartDataRouter:
    """智能数据源路由器
    
    根据 API 敏感度自动选择最优方案：
    - 低敏感 API：优先使用 curl_cffi（快速）
    - 高敏感 API：直接使用 Playwright（可靠）
    """
    
    API_CONFIGS = {
        # 高敏感 API - 必须使用 Playwright
        'stock_list': APIConfig('A股列表', APISensitivity.HIGH, 'playwright'),
        'realtime_quotes': APIConfig('实时行情', APISensitivity.HIGH, 'playwright'),
        'sector_list': APIConfig('板块列表', APISensitivity.HIGH, 'playwright'),
        'board_list': APIConfig('板块列表', APISensitivity.HIGH, 'playwright'),
        
        # 中敏感 API - 优先 curl_cffi，失败时切换 Playwright
        'fund_flow': APIConfig('资金流向', APISensitivity.MEDIUM, 'curl_cffi', 'playwright'),
        'main_fund_flow': APIConfig('主力资金', APISensitivity.MEDIUM, 'curl_cffi', 'playwright'),
        
        # 低敏感 API - 使用 curl_cffi
        'kline': APIConfig('K线数据', APISensitivity.LOW, 'curl_cffi'),
        'quote_history': APIConfig('历史行情', APISensitivity.LOW, 'curl_cffi'),
        'stock_info': APIConfig('个股信息', APISensitivity.LOW, 'curl_cffi'),
    }
    
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
        """获取 API 配置"""
        return self.API_CONFIGS.get(api_name, APIConfig(
            api_name, APISensitivity.MEDIUM, 'curl_cffi', 'playwright'
        ))
    
    async def execute(
        self,
        api_name: str,
        func_curl: Optional[Callable] = None,
        func_playwright: Optional[Callable] = None,
        **kwargs
    ) -> Any:
        """执行请求，自动选择最优方案
        
        Args:
            api_name: API 名称
            func_curl: curl_cffi 方式的请求函数
            func_playwright: Playwright 方式的请求函数
            **kwargs: 传递给请求函数的参数
        """
        config = self.get_api_config(api_name)
        
        if self._config['log_routing']:
            logger.info(f"路由 {api_name}: 敏感度={config.sensitivity.value}, 首选={config.preferred_client}")
        
        # 根据配置选择客户端
        if config.preferred_client == 'playwright':
            return await self._execute_playwright(api_name, func_playwright, **kwargs)
        else:
            result = await self._execute_curl(api_name, func_curl, **kwargs)
            
            # 如果失败且支持回退
            if result is None and config.fallback_client == 'playwright' and self._config['auto_fallback']:
                logger.info(f"{api_name}: curl_cffi 失败，回退到 Playwright")
                self._stats['fallback_count'] += 1
                result = await self._execute_playwright(api_name, func_playwright, **kwargs)
            
            return result
    
    async def _execute_curl(self, api_name: str, func: Optional[Callable], **kwargs) -> Any:
        """使用 curl_cffi 执行"""
        if not func or not self._curl_client:
            return None
        
        self._stats['curl_cffi_requests'] += 1
        
        try:
            result = await func(self._curl_client, **kwargs)
            self._stats['success_by_client']['curl_cffi'] += 1
            return result
        except Exception as e:
            self._stats['failure_by_client']['curl_cffi'] += 1
            logger.warning(f"curl_cffi {api_name} 失败: {type(e).__name__}")
            return None
    
    async def _execute_playwright(self, api_name: str, func: Optional[Callable], **kwargs) -> Any:
        """使用 Playwright 执行"""
        if not func:
            return None
        
        if not await self._ensure_playwright():
            return None
        
        self._stats['playwright_requests'] += 1
        
        try:
            result = await func(self._playwright_client, **kwargs)
            self._stats['success_by_client']['playwright'] += 1
            return result
        except Exception as e:
            self._stats['failure_by_client']['playwright'] += 1
            logger.error(f"Playwright {api_name} 失败: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self._stats,
            'curl_cffi_success_rate': (
                self._stats['success_by_client']['curl_cffi'] / 
                max(1, self._stats['curl_cffi_requests'])
            ),
            'playwright_success_rate': (
                self._stats['success_by_client']['playwright'] / 
                max(1, self._stats['playwright_requests'])
            ),
        }
    
    async def close(self):
        """关闭客户端"""
        if self._curl_client:
            try:
                self._curl_client.close()
            except:
                pass
        
        if self._playwright_client:
            try:
                await self._playwright_client.close()
            except:
                pass


class OptimizedRetryPolicy:
    """优化的重试策略
    
    根据错误类型决定是否重试：
    - TLS 指纹错误：不重试，直接切换方案
    - 网络错误：可重试
    - 限流：等待后重试
    """
    
    # 不应重试的错误（需要切换方案）
    NO_RETRY_ERRORS = [
        'Connection closed abruptly',
        'RemoteDisconnected',
        'Remote end closed connection',
        'Connection aborted',
        'Empty reply from server',
    ]
    
    @classmethod
    def should_retry(cls, error: Exception, attempt: int, max_retries: int = 2) -> bool:
        """判断是否应该重试"""
        error_str = str(error)
        
        # TLS 指纹错误不重试
        for indicator in cls.NO_RETRY_ERRORS:
            if indicator in error_str:
                return False
        
        # 其他错误可重试
        return attempt < max_retries
    
    @classmethod
    def get_action(cls, error: Exception) -> str:
        """获取建议的操作"""
        error_str = str(error)
        
        for indicator in cls.NO_RETRY_ERRORS:
            if indicator in error_str:
                return "switch_to_playwright"
        
        if 'timeout' in error_str.lower():
            return "retry_with_longer_timeout"
        
        if '429' in error_str or 'rate' in error_str.lower():
            return "wait_and_retry"
        
        return "retry"


def get_optimized_retry_config() -> Dict[str, Any]:
    """获取优化的重试配置"""
    return {
        # 不重试的情况
        'no_retry_on': [
            'Connection closed abruptly',
            'RemoteDisconnected',
            'Remote end closed connection',
            'Connection aborted',
            'Empty reply from server',
        ],
        
        # 可重试的情况
        'retry_on': {
            'timeout': {'max_retries': 2, 'base_delay': 3.0},
            'network_error': {'max_retries': 2, 'base_delay': 2.0},
            'server_error': {'max_retries': 2, 'base_delay': 5.0},
            'rate_limited': {'max_retries': 1, 'base_delay': 30.0},
        },
        
        # 重试间延迟策略
        'delay_strategy': 'exponential_jitter',  # 指数退避 + 随机抖动
        'max_delay': 60.0,
        'jitter_range': (0.8, 1.2),
    }


async def test_smart_router():
    """测试智能路由器"""
    print("\n=== 测试智能数据源路由器 ===\n")
    
    router = SmartDataRouter()
    
    print("API 敏感度配置:")
    for name, config in router.API_CONFIGS.items():
        print(f"  {name}: {config.sensitivity.value} → {config.preferred_client}")
    
    print("\n建议:")
    print("  1. 高敏感 API（A股列表、板块列表）: 直接使用 Playwright")
    print("  2. 中敏感 API（资金流向）: 优先 curl_cffi，失败时切换 Playwright")
    print("  3. 低敏感 API（K线）: 使用 curl_cffi")


if __name__ == "__main__":
    asyncio.run(test_smart_router())

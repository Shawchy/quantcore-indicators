"""
反风控策略模块（优化版）

提供统一的反爬虫策略门面，支持多种策略的动态组合和配置。

特性：
- 策略注册表：动态加载策略，符合开闭原则
- 配置分离：每个策略只提取需要的配置
- 统一初始化：由 Facade 管理初始化时机
- 性能优化：缓存启用的策略列表

策略分层：
- L1: 认证策略 (CookieInjectStrategy)
- L2: 伪装策略 (TLSFingerprintStrategy, UARotatorStrategy)
- L3: 限流策略 (RateLimitStrategy)
- L4: 重试策略 (SmartRetryStrategy)
- L5: 扩展策略 (ProxyPoolStrategy, CaptchaHandlerStrategy)

使用示例:
    >>> from app.adapters.anti_wind import AntiWindFacade, STANDARD_CONFIG
    >>> facade = AntiWindFacade(STANDARD_CONFIG)
    >>> result = await facade.execute_with_strategies(request_func, url)
"""

from .facade import (
    AntiWindFacade,
    BASIC_CONFIG,
    STANDARD_CONFIG,
    FULL_CONFIG,
    HEADLESS_CONFIG,
    BROWSER_CONFIG,
)
from .cookie_auto_fetcher import (
    CookieAutoFetcher,
    CookieRefreshListener,
)
from .metrics import (
    MetricsCollector,
    get_metrics_collector,
    AlertLevel,
    StrategyMetrics,
    APIMetrics,
    CookieMetrics,
    Alert,
)
from .registry import (
    register_strategy,
    get_strategy_class,
    get_all_strategy_names,
    STRATEGY_REGISTRY,
)
from .strategies.base import BaseStrategy
from .strategies.cookie_injector import CookieInjectStrategy
from .strategies.tls_fingerprint import TLSFingerprintStrategy
from .strategies.rate_limiter import RateLimitStrategy
from .strategies.ua_rotator import UARotatorStrategy
from .strategies.smart_retry import SmartRetryStrategy
from .strategies.proxy_pool import ProxyPoolStrategy
from .strategies.captcha_handler import CaptchaHandlerStrategy

__all__ = [
    # Facade
    'AntiWindFacade',
    
    # 预设配置模板
    'BASIC_CONFIG',
    'STANDARD_CONFIG',
    'FULL_CONFIG',
    'HEADLESS_CONFIG',
    'BROWSER_CONFIG',
    
    # Cookie 自动获取（v5.0 新增）
    'CookieAutoFetcher',
    'CookieRefreshListener',
    
    # 监控与统计（v5.0 新增）
    'MetricsCollector',
    'get_metrics_collector',
    'AlertLevel',
    'StrategyMetrics',
    'APIMetrics',
    'CookieMetrics',
    'Alert',
    
    # 策略类
    'BaseStrategy',
    'CookieInjectStrategy',
    'TLSFingerprintStrategy',
    'RateLimitStrategy',
    'UARotatorStrategy',
    'SmartRetryStrategy',
    'ProxyPoolStrategy',
    'CaptchaHandlerStrategy',
    
    # 注册表函数
    'register_strategy',
    'get_strategy_class',
    'get_all_strategy_names',
    'STRATEGY_REGISTRY',
]

"""
反风控策略模块

提供统一的反爬虫策略门面，支持多种策略的动态组合和配置。

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
    
    # 策略类
    'BaseStrategy',
    'CookieInjectStrategy',
    'TLSFingerprintStrategy',
    'RateLimitStrategy',
    'UARotatorStrategy',
    'SmartRetryStrategy',
    'ProxyPoolStrategy',
    'CaptchaHandlerStrategy',
]

"""
策略注册表

提供策略的动态注册和加载机制，符合开闭原则。
"""

from typing import Dict, Type, Any, Optional
from loguru import logger

from .strategies.base import BaseStrategy
from .strategies.cookie_injector import CookieInjectStrategy
from .strategies.tls_fingerprint import TLSFingerprintStrategy
from .strategies.rate_limiter import RateLimitStrategy
from .strategies.ua_rotator import UARotatorStrategy
from .strategies.smart_retry import SmartRetryStrategy
from .strategies.proxy_pool import ProxyPoolStrategy
from .strategies.captcha_handler import CaptchaHandlerStrategy


# 策略注册表：策略名称 -> 策略类
STRATEGY_REGISTRY: Dict[str, Type[BaseStrategy]] = {
    'cookie_inject': CookieInjectStrategy,
    'tls_fingerprint': TLSFingerprintStrategy,
    'rate_limit': RateLimitStrategy,
    'ua_rotation': UARotatorStrategy,
    'smart_retry': SmartRetryStrategy,
    'proxy_pool': ProxyPoolStrategy,
    'captcha_handler': CaptchaHandlerStrategy,
}

# 策略默认启用状态
STRATEGY_DEFAULTS: Dict[str, bool] = {
    'cookie_inject': True,
    'tls_fingerprint': True,
    'rate_limit': True,
    'ua_rotation': True,
    'smart_retry': True,
    'proxy_pool': False,  # 可选功能，默认禁用
    'captcha_handler': False,  # 可选功能，默认禁用
}

# 策略配置提取规则：策略名称 -> 相关配置键
STRATEGY_CONFIG_KEYS: Dict[str, list] = {
    'cookie_inject': [
        'cookie_storage_dir',
        'cookie_file_name',
        'cookie_max_age_hours',
        'refresh_before_minutes',
    ],
    'tls_fingerprint': [
        'tls_patch_mode',
        'impersonate',
        'timeout',
    ],
    'rate_limit': [
        'min_delay',
        'max_delay',
    ],
    'ua_rotation': [
        'rotation_interval',
        'user_agents',
    ],
    'smart_retry': [
        'max_retries',
    ],
    'proxy_pool': [
        'proxies',
        'min_success_rate',
        'block_duration_minutes',
    ],
    'captcha_handler': [
        'captcha_timeout',
        'captcha_check_interval',
    ],
}


def register_strategy(name: str, strategy_class: Type[BaseStrategy], default_enabled: bool = True):
    """
    注册新的策略类
    
    Args:
        name: 策略名称（用于配置键）
        strategy_class: 策略类
        default_enabled: 默认是否启用
    
    Example:
        >>> from app.adapters.anti_wind.registry import register_strategy
        >>> class MyCustomStrategy(BaseStrategy): ...
        >>> register_strategy('my_custom', MyCustomStrategy, default_enabled=False)
    """
    STRATEGY_REGISTRY[name] = strategy_class
    STRATEGY_DEFAULTS[name] = default_enabled
    logger.info(f"✅ 策略已注册：{name} -> {strategy_class.__name__}")


def get_strategy_class(name: str) -> Optional[Type[BaseStrategy]]:
    """获取策略类"""
    return STRATEGY_REGISTRY.get(name)


def is_strategy_enabled_by_default(name: str) -> bool:
    """获取策略默认启用状态"""
    return STRATEGY_DEFAULTS.get(name, True)


def extract_strategy_config(strategy_name: str, global_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    提取策略相关配置（避免传递完整 config）
    
    Args:
        strategy_name: 策略名称
        global_config: 全局配置
    
    Returns:
        策略相关配置字典
    """
    keys = STRATEGY_CONFIG_KEYS.get(strategy_name, [])
    strategy_config = {}
    
    # 始终包含 enable 键
    enable_key = f'enable_{strategy_name}'
    if enable_key in global_config:
        strategy_config['enabled'] = global_config[enable_key]
    
    # 提取相关配置键
    for key in keys:
        if key in global_config:
            strategy_config[key] = global_config[key]
    
    return strategy_config


def get_all_strategy_names() -> list:
    """获取所有注册的策略名称"""
    return list(STRATEGY_REGISTRY.keys())


def get_available_strategies() -> Dict[str, Type[BaseStrategy]]:
    """获取所有可用的策略"""
    return STRATEGY_REGISTRY.copy()

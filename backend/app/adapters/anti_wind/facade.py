"""
反爬策略统一门面

提供单一入口，封装所有反爬策略的执行逻辑。

策略分层：
- L1: 认证策略 (CookieInjectStrategy)
- L2: 伪装策略 (TLSFingerprintStrategy, UARotatorStrategy)
- L3: 限流策略 (RateLimitStrategy)
- L4: 重试策略 (SmartRetryStrategy)
- L5: 扩展策略 (ProxyPoolStrategy, CaptchaHandlerStrategy)
"""

import asyncio
import random
from typing import Any, Dict, List, Optional, Callable
from loguru import logger

from .strategies.base import BaseStrategy
from .strategies.cookie_injector import CookieInjectStrategy
from .strategies.tls_fingerprint import TLSFingerprintStrategy
from .strategies.rate_limiter import RateLimitStrategy
from .strategies.ua_rotator import UARotatorStrategy
from .strategies.smart_retry import SmartRetryStrategy
from .strategies.proxy_pool import ProxyPoolStrategy
from .strategies.captcha_handler import CaptchaHandlerStrategy


# ========== 预设配置模板 ==========

BASIC_CONFIG = {
    """基础配置（快速开始）"""
    'enable_cookie_inject': True,
    'enable_rate_limit': True,
    'enable_smart_retry': True,
    'max_retries': 3,
}

STANDARD_CONFIG = {
    """标准配置（推荐）"""
    'enable_cookie_inject': True,
    'enable_tls_fingerprint': True,
    'impersonate': 'chrome120',
    'enable_ua_rotation': True,
    'rotation_interval': 10,
    'enable_rate_limit': True,
    'min_delay': 1.0,
    'max_delay': 3.0,
    'enable_smart_retry': True,
    'max_retries': 3,
}

FULL_CONFIG = {
    """完整配置（高危 API）"""
    'enable_cookie_inject': True,
    'enable_tls_fingerprint': True,
    'impersonate': 'chrome120',
    'enable_ua_rotation': True,
    'rotation_interval': 5,
    'enable_rate_limit': True,
    'min_delay': 2.0,
    'max_delay': 5.0,
    'enable_smart_retry': True,
    'max_retries': 3,
    'enable_proxy_pool': False,
    'enable_captcha_handler': False,
}

HEADLESS_CONFIG = {
    """无浏览器模式（纯 HTTP）"""
    'enable_cookie_inject': True,
    'enable_tls_fingerprint': True,
    'impersonate': 'chrome120',
    'enable_rate_limit': True,
    'enable_smart_retry': True,
    'max_retries': 3,
}

BROWSER_CONFIG = {
    """浏览器模式（Playwright）"""
    'enable_cookie_inject': True,
    'enable_rate_limit': True,
    'enable_smart_retry': True,
    'max_retries': 3,
    'enable_captcha_handler': True,
    'captcha_timeout': 120,
}


class AntiWindFacade:
    """反爬策略统一门面"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化反爬策略门面
        
        Args:
            config: 配置字典，可使用预设模板（BASIC_CONFIG, STANDARD_CONFIG, etc.）
        
        Example:
            >>> facade = AntiWindFacade(STANDARD_CONFIG)
            >>> facade = AntiWindFacade({'enable_cookie_inject': True, 'max_retries': 5})
        """
        self.config = config or {}
        self.strategies: List[BaseStrategy] = []
        self._retry_strategy: Optional[SmartRetryStrategy] = None
        
        self._initialize_strategies()
        logger.info("✅ 反爬策略门面初始化完成")
    
    def _initialize_strategies(self):
        """初始化所有策略"""
        logger.info("🔧 开始初始化反爬策略...")
        
        # 1. Cookie 注入（优先级最高）
        if self.config.get('enable_cookie_inject', True):
            cookie_strategy = CookieInjectStrategy(self.config)
            self.strategies.append(cookie_strategy)
            logger.info("✅ Cookie 注入策略已启用")
        
        # 2. TLS 指纹伪装
        if self.config.get('enable_tls_fingerprint', True):
            tls_strategy = TLSFingerprintStrategy(self.config)
            self.strategies.append(tls_strategy)
            logger.info("✅ TLS 指纹策略已启用")
        
        # 3. 频率控制
        if self.config.get('enable_rate_limit', True):
            rate_strategy = RateLimitStrategy(self.config)
            self.strategies.append(rate_strategy)
            logger.info("✅ 频率控制策略已启用")
        
        # 4. UA 轮换
        if self.config.get('enable_ua_rotation', True):
            ua_strategy = UARotatorStrategy(self.config)
            self.strategies.append(ua_strategy)
            logger.info(f"✅ UA 轮换策略已启用（{ua_strategy.get_ua_pool_size()} 个 UA）")
        
        # 5. 智能重试（特殊处理）
        if self.config.get('enable_smart_retry', True):
            self._retry_strategy = SmartRetryStrategy(self.config)
            # 不添加到 strategies 列表，它作为执行器单独使用
            logger.info(f"✅ 智能重试策略已启用（最大{self.config.get('max_retries', 3)}次）")
        
        # 6. 代理池（可选）
        if self.config.get('enable_proxy_pool', False):
            proxy_strategy = ProxyPoolStrategy(self.config)
            self.strategies.append(proxy_strategy)
            logger.info(f"✅ 代理池策略已启用")
        
        # 7. 验证码处理（可选）
        if self.config.get('enable_captcha_handler', False):
            captcha_strategy = CaptchaHandlerStrategy(self.config)
            self.strategies.append(captcha_strategy)
            logger.info(f"✅ 验证码处理策略已启用")
        
        logger.info(f"🎯 反爬策略初始化完成，共 {len(self.strategies)} 个策略")
    
    async def execute_with_strategies(
        self,
        request_func: Callable,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Any:
        """
        使用策略执行请求
        
        Args:
            request_func: 请求函数（异步或同步）
            url: 请求 URL
            method: 请求方法
            headers: 请求头
            kwargs: 其他参数
            
        Returns:
            请求结果
            
        Raises:
            Exception: 所有重试失败后抛出异常
        """
        current_headers = headers or {}
        
        # 包装请求函数
        async def wrapped_request():
            nonlocal current_headers
            
            # 1. 执行所有 before_request
            for strategy in self.strategies:
                if strategy.is_enabled():
                    current_headers = await strategy.before_request(url, method, current_headers)
            
            # 2. 执行实际请求
            if asyncio.iscoroutinefunction(request_func):
                response = await request_func(url=url, method=method, headers=current_headers, **kwargs)
            else:
                response = request_func(url=url, method=method, headers=current_headers, **kwargs)
            
            # 3. 执行所有 after_request
            for strategy in reversed(self.strategies):
                if strategy.is_enabled():
                    response = await strategy.after_request(response)
            
            return response
        
        # 4. 使用智能重试执行
        if self._retry_strategy and self._retry_strategy.is_enabled():
            return await self._retry_strategy.execute_with_retry(
                func=wrapped_request,
                context=f"{method} {url}",
                on_switch_mode=lambda: logger.info("🔄 切换到降级模式")
            )
        else:
            # 无重试，直接执行
            return await wrapped_request()
    
    # ========== 便捷方法 ==========
    
    def enable_strategy(self, strategy_name: str):
        """
        启用策略
        
        Args:
            strategy_name: 策略名称（类名）
        """
        for strategy in self.strategies:
            if strategy.__class__.__name__ == strategy_name:
                strategy.enable()
                logger.info(f"✅ 策略 {strategy_name} 已启用")
                return
        
        logger.warning(f"⚠️  策略 {strategy_name} 不存在")
    
    def disable_strategy(self, strategy_name: str):
        """
        禁用策略
        
        Args:
            strategy_name: 策略名称（类名）
        """
        for strategy in self.strategies:
            if strategy.__class__.__name__ == strategy_name:
                strategy.disable()
                logger.info(f"⚠️  策略 {strategy_name} 已禁用")
                return
        
        logger.warning(f"⚠️  策略 {strategy_name} 不存在")
    
    def get_strategy(self, strategy_name: str) -> Optional[BaseStrategy]:
        """
        获取策略实例
        
        Args:
            strategy_name: 策略名称
            
        Returns:
            策略实例或 None
        """
        for strategy in self.strategies:
            if strategy.__class__.__name__ == strategy_name:
                return strategy
        return None
    
    def get_enabled_strategies(self) -> List[str]:
        """获取所有启用的策略名称"""
        return [s.__class__.__name__ for s in self.strategies if s.is_enabled()]
    
    def get_strategy_status(self) -> Dict[str, bool]:
        """获取所有策略的状态"""
        return {s.__class__.__name__: s.is_enabled() for s in self.strategies}
    
    def print_status(self):
        """打印策略状态"""
        logger.info("📊 反爬策略状态:")
        for strategy in self.strategies:
            status = "✅ 启用" if strategy.is_enabled() else "⚠️  禁用"
            logger.info(f"  - {strategy.__class__.__name__}: {status}")
        
        if self._retry_strategy:
            status = "✅ 启用" if self._retry_strategy.is_enabled() else "⚠️  禁用"
            logger.info(f"  - SmartRetryStrategy: {status} (max_retries={self.config.get('max_retries', 3)})")
    
    def update_config(self, config: Dict[str, Any]):
        """
        更新配置
        
        Args:
            config: 新配置字典
        """
        self.config.update(config)
        
        # 更新策略配置
        for strategy in self.strategies:
            strategy.update_config(config)
        
        if self._retry_strategy:
            self._retry_strategy.update_config(config)
        
        logger.info("✅ 配置已更新")
    
    def reset(self):
        """重置所有策略状态"""
        for strategy in self.strategies:
            if hasattr(strategy, 'reset'):
                strategy.reset()
        
        if self._retry_strategy:
            self._retry_strategy.reset()
        
        logger.info("✅ 所有策略已重置")
    
    def get_layer_strategies(self, layer: int) -> List[BaseStrategy]:
        """
        获取指定层级的策略
        
        Args:
            layer: 层级编号 (1-5)
            
        Returns:
            该层级的策略列表
        """
        layer_map = {
            1: ['CookieInjectStrategy'],
            2: ['TLSFingerprintStrategy', 'UARotatorStrategy'],
            3: ['RateLimitStrategy'],
            4: ['SmartRetryStrategy'],
            5: ['ProxyPoolStrategy', 'CaptchaHandlerStrategy'],
        }
        
        strategy_names = layer_map.get(layer, [])
        result = []
        
        for strategy in self.strategies:
            if strategy.__class__.__name__ in strategy_names:
                result.append(strategy)
        
        if layer == 4 and self._retry_strategy:
            result.append(self._retry_strategy)
        
        return result
    
    def get_strategy_by_layer(self) -> Dict[int, List[str]]:
        """
        按层级获取策略
        
        Returns:
            字典 {layer: [strategy_names]}
        """
        return {
            1: [s.__class__.__name__ for s in self.get_layer_strategies(1)],
            2: [s.__class__.__name__ for s in self.get_layer_strategies(2)],
            3: [s.__class__.__name__ for s in self.get_layer_strategies(3)],
            4: [s.__class__.__name__ for s in self.get_layer_strategies(4)],
            5: [s.__class__.__name__ for s in self.get_layer_strategies(5)],
        }

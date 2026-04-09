"""
反爬策略统一门面（优化版）

使用策略注册表动态加载策略，符合开闭原则。

策略分层：
- L1: 认证策略 (CookieInjectStrategy)
- L2: 伪装策略 (TLSFingerprintStrategy, UARotatorStrategy)
- L3: 限流策略 (RateLimitStrategy)
- L4: 重试策略 (SmartRetryStrategy)
- L5: 扩展策略 (ProxyPoolStrategy, CaptchaHandlerStrategy)
"""

import asyncio
from typing import Any, Dict, List, Optional, Callable
from loguru import logger

from .strategies.base import BaseStrategy
from .strategies.smart_retry import SmartRetryStrategy
from .cookie_auto_fetcher import CookieAutoFetcher, CookieRefreshListener
from .metrics import MetricsCollector, get_metrics_collector, AlertLevel
from .registry import (
    STRATEGY_REGISTRY,
    STRATEGY_DEFAULTS,
    extract_strategy_config,
    get_all_strategy_names,
)


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
    """反爬策略统一门面（优化版 v5.0）
    
    新增功能:
    - Cookie 自动获取（支持 Edge/Chrome）
    - Cookie 自动续期监听
    - 成功率监控与统计
    """
    
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
        self._initialized = False
        
        # 缓存启用的策略列表（优化 5）
        self._enabled_strategies: List[BaseStrategy] = []
        
        # Cookie 自动获取器（v5.0 新增）
        self._cookie_fetcher: Optional[CookieAutoFetcher] = None
        self._cookie_listener: Optional[CookieRefreshListener] = None
        
        # 指标收集器（v5.0 新增）
        self._metrics_collector: MetricsCollector = get_metrics_collector()
        
        self._initialize_strategies()
        logger.info("✅ 反爬策略门面初始化完成")
    
    def _initialize_strategies(self):
        """初始化所有策略（使用注册表）"""
        logger.info("🔧 开始初始化反爬策略...")
        
        # 动态加载所有注册的策略
        for strategy_name, strategy_class in STRATEGY_REGISTRY.items():
            # 检查是否启用（配置或默认值）
            enable_key = f'enable_{strategy_name}'
            is_enabled = self.config.get(enable_key, STRATEGY_DEFAULTS.get(strategy_name, True))
            
            if not is_enabled:
                logger.debug(f"⚠️  策略 {strategy_name} 已禁用")
                continue
            
            # 提取策略相关配置（优化 3：配置分离）
            strategy_config = extract_strategy_config(strategy_name, self.config)
            
            # 创建策略实例
            strategy = strategy_class(strategy_config)
            self.strategies.append(strategy)
            
            logger.info(f"✅ {strategy_name} 策略已启用")
        
        # 特殊处理：智能重试策略（作为执行器）
        if self.config.get('enable_smart_retry', True):
            retry_config = extract_strategy_config('smart_retry', self.config)
            self._retry_strategy = SmartRetryStrategy(retry_config)
            logger.info(f"✅ 智能重试策略已启用（最大{self.config.get('max_retries', 3)}次）")
        
        # 更新启用的策略缓存（优化 5）
        self._update_enabled_strategies()
        
        logger.info(f"🎯 反爬策略初始化完成，共 {len(self.strategies)} 个策略")
        self._initialized = True
    
    def _update_enabled_strategies(self):
        """更新启用的策略缓存（优化 5）"""
        self._enabled_strategies = [
            s for s in self.strategies if s.is_enabled()
        ]
    
    async def initialize(self):
        """统一初始化所有策略（优化 2）"""
        if self._initialized:
            return
        
        for strategy in self.strategies:
            if hasattr(strategy, 'initialize'):
                await strategy.initialize()
        
        self._initialized = True
        logger.info("✅ 所有策略初始化完成")
    
    async def execute_with_strategies(
        self,
        request_func: Callable,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Any:
        """
        使用策略执行请求（带监控）
        
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
        import time
        
        # 确保已初始化（优化 2）
        if not self._initialized:
            await self.initialize()
        
        current_headers = headers or {}
        start_time = time.time()
        success = False
        
        # 包装请求函数
        async def wrapped_request():
            nonlocal current_headers, success
            
            # 1. 执行所有 before_request（使用缓存的启用策略列表）
            for strategy in self._enabled_strategies:
                strategy_start = time.time()
                try:
                    current_headers = await strategy.before_request(url, method, current_headers)
                    execution_time = (time.time() - strategy_start) * 1000
                    self._metrics_collector.record_strategy_request(
                        strategy_name=strategy.__class__.__name__,
                        success=True,
                        execution_time_ms=execution_time
                    )
                except Exception as e:
                    execution_time = (time.time() - strategy_start) * 1000
                    self._metrics_collector.record_strategy_request(
                        strategy_name=strategy.__class__.__name__,
                        success=False,
                        execution_time_ms=execution_time,
                        error=str(e)
                    )
                    raise
            
            # 2. 执行实际请求
            request_start = time.time()
            try:
                if asyncio.iscoroutinefunction(request_func):
                    response = await request_func(url=url, method=method, headers=current_headers, **kwargs)
                else:
                    response = request_func(url=url, method=method, headers=current_headers, **kwargs)
                
                request_time = (time.time() - request_start) * 1000
                
                # 记录 API 指标
                api_key = self._extract_api_key(url)
                self._metrics_collector.record_api_request(
                    api_key=api_key,
                    success=True,
                    response_time_ms=request_time
                )
                
                success = True
                
            except Exception as e:
                request_time = (time.time() - request_start) * 1000
                
                # 记录 API 指标
                api_key = self._extract_api_key(url)
                self._metrics_collector.record_api_request(
                    api_key=api_key,
                    success=False,
                    response_time_ms=request_time
                )
                
                raise
            
            # 3. 执行所有 after_request
            for strategy in reversed(self._enabled_strategies):
                strategy_start = time.time()
                try:
                    response = await strategy.after_request(response)
                    execution_time = (time.time() - strategy_start) * 1000
                    self._metrics_collector.record_strategy_request(
                        strategy_name=strategy.__class__.__name__,
                        success=True,
                        execution_time_ms=execution_time
                    )
                except Exception as e:
                    execution_time = (time.time() - strategy_start) * 1000
                    self._metrics_collector.record_strategy_request(
                        strategy_name=strategy.__class__.__name__,
                        success=False,
                        execution_time_ms=execution_time,
                        error=str(e)
                    )
                    raise
            
            return response
        
        try:
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
        finally:
            # 记录总执行时间
            total_time = (time.time() - start_time) * 1000
            if not success:
                # 记录失败
                self._metrics_collector.record_strategy_request(
                    strategy_name="AntiWindFacade",
                    success=False,
                    execution_time_ms=total_time
                )
    
    # ========== 核心接口（精简版） ==========
    
    def enable_strategy(self, strategy_name: str):
        """启用策略"""
        for strategy in self.strategies:
            if strategy.__class__.__name__ == strategy_name:
                strategy.enable()
                self._update_enabled_strategies()
                logger.info(f"✅ 策略 {strategy_name} 已启用")
                return
        
        logger.warning(f"⚠️  策略 {strategy_name} 不存在")
    
    def disable_strategy(self, strategy_name: str):
        """禁用策略"""
        for strategy in self.strategies:
            if strategy.__class__.__name__ == strategy_name:
                strategy.disable()
                self._update_enabled_strategies()
                logger.info(f"⚠️  策略 {strategy_name} 已禁用")
                return
        
        logger.warning(f"⚠️  策略 {strategy_name} 不存在")
    
    def get_strategy(self, strategy_name: str) -> Optional[BaseStrategy]:
        """获取策略实例"""
        for strategy in self.strategies:
            if strategy.__class__.__name__ == strategy_name:
                return strategy
        return None
    
    # ========== Cookie 自动获取（v5.0 新增） ==========
    
    async def auto_fetch_cookie(self, domain: str = None, browser: str = "edge") -> bool:
        """
        自动获取 Cookie
        
        Args:
            domain: 域名（默认从配置读取）
            browser: 浏览器类型（edge/chrome）
        
        Returns:
            是否成功获取
        """
        domain = domain or self.config.get('domain', 'eastmoney.com')
        browser_path = self.config.get('browser_path')
        
        logger.info(f"🍪 开始自动获取 Cookie（{domain}）")
        
        self._cookie_fetcher = CookieAutoFetcher(
            domain=domain,
            browser=browser,
            browser_path=browser_path,
            storage_dir=self.config.get('cookie_storage_dir', 'data/cookies'),
            expires_in_days=self.config.get('cookie_expires_in_days', 7),
        )
        
        success = await self._cookie_fetcher.fetch()
        
        if success:
            logger.info("✅ Cookie 获取成功，CookieInjectStrategy 将自动使用")
        else:
            logger.warning("⚠️  Cookie 获取失败，请检查浏览器配置或使用手动获取")
        
        return success
    
    def start_cookie_auto_refresh(self, domain: str = None):
        """
        启动 Cookie 自动续期监听器
        
        Args:
            domain: 域名（默认从配置读取）
        """
        domain = domain or self.config.get('domain', 'eastmoney.com')
        
        logger.info(f"🕐 启动 Cookie 自动续期监听器（{domain}）")
        
        self._cookie_listener = CookieRefreshListener(domain=domain)
        
        logger.info("✅ Cookie 自动续期监听器已启动")
        logger.info("💡 提示：调用 check_and_refresh_cookie() 定期检查并续期")
    
    async def check_and_refresh_cookie(self) -> bool:
        """
        检查并续期 Cookie
        
        Returns:
            是否成功续期
        """
        if not self._cookie_listener:
            logger.warning("⚠️  Cookie 监听器未启动，请先调用 start_cookie_auto_refresh()")
            return False
        
        return await self._cookie_listener.check_and_refresh()
    
    def get_cookie_status(self) -> Optional[Dict[str, Any]]:
        """获取 Cookie 状态"""
        if not self._cookie_listener:
            return None
        
        return self._cookie_listener.get_status()
    
    def print_cookie_status(self):
        """打印 Cookie 状态"""
        if not self._cookie_listener:
            logger.warning("⚠️  Cookie 监听器未启动")
            return
        
        self._cookie_listener.print_status()
    
    # ========== 监控与统计（v5.0 新增） ==========
    
    def get_metrics_report(self) -> Dict[str, Any]:
        """获取监控报告"""
        return self._metrics_collector.generate_report()
    
    def print_metrics_report(self):
        """打印监控报告"""
        self._metrics_collector.print_report()
    
    def get_strategy_stats(self, strategy_name: str) -> Optional[Dict[str, Any]]:
        """获取策略统计"""
        metrics = self._metrics_collector.get_strategy_metrics(strategy_name)
        if metrics:
            return metrics.to_dict()
        return None
    
    def get_api_stats(self, api_key: str) -> Optional[Dict[str, Any]]:
        """获取 API 统计"""
        metrics = self._metrics_collector.get_api_metrics(api_key)
        if metrics:
            return metrics.to_dict()
        return None
    
    def get_cookie_stats(self, domain: str) -> Optional[Dict[str, Any]]:
        """获取 Cookie 统计"""
        metrics = self._metrics_collector.get_cookie_metrics(domain)
        if metrics:
            return metrics.to_dict()
        return None
    
    def get_alerts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取告警列表"""
        alerts = self._metrics_collector.get_alerts(limit=limit)
        return [a.to_dict() for a in alerts]
    
    def register_alert_callback(self, callback):
        """注册告警回调"""
        self._metrics_collector.register_alert_callback(callback)
    
    def clear_alerts(self):
        """清空告警"""
        self._metrics_collector.clear_alerts()
    
    # ========== 辅助方法 ==========
    
    def _extract_api_key(self, url: str) -> str:
        """提取 API 标识（用于统计）"""
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        return f"{parsed.netloc}{parsed.path.split('/')[1] if parsed.path else ''}"
    
    def print_status(self):
        """打印策略状态"""
        logger.info("📊 反爬策略状态:")
        for strategy in self.strategies:
            status = "✅ 启用" if strategy.is_enabled() else "⚠️  禁用"
            logger.info(f"  - {strategy.__class__.__name__}: {status}")
        
        if self._retry_strategy:
            status = "✅ 启用" if self._retry_strategy.is_enabled() else "⚠️  禁用"
            logger.info(f"  - SmartRetryStrategy: {status} (max_retries={self.config.get('max_retries', 3)})")
        
        # 打印 Cookie 状态（v5.0 新增）
        if self._cookie_listener:
            self.print_cookie_status()
    
    # ========== 辅助方法 ==========
    
    def get_enabled_strategies(self) -> List[str]:
        """获取所有启用的策略名称"""
        return [s.__class__.__name__ for s in self._enabled_strategies]
    
    def get_strategy_status(self) -> Dict[str, bool]:
        """获取所有策略的状态"""
        return {s.__class__.__name__: s.is_enabled() for s in self.strategies}
    
    def update_config(self, config: Dict[str, Any]):
        """更新配置"""
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
    
    # ========== 已移除的方法（优化 4） ==========
    # - get_layer_strategies() - 内部方法，外部不需要
    # - get_strategy_by_layer() - 内部方法，外部不需要

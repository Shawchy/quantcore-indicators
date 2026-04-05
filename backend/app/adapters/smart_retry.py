"""
智能重试策略模块

根据错误类型决定是否重试：
1. 网络错误 → 可重试
2. TLS 指纹被识别 → 不重试（需要切换方案）
3. 限流 (429) → 等待后重试
4. 封禁 (403) → 不重试（需要切换代理）
5. 服务器错误 (5xx) → 可重试
6. 客户端错误 (4xx) → 不重试
"""

from typing import Optional, Callable, Any, Dict, List
from loguru import logger
from dataclasses import dataclass
from enum import Enum
import asyncio
import random
import time


class ErrorType(Enum):
    NETWORK_ERROR = "network_error"
    TLS_FINGERPRINT = "tls_fingerprint"
    RATE_LIMITED = "rate_limited"
    IP_BLOCKED = "ip_blocked"
    SERVER_ERROR = "server_error"
    CLIENT_ERROR = "client_error"
    TIMEOUT = "timeout"
    CONNECTION_CLOSED = "connection_closed"
    UNKNOWN = "unknown"


@dataclass
class RetryDecision:
    should_retry: bool
    wait_seconds: float
    reason: str
    error_type: ErrorType
    should_switch_mode: bool = False


class ErrorClassifier:
    """错误分类器"""
    
    TLS_INDICATORS = [
        'Connection closed abruptly',
        'Empty reply from server',
        'RemoteDisconnected',
        'Connection aborted',
        'Remote end closed connection',
    ]
    
    RATE_LIMIT_INDICATORS = [
        '429',
        'rate limit',
        'too many requests',
        '请求过于频繁',
    ]
    
    BLOCK_INDICATORS = [
        '403',
        'forbidden',
        'blocked',
        '访问被拒绝',
        'IP',
    ]
    
    @classmethod
    def classify(cls, error: Exception, status_code: Optional[int] = None) -> ErrorType:
        error_str = str(error).lower()
        error_type = type(error).__name__
        
        if status_code:
            if status_code == 429:
                return ErrorType.RATE_LIMITED
            if status_code == 403:
                return ErrorType.IP_BLOCKED
            if 500 <= status_code < 600:
                return ErrorType.SERVER_ERROR
            if 400 <= status_code < 500:
                return ErrorType.CLIENT_ERROR
        
        for indicator in cls.TLS_INDICATORS:
            if indicator.lower() in error_str:
                return ErrorType.CONNECTION_CLOSED
        
        for indicator in cls.RATE_LIMIT_INDICATORS:
            if indicator.lower() in error_str:
                return ErrorType.RATE_LIMITED
        
        for indicator in cls.BLOCK_INDICATORS:
            if indicator.lower() in error_str:
                return ErrorType.IP_BLOCKED
        
        if 'timeout' in error_str or 'Timeout' in error_type:
            return ErrorType.TIMEOUT
        
        if 'connection' in error_str or 'network' in error_str:
            return ErrorType.NETWORK_ERROR
        
        return ErrorType.UNKNOWN


class SmartRetryStrategy:
    """智能重试策略
    
    根据错误类型决定：
    1. 是否重试
    2. 等待时间
    3. 是否需要切换模式（如切换到 Playwright）
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        
        # 默认配置
        default_max_retries = {
            ErrorType.NETWORK_ERROR: 2,
            ErrorType.TIMEOUT: 2,
            ErrorType.SERVER_ERROR: 2,
            ErrorType.RATE_LIMITED: 1,
            ErrorType.CONNECTION_CLOSED: 0,
            ErrorType.TLS_FINGERPRINT: 0,
            ErrorType.IP_BLOCKED: 0,
            ErrorType.CLIENT_ERROR: 0,
        }
        
        default_base_wait = {
            ErrorType.NETWORK_ERROR: 2.0,
            ErrorType.TIMEOUT: 3.0,
            ErrorType.SERVER_ERROR: 5.0,
            ErrorType.RATE_LIMITED: 30.0,
            ErrorType.CONNECTION_CLOSED: 0,
            ErrorType.TLS_FINGERPRINT: 0,
            ErrorType.IP_BLOCKED: 0,
            ErrorType.CLIENT_ERROR: 0,
        }
        
        # 处理简化的配置格式：如果传入数字，应用到所有可重试的错误类型
        max_retries_config = config.get('max_retries', {})
        if isinstance(max_retries_config, int):
            # 将数字应用到所有可重试的错误类型
            max_retries_config = {
                ErrorType.NETWORK_ERROR: max_retries_config,
                ErrorType.TIMEOUT: max_retries_config,
                ErrorType.SERVER_ERROR: max_retries_config,
                ErrorType.RATE_LIMITED: max_retries_config,
                ErrorType.UNKNOWN: max_retries_config,  # 未知错误也重试
                ErrorType.CONNECTION_CLOSED: 0,
                ErrorType.TLS_FINGERPRINT: 0,
                ErrorType.IP_BLOCKED: 0,
                ErrorType.CLIENT_ERROR: 0,
            }
        else:
            # 合并配置，确保所有错误类型都有默认值
            max_retries_config = {**default_max_retries, **max_retries_config}
            # 确保 UNKNOWN 类型有默认值
            if ErrorType.UNKNOWN not in max_retries_config:
                max_retries_config[ErrorType.UNKNOWN] = 2
        
        base_wait_config = config.get('base_wait_seconds', {})
        if isinstance(base_wait_config, (int, float)):
            base_wait_config = {
                ErrorType.NETWORK_ERROR: base_wait_config,
                ErrorType.TIMEOUT: base_wait_config,
                ErrorType.SERVER_ERROR: base_wait_config,
                ErrorType.RATE_LIMITED: max(base_wait_config, 30.0),
                ErrorType.UNKNOWN: base_wait_config,
                ErrorType.CONNECTION_CLOSED: 0,
                ErrorType.TLS_FINGERPRINT: 0,
                ErrorType.IP_BLOCKED: 0,
                ErrorType.CLIENT_ERROR: 0,
            }
        else:
            # 合并配置，确保所有错误类型都有默认值
            base_wait_config = {**default_base_wait, **base_wait_config}
            # 确保 UNKNOWN 类型有默认值
            if ErrorType.UNKNOWN not in base_wait_config:
                base_wait_config[ErrorType.UNKNOWN] = 2.0
        
        self._config = {
            'max_retries': max_retries_config,
            'base_wait_seconds': base_wait_config,
            'jitter_range': config.get('jitter_range', (0.8, 1.2)),
            'exponential_backoff': config.get('exponential_backoff', True),
            'max_wait_seconds': config.get('max_wait_seconds', 60.0),
        }
        
        self._retry_counts: Dict[str, int] = {}
        self._last_errors: Dict[str, List[ErrorType]] = {}
    
    def should_retry(
        self,
        error: Exception,
        attempt: int,
        context: Optional[str] = None,
        status_code: Optional[int] = None
    ) -> RetryDecision:
        error_type = ErrorClassifier.classify(error, status_code)
        max_retries = self._config['max_retries'].get(error_type, 0)
        
        context = context or 'default'
        
        if error_type in [ErrorType.TLS_FINGERPRINT, ErrorType.CONNECTION_CLOSED]:
            return RetryDecision(
                should_retry=False,
                wait_seconds=0,
                reason=f"TLS 指纹/连接被识别，重试无效，建议切换到 Playwright 模式",
                error_type=error_type,
                should_switch_mode=True
            )
        
        if error_type == ErrorType.IP_BLOCKED:
            return RetryDecision(
                should_retry=False,
                wait_seconds=0,
                reason=f"IP 被封禁，需要切换代理或等待",
                error_type=error_type,
                should_switch_mode=True
            )
        
        if error_type == ErrorType.CLIENT_ERROR:
            return RetryDecision(
                should_retry=False,
                wait_seconds=0,
                reason=f"客户端错误，请检查请求参数",
                error_type=error_type
            )
        
        if attempt >= max_retries:
            return RetryDecision(
                should_retry=False,
                wait_seconds=0,
                reason=f"已达到最大重试次数 ({max_retries})",
                error_type=error_type
            )
        
        base_wait = self._config['base_wait_seconds'].get(error_type, 2.0)
        
        if self._config['exponential_backoff']:
            wait_seconds = base_wait * (2 ** attempt)
        else:
            wait_seconds = base_wait
        
        jitter_min, jitter_max = self._config['jitter_range']
        jitter = random.uniform(jitter_min, jitter_max)
        wait_seconds = min(wait_seconds * jitter, self._config['max_wait_seconds'])
        
        if error_type == ErrorType.RATE_LIMITED:
            wait_seconds = max(wait_seconds, 30.0)
        
        self._retry_counts[context] = self._retry_counts.get(context, 0) + 1
        
        if context not in self._last_errors:
            self._last_errors[context] = []
        self._last_errors[context].append(error_type)
        
        return RetryDecision(
            should_retry=True,
            wait_seconds=wait_seconds,
            reason=f"{error_type.value} 错误，第 {attempt + 1}/{max_retries} 次重试",
            error_type=error_type
        )
    
    def get_retry_stats(self, context: Optional[str] = None) -> Dict[str, Any]:
        if context:
            return {
                'retry_count': self._retry_counts.get(context, 0),
                'last_errors': [e.value for e in self._last_errors.get(context, [])],
            }
        
        return {
            'all_contexts': {
                ctx: {
                    'retry_count': count,
                    'last_errors': [e.value for e in self._last_errors.get(ctx, [])],
                }
                for ctx, count in self._retry_counts.items()
            }
        }
    
    def reset_stats(self, context: Optional[str] = None):
        if context:
            self._retry_counts.pop(context, None)
            self._last_errors.pop(context, None)
        else:
            self._retry_counts.clear()
            self._last_errors.clear()


class SmartRetryExecutor:
    """智能重试执行器
    
    使用方法：
        executor = SmartRetryExecutor()
        
        result = await executor.execute(
            func=lambda: fetch_data(url),
            context="fetch_stock_list"
        )
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._strategy = SmartRetryStrategy(config)
        self._on_switch_mode_callback: Optional[Callable] = None
    
    def set_switch_mode_callback(self, callback: Callable):
        self._on_switch_mode_callback = callback
    
    async def execute(
        self,
        func: Callable,
        context: Optional[str] = None,
        on_retry: Optional[Callable[[RetryDecision], None]] = None,
        on_switch_mode: Optional[Callable[[], Any]] = None,
    ) -> Any:
        attempt = 0
        
        while True:
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func()
                else:
                    result = func()
                
                self._strategy.reset_stats(context)
                return result
                
            except Exception as e:
                decision = self._strategy.should_retry(e, attempt, context)
                
                logger.warning(
                    f"请求失败 [{context or 'default'}]: {type(e).__name__}: {e}\n"
                    f"  错误类型: {decision.error_type.value}\n"
                    f"  决策: {'重试' if decision.should_retry else '不重试'}\n"
                    f"  原因: {decision.reason}"
                )
                
                if on_retry:
                    on_retry(decision)
                
                if decision.should_switch_mode:
                    if on_switch_mode:
                        logger.info(f"切换模式...")
                        return await on_switch_mode()
                    elif self._on_switch_mode_callback:
                        logger.info(f"切换模式...")
                        return await self._on_switch_mode_callback()
                
                if not decision.should_retry:
                    raise e
                
                if decision.wait_seconds > 0:
                    logger.info(f"等待 {decision.wait_seconds:.1f} 秒后重试...")
                    await asyncio.sleep(decision.wait_seconds)
                
                attempt += 1


class RequestFrequencyController:
    """请求频率控制器
    
    智能控制请求频率：
    1. 基础延迟
    2. 自适应调整（根据成功率）
    3. 时间段调整（交易时间更保守）
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._config = {
            'base_delay': 2.0,
            'min_delay': 1.0,
            'max_delay': 30.0,
            'success_decrease_factor': 0.95,
            'failure_increase_factor': 1.5,
            'burst_threshold': 5,
            'burst_cooldown': 60.0,
            'trading_hours': [(9, 11.5), (13, 15)],
            'trading_hours_multiplier': 2.0,
            **(config or {})
        }
        
        self._current_delay = self._config['base_delay']
        self._request_times: List[float] = []
        self._consecutive_failures = 0
        self._consecutive_successes = 0
    
    def _is_trading_hours(self) -> bool:
        import datetime
        now = datetime.datetime.now()
        current_hour = now.hour + now.minute / 60
        
        for start, end in self._config['trading_hours']:
            if start <= current_hour < end:
                return True
        return False
    
    def _check_burst(self) -> bool:
        now = time.time()
        self._request_times = [t for t in self._request_times if now - t < 60]
        
        if len(self._request_times) >= self._config['burst_threshold']:
            return True
        return False
    
    def get_delay(self) -> float:
        delay = self._current_delay
        
        if self._is_trading_hours():
            delay *= self._config['trading_hours_multiplier']
        
        if self._check_burst():
            delay *= 1.5
        
        jitter = random.uniform(0.8, 1.2)
        delay = delay * jitter
        
        delay = max(self._config['min_delay'], min(delay, self._config['max_delay']))
        
        return delay
    
    async def wait(self) -> float:
        delay = self.get_delay()
        await asyncio.sleep(delay)
        
        self._request_times.append(time.time())
        
        return delay
    
    def report_success(self):
        self._consecutive_successes += 1
        self._consecutive_failures = 0
        
        if self._consecutive_successes >= 3:
            self._current_delay *= self._config['success_decrease_factor']
            self._current_delay = max(self._current_delay, self._config['min_delay'])
            self._consecutive_successes = 0
    
    def report_failure(self, is_rate_limited: bool = False):
        self._consecutive_failures += 1
        self._consecutive_successes = 0
        
        increase = self._config['failure_increase_factor']
        if is_rate_limited:
            increase *= 2
        
        self._current_delay *= increase
        self._current_delay = min(self._current_delay, self._config['max_delay'])
    
    def get_status(self) -> Dict[str, Any]:
        return {
            'current_delay': round(self._current_delay, 2),
            'consecutive_failures': self._consecutive_failures,
            'consecutive_successes': self._consecutive_successes,
            'is_trading_hours': self._is_trading_hours(),
            'requests_in_last_minute': len(self._request_times),
        }


async def test_smart_retry():
    """测试智能重试策略"""
    print("\n=== 测试智能重试策略 ===\n")
    
    strategy = SmartRetryStrategy()
    
    test_cases = [
        ("Connection closed abruptly", None, "TLS 指纹被识别"),
        ("RemoteDisconnected: Remote end closed connection", None, "连接被关闭"),
        ("429 Too Many Requests", 429, "限流"),
        ("403 Forbidden", 403, "IP 封禁"),
        ("500 Internal Server Error", 500, "服务器错误"),
        ("Timeout waiting for response", None, "超时"),
        ("Network is unreachable", None, "网络错误"),
    ]
    
    for error_msg, status_code, description in test_cases:
        error = Exception(error_msg)
        decision = strategy.should_retry(error, attempt=0, status_code=status_code)
        
        print(f"{description}:")
        print(f"  错误类型: {decision.error_type.value}")
        print(f"  是否重试: {decision.should_retry}")
        print(f"  等待时间: {decision.wait_seconds:.1f}s")
        print(f"  原因: {decision.reason}")
        print(f"  需要切换模式: {decision.should_switch_mode}")
        print()


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_smart_retry())

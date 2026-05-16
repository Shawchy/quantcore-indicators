import inspect
import random
import time
from typing import Any, Callable, Dict, List, Optional
from enum import Enum
from loguru import logger


class ErrorType(Enum):
    NETWORK = "network"
    RATE_LIMIT = "rate_limit"
    TLS_FINGERPRINT = "tls_fingerprint"
    SERVER = "server"
    AUTH = "auth"
    DATA = "data"
    UNKNOWN = "unknown"


class RetryDecision:
    __slots__ = ('should_retry', 'wait_seconds', 'fallback_mode')

    def __init__(self, should_retry: bool = False, wait_seconds: float = 0.0, fallback_mode: bool = False):
        self.should_retry = should_retry
        self.wait_seconds = wait_seconds
        self.fallback_mode = fallback_mode


class ErrorClassifier:
    _RATE_LIMIT_SIGNALS = ('429', 'too many requests', 'rate limit', '频率限制')
    _TLS_SIGNALS = ('remotedisconnected', 'remote end closed connection', 'tls', 'ssl', 'fingerprint')
    _NETWORK_SIGNALS = ('connectionerror', 'connectionabortederror', 'connectionreseterror', 'timeout', 'connecttimeout')
    _SERVER_SIGNALS = ('500', '502', '503', '504', 'internal server error', 'bad gateway', 'service unavailable')
    _AUTH_SIGNALS = ('401', '403', 'unauthorized', 'forbidden')

    @classmethod
    def classify(cls, error: Exception) -> ErrorType:
        error_type_name = type(error).__name__.lower()
        error_msg = str(error).lower()
        status_code = getattr(error, 'status_code', None)

        if status_code:
            if status_code == 429:
                return ErrorType.RATE_LIMIT
            if status_code in (401, 403):
                return ErrorType.AUTH
            if 500 <= status_code < 600:
                return ErrorType.SERVER

        for signal in cls._TLS_SIGNALS:
            if signal in error_type_name or signal in error_msg:
                return ErrorType.TLS_FINGERPRINT

        for signal in cls._RATE_LIMIT_SIGNALS:
            if signal in error_msg:
                return ErrorType.RATE_LIMIT

        for signal in cls._NETWORK_SIGNALS:
            if signal in error_type_name or signal in error_msg:
                return ErrorType.NETWORK

        for signal in cls._SERVER_SIGNALS:
            if signal in error_msg:
                return ErrorType.SERVER

        for signal in cls._AUTH_SIGNALS:
            if signal in error_msg:
                return ErrorType.AUTH

        return ErrorType.UNKNOWN

    @classmethod
    def should_retry(cls, error_type: ErrorType, attempt: int, max_retries: int) -> RetryDecision:
        if attempt >= max_retries:
            return RetryDecision(should_retry=False, fallback_mode=True)

        if error_type == ErrorType.TLS_FINGERPRINT:
            return RetryDecision(should_retry=False, fallback_mode=True)

        if error_type == ErrorType.AUTH:
            return RetryDecision(should_retry=False)

        if error_type == ErrorType.RATE_LIMIT:
            wait = min(2 ** attempt + random.uniform(0, 2), 30.0)
            return RetryDecision(should_retry=attempt < 1, wait_seconds=wait)

        if error_type == ErrorType.NETWORK:
            wait = min(2 ** attempt + random.uniform(0, 1), 10.0)
            return RetryDecision(should_retry=attempt < 2, wait_seconds=wait)

        if error_type == ErrorType.SERVER:
            wait = min(2 ** attempt + random.uniform(0, 1), 10.0)
            return RetryDecision(should_retry=attempt < 2, wait_seconds=wait)

        if error_type == ErrorType.DATA:
            return RetryDecision(should_retry=False)

        return RetryDecision(should_retry=False)


class SmartRetryExecutor:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._config = config or {}
        self._max_retries = self._config.get('max_retries', 3)
        self._base_wait = self._config.get('base_wait_seconds', 2.0)
        self._current_attempt = 0
        self._switch_mode_callback: Optional[Callable] = None

    def set_switch_mode_callback(self, callback: Callable) -> None:
        self._switch_mode_callback = callback

    async def execute_with_retry(
        self,
        func: Callable,
        *args: Any,
        context: str = "unknown",
        **kwargs: Any,
    ) -> Any:
        self._current_attempt = 0
        last_error: Optional[Exception] = None

        while self._current_attempt < self._max_retries:
            try:
                self._current_attempt += 1
                logger.debug(f"执行 {context}（第 {self._current_attempt}/{self._max_retries} 次尝试）")

                result = await func(*args, **kwargs) if inspect.iscoroutinefunction(func) else func(*args, **kwargs)
                self._current_attempt = 0
                return result

            except Exception as e:
                last_error = e
                error_type = ErrorClassifier.classify(e)
                decision = ErrorClassifier.should_retry(error_type, self._current_attempt, self._max_retries)

                logger.warning(
                    f"{context} 失败（尝试 {self._current_attempt}/{self._max_retries}）: "
                    f"{type(e).__name__}: {e} [error_type={error_type.value}]"
                )

                if decision.fallback_mode and self._switch_mode_callback:
                    logger.info(f"🔄 {context} 切换到降级模式")
                    self._switch_mode_callback()

                if not decision.should_retry:
                    break

                wait_time = decision.wait_seconds or min(self._base_wait * (2 ** (self._current_attempt - 1)) + random.uniform(0, 1), 10.0)
                logger.info(f"⏳ {context} {wait_time:.2f}秒后重试...")
                await asyncio.sleep(wait_time)

        self._current_attempt = 0
        if last_error is not None:
            raise last_error
        raise RuntimeError(f"{context} 执行失败，无异常信息")

    @property
    def current_attempt(self) -> int:
        return self._current_attempt


class RequestFrequencyController:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._config = config or {}
        self._min_interval = self._config.get('min_interval_seconds', 0.5)
        self._max_interval = self._config.get('max_interval_seconds', 5.0)
        self._request_timestamps: Dict[str, List[float]] = {}
        self._current_interval = self._min_interval

    async def acquire(self, key: str = "default") -> None:
        now = time.monotonic()
        timestamps = self._request_timestamps.get(key, [])
        timestamps = [t for t in timestamps if now - t < 60]
        self._request_timestamps[key] = timestamps

        if timestamps:
            elapsed = now - timestamps[-1]
            if elapsed < self._current_interval:
                wait = self._current_interval - elapsed
                await asyncio.sleep(wait)

        self._request_timestamps[key].append(time.monotonic())

    def on_success(self) -> None:
        self._current_interval = max(self._min_interval, self._current_interval * 0.9)

    def on_failure(self) -> None:
        self._current_interval = min(self._max_interval, self._current_interval * 1.5)

    def reset(self) -> None:
        self._current_interval = self._min_interval
        self._request_timestamps.clear()

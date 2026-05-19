class QuantException(Exception):
    def __init__(
        self,
        code: str = "UNKNOWN_ERROR",
        message: str = "未知错误",
        status_code: int = 500,
        detail: dict = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.detail = detail or {}
        super().__init__(self.message)
    
    def to_dict(self) -> dict:
        return {
            "success": False,
            "code": self.code,
            "message": self.message,
            "detail": self.detail
        }


class DataNotFoundException(QuantException):
    def __init__(self, message: str = "数据不存在", detail: dict = None):
        super().__init__(
            code="DATA_NOT_FOUND",
            message=message,
            status_code=404,
            detail=detail
        )


class InvalidParameterException(QuantException):
    def __init__(self, message: str = "参数错误", detail: dict = None):
        super().__init__(
            code="INVALID_PARAMETER",
            message=message,
            status_code=400,
            detail=detail
        )


class DataSourceException(QuantException):
    def __init__(self, message: str = "数据源错误", detail: dict = None):
        super().__init__(
            code="DATA_SOURCE_ERROR",
            message=message,
            status_code=503,
            detail=detail
        )


class StrategyException(QuantException):
    def __init__(self, message: str = "策略执行错误", detail: dict = None):
        super().__init__(
            code="STRATEGY_ERROR",
            message=message,
            status_code=500,
            detail=detail
        )


class BacktestException(QuantException):
    def __init__(self, message: str = "回测执行错误", detail: dict = None):
        super().__init__(
            code="BACKTEST_ERROR",
            message=message,
            status_code=500,
            detail=detail
        )


class AuthenticationException(QuantException):
    def __init__(self, message: str = "认证失败", detail: dict = None):
        super().__init__(
            code="AUTHENTICATION_FAILED",
            message=message,
            status_code=401,
            detail=detail
        )


class AuthorizationException(QuantException):
    def __init__(self, message: str = "权限不足", detail: dict = None):
        super().__init__(
            code="AUTHORIZATION_FAILED",
            message=message,
            status_code=403,
            detail=detail
        )


class RateLimitException(QuantException):
    def __init__(self, message: str = "请求过于频繁，请稍后再试", detail: dict = None):
        super().__init__(
            code="RATE_LIMIT_EXCEEDED",
            message=message,
            status_code=429,
            detail=detail
        )


class CircuitBreakerException(QuantException):
    def __init__(self, source: str = "", message: str = "", detail: dict = None):
        msg = message or f"数据源 {source} 当前不可用，请稍后重试"
        super().__init__(
            code="CIRCUIT_BREAKER_OPEN",
            message=msg,
            status_code=503,
            detail={"source": source, **(detail or {})}
        )


class ValidationException(QuantException):
    def __init__(self, message: str = "数据验证失败", detail: dict = None):
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            status_code=422,
            detail=detail
        )


class CacheException(QuantException):
    def __init__(self, message: str = "缓存操作失败", detail: dict = None):
        super().__init__(
            code="CACHE_ERROR",
            message=message,
            status_code=500,
            detail=detail
        )

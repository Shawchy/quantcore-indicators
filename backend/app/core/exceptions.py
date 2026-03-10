class QuantException(Exception):
    def __init__(
        self,
        code: str = "UNKNOWN_ERROR",
        message: str = "未知错误",
        status_code: int = 500
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class DataNotFoundException(QuantException):
    def __init__(self, message: str = "数据不存在"):
        super().__init__(
            code="DATA_NOT_FOUND",
            message=message,
            status_code=404
        )


class InvalidParameterException(QuantException):
    def __init__(self, message: str = "参数错误"):
        super().__init__(
            code="INVALID_PARAMETER",
            message=message,
            status_code=400
        )


class DataSourceException(QuantException):
    def __init__(self, message: str = "数据源错误"):
        super().__init__(
            code="DATA_SOURCE_ERROR",
            message=message,
            status_code=503
        )


class StrategyException(QuantException):
    def __init__(self, message: str = "策略执行错误"):
        super().__init__(
            code="STRATEGY_ERROR",
            message=message,
            status_code=500
        )


class BacktestException(QuantException):
    def __init__(self, message: str = "回测执行错误"):
        super().__init__(
            code="BACKTEST_ERROR",
            message=message,
            status_code=500
        )

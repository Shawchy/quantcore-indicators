"""数据适配器异常模块

提供统一的异常层级结构，用于处理数据适配器中的各种异常情况。

使用示例：
    async def get_kline(self, code: str, start_date: str, end_date: str) -> List[KLineData]:
        try:
            # ... 获取数据 ...
        except asyncio.TimeoutError:
            raise NetworkError(
                "获取 K 线数据超时",
                source_type=self.source_type.value,
                error_code="TIMEOUT",
                context={"code": code, "start_date": start_date, "end_date": end_date}
            )
        except PermissionError:
            raise AuthenticationError(
                "积分不足或权限受限",
                source_type=self.source_type.value,
                error_code="PERMISSION_DENIED",
                context={"code": code}
            )
"""
from typing import Optional, Dict, Any


class DataAdapterError(Exception):
    """数据适配器基础异常
    
    所有数据适配器相关异常的基类，提供统一的错误信息格式和上下文支持。
    
    Attributes:
        message: 错误消息
        source_type: 数据源类型（如 TUSHARE, AKSHARE 等）
        error_code: 错误代码（如 TIMEOUT, PERMISSION_DENIED 等）
        context: 错误上下文信息，包含有助于调试的额外信息
    """
    
    def __init__(
        self,
        message: str,
        source_type: Optional[str] = None,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.source_type = source_type
        self.error_code = error_code
        self.context = context or {}
    
    def __str__(self) -> str:
        """格式化错误信息"""
        parts = [self.message]
        if self.source_type:
            parts.append(f"数据源：{self.source_type}")
        if self.error_code:
            parts.append(f"错误代码：{self.error_code}")
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            parts.append(f"上下文：{context_str}")
        return " | ".join(parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """将异常信息转换为字典"""
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "source_type": self.source_type,
            "error_code": self.error_code,
            "context": self.context
        }


class AuthenticationError(DataAdapterError):
    """认证失败异常
    
    在以下情况抛出：
    - Token 无效或过期
    - API Key 权限不足
    - 用户积分不足
    - 账户被禁用
    
    示例：
        raise AuthenticationError(
            "Tushare Token 无效",
            source_type="TUSHARE",
            error_code="INVALID_TOKEN",
            context={"token_prefix": "abc123..."}
        )
    """
    pass


class NotFoundError(DataAdapterError):
    """数据未找到异常
    
    在以下情况抛出：
    - 股票代码不存在
    - 指定日期范围无数据
    - 接口不支持该数据类型的查询
    
    示例：
        raise NotFoundError(
            "股票不存在",
            source_type="AKSHARE",
            error_code="STOCK_NOT_FOUND",
            context={"code": "000001"}
        )
    """
    pass


class RateLimitError(DataAdapterError):
    """频率限制异常
    
    在以下情况抛出：
    - 请求过于频繁，触发限流
    - 超过 API 调用次数限制
    - 并发请求数超出允许范围
    
    示例：
        raise RateLimitError(
            "请求过于频繁，请稍后再试",
            source_type="TUSHARE",
            error_code="RATE_LIMITED",
            context={"retry_after": 60}
        )
    """
    pass


class NetworkError(DataAdapterError):
    """网络异常
    
    在以下情况抛出：
    - 连接超时
    - DNS 解析失败
    - 网络连接中断
    - SSL 证书验证失败
    
    示例：
        raise NetworkError(
            "连接超时",
            source_type="YFINANCE",
            error_code="CONNECTION_TIMEOUT",
            context={"url": "https://query1.finance.yahoo.com/", "timeout": 10}
        )
    """
    pass


class DataValidationError(DataAdapterError):
    """数据验证异常
    
    在以下情况抛出：
    - 数据格式不符合预期
    - 必填字段缺失
    - 数据值超出合理范围
    - 多数据源数据不一致
    
    示例：
        raise DataValidationError(
            "K 线数据缺少收盘价",
            source_type="BAOSTOCK",
            error_code="MISSING_FIELD",
            context={"field": "close", "code": "600000"}
        )
    """
    pass


class ConfigError(DataAdapterError):
    """配置错误
    
    在以下情况抛出：
    - 缺少必要的配置项
    - 配置值格式无效
    - 配置值超出允许范围
    - 配置文件无法读取
    
    示例：
        raise ConfigError(
            "缺少 Tushare Token 配置",
            source_type="TUSHARE",
            error_code="MISSING_CONFIG",
            context={"config_key": "tushare_token"}
        )
    """
    pass


class DataSourceUnavailableError(DataAdapterError):
    """数据源不可用异常
    
    在以下情况抛出：
    - 数据源服务宕机
    - 数据源维护中
    - 数据源接口已废弃
    
    示例：
        raise DataSourceUnavailableError(
            "数据源暂时不可用，请稍后重试",
            source_type="TICKFLOW",
            error_code="SERVICE_DOWN",
            context={"downtime_start": "2024-01-01 10:00:00"}
        )
    """
    pass


class DataIncompleteError(DataAdapterError):
    """数据不完整异常
    
    在以下情况抛出：
    - 返回数据量少于预期
    - 部分字段数据缺失
    - 历史数据有断档
    
    示例：
        raise DataIncompleteError(
            "只获取到部分数据",
            source_type="AKSHARE",
            error_code="INCOMPLETE_DATA",
            context={"expected": 1000, "actual": 500}
        )
    """
    pass


# 异常工厂函数
def create_error_from_exception(
    exc: Exception,
    source_type: Optional[str] = None,
    default_error_type: str = "DataAdapterError"
) -> DataAdapterError:
    """根据异常类型创建对应的数据适配器异常
    
    Args:
        exc: 原始异常对象
        source_type: 数据源类型
        default_error_type: 默认错误类型，当无法匹配时使用
    
    Returns:
        DataAdapterError: 数据适配器异常对象
    
    Example:
        try:
            # ... 某些操作 ...
        except Exception as e:
            error = create_error_from_exception(e, source_type="TUSHARE")
            raise error
    """
    error_mapping = {
        asyncio.TimeoutError: NetworkError,
        TimeoutError: NetworkError,
        ConnectionError: NetworkError,
        PermissionError: AuthenticationError,
        ValueError: DataValidationError,
        KeyError: DataValidationError,
        FileNotFoundError: ConfigError,
    }
    
    error_class = error_mapping.get(type(exc), globals().get(default_error_type, DataAdapterError))
    
    return error_class(
        message=str(exc),
        source_type=source_type,
        error_code=type(exc).__name__.upper(),
        context={"original_exception": repr(exc)}
    )


# 导入 asyncio 以便在工厂函数中使用
import asyncio

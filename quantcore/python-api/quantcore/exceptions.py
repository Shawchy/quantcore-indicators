# -*- coding: utf-8 -*-
"""
QuantCore 异常模块

提供统一的异常处理机制：
- QuantCoreException: 基础异常类
- DataException: 数据相关异常
- StrategyException: 策略相关异常
- RiskException: 风控相关异常
- EngineException: 引擎相关异常
- ConfigException: 配置相关异常
"""


class QuantCoreException(Exception):
    """QuantCore 基础异常类"""
    
    def __init__(self, message: str, code: str = None):
        """
        初始化异常
        
        Args:
            message: 异常消息
            code: 异常代码（可选）
        """
        super().__init__(message)
        self.message = message
        self.code = code
    
    def __str__(self):
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class DataException(QuantCoreException):
    """数据相关异常"""
    
    def __init__(self, message: str, code: str = "DATA_ERROR"):
        super().__init__(message, code)


class DataNotFoundException(DataException):
    """数据未找到"""
    
    def __init__(self, message: str = "数据未找到"):
        super().__init__(message, "DATA_NOT_FOUND")


class DataFormatException(DataException):
    """数据格式错误"""
    
    def __init__(self, message: str = "数据格式错误"):
        super().__init__(message, "DATA_FORMAT_ERROR")


class InsufficientDataException(DataException):
    """数据不足"""
    
    def __init__(self, message: str = "数据不足"):
        super().__init__(message, "INSUFFICIENT_DATA")


class StrategyException(QuantCoreException):
    """策略相关异常"""
    
    def __init__(self, message: str, code: str = "STRATEGY_ERROR"):
        super().__init__(message, code)


class StrategyNotInitializedException(StrategyException):
    """策略未初始化"""
    
    def __init__(self, message: str = "策略未初始化"):
        super().__init__(message, "STRATEGY_NOT_INITIALIZED")


class SignalException(StrategyException):
    """信号异常"""
    
    def __init__(self, message: str, signal_type: str = None):
        super().__init__(message, "SIGNAL_ERROR")
        self.signal_type = signal_type


class RiskException(QuantCoreException):
    """风控相关异常"""
    
    def __init__(self, message: str, code: str = "RISK_ERROR"):
        super().__init__(message, code)


class PositionLimitException(RiskException):
    """仓位限制异常"""
    
    def __init__(self, message: str = "超过仓位限制"):
        super().__init__(message, "POSITION_LIMIT")


class LossLimitException(RiskException):
    """亏损限制异常"""
    
    def __init__(self, message: str = "超过亏损限制"):
        super().__init__(message, "LOSS_LIMIT")


class TradingHaltException(RiskException):
    """交易暂停异常"""
    
    def __init__(self, message: str = "交易已暂停"):
        super().__init__(message, "TRADING_HALTED")


class EngineException(QuantCoreException):
    """引擎相关异常"""
    
    def __init__(self, message: str, code: str = "ENGINE_ERROR"):
        super().__init__(message, code)


class OrderException(EngineException):
    """订单异常"""
    
    def __init__(self, message: str, order_id: str = None):
        super().__init__(message, "ORDER_ERROR")
        self.order_id = order_id


class InvalidOrderException(OrderException):
    """无效订单"""
    
    def __init__(self, message: str = "无效订单"):
        super().__init__(message, "INVALID_ORDER")


class MatchingException(EngineException):
    """撮合异常"""
    
    def __init__(self, message: str = "撮合失败"):
        super().__init__(message, "MATCHING_ERROR")


class ConfigException(QuantCoreException):
    """配置相关异常"""
    
    def __init__(self, message: str, code: str = "CONFIG_ERROR"):
        super().__init__(message, code)


class InvalidConfigException(ConfigException):
    """无效配置"""
    
    def __init__(self, message: str = "配置无效"):
        super().__init__(message, "INVALID_CONFIG")


class MissingConfigException(ConfigException):
    """缺少配置"""
    
    def __init__(self, message: str = "缺少配置"):
        super().__init__(message, "MISSING_CONFIG")


# 导出
__all__ = [
    # 基础异常
    'QuantCoreException',
    
    # 数据异常
    'DataException',
    'DataNotFoundException',
    'DataFormatException',
    'InsufficientDataException',
    
    # 策略异常
    'StrategyException',
    'StrategyNotInitializedException',
    'SignalException',
    
    # 风控异常
    'RiskException',
    'PositionLimitException',
    'LossLimitException',
    'TradingHaltException',
    
    # 引擎异常
    'EngineException',
    'OrderException',
    'InvalidOrderException',
    'MatchingException',
    
    # 配置异常
    'ConfigException',
    'InvalidConfigException',
    'MissingConfigException',
]

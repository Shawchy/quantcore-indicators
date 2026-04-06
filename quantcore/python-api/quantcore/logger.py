"""
QuantCore 日志系统

提供统一的日志接口，支持：
- 日志级别控制
- 多输出目标（控制台/文件）
- 彩色输出
- 模块级别控制
"""

import logging
import sys
from datetime import datetime
from typing import Optional
from dataclasses import dataclass


# 日志级别
class LogLevel:
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


@dataclass
class LogConfig:
    """日志配置"""
    level: int = LogLevel.INFO
    console: bool = True
    file_path: Optional[str] = None
    format_string: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    color: bool = True


class QuantLogger:
    """
    QuantCore 日志器
    
    使用示例:
        logger = QuantLogger("QuantCore")
        logger.info("回测开始")
        logger.debug("订单已创建")
        logger.warning("资金不足")
        logger.error("交易失败")
    """
    
    _loggers = {}
    
    def __init__(self, name: str, config: Optional[LogConfig] = None):
        self.name = name
        self.config = config or LogConfig()
        self._logger = self._create_logger()
    
    def _create_logger(self) -> logging.Logger:
        """创建日志器"""
        logger = logging.getLogger(self.name)
        logger.setLevel(self.config.level)
        logger.handlers.clear()
        
        # 格式化器
        formatter = logging.Formatter(
            self.config.format_string,
            datefmt=self.config.date_format
        )
        
        # 控制台处理器
        if self.config.console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.config.level)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # 文件处理器
        if self.config.file_path:
            file_handler = logging.FileHandler(self.config.file_path, encoding='utf-8')
            file_handler.setLevel(self.config.level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    @classmethod
    def get_logger(cls, name: str, config: Optional[LogConfig] = None) -> 'QuantLogger':
        """获取日志器（单例模式）"""
        if name not in cls._loggers:
            cls._loggers[name] = QuantLogger(name, config)
        return cls._loggers[name]
    
    def debug(self, message: str):
        """调试信息"""
        self._logger.debug(message)
    
    def info(self, message: str):
        """一般信息"""
        self._logger.info(message)
    
    def warning(self, message: str):
        """警告信息"""
        self._logger.warning(message)
    
    def error(self, message: str):
        """错误信息"""
        self._logger.error(message)
    
    def critical(self, message: str):
        """严重错误"""
        self._logger.critical(message)
    
    def log(self, level: int, message: str):
        """自定义级别日志"""
        self._logger.log(level, message)


# 全局配置
_global_config = LogConfig(level=LogLevel.INFO, console=True, color=True)


def set_log_level(level: int):
    """设置全局日志级别"""
    global _global_config
    _global_config.level = level
    for logger in QuantLogger._loggers.values():
        logger._logger.setLevel(level)


def set_log_file(file_path: str):
    """设置日志文件路径"""
    global _global_config
    _global_config.file_path = file_path


def get_logger(name: str) -> QuantLogger:
    """获取日志器的便捷函数"""
    return QuantLogger.get_logger(name, _global_config)


# 预定义日志器
def get_backtest_logger() -> QuantLogger:
    """获取回测日志器"""
    return get_logger("QuantCore.Backtest")


def get_strategy_logger() -> QuantLogger:
    """获取策略日志器"""
    return get_logger("QuantCore.Strategy")


def get_data_logger() -> QuantLogger:
    """获取数据日志器"""
    return get_logger("QuantCore.Data")


def get_trade_logger() -> QuantLogger:
    """获取交易日志器"""
    return get_logger("QuantCore.Trade")


# 上下文管理器，用于临时改变日志级别
class log_context:
    """日志上下文管理器"""
    
    def __init__(self, logger: QuantLogger, level: int):
        self.logger = logger
        self.new_level = level
        self.old_level = None
    
    def __enter__(self):
        self.old_level = self.logger._logger.level
        self.logger._logger.setLevel(self.new_level)
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger._logger.setLevel(self.old_level)


# 装饰器，用于记录函数调用
def log_call(logger: Optional[QuantLogger] = None):
    """记录函数调用的装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            log = logger or get_logger(func.__module__)
            log.debug(f"调用 {func.__name__}")
            try:
                result = func(*args, **kwargs)
                log.debug(f"{func.__name__} 执行完成")
                return result
            except Exception as e:
                log.error(f"{func.__name__} 执行失败: {e}")
                raise
        return wrapper
    return decorator

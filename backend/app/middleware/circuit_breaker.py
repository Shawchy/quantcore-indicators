"""
断路器实现

实现断路器模式，防止故障数据源拖垮系统
"""
import asyncio
from enum import Enum
from datetime import datetime, timedelta
from typing import Optional, Callable, Any, Dict
from loguru import logger


class CircuitState(Enum):
    """断路器状态"""
    CLOSED = "closed"          # 正常状态
    OPEN = "open"              # 熔断状态
    HALF_OPEN = "half_open"    # 半开状态（试探）


class CircuitBreaker:
    """断路器"""
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 3
    ):
        """
        初始化断路器
        
        Args:
            name: 断路器名称
            failure_threshold: 失败阈值
            recovery_timeout: 恢复超时（秒）
            half_open_max_calls: 半开状态最大调用数
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self._failure_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._state = CircuitState.CLOSED
        self._half_open_calls = 0
        
        self._stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "rejected_calls": 0
        }
        
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        执行调用（带断路器保护）
        
        Args:
            func: 要执行的异步函数
            *args: 位置参数
            **kwargs: 关键字参数
        
        Returns:
            函数执行结果
        
        Raises:
            Exception: 断路器打开或函数执行失败
        """
        async with self._lock:
            self._stats["total_calls"] += 1
            
            # 检查断路器状态
            if self._state == CircuitState.OPEN:
                if self._should_try_reset():
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    logger.info(f"断路器 [{self.name}] 进入半开状态")
                else:
                    self._stats["rejected_calls"] += 1
                    raise Exception(
                        f"断路器 [{self.name}] 已打开，拒绝调用"
                    )
        
        # 执行调用
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise e
    
    async def _on_success(self):
        """成功回调"""
        async with self._lock:
            self._stats["successful_calls"] += 1
            self._failure_count = 0
            
            if self._state == CircuitState.HALF_OPEN:
                self._half_open_calls += 1
                if self._half_open_calls >= self.half_open_max_calls:
                    self._state = CircuitState.CLOSED
                    logger.info(f"断路器 [{self.name}] 关闭，恢复正常")
    
    async def _on_failure(self):
        """失败回调"""
        async with self._lock:
            self._stats["failed_calls"] += 1
            self._failure_count += 1
            self._last_failure_time = datetime.now()
            
            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning(
                    f"断路器 [{self.name}] 打开，"
                    f"失败次数: {self._failure_count}"
                )
    
    def _should_try_reset(self) -> bool:
        """是否应该尝试重置"""
        if self._last_failure_time is None:
            return True
        return (
            datetime.now() - self._last_failure_time
        ).seconds >= self.recovery_timeout
    
    def get_state(self) -> str:
        """获取当前状态"""
        return self._state.value
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        total = self._stats["total_calls"]
        success_rate = (
            self._stats["successful_calls"] / total * 100
            if total > 0 else 0.0
        )
        
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            **self._stats,
            "success_rate": f"{success_rate:.2f}%",
            "last_failure_time": (
                self._last_failure_time.isoformat()
                if self._last_failure_time else None
            )
        }
    
    def reset(self):
        """重置断路器"""
        self._failure_count = 0
        self._last_failure_time = None
        self._state = CircuitState.CLOSED
        self._half_open_calls = 0
        logger.info(f"断路器 [{self.name}] 已重置")


# 断路器配置
CIRCUIT_BREAKER_CONFIG = {
    "efinance": {
        "failure_threshold": 5,
        "recovery_timeout": 60,
        "half_open_max_calls": 3
    },
    "akshare": {
        "failure_threshold": 5,
        "recovery_timeout": 60,
        "half_open_max_calls": 3
    },
    "baostock": {
        "failure_threshold": 3,
        "recovery_timeout": 120,
        "half_open_max_calls": 2
    },
    "tickflow": {
        "failure_threshold": 10,
        "recovery_timeout": 30,
        "half_open_max_calls": 5
    },
}

# 全局断路器实例
circuit_breakers: Dict[str, CircuitBreaker] = {}


def init_circuit_breakers():
    """初始化断路器"""
    global circuit_breakers
    
    for source, config in CIRCUIT_BREAKER_CONFIG.items():
        circuit_breakers[source] = CircuitBreaker(
            name=source,
            failure_threshold=config["failure_threshold"],
            recovery_timeout=config["recovery_timeout"],
            half_open_max_calls=config["half_open_max_calls"]
        )
        logger.info(
            f"初始化断路器: {source}, "
            f"失败阈值: {config['failure_threshold']}, "
            f"恢复超时: {config['recovery_timeout']}s"
        )


def get_circuit_breaker(source: str) -> Optional[CircuitBreaker]:
    """获取指定数据源的断路器"""
    return circuit_breakers.get(source)

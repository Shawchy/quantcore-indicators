"""
智能重试策略

根据错误类型智能决策重试策略，自动降级。
"""

import inspect
import random
from typing import Any, Dict, Optional, Callable
from loguru import logger
from .base import BaseStrategy


class SmartRetryStrategy(BaseStrategy):
    """智能重试策略"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._max_retries = self.config.get('max_retries', 3)
        self._current_attempt = 0
    
    async def before_request(self, url: str, method: str, headers: Dict[str, str]) -> Dict[str, str]:
        """请求前处理"""
        return headers
    
    async def after_request(self, response: Any) -> Any:
        """请求后处理"""
        return response
    
    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        context: str = "unknown",
        on_switch_mode: Optional[Callable] = None,
        **kwargs
    ) -> Any:
        """
        带智能重试的执行
        
        Args:
            func: 要执行的函数
            args: 位置参数
            context: 执行上下文（用于日志）
            on_switch_mode: 切换模式时的回调函数
            kwargs: 关键字参数
            
        Returns:
            函数执行结果
            
        Raises:
            Exception: 所有重试失败后抛出异常
        """
        self._current_attempt = 0
        last_error = None
        
        while self._current_attempt < self._max_retries:
            try:
                self._current_attempt += 1
                logger.debug(f"执行 {context}（第 {self._current_attempt}/{self._max_retries} 次尝试）")
                
                # 执行函数
                result = await func(*args, **kwargs) if inspect.iscoroutinefunction(func) else func(*args, **kwargs)
                
                # 成功，重置尝试计数
                self._current_attempt = 0
                return result
                
            except Exception as e:
                last_error = e
                error_type = type(e).__name__
                error_msg = str(e)
                
                logger.warning(f"{context} 失败（尝试 {self._current_attempt}/{self._max_retries}）: {error_type}: {error_msg}")
                
                # 智能决策：是否重试
                should_retry = await self._should_retry(e)
                
                if not should_retry:
                    logger.warning(f"{context} 不重试，直接失败")
                    break
                
                # 检查是否达到最大重试次数
                if self._current_attempt >= self._max_retries:
                    logger.warning(f"{context} 达到最大重试次数")
                    break
                
                # 等待后重试
                wait_time = self._calculate_wait_time()
                logger.info(f"⏳ {context} {wait_time:.2f}秒后重试...")
                await asyncio.sleep(wait_time)
        
        # 所有重试失败
        logger.error(f"❌ {context} 所有重试失败（{self._max_retries}次）: {last_error}")
        
        if on_switch_mode:
            logger.info(f"🔄 准备切换到降级模式")
            on_switch_mode()
        
        raise last_error
    
    async def _should_retry(self, error: Exception) -> bool:
        """
        判断是否应该重试
        
        Args:
            error: 异常对象
            
        Returns:
            是否重试
        """
        error_type = type(error).__name__
        error_msg = str(error).lower()
        
        # TLS 指纹错误：不重试，直接降级
        if error_type == 'RemoteDisconnected' or 'Remote end closed connection' in error_msg:
            logger.warning("检测到 TLS 指纹错误，不重试，切换到降级模式")
            return False
        
        # HTTP 429：频率限制，重试 1 次
        if '429' in error_msg or 'Too Many Requests' in error_msg:
            logger.warning("检测到频率限制（429），重试 1 次")
            return self._current_attempt < 1
        
        # 网络错误：重试 2 次
        if error_type in ['ConnectionError', 'ConnectionAbortedError', 'ConnectionResetError']:
            logger.warning("检测到网络错误，重试 2 次")
            return self._current_attempt < 2
        
        # 服务器错误（5xx）：重试 2 次
        if hasattr(error, 'status_code') and error.status_code and 500 <= error.status_code < 600:
            logger.warning("检测到服务器错误（5xx），重试 2 次")
            return self._current_attempt < 2
        
        # 其他错误：不重试
        logger.debug(f"其他错误类型，不重试")
        return False
    
    def _calculate_wait_time(self) -> float:
        """
        计算等待时间（指数退避）
        
        Returns:
            等待时间（秒）
        """
        # 指数退避：2^attempt + 随机抖动
        base_delay = 2 ** (self._current_attempt - 1)
        jitter = random.uniform(0, 1)  # 0-1 秒随机抖动
        wait_time = base_delay + jitter
        
        # 最大等待时间不超过 10 秒
        return min(wait_time, 10.0)
    
    def get_current_attempt(self) -> int:
        """获取当前尝试次数"""
        return self._current_attempt
    
    def reset(self):
        """重置尝试计数"""
        self._current_attempt = 0

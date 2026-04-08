"""
请求频率控制策略

自适应延迟，根据时间段和失败次数动态调整请求频率。
"""

import asyncio
import random
from datetime import datetime
from typing import Any, Dict, Optional
from loguru import logger
from .base import BaseStrategy


class RateLimitStrategy(BaseStrategy):
    """频率控制策略"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._consecutive_failures = 0
        self._request_count = 0
        self._last_request_time: Optional[datetime] = None
        
        # 基础延迟配置（秒）
        self._base_min_delay = self.config.get('min_delay', 1.0)
        self._base_max_delay = self.config.get('max_delay', 3.0)
    
    async def before_request(self, url: str, method: str, headers: Dict[str, str]) -> Dict[str, str]:
        """请求前执行限流"""
        if not self.enabled:
            return headers
        
        # 计算延迟
        delay = await self._calculate_delay()
        
        if delay > 0:
            logger.debug(f"⏳ 请求限流：延迟 {delay:.2f}秒")
            await asyncio.sleep(delay)
        
        self._request_count += 1
        self._last_request_time = datetime.now()
        
        return headers
    
    async def _calculate_delay(self) -> float:
        """计算延迟时间"""
        min_delay, max_delay = self._get_time_based_delay()
        
        # 根据失败次数增加延迟
        if self._consecutive_failures > 3:
            multiplier = 1 + (self._consecutive_failures - 3) * 0.5
            min_delay *= multiplier
            max_delay *= multiplier
            logger.debug(f"⚠️  连续失败 {_consecutive_failures} 次，延迟增加 {multiplier:.1f}x")
        
        # 随机延迟
        delay = random.uniform(min_delay, max_delay)
        return delay
    
    def _get_time_based_delay(self) -> tuple:
        """根据时间段获取基础延迟"""
        now = datetime.now()
        hour = now.hour
        
        # 交易时段：9:30-15:00
        if (hour == 9 and now.minute >= 30) or (10 <= hour <= 14) or (hour == 15 and now.minute == 0):
            # 交易时段，使用保守延迟
            return (max(2.0, self._base_min_delay), max(4.0, self._base_max_delay))
        
        # 非交易时段，使用正常延迟
        return (self._base_min_delay, self._base_max_delay)
    
    async def after_request(self, response: Any) -> Any:
        """请求后处理（根据响应调整）"""
        if response is not None:
            # 检查状态码
            status_code = getattr(response, 'status_code', None)
            
            if status_code == 429:
                # 触发限流，增加失败计数
                self._consecutive_failures += 1
                logger.warning(f"⚠️  触发限流（429），增加延迟")
            elif status_code and 200 <= status_code < 300:
                # 成功，重置失败计数
                self._consecutive_failures = 0
        
        return response
    
    def record_failure(self):
        """记录失败"""
        self._consecutive_failures += 1
        logger.debug(f"失败计数：{self._consecutive_failures}")
    
    def reset_failure_count(self):
        """重置失败计数"""
        self._consecutive_failures = 0
        logger.debug("失败计数已重置")
    
    def get_current_delay_range(self) -> tuple:
        """获取当前延迟范围"""
        min_delay, max_delay = self._get_time_based_delay()
        
        if self._consecutive_failures > 3:
            multiplier = 1 + (self._consecutive_failures - 3) * 0.5
            min_delay *= multiplier
            max_delay *= multiplier
        
        return (min_delay, max_delay)

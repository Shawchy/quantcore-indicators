"""
User-Agent 轮换策略

定期轮换 User-Agent，降低被识别风险。
"""

import random
from typing import Any, Dict, Optional
from loguru import logger
from .base import BaseStrategy


class UARotatorStrategy(BaseStrategy):
    """UA 轮换策略"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._request_count = 0
        self._current_ua_index = 0
        self._rotation_interval = self.config.get('rotation_interval', 10)  # 每 10 次请求轮换
        
        # 初始化 UA 池（11 个，带概率权重）
        self._user_agents = self._initialize_user_agents()
    
    def _initialize_user_agents(self) -> list:
        """初始化 User-Agent 池"""
        return [
            # Windows + Chrome（主力，50% 概率）
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            
            # macOS + Chrome（20% 概率）
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            
            # Windows + Edge（15% 概率）
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
            
            # Windows + Firefox（10% 概率）
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
            
            # macOS + Safari（5% 概率）
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
        ]
    
    async def before_request(self, url: str, method: str, headers: Dict[str, str]) -> Dict[str, str]:
        """请求前轮换 UA"""
        if not self.enabled:
            return headers
        
        self._request_count += 1
        
        # 定期轮换
        if self._request_count % self._rotation_interval == 0:
            self._rotate()
        
        # 设置当前 UA
        current_ua = self._get_current_ua()
        headers['User-Agent'] = current_ua
        
        logger.debug(f"使用 UA: {current_ua[:50]}...")
        
        return headers
    
    async def after_request(self, response: Any) -> Any:
        """请求后处理"""
        return response
    
    def _rotate(self):
        """轮换到下一个 UA"""
        self._current_ua_index = (self._current_ua_index + 1) % len(self._user_agents)
        logger.info(f"UA 已轮换：{self._user_agents[self._current_ua_index][:50]}...")
    
    def _get_current_ua(self) -> str:
        """获取当前 UA"""
        return self._user_agents[self._current_ua_index]
    
    def get_current_ua(self) -> str:
        """获取当前 UA（公开方法）"""
        return self._get_current_ua()
    
    def get_ua_pool_size(self) -> int:
        """获取 UA 池大小"""
        return len(self._user_agents)
    
    def add_user_agent(self, ua: str):
        """添加自定义 UA"""
        self._user_agents.append(ua)
        logger.info(f"已添加自定义 UA")

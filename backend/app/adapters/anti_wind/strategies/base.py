"""
反爬策略基类

所有反爬策略都应继承此基类，实现统一的接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from loguru import logger


class BaseStrategy(ABC):
    """反爬策略基类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化策略
        
        Args:
            config: 策略配置字典
        """
        self.config = config or {}
        self.enabled = True
        self.name = self.__class__.__name__
        logger.debug(f"策略 {self.name} 初始化完成")
    
    @abstractmethod
    async def before_request(self, url: str, method: str, headers: Dict[str, str]) -> Dict[str, str]:
        """
        请求前执行
        
        Args:
            url: 请求 URL
            method: 请求方法
            headers: 请求头
            
        Returns:
            处理后的请求头
        """
        pass
    
    @abstractmethod
    async def after_request(self, response: Any) -> Any:
        """
        请求后执行
        
        Args:
            response: 响应对象
            
        Returns:
            处理后的响应对象
        """
        pass
    
    def enable(self):
        """启用策略"""
        self.enabled = True
        logger.info(f"策略 {self.name} 已启用")
    
    def disable(self):
        """禁用策略"""
        self.enabled = False
        logger.info(f"策略 {self.name} 已禁用")
    
    def is_enabled(self) -> bool:
        """检查策略是否启用"""
        return self.enabled
    
    def update_config(self, config: Dict[str, Any]):
        """更新配置"""
        self.config.update(config)
        logger.debug(f"策略 {self.name} 配置已更新")

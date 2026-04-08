"""
Cookie 注入策略

优先级最高的策略，注入真实用户 Cookie 绕过反爬检测。
"""

from typing import Any, Dict, Optional
from loguru import logger
from .base import BaseStrategy


class CookieInjectStrategy(BaseStrategy):
    """Cookie 注入策略"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._cookies: Dict[str, str] = {}
        self._cookies_updated_at: Optional[Any] = None
    
    async def initialize(self):
        """初始化 Cookie（懒加载）"""
        if self._cookies:
            return
        
        # 从配置文件加载手动 Cookie
        await self._load_manual_cookies()
    
    async def _load_manual_cookies(self):
        """加载手动配置的 Cookie"""
        import os
        import json
        from pathlib import Path
        from datetime import datetime
        
        cookie_file = Path(self.config.get('cookie_storage_dir', 'data/cookies')) / 'eastmoney_com_manual.json'
        
        if cookie_file.exists():
            try:
                with open(cookie_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 检查是否过期
                captured_at = datetime.fromisoformat(data['captured_at'])
                expires_in_days = data.get('expires_in_days', 7)
                
                if (datetime.now() - captured_at).days < expires_in_days:
                    # 转换为字典格式
                    for cookie in data['cookies']:
                        self._cookies[cookie['name']] = cookie['value']
                    
                    self._cookies_updated_at = captured_at
                    logger.info(f"✅ 手动 Cookie 加载成功（{len(self._cookies)} 个）")
                else:
                    logger.warning(f"⚠️  手动 Cookie 已过期")
                    
            except Exception as e:
                logger.error(f"加载手动 Cookie 失败：{e}")
    
    async def before_request(self, url: str, method: str, headers: Dict[str, str]) -> Dict[str, str]:
        """请求前注入 Cookie"""
        if not self.enabled:
            return headers
        
        # 确保已初始化
        if not self._cookies:
            await self.initialize()
        
        # 注入 Cookie
        if self._cookies:
            cookie_string = '; '.join([f"{k}={v}" for k, v in self._cookies.items()])
            headers['Cookie'] = cookie_string
            logger.debug(f"✅ Cookie 已注入（{len(self._cookies)} 个）")
        
        return headers
    
    async def after_request(self, response: Any) -> Any:
        """请求后处理（更新 Cookie）"""
        return response
    
    def set_cookie(self, name: str, value: str):
        """设置单个 Cookie"""
        self._cookies[name] = value
        logger.debug(f"Cookie 已设置：{name}")
    
    def get_cookie(self, name: str) -> Optional[str]:
        """获取单个 Cookie"""
        return self._cookies.get(name)
    
    def clear_cookies(self):
        """清空所有 Cookie"""
        self._cookies.clear()
        self._cookies_updated_at = None
        logger.info("所有 Cookie 已清空")
